# Milestone 4: Tier 4 E2E Play Scenarios Design Report

This report designs and details the Tier 4 E2E Play Scenarios for the Dandy Dungeon Game Boy (`dandy-gb`) implementation. These scenarios represent typical, complex, multi-step real-world playthroughs designed to run deterministically within the host-side offline testing harness.

---

## 1. Executive Summary

This design provides **5 distinct, complex, multi-step playthrough scenarios** that verify the end-to-end integration of the game's core systems. All designs are requirement-driven, opaque-box, and assert on both internal state (engine globals) and external side-effects (mock HAL graphics, sprites, audio, and camera) in compliance with the **Double-Assert Rule** and **Edge Wall Elision** constraints.

### Scenarios Overview
1. **Scenario 1: Full Level 0 Playthrough**: A single-player run demonstrating navigation, key collection, door unlocking, combat (shooting), food collection, and transitioning to Level 1.
2. **Scenario 2: Cooperative Multiplayer Playthrough**: A two-player run demonstrating independent navigation, synchronized movement, cooperative door opening via flood-fill, separate inventory scoring, and coordinated level exit.
3. **Scenario 3: Game Over Reset Playthrough**: A run demonstrating player damage and death by monsters, followed by a complete game-state reset, reloading Level 0, and wiping inventories and scores.
4. **Scenario 4: Combative Maze Scenario**: A high-intensity combat run utilizing a smart bomb to clear a viewport-clamped cluster of monsters/generators, followed by precise arrow shots to clear remaining targets down a corridor.
5. **Scenario 5: Viewport Scrolling & Boundary Scenario**: A diagonal traversal verifying camera centering, boundary clamping at all four edges, and viewport-relative hardware sprite coordinates.

---

## 2. Testing Framework & Assertion Rules

To ensure maximum rigor, every scenario follows two fundamental test constraints:

### 2.1 The Double-Assert Rule
For every critical step, the test must assert on:
1. **Internal Globals**: Player coordinates (`player_x`, `player_y`), health, score, keys, bombs, arrow status, and current level.
2. **Mock HAL Side-Effects**:
   - **Sprites**: Using `mock_get_sprites()` to check that hardware sprites are active and registered at the correct viewport-relative pixel coordinates (`x = sx * 8`, `y = sy * 8`).
   - **Sound**: Using `mock_get_sounds()` to verify the exact retro sound effect IDs played during the tick.
   - **Camera**: Using `mock_get_camera()` to verify that the camera viewport coordinates (`vp_left`, `vp_top`) are correctly calculated.
   - **HUD**: Checking `mock_get_hud_update_count()` to verify HUD redraws occur when state changes.

### 2.2 Edge Wall Elision Verification
To ensure that map boundaries are never corrupted or bypassed, the test must execute a border sweep before, during, and after each scenario. The helper `assert_outer_border_walls(self)` in `dandy_env.py` checks that all 176 border tiles of the 60x30 map (`y = 0`, `y = 29`, `x = 0`, `x = 59`) are strictly set to `TILE_WALL` (1).

---

## 3. Play Scenario Designs

---

### Scenario 1: Full Level 0 Playthrough

#### 1. Objective & Features Tested
Tests a complete single-player level walkthrough: starts at entrance, collects a key, unlocks a door, shoots a monster, collects food, and exits via stairs to Level 1.
- **Features**: F-01 (Movement & Timing), F-03 (Item Collection), F-04 (Door & Key Mechanics), F-05 (Combat & Projectiles), F-10 (Level Transitions).

#### 2. Map Layout (Custom 60x30)
We define a custom map layout where the playable area is enclosed in wall borders, forming a narrow corridor.
- **Borders**: All outer borders (`x=0`, `x=59`, `y=0`, `y=29`) are `TILE_WALL` (1).
- **Portal (`TILE_UP`, 3)**: Placed at `(10, 10)`.
- **Player 0 Spawn**: Relocated to `(10, 9)` (since spawn offset for Player 0 is `(0, -1)`).
- **Key (`TILE_KEY`, 5)**: Placed at `(10, 8)`.
- **Door (`TILE_DOOR`, 2)**: Placed at `(10, 12)`.
- **Monster (`TILE_MONSTER1`, 9)**: Placed at `(11, 13)`.
- **Food (`TILE_FOOD`, 6)**: Placed at `(12, 13)`.
- **Stairs (`TILE_DOWN`, 4)**: Placed at `(12, 15)`.
- **Walls (`TILE_WALL`, 1)**: Placed at `x=9` (for `y=8..15`) and `x=11` (for `y=8..12`) to form a corridor.

#### 3. Input Injection Sequence (Tick-by-Tick)
Movement cooldown is 4 ticks. Input is injected at the start of each step (every 4 ticks), with empty inputs in between.

| Tick | Player 0 Input | Expected Action / State Change |
| :--- | :--- | :--- |
| **0** | `BUTTON_UP` | Move Up to `(10, 8)`. Collect Key. Keys = 1. Play `SOUND_KEY`. |
| **1-3** | `0` | Cooldown. Move timer decrements `3 -> 2 -> 1 -> 0`. |
| **4** | `BUTTON_DOWN` | Move Down to `(10, 9)`. Dir = 4 (Down). |
| **5-7** | `0` | Cooldown. Move timer decrements to 0. |
| **8** | `BUTTON_DOWN` | Move Down to `(10, 10)` (portal tile). |
| **9-11** | `0` | Cooldown. Move timer decrements to 0. |
| **12** | `BUTTON_DOWN` | Move Down to `(10, 11)`. |
| **13-15** | `0` | Cooldown. Move timer decrements to 0. |
| **16** | `BUTTON_DOWN` | Move Down into `(10, 12)` (Door). Unlock door (keys = 0). Play `SOUND_KEY`. |
| **17-19** | `0` | Cooldown. Move timer decrements to 0. |
| **20** | `BUTTON_DOWN` | Move Down to `(10, 13)`. |
| **21-23** | `0` | Cooldown. Move timer decrements to 0. |
| **24** | `BUTTON_RIGHT \| BUTTON_FIRE` | Turn Right. Shoot Arrow. Arrow spawned at `(10, 13)` facing Right (dir 2). Play `SOUND_SHOOT`. Player movement blocked by monster at `(11, 13)`. Arrow steps and hits monster at `(11, 13)`. Monster destroyed. Play `SOUND_HIT`. |
| **25-27** | `0` | Cooldown. Move timer decrements to 0. Arrow inactive. |
| **28** | `BUTTON_RIGHT` | Move Right to `(11, 13)` (cleared space). |
| **29-31** | `0` | Cooldown. Move timer decrements to 0. |
| **32** | `BUTTON_RIGHT` | Move Right to `(12, 13)`. Collect Food. Health = 200. Play `SOUND_FOOD`. |
| **33-35** | `0` | Cooldown. Move timer decrements to 0. |
| **36** | `BUTTON_DOWN` | Move Down to `(12, 14)`. |
| **37-39** | `0` | Cooldown. Move timer decrements to 0. |
| **40** | `BUTTON_DOWN` | Move Down to `(12, 15)` (Stairs). Play `SOUND_WARP`. Load Level 1. Reset player to Level 1 spawn portal `(57, 1)`. |

#### 4. Step-by-Step Logic & Assertions

##### Initialization (Tick 0, before step)
- Assert Player 0 is joined, health = 100, keys = 0, score = 0, position = `(10, 9)`.
- Assert `current_level = 0`.
- Verify borders are walls: `self.env.assert_outer_border_walls(self)`.

##### Checkpoint 1 (Tick 1, after Key Collection)
- **Globals**: `player_x[0] = 10`, `player_y[0] = 8`, `player_keys[0] = 1`.
- **HAL Side-Effects**: `SOUND_KEY` is in sound logs. Sprite 0 active at `x = 80`, `y = 64` (viewport `vp_left=0`, `vp_top=0`).

##### Checkpoint 2 (Tick 17, after Door Unlocking)
- **Globals**: `player_x[0] = 10`, `player_y[0] = 12`, `player_keys[0] = 0`.
- **HAL Side-Effects**: `SOUND_KEY` played. `dandy_map` tile at `(10, 12)` is now `TILE_SPACE` (0).

##### Checkpoint 3 (Tick 25, after Combat Shoot)
- **Globals**: `player_x[0] = 10`, `player_y[0] = 13`, `arrow_dir[0] = -1` (destroyed).
- **HAL Side-Effects**: `SOUND_SHOOT` and `SOUND_HIT` in sound logs. `dandy_map` tile at `(11, 13)` is now `TILE_SPACE` (0).

##### Checkpoint 4 (Tick 33, after Food Collection)
- **Globals**: `player_x[0] = 12`, `player_y[0] = 13`, `player_health[0] = 200`.
- **HAL Side-Effects**: `SOUND_FOOD` played.

##### Final State (Tick 41, after Level Transition)
- **Globals**: `current_level = 1`, `player_x[0] = 57`, `player_y[0] = 1`, `player_health[0] = 200` (preserved).
- **HAL Side-Effects**: `SOUND_WARP` played. Camera updated to Level 1 spawn centroid.
- **Border Check**: `self.env.assert_outer_border_walls(self)` passes on the newly loaded Level 1 map.

---

### Scenario 2: Cooperative Multiplayer Playthrough

#### 1. Objective & Features Tested
Cooperative puzzle solving: two players join, navigate separate corridors, one player collects a key to unlock a shared multi-tile door (flood fill) to clear both paths, they collect separate scores, meet, and exit.
- **Features**: F-01 (Movement & Timing), F-03 (Item Collection), F-04 (Door & Key Mechanics), F-09 (Multiplayer & Viewport), F-10 (Level Transitions).

#### 2. Map Layout (Custom 60x30)
- **Portal (`TILE_UP`, 3)**: Placed at `(10, 10)`.
- **Player 0 Spawn**: `(10, 9)`. **Player 1 Spawn**: `(11, 10)`.
- **Key (`TILE_KEY`, 5)**: Placed at `(12, 8)` (accessible only by Player 0).
- **Shared Double Door (`TILE_DOOR`, 2)**: Placed at `(14, 8)`, `(14, 9)`, and `(14, 10)` (vertical wall of doors blocking both corridors).
- **Gold P0 (`TILE_MONEY`, 7)**: Placed at `(15, 8)`.
- **Gold P1 (`TILE_MONEY`, 7)**: Placed at `(15, 10)`.
- **Stairs (`TILE_DOWN`, 4)**: Placed at `(17, 9)`.
- **Separating Walls (`TILE_WALL`, 1)**: Placed at `(11, 9)`, `(12, 9)`, `(13, 9)`, `(15, 9)` to keep the top and bottom paths separate.

#### 3. Input Injection Sequence (Tick-by-Tick)

| Tick | Player 0 Input | Player 1 Input | Expected Action / State Change |
| :--- | :--- | :--- | :--- |
| **0** | `BUTTON_UP` | `BUTTON_RIGHT` | P0 moves to `(10, 8)`. P1 moves to `(12, 10)`. |
| **1-3** | `0` | `0` | Cooldown. |
| **4** | `BUTTON_RIGHT` | `BUTTON_RIGHT` | P0 moves to `(11, 8)`. P1 moves to `(13, 10)`. |
| **5-7** | `0` | `0` | Cooldown. |
| **8** | `BUTTON_RIGHT` | `BUTTON_RIGHT` | P0 moves to `(12, 8)` and collects Key (keys=1). P1 tries to move to `(14, 10)` but is blocked by Door. P1 stays at `(13, 10)`. |
| **9-11** | `0` | `0` | Cooldown. |
| **12** | `BUTTON_RIGHT` | `0` | P0 moves to `(13, 8)`. P1 waits. |
| **13-15** | `0` | `0` | Cooldown. |
| **16** | `BUTTON_RIGHT` | `0` | P0 moves to `(14, 8)`. Unlocks door (keys=0). Flood fill clears `(14, 8)`, `(14, 9)`, and `(14, 10)`. P1 corridor now open! |
| **17-19** | `0` | `0` | Cooldown. |
| **20** | `BUTTON_RIGHT` | `BUTTON_RIGHT` | P0 moves to `(15, 8)` (collects Gold, score=100). P1 moves to `(14, 10)` (now open). |
| **21-23** | `0` | `0` | Cooldown. |
| **24** | `BUTTON_DOWN \| BUTTON_RIGHT` | `BUTTON_RIGHT` | P0 moves to `(16, 9)`. P1 moves to `(15, 10)` (collects Gold, score=100). |
| **25-27** | `0` | `0` | Cooldown. |
| **28** | `BUTTON_RIGHT` | `BUTTON_UP \| BUTTON_RIGHT` | P0 moves to `(17, 9)` (Stairs) and triggers Level Transition. P1 tries to move to `(16, 9)` but is blocked by P0 (if transition didn't happen, but transition is instant). |

#### 4. Step-by-Step Logic & Assertions

##### Initialization (Tick 0)
- Call `dandy_join_player(0)` and `dandy_join_player(1)`.
- Assert both players active, P0 at `(10, 9)`, P1 at `(11, 10)`.
- Verify border walls.

##### Checkpoint 1 (Tick 9, Player 1 Blocked, Player 0 has Key)
- **Globals**: `player_x[0] = 12`, `player_y[0] = 8`, `player_keys[0] = 1`.
- **Globals**: `player_x[1] = 13`, `player_y[1] = 10`, `player_keys[1] = 0` (blocked).
- **HAL Side-Effects**: `SOUND_KEY` played. `dandy_map` tile at `(14, 10)` remains `TILE_DOOR` (2).

##### Checkpoint 2 (Tick 17, Shared Door Cleared)
- **Globals**: `player_x[0] = 14`, `player_y[0] = 8`, `player_keys[0] = 0`.
- **HAL Side-Effects**: `SOUND_KEY` played (door unlock).
- **Map Assertion**: `dandy_map` at `(14, 8)`, `(14, 9)`, and `(14, 10)` are ALL `TILE_SPACE` (0) due to flood fill.

##### Checkpoint 3 (Tick 25, Scoring & Positioning)
- **Globals**: P0 score = 100, P0 position = `(16, 9)`.
- **Globals**: P1 score = 100, P1 position = `(15, 10)`.
- **HAL Side-Effects**: `SOUND_KEY` played twice (gold collections).

##### Final State (Tick 29, Transition)
- **Globals**: `current_level = 1`. Both players relocated to Level 1 portal spawn points.
- **HAL Side-Effects**: `SOUND_WARP` in sound logs.
- **Border Check**: `assert_outer_border_walls` passes.

---

### Scenario 3: Game Over Reset Playthrough

#### 1. Objective & Features Tested
Asserts that when all players die (health reaches 0), the game triggers a full reset: resets `current_level` to 0, wipes all player scores, keys, bombs, restores health to 100, and reloads Level 0.
- **Features**: F-07 (Monster Behavior), F-09 (Multiplayer & Viewport), Game Over Reset Logic.

#### 2. Map Layout (Level 1 + Custom Entities)
To test a true reset from another level:
- We load Level 1 (`load_level(1)`).
- We set the player starting position to `(10, 10)` on Level 1.
- We place a high-damage Monster 3 (`TILE_MONSTER3`, 11) at `(11, 10)`.
- We initialize the player with high stats to verify they are wiped: health = 30, keys = 5, bombs = 3, score = 1200.

#### 3. Input Injection Sequence (Tick-by-Tick)
This playthrough requires exactly **1 tick** to execute death and reset. We set up the rotor to tick the monster immediately.
- Before step: `monster_rotor = 10`.
- Tick 0: Input `[0, 0, 0, 0]`.

| Tick | Input | Expected Action / State Change |
| :--- | :--- | :--- |
| **0** | `0` | `monster_rotor` increments to 11. Monster 3 at `(11, 10)` ticks (visible in viewport), moves Left to `(10, 10)`, collides with Player 0. Deals 30 damage. Player 0 health: `30 - 30 = 0`. All players dead. `end_game()` triggered. |

#### 4. Step-by-Step Logic & Assertions

##### Pre-Step Setup (Tick 0, before step)
- Load Level 1: `self.env.load_level(1)`.
- Set Player 0 position = `(10, 10)`, health = 30, keys = 5, bombs = 3, score = 1200.
- Write Player 0 tile to `dandy_map` at `(10, 10)`.
- Write Monster 3 tile to `dandy_map` at `(11, 10)`.
- Set `self.env.monster_rotor = 10`.

##### Final State (Tick 1, after death step)
- **Globals**: `current_level = 0` (reset to Level 0).
- **Globals**: `player_health[0] = 100` (restored).
- **Globals**: `player_keys[0] = 0`, `player_bombs[0] = 0`, `player_score[0] = 0` (all wiped).
- **Globals**: Player 0 coordinates reset to Level 0 starting portal spawn `(10, 9)`.
- **Globals**: `player_joined[1]` to `[3]` are `False` (unjoined).
- **HAL Side-Effects**: `SOUND_DIE` in sound logs.
- **Map Assertion**: The map is reloaded to Level 0. `dandy_map` at `(10, 10)` (where player died on Level 1) is now whatever tile Level 0 has there.
- **Border Check**: `assert_outer_border_walls` passes for Level 0.

---

### Scenario 4: Combative Maze Scenario

#### 1. Objective & Features Tested
High-intensity combat scenario: player uses a smart bomb to clear a viewport-confined cluster of monsters and generators, moves forward, and shoots arrows to eliminate a monster and generator further down the corridor (outside the initial viewport).
- **Features**: F-05 (Combat & Projectiles), F-06 (Smart Bomb Action), F-01 (Movement & Timing).

#### 2. Map Layout (Custom 60x30)
- **Player 0 Spawn**: `(10, 10)`, facing Right (dir 2).
- **Corridor**: Horizontal corridor along `y = 10` from `x = 10` to `x = 30`.
- **Items**: Player starts with 1 bomb (`player_bombs[0] = 1`) and 0 keys.
- **Viewport Bounds**: With player at `(10, 10)`, viewport range is `x` in `[0, 19]`, `y` in `[5, 14]`.
- **Entities inside initial viewport**:
  - Generator 1 (`TILE_GENERATOR1`, 13) at `(15, 10)`.
  - Monster 2 (`TILE_MONSTER2`, 10) at `(18, 10)`.
- **Entities outside initial viewport**:
  - Monster 1 (`TILE_MONSTER1`, 9) at `(22, 10)`.
  - Generator 2 (`TILE_GENERATOR2`, 14) at `(25, 10)`.

#### 3. Input Injection Sequence (Tick-by-Tick)

| Tick | Player 0 Input | Expected Action / State Change |
| :--- | :--- | :--- |
| **0** | `BUTTON_BOMB` | Trigger Smart Bomb. Bombs = 0. Play `SOUND_BOMB`. Generator 1 at `(15, 10)` and Monster 2 at `(18, 10)` are inside the viewport and destroyed. Monster 1 at `(22, 10)` and Generator 2 at `(25, 10)` are outside the viewport and unaffected. |
| **1-3** | `0` | Cooldown. |
| **4** | `BUTTON_RIGHT` | Move Right to `(11, 10)`. |
| **5-7** | `0` | Cooldown. |
| **8** | `BUTTON_RIGHT` | Move Right to `(12, 10)`. |
| **9-11** | `0` | Cooldown. |
| **12** | `BUTTON_RIGHT` | Move Right to `(13, 10)`. |
| **13-15** | `0` | Cooldown. |
| **16** | `BUTTON_RIGHT` | Move Right to `(14, 10)`. |
| **17-19** | `0` | Cooldown. |
| **20** | `BUTTON_RIGHT` | Move Right to `(15, 10)` (now empty space). Viewport shifts: `x` in `[5, 24]`. Monster 1 at `(22, 10)` is now visible. Generator 2 at `(25, 10)` is still off-screen. |
| **21-23** | `0` | Cooldown. |
| **24** | `BUTTON_FIRE` | Shoot Arrow Right. Arrow spawned at `(15, 10)`. Play `SOUND_SHOOT`. |
| **25** | `0` | Arrow steps to `(16, 10)`. |
| **26** | `0` | Arrow steps to `(17, 10)`. |
| **27** | `0` | Arrow steps to `(18, 10)`. |
| **28** | `0` | Arrow steps to `(19, 10)`. |
| **29** | `0` | Arrow steps to `(20, 10)`. |
| **30** | `0` | Arrow steps to `(21, 10)`. |
| **31** | `0` | Arrow steps to `(22, 10)`. Hits Monster 1. Monster 1 destroyed. Play `SOUND_HIT`. Arrow destroyed (`arrow_dir = -1`). |
| **32** | `BUTTON_RIGHT` | Move Right to `(16, 10)`. |
| **33-35** | `0` | Cooldown. |
| **36** | `BUTTON_RIGHT` | Move Right to `(17, 10)`. |
| **37-39** | `0` | Cooldown. |
| **40** | `BUTTON_RIGHT` | Move Right to `(18, 10)`. |
| **41-43** | `0` | Cooldown. |
| **44** | `BUTTON_RIGHT` | Move Right to `(19, 10)`. |
| **45-47** | `0` | Cooldown. |
| **48** | `BUTTON_RIGHT` | Move Right to `(20, 10)`. Viewport shifts: `x` in `[10, 29]`. Generator 2 at `(25, 10)` is now visible. |
| **49-51** | `0` | Cooldown. |
| **52** | `BUTTON_FIRE` | Shoot Arrow Right. Arrow spawned at `(20, 10)`. Play `SOUND_SHOOT`. |
| **53** | `0` | Arrow steps to `(21, 10)`. |
| **54** | `0` | Arrow steps to `(22, 10)`. |
| **55** | `0` | Arrow steps to `(23, 10)`. |
| **56** | `0` | Arrow steps to `(24, 10)`. |
| **57** | `0` | Arrow steps to `(25, 10)`. Hits Generator 2. Generator 2 destroyed. Play `SOUND_HIT`. Arrow destroyed. |

#### 4. Step-by-Step Logic & Assertions

##### Checkpoint 1 (Tick 1, after Smart Bomb)
- **Globals**: `player_bombs[0] = 0`.
- **Map Assertion**: `dandy_map` tiles at `(15, 10)` and `(18, 10)` are `TILE_SPACE` (0).
- **Map Assertion**: `dandy_map` tiles at `(22, 10)` (Monster 1) and `(25, 10)` (Generator 2) remain unchanged.
- **HAL Side-Effects**: `SOUND_BOMB` in sound logs.

##### Checkpoint 2 (Tick 31, Arrow hits Monster 1)
- **Globals**: `arrow_dir[0] = -1` (destroyed).
- **Map Assertion**: `dandy_map` tile at `(22, 10)` is `TILE_SPACE` (0).
- **HAL Side-Effects**: `SOUND_SHOOT` (Tick 24) and `SOUND_HIT` (Tick 31) in sound logs.

##### Checkpoint 3 (Tick 57, Arrow hits Generator 2)
- **Globals**: `arrow_dir[0] = -1` (destroyed).
- **Map Assertion**: `dandy_map` tile at `(25, 10)` is `TILE_SPACE` (0).
- **HAL Side-Effects**: `SOUND_SHOOT` (Tick 52) and `SOUND_HIT` (Tick 57) in sound logs.
- **Border Check**: `assert_outer_border_walls` passes.

---

### Scenario 5: Viewport Scrolling & Boundary Scenario

#### 1. Objective & Features Tested
Verifies camera viewport movement and clamping: player moves diagonally from top-left corner `(1, 1)` to bottom-right corner `(58, 28)`. The test asserts correct camera viewport coordinates (`vp_left`, `vp_top`) and verifies that hardware sprites are registered at correct viewport-relative coordinates.
- **Features**: F-09 (Multiplayer & Viewport), F-01 (Movement & Timing).

#### 2. Map Layout (Custom 60x30)
- **Borders**: Enclosed in standard walls.
- **Entities**: Player 0 starts at `(1, 1)`, facing Down-Right. All other tiles in the playable area are `TILE_SPACE` (0).

#### 3. Traversal Path & Inputs
The player travels diagonally Down-Right for 27 steps, reaching `(28, 28)` at Tick 107. Then, the player travels cardinally Right for 30 steps, reaching the final corner `(58, 28)` at Tick 227.
- **Diagonal Step Input**: `BUTTON_DOWN | BUTTON_RIGHT` (injected every 4 ticks from Tick 0 to 104).
- **Cardinal Step Input**: `BUTTON_RIGHT` (injected every 4 ticks from Tick 108 to 224).

#### 4. Step-by-Step Logic & Assertions

##### Initial State (Tick 0)
- Player at `(1, 1)`, dir = 3 (Down-Right).
- Camera coordinates:
  - `vp_left = clamp(1 - 10, 0, 40) = 0`.
  - `vp_top = clamp(1 - 5, 0, 20) = 0`.
- **Double Assert**:
  - `get_camera()` returns `(0, 0)`.
  - `get_sprites()` contains Player 0 sprite active at `x = (1 - 0) * 8 = 8`, `y = (1 - 0) * 8 = 8`.

##### Checkpoint 1 (Tick 40, Player at (11, 11) - Camera Scrolling)
- Player position: `(11, 11)`.
- Camera coordinates:
  - `vp_left = clamp(11 - 10, 0, 40) = 1`.
  - `vp_top = clamp(11 - 5, 0, 20) = 6`.
- **Double Assert**:
  - `get_camera()` returns `(1, 6)`.
  - `get_sprites()` contains Player 0 sprite active at `x = (11 - 1) * 8 = 80`, `y = (11 - 6) * 8 = 40`.

##### Checkpoint 2 (Tick 108, Player at (28, 28) - Vertical Camera Clamping)
- Player position: `(28, 28)`.
- Camera coordinates:
  - `vp_left = clamp(28 - 10, 0, 40) = 18`.
  - `vp_top = clamp(28 - 5, 0, 20) = 20` (clamped to max height offset 20!).
- **Double Assert**:
  - `get_camera()` returns `(18, 20)`.
  - `get_sprites()` contains Player 0 sprite active at `x = (28 - 18) * 8 = 80`, `y = (28 - 20) * 8 = 64`.

##### Final State (Tick 228, Player at (58, 28) - Fully Clamped Corner)
- Player position: `(58, 28)`.
- Camera coordinates:
  - `vp_left = clamp(58 - 10, 0, 40) = 40` (clamped to max width offset 40!).
  - `vp_top = clamp(28 - 5, 0, 20) = 20` (clamped!).
- **Double Assert**:
  - `get_camera()` returns `(40, 20)`.
  - `get_sprites()` contains Player 0 sprite active at `x = (58 - 40) * 8 = 144`, `y = (28 - 20) * 8 = 64`.
- **Border Check**: `assert_outer_border_walls` passes.

---

## 4. Verification Plan

An implementer should integrate these scenarios into a new test file `dandy-gb/tests/test_tier4.py` by implementing them as programmatic unittest test cases.

### 4.1 Implementation Steps
1. **Create the Test File**: Create `dandy-gb/tests/test_tier4.py` and import `unittest`, `sys`, `os`, and `DandyEnv` from `dandy_env`.
2. **Implement Scenario Helpers**:
   - Write a helper method `helper_setup_custom_map(self, layout_dict, player_start_positions)` that:
     - Initializes an array of size 1800 with `TILE_WALL` (1) on all borders and `TILE_SPACE` (0) in the interior.
     - Places custom entities specified in `layout_dict` (keys are `(x, y)` tuples, values are tile IDs).
     - Assigns the map to `self.env.dandy_map`.
     - Joins the active players and sets their starting coordinates.
     - Calls `self.env.clear_mock_buffers()` to start with a clean slate.
3. **Write Scenario Test Cases**: Implement each of the 5 designed scenarios as a separate test method (e.g. `test_scenario1_full_level0_playthrough`).
4. **Compile and Run**:
   - Compile the test shared library:
     ```bash
     make test_lib
     ```
   - Execute the test suite:
     ```bash
     make test
     ```
     This will run all tests, including the new `test_tier4.py`.

### 4.2 Robustness Checks
- **Timing**: Ensure that the exact 4-tick cadence is strictly followed for all player movements, or the player will be blocked by the move timer cooldown.
- **Rotor Indexing**: For Scenario 3, make sure to set `monster_rotor = 10` before executing the step, ensuring that the monster at `(11, 10)` ticks on the very first step.
- **Viewport Draws**: Remember to call `self.env.draw_viewport(0)` before querying sprites or camera coordinates, as the camera and sprite buffers are populated during the viewport drawing process.
- **Cleanups**: The `DandyEnv` wrapper automatically manages state isolation by creating a temporary copy of `libdandy_test.so` for each test class execution. Unittest's `setUp` will instantiate a fresh `DandyEnv`, ensuring no cross-test state leakage.
