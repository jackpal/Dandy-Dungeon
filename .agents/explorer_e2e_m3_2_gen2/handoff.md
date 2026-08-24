# Handoff Report - E2E Tier 2 & Tier 3 Test Case Design (Milestone 3)

This handoff report summarizes the complete analysis and design of the E2E test suite for Milestone 3, focusing on Tier 2 (Boundary & Corner Cases) and Tier 3 (Cross-Feature Interactions) tests.

---

## 1. Observation

We directly examined and analyzed the following codebase files:
* Core engine definition and implementation:
  * `dandy-gb/src/dandy_core.h`: Defines game constants, tile IDs, button bitmasks, global state variables (`dandy_map`, `current_level`, `monster_rotor`, player arrays, arrow arrays), and core platform-independent functions.
  * `dandy-gb/src/dandy_core.c`: Implements level loading, player movement, sliding, arrow flight, smart bombs, monster pathfinding, generator spawning, and multi-player state updates.
* Test runner and existing test cases:
  * `dandy-gb/tests/dandy_env.py`: Programmatic `DandyEnv` class wrapping the unique temporary compilations of the shared library `libdandy_test.so` via `ctypes`.
  * `dandy-gb/tests/test_tier1.py`: Implements 59 headful/headless functional tests checking F-01 to F-10.
* Project testing standards:
  * `TEST_INFRA.md`: Outlines the offline E2E architectural design, the 10 core game features, the five testing tiers, and the mandatory **Double-Assert Rule**.

We ran the existing test suite via:
```bash
make test_lib && make test
```
The command completed successfully with:
```
Ran 59 tests in 3.158s
OK
```
Verifying that the offline test environment is fully functional and stable.

---

## 2. Logic Chain

From our deep analysis of the engine code, we identified several crucial architectural nuances and boundaries that served as the logical foundation for our test designs:

1. **Arrow Viewport and Destruction Logic (F-05 & F-06)**:
   * **Observation**: In `dandy_core.c`, `move_arrows()` performs a viewport boundary check *before* checking the target tile content:
     ```c
     if (nx < vp_left || ny < vp_top || nx >= vp_left + 20 || ny >= vp_top + 10) {
         arrow_dir[p] = -1;
         is_dirty = true;
         continue;
     }
     ```
   * **Deduction**: This means that any destructible target (monster, generator, bomb tile) residing outside the active viewport is *completely immune* to arrow damage, as the arrow is destroyed before it can perform the hit check.
   * **Test Design**: Designed `test_f05_arrow_destructible_outside_viewport` to verify this exact boundary immunity.

2. **Flood Fill Stack Bounds (F-04)**:
   * **Observation**: In `dandy_core.c`, the flood fill uses a static stack of size 64:
     ```c
     #define FLOOD_STACK_SIZE 64
     static uint8_t flood_stack_x[FLOOD_STACK_SIZE];
     ```
     If the stack is full, `flood_push` silently ignores subsequent pushes.
   * **Deduction**: In extremely large or highly branching door networks exceeding 64 tiles, the flood fill will terminate early, leaving the furthest doors locked.
   * **Test Design**: Designed `test_f04_door_flood_fill_stack_limit_reached` to assert that exactly 64 doors are cleared and the remaining ones remain locked. This is a critical engine boundary constraint.

3. **Monster and Generator Viewport Freezing (F-07 & F-08)**:
   * **Observation**: In `dandy_core.c`, monsters and generators are scanned on a sparse grid rotor, but are immediately bypassed if they are not within any active player's viewport:
     ```c
     if (!is_visible) {
         continue; // Freeze this off-screen monster/generator!
     }
     ```
   * **Deduction**: Frozen off-screen generators do not update the global LFSR seed (`rand_seed`). Thus, random state transitions only advance when the generator is visible.
   * **Test Design**: Designed `test_f08_generator_off_viewport_freeze` to verify that the seed does not update when a generator is off-screen.

4. **Multiplayer Sprite Registration Limit (F-09)**:
   * **Observation**: `dandy_draw_viewport()` enforces a strict hardware sprite cap of 40:
     ```c
     if (sprite_count < 40) { ... hal_set_sprite(...) ... }
     ```
   * **Deduction**: Under extreme entity density, only the first 40 entities will receive hardware sprites; the rest must be drawn as background spaces to prevent OAM corruption.
   * **Test Design**: Designed `test_f09_viewport_hardware_sprite_limit` to assert that exactly 40 sprites are registered when 50 monsters are in view.

---

## 3. Caveats

* **Engine Level Loading Limitations**: The C function `dandy_load_level()` does not perform an out-of-bounds check on the level index. Passing an invalid index causes a segmentation fault (`SIGSEGV`). This behavior is expected and verified via a subprocess crash test in the existing Tier 1 suite.
* **Double-Assert Rule Strictness**: Every designed test case requires asserting on both C globals (e.g. `player_x`, `player_health`, `arrow_dir`, `dandy_map`) and mock HAL side-effects (sound counts, camera coordinates, drawn tiles, hardware sprites). Implementing agents must verify both sides of the contract.

---

## 4. Conclusion

We have designed a highly comprehensive, robust, and complete suite of **63 tests** (47 Tier 2 boundary tests, 16 Tier 3 interaction tests) spanning all 10 core features. 

The concrete designs are fully written to:
`/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/.agents/explorer_e2e_m3_2_gen2/analysis.md`

This design is fully self-contained and ready for immediate implementation by the downstream Implementer agent.

---

## 5. Verification Method

To independently verify this design:
1. Inspect the detailed test case specifications in `/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/.agents/explorer_e2e_m3_2_gen2/analysis.md`.
2. Confirm that every test case has:
   * A descriptive name (e.g. `test_f05_arrow_off_viewport_top`).
   * A clear setup (map tiles, coordinates, inventory, health).
   * Exact inputs (button presses, empty steps, programmatic calls).
   * Double-assertions (verifying both C globals and mock HAL side-effects).
3. The Implementer can code these tests directly in `dandy-gb/tests/test_tier2.py` and `dandy-gb/tests/test_tier3.py`, then verify execution using:
   ```bash
   make test
   ```
