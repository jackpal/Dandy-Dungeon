#!/usr/bin/env python3
"""
verify_graphics.py
Milestone 1/2 Graphics Verification Tool for Dandy Dungeon.

This script:
1. Extracts the base64-encoded sprite sheet from dandy-js/strike.js and saves it
   as a reference image strike_original.png (256x32 pixels, 32 sprites).
2. Parses dandy-gb/src/tiles.c to extract GBDK 2bpp tile byte arrays.
3. Decodes the 2bpp bytes back into 8x8 pixel grids.
4. Slices strike_original.png into 32 sprites of 16x16 pixels.
5. Generates a side-by-side visual comparison sheet graphics_audit.png,
   where each 16x16 reference sprite is upscaled 8x (to 128x128) and placed
   next to its corresponding 8x8 compiled GameBoy tile upscaled 16x (to 128x128).
"""

import os
import re
import base64
import struct
from PIL import Image, ImageDraw

# Paths
JS_STRIKE_PATH = "/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-js/strike.js"
C_TILES_PATH = "/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb/src/tiles.c"
OUTPUT_DIR = "/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb/teamwork_graphics"
REFERENCE_PNG_PATH = os.path.join(OUTPUT_DIR, "strike_original.png")
AUDIT_PNG_PATH = os.path.join(OUTPUT_DIR, "graphics_audit.png")

# Palette for GBDK 2bpp decoding (Grayscale)
PALETTE = {
    0: (0, 0, 0, 255),         # Color 0: Black
    1: (85, 85, 85, 255),      # Color 1: Dark Gray
    2: (170, 170, 170, 255),    # Color 2: Light Gray
    3: (255, 255, 255, 255),    # Color 3: White
}

def extract_reference_png():
    """Extracts base64 PNG from strike.js and saves it to disk."""
    print(f"Reading base64 sprite sheet from {JS_STRIKE_PATH}...")
    with open(JS_STRIKE_PATH, 'r') as f:
        content = f.read()

    # Find all double-quoted strings
    matches = re.findall(r'"([^"]*)"', content)
    base64_parts = []
    for m in matches:
        if m.startswith('data:image/png;base64,'):
            base64_parts.append(m.replace('data:image/png;base64,', ''))
        else:
            base64_parts.append(m)

    base64_str = "".join(base64_parts)
    img_data = base64.b64decode(base64_str)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(REFERENCE_PNG_PATH, 'wb') as f:
        f.write(img_data)
    print(f"Saved reference image to {REFERENCE_PNG_PATH}")
    return REFERENCE_PNG_PATH

def parse_tiles_c():
    """Parses tiles.c and extracts the 32 tiles as lists of 16 bytes."""
    print(f"Parsing GBDK tiles from {C_TILES_PATH}...")
    with open(C_TILES_PATH, 'r') as f:
        content = f.read()

    # Find the dandy_tiles array content
    array_match = re.search(r'const\s+unsigned\s+char\s+dandy_tiles\[\]\s*=\s*\{([^}]+)\};', content)
    if not array_match:
        raise ValueError("Could not find dandy_tiles array in tiles.c")

    array_str = array_match.group(1)
    # Extract all hex numbers
    hex_vals = re.findall(r'0x[0-9a-fA-F]{2}', array_str)
    bytes_data = [int(val, 16) for val in hex_vals]

    if len(bytes_data) != 512:
        raise ValueError(f"Expected 512 bytes (32 tiles * 16 bytes), but found {len(bytes_data)} bytes.")

    tiles = []
    for i in range(32):
        tile_bytes = bytes_data[i * 16 : (i + 1) * 16]
        tiles.append(tile_bytes)
    return tiles

def decode_2bpp_tile(tile_bytes):
    """Decodes 16 GBDK 2bpp bytes into an 8x8 PIL Image."""
    img = Image.new('RGBA', (8, 8))
    pixels = img.load()

    for r in range(8):
        low = tile_bytes[2 * r]
        high = tile_bytes[2 * r + 1]
        for c in range(8):
            bit0 = (low >> (7 - c)) & 1
            bit1 = (high >> (7 - c)) & 1
            color_idx = (bit1 << 1) | bit0
            pixels[c, r] = PALETTE[color_idx]
    return img

def main():
    # 1. Extract and save the reference image
    ref_path = extract_reference_png()
    ref_img = Image.open(ref_path)
    print(f"Reference image loaded: {ref_img.size} {ref_img.mode}")

    # 2. Parse tiles.c to get GBDK bytes
    tiles_bytes = parse_tiles_c()

    # 3. Create audit sheet layout
    # Each row in strike_original.png has 16 sprites of 16x16.
    # Total 32 sprites, arranged in a 16x2 grid.
    # We will arrange the audit sheet as a 16x2 grid of blocks.
    # Each block is 258x130 (128x128 original + 1px border + 128x128 compiled + 1px border).
    block_w = 258
    block_h = 130
    grid_cols = 16
    grid_rows = 2

    audit_img = Image.new('RGBA', (grid_cols * block_w + 2, grid_rows * block_h + 2), (30, 30, 30, 255))
    draw = ImageDraw.Draw(audit_img)

    for idx in range(32):
        col_idx = idx % 16
        row_idx = idx // 16

        # Slice the original 16x16 sprite from the reference sheet
        rx = col_idx * 16
        ry = row_idx * 16
        orig_sprite = ref_img.crop((rx, ry, rx + 16, ry + 16))

        # Decode the corresponding compiled GameBoy tile
        comp_tile = decode_2bpp_tile(tiles_bytes[idx])

        # Upscale both to 128x128 using nearest-neighbor
        orig_sprite_scaled = orig_sprite.resize((128, 128), Image.NEAREST)
        comp_tile_scaled = comp_tile.resize((128, 128), Image.NEAREST)

        # Calculate position on the audit sheet
        bx = col_idx * block_w + 1
        by = row_idx * block_h + 1

        # Paste original on the left side of the block
        audit_img.paste(orig_sprite_scaled, (bx + 1, by + 1))
        # Paste compiled on the right side of the block
        audit_img.paste(comp_tile_scaled, (bx + 129, by + 1))

        # Draw borders around the block and between the two tiles
        draw.rectangle([bx, by, bx + block_w - 1, by + block_h - 1], outline=(100, 100, 100, 255), width=1)
        draw.line([bx + 128, by, bx + 128, by + block_h - 1], fill=(100, 100, 100, 255), width=1)

        # Label each block with its Index/Tile ID
        draw.text((bx + 4, by + 4), f"ID: {idx}", fill=(255, 255, 255, 200))

    audit_img.save(AUDIT_PNG_PATH)
    print(f"Successfully generated visual comparison sheet at: {AUDIT_PNG_PATH}")

if __name__ == "__main__":
    main()
