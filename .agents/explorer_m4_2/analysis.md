# Dandy Dungeon E2E Test Suite Design Report
**Milestone 4: Complex Combat & Survival Scenarios**
**Author**: Explorer 2 (Milestone 4)
**Working Directory**: `/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/.agents/explorer_m4_2`

---

## 1. Codebase Analysis Summary

Through a comprehensive read-only investigation of the core engine (`dandy_core.c`), level definition (`levels.c`), and python test environment (`dandy_env.py`), we have analyzed the implementation details of combat, generator spawning, and smart bomb mechanics.

### 1.1. Smart Bomb Mechanics
The smart bomb feature is governed by `do_bomb(uint8_t p_idx)`:
*   **AABB / Viewport Scoping**: Clears destructible entities within the player's 10x20 viewport.
    *   `vp_left = clamp(player_x[p_idx] - 10, 0, DANDY_LEVEL_WIDTH - 20)`
    *   `vp_top = clamp(player_y[p_idx] - 5, 0, DANDY_LEVEL_HEIGHT - 10)`
*   **Clearing Logic**: Iterates over all tiles in `[vp_left, vp_left + 19]` and `[vp_top, vp_top + 9]`. If a tile is a monster (`TILE_MONSTER1` to `TILE_MONSTER3`) or a generator (`TILE_GENERATOR1` to `TILE_GENERATOR3`), it is set to `TILE_SPACE` (0).
*   **Triggering Methods**:
    1.  **Inventory Bomb**: Pressed `BUTTON_BOMB` with `player_bombs[p_idx] > 0`. Consumes 1 bomb, triggers `do_bomb`, and plays `SOUND_BOMB`.
    2.  **Projectile Bomb**: Fired arrow hits a `TILE_BOMB` on the map. Triggers `do_bomb` centered on the shooter, clears the hit bomb tile, and plays `SOUND_HIT` (without consuming the player's inventory bomb).

### 1.2. Generator Spawning & LFSR Determinism
*   **Sparse Grid Tick**: Monsters and generators tick once every 16 steps in a grid pattern determined by `monster_rotor`:
    *   `x_start = monster_rotor % 4`
    *   `y_start = monster_rotor / 4`
    *   A generator at `(mx, my)` is ticked only when `monster_rotor == (my % 4) * 4 + (mx % 4)`.
*   **Viewport Freeze**: Generators only tick if they are visible in at least one active player's viewport.
*   **Deterministic Spawning (Galois LFSR)**:
    *   The random seed is shared and static: `static uint16_t rand_seed = 0xACE1;`.
    *   On every ticked and visible generator check, the seed is updated:
        ```c
        uint8_t lsb = rand_seed & 1;
        rand_seed >>= 1;
        if (lsb) rand_seed ^= 0xB400u;
        ```
    *   Spawn condition: `(rand_seed & 7) < 4`.
    *   Spawn direction: `spawn_dir = (rand_seed & 3) * 2` (0=Up, 2=Right, 4=Down, 6=Left).
    *   It checks the 4 orthogonal directions in order: `spawn_dir`, `(spawn_dir + 2) % 8`, `(spawn_dir + 4) % 8`, `(spawn_dir + 6) % 8`. The first one that is `TILE_SPACE` receives the spawned monster.
    *   The spawned monster type matches the generator's tier (`TILE_GENERATOR_n` -> `TILE_MONSTER_n`).

### 1.3. Combat & Projectile Flight
*   **Firing**: Pressed `BUTTON_FIRE` when `arrow_dir[p_idx] == -1` (no active arrow). Firing plays `SOUND_SHOOT` and spawns the arrow at the player's coordinate.
*   **Flight**: Every tick, active arrows advance 1 tile in their direction. Fired arrows are restricted to the player's viewport; crossing the viewport boundary instantly destroys the arrow.
*   **Arrow Tile Rotation**: The arrow's tile on the map is set to `TILE_ARROW + ((arrow_dir[p_idx] - 5) & 7)`.
*   **Destruction and Degradation**:
    *   Hitting solid walls or doors: Arrow is destroyed, no sound is played.
    *   Hitting `TILE_BOMB`: Triggers `do_bomb` and destroys the arrow.
    *   Hitting `TILE_HEART`: Replaced by `TILE_MONSTER3`.
    *   Hitting `TILE_MONSTER3` or `TILE_MONSTER2`: Degrades to the next lower tier (`tile_at_new - 1`). Arrow dies, plays `SOUND_HIT`.
    *   Hitting `TILE_MONSTER1` or any generator (`TILE_GENERATOR1` to `TILE_GENERATOR3`): Replaced by `TILE_SPACE` (one-hit kill!). Arrow dies, plays `SOUND_HIT`.

---

## 2. E2E Test Scenario Designs

Both designed scenarios adhere strictly to the **Double-Assert Rule**, verifying:
1.  **Globals (State Changes)**: Exact C engine internal globals via `DandyEnv` (positions, health, inventory, map tiles).
2.  **HAL Logs (Side Effects)**: Retro-hardware events (viewport camera scroll, sprite tables, sound effect registers).

### Scenario A: Generator & Monster Swarm (Deterministic Combat & Degradation)

#### Overview
A single player at `(10, 10)` is surrounded by 4 generators at `(9, 8)`, `(13, 8)`, `(9, 12)`, and `(13, 12)`. In Step 1, these generators tick and spawn monsters based on the LFSR seed. The player then performs a precise sequence of actions to shoot and destroy Generator 1, destroy its spawned Monster 1, navigate to a new row, and hit Generator 2's spawned Monster 2 (testing degradation), before finally destroying Generator 2.

#### Test Setup
1.  Initialize empty map: `[TILE_SPACE] * 1800` with outer border walls of `TILE_WALL`.
2.  Join Player 0 at `(10, 10)`, facing Up (0).
3.  Place Generators inside the player's viewport:
    *   `(9, 8)`: `TILE_GENERATOR1`
    *   `(13, 8)`: `TILE_GENERATOR2`
    *   `(9, 12)`: `TILE_GENERATOR3`
    *   `(13, 12)`: `TILE_GENERATOR1`
4.  Set `monster_rotor = 0` to ensure it increments to 1 in Step 1.

#### Step-by-Step Execution Trace

##### Step 1: Spawning and Movement
*   **Action**: Player moves Left. Input: `[BUTTON_LEFT, 0, 0, 0]`.
*   **State Changes (Globals)**:
    *   Player 0 moves to `(9, 10)`, facing Left. `player_move_timer` becomes 3.
    *   `monster_rotor` becomes 1.
    *   All 4 generators are checked because they are visible and their coordinates satisfy `mx % 4 == 1` and `my % 4 == 0`:
        1.  **Generator 1 at (9, 8)**: LFSR seed updates to `0xE270`. Spawn decision: `(0xE270 & 7) < 4` -> **True**. Spawn dir: `0` (Up). Target `(9, 7)` is space. Spawns `TILE_MONSTER1` at `(9, 7)`.
        2.  **Generator 2 at (13, 8)**: LFSR seed updates to `0x7138`. Spawn decision: `(0x7138 & 7) < 4` -> **True**. Spawn dir: `0` (Up). Target `(13, 7)` is space. Spawns `TILE_MONSTER2` at `(13, 7)`.
        3.  **Generator 3 at (9, 12)**: LFSR seed updates to `0x389C`. Spawn decision: `(0x389C & 7) < 4` -> **False**.
        4.  **Generator 4 at (13, 12)**: LFSR seed updates to `0x1C4E`. Spawn decision: `(0x1C4E & 7) < 4` -> **False**.
*   **Double-Assert Assertions**:
    *   *Globals*: Player at `(9, 10)` facing Left (`TILE_PLAYER1 + 6`). `dandy_map` contains `TILE_MONSTER1` at `(9, 7)` and `TILE_MONSTER2` at `(13, 7)`.
    *   *HAL*: Viewport camera: `(0, 5)`. Sound count: 0. Sprites active for Player 0, Monster 1, and Monster 2.

##### Step 2: Fire First Arrow
*   **Action**: Player turns Up and fires an arrow. Input: `[BUTTON_UP | BUTTON_FIRE, 0, 0, 0]`.
*   **State Changes (Globals)**:
    *   Player 0 turns Up. Movement blocked by cooldown.
    *   Arrow spawned at `(9, 10)` in direction 0 (Up).
    *   Arrow steps to `(9, 9)`.
    *   `monster_rotor` becomes 2 (no generators tick).
*   **Double-Assert Assertions**:
    *   *Globals*: Player at `(9, 10)` facing Up (`TILE_PLAYER1 + 0`). Arrow at `(9, 9)` facing Up (`TILE_ARROW + 3`). `arrow_dir[0] = 0`.
    *   *HAL*: Sound buffer contains `[SOUND_SHOOT]`. Sprites active: Player at `(9, 10)` and Arrow at `(9, 9)`.

##### Step 3: Destroy Generator 1
*   **Action**: Player stands still. Input: `[0, 0, 0, 0]`.
*   **State Changes (Globals)**:
    *   Arrow steps from `(9, 9)` to `(9, 8)`.
    *   Hit target is `TILE_GENERATOR1`. Replaced by `TILE_SPACE`.
    *   Arrow is destroyed (`arrow_dir[0] = -1`).
    *   `monster_rotor` becomes 3.
*   **Double-Assert Assertions**:
    *   *Globals*: Generator 1 at `(9, 8)` is now `TILE_SPACE`. Arrow cleared. `arrow_dir[0] = -1`.
    *   *HAL*: Sound buffer contains `[SOUND_HIT]`. Generator sprite removed.

##### Step 4: Fire Second Arrow
*   **Action**: Player fires. Input: `[BUTTON_FIRE, 0, 0, 0]`.
*   **State Changes (Globals)**:
    *   Arrow spawned at `(9, 10)` facing Up. Steps to `(9, 9)`.
    *   `monster_rotor` becomes 4.
*   **Double-Assert Assertions**:
    *   *Globals*: Arrow at `(9, 9)` facing Up.
    *   *HAL*: Sound buffer contains `[SOUND_SHOOT]`.

##### Step 5: Second Arrow Flight
*   **Action**: Player stands still. Input: `[0, 0, 0, 0]`.
*   **State Changes (Globals)**:
    *   Arrow steps to `(9, 8)` (now a space).
    *   `monster_rotor` becomes 5.
*   **Double-Assert Assertions**:
    *   *Globals*: Arrow at `(9, 8)` facing Up.

##### Step 6: Destroy Monster 1
*   **Action**: Player stands still. Input: `[0, 0, 0, 0]`.
*   **State Changes (Globals)**:
    *   Arrow steps from `(9, 8)` to `(9, 7)`.
    *   Hit target is `TILE_MONSTER1`. Replaced by `TILE_SPACE`.
    *   Arrow is destroyed.
    *   `monster_rotor` becomes 6.
*   **Double-Assert Assertions**:
    *   *Globals*: Monster 1 at `(9, 7)` is now `TILE_SPACE`. Arrow destroyed.
    *   *HAL*: Sound buffer contains `[SOUND_HIT]`.

##### Step 7: Move Up
*   **Action**: Player steps Up. Input: `[BUTTON_UP, 0, 0, 0]`.
*   **State Changes (Globals)**:
    *   Player moves from `(9, 10)` to `(9, 9)`. `player_move_timer` becomes 3.
    *   `monster_rotor` becomes 7.
*   **Double-Assert Assertions**:
    *   *Globals*: Player at `(9, 9)`.

##### Steps 8 - 10: Cooldown Wait
*   **Action**: Player stands still for 3 steps. Input: `[0, 0, 0, 0]` three times.
*   **State Changes (Globals)**:
    *   Player cooldown decreases to 0.
    *   `monster_rotor` advances to 10.
*   **Double-Assert Assertions**:
    *   *Globals*: Player at `(9, 9)`. `player_move_timer = 0`.

##### Step 11: Move Up to Row 8
*   **Action**: Player steps Up. Input: `[BUTTON_UP, 0, 0, 0]`.
*   **State Changes (Globals)**:
    *   Player moves to `(9, 8)`. `player_move_timer = 3`.
    *   `monster_rotor` becomes 11.
*   **Double-Assert Assertions**:
    *   *Globals*: Player at `(9, 8)` facing Up.

##### Step 12: Turn Right and Fire Third Arrow
*   **Action**: Player turns Right and fires. Input: `[BUTTON_RIGHT | BUTTON_FIRE, 0, 0, 0]`.
*   **State Changes (Globals)**:
    *   Player turns Right. Movement blocked by cooldown.
    *   Arrow spawned at `(9, 8)` facing Right. Steps to `(10, 8)`.
    *   `monster_rotor` becomes 12.
*   **Double-Assert Assertions**:
    *   *Globals*: Player at `(9, 8)` facing Right (`TILE_PLAYER1 + 2`). Arrow at `(10, 8)` facing Right (`TILE_ARROW + 5`).
    *   *HAL*: Sound buffer contains `[SOUND_SHOOT]`.

##### Step 13: Arrow Flight and Monster Pathfinding
*   **Action**: Player stands still. Input: `[0, 0, 0, 0]`.
*   **State Changes (Globals)**:
    *   Arrow steps to `(11, 8)`.
    *   `monster_rotor` becomes 13.
    *   **Monster 2 Movement (Rotor 13)**: Monster 2 at `(13, 7)` ticks!
        *   Target: Player at `(9, 8)`.
        *   Pathfinding: `p_dx = -1` (Left), `p_dy = 1` (Down). Best dir: 5 (Down-Left).
        *   Target cell `(12, 8)` is space. Monster 2 moves to `(12, 8)`.
*   **Double-Assert Assertions**:
    *   *Globals*: Arrow at `(11, 8)` facing Right. Monster 2 at `(12, 8)`.
    *   *HAL*: Sprite table contains active Monster 2 at `(12, 8)`.

##### Step 14: Degrade Monster 2
*   **Action**: Player stands still. Input: `[0, 0, 0, 0]`.
*   **State Changes (Globals)**:
    *   Arrow steps from `(11, 8)` to `(12, 8)`.
    *   Hit target is `TILE_MONSTER2`. Replaced by degraded `TILE_MONSTER1`.
    *   Arrow is destroyed.
    *   `monster_rotor` becomes 14.
*   **Double-Assert Assertions**:
    *   *Globals*: `dandy_map` contains `TILE_MONSTER1` at `(12, 8)`. `arrow_dir[0] = -1`.
    *   *HAL*: Sound buffer contains `[SOUND_HIT]`.

##### Step 15: Fire Fourth Arrow
*   **Action**: Player fires. Input: `[BUTTON_FIRE, 0, 0, 0]`.
*   **State Changes (Globals)**:
    *   Arrow spawned at `(9, 8)` facing Right. Steps to `(10, 8)`.
    *   `monster_rotor` becomes 15.
*   **Double-Assert Assertions**:
    *   *Globals*: Arrow at `(10, 8)` facing Right.
    *   *HAL*: Sound buffer contains `[SOUND_SHOOT]`.

##### Step 16: Fourth Arrow Flight
*   **Action**: Player stands still. Input: `[0, 0, 0, 0]`.
*   **State Changes (Globals)**:
    *   Arrow steps to `(11, 8)`.
    *   `monster_rotor` becomes 0.
*   **Double-Assert Assertions**:
    *   *Globals*: Arrow at `(11, 8)` facing Right.

##### Step 17: Destroy Monster 2 (now Monster 1)
*   **Action**: Player stands still. Input: `[0, 0, 0, 0]`.
*   **State Changes (Globals)**:
    *   Arrow steps from `(11, 8)` to `(12, 8)`.
    *   Hit target is `TILE_MONSTER1`. Replaced by `TILE_SPACE`.
    *   Arrow is destroyed.
    *   `monster_rotor` becomes 1.
    *   **Generator 2 at (13, 8) ticks**: LFSR Step 5 (seed `0x0E27`). Spawn: False.
    *   **Generator 3 at (9, 12) ticks**: LFSR Step 6 (seed `0xB313`). Spawn: True. Dir: 6 (Left). Target `(8, 12)` is space. Spawns `TILE_MONSTER3` at `(8, 12)`.
    *   **Generator 4 at (13, 12) ticks**: LFSR Step 7 (seed `0xED89`). Spawn: True. Dir: 2 (Right). Target `(14, 12)` is space. Spawns `TILE_MONSTER1` at `(14, 12)`.
*   **Double-Assert Assertions**:
    *   *Globals*: `(12, 8)` is `TILE_SPACE`. `(8, 12)` is `TILE_MONSTER3`. `(14, 12)` is `TILE_MONSTER1`.
    *   *HAL*: Sound buffer contains `[SOUND_HIT]`.

##### Step 18: Fire Fifth Arrow
*   **Action**: Player fires. Input: `[BUTTON_FIRE, 0, 0, 0]`.
*   **State Changes (Globals)**:
    *   Arrow spawned at `(9, 8)` facing Right. Steps to `(10, 8)`.
    *   `monster_rotor` becomes 2.
*   **Double-Assert Assertions**:
    *   *Globals*: Arrow at `(10, 8)`.

##### Steps 19 - 20: Flight
*   **Action**: Player stands still for 2 steps. Input: `[0, 0, 0, 0]` twice.
*   **State Changes (Globals)**:
    *   Arrow advances: `(11, 8)` then `(12, 8)`.
    *   `monster_rotor` becomes 4.

##### Step 21: Destroy Generator 2
*   **Action**: Player stands still. Input: `[0, 0, 0, 0]`.
*   **State Changes (Globals)**:
    *   Arrow steps from `(12, 8)` to `(13, 8)`.
    *   Hit target is `TILE_GENERATOR2`. Replaced by `TILE_SPACE`.
    *   Arrow is destroyed.
    *   `monster_rotor` becomes 5.
*   **Double-Assert Assertions**:
    *   *Globals*: Generator 2 at `(13, 8)` is now `TILE_SPACE`. Arrow destroyed.
    *   *HAL*: Sound buffer contains `[SOUND_HIT]`.

---

### Scenario B: Smart Bomb Room Clear (Area of Effect and Boundaries)

#### Overview
The player enters a highly crowded room, retrieves a smart bomb, and detonates it. This scenario comprehensively tests the smart bomb's viewport-wide damage radius, verifying that every single monster and generator inside the 10x20 viewport is completely obliterated while entities even 1 tile outside the viewport borders remain entirely unaffected.

#### Test Setup
1.  Initialize empty map: `[TILE_SPACE] * 1800` with outer border walls of `TILE_WALL`.
2.  Join Player 0 at `(10, 10)`, facing Up (0).
    *   *Viewport Coordinates*: Column bounds `[0, 19]`, row bounds `[5, 14]`.
3.  Set Player 0's bomb inventory to 1: `self.env.set_player_bombs(0, 1)`.
4.  Place entities **inside** the viewport:
    *   `(5, 7)`: `TILE_MONSTER1`
    *   `(12, 6)`: `TILE_MONSTER2`
    *   `(18, 13)`: `TILE_MONSTER3`
    *   `(2, 10)`: `TILE_GENERATOR1`
    *   `(15, 12)`: `TILE_GENERATOR3`
5.  Place entities **outside** the viewport:
    *   `(20, 10)`: `TILE_MONSTER2` (1 tile beyond right edge `x=19`)
    *   `(10, 4)`: `TILE_MONSTER1` (1 tile beyond top edge `y=5`)
    *   `(25, 12)`: `TILE_GENERATOR2` (well outside right edge)
    *   `(8, 15)`: `TILE_GENERATOR1` (1 tile beyond bottom edge `y=14`)

#### Step-by-Step Execution Trace

##### Step 1: Detonation
*   **Action**: Player presses the BOMB button. Input: `[BUTTON_BOMB, 0, 0, 0]`.
*   **State Changes (Globals)**:
    *   Player bomb inventory is decremented: `player_bombs[0]` becomes 0.
    *   `do_bomb(0)` executes, calculating the viewport boundary: `vp_left = 0`, `vp_top = 5`.
    *   It sweeps coordinates `x` in `[0, 19]` and `y` in `[5, 14]`.
    *   All 5 entities inside this viewport are replaced with `TILE_SPACE`.
    *   All 4 entities outside this viewport are preserved.
    *   `SOUND_BOMB` is played.
*   **Double-Assert Assertions**:
    *   *Globals*:
        *   `self.env.get_player_bombs(0)` is 0.
        *   `self.get_tile(5, 7)` is `TILE_SPACE`.
        *   `self.get_tile(12, 6)` is `TILE_SPACE`.
        *   `self.get_tile(18, 13)` is `TILE_SPACE`.
        *   `self.get_tile(2, 10)` is `TILE_SPACE`.
        *   `self.get_tile(15, 12)` is `TILE_SPACE`.
        *   `self.get_tile(20, 10)` is `TILE_MONSTER2` (preserved!).
        *   `self.get_tile(10, 4)` is `TILE_MONSTER1` (preserved!).
        *   `self.get_tile(25, 12)` is `TILE_GENERATOR2` (preserved!).
        *   `self.get_tile(8, 15)` is `TILE_GENERATOR1` (preserved!).
    *   *HAL*:
        *   `self.env.draw_viewport(0)`.
        *   Viewport camera: `(0, 5)`.
        *   Sound buffer contains exactly `[SOUND_BOMB]`.
        *   Sprites: active sprites count is 1 (only the Player at `(10, 10)`). All monster sprites inside the viewport have been removed.

---

## 3. Python Implementation Sketch

The designed E2E test cases can be integrated directly into a new python test file, e.g., `tests/test_tier4_combat.py`, following the project's established pattern. Below is a structured blueprint of the python implementation.

```python
import unittest
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dandy_env import DandyEnv

class TestTier4Combat(unittest.TestCase):
    def setUp(self):
        self.env = DandyEnv()
        self.env.init()
        self.env.assert_outer_border_walls(self)

    def helper_setup_clean_map(self, player_x=10, player_y=10, p_idx=0):
        custom_map = [self.env.TILE_SPACE] * self.env.MAP_SIZE
        custom_map[player_y * 60 + player_x] = self.env.TILE_PLAYER1
        self.env.dandy_map = custom_map
        self.env.set_player_position(p_idx, player_x, player_y)
        self.env.set_player_joined(p_idx, True)
        self.env.set_player_health(p_idx, 100)
        self.env.set_player_score(p_idx, 0)
        self.env.set_player_bombs(p_idx, 0)
        self.env.set_player_keys(p_idx, 0)
        self.env.set_player_dir(p_idx, 0) # Up
        self.env.set_player_move_timer(p_idx, 0)
        self.env.monster_rotor = 0
        self.env.clear_mock_buffers()

    def set_tile(self, x, y, tile_id):
        m = self.env.dandy_map
        m[y * 60 + x] = tile_id
        self.env.dandy_map = m

    def get_tile(self, x, y):
        return self.env.dandy_map[y * 60 + x]

    def test_scenario_a_generator_monster_swarm(self):
        """Scenario A: Deterministic generator spawning, arrow combat, degradation, and clearing."""
        # 1. Setup
        self.helper_setup_clean_map(10, 10)
        self.set_tile(9, 8, self.env.TILE_GENERATOR1)
        self.set_tile(13, 8, self.env.TILE_GENERATOR2)
        self.set_tile(9, 12, self.env.TILE_GENERATOR3)
        self.set_tile(13, 12, self.env.TILE_GENERATOR1)
        
        # 2. Step 1: Move Left -> triggers spawn at (9,7) and (13,7)
        self.env.step([self.env.BUTTON_LEFT, 0, 0, 0])
        self.assertEqual(self.env.get_player_x(0), 9)
        self.assertEqual(self.env.get_player_y(0), 10)
        self.assertEqual(self.get_tile(9, 7), self.env.TILE_MONSTER1)
        self.assertEqual(self.get_tile(13, 7), self.env.TILE_MONSTER2)
        self.assertEqual(self.get_tile(9, 12), self.env.TILE_GENERATOR3) # No spawn
        self.assertEqual(self.get_tile(13, 12), self.env.TILE_GENERATOR1) # No spawn
        
        # HAL asserts
        self.env.draw_viewport(0)
        cam_x, cam_y = self.env.get_camera()
        self.assertEqual(cam_x, 0)
        self.assertEqual(cam_y, 5)
        self.assertEqual(len(self.env.get_sounds()), 0)
        
        # 3. Step 2: Turn Up & Fire arrow
        self.env.step([self.env.BUTTON_UP | self.env.BUTTON_FIRE, 0, 0, 0])
        self.assertEqual(self.env.get_player_dir(0), 0) # Up
        self.assertEqual(self.env.get_arrow_dir(0), 0)
        self.assertEqual(self.get_tile(9, 9), self.env.TILE_ARROW + 3)
        
        # HAL asserts
        self.env.draw_viewport(0)
        self.assertIn(self.env.SOUND_SHOOT, self.env.get_sounds())
        
        # 4. Step 3: Arrow hits and destroys Generator 1
        self.env.step([0, 0, 0, 0])
        self.assertEqual(self.get_tile(9, 8), self.env.TILE_SPACE)
        self.assertEqual(self.env.get_arrow_dir(0), -1)
        
        # HAL asserts
        self.env.draw_viewport(0)
        self.assertIn(self.env.SOUND_HIT, self.env.get_sounds())
        
        # 5. Step 4: Fire second arrow at Monster 1
        self.env.step([self.env.BUTTON_FIRE, 0, 0, 0])
        self.assertEqual(self.get_tile(9, 9), self.env.TILE_ARROW + 3)
        
        # 6. Step 5: Arrow fly
        self.env.step([0, 0, 0, 0])
        self.assertEqual(self.get_tile(9, 8), self.env.TILE_ARROW + 3)
        
        # 7. Step 6: Arrow hits and destroys Monster 1
        self.env.step([0, 0, 0, 0])
        self.assertEqual(self.get_tile(9, 7), self.env.TILE_SPACE)
        self.assertEqual(self.env.get_arrow_dir(0), -1)
        
        # HAL asserts
        self.env.draw_viewport(0)
        self.assertIn(self.env.SOUND_HIT, self.env.get_sounds())
        
        # 8. Step 7: Move Up
        self.env.step([self.env.BUTTON_UP, 0, 0, 0])
        self.assertEqual(self.env.get_player_y(0), 9)
        
        # 9. Step 8-10: Cooldown
        for _ in range(3):
            self.env.step([0, 0, 0, 0])
            
        # 10. Step 11: Move Up to row 8
        self.env.step([self.env.BUTTON_UP, 0, 0, 0])
        self.assertEqual(self.env.get_player_y(0), 8)
        
        # 11. Step 12: Turn Right and Fire third arrow
        self.env.step([self.env.BUTTON_RIGHT | self.env.BUTTON_FIRE, 0, 0, 0])
        self.assertEqual(self.env.get_player_dir(0), 2) # Right
        self.assertEqual(self.env.get_arrow_dir(0), 2)
        self.assertEqual(self.get_tile(10, 8), self.env.TILE_ARROW + 5)
        
        # 12. Step 13: Arrow fly, Monster 2 ticks (rotor 13) and moves into arrow path
        # monster_rotor starts at 0.
        # step 1: rotor=1
        # step 2: rotor=2
        # step 3: rotor=3
        # step 4: rotor=4
        # step 5: rotor=5
        # step 6: rotor=6
        # step 7: rotor=7
        # step 8: rotor=8
        # step 9: rotor=9
        # step 10: rotor=10
        # step 11: rotor=11
        # step 12: rotor=12
        # step 13: rotor=13 -> Monster 2 ticks and moves from (13,7) to (12,8)
        self.env.step([0, 0, 0, 0])
        self.assertEqual(self.env.get_arrow_x(0), 11)
        self.assertEqual(self.get_tile(12, 8), self.env.TILE_MONSTER2)
        
        # 13. Step 14: Arrow hits and degrades Monster 2 to Monster 1
        self.env.step([0, 0, 0, 0])
        self.assertEqual(self.get_tile(12, 8), self.env.TILE_MONSTER1)
        self.assertEqual(self.env.get_arrow_dir(0), -1)
        
        # HAL asserts
        self.env.draw_viewport(0)
        self.assertIn(self.env.SOUND_HIT, self.env.get_sounds())
        
        # 14. Step 15: Fire fourth arrow
        self.env.step([self.env.BUTTON_FIRE, 0, 0, 0])
        self.assertEqual(self.get_tile(10, 8), self.env.TILE_ARROW + 5)
        
        # 15. Step 16: Arrow fly
        self.env.step([0, 0, 0, 0])
        self.assertEqual(self.get_tile(11, 8), self.env.TILE_ARROW + 5)
        
        # 16. Step 17: Arrow hits and destroys degraded Monster 2 (now Monster 1)
        # monster_rotor becomes 1 (ticks generators again: Gen 3 spawns at (8,12), Gen 4 at (14,12))
        self.env.step([0, 0, 0, 0])
        self.assertEqual(self.get_tile(12, 8), self.env.TILE_SPACE)
        self.assertEqual(self.get_tile(8, 12), self.env.TILE_MONSTER3)
        self.assertEqual(self.get_tile(14, 12), self.env.TILE_MONSTER1)
        
        # 17. Step 18: Fire fifth arrow
        self.env.step([self.env.BUTTON_FIRE, 0, 0, 0])
        
        # 18. Step 19-20: Arrow fly
        for _ in range(2):
            self.env.step([0, 0, 0, 0])
            
        # 19. Step 21: Arrow hits and destroys Generator 2
        self.env.step([0, 0, 0, 0])
        self.assertEqual(self.get_tile(13, 8), self.env.TILE_SPACE)
        self.assertEqual(self.env.get_arrow_dir(0), -1)
        
        # HAL asserts
        self.env.draw_viewport(0)
        self.assertIn(self.env.SOUND_HIT, self.env.get_sounds())

    def test_scenario_b_smart_bomb_room_clear(self):
        """Scenario B: Viewport-wide smart bomb room clear with strict boundary protection."""
        # 1. Setup
        self.helper_setup_clean_map(10, 10)
        self.env.set_player_bombs(0, 1)
        
        # Inside Viewport (x in [0, 19], y in [5, 14])
        self.set_tile(5, 7, self.env.TILE_MONSTER1)
        self.set_tile(12, 6, self.env.TILE_MONSTER2)
        self.set_tile(18, 13, self.env.TILE_MONSTER3)
        self.set_tile(2, 10, self.env.TILE_GENERATOR1)
        self.set_tile(15, 12, self.env.TILE_GENERATOR3)
        
        # Outside Viewport
        self.set_tile(20, 10, self.env.TILE_MONSTER2)  # just outside right edge (x=20)
        self.set_tile(10, 4, self.env.TILE_MONSTER1)   # just outside top edge (y=4)
        self.set_tile(25, 12, self.env.TILE_GENERATOR2) # outside right
        self.set_tile(8, 15, self.env.TILE_GENERATOR1)  # just outside bottom edge (y=15)
        
        # 2. Detonate Bomb
        self.env.step([self.env.BUTTON_BOMB, 0, 0, 0])
        
        # 3. Assert Globals (State Changes)
        self.assertEqual(self.env.get_player_bombs(0), 0)
        
        # Verify inside cleared
        self.assertEqual(self.get_tile(5, 7), self.env.TILE_SPACE)
        self.assertEqual(self.get_tile(12, 6), self.env.TILE_SPACE)
        self.assertEqual(self.get_tile(18, 13), self.env.TILE_SPACE)
        self.assertEqual(self.get_tile(2, 10), self.env.TILE_SPACE)
        self.assertEqual(self.get_tile(15, 12), self.env.TILE_SPACE)
        
        # Verify outside intact
        self.assertEqual(self.get_tile(20, 10), self.env.TILE_MONSTER2)
        self.assertEqual(self.get_tile(10, 4), self.env.TILE_MONSTER1)
        self.assertEqual(self.get_tile(25, 12), self.env.TILE_GENERATOR2)
        self.assertEqual(self.get_tile(8, 15), self.env.TILE_GENERATOR1)
        
        # 4. Assert HAL (Side Effects)
        self.env.draw_viewport(0)
        self.assertIn(self.env.SOUND_BOMB, self.env.get_sounds())
        cam_x, cam_y = self.env.get_camera()
        self.assertEqual(cam_x, 0)
        self.assertEqual(cam_y, 5)
        
        # Verify only 1 active sprite remaining (the player at 10,10)
        sprites = self.env.get_sprites()
        self.assertEqual(len(sprites), 1)
        player_sprite = list(sprites.values())[0]
        self.assertEqual(player_sprite['tile_id'], self.env.TILE_PLAYER1)
```

---
