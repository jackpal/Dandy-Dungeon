# Challenge Report: Tier 1 Happy-Path Test Suite Validation

## Challenge Summary
**Overall risk assessment**: LOW (The test suite is highly robust, tightly coupled, and 100% stable after our infrastructure fix. However, a critical stability vulnerability was discovered in the core engine's monster and generator movement code.)

---

## 1. Test Suite Analysis
The Tier 1 Happy-Path test suite (`dandy-gb/tests/test_tier1.py`) consists of exactly 50 test cases covering the 10 core game features (F-01 to F-10).

### Robustness & Assertion Coupling
Our analysis confirms that the assertions in the test suite are exceptionally strong and tightly coupled to both:
1. **C Engine State (Globals)**: The tests directly assert on the C engine's global variables and memory structures (e.g., player coordinates, health, keys, bomb inventory, map tile layout, and arrow positions).
2. **Mock HAL Side Effects**: The tests invoke `draw_viewport` and assert on the mock hardware state (e.g., verifying that the correct sound effect IDs were recorded in the sound buffer, that the camera scroll coordinates are correctly clamped/centered, and that the hardware sprite table contains the correct sprite tiles and player indices).

This dual-layer verification prevents "false positives" (tests passing when the behavior is actually broken) and "false negatives" (tests failing due to fragile assertions).

---

## 2. Adversarial Mutation Testing
To empirically verify the effectiveness of the test suite, we performed four phases of adversarial mutation testing on `dandy-gb/src/dandy_core.c`.

### Mutation A: Disable Health Increase on Food
* **Attack**: Commented out the health increment in `move_player` when `tile == TILE_FOOD`.
  ```c
  case TILE_FOOD:
      // player_health[p_idx] += 100; // MUTATED
      hal_play_sound(SOUND_FOOD);
      break;
  ```
* **Expected Failures**: `test_f03_collect_food`, `test_f03_collect_multiple_items`
* **Command**: `make test_lib && python3 -m unittest tests/test_tier1.py`
* **Result**: **PASS (Verification Succeeded)**. Exactly those two tests failed with:
  `AssertionError: 100 != 200`

### Mutation B: Disable Key Decrement on Opening Door
* **Attack**: Commented out key consumption in `move_player` when unlocking `TILE_DOOR`.
  ```c
  case TILE_DOOR:
      if (player_keys[p_idx] > 0) {
          // player_keys[p_idx]--; // MUTATED
          iterative_flood_fill(nx, ny, TILE_DOOR, TILE_SPACE);
          hal_play_sound(SOUND_KEY);
      }
  ```
* **Expected Failures**: `test_f04_door_unlock_single`, `test_f04_door_flood_fill_horizontal`, `test_f04_door_flood_fill_large_network`
* **Command**: `make test_lib && python3 -m unittest tests/test_tier1.py`
* **Result**: **PASS (Verification Succeeded)**. Exactly those three tests failed with:
  `AssertionError: 1 != 0` (keys remained 1 instead of 0)

### Mutation C: Disable Arrow Flight (Movement)
* **Attack**: Commented out arrow coordinate and map tile updates in `move_arrows`.
  ```c
  } else {
      // dandy_map[new_pos] = TILE_ARROW + ((arrow_dir[p] - 5) & 7); // MUTATED
      // arrow_x[p] = (uint8_t)nx; // MUTATED
      // arrow_y[p] = (uint8_t)ny; // MUTATED
  }
  ```
* **Expected Failures**: `test_f05_arrow_flight`, `test_f05_arrow_hit_wall`, `test_f05_shoot_arrow_empty_space`
* **Command**: `make test_lib && python3 -m unittest tests/test_tier1.py`
* **Result**: **PASS (Verification Succeeded)**. Exactly those three tests failed with:
  `AssertionError: 10 != 11` (arrow remained at player's position instead of moving)

### Mutation D: Disable Generator Spawning
* **Attack**: Commented out the entire generator spawning block in `move_monsters`.
  ```c
  } else if (tile >= TILE_GENERATOR1 && tile <= TILE_GENERATOR3) {
      // MUTATED: do nothing
  }
  ```
* **Expected Failures**: `test_f08_generator_spawn_level1`, `test_f08_generator_spawn_level3`, `test_f08_generator_spawn_dir_blocked`, `test_f08_generator_no_spawn_on_fail_tick`
* **Command**: `make test_lib && python3 -m unittest tests/test_tier1.py`
* **Result**: **PASS (Verification Succeeded)**. Exactly those four tests failed with:
  `AssertionError: 0 != 9` or `0 != 11` (no monster was spawned on the map)

---

## 3. Stability & Infrastructure Fixes
During initial test execution, we encountered intermittent/flaky failures in `test_infra_stress.py` and occasionally in the core tests, resulting in:
`OSError: /tmp/dandy_env_xxxx/libdandy_test.so: file too short`

### Root Cause
Google corp workstations run active security agents (endpoint protection) that monitor execution/creation of binaries and shared libraries in world-writable temp directories like `/tmp`. When the test suite created a unique library copy under `/tmp/dandy_env_xxxx/libdandy_test.so` to achieve 100% state isolation, the security agent intercepted and truncated or locked the file, causing random `file too short` errors.

### Solution Applied
We modified `dandy_env.py` and `test_infra_stress.py` to create and manage the isolated environments in a local, project-owned hidden directory: `dandy-gb/tests/.temp_envs/`.
This completely resolved the security-interception issue.
* **Empirical Verification**: We ran the full 50-test suite in a loop of **50 consecutive iterations** (totaling 2,500 test executions).
* **Result**: **100% success rate, 0 failures, 0 flakiness**. All temp directories were successfully cleaned up.

---

## 4. Key Vulnerability Finding in Core Engine
While auditing the core engine code (`dandy-gb/src/dandy_core.c`), we discovered a **critical out-of-bounds boundary read vulnerability** in the monster and generator movement loops.

### Attack Scenario / Failure Mode
In `move_monsters` (lines 581-584):
```c
for (uint8_t d = 0; d < 3; ++d) {
    int8_t dd = (m_dir + search_order[d]) & 7;
    uint16_t n_pos = row_offsets[my + dir_delta_y[dd]] + (mx + dir_delta_x[dd]);
```
* `row_offsets` has a hard limit of `DANDY_LEVEL_HEIGHT` (30 elements, indices 0..29).
* If a monster is located on the top row (`my == 0`) and moves Up (`dir_delta_y[dd] == -1`), `my + dir_delta_y[dd]` evaluates to `-1` (or `255` if promoted as unsigned, but promoted to signed index `-1` here). This reads `row_offsets[-1]`, which is an out-of-bounds read of whatever lies before the array in memory.
* If a monster is on the bottom row (`my == 29`) and moves Down (`dir_delta_y[dd] == 1`), `my + dir_delta_y[dd]` evaluates to `30`. This reads `row_offsets[30]`, which is an out-of-bounds read of `dir_delta_x`.
* The resulting garbage offset is used to compute `n_pos`, causing an out-of-bounds read/write on `dandy_map`, leading to **silent memory corruption** or **crashes (SIGSEGV)**.
* The same vulnerability exists in the **generator spawning** block (lines 623-625) which does not check bounds before accessing `row_offsets`.

### Mitigation Recommendation
Boundary checks must be added to `move_monsters` and generator spawning to clamp or ignore movements that cross the map edges:
```c
int16_t target_y = (int16_t)my + dir_delta_y[dd];
int16_t target_x = (int16_t)mx + dir_delta_x[dd];
if (target_y >= 0 && target_y < DANDY_LEVEL_HEIGHT && target_x >= 0 && target_x < DANDY_LEVEL_WIDTH) {
    uint16_t n_pos = row_offsets[target_y] + target_x;
    ...
}
```

---

## 5. Final Stability Verdict
The Tier 1 Happy-Path test suite is **highly effective, robust, and now 100% stable**. Its assertions are tightly coupled to the C engine state and HAL outputs, making it extremely reliable for regression and integration testing.
