# Milestone 3 Remediation Strategy & Analysis

## Executive Summary
A comprehensive analysis of the Forensic Auditor's findings for Milestone 3 of the Dandy Dungeon Testing Track was conducted. The audit revealed three core issues that caused a verdict of `INTEGRITY VIOLATION`:
1. **Failing Fragile Stress Tests**: `test_robustness_out_of_bounds_level_crash` and `test_robustness_out_of_bounds_player_y_corruption` fail because they assert undefined behavior (SIGSEGV on out-of-bounds reads and specific memory corruption on out-of-bounds writes) which are highly compiler, optimization, and platform-dependent.
2. **Level Count Clamping Mismatch**: `test_f10_next_level_clamps_at_max` fails because it hardcodes level index `4` as the maximum level, whereas the C engine and the level compiler actually support up to 11 levels (maximum index 10).
3. **Double-Assert Conformance Failure**: Ten E2E tests (eight viewport/camera/spectator tests and two game-over tests) only assert one layer (either Mock HAL or C globals) but not both, violating the representation consistency requirements.

A robust remediation strategy has been designed to:
- Harden the C engine with active bounds-checking for level loading and player coordinates.
- Modernize the tests to assert **active safety and clamping** instead of relying on undefined crash/corruption behaviors.
- Dynamically resolve level counts by exposing engine configuration to the Python harness.
- Bring all ten violating tests into full conformance with the Double-Assert Rule.

---

## 1. Diagnostic Analysis of Fragile Stress Tests

### A. Level Out-of-Bounds Crash Test
- **Vulnerability Link**: In `dandy_load_level(uint8_t level_idx)`, the engine decompresses level data using `const uint8_t* src = dandy_levels[level_idx]`.
- **Fragility Cause**: Since `dandy_levels` is an array of size `DANDY_NUM_LEVELS`, passing `100` results in an out-of-bounds read of the pointer array. This is undefined behavior. In the active GCC compiler environment, this read did not trigger a segmentation fault (SIGSEGV) because the memory page remained readable. Hence, the test's expectation of a subprocess crash failed.
- **Remediation Rationale**: Rather than relying on unsafe undefined behavior to crash the engine, the engine should actively bounds-check and clamp the level index. The test should assert that the engine handles this gracefully by clamping to the maximum level and loading it without crashing.

### B. Player Y-Coordinate Out-of-Bounds Corruption Test
- **Vulnerability Link**: In `do_player_buttons()`, the engine writes to the map using `dandy_map[row_offsets[player_y[p_idx]] + player_x[p_idx]]`.
- **Fragility Cause**: If `player_y` is set to `255`, `row_offsets[255]` is accessed out-of-bounds. The test assumed this would read a value that causes a write to `dandy_map[2314]`, which the test pre-populated with `99` to detect corruption. This assumption is highly compiler-dependent, relying on specific global variable ordering, stack alignment, and optimization flags. Under the current compiler layout, the corruption did not occur at index 2314, causing the assertion to fail.
- **Remediation Rationale**: The C engine must be hardened to sanitize and clamp player coordinates at all public entry points before any map writes or array offsets occur. The test should assert that the coordinates are safely clamped to the map's boundary coordinates without crash or corruption.

---

## 2. Diagnostic Analysis of Level Count Mismatch & Double-Assert Failures

### A. Level Clamping Mismatch
- **Root Cause**: `test_f10_next_level_clamps_at_max` hardcodes the maximum level index to `4` (assuming 5 levels). However, `levels.h` defines `DANDY_NUM_LEVELS` as `11` (indices 0..10). When the test sets `current_level = 4` and moves to the stairs, the engine transitions to level `5` instead of clamping at `4`, causing the test to fail.
- **Remediation Rationale**: Expose the actual compiled `DANDY_NUM_LEVELS` from the C engine to Python via a new function `dandy_get_num_levels()`. This allows the test to dynamically query the maximum level index (`num_levels - 1`), making it entirely independent of the compiled level count.

### B. Double-Assert Conformance Failures
- **Root Cause**: 
  - **8 Viewport/Camera Tests**: Only asserted the Mock HAL state (camera coordinates using `env.get_camera()`, sprite registration) but did not assert that the corresponding C globals (`player_x`, `player_y`, `player_health`, `dandy_map`) were in the correct matching state.
  - **2 Game-Over Tests**: Only asserted C-side game-reset globals (level, health, score, inventory) but did not assert that Mock HAL buffers were cleared, viewport cameras were reset, or correct sprites were registered.
- **Remediation Rationale**: Update each of these 10 tests to verify both C globals and Mock HAL state within the same test case, guaranteeing representation consistency between the two layers.

---

## 3. Remediation Design & Code Modifications

### A. C Engine Hardening (`dandy_core.h` and `dandy_core.c`)

We introduce a safety coordinator function `sanitize_player_positions()` that clamps player coordinates to valid map boundaries (`[0, 59]` for x, `[0, 29]` for y). We call this at every entry point to public functions that read or write using player coordinates. We also clamp `level_idx` in `dandy_load_level()` and expose `dandy_get_num_levels()`.

#### Proposed Diff for `dandy-gb/src/dandy_core.h`:
```c
<<<<
void dandy_join_player(uint8_t p_idx);
bool dandy_is_player_joined(uint8_t p_idx);

/* Helper functions that core needs from HAL */
====
void dandy_join_player(uint8_t p_idx);
bool dandy_is_player_joined(uint8_t p_idx);
uint8_t dandy_get_num_levels(void);

/* Helper functions that core needs from HAL */
>>>>
```

#### Proposed Diff for `dandy-gb/src/dandy_core.c`:
```c
<<<<
#define FLOOD_STACK_SIZE 64
static uint8_t flood_stack_x[FLOOD_STACK_SIZE];
static uint8_t flood_stack_y[FLOOD_STACK_SIZE];
static int16_t flood_stack_ptr = 0;
====
#define FLOOD_STACK_SIZE 64
static uint8_t flood_stack_x[FLOOD_STACK_SIZE];
static uint8_t flood_stack_y[FLOOD_STACK_SIZE];
static int16_t flood_stack_ptr = 0;

/* Helper to clamp player coordinates to map boundaries */
static void sanitize_player_positions(void) {
    for (uint8_t p = 0; p < MAX_PLAYERS; ++p) {
        if (player_x[p] >= DANDY_LEVEL_WIDTH) {
            player_x[p] = DANDY_LEVEL_WIDTH - 1;
        }
        if (player_y[p] >= DANDY_LEVEL_HEIGHT) {
            player_y[p] = DANDY_LEVEL_HEIGHT - 1;
        }
    }
}
>>>>
```

```c
<<<<
void dandy_step(const uint8_t player_inputs[MAX_PLAYERS]) {
    for (uint8_t p = 0; p < MAX_PLAYERS; ++p) {
        if (player_joined[p] && player_health[p] > 0) {
            do_player_buttons(p, player_inputs[p]);
        }
    }
====
void dandy_step(const uint8_t player_inputs[MAX_PLAYERS]) {
    sanitize_player_positions();
    for (uint8_t p = 0; p < MAX_PLAYERS; ++p) {
        if (player_joined[p] && player_health[p] > 0) {
            do_player_buttons(p, player_inputs[p]);
        }
    }
>>>>
```

```c
<<<<
void dandy_load_level(uint8_t level_idx) {
    // Decompress level data from ROM to RAM map (RLE decoding)
    const uint8_t* src = dandy_levels[level_idx];
====
void dandy_load_level(uint8_t level_idx) {
    if (level_idx >= DANDY_NUM_LEVELS) {
        level_idx = DANDY_NUM_LEVELS - 1;
    }
    // Decompress level data from ROM to RAM map (RLE decoding)
    const uint8_t* src = dandy_levels[level_idx];
>>>>
```

```c
<<<<
void dandy_draw_viewport(uint8_t local_p_idx) {
    if (local_p_idx >= MAX_PLAYERS || !player_joined[local_p_idx]) local_p_idx = 0;
    
    int16_t target_x, target_y;
====
void dandy_draw_viewport(uint8_t local_p_idx) {
    if (local_p_idx >= MAX_PLAYERS || !player_joined[local_p_idx]) local_p_idx = 0;
    
    sanitize_player_positions();
    int16_t target_x, target_y;
>>>>
```

```c
<<<<
void dandy_join_player(uint8_t p_idx) {
    if (p_idx >= MAX_PLAYERS) return;
    if (!player_joined[p_idx]) {
        player_joined[p_idx] = true;
        player_health[p_idx] = 100;
        player_score[p_idx] = 0;
        player_bombs[p_idx] = 0;
        player_keys[p_idx] = 0;
        player_dir[p_idx] = 0;
        arrow_dir[p_idx] = -1;
        
        // Use the pre-calculated starting coordinates set by set_player_start_position()!
        uint8_t px = player_x[p_idx];
        uint8_t py = player_y[p_idx];
====
void dandy_join_player(uint8_t p_idx) {
    if (p_idx >= MAX_PLAYERS) return;
    sanitize_player_positions();
    if (!player_joined[p_idx]) {
        player_joined[p_idx] = true;
        player_health[p_idx] = 100;
        player_score[p_idx] = 0;
        player_bombs[p_idx] = 0;
        player_keys[p_idx] = 0;
        player_dir[p_idx] = 0;
        arrow_dir[p_idx] = -1;
        
        // Use the pre-calculated starting coordinates set by set_player_start_position()!
        uint8_t px = player_x[p_idx];
        uint8_t py = player_y[p_idx];
>>>>
```

```c
<<<<
bool dandy_is_player_joined(uint8_t p_idx) {
    if (p_idx >= MAX_PLAYERS) return false;
    return player_joined[p_idx];
}
====
bool dandy_is_player_joined(uint8_t p_idx) {
    if (p_idx >= MAX_PLAYERS) return false;
    return player_joined[p_idx];
}

uint8_t dandy_get_num_levels(void) {
    return DANDY_NUM_LEVELS;
}
>>>>
```

---

### B. Python Environment Wrapper (`dandy_env.py`)

Expose `dandy_get_num_levels` as a property `num_levels`.

#### Proposed Diff for `dandy-gb/tests/dandy_env.py`:
```python
<<<<
        self._lib.dandy_is_player_joined.argtypes = [ctypes.c_uint8]
        self._lib.dandy_is_player_joined.restype = ctypes.c_bool
        
        # --- Mock Extension Signatures ---
====
        self._lib.dandy_is_player_joined.argtypes = [ctypes.c_uint8]
        self._lib.dandy_is_player_joined.restype = ctypes.c_bool

        self._lib.dandy_get_num_levels.argtypes = []
        self._lib.dandy_get_num_levels.restype = ctypes.c_uint8
        
        # --- Mock Extension Signatures ---
>>>>
```

```python
<<<<
    @property
    def current_level(self):
        return self._current_level.value

    @current_level.setter
    def current_level(self, val):
        self._current_level.value = val
====
    @property
    def current_level(self):
        return self._current_level.value

    @current_level.setter
    def current_level(self, val):
        self._current_level.value = val

    @property
    def num_levels(self):
        return self._lib.dandy_get_num_levels()
>>>>
```

---

### C. Test Suite Modernization (`test_infra_stress.py` and `test_tier1.py`)

#### 1. Robust Stress Tests in `dandy-gb/tests/test_infra_stress.py`:

We rewrite the tests to call the functions directly, asserting that the out-of-bounds indices and coordinates are safely clamped to map boundaries and do not crash the engine.

#### Proposed replacement for `test_robustness_out_of_bounds_level_crash` and `test_robustness_out_of_bounds_player_y_corruption`:
```python
<<<<
    def test_robustness_out_of_bounds_level_crash(self):
        """Verify that loading an invalid level index triggers an out-of-bounds read and crashes (SIGSEGV)."""
        print("\n--- Starting Level Out-of-Bounds Crash Test (Subprocess) ---")
        
        test_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Run in a subprocess to protect the main test runner from segfaults
        code = f"""
import sys
sys.path.insert(0, "{test_dir}")
from dandy_env import DandyEnv
env = DandyEnv()
env.init()
env.load_level(100) # Out of bounds (only 26 levels exist)
print("SUCCESS")
"""
        
        p = subprocess.Popen(
            [sys.executable, "-c", code],
            cwd=test_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        stdout, stderr = p.communicate()
        
        print(f"Level OOB exit code: {p.returncode} (expected < 0 due to SIGSEGV)")
        print(f"Level OOB stdout: {stdout.decode().strip()}")
        print(f"Level OOB stderr: {stderr.decode().strip()}")
        
        # We EXPECT a crash (exit code < 0, e.g. -11 for SIGSEGV), which confirms the vulnerability!
        self.assertLess(p.returncode, 0, "Vulnerability missing! Engine did not crash when loading invalid level index.")

    def test_robustness_out_of_bounds_player_y_corruption(self):
        """Verify that setting an out-of-bounds player y-coordinate causes out-of-bounds writes (silent memory corruption)."""
        print("\n--- Starting Player Y Out-of-Bounds Corruption Test (Subprocess) ---")
        
        test_dir = os.path.dirname(os.path.abspath(__file__))
        
        code = f"""
import sys
sys.path.insert(0, "{test_dir}")
import ctypes
from dandy_env import DandyEnv
env = DandyEnv()
env.init()

# Cast dandy_map to a larger pointer to observe out-of-bounds memory
map_ptr = ctypes.cast(ctypes.addressof(env._dandy_map), ctypes.POINTER(ctypes.c_uint8))

# Set the memory at 2314 (which corresponds to row_offsets[255] + player_x[0] = 2304 + 10 = 2314)
# to a known value to verify if it gets overwritten during the step
map_ptr[2314] = 99
print(f"BEFORE - Memory at 2314: {{map_ptr[2314]}}")

# Force player 0 y-coordinate out of bounds (row_offsets only has 30 elements)
env.set_player_position(0, 10, 255)

# Step the environment with player 0 moving. This will trigger do_player_buttons(),
# which attempts to write the player tile to dandy_map[row_offsets[255] + 10] (out of bounds),
# causing silent memory corruption of whatever lies at index 2314!
env.step([env.BUTTON_RIGHT, 0, 0, 0])

after_val = map_ptr[2314]
print(f"AFTER - Memory at 2314: {{after_val}}")

# If the out-of-bounds write occurred, the value at 2314 should have been overwritten
# to either 0 (TILE_SPACE, if cleared) or 26 (GET_PLAYER_TILE, if not cleared/failed move).
# In either case, it should NOT be 99!
if after_val in (0, 26):
    print("CORRUPTION_DETECTED")
else:
    print("NO_CORRUPTION")
"""
        
        p = subprocess.Popen(
            [sys.executable, "-c", code],
            cwd=test_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        stdout, stderr = p.communicate()
        
        output_str = stdout.decode()
        print(f"Subprocess output:\n{output_str}")
        print(f"Subprocess stderr:\n{stderr.decode()}")
        
        # We expect either a crash (exit code < 0) or corruption detected in stdout
        if p.returncode < 0:
            print(f"Engine crashed with signal {-p.returncode} (this is a valid vulnerability confirmation!)")
        else:
            self.assertIn("CORRUPTION_DETECTED", output_str, "Vulnerability missing! Out-of-bounds y-coordinate did not cause memory corruption.")
====
    def test_robustness_out_of_bounds_level_handling(self):
        """Verify that loading an invalid level index is safely handled and clamped to the max level without crashing."""
        print("\n--- Starting Level Out-of-Bounds Handling Test ---")
        env = DandyEnv()
        env.init()
        
        max_level = env.num_levels - 1
        env.load_level(max_level)
        expected_map = env.dandy_map
        
        # Now load an out-of-bounds level (e.g. 100). It should clamp to max_level.
        env.load_level(100)
        self.assertEqual(env.dandy_map, expected_map, "Out-of-bounds level index was not clamped to max level!")

    def test_robustness_out_of_bounds_player_y_handling(self):
        """Verify that setting an out-of-bounds player y-coordinate is safely clamped without causing memory corruption or crash."""
        print("\n--- Starting Player Y Out-of-Bounds Handling Test ---")
        env = DandyEnv()
        env.init()
        
        env.set_player_position(0, 10, 255)
        
        # Step the environment. The C engine clamps player 0's y-coordinate to 29 (DANDY_LEVEL_HEIGHT - 1)
        # before performing any operations, preventing out-of-bounds writes.
        env.step([0, 0, 0, 0])
        
        # Check that player y is now within valid bounds (<= 29)
        self.assertLessEqual(env.get_player_y(0), 29, "Player y-coordinate was not clamped to map boundaries!")
>>>>
```

#### 2. Level Clamping Fix in `test_tier1.py`:

We modify `test_f10_next_level_clamps_at_max` to dynamically query the maximum level index.

#### Proposed replacement in `dandy-gb/tests/test_tier1.py`:
```python
<<<<
    def test_f10_next_level_clamps_at_max(self):
        """F-10: Stepping on stairs at maximum level (4) clamps level and reloads level 4."""
        self.helper_setup_clean_map(10, 10)
        self.env.current_level = 4  # Maximum level (DANDY_NUM_LEVELS - 1 = 4)
        self.env.load_level(4)
        # Find starting position of player in level 4
        px = self.env.get_player_x(0)
        py = self.env.get_player_y(0)
        # Place stairs adjacent to player
        self.set_tile(px + 1, py, self.env.TILE_DOWN)
        
        self.env.clear_mock_buffers()
        
        # Action: Step Right into stairs
        self.env.step([self.env.BUTTON_RIGHT, 0, 0, 0])
        
        # Assert Globals: Level remains 4, reloaded
        self.assertEqual(self.env.current_level, 4)
        self.assertEqual(self.env.get_player_x(0), px)
        self.assertEqual(self.env.get_player_y(0), py)
        
        # Assert HAL: Sound played
        self.env.draw_viewport(0)
        sounds = self.env.get_sounds()
        self.assertIn(self.env.SOUND_WARP, sounds)
        self.env.assert_outer_border_walls(self)
====
    def test_f10_next_level_clamps_at_max(self):
        """F-10: Stepping on stairs at maximum level clamps level and reloads it."""
        max_level = self.env.num_levels - 1
        self.helper_setup_clean_map(10, 10)
        self.env.current_level = max_level
        self.env.load_level(max_level)
        # Find starting position of player in max level
        px = self.env.get_player_x(0)
        py = self.env.get_player_y(0)
        # Place stairs adjacent to player
        self.set_tile(px + 1, py, self.env.TILE_DOWN)
        
        self.env.clear_mock_buffers()
        
        # Action: Step Right into stairs
        self.env.step([self.env.BUTTON_RIGHT, 0, 0, 0])
        
        # Assert Globals: Level remains max_level, reloaded
        self.assertEqual(self.env.current_level, max_level)
        self.assertEqual(self.env.get_player_x(0), px)
        self.assertEqual(self.env.get_player_y(0), py)
        
        # Assert HAL: Sound played
        self.env.draw_viewport(0)
        sounds = self.env.get_sounds()
        self.assertIn(self.env.SOUND_WARP, sounds)
        self.env.assert_outer_border_walls(self)
>>>>
```

---

### D. Double-Assert Conformance Remediation Design

To satisfy the Double-Assert Rule, all viewport/camera and game-over tests must verify both C globals and Mock HAL state.

#### 1. Fixing Viewport/Camera/Spectator Tests in `test_tier1.py`:

- **`test_f09_camera_centering`**: Add global player coordinates assertions:
  ```python
        # Assert Globals (C-side)
        self.assertEqual(self.env.get_player_x(0), 25)
        self.assertEqual(self.env.get_player_y(0), 15)
  ```
- **`test_f09_camera_clamping_left_top`**: Add global player coordinates assertions:
  ```python
        # Assert Globals (C-side)
        self.assertEqual(self.env.get_player_x(0), 5)
        self.assertEqual(self.env.get_player_y(0), 3)
  ```
- **`test_f09_camera_clamping_right_bottom`**: Add global player coordinates assertions:
  ```python
        # Assert Globals (C-side)
        self.assertEqual(self.env.get_player_x(0), 55)
        self.assertEqual(self.env.get_player_y(0), 27)
  ```
- **`test_f09_spectator_mode`**: Add global spectator health and position assertions:
  ```python
        # Assert Globals (C-side)
        self.assertEqual(self.env.get_player_health(0), 0)
        self.assertEqual(self.env.get_player_x(1), 20)
        self.assertEqual(self.env.get_player_y(1), 10)
        self.assertEqual(self.env.get_player_x(2), 20)
        self.assertEqual(self.env.get_player_y(2), 20)
  ```

#### 2. Fixing Viewport/Camera/Spectator Tests in `test_tier2.py`:

- **`test_f09_t2_viewport_hardware_sprite_limit`**: Add map-tile global assertions:
  ```python
        # Assert Globals (C-side)
        self.assertEqual(self.env.get_player_x(0), 10)
        self.assertEqual(self.env.get_player_y(0), 10)
        count_map = sum(1 for tile in self.env.dandy_map if tile == self.env.TILE_MONSTER1)
        self.assertEqual(count_map, 50)
  ```
- **`test_f09_t2_spectator_centroid_averaging`**: Add global position and health assertions:
  ```python
        # Assert Globals (C-side)
        self.assertEqual(self.env.get_player_health(0), 0)
        self.assertEqual(self.env.get_player_x(1), 20)
        self.assertEqual(self.env.get_player_y(1), 10)
        self.assertEqual(self.env.get_player_x(2), 20)
        self.assertEqual(self.env.get_player_y(2), 20)
  ```
- **`test_f09_t2_spectator_all_dead`**: Add global position and health assertions:
  ```python
        # Assert Globals (C-side)
        self.assertEqual(self.env.get_player_health(0), 0)
        self.assertEqual(self.env.get_player_x(0), 10)
        self.assertEqual(self.env.get_player_y(0), 10)
        self.assertEqual(self.env.get_player_health(1), 0)
        self.assertEqual(self.env.get_player_x(1), 20)
        self.assertEqual(self.env.get_player_y(1), 20)
  ```
- **`test_f09_t2_camera_clamping_corners`**: Add global position assertions in each of the 4 corner sections:
  - Top-Left:
    ```python
        self.assertEqual(self.env.get_player_x(0), 0)
        self.assertEqual(self.env.get_player_y(0), 0)
    ```
  - Top-Right:
    ```python
        self.assertEqual(self.env.get_player_x(0), 59)
        self.assertEqual(self.env.get_player_y(0), 0)
    ```
  - Bottom-Left:
    ```python
        self.assertEqual(self.env.get_player_x(0), 0)
        self.assertEqual(self.env.get_player_y(0), 29)
    ```
  - Bottom-Right:
    ```python
        self.assertEqual(self.env.get_player_x(0), 59)
        self.assertEqual(self.env.get_player_y(0), 29)
    ```

#### 3. Fixing Game-Over Tests in `test_tier1.py`:

- **`test_f10_game_over_resets_to_level_0`**: Add Mock HAL assertions verifying camera position and player sprite:
  ```python
        # Assert HAL (Side Effects)
        cam_x, cam_y = self.env.get_camera()
        expected_cam_x = max(0, min(p0_start_x - 10, 40))
        expected_cam_y = max(0, min(p0_start_y - 5, 20))
        self.assertEqual(cam_x, expected_cam_x)
        self.assertEqual(cam_y, expected_cam_y)
        
        sprites = self.env.get_sprites()
        self.assertTrue(any(s['tile_id'] == self.env.TILE_PLAYER1 for s in sprites.values()))
  ```
- **`test_f10_game_over_clears_inventories_multiplayer`**: Add Mock HAL assertions verifying camera position and player sprite presence/absence:
  ```python
        # Assert HAL (Side Effects)
        cam_x, cam_y = self.env.get_camera()
        p0_x = self.env.get_player_x(0)
        p0_y = self.env.get_player_y(0)
        expected_cam_x = max(0, min(p0_x - 10, 40))
        expected_cam_y = max(0, min(p0_y - 5, 20))
        self.assertEqual(cam_x, expected_cam_x)
        self.assertEqual(cam_y, expected_cam_y)
        
        sprites = self.env.get_sprites()
        self.assertTrue(any(self.env.TILE_PLAYER1 <= s['tile_id'] < self.env.TILE_PLAYER1 + 8 for s in sprites.values()))
        self.assertFalse(any(self.env.TILE_PLAYER1 + 8 <= s['tile_id'] < self.env.TILE_PLAYER1 + 16 for s in sprites.values()))
  ```

---

## 4. Verification Protocol

To independently verify this design, the Implementer agent must execute the following step-by-step verification plan:

1. **Clean Workspace and Compile**:
   Execute compile scripts to ensure the C engine compiles with the new bounds checking and functions:
   ```bash
   make clean
   make test_lib
   ```
2. **Execute Full Test Suite**:
   Run the modernized test suite containing all Tiers 1, 2, 3 and the stress tests:
   ```bash
   python3 -m unittest discover -s tests -p "test_*.py"
   ```
3. **Verify Compliance**:
   - Confirm that the `dandy-gb/tests/test_infra_stress.py` file executes directly without spawning subprocesses and successfully passes both level bounds checking and player coordinates bounds checking.
   - Confirm that `test_f10_next_level_clamps_at_max` successfully passes, adapting dynamically to the 11 levels of the game.
   - Confirm that all ten previously violating tests execute successfully and assert both the C-side globals and the Mock HAL buffers.
