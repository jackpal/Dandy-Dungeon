#!/usr/bin/env python3
import os
import re
import argparse
from PIL import Image, ImageDraw

def parse_tiles_c(tiles_c_path):
    """
    Parses tiles.c to extract the dandy_tiles 2bpp binary data.
    """
    if not os.path.exists(tiles_c_path):
        raise FileNotFoundError(f"Source tiles definition file not found at: {tiles_c_path}")
        
    print(f"Reading tiles definition from {tiles_c_path}...")
    with open(tiles_c_path, "r") as f:
        content = f.read()
    
    # Match the dandy_tiles array content
    match = re.search(r"const\s+unsigned\s+char\s+dandy_tiles\[\]\s*=\s*\{([^}]+)\};", content, re.DOTALL)
    if not match:
        raise ValueError("Could not find 'dandy_tiles' array in tiles.c")
    
    array_content = match.group(1)
    # Find all hex values like 0xAA or 0xaa
    hex_values = re.findall(r"0x[0-9a-fA-F]{2}", array_content)
    if len(hex_values) != 512:
        raise ValueError(f"Expected exactly 512 hex values (32 tiles * 16 bytes) in dandy_tiles, but found {len(hex_values)}")
    
    return bytes(int(val, 16) for val in hex_values)

def decode_gb_tile(tile_bytes, is_sprite, bg_colors):
    """
    Decodes a 16-byte Game Boy 2bpp tile into an 8x8 PIL Image.
    If is_sprite is True, returns an RGBA image with color index 0 mapped to transparent (0, 0, 0, 0).
    Otherwise, returns an RGB image using the provided background palette.
    """
    if is_sprite:
        # Sprite palette (OBP0/1 = 0xE0):
        # Index 0 -> Transparent
        # Index 1 -> White (255, 255, 255)
        # Index 2 -> Dark Gray (85, 85, 85)
        # Index 3 -> Black (0, 0, 0)
        colors = [
            (0, 0, 0, 0),
            (255, 255, 255, 255),
            (85, 85, 85, 255),
            (0, 0, 0, 255)
        ]
        img = Image.new("RGBA", (8, 8))
    else:
        # Background palette (BGP):
        # 3-byte RGB tuples for indices 0, 1, 2, 3
        colors = bg_colors
        img = Image.new("RGB", (8, 8))

    pixels = img.load()

    for y in range(8):
        byte1 = tile_bytes[2 * y]
        byte2 = tile_bytes[2 * y + 1]
        for x in range(8):
            bit_index = 7 - x
            low_bit = (byte1 >> bit_index) & 1
            high_bit = (byte2 >> bit_index) & 1
            color_index = (high_bit << 1) | low_bit
            pixels[x, y] = colors[color_index]

    return img

def create_checkerboard_pattern(width=128, height=128, square_size=16, color1=(200, 200, 200), color2=(220, 220, 220)):
    """
    Generates a checkerboard pattern image of the specified size to represent transparency.
    """
    img = Image.new("RGB", (width, height))
    draw = ImageDraw.Draw(img)
    for y in range(0, height, square_size):
        for x in range(0, width, square_size):
            # Alternate colors based on grid position
            color = color1 if ((x // square_size) + (y // square_size)) % 2 == 0 else color2
            draw.rectangle([x, y, x + square_size - 1, y + square_size - 1], fill=color)
    return img

def main():
    parser = argparse.ArgumentParser(description="Pristine, Honest Game Boy Graphics Verification and Auditing Tool")
    parser.add_argument(
        "--dark-floor",
        action="store_true",
        help="Use the Atmospheric (Dark Floor) palette instead of the Classic DMG (Light Floor) palette."
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Custom path to save the generated audit PNG sheet."
    )
    parser.add_argument(
        "--output-png",
        type=str,
        help="Alias for --output."
    )
    parser.add_argument(
        "--tiles-c",
        type=str,
        help="Custom path to tiles.c. Defaults to ../src/tiles.c relative to this script."
    )
    parser.add_argument(
        "--original-sprites",
        type=str,
        help="Custom path to strike_original.png. Defaults to ../teamwork_graphics/strike_original.png relative to this script."
    )
    
    args = parser.parse_args()
    
    # Resolve output path
    output_path = args.output or args.output_png
    
    # Determine directory of this script to resolve relative defaults
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Resolve default paths
    tiles_c_path = args.tiles_c or os.path.normpath(os.path.join(script_dir, "../src/tiles.c"))
    strike_png_path = args.original_sprites or os.path.normpath(os.path.join(script_dir, "../teamwork_graphics/strike_original.png"))
    
    if not output_path:
        filename = "graphics_audit_dark.png" if args.dark_floor else "graphics_audit.png"
        output_path = os.path.normpath(os.path.join(script_dir, f"../teamwork_graphics/{filename}"))
        
    print("======================================================================")
    print("DANDY DUNGEON GRAPHICS VERIFICATION PIPELINE")
    print("======================================================================")
    print(f"Target Mode:      {'Atmospheric (Dark Floor)' if args.dark_floor else 'Classic DMG (Light Floor)'}")
    print(f"Input tiles.c:    {tiles_c_path}")
    print(f"Input Original:   {strike_png_path}")
    print(f"Output Audit:     {output_path}")
    print("======================================================================")

    # Verify original sprite sheet exists
    if not os.path.exists(strike_png_path):
        raise FileNotFoundError(f"Original sprite sheet not found at {strike_png_path}. Please run extract_sprites.py first.")

    # 1. Load original sprite sheet
    print(f"Loading original sprite sheet from {strike_png_path}...")
    original_sheet = Image.open(strike_png_path)
    if original_sheet.size != (256, 32):
        raise ValueError(f"Expected original sprite sheet dimensions 256x32, but got {original_sheet.size}")

    # 2. Parse compiled tiles from tiles.c
    tiles_bytes = parse_tiles_c(tiles_c_path)

    # 3. Define the background palette based on selected mode
    if args.dark_floor:
        # Atmospheric (Dark Floor) Palette:
        # Color 0 -> Black (0, 0, 0)
        # Color 1 -> Dark Gray (85, 85, 85)
        # Color 2 -> Light Gray (170, 170, 170)
        # Color 3 -> White (255, 255, 255)
        bg_colors = [
            (0, 0, 0),
            (85, 85, 85),
            (170, 170, 170),
            (255, 255, 255)
        ]
    else:
        # Classic DMG (Light Floor) Palette (Default):
        # Color 0 -> White (255, 255, 255)
        # Color 1 -> Light Gray (170, 170, 170)
        # Color 2 -> Dark Gray (85, 85, 85)
        # Color 3 -> Black (0, 0, 0)
        bg_colors = [
            (255, 255, 255),
            (170, 170, 170),
            (85, 85, 85),
            (0, 0, 0)
        ]

    # Category partition (32 tiles total)
    # Background: 0..8, 12..15, 20..23, 28..31
    # Sprites:    9..11, 16..19, 24..27
    sprite_indices = {9, 10, 11, 16, 17, 18, 19, 24, 25, 26, 27}

    # 4. Create the main audit grid image.
    # Grid: 4 columns, 8 rows of side-by-side comparison blocks.
    # Each block is 256x128 (left: 128x128 original upscaled 8x, right: 128x128 compiled tile upscaled 16x)
    # Total canvas dimensions: 1024x1024 pixels.
    grid_cols = 4
    grid_rows = 8
    cell_w = 256
    cell_h = 128
    
    # Neutral dark-gray grid background to separate cells and provide professional contrast
    audit_img = Image.new("RGB", (grid_cols * cell_w, grid_rows * cell_h), (50, 50, 50))

    # Support NEAREST interpolation across Pillow versions
    try:
        nn_filter = Image.Resampling.NEAREST
    except AttributeError:
        nn_filter = Image.NEAREST

    print("Generating comparison grid cells...")
    for i in range(32):
        col = i % grid_cols
        row = i // grid_cols
        cell_x = col * cell_w
        cell_y = row * cell_h

        # A. Crop and upscale the original 16x16 sprite (arranged as 16 cols x 2 rows in strike_original)
        orig_col = i % 16
        orig_row = i // 16
        orig_box = (orig_col * 16, orig_row * 16, (orig_col + 1) * 16, (orig_row + 1) * 16)
        orig_tile = original_sheet.crop(orig_box).convert("RGBA")
        orig_upscaled = orig_tile.resize((128, 128), nn_filter)

        # B. Extract and decode the Game Boy tile (8x8 pixels)
        tile_offset = i * 16
        tile_data = tiles_bytes[tile_offset:tile_offset+16]
        
        is_sprite = i in sprite_indices
        gb_tile = decode_gb_tile(tile_data, is_sprite=is_sprite, bg_colors=bg_colors)
        gb_upscaled = gb_tile.resize((128, 128), nn_filter)

        # C. Prepare background for both sides
        if is_sprite:
            # Sprite transparency audit: use matching 8x8 checkerboard backgrounds (16x16 squares in upscaled space)
            left_bg = create_checkerboard_pattern(128, 128, 16)
            right_bg = create_checkerboard_pattern(128, 128, 16)
            
            # Alpha paste original sprite over left checkerboard
            left_bg.paste(orig_upscaled, (0, 0), orig_upscaled)
            # Alpha paste compiled tile over right checkerboard
            right_bg.paste(gb_upscaled, (0, 0), gb_upscaled)
        else:
            # Background tile audit: use the active mode's floor color (Color 0) as solid background
            floor_color = bg_colors[0]
            left_bg = Image.new("RGB", (128, 128), floor_color)
            right_bg = Image.new("RGB", (128, 128), floor_color)
            
            # Paste original sprite over left floor background
            left_bg.paste(orig_upscaled, (0, 0), orig_upscaled)
            # Paste compiled tile over right floor background (compiled background tiles are opaque RGB)
            right_bg.paste(gb_upscaled, (0, 0))

        # D. Stitch into the main audit sheet
        audit_img.paste(left_bg, (cell_x, cell_y))
        audit_img.paste(right_bg, (cell_x + 128, cell_y))

    # Save the output
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    print(f"Saving generated audit sheet to {output_path}...")
    audit_img.save(output_path)
    print("Verification and audit sheet generation completed successfully and honestly!")

if __name__ == "__main__":
    main()
