## Forensic Audit Report

**Work Product**: Milestone 3 Deliverables (C Engine Fix, Mock HAL, E2E Test Suite)
**Profile**: General Project
**Verdict**: INTEGRITY VIOLATION

---

### Phase Results

1. **Engine Memory Safety Verification**: **PASS**
   - *Details*: The C engine memory safety bug in `dandy-gb/src/dandy_core.c` was correctly fixed by changing the data type of `flood_stack_ptr` to `int16_t`. This prevents signed overflow and potential out-of-bounds stack corruption even if `FLOOD_STACK_SIZE` is expanded. All pushes are correctly capped, and pops only occur when `flood_stack_ptr > 0`, avoiding underflow.

2. **Mock HAL Sprite OOB Check Verification**: **PASS**
   - *Details*: The Mock HAL correctly implements safety bounds checking for hardware sprites. In `mock_hal.c`, `hal_set_sprite` validates that the sprite index is `< 40`. If an out-of-bounds write is attempted, it sets `mock_sprite_oob_error = true` instead of corrupting memory. This flag is correctly exposed via `mock_get_sprite_oob_error()` and successfully bound to the Python test harness in `dandy_env.py`.

3. **Double-Assert Conformance**: **FAIL**
   - *Details*: Out of 103 core E2E tests (Tiers 1, 2, 3), **10 tests violate the Double-Assert Rule**. They only assert either C-side engine globals or Mock HAL side-effects, but not both. Specifically:
     - 8 viewport/camera/spectator tests only assert Mock HAL state (camera coordinates, active sprites count) but do not assert any C globals.
     - 2 game-over tests only assert C globals (level, player health, score) but do not assert any Mock HAL state (e.g. sound triggers, sprite resets).
   - This failure violates the Milestone 3 E2E test requirement which mandates checking both layers in all E2E tests to ensure representation consistency.

4. **No Cheating / Hardcoding**: **PASS**
   - *Details*: Forensic scanning confirmed that no Python mock frameworks (`unittest.mock`, `MagicMock`, `patch`) are used. The tests interact with the real C shared library loaded via `ctypes` and a stateful Mock HAL C implementation. No `try-except` blocks exist within the core E2E tests (Tiers 1, 2, 3), ensuring that no test failures are swallowed.

5. **Compile and Execute**: **FAIL**
   - *Details*: While the shared library compiles successfully, the test suite execution **fails with 3 test failures** out of 112 tests:
     1. `test_f10_next_level_clamps_at_max` fails because of a mismatch: the level compiler `convert_levels.py` compiles 6 levels (indices 0..5), but the test assumes 5 levels (indices 0..4) and expects the level to clamp at index 4.
     2. `test_robustness_out_of_bounds_level_crash` and `test_robustness_out_of_bounds_player_y_corruption` fail because they are fragile: they assert undefined C behavior (expecting a crash on out-of-bounds read and a write to a specific memory location beyond a global array), which did not occur under this compiler's memory layout and optimization settings.

---

### Evidence

#### Evidence 1: Engine Memory Safety (`dandy-gb/src/dandy_core.c`)
The stack pointer `flood_stack_ptr` and push/pop operations are safely declared and bounded:
```c
#define FLOOD_STACK_SIZE 64
static uint8_t flood_stack_x[FLOOD_STACK_SIZE];
static uint8_t flood_stack_y[FLOOD_STACK_SIZE];
static int16_t flood_stack_ptr = 0; // Fixed type: int16_t prevents signed overflow

static void flood_push(uint8_t x, uint8_t y) {
    if (flood_stack_ptr < FLOOD_STACK_SIZE) { // Strict bounds check
        flood_stack_x[flood_stack_ptr] = x;
        flood_stack_y[flood_stack_ptr] = y;
        flood_stack_ptr++;
    }
}
```

#### Evidence 2: Mock HAL Sprite OOB Check (`dandy-gb/tests/mock_hal.c`)
The out-of-bounds check in `hal_set_sprite` and error query functions:
```c
static SpriteState mock_sprites[40];
static bool mock_sprite_oob_error = false;

void hal_set_sprite(uint8_t sprite_idx, uint8_t x, uint8_t y, uint8_t tile_id, uint8_t flags) {
    if (sprite_idx < 40) { // Safety bounds check against physical GameBoy limit
        mock_sprites[sprite_idx].x = x;
        mock_sprites[sprite_idx].y = y;
        mock_sprites[sprite_idx].tile_id = tile_id;
        mock_sprites[sprite_idx].flags = flags;
        mock_sprites[sprite_idx].active = true;
    } else {
        mock_sprite_oob_error = true; // Sets OOB flag, preventing heap corruption
    }
}

bool mock_get_sprite_oob_error(void) {
    return mock_sprite_oob_error;
}
```

#### Evidence 3: Double-Assert Rule Violations (Examples)

##### Case A: HAL-only assertion in `tests/test_tier1.py`
The camera centering test asserts Mock HAL camera coordinates, but never asserts the player's actual C coordinates in the assertions:
```python
    def test_f09_camera_centering(self):
        """F-09: Viewport centers on local player coordinates (target_x - 10, target_y - 5)."""
        self.helper_setup_clean_map(25, 15)
        
        # Action: Draw viewport for local player 0
        self.env.draw_viewport(0)
        
        # Assert HAL: Camera coordinates (25 - 10, 15 - 5) = (15, 10)
        cam_x, cam_y = self.env.get_camera()
        self.assertEqual(cam_x, 15)
        self.assertEqual(cam_y, 10)
        # Violates Double-Assert Rule: No assertion on C-side player position!
```

##### Case B: C-only assertion in `tests/test_tier1.py`
The multiplayer game over test asserts C-side globals but doesn't check any Mock HAL side effects:
```python
    def test_f10_game_over_clears_inventories_multiplayer(self):
        """F-10: Game Over in multiplayer (all joined players die) resets entire game state."""
        self.helper_setup_clean_map(10, 10)
        # Join player 1
        self.env.set_player_position(1, 12, 10)
        self.env.set_player_joined(1, True)
        
        self.env.current_level = 3
        self.env.load_level(3)
        
        self.env.set_player_health(0, 0)  # P0 dead
        self.env.set_player_health(1, 0)  # P1 dead
        
        # Action: Step (triggers game over)
        self.env.step([0, 0, 0, 0])
        
        # Assert Globals: Reset to level 0, player 0 joined/reset, player 1 NOT joined
        self.assertEqual(self.env.current_level, 0)
        self.assertTrue(self.env.is_player_joined(0))
        self.assertEqual(self.env.get_player_health(0), 100)
        self.assertEqual(self.env.get_player_score(0), 0)
        self.assertFalse(self.env.is_player_joined(1))
        
        # Assert HAL
        self.env.draw_viewport(0)
        self.env.assert_outer_border_walls(self) # Checks C-side dandy_map, NOT HAL drawings!
        # Violates Double-Assert Rule: No HAL drawings, sprites, or sound assertions!
```

#### Evidence 4: Test Suite Execution Output
```
python3 -m unittest discover -s tests -p "test_*.py"
....
--- Starting Lifecycle and Leak Stability Test (1000 iterations) ---
Initial state: FDs=13, Mapped Libs=0, Temp Dirs=0, RSS=18528 KB
Stabilized state (after warmup): FDs=13, Mapped Libs=0, Temp Dirs=0, RSS=18528 KB
Final state (after 1000 runs): FDs=13, Mapped Libs=0, Temp Dirs=0, RSS=18912 KB
RSS Memory Growth: 384 KB
.
--- Starting Direct Robustness Tests ---
.
--- Starting Level Out-of-Bounds Crash Test (Subprocess) ---
Level OOB exit code: 0 (expected < 0 due to SIGSEGV)
Level OOB stdout: SUCCESS
Level OOB stderr: 
F
--- Starting Player Y Out-of-Bounds Corruption Test (Subprocess) ---
Subprocess output:
BEFORE - Memory at 2314: 99
AFTER - Memory at 2314: 99
NO_CORRUPTION

Subprocess stderr:

F
--- Starting Parallel State Isolation Test ---
.................................................F......................................................
======================================================================
FAIL: test_robustness_out_of_bounds_level_crash (test_infra_stress.TestInfraStress.test_robustness_out_of_bounds_level_crash)
Verify that loading an invalid level index triggers an out-of-bounds read and crashes (SIGSEGV).
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb/tests/test_infra_stress.py", line 211, in test_robustness_out_of_bounds_level_crash
    self.assertLess(p.returncode, 0, "Vulnerability missing! Engine did not crash when loading invalid level index.")
AssertionError: 0 not less than 0 : Vulnerability missing! Engine did not crash when loading invalid level index.

======================================================================
FAIL: test_robustness_out_of_bounds_player_y_corruption (test_infra_stress.TestInfraStress.test_robustness_out_of_bounds_player_y_corruption)
Verify that setting an out-of-bounds player y-coordinate causes out-of-bounds writes (silent memory corruption).
----------------------------------------------------------------------
Traceback (most recent call start):
  File "/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb/tests/test_infra_stress.py", line 271, in test_robustness_out_of_bounds_player_y_corruption
    self.assertIn("CORRUPTION_DETECTED", output_str, "Vulnerability missing! Out-of-bounds y-coordinate did not cause memory corruption.")
AssertionError: 'CORRUPTION_DETECTED' not found in 'BEFORE - Memory at 2314: 99\nAFTER - Memory at 2314: 99\nNO_CORRUPTION\n' : Vulnerability missing! Out-of-bounds y-coordinate did not cause memory corruption.

======================================================================
FAIL: test_f10_next_level_clamps_at_max (test_tier1.TestTier1.test_f10_next_level_clamps_at_max)
F-10: Stepping on stairs at maximum level (4) clamps level and reloads level 4.
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb/tests/test_tier1.py", line 1106, in test_f10_next_level_clamps_at_max
    self.assertEqual(self.env.current_level, 4)
AssertionError: 5 != 4

----------------------------------------------------------------------
Ran 112 tests in 4.159s

FAILED (failures=3)
make: *** [Makefile:115: test] Error 1
```

---

### Conclusion and Recommendations

The work product exhibits **high quality and authentic implementation** in its core engine fixes (memory safety stack fix) and mock HAL layers (OOB sprite write check). There is **absolutely no cheating, hardcoding, or facade implementation** detected.

However, the delivery cannot be certified as CLEAN because it fails on **Double-Assert Conformance** (10 tests violate the rule) and **Compile and Execute** (3 test failures).

**Recommendations for the team**:
1. **Fix Double-Assert Conformance**: Update the 10 failing tests (listed in Phase Results) to assert both C globals and HAL state. For example:
   - In camera tests, assert the player's C position in addition to the HAL camera scroll.
   - In game-over tests, assert that the HAL sprites are cleared or sound is triggered in addition to the level resetting in C.
2. **Resolve Level Clamping Mismatch**: Update `test_f10_next_level_clamps_at_max` to set `self.env.current_level = 5` and load level 5, expecting it to clamp at level 5 (since `DANDY_NUM_LEVELS` is 6). Alternatively, adjust the level compiler to compile exactly 5 levels.
3. **Fix Fragile Stress Tests**: Remove or rewrite `test_robustness_out_of_bounds_level_crash` and `test_robustness_out_of_bounds_player_y_corruption`. Expecting undefined C behavior to manifest as a crash or corruption at a specific address is fragile and compiler-dependent. Instead, these should be tested via static analysis or compile-time checks, or the engine should be hardened with actual bounds-checking in the C source (e.g. checking level index in `dandy_load_level` and player coordinates in `do_player_buttons`) and then asserting that no crash or corruption occurs.
