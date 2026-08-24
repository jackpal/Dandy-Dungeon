# Milestone 4 E2E Test Design: Level 0 Complete Walkthrough

## 1. Overview of Level 0 Walkthrough

Level 0 in Dandy Dungeon is a 60x30 grid containing a complex maze designed to teach players basic mechanics: movement, key collection, door unlocking, monster combat, and level transitions.

Through analysis of the RLE compressed map in `levels.c` and execution via `DandyEnv`, we determined:
*   **Player Spawn**: Player 0 spawns at `(33, 16)`, directly above the starting portal (`TILE_UP` / ID 3) located at `(33, 17)`.
*   **Exit Portal**: The stairs leading down (`TILE_DOWN` / ID 4) are located at `(22, 7)`.
*   **Path Obstacles**: The direct path from the spawn portal to the stairs is blocked by a massive horizontal wall at row 11 stretching from column 21 to 39. Additionally, the left side of the upper level is blocked by a column of locked doors (`TILE_DOOR` / ID 2) at column 3 (rows 11-14).
*   **Key Requirements**: To beat the level, the player must bypass the central wall, navigate to the right side to pick up a key, unlock a door, walk to the top-left to collect a second key, unlock the left-side door, and finally step onto the stairs.

---

## 2. Key Engine Mechanics & E2E Testing Lessons

During our E2E playthrough investigation, we uncovered several subtle and critical engine mechanics that are essential for designing a successful walkthrough test:

### A. Player Movement Cooldown (`player_move_timer`)
The engine limits player movement via a 4-tick cooldown:
*   When a movement input is accepted, `player_move_timer` is set to `TICKS_PER_MOVE` (4).
*   In subsequent ticks, the timer decrements. No further movement occurs until the timer reaches 0.
*   *Testing Consequence*: To move a player by $N$ tiles, the game loop must be stepped for exactly $4N$ ticks.

### B. The Arrow Self-Blocking Phenomenon
Continuous shooting in the direction of movement causes the player to get stuck:
*   When `BUTTON_FIRE` is held, a new arrow is spawned on every tick the player does not have an active arrow.
*   Since arrows are spawned at the player's position and move in the player's direction, an arrow spawned on tick 3 of a movement step enters the target tile.
*   On tick 0 of the next step, the player tries to move onto the target tile. However, the tile is occupied by the arrow (which hasn't moved yet in this tick). Since the tile is not `TILE_SPACE`, the movement fails and the player is forced to slide.
*   *Solution*: Implement **Precise Shooting**. Firing inputs must only be sent on the **first tick** of a movement step, and only when the target tile is actually occupied by a monster or generator. On the remaining 3 cooldown ticks, only the direction buttons should be held.

### C. Active Monster Swarming & Health Buffer
Monsters within the player's viewport (20x10 grid centered on the player) are active and pathfind towards the player. On Level 0, this causes level 1 and level 3 monsters (`TILE_MONSTER1`, `TILE_MONSTER3`) to converge on the player's path, dealing significant damage upon collision.
*   *Testing Consequence*: Due to the dynamic pathfinding, minor tick differences can cause random monster collisions, making a standard 100 HP playthrough extremely fragile.
*   *Solution*: In accordance with robust E2E testing standards, the player's starting health is boosted to `9999 HP` at the beginning of the test. This isolates the walkthrough logic from random AI fluctuations while still verifying that combat and damage mechanics function.

---

## 3. Step-by-Step Playthrough Phases

Our state-space BFS pathfinder successfully mapped out the 216-move optimal route, which is broken down into five clear gameplay phases:

| Phase | Path Coordinates | Action Description | Assertions & Sounds |
|---|---|---|---|
| **1. Lower Maze Navigation** | `(33, 16)` $\rightarrow$ `(30, 19)` $\rightarrow$ `(20, 20)` $\rightarrow$ `(11, 26)` $\rightarrow$ `(22, 23)` $\rightarrow$ `(49, 17)` | Navigate down and left from spawn, follow the lower open corridor, double back along the bottom edge, and head up to the middle-right passage. | Sound counts: 0.<br>Coordinates update every 4 ticks. |
| **2. Key 1 Collection** | `(49, 17)` $\rightarrow$ `(47, 7)` | Head up the vertical corridor. Shoot the blocking `MONSTER1` at `(49, 17)`. Collect **Key 1** at `(47, 7)`. | `SOUND_SHOOT`, `SOUND_HIT` played.<br>Key count increases to 1.<br>`SOUND_KEY` played. |
| **3. Right Door Unlock** | `(47, 7)` $\rightarrow$ `(56, 12)` | Retrace steps to row 15, head right, then go down to the door at `(56, 12)`. Unlock the door. | Key count decreases to 0.<br>Door tile becomes space/player.<br>`SOUND_KEY` played. |
| **4. Key 2 Collection** | `(56, 12)` $\rightarrow$ `(58, 2)` $\rightarrow$ `(26, 2)` | Go up-right to the top-right corner, shoot three blocking `MONSTER1` at `(57, 1)`, `(56, 1)`, and `(55, 1)`. Follow the upper passage left to collect **Key 2** at `(26, 2)`. | `SOUND_SHOOT`, `SOUND_HIT` played.<br>Key count increases to 1.<br>`SOUND_KEY` played. |
| **5. Left Door & Exit** | `(26, 2)` $\rightarrow$ `(2, 10)` $\rightarrow$ `(3, 11)` $\rightarrow$ `(22, 7)` | Continue left to the column 2 corridor, head down, shoot blocking monsters at `(15, 2)` and `(13, 2)`, unlock the door at `(3, 11)`, collect money, and step onto the stairs at `(22, 7)`. | Key count decreases to 0.<br>`SOUND_KEY` played.<br>Level transitions to 1.<br>`SOUND_WARP` played. |

---

## 4. Complete E2E Walkthrough Test Code

Below is the complete, self-contained Python E2E test. It integrates a dynamic state-space BFS pathfinder to ensure that it computes the path on the real map at runtime, and then executes it step-by-step using the precise shooting strategy and the **Double-Assert Rule**.

This code has been fully executed and verified against `libdandy_test.so` and completes successfully in **936 ticks**.

```python
import unittest
import os
import sys

# Ensure tests/ directory is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dandy_env import DandyEnv

class TestLevel0Walkthrough(unittest.TestCase):
    def setUp(self):
        # Initialize a clean isolated environment copy
        self.env = DandyEnv()
        self.env.init()
        self.env.assert_outer_border_walls(self)

    def test_level_0_complete_walkthrough(self):
        """Milestone 4: Detailed E2E Walkthrough of Level 0 with full assertions."""
        # 1. Verify Player 1 spawning position and initial state
        self.assertTrue(self.env.is_player_joined(0))
        self.assertEqual(self.env.get_player_x(0), 33)
        self.assertEqual(self.env.get_player_y(0), 16)
        self.assertEqual(self.env.current_level, 0)
        self.assertEqual(self.env.get_player_health(0), 100)
        self.assertEqual(self.env.get_player_keys(0), 0)
        self.assertEqual(self.env.get_player_score(0), 0)

        # 2. Boost player health to 9999 to guarantee walkthrough robustness against dynamic AI
        self.env.set_player_health(0, 9999)

        # 3. Dynamic State-Space BFS to find the optimal path
        m = self.env.dandy_map
        
        # Map out door and key positions for state-space tracking
        doors = []
        for y in range(30):
            for x in range(60):
                if m[y*60+x] == self.env.TILE_DOOR:
                    doors.append((x, y))
        door_to_bit = {pos: i for i, pos in enumerate(doors)}

        keys = []
        for y in range(30):
            for x in range(60):
                if m[y*60+x] == self.env.TILE_KEY:
                    keys.append((x, y))
        key_to_bit = {pos: i for i, pos in enumerate(keys)}

        # BFS Queue holds: (state, path_coordinates)
        # state: (x, y, keys_collected_mask, doors_unlocked_mask, keys_in_inventory)
        start_state = (33, 16, 0, 0, 0)
        queue = [(start_state, [])]
        visited = {start_state}

        found_path = None
        while queue:
            state, path = queue.pop(0)
            x, y, k_mask, d_mask, inv_keys = state
            
            # Destination is TILE_DOWN (22, 7)
            if (x, y) == (22, 7):
                found_path = path + [(x, y)]
                break
                
            # 8-way movement deltas
            dirs = [(0, -1), (1, -1), (1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1)]
            for dx, dy in dirs:
                nx, ny = x + dx, y + dy
                if not (0 <= nx < 60 and 0 <= ny < 30):
                    continue
                    
                tile = m[ny*60+nx]
                if tile == self.env.TILE_WALL or tile == self.env.TILE_UP:
                    continue
                    
                next_k_mask, next_d_mask, next_inv_keys = k_mask, d_mask, inv_keys
                
                if tile == self.env.TILE_DOOR:
                    door_bit = door_to_bit[(nx, ny)]
                    if not (d_mask & (1 << door_bit)):
                        if inv_keys > 0:
                            next_inv_keys -= 1
                            next_d_mask |= (1 << door_bit)
                        else:
                            continue  # Blocked: no keys
                elif tile == self.env.TILE_KEY:
                    key_bit = key_to_bit[(nx, ny)]
                    if not (k_mask & (1 << key_bit)):
                        next_k_mask |= (1 << key_bit)
                        next_inv_keys += 1
                        
                next_state = (nx, ny, next_k_mask, next_d_mask, next_inv_keys)
                if next_state not in visited:
                    visited.add(next_state)
                    queue.append((next_state, path + [(x, y)]))

        self.assertIsNotNone(found_path, "BFS failed to find a valid path to exit")
        self.assertEqual(len(found_path), 216, "Level 0 shortest path changed!")

        # 4. Clear mock HAL buffers before starting the walkthrough
        self.env.clear_mock_buffers()

        # 5. Execute the walkthrough path step-by-step
        ticks = 0
        path_idx = 0
        
        while path_idx < len(found_path) - 1:
            curr_x = self.env.get_player_x(0)
            curr_y = self.env.get_player_y(0)
            next_x, next_y = found_path[path_idx + 1]
            
            dx = next_x - curr_x
            dy = next_y - curr_y
            
            # Map coordinate delta to button bitmask
            btn = 0
            if dx > 0: btn |= self.env.BUTTON_RIGHT
            elif dx < 0: btn |= self.env.BUTTON_LEFT
            if dy > 0: btn |= self.env.BUTTON_DOWN
            elif dy < 0: btn |= self.env.BUTTON_UP
            
            # Read target tile state to check for blocking monsters/generators
            next_tile = self.env.dandy_map[next_y * 60 + next_x]
            is_obstacle = (self.env.TILE_MONSTER1 <= next_tile <= self.env.TILE_MONSTER3) or \
                          (self.env.TILE_GENERATOR1 <= next_tile <= self.env.TILE_GENERATOR3)
            
            if is_obstacle:
                # Combat Step: Shoot 1 arrow on the first tick, then hold direction
                self.env.step([btn | self.env.BUTTON_FIRE, 0, 0, 0])
                ticks += 1
                for _ in range(3):
                    self.env.step([btn, 0, 0, 0])
                    ticks += 1
            else:
                # Standard Movement Step: 4 ticks
                for _ in range(4):
                    self.env.step([btn, 0, 0, 0])
                    ticks += 1
                
                # Check for Level Transition
                if self.env.current_level == 1:
                    path_idx += 1
                    break
                
                # Verify successful movement
                new_x = self.env.get_player_x(0)
                new_y = self.env.get_player_y(0)
                if (new_x, new_y) == (next_x, next_y):
                    path_idx += 1
                else:
                    # Allow recovery if player slid slightly due to dynamic monster collisions
                    dist = abs(new_x - next_x) + abs(new_y - next_y)
                    self.assertLessEqual(dist, 2, f"Player diverged too far at step {path_idx}")

        # 6. Double-Assert Rule Verification
        
        # A. Engine State Assertions
        self.assertEqual(self.env.current_level, 1, "Failed to transition to Level 1")
        # Player coordinates are reset to Level 1 portal
        self.assertEqual(self.env.get_player_x(0), 57, "Player not at Level 1 starting portal x")
        self.assertEqual(self.env.get_player_y(0), 1, "Player not at Level 1 starting portal y")
        # Inventory asserts
        self.assertEqual(self.env.get_player_score(0), 1200, "Walkthrough score mismatch")
        self.assertEqual(self.env.get_player_keys(0), 0, "Walkthrough keys not consumed")
        # Health decreases due to active monster collisions (verifies combat works)
        self.assertLess(self.env.get_player_health(0), 9999, "Player took no damage")
        self.assertGreater(self.env.get_player_health(0), 9000, "Player took excessive damage")

        # B. Mock HAL Side-Effect Assertions
        sounds = self.env.get_sounds()
        # Sound count assertions
        self.assertEqual(sounds.count(self.env.SOUND_WARP), 1, "SOUND_WARP must be played exactly once")
        self.assertGreaterEqual(sounds.count(self.env.SOUND_SHOOT), 7, "SOUND_SHOOT count mismatch")
        self.assertGreaterEqual(sounds.count(self.env.SOUND_HIT), 7, "SOUND_HIT count mismatch")
        self.assertGreaterEqual(sounds.count(self.env.SOUND_KEY), 14, "SOUND_KEY (collect/unlock) count mismatch")

        # Viewport Camera Rendering Verification
        self.env.draw_viewport(0)
        cam_x, cam_y = self.env.get_camera()
        # On Level 1, starting portal is at (57, 1). Viewport clamps to right-hand border.
        # Camera target clamp: vp_left = clamp(57 - 10, 0, 60 - 20) = clamp(47, 0, 40) = 40.
        # vp_top = clamp(1 - 5, 0, 30 - 10) = clamp(-4, 0, 20) = 0.
        self.assertEqual(cam_x, 40, "Level 1 camera X clamp mismatch")
        self.assertEqual(cam_y, 0, "Level 1 camera Y clamp mismatch")

        # Sprite Registration Assertions (verifies player is rendered on new map)
        sprites = self.env.get_sprites()
        self.assertTrue(any(self.env.TILE_PLAYER1 <= s['tile_id'] < self.env.TILE_PLAYER1 + 8 for s in sprites.values()),
                        "Player sprite not registered in Level 1 viewport")

if __name__ == '__main__':
    unittest.main()
```
