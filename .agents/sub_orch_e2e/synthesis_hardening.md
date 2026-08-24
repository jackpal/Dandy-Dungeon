# Synthesized Hardening Plan: C Engine & E2E Test Suite

This document synthesizes the critical findings, vulnerabilities, and weak assertions discovered by **Reviewer 1**, **Challenger 1**, and **Challenger 2** during their independent verification of the Milestone 3 E2E test suite. 

You must implement these exact fixes to resolve all engine vulnerabilities, close E2E test blind spots, and strictly satisfy the **Double-Assert Rule**.

---

## 1. C Engine Fixes

### A. Fix Signed Flood-Fill Stack Pointer Overflow (`dandy_core.c`)
- **Vulnerability**: `flood_stack_ptr` is defined as a signed 8-bit integer (`int8_t`). If the stack size `FLOOD_STACK_SIZE` is increased past 127, the pointer overflows to negative values, causing out-of-bounds negative array index writes (memory corruption) and premature loop termination.
- **Fix**: Open `dandy-gb/src/dandy_core.c` and modify the declaration of `flood_stack_ptr` around line 101:
  ```c
  // Change from int8_t to int16_t
  static int16_t flood_stack_ptr = 0;
  ```

---

## 2. Mock HAL & Python Bridge Enhancements

### A. Implement Sprite Out-of-Bounds Error Flag (`mock_hal.c` & `mock_hal.h`)
- **Vulnerability**: `hal_set_sprite` silently discards writes where `sprite_idx >= 40`. The Python test runner is blind to OOB sprite writes, allowing sprite limit guard bypasses to pass undetected.
- **Fix in `dandy-gb/tests/mock_hal.h`**:
  Add declaration:
  ```c
  bool mock_get_sprite_oob_error(void);
  ```
- **Fix in `dandy-gb/tests/mock_hal.c`**:
  1. Add a static global error flag:
     ```c
     static bool mock_sprite_oob_error = false;
     ```
  2. Modify `hal_set_sprite`:
     ```c
     void hal_set_sprite(uint8_t sprite_idx, uint8_t x, uint8_t y, uint8_t tile_id, uint8_t flags) {
         if (sprite_idx < 40) {
             mock_sprites[sprite_idx].x = x;
             mock_sprites[sprite_idx].y = y;
             mock_sprites[sprite_idx].tile_id = tile_id;
             mock_sprites[sprite_idx].flags = flags;
             mock_sprites[sprite_idx].active = true;
         } else {
             mock_sprite_oob_error = true;
         }
     }
     ```
  3. Reset the flag in `mock_clear_buffers`:
     ```c
     mock_sprite_oob_error = false;
     ```
  4. Implement the query function:
     ```c
     bool mock_get_sprite_oob_error(void) {
         return mock_sprite_oob_error;
     }
     ```

### B. Expose Sprite OOB Error in Python Wrapper (`dandy_env.py`)
- **Fix**: Open `dandy-gb/tests/dandy_env.py` and map `mock_get_sprite_oob_error`:
  1. Add the `ctypes` function binding in `DandyEnv.__init__`:
     ```python
     self._lib.mock_get_sprite_oob_error.argtypes = []
     self._lib.mock_get_sprite_oob_error.restype = ctypes.c_bool
     ```
  2. Add a Python wrapper method in `DandyEnv` class:
     ```python
     def get_sprite_oob_error(self):
         return self._lib.mock_get_sprite_oob_error()
     ```

---

## 3. E2E Test Suite Hardening

### A. Tighten Flood-Fill Stack Overflow Test Assertion (`test_tier2.py`)
- **Weakness**: `test_f04_t2_door_flood_fill_stack_overflow` uses a weak assertion `assertTrue(doors_left > 0)`.
- **Harden**: Modify the assertion to check for the **exact expected count of remaining doors** under a stack size of 64.
  ```python
  # Change:
  # self.assertTrue(doors_left > 0)
  # To:
  self.assertEqual(doors_left, 418)
  ```

### B. Assert Sprite OOB Error Flag in Sprite Cap Test (`test_tier2.py`)
- **Fix**: In `test_f09_t2_viewport_hardware_sprite_limit`, add an assertion to verify that no out-of-bounds sprite writes occurred:
  ```python
  self.assertFalse(self.env.get_sprite_oob_error(), "Out-of-bounds sprite index registered!")
  ```

### C. Assert Player Post-Warp Coordinates in Level Transitions (`test_tier2.py`)
- **Weakness**: Level transition tests check `current_level` and player stats, but never check coordinates.
- **Harden**: In `test_f10_t2_level_transition_state_retention`, assert that the player is placed at the exact starting portal coordinates of Level 1.
  ```python
  # After stepping into stairs and transition completes:
  # Assert that the player is positioned at the portal tile (TILE_UP) on Level 1
  # Portal is at (2, 2) on Level 1 map (or whatever the portal position is in levels.c for Level 1)
  # Verify player coordinates are correct:
  self.assertEqual(self.env.get_player_x(0), expected_portal_x)
  self.assertEqual(self.env.get_player_y(0), expected_portal_y)
  ```
  *(Note: Query the portal coordinate dynamically from Level 1's decompressed map in the test, or use the expected starting coordinate).*

---

## 4. Enforce the Double-Assert Rule (37 Test Cases)

Retrofit all 37 identified weak test cases in `dandy-gb/tests/test_tier2.py` and `dandy-gb/tests/test_tier3.py` to verify **both C engine globals and mock HAL logs**.

### Mandatory HAL Assertions to Add:
1. **Movement and Slide Blocks** (F-01, F-02):
   - Assert that no sounds were played:
     ```python
     self.assertEqual(self.env.mock_get_sound_count(), 0)
     ```
   - Assert that the camera coordinates did not change (or are clamped correctly).
2. **Item Collections** (F-03):
   - Assert that the correct sound was played:
     - Food: `SOUND_FOOD` (health increases)
     - Money/Key/Bomb: `SOUND_KEY` (score, keys, bombs increase)
   - Assert that the collected item tile was redrawn as `TILE_SPACE` or the player's sprite.
3. **Door Unlocking** (F-04):
   - Successful Unlock: Assert `SOUND_KEY` was played exactly once and the unlocked door tiles were redrawn as `TILE_SPACE`.
   - Blocked (no keys): Assert no sound was played and the door tile remains `TILE_DOOR`.
4. **Projectiles & Monsters** (F-05, F-07):
   - Shoot: Assert `SOUND_SHOOT` was played and camera/active sprites are tracked.
   - Hit: Assert `SOUND_HIT` was played.
   - Monster damage: Assert player health decreased and `SOUND_HIT` (or `SOUND_DIE` if killed) was played.
5. **Generators** (F-08):
   - Spawning: Assert that when a monster spawns, it is drawn on the viewport and registered as an active sprite.
6. **Level Transitions** (F-10):
   - Warp: Assert `SOUND_WARP` is played and the camera centers on the new portal coordinates.
