# Graphics Conversion Pipeline - Milestone 1 Analysis Report

## Executive Summary
This report analyzes the graphics format mapping, sprite sheet structure, GameBoy build process, and designs the verification script `verify_graphics.py` for Milestone 1 of the Dandy Dungeon graphics conversion pipeline. We have confirmed a 1-to-1 mapping where the 32 original 16x16 sprites in `strike_original.png` (dimensions 256x32) are downscaled to 32 8x8 tiles in `tiles.c` to fit the GameBoy viewport.

---

## 1. Observation

### A. Original Sprite Sheet and Base64 Data
In `dandy-js/strike.js` (lines 5-54), we observed the base64-encoded sprite sheet:
```javascript
const strike = new Image();
strike.src = "data:image/png;base64,"+
"iVBORw0KGgoAAAANSUhEUgAAAQAAAAAgCAYAAAD9qabk..."
```
Decoding the base64 string `iVBORw0KGgoAAAANSUhEUgAAAQAAAAAg` reveals:
- **Signature**: `\x89PNG\r\n\x1a\n` (standard PNG header)
- **Width**: `0x00000100` = 256 pixels
- **Height**: `0x00000020` = 32 pixels
- **Format**: 2 rows of 16 columns, where each sprite is 16x16 pixels. Total sprites = 32.

This matches the file `dandy-gb/web/strike_original.png` which has a size of 2052 bytes and dimensions of 256x32 pixels.

*Note on discrepancy*: The Scope document (`SCOPE.md`) erroneously refers to `strike_original.png` as 256x16 pixels. A 256x16 image would only contain 16 sprites, whereas the game has 32 sprites (including arrows and player frames).

### B. GameBoy GBDK 2bpp Format Structure
In `dandy-gb/src/tiles.c` (lines 4-102), we observed that the GameBoy tiles are stored as a single `unsigned char` array:
```c
/* 32 tiles * 16 bytes per tile = 512 bytes */
const unsigned char dandy_tiles[] = {
    /* Tile 0 */
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    ...
};
```
There are exactly 32 tiles, each occupying 16 bytes.

In `dandy-gb/tools/compile_bmp_sprites.py` (lines 315-331), we observed how these 2bpp bytes are packed:
```python
        # Pack each of the 8 rows of the glyph
        for y in range(8):
            low_byte = 0
            high_byte = 0
            row_str = glyph[y]
            
            # Pack the 8 horizontal pixels into 2 planar bytes (low_byte & high_byte)
            for x in range(8):
                val = int(row_str[x]) # Color index 0..3
                bit0 = val & 1
                bit1 = (val >> 1) & 1
                
                # Pack MSB-first
                low_byte |= (bit0 << (7 - x))
                high_byte |= (bit1 << (7 - x))
                
            tile_bytes.append(low_byte)
            tile_bytes.append(high_byte)
```
Each row of 8 pixels is encoded as a pair of bytes: the first byte holds the LSB (bit 0) of the color index for all 8 pixels, and the second byte holds the MSB (bit 1) of the color index. A tile is 8 rows high, resulting in 16 bytes per tile.

### C. Game Engine Mapping and Drawing
In `dandy-gb/src/dandy_core.h` (lines 13-31), the tile constants are defined:
```c
#define TILE_SPACE       0
#define TILE_WALL        1
#define TILE_DOOR        2
#define TILE_UP          3
#define TILE_DOWN        4
#define TILE_KEY         5
#define TILE_FOOD        6
#define TILE_MONEY       7
#define TILE_BOMB        8
#define TILE_MONSTER1    9
#define TILE_MONSTER2    10
#define TILE_MONSTER3    11
#define TILE_HEART       12
#define TILE_GENERATOR1  13
#define TILE_GENERATOR2  14
#define TILE_GENERATOR3  15
#define TILE_ARROW       16
#define TILE_PLAYER1     24
```

In `dandy-gb/src/dandy_core.c` (lines 301-338), we observed that the engine draws the viewport by mapping each cell to a single tile index (0 to 31):
```c
            if (is_sprite) {
                // Draw background behind the sprite
                hal_draw_tile(sx, sy, TILE_SPACE);
                ...
                hal_set_sprite(sprite_count++, sx * 8, sy * 8, tile, sprite_flags);
            } else {
                // Static tile (wall, door, items, generator, etc.)
                hal_draw_tile(sx, sy, tile);
            }
```
And `hal_draw_tile` in `dandy-gb/src/gameboy_hal.c` (lines 54-62) maps the tile ID directly to background VRAM starting at index 128:
```c
void hal_draw_tile(uint8_t x, uint8_t y, uint8_t tile_id) {
    ...
    // Draw custom background tile loaded starting at index 128 (0x80)
    set_bkg_tile_xy(x, y, 128 + tile_id);
}
```

### D. GameBoy Build Process
In `dandy-gb/Makefile` (lines 27-58), we observed the build process:
```makefile
# Default target
all: setup levels sprites $(BIN_DIR)/$(ROM_NAME)

# Link the ROM
$(BIN_DIR)/$(ROM_NAME): $(OBJS)
	$(LCC) $(LCCFLAGS) -o $@ $(OBJS)

# Compile C source files
$(OBJ_DIR)/%.o: $(SRC_DIR)/%.c
	$(LCC) -Wf--opt-code-size -c -o $@ $<

# Run the level converter tool (requires Python 3)
levels:
	@echo "Converting levels from JS to C header..."
	python3 $(TOOLS_DIR)/convert_levels.py

# Run the sprite compiler tool
sprites:
	@echo "Compiling pristine BMP sprite assets..."
	python3 $(TOOLS_DIR)/compile_bmp_sprites.py
```
This demonstrates that `make sprites` generates `tiles.c` and `tiles.h` from native 8x8 code-as-art representation, which are then compiled into `obj/tiles.o` and linked into `bin/dandy.gb`.

---

## 2. Logic Chain

1. **Viewport Constraints**: The original JS game uses a viewport of 20x10 cells. On GameBoy, the screen resolution is 160x144 pixels.
2. **Dimension Math**: If the GameBoy version used 16x16 pixel tiles (composed of four 8x8 tiles), a 20x10 viewport would require 320x160 pixels, which exceeds the GameBoy screen size. To display the full viewport, each cell must be represented by a single 8x8 tile ($20 \times 8 = 160$ pixels wide; $10 \times 8 = 80$ pixels high, leaving $144 - 80 = 64$ pixels for the HUD).
3. **1-to-1 Mapping**: Since the game engine (`dandy_core.c` and `gameboy_hal.c`) renders each map cell as a single 8x8 tile, the 32 16x16 sprites in `strike_original.png` must map 1-to-1 to the 32 8x8 tiles in `tiles.c`.
4. **Reference Sprite Sheet Layout**:
   - Total Sprites: 32 (each 16x16 pixels).
   - Arranged in 2 rows of 16 columns ($16 \times 16 = 256$ pixels wide, $2 \times 16 = 32$ pixels high).
   - Row 0 (Y: 0..15) contains Sprites 0..15 (static background tiles and items).
   - Row 1 (Y: 16..31) contains Sprites 16..31 (dynamic entities: 8 arrows and 8 player frames/directions).
5. **Tile Mapping Table**:

| Sprite ID | Name | Type | Row in Reference | Col in Reference | Tile Index in `tiles.c` |
|---|---|---|---|---|---|
| 0 | Space | Background | 0 | 0 | 0 |
| 1 | Wall | Background | 0 | 1 | 1 |
| 2 | Door | Background | 0 | 2 | 2 |
| 3 | Stairs Up | Background | 0 | 3 | 3 |
| 4 | Stairs Down | Background | 0 | 4 | 4 |
| 5 | Key | Item | 0 | 5 | 5 |
| 6 | Food | Item | 0 | 6 | 6 |
| 7 | Money ($) | Item | 0 | 7 | 7 |
| 8 | Bomb | Item | 0 | 8 | 8 |
| 9 | Ghost | Monster | 0 | 9 | 9 |
| 10 | Demon | Monster | 0 | 10 | 10 |
| 11 | Golem | Monster | 0 | 11 | 11 |
| 12 | Heart | Item | 0 | 12 | 12 |
| 13 | Generator 1 | Nest | 0 | 13 | 13 |
| 14 | Generator 2 | Nest | 0 | 14 | 14 |
| 15 | Generator 3 | Nest | 0 | 15 | 15 |
| 16..23 | Arrows (0..7) | Projectiles | 1 | 0..7 | 16..23 |
| 24..31 | Player 1 (0..7) | Player | 1 | 8..15 | 24..31 |

---

## 3. Caveats
- **Colors**: The original `strike_original.png` contains full RGB colors, whereas the GameBoy 2bpp tiles only support 4 shades. The verification script will decode the 2bpp tiles to grayscale (Black, Dark Gray, Light Gray, White). Visual comparison will require comparing color shapes to grayscale shapes.
- **Reference Image Size**: We assumed `strike_original.png` is 256x32 pixels based on our analysis of the base64 string and the file in `dandy-gb/web/strike_original.png`. If a 256x16 file is supplied instead, it will only contain the first 16 sprites.

---

## 4. Conclusion
1. The base64 sprite sheet in `dandy-js/strike.js` decodes to a 256x32 pixel PNG containing 32 16x16 sprites.
2. The GBDK 2bpp tiles in `tiles.c` contain 32 8x8 tiles, mapping 1-to-1 to the 16x16 original sprites.
3. The build process uses `make sprites` to compile native code-as-art assets to `tiles.c`/`tiles.h`.
4. The verification script `verify_graphics.py` should be placed in `dandy-gb/tools/` and will generate `dandy-gb/teamwork_graphics/graphics_audit.png` showing the 32 reference sprites (upscaled 4x to 64x64) side-by-side with the decoded GameBoy tiles (upscaled 8x to 64x64) in a clear grid layout.

---

## 5. Verification Method (Verification Script Design)

Below is the design and full implementation plan for `dandy-gb/tools/verify_graphics.py`:

### A. Dependencies
- Python 3
- `pillow` (PIL) library

### B. Verification Script Implementation Design

```python
import os
import re
import sys
from PIL import Image, ImageDraw

def parse_tiles_c(tiles_c_path):
    """Parses tiles.c and extracts 32 tiles, 16 bytes each."""
    with open(tiles_c_path, "r") as f:
        content = f.read()
    match = re.search(r'dandy_tiles\s*\[\s*\]\s*=\s*\{([^}]+)\}', content)
    if not match:
        raise ValueError("Could not find dandy_tiles array in tiles.c")
    hex_values = re.findall(r'0[xX][0-9a-fA-F]{2}', match.group(1))
    byte_values = [int(val, 16) for val in hex_values]
    if len(byte_values) != 512:
        raise ValueError(f"Expected 512 bytes, found {len(byte_values)}")
    return [byte_values[i*16:(i+1)*16] for i in range(32)]

def decode_gb_tile(tile_bytes):
    """Decodes 16 bytes of GameBoy 2bpp to an 8x8 list of color indices (0..3)."""
    pixels = []
    for r in range(8):
        low_byte = tile_bytes[r * 2]
        high_byte = tile_bytes[r * 2 + 1]
        row = []
        for c in range(8):
            bit_index = 7 - c
            bit0 = (low_byte >> bit_index) & 1
            bit1 = (high_byte >> bit_index) & 1
            row.append((bit1 << 1) | bit0)
        pixels.append(row)
    return pixels

def render_tile_to_image(decoded_tile):
    """Converts an 8x8 decoded tile to a PIL Image (grayscale)."""
    # Palette mapping: 0 -> Black, 1 -> Dark Gray, 2 -> Light Gray, 3 -> White
    colors = [
        (0, 0, 0),       # 0: Black
        (85, 85, 85),    # 1: Dark Gray
        (170, 170, 170),  # 2: Light Gray
        (255, 255, 255)  # 3: White
    ]
    img = Image.new("RGB", (8, 8))
    for y in range(8):
        for x in range(8):
            img.putpixel((x, y), colors[decoded_tile[y][x]])
    return img

def main():
    # Paths
    current_dir = os.path.dirname(os.path.abspath(__file__))
    tiles_c_path = os.path.normpath(os.path.join(current_dir, "../src/tiles.c"))
    ref_png_path = os.path.normpath(os.path.join(current_dir, "../web/strike_original.png"))
    output_dir = os.path.normpath(os.path.join(current_dir, "../teamwork_graphics"))
    output_png_path = os.path.join(output_dir, "graphics_audit.png")
    
    os.makedirs(output_dir, exist_ok=True)
    
    print("Loading reference spritesheet...")
    if not os.path.exists(ref_png_path):
        print(f"Error: Reference image {ref_png_path} not found. Please run extract_sprites.py first.")
        sys.exit(1)
        
    ref_sheet = Image.open(ref_png_path)
    if ref_sheet.size != (256, 32):
        print(f"Warning: Reference sheet size is {ref_sheet.size}, expected (256, 32)")
        
    print("Parsing and decoding GameBoy 2bpp tiles...")
    gb_tile_data = parse_tiles_c(tiles_c_path)
    decoded_tiles = [decode_gb_tile(tile) for tile in gb_tile_data]
    
    # Grid parameters
    # 4 rows, 8 columns of tiles
    cols, rows = 8, 4
    cell_w, cell_h = 140, 70  # Size of each comparison block
    padding = 10
    
    audit_img = Image.new("RGB", (cols * (cell_w + padding) + padding, rows * (cell_h + padding) + padding), (50, 50, 50))
    draw = ImageDraw.Draw(audit_img)
    
    tile_names = [
        "SPACE", "WALL", "DOOR", "STAIRS_UP", "STAIRS_DOWN", "KEY", "FOOD", "MONEY",
        "BOMB", "GHOST", "DEMON", "GOLEM", "HEART", "NEST_1", "NEST_2", "NEST_3",
        "ARROW_0", "ARROW_1", "ARROW_2", "ARROW_3", "ARROW_4", "ARROW_5", "ARROW_6", "ARROW_7",
        "PLAYER_0", "PLAYER_1", "PLAYER_2", "PLAYER_3", "PLAYER_4", "PLAYER_5", "PLAYER_6", "PLAYER_7"
    ]
    
    for idx in range(32):
        r_idx = idx // cols
        c_idx = idx % cols
        
        # 1. Extract and upscale reference tile (16x16 -> 64x64, 4x nearest neighbor)
        ref_x = (idx % 16) * 16
        ref_y = (idx // 16) * 16
        ref_tile = ref_sheet.crop((ref_x, ref_y, ref_x + 16, ref_y + 16))
        ref_tile_scaled = ref_tile.resize((64, 64), Image.NEAREST)
        
        # 2. Render and upscale GameBoy tile (8x8 -> 64x64, 8x nearest neighbor)
        gb_tile_img = render_tile_to_image(decoded_tiles[idx])
        gb_tile_scaled = gb_tile_img.resize((64, 64), Image.NEAREST)
        
        # 3. Position in grid
        x_pos = padding + c_idx * (cell_w + padding)
        y_pos = padding + r_idx * (cell_h + padding)
        
        # Paste side-by-side
        audit_img.paste(ref_tile_scaled, (x_pos, y_pos + 12))
        audit_img.paste(gb_tile_scaled, (x_pos + 68, y_pos + 12))
        
        # Label text
        label = f"{idx}: {tile_names[idx]}"
        draw.text((x_pos, y_pos), label, fill=(255, 255, 255))
        
    print(f"Saving comparison audit sheet to {output_png_path}...")
    audit_img.save(output_png_path)
    print("Graphics verification audit sheet generated successfully!")

if __name__ == "__main__":
    main()
```
