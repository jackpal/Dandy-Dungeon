#!/usr/bin/env python3
"""
verify_graphics.py
Programmatic verification tool for the Dandy Dungeon GameBoy graphics pipeline.
Supports Classic DMG and Atmospheric palettes, sprite transparency visualization,
and command-line configuration of outputs and palettes.
"""

import os
import re
import argparse
import sys
from PIL import Image

# Explicit mapping from GBDK C tile index (0..31) to original JS sprite sheet index (0..31)
# This resolves the Visual Audit Mismatch caused by asset reordering in the Game Boy port.
GB_TO_JS_MAPPING = {
    0: 0,    # Space
    1: 1,    # Wall
    2: 2,    # Door
    3: 3,    # Stairs Up
    4: 5,    # Stairs Down (GB 4 -> JS 5)
    5: 4,    # Key (GB 5 -> JS 4)
    6: 7,    # Food (GB 6 -> JS 7)
    7: 6,    # Money/Gold (GB 7 -> JS 6)
    8: 8,    # Bomb (GB 8 -> JS 8)
    9: 9,    # Monster 1
    10: 10,  # Monster 2
    11: 11,  # Monster 3 (Golem maps to JS index 11 Heart monster)
    12: 12,  # Heart (Flask maps to JS index 12 Skull monster)
    13: 13,  # Generator 1
    14: 14,  # Generator 2
    15: 15,  # Generator 3
    16: 23,  # Arrow Down (GB 16 -> JS 23)
    17: 19,  # Arrow Up (GB 17 -> JS 19)
    18: 17,  # Arrow Left (GB 18 -> JS 17)
    19: 21,  # Arrow Right (GB 19 -> JS 21)
    20: 20,  # Padding/Unused
    21: 21,
    22: 22,
    23: 23,
    24: 24,  # Player Down
    25: 25,  # Player Up
    26: 26,  # Player Left
    27: 27,  # Player Right
    28: 28,  # Padding/Unused
    29: 29,
    30: 30,
    31: 31
}

def parse_tiles_c(tiles_c_path):
    """
    Parses tiles.c to extract the dandy_tiles 2bpp binary data.
    Robustly strips comments and handles hex/decimal values and array sizes.
    """
    if not os.path.exists(tiles_c_path):
        raise FileNotFoundError(f"Source tiles definition file not found at: {tiles_c_path}")
        
    print(f"Reading tiles definition from {tiles_c_path}...")
    with open(tiles_c_path, "r") as f:
        content = f.read()

    # Strip multi-line comments
    content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
    # Strip single-line comments
    content = re.sub(r'//.*?\n', '\n', content)

    # Match the dandy_tiles array content (allowing optional size in brackets)
    match = re.search(r"const\s+unsigned\s+char\s+dandy_tiles\s*(?:\[[^\]]*\])?\s*=\s*\{([^}]+)\}", content, re.DOTALL)
    if not match:
        raise ValueError("Could not find 'dandy_tiles' array in tiles.c")

    array_content = match.group(1)
    # Find all hex and decimal values
    num_strings = re.findall(r"0[xX][0-9a-fA-F]+|\d+", array_content)
    if len(num_strings) != 512:
        raise ValueError(f"Expected exactly 512 values (32 tiles * 16 bytes), but found {len(num_strings)}")

    bytes_list = []
    for s in num_strings:
        if s.lower().startswith('0x'):
            bytes_list.append(int(s, 16))
        else:
            bytes_list.append(int(s, 10))

    return bytes(bytes_list)

def decode_gb_tile(tile_bytes, is_sprite=False, use_dark_floor=False):
    """
    Decodes a 16-byte Game Boy 2bpp tile into an 8x8 RGBA Image.
    For sprites, Color 0 is mapped to transparent (0, 0, 0, 0).
    For background, maps to the active palette (Classic DMG or Atmospheric).
    """
    if is_sprite:
        # Sprite palette (OBP0/1 = 0xE0):
        # Index 0 -> Transparent
        # Index 1 -> White (255, 255, 255)
        # Index 2 -> Dark Gray (85, 85, 85)
        # Index 3 -> Black (0, 0, 0)
        colors = [
            (0, 0, 0, 0),
            (255, 255, 255, 255),
            (85, 85, 85, 255),
            (0, 0, 0, 255)
        ]
    else:
        if use_dark_floor:
            # Atmospheric (Dark Floor) Palette:
            # Color 0 -> Black, 1 -> Dark Gray, 2 -> Light Gray, 3 -> White
            colors = [
                (0, 0, 0, 255),
                (85, 85, 85, 255),
                (170, 170, 170, 255),
                (255, 255, 255, 255)
            ]
        else:
            # Classic DMG (Light Floor) Palette (Default):
            # Color 0 -> White, 1 -> Light Gray, 2 -> Dark Gray, 3 -> Black
            colors = [
                (255, 255, 255, 255),
                (170, 170, 170, 255),
                (85, 85, 85, 255),
                (0, 0, 0, 255)
            ]

    img = Image.new("RGBA", (8, 8))
    pixels = img.load()

    for y in range(8):
        byte1 = tile_bytes[2 * y]
        byte2 = tile_bytes[2 * y + 1]
        for x in range(8):
            bit_index = 7 - x
            low_bit = (byte1 >> bit_index) & 1
            high_bit = (byte2 >> bit_index) & 1
            color_index = (high_bit << 1) | low_bit
            pixels[x, y] = colors[color_index]

    return img

def create_checkerboard(width=128, height=128, check_size=16, color1=200, color2=220):
    """
    Generates an RGBA checkerboard image for representing transparency with crisp edges.
    """
    cols = width // check_size
    rows = height // check_size
    small_img = Image.new("RGBA", (cols, rows))
    pixels = small_img.load()
    for y in range(rows):
        for x in range(cols):
            val = color1 if (x + y) % 2 == 0 else color2
            pixels[x, y] = (val, val, val, 255)
            
    try:
        nn_filter = Image.Resampling.NEAREST
    except AttributeError:
        nn_filter = Image.NEAREST
        
    return small_img.resize((width, height), nn_filter)

def main(argv=None):
    """Main execution block supporting CLI flags and unit test invocation."""
    parser = argparse.ArgumentParser(description="Generate graphics verification audit sheet for Dandy Dungeon GameBoy port.")
    parser.add_argument(
        "--dark-floor",
        action="store_true",
        help="Use the Atmospheric (Dark Floor) palette for background tiles."
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        help="Custom path to save the generated audit PNG image."
    )
    parser.add_argument(
        "--output-png",
        type=str,
        help="Alias for --output."
    )
    
    args = parser.parse_args(argv)
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    tiles_c_path = os.path.normpath(os.path.join(current_dir, "../src/tiles.c"))
    strike_png_path = os.path.normpath(os.path.join(current_dir, "../teamwork_graphics/strike_original.png"))
    
    output_path = args.output or args.output_png
    if not output_path:
        filename = "graphics_audit_dark.png" if args.dark_floor else "graphics_audit.png"
        output_path = os.path.normpath(os.path.join(current_dir, f"../teamwork_graphics/{filename}"))

    # Verify original sprite sheet exists
    if not os.path.exists(strike_png_path):
        raise FileNotFoundError(f"Original sprite sheet not found at {strike_png_path}. Please run extract_sprites.py first.")

    # 1. Parse tiles
    tiles_bytes = parse_tiles_c(tiles_c_path)

    # 2. Load original spritesheet
    print(f"Loading original sprite sheet from {strike_png_path}...")
    original_sheet = Image.open(strike_png_path)
    if original_sheet.size != (256, 32):
        raise ValueError(f"Expected original sprite sheet dimensions 256x32, but got {original_sheet.size}")

    # 3. Create audit grid: 4 columns, 8 rows of comparison blocks.
    grid_cols = 4
    grid_rows = 8
    cell_w = 256
    cell_h = 128
    
    # Neutral dark-gray grid background to separate cells and provide professional contrast
    audit_img = Image.new("RGBA", (grid_cols * cell_w, grid_rows * cell_h), (80, 80, 80, 255))

    try:
        nn_filter = Image.Resampling.NEAREST
    except AttributeError:
        nn_filter = Image.NEAREST

    # Category sets
    bg_indices = set(list(range(9)) + list(range(12, 16)) + list(range(20, 24)) + list(range(28, 32)))
    sprite_indices = set(list(range(9, 12)) + list(range(16, 20)) + list(range(24, 28)))

    # Pre-generate checkerboard pattern for sprites
    checkerboard = create_checkerboard(128, 128, check_size=16, color1=200, color2=220)

    print("Stitching side-by-side comparison sheet...")
    for i in range(32):
        col = i % grid_cols
        row = i // grid_cols
        cell_x = col * cell_w
        cell_y = row * cell_h

        # A. Crop original 16x16 sprite using the explicit layout mapping dictionary
        js_index = GB_TO_JS_MAPPING.get(i, i)
        orig_col = js_index % 16
        orig_row = js_index // 16
        orig_box = (orig_col * 16, orig_row * 16, (orig_col + 1) * 16, (orig_row + 1) * 16)
        orig_tile = original_sheet.crop(orig_box)
        orig_upscaled = orig_tile.resize((128, 128), nn_filter)
        orig_rgba = orig_upscaled.convert("RGBA")

        # B. Decode Game Boy 8x8 tile
        tile_offset = i * 16
        tile_data = tiles_bytes[tile_offset:tile_offset+16]
        
        is_sprite = i in sprite_indices
        gb_tile = decode_gb_tile(tile_data, is_sprite=is_sprite, use_dark_floor=args.dark_floor)
        gb_upscaled = gb_tile.resize((128, 128), nn_filter)

        # C. Draw onto audit sheet
        if is_sprite:
            # Sprite transparency audit: use checkerboard backgrounds
            audit_img.paste(checkerboard, (cell_x, cell_y))
            audit_img.paste(checkerboard, (cell_x + 128, cell_y))
            
            # Alpha paste original sprite and GB tile over checkerboard
            audit_img.paste(orig_rgba, (cell_x, cell_y), orig_rgba)
            audit_img.paste(gb_upscaled, (cell_x + 128, cell_y), gb_upscaled)
        else:
            # Background tile audit: use the active mode's floor color (Color 0) as solid background
            bg_color = (0, 0, 0, 255) if args.dark_floor else (255, 255, 255, 255)
            solid_bg = Image.new("RGBA", (128, 128), bg_color)
            
            audit_img.paste(solid_bg, (cell_x, cell_y))
            audit_img.paste(solid_bg, (cell_x + 128, cell_y))
            
            # Paste original sprite and GB tile
            audit_img.paste(orig_rgba, (cell_x, cell_y), orig_rgba)
            audit_img.paste(gb_upscaled, (cell_x + 128, cell_y))

    # Convert to RGB before saving (audit image is fully opaque RGB)
    final_rgb_img = audit_img.convert("RGB")
    
    # Ensure target directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    print(f"Saving audit sheet to {output_path}...")
    final_rgb_img.save(output_path)
    print("Verification and audit sheet generation complete!")

if __name__ == "__main__":
    main()
