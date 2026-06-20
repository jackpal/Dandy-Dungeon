import os
import sys
import struct

def map_bgr_to_gb(b, g, r):
    """
    Precisely maps the raw BGR colors from dandy.bmp to the 4 GameBoy grayscale shades
    based on the user's specification:
    - Black -> Black (3)
    - Dark Blue -> Dark Gray (2)
    - Gold -> Light Gray (1)
    - White -> White (0)
    
    Handles minor 1-2 unit rounding noise in the BMP file.
    """
    # 1. Map Black and near-blacks to GameBoy Color 3 (Black)
    if r < 20 and g < 20 and b < 20:
        return 3
        
    # 2. Map Dark Blue (B=174, G=55, R=47) to GameBoy Color 2 (Dark Gray)
    if b > 150 and g < 100 and r < 100:
        return 2
        
    # 3. Map Gold/Pink/Red (B=98, G=98, R=199) to GameBoy Color 1 (Light Gray)
    if r > 180 and g < 120 and b < 120:
        return 1
        
    # 4. Map White (255,255,255) and Light Blue (215,223,240) to GameBoy Color 0 (White)
    return 0

def downscale_2x2_block(v00, v01, v10, v11):
    """
    Smart, feature-preserving downscaler for a 2x2 block of GameBoy color indices.
    Since the floor is solid Black (3), Black acts as the background/empty space.
    If a block contains active drawing pixels (Gold/1, Dark Blue/2, or White/0) mixed
    with Black (3) background, we ignore the background and select the dominant foreground
    color. This perfectly preserves thin 1px lines (like the bottom of the 'U' stairs tile)
    from being overwritten by the dark background!
    """
    shades = [v00, v01, v10, v11]
    
    # Filter out the background color (Black = 3)
    non_bg_shades = [s for s in shades if s != 3]
    
    # If the block is completely background, return Black (3)
    if not non_bg_shades:
        return 3
        
    # Count frequencies of the active drawing colors in the block
    counts = {}
    for s in non_bg_shades:
        counts[s] = counts.get(s, 0) + 1
        
    # Sort the unique active colors by:
    # 1. Frequency (descending)
    # 2. Intensity value (descending: 2 > 1 > 0 to prefer Dark Blue/Gold over White highlights)
    unique_active = list(set(non_bg_shades))
    unique_active.sort(key=lambda x: (counts[x], x), reverse=True)
    
    return unique_active[0]

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
    
    # BMP Row width in bytes
    row_width_bytes = 256 * 3
    
    tile_width = 16
    tile_height = 16
    cols = 16
    rows = 2
    num_tiles = cols * rows
    
    gb_tile_bytes = []
    
    # Extract each 16x16 tile and downscale to 8x8 using smart active-pixel voting
    for r in range(rows):
        for c in range(cols):
            t_idx = r * cols + c
            
            # Special Case: Force Tile 0 (Space/Floor) to be completely solid Black (3)
            # Renders the empty corridors as a dark void, matching original game aesthetics.
            if t_idx == 0:
                tile_bytes = [0xFF] * 16
                gb_tile_bytes.append(tile_bytes)
                continue
                
            tile_left = c * tile_width
            tile_top = r * tile_height
            
            tile_bytes = []
            for y in range(8):
                low_byte = 0
                high_byte = 0
                for x in range(8):
                    # Read all 4 pixels in the 2x2 block
                    px0 = tile_left + x * 2
                    px1 = tile_left + x * 2 + 1
                    py0 = tile_top + y * 2
                    py1 = tile_top + y * 2 + 1
                    
                    # BMP rows are bottom-to-top in file bytes
                    offset_00 = pixel_offset + (31 - py0) * row_width_bytes + px0 * 3
                    offset_01 = pixel_offset + (31 - py0) * row_width_bytes + px1 * 3
                    offset_10 = pixel_offset + (31 - py1) * row_width_bytes + px0 * 3
                    offset_11 = pixel_offset + (31 - py1) * row_width_bytes + px1 * 3
                    
                    # Map BGR to GameBoy color index for all 4 pixels
                    v00 = map_bgr_to_gb(data[offset_00], data[offset_00 + 1], data[offset_00 + 2])
                    v01 = map_bgr_to_gb(data[offset_01], data[offset_01 + 1], data[offset_01 + 2])
                    v10 = map_bgr_to_gb(data[offset_10], data[offset_10 + 1], data[offset_10 + 2])
                    v11 = map_bgr_to_gb(data[offset_11], data[offset_11 + 1], data[offset_11 + 2])
                    
                    # Apply smart active-pixel downscaling
                    val = downscale_2x2_block(v00, v01, v10, v11)
                    
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
        
    print("Sprite compilation complete! Output: 512 bytes of pristine, active-pixel-preserved GBDK tile data.")

if __name__ == "__main__":
    main()
