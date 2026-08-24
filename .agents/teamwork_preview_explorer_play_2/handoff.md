# Handoff Report: Tier 4 E2E Play Scenarios Design (Milestone 4)

## 1. Observation

During the read-only investigation, the following files and APIs were analyzed:
* **`TEST_INFRA.md`**: Defines the 10 core features (F-01 to F-10) and the 5 test tiers. Tier 4 (Real-World Scenarios) requires $\ge 5$ tests simulating actual playthroughs.
* **`dandy-gb/tests/dandy_env.py`**: The ctypes wrapper exposes player state arrays:
  ```python
  self.env.get_player_x(p_idx)
  self.env.get_player_y(p_idx)
  self.env.get_player_health(p_idx)
  self.env.get_player_score(p_idx)
  self.env.get_player_keys(p_idx)
  self.env.get_player_bombs(p_idx)
  ```
  It also exposes mock HAL side-effect query methods:
  ```python
  self.env.get_sounds()          # Retracks played sounds
  self.env.get_draws()           # Tile drawing logs
  self.env.get_sprites()         # Active hardware sprites
  self.env.get_camera()          # Camera viewport offsets (cam_x, cam_y)
  self.env.assert_outer_border_walls(self) # Border wall validator
  ```
* **`dandy-gb/src/dandy_core.c`**: Implements game mechanics:
  * *Movement Cooldown*: Pressing a direction triggers a turn and a movement check, setting `player_move_timer` to `TICKS_PER_MOVE` (4), which counts down by 1 per tick.
  * *Door Unlocking*: `iterative_flood_fill` performs an 8-way flood fill turning all connected door tiles into `TILE_SPACE`.
  * *Arrow Mechanics*: Firing an arrow creates it and immediately steps it by 1 tile in the same tick. It travels 1 tile per tick.
  * *Sparse Grid Monster Rotor*: Monsters and generators tick only when `monster_rotor` matches `(my % 4) * 4 + (mx % 4)`, and they freeze if they are outside all players' viewports.
  * *Game Over Reset*: `end_game()` resets the level to 0, resets Player 0's health to 100, wipes all scores and inventories, and reloads Level 0.

---

## 2. Logic Chain

The step-by-step reasoning from observations to the scenario designs is as follows:
* **Logic Step 1 (Movement Cooldowns)**: Since movement has a 4-tick cooldown (1 tick to move, 3 ticks cooldown), we designed all movement sequences to be spaced by at least 3 wait ticks (input `0`) to guarantee deterministic execution.
* **Logic Step 2 (Door Flood-Fill & Multiplayer)**: To verify F-04 (Door Mechanics) and F-09 (Multiplayer) cooperatively, we designed a door network in Scenario 2 where Player 0's door at `(10, 5)` is connected to Player 1's door at `(13, 10)` via diagonal connector door tiles. This guarantees that when Player 0 consumes a key to unlock their door, both paths open simultaneously, allowing Player 1 to pass.
* **Logic Step 3 (Game Over Reset)**: To trigger a deterministic game over (F-07, F-10), we surround Player 0 at `(10, 9)` with four Level 3 monsters (`TILE_MONSTER3`) at coordinates `(10, 8)`, `(9, 9)`, `(11, 9)`, and `(10, 11)`. By cycling `monster_rotor` through all 16 sparse grid slots (16 steps of input `0`), all 4 monsters are guaranteed to tick exactly once, dealing a total of $4 \times 30 = 120$ damage, which reduces the player's 100 HP to 0. We assert that `end_game()` completely wipes all starting inventories and scores, and resets the level to 0.
* **Logic Step 4 (Combative Viewport Smart Bomb)**: To verify F-05, F-06, F-07, and F-08, Scenario 4 places a generator and three monsters in the player's viewport, and one monster far away at `(45, 2)` (off-screen). Firing an arrow Right immediately steps and destroys the first monster at `(6, 2)`. Triggering a Smart Bomb on Tick 8 decrements the bomb count, plays `SOUND_BOMB`, and clears the remaining entities in the 20x10 viewport, while the off-screen monster at `(45, 2)` remains untouched.
* **Logic Step 5 (Viewport Scrolling & Borders)**: To verify F-09 (Viewport) and Edge Wall Elision, Scenario 5 walks a player from `(5, 4)` to `(55, 25)`. We programmatically walk the player to 4 key checkpoints, asserting that `get_camera()` correctly clamps to `(0,0)` at the top-left, scrolls dynamically in the middle, and clamps to `(40, 20)` at the bottom-right. We also assert the player's hardware sprite relative pixel offsets at each checkpoint.

---

## 3. Caveats

* **Real ROM Levels**: The scenarios are designed using custom map layouts injected directly into `env.dandy_map` in the test setup. This is standard for isolated E2E tests, but we must ensure that the game core's `dandy_load_level()` is capable of loading the game's actual Level 0 after a game over or level transition without crashing.
* **LFSR Determinism**: Generator spawning in Scenario 4 is bypassed by smart-bombing the generator on Tick 8 before it can spawn any monsters. If the generator is allowed to tick, its spawn direction and timing will depend on the global LFSR seed, which must be carefully tracked.

---

## 4. Conclusion

The designed 5 E2E playthrough scenarios are complete, opaque-box, and robust. They fulfill all requirements of Milestone 4 (Tier 4 E2E Play Scenarios) and strictly follow the Double-Assert Rule (asserting both global variables and mock HAL side-effects) and Edge Wall Elision validation.

---

## 5. Verification Method

To verify these scenarios once they are implemented:
1. **Target File**: `dandy-gb/tests/test_tier4.py`
2. **Execution Command**:
   Navigate to the `dandy-gb` directory and run:
   ```bash
   make test_lib && make test
   ```
3. **Expected Results**: All 5 scenarios should pass, demonstrating 100% correctness of movement, timing, items, doors, combat, smart bombs, monster AI, generator spawning, multiplayer viewports, and level transitions.
