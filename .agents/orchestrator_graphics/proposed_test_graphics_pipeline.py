"""Unit and integration tests for the graphics extraction and verification pipeline."""

import os
import sys
import re
import base64
import unittest
from PIL import Image

# Add the tools directory to sys.path so we can import modules from there
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(os.path.join(parent_dir, "tools"))

import extract_sprites
import verify_graphics

class TestGraphicsPipeline(unittest.TestCase):
    
    def setUp(self):
        self.tiles_c_path = os.path.join(parent_dir, "src/tiles.c")
        self.strike_js_path = os.path.join(parent_dir, "../dandy-js/strike.js")
        self.output_dir = os.path.join(parent_dir, "teamwork_graphics")
        self.strike_png_path = os.path.join(self.output_dir, "strike_original.png")
        self.audit_png_path = os.path.join(self.output_dir, "graphics_audit.png")
        self.audit_dark_png_path = os.path.join(self.output_dir, "graphics_audit_dark.png")

    def test_independent_tile_decoding(self):
        """Independently parse tiles.c and decode them, asserting pixel-for-pixel match."""
        # 1. Parse tiles.c using our own independent regex to verify parse_tiles_c
        with open(self.tiles_c_path, "r") as f:
            content = f.read()
        
        content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
        content = re.sub(r'//.*?\n', '\n', content)
        
        match = re.search(r"const\s+unsigned\s+char\s+dandy_tiles\s*(?:\[[^\]]*\])?\s*=\s*\{([^}]+)\}", content, re.DOTALL)
        self.assertTrue(match, "Could not find dandy_tiles array in tiles.c")
        
        array_content = match.group(1)
        hex_values = re.findall(r"0x[0-9a-fA-F]{2}", array_content)
        self.assertEqual(len(hex_values), 512, f"Expected 512 hex values, found {len(hex_values)}")
        
        independent_bytes = bytes(int(val, 16) for val in hex_values)
        
        # Parse using tools/verify_graphics.py
        pipeline_bytes = verify_graphics.parse_tiles_c(self.tiles_c_path)
        self.assertEqual(independent_bytes, pipeline_bytes, "Parsed bytes do not match pipeline bytes")

        # 2. Independently decode GB tile format and match pixel-for-pixel (Light Floor - Default)
        sprite_indices = set(list(range(9, 12)) + list(range(16, 20)) + list(range(24, 28)))

        for i in range(32):
            tile_offset = i * 16
            tile_data = independent_bytes[tile_offset : tile_offset + 16]
            is_sprite = i in sprite_indices
            
            # Call pipeline decoder (defaults to Light Floor)
            pipeline_img = verify_graphics.decode_gb_tile(tile_data, is_sprite=is_sprite)
            self.assertEqual(pipeline_img.mode, "RGBA", "Expected RGBA image mode")
            pipeline_pixels = pipeline_img.load()

            # Independent decoding implementation for Light Floor
            if is_sprite:
                # Sprite palette (OBP0 = 0xE0)
                # Index 0: Transparent (alpha=0), Index 1: White, Index 2: Dark Gray, Index 3: Black
                colors = [
                    (0, 0, 0, 0),          # 0: Transparent
                    (255, 255, 255, 255),  # 1: White
                    (85, 85, 85, 255),     # 2: Dark Gray
                    (0, 0, 0, 255)         # 3: Black
                ]
            else:
                # Background palette: Classic DMG (Light Floor)
                # Index 0: White, Index 1: Light Gray, Index 2: Dark Gray, Index 3: Black
                colors = [
                    (255, 255, 255, 255),  # 0: White
                    (170, 170, 170, 255),  # 1: Light Gray
                    (85, 85, 85, 255),     # 2: Dark Gray
                    (0, 0, 0, 255)         # 3: Black
                ]

            # Decode 8x8 pixels
            independent_pixels = {}
            for y in range(8):
                low_byte = tile_data[2 * y]
                high_byte = tile_data[2 * y + 1]
                for x in range(8):
                    bit = 7 - x
                    low_bit = (low_byte >> bit) & 1
                    high_bit = (high_byte >> bit) & 1
                    color_idx = (high_bit << 1) | low_bit
                    independent_pixels[(x, y)] = colors[color_idx]

            # Assert pixel-for-pixel correctness
            for y in range(8):
                for x in range(8):
                    self.assertEqual(
                        pipeline_pixels[x, y],
                        independent_pixels[(x, y)],
                        f"Pixel mismatch at tile {i}, coordinate ({x}, {y})"
                    )

        # 3. Independently decode GB tile format and match pixel-for-pixel (Dark Floor)
        for i in range(32):
            tile_offset = i * 16
            tile_data = independent_bytes[tile_offset : tile_offset + 16]
            is_sprite = i in sprite_indices
            
            # Call pipeline decoder with use_dark_floor=True
            pipeline_img = verify_graphics.decode_gb_tile(tile_data, is_sprite=is_sprite, use_dark_floor=True)
            self.assertEqual(pipeline_img.mode, "RGBA", "Expected RGBA image mode")
            pipeline_pixels = pipeline_img.load()

            # Independent decoding implementation for Dark Floor
            if is_sprite:
                # Sprite palette (OBP0 = 0xE0) - does not change
                colors = [
                    (0, 0, 0, 0),          # 0: Transparent
                    (255, 255, 255, 255),  # 1: White
                    (85, 85, 85, 255),     # 2: Dark Gray
                    (0, 0, 0, 255)         # 3: Black
                ]
            else:
                # Background palette: Atmospheric (Dark Floor)
                # Index 0: Black, Index 1: Dark Gray, Index 2: Light Gray, Index 3: White
                colors = [
                    (0, 0, 0, 255),        # 0: Black
                    (85, 85, 85, 255),     # 1: Dark Gray
                    (170, 170, 170, 255),  # 2: Light Gray
                    (255, 255, 255, 255)   # 3: White
                ]

            # Decode 8x8 pixels
            independent_pixels = {}
            for y in range(8):
                low_byte = tile_data[2 * y]
                high_byte = tile_data[2 * y + 1]
                for x in range(8):
                    bit = 7 - x
                    low_bit = (low_byte >> bit) & 1
                    high_bit = (high_byte >> bit) & 1
                    color_idx = (high_bit << 1) | low_bit
                    independent_pixels[(x, y)] = colors[color_idx]

            # Assert pixel-for-pixel correctness
            for y in range(8):
                for x in range(8):
                    self.assertEqual(
                        pipeline_pixels[x, y],
                        independent_pixels[(x, y)],
                        f"Pixel mismatch at dark tile {i}, coordinate ({x}, {y})"
                    )

    def test_nearest_neighbor_upscaling(self):
        """Verify that upscaling uses exact nearest-neighbor interpolation without introducing blur."""
        # Clean up any pre-existing files to make sure we generate them honestly
        for path in [self.audit_png_path, self.audit_dark_png_path]:
            if os.path.exists(path):
                os.remove(path)

        # 1. Run verify_graphics to generate Light Floor audit sheet
        verify_graphics.main([])
        self.assertTrue(os.path.exists(self.audit_png_path), "graphics_audit.png was not generated")
        
        # 2. Run verify_graphics with --dark-floor to generate Dark Floor audit sheet
        verify_graphics.main(["--dark-floor"])
        self.assertTrue(os.path.exists(self.audit_dark_png_path), "graphics_audit_dark.png was not generated")
        
        # Verify that each 128x128 GB tile block contains exact 16x16 pixel blocks
        for audit_path in [self.audit_png_path, self.audit_dark_png_path]:
            audit_img = Image.open(audit_path)
            self.assertEqual(audit_img.size, (1024, 1024), f"Expected audit sheet size 1024x1024 for {audit_path}")
            
            grid_cols = 4
            pixels = audit_img.load()

            for i in range(32):
                col = i % grid_cols
                row = i // grid_cols
                cell_x = col * 256
                cell_y = row * 128
                gb_start_x = cell_x + 128
                gb_start_y = cell_y

                # Check every 16x16 block within the 128x128 upscaled GB tile
                for ty in range(8):
                    for tx in range(8):
                        block_x = gb_start_x + tx * 16
                        block_y = gb_start_y + ty * 16
                        
                        reference_color = pixels[block_x, block_y]
                        
                        for dy in range(16):
                            for dx in range(16):
                                current_color = pixels[block_x + dx, block_y + dy]
                                self.assertEqual(
                                    current_color,
                                    reference_color,
                                    f"Antialiasing/blur detected in upscaled GB tile at tile {i}, sub-block ({tx},{ty}) in {audit_path}"
                                )

    def test_base64_robustness(self):
        """Test extraction robustness against format changes and whitespaces in strike.js."""
        def run_extraction_on_content(js_content):
            match = re.search(r"strike\.src\s*=\s*([\"\'])data:image/png;base64,(.*?)\1\s*(?:\+\s*(.+?))?;", js_content, re.DOTALL)
            if not match:
                match = re.search(r"strike\.src\s*=\s*([\"\'])data:image/png;base64,\1\s*\+\s*(.+?);", js_content, re.DOTALL)
                if not match:
                    raise ValueError("Could not find strike.src assignment with base64 data URL prefix in strike.js")
                assignment = match.group(2)
            else:
                g2 = match.group(2)
                g3 = match.group(3)
                if g3 is None:
                    assignment = f'"{g2}"'
                else:
                    assignment = f'"{g2}" + ' + g3

            comment_pattern = re.compile(r'("(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\'|/\*.*?\*/|//[^\n]*)', re.DOTALL)
            def replacer(m):
                s = m.group(0)
                if s.startswith('/') or s.startswith('//'):
                    return ''
                return s
            assignment = comment_pattern.sub(replacer, assignment)
            strings = re.findall(r"([\"\'])(.*?)\1", assignment)
            base64_str = "".join(s[1] for s in strings)
            return base64.b64decode(base64_str)

        with open(self.strike_js_path, "r") as f:
            original_content = f.read()

        # Test case: unexpected whitespaces and newlines
        modified_content_1 = original_content.replace('"+', '"  +\n  ')
        modified_content_1 = modified_content_1.replace('"\n"', '"\n\n\n"')
        try:
            decoded = run_extraction_on_content(modified_content_1)
            with open(self.strike_png_path, "rb") as f:
                original_png_bytes = f.read()
            self.assertEqual(decoded, original_png_bytes, "Whitespace modification broke base64 decoding")
        except Exception as e:
            self.fail(f"Failed to decode with modified whitespaces: {e}")

if __name__ == "__main__":
    unittest.main()
