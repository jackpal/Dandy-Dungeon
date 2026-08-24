# Handoff Report: Tier 4 E2E Play Scenarios Design

This handoff report summarizes the read-only investigation, the reasoning behind the designs of the Tier 4 E2E play scenarios, and the verification plan.

---

## 1. Observation

During the read-only investigation, the following files, code structures, and mechanics were observed and analyzed:

1. **Test Environment (`dandy-gb/tests/dandy_env.py`)**:
   - Offers an isolated test wrapper (`DandyEnv`) which copies `libdandy_test.so` per test case.
   - Binds C globals like `dandy_map`, `player_x`, `player_y`, `player_health`, `player_score`, `player_bombs`, `player_keys`, `player_dir`, and `player_move_timer`.
   - Exposes mock HAL query functions such as `mock_get_sounds()`, `mock_get_sprites()`, `mock_get_camera()`, and `mock_get_draws()`.
   - Contains a helper `assert_outer_border_walls(self, test_case)` that verifies all 176 border tiles are `TILE_WALL` (1) (lines 453-475).

2. **Movement and Cooldown (`dandy-gb/src/dandy_core.c`)**:
   - Player movement is governed by a 4-tick cooldown:
     ```c
     if (player_move_timer[p_idx] == 0) {
         player_move_timer[p_idx] = TICKS_PER_MOVE; // 4
         ...
     }
     ...
     if (player_move_timer[p_idx] > 0) {
         player_move_timer[p_idx]--;
     }
     ```
     This means that movement inputs must be spaced by exactly 4 ticks.

3. **Door & Key Flood Fill (`dandy-gb/src/dandy_core.c`)**:
   - Moving onto a locked door tile consumes a key and triggers an 8-way iterative flood fill that clears all connected doors:
     ```c
     iterative_flood_fill(nx, ny, TILE_DOOR, TILE_SPACE);
     ```
     This allows cooperative door-opening mechanics where unlocking a door in one corridor can open a path in an adjacent corridor if they are connected.

4. **Combat & Viewport Clamping (`dandy-gb/src/dandy_core.c`)**:
   - Firing arrows creates a projectile that travels 1 tile per tick until it hits a wall, monster, generator, or leaves the viewport.
   - Hitting a monster/generator destroys the arrow and targets:
     ```c
     if (tile_at_new >= TILE_BOMB && tile_at_new < TILE_ARROW) { ... }
     ```
   - Viewport camera is centered on the player and clamped:
     ```c
     int16_t vp_left = clamp(target_x - 10, 0, DANDY_LEVEL_WIDTH - 20); // max 40
     int16_t vp_top = clamp(target_y - 5, 0, DANDY_LEVEL_HEIGHT - 10);  // max 20
     ```
   - Hardware sprites are registered at viewport-relative positions in pixel space:
     ```c
     hal_set_sprite(sprite_count++, sx * 8, sy * 8, tile, sprite_flags);
     ```

5. **Monster Rotor Sparse Grid (`dandy-gb/src/dandy_core.c`)**:
   - Monsters are updated on a 16-tick sparse grid rotor:
     ```c
     monster_rotor++;
     if (monster_rotor >= 16) { monster_rotor = 0; }
     ...
     uint8_t x_start = monster_rotor % 4;
     uint8_t y_start = monster_rotor / 4;
     ```
     A monster at `(mx, my)` only ticks when `mx % 4 == monster_rotor % 4` and `my % 4 == monster_rotor / 4`.

---

## 2. Logic Chain

From these observations, we constructed the following reasoning:

1. **Deterministic Cooldowns**: Since movement has a 4-tick cooldown, all step-by-step player paths must inject the movement bitmask at the start of a 4-tick window and send `0` for the remaining 3 ticks. This ensures that the player stays in sync and does not lose moves.
2. **Cooperative Double Doors**: Since `iterative_flood_fill` clears all connected doors, placing a vertical line of door tiles spanning both Player 0's top corridor and Player 1's bottom corridor allows Player 0 to collect a key, unlock their door, and automatically open the path for Player 1.
3. **Deterministic Death & Reset**: Since the sparse rotor ticks monsters deterministically based on `monster_rotor`, we can place a Monster 3 at `(11, 10)` and Player 0 at `(10, 10)`, and set `monster_rotor = 10`. On the next step, `monster_rotor` becomes `11` (`11 % 4 = 3`, `11 / 4 = 2`), matching `(11 % 4, 10 % 4) = (3, 2)`. This guarantees that the monster ticks immediately, attacks Player 0, and triggers `end_game()`, resetting the level to 0 and wiping all stats.
4. **Smart Bomb Viewport Boundaries**: Since `do_bomb` scans the visible viewport `[vp_left, vp_left + 20]` and `[vp_top, vp_top + 10]`, placing a Generator and a Monster within `x=18` and another Monster/Generator at `x >= 22` when the player is at `(10, 10)` (viewport range `[0, 19]`) allows us to prove that the smart bomb only clears the on-screen entities, leaving the off-screen ones intact.
5. **Camera Scroll & Sprite Coordinates**: The camera clamps to `(40, 20)`. If a player starts at `(1, 1)` (camera `0,0`) and moves to `(58, 28)` (camera `40,20`), we can verify camera scroll offsets and assert that the hardware sprite coordinate registered in the mock HAL is exactly `((px - vp_left) * 8, (py - vp_top) * 8)`.

---

## 3. Caveats

- **LFSR Determinism**: Generator spawning uses an LFSR seed. While this design does not rely on random generator spawns (we either blow them up with a smart bomb or shoot them immediately), any test asserting on random spawns must ensure a fresh environment to guarantee identical LFSR state.
- **Player-Player Collisions**: Players cannot step on each other's tiles because the C engine treats player tiles as solid obstacles. In Scenario 2, Player 1 must wait until Player 0 clears the intersection to avoid collision blocking.

---

## 4. Conclusion

We have successfully designed 5 robust, complex, multi-step playthrough scenarios that fully cover the Tier 4 requirements. The designs are fully documented in `analysis.md` and are ready to be translated into unittest cases in `dandy-gb/tests/test_tier4.py`.

---

## 5. Verification Method

To verify the designs once implemented in `test_tier4.py`:
1. Navigate to the `dandy-gb/` directory.
2. Compile the shared library:
   ```bash
   make test_lib
   ```
3. Run the test suite:
   ```bash
   make test
   ```
4. Confirm that all 5 new scenarios pass successfully and that the test suite continues to show 100% pass rates.
5. Inspect `test_tier4.py` to verify that every test uses the `assert_outer_border_walls(self)` method to confirm Edge Wall Elision is maintained throughout the playthroughs.
