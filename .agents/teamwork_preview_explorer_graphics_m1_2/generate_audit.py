import re
import base64
import io
from PIL import Image

def extract_base64_from_js(js_path):
    with open(js_path, 'r') as f:
        content = f.read()
    
    pattern = r'strike\.src\s*=\s*"data:image/png;base64,"\s*\+\s*(.*?;)'
    match = re.search(pattern, content, re.DOTALL)
    if not match:
        raise ValueError("Could not find strike.src base64 data in JS file")
    
    parts_block = match.group(1)
    str_pattern = r'"([^"]*)"'
    strings = re.findall(str_pattern, parts_block)
    return "".join(strings)

def parse_tiles_c(tiles_c_path):
    with open(tiles_c_path, 'r') as f:
        content = f.read()
    
    match = re.search(r'const unsigned char dandy_tiles\[\]\s*=\s*\{(.*?)\};', content, re.DOTALL)
    if not match:
        raise ValueError("Could not find dandy_tiles array in tiles.c")
        
    array_content = match.group(1)
    hex_values = re.findall(r'0x[0-9a-fA-F]{2}', array_content)
    return bytearray(int(val, 16) for val in hex_values)

def decode_gb_tile(tile_bytes, is_sprite=False):
    pixels = bytearray(8 * 8 * 4)
    
    if is_sprite:
        palette = [
            (0, 0, 0, 0),          # 0: Transparent (render transparent)
            (255, 255, 255, 255),  # 1: White
            (100, 100, 100, 255),  # 2: Dark Gray
            (0, 0, 0, 255)         # 3: Black
        ]
    else:
        palette = [
            (0, 0, 0, 255),        # 0: Black
            (100, 100, 100, 255),  # 1: Dark Gray
            (170, 170, 170, 255),  # 2: Light Gray
            (255, 255, 255, 255)   # 3: White
        ]
        
    for y in range(8):
        low_byte = tile_bytes[y * 2]
        high_byte = tile_bytes[y * 2 + 1]
        for x in range(8):
            bit_idx = 7 - x
            bit0 = (low_byte >> bit_idx) & 1
            bit1 = (high_byte >> bit_idx) & 1
            color_idx = (bit1 << 1) | bit0
            
            r, g, b, a = palette[color_idx]
            pixel_idx = (y * 8 + x) * 4
            pixels[pixel_idx] = r
            pixels[pixel_idx+1] = g
            pixels[pixel_idx+2] = b
            pixels[pixel_idx+3] = a
            
    return Image.frombytes("RGBA", (8, 8), bytes(pixels))

def main():
    js_path = "/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-js/strike.js"
    tiles_c_path = "/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb/src/tiles.c"
    output_audit_path = "graphics_audit_test.png"
    
    try:
        # 1. Extract and decode original sprite sheet
        b64_str = extract_base64_from_js(js_path)
        png_bytes = base64.b64decode(b64_str)
        original_sheet = Image.open(io.BytesIO(png_bytes))
        
        # 2. Parse tiles.c
        tiles_bytes = parse_tiles_c(tiles_c_path)
        
        # 3. Create audit image: 8 columns, 4 rows.
        # Each cell is 128x64 (64x64 original, 64x64 Game Boy)
        cell_width = 128
        cell_height = 64
        grid_cols = 8
        grid_rows = 4
        
        audit_image = Image.new("RGBA", (grid_cols * cell_width, grid_rows * cell_height), (50, 50, 50, 255))
        
        # Determine nearest-neighbor filter
        try:
            nn_filter = Image.Resampling.NEAREST
        except AttributeError:
            nn_filter = Image.NEAREST
            
        for i in range(32):
            col = i % grid_cols
            row = i // grid_cols
            
            # Position in audit sheet
            cell_x = col * cell_width
            cell_y = row * cell_height
            
            # Extract original 16x16 tile
            orig_col = i % 16
            orig_row = i // 16
            orig_tile = original_sheet.crop((orig_col * 16, orig_row * 16, (orig_col + 1) * 16, (orig_row + 1) * 16))
            orig_upscaled = orig_tile.resize((64, 64), nn_filter)
            
            # Decode Game Boy 8x8 tile
            tile_offset = i * 16
            tile_data = tiles_bytes[tile_offset:tile_offset+16]
            
            is_sprite = (9 <= i <= 11) or (16 <= i <= 19) or (24 <= i <= 27)
            gb_tile = decode_gb_tile(tile_data, is_sprite=is_sprite)
            gb_upscaled = gb_tile.resize((64, 64), nn_filter)
            
            # Paste side-by-side
            audit_image.paste(orig_upscaled, (cell_x, cell_y))
            # Draw a subtle separator line between original and GB
            audit_image.paste(gb_upscaled, (cell_x + 64, cell_y), gb_upscaled)
            
        audit_image.save(output_audit_path)
        print(f"Audit image successfully generated and saved to {output_audit_path}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
