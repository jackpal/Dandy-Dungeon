# Analysis Report: Graphics Conversion Pipeline (Milestone 1)

**Date**: 2026-06-21T00:22:32Z  
**Author**: Explorer 2 (Graphics Milestone 1)  
**Status**: Read-Only Analysis Complete  

---

## Executive Summary
This report presents the findings and plan for the visual verification of Dandy Dungeon's graphics conversion pipeline (Milestone 1). We have analyzed the original JS codebase, the GameBoy build system, the GBDK 2bpp tileset structure, and designed a robust Python-based verification script (`verify_graphics.py`) to generate a side-by-side visual comparison audit (`graphics_audit.png`).

---

## 1. Analysis of the Original Sprite Sheet (`dandy-js/strike.js`)
* **Exact Variable**: The base64-encoded sprite sheet is stored in the variable `strike.src` as a data URL:
  ```javascript
  const strike = new Image();
  strike.src = "data:image/png;base64," + "iVBORw0KGgoAAA..."
  ```
* **Format**: It is a standard PNG image with an RGBA color model and dimensions of **256x32 pixels**.
  * Each original sprite is **16x16 pixels**.
  * The sheet contains **32 sprites** arranged in a 16-column by 2-row grid:
    * **Row 0 (Y: 0-15)**: 16 background elements, interactive items, and monsters (indices 0 to 15).
    * **Row 1 (Y: 16-31)**: 8 arrow direction sprites (indices 16 to 23) and 8 player/hero direction sprites (indices 24 to 31).
* **Programmatic Extraction**:
  * The base64 string can be programmatically extracted from `strike.js` using regular expressions to grab all quoted strings following `"data:image/png;base64,"`.
  * The extracted string is then decoded using `base64.b64decode()` and written to a file (e.g. `dandy-gb/web/strike_original.png`). This is already implemented in `dandy-gb/tools/extract_sprites.py`.

---

## 2. GBDK 2bpp Format Structure (`dandy-gb/src/tiles.c`)
* **Array Definition**:
  * Declared in `src/tiles.h` as:  
    `extern const unsigned char dandy_tiles[32 * 16];`
  * Defined in `src/tiles.c` as a flat `unsigned char` array containing exactly **512 bytes** (32 tiles * 16 bytes/tile).
* **2bpp Layout**:
  * On the GameBoy, each tile is **8x8 pixels** with 2 bits per pixel (2bpp), allowing 4 color indices (0, 1, 2, 3).
  * An 8x8 tile is stored as 8 rows. Each row of 8 pixels is packed into **2 bytes**:
    * **Byte 1 (planar low byte)**: Contains the least-significant bit (LSB) for the 8 pixels.
    * **Byte 2 (planar high byte)**: Contains the most-significant bit (MSB) for the 8 pixels.
    * Bit 7 corresponds to the leftmost pixel (column 0), and Bit 0 corresponds to the rightmost pixel (column 7).
    * The color index for column `x` in a row is calculated as:  
      `color_idx = (((high_byte >> (7 - x)) & 1) << 1) | ((low_byte >> (7 - x)) & 1)`
  * This matches the 16 bytes per tile in `dandy_tiles`.
* **Mapping to 16x16 Sprites**:
  * In the original JS game, the grid is 16x16 pixels per cell.
  * On the GameBoy, the screen is 160x144 pixels (20x18 tiles). The viewport displays a 20x10 grid of 8x8 cells, with the remaining 20x8 tiles used for the HUD.
  * Therefore, each 16x16 cell in the original game maps **1-to-1** to a single 8x8 tile in the GameBoy version.
  * The 32 tiles in the original sprite sheet map directly to the 32 tiles in `dandy_tiles` by their 0-indexed position (0..31):
    * **0..15**: Backgrounds, items, monsters, nests (1-to-1 match).
    * **16..19**: Arrow directions (down, up, left, right).
    * **24..27**: Hero directions (down, up, left, right).

---

## 3. GameBoy Build Process (`dandy-gb/Makefile`)
* **Asset Compilation**:
  * The `sprites` target compiles the sprite assets:
    ```makefile
    sprites:
    	@echo "Compiling pristine BMP sprite assets..."
    	python3 $(TOOLS_DIR)/compile_bmp_sprites.py
    ```
  * `compile_bmp_sprites.py` contains a hardcoded `GLYPHS` dictionary defining the 8x8 pixel layouts using ASCII strings. It packs these into GBDK 2bpp format and writes them directly to `src/tiles.c` and `src/tiles.h`.
* **ROM Compilation**:
  * The `all` target runs `setup`, `levels`, `sprites`, and compiles the ROM:
    ```makefile
    $(BIN_DIR)/$(ROM_NAME): $(OBJS)
    	$(LCC) $(LCCFLAGS) -o $@ $(OBJS)
    ```
  * `lcc` (the GBDK compiler/linker wrapper) compiles the C files (including `src/tiles.c` and `src/gameboy_hal.c`) and links them into the final ROM `bin/dandy.gb`.

---

## 4. Verification Script Design (`verify_graphics.py`)
To audit the graphics pipeline, we have designed and written a proposed script `proposed_verify_graphics.py` in our folder. It performs the following operations:
1. **Decode GBDK 2bpp**:
   * Parses `src/tiles.c` using regular expressions to locate and extract the 512 bytes of `dandy_tiles`.
   * For each tile (16 bytes), decodes it into an 8x8 matrix of color indices (0..3) using the GameBoy planar decoding logic.
2. **Color Palette Mapping**:
   * **Background Tiles (0..15, 20..23, 28..31)**: Uses the BGP palette (0=Black, 1=Dark Gray, 2=Light Gray, 3=White).
   * **Sprite Tiles (16..19, 24..27)**: Uses the OBP0/1 palette (0=Black/Transparent, 1=White, 2=Dark Gray, 3=Black).
3. **Slice Reference Images**:
   * Loads the 256x32 `strike_original.png` and slices it into thirty-two 16x16 original tiles.
4. **Nearest-Neighbor Upscaling**:
   * Upscales the original 16x16 tiles 8x (to 128x128 pixels).
   * Upscales the compiled 8x8 tiles 8x (to 64x64 pixels).
5. **Visual Audit Grid (`graphics_audit.png`)**:
   * Generates a master audit image of **1600x640 pixels** arranged in an 8x4 grid.
   * Each cell in the grid is **200x160 pixels** and contains:
     * A text label displaying the tile index and name (e.g. `Tile 1: WALL`).
     * The original 16x16 tile upscaled 8x (128x128) on the left.
     * The compiled 8x8 tile upscaled 8x (64x64) on the right, centered vertically.
     * Clear cell borders for easy visual alignment.

---

## 5. Verification Plan

To run and verify the graphics audit:
1. **Extract Reference Sprites**:
   ```bash
   python3 tools/extract_sprites.py
   ```
   *Verify that `web/strike_original.png` is generated and has dimensions 256x32.*
2. **Generate Visual Audit Sheet**:
   Copy the proposed `proposed_verify_graphics.py` to `tools/verify_graphics.py` and run:
   ```bash
   python3 tools/verify_graphics.py
   ```
   *Verify that `web/graphics_audit.png` is created.*
3. **Visual Invalidation Conditions**:
   * The audit sheet must be inspected to ensure:
     1. **Contrast & Accuracy**: The 8x8 tiles preserve the iconic features of the 16x16 counterparts (e.g., the face visor of the Hero, the fangs/eyes of the Demon).
     2. **Grid Alignment**: Colors match the specified palettes (BGP for background, OBP for sprites).
     3. **Perfect Decoding**: No shearing or pixel offsets in the decoded 8x8 tiles.
