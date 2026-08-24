#!/usr/bin/env python3
"""
verify_graphics.py
Milestone 1 Verification Script for Dandy Dungeon Graphics Conversion Pipeline.
Decodes compiled 2bpp tiles from src/tiles.c and compares them side-by-side
with the original 16x16 sprites in strike_original.png, outputting a visual audit sheet.
"""

import os
import re
import sys
from PIL import Image, ImageDraw, ImageFont

# Tile Names mapping for readability
TILE_NAMES = [
    "SPACE", "WALL", "DOOR", "STAIRS_UP", "STAIRS_DOWN", "KEY", "FOOD", "GOLD",
    "BOMB", "MONSTER1", "MONSTER2", "MONSTER3", "HEART", "NEST1", "NEST2", "NEST3",
    "ARROW_D", "ARROW_U", "ARROW_L", "ARROW_R", "PADD_20", "PADD_21", "PADD_22", "PADD_23",
    "PLAYER_D", "PLAYER_U", "PLAYER_L", "PLAYER_R", "PADD_28", "PADD_29", "PADD_30", "PADD_31"
]

# Hardware color palettes from src/main.c
BGP = [
    (0, 0, 0),        # 0: Black (floor)
    (85, 85, 85),     # 1: Dark Gray (walls)
    (170, 170, 170),  # 2: Light Gray (items)
    (255, 255, 255)   # 3: White (text)
]

OBP = [
    None,             # 0: Transparent (background checkerboard shows through)
    (255, 255, 255),  # 1: White (body)
    (85, 85, 85),     # 2: Dark Gray (details)
    (0, 0, 0)         # 3: Black (outlines)
]

def is_sprite_tile(tile_idx):
    """Monsters (9..11), Arrows (16..23), and Players (24..31) are sprites with transparency."""
    return (9 <= tile_idx <= 11) or (16 <= tile_idx <= 31)

def parse_tiles_c(tiles_c_path):
    """Parses tiles.c to extract the 512 bytes of dandy_tiles."""
    with open(tiles_c_path, "r") as f:
        content = f.read()
    
    # Locate array definition
    array_start = content.find("dandy_tiles")
    if array_start == -1:
        raise ValueError("Could not find 'dandy_tiles' array in tiles.c")
    
    brace_start = content.find("{", array_start)
    if brace_start == -1:
        raise ValueError("Could not find opening brace '{' of dandy_tiles")
        
    brace_end = content.find("}", brace_start)
    if brace_end == -1:
        raise ValueError("Could not find closing brace '}' of dandy_tiles")
        
    array_data = content[brace_start+1:brace_end]
    
    # Extract hex or decimal literals
    hex_values = re.findall(r'0x[0-9A-Fa-f]{2}', array_data)
    if not hex_values:
        hex_values = re.findall(r'\b\d+\b', array_data)
        
    bytes_list = [int(val, 0) for val in hex_values]
    return bytes_list

def decode_gb_tile(tile_bytes):
    """Decodes 16 bytes of GameBoy 2bpp data to an 8x8 list of color indices (0..3)."""
    pixels = []
    for r in range(8):
        low_byte = tile_bytes[r * 2]
        high_byte = tile_bytes[r * 2 + 1]
        row_pixels = []
        for c in range(8):
            bit_idx = 7 - c
            bit0 = (low_byte >> bit_idx) & 1
            bit1 = (high_byte >> bit_idx) & 1
            color_idx = (bit1 << 1) | bit0
            row_pixels.append(color_idx)
        pixels.append(row_pixels)
    return pixels

def create_checkerboard(width, height, box_size=16):
    """Generates a soft checkered pattern for visualizing sprite transparency."""
    img = Image.new("RGB", (width, height))
    pixels = img.load()
    for y in range(height):
        for x in range(width):
            if ((x // box_size) + (y // box_size)) % 2 == 0:
                pixels[x, y] = (230, 235, 240)  # Very light blue-gray
            else:
                pixels[x, y] = (255, 255, 255)  # Pure white
    return img

def render_gb_tile(tile_pixels, tile_idx):
    """Renders decoded 8x8 tile pixels into a 128x128 RGB image using the correct palette."""
    if is_sprite_tile(tile_idx):
        img = create_checkerboard(128, 128, box_size=16)
        palette = OBP
    else:
        img = Image.new("RGB", (128, 128), (0, 0, 0)) # Background tiles default to black
        palette = BGP
        
    pixels = img.load()
    for y in range(8):
        for x in range(8):
            color_idx = tile_pixels[y][x]
            color = palette[color_idx]
            if color is not None:
                # Upscale 16x (8x8 -> 128x128)
                for dy in range(16):
                    for dx in range(16):
                        pixels[x * 16 + dx, y * 16 + dy] = color
    return img

def extract_original_tile(original_img, tile_idx):
    """Extracts a 16x16 tile from the 256x32 sheet and upscales it 8x to 128x128."""
    row = tile_idx // 16
    col = tile_idx % 16
    
    x1 = col * 16
    y1 = row * 16
    x2 = x1 + 16
    y2 = y1 + 16
    
    tile_img = original_img.crop((x1, y1, x2, y2))
    return tile_img.resize((128, 128), Image.NEAREST)

def main():
    # Setup paths relative to script location
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Assuming we are in tools/ or our working directory, let's make it robust
    # We will search for dandy-gb root directory
    dandy_gb_dir = None
    
    # Walk up to find dandy-gb root
    curr = script_dir
    while curr != os.path.dirname(curr):
        if os.path.exists(os.path.join(curr, "src/tiles.c")) and os.path.exists(os.path.join(curr, "web/strike_original.png")):
            dandy_gb_dir = curr
            break
        curr = os.path.dirname(curr)
        
    if not dandy_gb_dir:
        # Fallbacks for specific agent directories
        possible_roots = [
            os.path.normpath(os.path.join(script_dir, "../../dandy-gb")),
            os.path.normpath(os.path.join(script_dir, "../dandy-gb")),
            "/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb"
        ]
        for root in possible_roots:
            if os.path.exists(os.path.join(root, "src/tiles.c")):
                dandy_gb_dir = root
                break
                
    if not dandy_gb_dir or not os.path.exists(dandy_gb_dir):
        print("Error: Could not find dandy-gb directory containing src/tiles.c and web/strike_original.png")
        sys.exit(1)
        
    tiles_c_path = os.path.join(dandy_gb_dir, "src/tiles.c")
    original_png_path = os.path.join(dandy_gb_dir, "web/strike_original.png")
    output_png_path = os.path.join(dandy_gb_dir, "tools/graphics_audit.png")
    
    print(f"Loading files:\n  tiles.c: {tiles_c_path}\n  original: {original_png_path}")
    
    # 1. Parse tiles.c
    bytes_list = parse_tiles_c(tiles_c_path)
    if len(bytes_list) != 512:
        print(f"Error: Parse failed, expected 512 bytes, got {len(bytes_list)} bytes.")
        sys.exit(1)
        
    # 2. Load original image
    original_img = Image.open(original_png_path).convert("RGB")
    if original_img.size != (256, 32):
        print(f"Error: Original image must be 256x32 pixels, got {original_img.size}")
        sys.exit(1)
        
    # 3. Create grid image (8 columns, 4 rows)
    cols = 8
    rows = 4
    cell_w = 280
    cell_h = 160
    
    grid_img = Image.new("RGB", (cols * cell_w, rows * cell_h), (240, 240, 240))
    draw = ImageDraw.Draw(grid_img)
    
    # Try to load a clean font, fallback to default
    font = None
    font_paths = ["DejaVuSans.ttf", "LiberationSans-Regular.ttf", "Ubuntu-R.ttf"]
    for fp in font_paths:
        try:
            font = ImageFont.truetype(fp, 12)
            break
        except IOError:
            continue
    if font is None:
        font = ImageFont.load_default()
        
    # 4. Process all 32 tiles
    for i in range(32):
        col_idx = i % cols
        row_idx = i // cols
        
        cell_x = col_idx * cell_w
        cell_y = row_idx * cell_h
        
        # Draw cell background/border
        draw.rectangle(
            [cell_x, cell_y, cell_x + cell_w - 1, cell_y + cell_h - 1],
            outline=(200, 200, 200),
            fill=(245, 245, 245)
        )
        
        # Draw label
        name = TILE_NAMES[i]
        label = f"{i:02d}: {name}"
        draw.text((cell_x + 10, cell_y + 5), label, fill=(0, 0, 0), font=font)
        
        # Extract and draw original tile (upscaled 8x to 128x128)
        orig_tile = extract_original_tile(original_img, i)
        grid_img.paste(orig_tile, (cell_x + 10, cell_y + 25))
        draw.rectangle([cell_x + 10, cell_y + 25, cell_x + 10 + 127, cell_y + 25 + 127], outline=(0, 0, 0))
        
        # Decode and render GBDK tile (upscaled 16x to 128x128)
        tile_start = i * 16
        tile_bytes = bytes_list[tile_start:tile_start+16]
        tile_pixels = decode_gb_tile(tile_bytes)
        gb_tile = render_gb_tile(tile_pixels, i)
        
        grid_img.paste(gb_tile, (cell_x + 142, cell_y + 25))
        draw.rectangle([cell_x + 142, cell_y + 25, cell_x + 142 + 127, cell_y + 25 + 127], outline=(0, 0, 0))
        
    print(f"Saving visual audit sheet to {output_png_path}...")
    grid_img.save(output_png_path)
    print("Visual audit sheet generation complete! Audit: SUCCESS.")

if __name__ == "__main__":
    main()
