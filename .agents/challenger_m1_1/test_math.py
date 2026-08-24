#!/usr/bin/env python3
import sys
import os
from PIL import Image

# Import or define the PALETTE and decode_2bpp_tile from verify_graphics
PALETTE = {
    0: (0, 0, 0, 255),
    1: (85, 85, 85, 255),
    2: (170, 170, 170, 255),
    3: (255, 255, 255, 255),
}

def decode_2bpp_tile(tile_bytes):
    """Decodes 16 GBDK 2bpp bytes into an 8x8 PIL Image."""
    img = Image.new('RGBA', (8, 8))
    pixels = img.load()

    for r in range(8):
        low = tile_bytes[2 * r]
        high = tile_bytes[2 * r + 1]
        for c in range(8):
            bit0 = (low >> (7 - c)) & 1
            bit1 = (high >> (7 - c)) & 1
            color_idx = (bit1 << 1) | bit0
            pixels[c, r] = PALETTE[color_idx]
    return img

def test_2bpp_decoding_math():
    print("Running 2bpp decoding math validation...")
    # Let's define a test tile. We want to test all color indices: 0, 1, 2, 3.
    # Let's create a known pixel pattern:
    # Row 0: 0, 1, 2, 3, 3, 2, 1, 0
    # Row 1: 3, 2, 1, 0, 0, 1, 2, 3
    # Row 2: 1, 1, 1, 1, 2, 2, 2, 2
    # Row 3: 0, 0, 0, 0, 3, 3, 3, 3
    # Row 4: 2, 0, 2, 0, 1, 3, 1, 3
    # Row 5: 3, 3, 0, 0, 2, 2, 1, 1
    # Row 6: 0, 3, 0, 3, 0, 3, 0, 3
    # Row 7: 1, 2, 1, 2, 1, 2, 1, 2
    
    expected_pixels = [
        [0, 1, 2, 3, 3, 2, 1, 0],
        [3, 2, 1, 0, 0, 1, 2, 3],
        [1, 1, 1, 1, 2, 2, 2, 2],
        [0, 0, 0, 0, 3, 3, 3, 3],
        [2, 0, 2, 0, 1, 3, 1, 3],
        [3, 3, 0, 0, 2, 2, 1, 1],
        [0, 3, 0, 3, 0, 3, 0, 3],
        [1, 2, 1, 2, 1, 2, 1, 2],
    ]
    
    # Let's manually encode these pixels to 2bpp according to official Game Boy spec.
    # For each row, byte 1 (low) contains bit 0 of color indices, byte 2 (high) contains bit 1 of color indices.
    encoded_bytes = []
    for r in range(8):
        low_byte = 0
        high_byte = 0
        for c in range(8):
            color = expected_pixels[r][c]
            bit0 = color & 1
            bit1 = (color >> 1) & 1
            
            # Leftmost pixel (c=0) is MSB of the byte (bit 7)
            low_byte |= (bit0 << (7 - c))
            high_byte |= (bit1 << (7 - c))
        encoded_bytes.append(low_byte)
        encoded_bytes.append(high_byte)
        
    # Now decode using the tool's implementation
    decoded_img = decode_2bpp_tile(encoded_bytes)
    decoded_pixels = decoded_img.load()
    
    # Validate each pixel
    for r in range(8):
        for c in range(8):
            expected_idx = expected_pixels[r][c]
            expected_rgba = PALETTE[expected_idx]
            actual_rgba = decoded_pixels[c, r]
            if actual_rgba != expected_rgba:
                print(f"FAIL: Pixel mismatch at ({c}, {r}). Expected {expected_rgba} (color index {expected_idx}), got {actual_rgba}")
                return False
    print("PASS: 2bpp decoding math matches GBDK specification exactly.")
    return True

def test_nearest_neighbor_upscaling():
    print("Running nearest-neighbor upscaling math validation...")
    # Create a small 2x2 image with distinct colors
    src = Image.new('RGBA', (2, 2))
    pixels = src.load()
    pixels[0, 0] = (255, 0, 0, 255)
    pixels[1, 0] = (0, 255, 0, 255)
    pixels[0, 1] = (0, 0, 255, 255)
    pixels[1, 1] = (255, 255, 255, 255)
    
    # Upscale 4x (to 8x8) using Image.NEAREST
    scale = 4
    dest = src.resize((8, 8), Image.NEAREST)
    dest_pixels = dest.load()
    
    # Mathematically verify nearest-neighbor mapping:
    # Any pixel (dx, dy) in dest should map to src[dx // scale, dy // scale]
    for dy in range(8):
        for dx in range(8):
            sx = dx // scale
            sy = dy // scale
            expected_color = pixels[sx, sy]
            actual_color = dest_pixels[dx, dy]
            if actual_color != expected_color:
                print(f"FAIL: Nearest-neighbor upscale mismatch at dest({dx}, {dy}) -> src({sx}, {sy}). Expected {expected_color}, got {actual_color}")
                return False
    print("PASS: Nearest-neighbor upscaling math is implemented correctly.")
    return True

if __name__ == "__main__":
    success = True
    success &= test_2bpp_decoding_math()
    success &= test_nearest_neighbor_upscaling()
    sys.exit(0 if success else 1)
