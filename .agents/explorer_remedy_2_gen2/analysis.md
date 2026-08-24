# Dandy Dungeon Milestone 3 Remediation Strategy & Analysis

This report presents a comprehensive analysis of the Milestone 3 test suite failures and integrity violations, along with a robust, production-grade remediation strategy designed to resolve them permanently.

---

## 1. Summary of Findings

1. **Level Clamping Mismatch (`test_f10_next_level_clamps_at_max`)**:
   - **Root Cause**: The C engine constant `DANDY_NUM_LEVELS` is dynamically defined during compilation by `convert_levels.py` based on how many levels are extracted. In the failing run, 6 levels were compiled, resulting in `DANDY_NUM_LEVELS` being 6 (indices 0..5). However, the test `test_f10_next_level_clamps_at_max` had a hardcoded expectation of 5 levels (maximum index 4), setting `self.env.current_level = 4` and expecting it to clamp. Because the engine allowed advancing up to index 5, the clamp did not trigger at 4, and the level incremented to 5, failing the assertion `5 != 4`.
   - **Remediation**: Expose a new C global variable `const uint8_t dandy_num_levels = DANDY_NUM_LEVELS;` in the C engine (`dandy_core.c` / `dandy_core.h`). Bind this variable to the Python test harness `DandyEnv` as a property `num_levels`. Update the test `test_f10_next_level_clamps_at_max` to dynamically query `self.env.num_levels - 1` as the maximum level index, ensuring the test is completely decoupled from compilation-time level count changes.

2. **Double-Assert Rule Violations**:
   - **Root Cause**: Out of 103 E2E tests, 10 tests violated the Double-Assert Rule. 8 viewport/camera/spectator tests only asserted Mock HAL state (camera coordinates or active sprite counts) but never verified C-side player coordinates or health. 2 game-over tests only asserted C-side globals (resetting to level 0, health, score) but never verified Mock HAL side-effects (e.g., sound triggers, camera resets, viewport drawing counts).
   - **Remediation**: Expand all 10 tests to perform assertions on both layers:
     - For the 8 camera/spectator tests, add C-side assertions to verify player positions and health status.
     - For the 2 game-over tests, add HAL-side assertions to verify the viewport camera centering, the logged drawing counts (exactly 200 tiles for a full redraw), and sound triggers.

3. **Fragile Robustness Tests (`test_robustness_out_of_bounds_level_crash` and `test_robustness_out_of_bounds_player_y_corruption`)**:
   - **Root Cause**: These tests asserted *undefined C behavior* (expecting a crash on out-of-bounds array reads and expecting a specific memory corruption address beyond a global array). Undefined behavior is compiler- and platform-dependent; under the current compiler's optimization and memory layout settings, the crash did not occur and the specific memory location was not corrupted, resulting in test failures.
   - **Remediation**: Implement strict, defensive input bounds checking directly in the C engine:
     - In `dandy_load_level`, clamp the level index: `if (level_idx >= DANDY_NUM_LEVELS) { level_idx = DANDY_NUM_LEVELS - 1; }`
     - In `dandy_step`, clamp player coordinates before processing: `if (player_x[p] >= DANDY_LEVEL_WIDTH) player_x[p] = DANDY_LEVEL_WIDTH - 1;` and `if (player_y[p] >= DANDY_LEVEL_HEIGHT) player_y[p] = DANDY_LEVEL_HEIGHT - 1;`
     - Update the tests to assert *safe, defined behavior* (that the process does NOT crash and that NO memory corruption occurs), converting a fragile undefined-behavior test into a robust, ironclad memory safety verification.

---

## 2. Detailed Remediation Design

### 2.1 C Engine Modifications
We introduce proper bounds checking to the core logic in `dandy-gb/src/dandy_core.c` and expose the compilation-time level count:

1. **Expose Level Count Symbol**:
   - In `dandy_core.h`:
     ```c
     extern const uint8_t dandy_num_levels;
     ```
   - In `dandy_core.c`:
     ```c
     const uint8_t dandy_num_levels = DANDY_NUM_LEVELS;
     ```

2. **Level Index Bounds Check**:
   - In `dandy_load_level`:
     ```c
     void dandy_load_level(uint8_t level_idx) {
         if (level_idx >= DANDY_NUM_LEVELS) {
             level_idx = DANDY_NUM_LEVELS - 1;
         }
         // ... decompress level ...
     ```

3. **Player Position Bounds Check**:
   - In `dandy_step` (before processing inputs):
     ```c
     void dandy_step(const uint8_t player_inputs[MAX_PLAYERS]) {
         for (uint8_t p = 0; p < MAX_PLAYERS; ++p) {
             if (player_joined[p]) {
                 if (player_x[p] >= DANDY_LEVEL_WIDTH) player_x[p] = DANDY_LEVEL_WIDTH - 1;
                 if (player_y[p] >= DANDY_LEVEL_HEIGHT) player_y[p] = DANDY_LEVEL_HEIGHT - 1;
             }
         }
         // ... process step ...
     ```

### 2.2 Python Test Harness (`dandy_env.py`)
Bind the new global symbol `dandy_num_levels` and expose it as a property:
```python
# In DandyEnv._setup_bindings()
self._dandy_num_levels = ctypes.c_uint8.in_dll(self._lib, "dandy_num_levels")

# In DandyEnv properties
@property
def num_levels(self):
    return self._dandy_num_levels.value
```

### 2.3 Double-Assert & Clamping Test Updates (`test_tier1.py` & `test_tier2.py`)
1. **Dynamic Level Clamping Test**:
   ```python
   def test_f10_next_level_clamps_at_max(self):
       """F-10: Stepping on stairs at maximum level clamps level and reloads maximum level."""
       self.helper_setup_clean_map(10, 10)
       max_level = self.env.num_levels - 1
       self.env.current_level = max_level
       self.env.load_level(max_level)
       # ...
       self.env.step([self.env.BUTTON_RIGHT, 0, 0, 0])
       self.assertEqual(self.env.current_level, max_level)
   ```

2. **Double-Assert Camera & Spectator Tests**:
   For all camera and spectator tests (e.g. `test_f09_camera_centering`), we assert the C globals (e.g., player position/health) alongside the HAL-side camera coordinates.
   Example:
   ```python
   # Assert C Globals (Double-Assert)
   self.assertEqual(self.env.get_player_x(0), 25)
   self.assertEqual(self.env.get_player_y(0), 15)
   # Assert HAL
   cam_x, cam_y = self.env.get_camera()
   self.assertEqual(cam_x, 15)
   self.assertEqual(cam_y, 10)
   ```

3. **Double-Assert Game-Over Tests**:
   For the game-over tests, we assert the HAL-side drawing updates and camera resets alongside the C globals.
   Example:
   ```python
   # Assert Globals: level 0, health 100, score 0
   self.assertEqual(self.env.current_level, 0)
   # Assert HAL: Camera reset & drawn tiles (exactly 200 tiles logged for viewport)
   self.assertEqual(self.env.get_draw_count(), 200)
   cam_x, cam_y = self.env.get_camera()
   self.assertEqual(cam_x, expected_cam_x)
   ```

### 2.4 Robustness Test Updates (`test_infra_stress.py`)
Convert fragile undefined-behavior checks into defensive bounds-checking verifications:
1. **Level OOB**:
   Assert that loading an invalid level index (e.g., 100) is handled safely (exit code 0) and does not crash.
2. **Player Y OOB**:
   Assert that setting player y to 255 does not corrupt the map memory (index 2314 remains 99) because the C engine successfully clamps the y-coordinate to a valid value before drawing.

---

## 3. Verification Method

To verify the remedy strategy once implemented:
1. Recompile the test library:
   ```bash
   make test_lib
   ```
2. Run the test suite and verify all 112 tests pass cleanly:
   ```bash
   python3 -m unittest discover -s tests -p "test_*.py"
   ```
3. Verify that all 10 formerly violating tests now contain assertions checking BOTH layers.

A complete machine-applicable unified patch containing all of these changes is located in `/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/.agents/explorer_remedy_2_gen2/remedy.patch`.
