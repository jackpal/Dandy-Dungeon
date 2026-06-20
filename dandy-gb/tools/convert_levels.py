import os
import re

# Paths
current_dir = os.path.dirname(os.path.abspath(__file__))
levels_js_path = os.path.normpath(os.path.join(current_dir, "../../dandy-js/levels.js"))
output_h_path = os.path.normpath(os.path.join(current_dir, "../src/levels.h"))
output_c_path = os.path.normpath(os.path.join(current_dir, "../src/levels.c"))

# Create src directory if it doesn't exist
os.makedirs(os.path.dirname(output_h_path), exist_ok=True)

# Tile Character-to-ID Encoding Mapping
ENCODING = " *DudKF$i123mnop"

def char_to_tile_id(c):
    try:
        return ENCODING.index(c)
    except ValueError:
        print(f"Warning: Unknown character '{c}' in level data, defaulting to space (0)")
        return 0

# --- STAGE 1: Edge Wall Elision ---
def elide_edge_walls(tile_ids):
    """Omits the outer 176 border tiles, keeping only the inner 58x28 (1,624 tiles) grid."""
    inner_tiles = []
    for r in range(1, 29):
        start_idx = r * 60 + 1
        end_idx = r * 60 + 59
        inner_tiles.extend(tile_ids[start_idx:end_idx])
    return inner_tiles

# --- STAGE 2: Scheme B2 Prefix Encoding ---
def encode_tile_b2(tile_id):
    """Encodes a single tile ID into Scheme B2 prefix bits."""
    if tile_id == 0:
        return [0]
    elif tile_id == 1:
        return [1, 0]
    elif 2 <= tile_id <= 15:
        bits = [1, 1]
        for i in range(3, -1, -1):
            bits.append((tile_id >> i) & 1)
        return bits
    else:
        raise ValueError(f"Invalid tile ID {tile_id}")

# --- STAGE 3: Bitstream Packing ---
def pack_bits_to_bytes(bits):
    """Packs bits MSB-first into bytes, padded with 0s."""
    packed_bytes = []
    for i in range(0, len(bits), 8):
        chunk = bits[i:i+8]
        byte_val = 0
        for bit_idx, bit in enumerate(chunk):
            byte_val |= (bit << (7 - bit_idx))
        packed_bytes.append(byte_val)
    return packed_bytes

# --- Main Compressor entry point ---
def compress_level(tile_ids):
    """
    Compresses a full 1,800-tile map using Edge Wall Elision + Scheme B2.
    Returns a list of packed bytes.
    """
    # 1. Elide border walls
    inner_tiles = elide_edge_walls(tile_ids)
    # 2. Convert to Scheme B2 bits
    bits = []
    for tile in inner_tiles:
        bits.extend(encode_tile_b2(tile))
    # 3. Pack bits to bytes
    return pack_bits_to_bytes(bits)

def main():
    print(f"Reading levels from {levels_js_path}...")
    with open(levels_js_path, "r") as f:
        content = f.read()

    all_strings = re.findall(r'"([^"]*)"', content)
    level_rows = [s for s in all_strings if len(s) == 60]

    levels = []
    for i in range(0, len(level_rows), 30):
        levels.append(level_rows[i:i+30])

    print(f"Found {len(levels)} levels.")

    # ==========================================
    # Generate C Header (levels.h)
    # ==========================================
    h_content = [
        "/* Generated automatically from dandy-js/levels.js. Do not edit. */",
        "#ifndef DANDY_LEVELS_H",
        "#define DANDY_LEVELS_H",
        "",
        "#include <stdint.h>",
        "",
        "#define DANDY_LEVEL_WIDTH  60",
        "#define DANDY_LEVEL_HEIGHT 30",
        f"#define DANDY_NUM_LEVELS   {len(levels)}",
        "",
        "/* Extern declaration of pointer array to all compressed levels in ROM */",
        "extern const uint8_t* const dandy_levels[DANDY_NUM_LEVELS];",
        "extern const uint16_t dandy_level_sizes[DANDY_NUM_LEVELS];",
        "",
        "#endif /* DANDY_LEVELS_H */"
    ]

    print(f"Writing C header to {output_h_path}...")
    with open(output_h_path, "w") as f:
        f.write("\n".join(h_content))

    # ==========================================
    # Generate C Source (levels.c)
    # ==========================================
    c_content = [
        "/* Generated automatically from dandy-js/levels.js. Do not edit. */",
        '#include "levels.h"',
        ""
    ]

    total_uncompressed = 0
    total_compressed = 0

    for l_idx, lvl in enumerate(levels):
        flat_tiles = []
        for row in lvl:
            flat_tiles.extend([char_to_tile_id(c) for c in row])
            while len(flat_tiles) % 60 != 0:
                flat_tiles.append(0)
                
        uncompressed_size = len(flat_tiles)
        compressed_bytes = compress_level(flat_tiles)
        compressed_size = len(compressed_bytes)
        
        total_uncompressed += uncompressed_size
        total_compressed += compressed_size
        
        saving = (1.0 - (compressed_size / uncompressed_size)) * 100
        print(f"Level {l_idx:2d}: Raw={uncompressed_size:4d}B -> B2={compressed_size:4d}B (Saved {saving:4.1f}%)")
        
        c_content.append(f"/* Level {l_idx} (Raw: {uncompressed_size}B, B2: {compressed_size}B) */")
        c_content.append(f"const uint8_t dandy_level_{l_idx}[] = {{")
        
        hex_rows = []
        for r in range(0, len(compressed_bytes), 16):
            chunk = compressed_bytes[r:r+16]
            hex_str = ", ".join([f"0x{val:02X}" for val in chunk])
            hex_rows.append(f"    {hex_str}")
        
        c_content.append(",\n".join(hex_rows))
        c_content.append("};")
        c_content.append("")

    c_content.append("/* Pointer array to all compressed levels in ROM */")
    c_content.append("const uint8_t* const dandy_levels[DANDY_NUM_LEVELS] = {")
    level_pointers = [f"    dandy_level_{i}" for i in range(len(levels))]
    c_content.append(",\n".join(level_pointers))
    c_content.append("};")
    c_content.append("")
    c_content.append("/* Array of compressed level sizes in bytes */")
    c_content.append("const uint16_t dandy_level_sizes[DANDY_NUM_LEVELS] = {")
    level_sizes = [f"    sizeof(dandy_level_{i})" for i in range(len(levels))]
    c_content.append(",\n".join(level_sizes))
    c_content.append("};")
    c_content.append("")

    overall_saving = (1.0 - (total_compressed / total_uncompressed)) * 100
    print(f"--------------------------------------------------")
    print(f"TOTAL MAP BUDGET Footprint in ROM:")
    print(f"Raw uncompressed:  {total_uncompressed:5d} Bytes ({total_uncompressed/1024:.1f} KB)")
    print(f"B2 compressed:     {total_compressed:5d} Bytes ({total_compressed/1024:.1f} KB)")
    print(f"Overall savings:   {overall_saving:.1f}%")
    print(f"--------------------------------------------------")

    print(f"Writing C source to {output_c_path}...")
    with open(output_c_path, "w") as f:
        f.write("\n".join(c_content))

    print("Conversion complete!")

if __name__ == "__main__":
    main()
