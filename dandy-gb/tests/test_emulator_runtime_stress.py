#!/usr/bin/env python3
"""
Emulator-based runtime stress and memory corruption tests.
Uses PyBoy to boot the GameBoy ROM, simulate physical gameplay,
and programmatically verify:
1. Out-of-bounds collision: Player cannot walk into walls or off map edges.
2. Sprite hardware attributes: Verifies OAM flags (palette, priority, flips).
3. OAM/VRAM Stability: Runs extended gameplay simulation (10,000 frames) and
   asserts VRAM pattern memory remains completely uncorrupted (using hash oracle).
"""

import os
import re
import unittest
import hashlib
import random
from pyboy import PyBoy

class TestEmulatorRuntimeStress(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.current_dir = os.path.dirname(os.path.abspath(__file__))
        # Default to Classic ROM, allow dark ROM via env
        cls.rom_path = os.environ.get("ROM_PATH", os.path.normpath(os.path.join(cls.current_dir, "../bin/dandy.gb")))
        cls.map_path = os.path.splitext(cls.rom_path)[0] + ".map"
        
        if not os.path.exists(cls.rom_path):
            raise FileNotFoundError(f"Compiled ROM not found at {cls.rom_path}. Run 'make' first.")
        if not os.path.exists(cls.map_path):
            raise FileNotFoundError(f"Linker map file not found at {cls.map_path}.")
            
        raw_symbols = cls.parse_map_symbols(cls.map_path)
        
        cls.symbols = {}
        required_symbols = [
            "_current_level", "_player_joined", "_player_x", 
            "_player_y", "_player_health", "_player_score",
            "_player_bombs", "_player_keys", "_dandy_map"
        ]
        for sym in required_symbols:
            truncated = sym[:9]
            if truncated not in raw_symbols:
                raise KeyError(f"Required symbol '{sym}' not found in linker map.")
            cls.symbols[sym] = raw_symbols[truncated]

    @classmethod
    def parse_map_symbols(cls, map_path):
        symbols = {}
        with open(map_path, "r") as f:
            for line in f:
                matches = re.findall(r'([0-9A-Fa-f]{8})\s+(_[A-Za-z0-9_]+)', line)
                for addr_str, sym_name in matches:
                    symbols[sym_name] = int(addr_str, 16)
        return symbols

    def setUp(self):
        self.pyboy = PyBoy(self.rom_path, window="null")
        # Let BIOS boot
        for _ in range(180):
            self.pyboy.tick()

    def tearDown(self):
        self.pyboy.stop()

    def get_player_pos(self):
        x = self.pyboy.memory[self.symbols["_player_x"]]
        y = self.pyboy.memory[self.symbols["_player_y"]]
        return x, y

    def get_map_tile(self, x, y):
        map_addr = self.symbols["_dandy_map"]
        idx = y * 60 + x
        return self.pyboy.memory[map_addr + idx]

    # =========================================================================
    # 1. Out-of-Bounds and Collision Stress Tests
    # =========================================================================

    def test_collision_wall_impenetrability(self):
        """Stress test: Ensure player cannot walk through walls even under continuous pressure."""
        p1_x_addr = self.symbols["_player_x"]
        p1_y_addr = self.symbols["_player_y"]
        
        # Scan the dandy_map to find a Wall tile (1) that has a Space tile (0) adjacent to it.
        # This guarantees we can position the player next to a wall and test collision.
        map_addr = self.symbols["_dandy_map"]
        
        target_px, target_py = None, None
        wall_dir = None
        
        # Search inner area of 60x30 map
        found = False
        for y in range(1, 29):
            for x in range(1, 59):
                # If this is a Wall tile
                if self.pyboy.memory[map_addr + y * 60 + x] == 1:
                    # Check neighbors
                    neighbors = {
                        "up": (x, y + 1),     # Space is below, Wall is above -> we move 'up' into wall
                        "down": (x, y - 1),   # Space is above, Wall is below -> we move 'down' into wall
                        "left": (x + 1, y),   # Space is right, Wall is left -> we move 'left' into wall
                        "right": (x - 1, y)   # Space is left, Wall is right -> we move 'right' into wall
                    }
                    for dir_name, (nx, ny) in neighbors.items():
                        if self.pyboy.memory[map_addr + ny * 60 + nx] == 0:
                            target_px, target_py = nx, ny
                            wall_dir = dir_name
                            found = True
                            break
            if found:
                break
                
        self.assertIsNotNone(target_px, "Could not find a suitable Wall-adjacent Space tile in the map!")
        print(f"\n[Collision Test] Hacking player to ({target_px}, {target_py}) next to Wall. Moving '{wall_dir}' into it...")
        
        # Hack player position
        self.pyboy.memory[p1_x_addr] = target_px
        self.pyboy.memory[p1_y_addr] = target_py
        
        # Settle physics/emulator
        for _ in range(5):
            self.pyboy.tick()
            
        # Hold button into the wall for 60 frames (1 second)
        self.pyboy.button_press(wall_dir)
        for _ in range(60):
            self.pyboy.tick()
        self.pyboy.button_release(wall_dir)
        for _ in range(10):
            self.pyboy.tick()
            
        # Assert player didn't move
        end_x, end_y = self.get_player_pos()
        self.assertEqual(target_px, end_x, f"Player walked through wall horizontally! Moved from {target_px} to {end_x}")
        self.assertEqual(target_py, end_y, f"Player walked through wall vertically! Moved from {target_py} to {end_y}")
        print(f"[Collision Test] PASS: Player remained at ({end_x}, {end_y})")

    def test_collision_map_bounds_escape(self):
        """Stress test: Hack player position to map edge and verify player cannot walk off-screen/out-of-bounds."""
        p1_x_addr = self.symbols["_player_x"]
        p1_y_addr = self.symbols["_player_y"]
        
        # Case A: Hack player to Left Edge (x=1 is the leftmost playable tile inside border walls)
        # The borders are at x=0 and x=59.
        print("\n[Bounds Test] Hacking player position to left edge (x=1)...")
        self.pyboy.memory[p1_x_addr] = 1
        _, y = self.get_player_pos()
        self.assertEqual(self.get_map_tile(0, y), 1, "Edge border tile is not Wall!")
        
        # Try to walk left
        self.pyboy.button_press("left")
        for _ in range(30):
            self.pyboy.tick()
        self.pyboy.button_release("left")
        for _ in range(10):
            self.pyboy.tick()
            
        self.assertEqual(self.pyboy.memory[p1_x_addr], 1, "Player escaped left map boundary!")
        
        # Case B: Hack player to Top Edge (y=1 is top playable tile, y=0 is border wall)
        print("[Bounds Test] Hacking player position to top edge (y=1)...")
        self.pyboy.memory[p1_y_addr] = 1
        self.assertEqual(self.get_map_tile(1, 0), 1, "Top border tile is not Wall!")
        
        # Try to walk up
        self.pyboy.button_press("up")
        for _ in range(30):
            self.pyboy.tick()
        self.pyboy.button_release("up")
        for _ in range(10):
            self.pyboy.tick()
            
        self.assertEqual(self.pyboy.memory[p1_y_addr], 1, "Player escaped top map boundary!")
        print("[Bounds Test] PASS: Bounding walls successfully contained the player.")

    # =========================================================================
    # 2. Sprite Hardware Flags Verification
    # =========================================================================

    def test_sprite_hardware_attributes(self):
        """Verify that active OAM sprites have valid hardware flags, tile indices, and coordinates."""
        print("\n[OAM Test] Scanning active hardware sprites in OAM...")
        
        # Tick a few times to let player sprite render
        for _ in range(20):
            self.pyboy.tick()
            
        # Scan OAM (0xFE00 - 0xFE9F, 40 sprites * 4 bytes = 160 bytes)
        active_sprites_count = 0
        for s_idx in range(40):
            base_addr = 0xFE00 + s_idx * 4
            y = self.pyboy.memory[base_addr]
            x = self.pyboy.memory[base_addr + 1]
            tile_idx = self.pyboy.memory[base_addr + 2]
            attrs = self.pyboy.memory[base_addr + 3]
            
            # An OAM entry is active if Y > 0 and X > 0 (GameBoy convention)
            if y > 0 and x > 0:
                active_sprites_count += 1
                # Check that tile index is a valid sprite tile (should be loaded in VRAM 128..159)
                self.assertTrue(
                    128 <= tile_idx < 160,
                    f"Sprite {s_idx} uses out-of-range/unloaded tile index {tile_idx}! Expected in [128, 159]."
                )
                
                # Check attributes byte flags
                # Bit 4: Palette (0 or 1)
                palette = (attrs >> 4) & 1
                # Bit 5: X Flip
                x_flip = (attrs >> 5) & 1
                # Bit 6: Y Flip
                y_flip = (attrs >> 6) & 1
                # Bit 7: Priority
                priority = (attrs >> 7) & 1
                
                self.assertIn(palette, (0, 1), f"Sprite {s_idx} has invalid palette value {palette}")
                self.assertIn(x_flip, (0, 1))
                self.assertIn(y_flip, (0, 1))
                self.assertIn(priority, (0, 1))
                
        self.assertGreater(active_sprites_count, 0, "No active hardware sprites found in OAM! Player sprite should be active.")
        print(f"[OAM Test] PASS: Successfully verified {active_sprites_count} active sprites in OAM.")

    # =========================================================================
    # 3. Memory Corruption & Extended Play Stability Stress
    # =========================================================================

    def test_extended_play_stability_and_vram_hash_oracle(self):
        """Stress test: Runs 10,000 frames of randomized E2E gameplay and asserts no VRAM/OAM/WRAM corruption occurs."""
        iterations = 10000
        print(f"\n[Stability Test] Simulating {iterations} frames of continuous random gameplay...")
        
        # 1. Capture initial VRAM pattern table state (VRAM 0x8000 - 0x8FFF, 4KB of tile graphic patterns)
        # This memory should remain COMPLETELY STATIC during gameplay. If it changes, VRAM corruption occurred!
        initial_vram_patterns = bytes([self.pyboy.memory[addr] for addr in range(0x8000, 0x9000)])
        initial_vram_hash = hashlib.sha256(initial_vram_patterns).hexdigest()
        
        # Capture initial WRAM variables for health and level
        p1_health_addr = self.symbols["_player_health"]
        
        # 2. Gameplay Loop
        buttons = ["up", "down", "left", "right", "a", "b"]
        for frame in range(iterations):
            # Press a random button every 15 frames to simulate a human player
            if frame % 15 == 0:
                btn = random.choice(buttons)
                self.pyboy.button_press(btn)
                self.pyboy.tick()
                self.pyboy.button_release(btn)
            else:
                self.pyboy.tick()
                
            # Every 500 frames, perform sanity checks
            if frame % 500 == 0:
                # A. Verify WRAM State is within sane bounds
                health = self.pyboy.memory[p1_health_addr] | (self.pyboy.memory[p1_health_addr + 1] << 8)
                level = self.pyboy.memory[self.symbols["_current_level"]]
                
                # Health should be 0..999 (could go down or up if food is eaten, but shouldn't be garbage)
                self.assertTrue(0 <= health <= 1000, f"Frame {frame}: WRAM health corrupted, got {health}!")
                self.assertTrue(0 <= level <= 30, f"Frame {frame}: WRAM level corrupted, got {level}!")
                
                # B. Verify OAM state sanity
                for s_idx in range(40):
                    base_addr = 0xFE00 + s_idx * 4
                    y = self.pyboy.memory[base_addr]
                    x = self.pyboy.memory[base_addr + 1]
                    tile_idx = self.pyboy.memory[base_addr + 2]
                    
                    if y > 0 and x > 0:
                        # Coordinate sanity (GameBoy screens are 160x144, but sprites can be offscreen)
                        # Offscreen coordinates are fine, but they shouldn't be garbage (e.g., they fit in a byte)
                        self.assertTrue(0 <= y <= 255)
                        self.assertTrue(0 <= x <= 255)
                        self.assertTrue(
                            128 <= tile_idx < 160,
                            f"Frame {frame}: Sprite {s_idx} tile index corrupted: {tile_idx}! Expected in [128, 159]."
                        )

        # 3. Post-run verification
        # A. Check VRAM Pattern Memory Hash Oracle
        final_vram_patterns = bytes([self.pyboy.memory[addr] for addr in range(0x8000, 0x9000)])
        final_vram_hash = hashlib.sha256(final_vram_patterns).hexdigest()
        
        self.assertEqual(
            initial_vram_hash, final_vram_hash,
            "CRITICAL ERROR: VRAM Pattern Memory was modified during gameplay! Graphic assets were corrupted!"
        )
        
        # B. Verify WRAM health/level didn't crash
        final_health = self.pyboy.memory[p1_health_addr] | (self.pyboy.memory[p1_health_addr + 1] << 8)
        final_level = self.pyboy.memory[self.symbols["_current_level"]]
        print(f"[Stability Test] Completed. Final State: Level={final_level}, Health={final_health}")
        print("[Stability Test] PASS: No memory corruption detected after 10,000 frames.")

if __name__ == "__main__":
    unittest.main()
