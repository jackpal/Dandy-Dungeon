# Dandy Dungeon E2E Test Suite Design: Tier 2 & Tier 3

This document presents a comprehensive test suite design for Milestone 3 of the Dandy Dungeon E2E Testing Track. It specifies **44 Tier 2 (Boundary & Corner Cases)** and **8 Tier 3 (Cross-Feature Interactions)** test cases. 

All test cases are designed to run headlessly in the `libdandy_test.so` shared library harness, programmatic controlled via the `dandy_env.py` Python wrapper, and strictly adhere to the **Double-Assert Rule** (asserting on both C engine globals and mock HAL side-effects).

---

## 1. Core Engine Order of Operations (Context)
To design precise tick-aligned tests, we must understand the exact sequence of events executed in `dandy_step` during a single tick:
1. **Player Inputs**: Processed for each joined, alive player in index order ($0 \dots 3$).
   - Firing arrows is level-triggered (spawns an arrow at the player's current tile).
   - Smart bombs are edge-triggered (instantly clears all monsters/generators in the player's viewport).
   - Movement is processed. If the movement timer is $0$, the player attempts to move in their input direction, sliding clockwise/counter-clockwise if blocked. The move timer is set to $4$ ticks.
2. **Arrow Movement**: Active arrows travel $1$ tile in their direction. Viewport exits, solid obstacle hits, and target hits (monsters, generators, bombs, hearts) are resolved.
3. **Monster & Generator Updates**: Executed on a sparse grid according to the 16-tick `monster_rotor`. Visible entities tick; off-screen entities are frozen.
   - Monsters pathfind towards the nearest active player, sliding around obstacles, and deal damage on contact.
   - Generators run their LFSR seed to deterministically decide whether and where to spawn a monster.
4. **HUD & State Updates**: HUD is redrawn via `hal_update_hud()`.
5. **Game Over Check**: If all players are dead, the game is reset to Level 0.

---

## 2. Tier 2: Boundary & Corner Cases (44 Tests)

### F-01: Movement & Timing (7 Tests)

#### Test 2.1: `test_f01_boundary_left`
- **Feature**: F-01 Movement & Timing
- **Description**: Verifies that a player at the extreme left edge of the map cannot move further left and is clamped.
- **Setup**: Clean map, Player 0 at $(0, 10)$, facing Left (direction 6).
- **Input**: Step with `[BUTTON_LEFT, 0, 0, 0]`.
- **Expected Assertions**:
  - **Globals**: Player coordinates remain $(0, 10)$. Direction is 6. Move timer is set to 3. Map tile at $(0, 10)$ remains Player 0 facing Left.
  - **Mock HAL**: `get_camera()` returns $(0, 5)$ (clamped to map left edge). `get_sounds()` contains no sounds.

#### Test 2.2: `test_f01_boundary_right`
- **Feature**: F-01 Movement & Timing
- **Description**: Verifies that a player at the extreme right edge of the map cannot move further right.
- **Setup**: Clean map, Player 0 at $(59, 10)$, facing Right (direction 2).
- **Input**: Step with `[BUTTON_RIGHT, 0, 0, 0]`.
- **Expected Assertions**:
  - **Globals**: Player coordinates remain $(59, 10)$. Move timer is 3. Map tile at $(59, 10)$ remains Player facing Right.
  - **Mock HAL**: `get_camera()` returns $(40, 5)$ (clamped to map right edge).

#### Test 2.3: `test_f01_boundary_top`
- **Feature**: F-01 Movement & Timing
- **Description**: Verifies that a player at the extreme top edge of the map cannot move further up.
- **Setup**: Clean map, Player 0 at $(10, 0)$, facing Up (direction 0).
- **Input**: Step with `[BUTTON_UP, 0, 0, 0]`.
- **Expected Assertions**:
  - **Globals**: Player coordinates remain $(10, 0)$. Move timer is 3.
  - **Mock HAL**: `get_camera()` returns $(0, 0)$ (clamped to map top edge).

#### Test 2.4: `test_f01_boundary_bottom`
- **Feature**: F-01 Movement & Timing
- **Description**: Verifies that a player at the extreme bottom edge of the map cannot move further down.
- **Setup**: Clean map, Player 0 at $(10, 29)$, facing Down (direction 4).
- **Input**: Step with `[BUTTON_DOWN, 0, 0, 0]`.
- **Expected Assertions**:
  - **Globals**: Player coordinates remain $(10, 29)$. Move timer is 3.
  - **Mock HAL**: `get_camera()` returns $(0, 20)$ (clamped to map bottom edge).

#### Test 2.5: `test_f01_invalid_input_horizontal_conflict`
- **Feature**: F-01 Movement & Timing
- **Description**: Verifies that pressing contradictory horizontal buttons results in no movement and no cooldown activation.
- **Setup**: Clean map, Player 0 at $(10, 10)$, facing Up (direction 0).
- **Input**: Step with `[BUTTON_LEFT | BUTTON_RIGHT, 0, 0, 0]`.
- **Expected Assertions**:
  - **Globals**: Player coordinates remain $(10, 10)$. Player direction remains 0. Move timer remains 0 (no cooldown activated).
  - **Mock HAL**: No new sprites or camera updates.

#### Test 2.6: `test_f01_invalid_input_vertical_conflict`
- **Feature**: F-01 Movement & Timing
- **Description**: Verifies that pressing contradictory vertical buttons results in no movement.
- **Setup**: Clean map, Player 0 at $(10, 10)$, facing Up (direction 0).
- **Input**: Step with `[BUTTON_UP | BUTTON_DOWN, 0, 0, 0]`.
- **Expected Assertions**:
  - **Globals**: Player coordinates remain $(10, 10)$. Move timer remains 0.

#### Test 2.7: `test_f01_blocked_movement_cooldown`
- **Feature**: F-01 Movement & Timing
- **Description**: Verifies the core rule that even when a move is completely blocked, the player move timer is still set to 4 ticks (applying a cooldown).
- **Setup**: Clean map. Player 0 at $(10, 10)$. Completely surround player with walls at $(10, 9)$, $(11, 9)$, $(11, 10)$, $(11, 11)$, $(10, 11)$, $(9, 11)$, $(9, 10)$, $(9, 9)$.
- **Input**: Step with `[BUTTON_RIGHT, 0, 0, 0]`.
- **Expected Assertions**:
  - **Globals**: Player coordinates remain $(10, 10)$. Move timer is set to 3 (4 minus 1 tick).
  - **Mock HAL**: Viewport drawing registers player at $(10, 10)$. No movement sounds.

---

### F-02: Slide Mechanics (5 Tests)

#### Test 2.8: `test_f02_slide_edge_top`
- **Feature**: F-02 Slide Mechanics
- **Description**: Verifies that a player at the top edge ($y=0$) blocked cardinally to the Right slides Down-Right because Up-Right is out of bounds.
- **Setup**: Clean map, Player 0 at $(10, 0)$. Wall placed at $(11, 0)$ (blocking Right). Up-Right $(11, -1)$ is out of bounds. Down-Right $(11, 1)$ is Space.
- **Input**: Step with `[BUTTON_RIGHT, 0, 0, 0]`.
- **Expected Assertions**:
  - **Globals**: Player coordinates become $(11, 1)$ (slid Down-Right). Player direction is 2 (Right, reflecting the input). Move timer is 3.
  - **Mock HAL**: Camera centered around $(11, 1)$. Sprite at $(11, 1)$ has player tile facing Right.

#### Test 2.9: `test_f02_slide_edge_left`
- **Feature**: F-02 Slide Mechanics
- **Description**: Verifies that a player at the left edge ($x=0$) blocked cardinally Up slides Up-Right because Up-Left is out of bounds.
- **Setup**: Clean map, Player 0 at $(0, 10)$. Wall at $(0, 9)$ (blocking Up). Up-Left $(-1, 9)$ is out of bounds. Up-Right $(1, 9)$ is Space.
- **Input**: Step with `[BUTTON_UP, 0, 0, 0]`.
- **Expected Assertions**:
  - **Globals**: Player coordinates become $(1, 9)$. Player direction is 0 (Up).
  - **Mock HAL**: Sprite at $(1, 9)$ has player tile facing Up.

#### Test 2.10: `test_f02_slide_blocked_by_monster`
- **Feature**: F-02 Slide Mechanics
- **Description**: Verifies that monsters act as solid obstacles, triggering the player's slide mechanics.
- **Setup**: Clean map, Player 0 at $(10, 10)$. Place `TILE_MONSTER1` at $(11, 10)$ (blocking Right). Place `TILE_WALL` at $(11, 9)$ (blocking Up-Right). Down-Right $(11, 11)$ is Space.
- **Input**: Step with `[BUTTON_RIGHT, 0, 0, 0]`.
- **Expected Assertions**:
  - **Globals**: Player coordinates become $(11, 11)$ (slid Down-Right). Monster remains at $(11, 10)$.
  - **Mock HAL**: Sprite rendered at $(11, 11)$ (player) and $(11, 10)$ (monster).

#### Test 2.11: `test_f02_slide_blocked_by_player`
- **Feature**: F-02 Slide Mechanics
- **Description**: Verifies that another joined player acts as a solid obstacle, triggering slide mechanics.
- **Setup**: Clean map, Player 0 at $(10, 10)$. Player 1 joined and positioned at $(11, 10)$. Wall at $(11, 9)$. Down-Right $(11, 11)$ is Space.
- **Input**: Step with `[BUTTON_RIGHT, 0, 0, 0]`.
- **Expected Assertions**:
  - **Globals**: Player 0 coordinates become $(11, 11)$. Player 1 remains at $(11, 10)$.
  - **Mock HAL**: Sprites registered for both players at their respective coordinates.

#### Test 2.12: `test_f02_slide_into_food`
- **Feature**: F-02 Slide Mechanics, F-03 Item Collection
- **Description**: Verifies that if a player slides into a tile containing an item, they successfully move and collect the item.
- **Setup**: Clean map, Player 0 at $(10, 10)$. Wall at $(11, 10)$ (blocking Right), wall at $(11, 9)$ (blocking Up-Right). Place `TILE_FOOD` at $(11, 11)$.
- **Input**: Step with `[BUTTON_RIGHT, 0, 0, 0]`.
- **Expected Assertions**:
  - **Globals**: Player coordinates become $(11, 11)$. Player health becomes 200. Tile at $(11, 11)$ becomes Player tile.
  - **Mock HAL**: `get_sounds()` contains `SOUND_FOOD`.

---

### F-03: Item Collection (6 Tests)

#### Test 2.13: `test_f03_health_overflow_death`
- **Feature**: F-03 Item Collection, F-10 Level Transitions
- **Description**: Verifies the extreme corner case where collecting food when health is near the signed 16-bit maximum ($32767$) causes an overflow into a negative value, triggering immediate player death and game reset to Level 0.
- **Setup**: Clean map, Player 0 at $(10, 10)$. Set Player 0 health directly to $32700$. Place `TILE_FOOD` at $(11, 10)$.
- **Input**: Step with `[BUTTON_RIGHT, 0, 0, 0]`.
- **Expected Assertions**:
  - **Globals**: Current level is reset to 0 (game over occurred). Player 0 health is reset to 100. Score, keys, and bombs are reset to 0. Player coordinates are reset to the Level 0 portal.
  - **Mock HAL**: `get_sounds()` contains `SOUND_FOOD` (from the collection step) followed by `SOUND_DIE` (from the death step).

#### Test 2.14: `test_f03_score_wrap_around`
- **Feature**: F-03 Item Collection
- **Description**: Verifies that player score (uint16_t) wraps around cleanly when exceeding $65535$.
- **Setup**: Clean map, Player 0 at $(10, 10)$. Set Player 0 score directly to $65500$. Place `TILE_MONEY` at $(11, 10)$.
- **Input**: Step with `[BUTTON_RIGHT, 0, 0, 0]`.
- **Expected Assertions**:
  - **Globals**: Player 0 score becomes $64$ ($65500 + 100 - 65536$). Player coordinates become $(11, 10)$.
  - **Mock HAL**: `get_sounds()` contains `SOUND_KEY`.

#### Test 2.15: `test_f03_keys_wrap_around`
- **Feature**: F-03 Item Collection
- **Description**: Verifies that player keys (uint8_t) wrap around cleanly when exceeding $255$.
- **Setup**: Clean map, Player 0 at $(10, 10)$. Set Player 0 keys directly to $255$. Place `TILE_KEY` at $(11, 10)$.
- **Input**: Step with `[BUTTON_RIGHT, 0, 0, 0]`.
- **Expected Assertions**:
  - **Globals**: Player 0 keys becomes $0$ ($255 + 1 - 256$).
  - **Mock HAL**: `get_sounds()` contains `SOUND_KEY`.

#### Test 2.16: `test_f03_bombs_wrap_around`
- **Feature**: F-03 Item Collection
- **Description**: Verifies that player bombs (uint8_t) wrap around cleanly when exceeding $255$.
- **Setup**: Clean map, Player 0 at $(10, 10)$. Set Player 0 bombs directly to $255$. Place `TILE_BOMB` at $(11, 10)$.
- **Input**: Step with `[BUTTON_RIGHT, 0, 0, 0]`.
- **Expected Assertions**:
  - **Globals**: Player 0 bombs becomes $0$.
  - **Mock HAL**: `get_sounds()` contains `SOUND_KEY`.

#### Test 2.17: `test_f03_collect_on_cooldown`
- **Feature**: F-03 Item Collection, F-01 Movement & Timing
- **Description**: Verifies that a player cannot collect an item if they try to step onto it while their movement timer is still cooling down ($>0$).
- **Setup**: Clean map, Player 0 at $(10, 10)$. Place `TILE_FOOD` at $(11, 10)$. Set Player 0 move timer directly to $2$.
- **Input**: Step with `[BUTTON_RIGHT, 0, 0, 0]`.
- **Expected Assertions**:
  - **Globals**: Player coordinates remain $(10, 10)$. Player health remains 100. Move timer decrements to 1. `TILE_FOOD` remains intact at $(11, 10)$.
  - **Mock HAL**: `get_sounds()` is empty.

#### Test 2.18: `test_f03_multiple_items_adjacent_ticks`
- **Feature**: F-03 Item Collection, F-01 Movement & Timing
- **Description**: Verifies that a player stepping onto multiple items over multiple ticks correctly updates their inventory and logs all sounds in chronological order.
- **Setup**: Clean map, Player 0 at $(10, 10)$. Place `TILE_FOOD` at $(11, 10)$ and `TILE_KEY` at $(12, 10)$.
- **Input**: 
  1. Step with `[BUTTON_RIGHT, 0, 0, 0]` (moves to 11,10, collects food, cooldown=3).
  2. Step 3 times with `[0, 0, 0, 0]` (cooldown decrements to 0).
  3. Step with `[BUTTON_RIGHT, 0, 0, 0]` (moves to 12,10, collects key).
- **Expected Assertions**:
  - **Globals**: Player coordinates are $(12, 10)$. Health is 200. Keys is 1.
  - **Mock HAL**: `get_sounds()` returns exactly `[SOUND_FOOD, SOUND_KEY]`.

---

### F-04: Door & Key Mechanics (5 Tests)

#### Test 2.19: `test_f04_door_circular_network`
- **Feature**: F-04 Door & Key Mechanics
- **Description**: Verifies that unlocking one door in a circular network of doors flood-fills and clears the entire loop, consuming exactly one key.
- **Setup**: Clean map. Player 0 at $(9, 10)$, keys = 1. Create a 2x2 loop of doors: $(10, 10)$, $(11, 10)$, $(11, 11)$, $(10, 11)$.
- **Input**: Step with `[BUTTON_RIGHT, 0, 0, 0]`.
- **Expected Assertions**:
  - **Globals**: Player at $(10, 10)$. Keys is 0. All 4 door tiles are cleared (turned to Space or Player tile).
  - **Mock HAL**: `get_sounds()` contains exactly one `SOUND_KEY`.

#### Test 2.20: `test_f04_door_map_edge`
- **Feature**: F-04 Door & Key Mechanics
- **Description**: Verifies that a door placed on the map edge is unlocked and flood-filled without causing out-of-bounds array access.
- **Setup**: Clean map. Player 0 at $(1, 10)$, keys = 1. Place `TILE_DOOR` at $(0, 10)$.
- **Input**: Step with `[BUTTON_LEFT, 0, 0, 0]`.
- **Expected Assertions**:
  - **Globals**: Player at $(0, 10)$. Keys is 0. Door tile is cleared.
  - **Mock HAL**: `get_sounds()` contains `SOUND_KEY`.

#### Test 2.21: `test_f04_door_massive_flood_stack_overflow`
- **Feature**: F-04 Door & Key Mechanics
- **Description**: Verifies the engine's hard-coded limitation where the non-recursive flood-fill stack has a capacity of exactly 64. If a network of doors exceeds this size, the flood fill must stop clearing tiles once the stack is full, leaving the rest intact.
- **Setup**: Clean map. Player 0 at $(9, 10)$, keys = 1. Create a 10x10 grid of doors from $x \in [10, 19]$ and $y \in [5, 14]$ (100 doors in total).
- **Input**: Step with `[BUTTON_RIGHT, 0, 0, 0]`.
- **Expected Assertions**:
  - **Globals**: Player at $(10, 10)$. Keys is 0. Exactly 64 door tiles are cleared (turned to Space/Player), and exactly 36 door tiles remain untouched in the grid.
  - **Mock HAL**: `get_sounds()` contains exactly one `SOUND_KEY`.

#### Test 2.22: `test_f04_door_unlock_with_multiple_keys`
- **Feature**: F-04 Door & Key Mechanics
- **Description**: Verifies that unlocking a door consumes only 1 key even if the player has multiple keys.
- **Setup**: Clean map, Player 0 at $(10, 10)$. Keys = 5. Place `TILE_DOOR` at $(11, 10)$.
- **Input**: Step with `[BUTTON_RIGHT, 0, 0, 0]`.
- **Expected Assertions**:
  - **Globals**: Player at $(11, 10)$. Keys becomes 4.
  - **Mock HAL**: `get_sounds()` contains `SOUND_KEY`.

#### Test 2.23: `test_f04_door_no_key_blocked_slide`
- **Feature**: F-04 Door & Key Mechanics, F-02 Slide Mechanics
- **Description**: Verifies that a player with 0 keys trying to move into a door with blocked slide directions remains completely stationary.
- **Setup**: Clean map, Player 0 at $(10, 10)$. Keys = 0. Place `TILE_DOOR` at $(11, 10)$. Place `TILE_WALL` at $(11, 9)$ and $(11, 11)$.
- **Input**: Step with `[BUTTON_RIGHT, 0, 0, 0]`.
- **Expected Assertions**:
  - **Globals**: Player remains at $(10, 10)$. Door remains intact. Keys remains 0. Move timer is set to 3.
  - **Mock HAL**: `get_sounds()` is empty.

---

### F-05: Combat & Projectiles (5 Tests)

#### Test 2.24: `test_f05_arrow_map_edge_collision`
- **Feature**: F-05 Combat & Projectiles
- **Description**: Verifies that an arrow fired near the map edge destroys itself on the next tick because clamping keeps its new position identical to its old position (so it collides with itself).
- **Setup**: Clean map, Player 0 at $(58, 10)$, facing Right. Fired arrow is at $(59, 10)$, direction is 2.
- **Input**: Step with `[0, 0, 0, 0]` (moves arrow).
- **Expected Assertions**:
  - **Globals**: Arrow is destroyed (`arrow_dir[0] == -1`). Tile at $(59, 10)$ becomes Space.
  - **Mock HAL**: `get_sounds()` contains no new sounds (no sound on edge destruction).

#### Test 2.25: `test_f05_arrow_viewport_exit`
- **Feature**: F-05 Combat & Projectiles
- **Description**: Verifies that an arrow is destroyed on the exact tick it exits the player's 10x20 viewport.
- **Setup**: Clean map, Player 0 at $(10, 10)$ (viewport left is 0). Active arrow is at $(0, 10)$, direction is 6 (Left).
- **Input**: Step with `[0, 0, 0, 0]`.
- **Expected Assertions**:
  - **Globals**: Arrow is destroyed (`arrow_dir[0] == -1`). Tile at $(0, 10)$ becomes Space.
  - **Mock HAL**: No new sprites registered for the arrow.

#### Test 2.26: `test_f05_arrow_collision_asymmetry`
- **Feature**: F-05 Combat & Projectiles, F-09 Multiplayer
- **Description**: Verifies that if two arrows occupy the same tile in the same tick, Player 0's arrow (processed first) survives, while Player 1's arrow (processed second) hits it and destroys itself.
- **Setup**: Clean map. Player 0 joined and at $(10, 10)$. Player 1 joined and at $(14, 10)$.
  - Player 0's arrow is at $(11, 10)$, direction is 2 (Right).
  - Player 1's arrow is at $(13, 10)$, direction is 6 (Left).
- **Input**: Step with `[0, 0, 0, 0]`.
- **Expected Assertions**:
  - **Globals**: Both arrows wanted to move to $(12, 10)$. Player 0's arrow is now active at $(12, 10)$. Player 1's arrow is destroyed (`arrow_dir[1] == -1`).
  - **Mock HAL**: Only Player 0's arrow sprite is drawn at $(12, 10)$.

#### Test 2.27: `test_f05_arrow_blocked_by_food`
- **Feature**: F-05 Combat & Projectiles, F-03 Item Collection
- **Description**: Verifies that items (e.g., food) block arrows and destroy them, but are not themselves destroyed or collected.
- **Setup**: Clean map, Player 0 at $(10, 10)$. Fired arrow at $(11, 10)$ moving Right. Place `TILE_FOOD` at $(12, 10)$.
- **Input**: Step with `[0, 0, 0, 0]`.
- **Expected Assertions**:
  - **Globals**: Arrow is destroyed (`arrow_dir[0] == -1`). `TILE_FOOD` remains intact at $(12, 10)$.
  - **Mock HAL**: `get_sounds()` contains no new sounds.

#### Test 2.28: `test_f05_arrow_degrade_monster3`
- **Feature**: F-05 Combat & Projectiles
- **Description**: Verifies that an arrow hitting a Level 3 monster degrades it to Level 2 and plays the hit sound.
- **Setup**: Clean map, Player 0 at $(10, 10)$. Fired arrow at $(11, 10)$ moving Right. Place `TILE_MONSTER3` at $(12, 10)$.
- **Input**: Step with `[0, 0, 0, 0]`.
- **Expected Assertions**:
  - **Globals**: Arrow is destroyed. Tile at $(12, 10)$ becomes `TILE_MONSTER2`.
  - **Mock HAL**: `get_sounds()` contains `SOUND_HIT`.

---

### F-06: Smart Bomb Action (3 Tests)

#### Test 2.29: `test_f06_bomb_viewport_clamp_left`
- **Feature**: F-06 Smart Bomb Action
- **Description**: Verifies that when the player viewport is clamped to the left edge of the map, a smart bomb only clears monsters inside this clamped viewport.
- **Setup**: Clean map. Player 0 at $(2, 10)$ (clamped viewport is columns $0 \dots 19$, rows $5 \dots 14$). Place `TILE_MONSTER1` at $(19, 10)$ (inside) and $(20, 10)$ (outside). Set Player 0 bombs to 1.
- **Input**: Step with `[BUTTON_BOMB, 0, 0, 0]`.
- **Expected Assertions**:
  - **Globals**: Monster at $(19, 10)$ is cleared. Monster at $(20, 10)$ remains intact.
  - **Mock HAL**: `get_sounds()` contains `SOUND_BOMB`.

#### Test 2.30: `test_f06_bomb_max_entities`
- **Feature**: F-06 Smart Bomb Action
- **Description**: Verifies that a smart bomb can clear a massive number of monsters (e.g. 190) in a single tick without crash and playing exactly one sound.
- **Setup**: Clean map, Player 0 at $(10, 10)$. Fill the entire $10\times20$ viewport with `TILE_MONSTER1` (except the player's tile). Set Player 0 bombs to 1.
- **Input**: Step with `[BUTTON_BOMB, 0, 0, 0]`.
- **Expected Assertions**:
  - **Globals**: All 190 monsters are cleared to Space. Bombs is 0.
  - **Mock HAL**: `get_sounds()` contains exactly one `SOUND_BOMB`.

#### Test 2.31: `test_f06_bomb_ignores_static_tiles`
- **Feature**: F-06 Smart Bomb Action
- **Description**: Verifies that smart bombs do not clear walls, doors, keys, or food.
- **Setup**: Clean map, Player 0 at $(10, 10)$. Viewport contains `TILE_WALL`, `TILE_DOOR`, `TILE_KEY`, `TILE_FOOD`. Bombs = 1.
- **Input**: Step with `[BUTTON_BOMB, 0, 0, 0]`.
- **Expected Assertions**:
  - **Globals**: All walls, doors, keys, and food tiles remain completely intact. Bombs is 0.

---

### F-07: Monster Behavior (4 Tests)

#### Test 2.32: `test_f07_monster_rotor_exact_ticks`
- **Feature**: F-07 Monster Behavior
- **Description**: Verifies that a monster at a specific coordinate only updates on its exact rotor tick ($rotor == (y \% 4) * 4 + (x \% 4)$) and remains frozen on all other 15 ticks.
- **Setup**: Clean map, Player 0 at $(10, 10)$. Place `TILE_MONSTER1` at $(9, 8)$.
  - **Calculation**: $my = 8$, $mx = 9$.
  - **Rotor Tick**: $(8 \% 4) * 4 + (9 \% 4) = 0 * 4 + 1 = 1$.
- **Input**: Step 16 times with no input `[0, 0, 0, 0]`.
- **Expected Assertions**:
  - **Globals**: The monster only moves (from $(9, 8)$ to $(10, 9)$) on the step where `monster_rotor` becomes 1. On all other 15 steps, its position remains unchanged.
  - **Mock HAL**: Viewport drawings show monster moving exactly once.

#### Test 2.33: `test_f07_monster_slide_around_wall`
- **Feature**: F-07 Monster Behavior, F-02 Slide Mechanics
- **Description**: Verifies that a monster pathfinding to a player slides around a wall using the slide search order.
- **Setup**: Clean map, Player 0 at $(10, 10)$. Place `TILE_MONSTER1` at $(10, 8)$ (wants to move Down). Place `TILE_WALL` at $(10, 9)$ (blocking Down). Place `TILE_WALL` at $(9, 9)$ (blocking Down-Left). Down-Right $(11, 9)$ is Space. Set rotor to tick the monster.
- **Input**: Step to trigger monster tick.
- **Expected Assertions**:
  - **Globals**: Monster slides Down-Right and moves to $(11, 9)$.
  - **Mock HAL**: Sprite registered at $(11, 9)$.

#### Test 2.34: `test_f07_monster_target_switching`
- **Feature**: F-07 Monster Behavior, F-09 Multiplayer
- **Description**: Verifies that a monster always targets the nearest active player and dynamically switches targets if the closest player dies.
- **Setup**: Clean map. Player 0 at $(10, 10)$ (health = 10). Player 1 at $(20, 10)$ (health = 100). Place `TILE_MONSTER1` at $(11, 10)$ (adjacent to Player 0).
- **Input**: 
  1. Step to let the monster attack Player 0 (kills Player 0, health = 0).
  2. Step to let the monster tick again.
- **Expected Assertions**:
  - **Globals**: Player 0 is dead (tile cleared from map). Monster is at $(12, 10)$, moving towards Player 1 at $(20, 10)$ (the new closest active player).
  - **Mock HAL**: `get_sounds()` contains `SOUND_DIE` (Player 0 death) and later `SOUND_HIT` or movement.

#### Test 2.35: `test_f07_monster_frozen_at_viewport_boundary`
- **Feature**: F-07 Monster Behavior
- **Description**: Verifies that a monster just 1 tile outside the player's viewport remains completely frozen (does not pathfind or move).
- **Setup**: Clean map, Player 0 at $(10, 10)$ (viewport right boundary is $x=19$). Place `TILE_MONSTER1` at $(20, 10)$ (rotor index 0).
- **Input**: Step with no input to trigger rotor tick 0.
- **Expected Assertions**:
  - **Globals**: Monster remains at $(20, 10)$ (frozen).
  - **Mock HAL**: Viewport drawing registers no monster sprite.

---

### F-08: Generator Spawning (3 Tests)

#### Test 2.36: `test_f08_generator_lfsr_deterministic_sequence`
- **Feature**: F-08 Generator Spawning
- **Description**: Verifies the exact deterministic tick and direction sequence of a generator based on the initial LFSR seed `0xACE1`.
- **Setup**: Clean map, Player 0 at $(10, 10)$. Place `TILE_GENERATOR1` at $(9, 8)$ (rotor index 1).
- **Input**: Step 10 times, clearing any spawned monsters immediately to keep adjacent cells free.
- **Expected Assertions**:
  - **Globals**: 
    - Tick 1 (seed=0xE270): Spawns monster at $(9, 7)$ (Up).
    - Tick 2 (seed=0x7138): Spawns monster at $(9, 7)$ (Up).
    - Ticks 3, 4, 5: No spawn occurs (conditions fail).
  - **Mock HAL**: Sprites registered for spawned monsters.

#### Test 2.37: `test_f08_generator_blocked_all_sides`
- **Feature**: F-08 Generator Spawning
- **Description**: Verifies that if all four adjacent cardinal directions of a generator are blocked, it ticks but fails to spawn any monster.
- **Setup**: Clean map, Player 0 at $(10, 10)$. Place `TILE_GENERATOR1` at $(9, 8)$ (rotor index 1). Place `TILE_WALL` at $(9, 7)$, $(10, 8)$, $(9, 9)$, $(8, 8)$ (blocking Up, Right, Down, Left).
- **Input**: Step to trigger generator tick.
- **Expected Assertions**:
  - **Globals**: No monster spawned. Map remains unchanged.

#### Test 2.38: `test_f08_generator_frozen_at_viewport_boundary`
- **Feature**: F-08 Generator Spawning
- **Description**: Verifies that a generator just 1 tile outside the viewport remains frozen and does not spawn monsters.
- **Setup**: Clean map, Player 0 at $(10, 10)$ (viewport right is $19$). Place `TILE_GENERATOR1` at $(20, 10)$ (rotor index 0).
- **Input**: Step to trigger rotor tick 0.
- **Expected Assertions**:
  - **Globals**: No monster spawned at $(20, 9)$, $(21, 10)$, etc.

---

### F-09: Multiplayer & Viewport (3 Tests)

#### Test 2.39: `test_f09_spectator_all_dead`
- **Feature**: F-09 Multiplayer & Viewport
- **Description**: Verifies that if all joined players are dead, the spectator camera target falls back to centering on the dead local player's last coordinates.
- **Setup**: Clean map. Player 0 joined, dead at $(10, 10)$. Player 1 joined, dead at $(20, 10)$.
- **Input**: Call `draw_viewport(0)`.
- **Expected Assertions**:
  - **Globals**: Both players dead.
  - **Mock HAL**: Camera centered around Player 0's coordinates: `get_camera()` returns $(0, 5)$ (clamped).

#### Test 2.40: `test_f09_spectator_clamping`
- **Feature**: F-09 Multiplayer & Viewport
- **Description**: Verifies that spectator mode camera centering on player centroid is fully clamped to map boundaries.
- **Setup**: Clean map. Player 0 (local) is dead at $(10, 10)$. Joined Player 1 at $(59, 29)$ (alive), Joined Player 2 at $(58, 28)$ (alive).
  - Centroid: target_x = 58, target_y = 28.
- **Input**: Call `draw_viewport(0)`.
- **Expected Assertions**:
  - **Mock HAL**: `get_camera()` returns $(40, 20)$ (clamped to bottom-right map edge, instead of $58-10, 28-5 = 48, 23$).

#### Test 2.41: `test_f09_multiplayer_viewport_independence`
- **Feature**: F-09 Multiplayer & Viewport
- **Description**: Verifies that calling `draw_viewport` for different players in the same tick yields completely independent camera offsets and sprite rendering based on their positions.
- **Setup**: Clean map. Player 0 joined at $(10, 10)$. Player 1 joined at $(40, 20)$.
- **Input**: 
  1. Call `draw_viewport(0)`. Query camera.
  2. Call `draw_viewport(1)`. Query camera.
- **Expected Assertions**:
  - **Mock HAL**: First camera query returns $(0, 5)$. Second camera query returns $(30, 15)$.

---

### F-10: Level Transitions (3 Tests)

#### Test 2.42: `test_f10_transition_destroys_arrows`
- **Feature**: F-10 Level Transitions, F-05 Combat & Projectiles
- **Description**: Verifies that advancing to the next level destroys all active player arrows.
- **Setup**: Clean map. Player 0 at $(10, 10)$. Fired arrow active at $(11, 10)$. Place `TILE_DOWN` at $(12, 10)$.
- **Input**: Move player onto stairs to transition.
- **Expected Assertions**:
  - **Globals**: Current level is 1. Arrow direction is reset to -1.
  - **Mock HAL**: `get_sounds()` contains `SOUND_WARP`.

#### Test 2.43: `test_f10_transition_preserves_rotor`
- **Feature**: F-10 Level Transitions, F-07 Monster Behavior
- **Description**: Verifies that the monster rotor sparse tick count is NOT reset during a level transition, preserving the sparse tick cadence.
- **Setup**: Clean map. Set `monster_rotor` directly to $7$. Player 0 adjacent to `TILE_DOWN` (stairs).
- **Input**: Step onto stairs.
- **Expected Assertions**:
  - **Globals**: Current level is 1. `monster_rotor` becomes 8 (incremented by the step).

#### Test 2.44: `test_f10_stairs_at_map_edge`
- **Feature**: F-10 Level Transitions
- **Description**: Verifies that stairs placed at the extreme edge of the map function correctly.
- **Setup**: Clean map. Place `TILE_DOWN` at $(59, 29)$. Player 0 at $(58, 29)$.
- **Input**: Step Right onto stairs.
- **Expected Assertions**:
  - **Globals**: Current level is 1. Player coordinates reset to starting portal of Level 1.
  - **Mock HAL**: `get_sounds()` contains `SOUND_WARP`.

---

## 3. Tier 3: Cross-Feature Interactions (8 Tests)

### Test 3.1: `test_f3_01_arrow_bomb_clears_monsters`
- **Features**: F-05 Combat & Projectiles, F-06 Smart Bomb Action
- **Description**: Verifies that shooting a bomb tile with an arrow triggers a viewport-wide smart bomb explosion that destroys a monster which was about to attack the player.
- **Setup**: Clean map, Player 0 at $(10, 10)$, facing Right. 
  - Place `TILE_BOMB` at $(12, 10)$.
  - Place `TILE_MONSTER1` at $(9, 10)$ (rotor index 9, adjacent to player, poised to attack).
  - Fire arrow (arrow is at $(11, 10)$, moving Right towards the bomb).
- **Input**: Step with `[0, 0, 0, 0]`.
- **Expected Assertions**:
  - **Globals**: Arrow moves to $(12, 10)$, hits the bomb tile. Bomb tile is cleared, triggering a smart bomb. The monster at $(9, 10)$ is cleared to Space. Player health remains 100.
  - **Mock HAL**: `get_sounds()` contains `SOUND_HIT` (arrow striking the bomb). Viewport draw has no monsters.

### Test 3.2: `test_f3_02_player_collect_food_and_monster_attacks`
- **Features**: F-03 Item Collection, F-07 Monster Behavior
- **Description**: Verifies the tick-ordering of movements: Player moves and collects food (HP increases by 100) *before* a monster moves and attacks (HP decreases). If a player at 10 HP collects food and is attacked by a Level 3 monster in the same tick, they must survive.
- **Setup**: Clean map. Player 0 at $(10, 10)$ with health = 10. Place `TILE_FOOD` at $(11, 10)$. Place `TILE_MONSTER3` at $(12, 10)$ (rotor index 10, adjacent to the food).
- **Input**: Step with `[BUTTON_RIGHT, 0, 0, 0]`.
- **Expected Assertions**:
  - **Globals**:
    - Player moves to $(11, 10)$ and collects food (health: $10 \to 110$).
    - Monster ticks and moves onto player at $(11, 10)$, dealing 30 damage (health: $110 \to 80$).
    - Monster is removed. Player survives at $(11, 10)$ with 80 HP.
  - **Mock HAL**: `get_sounds()` contains exactly `[SOUND_FOOD, SOUND_HIT]`.

### Test 3.3: `test_f3_03_monster_blocked_by_arrow`
- **Features**: F-05 Combat & Projectiles, F-07 Monster Behavior
- **Description**: Verifies the interaction when an arrow and a monster move into the same tile on the same tick. Since arrows process first, the arrow occupies the tile, blocking the monster's movement. On the next tick, the arrow flies into the monster, degrading it.
- **Setup**: Clean map. Player 0 at $(10, 10)$. 
  - Fired arrow at $(10, 10)$ (just fired) moving Right (destination $(11, 10)$).
  - Monster at $(12, 10)$ (rotor index 9) moving Left (destination $(11, 10)$).
- **Input**: 
  1. Step with `[BUTTON_FIRE, 0, 0, 0]` (spawns arrow, moves arrow to 11,10. Monster ticks, sees arrow at 11,10, is blocked and remains at 12,10).
  2. Step with `[0, 0, 0, 0]` (arrow moves to 12,10, hitting monster).
- **Expected Assertions**:
  - **Globals**: 
    - After step 1: Arrow is at $(11, 10)$. Monster remains at $(12, 10)$.
    - After step 2: Arrow is destroyed. Monster at $(12, 10)$ is degraded.
  - **Mock HAL**: `get_sounds()` contains `SOUND_SHOOT` followed by `SOUND_HIT`.

### Test 3.4: `test_f3_04_player_shoots_self_in_back`
- **Features**: F-04 Door & Key Mechanics, F-05 Combat & Projectiles
- **Description**: Verifies that if a player fires an arrow and moves forward in the same tick to unlock a door, they move to the door tile first, and then their own arrow flies forward, hitting the player from behind and destroying itself harmlessly.
- **Setup**: Clean map. Player 0 at $(10, 10)$, keys = 1, facing Right. Place `TILE_DOOR` at $(11, 10)$.
- **Input**: Step with `[BUTTON_FIRE | BUTTON_RIGHT, 0, 0, 0]`.
- **Expected Assertions**:
  - **Globals**: 
    - Firing sets arrow at $(10, 10)$ facing Right.
    - Player moves to $(11, 10)$, unlocking door (keys = 0). Old position $(10, 10)$ becomes Space.
    - Arrow moves from $(10, 10)$ to $(11, 10)$. It hits the player tile, which is not in the destructible range, so the arrow is destroyed (`arrow_dir[0] == -1`).
    - Player survives at $(11, 10)$ with 100 HP.
  - **Mock HAL**: `get_sounds()` contains `SOUND_SHOOT` and `SOUND_KEY`.

### Test 3.5: `test_f3_05_teammate_smart_bomb_saves_player`
- **Features**: F-06 Smart Bomb Action, F-07 Monster Behavior, F-09 Multiplayer
- **Description**: Verifies that in a multiplayer game, Player 1 triggering a smart bomb clears a monster adjacent to Player 0 in the same tick, preventing the monster from attacking Player 0.
- **Setup**: Clean map. Player 0 joined at $(10, 10)$. Player 1 joined at $(11, 11)$, has 1 bomb. Place `TILE_MONSTER1` at $(9, 10)$ (adjacent to Player 0, rotor index 9).
- **Input**: Step with `[0, BUTTON_BOMB, 0, 0]` (Player 1 triggers bomb).
- **Expected Assertions**:
  - **Globals**: Smart bomb clears the monster. Player 0 health remains 100 (no attack occurs).
  - **Mock HAL**: `get_sounds()` contains exactly `SOUND_BOMB` (no `SOUND_HIT`).

### Test 3.6: `test_f3_06_smart_bomb_prevents_spawn`
- **Features**: F-06 Smart Bomb Action, F-08 Generator Spawning
- **Description**: Verifies that a player triggering a smart bomb on the same tick a generator is scheduled to spawn a monster destroys the generator first, preventing the spawn.
- **Setup**: Clean map. Player 0 at $(10, 10)$, has 1 bomb. Place `TILE_GENERATOR1` at $(9, 8)$ (rotor index 1, scheduled to spawn on this tick).
- **Input**: Step with `[BUTTON_BOMB, 0, 0, 0]`.
- **Expected Assertions**:
  - **Globals**: Generator at $(9, 8)$ is destroyed (turned to Space). No monster is spawned at $(9, 7)$.
  - **Mock HAL**: `get_sounds()` contains `SOUND_BOMB`.

### Test 3.7: `test_f3_07_transition_escapes_monsters`
- **Features**: F-10 Level Transitions, F-07 Monster Behavior
- **Description**: Verifies that if a player moves onto stairs to transition levels on the same tick a monster is poised to attack, the level transition occurs first, safely warping the player and removing all old level monsters.
- **Setup**: Clean map. Player 0 at $(10, 10)$ with 10 HP. Place `TILE_DOWN` (stairs) at $(11, 10)$. Place `TILE_MONSTER1` at $(9, 10)$ (rotor index 9).
- **Input**: Step with `[BUTTON_RIGHT, 0, 0, 0]`.
- **Expected Assertions**:
  - **Globals**: Current level is 1. Player 0 is at Level 1 starting portal with 10 HP (alive, no damage taken). Old level monsters no longer exist.
  - **Mock HAL**: `get_sounds()` contains `SOUND_WARP` (no `SOUND_HIT` or `SOUND_DIE`).

### Test 3.8: `test_f3_08_arrow_destroys_generator_prevents_spawn`
- **Features**: F-05 Combat & Projectiles, F-08 Generator Spawning
- **Description**: Verifies that a flying arrow striking a generator on the same tick it was scheduled to spawn a monster destroys the generator first, preventing the spawn.
- **Setup**: Clean map. Player 0 at $(10, 10)$. Fired arrow at $(9, 9)$ moving Down (towards generator). Place `TILE_GENERATOR1` at $(9, 8)$ (rotor index 1, scheduled to spawn on this tick).
- **Input**: Step with `[0, 0, 0, 0]`.
- **Expected Assertions**:
  - **Globals**: Arrow moves to $(9, 8)$ and destroys the generator (turned to Space). Arrow is destroyed. No monster is spawned.
  - **Mock HAL**: `get_sounds()` contains `SOUND_HIT`.
