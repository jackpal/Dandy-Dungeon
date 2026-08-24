#!/usr/bin/env python3
"""
test_2bpp_decoding.py
Independent tests to verify GBDK 2bpp decoding math and nearest-neighbor upscaling.
"""

import sys
import os
from PIL import Image

# Add tools directory to path to import verify_graphics if needed,
# but we can also just copy/re-implement the decoder to test it independently,
# or import it directly. Let's import it.
sys.path.append("/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb/tools")
try:
    import verify_graphics
except ImportError as e:
    print(f"Failed to import verify_graphics: {e}")
    sys.exit(1)

def test_decoding_correctness():
    print("Running test_decoding_correctness...")
    
    # 1. Define a target pixel pattern (8x8) using color indices 0, 1, 2, 3
    # Let's create a known grid where each row has a different color pattern
    expected_grid = [
        [0, 1, 2, 3, 0, 1, 2, 3], # Row 0: alternating 0,1,2,3
        [3, 2, 1, 0, 3, 2, 1, 0], # Row 1: alternating 3,2,1,0
        [0, 0, 0, 0, 3, 3, 3, 3], # Row 2: solid halves
        [1, 1, 1, 1, 2, 2, 2, 2], # Row 3: solid halves
        [0, 2, 0, 2, 1, 3, 1, 3], # Row 4
        [3, 1, 3, 1, 2, 0, 2, 0], # Row 5
        [0, 1, 0, 1, 0, 1, 0, 1], # Row 6: checkerboard color 0/1
        [2, 3, 2, 3, 2, 3, 2, 3], # Row 7: checkerboard color 2/3
    ]
    
    # 2. Manually construct the GBDK 2bpp byte representation of this grid
    tile_bytes = []
    for r in range(8):
        row_pixels = expected_grid[r]
        low_byte = 0
        high_byte = 0
        for c in range(8):
            val = row_pixels[c]
            bit0 = val & 1
            bit1 = (val >> 1) & 1
            low_byte |= (bit0 << (7 - c))
            high_byte |= (bit1 << (7 - c))
        tile_bytes.append(low_byte)
        tile_bytes.append(high_byte)
        
    print(f"Generated tile bytes: {[hex(b) for b in tile_bytes]}")
    
    # 3. Decode using verify_graphics.decode_2bpp_tile
    decoded_img = verify_graphics.decode_2bpp_tile(tile_bytes)
    
    # 4. Verify decoded pixel colors match the expected palette colors
    decoded_pixels = decoded_img.load()
    for r in range(8):
        for c in range(8):
            color_idx = expected_grid[r][c]
            expected_color = verify_graphics.PALETTE[color_idx]
            actual_color = decoded_pixels[c, r]
            if actual_color != expected_color:
                print(f"Error: Mismatch at ({c}, {r}). Expected color index {color_idx} ({expected_color}), but got {actual_color}.")
                return False
                
    print("Decoding correctness test PASSED!")
    return True

def test_upscaling_correctness():
    print("Running test_upscaling_correctness...")
    
    # Create a simple 8x8 image with a single non-black pixel at (3, 4)
    img = Image.new('RGBA', (8, 8), (0, 0, 0, 255))
    pixels = img.load()
    target_color = (255, 255, 255, 255)
    pixels[3, 4] = target_color
    
    # Upscale 16x using nearest-neighbor (to 128x128)
    scale = 16
    upscaled_img = img.resize((128, 128), Image.NEAREST)
    upscaled_pixels = upscaled_img.load()
    
    # Verify that the pixel at (3, 4) becomes a perfect 16x16 block from x=[48..63], y=[64..79]
    # And all other pixels are black
    for y in range(128):
        orig_y = y // scale
        for x in range(128):
            orig_x = x // scale
            
            actual_color = upscaled_pixels[x, y]
            if orig_x == 3 and orig_y == 4:
                expected_color = target_color
            else:
                expected_color = (0, 0, 0, 255)
                
            if actual_color != expected_color:
                print(f"Error in upscaling: Mismatch at upscaled ({x}, {y}) [original ({orig_x}, {orig_y})]. Expected {expected_color}, but got {actual_color}.")
                return False
                
    print("Nearest-neighbor upscaling correctness test PASSED!")
    return True

if __name__ == "__main__":
    success = True
    if not test_decoding_correctness():
        success = False
    if not test_upscaling_correctness():
        success = False
        
    if success:
        print("All correctness tests passed!")
        sys.exit(0)
    else:
        print("Some correctness tests failed!")
        sys.exit(1)
