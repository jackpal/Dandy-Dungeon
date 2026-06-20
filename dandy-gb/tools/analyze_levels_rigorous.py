#!/usr/bin/env python3
import json
import os
import re
from collections import Counter

# File paths
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
LEVELS_JS = os.path.normpath(os.path.join(CURRENT_DIR, "../../dandy-js/levels.js"))
OUTPUT_JSON = os.path.normpath(os.path.join(CURRENT_DIR, "analysis_results.json"))
OUTPUT_MD = os.path.normpath(os.path.join(CURRENT_DIR, "analysis_summary.md"))

# Encoding
ENCODING = " *DudKF$i123mnop"

def char_to_id(c):
    try:
        return ENCODING.index(c)
    except ValueError:
        return 0

def main():
    print(f"Reading levels from {LEVELS_JS}...")
    if not os.path.exists(LEVELS_JS):
        print(f"Error: {LEVELS_JS} does not exist.")
        return

    with open(LEVELS_JS, "r") as f:
        content = f.read()

    # Parse levels by extracting all 60-character double-quoted strings
    all_strings = re.findall(r'"([^"\n]{60})"', content)
    
    # Group into levels (each level is exactly 30 rows)
    levels = []
    for i in range(0, len(all_strings), 30):
        level_chunk = all_strings[i:i+30]
        if len(level_chunk) == 30:
            levels.append(level_chunk)
        else:
            print(f"Warning: Found incomplete level chunk at index {i} (length {len(level_chunk)})")

    print(f"Successfully parsed {len(levels)} levels.")
    if len(levels) != 26:
        print(f"Error: Expected 26 levels, but parsed {len(levels)}.")
        return

    # 1. Tile Frequency Analysis
    tile_counts = Counter()
    total_tiles = 0
    for lvl in levels:
        for row in lvl:
            for c in row:
                tile_counts[c] += 1
                total_tiles += 1

    tile_frequencies = {}
    for idx, char in enumerate(ENCODING):
        count = tile_counts.get(char, 0)
        percentage = (count / total_tiles) * 100
        tile_frequencies[str(idx)] = {
            "char": char,
            "count": count,
            "percentage": round(percentage, 3)
        }

    # 2. Edge Wall Elision Analysis
    non_wall_border_tiles = []
    
    # Outer border is: row 0, row 29, column 0, column 59
    for l_idx, lvl in enumerate(levels):
        for r in range(30):
            for c in range(60):
                is_border = (r == 0 or r == 29 or c == 0 or c == 59)
                if is_border:
                    char = lvl[r][c]
                    if char != '*':
                        non_wall_border_tiles.append({
                            "level_index": l_idx,
                            "row": r,
                            "col": c,
                            "char": char,
                            "tile_id": char_to_id(char)
                        })

    is_100_percent_walls = len(non_wall_border_tiles) == 0

    # Calculate exact storage savings of omitting border walls
    # Total border tiles per level: 60 (top) + 60 (bottom) + 28 (left) + 28 (right) = 176
    # Uncompressed level: 1800 tiles. 4-bit packed: 900 bytes.
    # Elided level: 1624 tiles. 4-bit packed: 812 bytes.
    # Savings per level: 88 bytes.
    savings_bytes_per_level = 88
    savings_percentage = (savings_bytes_per_level / 900.0) * 100.0
    db_size_without_elision_bytes = 26 * 900
    db_size_with_elision_bytes = 26 * 812
    total_savings_bytes = db_size_without_elision_bytes - db_size_with_elision_bytes

    border_analysis = {
        "is_100_percent_walls": is_100_percent_walls,
        "non_wall_tiles_count": len(non_wall_border_tiles),
        "non_wall_tiles": non_wall_border_tiles,
        "savings_bytes_per_level": savings_bytes_per_level,
        "savings_percentage": round(savings_percentage, 3),
        "database_size_without_elision_bytes": db_size_without_elision_bytes,
        "database_size_with_elision_bytes": db_size_with_elision_bytes,
        "total_savings_bytes": total_savings_bytes
    }

    # 3. Spatial Repetition (Meta-tiles)
    def extract_blocks(block_w, block_h, use_inner=False):
        blocks = []
        for lvl in levels:
            if use_inner:
                start_r, end_r = 1, 29
                start_c, end_c = 1, 59
            else:
                start_r, end_r = 0, 30
                start_c, end_c = 0, 60

            r_range = range(start_r, end_r - block_h + 1, block_h)
            c_range = range(start_c, end_c - block_w + 1, block_w)

            for r in r_range:
                for c in c_range:
                    block = []
                    for br in range(block_h):
                        for bc in range(block_w):
                            block.append(char_to_id(lvl[r + br][c + bc]))
                    blocks.append(tuple(block))
        return blocks

    meta_tiles = {}
    for config_name, config_use_inner in [("full_map", False), ("inner_map", True)]:
        meta_tiles[config_name] = {}
        for size_name, (w, h) in [("2x2", (2, 2)), ("2x3", (2, 3)), ("4x4", (4, 4))]:
            blocks = extract_blocks(w, h, use_inner=config_use_inner)
            counter = Counter(blocks)
            total_blocks = len(blocks)
            unique_blocks = len(counter)

            top_10 = []
            for block, count in counter.most_common(10):
                percentage = (count / total_blocks) * 100
                top_10.append({
                    "block": list(block),
                    "count": count,
                    "percentage": round(percentage, 3)
                })

            meta_tiles[config_name][size_name] = {
                "total_blocks": total_blocks,
                "unique_blocks": unique_blocks,
                "top_10": top_10
            }

    # Write raw output to JSON
    results = {
        "tile_frequencies": tile_frequencies,
        "border_analysis": border_analysis,
        "meta_tiles": meta_tiles
    }

    print(f"Writing raw results to {OUTPUT_JSON}...")
    with open(OUTPUT_JSON, "w") as f:
        json.dump(results, f, indent=2)

    # Generate human-readable Markdown summary
    print(f"Writing Markdown summary to {OUTPUT_MD}...")
    generate_markdown_summary(results)
    print("Analysis complete!")

def generate_markdown_summary(results):
    md = []
    md.append("# Dandy Dungeon Level Analysis Report")
    md.append("")
    md.append("This report presents a rigorous statistical analysis of all 26 levels of Dandy Dungeon. The analysis is designed to identify redundancy and spatial structures to guide the design of an optimal custom 2D compression algorithm for the GameBoy port.")
    md.append("")

    # Section 1: Tile Frequency Analysis
    md.append("## 1. Tile Frequency Analysis")
    md.append("")
    md.append("Total tiles analyzed across all 26 levels: **46,800** (26 levels × 60 columns × 30 rows).")
    md.append("")
    md.append("| ID | Char | Name | Count | Percentage |")
    md.append("|----|------|------|-------|------------|")
    
    tile_names = {
        0: "Space (Empty)", 1: "Wall", 2: "Door", 3: "Stairs Up",
        4: "Stairs Down", 5: "Key", 6: "Food", 7: "Money",
        8: "Bomb", 9: "Monster 1", 10: "Monster 2", 11: "Monster 3",
        12: "Heart (Extra Life)", 13: "Monster 4 (Ghost/Bat)",
        14: "Monster 5 (Spider)", 15: "Monster 6 (Wizard)"
    }
    
    for tile_id in range(16):
        data = results["tile_frequencies"][str(tile_id)]
        name = tile_names.get(tile_id, "Unknown")
        char = data["char"]
        if char == " ":
            char_display = "` ` (Space)"
        else:
            char_display = f"`{char}`"
        md.append(f"| {tile_id:2d} | {char_display} | {name} | {data['count']:,} | {data['percentage']:.3f}% |")
    
    md.append("")
    
    # Section 2: Edge Wall Elision Analysis
    border = results["border_analysis"]
    md.append("## 2. Edge Wall Elision Analysis")
    md.append("")
    md.append("Inspecting the outer borders (row 0, row 29, column 0, column 59) of all 26 levels (176 border tiles per level):")
    md.append("")
    if border["is_100_percent_walls"]:
        md.append("- **Verification Result**: ✅ **100% of outer border tiles are Wall tiles (`*`, ID 1) across all 26 levels.**")
    else:
        md.append(f"- **Verification Result**: ⚠️ **Found {border['non_wall_tiles_count']} non-wall tiles on the outer border!**")
        md.append("")
        md.append("| Level | Row | Col | Char | Tile ID |")
        md.append("|-------|-----|-----|------|---------|")
        for tile in border["non_wall_tiles"]:
            md.append(f"| {tile['level_index']} | {tile['row']} | {tile['col']} | `{tile['char']}` | {tile['tile_id']} |")
    md.append("")
    md.append("### Storage Savings with Edge Wall Elision & 4-Bit Packing")
    md.append("")
    md.append("- **Uncompressed level size**: 60 × 30 = 1,800 tiles.")
    md.append("- **Elided level size** (omitting 176 border walls): 1,624 tiles.")
    md.append("- **4-Bit Packing Baseline** (without elision): **900 bytes** per level.")
    md.append("- **4-Bit Packing with Border Elision**: **812 bytes** per level.")
    md.append("- **Savings per level**: **88 bytes**.")
    md.append(f"- **Database size (26 levels)**:")
    md.append(f"  - Baseline (No Elision): **{border['database_size_without_elision_bytes']:,} bytes** ({border['database_size_without_elision_bytes']/1024:.2f} KB)")
    md.append(f"  - With Border Elision: **{border['database_size_with_elision_bytes']:,} bytes** ({border['database_size_with_elision_bytes']/1024:.2f} KB)")
    md.append(f"  - Total savings: **{border['total_savings_bytes']:,} bytes** ({border['total_savings_bytes']/1024:.2f} KB, **{border['savings_percentage']:.3f}%** reduction)")
    md.append("")

    # Section 3: Spatial Repetition (Meta-tiles)
    md.append("## 3. Spatial Repetition (Meta-tiles) Analysis")
    md.append("")
    md.append("Analyzing non-overlapping, grid-aligned block frequencies. This is highly relevant for dictionary-based compression or block-based encoding.")
    md.append("")

    def format_md_block(block, w, h):
        visual_rows = []
        id_rows = []
        for r in range(h):
            vis_row = []
            id_row = []
            for c in range(w):
                tile_id = block[r * w + c]
                vis_row.append(ENCODING[tile_id])
                id_row.append(f"{tile_id:x}")
            visual_rows.append("".join(vis_row))
            id_rows.append("".join(id_row))
        
        vis_str = "<br>".join([f"`{r}`" for r in visual_rows])
        id_str = f"`{'/'.join(id_rows)}`"
        return vis_str, id_str

    for config_key, config_name in [("full_map", "Full 60x30 Map"), ("inner_map", "Inner 58x28 Map (Border Elided)")]:
        md.append(f"### 3.1. {config_name}")
        md.append("")
        
        for size_key in ["2x2", "2x3", "4x4"]:
            size_data = results["meta_tiles"][config_key][size_key]
            w, h = map(int, size_key.split('x'))
            
            md.append(f"#### {size_key} Meta-tiles ({config_name})")
            md.append("")
            md.append(f"- **Total Blocks**: {size_data['total_blocks']:,}")
            md.append(f"- **Unique Blocks**: {size_data['unique_blocks']:,} (out of {16**(w*h):,} possible)")
            md.append("")
            md.append("| Rank | Count | Percentage | Visual Grid | Hex ID String |")
            md.append("|------|-------|------------|-------------|---------------|")
            
            for rank, entry in enumerate(size_data["top_10"]):
                vis, ids = format_md_block(entry["block"], w, h)
                md.append(f"| {rank+1} | {entry['count']:,} | {entry['percentage']:.2f}% | {vis} | {ids} |")
            
            md.append("")

    with open(OUTPUT_MD, "w") as f:
        f.write("\n".join(md))

if __name__ == "__main__":
    main()
