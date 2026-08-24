# Dandy Dungeon E2E Test Suite Design (Milestone 3)

This document contains the comprehensive analysis and design of Tier 2 (Boundary & Corner Cases) and Tier 3 (Cross-Feature Interactions) E2E tests for the Dandy Dungeon C engine.

All test cases are designed for the programmatic E2E test runner (`dandy_env.py`) and strictly adhere to the **Double-Assert Rule**, verifying both internal C globals and mock HAL side-effects (sound counts, tile draws, camera coordinates, and hardware sprites).

---

## 1. Feature Coverage & Test Tally

| Feature ID | Feature Name | Tier 2 (Boundary) Count | Tier 3 (Interaction) Count |
|---|---|---|---|
| **F-01** | Movement & Timing | 6 | 1 |
| **F-02** | Slide Mechanics | 4 | 1 |
| **F-03** | Item Collection | 3 | 1 |
| **F-04** | Door & Key Mechanics | 4 | 1 |
| **F-05** | Combat & Projectiles | 8 | 3 |
| **F-06** | Smart Bomb Action | 4 | 1 |
| **F-07** | Monster Behavior | 7 | 3 |
| **F-08** | Generator Spawning | 4 | 1 |
| **F-09** | Multiplayer & Viewport | 4 | 2 |
| **F-10** | Level Transitions | 3 | 2 |
| **Total** | | **47** | **16** |

*Total Designed Tests*: **63 Tests** (47 Tier 2, 16 Tier 3), far exceeding the milestone requirement of 40 Tier 2 and 8 Tier 3 tests.

---

## 2. Tier 2: Boundary & Corner Cases (47 Tests)

### F-01: Movement & Timing (6 Tests)

#### 1. `test_f01_move_boundary_clamp_left`
* **Setup**: Clean map. Player 0 at `x = 0, y = 10`.
* **Input**: Step Left (`BUTTON_LEFT`) for Player 0.
* **Assertions**:
  * *Globals*: Player 0 coordinates remain `(0, 10)`. `player_move_timer[0]` is set to `3` (cooldown active). Map tile at `(0, 10)` remains `TILE_PLAYER1` (facing Left).
  * *HAL*: No sound played. Viewport drawn: camera target is `(0, 10)`, camera scroll clamped to `(0, 5)`. Active sprite list contains Player 0 sprite facing Left at viewport relative coordinates.

#### 2. `test_f01_move_boundary_clamp_right`
* **Setup**: Clean map. Player 0 at `x = 59, y = 10`.
* **Input**: Step Right (`BUTTON_RIGHT`) for Player 0.
* **Assertions**:
  * *Globals*: Player 0 coordinates remain `(59, 10)`. `player_move_timer[0]` is set to `3`. Map tile at `(59, 10)` remains `TILE_PLAYER1` (facing Right).
  * *HAL*: No sound played. Viewport drawn: camera target is `(59, 10)`, camera scroll clamped to `(40, 5)`. Sprite list contains Player 0 facing Right at viewport relative `x = 19 * 8`.

#### 3. `test_f01_move_boundary_clamp_top`
* **Setup**: Clean map. Player 0 at `x = 10, y = 0`.
* **Input**: Step Up (`BUTTON_UP`) for Player 0.
* **Assertions**:
  * *Globals*: Player 0 coordinates remain `(10, 0)`. `player_move_timer[0]` is set to `3`. Map tile at `(10, 0)` remains `TILE_PLAYER1` (facing Up).
  * *HAL*: No sound. Viewport drawn: camera target `(10, 0)`, camera scroll clamped to `(0, 0)`. Sprite list contains Player 0 facing Up.

#### 4. `test_f01_move_boundary_clamp_bottom`
* **Setup**: Clean map. Player 0 at `x = 10, y = 29`.
* **Input**: Step Down (`BUTTON_DOWN`) for Player 0.
* **Assertions**:
  * *Globals*: Player 0 coordinates remain `(10, 29)`. `player_move_timer[0]` is set to `3`. Map tile at `(10, 29)` remains `TILE_PLAYER1` (facing Down).
  * *HAL*: No sound. Viewport drawn: camera target `(10, 29)`, camera scroll clamped to `(0, 20)`. Sprite list contains Player 0 facing Down.

#### 5. `test_f01_move_diagonal_boundary_clamp`
* **Setup**: Clean map. Player 0 at `x = 0, y = 0` (top-left corner).
* **Input**: Step Up-Left (`BUTTON_UP | BUTTON_LEFT`) for Player 0.
* **Assertions**:
  * *Globals*: Player 0 coordinates remain `(0, 0)`. `player_move_timer[0]` is set to `3`. Map tile at `(0, 0)` remains Player 0 facing Up-Left.
  * *HAL*: No sound. Viewport drawn: camera scroll clamped to `(0, 0)`. Sprite list contains Player 0 facing Up-Left.

#### 6. `test_f01_move_timer_cooldown_multi_input`
* **Setup**: Clean map. Player 0 at `x = 10, y = 10`.
* **Input**: Hold Right (`BUTTON_RIGHT`) across 6 successive steps.
* **Assertions**:
  * *Globals*:
    * Step 1: Moves to `(11, 10)`, timer = 3.
    * Step 2, 3, 4: Remains at `(11, 10)`, timer decrements to 2, 1, 0.
    * Step 5: Moves to `(12, 10)`, timer = 3.
    * Step 6: Remains at `(12, 10)`, timer = 2.
  * *HAL*: Verify no sounds. Camera target on Step 5 is `(12, 10)`, camera scroll `(2, 5)`.

---

### F-02: Slide Mechanics (4 Tests)

#### 7. `test_f02_slide_boundary_corner_blocked`
* **Setup**: Clean map. Player 0 at `x = 1, y = 0`. Wall at `(0, 0)`.
* **Input**: Step Up-Left (`BUTTON_UP | BUTTON_LEFT`).
* **Assertions**:
  * *Globals*:
    * Primary: `(0, 0)` is wall (blocked).
    * Clockwise (Left): `clamp(1-1) = 0`, `clamp(0-0) = 0` -> `(0, 0)` is wall (blocked).
    * Counter-clockwise (Up): `clamp(1-0) = 1`, `clamp(0-1) = 0` -> `(1, 0)` is Player's own tile (blocked).
    * Player remains at `(1, 0)`.
  * *HAL*: No sound. Viewport scroll clamped to `(0, 0)`. Player sprite remains at `(1, 0)`.

#### 8. `test_f02_slide_at_boundary_success`
* **Setup**: Clean map. Player 0 at `x = 1, y = 1`. Wall at `(0, 0)` (Up-Left) and `(0, 1)` (Left).
* **Input**: Step Up-Left (`BUTTON_UP | BUTTON_LEFT`).
* **Assertions**:
  * *Globals*:
    * Primary `(0, 0)` is blocked by wall.
    * Clockwise `(0, 1)` is blocked by wall.
    * Counter-clockwise `(1, 0)` is space (free).
    * Player successfully slides to `(1, 0)`.
  * *HAL*: Player sprite drawn at `(1, 0)`. Camera scroll clamped to `(0, 0)`.

#### 9. `test_f02_slide_obstacle_non_solid_items`
* **Setup**: Clean map. Player 0 at `x = 10, y = 10`. Wall at `(11, 10)` (Right). Food at `(11, 9)` (Up-Right). Space at `(11, 11)` (Down-Right).
* **Input**: Step Right (`BUTTON_RIGHT`).
* **Assertions**:
  * *Globals*:
    * Primary `(11, 10)` is wall (blocked).
    * Clockwise search order `search_order[1] = -1` (Up-Right) target is `(11, 9)` (Food).
    * Since Food is a non-solid, `move_player` treats it as passable!
    * Player slides to `(11, 9)`, collects Food. Health becomes `200`.
  * *HAL*: Plays `SOUND_FOOD`. Player sprite at `(11, 9)`.

#### 10. `test_f02_slide_between_two_monsters`
* **Setup**: Clean map. Player 0 at `x = 10, y = 10`. Monster 1 at `(11, 10)` (Right) and `(11, 9)` (Up-Right).
* **Input**: Step Right (`BUTTON_RIGHT`).
* **Assertions**:
  * *Globals*:
    * Primary `(11, 10)` is Monster 1 (solid for player movement, blocked).
    * Clockwise `(11, 9)` is Monster 1 (blocked).
    * Counter-clockwise `(11, 11)` is Space (free).
    * Player slides to `(11, 11)`. No monster contact occurs.
  * *HAL*: No contact sounds. Player sprite at `(11, 11)`.

---

### F-03: Item Collection (3 Tests)

#### 11. `test_f03_collect_food_extreme_health`
* **Setup**: Clean map. Player 0 at `x = 10, y = 10`. Place 10 Food tiles on a line from `(11, 10)` to `(20, 10)`.
* **Input**: Move player Right repeatedly over 10 steps (waiting out move cooldowns).
* **Assertions**:
  * *Globals*: Player health increments by 100 on each step, reaching exactly `1100` HP. No integer overflow or clamping occurs.
  * *HAL*: Plays `SOUND_FOOD` exactly 10 times.

#### 12. `test_f03_collect_item_at_map_edge`
* **Setup**: Clean map. Place `TILE_KEY` at `(0, 0)`. Player 0 at `(1, 0)`.
* **Input**: Step Left (`BUTTON_LEFT`).
* **Assertions**:
  * *Globals*: Player 0 at `(0, 0)`. `player_keys[0]` becomes `1`. Map tile at `(0, 0)` is Player.
  * *HAL*: Plays `SOUND_KEY`.

#### 13. `test_f03_collect_items_simultaneously_multiplayer`
* **Setup**: Clean map. Player 0 at `(10, 10)`. Player 1 at `(20, 10)`. Place `TILE_BOMB` at `(11, 10)` and `TILE_FOOD` at `(19, 10)`.
* **Input**: Player 0 steps Right, Player 1 steps Left.
* **Assertions**:
  * *Globals*:
    * Player 0 at `(11, 10)`, `player_bombs[0]` = 1.
    * Player 1 at `(19, 10)`, `player_health[1]` = 200.
  * *HAL*: `mock_get_sound_count()` is 2. Played sounds include `SOUND_KEY` and `SOUND_FOOD`.

---

### F-04: Door & Key Mechanics (4 Tests)

#### 14. `test_f04_door_flood_fill_boundary_limits`
* **Setup**: Create a solid vertical line of door tiles spanning from `(11, 0)` to `(11, 29)` (full map height). Player 0 at `(10, 10)` with 1 key.
* **Input**: Step Right (`BUTTON_RIGHT`).
* **Assertions**:
  * *Globals*: Player at `(11, 10)`, key count is `0`. Every single door tile from `(11, 0)` to `(11, 29)` is cleared to `TILE_SPACE` (or player).
  * *HAL*: Plays `SOUND_KEY`. Viewport drawn: all visible door tiles cleared.

#### 15. `test_f04_door_flood_fill_circular`
* **Setup**: Create a circular ring of door tiles (e.g. a 3x3 hollow square of doors at `x = [11..13], y = [9..11]`). Player 0 at `(10, 10)` with 1 key.
* **Input**: Step Right into the ring.
* **Assertions**:
  * *Globals*: Player at `(11, 10)`, key count is `0`. Entire ring of doors is cleared. Algorithm terminates cleanly.
  * *HAL*: Plays `SOUND_KEY`.

#### 16. `test_f04_door_flood_fill_stack_limit_reached`
* **Setup**: Create a massive contiguous grid of door tiles of size 9x9 (81 doors total) at `x = [11..19], y = [5..13]`. Player 0 at `(10, 9)` with 1 key.
* **Input**: Step Right into the grid.
* **Assertions**:
  * *Globals*:
    * Since the engine's non-recursive flood fill has a static stack limit of `FLOOD_STACK_SIZE = 64`:
    * Exactly 64 door tiles are cleared.
    * The remaining 17 door tiles furthest from the entry point remain intact as `TILE_DOOR`.
    * Player at `(11, 9)`, key count is `0`.
  * *HAL*: Plays `SOUND_KEY`. Viewport draws the partially cleared door block.

#### 17. `test_f04_door_diagonal_flood_fill_only`
* **Setup**: Place door tiles only diagonally connected: `(11, 10)` and `(12, 11)`. Block cardinal spaces around them with walls. Player 0 at `(10, 10)` with 1 key.
* **Input**: Step Right into `(11, 10)`.
* **Assertions**:
  * *Globals*: Both doors cleared to `TILE_SPACE`/Player. Player at `(11, 10)`. Key count = 0.
  * *HAL*: Plays `SOUND_KEY`.

---

### F-05: Combat & Projectiles (8 Tests)

#### 18. `test_f05_arrow_off_viewport_top`
* **Setup**: Clean map. Player 0 at `(15, 10)`. Viewport top is `vp_top = 5`.
* **Input**: Face Up and press `BUTTON_FIRE`. Step empty inputs (`0`) across successive ticks.
* **Assertions**:
  * *Globals*:
    * Tick 0: Arrow spawned at player, moves to `(15, 9)` in same tick. `arrow_dir[0] = 0`.
    * Tick 1, 2, 3, 4: Arrow moves to `(15, 8)`, `(15, 7)`, `(15, 6)`, `(15, 5)`.
    * Tick 5: Arrow target is `(15, 4)`. Since `4 < vp_top` (`4 < 5`), arrow is destroyed. `arrow_dir[0] = -1`.
  * *HAL*: `SOUND_SHOOT` played. No `SOUND_HIT`. Active sprite list has arrow sprite on ticks 0..4, no arrow sprite on tick 5.

#### 19. `test_f05_arrow_off_viewport_bottom`
* **Setup**: Clean map. Player 0 at `(15, 10)`. Viewport bottom is `vp_top + 10 = 15`.
* **Input**: Face Down and press `BUTTON_FIRE`. Step empty inputs.
* **Assertions**:
  * *Globals*:
    * Tick 0: Arrow moves to `(15, 11)`.
    * Tick 1, 2, 3, 4: Arrow moves to `(15, 12)`, `(15, 13)`, `(15, 14)`. On tick 4, it is at `(15, 14)` (edge).
    * Tick 5: Target is `(15, 15)`. Since `15 >= 15` (out of viewport), arrow destroyed (`arrow_dir[0] = -1`).
  * *HAL*: Arrow sprite active on ticks 0..4, inactive on tick 5.

#### 20. `test_f05_arrow_off_viewport_left`
* **Setup**: Clean map. Player 0 at `(15, 10)`. Viewport left is `vp_left = 5`.
* **Input**: Face Left and press `BUTTON_FIRE`. Step empty inputs.
* **Assertions**:
  * *Globals*:
    * Tick 0: Arrow moves to `(14, 10)`.
    * Ticks 1..8: Arrow moves to `(6, 10)` on Tick 8.
    * Tick 9: Target is `(5, 10)`? Wait! Viewport left is `vp_left = 5`.
      * Viewport columns are `[5..24]`.
      * So `5` is inside the viewport!
      * Tick 9: Arrow moves to `(5, 10)` (inside).
      * Tick 10: Target is `(4, 10)`. Since `4 < 5` (out of viewport), arrow destroyed (`arrow_dir[0] = -1`).
  * *HAL*: Arrow sprite active on ticks 0..9, inactive on tick 10.

#### 21. `test_f05_arrow_off_viewport_right`
* **Setup**: Clean map. Player 0 at `(15, 10)`. Viewport right is `vp_left + 20 = 25`.
* **Input**: Face Right and press `BUTTON_FIRE`. Step empty inputs.
* **Assertions**:
  * *Globals*:
    * Tick 0: Arrow moves to `(16, 10)`.
    * Ticks 1..8: Arrow moves to `(24, 10)` on Tick 8.
    * Tick 9: Target is `(25, 10)`. Since `25 >= 25` (out of viewport), arrow destroyed (`arrow_dir[0] = -1`).
  * *HAL*: Arrow sprite active on ticks 0..8, inactive on tick 9.

#### 22. `test_f05_arrow_diagonal_flight_corridors`
* **Setup**: Clean map. Player 0 at `(10, 10)`. Place walls at `(11, 10)` (Right) and `(10, 9)` (Up). Space at `(11, 9)` (Up-Right).
* **Input**: Face Up-Right and press `BUTTON_FIRE`.
* **Assertions**:
  * *Globals*:
    * Target is `(11, 9)` (space).
    * Arrow successfully flies through the diagonal gap between the two walls to `(11, 9)`.
    * `arrow_dir[0] = 1`. Map tile at `(11, 9)` is arrow.
  * *HAL*: Plays `SOUND_SHOOT`. Arrow sprite registered at `(11, 9)`.

#### 23. `test_f05_arrow_boundary_clamp_hits`
* **Setup**: Clean map. Player 0 at `x = 0, y = 5`. Viewport is clamped to `vp_left = 0`.
* **Input**: Face Left and press `BUTTON_FIRE`.
* **Assertions**:
  * *Globals*:
    * Target: `nx = clamp(0-1, 0, 59) = 0`.
    * `new_pos` is `(0, 5)`, which is the Player's own tile!
    * Since Player tile is not a destructible, the arrow hits a solid and is destroyed immediately in the same tick.
    * `arrow_dir[0] = -1`. Player remains intact.
  * *HAL*: `SOUND_SHOOT` played, no `SOUND_HIT`. No arrow sprite ever registered.

#### 24. `test_f05_arrow_destructible_outside_viewport`
* **Setup**: Clean map. Player 0 at `(15, 10)`. Viewport top is `vp_top = 5`. Place Monster 1 at `(15, 4)` (just outside viewport).
* **Input**: Face Up and press `BUTTON_FIRE`. Step empty inputs.
* **Assertions**:
  * *Globals*:
    * Tick 0..4: Arrow moves up.
    * Tick 5: Target is `(15, 4)`. Viewport check triggers first (`4 < 5`), so arrow is destroyed.
    * Monster 1 at `(15, 4)` remains completely intact (not degraded or killed).
  * *HAL*: `SOUND_SHOOT` played. No `SOUND_HIT`. Monster remains on map.

#### 25. `test_f05_arrow_max_concurrency`
* **Setup**: Clean map. Join all 4 players: Player 0 at `(10, 10)`, Player 1 at `(20, 10)`, Player 2 at `(10, 20)`, Player 3 at `(20, 20)`.
* **Input**: Press `BUTTON_FIRE` for all 4 players in the same tick.
* **Assertions**:
  * *Globals*: All 4 players have active arrows: `arrow_dir[0..3] != -1`. Arrow coordinates match their respective spawn trajectories.
  * *HAL*: `mock_get_sound_count()` is 4 (four `SOUND_SHOOT` plays). All 4 arrows rendered in viewport drawing.

---

### F-06: Smart Bomb Action (4 Tests)

#### 26. `test_f06_smart_bomb_no_entities`
* **Setup**: Clean map. Player 0 at `(10, 10)` with 1 bomb. Viewport is empty of monsters/generators.
* **Input**: Press `BUTTON_BOMB`.
* **Assertions**:
  * *Globals*: `player_bombs[0]` becomes `0`. Map is completely unchanged.
  * *HAL*: Plays `SOUND_BOMB`.

#### 27. `test_f06_smart_bomb_viewport_edge_clearing`
* **Setup**: Clean map. Player 0 at `(10, 10)`. Viewport is `[0..19, 5..14]`. Place Monster 1 at the 4 edges of the viewport: `(0, 5)`, `(19, 5)`, `(0, 14)`, `(19, 14)`. Player 0 has 1 bomb.
* **Input**: Press `BUTTON_BOMB`.
* **Assertions**:
  * *Globals*: `player_bombs[0]` = 0. All 4 edge monsters are cleared to `TILE_SPACE`.
  * *HAL*: Plays `SOUND_BOMB`. Viewport draws space at all 4 locations.

#### 28. `test_f06_smart_bomb_off_viewport_immunity`
* **Setup**: Clean map. Player 0 at `(10, 10)`. Viewport is `[0..19, 5..14]`. Place Monster 1 just outside the edges: `(20, 10)` (Right) and `(10, 4)` (Top). Player 0 has 1 bomb.
* **Input**: Press `BUTTON_BOMB`.
* **Assertions**:
  * *Globals*: Both off-screen monsters remain intact. `player_bombs[0]` = 0.
  * *HAL*: Plays `SOUND_BOMB`.

#### 29. `test_f06_smart_bomb_clamped_viewport`
* **Setup**: Clean map. Player 0 at `(0, 0)` (clamped viewport `[0..19, 0..9]`). Place Monster 1 at `(10, 5)` (inside clamped viewport) and `(10, 10)` (outside clamped viewport). Player 0 has 1 bomb.
* **Input**: Press `BUTTON_BOMB`.
* **Assertions**:
  * *Globals*: Monster at `(10, 5)` is cleared. Monster at `(10, 10)` remains intact.
  * *HAL*: Plays `SOUND_BOMB`.

---

### F-07: Monster Behavior (7 Tests)

#### 30. `test_f07_monster_rotor_ticks_exactly`
* **Setup**: Clean map. Player 0 at `(10, 10)`. Place Monster 1 at `(9, 8)`.
  * Rotor index calculation: `mx = 9, my = 8`.
  * `rotor_index = (8 % 4) * 4 + (9 % 4) = 0 * 4 + 1 = 1`.
* **Input**: Step 16 times with empty inputs (`0`).
* **Assertions**:
  * *Globals*:
    * Step 1: `monster_rotor` becomes 1. Monster ticks and moves towards player (moves to `(10, 9)` or similar).
    * Steps 2..16: Monster does NOT move on any other steps because `monster_rotor != 1`.
  * *HAL*: Sprite coordinates updated on Step 1, remain identical on Steps 2..16.

#### 31. `test_f07_monster_off_viewport_freeze`
* **Setup**: Clean map. Player 0 at `(10, 10)`. Viewport is `[0..19, 5..14]`. Place Monster 1 at `(21, 8)` (off-screen).
  * Rotor index: `(8 % 4) * 4 + (21 % 4) = 1`.
* **Input**: Step 1 time (rotor becomes 1).
* **Assertions**:
  * *Globals*: Monster at `(21, 8)` does NOT move (remains frozen because it is off-viewport).
  * *HAL*: Sprite is not registered.

#### 32. `test_f07_monster_pathfinding_blocked_all`
* **Setup**: Clean map. Player 0 at `(10, 10)`. Place Monster 1 at `(9, 8)` (rotor index 1). Surround `(9, 8)` with 8 walls.
* **Input**: Step 1 time.
* **Assertions**:
  * *Globals*: Monster remains at `(9, 8)` (blocked in all directions). No crash or memory corruption.
  * *HAL*: Monster sprite remains at `(9, 8)`.

#### 33. `test_f07_monster_pathfinding_slide`
* **Setup**: Clean map. Player 0 at `(10, 10)`. Place Monster 1 at `(9, 10)` (rotor index 9). Block `(10, 10)` from `(9, 10)`?
  * Wait! The player is at `(10, 10)`. The monster is at `(9, 10)`.
  * The primary direction for monster is Right (`dir = 2`).
  * Let's block `(10, 10)` (player is there, but monster contact is solid, so it would attack player).
  * What if we want to test monster sliding around an obstacle?
  * Place Monster 1 at `(8, 10)` (rotor index: `(10%4)*4 + (8%4) = 8`).
  * Player at `(11, 10)`.
  * Place a Wall at `(9, 10)` (Right, primary path).
  * Place a Wall at `(9, 9)` (Up-Right, clockwise slide path).
  * Space is free at `(9, 11)` (Down-Right, counter-clockwise slide path).
* **Input**: Step 8 times to tick the monster.
* **Assertions**:
  * *Globals*:
    * Primary path `(9, 10)` is Wall (blocked).
    * Clockwise `(9, 9)` is Wall (blocked).
    * Counter-clockwise `(9, 11)` is Space (free).
    * Monster slides to `(9, 11)`.
  * *HAL*: Monster sprite drawn at `(9, 11)`.

#### 34. `test_f07_monster_boundary_chasing`
* **Setup**: Clean map. Player 0 at `(0, 0)`. Place Monster 1 at `(1, 1)` (rotor index: `(1%4)*4 + (1%4) = 5`).
* **Input**: Step 5 times.
* **Assertions**:
  * *Globals*: Monster tracks player and moves to `(0, 0)`, attacking Player 0. Player 0 health reduces by 10. Monster removed.
  * *HAL*: Plays `SOUND_HIT`.

#### 35. `test_f07_monster_damage_player_lethal`
* **Setup**: Clean map. Player 0 at `(10, 10)` with `10` HP. Join Player 1 at `(1, 1)` to keep game running. Place Monster 1 at `(9, 10)` (rotor index 9).
* **Input**: Step 9 times.
* **Assertions**:
  * *Globals*: Player 0 HP becomes `0` (dead). Player 0 tile at `(10, 10)` is replaced by `TILE_SPACE` immediately. Monster at `(9, 10)` is removed.
  * *HAL*: Plays `SOUND_DIE` (lethal attack). Player 0 sprite is deactivated.

#### 36. `test_f07_monster_concurrent_player_damage`
* **Setup**: Clean map. Player 0 at `(10, 10)`. Player 1 at `(20, 10)`. Place Monster 1 adjacent to Player 0 at `(9, 10)` (rotor index 9) and Monster 1 adjacent to Player 1 at `(19, 10)` (rotor index 9).
* **Input**: Step 9 times.
* **Assertions**:
  * *Globals*: Both players receive 10 damage. Both monsters removed.
  * *HAL*: Plays `SOUND_HIT` exactly twice.

---

### F-08: Generator Spawning (4 Tests)

#### 37. `test_f08_generator_off_viewport_freeze`
* **Setup**: Clean map. Player 0 at `(10, 10)`. Viewport is `[0..19, 5..14]`. Place Generator 1 at `(21, 8)` (off-screen, rotor index 1).
* **Input**: Step 1 time.
* **Assertions**:
  * *Globals*: No monster is spawned around `(21, 8)`. The global random seed is NOT ticked/updated by this generator.
  * *HAL*: No new sprites.

#### 38. `test_f08_generator_rotor_tick`
* **Setup**: Clean map. Player 0 at `(10, 10)`. Place Generator 1 at `(9, 8)` (rotor index 1).
* **Input**: Step 16 times with empty inputs.
* **Assertions**:
  * *Globals*: Generator only attempts to spawn on Step 1 (when `monster_rotor == 1`). On Steps 2..16, it does not spawn or tick.
  * *HAL*: Spawned monster sprite appears on Step 1, moves on its own rotor tick later.

#### 39. `test_f08_generator_spawn_all_dirs_blocked`
* **Setup**: Clean map. Player 0 at `(10, 10)`. Place Generator 1 at `(9, 8)` (rotor index 1). Surround it with 4 walls at cardinal directions: `(9, 7)` (Up), `(10, 8)` (Right), `(9, 9)` (Down), `(8, 8)` (Left).
* **Input**: Step 1 time.
* **Assertions**:
  * *Globals*: No monster spawned. Generator intact. No crash.
  * *HAL*: Viewport drawn correctly.

#### 40. `test_f08_generator_spawn_levels`
* **Setup**: Clean map. Place Generator 2 at `(9, 8)` (rotor index 1).
* **Input**: Step 1 time.
* **Assertions**:
  * *Globals*: Generator 2 spawns Monster 2 (`TILE_MONSTER2`) at `(9, 7)`.
  * *HAL*: Level 2 monster sprite registered.

---

### F-09: Multiplayer & Viewport (4 Tests)

#### 41. `test_f09_multiplayer_join_max_limit`
* **Setup**: Join Players 0, 1, 2, 3.
* **Input**: Call `dandy_join_player(4)` (5th player index).
* **Assertions**:
  * *Globals*: Call is ignored. `player_joined` array has only 4 elements. No memory corruption.
  * *HAL*: HUD updates only show 4 players.

#### 42. `test_f09_camera_viewport_clamping_all_corners`
* **Setup**: Clean map.
* **Input / Actions**:
  * Move Player 0 to `(0, 0)` -> Draw -> Assert camera scroll clamped to `(0, 0)`.
  * Move Player 0 to `(59, 0)` -> Draw -> Assert camera scroll clamped to `(40, 0)`.
  * Move Player 0 to `(0, 29)` -> Draw -> Assert camera scroll clamped to `(0, 20)`.
  * Move Player 0 to `(59, 29)` -> Draw -> Assert camera scroll clamped to `(40, 20)`.
* **Assertions**:
  * *HAL*: Camera scroll values match expected clamped boundaries exactly.

#### 43. `test_f09_spectator_mode_no_alive_players`
* **Setup**: Join Players 0 and 1. Player 0 at `(10, 10)`, Player 1 at `(20, 20)`. Set both players' health to `0` (all dead).
* **Input**: Draw viewport for Player 0.
* **Assertions**:
  * *Globals*: `alive_count` is 0.
  * *HAL*: Camera scroll target defaults to Player 0's last coordinates `(10, 10)`, so camera scroll is `(0, 5)`.

#### 44. `test_f09_viewport_hardware_sprite_limit`
* **Setup**: Clean map. Player 0 at `(10, 10)` (viewport `[0..19, 5..14]`). Place 50 Monster 1 tiles inside this viewport.
* **Input**: Draw viewport.
* **Assertions**:
  * *Globals*: Map contains 50 monsters.
  * *HAL*: `hal_set_sprite` is called exactly 40 times (sprite count clamped to 40). The remaining 10 monsters are drawn as background space tiles instead of hardware sprites, avoiding OAM overflow.

---

### F-10: Level Transitions (3 Tests)

#### 45. `test_f10_stairs_next_level_max_boundary`
* **Setup**: Player 0 at `(10, 10)`. Set `current_level = 25` (maximum level). Place `TILE_DOWN` at `(11, 10)`.
* **Input**: Step Right (`BUTTON_RIGHT`).
* **Assertions**:
  * *Globals*: `current_level` remains `25` (clamped). Map reloaded to Level 25. Coordinates warped to portal.
  * *HAL*: Plays `SOUND_WARP`.

#### 46. `test_f10_load_level_clean_state_reset`
* **Setup**: Player 0 has high stats: score = 500, keys = 5, bombs = 3, health = 200. Fired arrow is active (`arrow_dir = 2`).
* **Input**: Call `dandy_load_level(1)`.
* **Assertions**:
  * *Globals*:
    * Player coordinates reset to Level 1 portal.
    * Player stats (health, keys, bombs, score) are PRESERVED (load_level does not wipe player stats!).
    * Fired arrow is destroyed: `arrow_dir[0]` becomes `-1`.
  * *HAL*: No warp sound played. Viewport updated.

#### 47. `test_f10_game_over_clears_joined_players_state`
* **Setup**: Join Players 0, 1, 2. Set all healths to `0`.
* **Input**: Step 1 time to trigger game over.
* **Assertions**:
  * *Globals*:
    * Game resets to Level 0: `current_level` = 0.
    * Player 0 is joined and reset to 100 HP.
    * Players 1 and 2 are set to UNJOINED (`player_joined[1] = false`, `player_joined[2] = false`).
  * *HAL*: Viewport centered on Player 0 Level 0 portal.

---

## 3. Tier 3: Cross-Feature Interactions (16 Tests)

### F-05 Combat & F-06 Smart Bomb (2 Tests)

#### 48. `test_f03_arrow_triggers_smart_bomb_on_bomb_tile`
* **Setup**: Clean map. Player 0 at `(10, 10)`. Place `TILE_BOMB` at `(12, 10)`. Place Monster 1 at `(15, 10)` (inside viewport). Player has 0 bombs in inventory.
* **Input**: Face Right, press `BUTTON_FIRE`. Step empty inputs.
* **Assertions**:
  * *Globals*:
    * Tick 0: Arrow spawned, moves to `(11, 10)`.
    * Tick 1: Arrow moves to `(12, 10)`, hits `TILE_BOMB`.
      * Triggers `do_bomb()`, which clears all monsters in viewport.
      * Monster 1 at `(15, 10)` is cleared to `TILE_SPACE`.
      * Bomb tile at `(12, 10)` is cleared to `TILE_SPACE`.
      * Player inventory bombs remain `0`.
      * Arrow is destroyed: `arrow_dir[0] = -1`.
  * *HAL*: Plays `SOUND_SHOOT` (Tick 0) and `SOUND_HIT` (Tick 1). `SOUND_BOMB` is NOT played.

#### 49. `test_f03_arrow_strikes_bomb_outside_viewport`
* **Setup**: Clean map. Player 0 at `(10, 10)`. Viewport is `[0..19, 5..14]`. Place `TILE_BOMB` at `(20, 10)` (just outside viewport). Place Monster 1 at `(22, 10)` (outside) and Monster 1 at `(15, 10)` (inside).
* **Input**: Face Right, press `BUTTON_FIRE`. Step empty inputs.
* **Assertions**:
  * *Globals*:
    * Arrow travels Right.
    * On the tick it reaches `(20, 10)`, the viewport boundary check triggers *before* the hit, destroying the arrow.
    * `TILE_BOMB` at `(20, 10)` is NOT triggered.
    * Monsters at `(15, 10)` and `(22, 10)` remain intact.
  * *HAL*: No hit sound.

---

### F-05 Combat & F-07 Monster Behavior (4 Tests)

#### 50. `test_f05_arrow_hits_moving_monster_head_on`
* **Setup**: Clean map. Player 0 at `(10, 10)`. Place Monster 1 at `(12, 10)` (rotor index 8).
* **Input**:
  * Tick 0: Player shoots Right.
    * `do_player_buttons` spawns arrow.
    * `move_arrows` moves arrow to `(11, 10)`.
    * `move_monsters` ticks. Monster 1 at `(12, 10)` wants to move to `(11, 10)`. Since `(11, 10)` contains the arrow tile, the monster is blocked and stays at `(12, 10)`.
  * Tick 1: Empty step.
    * `move_arrows` moves arrow to `(12, 10)`. It hits the monster, destroys the monster, and arrow dies.
* **Assertions**:
  * *Globals*: Monster 1 replaced by `TILE_SPACE`. Arrow destroyed.
  * *HAL*: Plays `SOUND_SHOOT` and `SOUND_HIT`.

#### 51. `test_f05_monster_attacks_player_on_firing_tick`
* **Setup**: Clean map. Player 0 at `(10, 10)` with 10 HP. Place Monster 1 at `(11, 10)` (rotor index 0).
* **Input**: Press `BUTTON_FIRE` (facing Right).
* **Assertions**:
  * *Globals*:
    * `do_player_buttons` spawns arrow at `(10, 10)`, sets `arrow_dir = 2`.
    * `move_arrows` moves arrow to `(11, 10)`. It hits Monster 1 at `(11, 10)`.
      * Monster 1 is destroyed immediately!
      * Arrow is destroyed.
    * `move_monsters` runs. Monster 1 is already dead, so it cannot attack Player 0!
    * Player 0 survives with 10 HP!
  * *HAL*: Plays `SOUND_SHOOT` and `SOUND_HIT`. `SOUND_DIE` is NOT played.

#### 52. `test_f05_arrow_hits_monster_attacking_another_player`
* **Setup**: Join Player 0 at `(10, 10)` and Player 1 at `(12, 10)`. Place Monster 1 at `(13, 10)` (rotor index 9).
* **Input**: Player 0 shoots Right. Step 9 times to trigger monster attack.
* **Assertions**:
  * *Globals*:
    * Arrow flies Right, hits Monster 1 at `(13, 10)` before the 9th step.
    * Monster 1 is killed.
    * Player 1 is saved (receives 0 damage on Step 9).
  * *HAL*: Plays `SOUND_SHOOT` and `SOUND_HIT`.

#### 53. `test_f05_arrow_flight_through_portal`
* **Setup**: Clean map. Place `TILE_UP` (portal) at `(12, 10)`. Player 0 at `(10, 10)`.
* **Input**: Shoot Right.
* **Assertions**:
  * *Globals*: Arrow flies through `TILE_UP` at `(12, 10)`?
    * Wait! Is `TILE_UP` a solid for arrows?
    * In `move_arrows()`: `if (tile_at_new != TILE_SPACE) { arrow_dir = -1; ... }`.
    * Since `TILE_UP` is not `TILE_SPACE`, the arrow hits it and is destroyed!
    * Let's verify this! The portal acts as a solid blocker for projectiles.
  * *HAL*: Arrow destroyed, no hit sound (since `TILE_UP` is not in the destructible range `[TILE_BOMB, TILE_ARROW - 1]`).

---

### F-03 Item Collection & F-07 Monster Behavior (2 Tests)

#### 54. `test_f03_monster_attacks_player_collecting_food`
* **Setup**: Clean map. Player 0 at `(10, 10)` with 10 HP. Place `TILE_FOOD` at `(11, 10)`. Place Monster 1 at `(12, 10)` (rotor index 9).
* **Input**:
  * Step 9: Player 0 steps Right (`BUTTON_RIGHT`) into food.
* **Assertions**:
  * *Globals*:
    * `do_player_buttons` moves Player 0 to `(11, 10)`. HP becomes `10 + 100 = 110`.
    * `move_monsters` ticks Monster 1.
      * Monster 1 targets Player at `(11, 10)`.
      * Monster moves to `(11, 10)`, attacks Player.
      * Deals 10 damage. Player HP becomes `110 - 10 = 100`.
      * Monster removed. Player survives!
  * *HAL*: Plays `SOUND_FOOD` (player moving) and `SOUND_HIT` (monster attack). Player remains alive at `(11, 10)`.

#### 55. `test_f03_monster_steals_food`
* **Setup**: Clean map. Place `TILE_FOOD` at `(11, 10)`. Place Monster 1 at `(12, 10)` (rotor index 9). Player 0 at `(5, 10)`.
* **Input**: Step 9 times.
* **Assertions**:
  * *Globals*:
    * Monster 1 moves towards player. Its path goes through `(11, 10)` (Food).
    * Can monster move onto Food?
      * In `move_monsters()`: monster can only move if `n_tile == TILE_SPACE` or `IS_PLAYER(n_tile)`.
      * Since `TILE_FOOD` is neither, the monster is blocked by the Food tile and cannot pass!
      * Verify that the monster is blocked and does NOT destroy or collect the Food!
  * *HAL*: Food tile remains drawn on map.

---

### F-04 Door Mechanics & F-07 Monster Behavior (2 Tests)

#### 56. `test_f04_monster_blocked_by_door`
* **Setup**: Clean map. Player 0 at `(10, 10)`. Place `TILE_DOOR` at `(11, 10)`. Place Monster 1 at `(12, 10)` (rotor index 9).
* **Input**: Step 9 times.
* **Assertions**:
  * *Globals*: Monster wants to chase player but is blocked by `TILE_DOOR`. Monster remains at `(12, 10)`.
  * *HAL*: Monster sprite remains at `(12, 10)`.

#### 57. `test_f04_monster_pathfinds_through_unlocked_door`
* **Setup**: Clean map. Player 0 at `(10, 10)` with 1 key. Place `TILE_DOOR` at `(11, 10)`. Place Monster 1 at `(12, 10)` (rotor index 9).
* **Input**:
  * Step 1: Player moves Right, unlocking the door (player at 11, 10, door cleared).
  * Wait for Step 9: Monster ticks.
* **Assertions**:
  * *Globals*:
    * On Step 9, the door is gone. Monster successfully moves to `(11, 10)`, attacking Player 0.
  * *HAL*: Plays `SOUND_KEY` (Step 1) and `SOUND_HIT` (Step 9).

---

### F-07 Monster Behavior & F-08 Generator Spawning (2 Tests)

#### 58. `test_f07_generator_spawn_blocked_by_monster`
* **Setup**: Clean map. Place Generator 1 at `(9, 8)` (rotor index 1). Place Monster 1 at `(9, 7)` (Up, primary spawn direction).
  * Generator seed tick 1: LFSR chooses Up (blocked). It tries clockwise search: Right `(10, 8)`.
  * Let's block all 4 cardinal directions around generator with Monster 1: `(9, 7)`, `(10, 8)`, `(9, 9)`, `(8, 8)`.
* **Input**: Step 1 time.
* **Assertions**:
  * *Globals*: Generator unable to spawn. No monsters overwritten. All monsters and generator remain intact.
  * *HAL*: Map drawn correctly.

#### 59. `test_f07_monster_blocks_generator_spawning_line`
* **Setup**: Place Generator 1 at `(9, 8)` (rotor index 1). Place Monster 1 at `(9, 7)` (Up, primary). Right `(10, 8)` is free.
* **Input**: Step 1 time.
* **Assertions**:
  * *Globals*: Generator spawns Monster 1 at the next free clockwise direction: `(10, 8)`.
  * *HAL*: Monster sprite registered at `(10, 8)`.

---

### F-09 Multiplayer & F-07 Monster Behavior (2 Tests)

#### 60. `test_f09_monster_chases_nearest_player_dynamic_switch`
* **Setup**: Clean map. Join Players 0 and 1. Player 0 at `(10, 10)`. Player 1 at `(20, 10)`. Place Monster 1 at `(12, 10)` (rotor index 8).
  * Distance to P0 is 2. Distance to P1 is 8.
* **Input**:
  * Step 8: Monster ticks. It moves Left towards P0 (moves to 11, 10).
  * Now, programmatically teleport Player 0 to `(30, 10)`.
    * Distance to P0 is now 19. Distance to P1 is 8.
  * Step 24 (next monster tick): Monster ticks.
* **Assertions**:
  * *Globals*: On Step 24, the monster dynamically targets Player 1 (now the nearest) and moves Right (back to 12, 10).
  * *HAL*: Monster sprite moves Left, then moves Right.

#### 61. `test_f09_monster_rotor_ticks_when_visible_to_any_player`
* **Setup**: Join Players 0 and 1. Player 0 at `(10, 10)` (viewport `[0..19, 5..14]`). Player 1 at `(40, 10)` (viewport `[30..49, 5..14]`).
  * Place Monster 1 at `(35, 10)` (invisible to Player 0, but visible to Player 1).
  * Rotor index: `(10%4)*4 + (35%4) = 11`.
* **Input**: Step 11 times.
* **Assertions**:
  * *Globals*: Since Monster is visible to Player 1, it is NOT frozen! It ticks on Step 11 and moves towards Player 1.
  * *HAL*: Monster sprite moves.

---

### F-09 Multiplayer & F-10 Level Transitions (2 Tests)

#### 62. `test_f09_multiplayer_level_transition`
* **Setup**: Join Players 0, 1, 2. Player 0 at `(10, 10)`. Player 1 at `(11, 10)`. Player 2 at `(10, 11)`. Place `TILE_DOWN` at `(10, 9)` (adjacent to P0).
* **Input**: Player 0 steps Up (`BUTTON_UP`) into stairs.
* **Assertions**:
  * *Globals*:
    * Game advances: `current_level` becomes `1`.
    * All 3 players are warped to Level 1 starting portal offsets:
      * Player 0: `(up_x, up_y - 1)`
      * Player 1: `(up_x + 1, up_y)`
      * Player 2: `(up_x, up_y + 1)`
    * All players' healths/stats are preserved.
  * *HAL*: Plays `SOUND_WARP`.

#### 63. `test_f05_arrow_destroyed_on_level_transition`
* **Setup**: Player 0 at `(10, 10)`. Place `TILE_DOWN` at `(11, 10)`.
* **Input**:
  * Tick 0: Press `BUTTON_FIRE` (fires arrow Right, arrow moves to 11, 10, which is the stairs tile. Wait! Stairs tile is not space, so arrow would hit it and die immediately.
    * Let's place stairs at `(12, 10)`.
    * Tick 0: Shoot Right (arrow moves to 11, 10).
    * Tick 1: Player moves Right (player at 11, 10, arrow moves to 12, 10. Wait! Arrow hits stairs and dies!).
    * Let's change the setup:
      * Player at `(10, 10)`. Stairs at `(10, 11)` (Down).
      * Tick 0: Shoot Right (arrow moves to 11, 10). Player steps Down into stairs.
* **Assertions**:
  * *Globals*:
    * Step 0 triggers level transition (Player steps on stairs).
    * Next level is loaded.
    * Player 0's arrow is destroyed: `arrow_dir[0]` becomes `-1`.
    * Arrow does not carry over or affect the new level map.
  * *HAL*: Plays `SOUND_WARP`.
