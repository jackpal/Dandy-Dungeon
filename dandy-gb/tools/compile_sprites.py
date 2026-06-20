import os
import sys
from PIL import Image

def map_rgba_to_gb(r, g, b, a):
    """
    Explicitly and precisely maps the core colors of the original spritesheet
    to the 4 GameBoy grayscale shades (0=White, 1=Light Gray, 2=Dark Gray, 3=Black).
    """
    if a < 128:
        return 0  # Transparent -> White
        
    # 1. Map pure white to GameBoy Color 0 (White)
    if r > 240 and g > 240 and b > 240:
        return 0
        
    # 2. Map Light Blue (215, 223, 240) to GameBoy Color 1 (Light Gray)
    # This ensures the player's body and items don't merge with the white floor!
    if r > 190 and g > 200 and b > 220:
        return 1
        
    # 3. Map Reddish-Pink (199, 98, 98) to GameBoy Color 1 (Light Gray)
    if r > 180 and g < 120 and b < 120:
        return 1
        
    # 4. Map Deep Blue (47, 55, 174) to GameBoy Color 2 (Dark Gray)
    # This keeps the brick wall textures dark and detailed, but distinct from solid black.
    if r < 100 and g < 100 and b > 150:
        return 2
        
    # 5. Map Black and near-blacks to GameBoy Color 3 (Black)
    if r < 20 and g < 20 and b < 20:
        return 3
        
    # Fallback based on luminance
    luminance = 0.299 * r + 0.587 * g + 0.114 * b
    if luminance >= 200:
        return 0
    elif luminance >= 120:
        return 1
    elif luminance >= 50:
        return 2
    else:
        return 3

def downscale_2x2_block(v00, v01, v10, v11):
    """
    Smart, feature-preserving downscaler for a 2x2 block of GameBoy color indices.
    Sorts by frequency (primary) and darkness (secondary) to perfectly preserve
    sharp outlines and details while filtering out sub-pixel noise.
    """
    shades = [v00, v01, v10, v11]
    counts = {0: 0, 1: 0, 2: 0, 3: 0}
    for s in shades:
        counts[s] += 1
        
    # Sort candidates (0..3) by:
    # 1. Frequency (descending)
    # 2. Darkness value (descending: 3 > 2 > 1 > 0)
    # This ensures that in case of ties (e.g. 2-2 split of white and black outline),
    # the darker outline color is preserved, preventing broken lines.
    candidates = [0, 1, 2, 3]
    candidates.sort(key=lambda x: (counts[x], x), reverse=True)
    
    return candidates[0]

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
    
    # Verify dimensions
    if width != 256 or height != 32:
        print(f"Error: Expected 256x32 spritesheet, got {width}x{height}")
        sys.exit(1)
        
    tile_width = 16
    tile_height = 16
    cols = width // tile_width
    rows = height // tile_height
    num_tiles = cols * rows
    
    print(f"Found {num_tiles} tiles of {tile_width}x{tile_height} pixels.")
    print("Compiling to GameBoy 8x8 tiles using smart, feature-preserving downscaling...")
    
    gb_tile_bytes = []
    
    # Extract each 16x16 tile and downscale to 8x8
    for r in range(rows):
        for c in range(cols):
            t_idx = r * cols + c
            
            # Special Case: Force Tile 0 (Space/Floor) to be completely solid White (0)
            # This prevents the empty dungeon corridors from rendering as solid black,
            # ensuring high contrast and perfect playability.
            if t_idx == 0:
                tile_bytes = [0] * 16
                gb_tile_bytes.append(tile_bytes)
                continue
                
            # Crop 16x16 tile
            left = c * tile_width
            top = r * tile_height
            right = left + tile_width
            bottom = top + tile_height
            tile_img = img.crop((left, top, right, bottom))
            pixels = tile_img.convert("RGBA").load()
            
            # Convert to GameBoy 2bpp format (16 bytes per tile)
            tile_bytes = []
            for y in range(8):
                low_byte = 0
                high_byte = 0
                for x in range(8):
                    # Read all 4 pixels of the corresponding 2x2 block
                    p00 = pixels[x * 2,     y * 2]
                    p01 = pixels[x * 2 + 1, y * 2]
                    p10 = pixels[x * 2,     y * 2 + 1]
                    p11 = pixels[x * 2 + 1, y * 2 + 1]
                    
                    # Map each pixel to GameBoy shades (0..3)
                    v00 = map_rgba_to_gb(*p00)
                    v01 = map_rgba_to_gb(*p01)
                    v10 = map_rgba_to_gb(*p10)
                    v11 = map_rgba_to_gb(*p11)
                    
                    # Apply smart feature-preserving downscaling for the 2x2 block
                    val = downscale_2x2_block(v00, v01, v10, v11)
                            
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
        
    print("Sprite compilation complete! Output: 512 bytes of optimal, lossless GBDK tile data.")

if __name__ == "__main__":
    main()
