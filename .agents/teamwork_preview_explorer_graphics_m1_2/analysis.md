# Milestone 1 Analysis Report: Graphics Conversion Pipeline

## Executive Summary
This report presents the findings, codebase analysis, and detailed implementation plan for Milestone 1 of the Dandy Dungeon graphics conversion pipeline. Through direct static analysis of the JavaScript and Game Boy codebases, combined with dynamic execution of custom prototyping scripts, we have established the ground truth regarding the asset dimensions, format representation, and build configurations.

Our key discovery is that the Game Boy port is strictly designed around **8x8 pixel gameplay cells and sprite tiles**. Consequently, the 32 original **16x16 pixel sprites** from the JavaScript version map **1-to-1** to the 32 Game Boy **8x8 pixel tiles** (which are hand-crafted, downscaled representations). A 16x16 sprite is **not** composed of four 8x8 tiles.

We have fully prototyped and verified the extraction, decoding, and side-by-side nearest-neighbor stitching logic. The proposed implementation strategy for the Worker is complete, robust, and utilizes the project's existing virtual environment to ensure zero external dependency issues.

---

## 1. JavaScript Sprite Sheet Analysis (`dandy-js/strike.js`)
- **Variable Name**: `strike.src` (assigned to an `Image` object named `strike` on line 5).
- **Exact Format**: A PNG image embedded as a Base64-encoded Data URL: `"data:image/png;base64," + ...`
- **Base64 String Length**: **2,736 characters** (excluding quotes, plus signs, and newlines).
- **Decoded PNG Size**: **2,052 bytes**.
- **Dimensions**: **256x32 pixels** (verified via PNG IHDR chunk parsing).
- **Sprite Layout**:
  - The sprite sheet contains **32 sprites**, each of size **16x16 pixels**, arranged in a **16x2 grid** (16 columns, 2 rows).
  - Row 0 (top row) contains sprites for tile IDs **0 to 15** (mapped as `x_start = (i % 16) * 16`, `y_start = 0`).
  - Row 1 (bottom row) contains sprites for tile IDs **16 to 31** (mapped as `x_start = (i - 16) * 16`, `y_start = 16`).
  - These IDs map exactly to the game's semantic entities: Space (0), Wall (1), Door (2), Up (3), Down (4), Key (5), Food (6), Money (7), Bomb (8), Monsters (9-11), Heart (12), Generators (13-15), Arrows (16-19), and Player 1 (24-27).

---

## 2. Game Boy Compiled Tiles Analysis (`dandy-gb/src/tiles.c`)
- **Representation**: A flat 1D byte array defined as `const unsigned char dandy_tiles[]`.
- **Array Size**: **512 bytes** (32 tiles * 16 bytes per tile).
- **Number of Tiles**: **32 tiles**, numbered 0 to 31.
- **GBDK 2bpp Format Encoding**:
  - Each tile is **8x8 pixels** (2 bits per pixel, supporting 4 colors).
  - A tile consists of **16 bytes**, with **2 bytes per row** for the 8 horizontal rows:
    - **Byte 1 (Low Byte)**: Holds the least significant bit (bit 0) of the color index for the 8 pixels (MSB-first, left-to-right).
    - **Byte 2 (High Byte)**: Holds the most significant bit (bit 1) of the color index for the 8 pixels (MSB-first, left-to-right).
  - The color index of pixel `x` (0 to 7) in row `y` is:
    ```python
    low_byte = tile_bytes[y * 2]
    high_byte = tile_bytes[y * 2 + 1]
    bit0 = (low_byte >> (7 - x)) & 1
    bit1 = (high_byte >> (7 - x)) & 1
    color_index = (bit1 << 1) | bit0
    ```
- **Spatial Mapping and Viewport Geometry**:
  - In `dandy-gb/src/dandy_core.c`, the gameplay viewport is drawn on a **20x10 grid of cells**.
  - On the Game Boy's **160x144 pixel screen**, 20 columns * 8 pixels = 160 pixels (full width).
  - The gameplay area occupies 10 rows * 8 pixels = 80 pixels in height.
  - The remaining 64 pixels (8 rows of 8x8 tiles) are filled by the HUD/Scoreboard (columns 0..19, rows 10..17 in VRAM).
  - This confirms that **all sprites and background tiles in the Game Boy game are strictly 8x8 pixels**.
  - **Correction of Assumption**: A 16x16 sprite is **not** composed of four 8x8 tiles in the Game Boy port. Instead, there is a **1-to-1 mapping** where each 16x16 sprite in the original JS version maps directly to a single 8x8 tile in the Game Boy version. The 8x8 tiles are hand-crafted downscaled pixel art, designed to fit the Game Boy's hardware constraints.

---

## 3. Game Boy Build System Analysis (`dandy-gb/Makefile`)
- **Compiler**: Uses the GBDK compiler `lcc` located at `/usr/local/google/home/jackpal/Developer/gbdk/bin/lcc` (which has been verified to exist and be executable on the system).
- **Compile Targets**:
  - `all` (default): Runs `setup`, `levels`, `sprites`, and links the final ROM `bin/dandy.gb`.
  - `setup`: Creates the output directories: `obj/`, `bin/`, and `web/`.
  - `levels`: Executes `python3 tools/convert_levels.py` to translate levels from JavaScript into C header files.
  - `sprites`: Executes `python3 tools/compile_bmp_sprites.py` to compile the 32 hand-crafted 8x8 glyph definitions into the GBDK 2bpp `tiles.c` and `tiles.h` source files.
  - `clean`: Deletes intermediate object files in `obj/`, the output binaries in `bin/`, WebAssembly outputs in `web/`, and temporary test assets.
- **Compiler Flags**:
  - `LCCFLAGS = -Wa-l -Wl-m -Wl-yo2` (Generates assembler list file, linker map file, and configures ROM size/MBC type).
  - For standard C compilation: `-Wf--opt-code-size -c` (optimizes for code size, crucial for ROM space).

---

## 4. Scope Document Summary (`SCOPE.md`)
Milestone 1 establishes the foundations for asset extraction, decoding, and visual audit verification. It defines four clear tasks:
1. **T1 (Extract & Decode)**: Extract base64 from `strike.js`, decode to PNG, and save to `dandy-gb/teamwork_graphics/strike_original.png`.
2. **T2 (Verification Script)**: Develop `verify_graphics.py` to parse GBDK 2bpp from `tiles.c`, decode to pixels, upscale 8x, and compare side-by-side with original.
3. **T3 (GBDK Project Compilation)**: Verify the Game Boy C codebase compiles cleanly with zero warnings/errors via `make clean && make`.
4. **T4 (Run Audit & Verification)**: Run the script to generate `graphics_audit.png` and verify the correctness of the asset mappings.

---

## 5. Proposed Implementation Strategy for the Worker

### A. Python Environment Optimization
The project contains a pre-configured Python virtual environment located at `/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb/.venv/`.
This environment has been verified to contain **Pillow (12.2.0)** and **numpy**.
**Recommendation**: The Worker must run all python commands using `/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb/.venv/bin/python` to ensure that Pillow is available and no system package installation is required.

### B. Task 1: Sprite Sheet Extraction Script
The Worker should write and execute a Python script to dynamically extract the base64 string from `strike.js`, decode it, and save the original PNG. This avoids manual copy-paste errors.

**Proposed Extraction Code (`dandy-gb/tools/extract_sprites.py`)**:
```python
import os
import re
import base64

def main():
    js_path = os.path.normpath(os.path.join(os.path.dirname(__file__), "../../dandy-js/strike.js"))
    output_dir = os.path.normpath(os.path.join(os.path.dirname(__file__), "../teamwork_graphics"))
    output_path = os.path.join(output_dir, "strike_original.png")
    
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"Reading sprite sheet from {js_path}...")
    with open(js_path, "r") as f:
        content = f.read()
        
    # Regex to extract all quoted strings after strike.src assignment
    pattern = r'strike\.src\s*=\s*"data:image/png;base64,"\s*\+\s*(.*?;)'
    match = re.search(pattern, content, re.DOTALL)
    if not match:
        raise ValueError("Could not find base64 sprite data in strike.js")
        
    parts_block = match.group(1)
    str_pattern = r'"([^"]*)"'
    strings = re.findall(str_pattern, parts_block)
    base64_str = "".join(strings)
    
    print(f"Decoding base64 string (length: {len(base64_str)})...")
    png_bytes = base64.b64decode(base64_str)
    
    print(f"Saving decoded PNG to {output_path}...")
    with open(output_path, "wb") as f:
        f.write(png_bytes)
        
    print("Sprite sheet extraction complete!")

if __name__ == "__main__":
    main()
```

### C. Task 2: GBDK 2bpp Decoder & Auditing Script (`verify_graphics.py`)
To perform high-fidelity visual audits, we must decode the GBDK 2bpp tiles using the exact color mappings intended for the Game Boy hardware. Since background and sprite tiles use different hardware palettes, we apply the BGP palette to background tiles and the transparent-aware OBP0 palette to sprite tiles.
To make the comparison visually clear, we upscale the original 16x16 tiles by **4x** (to 64x64) and the Game Boy 8x8 tiles by **8x** (to 64x64), stitching them side-by-side into a neat 8-column by 4-row grid.

**Proposed Verification Code (`dandy-gb/tools/verify_graphics.py`)**:
```python
import os
import re
import io
import base64
from PIL import Image

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
    # Decodes a 16-byte Game Boy 2bpp tile to an 8x8 RGBA Image
    pixels = bytearray(8 * 8 * 4)
    
    if is_sprite:
        # Sprite palette (OBP0): 0=Transparent, 1=White, 2=Dark Gray, 3=Black
        palette = [
            (0, 0, 0, 0),          # 0: Transparent
            (255, 255, 255, 255),  # 1: White
            (100, 100, 100, 255),  # 2: Dark Gray
            (0, 0, 0, 255)         # 3: Black
        ]
    else:
        # Background palette (BGP): 0=Black, 1=Dark Gray, 2=Light Gray, 3=White
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
    current_dir = os.path.dirname(os.path.abspath(__file__))
    js_path = os.path.normpath(os.path.join(current_dir, "../../dandy-js/strike.js"))
    tiles_c_path = os.path.normpath(os.path.join(current_dir, "../src/tiles.c"))
    original_png_path = os.path.normpath(os.path.join(current_dir, "../teamwork_graphics/strike_original.png"))
    output_audit_path = os.path.normpath(os.path.join(current_dir, "../teamwork_graphics/graphics_audit.png"))
    
    print("Starting graphics verification and audit...")
    
    # 1. Extract and load original sprite sheet
    if os.path.exists(original_png_path):
        print(f"Loading existing original sprite sheet from {original_png_path}...")
        original_sheet = Image.open(original_png_path)
    else:
        print("Original sprite sheet not found at path, extracting dynamically from strike.js...")
        # Fallback dynamic extraction
        with open(js_path, "r") as f:
            content = f.read()
        pattern = r'strike\.src\s*=\s*"data:image/png;base64,"\s*\+\s*(.*?;)'
        match = re.search(pattern, content, re.DOTALL)
        parts_block = match.group(1)
        strings = re.findall(r'"([^"]*)"', parts_block)
        b64_str = "".join(strings)
        original_sheet = Image.open(io.BytesIO(base64.b64decode(b64_str)))
        
    # 2. Parse GBDK tiles from tiles.c
    print(f"Parsing GBDK tiles from {tiles_c_path}...")
    tiles_bytes = parse_tiles_c(tiles_c_path)
    
    # 3. Setup audit image grid (8 columns, 4 rows)
    # Each cell is 128x64 (64x64 original upscaled 4x, 64x64 Game Boy upscaled 8x)
    cell_width = 128
    cell_height = 64
    grid_cols = 8
    grid_rows = 4
    
    audit_image = Image.new("RGBA", (grid_cols * cell_width, grid_rows * cell_height), (50, 50, 50, 255))
    
    # Select nearest-neighbor filter
    try:
        nn_filter = Image.Resampling.NEAREST
    except AttributeError:
        nn_filter = Image.NEAREST
        
    print("Decoding, scaling, and stitching tiles side-by-side...")
    for i in range(32):
        col = i % grid_cols
        row = i // grid_cols
        cell_x = col * cell_width
        cell_y = row * cell_height
        
        # Crop original 16x16 tile (arranged 16 columns, 2 rows in original sheet)
        orig_col = i % 16
        orig_row = i // 16
        orig_tile = original_sheet.crop((orig_col * 16, orig_row * 16, (orig_col + 1) * 16, (orig_row + 1) * 16))
        orig_upscaled = orig_tile.resize((64, 64), nn_filter)
        
        # Extract and decode Game Boy 8x8 tile
        tile_offset = i * 16
        tile_data = tiles_bytes[tile_offset:tile_offset+16]
        
        # Categorize sprite tiles vs background tiles to apply correct hardware palettes
        is_sprite = (9 <= i <= 11) or (16 <= i <= 19) or (24 <= i <= 27)
        gb_tile = decode_gb_tile(tile_data, is_sprite=is_sprite)
        gb_upscaled = gb_tile.resize((64, 64), nn_filter)
        
        # Paste side-by-side into the cell
        audit_image.paste(orig_upscaled, (cell_x, cell_y))
        audit_image.paste(gb_upscaled, (cell_x + 64, cell_y), gb_upscaled)
        
    # Save the audit image
    os.makedirs(os.path.dirname(output_audit_path), exist_ok=True)
    audit_image.save(output_audit_path)
    print(f"Graphics audit image saved successfully to {output_audit_path}!")

if __name__ == "__main__":
    main()
```

### D. Exact Build and Verification Commands
The Worker can build the codebase and run the entire verification pipeline by executing the following commands sequentially:

1. **Clean and Compile the ROM**:
   ```bash
   cd dandy-gb
   make clean && make
   ```
   *Expectation*: This must complete with zero errors and warnings, and generate the final Game Boy ROM at `bin/dandy.gb`.

2. **Run Sprite Sheet Extraction**:
   ```bash
   dandy-gb/.venv/bin/python tools/extract_sprites.py
   ```
   *Expectation*: Decodes and writes `teamwork_graphics/strike_original.png` (256x32, 2052 bytes).

3. **Run Verification and Generate Audit Image**:
   ```bash
   dandy-gb/.venv/bin/python tools/verify_graphics.py
   ```
   *Expectation*: Decodes GBDK 2bpp tiles, upscales them, compares them with the original sprites, and generates `teamwork_graphics/graphics_audit.png` (1024x256).

---

## 6. Recommendations & Findings Summary
- **No Multi-Tile Layout Needed**: The codebase analysis confirms that sprites are drawn directly as 8x8 tiles in the Game Boy game. We do not need to support composing 16x16 sprites out of four 8x8 tiles, because each game cell is exactly 8x8.
- **Palette Sensitivity**: Background tiles and sprite tiles use different hardware palettes in `main.c` (BGP = `0x1B`, OBP0 = `0xE0`). Our proposed decoder handles this correctly by applying the appropriate palette based on the tile type, ensuring the audit images have accurate colors.
- **Robust Execution**: Using the project's pre-configured virtual environment `dandy-gb/.venv` ensures that the Worker can run the Pillow-based scripts without any installation issues or missing dependency failures.
