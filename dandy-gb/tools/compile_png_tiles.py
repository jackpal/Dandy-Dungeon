import os
import sys
import argparse
from PIL import Image

def pack_tile_2bpp(img, tile_x):
    """
    Packs a single 8x8 tile from the image at column tile_x into GameBoy 2bpp format (16 bytes).
    """
    tile_bytes = []
    pixels = img.load()
    
    for y in range(8):
        low_byte = 0
        high_byte = 0
        
        for x in range(8):
            px_val = pixels[tile_x + x, y]
            
            # Map grayscale (0..255) to 2bpp color index (0..3):
            # 0 -> White (index 0)
            # 1 -> Light Gray (index 1)
            # 2 -> Dark Gray (index 2)
            # 3 -> Black (index 3)
            # Since artists draw in different gray shades, we use simple robust thresholds:
            if px_val > 220:
                color_idx = 0  # White
            elif px_val > 120:
                color_idx = 1  # Light Gray
            elif px_val > 50:
                color_idx = 2  # Dark Gray
            else:
                color_idx = 3  # Black
                
            bit0 = color_idx & 1
            bit1 = (color_idx >> 1) & 1
            
            # Pack MSB-first
            low_byte |= (bit0 << (7 - x))
            high_byte |= (bit1 << (7 - x))
            
        tile_bytes.append(low_byte)
        tile_bytes.append(high_byte)
        
    return tile_bytes

def main():
    parser = argparse.ArgumentParser(description="Compile 8x8 pixel-art grayscale PNG sheets into GBDK 2bpp C arrays.")
    parser.add_argument("--input", required=True, help="Input 256x8 grayscale PNG file.")
    parser.add_argument("--output-c", required=True, help="Output C source file path.")
    parser.add_argument("--output-h", required=True, help="Output C header file path.")
    parser.add_argument("--name", required=True, help="Name of the GBDK C array variable (e.g. dandy_tiles_light).")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.input):
        print(f"Error: Input file not found at {args.input}")
        sys.exit(1)
        
    # Read and verify image dimensions
    try:
        with Image.open(args.input) as img:
            width, height = img.size
            if width != 256 or height != 8:
                print(f"Error: Expected image size 256x8 (32 tiles of 8x8), but got {width}x{height}")
                sys.exit(1)
                
            # Convert to grayscale
            img_gray = img.convert("L")
            
            print(f"Compiling {args.input} into GBDK array '{args.name}'...")
            
            # Pack all 32 tiles
            gb_tile_bytes = []
            for t_idx in range(32):
                tile_bytes = pack_tile_2bpp(img_gray, t_idx * 8)
                gb_tile_bytes.append(tile_bytes)
    except Exception as e:
        print(f"Error reading image: {e}")
        sys.exit(1)
        
    # Generate C Header (.h)
    h_guard = args.name.upper() + "_H"
    h_content = [
        "/* Generated automatically from 8x8 grayscale PNG. Do not edit. */",
        f"#ifndef {h_guard}",
        f"#define {h_guard}",
        "",
        "#include <stdint.h>",
        "",
        "#define DANDY_NUM_TILES 32",
        "#define DANDY_TILE_SIZE 16",
        "",
        f"extern const unsigned char {args.name}[DANDY_NUM_TILES * DANDY_TILE_SIZE];",
        "",
        f"#endif /* {h_guard} */"
    ]
    
    os.makedirs(os.path.dirname(args.output_h), exist_ok=True)
    with open(args.output_h, "w") as f:
        f.write("\n".join(h_content) + "\n")
        
    # Generate C Source (.c)
    c_content = [
        "/* Generated automatically from 8x8 grayscale PNG. Do not edit. */",
        f'#include "{os.path.basename(args.output_h)}"',
        "",
        f"const unsigned char {args.name}[] = {{"
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
    
    os.makedirs(os.path.dirname(args.output_c), exist_ok=True)
    with open(args.output_c, "w") as f:
        f.write("\n".join(c_content) + "\n")
        
    print(f"Successfully compiled {args.input} -> {args.output_c}")

if __name__ == "__main__":
    main()
