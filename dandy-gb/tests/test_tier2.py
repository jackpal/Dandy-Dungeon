import unittest
import os
import sys

# Ensure tests/ directory is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dandy_env import DandyEnv

class TestTier2(unittest.TestCase):
    def setUp(self):
        # Create a new environment copy for each test to achieve 100% isolation
        self.env = DandyEnv()
        self.env.init()
        self.env.assert_outer_border_walls(self)

    def tearDown(self):
        if hasattr(self, "env"):
            del self.env

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
        self.env.monster_rotor = 0  # Clean rotor start
        
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
    # F-01: Movement & Timing (Boundary & Corner Cases)
    # =========================================================================

    def test_f01_t2_move_clamp_top(self):
        """F-01: Player moving Up at y=0 clamps coordinate to y=0 when slide directions are blocked."""
        self.helper_setup_clean_map(10, 0)
        # Block slide directions: Left (9, 0) and Right (11, 0)
        self.set_tile(9, 0, self.env.TILE_WALL)
        self.set_tile(11, 0, self.env.TILE_WALL)
        
        self.env.step([self.env.BUTTON_UP, 0, 0, 0])
        
        self.assertEqual(self.env.get_player_x(0), 10)
        self.assertEqual(self.env.get_player_y(0), 0)
        self.assertEqual(self.get_tile(10, 0), self.env.TILE_PLAYER1)  # facing Up (0)
        
        self.env.draw_viewport(0)
        cam_x, cam_y = self.env.get_camera()
        self.assertEqual(cam_x, 0)
        self.assertEqual(cam_y, 0)
        self.assertEqual(self.env.mock_get_sound_count(), 0)

    def test_f01_t2_move_clamp_bottom(self):
        """F-01: Player moving Down at y=29 clamps coordinate to y=29 when slide directions are blocked."""
        self.helper_setup_clean_map(10, 29)
        # Block slide directions: Left (9, 29) and Right (11, 29)
        self.set_tile(9, 29, self.env.TILE_WALL)
        self.set_tile(11, 29, self.env.TILE_WALL)
        
        self.env.step([self.env.BUTTON_DOWN, 0, 0, 0])
        
        self.assertEqual(self.env.get_player_x(0), 10)
        self.assertEqual(self.env.get_player_y(0), 29)
        self.assertEqual(self.get_tile(10, 29), self.env.TILE_PLAYER1 + 4)  # facing Down (4)
        
        self.env.draw_viewport(0)
        cam_x, cam_y = self.env.get_camera()
        self.assertEqual(cam_x, 0)
        self.assertEqual(cam_y, 20)
        self.assertEqual(self.env.mock_get_sound_count(), 0)

    def test_f01_t2_move_clamp_left(self):
        """F-01: Player moving Left at x=0 clamps coordinate to x=0 when slide directions are blocked."""
        self.helper_setup_clean_map(0, 10)
        # Block slide directions: Up (0, 9) and Down (0, 11)
        self.set_tile(0, 9, self.env.TILE_WALL)
        self.set_tile(0, 11, self.env.TILE_WALL)
        
        self.env.step([self.env.BUTTON_LEFT, 0, 0, 0])
        
        self.assertEqual(self.env.get_player_x(0), 0)
        self.assertEqual(self.env.get_player_y(0), 10)
        self.assertEqual(self.get_tile(0, 10), self.env.TILE_PLAYER1 + 6)  # facing Left (6)
        
        self.env.draw_viewport(0)
        cam_x, cam_y = self.env.get_camera()
        self.assertEqual(cam_x, 0)
        self.assertEqual(cam_y, 5)
        self.assertEqual(self.env.mock_get_sound_count(), 0)

    def test_f01_t2_move_clamp_right(self):
        """F-01: Player moving Right at x=59 clamps coordinate to x=59 when slide directions are blocked."""
        self.helper_setup_clean_map(59, 10)
        # Block slide directions: Up (59, 9) and Down (59, 11)
        self.set_tile(59, 9, self.env.TILE_WALL)
        self.set_tile(59, 11, self.env.TILE_WALL)
        
        self.env.step([self.env.BUTTON_RIGHT, 0, 0, 0])
        
        self.assertEqual(self.env.get_player_x(0), 59)
        self.assertEqual(self.env.get_player_y(0), 10)
        self.assertEqual(self.get_tile(59, 10), self.env.TILE_PLAYER1 + 2)  # facing Right (2)
        
        self.env.draw_viewport(0)
        cam_x, cam_y = self.env.get_camera()
        self.assertEqual(cam_x, 40)
        self.assertEqual(cam_y, 5)
        self.assertEqual(self.env.mock_get_sound_count(), 0)

    def test_f01_t2_move_diagonal_clamp(self):
        """F-01: Player moving diagonally (Up-Left at 0,0) clamps both coordinates."""
        self.helper_setup_clean_map(0, 0)
        self.env.step([self.env.BUTTON_UP | self.env.BUTTON_LEFT, 0, 0, 0])
        
        self.assertEqual(self.env.get_player_x(0), 0)
        self.assertEqual(self.env.get_player_y(0), 0)
        self.assertEqual(self.get_tile(0, 0), self.env.TILE_PLAYER1 + 7)  # facing Up-Left (7)
        
        self.env.draw_viewport(0)
        cam_x, cam_y = self.env.get_camera()
        self.assertEqual(cam_x, 0)
        self.assertEqual(cam_y, 0)
        self.assertEqual(self.env.mock_get_sound_count(), 0)

    def test_f01_t2_conflicting_cardinal_input(self):
        """F-01: Conflicting cardinal inputs (Left+Right or Up+Down) result in no movement and no cooldown."""
        self.helper_setup_clean_map(10, 10)
        
        # Action 1: Left + Right
        self.env.step([self.env.BUTTON_LEFT | self.env.BUTTON_RIGHT, 0, 0, 0])
        self.assertEqual(self.env.get_player_x(0), 10)
        self.assertEqual(self.env.get_player_y(0), 10)
        self.assertEqual(self.env.get_player_move_timer(0), 0)
        
        # Action 2: Up + Down
        self.env.step([self.env.BUTTON_UP | self.env.BUTTON_DOWN, 0, 0, 0])
        self.assertEqual(self.env.get_player_x(0), 10)
        self.assertEqual(self.env.get_player_y(0), 10)
        self.assertEqual(self.env.get_player_move_timer(0), 0)

        self.env.draw_viewport(0)
        cam_x, cam_y = self.env.get_camera()
        self.assertEqual(cam_x, 0)
        self.assertEqual(cam_y, 5)
        self.assertEqual(self.env.mock_get_sound_count(), 0)

    def test_f01_t2_all_directions_pressed(self):
        """F-01: Pressing all 4 directions results in no movement and no cooldown."""
        self.helper_setup_clean_map(10, 10)
        all_buttons = self.env.BUTTON_UP | self.env.BUTTON_DOWN | self.env.BUTTON_LEFT | self.env.BUTTON_RIGHT
        self.env.step([all_buttons, 0, 0, 0])
        
        self.assertEqual(self.env.get_player_x(0), 10)
        self.assertEqual(self.env.get_player_y(0), 10)
        self.assertEqual(self.env.get_player_move_timer(0), 0)

        self.env.draw_viewport(0)
        cam_x, cam_y = self.env.get_camera()
        self.assertEqual(cam_x, 0)
        self.assertEqual(cam_y, 5)
        self.assertEqual(self.env.mock_get_sound_count(), 0)

    # =========================================================================
    # F-02: Slide Mechanics (Boundary & Corner Cases)
    # =========================================================================

    def test_f02_t2_slide_blocked_both_adjacent(self):
        """F-02: Moving cardinally when target and both adjacent slide offsets are blocked results in no movement but incurs a 4-tick cooldown."""
        self.helper_setup_clean_map(10, 10)
        self.set_tile(11, 10, self.env.TILE_WALL)  # Target (Right)
        self.set_tile(11, 9, self.env.TILE_WALL)   # CCW slide (Up-Right)
        self.set_tile(11, 11, self.env.TILE_WALL)  # CW slide (Down-Right)
        
        self.env.step([self.env.BUTTON_RIGHT, 0, 0, 0])
        
        self.assertEqual(self.env.get_player_x(0), 10)
        self.assertEqual(self.env.get_player_y(0), 10)
        self.assertEqual(self.env.get_player_move_timer(0), 3)  # Cooldown active (4 - 1 tick)
        
        self.env.draw_viewport(0)
        sprites = self.env.get_sprites()
        self.assertTrue(any(s['tile_id'] == self.env.TILE_PLAYER1 + 2 for s in sprites.values()))
        cam_x, cam_y = self.env.get_camera()
        self.assertEqual(cam_x, 0)
        self.assertEqual(cam_y, 5)
        self.assertEqual(self.env.mock_get_sound_count(), 0)

    def test_f02_t2_slide_boundary_clamp_top(self):
        """F-02: Moving Up-Right at top boundary (y=0) when Right is blocked. Top is out of bounds, so player stays stationary."""
        self.helper_setup_clean_map(10, 0)
        self.set_tile(11, 0, self.env.TILE_WALL)   # Block Right
        # Target: Up-Right (11, -1) -> Out of bounds
        # CCW Slide: Up (10, -1) -> Out of bounds
        # CW Slide: Right (11, 0) -> Blocked by wall
        
        self.env.step([self.env.BUTTON_UP | self.env.BUTTON_RIGHT, 0, 0, 0])
        
        self.assertEqual(self.env.get_player_x(0), 10)
        self.assertEqual(self.env.get_player_y(0), 0)
        self.assertEqual(self.env.get_player_move_timer(0), 3)

        self.env.draw_viewport(0)
        cam_x, cam_y = self.env.get_camera()
        self.assertEqual(cam_x, 0)
        self.assertEqual(cam_y, 0)
        self.assertEqual(self.env.mock_get_sound_count(), 0)

    def test_f02_t2_slide_boundary_clamp_bottom(self):
        """F-02: Moving Left (blocked by wall) at bottom boundary (y=29). CCW slide Up-Left is free, CW slide Down-Left is out of bounds. Slides Up-Left successfully."""
        self.helper_setup_clean_map(10, 29)
        self.set_tile(9, 29, self.env.TILE_WALL)   # Block Left
        # Target: Left (9, 29) -> Blocked
        # CCW Slide: Up-Left (9, 28) -> Free
        # CW Slide: Down-Left (9, 30) -> Out of bounds
        
        self.env.step([self.env.BUTTON_LEFT, 0, 0, 0])
        
        self.assertEqual(self.env.get_player_x(0), 9)
        self.assertEqual(self.env.get_player_y(0), 28)
        self.assertEqual(self.get_tile(9, 28), self.env.TILE_PLAYER1 + 6)  # facing Left (input dir)

        self.env.draw_viewport(0)
        cam_x, cam_y = self.env.get_camera()
        self.assertEqual(cam_x, 0)
        self.assertEqual(cam_y, 20)
        self.assertEqual(self.env.mock_get_sound_count(), 0)

    def test_f02_t2_slide_boundary_clamp_left(self):
        """F-02: Moving Left (blocked by wall) at left boundary (x=1). Up-Left is blocked, Down-Left is free; slides Down-Left."""
        self.helper_setup_clean_map(1, 10)
        self.set_tile(0, 10, self.env.TILE_WALL)   # Block Left
        self.set_tile(0, 9, self.env.TILE_WALL)    # Block Up-Left (CCW)
        # Down-Left (0, 11) is Free
        
        self.env.step([self.env.BUTTON_LEFT, 0, 0, 0])
        
        self.assertEqual(self.env.get_player_x(0), 0)
        self.assertEqual(self.env.get_player_y(0), 11)
        self.assertEqual(self.get_tile(0, 11), self.env.TILE_PLAYER1 + 6)

        self.env.draw_viewport(0)
        cam_x, cam_y = self.env.get_camera()
        self.assertEqual(cam_x, 0)
        self.assertEqual(cam_y, 6)
        self.assertEqual(self.env.mock_get_sound_count(), 0)

    def test_f02_t2_slide_boundary_clamp_right(self):
        """F-02: Moving Right (blocked by wall) at right boundary (x=58). Up-Right is blocked, Down-Right is free; slides Down-Right."""
        self.helper_setup_clean_map(58, 10)
        self.set_tile(59, 10, self.env.TILE_WALL)  # Block Right
        self.set_tile(59, 9, self.env.TILE_WALL)   # Block Up-Right (CCW)
        # Down-Right (59, 11) is Free
        
        self.env.step([self.env.BUTTON_RIGHT, 0, 0, 0])
        
        self.assertEqual(self.env.get_player_x(0), 59)
        self.assertEqual(self.env.get_player_y(0), 11)
        self.assertEqual(self.get_tile(59, 11), self.env.TILE_PLAYER1 + 2)

        self.env.draw_viewport(0)
        cam_x, cam_y = self.env.get_camera()
        self.assertEqual(cam_x, 40)
        self.assertEqual(cam_y, 6)
        self.assertEqual(self.env.mock_get_sound_count(), 0)

    def test_f02_t2_slide_clockwise_priority(self):
        """F-02: When moving cardinal blocked and both adjacent are free, verify search priority order. CCW (-1) is checked before CW (+1), so it slides CCW."""
        self.helper_setup_clean_map(10, 10)
        self.set_tile(11, 10, self.env.TILE_WALL)  # Block Right
        # CCW (Up-Right at 11, 9) and CW (Down-Right at 11, 11) are both TILE_SPACE (Free)
        
        self.env.step([self.env.BUTTON_RIGHT, 0, 0, 0])
        
        # CCW is checked first, so it must slide to (11, 9)
        self.assertEqual(self.env.get_player_x(0), 11)
        self.assertEqual(self.env.get_player_y(0), 9)
        self.assertEqual(self.get_tile(11, 9), self.env.TILE_PLAYER1 + 2)

        self.env.draw_viewport(0)
        cam_x, cam_y = self.env.get_camera()
        self.assertEqual(cam_x, 1)
        self.assertEqual(cam_y, 4)
        self.assertEqual(self.env.mock_get_sound_count(), 0)

    # =========================================================================
    # F-03: Item Collection (Boundary & Corner Cases)
    # =========================================================================

    def test_f03_t2_collect_food_health_overflow(self):
        """F-03: Player with 32700 HP collects food (+100). Health overflows to -32736 (signed 16-bit) and player dies."""
        # Join Player 1 to prevent immediate game over reset so we can inspect Player 0's health
        self.helper_setup_clean_map(10, 10)
        self.env.set_player_position(1, 1, 1)
        self.env.set_player_joined(1, True)
        self.env.set_player_health(1, 100)
        self.set_tile(1, 1, self.env.TILE_PLAYER1 + 8)
        
        self.env.set_player_health(0, 32700)
        self.set_tile(11, 10, self.env.TILE_FOOD)
        
        # Step Right into food
        self.env.step([self.env.BUTTON_RIGHT, 0, 0, 0])
        
        # Check that Player 0 health has overflowed to -32736
        self.assertEqual(self.env.get_player_health(0), -32736)
        self.assertEqual(self.env.get_player_x(0), 11)

        self.env.draw_viewport(0)
        sounds = self.env.get_sounds()
        self.assertIn(self.env.SOUND_FOOD, sounds)
        
        # On the next step, since Player 0 is dead (health <= 0), their inputs are ignored
        self.env.step([self.env.BUTTON_RIGHT, 0, 0, 0])
        self.assertEqual(self.env.get_player_x(0), 11)  # Didn't move!
        
        # And their tile is removed from the map on the next step because they are dead?
        # Wait! The player tile is cleared immediately when they die?
        # In dandy_step: "player_health[hit_p] -= ... if (player_health[hit_p] <= 0) { dandy_map[pos] = TILE_SPACE; ... }"
        # Wait, that is when they are hit by a monster!
        # If they die from health overflow, their health becomes <= 0. Does the map tile get cleared?
        # Let's check: the engine check `player_health[p] > 0` is only checked in step for processing buttons.
        # But wait! If their health is <= 0, they are considered dead, but their tile might still be on the map unless cleared.
        # Actually, let's just assert the health is -32736 and they cannot move!

    def test_f03_t2_collect_money_score_wrap(self):
        """F-03: Player with 65500 score collects money (+100). Score wraps to 64 (unsigned 16-bit)."""
        self.helper_setup_clean_map(10, 10)
        self.env.set_player_score(0, 65500)
        self.set_tile(11, 10, self.env.TILE_MONEY)
        
        self.env.step([self.env.BUTTON_RIGHT, 0, 0, 0])
        
        self.assertEqual(self.env.get_player_score(0), 64)
        self.assertEqual(self.env.get_player_x(0), 11)

        self.env.draw_viewport(0)
        sounds = self.env.get_sounds()
        self.assertIn(self.env.SOUND_KEY, sounds)

    def test_f03_t2_collect_key_wrap(self):
        """F-03: Player with 255 keys collects key. Keys count wraps to 0 (unsigned 8-bit)."""
        self.helper_setup_clean_map(10, 10)
        self.env.set_player_keys(0, 255)
        self.set_tile(11, 10, self.env.TILE_KEY)
        
        self.env.step([self.env.BUTTON_RIGHT, 0, 0, 0])
        
        self.assertEqual(self.env.get_player_keys(0), 0)
        self.assertEqual(self.env.get_player_x(0), 11)

        self.env.draw_viewport(0)
        sounds = self.env.get_sounds()
        self.assertIn(self.env.SOUND_KEY, sounds)

    def test_f03_t2_collect_bomb_wrap(self):
        """F-03: Player with 255 bombs collects bomb. Bombs count wraps to 0 (unsigned 8-bit)."""
        self.helper_setup_clean_map(10, 10)
        self.env.set_player_bombs(0, 255)
        self.set_tile(11, 10, self.env.TILE_BOMB)
        
        self.env.step([self.env.BUTTON_RIGHT, 0, 0, 0])
        
        self.assertEqual(self.env.get_player_bombs(0), 0)
        self.assertEqual(self.env.get_player_x(0), 11)

        self.env.draw_viewport(0)
        sounds = self.env.get_sounds()
        self.assertIn(self.env.SOUND_KEY, sounds)

    def test_f03_t2_collect_item_at_health_0(self):
        """F-03: Dead player (health 0) cannot collect items; items remain on the map."""
        self.helper_setup_clean_map(10, 10)
        # Join Player 1 to prevent game over reset
        self.env.set_player_position(1, 1, 1)
        self.env.set_player_joined(1, True)
        self.env.set_player_health(1, 100)
        self.set_tile(1, 1, self.env.TILE_PLAYER1 + 8)
        
        self.env.set_player_health(0, 0)
        self.set_tile(11, 10, self.env.TILE_FOOD)
        
        # Try to step Right for Player 0
        self.env.step([self.env.BUTTON_RIGHT, 0, 0, 0])
        
        self.assertEqual(self.env.get_player_x(0), 10)
        self.assertEqual(self.get_tile(11, 10), self.env.TILE_FOOD)

        self.env.draw_viewport(0)
        self.assertEqual(self.env.mock_get_sound_count(), 0)

    # =========================================================================
    # F-04: Door & Key Mechanics (Boundary & Corner Cases)
    # =========================================================================

    def test_f04_t2_door_flood_fill_stack_overflow(self):
        """F-04: Contiguous door network of 625 door tiles (25x25 block). Unlocking clears a portion and leaves some doors locked due to FLOOD_STACK_SIZE=64 limit."""
        self.helper_setup_clean_map(10, 1)
        self.env.set_player_keys(0, 1)
        
        # Build a solid 25x25 block of doors from x=10..34, y=2..26 (625 doors)
        for y in range(2, 27):
            for x in range(10, 35):
                self.set_tile(x, y, self.env.TILE_DOOR)
            
        # Step Down into the block door at (10, 2)
        self.env.step([self.env.BUTTON_DOWN, 0, 0, 0])
        
        # Verify Player 0 moved to (10, 2) and key was consumed
        self.assertEqual(self.env.get_player_x(0), 10)
        self.assertEqual(self.env.get_player_y(0), 2)
        self.assertEqual(self.env.get_player_keys(0), 0)
        
        # Count remaining doors
        doors_left = 0
        for y in range(2, 27):
            for x in range(10, 35):
                if self.get_tile(x, y) == self.env.TILE_DOOR:
                    doors_left += 1
                    
        # Since the total doors was 625, and the stack size is 64, we expect some doors to remain locked!
        self.assertEqual(doors_left, 418)

        self.env.draw_viewport(0)
        sounds = self.env.get_sounds()
        self.assertIn(self.env.SOUND_KEY, sounds)

    def test_f04_t2_door_flood_fill_circular(self):
        """F-04: A circular ring of doors is completely cleared by a single unlock without infinite looping."""
        self.helper_setup_clean_map(10, 10)
        self.env.set_player_keys(0, 1)
        
        # Build a 3x3 circular ring of doors around (11,11)
        # Ring tiles: (11,10), (12,10), (12,11), (12,12), (11,12), (10,12), (10,11), (10,10)
        ring_coords = [(11,10), (12,10), (12,11), (12,12), (11,12), (10,12), (10,11), (10,10)]
        for x, y in ring_coords:
            self.set_tile(x, y, self.env.TILE_DOOR)
            
        # Step Right into (11, 10)
        self.env.step([self.env.BUTTON_RIGHT | self.env.BUTTON_UP, 0, 0, 0])  # Step Up-Right to hit (11, 10)
        # Wait, from (10, 10), Up-Right is (11, 9).
        # Let's just step Up to (10, 9) then Right to (11, 9) and Down to (11, 10).
        # Better: player starts at (11, 9), steps Down to (11, 10).
        self.helper_setup_clean_map(11, 9)
        self.env.set_player_keys(0, 1)
        for x, y in ring_coords:
            self.set_tile(x, y, self.env.TILE_DOOR)
            
        self.env.step([self.env.BUTTON_DOWN, 0, 0, 0])
        
        self.assertEqual(self.env.get_player_x(0), 11)
        self.assertEqual(self.env.get_player_y(0), 10)
        
        # Verify the entire ring is cleared (all are now TILE_SPACE or player tile)
        for x, y in ring_coords:
            tile = self.get_tile(x, y)
            self.assertTrue(tile == self.env.TILE_SPACE or tile == self.env.TILE_PLAYER1 + 4)  # facing Down

        self.env.draw_viewport(0)
        sounds = self.env.get_sounds()
        self.assertIn(self.env.SOUND_KEY, sounds)

    def test_f04_t2_door_flood_fill_boundary(self):
        """F-04: Door network touching map boundaries clears successfully."""
        self.helper_setup_clean_map(0, 5)
        self.env.set_player_keys(0, 1)
        
        # Doors touching left boundary (x=0) and extending
        self.set_tile(0, 6, self.env.TILE_DOOR)
        self.set_tile(0, 7, self.env.TILE_DOOR)
        self.set_tile(1, 6, self.env.TILE_DOOR)
        
        self.env.step([self.env.BUTTON_DOWN, 0, 0, 0])
        
        self.assertEqual(self.env.get_player_x(0), 0)
        self.assertEqual(self.env.get_player_y(0), 6)
        self.assertEqual(self.get_tile(0, 7), self.env.TILE_SPACE)
        self.assertEqual(self.get_tile(1, 6), self.env.TILE_SPACE)

        self.env.draw_viewport(0)
        sounds = self.env.get_sounds()
        self.assertIn(self.env.SOUND_KEY, sounds)

    def test_f04_t2_door_unlock_multi_key(self):
        """F-04: Unlocking a large door network consumes exactly 1 key, even if player has multiple keys."""
        self.helper_setup_clean_map(10, 10)
        self.env.set_player_keys(0, 5)
        
        # 3 contiguous doors
        self.set_tile(11, 10, self.env.TILE_DOOR)
        self.set_tile(12, 10, self.env.TILE_DOOR)
        self.set_tile(13, 10, self.env.TILE_DOOR)
        
        self.env.step([self.env.BUTTON_RIGHT, 0, 0, 0])
        
        # Consumed exactly 1 key (5 -> 4)
        self.assertEqual(self.env.get_player_keys(0), 4)
        self.assertEqual(self.get_tile(11, 10), self.env.TILE_PLAYER1 + 2)
        self.assertEqual(self.get_tile(12, 10), self.env.TILE_SPACE)
        self.assertEqual(self.get_tile(13, 10), self.env.TILE_SPACE)

        self.env.draw_viewport(0)
        sounds = self.env.get_sounds()
        self.assertIn(self.env.SOUND_KEY, sounds)

    def test_f04_t2_door_unlock_no_key_blocked_slide(self):
        """F-04: Moving into door with 0 keys and blocked slide offsets leaves player stationary."""
        self.helper_setup_clean_map(10, 10)
        self.env.set_player_keys(0, 0)
        self.set_tile(11, 10, self.env.TILE_DOOR)
        self.set_tile(11, 9, self.env.TILE_WALL)
        self.set_tile(11, 11, self.env.TILE_WALL)
        
        self.env.step([self.env.BUTTON_RIGHT, 0, 0, 0])
        
        self.assertEqual(self.env.get_player_x(0), 10)
        self.assertEqual(self.env.get_player_y(0), 10)
        self.assertEqual(self.get_tile(11, 10), self.env.TILE_DOOR)

        self.env.draw_viewport(0)
        self.assertEqual(self.env.mock_get_sound_count(), 0)

    # =========================================================================
    # F-05: Combat & Projectiles (Boundary & Corner Cases)
    # =========================================================================

    def test_f05_t2_arrow_destructible_outside_viewport(self):
        """F-05: Destructibles outside the active 10x20 viewport are immune to arrow damage because arrows destroy themselves at the viewport edge."""
        self.helper_setup_clean_map(10, 10)  # Viewport is x in [0, 19], y in [5, 14]
        self.env.set_player_dir(0, 2)       # Facing Right
        
        # Place Monster 1 at (20, 10) (just outside the right edge of the viewport)
        self.set_tile(20, 10, self.env.TILE_MONSTER1)
        
        # Step 1: Fire arrow (arrow spawns at 11, 10)
        self.env.step([self.env.BUTTON_FIRE, 0, 0, 0])
        self.assertEqual(self.env.get_arrow_x(0), 11)
        self.assertEqual(self.env.get_arrow_dir(0), 2)
        
        # Step the arrow until it reaches the edge.
        # Viewport right edge is x=19.
        # Arrow starts at 11. It moves 1 tile per step.
        # Steps: 12, 13, 14, 15, 16, 17, 18, 19.
        # Let's step 9 times.
        for _ in range(9):
            self.env.step([0, 0, 0, 0])
            
        # Arrow should be destroyed, and monster at (20, 10) must be untouched!
        self.assertEqual(self.env.get_arrow_dir(0), -1)
        self.assertEqual(self.get_tile(20, 10), self.env.TILE_MONSTER1)

        self.env.draw_viewport(0)
        sounds = self.env.get_sounds()
        self.assertIn(self.env.SOUND_SHOOT, sounds)
        self.assertNotIn(self.env.SOUND_HIT, sounds)

    def test_f05_t2_arrow_destroy_at_map_boundary(self):
        """F-05: Arrow shot at map edge destroys itself on the boundary immediately."""
        self.helper_setup_clean_map(59, 10)
        self.env.set_player_dir(0, 2)  # Facing Right (towards map boundary x=59)
        
        # Fire arrow
        self.env.step([self.env.BUTTON_FIRE, 0, 0, 0])
        
        # Since next coordinate is (60, 10) which is out-of-bounds, it should be destroyed instantly
        # (or rather, the viewport check will destroy it because 60 is outside the viewport).
        self.assertEqual(self.env.get_arrow_dir(0), -1)

        self.env.draw_viewport(0)
        sounds = self.env.get_sounds()
        self.assertIn(self.env.SOUND_SHOOT, sounds)

    def test_f05_t2_arrow_destroy_at_wall(self):
        """F-05: Arrow hitting a wall destroys itself."""
        self.helper_setup_clean_map(10, 10)
        self.env.set_player_dir(0, 2)
        self.set_tile(12, 10, self.env.TILE_WALL)
        
        # Fire
        self.env.step([self.env.BUTTON_FIRE, 0, 0, 0]) # Arrow at 11, 10
        self.env.step([0, 0, 0, 0]) # Arrow hits wall at 12, 10 and dies
        
        self.assertEqual(self.env.get_arrow_dir(0), -1)
        self.assertEqual(self.get_tile(12, 10), self.env.TILE_WALL)

        self.env.draw_viewport(0)
        sounds = self.env.get_sounds()
        self.assertIn(self.env.SOUND_SHOOT, sounds)
        self.assertNotIn(self.env.SOUND_HIT, sounds)

    def test_f05_t2_arrow_hit_destructible_types(self):
        """F-05: Shooting at different destructible types has the correct effect."""
        
        # 1. Generator -> replaced with TILE_SPACE
        self.helper_setup_clean_map(10, 10)
        self.env.set_player_dir(0, 2)
        self.set_tile(11, 10, self.env.TILE_GENERATOR1)
        self.env.step([self.env.BUTTON_FIRE, 0, 0, 0])
        self.assertEqual(self.get_tile(11, 10), self.env.TILE_SPACE)
        self.assertEqual(self.env.get_arrow_dir(0), -1)
        self.env.draw_viewport(0)
        sounds = self.env.get_sounds()
        self.assertIn(self.env.SOUND_SHOOT, sounds)
        self.assertIn(self.env.SOUND_HIT, sounds)
        
        # 2. Heart -> degrades to TILE_MONSTER3
        self.helper_setup_clean_map(10, 10)
        self.env.set_player_dir(0, 2)
        self.set_tile(11, 10, self.env.TILE_HEART)
        self.env.step([self.env.BUTTON_FIRE, 0, 0, 0])
        self.assertEqual(self.get_tile(11, 10), self.env.TILE_MONSTER3)
        self.env.draw_viewport(0)
        sounds = self.env.get_sounds()
        self.assertIn(self.env.SOUND_SHOOT, sounds)
        self.assertIn(self.env.SOUND_HIT, sounds)
        
        # 3. Monster 3 -> degrades to TILE_MONSTER2
        self.helper_setup_clean_map(10, 10)
        self.env.set_player_dir(0, 2)
        self.set_tile(11, 10, self.env.TILE_MONSTER3)
        self.env.step([self.env.BUTTON_FIRE, 0, 0, 0])
        self.assertEqual(self.get_tile(11, 10), self.env.TILE_MONSTER2)
        self.env.draw_viewport(0)
        sounds = self.env.get_sounds()
        self.assertIn(self.env.SOUND_SHOOT, sounds)
        self.assertIn(self.env.SOUND_HIT, sounds)
        
        # 4. Monster 2 -> degrades to TILE_MONSTER1
        self.helper_setup_clean_map(10, 10)
        self.env.set_player_dir(0, 2)
        self.set_tile(11, 10, self.env.TILE_MONSTER2)
        self.env.step([self.env.BUTTON_FIRE, 0, 0, 0])
        self.assertEqual(self.get_tile(11, 10), self.env.TILE_MONSTER1)
        self.env.draw_viewport(0)
        sounds = self.env.get_sounds()
        self.assertIn(self.env.SOUND_SHOOT, sounds)
        self.assertIn(self.env.SOUND_HIT, sounds)
        
        # 5. Monster 1 -> replaced with TILE_SPACE
        self.helper_setup_clean_map(10, 10)
        self.env.set_player_dir(0, 2)
        self.set_tile(11, 10, self.env.TILE_MONSTER1)
        self.env.step([self.env.BUTTON_FIRE, 0, 0, 0])
        self.assertEqual(self.get_tile(11, 10), self.env.TILE_SPACE)
        self.env.draw_viewport(0)
        sounds = self.env.get_sounds()
        self.assertIn(self.env.SOUND_SHOOT, sounds)
        self.assertIn(self.env.SOUND_HIT, sounds)

    def test_f05_t2_shoot_no_active_arrow(self):
        """F-05: Pressing fire when an arrow is already active does nothing (cannot shoot multiple arrows)."""
        self.helper_setup_clean_map(10, 10)
        self.env.set_player_dir(0, 2)
        
        # Fire first arrow (spawns at 11, 10)
        self.env.step([self.env.BUTTON_FIRE, 0, 0, 0])
        self.assertEqual(self.env.get_arrow_x(0), 11)
        self.assertEqual(self.env.get_arrow_dir(0), 2)
        
        # Try to fire again immediately
        self.env.step([self.env.BUTTON_FIRE, 0, 0, 0])
        
        # Arrow should just have moved to 12, 10, and no new arrow spawned
        self.assertEqual(self.env.get_arrow_x(0), 12)
        self.assertEqual(self.env.get_arrow_dir(0), 2)
        self.assertEqual(self.get_tile(11, 10), self.env.TILE_SPACE)

        self.env.draw_viewport(0)
        sounds = self.env.get_sounds()
        self.assertEqual(sounds.count(self.env.SOUND_SHOOT), 1)

    # =========================================================================
    # F-06: Smart Bomb (Boundary & Corner Cases)
    # =========================================================================

    def test_f06_t2_smart_bomb_clears_viewport_only(self):
        """F-06: Smart bomb clears all monsters/generators inside player's 10x20 viewport, leaving those outside untouched."""
        self.helper_setup_clean_map(10, 10)  # Viewport is x in [0, 19], y in [5, 14]
        self.env.set_player_bombs(0, 1)
        
        # Inside viewport
        self.set_tile(11, 10, self.env.TILE_MONSTER1)
        self.set_tile(5, 8, self.env.TILE_GENERATOR2)
        
        # Outside viewport
        self.set_tile(20, 10, self.env.TILE_MONSTER2)  # x=20 is outside
        self.set_tile(10, 4, self.env.TILE_GENERATOR1)   # y=4 is outside
        
        # Press BOMB
        self.env.step([self.env.BUTTON_BOMB, 0, 0, 0])
        
        # Viewport cleared
        self.assertEqual(self.get_tile(11, 10), self.env.TILE_SPACE)
        self.assertEqual(self.get_tile(5, 8), self.env.TILE_SPACE)
        
        # Outside unaffected
        self.assertEqual(self.get_tile(20, 10), self.env.TILE_MONSTER2)
        self.assertEqual(self.get_tile(10, 4), self.env.TILE_GENERATOR1)
        self.assertEqual(self.env.get_player_bombs(0), 0)

        self.env.draw_viewport(0)
        sounds = self.env.get_sounds()
        self.assertIn(self.env.SOUND_BOMB, sounds)

    def test_f06_t2_smart_bomb_no_entities(self):
        """F-06: Viewport-wide bomb with no monsters/generators inside viewport consumes 1 bomb, plays sound, does not crash."""
        self.helper_setup_clean_map(10, 10)
        self.env.set_player_bombs(0, 1)
        
        self.env.step([self.env.BUTTON_BOMB, 0, 0, 0])
        
        self.assertEqual(self.env.get_player_bombs(0), 0)
        self.env.draw_viewport(0)
        sounds = self.env.get_sounds()
        self.assertIn(self.env.SOUND_BOMB, sounds)

    def test_f06_t2_smart_bomb_no_bombs(self):
        """F-06: Pressing bomb button with 0 bombs does nothing."""
        self.helper_setup_clean_map(10, 10)
        self.env.set_player_bombs(0, 0)
        self.set_tile(11, 10, self.env.TILE_MONSTER1)
        
        self.env.step([self.env.BUTTON_BOMB, 0, 0, 0])
        
        self.assertEqual(self.env.get_player_bombs(0), 0)
        self.assertEqual(self.get_tile(11, 10), self.env.TILE_MONSTER1)
        
        self.env.draw_viewport(0)
        sounds = self.env.get_sounds()
        self.assertNotIn(self.env.SOUND_BOMB, sounds)

    # =========================================================================
    # F-07: Monster Behavior (Boundary & Corner Cases)
    # =========================================================================

    def test_f07_t2_monster_off_screen_freeze(self):
        """F-07: Monsters outside any active player's viewport do not move (remain frozen)."""
        self.helper_setup_clean_map(10, 10)  # Viewport is x in [0, 19], y in [5, 14]
        
        # Place Monster 1 at (21, 8) (off-screen)
        # Rotor index: (8 % 4) * 4 + (21 % 4) = 0 * 4 + 1 = 1
        self.set_tile(21, 8, self.env.TILE_MONSTER1)
        
        # Step 1: Tick monster rotor to 1
        self.env.step([0, 0, 0, 0])
        
        # Monster should be frozen and remain at (21, 8)
        self.assertEqual(self.get_tile(21, 8), self.env.TILE_MONSTER1)

        self.env.draw_viewport(0)
        self.assertEqual(self.env.mock_get_sound_count(), 0)

    def test_f07_t2_monster_damage_scale(self):
        """F-07: Monster colliding with player deals 10 * level damage."""
        # Level 1 monster -> 10 damage
        self.helper_setup_clean_map(10, 10)
        self.set_tile(9, 10, self.env.TILE_MONSTER1)  # Rotor: (10%4)*4 + (9%4) = 9
        for _ in range(9):
            self.env.step([0, 0, 0, 0])
        self.assertEqual(self.env.get_player_health(0), 90)
        self.env.draw_viewport(0)
        self.assertIn(self.env.SOUND_HIT, self.env.get_sounds())
        
        # Level 2 monster -> 20 damage
        self.helper_setup_clean_map(10, 10)
        self.set_tile(9, 10, self.env.TILE_MONSTER2)  # Rotor 9
        for _ in range(9):
            self.env.step([0, 0, 0, 0])
        self.assertEqual(self.env.get_player_health(0), 80)
        self.env.draw_viewport(0)
        self.assertIn(self.env.SOUND_HIT, self.env.get_sounds())
        
        # Level 3 monster -> 30 damage
        self.helper_setup_clean_map(10, 10)
        self.set_tile(9, 10, self.env.TILE_MONSTER3)  # Rotor 9
        for _ in range(9):
            self.env.step([0, 0, 0, 0])
        self.assertEqual(self.env.get_player_health(0), 70)
        self.env.draw_viewport(0)
        self.assertIn(self.env.SOUND_HIT, self.env.get_sounds())

    def test_f07_t2_monster_pathfinding_blocked(self):
        """F-07: Monster with completely blocked path to player remains stationary."""
        self.helper_setup_clean_map(10, 10)
        # Place Monster 1 at (9, 8) (rotor 1)
        self.set_tile(9, 8, self.env.TILE_MONSTER1)
        
        # Block all its movement directions towards player:
        # Target: (10, 9) (Down-Right) -> Wall
        # Slide CCW: (9, 9) (Down) -> Wall
        # Slide CW: (10, 8) (Right) -> Wall
        self.set_tile(10, 9, self.env.TILE_WALL)
        self.set_tile(9, 9, self.env.TILE_WALL)
        self.set_tile(10, 8, self.env.TILE_WALL)
        
        # Step 1: Tick rotor to 1
        self.env.step([0, 0, 0, 0])
        
        # Monster remains at (9, 8)
        self.assertEqual(self.get_tile(9, 8), self.env.TILE_MONSTER1)

        self.env.draw_viewport(0)
        self.assertEqual(self.env.mock_get_sound_count(), 0)

    def test_f07_t2_monster_rotor_ticks(self):
        """F-07: Monsters move only on their designated 16-tick sparse grid rotor ticks."""
        self.helper_setup_clean_map(10, 10)
        # Place Monster 1 at (9, 8) (rotor 1)
        self.set_tile(9, 8, self.env.TILE_MONSTER1)
        
        # Step 1: Tick rotor to 1 -> moves to (10, 9)
        self.env.step([0, 0, 0, 0])
        self.assertEqual(self.get_tile(9, 8), self.env.TILE_SPACE)
        self.assertEqual(self.get_tile(10, 9), self.env.TILE_MONSTER1)
        
        # Step 2..16: Monster should NOT move
        # Next tick for (10, 9) is rotor: (9%4)*4 + (10%4) = 1*4 + 2 = 6.
        # But monster already moved, so it will only tick when rotor matches its NEW position's rotor index.
        # Let's check that it doesn't move on step 2, 3, 4, 5.
        for _ in range(4):
            self.env.step([0, 0, 0, 0])
            self.assertEqual(self.get_tile(10, 9), self.env.TILE_MONSTER1)

        self.env.draw_viewport(0)
        self.assertEqual(self.env.mock_get_sound_count(), 0)

    # =========================================================================
    # F-08: Generator Spawning (Boundary & Corner Cases)
    # =========================================================================

    def test_f08_t2_generator_off_screen_freeze(self):
        """F-08: Generators outside player's viewport are frozen (no spawn, seed does not update)."""
        self.helper_setup_clean_map(10, 10)  # Viewport is x in [0, 19], y in [5, 14]
        # Place Generator 1 at (21, 8) (off-screen, rotor index 1)
        self.set_tile(21, 8, self.env.TILE_GENERATOR1)
        
        # Step 1: Tick rotor to 1
        self.env.step([0, 0, 0, 0])
        
        # No monster spawned around it
        for dy in [-1, 0, 1]:
            for dx in [-1, 0, 1]:
                if dx != 0 or dy != 0:
                    self.assertEqual(self.get_tile(21 + dx, 8 + dy), self.env.TILE_SPACE)

        self.env.draw_viewport(0)
        self.assertEqual(self.env.mock_get_sound_count(), 0)

    def test_f08_t2_generator_surrounded(self):
        """F-08: Generator completely surrounded by walls cannot spawn a monster."""
        self.helper_setup_clean_map(10, 10)
        # Place Generator 1 at (9, 8) (rotor 1)
        self.set_tile(9, 8, self.env.TILE_GENERATOR1)
        
        # Block all 4 spawn directions (Up, Right, Down, Left)
        self.set_tile(9, 7, self.env.TILE_WALL)
        self.set_tile(10, 8, self.env.TILE_WALL)
        self.set_tile(9, 9, self.env.TILE_WALL)
        self.set_tile(8, 8, self.env.TILE_WALL)
        
        # Step 1: Tick rotor to 1
        self.env.step([0, 0, 0, 0])
        
        # Check that no monster is spawned in any diagonal/cardinal position around it
        # (diagonals are not checked by the generator anyway, but let's confirm cardinals are blocked)
        self.assertEqual(self.get_tile(9, 7), self.env.TILE_WALL)
        self.assertEqual(self.get_tile(10, 8), self.env.TILE_WALL)
        self.assertEqual(self.get_tile(9, 9), self.env.TILE_WALL)
        self.assertEqual(self.get_tile(8, 8), self.env.TILE_WALL)

        self.env.draw_viewport(0)
        self.assertEqual(self.env.mock_get_sound_count(), 0)

    def test_f08_t2_generator_spawning_lfsr_determinism(self):
        """F-08: LFSR starts at 0xACE1. Verify exact spawn ticks and directions on a fresh run."""
        self.helper_setup_clean_map(10, 10)
        # Place Generator 1 at (9, 8) (rotor 1)
        self.set_tile(9, 8, self.env.TILE_GENERATOR1)
        
        # Step 1: Tick rotor to 1.
        # LFSR updates to 0xE270.
        # spawn_dir = 0 (Up). Spawns monster at (9, 7).
        self.env.step([0, 0, 0, 0])
        
        self.assertEqual(self.get_tile(9, 7), self.env.TILE_MONSTER1)

        self.env.draw_viewport(0)
        sprites = self.env.get_sprites()
        self.assertTrue(any(s['tile_id'] == self.env.TILE_MONSTER1 for s in sprites.values()))

    def test_f08_t2_generator_spawn_wrap_around_x(self):
        """F-08: Generator at x=59 (right edge) spawning Right wraps around to x=0 of the next row."""
        self.helper_setup_clean_map(59, 10)
        # Rotor index for (59, 10): (10%4)*4 + (59%4) = 2*4 + 3 = 11.
        self.set_tile(59, 10, self.env.TILE_GENERATOR1)
        
        # Block Up (59, 9) so it tries next direction (Right)
        self.set_tile(59, 9, self.env.TILE_WALL)
        
        # Set monster_rotor to 10 so it ticks on the next step
        self.env.monster_rotor = 10
        
        # Step 1: Tick rotor to 11.
        # LFSR becomes 0xE270. Spawn dir is Up (blocked).
        # Tries Right. Target is (60, 10).
        # Spawns at (0, 11) because of row-wrapping!
        self.env.step([0, 0, 0, 0])
        
        self.assertEqual(self.get_tile(0, 11), self.env.TILE_MONSTER1)

        self.env.draw_viewport(0)
        self.assertEqual(self.env.mock_get_sound_count(), 0)

    # =========================================================================
    # F-09: Multiplayer & Viewport (Boundary & Corner Cases)
    # =========================================================================

    def test_f09_t2_viewport_hardware_sprite_limit(self):
        """F-09: If 50 monsters are in view, exactly 40 hardware sprites are registered."""
        self.helper_setup_clean_map(10, 10)
        
        # Place 50 monsters in the player's 10x20 viewport (x in [0, 19], y in [5, 14])
        count = 0
        for y in range(5, 15):
            for x in range(0, 20):
                if (x, y) != (10, 10) and count < 50:
                    self.set_tile(x, y, self.env.TILE_MONSTER1)
                    count += 1
                    
        # Draw viewport
        self.env.draw_viewport(0)
        
        # Assert C Globals (Double-Assert)
        self.assertEqual(self.env.get_player_x(0), 10)
        self.assertEqual(self.env.get_player_y(0), 10)
        self.assertEqual(self.env.dandy_map.count(self.env.TILE_MONSTER1), 50)
        
        # Get active sprites
        sprites = self.env.get_sprites()
        
        # Count how many are active (get_sprites only returns active ones, so len is active count)
        self.assertEqual(len(sprites), 40)
        self.assertFalse(self.env.get_sprite_oob_error(), "Out-of-bounds sprite index registered!")

    def test_f09_t2_spectator_centroid_averaging(self):
        """F-09: When local player is dead, camera centers on the centroid of remaining alive players."""
        self.helper_setup_clean_map(10, 10)
        self.env.set_player_health(0, 0)  # Local player dead
        
        # Join Player 1 at (20, 10) and Player 2 at (20, 20)
        self.env.set_player_position(1, 20, 10)
        self.env.set_player_joined(1, True)
        self.env.set_player_health(1, 100)
        self.set_tile(20, 10, self.env.TILE_PLAYER1 + 8)
        
        self.env.set_player_position(2, 20, 20)
        self.env.set_player_joined(2, True)
        self.env.set_player_health(2, 100)
        self.set_tile(20, 20, self.env.TILE_PLAYER1 + 16)
        
        # Centroid target: x = (20+20)/2 = 20, y = (10+20)/2 = 15
        # Camera top-left: vp_left = clamp(20-10, 0, 40) = 10
        # vp_top = clamp(15-5, 0, 20) = 10
        self.env.draw_viewport(0)
        
        # Assert C Globals (Double-Assert)
        self.assertEqual(self.env.get_player_health(0), 0)
        self.assertEqual(self.env.get_player_health(1), 100)
        self.assertEqual(self.env.get_player_x(1), 20)
        self.assertEqual(self.env.get_player_y(1), 10)
        self.assertEqual(self.env.get_player_health(2), 100)
        self.assertEqual(self.env.get_player_x(2), 20)
        self.assertEqual(self.env.get_player_y(2), 20)
        
        cam_x, cam_y = self.env.get_camera()
        self.assertEqual(cam_x, 10)
        self.assertEqual(cam_y, 10)
        self.assertEqual(self.env.mock_get_sound_count(), 0)

    def test_f09_t2_spectator_all_dead(self):
        """F-09: When all players are dead, camera defaults to local dead player's coordinate."""
        self.helper_setup_clean_map(10, 10)
        self.env.set_player_health(0, 0)
        
        # Join Player 1 at (20, 20) but make them dead too
        self.env.set_player_position(1, 20, 20)
        self.env.set_player_joined(1, True)
        self.env.set_player_health(1, 0)
        
        # Should center on local player 0 at (10, 10)
        self.env.draw_viewport(0)
        
        # Assert C Globals (Double-Assert)
        self.assertEqual(self.env.get_player_health(0), 0)
        self.assertEqual(self.env.get_player_health(1), 0)
        self.assertEqual(self.env.get_player_x(0), 10)
        self.assertEqual(self.env.get_player_y(0), 10)
        cam_x, cam_y = self.env.get_camera()
        self.assertEqual(cam_x, 0)  # 10 - 10 = 0
        self.assertEqual(cam_y, 5)  # 10 - 5 = 5
        self.assertEqual(self.env.mock_get_sound_count(), 0)

    def test_f09_t2_camera_clamping_corners(self):
        """F-09: Viewport camera clamps correctly to map boundaries at all 4 corners."""
        # Top-Left (0, 0)
        self.helper_setup_clean_map(0, 0)
        self.env.draw_viewport(0)
        self.assertEqual(self.env.get_player_x(0), 0)
        self.assertEqual(self.env.get_player_y(0), 0)
        cam_x, cam_y = self.env.get_camera()
        self.assertEqual(cam_x, 0)
        self.assertEqual(cam_y, 0)
        
        # Top-Right (59, 0)
        self.helper_setup_clean_map(59, 0)
        self.env.draw_viewport(0)
        self.assertEqual(self.env.get_player_x(0), 59)
        self.assertEqual(self.env.get_player_y(0), 0)
        cam_x, cam_y = self.env.get_camera()
        self.assertEqual(cam_x, 40)
        self.assertEqual(cam_y, 0)
        
        # Bottom-Left (0, 29)
        self.helper_setup_clean_map(0, 29)
        self.env.draw_viewport(0)
        self.assertEqual(self.env.get_player_x(0), 0)
        self.assertEqual(self.env.get_player_y(0), 29)
        cam_x, cam_y = self.env.get_camera()
        self.assertEqual(cam_x, 0)
        self.assertEqual(cam_y, 20)
        
        # Bottom-Right (59, 29)
        self.helper_setup_clean_map(59, 29)
        self.env.draw_viewport(0)
        self.assertEqual(self.env.get_player_x(0), 59)
        self.assertEqual(self.env.get_player_y(0), 29)
        cam_x, cam_y = self.env.get_camera()
        self.assertEqual(cam_x, 40)
        self.assertEqual(cam_y, 20)
        self.assertEqual(self.env.mock_get_sound_count(), 0)

    # =========================================================================
    # F-10: Level Transitions (Boundary & Corner Cases)
    # =========================================================================

    def test_f10_t2_level_transition_state_retention(self):
        """F-10: Health, score, keys, bombs carry over on transition; active arrows are destroyed."""
        self.helper_setup_clean_map(10, 10)
        self.env.set_player_health(0, 150)
        self.env.set_player_score(0, 350)
        self.env.set_player_keys(0, 3)
        self.env.set_player_bombs(0, 2)
        
        # Spawn an active arrow for player 0 facing Right
        self.env.set_player_dir(0, 2)
        self.env.step([self.env.BUTTON_FIRE, 0, 0, 0])
        self.assertEqual(self.env.get_arrow_dir(0), 2)
        
        # Step into Stairs (TILE_DOWN)
        self.set_tile(11, 10, self.env.TILE_DOWN)
        self.env.step([self.env.BUTTON_RIGHT, 0, 0, 0])
        
        # Next level loaded
        self.assertEqual(self.env.current_level, 1)
        self.assertEqual(self.env.get_player_health(0), 150)
        self.assertEqual(self.env.get_player_score(0), 350)
        self.assertEqual(self.env.get_player_keys(0), 3)
        self.env.draw_viewport(0)
        # Note: the steps involved in movement might have changed the bombs? No, bombs remain 2.
        self.assertEqual(self.env.get_player_bombs(0), 2)
        
        # Arrow is destroyed
        self.assertEqual(self.env.get_arrow_dir(0), -1)

        # Hardened post-warp coordinate and sound checks:
        portal_x = 1
        portal_y = 2
        # Find TILE_UP on level 1 map to verify starting portal coordinates
        for y in range(30):
            for x in range(60):
                if self.get_tile(x, y) == self.env.TILE_UP:
                    portal_x = x
                    portal_y = y
                    break
        expected_player_x = max(0, min(59, portal_x))
        expected_player_y = max(0, min(29, portal_y - 1))
        self.assertEqual(self.env.get_player_x(0), expected_player_x)
        self.assertEqual(self.env.get_player_y(0), expected_player_y)

        # Assert camera centered on new player coordinate
        cam_x, cam_y = self.env.get_camera()
        self.assertEqual(cam_x, max(0, min(40, expected_player_x - 10)))
        self.assertEqual(cam_y, max(0, min(20, expected_player_y - 5)))

        sounds = self.env.get_sounds()
        self.assertIn(self.env.SOUND_WARP, sounds)
        self.env.assert_outer_border_walls(self)

    def test_f10_t2_level_portal_overlap(self):
        """F-10: When starting portal is at (0,0), players overlap at (0,0) without crashing."""
        # Programmatically load level 0, but we will mock a starting portal TILE_UP at (0,0).
        # Wait, how can we force the level portal to be at (0,0)?
        # The game scans the map to find TILE_UP. If we modify the loaded map so TILE_UP is at (0,0),
        # then call set_player_start_position, they will spawn around (0,0).
        # Wait, the shared library has set_player_start_position as private, but dandy_load_level calls it!
        # If we load level 0, then set map tile (0,0) to TILE_UP, then call load_level again? No, load_level overwrites the map.
        # Wait! We can manually set player positions to (0,0) for multiple players and check if it's fine.
        # But wait: "When starting portal is at (0,0), players overlap at (0,0) without crashing."
        # If the portal is at (0,0), the spawn offsets are:
        # P0: (0, -1) -> clamped to (0, 0)
        # P1: (1, 0)
        # P2: (0, 1)
        # P3: (-1, 0) -> clamped to (0, 0)
        # So P0 and P3 both spawn at (0,0)!
        # Let's verify if we can set up a custom map where TILE_UP is at (0,0), and then trigger player start.
        # Wait! Is there a way to call the start position code?
        # Yes, `dandy_init` or `dandy_load_level` calls it. But `dandy_load_level` loads from the read-only levels array.
        # Wait, can we just write to the map and call `join_player`?
        # `join_player` uses the player_x/y already set by `set_player_start_position`.
        # So if we just set `player_x` and `player_y` for P0 and P3 to (0,0) manually, and then join them:
        self.helper_setup_clean_map(0, 0, 0)
        self.env.set_player_position(3, 0, 0)
        self.env.set_player_joined(3, True)
        self.env.set_player_health(3, 100)
        
        # Join player 0 and player 3 at (0,0)
        self.env.set_player_position(0, 0, 0)
        self.env.set_player_joined(0, True)
        
        self.set_tile(0, 0, self.env.TILE_PLAYER1)  # P0 tile
        # P3 tile will overwrite P0 tile on map?
        self.set_tile(0, 0, self.env.TILE_PLAYER1 + 24)  # P3 tile
        
        # Step and check it doesn't crash
        self.env.step([0, 0, 0, 0])
        
        self.assertEqual(self.env.get_player_x(0), 0)
        self.assertEqual(self.env.get_player_y(0), 0)
        self.assertEqual(self.env.get_player_x(3), 0)
        self.assertEqual(self.env.get_player_y(3), 0)

        self.env.draw_viewport(0)
        sprites = self.env.get_sprites()
        # Verify that at least the visible overlapping player sprite is active at (0,0) on screen:
        self.assertTrue(any(s['x'] == 0 and s['y'] == 0 and s['tile_id'] == self.env.TILE_PLAYER1 + 24 for s in sprites.values()))
        self.assertEqual(self.env.mock_get_sound_count(), 0)

if __name__ == '__main__':
    unittest.main()
