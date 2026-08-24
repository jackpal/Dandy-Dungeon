import os
import numpy as np
from PIL import Image

def get_char_for_idx(idx):
    # Map index to a character representation
    # 0: Light Blue/White -> 'L' (or '.' in DMG context, but let's use a clear symbol)
    # 1: Red -> 'R'
    # 2: Blue -> 'B'
    # 3: Black -> 'K'
    return ['.', 'B', 'R', 'K'][idx]

def get_tile_text_lines(tile):
    h, w = tile.shape
    lines = []
    for y in range(h):
        lines.append("".join(get_char_for_idx(tile[y, x]) for x in range(w)))
    return lines

def main():
    # We will load the downscaled results by running the downscale functions on the fly
    # (or loading from our saved files if we want, but doing it on the fly is easy and clean)
    from downscale_graphics import load_and_index_sheet, downscale_nearest, downscale_majority, downscale_hinted
    
    indexed_sheet, _ = load_and_index_sheet()
    tile_w, tile_h = 16, 16
    
    # We want to compare Tile 1 (Wall) and Tile 7 (Dollar sign)
    for target_idx in [1, 7]:
        r, c = target_idx // 16, target_idx % 16
        orig_tile = indexed_sheet[r*tile_h:(r+1)*tile_h, c*tile_w:(c+1)*tile_w]
        
        nn_tile = downscale_nearest(orig_tile)
        maj_tile = downscale_majority(orig_tile, 'dark')
        hint_tile = downscale_hinted(orig_tile, target_idx)
        
        orig_lines = get_tile_text_lines(orig_tile)
        nn_lines = get_tile_text_lines(nn_tile)
        maj_lines = get_tile_text_lines(maj_tile)
        hint_lines = get_tile_text_lines(hint_tile)
        
        # Pad the 8x8 tiles to align with the 16x16 original
        # For 8x8, we can double each character or just print them side-by-side with padding
        # Let's print them side-by-side. Since they have different heights, we can print them like:
        # Line 0..7: original (16 chars) | NN (8 chars) | Majority (8 chars) | Hinted (8 chars)
        # Line 8..15: original (16 chars) | (8 spaces) | (8 spaces) | (8 spaces)
        
        print(f"\n==================================================")
        print(f"TILE {target_idx} COMPARISON (Original vs NN vs Majority vs Hinted)")
        print(f"==================================================")
        print(f"{'Original (16x16)':<18} | {'NN (8x8)':<8} | {'Maj (8x8)':<8} | {'Hint (8x8)':<8}")
        print(f"-------------------+----------+----------+----------")
        
        for y in range(16):
            orig_str = orig_lines[y]
            if y < 8:
                nn_str = nn_lines[y]
                maj_str = maj_lines[y]
                hint_str = hint_lines[y]
            else:
                nn_str = " " * 8
                maj_str = " " * 8
                hint_str = " " * 8
                
            print(f"{orig_str:<18} | {nn_str:<8} | {maj_str:<8} | {hint_str:<8}")

if __name__ == '__main__':
    main()
