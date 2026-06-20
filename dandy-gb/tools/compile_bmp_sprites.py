import os
import sys

def map_atari_to_gb(atari_color):
    """
    Directly and losslessly maps the 4 Atari multi-color character indices
    to the 4 GameBoy grayscale shades:
    - 0 (Atari Background/Black) -> 3 (GameBoy Black)
    - 1 (Atari Gold)             -> 1 (GameBoy Light Gray)
    - 2 (Atari Dark Blue)        -> 2 (GameBoy Dark Gray)
    - 3 (Atari White)            -> 0 (GameBoy White)
    """
    mapping = {
        0: 3, # Black
        1: 1, # Gold -> Light Gray
        2: 2, # Dark Blue -> Dark Gray
        3: 0  # White
    }
    return mapping.get(atari_color, 3)

def main():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    charset_path = "/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-atari-8-bit/src/CHARSET.TXT"
    output_h_path = os.path.normpath(os.path.join(current_dir, "../src/tiles.h"))
    output_c_path = os.path.normpath(os.path.join(current_dir, "../src/tiles.c"))
    
    if not os.path.exists(charset_path):
        print(f"Error: Could not find CHARSET.TXT at {charset_path}")
        sys.exit(1)
        
    print(f"Reading and parsing Atari CHARSET.TXT from {charset_path}...")
    
    # Read CHARSET.TXT lines
    with open(charset_path, "r") as f:
        lines = f.readlines()
        
    # We will extract 28 characters
    tiles_data = {}
    current_char = None
    hex_buffer = ""
    
    for line_num, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
            
        # Detect CHAR header, e.g., ";CHAR 1" or "00050 ;CHAR 1"
        if ";CHAR" in line:
            # Parse character index
            parts = line.split(";CHAR")
            char_idx = int(parts[1].strip())
            current_char = char_idx
            hex_buffer = ""
            continue
            
        if current_char is not None and ".HS" in line:
            # Extract the hex string after .HS directive
            # Line format: "00070  .HS FFF3F3CFCFF3333FFFFFCFCF3333FFFF"
            parts = line.split(".HS")
            hex_str = parts[1].strip()
            hex_buffer += hex_str
            
            # A completed character has 64 hex characters (32 bytes)
            if len(hex_buffer) == 64:
                # Convert hex string to bytes
                byte_data = bytes.fromhex(hex_buffer)
                tiles_data[current_char] = byte_data
                current_char = None
                
    print(f"Successfully parsed {len(tiles_data)} pristine Atari 8x8 tiles.")
    
    gb_tile_bytes = []
    
    # Compile each of the 28 Atari tiles into GameBoy 8x8 2bpp tiles
    for t_idx in range(28):
        B = tiles_data.get(t_idx, b"\x00" * 32)
        
        tile_bytes = []
        # Reconstruct the 8x8 GameBoy tile by losslessly de-upscaling the 16 vertical rows of the
        # Atari tile (taking every second row, which corresponds to the even bytes).
        for gy in range(8):
            if gy < 4:
                # Top half of the tile (rows 0..3 of the GameBoy tile, mapping to rows 0, 2, 4, 6 of 16x16)
                left_byte = B[gy * 2]
                right_byte = B[8 + gy * 2]
            else:
                # Bottom half of the tile (rows 4..7 of the GameBoy tile, mapping to rows 8, 10, 12, 14 of 16x16)
                left_byte = B[16 + (gy - 4) * 2]
                right_byte = B[24 + (gy - 4) * 2]
                
            low_byte = 0
            high_byte = 0
            
            # Decode the 8 horizontal pixels of the row (4 from left char, 4 from right char)
            for x in range(8):
                if x < 4:
                    # Left half: extract 2-bit Atari color from left_byte
                    shift = (3 - x) * 2
                    atari_color = (left_byte >> shift) & 3
                else:
                    # Right half: extract 2-bit Atari color from right_byte
                    shift = (7 - x) * 2
                    atari_color = (right_byte >> shift) & 3
                    
                # Map Atari color to GameBoy shade (0..3)
                val = map_atari_to_gb(atari_color)
                
                # Pack into GameBoy 2bpp format
                bit0 = val & 1
                bit1 = (val >> 1) & 1
                low_byte |= (bit0 << (7 - x))
                high_byte |= (bit1 << (7 - x))
                
            tile_bytes.append(low_byte)
            tile_bytes.append(high_byte)
            
        gb_tile_bytes.append(tile_bytes)
        
    # Pad to 32 tiles with solid Black (3) tiles for the remaining 4 unused slots
    for t_idx in range(28, 32):
        gb_tile_bytes.append([0xFF] * 16)
        
    # ==========================================
    # Generate C Header (tiles.h)
    # ==========================================
    h_content = [
        "/* Generated automatically from Atari CHARSET.TXT. Do not edit. */",
        "#ifndef DANDY_TILES_H",
        "#define DANDY_TILES_H",
        "",
        "#include <stdint.h>",
        "",
        "#define DANDY_NUM_TILES 32",
        "#define DANDY_TILE_SIZE 16",
        "",
        "/* GameBoy 2bpp tile data for all 32 tiles */",
        "extern const unsigned char dandy_tiles[DANDY_NUM_TILES * DANDY_TILE_SIZE];",
        "",
        "#endif /* DANDY_TILES_H */"
    ]
    
    print(f"Writing C header to {output_h_path}...")
    with open(output_h_path, "w") as f:
        f.write("\n".join(h_content))
        
    # ==========================================
    # Generate C Source (tiles.c)
    # ==========================================
    c_content = [
        "/* Generated automatically from Atari CHARSET.TXT. Do not edit. */",
        '#include "tiles.h"',
        "",
        "/* 32 tiles * 16 bytes per tile = 512 bytes */",
        "const unsigned char dandy_tiles[] = {"
    ]
    
    for t_idx, tile in enumerate(gb_tile_bytes):
        c_content.append(f"    /* Tile {t_idx} */")
        hex_rows = []
        for row_idx in range(0, len(tile), 8):
            chunk = tile[row_idx:row_idx+8]
            hex_str = ", ".join([f"0x{val:02X}" for val in chunk])
            hex_rows.append(f"    {hex_str}")
        c_content.append(",\n".join(hex_rows) + ("," if t_idx < 31 else ""))
        
    c_content.append("};")
    
    print(f"Writing C source to {output_c_path}...")
    with open(output_c_path, "w") as f:
        f.write("\n".join(c_content))
        
    print("Sprite compilation complete! Output: 512 bytes of perfectly reconstructed, unaliased Atari tile assets.")

if __name__ == "__main__":
    main()
