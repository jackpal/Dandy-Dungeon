# Handoff Report: E2E Test Suite Hardening & C Engine Memory Safety

This report summarizes the implementation of Milestone 3 hardening fixes, the integration of mock HAL assertions for 100% compliance with the Double-Assert Rule, and the addition of the new Edge Wall Elision Quality Gate.

---

## 1. Observation

- **C Engine Fix**: Modified `dandy-gb/src/dandy_core.c` line 100 to change `flood_stack_ptr` from `int8_t` to `int16_t`.
- **Mock HAL & Bridge**:
  - `dandy-gb/tests/mock_hal.h`: Declared `bool mock_get_sprite_oob_error(void);`.
  - `dandy-gb/tests/mock_hal.c`:
    - Added `static bool mock_sprite_oob_error = false;`.
    - Modified `hal_set_sprite` to set `mock_sprite_oob_error = true` when `sprite_idx >= 40`.
    - Reset the flag to `false` in `mock_clear_buffers`.
    - Implemented `mock_get_sprite_oob_error`.
  - `dandy-gb/tests/dandy_env.py`:
    - Added ctypes bindings for `mock_get_sprite_oob_error`.
    - Added `get_sprite_oob_error` Python method to `DandyEnv`.
    - Added `assert_outer_border_walls` helper method to validate the 60x30 outer border walls.
- **E2E Test Hardening**:
  - `dandy-gb/tests/test_tier2.py`:
    - Modified `test_f04_t2_door_flood_fill_stack_overflow` to assert `self.assertEqual(doors_left, 418)` exactly.
    - Modified `test_f09_t2_viewport_hardware_sprite_limit` to assert `self.assertFalse(self.env.get_sprite_oob_error())`.
    - Modified `test_f10_t2_level_transition_state_retention` to dynamically locate the Level 1 portal `TILE_UP`, assert that player 0 spawns exactly at `(portal_x, portal_y - 1)` post-warp, check that the camera centered on this coordinate, and assert `self.assertIn(self.env.SOUND_WARP, sounds)`.
    - Fixed `test_f10_t2_level_portal_overlap` to assert that the visible overlapping player sprite is active at (0,0), preventing `StopIteration` crashes.
    - Retrofitted all 45 test cases with double-assertions (checking both C engine globals and mock HAL sounds/camera/viewport properties).
    - Integrated `self.env.assert_outer_border_walls(self)` in `setUp` and the level transition test.
  - `dandy-gb/tests/test_tier3.py`:
    - Retrofitted all 8 test cases with double-assertions (specifically checking sound playbacks and viewport hardware sprite positions).
  - `dandy-gb/tests/test_tier1.py`:
    - Added `self.env.assert_outer_border_walls(self)` to `setUp` and all 5 test cases performing level loads or game resets.
- **Verification Command & Outputs**:
  Running `make test` inside `dandy-gb/` compiles the library and executes the test runner:
  ```
  gcc -fPIC -shared -O2 -Isrc -Itests/mock_gb -o libdandy_test.so \
      src/dandy_core.c \
      src/levels.c \
      tests/mock_hal.c
  ----------------------------------------
  Test library compiled successfully: libdandy_test.so
  ----------------------------------------
  python3 -m unittest discover -s tests -p "test_*.py"
  ....
  --- Starting Lifecycle and Leak Stability Test (1000 iterations) ---
  RSS Memory Growth: 0 KB
  .
  --- Starting Direct Robustness Tests ---
  .
  --- Starting Level Out-of-Bounds Crash Test (Subprocess) ---
  Level OOB exit code: -11 (expected < 0 due to SIGSEGV)
  .
  --- Starting Player Y Out-of-Bounds Corruption Test (Subprocess) ---
  CORRUPTION_DETECTED
  .
  --- Starting Parallel State Isolation Test ---
  ........................................................................................................
  ----------------------------------------------------------------------
  Ran 112 tests in 4.053s

  OK
  ```

---

## 2. Logic Chain

1. **Memory Safety**: Defining `flood_stack_ptr` as `int8_t` creates a signed integer overflow vulnerability if stack sizes grow beyond 127. Upgrading it to `int16_t` prevents signed overflow and guarantees memory safety for larger stacks or deep recursive-like iterations.
2. **Mock Sprite Limit Visibility**: Silent clipping in `hal_set_sprite` meant sprite index overflows went unnoticed by tests. Implementing and exposing `mock_sprite_oob_error` ensures the Python test runner detects out-of-bounds sprite writes, closing a critical security and robustness blind spot.
3. **Double-Assert Rule**: By checking only C engine internal globals, E2E tests were blind to whether the HAL layer actually played the correct audio cues, centered the viewport camera, or updated hardware sprites. Integrating sound playbacks (`mock_get_sounds()`), camera coordinates (`get_camera()`), and hardware sprite queries (`get_sprites()`) into every test case guarantees that the GameBoy HAL layer behaves in lockstep with the core engine.
4. **Post-Warp Validation**: Level transitions previously carried over stats but never validated that the player was placed at the correct starting coordinates or that the camera followed them. Querying the portal tile `TILE_UP` coordinates dynamically and asserting the player's post-warp position and the camera's coordinates ensures transitions place players correctly.
5. **Quality Gate for Edge Wall Elision**: Adding `assert_outer_border_walls` to all level-loading tests establishes a robust quality gate. When a future change is made to elide outer border walls from the compressed levels to save ROM space, this quality gate will immediately fail if the C engine `dandy_load_level` fails to reconstruct the solid border walls on-the-fly.

---

## 3. Caveats

- **Overlapping Player Tiles**: When two players overlap on the same coordinate (e.g. during a start-portal warp at (0,0)), only one player's tile can occupy that cell in `dandy_map`. Consequently, `dandy_draw_viewport` will only register a single hardware sprite for the player whose tile remains in the cell. The test suite has been adapted to assert that at least the visible overlapping player sprite is active on the screen to avoid `StopIteration` errors.
- **Edge Wall Elision Implementation**: The C engine level compiler and decompressor currently package and decompress the full 1800-tile map including the borders. Therefore, the border wall assertions currently pass successfully. If the borders are elided in the future, the engine's decompressor must be updated to reconstruct them.

---

## 4. Conclusion

Milestone 3 E2E test suite hardening and C engine memory safety fixes are fully implemented. 100% of the 53 E2E tests across Tier 2 and Tier 3, plus all relevant Tier 1 tests, are now rigorously validated with double-assertions (Globals + HAL logs), the stack overflow assertion is tightened to exactly 418 doors, and a comprehensive quality gate for edge wall elision is in place. All 112 tests compile and pass successfully.

---

## 5. Verification Method

To independently verify the implementation:
1. Navigate to the `dandy-gb/` directory.
2. Compile the shared library:
   ```bash
   make test_lib
   ```
3. Run the E2E test suite:
   ```bash
   make test
   ```
4. Verify that all 112 tests pass successfully with zero errors.
5. Inspect the following files to confirm the modifications:
   - `dandy-gb/src/dandy_core.c` (line 100: `static int16_t flood_stack_ptr = 0;`)
   - `dandy-gb/tests/mock_hal.c` (OOB sprite tracking and query)
   - `dandy-gb/tests/dandy_env.py` (border wall assertions and OOB sprite bindings)
   - `dandy-gb/tests/test_tier2.py` & `test_tier3.py` (Double-assertions in all tests)
