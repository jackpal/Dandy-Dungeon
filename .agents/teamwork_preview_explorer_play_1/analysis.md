# Tier 4 E2E Play Scenarios Design Report

This report presents the complete, requirement-driven, and opaque-box design for the Tier 4 E2E Play Scenarios (Milestone 4) of the Dandy Dungeon project. These scenarios represent complex, multi-step real-world playthroughs designed to run on the offline E2E test runner (`libdandy_test.so` and `dandy_env.py`).

Each scenario includes:
1. **Map Layout**: Precise coordinates of solid boundaries, items, portals, and entities.
2. **Player Input Sequences**: Tick-by-tick inputs injected for all players.
3. **Step-by-Step Logic**: Trace of game state, cooldowns, and entity interactions.
4. **Double Assertions**: Globals state checks combined with mock HAL side-effect checks (sounds, drawing, camera, sprites).
5. **Edge Wall Elision Verification**: Assertion that borders remain intact as walls.

---

## Shared Setup Helper (Python)

To ensure consistency and clean setups across all test suites, the following helper method is recommended for the implementer:

```python
def setup_scenario_map(self, player_positions, custom_tiles):
    """
    Initializes a 60x30 map with an outer wall border (Edge Wall Elision),
    clears the interior to TILE_SPACE, injects custom tiles, and joins players.
    """
    # Initialize all to TILE_WALL
    custom_map = [self.env.TILE_WALL] * self.env.MAP_SIZE
    
    # Clear interior to TILE_SPACE
    for y in range(1, 29):
        for x in range(1, 59):
            custom_map[y * 60 + x] = self.env.TILE_SPACE
            
    # Inject custom tiles (walls, doors, items, monsters, generators)
    for (x, y), tile_id in custom_tiles.items():
        custom_map[y * 60 + x] = tile_id
        
    # Inject player tiles, positions, and default states
    for p_idx, (x, y) in player_positions.items():
        custom_map[y * 60 + x] = self.env.TILE_PLAYER1 + (p_idx * 8)
        self.env.set_player_position(p_idx, x, y)
        self.env.set_player_joined(p_idx, True)
        self.env.set_player_health(p_idx, 100)
        self.env.set_player_score(p_idx, 0)
        self.env.set_player_bombs(p_idx, 0)
        self.env.set_player_keys(p_idx, 0)
        self.env.set_player_dir(p_idx, 0) # Facing Up (0)
        self.env.set_player_move_timer(p_idx, 0)
        
    self.env.dandy_map = custom_map
    self.env.clear_mock_buffers()
    
    # Assert outer border is intact immediately after setup
    self.env.assert_outer_border_walls(self)
```

---

## Scenario 1: Full Level 0 Playthrough

### 1. Objective
A single player starts at the entrance, navigates a winding maze, collects a key, unlocks a door, shoots and defeats a monster from a distance, collects food, and steps onto the stairs to trigger the level transition, loading the compressed Level 1 from ROM.

### 2. Winding Maze Map Layout
A tight, single-tile-wide corridor is constructed around `(10, 10)` to prevent the player from straying and to verify collision:

- **Corridor Walls**:
  - `y = 9`, `x` in `[9, 13]` -> `TILE_WALL`
  - `y = 11`, `x` in `[9, 11]` -> `TILE_WALL`
  - `y = 12`, `x` in `[9, 11]` and `x = 13` -> `TILE_WALL`
  - `y = 14`, `x` in `[7, 13]` -> `TILE_WALL`
- **Portals & Items**:
  - `(10, 10)`: `TILE_UP` (spawn portal)
  - `(12, 10)`: `TILE_KEY` (key)
  - `(12, 12)`: `TILE_DOOR` (locked door)
  - `(10, 13)`: `TILE_MONSTER1` (level 1 monster)
  - `(9, 13)`: `TILE_FOOD` (food item)
  - `(8, 13)`: `TILE_DOWN` (exit stairs)
- **Visual ASCII representation**:
  ```
  Row  9:  W  W  W  W  W
  Row 10:  W  P  .  K  W     (P = Player start at 10,10; K = Key at 12,10)
  Row 11:  W  W  W  .  W
  Row 12:  W  W  W  D  W     (D = Door at 12,12)
  Row 13:  W  S  F  M  .  .  (S = Stairs at 8,13; F = Food at 9,13; M = Monster at 10,13)
  Row 14:  W  W  W  W  W  W  W
  ```

### 3. Tick-by-Tick Execution & Inputs
Total moves required: 7 cardinal steps. With a 4-tick cooldown, movement takes 28 ticks. Firing and waiting takes 5 ticks. Total ticks = 33.

- **Tick 0**: Setup map. Player 0 joins at `(10, 10)` facing Up.
  - *Assert*: `player_x[0] == 10`, `player_y[0] == 10`, `player_keys[0] == 0`, `player_health[0] == 100`.
- **Tick 1**: Input `[BUTTON_RIGHT, 0, 0, 0]`.
  - Player moves to `(11, 10)`. Direction becomes 2 (Right). `player_move_timer` becomes 3.
  - *Assert*: `player_x[0] == 11`, `player_y[0] == 10`, `player_move_timer[0] == 3`.
- **Ticks 2-4**: Input `[BUTTON_RIGHT, 0, 0, 0]`. (Hold right; timer decrements to 0).
- **Tick 5**: Input `[BUTTON_RIGHT, 0, 0, 0]`.
  - Player moves to `(12, 10)`, collecting the key. Cooldown becomes 3.
  - *Assert*: `player_x[0] == 12`, `player_y[0] == 10`, `player_keys[0] == 1`.
  - *HAL Assert*: `SOUND_KEY` is played.
- **Tick 6**: Input `[BUTTON_DOWN, 0, 0, 0]`.
  - Player turns Down (dir 4). Timer decrements to 2. No movement.
- **Ticks 7-8**: Input `[BUTTON_DOWN, 0, 0, 0]`. (Timer decrements to 0).
- **Tick 9**: Input `[BUTTON_DOWN, 0, 0, 0]`.
  - Player moves to `(12, 11)`. Cooldown becomes 3.
  - *Assert*: `player_x[0] == 12`, `player_y[0] == 11`.
- **Ticks 10-12**: Input `[BUTTON_DOWN, 0, 0, 0]`. (Timer decrements to 0).
- **Tick 13**: Input `[BUTTON_DOWN, 0, 0, 0]`.
  - Player moves to `(12, 12)`, unlocking the door. Door flood-fills to space. Cooldown becomes 3.
  - *Assert*: `player_x[0] == 12`, `player_y[0] == 12`, `player_keys[0] == 0`, tile at `(12, 12)` is `TILE_PLAYER1 + 4` (facing Down).
  - *HAL Assert*: `SOUND_KEY` is played.
- **Ticks 14-16**: Input `[BUTTON_DOWN, 0, 0, 0]`. (Timer decrements to 0).
- **Tick 17**: Input `[BUTTON_DOWN, 0, 0, 0]`.
  - Player moves to `(12, 13)`. Cooldown becomes 3.
  - *Assert*: `player_x[0] == 12`, `player_y[0] == 13`.
- **Tick 18**: Input `[BUTTON_LEFT, 0, 0, 0]`.
  - Player turns Left (dir 6). Timer decrements to 2. No movement.
- **Ticks 19-20**: Input `[BUTTON_LEFT, 0, 0, 0]`. (Timer decrements to 0).
- **Tick 21**: Input `[BUTTON_LEFT, 0, 0, 0]`.
  - Player moves to `(11, 13)`. Cooldown becomes 3.
  - *Assert*: `player_x[0] == 11`, `player_y[0] == 13`.
- **Tick 22**: Input `[BUTTON_FIRE, 0, 0, 0]`.
  - Player shoots Left (arrow spawns at `(11, 13)` facing Left).
  - In the same tick, `move_arrows()` steps the arrow to `(10, 13)`. It hits the monster, deactivates, and replaces the monster with `TILE_SPACE`.
  - *Assert*: `arrow_dir[0] == -1` (inactive), map tile at `(10, 13)` is `TILE_SPACE`.
  - *HAL Assert*: `SOUND_SHOOT` and `SOUND_HIT` are played.
  - Cooldown decrements to 2.
- **Ticks 23-24**: Input `[0, 0, 0, 0]`. (Wait for cooldown to reach 0).
- **Tick 25**: Input `[BUTTON_LEFT, 0, 0, 0]`.
  - Player moves to `(10, 13)`. Cooldown becomes 3.
  - *Assert*: `player_x[0] == 10`, `player_y[0] == 13`.
- **Ticks 26-28**: Input `[BUTTON_LEFT, 0, 0, 0]`. (Timer decrements to 0).
- **Tick 29**: Input `[BUTTON_LEFT, 0, 0, 0]`.
  - Player moves to `(9, 13)`, collecting food. Health increases to 200. Cooldown becomes 3.
  - *Assert*: `player_x[0] == 9`, `player_y[0] == 13`, `player_health[0] == 200`.
  - *HAL Assert*: `SOUND_FOOD` is played.
- **Ticks 30-32**: Input `[BUTTON_LEFT, 0, 0, 0]`. (Timer decrements to 0).
- **Tick 33**: Input `[BUTTON_LEFT, 0, 0, 0]`.
  - Player steps onto the stairs `TILE_DOWN` at `(8, 13)`.
  - The engine triggers `next_level()`, loading Level 1 from ROM!
  - *Assert*: `current_level == 1`, `player_health[0] == 200` (retained), player's coordinates have warped to Level 1's starting portal.
  - *HAL Assert*: `SOUND_WARP` is played.
  - *Edge Wall Elision Check*: `self.env.assert_outer_border_walls(self)` (verifies that Level 1's border is correctly reconstructed as walls after decompression!).

---

## Scenario 2: Cooperative Multiplayer Playthrough

### 1. Objective
Two players join, spawning in separate parallel corridors separated by a wall. Player 1 collects a key but has no door. Player 0 has no key but is blocked by a locked door. Both players collect individual treasures, and Player 1 must coordinate to walk over, unlock the door for Player 0, and move out of the way so Player 0 can pass. They both reach the exit stairs.

### 2. Map Layout
- **Corridor Wall**:
  - `x = 11`, `y` in `[9, 11]` -> `TILE_WALL` (separates starting positions)
- **Player Positions**:
  - `(10, 10)`: Player 0 start (`TILE_PLAYER1`)
  - `(12, 10)`: Player 1 start (`TILE_PLAYER1 + 8`)
- **Portals & Items**:
  - `(9, 11)`: `TILE_MONEY` (P0's treasure)
  - `(13, 11)`: `TILE_MONEY` (P1's treasure)
  - `(12, 11)`: `TILE_KEY` (key for P1)
  - `(10, 12)`: `TILE_DOOR` (door blocking P0)
  - `(10, 14)`: `TILE_DOWN` (stairs to Level 1)
- **Visual ASCII representation**:
  ```
  Row 10:   .  P0  W  P1  .     (P0 start at 10,10; P1 start at 12,10; W at 11,10)
  Row 11:   M  .   W  K   M     (M = Money at 9,11 and 13,11; K = Key at 12,11; W at 11,11)
  Row 12:   .  D   .  .   .     (D = Door at 10,12)
  Row 13:   .  .   .  .   .
  Row 14:   .  S   .  .   .     (S = Stairs at 10,14)
  ```

### 3. Tick-by-Tick Execution & Inputs
- **Tick 0**: Setup map. Join Player 0 at `(10, 10)` and Player 1 at `(12, 10)`.
  - *Assert*: P0 at `(10, 10)`, P1 at `(12, 10)`. Score of both = 0.
- **Tick 1**: Input `[BUTTON_DOWN, BUTTON_DOWN, 0, 0]`.
  - P0 moves Down to `(10, 11)`. Cooldown = 3.
  - P1 moves Down to `(12, 11)`, collecting the key. Cooldown = 3.
  - *Assert*: P0 at `(10, 11)`. P1 at `(12, 11)`. `player_keys[1] == 1`.
  - *HAL Assert*: `SOUND_KEY` is played.
- **Ticks 2-4**: Input `[BUTTON_DOWN, BUTTON_DOWN, 0, 0]`. (Hold; timers decrement to 0).
- **Tick 5**: Input `[BUTTON_LEFT, BUTTON_RIGHT, 0, 0]`.
  - P0 moves Left to `(9, 11)`, collecting P0's treasure. Cooldown = 3.
  - P1 moves Right to `(13, 11)`, collecting P1's treasure. Cooldown = 3.
  - *Assert*: P0 at `(9, 11)`, `player_score[0] == 100`. P1 at `(13, 11)`, `player_score[1] == 100`.
  - *HAL Assert*: Sound play count increases by 2 (both play `SOUND_KEY` on collection).
- **Ticks 6-8**: Input `[BUTTON_LEFT, BUTTON_RIGHT, 0, 0]`. (Hold; timers decrement to 0).
- **Tick 9**: Input `[BUTTON_RIGHT, BUTTON_LEFT, 0, 0]`.
  - P0 moves Right to `(10, 11)`. Cooldown = 3.
  - P1 moves Left to `(12, 11)`. Cooldown = 3.
- **Ticks 10-12**: Input `[BUTTON_RIGHT, BUTTON_LEFT, 0, 0]`. (Timers decrement to 0).
- **Tick 13**: Input `[BUTTON_DOWN, BUTTON_DOWN, 0, 0]`.
  - P0 tries to move Down to `(10, 12)`. Blocked by `TILE_DOOR` (0 keys). P0 stays at `(10, 11)` but cooldown is set to 3 anyway.
  - P1 moves Down to `(12, 12)`. Cooldown = 3.
  - *Assert*: P0 at `(10, 11)`. P1 at `(12, 12)`. `player_keys[1] == 1`. P0 move timer = 3.
- **Ticks 14-16**: Input `[BUTTON_DOWN, BUTTON_DOWN, 0, 0]`. (Timers decrement to 0).
- **Tick 17**: Input `[0, BUTTON_LEFT, 0, 0]`.
  - P0 stands still (no input).
  - P1 moves Left to `(11, 12)`. Cooldown = 3.
- **Ticks 18-20**: Input `[0, BUTTON_LEFT, 0, 0]`. (Timers decrement to 0).
- **Tick 21**: Input `[0, BUTTON_LEFT, 0, 0]`.
  - P1 moves Left to `(10, 12)` (locked door). Using P1's key, the door is unlocked and flood-filled to space. P1 is now at `(10, 12)`. Cooldown = 3.
  - *Assert*: P1 at `(10, 12)`, `player_keys[1] == 0`. Tile at `(10, 12)` is `TILE_PLAYER1 + 8 + 6` (P1 facing Left).
  - *HAL Assert*: `SOUND_KEY` is played.
- **Ticks 22-24**: Input `[0, BUTTON_LEFT, 0, 0]`. (Timers decrement to 0).
- **Tick 25**: Input `[0, BUTTON_DOWN, 0, 0]`.
  - P1 moves Down to `(10, 13)`. Cooldown = 3.
  - *Assert*: P1 at `(10, 13)`. Tile at `(10, 12)` is now `TILE_SPACE`. P0 is still at `(10, 11)`.
- **Ticks 26-28**: Input `[0, BUTTON_DOWN, 0, 0]`. (Timers decrement to 0).
- **Tick 29**: Input `[BUTTON_DOWN, 0, 0, 0]`.
  - P0 moves Down to `(10, 12)` (now open space!). Cooldown = 3.
  - *Assert*: P0 at `(10, 12)`. P1 at `(10, 13)`.
- **Ticks 30-32**: Input `[BUTTON_DOWN, 0, 0, 0]`. (Timers decrement to 0).
- **Tick 33**: Input `[BUTTON_DOWN, BUTTON_DOWN, 0, 0]`.
  - P0 tries to move Down to `(10, 13)`. Blocked by P1 who is currently occupying `(10, 13)` (players block each other). P0 stays at `(10, 12)`, cooldown becomes 3.
  - P1 moves Down to `(10, 14)` (stairs).
  - Since P1 steps on `TILE_DOWN`, `next_level()` is triggered, loading Level 1!
  - *Assert*: `current_level == 1`. Score of P0 (100) and P1 (100) are preserved. Both players spawned at Level 1 start portal.
  - *HAL Assert*: `SOUND_WARP` is played.

---

## Scenario 3: Game Over Reset Playthrough

### 1. Objective
Two players have collected inventory and scores. Monsters are placed adjacent to them. We trigger monster pathfinding, leveraging the sparse monster rotor to tick them in different columns step-by-step. The monsters attack and kill both players. The game loop detects all players are dead, triggers a game over, wipes all inventories and scores, resets the level to 0, and reloads Level 0.

### 2. Map Layout
- **Player Positions**:
  - `(10, 10)`: Player 0 start (`TILE_PLAYER1`)
  - `(20, 10)`: Player 1 start (`TILE_PLAYER1 + 8`)
- **Portals & Monsters**:
  - `(11, 10)`: `TILE_MONSTER3` (level 3 monster, deals 30 damage)
  - `(21, 10)`: `TILE_MONSTER2` (level 2 monster, deals 20 damage)
- **Player Stats (Pre-loaded for wiping)**:
  - P0: health = 10, score = 500, keys = 3, bombs = 2.
  - P1: health = 20, score = 300, keys = 1, bombs = 1.

### 3. Tick-by-Tick Execution & Inputs
- **Tick 0**: Setup map and player stats. Set `monster_rotor = 8`.
  - *Assert*: Player stats are as pre-loaded.
- **Tick 1**: Input `[0, 0, 0, 0]`.
  - `monster_rotor` increments to 9.
  - Since `monster_rotor == 9`, columns where `x % 4 == 1` and rows where `y % 4 == 2` tick.
  - The monster at `(21, 10)` ticks (since `21 % 4 == 1` and `10 % 4 == 2`).
  - It moves Left onto P1's tile `(20, 10)`, dealing $10 \times 2 = 20$ damage.
  - P1's health becomes 0. P1 dies! P1's tile is cleared from the map immediately.
  - P0 (at `10, 10`) is unaffected because the monster at `(11, 10)` does not tick (since `11 % 4 == 3`).
  - *Assert*: `player_health[1] == 0`, `player_health[0] == 10`. Map tile at `(20, 10)` is `TILE_SPACE`.
  - *HAL Assert*: `SOUND_DIE` is played.
- **Tick 2**: Input `[0, 0, 0, 0]`.
  - `monster_rotor` increments to 10. No monsters at `x % 4 == 2` tick.
  - *Assert*: State is unchanged.
- **Tick 3**: Input `[0, 0, 0, 0]`.
  - `monster_rotor` increments to 11.
  - Columns where `x % 4 == 3` and rows where `y % 4 == 2` tick.
  - The monster at `(11, 10)` ticks (since `11 % 4 == 3` and `10 % 4 == 2`).
  - It moves Left onto P0's tile `(10, 10)`, dealing $10 \times 3 = 30$ damage.
  - P0's health becomes 0. P0 dies! P0's tile is cleared from the map.
  - Since all players are dead, `end_game()` is called:
    - `current_level` resets to 0.
    - P0 is joined, P1 unjoined.
    - All health restored to 100, inventories/scores wiped to 0.
    - Real Level 0 is loaded.
  - *Assert*:
    - `current_level == 0`.
    - `player_joined[0] == True`, `player_joined[1] == False`.
    - `player_health[0] == 100`, `player_health[1] == 100`.
    - `player_score[0] == 0`, `player_keys[0] == 0`, `player_bombs[0] == 0`.
    - Map matches the decompressed Level 0.
  - *HAL Assert*: `SOUND_DIE` is played.
  - *Edge Wall Elision Check*: `self.env.assert_outer_border_walls(self)` (verifies that Level 0's border is reconstructed correctly after the game over reload!).

---

## Scenario 4: Combative Maze Scenario

### 1. Objective
A single player navigates a narrow corridor packed with monsters of different levels and a generator. The player shoots arrows to degrade and destroy a Level 3 monster step-by-step, moves forward, and then utilizes a smart bomb to clear the remaining visible monster and generator in their viewport while proving that off-screen entities are unaffected.

### 2. Map Layout
- **Player Position**:
  - `(10, 10)`: Player 0 start (`TILE_PLAYER1`), facing Right (dir 2).
- **Entities**:
  - `(12, 10)`: `TILE_MONSTER3` (Level 3 monster)
  - `(14, 10)`: `TILE_MONSTER2` (Level 2 monster)
  - `(16, 10)`: `TILE_GENERATOR1` (Level 1 generator)
  - `(25, 10)`: `TILE_MONSTER1` (Off-screen monster, outside player's viewport)
  - `(10, 20)`: `TILE_MONSTER1` (Off-screen monster, outside player's viewport)
- **Player Stats**:
  - P0 starts with 1 bomb (`player_bombs[0] = 1`).

### 3. Tick-by-Tick Execution & Inputs
- **Tick 0**: Setup map. Player 0 at `(10, 10)` facing Right (dir 2).
  - *Assert*: Entities are in their initial tiles. `player_bombs[0] == 1`.
- **Tick 1**: Input `[BUTTON_FIRE, 0, 0, 0]`.
  - Arrow is fired Right. Spawns at `(10, 10)` facing Right.
  - In the same tick, `move_arrows()` steps the arrow to `(11, 10)` (space).
  - *Assert*: Arrow active at `(11, 10)`.
  - *HAL Assert*: `SOUND_SHOOT` is played.
- **Tick 2**: Input `[0, 0, 0, 0]`.
  - `move_arrows()` steps the arrow to `(12, 10)`. It hits `TILE_MONSTER3`.
  - `TILE_MONSTER3` degrades to `TILE_MONSTER2`. Arrow is destroyed.
  - *Assert*: Tile at `(12, 10)` is `TILE_MONSTER2`. `arrow_dir[0] == -1`.
  - *HAL Assert*: `SOUND_HIT` is played.
- **Tick 3**: Input `[BUTTON_FIRE, 0, 0, 0]`.
  - Second arrow fired Right. Spawns at `(10, 10)`, steps to `(11, 10)`.
  - *HAL Assert*: `SOUND_SHOOT` is played.
- **Tick 4**: Input `[0, 0, 0, 0]`.
  - Second arrow steps to `(12, 10)`. Hits `TILE_MONSTER2` -> degrades to `TILE_MONSTER1`. Arrow dies.
  - *Assert*: Tile at `(12, 10)` is `TILE_MONSTER1`.
  - *HAL Assert*: `SOUND_HIT` is played.
- **Tick 5**: Input `[BUTTON_FIRE, 0, 0, 0]`.
  - Third arrow fired Right. Spawns at `(10, 10)`, steps to `(11, 10)`.
- **Tick 6**: Input `[0, 0, 0, 0]`.
  - Third arrow steps to `(12, 10)`. Hits `TILE_MONSTER1` -> replaced by `TILE_SPACE`. Arrow dies.
  - *Assert*: Tile at `(12, 10)` is `TILE_SPACE`.
  - *HAL Assert*: `SOUND_HIT` is played.
- **Tick 7**: Input `[BUTTON_RIGHT, 0, 0, 0]`.
  - Player moves to `(11, 10)`. Cooldown = 3.
- **Ticks 8-10**: Input `[BUTTON_RIGHT, 0, 0, 0]`. (Timers decrement to 0).
- **Tick 11**: Input `[BUTTON_RIGHT, 0, 0, 0]`.
  - Player moves to `(12, 10)` (the former monster tile). Cooldown = 3.
  - *Assert*: Player at `(12, 10)`.
- **Ticks 12-14**: Input `[BUTTON_RIGHT, 0, 0, 0]`. (Timers decrement to 0).
- **Tick 15**: Input `[BUTTON_BOMB, 0, 0, 0]`.
  - Player triggers a Smart Bomb!
  - Player's viewport is centered around `(12, 10)` -> `vp_left = 2`, `vp_top = 5`.
  - Viewport covers `x` in `[2, 21]` and `y` in `[5, 14]`.
  - Monsters and generators inside the viewport are destroyed:
    - Monster at `(14, 10)` becomes `TILE_SPACE`.
    - Generator at `(16, 10)` becomes `TILE_SPACE`.
  - Entities outside the viewport are unaffected:
    - Monster at `(25, 10)` (outside `x < 22`) remains `TILE_MONSTER1`.
    - Monster at `(10, 20)` (outside `y < 15`) remains `TILE_MONSTER1`.
  - *Assert*:
    - `player_bombs[0] == 0`.
    - Tile at `(14, 10)` is `TILE_SPACE`.
    - Tile at `(16, 10)` is `TILE_SPACE`.
    - Tile at `(25, 10)` is `TILE_MONSTER1`.
    - Tile at `(10, 20)` is `TILE_MONSTER1`.
  - *HAL Assert*: `SOUND_BOMB` is played.

---

## Scenario 5: Viewport Scrolling & Boundary Scenario

### 1. Objective
Verifies the viewport camera tracking, clamping, and dynamic sprite drawing rules. The player is placed at the top-left corner, middle, and bottom-right corner of the 60x30 map. We verify that the viewport camera coordinates are calculated correctly, clamp at map boundaries, and that the player's hardware sprite coordinates are correctly converted to viewport space. Finally, we test Spectator Mode camera centering when the local player is dead, centering on the centroid of the remaining alive players.

### 2. Map Layout
A clean, empty map (all `TILE_SPACE` inside a `TILE_WALL` border).

### 3. Step-by-Step Verification

#### Step 3.1: Top-Left Boundary Clamping
- **Action**: Place Player 0 at `(1, 1)`. Call `self.env.draw_viewport(0)`.
- **Mathematical Expectation**:
  - `target_x = 1`, `target_y = 1`.
  - `vp_left = clamp(1 - 10, 0, 40) = 0`.
  - `vp_top = clamp(1 - 5, 0, 20) = 0`.
  - Player's viewport coordinates: `sx = 1 - 0 = 1`, `sy = 1 - 0 = 1`.
  - Player's sprite pixel coordinates: `x = 1 * 8 = 8`, `y = 1 * 8 = 8`.
- **Assertions**:
  - *HAL Assert*: `mock_get_viewport_camera()` returns `(0, 0)`.
  - *HAL Assert*: Sprite 0 is active, `tile_id == TILE_PLAYER1`, `x == 8`, `y == 8`.

#### Step 3.2: Middle Map Scrolling
- **Action**: Warp Player 0 to `(15, 8)`. Call `self.env.draw_viewport(0)`.
- **Mathematical Expectation**:
  - `target_x = 15`, `target_y = 8`.
  - `vp_left = clamp(15 - 10, 0, 40) = 5`.
  - `vp_top = clamp(8 - 5, 0, 20) = 3`.
  - Player's viewport coordinates: `sx = 15 - 5 = 10`, `sy = 8 - 3 = 5`.
  - Player's sprite pixel coordinates: `x = 10 * 8 = 80`, `y = 5 * 8 = 40`.
- **Assertions**:
  - *HAL Assert*: `mock_get_viewport_camera()` returns `(5, 3)`.
  - *HAL Assert*: Sprite 0 is active, `tile_id == TILE_PLAYER1`, `x == 80`, `y == 40`.

#### Step 3.3: Bottom-Right Boundary Clamping
- **Action**: Warp Player 0 to `(58, 28)`. Call `self.env.draw_viewport(0)`.
- **Mathematical Expectation**:
  - `target_x = 58`, `target_y = 28`.
  - `vp_left = clamp(58 - 10, 0, 40) = 40`.
  - `vp_top = clamp(28 - 5, 0, 20) = 20`.
  - Player's viewport coordinates: `sx = 58 - 40 = 18`, `sy = 28 - 20 = 8`.
  - Player's sprite pixel coordinates: `x = 18 * 8 = 144`, `y = 8 * 8 = 64`.
- **Assertions**:
  - *HAL Assert*: `mock_get_viewport_camera()` returns `(40, 20)`.
  - *HAL Assert*: Sprite 0 is active, `tile_id == TILE_PLAYER1`, `x == 144`, `y == 64`.

#### Step 3.4: Spectator Mode Camera Centering
- **Action**:
  - Set Player 0 (local player) health to 0 (dead).
  - Join Player 1 at `(10, 10)`, health = 100.
  - Join Player 2 at `(20, 16)`, health = 100.
  - Call `self.env.draw_viewport(0)`.
- **Mathematical Expectation**:
  - Since local player 0 is dead, camera targets the centroid of alive players (P1 and P2).
  - `target_x = (10 + 20) / 2 = 15`.
  - `target_y = (10 + 16) / 2 = 13`.
  - `vp_left = clamp(15 - 10, 0, 40) = 5`.
  - `vp_top = clamp(13 - 5, 0, 20) = 8`.
- **Assertions**:
  - *HAL Assert*: `mock_get_viewport_camera()` returns `(5, 8)`.

---

## Verification Plan

### 1. Test Targets & Execution
To verify these E2E play scenarios, the implementer must:
1. Write these scenarios as Python `unittest` methods in a new file `dandy-gb/tests/test_tier4.py`.
2. Run the test suite using the Makefile:
   ```bash
   make test
   ```
   This will compile `libdandy_test.so` and run the entire Python test suite, including the new Tier 4 test file.

### 2. Correctness Metrics
- **Pass/Fail**: All 5 test cases must pass with 100% success.
- **Side-Effects Logs**: Sound count, camera scroll offsets, and sprite registration logs must match the mathematical expectations exactly.
- **Edge Wall Integrity**: No border elision errors; `assert_outer_border_walls` must pass on every level load.
- **Timing**: No frame timing or cooldown slip; holding buttons must trigger movement exactly once every 4 ticks.
