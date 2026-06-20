import os
import sys
from PIL import Image

def main():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    png_path = os.path.normpath(os.path.join(current_dir, "../web/strike_original.png"))
    output_h_path = os.path.normpath(os.path.join(current_dir, "../src/tiles.h"))
    output_c_path = os.path.normpath(os.path.join(current_dir, "../src/tiles.c"))
    
    if not os.path.exists(png_path):
        print(f"Error: Original spritesheet not found at {png_path}. Run 'make sprites' first.")
        sys.exit(1)
        
    print(f"Loading spritesheet from {png_path}...")
    img = Image.open(png_path)
    width, height = img.size
    
    # Verify dimensions (expecting 256x32, 16x2 grid of 16x16 tiles)
    if width != 256 or height != 32:
        print(f"Error: Expected 256x32 spritesheet, got {width}x{height}")
        sys.exit(1)
        
    tile_width = 16
    tile_height = 16
    cols = width // tile_width
    rows = height // tile_height
    num_tiles = cols * rows
    
    print(f"Found {num_tiles} tiles of {tile_width}x{tile_height} pixels. Compiling to GameBoy 8x8 tiles...")
    
    gb_tile_bytes = []
    
    # Extract each 16x16 tile and downscale to 8x8
    for r in range(rows):
        for c in range(cols):
            # Crop 16x16 tile
            left = c * tile_width
            top = r * tile_height
            right = left + tile_width
            bottom = top + tile_height
            tile_img = img.crop((left, top, right, bottom))
            
            # Downscale to 8x8 using nearest-neighbor for clean pixel art
            tile_8x8 = tile_img.resize((8, 8), Image.Resampling.NEAREST)
            pixels = tile_8x8.convert("RGBA").load()
            
            # Convert 8x8 RGBA pixels to GameBoy 2bpp format (16 bytes per tile)
            tile_bytes = []
            for y in range(8):
                low_byte = 0
                high_byte = 0
                for x in range(8):
                    rgba = pixels[x, y]
                    r_val, g_val, b_val, a_val = rgba
                    
                    # Handle transparency (alpha < 128 -> Color 0, which is white/transparent)
                    if a_val < 128:
                        val = 0
                    else:
                        # Calculate luminance
                        luminance = 0.299 * r_val + 0.587 * g_val + 0.114 * b_val
                        # Map to 4 grayscale shades
                        if luminance >= 200:
                            val = 0  # Color 0: White
                        elif luminance >= 120:
                            val = 1  # Color 1: Light Gray
                        elif luminance >= 50:
                            val = 2  # Color 2: Dark Gray
                        else:
                            val = 3  # Color 3: Black
                            
                    # Pack bits MSB-first (leftmost pixel is MSB)
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
        "/* Generated automatically from strike_original.png. Do not edit. */",
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
        "/* Generated automatically from strike_original.png. Do not edit. */",
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
        
    print("Sprite compilation complete! Output: 512 bytes of GBDK tile data.")

if __name__ == "__main__":
    main()
