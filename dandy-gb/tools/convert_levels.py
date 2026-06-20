import os
import re

# Paths
current_dir = os.path.dirname(os.path.abspath(__file__))
levels_js_path = os.path.join(current_dir, "../../dandy-js/levels.js")
output_h_path = os.path.join(current_dir, "../src/levels.h")

# Create src directory if it doesn't exist
os.makedirs(os.path.dirname(output_h_path), exist_ok=True)

encoding = " *DudKF$i123mnop"

def char_to_tile_id(c):
    try:
        return encoding.index(c)
    except ValueError:
        print(f"Warning: Unknown character '{c}' in level data, defaulting to space (0)")
        return 0

# Simple, highly-efficient Run-Length Encoding (RLE) Compressor
# Only compresses runs of length >= 4. Writes shorter runs literally.
# Run-length token format: [0xFF, RUN_LENGTH, TILE_ID]
def compress_level(tile_ids):
    compressed = []
    i = 0
    n = len(tile_ids)
    while i < n:
        tile = tile_ids[i]
        run_len = 1
        while i + run_len < n and tile_ids[i + run_len] == tile and run_len < 255:
            run_len += 1
        
        if run_len >= 4:
            # Compress as an RLE run: [0xFF, RUN_LENGTH, TILE_ID]
            compressed.extend([255, run_len, tile])
            i += run_len
        else:
            # Write literally
            compressed.append(tile)
            i += 1
    return compressed

print(f"Reading levels from {levels_js_path}...")
with open(levels_js_path, "r") as f:
    content = f.read()

# Find all double-quoted strings in levels.js
all_strings = re.findall(r'"([^"]*)"', content)
level_rows = [s for s in all_strings if len(s) == 60]

levels = []
for i in range(0, len(level_rows), 30):
    levels.append(level_rows[i:i+30])

print(f"Found {len(levels)} levels.")

# Generate C header
h_content = []
h_content.append("/* Generated automatically from dandy-js/levels.js. Do not edit. */")
h_content.append("#ifndef DANDY_LEVELS_H")
h_content.append("#define DANDY_LEVELS_H")
h_content.append("")
h_content.append("#include <stdint.h>")
h_content.append("")
h_content.append(f"#define DANDY_LEVEL_WIDTH  60")
h_content.append(f"#define DANDY_LEVEL_HEIGHT 30")
h_content.append(f"#define DANDY_NUM_LEVELS   {len(levels)}")
h_content.append("")

# Write tile definitions
h_content.append("/* Tile ID Constants */")
h_content.append("#define TILE_SPACE       0")
h_content.append("#define TILE_WALL        1")
h_content.append("#define TILE_DOOR        2")
h_content.append("#define TILE_UP          3")
h_content.append("#define TILE_DOWN        4")
h_content.append("#define TILE_KEY         5")
h_content.append("#define TILE_FOOD        6")
h_content.append("#define TILE_MONEY       7")
h_content.append("#define TILE_BOMB        8")
h_content.append("#define TILE_MONSTER1    9")
h_content.append("#define TILE_MONSTER2    10")
h_content.append("#define TILE_MONSTER3    11")
h_content.append("#define TILE_HEART       12")
h_content.append("#define TILE_GENERATOR1  13")
h_content.append("#define TILE_GENERATOR2  14")
h_content.append("#define TILE_GENERATOR3  15")
h_content.append("#define TILE_ARROW       16")
h_content.append("#define TILE_PLAYER1     24")
h_content.append("")

total_uncompressed = 0
total_compressed = 0

# Write individual compressed level arrays
for l_idx, lvl in enumerate(levels):
    # Flatten level rows to 1800 tile IDs
    flat_tiles = []
    for row in lvl:
        flat_tiles.extend([char_to_tile_id(c) for c in row])
        while len(flat_tiles) % 60 != 0: # Safety pad row
            flat_tiles.append(0)
            
    uncompressed_size = len(flat_tiles)
    compressed_tiles = compress_level(flat_tiles)
    compressed_size = len(compressed_tiles)
    
    total_uncompressed += uncompressed_size
    total_compressed += compressed_size
    
    saving = (1.0 - (compressed_size / uncompressed_size)) * 100
    print(f"Level {l_idx:2d}: Raw={uncompressed_size:4d}B -> RLE={compressed_size:4d}B (Saved {saving:4.1f}%)")
    
    h_content.append(f"/* Level {l_idx} (Raw: {uncompressed_size}B, RLE: {compressed_size}B) */")
    h_content.append(f"const uint8_t dandy_level_{l_idx}[] = {{")
    
    # Format hex output in clean rows of 16 values
    hex_rows = []
    for r in range(0, len(compressed_tiles), 16):
        chunk = compressed_tiles[r:r+16]
        hex_str = ", ".join([f"0x{val:02X}" for val in chunk])
        hex_rows.append(f"    {hex_str}")
    
    h_content.append(",\n".join(hex_rows))
    h_content.append("};")
    h_content.append("")

# Write pointer array for dandy_levels
h_content.append("/* Pointer array to all compressed levels in ROM */")
h_content.append("const uint8_t* const dandy_levels[DANDY_NUM_LEVELS] = {")
level_pointers = [f"    dandy_level_{i}" for i in range(len(levels))]
h_content.append(",\n".join(level_pointers))
h_content.append("};")
h_content.append("")

overall_saving = (1.0 - (total_compressed / total_uncompressed)) * 100
print(f"--------------------------------------------------")
print(f"TOTAL MAP BUDGET Footprint in ROM:")
print(f"Raw uncompressed:  {total_uncompressed:5d} Bytes ({total_uncompressed/1024:.1f} KB)")
print(f"RLE compressed:    {total_compressed:5d} Bytes ({total_compressed/1024:.1f} KB)")
print(f"Overall savings:   {overall_saving:.1f}%")
print(f"--------------------------------------------------")

h_content.append("#endif /* DANDY_LEVELS_H */")

print(f"Writing C header to {output_h_path}...")
with open(output_h_path, "w") as f:
    f.write("\n".join(h_content))

print("Conversion complete!")
