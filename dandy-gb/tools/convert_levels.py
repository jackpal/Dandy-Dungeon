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

print(f"Reading levels from {levels_js_path}...")
with open(levels_js_path, "r") as f:
    content = f.read()

# Find all double-quoted strings in levels.js
# Dandy levels are strictly 60 characters wide and 30 characters high.
# We can extract all double-quoted strings of length 60 and group them into blocks of 30.
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
h_content.append("#define TILE_PLAYER1     24")  # kArrow + 8
h_content.append("")

# Write level data array
h_content.append(f"const uint8_t dandy_levels[DANDY_NUM_LEVELS][DANDY_LEVEL_HEIGHT * DANDY_LEVEL_WIDTH] = {{")

for l_idx, lvl in enumerate(levels):
    h_content.append(f"    /* Level {l_idx} */")
    h_content.append("    {")
    for r_idx, row in enumerate(lvl):
        tile_ids = [str(char_to_tile_id(c)) for c in row]
        while len(tile_ids) < 60:
            tile_ids.append("0")
        row_str = ", ".join(tile_ids)
        comma = "," if r_idx < len(lvl) - 1 else ""
        h_content.append(f"        {row_str}{comma} /* Row {r_idx} */")
    comma = "," if l_idx < len(levels) - 1 else ""
    h_content.append(f"    }}{comma}")

h_content.append("};")
h_content.append("")
h_content.append("#endif /* DANDY_LEVELS_H */")

print(f"Writing C header to {output_h_path}...")
with open(output_h_path, "w") as f:
    f.write("\n".join(h_content))

print("Conversion complete!")
