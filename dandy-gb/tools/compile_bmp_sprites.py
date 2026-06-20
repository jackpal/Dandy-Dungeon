import os
import sys
import struct

def map_bgr_to_gb(b, g, r):
    """
    Precisely maps the raw BGR colors from dandy.bmp to the 4 GameBoy grayscale shades
    (0=White, 1=Light Gray, 2=Dark Gray, 3=Black).
    Handles minor 1-2 unit rounding noise in the BMP file.
    """
    # 1. Map pure white to GameBoy Color 0 (White)
    if r > 240 and g > 240 and b > 240:
        return 0
        
    # 2. Map Light Blue (B=240, G=223, R=215) to GameBoy Color 1 (Light Gray)
    # Allows for +/- 5 units of rounding noise
    if b > 210 and g > 200 and r > 190 and b > r:
        return 1
        
    # 3. Map Reddish-Pink (B=98, G=98, R=199) to GameBoy Color 1 (Light Gray)
    if r > 180 and g < 120 and b < 120:
        return 1
        
    # 4. Map Deep Blue (B=174, G=55, R=47) to GameBoy Color 2 (Dark Gray)
    if b > 150 and g < 100 and r < 100:
        return 2
        
    # 5. Map Black and near-blacks to GameBoy Color 3 (Black)
    if r < 20 and g < 20 and b < 20:
        return 3
        
    # Fallback based on standard luminance
    luminance = 0.299 * r + 0.587 * g + 0.114 * b
    if luminance >= 200:
        return 0
    elif luminance >= 120:
        return 1
    elif luminance >= 50:
        return 2
    else:
        return 3

def main():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    bmp_path = "/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-c++/dandy.bmp"
    output_h_path = os.path.normpath(os.path.join(current_dir, "../src/tiles.h"))
    output_c_path = os.path.normpath(os.path.join(current_dir, "../src/tiles.c"))
    
    if not os.path.exists(bmp_path):
        print(f"Error: Could not find dandy.bmp at {bmp_path}")
        sys.exit(1)
        
    print(f"Opening and manually decoding raw BMP from {bmp_path}...")
    
    with open(bmp_path, "rb") as f:
        data = f.read()
        
    # Manual BMP Header Validation
    if data[:2] != b'BM':
        print("Error: Invalid BMP file signature!")
        sys.exit(1)
        
    pixel_offset = struct.unpack("<I", data[10:14])[0]
    width = struct.unpack("<i", data[18:22])[0]
    height = struct.unpack("<i", data[22:26])[0]
    bpp = struct.unpack("<H", data[28:30])[0]
    compression = struct.unpack("<I", data[30:34])[0]
    
    if width != 256 or height != 32 or bpp != 24 or compression != 0:
        print(f"Error: Unsupported BMP format! Expected 256x32, 24bpp, uncompressed. Got {width}x{height}, {bpp}bpp, compression {compression}")
        sys.exit(1)
        
    print(f"BMP verified: {width}x{height} pixels, {bpp}bpp, uncompressed. Decoding raw pixel bytes...")
    
    # BMP Row width in bytes (must be padded to multiple of 4, but 256*3 = 768 which is already a multiple of 4)
    row_width_bytes = 256 * 3
    
    tile_width = 16
    tile_height = 16
    cols = 16
    rows = 2
    num_tiles = cols * rows
    
    gb_tile_bytes = []
    
    # Extract each 16x16 tile and sub-sample to 8x8
    for r in range(rows):
        for c in range(cols):
            t_idx = r * cols + c
            
            # Special Case: Force Tile 0 (Space/Floor) to be completely solid White (0)
            # This ensures the empty dungeon corridors render as light floor instead of solid black.
            if t_idx == 0:
                tile_bytes = [0] * 16
                gb_tile_bytes.append(tile_bytes)
                continue
                
            tile_left = c * tile_width
            tile_top = r * tile_height
            
            tile_bytes = []
            for y in range(8):
                low_byte = 0
                high_byte = 0
                for x in range(8):
                    # Manual 2x2 sub-sampling: read the pixel at the top-left of the 2x2 block.
                    # Since the BMP contains bottom-to-top rows, we map row 'tile_top + y * 2'
                    # to '31 - (tile_top + y * 2)' in the raw file bytes.
                    px = tile_left + x * 2
                    py = tile_top + y * 2
                    
                    offset = pixel_offset + (31 - py) * row_width_bytes + px * 3
                    b = data[offset]
                    g = data[offset + 1]
                    r_val = data[offset + 2]
                    
                    # Map BGR to GameBoy color index (0..3)
                    val = map_bgr_to_gb(b, g, r_val)
                    
                    # Pack bits MSB-first
                    bit0 = val & 1
                    bit1 = (val >> 1) & 1
                    low_byte |= (bit0 << (7 - x))
                    high_byte |= (bit1 << (7 - x))
                    
                tile_bytes.append(low_byte)
                tile_bytes.append(high_byte)
                
            gb_tile_bytes.append(tile_bytes)
            
    # ==========================================
    # Generate C Header (tiles.h)
    # ==========================================
    h_content = [
        "/* Generated automatically from dandy.bmp. Do not edit. */",
        "#ifndef DANDY_TILES_H",
        "#define DANDY_TILES_H",
        "",
        "#include <stdint.h>",
        "",
        f"#define DANDY_NUM_TILES {num_tiles}",
        f"#define DANDY_TILE_SIZE 16",
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
        "/* Generated automatically from dandy.bmp. Do not edit. */",
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
        c_content.append(",\n".join(hex_rows) + ("," if t_idx < num_tiles - 1 else ""))
        
    c_content.append("};")
    
    print(f"Writing C source to {output_c_path}...")
    with open(output_c_path, "w") as f:
        f.write("\n".join(c_content))
        
    print("Sprite compilation complete! Output: 512 bytes of pristine, unaliased GBDK tile data.")

if __name__ == "__main__":
    main()
