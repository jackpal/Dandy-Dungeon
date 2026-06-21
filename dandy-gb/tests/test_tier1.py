import unittest
import os
import sys

# Ensure tests/ directory is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dandy_env import DandyEnv

class TestTier1(unittest.TestCase):
    def setUp(self):
        # Create a new environment copy for each test to achieve 100% isolation
        self.env = DandyEnv()
        self.env.init()
        self.env.assert_outer_border_walls(self)

    def tearDown(self):
        if hasattr(self, "env") and self.env is not None:
            self.env.close()
            self.env = None

    def helper_setup_clean_map(self, player_x=10, player_y=10, p_idx=0):
        """Helper to initialize a completely empty map with player 0 at a given position."""
        custom_map = [self.env.TILE_SPACE] * self.env.MAP_SIZE
        # Set player tile
        custom_map[player_y * 60 + player_x] = self.env.TILE_PLAYER1
        self.env.dandy_map = custom_map
        
        # Set player position and stats
        self.env.set_player_position(p_idx, player_x, player_y)
        self.env.set_player_joined(p_idx, True)
        self.env.set_player_health(p_idx, 100)
        self.env.set_player_score(p_idx, 0)
        self.env.set_player_bombs(p_idx, 0)
        self.env.set_player_keys(p_idx, 0)
        self.env.set_player_dir(p_idx, 0) # Up
        self.env.set_player_move_timer(p_idx, 0)
        
        self.env.clear_mock_buffers()

    def set_tile(self, x, y, tile_id):
        """Helper to set a single tile on the map."""
        m = self.env.dandy_map
        m[y * 60 + x] = tile_id
        self.env.dandy_map = m

    def get_tile(self, x, y):
        """Helper to get a single tile from the map."""
        return self.env.dandy_map[y * 60 + x]

    # =========================================================================
    # F-01: Movement & Timing
    # =========================================================================

    def test_f01_move_success_cardinal(self):
        """F-01: Moving into TILE_SPACE cardinally updates coordinates and sets move timer."""
        self.helper_setup_clean_map(10, 10)
        
        # Action: Step Right
        self.env.step([self.env.BUTTON_RIGHT, 0, 0, 0])
        
        # Assert Globals (State Changes)
        self.assertEqual(self.env.get_player_x(0), 11)
        self.assertEqual(self.env.get_player_y(0), 10)
        self.assertEqual(self.env.get_player_dir(0), 2)  # Right
        self.assertEqual(self.env.get_player_move_timer(0), 3)  # Cooldown active (4 - 1 tick)
        self.assertEqual(self.get_tile(10, 10), self.env.TILE_SPACE)
        self.assertEqual(self.get_tile(11, 10), self.env.TILE_PLAYER1 + 2)  # Player facing Right
        
        # Assert HAL (Side Effects)
        self.env.draw_viewport(0)
        self.assertEqual(len(self.env.get_sounds()), 0)  # No sound on standard movement
        cam_x, cam_y = self.env.get_camera()
        self.assertEqual(cam_x, 1)  # Centered around (11, 10): 11 - 10 = 1
        self.assertEqual(cam_y, 5)  # Centered around (11, 10): 10 - 5 = 5
        sprites = self.env.get_sprites()
        self.assertTrue(any(s['tile_id'] == self.env.TILE_PLAYER1 + 2 for s in sprites.values()))

    def test_f01_move_success_diagonal(self):
        """F-01: Moving into TILE_SPACE diagonally updates coordinates and sets move timer."""
        self.helper_setup_clean_map(10, 10)
        
        # Action: Step Up-Right
        self.env.step([self.env.BUTTON_UP | self.env.BUTTON_RIGHT, 0, 0, 0])
        
        # Assert Globals (State Changes)
        self.assertEqual(self.env.get_player_x(0), 11)
        self.assertEqual(self.env.get_player_y(0), 9)
        self.assertEqual(self.env.get_player_dir(0), 1)  # Up-Right
        self.assertEqual(self.env.get_player_move_timer(0), 3)
        self.assertEqual(self.get_tile(10, 10), self.env.TILE_SPACE)
        self.assertEqual(self.get_tile(11, 9), self.env.TILE_PLAYER1 + 1)
        
        # Assert HAL (Side Effects)
        self.env.draw_viewport(0)
        self.assertEqual(len(self.env.get_sounds()), 0)
        cam_x, cam_y = self.env.get_camera()
        self.assertEqual(cam_x, 1)
        self.assertEqual(cam_y, 4)  # 9 - 5 = 4
        sprites = self.env.get_sprites()
        self.assertTrue(any(s['tile_id'] == self.env.TILE_PLAYER1 + 1 for s in sprites.values()))

    def test_f01_move_cooldown_blocking(self):
        """F-01: player_move_timer prevents movement until it reaches 0."""
        self.helper_setup_clean_map(10, 10)
        
        # Step 1: Move Right (timer becomes 3, player at 11,10)
        self.env.step([self.env.BUTTON_RIGHT, 0, 0, 0])
        self.assertEqual(self.env.get_player_x(0), 11)
        self.assertEqual(self.env.get_player_move_timer(0), 3)
        
        # Step 2: Hold Right (timer becomes 2, player stays at 11,10)
        self.env.step([self.env.BUTTON_RIGHT, 0, 0, 0])
        self.assertEqual(self.env.get_player_x(0), 11)
        self.assertEqual(self.env.get_player_move_timer(0), 2)
        
        # Step 3: Hold Right (timer becomes 1, player stays at 11,10)
        self.env.step([self.env.BUTTON_RIGHT, 0, 0, 0])
        self.assertEqual(self.env.get_player_x(0), 11)
        self.assertEqual(self.env.get_player_move_timer(0), 1)
        
        # Step 4: Hold Right (timer becomes 0, player stays at 11,10)
        self.env.step([self.env.BUTTON_RIGHT, 0, 0, 0])
        self.assertEqual(self.env.get_player_x(0), 11)
        self.assertEqual(self.env.get_player_move_timer(0), 0)
        
        # Step 5: Hold Right (moves again! timer becomes 3, player at 12,10)
        self.env.step([self.env.BUTTON_RIGHT, 0, 0, 0])
        self.assertEqual(self.env.get_player_x(0), 12)
        self.assertEqual(self.env.get_player_move_timer(0), 3)
        
        # Assert HAL
        self.env.draw_viewport(0)
        self.assertEqual(len(self.env.get_sounds()), 0)
        cam_x, cam_y = self.env.get_camera()
        self.assertEqual(cam_x, 2)  # 12 - 10 = 2

    def test_f01_unjoined_player_ignored(self):
        """F-01: Inputs for unjoined players are ignored."""
        self.helper_setup_clean_map(10, 10)
        
        # Player 1 is not joined
        self.assertFalse(self.env.is_player_joined(1))
        p1_initial_x = self.env.get_player_x(1)
        p1_initial_y = self.env.get_player_y(1)
        
        # Action: Inject move input for player 1
        self.env.step([0, self.env.BUTTON_RIGHT, 0, 0])
        
        # Assert Globals: Player 1 did not move
        self.assertEqual(self.env.get_player_x(1), p1_initial_x)
        self.assertEqual(self.env.get_player_y(1), p1_initial_y)
        
        # Assert HAL: No sprite for player 1 is rendered
        self.env.draw_viewport(0)
        sprites = self.env.get_sprites()
        p1_tile_base = self.env.TILE_PLAYER1 + 8
        self.assertFalse(any(p1_tile_base <= s['tile_id'] < p1_tile_base + 8 for s in sprites.values()))

    def test_f01_dead_player_ignored(self):
        """F-01: Dead players (health <= 0) do not process inputs."""
        self.helper_setup_clean_map(10, 10)
        # Join player 1 and keep them alive to prevent game over
        self.env.set_player_position(1, 1, 1)
        self.env.set_player_joined(1, True)
        self.env.set_player_health(1, 100)
        self.set_tile(1, 1, self.env.TILE_PLAYER1 + 8)
        
        self.env.set_player_health(0, 0)
        
        # Action: Step Right for player 0
        self.env.step([self.env.BUTTON_RIGHT, 0, 0, 0])
        
        # Assert Globals: Coordinates unchanged for player 0
        self.assertEqual(self.env.get_player_x(0), 10)
        self.assertEqual(self.env.get_player_y(0), 10)
        
        # Assert HAL: Viewport drawn, no player sprite active for player 0
        self.env.draw_viewport(1)  # Draw viewport for player 1
        sprites = self.env.get_sprites()
        self.assertFalse(any(self.env.TILE_PLAYER1 <= s['tile_id'] < self.env.TILE_PLAYER1 + 8 for s in sprites.values()))


    # =========================================================================
    # F-02: Slide Mechanics
    # =========================================================================

    def test_f02_slide_cardinal_blocked_clockwise(self):
        """F-02: Moving Right blocked by wall slides player Down-Right (clockwise) if free."""
        self.helper_setup_clean_map(10, 10)
        self.set_tile(11, 10, self.env.TILE_WALL)  # Block Right
        self.set_tile(11, 9, self.env.TILE_WALL)   # Block Up-Right
        # (11, 11) is TILE_SPACE (Down-Right)
        
        # Action: Step Right (dir 2)
        self.env.step([self.env.BUTTON_RIGHT, 0, 0, 0])
        
        # Assert Globals: Player slid to (11, 11), direction is 2 (Right, input dir)
        self.assertEqual(self.env.get_player_x(0), 11)
        self.assertEqual(self.env.get_player_y(0), 11)
        self.assertEqual(self.env.get_player_dir(0), 2)
        self.assertEqual(self.get_tile(11, 11), self.env.TILE_PLAYER1 + 2)
        
        # Assert HAL
        self.env.draw_viewport(0)
        cam_x, cam_y = self.env.get_camera()
        self.assertEqual(cam_x, 1)
        self.assertEqual(cam_y, 6)

    def test_f02_slide_cardinal_blocked_counterclockwise(self):
        """F-02: Moving Right blocked by wall slides player Up-Right (counter-clockwise) if free."""
        self.helper_setup_clean_map(10, 10)
        self.set_tile(11, 10, self.env.TILE_WALL)  # Block Right
        self.set_tile(11, 11, self.env.TILE_WALL)  # Block Down-Right
        # (11, 9) is TILE_SPACE (Up-Right)
        
        # Action: Step Right
        self.env.step([self.env.BUTTON_RIGHT, 0, 0, 0])
        
        # Assert Globals: Player slid to (11, 9)
        self.assertEqual(self.env.get_player_x(0), 11)
        self.assertEqual(self.env.get_player_y(0), 9)
        self.assertEqual(self.env.get_player_dir(0), 2)
        self.assertEqual(self.get_tile(11, 9), self.env.TILE_PLAYER1 + 2)
        
        # Assert HAL
        self.env.draw_viewport(0)
        cam_x, cam_y = self.env.get_camera()
        self.assertEqual(cam_x, 1)
        self.assertEqual(cam_y, 4)

    def test_f02_slide_diagonal_blocked_clockwise(self):
        """F-02: Moving Up-Right blocked by wall slides player Right (clockwise) if free."""
        self.helper_setup_clean_map(10, 10)
        self.set_tile(11, 9, self.env.TILE_WALL)   # Block Up-Right
        self.set_tile(10, 9, self.env.TILE_WALL)   # Block Up
        # (11, 10) is TILE_SPACE (Right)
        
        # Action: Step Up-Right
        self.env.step([self.env.BUTTON_UP | self.env.BUTTON_RIGHT, 0, 0, 0])
        
        # Assert Globals: Player slid to (11, 10), direction is 1 (Up-Right)
        self.assertEqual(self.env.get_player_x(0), 11)
        self.assertEqual(self.env.get_player_y(0), 10)
        self.assertEqual(self.env.get_player_dir(0), 1)
        self.assertEqual(self.get_tile(11, 10), self.env.TILE_PLAYER1 + 1)
        
        # Assert HAL
        self.env.draw_viewport(0)
        cam_x, cam_y = self.env.get_camera()
        self.assertEqual(cam_x, 1)
        self.assertEqual(cam_y, 5)

    def test_f02_slide_diagonal_blocked_counterclockwise(self):
        """F-02: Moving Up-Right blocked by wall slides player Up (counter-clockwise) if free."""
        self.helper_setup_clean_map(10, 10)
        self.set_tile(11, 9, self.env.TILE_WALL)   # Block Up-Right
        self.set_tile(11, 10, self.env.TILE_WALL)  # Block Right
        # (10, 9) is TILE_SPACE (Up)
        
        # Action: Step Up-Right
        self.env.step([self.env.BUTTON_UP | self.env.BUTTON_RIGHT, 0, 0, 0])
        
        # Assert Globals: Player slid to (10, 9)
        self.assertEqual(self.env.get_player_x(0), 10)
        self.assertEqual(self.env.get_player_y(0), 9)
        self.assertEqual(self.env.get_player_dir(0), 1)
        self.assertEqual(self.get_tile(10, 9), self.env.TILE_PLAYER1 + 1)
        
        # Assert HAL
        self.env.draw_viewport(0)
        cam_x, cam_y = self.env.get_camera()
        self.assertEqual(cam_x, 0)
        self.assertEqual(cam_y, 4)

    def test_f02_slide_all_blocked(self):
        """F-02: If main direction and both adjacent slide directions are blocked, player remains stationary."""
        self.helper_setup_clean_map(10, 10)
        self.set_tile(11, 10, self.env.TILE_WALL)  # Block Right
        self.set_tile(11, 9, self.env.TILE_WALL)   # Block Up-Right
        self.set_tile(11, 11, self.env.TILE_WALL)  # Block Down-Right
        
        # Action: Step Right
        self.env.step([self.env.BUTTON_RIGHT, 0, 0, 0])
        
        # Assert Globals: Player did not move
        self.assertEqual(self.env.get_player_x(0), 10)
        self.assertEqual(self.env.get_player_y(0), 10)
        self.assertEqual(self.env.get_player_dir(0), 2)
        self.assertEqual(self.get_tile(10, 10), self.env.TILE_PLAYER1 + 2)
        
        # Assert HAL
        self.env.draw_viewport(0)
        cam_x, cam_y = self.env.get_camera()
        self.assertEqual(cam_x, 0)
        self.assertEqual(cam_y, 5)


    # =========================================================================
    # F-03: Item Collection
    # =========================================================================

    def test_f03_collect_food(self):
        """F-03: Collecting TILE_FOOD adds 100 HP, plays SOUND_FOOD, and can exceed 100 HP."""
        self.helper_setup_clean_map(10, 10)
        self.set_tile(11, 10, self.env.TILE_FOOD)
        
        # Action: Step Right
        self.env.step([self.env.BUTTON_RIGHT, 0, 0, 0])
        
        # Assert Globals: Health is 200, tile is player
        self.assertEqual(self.env.get_player_health(0), 200)
        self.assertEqual(self.env.get_player_x(0), 11)
        self.assertEqual(self.get_tile(11, 10), self.env.TILE_PLAYER1 + 2)
        
        # Assert HAL: Sound played
        self.env.draw_viewport(0)
        sounds = self.env.get_sounds()
        self.assertIn(self.env.SOUND_FOOD, sounds)

    def test_f03_collect_money(self):
        """F-03: Collecting TILE_MONEY adds 100 to score, plays SOUND_KEY."""
        self.helper_setup_clean_map(10, 10)
        self.set_tile(11, 10, self.env.TILE_MONEY)
        
        # Action: Step Right
        self.env.step([self.env.BUTTON_RIGHT, 0, 0, 0])
        
        # Assert Globals: Score is 100, tile is player
        self.assertEqual(self.env.get_player_score(0), 100)
        self.assertEqual(self.env.get_player_x(0), 11)
        
        # Assert HAL: Sound played
        self.env.draw_viewport(0)
        sounds = self.env.get_sounds()
        self.assertIn(self.env.SOUND_KEY, sounds)

    def test_f03_collect_key(self):
        """F-03: Collecting TILE_KEY increments keys by 1, plays SOUND_KEY."""
        self.helper_setup_clean_map(10, 10)
        self.set_tile(11, 10, self.env.TILE_KEY)
        
        # Action: Step Right
        self.env.step([self.env.BUTTON_RIGHT, 0, 0, 0])
        
        # Assert Globals: Keys is 1
        self.assertEqual(self.env.get_player_keys(0), 1)
        self.assertEqual(self.env.get_player_x(0), 11)
        
        # Assert HAL
        self.env.draw_viewport(0)
        sounds = self.env.get_sounds()
        self.assertIn(self.env.SOUND_KEY, sounds)

    def test_f03_collect_bomb(self):
        """F-03: Collecting TILE_BOMB increments bombs by 1, plays SOUND_KEY."""
        self.helper_setup_clean_map(10, 10)
        self.set_tile(11, 10, self.env.TILE_BOMB)
        
        # Action: Step Right
        self.env.step([self.env.BUTTON_RIGHT, 0, 0, 0])
        
        # Assert Globals: Bombs is 1
        self.assertEqual(self.env.get_player_bombs(0), 1)
        self.assertEqual(self.env.get_player_x(0), 11)
        
        # Assert HAL
        self.env.draw_viewport(0)
        sounds = self.env.get_sounds()
        self.assertIn(self.env.SOUND_KEY, sounds)

    def test_f03_collect_multiple_items(self):
        """F-03: Multiple items collected in sequence update inventory and play sounds."""
        self.helper_setup_clean_map(10, 10)
        self.set_tile(11, 10, self.env.TILE_FOOD)
        self.set_tile(12, 10, self.env.TILE_KEY)
        
        # Step 1: Collect food
        self.env.step([self.env.BUTTON_RIGHT, 0, 0, 0])
        
        # Wait out move cooldown (3 ticks)
        for _ in range(3):
            self.env.step([0, 0, 0, 0])
            
        # Step 5: Collect key
        self.env.step([self.env.BUTTON_RIGHT, 0, 0, 0])
        
        # Assert Globals
        self.assertEqual(self.env.get_player_x(0), 12)
        self.assertEqual(self.env.get_player_health(0), 200)
        self.assertEqual(self.env.get_player_keys(0), 1)
        
        # Assert HAL: Both sounds recorded
        self.env.draw_viewport(0)
        sounds = self.env.get_sounds()
        self.assertEqual(sounds, [self.env.SOUND_FOOD, self.env.SOUND_KEY])


    # =========================================================================
    # F-04: Door & Key Mechanics
    # =========================================================================

    def test_f04_door_blocked_with_no_key(self):
        """F-04: Moving onto TILE_DOOR with 0 keys is blocked."""
        self.helper_setup_clean_map(10, 10)
        self.set_tile(11, 10, self.env.TILE_DOOR)
        # Block diagonal slide paths so player cannot slide around the door
        self.set_tile(11, 9, self.env.TILE_WALL)
        self.set_tile(11, 11, self.env.TILE_WALL)
        self.env.set_player_keys(0, 0)
        
        # Action: Step Right
        self.env.step([self.env.BUTTON_RIGHT, 0, 0, 0])
        
        # Assert Globals: Stationary, door intact, keys remain 0
        self.assertEqual(self.env.get_player_x(0), 10)
        self.assertEqual(self.env.get_player_y(0), 10)
        self.assertEqual(self.get_tile(11, 10), self.env.TILE_DOOR)
        self.assertEqual(self.env.get_player_keys(0), 0)
        
        # Assert HAL
        self.env.draw_viewport(0)
        self.assertEqual(len(self.env.get_sounds()), 0)

    def test_f04_door_unlock_single(self):
        """F-04: Moving onto isolated TILE_DOOR with >= 1 key consumes 1 key, unlocks it, plays SOUND_KEY."""
        self.helper_setup_clean_map(10, 10)
        self.set_tile(11, 10, self.env.TILE_DOOR)
        self.env.set_player_keys(0, 1)
        
        # Action: Step Right
        self.env.step([self.env.BUTTON_RIGHT, 0, 0, 0])
        
        # Assert Globals: Moved, key consumed, door becomes player
        self.assertEqual(self.env.get_player_x(0), 11)
        self.assertEqual(self.env.get_player_keys(0), 0)
        self.assertEqual(self.get_tile(11, 10), self.env.TILE_PLAYER1 + 2)
        
        # Assert HAL: Sound played
        self.env.draw_viewport(0)
        sounds = self.env.get_sounds()
        self.assertIn(self.env.SOUND_KEY, sounds)

    def test_f04_door_flood_fill_horizontal(self):
        """F-04: Unlocking a door flood-fills and clears contiguous horizontal door tiles."""
        self.helper_setup_clean_map(10, 10)
        self.set_tile(11, 10, self.env.TILE_DOOR)
        self.set_tile(12, 10, self.env.TILE_DOOR)
        self.set_tile(13, 10, self.env.TILE_DOOR)
        self.env.set_player_keys(0, 1)
        
        # Action: Step Right
        self.env.step([self.env.BUTTON_RIGHT, 0, 0, 0])
        
        # Assert Globals: Player at 11,10, all 3 doors turned to SPACE/player
        self.assertEqual(self.env.get_player_x(0), 11)
        self.assertEqual(self.env.get_player_keys(0), 0)
        self.assertEqual(self.get_tile(11, 10), self.env.TILE_PLAYER1 + 2)
        self.assertEqual(self.get_tile(12, 10), self.env.TILE_SPACE)
        self.assertEqual(self.get_tile(13, 10), self.env.TILE_SPACE)
        
        # Assert HAL
        self.env.draw_viewport(0)
        sounds = self.env.get_sounds()
        self.assertIn(self.env.SOUND_KEY, sounds)

    def test_f04_door_flood_fill_diagonal(self):
        """F-04: Unlocking a door flood-fills and clears diagonally-connected door tiles (8-way)."""
        self.helper_setup_clean_map(10, 10)
        self.set_tile(11, 10, self.env.TILE_DOOR)
        self.set_tile(12, 11, self.env.TILE_DOOR)  # Connected diagonally (Down-Right)
        self.env.set_player_keys(0, 1)
        
        # Action: Step Right
        self.env.step([self.env.BUTTON_RIGHT, 0, 0, 0])
        
        # Assert Globals: Both doors cleared
        self.assertEqual(self.env.get_player_x(0), 11)
        self.assertEqual(self.env.get_player_keys(0), 0)
        self.assertEqual(self.get_tile(11, 10), self.env.TILE_PLAYER1 + 2)
        self.assertEqual(self.get_tile(12, 11), self.env.TILE_SPACE)
        
        # Assert HAL
        self.env.draw_viewport(0)
        sounds = self.env.get_sounds()
        self.assertIn(self.env.SOUND_KEY, sounds)

    def test_f04_door_flood_fill_large_network(self):
        """F-04: Unlocking a door clears a large complex contiguous door network with 1 key."""
        self.helper_setup_clean_map(10, 10)
        # Create a 2x3 block of doors
        for x in [11, 12]:
            for y in [9, 10, 11]:
                self.set_tile(x, y, self.env.TILE_DOOR)
        self.env.set_player_keys(0, 1)
        
        # Action: Step Right into the block
        self.env.step([self.env.BUTTON_RIGHT, 0, 0, 0])
        
        # Assert Globals: Entire block cleared, 1 key consumed
        self.assertEqual(self.env.get_player_x(0), 11)
        self.assertEqual(self.env.get_player_keys(0), 0)
        for x in [11, 12]:
            for y in [9, 10, 11]:
                if x == 11 and y == 10:
                    self.assertEqual(self.get_tile(x, y), self.env.TILE_PLAYER1 + 2)
                else:
                    self.assertEqual(self.get_tile(x, y), self.env.TILE_SPACE)
                    
        # Assert HAL
        self.env.draw_viewport(0)
        sounds = self.env.get_sounds()
        self.assertIn(self.env.SOUND_KEY, sounds)


    # =========================================================================
    # F-05: Combat & Projectiles
    # =========================================================================

    def test_f05_shoot_arrow_empty_space(self):
        """F-05: Pressing FIRE spawns an arrow in player's direction, plays SOUND_SHOOT."""
        self.helper_setup_clean_map(10, 10)
        self.env.set_player_dir(0, 2)  # Facing Right
        self.set_tile(10, 10, self.env.TILE_PLAYER1 + 2)
        
        # Action: Press FIRE (with Right direction held so they face Right, or just FIRE)
        # In dandy_core.c: "Pressing BUTTON_FIRE when arrow_dir == -1 fires..."
        self.env.step([self.env.BUTTON_FIRE, 0, 0, 0])
        
        # Assert Globals: Arrow spawned at (11, 10) in direction 2
        self.assertEqual(self.env.get_arrow_dir(0), 2)
        self.assertEqual(self.env.get_arrow_x(0), 11)
        self.assertEqual(self.env.get_arrow_y(0), 10)
        # Note: arrow tile at (11, 10) is TILE_ARROW + ((arrow_dir - 5) & 7)
        # ((2 - 5) & 7) = 5. TILE_ARROW + 5 = 16 + 5 = 21
        self.assertEqual(self.get_tile(11, 10), self.env.TILE_ARROW + 5)
        
        # Assert HAL: SOUND_SHOOT played
        self.env.draw_viewport(0)
        sounds = self.env.get_sounds()
        self.assertIn(self.env.SOUND_SHOOT, sounds)

    def test_f05_arrow_flight(self):
        """F-05: Active arrow travels 1 tile per tick in its direction."""
        self.helper_setup_clean_map(10, 10)
        self.env.set_player_dir(0, 2)
        self.set_tile(10, 10, self.env.TILE_PLAYER1 + 2)
        
        # Step 1: Fire arrow (arrow moves to 11, 10)
        self.env.step([self.env.BUTTON_FIRE, 0, 0, 0])
        self.assertEqual(self.env.get_arrow_x(0), 11)
        self.assertEqual(self.get_tile(11, 10), self.env.TILE_ARROW + 5)
        
        # Step 2: Empty step (arrow moves to 12, 10)
        self.env.step([0, 0, 0, 0])
        
        # Assert Globals
        self.assertEqual(self.env.get_arrow_x(0), 12)
        self.assertEqual(self.get_tile(11, 10), self.env.TILE_SPACE)
        self.assertEqual(self.get_tile(12, 10), self.env.TILE_ARROW + 5)
        
        # Assert HAL
        self.env.draw_viewport(0)
        sounds = self.env.get_sounds()
        self.assertEqual(sounds.count(self.env.SOUND_SHOOT), 1)

    def test_f05_arrow_hit_wall(self):
        """F-05: Arrow hitting a solid wall is destroyed, no sound is played."""
        self.helper_setup_clean_map(10, 10)
        self.env.set_player_dir(0, 2)
        self.set_tile(10, 10, self.env.TILE_PLAYER1 + 2)
        self.set_tile(12, 10, self.env.TILE_WALL)  # Wall at 12, 10
        
        # Step 1: Fire arrow (moves to 11, 10)
        self.env.step([self.env.BUTTON_FIRE, 0, 0, 0])
        self.assertEqual(self.env.get_arrow_x(0), 11)
        
        # Step 2: Empty step (hits wall at 12, 10 and dies)
        self.env.step([0, 0, 0, 0])
        
        # Assert Globals: Arrow destroyed, wall intact
        self.assertEqual(self.env.get_arrow_dir(0), -1)
        self.assertEqual(self.get_tile(12, 10), self.env.TILE_WALL)
        self.assertEqual(self.get_tile(11, 10), self.env.TILE_SPACE)
        
        # Assert HAL: No HIT sound (only SHOOT)
        self.env.draw_viewport(0)
        sounds = self.env.get_sounds()
        self.assertNotIn(self.env.SOUND_HIT, sounds)

    def test_f05_arrow_hit_monster_degrade(self):
        """F-05: Arrow hitting TILE_MONSTER2 degrades it to TILE_MONSTER1, plays SOUND_HIT, destroys arrow."""
        self.helper_setup_clean_map(10, 10)
        self.env.set_player_dir(0, 2)
        self.set_tile(10, 10, self.env.TILE_PLAYER1 + 2)
        self.set_tile(11, 10, self.env.TILE_MONSTER2)  # Monster right next to player
        
        # Action: Fire arrow (fires and hits in same step!)
        self.env.step([self.env.BUTTON_FIRE, 0, 0, 0])
        
        # Assert Globals: Arrow destroyed, monster degraded to level 1
        self.assertEqual(self.env.get_arrow_dir(0), -1)
        self.assertEqual(self.get_tile(11, 10), self.env.TILE_MONSTER1)
        
        # Assert HAL: Both SHOOT and HIT sounds played
        self.env.draw_viewport(0)
        sounds = self.env.get_sounds()
        self.assertIn(self.env.SOUND_SHOOT, sounds)
        self.assertIn(self.env.SOUND_HIT, sounds)

    def test_f05_arrow_hit_generator_destroy(self):
        """F-05: Arrow hitting a generator replaces it with TILE_SPACE, plays SOUND_HIT."""
        self.helper_setup_clean_map(10, 10)
        self.env.set_player_dir(0, 2)
        self.set_tile(10, 10, self.env.TILE_PLAYER1 + 2)
        self.set_tile(11, 10, self.env.TILE_GENERATOR1)
        
        # Action: Fire
        self.env.step([self.env.BUTTON_FIRE, 0, 0, 0])
        
        # Assert Globals: Generator replaced by space
        self.assertEqual(self.env.get_arrow_dir(0), -1)
        self.assertEqual(self.get_tile(11, 10), self.env.TILE_SPACE)
        
        # Assert HAL: HIT sound played
        self.env.draw_viewport(0)
        sounds = self.env.get_sounds()
        self.assertIn(self.env.SOUND_HIT, sounds)


    # =========================================================================
    # F-06: Smart Bomb Action
    # =========================================================================

    def test_f06_bomb_no_bombs(self):
        """F-06: Pressing BOMB with 0 bombs in inventory does nothing."""
        self.helper_setup_clean_map(10, 10)
        self.set_tile(11, 10, self.env.TILE_MONSTER1)
        self.env.set_player_bombs(0, 0)
        
        # Action: Press BOMB
        self.env.step([self.env.BUTTON_BOMB, 0, 0, 0])
        
        # Assert Globals: Monster intact, bombs remain 0
        self.assertEqual(self.get_tile(11, 10), self.env.TILE_MONSTER1)
        self.assertEqual(self.env.get_player_bombs(0), 0)
        
        # Assert HAL: No bomb sound
        self.env.draw_viewport(0)
        sounds = self.env.get_sounds()
        self.assertNotIn(self.env.SOUND_BOMB, sounds)

    def test_f06_bomb_success_clears_monsters(self):
        """F-06: Pressing BOMB consumes 1 bomb, plays SOUND_BOMB, and clears all monsters in viewport."""
        self.helper_setup_clean_map(10, 10)
        self.set_tile(11, 10, self.env.TILE_MONSTER1)
        self.set_tile(5, 8, self.env.TILE_MONSTER3)  # Also inside viewport
        self.env.set_player_bombs(0, 1)
        
        # Action: Press BOMB
        self.env.step([self.env.BUTTON_BOMB, 0, 0, 0])
        
        # Assert Globals: Monsters cleared, bomb consumed
        self.assertEqual(self.get_tile(11, 10), self.env.TILE_SPACE)
        self.assertEqual(self.get_tile(5, 8), self.env.TILE_SPACE)
        self.assertEqual(self.env.get_player_bombs(0), 0)
        
        # Assert HAL: Sound played
        self.env.draw_viewport(0)
        sounds = self.env.get_sounds()
        self.assertIn(self.env.SOUND_BOMB, sounds)

    def test_f06_bomb_success_clears_generators(self):
        """F-06: Pressing BOMB clears all generators in player's viewport."""
        self.helper_setup_clean_map(10, 10)
        self.set_tile(11, 10, self.env.TILE_GENERATOR1)
        self.set_tile(5, 8, self.env.TILE_GENERATOR3)
        self.env.set_player_bombs(0, 1)
        
        # Action: Press BOMB
        self.env.step([self.env.BUTTON_BOMB, 0, 0, 0])
        
        # Assert Globals: Generators cleared
        self.assertEqual(self.get_tile(11, 10), self.env.TILE_SPACE)
        self.assertEqual(self.get_tile(5, 8), self.env.TILE_SPACE)
        self.assertEqual(self.env.get_player_bombs(0), 0)
        
        # Assert HAL: Sound played
        self.env.draw_viewport(0)
        sounds = self.env.get_sounds()
        self.assertIn(self.env.SOUND_BOMB, sounds)

    def test_f06_bomb_does_not_affect_outside(self):
        """F-06: BOMB clears ONLY monsters/generators inside player's 10x20 viewport, leaving off-screen ones intact."""
        self.helper_setup_clean_map(10, 10)  # Viewport is columns 0..19, rows 5..14
        self.set_tile(20, 10, self.env.TILE_MONSTER1)  # Just outside right edge
        self.set_tile(10, 4, self.env.TILE_MONSTER1)   # Just above top edge
        self.env.set_player_bombs(0, 1)
        
        # Action: Press BOMB
        self.env.step([self.env.BUTTON_BOMB, 0, 0, 0])
        
        # Assert Globals: Off-screen monsters remain untouched
        self.assertEqual(self.get_tile(20, 10), self.env.TILE_MONSTER1)
        self.assertEqual(self.get_tile(10, 4), self.env.TILE_MONSTER1)
        self.assertEqual(self.env.get_player_bombs(0), 0)
        
        # Assert HAL
        self.env.draw_viewport(0)
        sounds = self.env.get_sounds()
        self.assertIn(self.env.SOUND_BOMB, sounds)

    def test_f06_bomb_by_shooting_bomb_tile(self):
        """F-06: Shooting TILE_BOMB with an arrow triggers a viewport explosion without consuming inventory bombs."""
        self.helper_setup_clean_map(10, 10)
        self.env.set_player_dir(0, 2)
        self.set_tile(10, 10, self.env.TILE_PLAYER1 + 2)
        self.set_tile(11, 10, self.env.TILE_BOMB)  # Bomb tile in front of player
        self.set_tile(12, 10, self.env.TILE_MONSTER1)  # Monster in viewport
        self.env.set_player_bombs(0, 0)
        
        # Action: Fire arrow
        self.env.step([self.env.BUTTON_FIRE, 0, 0, 0])
        
        # Assert Globals: Bomb tile cleared, monster cleared, player bombs remain 0
        self.assertEqual(self.get_tile(11, 10), self.env.TILE_SPACE)
        self.assertEqual(self.get_tile(12, 10), self.env.TILE_SPACE)
        self.assertEqual(self.env.get_player_bombs(0), 0)
        self.assertEqual(self.env.get_arrow_dir(0), -1)
        
        # Assert HAL: Plays SOUND_HIT when arrow strikes the bomb
        self.env.draw_viewport(0)
        sounds = self.env.get_sounds()
        self.assertIn(self.env.SOUND_HIT, sounds)


    # =========================================================================
    # F-07: Monster Behavior
    # =========================================================================

    def test_f07_monster_pathfinding_towards_player(self):
        """F-07: Visible monster pathfinds towards nearest player on its active rotor tick."""
        self.helper_setup_clean_map(10, 10)
        # Place Monster 1 at (9, 8). Inside viewport, rotor index: (8%4)*4 + (9%4) = 0*4 + 1 = 1.
        self.set_tile(9, 8, self.env.TILE_MONSTER1)
        
        # Action: Step 1 (monster rotor becomes 1, monster ticks and moves towards player)
        self.env.step([0, 0, 0, 0])
        
        # Assert Globals: Monster moved to (10, 9) (closer to player at 10,10)
        self.assertEqual(self.get_tile(9, 8), self.env.TILE_SPACE)
        self.assertEqual(self.get_tile(10, 9), self.env.TILE_MONSTER1)
        
        # Assert HAL
        self.env.draw_viewport(0)
        sprites = self.env.get_sprites()
        self.assertTrue(any(s['tile_id'] == self.env.TILE_MONSTER1 for s in sprites.values()))

    def test_f07_monster_contact_damage(self):
        """F-07: Monster colliding with player deals 10 * level damage, plays SOUND_HIT, and is removed."""
        self.helper_setup_clean_map(10, 10)
        # Place Monster 1 (level 1) at (9, 10). Rotor index: (10%4)*4 + (9%4) = 2*4 + 1 = 9.
        self.set_tile(9, 10, self.env.TILE_MONSTER1)
        
        # Action: Step 9 times to let monster rotor reach 9
        for _ in range(9):
            self.env.step([0, 0, 0, 0])
            
        # Assert Globals: Player health reduced by 10 (100 -> 90), monster removed
        self.assertEqual(self.env.get_player_health(0), 90)
        self.assertEqual(self.get_tile(9, 10), self.env.TILE_SPACE)
        
        # Assert HAL: Sound played
        self.env.draw_viewport(0)
        sounds = self.env.get_sounds()
        self.assertIn(self.env.SOUND_HIT, sounds)

    def test_f07_monster_contact_damage_by_level(self):
        """F-07: Level 3 monster deals 30 damage."""
        self.helper_setup_clean_map(10, 10)
        # Place Monster 3 (level 3) at (9, 10). Rotor index 9.
        self.set_tile(9, 10, self.env.TILE_MONSTER3)
        
        for _ in range(9):
            self.env.step([0, 0, 0, 0])
            
        # Assert Globals: Health reduced by 30 (100 -> 70), monster removed
        self.assertEqual(self.env.get_player_health(0), 70)
        self.assertEqual(self.get_tile(9, 10), self.env.TILE_SPACE)
        
        # Assert HAL: Sound played
        self.env.draw_viewport(0)
        sounds = self.env.get_sounds()
        self.assertIn(self.env.SOUND_HIT, sounds)

    def test_f07_player_death_removes_tile(self):
        """F-07: Player dying (HP <= 0) clears player tile immediately and plays SOUND_DIE."""
        self.helper_setup_clean_map(10, 10)
        # Join Player 1 at (1, 1) to keep game running and prevent immediate game over level reset
        self.env.set_player_position(1, 1, 1)
        self.env.set_player_joined(1, True)
        self.env.set_player_health(1, 100)
        self.set_tile(1, 1, self.env.TILE_PLAYER1 + 8)
        
        # Set Player 0 health to 10. Place Monster 1 at (9, 10) (rotor index 9).
        self.env.set_player_health(0, 10)
        self.set_tile(9, 10, self.env.TILE_MONSTER1)
        
        # Action: Step 9 times to trigger attack
        for _ in range(9):
            self.env.step([0, 0, 0, 0])
            
        # Assert Globals: Player 0 is dead (HP 0), player 0 tile cleared from map
        self.assertEqual(self.env.get_player_health(0), 0)
        self.assertEqual(self.get_tile(10, 10), self.env.TILE_SPACE)
        self.assertEqual(self.get_tile(9, 10), self.env.TILE_SPACE)
        self.assertEqual(self.env.get_player_health(1), 100)  # Player 1 unaffected
        
        # Assert HAL: SOUND_DIE played
        self.env.draw_viewport(1)  # Draw viewport for player 1
        sounds = self.env.get_sounds()
        self.assertIn(self.env.SOUND_DIE, sounds)

    def test_f07_off_screen_monster_frozen(self):
        """F-07: Monsters outside any active player's viewport remain frozen (do not pathfind)."""
        self.helper_setup_clean_map(10, 10)  # Viewport is columns 0..19, rows 5..14
        # Place Monster 1 at (21, 8) (off-screen). Rotor index: (8%4)*4 + (21%4) = 0*4 + 1 = 1.
        self.set_tile(21, 8, self.env.TILE_MONSTER1)
        
        # Action: Step 1 (rotor index 1 ticked)
        self.env.step([0, 0, 0, 0])
        
        # Assert Globals: Monster did not move
        self.assertEqual(self.get_tile(21, 8), self.env.TILE_MONSTER1)
        
        # Assert HAL: Sprite is not active in viewport
        self.env.draw_viewport(0)
        sprites = self.env.get_sprites()
        self.assertFalse(any(s['tile_id'] == self.env.TILE_MONSTER1 for s in sprites.values()))


    # =========================================================================
    # F-08: Generator Spawning
    # =========================================================================

    def test_f08_generator_spawn_level1(self):
        """F-08: Generator 1 spawns Level 1 monster on its seed tick in adjacent cardinal space."""
        self.helper_setup_clean_map(10, 10)
        # Place Generator 1 at (9, 8). Rotor index 1.
        self.set_tile(9, 8, self.env.TILE_GENERATOR1)
        
        # Action: Step 1. Ticks generator.
        # LFSR 1st update: rand_seed becomes 0xE270.
        # (0xE270 & 7) < 4 is True (0 < 4). spawn_dir = 0 (Up).
        # It spawns a level 1 monster at (9, 7) (Up of generator).
        self.env.step([0, 0, 0, 0])
        
        # Assert Globals: Monster spawned
        self.assertEqual(self.get_tile(9, 8), self.env.TILE_GENERATOR1)
        self.assertEqual(self.get_tile(9, 7), self.env.TILE_MONSTER1)
        
        # Assert HAL
        self.env.draw_viewport(0)
        sprites = self.env.get_sprites()
        self.assertTrue(any(s['tile_id'] == self.env.TILE_MONSTER1 for s in sprites.values()))

    def test_f08_generator_spawn_level3(self):
        """F-08: Generator 3 spawns Level 3 monster."""
        self.helper_setup_clean_map(10, 10)
        # Place Generator 3 at (9, 8). Rotor index 1.
        self.set_tile(9, 8, self.env.TILE_GENERATOR3)
        
        # Action: Step 1
        self.env.step([0, 0, 0, 0])
        
        # Assert Globals: Level 3 monster spawned at (9, 7)
        self.assertEqual(self.get_tile(9, 8), self.env.TILE_GENERATOR3)
        self.assertEqual(self.get_tile(9, 7), self.env.TILE_MONSTER3)
        
        # Assert HAL
        self.env.draw_viewport(0)
        sprites = self.env.get_sprites()
        self.assertTrue(any(s['tile_id'] == self.env.TILE_MONSTER3 for s in sprites.values()))

    def test_f08_generator_spawn_dir_blocked(self):
        """F-08: If primary spawn direction is blocked, generator spawns in next clockwise direction."""
        self.helper_setup_clean_map(10, 10)
        # Place Generator 1 at (9, 8) (rotor index 1). Block Up (9, 7) with a wall.
        self.set_tile(9, 8, self.env.TILE_GENERATOR1)
        self.set_tile(9, 7, self.env.TILE_WALL)
        
        # Action: Step 1. Primary (Up) is blocked, should try Right (10, 8).
        self.env.step([0, 0, 0, 0])
        
        # Assert Globals: Monster spawned at (10, 8) (Right)
        self.assertEqual(self.get_tile(9, 7), self.env.TILE_WALL)
        self.assertEqual(self.get_tile(10, 8), self.env.TILE_MONSTER1)
        
        # Assert HAL
        self.env.draw_viewport(0)
        sprites = self.env.get_sprites()
        self.assertTrue(any(s['tile_id'] == self.env.TILE_MONSTER1 for s in sprites.values()))

    def test_f08_generator_off_screen_frozen(self):
        """F-08: Off-screen generators remain frozen (do not tick or spawn monsters)."""
        self.helper_setup_clean_map(10, 10)  # Viewport columns 0..19, rows 5..14
        # Place Generator at (21, 8) (off-screen, rotor index 1).
        self.set_tile(21, 8, self.env.TILE_GENERATOR1)
        
        # Action: Step 1
        self.env.step([0, 0, 0, 0])
        
        # Assert Globals: No spawning occurred
        self.assertEqual(self.get_tile(21, 7), self.env.TILE_SPACE)
        self.assertEqual(self.get_tile(22, 8), self.env.TILE_SPACE)
        
        # Assert HAL
        self.env.draw_viewport(0)
        sprites = self.env.get_sprites()
        self.assertFalse(any(s['tile_id'] == self.env.TILE_MONSTER1 for s in sprites.values()))

    def test_f08_generator_no_spawn_on_fail_tick(self):
        """F-08: Generator ticks sharing LFSR seed update; third tick fails spawning condition."""
        self.helper_setup_clean_map(10, 10)
        # Place 3 generators inside viewport, all with rotor index 1:
        # Gen 1 at (9, 8), Gen 2 at (13, 8), Gen 3 at (17, 8)
        self.set_tile(9, 8, self.env.TILE_GENERATOR1)
        self.set_tile(13, 8, self.env.TILE_GENERATOR1)
        self.set_tile(17, 8, self.env.TILE_GENERATOR1)
        
        # Action: Step 1.
        # Loop order scans row 8: (9,8) ticks 1st (spawns), (13,8) ticks 2nd (spawns), (17,8) ticks 3rd (fails!).
        self.env.step([0, 0, 0, 0])
        
        # Assert Globals
        # Gen 1 spawned monster at (9, 7)
        self.assertEqual(self.get_tile(9, 7), self.env.TILE_MONSTER1)
        # Gen 2 spawned monster at (13, 7)
        self.assertEqual(self.get_tile(13, 7), self.env.TILE_MONSTER1)
        # Gen 3 did NOT spawn any monster (all adjacent cells remain space)
        self.assertEqual(self.get_tile(17, 7), self.env.TILE_SPACE)
        self.assertEqual(self.get_tile(18, 8), self.env.TILE_SPACE)
        self.assertEqual(self.get_tile(17, 9), self.env.TILE_SPACE)
        self.assertEqual(self.get_tile(16, 8), self.env.TILE_SPACE)
        
        # Assert HAL
        self.env.draw_viewport(0)
        sprites = self.env.get_sprites()
        monster_sprites = [s for s in sprites.values() if s['tile_id'] == self.env.TILE_MONSTER1]
        self.assertEqual(len(monster_sprites), 2)  # Exactly 2 monster sprites active


    # =========================================================================
    # F-09: Multiplayer & Viewport
    # =========================================================================

    def test_f09_multiplayer_join(self):
        """F-09: Multiple players can join, spawning at specific offsets around the portal."""
        # Find TILE_UP on the default level 0 map dynamically to avoid hardcoding
        m = self.env.dandy_map
        up_x, up_y = -1, -1
        for y in range(30):
            for x in range(60):
                if m[y * 60 + x] == self.env.TILE_UP:
                    up_x, up_y = x, y
                    break
            if up_x != -1:
                break
        
        self.assertTrue(up_x != -1 and up_y != -1, "Portal TILE_UP must exist in Level 0")
        
        # Action: Join player 1, 2, and 3 (player 0 is already joined by init)
        self.env.join_player(1)
        self.env.join_player(2)
        self.env.join_player(3)
        
        # Assert Globals: Joined, spawned at spawn offsets around portal (up_x, up_y)
        # spawn_offsets_x = { 0, 1, 0, -1 }
        # spawn_offsets_y = { -1, 0, 1, 0 }
        self.assertTrue(self.env.is_player_joined(0))
        self.assertTrue(self.env.is_player_joined(1))
        self.assertTrue(self.env.is_player_joined(2))
        self.assertTrue(self.env.is_player_joined(3))
        
        self.assertEqual(self.env.get_player_x(0), up_x)
        self.assertEqual(self.env.get_player_y(0), up_y - 1)
        self.assertEqual(self.env.get_player_x(1), up_x + 1)
        self.assertEqual(self.env.get_player_y(1), up_y)
        self.assertEqual(self.env.get_player_x(2), up_x)
        self.assertEqual(self.env.get_player_y(2), up_y + 1)
        self.assertEqual(self.env.get_player_x(3), up_x - 1)
        self.assertEqual(self.env.get_player_y(3), up_y)
        
        # Check map tiles
        self.assertEqual(self.get_tile(up_x, up_y - 1), self.env.TILE_PLAYER1)  # Player 0
        self.assertEqual(self.get_tile(up_x + 1, up_y), self.env.TILE_PLAYER1 + 8)  # Player 1
        self.assertEqual(self.get_tile(up_x, up_y + 1), self.env.TILE_PLAYER1 + 16) # Player 2
        self.assertEqual(self.get_tile(up_x - 1, up_y), self.env.TILE_PLAYER1 + 24)  # Player 3
        
        # Assert HAL
        self.env.draw_viewport(0)
        sprites = self.env.get_sprites()
        self.assertEqual(len([s for s in sprites.values() if self.env.TILE_PLAYER1 <= s['tile_id'] <= self.env.TILE_PLAYER1 + 31]), 4)

    def test_f09_camera_centering(self):
        """F-09: Viewport centers on local player coordinates (target_x - 10, target_y - 5)."""
        self.helper_setup_clean_map(25, 15)
        
        # Action: Draw viewport for local player 0
        self.env.draw_viewport(0)
        
        # Assert C Globals (Double-Assert)
        self.assertEqual(self.env.get_player_x(0), 25)
        self.assertEqual(self.env.get_player_y(0), 15)
        
        # Assert HAL: Camera coordinates (25 - 10, 15 - 5) = (15, 10)
        cam_x, cam_y = self.env.get_camera()
        self.assertEqual(cam_x, 15)
        self.assertEqual(cam_y, 10)

    def test_f09_camera_clamping_left_top(self):
        """F-09: Viewport camera is clamped to (0, 0) at top-left map boundaries."""
        self.helper_setup_clean_map(5, 3)
        
        # Action: Draw
        self.env.draw_viewport(0)
        
        # Assert C Globals (Double-Assert)
        self.assertEqual(self.env.get_player_x(0), 5)
        self.assertEqual(self.env.get_player_y(0), 3)
        
        # Assert HAL: Clamped to (0, 0)
        cam_x, cam_y = self.env.get_camera()
        self.assertEqual(cam_x, 0)
        self.assertEqual(cam_y, 0)

    def test_f09_camera_clamping_right_bottom(self):
        """F-09: Viewport camera is clamped to (40, 20) at bottom-right map boundaries (60x30)."""
        self.helper_setup_clean_map(55, 27)
        
        # Action: Draw
        self.env.draw_viewport(0)
        
        # Assert C Globals (Double-Assert)
        self.assertEqual(self.env.get_player_x(0), 55)
        self.assertEqual(self.env.get_player_y(0), 27)
        
        # Assert HAL: Clamped to (40, 20)
        cam_x, cam_y = self.env.get_camera()
        self.assertEqual(cam_x, 40)
        self.assertEqual(cam_y, 20)

    def test_f09_spectator_mode(self):
        """F-09: Spectator Mode: Camera follows the centroid of remaining alive players when local player dies."""
        self.helper_setup_clean_map(10, 10)  # Local player 0 starts at (10, 10)
        self.env.set_player_health(0, 0)     # Local player 0 is dead
        
        # Join player 1 at (20, 10), player 2 at (20, 20)
        self.env.set_player_position(1, 20, 10)
        self.env.set_player_joined(1, True)
        self.env.set_player_health(1, 100)
        
        self.env.set_player_position(2, 20, 20)
        self.env.set_player_joined(2, True)
        self.env.set_player_health(2, 100)
        
        # Centroid of alive players (1 and 2):
        # target_x = (20 + 20) / 2 = 20
        # target_y = (10 + 20) / 2 = 15
        # Expected Camera: (20 - 10, 15 - 5) = (10, 10)
        
        # Action: Draw viewport for local player 0
        self.env.draw_viewport(0)
        
        # Assert C Globals (Double-Assert)
        self.assertEqual(self.env.get_player_health(0), 0)
        self.assertEqual(self.env.get_player_health(1), 100)
        self.assertEqual(self.env.get_player_x(1), 20)
        self.assertEqual(self.env.get_player_y(1), 10)
        self.assertEqual(self.env.get_player_health(2), 100)
        self.assertEqual(self.env.get_player_x(2), 20)
        self.assertEqual(self.env.get_player_y(2), 20)
        
        # Assert HAL: Camera centered on centroid
        cam_x, cam_y = self.env.get_camera()
        self.assertEqual(cam_x, 10)
        self.assertEqual(cam_y, 10)


    # =========================================================================
    # F-10: Level Transitions
    # =========================================================================

    def test_f10_stairs_loads_next_level(self):
        """F-10: Stepping onto TILE_DOWN increments level, warps coordinates to portal, plays SOUND_WARP."""
        self.helper_setup_clean_map(10, 10)
        self.set_tile(11, 10, self.env.TILE_DOWN)  # Place stairs
        
        # Action: Step Right
        self.env.step([self.env.BUTTON_RIGHT, 0, 0, 0])
        
        # Assert Globals: Next level loaded, coordinates reset to level 1 starting portal
        self.assertEqual(self.env.current_level, 1)
        # Verify player is at level 1 starting portal
        # Let's find TILE_UP in level 1 to see if we match it
        # We can just verify player coordinates are set to starting portal coordinates in level 1.
        self.assertTrue(self.env.get_player_x(0) != 11 or self.env.get_player_y(0) != 10)
        
        # Assert HAL: SOUND_WARP played
        self.env.draw_viewport(0)
        sounds = self.env.get_sounds()
        self.assertIn(self.env.SOUND_WARP, sounds)
        self.env.assert_outer_border_walls(self)

    def test_f10_next_level_clamps_at_max(self):
        """F-10: Stepping on stairs at maximum level (4) clamps level and reloads level 4."""
        self.helper_setup_clean_map(10, 10)
        max_level = self.env.num_levels - 1
        self.env.current_level = max_level
        self.env.load_level(max_level)
        # Find starting position of player in level 4
        px = self.env.get_player_x(0)
        py = self.env.get_player_y(0)
        # Place stairs adjacent to player
        self.set_tile(px + 1, py, self.env.TILE_DOWN)
        
        self.env.clear_mock_buffers()
        
        # Action: Step Right into stairs
        self.env.step([self.env.BUTTON_RIGHT, 0, 0, 0])
        
        # Assert Globals: Level remains 4, reloaded
        self.assertEqual(self.env.current_level, max_level)
        self.assertEqual(self.env.get_player_x(0), px)
        self.assertEqual(self.env.get_player_y(0), py)
        
        # Assert HAL: Sound played
        self.env.draw_viewport(0)
        sounds = self.env.get_sounds()
        self.assertIn(self.env.SOUND_WARP, sounds)
        self.env.assert_outer_border_walls(self)

    def test_f10_game_over_resets_to_level_0(self):
        """F-10: When all players die, game resets: progress/inventories wiped, reloads level 0."""
        # Dynamically query player 0's start position on level 0
        p0_start_x = self.env.get_player_x(0)
        p0_start_y = self.env.get_player_y(0)
        
        self.helper_setup_clean_map(10, 10)
        # Set up a high progress state
        self.env.current_level = 2
        self.env.load_level(2)
        px = self.env.get_player_x(0)
        py = self.env.get_player_y(0)
        self.env.set_player_health(0, 10)
        self.env.set_player_score(0, 500)
        self.env.set_player_bombs(0, 3)
        self.env.set_player_keys(0, 2)
        
        # Place Monster 1 adjacent to player (rotor index 9, or manually tick it/hit player)
        # Instead of waiting for rotor, we can just trigger contact damage directly by placing monster right there
        # and letting it tick, or we can just set player health to 0 and step.
        # Wait! If we set player health to 0 directly, does step trigger game over?
        # In dandy_step: "bool all_dead = true; ... if (all_dead) { end_game(); }"
        # Yes! If we set health to 0, then the next step (even with no inputs) will trigger game over!
        self.env.set_player_health(0, 0)
        self.env.clear_mock_buffers()
        
        # Action: Step
        self.env.step([0, 0, 0, 0])
        
        # Assert Globals: Wiped and reset to level 0
        self.assertEqual(self.env.current_level, 0)
        self.assertTrue(self.env.is_player_joined(0))
        self.assertEqual(self.env.get_player_health(0), 100)
        self.assertEqual(self.env.get_player_score(0), 0)
        self.assertEqual(self.env.get_player_bombs(0), 0)
        self.assertEqual(self.env.get_player_keys(0), 0)
        
        # Assert HAL
        self.env.draw_viewport(0)
        # Verify coordinates reset dynamically to level 0 portal
        self.assertEqual(self.env.get_player_x(0), p0_start_x)
        self.assertEqual(self.env.get_player_y(0), p0_start_y)
        
        # Assert HAL (Double-Assert)
        cam_x, cam_y = self.env.get_camera()
        expected_cam_x = max(0, min(40, p0_start_x - 10))
        expected_cam_y = max(0, min(20, p0_start_y - 5))
        self.assertEqual(cam_x, expected_cam_x)
        self.assertEqual(cam_y, expected_cam_y)
        self.assertEqual(self.env.get_draw_count(), 200)
        
        self.env.assert_outer_border_walls(self)

    def test_f10_game_over_clears_inventories_multiplayer(self):
        """F-10: Game Over in multiplayer (all joined players die) resets entire game state."""
        self.helper_setup_clean_map(10, 10)
        # Join player 1
        self.env.set_player_position(1, 12, 10)
        self.env.set_player_joined(1, True)
        
        # High stats
        self.env.current_level = 3
        self.env.load_level(3)
        
        self.env.set_player_health(0, 0)  # P0 dead
        self.env.set_player_health(1, 0)  # P1 dead
        
        # Action: Step (triggers game over)
        self.env.step([0, 0, 0, 0])
        
        # Assert Globals: Reset to level 0, player 0 joined/reset, player 1 NOT joined
        self.assertEqual(self.env.current_level, 0)
        self.assertTrue(self.env.is_player_joined(0))
        self.assertEqual(self.env.get_player_health(0), 100)
        self.assertEqual(self.env.get_player_score(0), 0)
        
        self.assertFalse(self.env.is_player_joined(1))
        
        # Assert HAL
        self.env.draw_viewport(0)
        
        # Assert HAL (Double-Assert)
        self.assertEqual(self.env.get_draw_count(), 200)
        p0_start_x = self.env.get_player_x(0)
        p0_start_y = self.env.get_player_y(0)
        cam_x, cam_y = self.env.get_camera()
        expected_cam_x = max(0, min(40, p0_start_x - 10))
        expected_cam_y = max(0, min(20, p0_start_y - 5))
        self.assertEqual(cam_x, expected_cam_x)
        self.assertEqual(cam_y, expected_cam_y)
        
        self.env.assert_outer_border_walls(self)

    def test_f10_manual_level_load(self):
        """F-10: Programmatic load_level loads map, resets coordinates, plays no sound."""
        self.helper_setup_clean_map(10, 10)
        
        # Action: Load level 2
        self.env.load_level(2)
        
        # Assert Globals
        self.assertEqual(self.env.current_level, 0)  # load_level doesn't change current_level, it just loads that level index!
        # Let's verify that current_level is still 0 (wait, is current_level updated by load_level?
        # No, load_level just loads the map. Wait, let's check dandy_core.c:
        # "void dandy_load_level(uint8_t level_idx) { ... }"
        # It does NOT update current_level! The global current_level is only updated in next_level() and end_game()!
        # This is a very important detail!).
        # But player position is reset to level 2 starting portal.
        # Let's check portal location in level 2.
        # Portal in level 2 map is at some location. We can just verify it is loaded.
        self.assertTrue(self.env.get_player_x(0) != 10 or self.env.get_player_y(0) != 10)
        
        # Assert HAL: No warp sound should be played
        self.env.draw_viewport(0)
        sounds = self.env.get_sounds()
        self.assertNotIn(self.env.SOUND_WARP, sounds)
        self.env.assert_outer_border_walls(self)

if __name__ == '__main__':
    unittest.main()
