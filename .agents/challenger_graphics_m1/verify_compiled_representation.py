import os
import sys

# Add dandy-gb/tools to path
current_dir = os.path.dirname(os.path.abspath(__file__))
tools_dir = os.path.normpath(os.path.join(current_dir, "../../dandy-gb/tools"))
sys.path.append(tools_dir)

from compile_bmp_sprites import GLYPHS
from verify_decoder import parse_tiles_c_robust

def compile_glyph_to_2bpp(glyph):
    """
    Independent helper to compile a single glyph (list of 8 strings) to 16 bytes 2bpp.
    """
    tile_bytes = []
    for y in range(8):
        low_byte = 0
        high_byte = 0
        row_str = glyph[y]
        for x in range(8):
            val = int(row_str[x]) # Color index 0..3
            bit0 = val & 1
            bit1 = (val >> 1) & 1
            
            # Game Boy 2bpp is MSB-first
            low_byte |= (bit0 << (7 - x))
            high_byte |= (bit1 << (7 - x))
            
        tile_bytes.append(low_byte)
        tile_bytes.append(high_byte)
    return bytes(tile_bytes)

def verify_representation():
    tiles_c_path = os.path.normpath(os.path.join(current_dir, "../../dandy-gb/src/tiles.c"))
    print("Verifying GBDK compiled representation in tiles.c...")
    
    # 1. Parse the actual tiles.c
    try:
        actual_bytes = parse_tiles_c_robust(tiles_c_path)
    except Exception as e:
        print(f"[-] Failed to parse tiles.c: {e}")
        return False
        
    # 2. Compile each glyph from GLYPHS definition
    expected_bytes_list = []
    for t_idx in range(32):
        glyph = GLYPHS.get(t_idx, [ "0"*8 ] * 8)
        compiled = compile_glyph_to_2bpp(glyph)
        expected_bytes_list.append(compiled)
        
    expected_bytes = b"".join(expected_bytes_list)
    
    # 3. Compare bytes
    if actual_bytes == expected_bytes:
        print("[+] SUCCESS: The compiled bytes in tiles.c exactly match the source GLYPHS specification from compile_bmp_sprites.py!")
        return True
    else:
        print("[-] FAILURE: The compiled bytes in tiles.c do NOT match the source GLYPHS specification!")
        # Find the mismatches
        for i in range(32):
            actual_tile = actual_bytes[i*16 : (i+1)*16]
            expected_tile = expected_bytes[i*16 : (i+1)*16]
            if actual_tile != expected_tile:
                print(f"  Mismatch in Tile {i}:")
                print(f"    Actual:   {actual_tile.hex()}")
                print(f"    Expected: {expected_tile.hex()}")
        return False

if __name__ == "__main__":
    success = verify_representation()
    sys.exit(0 if success else 1)
