# Handoff Report: Explorer - Graphics Conversion Pipeline (Milestone 1)

This report details the findings and implementation plan for the graphics conversion pipeline of Dandy Dungeon, preparing the ground for the Worker.

---

## 1. Observation

- **Base64-Encoded PNG**:
  - Location: `/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-js/strike.js`
  - Assigned variable: `strike` (lines 5-6).
  - Code segment:
    ```javascript
    const strike = new Image();
    strike.src = "data:image/png;base64,"+
    "iVBORw0KGgoAAAANSUhEUgAAAQAAAAAgCAYAAAD9qabkAAAACXBIWXMAAB"+
    // ... 48 concatenated parts total ...
    "f/f/v/v1eLFCI7FSwAAAAAElFTkSuQmCC";
    ```
  - Total base64 payload length: **2,736 characters**.
  - Decoded PNG size: **2,052 bytes**.
  - PNG Dimensions: **256 x 32 pixels**, color type **6 (RGBA)**, bit depth **8**.

- **GBDK Compiled Tiles**:
  - Location: `/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb/src/tiles.c`
  - Array name: `dandy_tiles` (line 5).
  - Total array size: **512 bytes** (line 4: `/* 32 tiles * 16 bytes per tile = 512 bytes */`).
  - Total number of tiles: **32** (0 to 31).
  - Format: GBDK 2bpp planar format (16 bytes per 8x8 tile, 2 planar bytes per row).

- **Game Engine Drawing Logic**:
  - Location: `/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb/src/dandy_core.c`
  - Player tile ID definition:
    ```c
    #define GET_PLAYER_TILE(p_idx, dir) (TILE_PLAYER1 + ((p_idx) << 3) + (dir))
    ```
  - Grid rendering: Uses 8x8 tiles for all background cells and hardware sprites (lines 318, 333, 337).

- **Build System**:
  - Location: `/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb/Makefile`
  - Compilation of ROM `bin/dandy.gb` is successful out-of-the-box using GBDK's compiler `lcc` via:
    ```bash
    make -C dandy-gb setup levels sprites bin/dandy.gb
    ```

- **Scope Document**:
  - Location: `/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/.agents/sub_orch_graphics_m1_gen2/SCOPE.md`
  - Discrepancy observed in Milestone T1 description:
    `Extract base64 from dandy-js/strike.js, decode, verify 256x16 PNG`

---

## 2. Logic Chain

1. **Verification of Sprite Sheet Size**:
   - The base64 data in `strike.js` decodes into a PNG image.
   - Parsing the PNG's `IHDR` chunk directly shows the dimensions are **256 x 32 pixels**.
   - This size represents exactly 32 sprites of 16x16 pixels (arranged in 2 rows of 16 sprites).
   - This contradicts the `SCOPE.md` statement that the sprite sheet is `256x16`. The scope must be corrected to prevent the Worker from failing verification checks on size.

2. **Verification of Tile Mapping**:
   - The Game Boy version's level maps use the same 60x30 grid size as the JS version.
   - However, the Game Boy viewport drawing code renders each cell as a single 8x8 tile or sprite.
   - In `tiles.c`, there are exactly 32 tiles of 8x8 pixels.
   - The 32 sprites in the JS version (16 static + 8 arrows + 8 players) map 1-to-1 to the 32 tiles in GBDK.
   - Therefore, there is no multi-tile layout (like 2x2 grids) for gameplay entities; each 16x16 JS sprite has been downscaled 2x to a single 8x8 GBDK tile.

3. **Validation of Environment Constraints**:
   - Running Python's `from PIL import Image` on the host system fails with `ModuleNotFoundError`.
   - To make the Worker robust and independent of external package installations, the verification script `verify_graphics.py` must use a **zero-dependency** pure-Python approach for decoding the original PNG and writing the stitched audit PNG (leveraging the standard `zlib` and `struct` libraries).

---

## 3. Caveats

- **Transparencies in Sprite Tiles**: GBDK hardware sprites treat color index 0 as transparent. In our audit sheet, transparent pixels should be rendered with a solid background color (e.g., black or dark gray) to remain visible alongside non-transparent background tiles.
- **Hardware Palettes**: The verification script must apply BGP and OBP0 palette definitions exactly to recreate the colors as they appear on the Game Boy screen.

---

## 4. Conclusion

Milestone 1 is fully planned and ready for implementation by the Worker:
- The base64 asset in `strike.js` is a **256x32** PNG with 32 sprites.
- The Game Boy compiled asset in `tiles.c` contains 32 tiles of 8x8 pixels.
- The build system is fully operational.
- The Worker should implement:
  1. `extract_graphics.py` to decode the base64 payload to `dandy-gb/teamwork_graphics/strike_original.png`.
  2. `verify_graphics.py` using a pure-Python decoder/encoder to create the side-by-side comparison sheet `dandy-gb/teamwork_graphics/graphics_audit.png` (upscaling the 16x16 original by 8x and the 8x8 compiled by 16x to match size).

---

## 5. Verification Method

To verify the findings and proposed build system, run:
```bash
# 1. Verify clean build of the GameBoy ROM
make -C dandy-gb clean && make -C dandy-gb all

# 2. Check the size of the compiled tiles binary
ls -la dandy-gb/obj/tiles.o
```
These actions confirm the compiler is functioning and outputting the expected binary.
The files generated by the Worker can be inspected under `dandy-gb/teamwork_graphics/`.
