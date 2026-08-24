import os
import re
import base64
import unittest
from PIL import Image

class TestGraphicsPipeline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Paths
        cls.current_dir = os.path.dirname(os.path.abspath(__file__))
        cls.repo_root = os.path.normpath(os.path.join(cls.current_dir, "../.."))
        cls.tiles_c_path = os.path.join(cls.repo_root, "dandy-gb/src/tiles.c")
        cls.strike_png_path = os.path.join(cls.repo_root, "dandy-gb/teamwork_graphics/strike_original.png")
        cls.audit_png_path = os.path.join(cls.repo_root, "dandy-gb/teamwork_graphics/graphics_audit.png")
        cls.js_path = os.path.join(cls.repo_root, "dandy-js/strike.js")

    def test_verify_files_exist(self):
        """Verify that the required source and generated files exist."""
        self.assertTrue(os.path.exists(self.tiles_c_path), f"tiles.c not found at {self.tiles_c_path}")
        self.assertTrue(os.path.exists(self.strike_png_path), f"strike_original.png not found. Run extract_sprites.py first.")
        self.assertTrue(os.path.exists(self.audit_png_path), f"graphics_audit.png not found. Run verify_graphics.py first.")
        self.assertTrue(os.path.exists(self.js_path), f"strike.js not found at {self.js_path}")

    def test_independent_tile_decoding_and_audit_match(self):
        """Independently parse tiles.c, decode them, and verify pixel-for-pixel match and exact nearest-neighbor upscaling in graphics_audit.png."""
        # 1. Independently parse tiles.c
        with open(self.tiles_c_path, "r") as f:
            content = f.read()

        # Find the dandy_tiles array
        array_match = re.search(r"const\s+unsigned\s+char\s+dandy_tiles\[\]\s*=\s*\{([^}]+)\};", content, re.DOTALL)
        self.assertTrue(array_match, "Failed to find dandy_tiles array in tiles.c using independent regex")

        hex_vals = re.findall(r"0x[0-9a-fA-F]{2}", array_match.group(1))
        self.assertEqual(len(hex_vals), 512, f"Expected 512 hex values in tiles.c, found {len(hex_vals)}")
        tiles_bytes = bytes(int(val, 16) for val in hex_vals)

        # 2. Define independent decoding and palette mapping
        # Category sets (must match verify_graphics.py)
        bg_indices = set(list(range(9)) + list(range(12, 16)) + list(range(20, 24)) + list(range(28, 32)))
        sprite_indices = set(list(range(9, 12)) + list(range(16, 20)) + list(range(24, 28)))

        def independent_decode_tile(tile_idx):
            offset = tile_idx * 16
            tile_data = tiles_bytes[offset:offset+16]
            is_sprite = tile_idx in sprite_indices

            if is_sprite:
                # OBP0 palette colors
                colors = [
                    (0, 0, 0),        # 0: Transparent (rendered as Black)
                    (255, 255, 255),  # 1: White
                    (96, 96, 96),     # 2: Dark Gray
                    (0, 0, 0)         # 3: Black
                ]
            else:
                # BGP palette colors
                colors = [
                    (0, 0, 0),        # 0: Black
                    (96, 96, 96),     # 1: Dark Gray
                    (176, 176, 176),  # 2: Light Gray
                    (255, 255, 255)   # 3: White
                ]

            decoded_pixels = []
            for y in range(8):
                byte1 = tile_data[2 * y]
                byte2 = tile_data[2 * y + 1]
                row_pixels = []
                for x in range(8):
                    bit_index = 7 - x
                    low_bit = (byte1 >> bit_index) & 1
                    high_bit = (byte2 >> bit_index) & 1
                    color_idx = (high_bit << 1) | low_bit
                    row_pixels.append(colors[color_idx])
                decoded_pixels.append(row_pixels)
            return decoded_pixels

        # 3. Load graphics_audit.png and verify
        audit_img = Image.open(self.audit_png_path)
        self.assertEqual(audit_img.size, (1024, 1024), f"Expected graphics_audit.png size to be 1024x1024, got {audit_img.size}")
        audit_pixels = audit_img.load()

        for i in range(32):
            decoded = independent_decode_tile(i)

            col = i % 4
            row = i // 4
            cell_x = col * 256
            cell_y = row * 128

            # Right half of cell (GB tile upscaled 16x)
            gb_x_start = cell_x + 128
            gb_y_start = cell_y

            for y in range(8):
                for x in range(8):
                    expected_color = decoded[y][x]
                    
                    # Each 8x8 pixel maps to a 16x16 block in the audit image
                    pixel_x_start = gb_x_start + x * 16
                    pixel_y_start = gb_y_start + y * 16

                    # Sample all 256 pixels in the 16x16 block to ensure 100% uniformity and match
                    for dy in range(16):
                        for dx in range(16):
                            actual_color = audit_pixels[pixel_x_start + dx, pixel_y_start + dy]
                            # Compare RGB values
                            self.assertEqual(
                                actual_color[:3], expected_color,
                                f"Pixel mismatch at Tile {i}, GB local pixel ({x},{y}), upscaled pixel offset (+{dx},+{dy}). "
                                f"Expected {expected_color}, got {actual_color[:3]}"
                            )

        print("SUCCESS: 32 tiles decoded independently and verified pixel-for-pixel against graphics_audit.png!")
        print("SUCCESS: Exact nearest-neighbor upscaling verified with zero blur or antialiasing!")

    def test_extract_sprites_robustness(self):
        """Test the robustness of extract_sprites.py regex against formatting variations."""
        # The extraction regex under test:
        extract_regex = r'strike\.src\s*=\s*"data:image/png;base64,"\s*\+\s*(.+?);'

        # Helper to simulate the extraction logic from extract_sprites.py
        def extract_base64(content):
            match = re.search(extract_regex, content, re.DOTALL)
            if not match:
                return None
            assignment = match.group(1)
            strings = re.findall(r'"([^"]*)"', assignment)
            return "".join(strings)

        # Case A: Original format (should pass)
        original_js = 'strike.src = "data:image/png;base64,"+\n"iVBORw"+\n"lFTkSuQmCC";'
        self.assertEqual(extract_base64(original_js), "iVBORwlFTkSuQmCC")

        # Case B: Extra/unexpected whitespace and newlines (should pass because of \s* and re.DOTALL)
        whitespace_js = '  strike.src   =   \n  "data:image/png;base64,"  \n  +  \n  "iVBORw"  \n  +  \n  "lFTkSuQmCC"  \n  ;  '
        self.assertEqual(extract_base64(whitespace_js), "iVBORwlFTkSuQmCC")

        # Case C: Single quotes used for the prefix (should fail!)
        single_quote_prefix_js = "strike.src = 'data:image/png;base64,' +\n\"iVBORw\" +\n\"lFTkSuQmCC\";"
        self.assertIsNone(extract_base64(single_quote_prefix_js), "Expected failure when single quotes are used for the prefix")

        # Case D: Single quotes used for the base64 chunks (should fail to extract chunks because of re.findall(r'"([^"]*)"'))
        single_quote_chunks_js = 'strike.src = "data:image/png;base64," +\n\'iVBORw\' +\n\'lFTkSuQmCC\';'
        self.assertEqual(extract_base64(single_quote_chunks_js), "", "Expected empty string chunk extraction when chunks use single quotes")

        # Case E: No concatenation (single long double-quoted string containing prefix + data) (should fail!)
        single_string_js = 'strike.src = "data:image/png;base64,iVBORwlFTkSuQmCC";'
        self.assertIsNone(extract_base64(single_string_js), "Expected failure when no concatenation (+) is used")

        # Case F: ES6 template literal (backticks) (should fail!)
        template_literal_js = 'strike.src = `data:image/png;base64,iVBORwlFTkSuQmCC`;'
        self.assertIsNone(extract_base64(template_literal_js), "Expected failure when backticks are used")

        print("SUCCESS: Robustness edge cases tested successfully! Documented regex limitations.")

if __name__ == "__main__":
    unittest.main()
