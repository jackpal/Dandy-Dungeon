# Milestone 4: Tier 4 E2E Play Scenarios Design

This document provides the complete, requirement-driven, and opaque-box design for the Tier 4 End-to-End (E2E) Play Scenarios of the Dandy Dungeon project. These scenarios simulate real-world gameplay sessions to verify the integration of all 10 core features under realistic conditions.

---

## 1. Executive Summary & Mapping of Core Features

The Tier 4 test suite consists of 5 distinct playthrough scenarios designed to thoroughly exercise the game rules, timing cooldowns, spatial mechanics, and hardware abstraction layer (HAL) side-effects.

### Feature Mapping Matrix
The table below shows how the 10 core features (F-01 to F-10) are distributed across the 5 playthrough scenarios:

| Feature ID | Feature Name | Scenario 1 | Scenario 2 | Scenario 3 | Scenario 4 | Scenario 5 |
|---|---|:---:|:---:|:---:|:---:|:---:|
| **F-01** | Movement & Timing | Yes | Yes | Yes | Yes | Yes |
| **F-02** | Slide Mechanics | - | - | - | - | - (Tier 2/3) |
| **F-03** | Item Collection | Yes | Yes | - | - | - |
| **F-04** | Door & Key Mechanics | Yes | Yes | - | - | - |
| **F-05** | Combat & Projectiles | Yes | - | - | Yes | - |
| **F-06** | Smart Bomb Action | - | - | - | Yes | - |
| **F-07** | Monster Behavior | Yes | - | Yes | Yes | - |
| **F-08** | Generator Spawning | - | - | - | Yes | - |
| **F-09** | Multiplayer & Viewport | - | Yes | Yes | - | Yes |
| **F-10** | Level Transitions | Yes | Yes | Yes | - | - |

---

## 2. Playthrough Scenario Designs

### Scenario 1: Full Level 0 Playthrough
* **Concept**: A single-player run starting at the portal of Level 0, navigating a winding corridor, collecting a key, unlocking a door, shooting a blocking monster from a distance, collecting food to boost health, and stepping on the stairs to warp to Level 1.
* **Core Features Verified**: F-01, F-03, F-04, F-05, F-07, F-10.

#### A. Map Layout
We define a custom 60x30 map containing a narrow winding corridor starting at the top-left and ending near the top-middle. The rest of the map is filled with walls or empty space, and the outer borders are strictly `TILE_WALL`.

```python
# Legend:
# 0 = TILE_SPACE, 1 = TILE_WALL, 2 = TILE_DOOR, 3 = TILE_UP (portal), 4 = TILE_DOWN (stairs)
# 5 = TILE_KEY, 6 = TILE_FOOD, 9 = TILE_MONSTER1

def make_scenario1_map(env):
    m = [env.TILE_SPACE] * env.MAP_SIZE
    
    # 1. Edge Wall Elision Setup (Outer borders = TILE_WALL)
    for x in range(60):
        m[0 * 60 + x] = env.TILE_WALL
        m[29 * 60 + x] = env.TILE_WALL
    for y in range(30):
        m[y * 60 + 0] = env.TILE_WALL
        m[y * 60 + 59] = env.TILE_WALL
        
    # 2. Portal TILE_UP at (2, 2)
    m[2 * 60 + 2] = env.TILE_UP
    # Player 0 will spawn at (2, 1) due to spawn offset (0, -1)
    
    # 3. Path Elements
    m[1 * 60 + 5] = env.TILE_KEY       # Key at (5, 1)
    m[4 * 60 + 5] = env.TILE_DOOR      # Door at (5, 4)
    m[5 * 60 + 7] = env.TILE_MONSTER1  # Monster at (7, 5)
    m[5 * 60 + 8] = env.TILE_FOOD      # Food at (8, 5)
    m[5 * 60 + 9] = env.TILE_DOWN      # Stairs at (9, 5)
    
    # 4. Corridor Walls (Enclosing the corridor to prevent wandering)
    m[1 * 60 + 1] = env.TILE_WALL
    m[1 * 60 + 6] = env.TILE_WALL
    m[2 * 60 + 1] = env.TILE_WALL
    m[2 * 60 + 3] = env.TILE_WALL
    m[2 * 60 + 4] = env.TILE_WALL
    m[2 * 60 + 6] = env.TILE_WALL
    m[3 * 60 + 4] = env.TILE_WALL
    m[3 * 60 + 6] = env.TILE_WALL
    m[4 * 60 + 4] = env.TILE_WALL
    m[4 * 60 + 6] = env.TILE_WALL
    m[5 * 60 + 4] = env.TILE_WALL
    for x in range(7, 11):
        m[4 * 60 + x] = env.TILE_WALL  # Corridor ceiling
    for x in range(5, 11):
        m[6 * 60 + x] = env.TILE_WALL  # Corridor floor
    m[5 * 60 + 10] = env.TILE_WALL     # Corridor dead-end wall behind stairs
    
    return m
```

#### B. Step-by-Step Execution & Input Sequence
Movement requires 4 ticks per step (1 tick to move, 3 ticks cooldown).
* **Tick 0**: Input `BUTTON_RIGHT`. Player moves to `(3, 1)`. Cooldown = 3.
* **Ticks 1–3**: Input `0`. Cooldown ticks down to 0.
* **Tick 4**: Input `BUTTON_RIGHT`. Player moves to `(4, 1)`. Cooldown = 3.
* **Ticks 5–7**: Input `0`. Cooldown ticks down to 0.
* **Tick 8**: Input `BUTTON_RIGHT`. Player moves to `(5, 1)`, collecting the key. Cooldown = 3.
* **Ticks 9–11**: Input `0`. Cooldown ticks down to 0.
* **Tick 12**: Input `BUTTON_DOWN`. Player turns Down (`player_dir = 4`) and moves to `(5, 2)`. Cooldown = 3.
* **Ticks 13–15**: Input `0`. Cooldown ticks down to 0.
* **Tick 16**: Input `BUTTON_DOWN`. Player moves to `(5, 3)`. Cooldown = 3.
* **Ticks 17–19**: Input `0`. Cooldown ticks down to 0.
* **Tick 20**: Input `BUTTON_DOWN`. Player steps onto `(5, 4)` (door). Door is unlocked (flood-filled to space) and player moves to `(5, 4)`. Cooldown = 3.
* **Ticks 21–23**: Input `0`. Cooldown ticks down to 0.
* **Tick 24**: Input `BUTTON_DOWN`. Player moves to `(5, 5)`. Cooldown = 3.
* **Ticks 25–27**: Input `0`. Cooldown ticks down to 0.
* **Tick 28**: Input `BUTTON_RIGHT`. Player turns Right (`player_dir = 2`) and moves to `(6, 5)`. Cooldown = 3.
* **Tick 29**: Input `BUTTON_FIRE`. Player shoots an arrow Right from `(6, 5)`. Arrow immediately steps to `(7, 5)` (monster position) in this tick, hitting and destroying the monster.
* **Ticks 30–31**: Input `0`. Cooldown ticks down.
* **Tick 32**: Input `BUTTON_RIGHT`. Player moves to `(7, 5)` (now space). Cooldown = 3.
* **Ticks 33–35**: Input `0`. Cooldown ticks down.
* **Tick 36**: Input `BUTTON_RIGHT`. Player moves to `(8, 5)`, collecting food. Cooldown = 3.
* **Ticks 37–39**: Input `0`. Cooldown ticks down.
* **Tick 40**: Input `BUTTON_RIGHT`. Player moves to `(9, 5)` (stairs), triggering level transition to Level 1.

#### C. Double-Assert Checkpoints (State + HAL)
* **Checkpoint 1 (After Tick 8 - Key Collection)**:
  * *Globals*: `player_x[0] == 5`, `player_y[0] == 1`, `player_keys[0] == 1`.
  * *HAL*: `SOUND_KEY` is present in `env.get_sounds()`.
* **Checkpoint 2 (After Tick 20 - Door Unlocked)**:
  * *Globals*: `player_x[0] == 5`, `player_y[0] == 4`, `player_keys[0] == 0`.
  * *Map Check*: `dandy_map[4 * 60 + 5]` is now the Player 0 tile (`TILE_PLAYER1 + 4` facing Down).
  * *HAL*: `SOUND_KEY` is present in `env.get_sounds()`.
* **Checkpoint 3 (After Tick 29 - Monster Defeated)**:
  * *Globals*: `arrow_dir[0] == -1` (destroyed).
  * *Map Check*: `dandy_map[5 * 60 + 7]` (monster tile) is now `TILE_SPACE`.
  * *HAL*: `SOUND_SHOOT` and `SOUND_HIT` are present in `env.get_sounds()`.
* **Checkpoint 4 (After Tick 36 - Food Collected)**:
  * *Globals*: `player_health[0] == 200` (started at 100, collected food +100).
  * *HAL*: `SOUND_FOOD` is present in `env.get_sounds()`.
* **Checkpoint 5 (After Tick 40 - Level Transition)**:
  * *Globals*: `current_level == 1`. Players' coordinates reset to Level 1's portal.
  * *HAL*: `SOUND_WARP` is present in `env.get_sounds()`.
  * *Edge Wall Elision*: `env.assert_outer_border_walls(self)` passes.

---

### Scenario 2: Cooperative Multiplayer Playthrough
* **Concept**: Two players join. They are split into separate paths by walls. Player 0 navigates their path to collect a key, then uses it to unlock a door network. Due to the 8-way flood fill door mechanics, unlocking Player 0's door automatically clears Player 1's door. Player 1, now unblocked, collects money and joins Player 0 at the stairs.
* **Core Features Verified**: F-01, F-03, F-04, F-09, F-10.

#### A. Map Layout
We design two paths branching from the starting portal at `(10, 10)`.

```python
def make_scenario2_map(env):
    m = [env.TILE_SPACE] * env.MAP_SIZE
    
    # 1. Edge Wall Elision Setup
    for x in range(60):
        m[0 * 60 + x] = env.TILE_WALL
        m[29 * 60 + x] = env.TILE_WALL
    for y in range(30):
        m[y * 60 + 0] = env.TILE_WALL
        m[y * 60 + 59] = env.TILE_WALL
        
    # 2. Portal TILE_UP at (10, 10)
    m[10 * 60 + 10] = env.TILE_UP
    # Player 0 spawns at (10, 9) (offset 0, -1)
    # Player 1 spawns at (11, 10) (offset 1, 0)
    
    # 3. Path 0 (Player 0) - Goes Up
    m[7 * 60 + 10] = env.TILE_KEY    # Key at (10, 7)
    
    # 4. Door Network (Diagonal/Orthogonal connected doors)
    m[5 * 60 + 10] = env.TILE_DOOR   # Player 0's door at (10, 5)
    m[6 * 60 + 11] = env.TILE_DOOR   # Connector 1
    m[7 * 60 + 12] = env.TILE_DOOR   # Connector 2
    m[8 * 60 + 12] = env.TILE_DOOR   # Connector 3
    m[9 * 60 + 12] = env.TILE_DOOR   # Connector 4
    m[10 * 60 + 13] = env.TILE_DOOR  # Player 1's door at (13, 10)
    
    # 5. Path 1 (Player 1) - Goes Right
    m[10 * 60 + 15] = env.TILE_MONEY # Money at (15, 10)
    
    # 6. Destination Stairs
    m[4 * 60 + 12] = env.TILE_DOWN   # Stairs at (12, 4)
    
    # 7. Restricting Walls
    # Separator wall between Path 0 and Path 1
    for y in range(5, 10):
        m[y * 60 + 9] = env.TILE_WALL
        m[y * 60 + 11] = env.TILE_WALL
    return m
```

#### B. Step-by-Step Execution & Input Sequence
* **Setup**: Call `env.join_player(1)` before starting. Player 0 starts at `(10, 9)`, Player 1 at `(11, 10)`.
* **Tick 0**: Input: Player 0 = `BUTTON_UP`, Player 1 = `BUTTON_RIGHT`.
  * Player 0 moves to `(10, 8)`.
  * Player 1 moves to `(12, 10)`.
* **Ticks 1–3**: Input `[0, 0, 0, 0]`. Cooldowns reset.
* **Tick 4**: Input: Player 0 = `BUTTON_UP`, Player 1 = `BUTTON_RIGHT`.
  * Player 0 moves to `(10, 7)` and collects key. `player_keys[0] = 1`.
  * Player 1 attempts to move to `(13, 10)` (door) but has no keys. Player 1 is **blocked** and remains at `(12, 10)`.
* **Ticks 5–7**: Input `[0, 0, 0, 0]`. Cooldowns reset.
* **Tick 8**: Input: Player 0 = `BUTTON_UP`, Player 1 = `0`.
  * Player 0 moves to `(10, 6)`.
* **Ticks 9–11**: Input `[0, 0, 0, 0]`. Cooldowns reset.
* **Tick 12**: Input: Player 0 = `BUTTON_UP`, Player 1 = `0`.
  * Player 0 steps onto `(10, 5)` (door) with a key. Door is unlocked, initiating a flood fill that turns all 6 connected door tiles (including `(13, 10)`) into `TILE_SPACE`. Player 0 moves to `(10, 5)`.
* **Ticks 13–15**: Input `[0, 0, 0, 0]`. Cooldowns reset.
* **Tick 16**: Input: Player 0 = `BUTTON_RIGHT`, Player 1 = `BUTTON_RIGHT`.
  * Player 0 moves to `(11, 5)`.
  * Player 1 moves to `(13, 10)` (now empty space!).
* **Ticks 17–19**: Input `[0, 0, 0, 0]`. Cooldowns reset.
* **Tick 20**: Input: Player 0 = `BUTTON_DOWN | BUTTON_RIGHT`, Player 1 = `BUTTON_RIGHT`.
  * Player 0 moves diagonally to `(12, 6)`.
  * Player 1 moves to `(14, 10)`.
* **Ticks 21–23**: Input `[0, 0, 0, 0]`. Cooldowns reset.
* **Tick 24**: Input: Player 0 = `BUTTON_UP`, Player 1 = `BUTTON_RIGHT`.
  * Player 0 moves to `(12, 5)`.
  * Player 1 moves to `(15, 10)` and collects money. `player_score[1] += 100`.
* **Ticks 25–27**: Input `[0, 0, 0, 0]`. Cooldowns reset.
* **Tick 28**: Input: Player 0 = `BUTTON_UP`, Player 1 = `0`.
  * Player 0 moves to `(12, 4)` (stairs), triggering level transition to Level 1.

#### C. Double-Assert Checkpoints (State + HAL)
* **Checkpoint 1 (After Tick 4 - Key Collection & Blocked Movement)**:
  * *Globals*: `player_x[0] == 10`, `player_y[0] == 7`, `player_keys[0] == 1`.
  * *Globals*: `player_x[1] == 12`, `player_y[1] == 10`, `player_keys[1] == 0`.
  * *HAL*: `SOUND_KEY` is present.
* **Checkpoint 2 (After Tick 12 - Flood Fill Unlock)**:
  * *Globals*: `player_x[0] == 10`, `player_y[0] == 5`, `player_keys[0] == 0`.
  * *Map Check*: The door at `(10, 5)` and the door at `(13, 10)` are both `TILE_SPACE`. All connector door tiles are `TILE_SPACE`.
  * *HAL*: `SOUND_KEY` is present.
* **Checkpoint 3 (After Tick 24 - Money Picked Up)**:
  * *Globals*: `player_x[1] == 15`, `player_y[1] == 10`, `player_score[1] == 100`.
  * *HAL*: `SOUND_KEY` is present.
* **Checkpoint 4 (After Tick 28 - Transition)**:
  * *Globals*: `current_level == 1`.
  * *HAL*: `SOUND_WARP` is present.
  * *Edge Wall Elision*: `env.assert_outer_border_walls(self)` passes.

---

### Scenario 3: Game Over Reset Playthrough
* **Concept**: Player starts on an advanced level with a high score, keys, and bombs in their inventory. They are surrounded by four powerful monsters. Over several ticks, the sparse grid monster rotor activates the monsters, which attack the player. The player takes fatal damage, triggering a game over. The test asserts that the engine completely resets to Level 0, wiping all scores and inventories, and re-joining only Player 0.
* **Core Features Verified**: F-01, F-07, F-09, F-10.

#### A. Map Layout
A custom map representing a room where the starting portal is surrounded by 4 level 3 monsters.

```python
def make_scenario3_map(env):
    m = [env.TILE_SPACE] * env.MAP_SIZE
    
    # 1. Edge Wall Elision Setup
    for x in range(60):
        m[0 * 60 + x] = env.TILE_WALL
        m[29 * 60 + x] = env.TILE_WALL
    for y in range(30):
        m[y * 60 + 0] = env.TILE_WALL
        m[y * 60 + 59] = env.TILE_WALL
        
    # 2. Portal TILE_UP at (10, 10)
    m[10 * 60 + 10] = env.TILE_UP
    # Player 0 spawns at (10, 9) (offset 0, -1)
    
    # 3. Surround the player's spawn point with TILE_MONSTER3 (deals 30 damage each)
    m[8 * 60 + 10] = env.TILE_MONSTER3   # Above at (10, 8)
    m[9 * 60 + 9] = env.TILE_MONSTER3    # Left at (9, 9)
    m[9 * 60 + 11] = env.TILE_MONSTER3   # Right at (11, 9)
    m[11 * 60 + 10] = env.TILE_MONSTER3  # Below at (10, 11)
    
    return m
```

#### B. Step-by-Step Execution & Input Sequence
* **Pre-conditions**:
  * Load our death map.
  * Explicitly set advanced player stats via wrapper:
    * `env.current_level = 3`
    * `env.set_player_health(0, 100)`
    * `env.set_player_score(0, 1500)`
    * `env.set_player_keys(0, 4)`
    * `env.set_player_bombs(0, 2)`
    * `env.monster_rotor = 0`
* **Execution**: We inject `0` inputs for 16 consecutive steps. This cycles `monster_rotor` through all 16 sparse grid slots, ensuring every monster ticks exactly once.
  * **Tick 2**: `monster_rotor` reaches 2. The monster at `(10, 8)` ticks, moves onto the player at `(10, 9)`, deals 30 damage, and is destroyed. Player health = 70.
  * **Tick 5**: `monster_rotor` reaches 5. The monster at `(9, 9)` ticks, moves onto the player at `(10, 9)`, deals 30 damage. Player health = 40.
  * **Tick 7**: `monster_rotor` reaches 7. The monster at `(11, 9)` ticks, moves onto the player at `(10, 9)`, deals 30 damage. Player health = 10.
  * **Tick 14**: `monster_rotor` reaches 14. The monster at `(10, 11)` ticks, moves onto the player at `(10, 9)`, deals 30 damage. Player health drops to 0 (death).
  * **Death & Reset**: The player tile is cleared immediately. Since all joined players are dead, `end_game()` triggers in the same step, resetting the engine to Level 0.

#### C. Double-Assert Checkpoints (State + HAL)
* **Checkpoint 1 (Before death, e.g., Tick 3)**:
  * *Globals*: `player_health[0] == 70` (took 30 damage from first monster).
  * *HAL*: `SOUND_HIT` is present.
* **Checkpoint 2 (After Tick 15 - Game Over Reset)**:
  * *Globals*: `current_level == 0` (reset to Level 0).
  * *Globals*: `player_health[0] == 100` (refilled).
  * *Globals*: `player_score[0] == 0` (wiped).
  * *Globals*: `player_keys[0] == 0` (wiped).
  * *Globals*: `player_bombs[0] == 0` (wiped).
  * *Globals*: `player_joined[0] == True`, all other player joined states are `False`.
  * *Map Check*: `dandy_map` is no longer our death map; it is now the game's actual Level 0 map loaded from ROM.
  * *HAL*: `SOUND_DIE` is present.
  * *Edge Wall Elision*: `env.assert_outer_border_walls(self)` passes on the newly loaded Level 0 map.

---

### Scenario 4: Combative Maze Scenario
* **Concept**: Player enters a corridor packed with multiple monsters and a generator. The player strategically shoots one monster with an arrow, then uses a Smart Bomb to obliterate all remaining monsters and generators within their screen viewport, proving that off-screen entities are untouched.
* **Core Features Verified**: F-01, F-05, F-06, F-07, F-08.

#### A. Map Layout
A long corridor containing a player, two monsters, a generator, and a far-away monster.

```python
def make_scenario4_map(env):
    m = [env.TILE_SPACE] * env.MAP_SIZE
    
    # 1. Edge Wall Elision Setup
    for x in range(60):
        m[0 * 60 + x] = env.TILE_WALL
        m[29 * 60 + x] = env.TILE_WALL
    for y in range(30):
        m[y * 60 + 0] = env.TILE_WALL
        m[y * 60 + 59] = env.TILE_WALL
        
    # 2. Portal TILE_UP at (2, 3)
    m[3 * 60 + 2] = env.TILE_UP
    # Player 0 spawns at (2, 2) (offset 0, -1)
    
    # 3. Corridor Entities
    m[2 * 60 + 6] = env.TILE_MONSTER1   # Monster 1 at (6, 2) (in viewport)
    m[2 * 60 + 7] = env.TILE_MONSTER1   # Monster 2 at (7, 2) (in viewport)
    m[2 * 60 + 10] = env.TILE_GENERATOR1 # Generator 1 at (10, 2) (in viewport)
    m[2 * 60 + 15] = env.TILE_MONSTER2  # Monster 3 at (15, 2) (in viewport)
    m[2 * 60 + 45] = env.TILE_MONSTER1  # Monster 4 at (45, 2) (OFF-SCREEN / outside viewport)
    
    # 4. Corridor Walls (Enclosing the narrow horizontal hallway)
    for x in range(1, 48):
        m[1 * 60 + x] = env.TILE_WALL   # Hallway ceiling
        if x != 2:
            m[3 * 60 + x] = env.TILE_WALL # Hallway floor
    m[2 * 60 + 48] = env.TILE_WALL      # Hallway end wall
    
    return m
```

#### B. Step-by-Step Execution & Input Sequence
* **Pre-conditions**:
  * Set `env.set_player_bombs(0, 1)`.
  * Player 0 is at `(2, 2)` facing Up.
* **Tick 0**: Input `BUTTON_RIGHT`. Player turns Right (`player_dir = 2`) and moves to `(3, 2)`. Cooldown = 3.
* **Ticks 1–3**: Input `0`. Cooldown resets.
* **Tick 4**: Input `BUTTON_FIRE`. Player shoots an arrow Right. Arrow is created at `(3, 2)` and immediately steps to `(4, 2)`.
* **Tick 5**: Input `0`. Arrow steps to `(5, 2)`.
* **Tick 6**: Input `0`. Arrow steps to `(6, 2)`, hitting the first monster. Monster is destroyed, arrow dies, `SOUND_HIT` plays.
* **Tick 7**: Input `0`.
* **Tick 8**: Input `BUTTON_BOMB`. Smart Bomb is triggered!
  * Viewport centered at player `(3, 2)` spans `x` in `[0, 19]` and `y` in `[0, 9]`.
  * The remaining entities within viewport: `(7, 2)` (monster), `(10, 2)` (generator), and `(15, 2)` (monster) are destroyed and replaced with `TILE_SPACE`.
  * The monster at `(45, 2)` is outside the viewport and remains **untouched**.
  * `player_bombs[0]` decrements to 0.
  * `SOUND_BOMB` is played.

#### C. Double-Assert Checkpoints (State + HAL)
* **Checkpoint 1 (After Tick 6 - Arrow Impact)**:
  * *Globals*: `arrow_dir[0] == -1` (inactive).
  * *Map Check*: `dandy_map[2 * 60 + 6]` is now `TILE_SPACE`.
  * *HAL*: `SOUND_SHOOT` and `SOUND_HIT` are present.
* **Checkpoint 2 (After Tick 8 - Smart Bomb Viewport Clear)**:
  * *Globals*: `player_bombs[0] == 0`.
  * *Map Check*: The tiles at `(7, 2)`, `(10, 2)`, and `(15, 2)` are all `TILE_SPACE`.
  * *Off-screen Check*: The tile at `(45, 2)` is still `TILE_MONSTER1` (100% frozen and untouched).
  * *HAL*: `SOUND_BOMB` is present.
  * *Edge Wall Elision*: `env.assert_outer_border_walls(self)` passes.

---

### Scenario 5: Viewport Scrolling & Boundary Scenario
* **Concept**: Player 0 moves across a large open 60x30 map from the top-left corner `(5, 4)` to the bottom-right corner `(55, 25)`. We verify that the camera viewport scrolls dynamically, clamps correctly at the boundaries, and registers hardware sprites at correct relative viewport coordinates.
* **Core Features Verified**: F-01, F-09.

#### A. Map Layout
A completely open map with walls only at the outer borders.

```python
def make_scenario5_map(env):
    m = [env.TILE_SPACE] * env.MAP_SIZE
    
    # 1. Edge Wall Elision Setup (Strict outer borders)
    for x in range(60):
        m[0 * 60 + x] = env.TILE_WALL
        m[29 * 60 + x] = env.TILE_WALL
    for y in range(30):
        m[y * 60 + 0] = env.TILE_WALL
        m[y * 60 + 59] = env.TILE_WALL
        
    # 2. Portal TILE_UP at (5, 5)
    m[5 * 60 + 5] = env.TILE_UP
    # Player 0 spawns at (5, 4) (offset 0, -1)
    
    return m
```

#### B. Step-by-Step Execution & Checkpoints
Instead of hardcoding a massive tick list, we programmatically navigate the player using a pathfinding helper in Python that steps the game loop and respects the 4-tick movement cooldown.

```python
def walk_to_checkpoint(env, test_case, target_x, target_y):
    """Simulates real-world tick-by-tick inputs to walk the player to a target."""
    while True:
        cx = env.get_player_x(0)
        cy = env.get_player_y(0)
        if cx == target_x and cy == target_y:
            break
            
        dx = target_x - cx
        dy = target_y - cy
        
        buttons = 0
        if dx > 0:
            buttons |= env.BUTTON_RIGHT
        elif dx < 0:
            buttons |= env.BUTTON_LEFT
            
        if dy > 0:
            buttons |= env.BUTTON_DOWN
        elif dy < 0:
            buttons |= env.BUTTON_UP
            
        # Step the game loop (Tick 1 of movement)
        env.step([buttons, 0, 0, 0])
        # Wait out the 3 cooldown ticks
        for _ in range(3):
            env.step([0, 0, 0, 0])
```

We execute this walk to 4 key checkpoints:

#### Checkpoint 1: Spawn Point (5, 4) - Left/Top Borders Clamped
* **Camera Offset Check**:
  * Centering calculation: `vp_left = clamp(5 - 10, 0, 40) = 0`, `vp_top = clamp(4 - 5, 0, 20) = 0`.
  * Assert that `env.get_camera()` returns `(0, 0)`.
* **Sprite Mapping Check**:
  * Player tile is drawn at relative coordinates: `sx = 5 - 0 = 5`, `sy = 4 - 0 = 4`.
  * Pixel coordinates passed to hardware sprites: `x = 5 * 8 = 40`, `y = 4 * 8 = 32`.
  * Call `env.draw_viewport(0)`. Assert that the active sprite matches `tile_id >= 24` and is at `x=40, y=32`.

#### Checkpoint 2: Top-Border Scrolling (15, 4) - Top Clamped, Left Scrolling
* Execute `walk_to_checkpoint(env, self, 15, 4)`.
* **Camera Offset Check**:
  * Centering calculation: `vp_left = clamp(15 - 10, 0, 40) = 5`, `vp_top = clamp(4 - 5, 0, 20) = 0`.
  * Assert that `env.get_camera()` returns `(5, 0)`.
* **Sprite Mapping Check**:
  * Player relative coordinates: `sx = 15 - 5 = 10`, `sy = 4 - 0 = 4`.
  * Pixel coordinates: `x = 10 * 8 = 80`, `y = 4 * 8 = 32`.
  * Call `env.draw_viewport(0)`. Assert active sprite is at `x=80, y=32`.

#### Checkpoint 3: Center of Map (35, 15) - Fully Scrolling (No Clamps)
* Execute `walk_to_checkpoint(env, self, 35, 15)`.
* **Camera Offset Check**:
  * Centering calculation: `vp_left = clamp(35 - 10, 0, 40) = 25`, `vp_top = clamp(15 - 5, 0, 20) = 10`.
  * Assert that `env.get_camera()` returns `(25, 10)`.
* **Sprite Mapping Check**:
  * Player relative coordinates: `sx = 35 - 25 = 10`, `sy = 15 - 10 = 5`.
  * Pixel coordinates: `x = 10 * 8 = 80`, `y = 5 * 8 = 40`.
  * Call `env.draw_viewport(0)`. Assert active sprite is at `x=80, y=40`.

#### Checkpoint 4: Bottom-Right Corner (55, 25) - Right/Bottom Borders Clamped
* Execute `walk_to_checkpoint(env, self, 55, 25)`.
* **Camera Offset Check**:
  * Centering calculation: `vp_left = clamp(55 - 10, 0, 40) = 40`, `vp_top = clamp(25 - 5, 0, 20) = 20`.
  * Assert that `env.get_camera()` returns `(40, 20)`.
* **Sprite Mapping Check**:
  * Player relative coordinates: `sx = 55 - 40 = 15`, `sy = 25 - 20 = 5`.
  * Pixel coordinates: `x = 15 * 8 = 120`, `y = 5 * 8 = 40`.
  * Call `env.draw_viewport(0)`. Assert active sprite is at `x=120, y=40`.
* **Edge Wall Elision**:
  * `env.assert_outer_border_walls(self)` passes.

---

## 3. Verification Plan & Test Suite Structure

The proposed tests should be implemented in `dandy-gb/tests/test_tier4.py` within the `TestTier4` class. This class will inherit from `unittest.TestCase` and leverage the `DandyEnv` wrapper.

### Test Harness Framework Execution
To verify these scenarios once they are written into `test_tier4.py`, the following commands are run:
1. Recompile the test shared library to include any core C engine changes:
   ```bash
   make test_lib
   ```
2. Execute the Python E2E test suite:
   ```bash
   make test
   ```

All tests will run deterministically in isolation, copying the shared library into a separate temporary directory for each test case to prevent any state leakage between runs.
