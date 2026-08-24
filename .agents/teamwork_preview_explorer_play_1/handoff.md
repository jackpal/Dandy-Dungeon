# Handoff Report: Tier 4 E2E Play Scenarios (Milestone 4)

This report provides the structured handoff for the Tier 4 E2E Play Scenarios design of the Dandy Dungeon project.

---

## 1. Observation

During my read-only investigation of the Dandy Dungeon codebase, I observed the following key files, lines, and structures:

1. **Architecture & Test Infrastructure**:
   - `PROJECT.md` lines 72-80: Defines the offline E2E test interface (Mock HAL) consisting of `hal_draw_tile`, `hal_update_hud`, `hal_clear_sprites`, `hal_set_sprite`, and `hal_play_sound`.
   - `SCOPE.md` lines 44-47: Explains that `dandy_env.py` exposes all core C globals (`dandy_map`, `player_x`, `player_y`, `player_health`, `player_score`, `player_bombs`, `player_keys`, `player_dir`, `player_move_timer`, `arrow_x`, `arrow_y`, `arrow_dir`) and functions (`dandy_init`, `dandy_step`, `dandy_load_level`, `dandy_join_player`).

2. **Player Movement & Cooldowns**:
   - `dandy_core.c` lines 368-377:
     ```c
     if (player_move_timer[p_idx] == 0) {
         player_move_timer[p_idx] = TICKS_PER_MOVE;
         // Slide mechanics: try main direction, then ±1 direction
         for (uint8_t di = 0; di < 3; ++di) {
             int8_t dd = (player_dir[p_idx] + search_order[di]) & 7;
             if (move_player(p_idx, dd)) {
                 break;
             }
         }
     }
     ```
     This confirms that a player's move timer is set to `TICKS_PER_MOVE` (4) immediately before trying to move, and that even if the move is blocked, the cooldown is still triggered.

3. **Weapon & Firing Mechanics**:
   - `dandy_core.c` lines 351-358:
     ```c
     // Fire Arrow (Level triggered)
     if (buttons & BUTTON_FIRE) {
         if (arrow_dir[p_idx] == -1) {
             arrow_x[p_idx] = player_x[p_idx];
             arrow_y[p_idx] = player_y[p_idx];
             arrow_dir[p_idx] = player_dir[p_idx];
             hal_play_sound(SOUND_SHOOT);
         }
     }
     ```
     This proves that firing an arrow is processed before movement in `do_player_buttons()`, spawning the arrow at the player's pre-move coordinate facing in the player's pre-move direction.
   - `dandy_core.c` lines 443-493: Shows the arrow steps 1 tile per tick in `move_arrows()`, deactivates on hit, degrades monsters/generators (monster3 -> monster2 -> monster1 -> space), and deactivates if leaving the player's viewport.

4. **Monster Ticking & Spawn Logic**:
   - `dandy_core.c` lines 536-540: Monsters tick on a 16-step rotor (`monster_rotor++` wrapping at 16).
   - `dandy_core.c` lines 556-561: Scan occurs on a sparse grid: `x_start = monster_rotor % 4`, `y_start = monster_rotor / 4`, stepping by 4.
   - `dandy_core.c` lines 570-582: Monsters and generators freeze (do not tick) if they are not visible in any active player's viewport.
   - `dandy_core.c` lines 622-642: Generator spawning uses a static Galois LFSR starting from `0xACE1` and spawns the generator's level monster in adjacent space tiles clockwise.

5. **Spectator Centroid Camera & Viewport Clamping**:
   - `dandy_core.c` lines 221-229: Target camera top-left `(vp_left, vp_top)` is calculated as:
     - `vp_left = clamp(target_x - 10, 0, DANDY_LEVEL_WIDTH - 20) = clamp(target_x - 10, 0, 40)`.
     - `vp_top = clamp(target_y - 5, 0, DANDY_LEVEL_HEIGHT - 10) = clamp(target_y - 5, 0, 20)`.
   - `dandy_core.c` lines 201-216: Spectator camera centers on the centroid of remaining alive players if the local player is dead.
   - `dandy_core.c` lines 254-268: Viewport coordinate to sprite coordinate conversion: `sx * 8` and `sy * 8` pixels.

6. **Edge Wall Elision & Resetting**:
   - `dandy_env.py` lines 453-475: Implements `assert_outer_border_walls(self, test_case)` to verify that the outer border of the 60x30 map is composed entirely of `TILE_WALL`.
   - `dandy_core.c` lines 320-334: `end_game()` resets `current_level` to 0, resets all players' health, score, keys, and bombs, and calls `dandy_load_level(0)`.

---

## 2. Logic Chain

From these observations, I established the following logical progression to design the E2E play scenarios:

1. **Custom Map Isolation**: Since the core engine exposes direct access to `dandy_map` RAM buffer and player coordinates via `dandy_env.py` (Observation 1.2), we can inject custom tile layouts and coordinates directly to create highly focused, rapid-running, and 100% deterministic test scenarios. This avoids having to write massive player input sequences (hundreds of steps) that would be needed to navigate the actual ROM levels.
2. **Deterministic Inputs**: Since movement is regulated by a 4-tick cooldown (Observation 1.2), we can construct exact tick-by-tick inputs where player movement ticks are spaced by 4 ticks, and intermediate ticks are held or zeroed.
3. **Double Assertion Strategy**:
   - Globals: After every action or transition, we assert on coordinates, inventory (keys, bombs), and health directly via `dandy_env.py`.
   - HAL side-effects: We call `dandy_draw_viewport()` and query the mock HAL logs (`mock_get_sounds()`, `mock_get_viewport_camera()`, and `mock_get_sprites()`) to assert on sound IDs, camera offsets, and hardware sprite coordinates.
4. **Integration of Compressores & Elision**: Since step-onto-stairs transitions trigger `next_level()` and `dandy_load_level()` (Observation 1.1/1.6), we can design Scenario 1 to start on a custom Level 0 layout, and then step onto the stairs to transition to the real, decompressed Level 1 from ROM. This successfully integrates and tests the level compiler decompression correctness and the Edge Wall Elision reconstruction (`assert_outer_border_walls`) in a real playthrough context.
5. **Deterministic AI & Game Over Reset**:
   - By setting `monster_rotor` directly and placing monsters at specific grid positions, we can predict exactly which tick a monster will pathfind and attack a player (Observation 1.4).
   - By dropping both players' health to 0, we can trigger the global `end_game()` reset and assert that all inventories and scores are wiped, and that Level 0 is loaded (Observation 1.5).

---

## 3. Caveats

- **LFSR Seed Reset**: The Galois LFSR seed `rand_seed` is static inside `move_monsters()` and is not reset by `dandy_init()`. The design relies on the Python wrapper's CDLL load isolation (which copies the `.so` to a unique temp file for every single test case) to ensure that the LFSR seed starts fresh at `0xACE1` for each scenario.
- **Player-Player Blocking**: Since players block each other, cooperative movements must be strictly ordered. Player 1 must move out of the way before Player 0 can step into their former position. This is accounted for in the cooperative scenario.

---

## 4. Conclusion

The 5 designed playthrough scenarios represent complete, requirement-driven, and robust coverage of the Tier 4 E2E Play Scenarios (Milestone 4):
- **Scenario 1**: Winding maze navigation, key collection, door unlocking, distant monster shooting, food collection, and stairs transition to real Level 1 (with Edge Wall Elision check).
- **Scenario 2**: Cooperative multiplayer, parallel pathing, item sharing, door unlocking for a teammate, player-player blocking, score splitting, and co-op level transition.
- **Scenario 3**: Multi-player monster attacks, sparse grid pathfinding, player death, game over trigger, full inventory/score wipe, and reset to Level 0.
- **Scenario 4**: Strategic shooting, multi-level monster degradation, generator clearing, smart bomb viewport sweep, and off-screen entity preservation.
- **Scenario 5**: Camera viewport scrolling, clamping at boundaries (top-left, middle, bottom-right), hardware sprite offset mapping, and spectator camera centroid tracking.

Detailed designs and step-by-step input/assertion tables are written in `analysis.md` in the working directory.

---

## 5. Verification Method

To independently verify this design and execute the scenarios:
1. Locate the detailed design report: `/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/.agents/teamwork_preview_explorer_play_1/analysis.md`.
2. Inspect the test file structure. The designs are fully prepared for implementation in `dandy-gb/tests/test_tier4.py`.
3. Run the E2E verification command from the `dandy-gb/` directory:
   ```bash
   make test
   ```
   All tests (including the new Tier 4 suite) should pass without errors, and the Edge Wall Elision check will validate the ROM decompression segment.
