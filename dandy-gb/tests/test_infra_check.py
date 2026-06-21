import unittest
import os
import sys

# Ensure tests/ directory is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dandy_env import DandyEnv

class TestInfraCheck(unittest.TestCase):
    def tearDown(self):
        if hasattr(self, "env"):
            del self.env

    def test_env_loading_and_globals(self):
        """Verify that DandyEnv can be loaded, initialized, and that globals are bound."""
        with DandyEnv() as env:
            env.init()
            
            # Verify initial level is 0
            self.assertEqual(env.current_level, 0)
            
            # Verify player 0 is joined and has 100 health initially
            self.assertTrue(env.is_player_joined(0))
            self.assertEqual(env.get_player_health(0), 100)
            self.assertEqual(env.get_player_score(0), 0)
            self.assertEqual(env.get_player_bombs(0), 0)
            self.assertEqual(env.get_player_keys(0), 0)

            # Verify writing/reading simple globals
            env.current_level = 3
            self.assertEqual(env.current_level, 3)
            
            env.is_dirty = True
            self.assertTrue(env.is_dirty)
            env.is_dirty = False
            self.assertFalse(env.is_dirty)

    def test_state_isolation(self):
        """Verify that multiple DandyEnv instances have 100% isolated static states (Copy-on-Load)."""
        with DandyEnv() as env1, DandyEnv() as env2:
            env1.init()
            env2.init()
            
            # Set distinct level on env1
            env1.current_level = 4
            self.assertEqual(env1.current_level, 4)
            self.assertEqual(env2.current_level, 0) # env2 should be completely isolated
            
            # Modify a player stat on env1
            env1.set_player_health(0, 456)
            self.assertEqual(env1.get_player_health(0), 456)
            self.assertEqual(env2.get_player_health(0), 100) # env2 should not be affected
            
            # Close env1, ensure env2 is still fully functional and unaffected
            env1.close()
            self.assertEqual(env2.current_level, 0)
            self.assertEqual(env2.get_player_health(0), 100)
            
            # env2 should still step correctly
            env2.step([0, 0, 0, 0])

    def test_mock_hal_logging_viewport(self):
        """Verify that drawing the viewport logs tile updates and camera positions in the mock HAL."""
        with DandyEnv() as env:
            env.init()
            
            # Clear mock buffers
            env.clear_mock_buffers()
            self.assertEqual(env.get_draw_count(), 0)
            
            # Draw viewport for player 0
            env.draw_viewport(0)
            
            # Viewport size is 20x10, so it should record exactly 200 draw tile calls
            draw_count = env.get_draw_count()
            self.assertEqual(draw_count, 200)
            
            # Verify we can retrieve the draw calls
            draws = env.get_draws()
            self.assertEqual(len(draws), 200)
            for draw in draws:
                self.assertIn('x', draw)
                self.assertIn('y', draw)
                self.assertIn('tile_id', draw)
                
            # Verify camera position was recorded
            cam_x, cam_y = env.get_camera()
            # Viewport camera is centered around player 0, clamped to map boundaries (60x30).
            # We can just verify it is within valid range.
            self.assertTrue(0 <= cam_x <= 40)
            self.assertTrue(0 <= cam_y <= 20)

    def test_game_loop_step_and_sound(self):
        """Verify engine step, global variable updates, and mock HAL sound recording (E2E style)."""
        with DandyEnv() as env:
            env.init()
            
            # Set up a controlled custom map: all space (0)
            custom_map = [env.TILE_SPACE] * env.MAP_SIZE
            
            # Place player 0 at (10, 10)
            player_x = 10
            player_y = 10
            custom_map[player_y * 60 + player_x] = env.TILE_PLAYER1 # Player 0 facing Up (default)
            
            # Place a food tile at (11, 10) - right of player
            food_x = 11
            food_y = 10
            custom_map[food_y * 60 + food_x] = env.TILE_FOOD
            
            # Load the custom map
            env.dandy_map = custom_map
            
            # Position player 0 at (10, 10), joined, health 100, move timer 0
            env.set_player_position(0, player_x, player_y)
            env.set_player_joined(0, True)
            env.set_player_health(0, 100)
            env.set_player_move_timer(0, 0)
            
            # Clear mock buffers
            env.clear_mock_buffers()
            self.assertEqual(len(env.get_sounds()), 0)
            
            # Step the game: Player 0 presses BUTTON_RIGHT
            # Inputs is a list of size 4: [player0_input, player1_input, player2_input, player3_input]
            env.step([env.BUTTON_RIGHT, 0, 0, 0])
            
            # Verify player 0 moved to (11, 10)
            self.assertEqual(env.get_player_x(0), food_x)
            self.assertEqual(env.get_player_y(0), food_y)
            
            # Verify player health increased by 100 (total 200)
            self.assertEqual(env.get_player_health(0), 200)
            
            # Verify the map was updated: (10, 10) is space, (11, 10) is player facing right (direction 2)
            # Player 0 tile facing direction d is: TILE_PLAYER1 + d
            # Facing right is direction 2
            expected_player_tile = env.TILE_PLAYER1 + 2
            self.assertEqual(env.dandy_map[player_y * 60 + player_x], env.TILE_SPACE)
            self.assertEqual(env.dandy_map[food_y * 60 + food_x], expected_player_tile)
            
            # Verify mock HAL recorded the SOUND_FOOD effect (ID: 2)
            sounds = env.get_sounds()
            self.assertIn(env.SOUND_FOOD, sounds)

if __name__ == '__main__':
    unittest.main()
