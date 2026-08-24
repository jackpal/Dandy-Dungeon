## 2026-06-20T22:15:00Z
You are an Explorer agent (archetype: teamwork_preview_explorer).
Your task is to analyze the Forensic Auditor's findings and design a remediation strategy to fix the identified integrity violations and test suite failures for Milestone 3 of the Dandy Dungeon Testing Track.

Your working directory is: /usr/local/google/home/jackpal/Developer/Dandy-Dungeon/.agents/explorer_remedy_3_gen2/

Below is the VERBATIM Forensic Auditor's evidence and audit report:
---
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
   - *Details*: Out of 103 core E2E tests (Tiers 1, 2, 3), **10 tests violate the Double-Assert Rule**. They only assert either C-side engine globals or Mock HAL state, but not both. Specifically:
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
FAIL: test_robustness_out_of_bounds_level_crash (test_infra_stress.TestInfraStress.test_robustness_out_of_bounds_level_crash)
AssertionError: 0 not less than 0 : Vulnerability missing! Engine did not crash when loading invalid level index.

FAIL: test_robustness_out_of_bounds_player_y_corruption (test_infra_stress.TestInfraStress.test_robustness_out_of_bounds_player_y_corruption)
AssertionError: 'CORRUPTION_DETECTED' not found in 'BEFORE - Memory at 2314: 99\nAFTER - Memory at 2314: 99\nNO_CORRUPTION\n'
---

Please perform the following:
1. Focus primarily on resolving the **failing fragile stress tests** in `dandy-gb/tests/test_infra_stress.py` (`test_robustness_out_of_bounds_level_crash` and `test_robustness_out_of_bounds_player_y_corruption`).
2. Analyze why these tests are fragile: they rely on undefined behavior (out-of-bounds reads triggering segfaults, and out-of-bounds writes corrupting specific segments) which are highly compiler-dependent and did not manifest under the active GCC environment.
3. Recommend a robust strategy:
   - Should the C engine itself be hardened with actual bounds-checking in `dandy_load_level` (clamping/verifying the level index) and `move_player` (checking player coordinates boundaries)?
   - If bounds-checking is added to the C engine, how should the tests be rewritten? Instead of expecting a crash/corruption, they should assert that the engine safely clamps or rejects the invalid coordinates/indices without crash or corruption.
   - Design the exact modifications for the C engine and the test suite to achieve absolute safety.
4. Document your findings and remediation design in `/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/.agents/explorer_remedy_3_gen2/analysis.md`.
5. Send a message to your parent (conversation ID: 1270ca6b-5147-4ec8-a7b8-2387eb40165b) when complete.
