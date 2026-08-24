#!/usr/bin/env python3
import os
import re
import argparse
from PIL import Image, ImageDraw

# ==============================================================================
# PALETTE DEFINITIONS (GameBoy DMG Grayscale Colors)
# ==============================================================================
# Classic DMG (Light Floor) Palette:
# Color 0 (Floor/Lightest) -> White
# Color 1                  -> Light Gray
# Color 2                  -> Dark Gray
# Color 3 (Walls/Darkest)  -> Black
PALETTE_LIGHT = {
    0: (255, 255, 255),  # White
    1: (170, 170, 170),  # Light Gray
    2: (85, 85, 85),     # Dark Gray
    3: (0, 0, 0)         # Black
}

# Atmospheric (Dark Floor) Palette:
# Color 0 (Floor/Darkest)  -> Black
# Color 1                  -> Dark Gray
# Color 2                  -> Light Gray
# Color 3 (Walls/Lightest) -> White
PALETTE_DARK = {
    0: (0, 0, 0),        # Black
    1: (85, 85, 85),     # Dark Gray
    2: (170, 170, 170),  # Light Gray
    3: (255, 255, 255)   # White
}

# Sprite Palette (OBP0/OBP1):
# Color 0 -> Transparent
# Color 1 -> White
# Color 2 -> Dark Gray
# Color 3 -> Black
# For sprite tiles, Color 0 is always transparent regardless of background mode.
PALETTE_SPRITE = {
    0: (0, 0, 0, 0),          # Transparent
    1: (255, 255, 255, 255),  # White
    2: (85, 85, 85, 255),     # Dark Gray
    3: (0, 0, 0, 255)         # Black
}

# ==============================================================================
# TILE CLASSIFICATION (From compile_bmp_sprites.py specifications)
# ==============================================================================
# Out of 32 tiles:
# - Sprite tiles: Monsters (9..11), Arrows (16..19), Player 1 directions (24..27)
# - Background tiles: Space, Wall, Door, Stairs, Items, Monoliths, and Padding (all others)
SPRITE_INDICES = {9, 10, 11, 16, 17, 18, 19, 24, 25, 26, 27}

# ==============================================================================
# CORE HELPER FUNCTIONS
# ==============================================================================
def parse_tiles_c(tiles_c_path):
    """
    Parses the GBDK 2bpp planar tile data from src/tiles.c.
    Returns a bytes object containing the 512 bytes (32 tiles * 16 bytes/tile).
    """
    print(f"Reading compiled tiles from: {tiles_c_path}")
    if not os.path.exists(tiles_c_path):
        raise FileNotFoundError(f"Source file not found: {tiles_c_path}")

    with open(tiles_c_path, "r") as f:
        content = f.read()

    # Match the dandy_tiles array content
    match = re.search(r"const\s+unsigned\s+char\s+dandy_tiles\[\]\s*=\s*\{([^}]+)\};", content, re.DOTALL)
    if not match:
        raise ValueError("Could not find 'dandy_tiles' array declaration in tiles.c")

    array_content = match.group(1)
    
    # Extract all hex values (e.g., 0xAA or 0xaa)
    hex_values = re.findall(r"0x[0-9a-fA-F]{2}", array_content)
    if len(hex_values) != 512:
        raise ValueError(f"Invalid tiles.c: Expected 512 hex values, but found {len(hex_values)}")

    print(f"Successfully parsed 512 byte values from tiles.c.")
    return bytes(int(val, 16) for val in hex_values)

def decode_gb_tile(tile_bytes, is_sprite, use_dark_floor):
    """
    Decodes a 16-byte Game Boy 2bpp planar tile into an 8x8 PIL Image.
    For sprite tiles: returns an RGBA image where Color 0 is transparent (0, 0, 0, 0).
    For background tiles: returns an RGB image mapped to the selected background palette.
    """
    if is_sprite:
        colors = [PALETTE_SPRITE[0], PALETTE_SPRITE[1], PALETTE_SPRITE[2], PALETTE_SPRITE[3]]
        img = Image.new("RGBA", (8, 8))
    else:
        palette = PALETTE_DARK if use_dark_floor else PALETTE_LIGHT
        colors = [palette[0], palette[1], palette[2], palette[3]]
        img = Image.new("RGB", (8, 8))

    pixels = img.load()

    # Decode 8 rows (each row is represented by 2 consecutive bytes)
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

def generate_checkerboard_128(color1=200, color2=220):
    """
    Generates a 128x128 checkerboard image with 16x16 pixel checks.
    This corresponds to a 1x1 check pattern at the 8x8 tile level upscaled 16x.
    """
    img = Image.new("RGB", (8, 8))
    pixels = img.load()
    for y in range(8):
        for x in range(8):
            c = color1 if (x + y) % 2 == 0 else color2
            pixels[x, y] = (c, c, c)
    # Upscale 16x using NEAREST to preserve crisp pixel check borders
    return img.resize((128, 128), Image.Resampling.NEAREST)

# ==============================================================================
# MAIN EXECUTION
# ==============================================================================
def main():
    # Resolve default paths relative to this script's location
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.normpath(os.path.join(script_dir, ".."))
    
    default_tiles_c = os.path.join(project_root, "src", "tiles.c")
    default_strike_png = os.path.join(project_root, "teamwork_graphics", "strike_original.png")

    # Command-line argument parsing
    parser = argparse.ArgumentParser(
        description="Verify compiled GameBoy 2bpp tiles against original HTML5/JS sprite sheet assets."
    )
    parser.add_argument(
        "--dark-floor",
        action="store_true",
        help="Use the Atmospheric (Dark Floor) palette instead of the default Classic DMG (Light Floor) palette."
    )
    parser.add_argument(
        "-o", "--output",
        help="Custom output path for the generated audit image. Defaults to teamwork_graphics/graphics_audit.png "
             "(or graphics_audit_dark.png if --dark-floor is set)."
    )
    parser.add_argument(
        "--tiles-c",
        default=default_tiles_c,
        help=f"Path to the src/tiles.c containing compiled GBDK tile bytes. Default: {default_tiles_c}"
    )
    parser.add_argument(
        "--strike-png",
        default=default_strike_png,
        help=f"Path to the strike_original.png original sprite sheet. Default: {default_strike_png}"
    )

    args = parser.parse_args()

    # Determine output path based on palette choice if not explicitly provided
    if args.output:
        output_path = os.path.abspath(args.output)
    else:
        filename = "graphics_audit_dark.png" if args.dark_floor else "graphics_audit.png"
        output_path = os.path.join(project_root, "teamwork_graphics", filename)

    print("======================================================================")
    print("DANDY GAMEBOY GRAPHICS VERIFICATION TOOL (HONEST COMPILING)")
    print("======================================================================")
    print(f"Mode: {'Atmospheric (Dark Floor)' if args.dark_floor else 'Classic DMG (Light Floor)'}")
    print(f"Original sheet: {args.strike_png}")
    print(f"Target output:  {output_path}")
    print("======================================================================")

    # Verify input original sprite sheet exists
    if not os.path.exists(args.strike_png):
        raise FileNotFoundError(
            f"Original sprite sheet not found at '{args.strike_png}'. "
            f"Please run 'extract_sprites.py' first to extract it from the JS version."
        )

    # 1. Parse tiles.c GBDK bytes
    tiles_bytes = parse_tiles_c(args.tiles_c)

    # 2. Load original sprite sheet
    print(f"Loading original sprite sheet: {args.strike_png}")
    original_sheet = Image.open(args.strike_png)
    if original_sheet.size != (256, 32):
        raise ValueError(f"Expected strike_original.png to be 256x32, got: {original_sheet.size}")

    # 3. Create the main audit grid image
    # Grid: 4 columns, 8 rows of blocks.
    # Each block: 256x128 pixels (left: 128x128 original, right: 128x128 compiled tile).
    # Total image dimensions: 1024x1024 pixels.
    grid_cols = 4
    grid_rows = 8
    cell_w = 256
    cell_h = 128
    
    # Grid background is neutral medium-dark gray (80, 80, 80)
    audit_img = Image.new("RGB", (grid_cols * cell_w, grid_rows * cell_h), (80, 80, 80))

    # Pre-generate backgrounds for stitching comparison blocks
    checkerboard_128 = generate_checkerboard_128(color1=200, color2=220)
    
    bg_floor_color = PALETTE_DARK[0] if args.dark_floor else PALETTE_LIGHT[0]
    solid_bg_128 = Image.new("RGB", (128, 128), bg_floor_color)

    print("Stitching comparison sheet side-by-side...")

    # Iterate through all 32 tiles
    for i in range(32):
        col = i % grid_cols
        row = i // grid_cols
        cell_x = col * cell_w
        cell_y = row * cell_h

        # A. Crop original 16x16 sprite (arranged 16 columns, 2 rows in strike_original.png)
        orig_col = i % 16
        orig_row = i // 16
        orig_box = (orig_col * 16, orig_row * 16, (orig_col + 1) * 16, (orig_row + 1) * 16)
        orig_tile = original_sheet.crop(orig_box)
        
        # Upscale original 8x to 128x128 using NEAREST to avoid blurring
        orig_upscaled = orig_tile.resize((128, 128), Image.Resampling.NEAREST)

        # B. Decode Game Boy 8x8 tile
        tile_offset = i * 16
        tile_data = tiles_bytes[tile_offset : tile_offset + 16]
        is_sprite = i in SPRITE_INDICES
        
        gb_tile = decode_gb_tile(tile_data, is_sprite=is_sprite, use_dark_floor=args.dark_floor)
        
        # Upscale compiled tile 16x to 128x128 using NEAREST
        gb_upscaled = gb_tile.resize((128, 128), Image.Resampling.NEAREST)

        # C. Stitch blocks with appropriate background (checkerboard for sprites, solid for background)
        if is_sprite:
            # Sprite block: checkerboard background to showcase transparency
            left_block = checkerboard_128.copy()
            right_block = checkerboard_128.copy()

            # Paste original (convert to RGBA, use as mask to respect transparency)
            orig_rgba = orig_upscaled.convert("RGBA")
            left_block.paste(orig_rgba, (0, 0), orig_rgba)

            # Paste compiled (use as mask to respect transparency of color 0)
            right_block.paste(gb_upscaled, (0, 0), gb_upscaled)
        else:
            # Background block: solid background of floor color (White or Black depending on palette)
            left_block = solid_bg_128.copy()
            right_block = solid_bg_128.copy()

            # Paste original (use alpha mask if present)
            orig_rgba = orig_upscaled.convert("RGBA")
            left_block.paste(orig_rgba, (0, 0), orig_rgba)

            # Paste compiled (solid RGB, paste directly)
            right_block.paste(gb_upscaled, (0, 0))

        # Paste comparison blocks side-by-side into the main audit grid
        audit_img.paste(left_block, (cell_x, cell_y))
        audit_img.paste(right_block, (cell_x + 128, cell_y))

    # 4. Draw grid lines for clean, professional layout alignment
    print("Drawing grid alignment borders...")
    draw = ImageDraw.Draw(audit_img)
    grid_color = (120, 120, 120)  # Distinct neutral gray for borders

    # Vertical borders between cells (2px wide)
    for col in range(1, grid_cols):
        x = col * cell_w
        draw.line([(x, 0), (x, 1024)], fill=grid_color, width=2)

    # Vertical splitters separating original vs compiled within each cell (1px wide)
    for col in range(grid_cols):
        x = col * cell_w + 128
        draw.line([(x, 0), (x, 1024)], fill=grid_color, width=1)

    # Horizontal borders between cells (2px wide)
    for row in range(1, grid_rows):
        y = row * cell_h
        draw.line([(0, y), (1024, y)], fill=grid_color, width=2)

    # 5. Save the generated audit sheet
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    audit_img.save(output_path)
    print(f"SUCCESS: Generated audit sheet saved to: {output_path}")
    print("Verification complete.")

if __name__ == "__main__":
    main()
