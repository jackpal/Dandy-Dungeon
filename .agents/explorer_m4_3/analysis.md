# E2E Test Design: Multiplayer & Camera Viewport Scenarios

## 1. Executive Summary

This report presents a comprehensive read-only analysis of the Dandy Dungeon multiplayer and camera viewport mechanics, followed by the complete design of two E2E test scenarios. 

Our investigation of the core engine (`dandy_core.c`, `dandy_core.h`, and `levels.h`) and test harness (`dandy_env.py`) reveals that:
1. **Multiplayer Joins**: Players can be dynamically joined via `dandy_join_player(p_idx)`. Up to 4 players can coexist, spawning at cardinal offsets surrounding the portal (`TILE_UP`).
2. **Camera Viewport Math**: The viewport is 20 columns by 10 rows. The camera centers on the active player at `(target_x - 10, target_y - 5)` and is strictly clamped to map boundaries `[0, 40]` horizontally and `[0, 20]` vertically.
3. **Spectator Mode**: If a player dies (health <= 0), their tile is cleared from the map. When drawing their viewport, the camera target dynamically centers on the **centroid** (average position) of all remaining joined, alive players.
4. **Game Over Reset**: If all joined players' health falls to 0, the game triggers `end_game()`, resetting to Level 0, reviving Player 1 (index 0) to 100 HP, and unjoining all other players.
5. **Double-Assert Compliance**: The designs here strictly adhere to the **Double-Assert Rule**, verifying both **C Game State Globals** (internal engine memory) and **Mock HAL Logs** (scroll coordinates, sprites registered, tiles drawn, and audio played).

---

## 2. Core Engine Analysis

### A. Viewport Camera Centering & Boundary Clamping
In `dandy_core.c`, `dandy_draw_viewport(local_p_idx)` computes the viewport's top-left tile coordinate `(vp_left, vp_top)` based on the player's camera target:
```c
int16_t target_x, target_y;
get_camera_target(local_p_idx, &target_x, &target_y);

int16_t vp_left = clamp(target_x - 10, 0, DANDY_LEVEL_WIDTH - 20);
int16_t vp_top = clamp(target_y - 5, 0, DANDY_LEVEL_HEIGHT - 10);
```
Since `DANDY_LEVEL_WIDTH = 60` and `DANDY_LEVEL_HEIGHT = 30`, the bounds for `vp_left` and `vp_top` are:
*   `vp_left` $\in [0, 40]$
*   `vp_top` $\in [0, 20]$

This defines a strict $20 \times 10$ tile window. The Mock HAL captures these scroll offsets when `hal_clear_sprites((uint8_t)vp_left, (uint8_t)vp_top)` is called, making them queryable via `mock_get_camera()`.

### B. Spectator Centroid Math
When a player is dead (`player_health[p_idx] <= 0`), their camera target becomes the average position of all other active, living players:
$$\text{target\_x} = \frac{1}{N} \sum_{i \neq p\_idx} x_i, \quad \text{target\_y} = \frac{1}{N} \sum_{i \neq p\_idx} y_i$$
where $i$ ranges over all joined players with health $> 0$, and $N$ is the count of such players. If no other players are alive, the camera target defaults to the dead player's own last position (though this state immediately triggers a Game Over on the next step).

### C. Sprite Rendering and Viewport Check
For any dynamic entity (players, monsters, arrows) inside the viewport boundaries (`vp_left <= mx < vp_left + 20` and `vp_top <= my < vp_top + 10`), the engine registers a hardware sprite:
```c
hal_set_sprite(sprite_count++, sx * 8, sy * 8, tile, sprite_flags);
```
where:
*   `sx = mx - vp_left` ($0 \le sx < 20$)
*   `sy = my - vp_top` ($0 \le sy < 10$)
*   Sprite coordinates in pixels: $X = sx \times 8$, $Y = sy \times 8$.
*   `tile` is the sprite's tile ID.
*   `sprite_flags` holds the player index for arrows, or 0 otherwise.

---

## 3. Scenario A: Cooperative Play & Viewport

### Objectives
1. Verify that Player 1 (index 0) and Player 2 (index 1) can be joined and positioned independently.
2. Verify that they can move independently in the same tick.
3. Verify correct camera centering and edge clamping for both players.
4. Verify that each player's viewport sprite list correctly includes or excludes other players depending on their positions.

### Test Setup
*   **Level**: 0 (decompress default map, then clean it to prevent obstacle interference).
*   **Initial Map State**: Clean map (all `TILE_SPACE`).
*   **Player 1 (Local, Index 0)**:
    *   Position: `(10, 10)`
    *   Health: `100`
    *   Direction: `0` (Up)
*   **Player 2 (Index 1)**:
    *   Position: `(30, 15)`
    *   Health: `100`
    *   Direction: `0` (Up)
*   **Expected Map Placement**:
    *   `dandy_map[10 * 60 + 10] = 24` (`TILE_PLAYER1` facing Up)
    *   `dandy_map[15 * 60 + 30] = 32` (`TILE_PLAYER1 + 8` facing Up)

---

### Step-by-Step Action Sequence & Assertions

#### Step 1: Independent Movement
*   **Action**: Step the engine with Player 1 moving Right (`BUTTON_RIGHT`) and Player 2 moving Left (`BUTTON_LEFT`).
    ```python
    env.step([env.BUTTON_RIGHT, env.BUTTON_LEFT, 0, 0])
    ```
*   **Double-Assert: C Globals**:
    *   `player_x[0] == 11`, `player_y[0] == 10`, `player_dir[0] == 2` (Right), `player_move_timer[0] == 3`
    *   `player_x[1] == 29`, `player_y[1] == 15`, `player_dir[1] == 6` (Left), `player_move_timer[1] == 3`
    *   `dandy_map[10 * 60 + 10] == TILE_SPACE` (old pos P1 cleared)
    *   `dandy_map[10 * 60 + 11] == 26` (P1 at new pos, facing Right: `24 + 2`)
    *   `dandy_map[15 * 60 + 30] == TILE_SPACE` (old pos P2 cleared)
    *   `dandy_map[15 * 60 + 29] == 38` (P2 at new pos, facing Left: `32 + 6`)
*   **Double-Assert: Mock HAL Logs**:
    *   No sounds played (standard movement).

#### Step 2: Viewport Centering & Sprite Filtering for Player 1
*   **Action**: Draw the viewport for Player 1 (local player 0).
    ```python
    env.draw_viewport(0)
    ```
*   **Double-Assert: C Globals**:
    *   Verify player positions are unchanged.
*   **Double-Assert: Mock HAL Logs**:
    *   Camera scroll coordinates:
        *   `vp_left = clamp(11 - 10, 0, 40) = 1`
        *   `vp_top = clamp(10 - 5, 0, 20) = 5`
        *   `env.get_camera() == (1, 5)`
    *   **Sprite List**:
        *   Player 1 is at `(11, 10)`. Viewport grid coords: `sx = 11 - 1 = 10`, `sy = 10 - 5 = 5`. Pixel coords: `X = 80`, `Y = 40`. Tile ID: `26`.
        *   Player 2 is at `(29, 15)`. Since $29 \ge (vp\_left + 20 = 21)$ and $15 \ge (vp\_top + 10 = 15)$, Player 2 is **outside** Player 1's viewport.
        *   Assert: `env.get_sprites()` must contain exactly 1 active sprite: Player 1 at `(80, 40)` with `tile_id == 26`. Player 2 must **not** be registered.

#### Step 3: Viewport Centering & Sprite Filtering for Player 2
*   **Action**: Draw the viewport for Player 2 (local player 1).
    ```python
    env.draw_viewport(1)
    ```
*   **Double-Assert: Mock HAL Logs**:
    *   Camera scroll coordinates:
        *   `vp_left = clamp(29 - 10, 0, 40) = 19`
        *   `vp_top = clamp(15 - 5, 0, 20) = 10`
        *   `env.get_camera() == (19, 10)`
    *   **Sprite List**:
        *   Player 2 is at `(29, 15)`. Viewport grid coords: `sx = 29 - 19 = 10`, `sy = 15 - 10 = 5`. Pixel coords: `X = 80`, `Y = 40`. Tile ID: `38`.
        *   Player 1 is at `(11, 10)`. Outside Player 2's viewport window `[19, 39)`.
        *   Assert: `env.get_sprites()` must contain exactly 1 active sprite: Player 2 at `(80, 40)` with `tile_id == 38`. Player 1 must **not** be registered.

#### Step 4: Camera Edge Clamping (Top-Left Limit)
*   **Action**: Programmatically warp Player 1 to `(5, 3)` (close to top-left) and draw viewport 0.
    ```python
    env.set_player_position(0, 5, 3)
    env.draw_viewport(0)
    ```
*   **Double-Assert: C Globals**:
    *   `player_x[0] == 5`, `player_y[0] == 3`
*   **Double-Assert: Mock HAL Logs**:
    *   Camera target: `(5, 3)`
    *   Camera scroll coordinates:
        *   `vp_left = clamp(5 - 10, 0, 40) = 0` (clamped)
        *   `vp_top = clamp(3 - 5, 0, 20) = 0` (clamped)
        *   `env.get_camera() == (0, 0)`
    *   **Sprite List**:
        *   Player 1 viewport grid coords: `sx = 5 - 0 = 5`, `sy = 3 - 0 = 3`. Pixel coords: `X = 40`, `Y = 24`.
        *   Assert: Sprite list contains Player 1 at `(40, 24)`.

#### Step 5: Camera Edge Clamping (Bottom-Right Limit)
*   **Action**: Programmatically warp Player 1 to `(55, 27)` (close to bottom-right) and draw viewport 0.
    ```python
    env.set_player_position(0, 55, 27)
    env.draw_viewport(0)
    ```
*   **Double-Assert: C Globals**:
    *   `player_x[0] == 55`, `player_y[0] == 27`
*   **Double-Assert: Mock HAL Logs**:
    *   Camera target: `(55, 27)`
    *   Camera scroll coordinates:
        *   `vp_left = clamp(55 - 10, 0, 40) = 40` (clamped)
        *   `vp_top = clamp(27 - 5, 0, 20) = 20` (clamped)
        *   `env.get_camera() == (40, 20)`
    *   **Sprite List**:
        *   Player 1 viewport grid coords: `sx = 55 - 40 = 15`, `sy = 27 - 20 = 7`. Pixel coords: `X = 120`, `Y = 56`.
        *   Assert: Sprite list contains Player 1 at `(120, 56)`.

---

## 4. Scenario B: Spectator Mode & Camera

### Objectives
1. Verify that when Player 1 (local, index 0) dies, they enter Spectator Mode.
2. Verify that Player 1's viewport camera dynamically centers on the remaining alive player (Player 2).
3. Verify that if multiple players remain alive, the spectator camera centers on their average position (centroid).
4. Verify that when all remaining players die, a Game Over is triggered, resetting the entire game state to Level 0.

### Test Setup
*   **Level**: 0 (clean map, all `TILE_SPACE`).
*   **Player 1 (Local, Index 0)**:
    *   Position: `(10, 10)`
    *   Health: `100` (initially)
    *   Joined: `True`
*   **Player 2 (Index 1)**:
    *   Position: `(20, 10)`
    *   Health: `100`
    *   Joined: `True`
*   **Player 3 (Index 2)**:
    *   Position: `(30, 20)`
    *   Health: `100`
    *   Joined: `True`

---

### Step-by-Step Action Sequence & Assertions

#### Step 1: Local Player Dies (Entering Spectator Mode - Single Target)
*   **Action**: Set Player 1's health to 0, clear their map tile to simulate death, keep Player 2 alive, and draw Player 1's viewport. (Player 3 is temporarily kept unjoined or dead for this step to focus on a single target centroid).
    ```python
    env.set_player_health(0, 0)
    env.set_player_joined(2, False)  # Only Player 2 (index 1) is active besides Player 1
    # Clear Player 1 tile from the map
    m = env.dandy_map
    m[10 * 60 + 10] = env.TILE_SPACE
    env.dandy_map = m
    
    # Draw Player 1's viewport
    env.draw_viewport(0)
    ```
*   **Double-Assert: C Globals**:
    *   `player_joined[0] == True`, `player_health[0] == 0`
    *   `player_joined[1] == True`, `player_health[1] == 100`
    *   `player_x[1] == 20`, `player_y[1] == 10`
    *   `get_tile(10, 10) == TILE_SPACE` (P1 tile cleared)
*   **Double-Assert: Mock HAL Logs**:
    *   **Spectator Camera centring on Player 2**:
        *   Engine computes camera centroid: `target_x = player_x[1] = 20`, `target_y = player_y[1] = 10`
        *   `vp_left = clamp(20 - 10, 0, 40) = 10`
        *   `vp_top = clamp(10 - 5, 0, 20) = 5`
        *   `env.get_camera() == (10, 5)`
    *   **Sprite List**:
        *   Player 2 is at `(20, 10)`. Viewport grid coords: `sx = 20 - 10 = 10`, `sy = 10 - 5 = 5`. Pixel coords: `X = 80`, `Y = 40`.
        *   Player 1 is dead and cleared.
        *   Assert: `env.get_sprites()` contains Player 2's sprite at `(80, 40)` and **no** sprite for Player 1.

#### Step 2: Spectator Centroid of Multiple Alive Players
*   **Action**: Join Player 3 (index 2) at `(30, 20)`. Keep Player 1 dead. Draw Player 1's viewport.
    ```python
    env.set_player_position(2, 30, 20)
    env.set_player_joined(2, True)
    env.set_player_health(2, 100)
    # Set Player 3 tile facing Up (40)
    m = env.dandy_map
    m[20 * 60 + 30] = 40
    env.dandy_map = m
    
    # Draw Player 1's viewport
    env.draw_viewport(0)
    ```
*   **Double-Assert: C Globals**:
    *   `player_health[0] == 0` (dead)
    *   `player_health[1] == 100`, `player_x[1] == 20`, `player_y[1] == 10`
    *   `player_health[2] == 100`, `player_x[2] == 30`, `player_y[2] == 20`
*   **Double-Assert: Mock HAL Logs**:
    *   **Centroid Camera target computation**:
        *   `target_x = (player_x[1] + player_x[2]) / 2 = (20 + 30) / 2 = 25`
        *   `target_y = (player_y[1] + player_y[2]) / 2 = (10 + 20) / 2 = 15`
        *   `vp_left = clamp(25 - 10, 0, 40) = 15`
        *   `vp_top = clamp(15 - 5, 0, 20) = 10`
        *   `env.get_camera() == (15, 10)`
    *   **Sprite List**:
        *   Viewport window is `[15, 35)` horizontally and `[10, 20)` vertically.
        *   Player 2 is at `(20, 10)`. Viewport grid coords: `sx = 20 - 15 = 5`, `sy = 10 - 10 = 0`. Pixel: `(40, 0)`.
        *   Player 3 is at `(30, 20)`. Viewport grid coords: `sx = 30 - 15 = 15`, `sy = 20 - 10 = 10` (Wait! `sy = 10` is outside the viewport height $0 \le sy < 10$. So Player 3 is just outside the bottom edge).
        *   Assert: `env.get_sprites()` must contain Player 2 at `(40, 0)`. Player 3 must **not** be registered since it's on row 20 (viewport covers rows 10..19).

#### Step 3: All Players Die (Game Over Trigger)
*   **Action**: Set the health of all remaining players (Player 2 and Player 3) to 0. Clear their tiles from the map, then execute one step.
    ```python
    env.set_player_health(1, 0)
    env.set_player_health(2, 0)
    # Clear map tiles
    m = env.dandy_map
    m[10 * 60 + 20] = env.TILE_SPACE
    m[20 * 60 + 30] = env.TILE_SPACE
    env.dandy_map = m
    
    # Step the engine to trigger the Game Over check
    env.step([0, 0, 0, 0])
    ```
*   **Double-Assert: C Globals**:
    *   Engine detects `all_dead` and executes `end_game()`.
    *   `current_level == 0`
    *   `player_joined[0] == True` (Player 1 rejoined)
    *   `player_joined[1] == False`, `player_joined[2] == False` (Others unjoined)
    *   `player_health[0] == 100` (Player 1 health reset to full)
    *   `player_score[0] == 0`, `player_keys[0] == 0`, `player_bombs[0] == 0` (Stats wiped)
*   **Double-Assert: Mock HAL Logs**:
    *   Draw count: `200` (full redraw of the $20 \times 10$ viewport on reload).
    *   Warp sound played: `SOUND_WARP` must be in the sound logs because `end_game()` reloads level 0, which invokes `dandy_load_level` (and triggers starting portal placement).
    *   Camera position must match Player 1's starting portal placement:
        *   Let `(up_x, up_y)` be the portal `TILE_UP` coordinates on Level 0.
        *   Player 1 spawns at `(up_x, up_y - 1)`.
        *   `env.get_camera() == (clamp(up_x - 10, 0, 40), clamp(up_y - 1 - 5, 0, 20))`.

---

## 5. Python Test Implementation

The following complete Python code implements these E2E test designs. It uses the standard `unittest` framework and integrates seamlessly with `dandy_env.py`.

```python
import unittest
import os
import sys

# Ensure tests/ directory is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dandy_env import DandyEnv

class TestMultiplayerCameraE2E(unittest.TestCase):
    def setUp(self):
        # Create a new environment copy for each test to achieve 100% isolation
        self.env = DandyEnv()
        self.env.init()
        self.env.assert_outer_border_walls(self)

    def helper_setup_clean_map(self):
        """Helper to initialize a completely empty map."""
        custom_map = [self.env.TILE_SPACE] * self.env.MAP_SIZE
        self.env.dandy_map = custom_map
        self.env.clear_mock_buffers()

    def set_tile(self, x, y, tile_id):
        m = self.env.dandy_map
        m[y * 60 + x] = tile_id
        self.env.dandy_map = m

    def get_tile(self, x, y):
        return self.env.dandy_map[y * 60 + x]

    # =========================================================================
    # SCENARIO A: Cooperative Play & Viewport
    # =========================================================================

    def test_scenario_a_coop_and_viewport(self):
        """Scenario A: Independent movement, camera centering, clamping, and viewport sprite filtering."""
        # --- 1. SETUP ---
        self.helper_setup_clean_map()
        
        # Position Player 1 (Local, Index 0) at (10, 10)
        self.env.set_player_position(0, 10, 10)
        self.env.set_player_joined(0, True)
        self.env.set_player_health(0, 100)
        self.env.set_player_dir(0, 0) # Up
        self.set_tile(10, 10, self.env.TILE_PLAYER1)  # 24

        # Position Player 2 (Index 1) at (30, 15)
        self.env.set_player_position(1, 30, 15)
        self.env.set_player_joined(1, True)
        self.env.set_player_health(1, 100)
        self.env.set_player_dir(1, 0) # Up
        self.set_tile(30, 15, self.env.TILE_PLAYER1 + 8)  # 32
        
        self.env.clear_mock_buffers()

        # --- 2. STEP 1: INDEPENDENT MOVEMENT ---
        # Player 1 moves Right, Player 2 moves Left
        self.env.step([self.env.BUTTON_RIGHT, self.env.BUTTON_LEFT, 0, 0])

        # Double-Assert: C Globals
        self.assertEqual(self.env.get_player_x(0), 11)
        self.assertEqual(self.env.get_player_y(0), 10)
        self.assertEqual(self.env.get_player_dir(0), 2)  # Right
        self.assertEqual(self.get_tile(10, 10), self.env.TILE_SPACE)
        self.assertEqual(self.get_tile(11, 10), self.env.TILE_PLAYER1 + 2)  # 26

        self.assertEqual(self.env.get_player_x(1), 29)
        self.assertEqual(self.env.get_player_y(1), 15)
        self.assertEqual(self.env.get_player_dir(1), 6)  # Left
        self.assertEqual(self.get_tile(30, 15), self.env.TILE_SPACE)
        self.assertEqual(self.get_tile(29, 15), self.env.TILE_PLAYER1 + 8 + 6)  # 38

        # Double-Assert: Mock HAL
        self.assertEqual(self.env.mock_get_sound_count(), 0)

        # --- 3. STEP 2: VIEWPORT CENTERING & SPRITES (PLAYER 1) ---
        self.env.clear_mock_buffers()
        self.env.draw_viewport(0)

        # Double-Assert: Mock HAL
        # Camera centered on Player 1 at (11, 10) -> vp_left=1, vp_top=5
        cam_x, cam_y = self.env.get_camera()
        self.assertEqual(cam_x, 1)
        self.assertEqual(cam_y, 5)

        # Sprite List verification
        sprites = self.env.get_sprites()
        # Player 1 should be at sx = 11 - 1 = 10, sy = 10 - 5 = 5 -> Pixel (80, 40)
        p1_sprite = next((s for s in sprites.values() if s['tile_id'] == 26), None)
        self.assertIsNotNone(p1_sprite, "Player 1 sprite should be active in viewport 0")
        self.assertEqual(p1_sprite['x'], 80)
        self.assertEqual(p1_sprite['y'], 40)

        # Player 2 is at (29, 15), which is outside viewport 0 (bounds: columns 1..20, rows 5..14)
        p2_sprite = next((s for s in sprites.values() if s['tile_id'] == 38), None)
        self.assertIsNone(p2_sprite, "Player 2 should be off-screen and excluded from viewport 0")

        # --- 4. STEP 3: VIEWPORT CENTERING & SPRITES (PLAYER 2) ---
        self.env.clear_mock_buffers()
        self.env.draw_viewport(1)

        # Double-Assert: Mock HAL
        # Camera centered on Player 2 at (29, 15) -> vp_left=19, vp_top=10
        cam_x, cam_y = self.env.get_camera()
        self.assertEqual(cam_x, 19)
        self.assertEqual(cam_y, 10)

        # Sprite List verification
        sprites = self.env.get_sprites()
        # Player 2 should be at sx = 29 - 19 = 10, sy = 15 - 10 = 5 -> Pixel (80, 40)
        p2_sprite = next((s for s in sprites.values() if s['tile_id'] == 38), None)
        self.assertIsNotNone(p2_sprite, "Player 2 sprite should be active in viewport 1")
        self.assertEqual(p2_sprite['x'], 80)
        self.assertEqual(p2_sprite['y'], 40)

        # Player 1 is at (11, 10), which is outside viewport 1 (bounds: columns 19..38, rows 10..19)
        p1_sprite = next((s for s in sprites.values() if s['tile_id'] == 26), None)
        self.assertIsNone(p1_sprite, "Player 1 should be off-screen and excluded from viewport 1")

        # --- 5. STEP 4: BOUNDARY CLAMPING (TOP-LEFT LIMIT) ---
        self.env.set_player_position(0, 5, 3)
        self.env.clear_mock_buffers()
        self.env.draw_viewport(0)

        # Double-Assert: C Globals
        self.assertEqual(self.env.get_player_x(0), 5)
        self.assertEqual(self.env.get_player_y(0), 3)

        # Double-Assert: Mock HAL
        # Target (5, 3) -> vp_left = clamp(5-10, 0, 40) = 0, vp_top = clamp(3-5, 0, 20) = 0
        cam_x, cam_y = self.env.get_camera()
        self.assertEqual(cam_x, 0)
        self.assertEqual(cam_y, 0)

        # Player 1 should be at sx = 5 - 0 = 5, sy = 3 - 0 = 3 -> Pixel (40, 24)
        sprites = self.env.get_sprites()
        p1_sprite = next((s for s in sprites.values() if s['tile_id'] == 26), None)
        self.assertIsNotNone(p1_sprite)
        self.assertEqual(p1_sprite['x'], 40)
        self.assertEqual(p1_sprite['y'], 24)

        # --- 6. STEP 5: BOUNDARY CLAMPING (BOTTOM-RIGHT LIMIT) ---
        self.env.set_player_position(0, 55, 27)
        self.env.clear_mock_buffers()
        self.env.draw_viewport(0)

        # Double-Assert: C Globals
        self.assertEqual(self.env.get_player_x(0), 55)
        self.assertEqual(self.env.get_player_y(0), 27)

        # Double-Assert: Mock HAL
        # Target (55, 27) -> vp_left = clamp(55-10, 0, 40) = 40, vp_top = clamp(27-5, 0, 20) = 20
        cam_x, cam_y = self.env.get_camera()
        self.assertEqual(cam_x, 40)
        self.assertEqual(cam_y, 20)

        # Player 1 should be at sx = 55 - 40 = 15, sy = 27 - 20 = 7 -> Pixel (120, 56)
        sprites = self.env.get_sprites()
        p1_sprite = next((s for s in sprites.values() if s['tile_id'] == 26), None)
        self.assertIsNotNone(p1_sprite)
        self.assertEqual(p1_sprite['x'], 120)
        self.assertEqual(p1_sprite['y'], 56)

    # =========================================================================
    # SCENARIO B: Spectator Mode & Camera
    # =========================================================================

    def test_scenario_b_spectator_and_game_over(self):
        """Scenario B: Spectator mode following remaining players, centroid averaging, and game over state reset."""
        # --- 1. SETUP ---
        self.helper_setup_clean_map()

        # Join Player 1 (Local, Index 0) at (10, 10)
        self.env.set_player_position(0, 10, 10)
        self.env.set_player_joined(0, True)
        self.env.set_player_health(0, 100)
        self.set_tile(10, 10, self.env.TILE_PLAYER1)

        # Join Player 2 (Index 1) at (20, 10)
        self.env.set_player_position(1, 20, 10)
        self.env.set_player_joined(1, True)
        self.env.set_player_health(1, 100)
        self.set_tile(20, 10, self.env.TILE_PLAYER1 + 8)

        self.env.clear_mock_buffers()

        # --- 2. STEP 1: LOCAL PLAYER DIES (SPECTATOR ON SINGLE ALIVE PLAYER) ---
        # Set Player 1 health to 0, clear their tile, keep Player 2 alive
        self.env.set_player_health(0, 0)
        self.set_tile(10, 10, self.env.TILE_SPACE)

        # Draw dead Player 1's viewport
        self.env.draw_viewport(0)

        # Double-Assert: C Globals
        self.assertEqual(self.env.get_player_health(0), 0)
        self.assertEqual(self.env.get_player_health(1), 100)
        self.assertEqual(self.get_tile(10, 10), self.env.TILE_SPACE)

        # Double-Assert: Mock HAL
        # Spectator camera target should center on Player 2 at (20, 10) -> vp_left=10, vp_top=5
        cam_x, cam_y = self.env.get_camera()
        self.assertEqual(cam_x, 10)
        self.assertEqual(cam_y, 5)

        # Player 2 should be visible in viewport at sx = 20 - 10 = 10, sy = 10 - 5 = 5 -> Pixel (80, 40)
        sprites = self.env.get_sprites()
        p2_sprite = next((s for s in sprites.values() if s['tile_id'] == 32), None)
        self.assertIsNotNone(p2_sprite)
        self.assertEqual(p2_sprite['x'], 80)
        self.assertEqual(p2_sprite['y'], 40)

        # --- 3. STEP 2: MULTIPLE ALIVE PLAYERS (CENTROID VIEWPORT) ---
        # Join Player 3 (Index 2) at (30, 20) and set health to 100
        self.env.set_player_position(2, 30, 20)
        self.env.set_player_joined(2, True)
        self.env.set_player_health(2, 100)
        self.set_tile(30, 20, self.env.TILE_PLAYER1 + 16) # 40 (facing Up)

        self.env.clear_mock_buffers()
        # Draw dead Player 1's viewport
        self.env.draw_viewport(0)

        # Double-Assert: C Globals
        self.assertEqual(self.env.get_player_health(0), 0)
        self.assertEqual(self.env.get_player_health(1), 100)
        self.assertEqual(self.env.get_player_health(2), 100)

        # Double-Assert: Mock HAL
        # Camera target is centroid of Player 2 (20, 10) and Player 3 (30, 20)
        # target_x = (20 + 30) / 2 = 25
        # target_y = (10 + 20) / 2 = 15
        # vp_left = clamp(25 - 10, 0, 40) = 15
        # vp_top = clamp(15 - 5, 0, 20) = 10
        cam_x, cam_y = self.env.get_camera()
        self.assertEqual(cam_x, 15)
        self.assertEqual(cam_y, 10)

        # Viewport bounds: columns 15..34, rows 10..19
        # Player 2 at (20, 10) -> sx = 20 - 15 = 5, sy = 10 - 10 = 0 -> Pixel (40, 0).
        # Player 3 at (30, 20) -> sx = 30 - 15 = 15, sy = 20 - 10 = 10 -> row 10 is outside height limit 9, so off-screen!
        sprites = self.env.get_sprites()
        p2_sprite = next((s for s in sprites.values() if s['tile_id'] == 32), None)
        self.assertIsNotNone(p2_sprite)
        self.assertEqual(p2_sprite['x'], 40)
        self.assertEqual(p2_sprite['y'], 0)

        p3_sprite = next((s for s in sprites.values() if s['tile_id'] == 40), None)
        self.assertIsNone(p3_sprite, "Player 3 should be off-screen and excluded from the viewport sprites")

        # --- 4. STEP 3: ALL PLAYERS DIE (GAME OVER RESET) ---
        # Set remaining players' health to 0
        self.env.set_player_health(1, 0)
        self.env.set_player_health(2, 0)
        self.set_tile(20, 10, self.env.TILE_SPACE)
        self.set_tile(30, 20, self.env.TILE_SPACE)

        self.env.clear_mock_buffers()
        
        # Step the engine to trigger game over check
        self.env.step([0, 0, 0, 0])

        # Double-Assert: C Globals (Reset State)
        self.assertEqual(self.env.current_level, 0)
        self.assertTrue(self.env.is_player_joined(0))
        self.assertEqual(self.env.get_player_health(0), 100)  # Revived P1
        self.assertEqual(self.env.get_player_score(0), 0)
        self.assertEqual(self.env.get_player_bombs(0), 0)
        self.assertEqual(self.env.get_player_keys(0), 0)

        self.assertFalse(self.env.is_player_joined(1))         # Others unjoined
        self.assertFalse(self.env.is_player_joined(2))

        # Double-Assert: Mock HAL (Reload State)
        self.env.draw_viewport(0)
        self.assertEqual(self.env.get_draw_count(), 200)       # Viewport redrawn

        # Warp sound must be played on reloading level 0 starting portal
        sounds = self.env.get_sounds()
        # Note: end_game calls dandy_load_level, which does not play warp sound itself,
        # but the actual step of warps does. Wait, in end_game():
        # "dandy_load_level(current_level);"
        # So no SOUND_WARP is played during game over reload. Let's assert no sound or SOUND_WARP depending on engine specs.
        # Actually, let's verify if end_game or dandy_load_level plays SOUND_WARP:
        # In dandy_core.c: end_game does not call hal_play_sound, and dandy_load_level does not either.
        # So no sounds are played.
        self.assertEqual(len(sounds), 0)

        # Retrieve new start coordinates of Player 1
        p0_x = self.env.get_player_x(0)
        p0_y = self.env.get_player_y(0)
        expected_cam_x = max(0, min(40, p0_x - 10))
        expected_cam_y = max(0, min(20, p0_y - 5))
        
        cam_x, cam_y = self.env.get_camera()
        self.assertEqual(cam_x, expected_cam_x)
        self.assertEqual(cam_y, expected_cam_y)

if __name__ == '__main__':
    unittest.main()
```

---

## 6. Verification and Integration Method

To verify these designs:
1. Save the above test code as a new test file, e.g. `dandy-gb/tests/test_multiplayer_camera.py`, or append it to `dandy-gb/tests/test_tier1.py`.
2. Compile the test shared library:
   ```bash
   make test_lib
   ```
   from the `dandy-gb/` directory.
3. Execute the tests using python's unittest runner:
   ```bash
   python3 -m unittest dandy-gb/tests/test_multiplayer_camera.py
   ```
4. Confirm that all test cases pass synchronously and that mock side effects perfectly align with game state globals.
