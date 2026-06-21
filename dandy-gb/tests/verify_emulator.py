import os
import re
import unittest
from pyboy import PyBoy

class TestEmulator(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Resolve absolute paths
        cls.current_dir = os.path.dirname(os.path.abspath(__file__))
        # Resolve ROM path, allowing override via environment variable
        cls.rom_path = os.environ.get("ROM_PATH", os.path.normpath(os.path.join(cls.current_dir, "../bin/dandy.gb")))
        cls.map_path = os.path.splitext(cls.rom_path)[0] + ".map"
        
        # Ensure the ROM and map files exist
        if not os.path.exists(cls.rom_path):
            raise FileNotFoundError(f"Compiled ROM not found at {cls.rom_path}. Run 'make' first.")
        if not os.path.exists(cls.map_path):
            raise FileNotFoundError(f"Linker map file not found at {cls.map_path}.")
            
        # Parse variable addresses from dandy.map
        raw_symbols = cls.parse_map_symbols(cls.map_path)
        
        # Resolve symbols taking GBDK's 9-character truncation into account
        cls.symbols = {}
        required_symbols = [
            "_current_level", "_player_joined", "_player_x", 
            "_player_y", "_player_health", "_player_score",
            "_player_bombs", "_player_keys", "_dandy_map"
        ]
        for sym in required_symbols:
            truncated = sym[:9]
            if truncated not in raw_symbols:
                raise KeyError(f"Required symbol '{sym}' (truncated: '{truncated}') not found in linker map file.")
            cls.symbols[sym] = raw_symbols[truncated]

    @classmethod
    def parse_map_symbols(cls, map_path):
        """Parses the GBDK linker map file to dynamically resolve symbol WRAM addresses."""
        symbols = {}
        with open(map_path, "r") as f:
            for line in f:
                # Match hex addresses (8-digit hex) and symbol names
                matches = re.findall(r'([0-9A-Fa-f]{8})\s+(_[A-Za-z0-9_]+)', line)
                for addr_str, sym_name in matches:
                    symbols[sym_name] = int(addr_str, 16)
        return symbols

    def setUp(self):
        # Initialize PyBoy in headless mode
        self.pyboy = PyBoy(self.rom_path, window="null")
        # Run for 180 frames (3 seconds) to let GameBoy BIOS boot and initialize the game state
        for _ in range(180):
            self.pyboy.tick()

    def tearDown(self):
        self.pyboy.stop()

    def test_game_initial_state(self):
        """Verify that the GameBoy game boots up and initializes the WRAM state correctly."""
        # Read variables from WRAM addresses
        current_level = self.pyboy.memory[self.symbols["_current_level"]]
        player1_joined = self.pyboy.memory[self.symbols["_player_joined"]]
        
        # Player 1 health is a 16-bit unsigned integer (2 bytes, little-endian)
        p1_health_addr = self.symbols["_player_health"]
        player1_health = self.pyboy.memory[p1_health_addr] | (self.pyboy.memory[p1_health_addr + 1] << 8)
        
        p1_x = self.pyboy.memory[self.symbols["_player_x"]]
        p1_y = self.pyboy.memory[self.symbols["_player_y"]]

        print(f"\n[Emulator Test] Initial State: Level={current_level}, P1_Joined={player1_joined}, Health={player1_health}, Pos=({p1_x}, {p1_y})")

        # Assertions
        self.assertEqual(current_level, 0, "Game should start on Level 0.")
        self.assertEqual(player1_joined, 1, "Player 1 should be joined by default.")
        self.assertEqual(player1_health, 100, "Player 1 starting health should be 100.")
        self.assertGreater(p1_x, 0, "Player 1 X spawn coordinate should be greater than 0.")
        self.assertGreater(p1_y, 0, "Player 1 Y spawn coordinate should be greater than 0.")

    def test_player_movement(self):
        """Simulate a player movement button press and verify coordinate changes in WRAM."""
        p1_x_addr = self.symbols["_player_x"]
        p1_y_addr = self.symbols["_player_y"]
        map_addr = self.symbols["_dandy_map"]
        
        # Get starting position
        start_x = self.pyboy.memory[p1_x_addr]
        start_y = self.pyboy.memory[p1_y_addr]
        
        # Read the tiles surrounding the player in the 60x30 WRAM map to find an empty direction
        # Each row is 60 bytes wide.
        idx_up = (start_y - 1) * 60 + start_x
        idx_down = (start_y + 1) * 60 + start_x
        idx_left = start_y * 60 + (start_x - 1)
        idx_right = start_y * 60 + (start_x + 1)
        
        tile_up = self.pyboy.memory[map_addr + idx_up]
        tile_down = self.pyboy.memory[map_addr + idx_down]
        tile_left = self.pyboy.memory[map_addr + idx_left]
        tile_right = self.pyboy.memory[map_addr + idx_right]
        
        print(f"[Emulator Test] Player adjacent tiles: UP={tile_up}, DOWN={tile_down}, LEFT={tile_left}, RIGHT={tile_right}")
        
        # Determine a valid direction to move (TILE_SPACE is 0)
        chosen_direction = None
        expected_x = start_x
        expected_y = start_y
        
        if tile_right == 0:
            chosen_direction = "right"
            expected_x = start_x + 1
        elif tile_down == 0:
            chosen_direction = "down"
            expected_y = start_y + 1
        elif tile_left == 0:
            chosen_direction = "left"
            expected_x = start_x - 1
        elif tile_up == 0:
            chosen_direction = "up"
            expected_y = start_y - 1
            
        self.assertIsNotNone(chosen_direction, "No empty spaces adjacent to the player spawn location! Player is stuck.")
        print(f"[Emulator Test] Simulating movement: '{chosen_direction}' from ({start_x}, {start_y}) to ({expected_x}, {expected_y})")
        
        # Simulate holding the direction button
        self.pyboy.button_press(chosen_direction)
        # Run for 20 frames (approx 330ms) to let the physics tick trigger and execute the move
        for _ in range(20):
            self.pyboy.tick()
            
        # Release the button and tick a few more times to settle the state
        self.pyboy.button_release(chosen_direction)
        for _ in range(10):
            self.pyboy.tick()
            
        # Verify new coordinates in WRAM
        new_x = self.pyboy.memory[p1_x_addr]
        new_y = self.pyboy.memory[p1_y_addr]
        print(f"[Emulator Test] Moved State: Pos=({new_x}, {new_y})")
        
        self.assertEqual(new_x, expected_x, f"X coordinate mismatch after moving {chosen_direction}!")
        self.assertEqual(new_y, expected_y, f"Y coordinate mismatch after moving {chosen_direction}!")

if __name__ == "__main__":
    unittest.main()
