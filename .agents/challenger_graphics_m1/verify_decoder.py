import os
import sys
import re
from PIL import Image

# Add dandy-gb/tools to path so we can import the worker's verify_graphics module
current_dir = os.path.dirname(os.path.abspath(__file__))
tools_dir = os.path.normpath(os.path.join(current_dir, "../../dandy-gb/tools"))
sys.path.append(tools_dir)

try:
    from verify_graphics import decode_gb_tile
except ImportError as e:
    print(f"Error: Could not import decode_gb_tile from verify_graphics.py. path: {tools_dir}")
    sys.exit(1)

def parse_tiles_c_robust(tiles_c_path):
    """
    An independent, robust parser for tiles.c that strips comments and extracts byte values.
    """
    if not os.path.exists(tiles_c_path):
        raise FileNotFoundError(f"tiles.c not found at {tiles_c_path}")
        
    with open(tiles_c_path, "r") as f:
        content = f.read()

    # Strip multi-line comments
    content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
    # Strip single-line comments
    content = re.sub(r'//.*?\n', '\n', content)

    # Find the array assignment: const unsigned char dandy_tiles[] = { ... }
    # Let's match the content inside the braces after dandy_tiles
    match = re.search(r'dandy_tiles\s*(?:\[[^\]]*\])?\s*=\s*\{([^}]+)\}', content)
    if not match:
        raise ValueError("Failed to find dandy_tiles array in tiles.c using robust parser")

    array_body = match.group(1)
    
    # Extract all numbers (supporting hex like 0xAA, 0Xaa, and decimal)
    # Find all sequences of word characters that look like hex or decimal numbers
    num_strings = re.findall(r'0[xX][0-9a-fA-F]+|\d+', array_body)
    
    bytes_list = []
    for s in num_strings:
        if s.lower().startswith('0x'):
            bytes_list.append(int(s, 16))
        else:
            bytes_list.append(int(s, 10))
            
    return bytes(bytes_list)

def decode_tile_independent(tile_bytes):
    """
    Independent implementation of Game Boy 2bpp decoding.
    Decodes 16 bytes into an 8x8 grid of color indices (0..3).
    """
    if len(tile_bytes) != 16:
        raise ValueError(f"Tile data must be exactly 16 bytes, got {len(tile_bytes)}")
        
    grid = []
    for y in range(8):
        byte1 = tile_bytes[2 * y]
        byte2 = tile_bytes[2 * y + 1]
        row = []
        for x in range(8):
            bit_index = 7 - x
            # Low bit (bit 0 of color index) is in the first byte (byte1)
            low_bit = (byte1 >> bit_index) & 1
            # High bit (bit 1 of color index) is in the second byte (byte2)
            high_bit = (byte2 >> bit_index) & 1
            color_idx = (high_bit << 1) | low_bit
            row.append(color_idx)
        grid.append(row)
    return grid

def verify_all_tiles():
    tiles_c_path = os.path.normpath(os.path.join(current_dir, "../../dandy-gb/src/tiles.c"))
    print(f"Independent Decoder Verification:")
    print(f"Parsing {tiles_c_path}...")
    
    try:
        tile_bytes = parse_tiles_c_robust(tiles_c_path)
    except Exception as e:
        print(f"[-] Parsing failed: {e}")
        return False

    print(f"[+] Successfully parsed {len(tile_bytes)} bytes from tiles.c")
    if len(tile_bytes) != 512:
        print(f"[-] Error: Expected 512 bytes for 32 tiles, got {len(tile_bytes)}")
        return False

    sprite_indices = set(list(range(9, 12)) + list(range(16, 20)) + list(range(24, 28)))
    
    # Palette definitions to map indices back to expected RGB colors
    bg_palette = [
        (0, 0, 0),        # 0: Black
        (96, 96, 96),     # 1: Dark Gray
        (176, 176, 176),  # 2: Light Gray
        (255, 255, 255)   # 3: White
    ]
    
    sprite_palette = [
        (0, 0, 0),        # 0: Transparent (drawn as black)
        (255, 255, 255),  # 1: White
        (96, 96, 96),     # 2: Dark Gray
        (0, 0, 0)         # 3: Black
    ]

    mismatches = 0
    for i in range(32):
        tile_offset = i * 16
        single_tile_bytes = tile_bytes[tile_offset : tile_offset + 16]
        
        is_sprite = i in sprite_indices
        palette = sprite_palette if is_sprite else bg_palette
        
        # 1. Decode using our independent decoder
        indep_grid = decode_tile_independent(single_tile_bytes)
        
        # 2. Decode using the worker's decoder
        worker_img = decode_gb_tile(single_tile_bytes, is_sprite=is_sprite)
        worker_pixels = worker_img.load()
        
        # 3. Compare programmatically
        tile_mismatches = 0
        for y in range(8):
            for x in range(8):
                expected_color = palette[indep_grid[y][x]]
                actual_color = worker_pixels[x, y]
                if expected_color != actual_color:
                    print(f"  Mismatch in Tile {i} (sprite={is_sprite}) at pixel ({x},{y}): "
                          f"Expected {expected_color} (index {indep_grid[y][x]}), "
                          f"got {actual_color}")
                    tile_mismatches += 1
                    
        if tile_mismatches > 0:
            print(f"[-] Tile {i} has {tile_mismatches} mismatched pixels!")
            mismatches += tile_mismatches
        else:
            # Print a snippet for verification
            pass

    if mismatches == 0:
        print("[+] SUCCESS: All 32 tiles decoded perfectly! No off-by-one, bit-shifting, or palette mapping errors found in the worker's decoder.")
        return True
    else:
        print(f"[-] FAILURE: Found {mismatches} pixel mismatches across tiles!")
        return False

if __name__ == "__main__":
    success = verify_all_tiles()
    sys.exit(0 if success else 1)
