import unittest
import os
import sys
import ctypes

# Ensure tests/ directory is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dandy_env import DandyEnv

class TestAdversarialCompression(unittest.TestCase):
    def setUp(self):
        self.env = DandyEnv()
        self.env.init()
        
        # Bind to the global dandy_levels array via ctypes
        # dandy_levels is const uint8_t* const dandy_levels[DANDY_NUM_LEVELS]
        self.dandy_levels = (ctypes.POINTER(ctypes.c_uint8) * self.env.num_levels).in_dll(self.env._lib, "dandy_levels")
        
        # Bind to the global dandy_level_sizes array via ctypes
        self.dandy_level_sizes = (ctypes.c_uint16 * self.env.num_levels).in_dll(self.env._lib, "dandy_level_sizes")
        
        # Make the memory pages containing the arrays writable using mprotect
        self.libc = ctypes.CDLL(None)
        pagesize = 4096
        
        addr = ctypes.addressof(self.dandy_levels)
        page_addr = addr & ~(pagesize - 1)
        res = self.libc.mprotect(ctypes.c_void_p(page_addr), pagesize * 2, 1 | 2) # PROT_READ | PROT_WRITE
        if res != 0:
            raise RuntimeError(f"mprotect failed to make dandy_levels writable: {res}")
            
        addr_sizes = ctypes.addressof(self.dandy_level_sizes)
        page_addr_sizes = addr_sizes & ~(pagesize - 1)
        res_sizes = self.libc.mprotect(ctypes.c_void_p(page_addr_sizes), pagesize * 2, 1 | 2)
        if res_sizes != 0:
            raise RuntimeError(f"mprotect failed to make dandy_level_sizes writable: {res_sizes}")

    def tearDown(self):
        if hasattr(self, "env") and self.env is not None:
            self.env.close()
            self.env = None

    def compress_map(self, tile_ids):
        """Python helper to compress a 60x30 map using Edge Wall Elision + Scheme B2."""
        # 1. Edge Wall Elision: keep only the inner 58x28 grid
        inner_tiles = []
        for r in range(1, 29):
            start_idx = r * 60 + 1
            end_idx = r * 60 + 59
            inner_tiles.extend(tile_ids[start_idx:end_idx])
            
        # 2. Scheme B2 Prefix Encoding
        bits = []
        for tile in inner_tiles:
            if tile == 0:
                bits.append(0)
            elif tile == 1:
                bits.extend([1, 0])
            elif 2 <= tile <= 15:
                bits.extend([1, 1])
                for i in range(3, -1, -1):
                    bits.append((tile >> i) & 1)
            else:
                raise ValueError(f"Invalid tile ID {tile} for Scheme B2 compression")
                
        # 3. Bitstream Packing (MSB-first)
        packed_bytes = []
        for i in range(0, len(bits), 8):
            chunk = bits[i:i+8]
            byte_val = 0
            for bit_idx, bit in enumerate(chunk):
                byte_val |= (bit << (7 - bit_idx))
            packed_bytes.append(byte_val)
        return bytes(packed_bytes)

    def set_custom_compressed_level(self, level_idx, compressed_bytes):
        """Points dandy_levels[level_idx] to a dynamically allocated ctypes byte array."""
        # We must keep a reference to the ctypes array to prevent garbage collection
        self.custom_data_ref = (ctypes.c_uint8 * len(compressed_bytes))(*compressed_bytes)
        self.dandy_levels[level_idx] = ctypes.cast(self.custom_data_ref, ctypes.POINTER(ctypes.c_uint8))
        self.dandy_level_sizes[level_idx] = len(compressed_bytes)

    # =========================================================================
    # ADV-01: Boundary Compression Tests (All Spaces, All Walls, All Doors)
    # =========================================================================

    def test_adv01_all_spaces_level(self):
        """ADV-01: A level with 100% space (minimal compressed footprint) loads and decodes correctly."""
        # Create a map with all spaces, but the outer border must be walls
        expected_map = [self.env.TILE_SPACE] * self.env.MAP_SIZE
        # Outer border filled with walls
        for x in range(60):
            expected_map[0 * 60 + x] = self.env.TILE_WALL
            expected_map[29 * 60 + x] = self.env.TILE_WALL
        for y in range(30):
            expected_map[y * 60 + 0] = self.env.TILE_WALL
            expected_map[y * 60 + 59] = self.env.TILE_WALL

        # The inner 1624 tiles are all spaces (0)
        # Scheme B2: 1624 spaces = 1624 bits of 0 = 203 bytes of 0x00
        compressed = self.compress_map(expected_map)
        self.assertEqual(len(compressed), 203)
        self.assertEqual(compressed, b'\x00' * 203)

        # Load custom level
        self.set_custom_compressed_level(0, compressed)
        self.env.load_level(0)

        # Clear active (joined) players from the decoded map copy
        decoded_map = self.env.dandy_map
        for p in range(self.env.MAX_PLAYERS):
            if self.env.is_player_joined(p):
                px = self.env.get_player_x(p)
                py = self.env.get_player_y(p)
                decoded_map[py * 60 + px] = self.env.TILE_SPACE

        self.assertEqual(decoded_map, expected_map)
        self.env.assert_outer_border_walls(self)

    def test_adv01_all_walls_level(self):
        """ADV-01: A level with 100% walls (2-bit codes) loads and decodes correctly."""
        # Create a map with all walls
        expected_map = [self.env.TILE_WALL] * self.env.MAP_SIZE

        # Inner 1624 tiles are all walls (1)
        # Scheme B2: 1624 walls = 3248 bits of '10' = 406 bytes of 0xAA (10101010)
        compressed = self.compress_map(expected_map)
        self.assertEqual(len(compressed), 406)
        self.assertEqual(compressed, b'\xAA' * 406)

        # Load custom level
        self.set_custom_compressed_level(0, compressed)
        self.env.load_level(0)

        # Clear active players
        decoded_map = self.env.dandy_map
        for p in range(self.env.MAX_PLAYERS):
            if self.env.is_player_joined(p):
                px = self.env.get_player_x(p)
                py = self.env.get_player_y(p)
                decoded_map[py * 60 + px] = self.env.TILE_WALL

        self.assertEqual(decoded_map, expected_map)
        self.env.assert_outer_border_walls(self)

    def test_adv01_all_doors_level(self):
        """ADV-01: A level with 100% doors (6-bit codes, maximum footprint) decodes correctly."""
        # Create a map with doors inside, walls on border
        expected_map = [self.env.TILE_DOOR] * self.env.MAP_SIZE
        for x in range(60):
            expected_map[0 * 60 + x] = self.env.TILE_WALL
            expected_map[29 * 60 + x] = self.env.TILE_WALL
        for y in range(30):
            expected_map[y * 60 + 0] = self.env.TILE_WALL
            expected_map[y * 60 + 59] = self.env.TILE_WALL

        # Inner 1624 tiles are all doors (2)
        # Scheme B2: '11' + '0010' = '110010' (6 bits per tile)
        # Total bits = 1624 * 6 = 9744 bits = 1218 bytes
        compressed = self.compress_map(expected_map)
        self.assertEqual(len(compressed), 1218)

        # Load custom level
        self.set_custom_compressed_level(0, compressed)
        self.env.load_level(0)

        # Clear active players
        decoded_map = self.env.dandy_map
        for p in range(self.env.MAX_PLAYERS):
            if self.env.is_player_joined(p):
                px = self.env.get_player_x(p)
                py = self.env.get_player_y(p)
                decoded_map[py * 60 + px] = self.env.TILE_SPACE # portal is space after player clears it

        # Verify doors are in the right spots
        for y in range(1, 29):
            for x in range(1, 59):
                # skip active player spawn spots which got cleared to TILE_SPACE
                is_spawn = False
                for p in range(self.env.MAX_PLAYERS):
                    if self.env.is_player_joined(p) and x == self.env.get_player_x(p) and y == self.env.get_player_y(p):
                        is_spawn = True
                if not is_spawn:
                    self.assertEqual(decoded_map[y * 60 + x], self.env.TILE_DOOR)

        self.env.assert_outer_border_walls(self)

    # =========================================================================
    # ADV-02: Padding & Bit-Alignment Corners
    # =========================================================================

    def test_adv02_padding_bits_ignored(self):
        """ADV-02: Verify that the decompressor stops exactly after 1624 tiles and ignores padding bits."""
        # We will craft a map with 1623 spaces and 1 wall as the very last tile.
        # Inner grid size = 1624 tiles.
        # First 1623 tiles: Space (0) -> 1623 bits of 0.
        # Last tile (1624th): Wall (1) -> 2 bits: '10'.
        # Total bits = 1623 + 2 = 1625 bits = 203 bytes + 1 bit.
        # Packed into 204 bytes.
        
        expected_map = [self.env.TILE_SPACE] * self.env.MAP_SIZE
        # Outer border walls
        for x in range(60):
            expected_map[0 * 60 + x] = self.env.TILE_WALL
            expected_map[29 * 60 + x] = self.env.TILE_WALL
        for y in range(30):
            expected_map[y * 60 + 0] = self.env.TILE_WALL
            expected_map[y * 60 + 59] = self.env.TILE_WALL
            
        # Set the very last inner tile (row 28, col 58) to TILE_WALL
        last_inner_idx = 28 * 60 + 58
        expected_map[last_inner_idx] = self.env.TILE_WALL

        compressed = self.compress_map(expected_map)
        self.assertEqual(len(compressed), 204) # 1625 bits requires 204 bytes

        # Load custom level
        self.set_custom_compressed_level(0, compressed)
        self.env.load_level(0)

        # Clear active players
        decoded_map = self.env.dandy_map
        for p in range(self.env.MAX_PLAYERS):
            if self.env.is_player_joined(p):
                px = self.env.get_player_x(p)
                py = self.env.get_player_y(p)
                decoded_map[py * 60 + px] = self.env.TILE_SPACE

        # Verify the last tile is indeed TILE_WALL
        self.assertEqual(decoded_map[last_inner_idx], self.env.TILE_WALL)
        # Verify all other inner tiles are TILE_SPACE
        for y in range(1, 29):
            for x in range(1, 59):
                idx = y * 60 + x
                if idx != last_inner_idx:
                    self.assertEqual(decoded_map[idx], self.env.TILE_SPACE)

    # =========================================================================
    # ADV-03: Huffman Bitstream Corruption & Invalid Prefixes
    # =========================================================================

    def test_adv03_corrupted_all_ones_bitstream(self):
        """ADV-03: Verify decoding behavior of a corrupted bitstream containing all 1s (0xFF)."""
        # A stream of 0xFF bytes:
        # Every bit is 1.
        # The decompressor reads '11' (other tile), then decodes 4 bits of ID: '1111' = 15 (TILE_GENERATOR3).
        # This consumes 6 bits.
        # Footprint: 1624 tiles * 6 bits = 9744 bits = 1218 bytes of 0xFF.
        compressed = b'\xFF' * 1218

        # Load custom level
        self.set_custom_compressed_level(0, compressed)
        self.env.load_level(0)

        # Verify that all non-spawn inner tiles are TILE_GENERATOR3
        decoded_map = self.env.dandy_map
        for y in range(1, 29):
            for x in range(1, 59):
                # skip player spawns
                is_spawn = False
                for p in range(self.env.MAX_PLAYERS):
                    if self.env.is_player_joined(p) and x == self.env.get_player_x(p) and y == self.env.get_player_y(p):
                        is_spawn = True
                if not is_spawn:
                    self.assertEqual(decoded_map[y * 60 + x], self.env.TILE_GENERATOR3)

    # =========================================================================
    # ADV-04: Truncated Bitstream (Out-of-Bounds Read Exposure)
    # =========================================================================

    def test_adv04_truncated_bitstream_oob_read(self):
        """ADV-04: Expose the out-of-bounds read vulnerability when loading a truncated bitstream."""
        # We will allocate a buffer of 1500 bytes.
        # The first 10 bytes are 0x00 (which decodes to spaces).
        # The remaining 1490 bytes are filled with 0xFF (which decodes to TILE_GENERATOR3 / 15).
        # We will set the size of level 0 to exactly 10 bytes.
        
        buffer_size = 1500
        logical_size = 10
        
        # Create a single contiguous block of memory
        full_buffer = [0x00] * logical_size + [0xFF] * (buffer_size - logical_size)
        
        # Point the level pointer to the START of this buffer
        self.set_custom_compressed_level(0, full_buffer)
        # Set the logical compressed size of this level to 10 bytes
        self.dandy_level_sizes[0] = logical_size
        
        # Call load_level. The engine expects 1624 tiles.
        # 10 bytes of 0x00 can only decode 80 tiles.
        # The remaining 1544 tiles should be decoded safely as spaces (0) instead of reading
        # out-of-bounds into the trailing 0xFF sentinel bytes.
        self.env.load_level(0)
        
        decoded_map = self.env.dandy_map
        
        # Verify that all inner tiles are safely decoded as TILE_SPACE (or player spawns)
        # and absolutely no tiles are decoded as TILE_GENERATOR3 (15) from the out-of-bounds sentinel region.
        for y in range(1, 29):
            for x in range(1, 59):
                is_spawn = False
                for p in range(self.env.MAX_PLAYERS):
                    if self.env.is_player_joined(p) and x == self.env.get_player_x(p) and y == self.env.get_player_y(p):
                        is_spawn = True
                if not is_spawn:
                    self.assertEqual(decoded_map[y * 60 + x], self.env.TILE_SPACE, f"Tile at ({x}, {y}) was {decoded_map[y * 60 + x]} instead of TILE_SPACE")

if __name__ == '__main__':
    unittest.main()
