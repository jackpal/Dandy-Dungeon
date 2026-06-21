import unittest
import os
import sys

# Ensure tests/ directory is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dandy_env import DandyEnv

class TestTier4(unittest.TestCase):
    def setUp(self):
        # Create a new environment copy for each test to achieve 100% isolation
        self.env = DandyEnv()
        self.env.init()
        self.env.assert_outer_border_walls(self)

    def tearDown(self):
        if hasattr(self, "env") and self.env is not None:
            self.env.close()
            self.env = None

    def setup_scenario_map(self, player_positions, custom_tiles):
        """
        Shared Setup Helper:
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

    def helper_setup_clean_map(self, player_x=10, player_y=10, p_idx=0):
        """Helper to initialize a completely clean map with outer border walls and player 0."""
        self.setup_scenario_map({p_idx: (player_x, player_y)}, {})

    def set_tile(self, x, y, tile_id):
        """Helper to set a single tile on the map."""
        m = self.env.dandy_map
        m[y * 60 + x] = tile_id
        self.env.dandy_map = m

    def get_tile(self, x, y):
        """Helper to get a single tile from the map."""
        return self.env.dandy_map[y * 60 + x]

    # =========================================================================
    # 1. test_level_0_complete_walkthrough
    # =========================================================================

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
            self.assertLessEqual(ticks, 2000, "Walkthrough exceeded maximum tick budget - player is likely stuck in an infinite loop!")
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
        self.assertEqual(cam_x, 40, "Level 1 camera X clamp mismatch")
        self.assertEqual(cam_y, 0, "Level 1 camera Y clamp mismatch")

        # Sprite Registration Assertions (verifies player is rendered on new map)
        sprites = self.env.get_sprites()
        self.assertTrue(any(self.env.TILE_PLAYER1 <= s['tile_id'] < self.env.TILE_PLAYER1 + 8 for s in sprites.values()),
                        "Player sprite not registered in Level 1 viewport")

        # Assert border wall integrity on the new level
        self.env.assert_outer_border_walls(self)

    # =========================================================================
    # 2. test_scenario_a_generator_monster_swarm
    # =========================================================================

    def test_scenario_a_generator_monster_swarm(self):
        """Scenario A: Deterministic generator spawning, arrow combat, degradation, and clearing."""
        # 1. Setup
        self.helper_setup_clean_map(10, 10)
        self.set_tile(9, 8, self.env.TILE_GENERATOR1)
        self.set_tile(13, 8, self.env.TILE_GENERATOR2)
        self.set_tile(9, 12, self.env.TILE_GENERATOR3)
        self.set_tile(13, 12, self.env.TILE_GENERATOR1)
        
        # 2. Step 1: Move Left (Tick 1) -> triggers spawn at (9,7) and (13,7)
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
        
        # 3. Step 2a: Turn Up (Tick 2) - split to avoid firing in old direction
        self.env.step([self.env.BUTTON_UP, 0, 0, 0])
        self.assertEqual(self.env.get_player_dir(0), 0) # Up
        
        # 4. Step 2b: Fire Up (Tick 3)
        self.env.clear_mock_buffers()
        self.env.step([self.env.BUTTON_FIRE, 0, 0, 0])
        self.assertEqual(self.env.get_arrow_dir(0), 0)
        self.assertEqual(self.get_tile(9, 9), self.env.TILE_ARROW + 3)
        # HAL asserts
        self.env.draw_viewport(0)
        self.assertIn(self.env.SOUND_SHOOT, self.env.get_sounds())
        
        # 5. Step 3: Wait (Tick 4) -> Arrow hits and destroys Generator 1
        self.env.clear_mock_buffers()
        self.env.step([0, 0, 0, 0])
        self.assertEqual(self.get_tile(9, 8), self.env.TILE_SPACE)
        self.assertEqual(self.env.get_arrow_dir(0), -1)
        # HAL asserts
        self.env.draw_viewport(0)
        self.assertIn(self.env.SOUND_HIT, self.env.get_sounds())
        
        # 6. Step 4: Fire second arrow at Monster 1 (Tick 5)
        self.env.clear_mock_buffers()
        self.env.step([self.env.BUTTON_FIRE, 0, 0, 0])
        self.assertEqual(self.get_tile(9, 9), self.env.TILE_ARROW + 3)
        self.assertIn(self.env.SOUND_SHOOT, self.env.get_sounds())
        
        # 7. Step 5: Arrow fly (Tick 6)
        self.env.step([0, 0, 0, 0])
        self.assertEqual(self.get_tile(9, 8), self.env.TILE_ARROW + 3)
        
        # 8. Step 6: Arrow hits and destroys Monster 1 (Tick 7)
        self.env.clear_mock_buffers()
        self.env.step([0, 0, 0, 0])
        self.assertEqual(self.get_tile(9, 7), self.env.TILE_SPACE)
        self.assertEqual(self.env.get_arrow_dir(0), -1)
        # HAL asserts
        self.env.draw_viewport(0)
        self.assertIn(self.env.SOUND_HIT, self.env.get_sounds())
        
        # 9. Step 7: Move Up (Tick 8)
        self.env.step([self.env.BUTTON_UP, 0, 0, 0])
        self.assertEqual(self.env.get_player_y(0), 9)
        
        # 10. Step 8-10: Cooldown (Ticks 9-11)
        for _ in range(3):
            self.env.step([0, 0, 0, 0])
            
        # 11. Step 11: Move Up to row 8 (Tick 12)
        self.env.step([self.env.BUTTON_UP, 0, 0, 0])
        self.assertEqual(self.env.get_player_y(0), 8)
        
        # 12. Step 12a: Turn Right (Tick 13) - split to avoid firing Up
        self.env.step([self.env.BUTTON_RIGHT, 0, 0, 0])
        self.assertEqual(self.env.get_player_dir(0), 2) # Right
        # Monster 2 ticks at rotor 13 in Tick 13, and moves to (12, 8)
        self.assertEqual(self.get_tile(12, 8), self.env.TILE_MONSTER2)
        
        # 13. Step 12b: Fire Right (Tick 14)
        self.env.clear_mock_buffers()
        self.env.step([self.env.BUTTON_FIRE, 0, 0, 0])
        self.assertEqual(self.env.get_arrow_dir(0), 2)
        self.assertEqual(self.get_tile(10, 8), self.env.TILE_ARROW + 5)
        self.assertIn(self.env.SOUND_SHOOT, self.env.get_sounds())
        
        # 14. Step 13: Arrow fly (Tick 15)
        self.env.step([0, 0, 0, 0])
        self.assertEqual(self.env.get_arrow_x(0), 11)
        
        # 15. Step 14: Arrow hits and degrades Monster 2 to Monster 1 (Tick 16)
        # Note: In Tick 16, the monster degrades to Monster 1, and then immediately ticks (rotor 0) and moves Left to (11, 8).
        self.env.clear_mock_buffers()
        self.env.step([0, 0, 0, 0])
        self.assertEqual(self.get_tile(12, 8), self.env.TILE_SPACE) # Moved away
        self.assertEqual(self.get_tile(11, 8), self.env.TILE_MONSTER1) # Moved here
        self.assertEqual(self.env.get_arrow_dir(0), -1)
        self.assertIn(self.env.SOUND_HIT, self.env.get_sounds())
        
        # 16. Step 15: Fire third arrow (Arrow 4) at the monster now at (11, 8) (Tick 17)
        self.env.clear_mock_buffers()
        self.env.step([self.env.BUTTON_FIRE, 0, 0, 0])
        self.assertEqual(self.get_tile(10, 8), self.env.TILE_ARROW + 5)
        self.assertIn(self.env.SOUND_SHOOT, self.env.get_sounds())
        
        # 17. Step 16: Arrow hits and destroys the monster at (11, 8) (Tick 18)
        self.env.clear_mock_buffers()
        self.env.step([0, 0, 0, 0])
        self.assertEqual(self.get_tile(11, 8), self.env.TILE_SPACE)
        self.assertEqual(self.env.get_arrow_dir(0), -1)
        self.assertIn(self.env.SOUND_HIT, self.env.get_sounds())
        
        # 18. Step 17: Wait 1 tick to keep step timing clean (Tick 19)
        self.env.step([0, 0, 0, 0])
        
        # 19. Step 18: Fire fifth arrow at Generator 2 at (13, 8) (Tick 20)
        self.env.clear_mock_buffers()
        self.env.step([self.env.BUTTON_FIRE, 0, 0, 0])
        self.assertEqual(self.get_tile(10, 8), self.env.TILE_ARROW + 5)
        self.assertIn(self.env.SOUND_SHOOT, self.env.get_sounds())
        
        # 20. Step 19-20: Arrow fly (Ticks 21-22)
        for _ in range(2):
            self.env.step([0, 0, 0, 0])
        self.assertEqual(self.env.get_arrow_x(0), 12)
            
        # 21. Step 21: Arrow hits and destroys Generator 2 (Tick 23)
        self.env.clear_mock_buffers()
        self.env.step([0, 0, 0, 0])
        self.assertEqual(self.get_tile(13, 8), self.env.TILE_SPACE)
        self.assertEqual(self.env.get_arrow_dir(0), -1)
        self.assertIn(self.env.SOUND_HIT, self.env.get_sounds())

    # =========================================================================
    # 3. test_scenario_b_smart_bomb_room_clear
    # =========================================================================

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

    # =========================================================================
    # 4. test_scenario_a_coop_and_viewport
    # =========================================================================

    def test_scenario_a_coop_and_viewport(self):
        """Scenario A: Independent movement, camera centering, clamping, and viewport sprite filtering."""
        # --- 1. SETUP ---
        self.helper_setup_clean_map(10, 10)
        
        # Player 1 (Local, Index 0) is already joined at (10, 10) facing Up (0) by helper.
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
        # Clear old player tile at (11, 10)
        self.set_tile(11, 10, self.env.TILE_SPACE)
        # Warp player position
        self.env.set_player_position(0, 5, 3)
        # Set new player tile at (5, 3) facing Right (26)
        self.set_tile(5, 3, self.env.TILE_PLAYER1 + 2)
        
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
        # Clear old player tile at (5, 3)
        self.set_tile(5, 3, self.env.TILE_SPACE)
        # Warp player position
        self.env.set_player_position(0, 55, 27)
        # Set new player tile at (55, 27) facing Right (26)
        self.set_tile(55, 27, self.env.TILE_PLAYER1 + 2)
        
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
    # 5. test_scenario_b_spectator_and_game_over
    # =========================================================================

    def test_scenario_b_spectator_and_game_over(self):
        """Scenario B: Spectator mode following remaining players, centroid averaging, and game over state reset."""
        # --- 1. SETUP ---
        self.helper_setup_clean_map(10, 10)

        # Player 1 is already joined at (10, 10) by helper.
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
        # Player 3 at (30, 20) -> sx = 30 - 15 = 15, sy = 20 - 10 = 10 -> row 20 is outside viewport!
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
        self.assertEqual(len(self.env.get_sounds()), 0)

        # Retrieve new start coordinates of Player 1
        p0_x = self.env.get_player_x(0)
        p0_y = self.env.get_player_y(0)
        expected_cam_x = max(0, min(40, p0_x - 10))
        expected_cam_y = max(0, min(20, p0_y - 5))
        
        cam_x, cam_y = self.env.get_camera()
        self.assertEqual(cam_x, expected_cam_x)
        self.assertEqual(cam_y, expected_cam_y)

        # Edge Wall Elision reconstruction check on level reload
        # Edge Wall Elision reconstruction check on level reload
        self.env.assert_outer_border_walls(self)

    # =========================================================================
    # 6. test_scenario_c_lfsr_multi_direction
    # =========================================================================

    def test_scenario_c_lfsr_multi_direction(self):
        """Scenario C: Verify LFSR multi-direction spawning determinism by ticking multiple generators in a single step."""
        self.helper_setup_clean_map(10, 10)
        
        # Place 6 generators matching rotor index 5 (mx % 4 == 1, my % 4 == 1)
        # Scan order: (1,5), (5,5), (9,5), (13,5), (17,5), (5,9)
        self.set_tile(1, 5, self.env.TILE_GENERATOR1)
        self.set_tile(5, 5, self.env.TILE_GENERATOR1)
        self.set_tile(9, 5, self.env.TILE_GENERATOR1)
        self.set_tile(13, 5, self.env.TILE_GENERATOR1)
        self.set_tile(17, 5, self.env.TILE_GENERATOR1)
        self.set_tile(5, 9, self.env.TILE_GENERATOR1)
        
        # Set monster_rotor to 4, so that after 1 step it becomes 5
        self.env.monster_rotor = 4
        
        # Step the engine 1 tick
        self.env.step([0, 0, 0, 0])
        
        # Assert spawns based on LFSR sequence:
        # Gen 1 (1,5) -> Tick 1 -> LFSR 0xE270 -> Spawn Up (1,4)
        # Gen 2 (5,5) -> Tick 2 -> LFSR 0x7138 -> Spawn Up (5,4)
        # Gen 3 (9,5) -> Tick 3 -> LFSR 0x389C -> No spawn
        # Gen 4 (13,5) -> Tick 4 -> LFSR 0x1C4E -> No spawn
        # Gen 5 (17,5) -> Tick 5 -> LFSR 0x0E27 -> No spawn
        # Gen 6 (5,9) -> Tick 6 -> LFSR 0xB313 -> Spawn Left (4,9)
        
        self.assertEqual(self.get_tile(1, 4), self.env.TILE_MONSTER1, "Gen 1 should spawn Up")
        self.assertEqual(self.get_tile(5, 4), self.env.TILE_MONSTER1, "Gen 2 should spawn Up")
        self.assertEqual(self.get_tile(4, 9), self.env.TILE_MONSTER1, "Gen 6 should spawn Left")
        
        # Check that no spawns occurred in other directions for Gen 6
        self.assertEqual(self.get_tile(5, 8), self.env.TILE_SPACE, "Gen 6 should NOT spawn Up")
        self.assertEqual(self.get_tile(6, 9), self.env.TILE_SPACE, "Gen 6 should NOT spawn Right")
        self.assertEqual(self.get_tile(5, 10), self.env.TILE_SPACE, "Gen 6 should NOT spawn Down")

if __name__ == '__main__':
    unittest.main()
