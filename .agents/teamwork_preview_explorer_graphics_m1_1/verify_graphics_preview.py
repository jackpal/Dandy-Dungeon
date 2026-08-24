import os
import re
from PIL import Image

def parse_tiles_c(file_path):
    with open(file_path, "r") as f:
        content = f.read()
    match = re.search(r"const\s+unsigned\s+char\s+dandy_tiles\[\]\s*=\s*\{([^}]+)\};", content)
    if not match:
        raise ValueError("Could not find dandy_tiles array in tiles.c")
    array_content = match.group(1)
    hex_values = re.findall(r"0x[0-9a-fA-F]{2}", array_content)
    return bytes(int(val, 16) for val in hex_values)

def decode_gb_tile(tile_bytes, is_sprite=False):
    # Standard palettes
    # Background (BGP): 0=Black, 1=Dark Gray, 2=Light Gray, 3=White
    bg_colors = [
        (0, 0, 0),        # 0: Black
        (96, 96, 96),     # 1: Dark Gray
        (176, 176, 176),  # 2: Light Gray
        (255, 255, 255)   # 3: White
    ]
    # Sprite (OBP0): 0=Transparent/Black, 1=White, 2=Dark Gray, 3=Black
    sprite_colors = [
        (0, 0, 0),        # 0: Transparent (rendered as Black in audit)
        (255, 255, 255),  # 1: White
        (96, 96, 96),     # 2: Dark Gray
        (0, 0, 0)         # 3: Black
    ]
    
    colors = sprite_colors if is_sprite else bg_colors
    
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

def main():
    working_dir = "/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/.agents/teamwork_preview_explorer_graphics_m1_1"
    tiles_c_path = "/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb/src/tiles.c"
    strike_png_path = os.path.join(working_dir, "strike_original.png")
    audit_png_path = os.path.join(working_dir, "graphics_audit_preview.png")
    
    print("Parsing GameBoy tiles from tiles.c...")
    tiles_data = parse_tiles_c(tiles_c_path)
    print(f"Total tile bytes parsed: {len(tiles_data)} ({len(tiles_data) // 16} tiles)")
    
    print("Loading original sprite sheet...")
    strike_img = Image.open(strike_png_path)
    print(f"Original image size: {strike_img.size}")
    
    # We will create a grid of 32 tiles, arranged as 8 rows and 4 columns.
    # Each cell in the grid will contain:
    # [Original 16x16 upscaled 8x (128x128)] [GameBoy 8x8 upscaled 16x (128x128)]
    # Total cell size: 256x128
    # Grid size: 1024x1024 (4 columns * 256 width, 8 rows * 128 height)
    
    grid_img = Image.new("RGB", (1024, 1024), (50, 50, 50)) # Gray background for grid lines
    
    # Background tile indices
    bg_indices = set(list(range(9)) + list(range(12, 16)))
    
    for i in range(32):
        # 1. Get original 16x16 tile
        # The original image is 256x32 (16 columns, 2 rows of 16x16 tiles)
        orig_col = i % 16
        orig_row = i // 16
        orig_box = (orig_col * 16, orig_row * 16, (orig_col + 1) * 16, (orig_row + 1) * 16)
        orig_tile = strike_img.crop(orig_box)
        orig_tile_scaled = orig_tile.resize((128, 128), Image.NEAREST)
        
        # 2. Get decoded GameBoy tile
        gb_tile_bytes = tiles_data[i * 16 : (i + 1) * 16]
        is_sprite = i not in bg_indices
        gb_tile = decode_gb_tile(gb_tile_bytes, is_sprite=is_sprite)
        gb_tile_scaled = gb_tile.resize((128, 128), Image.NEAREST)
        
        # 3. Paste into grid
        grid_col = i % 4
        grid_row = i // 4
        
        cell_x = grid_col * 256
        cell_y = grid_row * 128
        
        # Paste original on left, GB on right, with 1px border
        grid_img.paste(orig_tile_scaled, (cell_x + 1, cell_y + 1))
        grid_img.paste(gb_tile_scaled, (cell_x + 129, cell_y + 1))
        
    print(f"Saving audit image to {audit_png_path}...")
    grid_img.save(audit_png_path)
    print("Audit image saved successfully!")

if __name__ == "__main__":
    main()
