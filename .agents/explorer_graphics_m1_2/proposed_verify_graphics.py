#!/usr/bin/env python3
"""
verify_graphics.py
Milestone 1 Verification Tool for Dandy Dungeon Graphics Conversion Pipeline.

This script:
1. Parses `src/tiles.c` to extract the compiled 512 bytes of GBDK 2bpp tile data.
2. Decodes the 2bpp tile bytes back into 8x8 color index grids.
3. Renders the decoded tiles into Pillow images using GameBoy background and sprite palettes.
4. Loads the original 256x32 sprite sheet from `web/strike_original.png` and slices it into 32 reference 16x16 tiles.
5. Upscales both original and compiled tiles using nearest-neighbor interpolation.
6. Arranges the original 16x16 tiles (upscaled 8x) and compiled 8x8 tiles (upscaled 8x) side-by-side in a professional 2D audit grid.
7. Saves the output as `web/graphics_audit.png` for visual verification.
"""

import os
import re
import sys
from PIL import Image, ImageDraw

# Tile names for labeling in the audit sheet
TILE_NAMES = {
    0: "SPACE",
    1: "WALL",
    2: "DOOR",
    3: "STAIRS UP",
    4: "STAIRS DOWN",
    5: "KEY",
    6: "FOOD",
    7: "MONEY",
    8: "BOMB",
    9: "GHOST (M1)",
    10: "DEMON (M2)",
    11: "GOLEM (M3)",
    12: "HEART",
    13: "NEST L1",
    14: "NEST L2",
    15: "NEST L3",
    16: "ARROW DOWN",
    17: "ARROW UP",
    18: "ARROW LEFT",
    19: "ARROW RIGHT",
    20: "PADDING 20",
    21: "PADDING 21",
    22: "PADDING 22",
    23: "PADDING 23",
    24: "HERO DOWN",
    25: "HERO UP",
    26: "HERO LEFT",
    27: "HERO RIGHT",
    28: "PADDING 28",
    29: "PADDING 29",
    30: "PADDING 30",
    31: "PADDING 31",
}

def load_compiled_tiles(tiles_c_path):
    """Parses tiles.c to extract the 512 bytes of GBDK tile data."""
    if not os.path.exists(tiles_c_path):
        print(f"Error: Compiled tiles file not found at: {tiles_c_path}")
        sys.exit(1)

    print(f"Reading compiled tile data from {tiles_c_path}...")
    with open(tiles_c_path, "r") as f:
        content = f.read()

    # Locate the dandy_tiles array definition
    match = re.search(r"const\s+unsigned\s+char\s+dandy_tiles\[\]\s*=\s*\{(.*?)\};", content, re.DOTALL)
    if not match:
        raise ValueError("Could not find 'dandy_tiles' array definition in tiles.c")

    array_content = match.group(1)
    # Find all hex values (e.g. 0x00, 0x7F)
    hex_values = re.findall(r"0[xX][0-9a-fA-F]{2}", array_content)
    tile_bytes = [int(val, 16) for val in hex_values]

    if len(tile_bytes) != 512:
        raise ValueError(f"Expected exactly 512 bytes for 32 tiles (32 * 16), but parsed {len(tile_bytes)} bytes.")

    print("Successfully parsed 512 bytes of compiled tile data.")
    return tile_bytes

def decode_2bpp_tile(tile_bytes):
    """Decodes 16 bytes of GameBoy 2bpp tile data into an 8x8 color index grid."""
    pixels = []
    for row in range(8):
        low_byte = tile_bytes[row * 2]
        high_byte = tile_bytes[row * 2 + 1]
        row_pixels = []
        for col in range(8):
            bit_shift = 7 - col
            bit0 = (low_byte >> bit_shift) & 1
            bit1 = (high_byte >> bit_shift) & 1
            color_idx = (bit1 << 1) | bit0
            row_pixels.append(color_idx)
        pixels.append(row_pixels)
    return pixels

def render_compiled_tile(pixels, tile_idx):
    """Renders an 8x8 color index grid to a PIL RGBA image using the correct palette."""
    # Determine if it's a sprite or background tile
    # Sprites: 16..19 (arrows), 24..27 (player/hero)
    is_sprite = (16 <= tile_idx <= 19) or (24 <= tile_idx <= 27)

    img = Image.new("RGBA", (8, 8))
    for y in range(8):
        for x in range(8):
            color_idx = pixels[y][x]
            if is_sprite:
                # Sprite Palette (OBP0/OBP1):
                # 0 -> Transparent/Black (mapped to black for visual comparison)
                # 1 -> Bright White
                # 2 -> Dark Gray
                # 3 -> Solid Black
                if color_idx == 0:
                    color = (0, 0, 0, 255)
                elif color_idx == 1:
                    color = (255, 255, 255, 255)
                elif color_idx == 2:
                    color = (100, 100, 100, 255)
                else: # 3
                    color = (0, 0, 0, 255)
            else:
                # Background Palette (BGP):
                # 0 -> Solid Black
                # 1 -> Dark Gray
                # 2 -> Light Gray
                # 3 -> Bright White
                if color_idx == 0:
                    color = (0, 0, 0, 255)
                elif color_idx == 1:
                    color = (100, 100, 100, 255)
                elif color_idx == 2:
                    color = (180, 180, 180, 255)
                else: # 3
                    color = (255, 255, 255, 255)
            img.putpixel((x, y), color)
    return img

def slice_original_sprites(png_path):
    """Loads and slices strike_original.png into 32 reference 16x16 PIL images."""
    if not os.path.exists(png_path):
        print(f"Error: Reference spritesheet not found at: {png_path}")
        print("Please run extract_sprites.py first to extract it from strike.js.")
        sys.exit(1)

    print(f"Loading reference spritesheet from {png_path}...")
    img = Image.open(png_path).convert("RGBA")
    width, height = img.size

    if width != 256 or height != 32:
        print(f"Warning: Expected spritesheet dimensions 256x32, got {width}x{height}.")

    cols = width // 16
    rows = height // 16
    
    original_tiles = []
    for r in range(rows):
        for c in range(cols):
            left = c * 16
            top = r * 16
            right = left + 16
            bottom = top + 16
            tile = img.crop((left, top, right, bottom))
            original_tiles.append(tile)

    print(f"Successfully sliced {len(original_tiles)} reference 16x16 tiles.")
    return original_tiles

def main():
    # Setup paths relative to script location
    tools_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.normpath(os.path.join(tools_dir, ".."))
    
    tiles_c_path = os.path.join(project_dir, "src", "tiles.c")
    original_png_path = os.path.join(project_dir, "web", "strike_original.png")
    audit_png_path = os.path.join(project_dir, "web", "graphics_audit.png")

    # 1. Parse tiles.c
    compiled_bytes = load_compiled_tiles(tiles_c_path)
    
    # 2. Slice original spritesheet
    original_tiles = slice_original_sprites(original_png_path)
    
    # Grid Dimensions: 8 columns, 4 rows (32 cells total)
    # Cell size: 200 width, 160 height
    cell_w, cell_h = 200, 160
    grid_cols, grid_rows = 8, 4
    
    audit_w = grid_cols * cell_w
    audit_h = grid_rows * cell_h
    
    # Create the master audit image
    audit_img = Image.new("RGBA", (audit_w, audit_h), (20, 20, 20, 255))
    draw = ImageDraw.Draw(audit_img)
    
    print("Generating visual audit grid...")
    
    for idx in range(32):
        col = idx % grid_cols
        row = idx // grid_cols
        
        # Calculate cell bounds
        cell_x = col * cell_w
        cell_y = row * cell_h
        
        # Draw cell background border
        draw.rectangle(
            [cell_x, cell_y, cell_x + cell_w - 1, cell_y + cell_h - 1],
            outline=(50, 50, 50, 255),
            width=1
        )
        
        # Draw label: "Tile # - Name"
        label = f"Tile {idx}: {TILE_NAMES.get(idx, 'UNKNOWN')}"
        draw.text((cell_x + 10, cell_y + 8), label, fill=(230, 230, 230, 255))
        
        # --- Left Side: Original 16x16 upscaled 8x to 128x128 ---
        if idx < len(original_tiles):
            orig_tile = original_tiles[idx]
            orig_upscaled = orig_tile.resize((128, 128), Image.NEAREST)
            audit_img.paste(orig_upscaled, (cell_x + 10, cell_y + 24))
            draw.text((cell_x + 10, cell_y + 144), "16x16 (Orig)", fill=(150, 150, 150, 255))
            
        # --- Right Side: Compiled 8x8 upscaled 8x to 64x64 ---
        tile_offset = idx * 16
        tile_bytes = compiled_bytes[tile_offset:tile_offset+16]
        decoded_pixels = decode_2bpp_tile(tile_bytes)
        compiled_tile = render_compiled_tile(decoded_pixels, idx)
        compiled_upscaled = compiled_tile.resize((64, 64), Image.NEAREST)
        
        # Paste centered vertically relative to the 128x128 original tile
        # Original starts at y + 24. Center is y + 24 + (128 - 64) // 2 = y + 56
        audit_img.paste(compiled_upscaled, (cell_x + 144, cell_y + 56))
        draw.text((cell_x + 144, cell_y + 124), "8x8 (GB)", fill=(150, 150, 150, 255))
        
    print(f"Saving visual audit sheet to {audit_png_path}...")
    audit_img.save(audit_png_path)
    print("Verification sheet generated successfully!")

if __name__ == "__main__":
    main()
