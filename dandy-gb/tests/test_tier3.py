import unittest
import os
import sys

# Ensure tests/ directory is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dandy_env import DandyEnv

class TestTier3(unittest.TestCase):
    def setUp(self):
        # Create a new environment copy for each test to achieve 100% isolation
        self.env = DandyEnv()
        self.env.init()

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
    # Tier 3: Cross-Feature Interactions
    # =========================================================================

    def test_f03_f07_t3_combat_and_food(self):
        """Tier 3: Player collects food (+100 HP) and is hit by a Monster (-10 HP) in the same tick. Net health should be 190 HP."""
        self.helper_setup_clean_map(10, 10)
        self.set_tile(11, 10, self.env.TILE_FOOD)
        
        # Place Monster 1 at (12, 10). Rotor index: (10%4)*4 + (12%4) = 2*4 + 0 = 8.
        self.set_tile(12, 10, self.env.TILE_MONSTER1)
        
        # Set monster_rotor to 7 so it increments to 8 and ticks on the next step
        self.env.monster_rotor = 7
        
        # Action: Step Right (into food)
        self.env.step([self.env.BUTTON_RIGHT, 0, 0, 0])
        
        # Assert Globals:
        # Player moves to (11, 10), collects food (+100 HP -> 200 HP).
        # Then Monster 1 ticks, targets player at (11, 10), moves there, collides and deals 10 damage -> 190 HP.
        # Monster is destroyed.
        self.assertEqual(self.env.get_player_health(0), 190)
        self.assertEqual(self.env.get_player_x(0), 11)
        self.assertEqual(self.get_tile(11, 10), self.env.TILE_PLAYER1 + 2)  # Player tile remains
        self.assertEqual(self.get_tile(12, 10), self.env.TILE_SPACE)
        
        # Assert HAL: Both FOOD and HIT sounds played
        self.env.draw_viewport(0)
        sounds = self.env.get_sounds()
        self.assertIn(self.env.SOUND_FOOD, sounds)
        self.assertIn(self.env.SOUND_HIT, sounds)

    def test_f05_f06_t3_arrow_hits_bomb_tile(self):
        """Tier 3: Shooting an arrow at a bomb tile triggers a smart bomb viewport clear in the same tick."""
        self.helper_setup_clean_map(10, 10)
        self.env.set_player_dir(0, 2)  # Facing Right
        
        self.set_tile(11, 10, self.env.TILE_BOMB)
        self.set_tile(12, 10, self.env.TILE_MONSTER1)  # Monster in viewport
        
        # Action: Fire arrow
        self.env.step([self.env.BUTTON_FIRE, 0, 0, 0])
        
        # Assert Globals:
        # Arrow spawns, steps to (11, 10), hits bomb, triggers do_bomb, clears monster at (12, 10).
        # Arrow dies. Bomb tile is cleared.
        self.assertEqual(self.env.get_arrow_dir(0), -1)
        self.assertEqual(self.get_tile(11, 10), self.env.TILE_SPACE)
        self.assertEqual(self.get_tile(12, 10), self.env.TILE_SPACE)
        self.assertEqual(self.env.get_player_bombs(0), 0)  # Inventory bomb not consumed
        
        # Assert HAL: SOUND_SHOOT and SOUND_HIT played
        self.env.draw_viewport(0)
        sounds = self.env.get_sounds()
        self.assertIn(self.env.SOUND_SHOOT, sounds)
        self.assertIn(self.env.SOUND_HIT, sounds)

    def test_f01_f05_t3_shoot_while_moving_cardinal(self):
        """Tier 3: Firing and moving in the same cardinal direction on the same tick causes the arrow (starting at player's old coordinate) to step into player's new coordinate, causing self-collision and self-destruction."""
        self.helper_setup_clean_map(10, 10)
        self.env.set_player_dir(0, 2)  # Facing Right
        
        # Action: Fire and move Right
        self.env.step([self.env.BUTTON_RIGHT | self.env.BUTTON_FIRE, 0, 0, 0])
        
        # Assert Globals:
        # 1. Fire: Arrow created at (10, 10) facing Right.
        # 2. Move: Player moves to (11, 10).
        # 3. Arrow Step: Arrow steps to (11, 10), collides with player, and is destroyed.
        self.assertEqual(self.env.get_player_x(0), 11)
        self.assertEqual(self.env.get_arrow_dir(0), -1)  # Destroyed
        self.assertEqual(self.get_tile(11, 10), self.env.TILE_PLAYER1 + 2)
        
        # Player should be unharmed
        self.assertEqual(self.env.get_player_health(0), 100)
        
        # Assert HAL
        self.env.draw_viewport(0)
        sounds = self.env.get_sounds()
        self.assertIn(self.env.SOUND_SHOOT, sounds)
        self.assertNotIn(self.env.SOUND_HIT, sounds)  # No hit sound on player self-collision

    def test_f01_f05_t3_shoot_while_moving_perpendicular(self):
        """Tier 3: Firing Up while moving Right on the same tick; arrow and player move independently and do not collide."""
        self.helper_setup_clean_map(10, 10)
        self.env.set_player_dir(0, 0)  # Facing Up initially
        
        # Action: Fire and move Right
        self.env.step([self.env.BUTTON_RIGHT | self.env.BUTTON_FIRE, 0, 0, 0])
        
        # Assert Globals:
        # 1. Fire: Arrow created at (10, 10) facing Up (player's pre-move direction).
        # 2. Move: Player turns Right and moves to (11, 10).
        # 3. Arrow Step: Arrow steps to (10, 9) (Up).
        # No collision!
        self.assertEqual(self.env.get_player_x(0), 11)
        self.assertEqual(self.env.get_player_y(0), 10)
        self.assertEqual(self.env.get_player_dir(0), 2)  # Facing Right now
        
        self.assertEqual(self.env.get_arrow_x(0), 10)
        self.assertEqual(self.env.get_arrow_y(0), 9)
        self.assertEqual(self.env.get_arrow_dir(0), 0)  # Still active facing Up
        
        self.assertEqual(self.get_tile(11, 10), self.env.TILE_PLAYER1 + 2)
        self.assertEqual(self.get_tile(10, 9), self.env.TILE_ARROW + 3)  # Arrow facing Up
        
        # Assert HAL
        self.env.draw_viewport(0)
        sounds = self.env.get_sounds()
        self.assertIn(self.env.SOUND_SHOOT, sounds)

    def test_f04_f07_t3_monster_follows_through_open_door(self):
        """Tier 3: A monster tracks and moves through a door tile that the player unlocked in a previous tick."""
        self.helper_setup_clean_map(10, 10)
        self.env.set_player_keys(0, 1)
        
        self.set_tile(11, 10, self.env.TILE_DOOR)
        # Place Monster 1 at (12, 10). Rotor index: 8.
        self.set_tile(12, 10, self.env.TILE_MONSTER1)
        
        # Step 1: Player steps Right, unlocking door and moving to (11, 10)
        self.env.step([self.env.BUTTON_RIGHT, 0, 0, 0])
        self.assertEqual(self.env.get_player_x(0), 11)
        self.assertEqual(self.get_tile(11, 10), self.env.TILE_PLAYER1 + 2)
        
        # Step 2..4: Wait out player move cooldown (3 steps)
        for _ in range(3):
            self.env.step([0, 0, 0, 0])
            
        # Step 5: Player steps Left back to (10, 10)
        self.env.step([self.env.BUTTON_LEFT, 0, 0, 0])
        self.assertEqual(self.env.get_player_x(0), 10)
        self.assertEqual(self.get_tile(11, 10), self.env.TILE_SPACE)  # Door is now space!
        
        # Set monster rotor to 7 so it ticks on the next step
        self.env.monster_rotor = 7
        
        # Clear mock buffers before the final step to isolate sounds/spatials for the monster's move
        self.env.clear_mock_buffers()

        # Step 6: Step empty. Monster ticks (rotor 8), pathfinds to player at (10, 10), and moves through the now-open door at (11, 10).
        self.env.step([0, 0, 0, 0])
        
        self.assertEqual(self.get_tile(11, 10), self.env.TILE_MONSTER1)
        self.assertEqual(self.get_tile(12, 10), self.env.TILE_SPACE)

        self.env.draw_viewport(0)
        sprites = self.env.get_sprites()
        self.assertTrue(any(s['tile_id'] == self.env.TILE_MONSTER1 and s['x'] == 88 and s['y'] == 40 for s in sprites.values()))
        self.assertEqual(self.env.mock_get_sound_count(), 0)

    def test_f03_f04_t3_key_pickup_and_unlock(self):
        """Tier 3: Player walks onto a key and immediately unlocks a door in a single motion (two consecutive steps)."""
        self.helper_setup_clean_map(10, 10)
        self.env.set_player_keys(0, 0)
        
        self.set_tile(11, 10, self.env.TILE_KEY)
        self.set_tile(12, 10, self.env.TILE_DOOR)
        # Block diagonal slides around the door
        self.set_tile(12, 9, self.env.TILE_WALL)
        self.set_tile(12, 11, self.env.TILE_WALL)
        
        # Step 1: Move Right onto key
        self.env.step([self.env.BUTTON_RIGHT, 0, 0, 0])
        self.assertEqual(self.env.get_player_x(0), 11)
        self.assertEqual(self.env.get_player_keys(0), 1)
        
        # Wait out cooldown (3 steps)
        for _ in range(3):
            self.env.step([0, 0, 0, 0])
            
        # Clear mock buffers before unlocking to isolate sounds
        self.env.clear_mock_buffers()

        # Step 5: Move Right into door (should unlock using the newly acquired key!)
        self.env.step([self.env.BUTTON_RIGHT, 0, 0, 0])
        
        self.assertEqual(self.env.get_player_x(0), 12)
        self.assertEqual(self.env.get_player_keys(0), 0)
        self.assertEqual(self.get_tile(12, 10), self.env.TILE_PLAYER1 + 2)

        self.env.draw_viewport(0)
        sounds = self.env.get_sounds()
        self.assertIn(self.env.SOUND_KEY, sounds)

    def test_f07_f09_t3_monsters_target_closest_player(self):
        """Tier 3: In multiplayer, monsters split targeting and track their nearest player by Manhattan distance."""
        self.helper_setup_clean_map(10, 10, 0)  # P0 at (10, 10)
        
        # Join Player 1 at (20, 10)
        self.env.set_player_position(1, 20, 10)
        self.env.set_player_joined(1, True)
        self.env.set_player_health(1, 100)
        self.set_tile(20, 10, self.env.TILE_PLAYER1 + 8)
        
        # Monster A at (11, 10). Rotor index: (10%4)*4 + (11%4) = 2*4 + 3 = 11.
        self.set_tile(11, 10, self.env.TILE_MONSTER1)
        
        # Monster B at (19, 10). Rotor index: (10%4)*4 + (19%4) = 2*4 + 3 = 11.
        self.set_tile(19, 10, self.env.TILE_MONSTER1)
        
        # Set monster rotor to 10 so they both tick on the next step
        self.env.monster_rotor = 10
        
        # Action: Step
        self.env.step([0, 0, 0, 0])
        
        # Monster A is closer to P0 (dist 1 vs 9) -> moves Left towards P0 -> should be at (10, 10) (hitting P0!)
        # Wait, if Monster A moves Left to (10, 10), it collides with P0, deals 10 damage, and is cleared.
        # Monster B is closer to P1 (dist 1 vs 9) -> moves Right towards P1 -> should be at (20, 10) (hitting P1!)
        # Let's verify both were hit and cleared, and health reduced.
        self.assertEqual(self.env.get_player_health(0), 90)
        self.assertEqual(self.env.get_player_health(1), 90)
        
        self.assertEqual(self.get_tile(11, 10), self.env.TILE_SPACE)
        self.assertEqual(self.get_tile(19, 10), self.env.TILE_SPACE)

        self.env.draw_viewport(0)
        sounds = self.env.get_sounds()
        self.assertIn(self.env.SOUND_HIT, sounds)

    def test_f08_f10_t3_generator_spawn_during_transition(self):
        """Tier 3: A generator is about to spawn on its rotor tick, but player steps onto stairs; the transition aborts the spawn and loads the new level."""
        self.helper_setup_clean_map(10, 10)
        
        # Place Generator 1 at (9, 8) (rotor 1)
        self.set_tile(9, 8, self.env.TILE_GENERATOR1)
        
        # Place stairs at (11, 10)
        self.set_tile(11, 10, self.env.TILE_DOWN)
        
        # Set monster rotor to 0 so it ticks to 1 in this step
        self.env.monster_rotor = 0
        
        # Action: Step Right into stairs
        self.env.step([self.env.BUTTON_RIGHT, 0, 0, 0])
        
        # Assert Globals:
        # Transition triggered: Level 1 loaded, player coordinates reset to Level 1 portal.
        # No monster from Level 0 generator spawned since the map was overwritten.
        self.assertEqual(self.env.current_level, 1)
        self.assertTrue(self.env.get_player_x(0) != 11 or self.env.get_player_y(0) != 10)
        
        # Assert HAL: SOUND_WARP played, but no monster spawn occurred (no monster sprite from Level 0 on map)
        self.env.draw_viewport(0)
        sounds = self.env.get_sounds()
        self.assertIn(self.env.SOUND_WARP, sounds)

if __name__ == '__main__':
    unittest.main()
