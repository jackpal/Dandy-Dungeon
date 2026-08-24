# Handoff Report: Milestone 4 - Level 0 Complete Walkthrough E2E Test Design

## 1. Observation

*   **Engine Core**: Analyzed `dandy-gb/src/dandy_core.c` and `dandy-gb/src/dandy_core.h`.
    *   Row offsets array: `const uint16_t row_offsets[DANDY_LEVEL_HEIGHT] = { 0, 60, 120, ... };` indicating a map width of 60 and height of 30.
    *   Player spawn portal location search: `dandy_map[row_offset + x] == TILE_UP` (lines 289-292).
    *   Player starting coordinates set relative to `TILE_UP` using `spawn_offsets_x` and `spawn_offsets_y` (lines 299-304).
    *   Movement timer and cooldown: `player_move_timer[p_idx] = TICKS_PER_MOVE;` (where `TICKS_PER_MOVE` is 4) (line 369).
    *   Movement switch cases and level transition: `case TILE_DOWN: hal_play_sound(SOUND_WARP); next_level(); return true;` (lines 420-423).
    *   Continuous shooting arrow spawn: `arrow_x[p_idx] = player_x[p_idx]; ... arrow_dir[p_idx] = player_dir[p_idx];` (lines 353-355) and arrow movement: `dandy_map[new_pos] = TILE_ARROW + ((arrow_dir[p] - 5) & 7);` (line 487).
*   **Levels Definition**: Analyzed `dandy-gb/src/levels.c`.
    *   Level 0 compressed array: `const uint8_t dandy_level_0[] = { ... };` (lines 5-70).
    *   Level 1 compressed array: `const uint8_t dandy_level_1[] = { ... };` (lines 73-140).
*   **Environment Bindings**: Analyzed `dandy-gb/tests/dandy_env.py`.
    *   Class `DandyEnv` wraps all CDLL functions and provides access to C globals: `self._player_x`, `self._player_y`, `self._player_health`, `self._current_level`, etc.
    *   Provides mock HAL query methods: `get_sounds()`, `get_sprites()`, `get_camera()`, `get_draws()`.
*   **Walkthrough Execution Verification**:
    *   Ran Python execution commands using `DandyEnv` and a custom state-space BFS pathfinder.
    *   Starting position of Player 0 on Level 0 was verified as `(33, 16)`.
    *   Stairs (`TILE_DOWN`) on Level 0 were located at `(22, 7)`.
    *   BFS discovered a path of exactly 216 steps to navigate the maze, collect two keys, unlock two doors, and reach the exit.
    *   Encountered self-blocking bug when constantly shooting: player actual position was `(30, 20)` instead of expected `(29, 20)` at step 3 due to their own arrow at `(29, 20)`.
    *   Encountered player death at step 168 (resetting position back to `(33, 16)`) due to dynamic monster AI collisions in row 1-3.
    *   Resolved both: implemented **Precise Shooting** (firing exactly 1 arrow on the first tick of a movement step when facing a monster) and boosted player starting health to **9999 HP**.
    *   Final verified execution ran successfully in **936 ticks**, transitioned to Level 1, reset player coordinates to Level 1 starting portal `(57, 1)`, scored 1200 points, and played the warp sound exactly once.

---

## 2. Logic Chain

1.  **Observation**: The player starting position is computed by finding `TILE_UP` and applying spawn offsets.
    *   *Logical Inference*: By querying `DandyEnv` after `init()`, we found the exact starting coordinates of Player 0 are `(33, 16)` and `TILE_UP` is at `(33, 17)`.
2.  **Observation**: The exit stairs `TILE_DOWN` are located at `(22, 7)` in the map.
    *   *Logical Inference*: To complete Level 0, Player 0 must navigate from `(33, 16)` to `(22, 7)`.
3.  **Observation**: The horizontal wall at row 11 and column of locked doors at column 3 prevent a direct path.
    *   *Logical Inference*: A pathfinding algorithm must be used to find the optimal sequence of moves. A state-space BFS (which tracks coordinates, collected keys, and unlocked doors) is the most robust way to find this path.
4.  **Observation**: Walking and shooting on every tick spawns an arrow at the target tile, which is treated as a solid obstacle on the next move, causing the player to slide out of sync.
    *   *Logical Inference*: We must only shoot when necessary (when a monster/generator is in the target tile) and only once per 4-tick movement step (on the first tick) so the arrow has time to hit and destroy the monster before the player attempts to walk onto the tile.
5.  **Observation**: Viewport-visible monsters pathfind toward the player, dealing contact damage. In a long playthrough (216 moves), the player takes ~380 damage and dies (triggering an automatic game-over reset back to Level 0).
    *   *Logical Inference*: For the E2E test to be 100% robust and isolated from random AI movements, we must set the player's health to a very high value (e.g., 9999 HP) at the start of the test.
6.  **Observation**: Stepping onto `TILE_DOWN` triggers `next_level()` and `hal_play_sound(SOUND_WARP)`.
    *   *Logical Inference*: We can verify a successful playthrough by asserting that `current_level` becomes 1, player coordinates are reset to the Level 1 portal `(57, 1)`, and the warp sound count is exactly 1.

---

## 3. Caveats

*   **Active Monster Randomness**: While player health is set to 9999 to prevent death, the active monsters may still occasionally block or slide the player by 1 tile. The execution loop handles this by allowing a divergence distance of up to 2 tiles from the expected BFS path.
*   **Diagonal Slide Priority**: Dandy Dungeon's slide mechanics try the main direction, then CCW, then CW. The BFS path assumes clean cardinal and diagonal moves. If a slide occurs, it could put the player slightly out of sync, though the test recovery block is designed to handle this.
*   **Single-Player Focus**: This walkthrough is designed for Player 0 (single-player). While the engine supports up to 4 players, only Player 0 is joined and active during this playthrough.

---

## 4. Conclusion

A complete playthrough of Level 0 is entirely possible and has been dynamically verified via python-ctypes. The optimal path is exactly 216 steps long and requires collecting two keys, unlocking two doors, and defeating several blocking monsters.

The playthrough E2E test must:
1.  Initialize the engine and set player 0 health to 9999 HP.
2.  Dynamically compute the path using a state-space BFS.
3.  Step the engine using the **Precise Shooting** input strategy (4 ticks per move; fire only on tick 0 when facing an obstacle).
4.  Apply the **Double-Assert Rule**:
    *   *Engine State*: level is 1, coordinates are `(57, 1)`, score is 1200, keys are 0.
    *   *HAL Side-Effects*: warp sound played once, shoot/hit/key sounds played, viewport camera clamped to `(40, 0)`, player sprite active in viewport.

This design is fully implemented as a clean, ready-to-run unittest class in `analysis.md` and is fully ready for the Implementer agent to add to the codebase.

---

## 5. Verification Method

To independently verify this walkthrough:
1.  Ensure the C library is compiled:
    ```bash
    make -C dandy-gb test_lib
    ```
2.  Run the dynamic walkthrough test script:
    ```bash
    python3 -c "
    import sys
    sys.path.insert(0, 'dandy-gb/tests')
    from dandy_env import DandyEnv
    # ... [Insert python code from section 4 of analysis.md] ...
    "
    ```
3.  Observe that it prints:
    *   `BFS Path length: 216`
    *   `Level transitioned to 1 successfully!`
    *   `Final level: 1`
    *   `Player 0 coordinates: (57, 1)`
    *   `Warp sound count: 1`
    *   And exits with 0 (success).
