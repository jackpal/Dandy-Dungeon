import os
import re
import sys
from PIL import Image

def parse_tiles_c(filepath):
    with open(filepath, 'r') as f:
        content = f.read()
    # Find the array body
    match = re.search(r'const unsigned char dandy_tiles\[\]\s*=\s*\{([^}]+)\};', content)
    if not match:
        raise ValueError("Could not find dandy_tiles array in tiles.c")
    
    body = match.group(1)
    # Extract all hex values
    hex_vals = re.findall(r'0x[0-9A-Fa-f]{2}', body)
    bytes_data = [int(val, 16) for val in hex_vals]
    return bytes_data

def decode_2bpp_tile(tile_bytes):
    pixels = []
    for row_idx in range(8):
        byte1 = tile_bytes[row_idx * 2]
        byte2 = tile_bytes[row_idx * 2 + 1]
        row_pixels = []
        for col_idx in range(8):
            bit_shift = 7 - col_idx
            lsb = (byte1 >> bit_shift) & 1
            msb = (byte2 >> bit_shift) & 1
            color_idx = (msb << 1) | lsb
            row_pixels.append(color_idx)
        pixels.extend(row_pixels)
    return pixels

def main():
    tiles_c_path = '/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb/src/tiles.c'
    reference_png_path = '/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/.agents/explorer_m1_3/strike_decoded.png'
    output_audit_path = '/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/.agents/explorer_m1_3/graphics_audit.png'
    
    if not os.path.exists(tiles_c_path):
        print(f"Error: {tiles_c_path} does not exist.")
        return
    if not os.path.exists(reference_png_path):
        print(f"Error: {reference_png_path} does not exist.")
        return

    # 1. Parse tiles.c
    print("Parsing tiles.c...")
    tile_bytes_all = parse_tiles_c(tiles_c_path)
    print(f"Total bytes parsed: {len(tile_bytes_all)}")
    num_tiles = len(tile_bytes_all) // 16
    print(f"Number of tiles: {num_tiles}")

    # 2. Decode GBDK tiles
    decoded_tiles = []
    for t_idx in range(num_tiles):
        tile_bytes = tile_bytes_all[t_idx * 16 : (t_idx + 1) * 16]
        decoded_tiles.append(decode_2bpp_tile(tile_bytes))

    # 3. Load reference PNG
    print("Loading reference PNG...")
    ref_img = Image.open(reference_png_path).convert('RGBA')
    ref_w, ref_h = ref_img.size
    print(f"Reference dimensions: {ref_w}x{ref_h}")
    
    # Slice reference PNG into 16x16 tiles
    # Since image is 256x32, and tiles are 16x16, we have 16 columns and 2 rows = 32 tiles total
    ref_tiles = []
    for row in range(2):
        for col in range(16):
            box = (col * 16, row * 16, (col + 1) * 16, (row + 1) * 16)
            ref_tiles.append(ref_img.crop(box))

    # 4. Create Audit Sheet
    # Layout: 32 rows.
    # Each row contains:
    # - Reference tile upscaled 8x (128x128)
    # - Spacing (16 pixels)
    # - Decoded tile upscaled 8x (64x64) or upscaled 16x (128x128) for easy visual match.
    # Let's upscale GBDK tiles 8x (64x64) as requested, but place them in a 128x128 cell for alignment.
    # Total width of audit sheet: 128 + 16 + 128 = 272 pixels.
    # Total height of audit sheet: 32 * 128 = 4096 pixels.
    
    audit_img = Image.new('RGBA', (272, 32 * 128), color=(30, 30, 30, 255))
    
    # Palette mapping for GBDK 2bpp color indices (0..3) to grayscale
    # 0 -> Black, 1 -> Dark Gray, 2 -> Light Gray, 3 -> White
    palette = [
        (0, 0, 0, 255),
        (85, 85, 85, 255),
        (170, 170, 170, 255),
        (255, 255, 255, 255)
    ]

    for t_idx in range(32):
        y_offset = t_idx * 128
        
        # A. Reference Tile
        ref_tile = ref_tiles[t_idx]
        ref_upscaled = ref_tile.resize((128, 128), Image.NEAREST)
        audit_img.paste(ref_upscaled, (0, y_offset))
        
        # B. Decoded Compiled Tile
        # Create an 8x8 image from the decoded pixels
        decoded_pixels = decoded_tiles[t_idx]
        gb_tile_img = Image.new('RGBA', (8, 8))
        gb_tile_img.putdata([palette[color_idx] for color_idx in decoded_pixels])
        
        # Upscale 8x as requested (64x64)
        gb_upscaled = gb_tile_img.resize((64, 64), Image.NEAREST)
        
        # Paste it centered vertically in the 128x128 right-hand slot
        # Right slot starts at x=144, y=y_offset. Centering 64x64 inside 128x128:
        # x_start = 144 + (128 - 64) // 2 = 144 + 32 = 176
        # y_start = y_offset + (128 - 64) // 2 = y_offset + 32
        audit_img.paste(gb_upscaled, (176, y_offset + 32))

    # Save audit sheet
    audit_img.save(output_audit_path)
    print(f"Audit sheet saved to {output_audit_path}")

if __name__ == '__main__':
    main()
