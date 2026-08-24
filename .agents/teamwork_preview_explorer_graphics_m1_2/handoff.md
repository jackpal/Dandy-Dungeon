# Handoff Report: Graphics Conversion Pipeline Milestone 1

## 1. Observation
- **Original Sprite Sheet**:
  - Located in `dandy-js/strike.js` on lines 6-54:
    ```javascript
    const strike = new Image();
    strike.src = "data:image/png;base64,"+
    "iVBORw0KGgoAAAANSUhEUgAAAQAAAAAgCAYAAAD9qabkAAAACXBIWXMAAB"+
    ...
    "vFlyI7FSwAAAAAElFTkSuQmCC";
    ```
  - Base64 data length: **2,736 characters**.
  - Decoded PNG size: **2,052 bytes** (verified via PIL/Image).
  - PNG Dimensions: **256x32 pixels** (mode: RGBA, 32 sprites of 16x16 pixels arranged in a 16x2 grid).
- **Game Boy Tiles**:
  - Located in `dandy-gb/src/tiles.c` on lines 5-102:
    ```c
    const unsigned char dandy_tiles[] = {
        /* Tile 0 */
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        ...
    };
    ```
  - Total array size: **512 bytes** (representing exactly 32 tiles of 8x8 pixels in GBDK 2bpp format).
  - Checked `dandy-gb/src/dandy_core.c` for viewport/screen size:
    - Viewport dimensions: 20x10 cells.
    - Screen height: 144 pixels. Viewport gameplay height: 10 * 8 = 80 pixels. HUD height: 8 * 8 = 64 pixels (total 144 pixels).
    - This confirms that each gameplay grid cell and sprite is exactly **8x8 pixels**.
- **Game Boy Build System**:
  - Makefile targets in `dandy-gb/Makefile` include `all` (requires `setup`, `levels`, `sprites`, links `bin/dandy.gb`), `levels` (runs `convert_levels.py`), and `sprites` (runs `compile_bmp_sprites.py`).
  - GBDK compiler `lcc` is installed at `/usr/local/google/home/jackpal/Developer/gbdk/bin/lcc`.
- **Python Environment**:
  - The project's local virtual environment at `dandy-gb/.venv/` exists and contains Pillow version **12.2.0** and numpy.

---

## 2. Logic Chain
1. **Observation 1 (Viewport & Screen Geometry)** shows that the Game Boy screen is 160x144 pixels, divided into a 20x10 gameplay viewport (each cell being 8x8 pixels) and an 8-row HUD (each cell being 8x8 pixels).
2. **Observation 2 (Game Boy Sprite Coordinates)** in `gameboy_hal.c` registers hardware sprites with coordinates `sx * 8` and `sy * 8`, pointing to indices in VRAM loaded from `dandy_tiles`.
3. **Inference A**: Since all cells and sprites in the Game Boy game are strictly 8x8 pixels, the 32 original 16x16 sprites in the JS version cannot be composed of 4 tiles of 8x8. Instead, they must map 1-to-1 to the 32 Game Boy 8x8 tiles.
4. **Observation 3 (1-to-1 Mapping)**: The JS sprite sheet contains exactly 32 sprites (16x2 grid of 16x16 pixels) and the Game Boy `tiles.c` contains exactly 32 tiles (8x8 pixels). This confirms the 1-to-1 correspondence.
5. **Observation 4 (Python Venv)**: Since the local `.venv/` contains Pillow 12.2.0, we can run all python verification scripts using `/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb/.venv/bin/python` to ensure Pillow is available without system-level dependencies.
6. **Inference B**: A visual audit script can load both assets, decode the Game Boy 2bpp bytes to 8x8 pixels (using the correct BGP/OBP0 hardware palettes), upscale the Game Boy tiles by 8x (to 64x64) and the original tiles by 4x (to 64x64), and stitch them side-by-side to verify the visual fidelity of the hand-crafted downscaled assets.

---

## 3. Caveats
- **Colors & Palettes**: The original JS sprite sheet is RGBA with a black background, while the Game Boy rendering uses palettes (BGP/OBP0). In our verification script, we apply the BGP palette to background tiles (0..8, 12..15, 20..23, 28..31) and the OBP0 palette to sprite tiles (9..11, 16..19, 24..27) so the decoded tiles match the Game Boy's actual screen colors.
- **Compiler Availability**: We verified that `lcc` exists at `/usr/local/google/home/jackpal/Developer/gbdk/bin/lcc` and is executable. We assume the environment is stable for the compilation phase.

---

## 4. Conclusion
Milestone 1 is fully planned and verified. The Game Boy port is strictly 8x8, meaning there are no multi-tile 16x16 sprites; they map 1-to-1.
The Worker should write the proposed extraction script (`extract_sprites.py`) and verification script (`verify_graphics.py`), execute them in the local virtual environment, and compile the Game Boy codebase.
This will successfully extract the original assets, perform the pixel-level visual audit into `graphics_audit.png`, and compile the ROM cleanly.

---

## 5. Verification Method
To independently verify the implementation, the Worker can run:
1. **Compilation**:
   ```bash
   cd dandy-gb
   make clean && make
   ```
   *Verification*: Check that `bin/dandy.gb` is created and that the compiler output contains no errors or warnings.
2. **Extraction and Audit**:
   ```bash
   dandy-gb/.venv/bin/python tools/extract_sprites.py
   dandy-gb/.venv/bin/python tools/verify_graphics.py
   ```
   *Verification*: Inspect `dandy-gb/teamwork_graphics/strike_original.png` (dimensions must be 256x32) and `dandy-gb/teamwork_graphics/graphics_audit.png` (dimensions must be 1024x256, showing the 32 tiles side-by-side).
