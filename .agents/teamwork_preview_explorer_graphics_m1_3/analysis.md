# Analysis and Implementation Plan - Milestone 1

This document presents the codebase analysis and the proposed implementation strategy for Milestone 1 of the Dandy Dungeon graphics conversion pipeline.

---

## 1. Sprite Sheet Analysis (`dandy-js/strike.js`)

- **Variable Name**: `strike`
- **Asset Source**: A base64-encoded PNG image assigned to `strike.src`.
- **Data Format & Structure**: 
  - Prefixed with `"data:image/png;base64,"`.
  - The base64 payload is split into **48 double-quoted string literals**, concatenated with the JS `+` operator.
  - The exact length of the concatenated base64 payload is **2,736 characters**.
  - When decoded, it produces a binary PNG file of **2,052 bytes**.
  - **Image Dimensions**: **256 x 32 pixels** (not 256x16 as hypothesized in `SCOPE.md`).
  - **Color Format**: **RGBA** (Color type 6, 8 bits per channel), direct color with alpha channel, no palette chunk.
  - **Layout**: 32 sprites in total, each 16x16 pixels, arranged in a grid of 2 rows and 16 columns:
    - **Row 0 (Y=0..15)**: Sprites 0 to 15 (Static tiles: space, wall, door, stairs, items, generators).
    - **Row 1 (Y=16..31)**: Sprites 16 to 31 (Dynamic tiles: 8 arrow directions, 8 player directions).

---

## 2. GBDK 2bpp Tiles Analysis (`dandy-gb/src/tiles.c`)

- **Representation**: Standard Game Boy 2bpp (2 bits per pixel) planar format.
  - Each tile is 8x8 pixels.
  - Each tile requires **16 bytes** of storage.
  - Every row of 8 pixels is encoded in 2 consecutive bytes:
    - **Byte 1**: Low bit (bit 0) of the color index for the 8 pixels.
    - **Byte 2**: High bit (bit 1) of the color index for the 8 pixels.
    - Pixels are packed MSB-first (pixel 0 is bit 7, pixel 7 is bit 0).
- **Array Details**:
  - Array Name: `dandy_tiles`
  - Array Size: **512 bytes** (32 tiles * 16 bytes/tile).
  - Number of Tiles: **32 tiles** (indices 0 to 31).
- **16x16 Sprite Layout / Mapping**:
  - In the Game Boy implementation, **all game entities and gameplay elements are rendered as single 8x8 tiles**, not 16x16 sprites. The original 16x16 JS sprites have been downscaled 2x to fit the 8x8 Game Boy grid.
  - There is a **direct 1-to-1 mapping** between the 32 sprites in the 256x32 JS sprite sheet and the 32 8x8 tiles in `tiles.c`:
    - Tile `i` in `tiles.c` corresponds exactly to sprite `i` in `strike_original.png`.
  - If a 16x16 sprite *were* to be composed of four 8x8 tiles (e.g. for a future large-sprite mode), the standard layouts are:
    - **8x8 Sprite Mode (2x2 Grid)**: Top-Left (Tile 0), Top-Right (Tile 1), Bottom-Left (Tile 2), Bottom-Right (Tile 3) in consecutive VRAM indices.
    - **8x16 Sprite Mode (vertical stacks)**: Top-Left (Tile 0), Bottom-Left (Tile 1), Top-Right (Tile 2), Bottom-Right (Tile 3) in consecutive VRAM indices.

---

## 3. Build System Analysis (`dandy-gb/Makefile`)

- **Compiler**: Uses GBDK-2020 compiler toolchain (`lcc`), located by default at `$(HOME)/Developer/gbdk/bin/lcc`.
- **Target**: Compiles a Game Boy ROM named `bin/dandy.gb`.
- **Pre-build Assets Compilation**:
  - `make levels`: Compiles map files by running `python3 tools/convert_levels.py`.
  - `make sprites`: Generates Game Boy tile C source/header by running `python3 tools/compile_bmp_sprites.py`.
- **ROM Linking**:
  - Combines `obj/main.o`, `obj/dandy_core.o`, `obj/gameboy_hal.o`, `obj/levels.o`, and `obj/tiles.o` using `lcc` with flags `-Wa-l -Wl-m -Wl-yo2` (enabling 2 ROM banks).
- **Test / Verification Targets**:
  - `make test`: Compiles `libdandy_test.so` and runs host-side Python unit tests.
  - `make test_emu`: Sets up a virtual environment, installs PyBoy emulator, and runs automated E2E ROM tests.

---

## 4. Analysis of SCOPE.md

- **Scope Correction**: `SCOPE.md` states in T1 that the sprite sheet is "256x16 PNG". Our analysis of `strike.js` proves that the sprite sheet is actually **256x32 PNG**, containing 32 sprites in 2 rows. This matches the 32 tiles in GBDK.
- **Visual Comparability**: To perform an effective side-by-side comparison of the original 16x16 sprites and the compiled 8x8 tiles, the verification script must upscale the 8x8 tiles to match the display size of the upscaled 16x16 sprites. 
  - Upscaling the original 16x16 sprite 8x yields a **128x128 pixel block**.
  - Upscaling the compiled 8x8 tile 16x yields a matching **128x128 pixel block**.
  - Drawing them side-by-side in a single audit sheet provides perfect visual clarity.

---

## 5. Detailed Implementation Strategy for the Worker

We propose a robust, **zero-dependency Python implementation** for the Worker. By implementing a pure-Python PNG decoder and encoder, the verification script will run flawlessly in any standard Python 3 environment without requiring `Pillow` or `numpy`.

### A. Phase 1: Sprite Sheet Extraction (`extract_graphics.py`)
A Python script will:
1. Open `dandy-js/strike.js` and extract the base64 payload using a clean regex that finds the `strike.src` assignment and joins all double-quoted strings.
2. Decode the base64 payload to binary PNG bytes.
3. Ensure the output directory `dandy-gb/teamwork_graphics/` exists.
4. Write the binary bytes directly to `dandy-gb/teamwork_graphics/strike_original.png`.
5. Log the file path, size, and success.

### B. Phase 2: Auditing & Verification Script (`verify_graphics.py`)
A Python script located in `dandy-gb/tools/verify_graphics.py` will:
1. **Decode `strike_original.png`**:
   - Parse PNG chunks (`IHDR`, `IDAT`, `IEND`).
   - Decompress `IDAT` using `zlib.decompress()`.
   - Reconstruct the raw RGBA pixel map (`256x32` pixels) by applying standard PNG scanline defiltering (supporting None, Sub, Up, and Paeth filters).
2. **Parse `tiles.c`**:
   - Read `dandy-gb/src/tiles.c` and extract all hex values using `re.findall(r'0x[0-9a-fA-F]{2}', content)`.
   - Convert to a list of 512 bytes and assert that the length is correct.
3. **Decode 2bpp Tiles**:
   - Reconstruct the 8x8 pixels of each of the 32 tiles.
   - Map 2bpp color indices (0..3) to RGB colors based on the hardware palette blueprints:
     - **Background Tiles (0..8, 12..15)**: Index 0 -> Black `(0,0,0)`, 1 -> Dark Gray `(85,85,85)`, 2 -> Light Gray `(170,170,170)`, 3 -> White `(255,255,255)`.
     - **Sprite Tiles (9..11, 16..19, 24..27)**: Index 0 -> Transparent (draw as Green/Gray checkboard or solid Black), 1 -> White `(255,255,255)`, 2 -> Dark Gray `(85,85,85)`, 3 -> Black `(0,0,0)`.
4. **Stitch Audit Sheet (`graphics_audit.png`)**:
   - Create an output image buffer of size **272 x 4352 pixels** (32 rows, each row showing: 128x128 original upscaled 8x, 16px gap, 128x128 compiled upscaled 16x, with 8px margins).
   - Write the upscaled pixels into the buffer using nearest-neighbor scaling.
   - Save the buffer as a standard PNG using a pure-Python PNG encoder (writing signature, `IHDR`, compressing data with `zlib.compress` into `IDAT`, and `IEND`).

### C. Build & Verification Commands
The Worker should execute the following sequence to build the project and run the audit:
```bash
# 1. Clean previous build artifacts
make -C dandy-gb clean

# 2. Run standard compilation to verify build system and generate tiles.c
make -C dandy-gb all

# 3. Run the extraction and verification tool to generate audit images
python3 dandy-gb/tools/extract_graphics.py
python3 dandy-gb/tools/verify_graphics.py

# 4. Verify that the files were generated and are valid
ls -lh dandy-gb/teamwork_graphics/strike_original.png
ls -lh dandy-gb/teamwork_graphics/graphics_audit.png
```

---

## 6. Recommendations & Next Steps

1. **Proceed to Implementation**: The codebase compiles cleanly out of the box, and the asset structures are perfectly aligned. The Worker is ready to implement the python scripts.
2. **Zero-Dependency Mandate**: The pure-Python PNG decoder/encoder strategy is highly recommended as it avoids any dependency issues on systems without `PIL` or `pip` access.
3. **Correct Scope Metadata**: Update the sub-orchestrator's status files to reflect that the sprite sheet is **256x32**, containing 32 tiles in 2 rows.
