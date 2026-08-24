# Handoff Report: Milestone 1 - Exploration & Verification Foundation

**Author**: Explorer 2 (Milestone 1)  
**Date**: 2026-06-21  
**Status**: Soft Handoff (Transferred to Implementer)

---

## 1. Observation

### A. Source Sprite Sheet Location & Format
In `dandy-js/strike.js` (lines 5-54), we observed the base64-encoded sprite sheet:
```javascript
const strike = new Image();
strike.src = "data:image/png;base64,"+
"iVBORw0KGgoAAAANSUhEUgAAAQAAAAAgCAYAAAD9qabk..."
```
Decoding the first 32 characters (`iVBORw0KGgoAAAANSUhEUgAAAQAAAAAg`) gives the PNG IHDR dimensions:
- Width: `0x00000100` = 256 pixels
- Height: `0x00000020` = 32 pixels

This matches `dandy-gb/web/strike_original.png` which already exists in the workspace and contains 32 sprites of 16x16 pixels laid out in 2 rows of 16 columns.

### B. GameBoy Tile Data & 2bpp Format
In `dandy-gb/src/tiles.c` (lines 4-102), the GBDK tiles are defined in a 512-byte array:
```c
/* 32 tiles * 16 bytes per tile = 512 bytes */
const unsigned char dandy_tiles[] = {
    /* Tile 0 */
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    ...
};
```

In `dandy-gb/tools/compile_bmp_sprites.py` (lines 315-331), we observed how these 2bpp bytes are packed. Each row of 8 pixels is encoded as a pair of planar bytes:
- Byte 1 holds the LSB (bit 0) of the color index for all 8 pixels.
- Byte 2 holds the MSB (bit 1) of the color index for all 8 pixels.
A tile is 8 rows high, resulting in 16 bytes per tile.

### C. Game Engine Drawing
In `dandy-gb/src/dandy_core.c` (lines 301-338), the game viewport renders each cell as a single 8x8 tile:
```c
            if (is_sprite) {
                hal_draw_tile(sx, sy, TILE_SPACE);
                ...
                hal_set_sprite(sprite_count++, sx * 8, sy * 8, tile, sprite_flags);
            } else {
                hal_draw_tile(sx, sy, tile);
            }
```
And `hal_draw_tile` in `dandy-gb/src/gameboy_hal.c` (lines 54-62) draws the background tile using GBDK's `set_bkg_tile_xy(x, y, 128 + tile_id)`.

### D. Build Process
In `dandy-gb/Makefile` (lines 27-58), the build process is:
```makefile
all: setup levels sprites $(BIN_DIR)/$(ROM_NAME)

levels:
	python3 $(TOOLS_DIR)/convert_levels.py

sprites:
	python3 $(TOOLS_DIR)/compile_bmp_sprites.py
```

---

## 2. Logic Chain

1. **Viewport Scale**: The original JS game uses a viewport of 20x10 cells. The GameBoy screen resolution is 160x144 pixels.
2. **Dimension Math**: If the GameBoy version used 16x16 pixel tiles, a 20x10 viewport would require 320x160 pixels, which exceeds the GameBoy screen size. To display the full viewport, each cell must be represented by a single 8x8 tile ($20 \times 8 = 160$ pixels wide; $10 \times 8 = 80$ pixels high, leaving $144 - 80 = 64$ pixels for the HUD).
3. **1-to-1 Mapping**: Since the game engine (`dandy_core.c` and `gameboy_hal.c`) renders each map cell as a single 8x8 tile, the 32 16x16 sprites in `strike_original.png` must map 1-to-1 to the 32 8x8 tiles in `tiles.c`.
4. **Reference Sprite Sheet Layout**:
   - Total Sprites: 32 (each 16x16 pixels).
   - Arranged in 2 rows of 16 columns ($16 \times 16 = 256$ pixels wide, $2 \times 16 = 32$ pixels high).
   - Row 0 (Y: 0..15) contains Sprites 0..15 (static background tiles and items).
   - Row 1 (Y: 16..31) contains Sprites 16..31 (dynamic entities: 8 arrows and 8 player frames/directions).
5. **Compilation Verification**: The build process compiles native 8x8 code glyphs into GBDK 2bpp format using `compile_bmp_sprites.py` and then builds the ROM using the GBDK-2020 compiler `lcc`.

---

## 3. Caveats
- **Colors**: The original `strike_original.png` contains full RGB colors, whereas the GameBoy 2bpp tiles only support 4 shades. The verification script will decode the 2bpp tiles to grayscale (Black, Dark Gray, Light Gray, White). Visual comparison will require comparing color shapes to grayscale shapes.
- **Reference Image Size**: We confirmed `strike_original.png` is 256x32 pixels based on our analysis. The Scope document (`SCOPE.md`) erroneously refers to it as 256x16 pixels. A 256x16 image would only contain 16 sprites, whereas the game has 32 sprites.

---

## 4. Conclusion
1. The base64 sprite sheet in `dandy-js/strike.js` decodes to a 256x32 pixel PNG containing 32 16x16 sprites.
2. The GBDK 2bpp tiles in `tiles.c` contain 32 8x8 tiles, mapping 1-to-1 to the 16x16 original sprites.
3. The build process uses `make sprites` to compile native code-as-art assets to `tiles.c`/`tiles.h`.
4. The verification script `verify_graphics.py` should be placed in `dandy-gb/tools/` and will generate `dandy-gb/teamwork_graphics/graphics_audit.png` showing the 32 reference sprites (upscaled 4x to 64x64) side-by-side with the decoded GameBoy tiles (upscaled 8x to 64x64) in a clear grid layout.

---

## 5. Verification Method

To verify our findings independently:
1. **Analyze Dimensions**: Run the following python command to check the header of `dandy-gb/web/strike_original.png` and verify it is indeed 256x32:
   ```python
   from PIL import Image
   img = Image.open("dandy-gb/web/strike_original.png")
   print(img.size)  # Output must be (256, 32)
   ```
2. **Examine tiles.c**: Check the size of `dandy_tiles` in `dandy-gb/src/tiles.c`. It must contain exactly 32 blocks of 16 bytes (512 bytes total).
3. **Verify Makefile**: Run `make clean && make` to ensure the compilation pipeline runs cleanly with zero warnings/errors.

---

## 6. Remaining Work (Implementation Steps)

The receiving Implementer agent should perform the following concrete next steps:

1. **Task 1: Extract Sprite Sheet**
   - Run `python3 dandy-gb/tools/extract_sprites.py` to extract `strike_original.png` from `strike.js`.
   - Copy or save the decoded image to `dandy-gb/teamwork_graphics/strike_original.png` as required by the milestone.
   - Verify the size of the extracted image is 256x32 pixels.

2. **Task 2: Create Verification Script**
   - Create `dandy-gb/tools/verify_graphics.py` using the complete implementation provided in Section 5 of the Analysis Report (`analysis.md`).

3. **Task 3: Run Verification**
   - Run `python3 dandy-gb/tools/verify_graphics.py` to generate `dandy-gb/teamwork_graphics/graphics_audit.png`.
   - Visually inspect the audit sheet to ensure all 32 tiles match the reference sprites in layout, alignment, and design.

4. **Task 4: Build ROM**
   - Run `make clean && make` in `dandy-gb/` to ensure the GameBoy ROM compiles with zero errors or warnings.
