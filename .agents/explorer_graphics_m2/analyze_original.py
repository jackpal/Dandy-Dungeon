import os
from PIL import Image
import numpy as np

def analyze():
    img_path = '/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb/teamwork_graphics/strike_original.png'
    if not os.path.exists(img_path):
        print(f"Error: {img_path} does not exist.")
        return
    
    img = Image.open(img_path)
    print(f"Image format: {img.format}, size: {img.size}, mode: {img.mode}")
    
    # Get all unique colors in the image
    colors = img.getcolors(maxcolors=256)
    print(f"Unique colors in the entire sheet (count, color):")
    for count, color in sorted(colors, reverse=True):
        print(f"  {count:5d} : {color}")
        
    # Analyze each tile
    tile_w, tile_h = 16, 16
    cols = img.width // tile_w
    rows = img.height // tile_h
    
    print(f"\nGrid size: {cols}x{rows} tiles")
    
    # Let's map unique colors across all tiles
    # We want to see what colors appear in which tiles
    for r in range(rows):
        for c in range(cols):
            tile_idx = r * cols + c
            # Crop tile
            box = (c * tile_w, r * tile_h, (c + 1) * tile_w, (r + 1) * tile_h)
            tile = img.crop(box)
            tile_colors = tile.getcolors()
            print(f"Tile {tile_idx:2d} (row {r}, col {c}) unique colors:")
            for count, color in tile_colors:
                print(f"  - {count:3d} px of {color}")

if __name__ == '__main__':
    analyze()
