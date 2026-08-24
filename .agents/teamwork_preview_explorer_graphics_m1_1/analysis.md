# Milestone 1 Graphics Conversion Pipeline: Analysis & Proposal

## Executive Summary
This analysis establishes the foundation for the GameBoy Dandy Dungeon graphics conversion pipeline. By inspecting the JavaScript sprite sheet, GameBoy VRAM tile definitions, and GBDK build system, we have designed a robust verification script that decodes GBDK 2bpp tiles and compares them side-by-side with original assets. Crucially, we discovered that the GameBoy implementation uses a highly efficient **1-to-1 mapping** (downscaling 16x16 original sprites to single 8x8 GameBoy tiles) rather than a 4-to-1 layout, and we have successfully verified the GBDK build system on the host.

---

## 1. Base64 Sprite Sheet Analysis (`dandy-js/strike.js`)
*   **Variable Name**: `strike` (specifically, its `src` attribute is assigned the base64 data URL).
*   **Format**: Data URL format: `data:image/png;base64,` followed by the base64-encoded string.
*   **Structure**: The base64 string is split into **48 segments** in the JavaScript source file, concatenated together using the `+` operator.
*   **Length**:
    *   Total base64 characters (excluding quotes, pluses, and whitespace): **2,736 characters**.
    *   Decoded binary length: **2,052 bytes**.
*   **Image Properties**:
    *   Format: PNG.
    *   Dimensions: **256x32 pixels**.
    *   Since the original game uses 16x16 pixels per tile/sprite, this sprite sheet contains exactly **32 sprites** arranged in a 16x2 grid (16 columns, 2 rows).

---

## 2. GBDK 2bpp Tile Analysis (`dandy-gb/src/tiles.c`)
*   **Representation**: Stored as a flat C array of unsigned characters:
    ```c
    const unsigned char dandy_tiles[] = { ... };
    ```
*   **Size**: **512 bytes** (32 tiles * 16 bytes per tile).
*   **Number of Tiles**: **32 tiles**, numbered 0 to 31.
*   **Format details**:
    *   Each tile is 8x8 pixels.
    *   GameBoy 2bpp format uses 2 bytes per row of 8 pixels.
    *   `byte1` contains the low bit of the color index for the 8 pixels.
    *   `byte2` contains the high bit of the color index for the 8 pixels.
    *   For a pixel at column $x$ (0 to 7, MSB-first):
        *   `low_bit = (byte1 >> (7 - x)) & 1`
        *   `high_bit = (byte2 >> (7 - x)) & 1`
        *   `color_index = (high_bit << 1) | low_bit` (values 0, 1, 2, or 3).
*   **Tile Layout & 16x16 Mapping**:
    *   **Crucial Discovery**: The GameBoy version of Dandy Dungeon downscales the original 16x16 sprites into **single 8x8 tiles** to fit the GameBoy's screen resolution (160x144 pixels). The viewport is a 20x10 grid of 8x8 cells (160x80 pixels), with the remaining 160x64 pixels (20x8 cells) used for the HUD.
    *   Therefore, there is a **1-to-1 correspondence** between the 32 tiles in `dandy_tiles` and the 32 sprites in the original `strike.js` sheet.
    *   **Hypothetical 4-to-1 Layout**: If a 16x16 sprite *were* composed of four 8x8 tiles (e.g., Top-Left, Top-Right, Bottom-Left, Bottom-Right) in a sequential array, they would occupy 4 consecutive 8x8 tile indices (e.g., $N, N+1, N+2, N+3$), corresponding to:
        *   Top-Left: Tile $N$ (Bytes 0 to 15)
        *   Top-Right: Tile $N+1$ (Bytes 16 to 31)
        *   Bottom-Left: Tile $N+2$ (Bytes 32 to 47)
        *   Bottom-Right: Tile $N+3$ (Bytes 48 to 63)
        *   To reconstruct the 16x16 sprite, the pixels from these four 8x8 tiles would be stitched together into a 16x16 grid. *However, in the current dandy-gb implementation, this is not the case as every tile is standalone 8x8.*

---

## 3. Build System Analysis (`dandy-gb/Makefile`)
*   **Compiler**: `lcc` (linker/compiler front-end for GBDK/SDCC), located by default in `$(HOME)/Developer/gbdk/bin/lcc`.
*   **Compile Flags**:
    *   Individual files: `-Wf--opt-code-size -c` (optimizes for code size, crucial for 32KB GameBoy ROMs).
    *   Special case `levels.o`: `-Wf-bo1 -c` (compiles levels into ROM bank 1).
*   **Link Flags**:
    *   `LCCFLAGS = -Wa-l -Wl-m -Wl-yo2`
        *   `-Wa-l`: Generate assembler list file.
        *   `-Wl-m`: Generate linker map file.
        *   `-Wl-yo2`: Configure ROM size/MBC (MBC1 with 2 ROM banks, 32KB total ROM).
*   **Target Output**: `bin/dandy.gb` (GameBoy ROM).
*   **Build Targets**:
    *   `all`: Runs `setup`, `levels`, `sprites`, and links `bin/dandy.gb`.
    *   `setup`: Creates directories `obj/`, `bin/`, and `web/`.
    *   `levels`: Runs level converter `python3 tools/convert_levels.py` to generate `src/levels.c`/`levels.h`.
    *   `sprites`: Runs sprite compiler `python3 tools/compile_bmp_sprites.py` to generate `src/tiles.c`/`tiles.h`.
    *   `clean`: Removes `obj/`, `bin/`, and other build artifacts.
*   **Verification**: Executing `make clean && make` in the `dandy-gb/` directory succeeds with zero warnings and zero errors, successfully generating a working GameBoy ROM at `dandy-gb/bin/dandy.gb`.

---

## 4. Proposed Implementation Strategy for the Worker

We propose the following detailed plan and script designs for the implementer (Worker) to execute Milestone 1:

### A. Directory Structure Compliance
All new assets and verification tools must reside in their designated directories:
*   `dandy-gb/teamwork_graphics/` — Contains decoded original sheet and audit sheet.
*   `dandy-gb/tools/` — Contains the Python verification script.

### B. Python Environment Recommendation
*   **Important Discovery**: The `dandy-gb` directory contains a pre-configured virtual environment at `dandy-gb/.venv` which already includes the **Pillow** (`PIL`) and **PyBoy** libraries.
*   **Action**: The Worker must invoke Python using the virtual environment's interpreter:
    ```bash
    ./dandy-gb/.venv/bin/python3
    ```
    This avoids any library installation issues or global system package modifications.

### C. Step 1: Base64 Sprite Sheet Extraction Script
The Worker should implement a script `dandy-gb/tools/extract_original.py` (or integrate it into the verification script) using this robust, regex-based base64 parser:

```python
import base64
import os
import re

def extract_original_sprites():
    src_path = "dandy-js/strike.js"
    dest_dir = "dandy-gb/teamwork_graphics"
    dest_path = os.path.join(dest_dir, "strike_original.png")
    
    os.makedirs(dest_dir, exist_ok=True)
    
    print(f"Reading base64 sprite data from {src_path}...")
    with open(src_path, "r") as f:
        content = f.read()
        
    # Extract all double-quoted strings
    parts = re.findall(r'"([^"]+)"', content)
    b64_parts = []
    for p in parts:
        if not p.startswith("data:image/png;base64,"):
            clean = p.strip()
            if all(c in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=" for c in clean):
                b64_parts.append(clean)
                
    full_b64 = "".join(b64_parts)
    decoded_bytes = base64.b64decode(full_b64)
    
    print(f"Saving original spritesheet to {dest_path}...")
    with open(dest_path, "wb") as f:
        f.write(decoded_bytes)
    print("Extraction successful!")

if __name__ == "__main__":
    extract_original_sprites()
```

### D. Step 2: GBDK 2bpp Decoding & Visual Auditing Script
The Worker should implement the visual audit tool in `dandy-gb/tools/verify_graphics.py`.
This script will:
1. Parse the 2bpp bytes from `dandy-gb/src/tiles.c`.
2. Decode each 16-byte block into an 8x8 image using the appropriate hardware palette:
    *   **Background palette (BGP)** for background tiles.
    *   **Sprite palette (OBP0)** for player and monster sprites to ensure correct colors (handling transparency).
3. Upscale the GameBoy tiles 16x (to 128x128) and the corresponding original 16x16 tiles 8x (to 128x128) using nearest-neighbor scaling.
4. Stitch them side-by-side (256x128 per comparison block) in a 4x8 grid, saving to `dandy-gb/teamwork_graphics/graphics_audit.png`.

Here is the exact code for `dandy-gb/tools/verify_graphics.py`:

```python
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
    # GameBoy Hardware Palettes
    # Background (BGP = 0x1B): 0=Black, 1=Dark Gray, 2=Light Gray, 3=White
    bg_colors = [
        (0, 0, 0),        # 0: Black
        (96, 96, 96),     # 1: Dark Gray
        (176, 176, 176),  # 2: Light Gray
        (255, 255, 255)   # 3: White
    ]
    # Sprite (OBP0 = 0xE0): 0=Transparent/Black, 1=White, 2=Dark Gray, 3=Black
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
    base_dir = "dandy-gb"
    tiles_c_path = os.path.join(base_dir, "src/tiles.c")
    strike_png_path = os.path.join(base_dir, "teamwork_graphics/strike_original.png")
    audit_png_path = os.path.join(base_dir, "teamwork_graphics/graphics_audit.png")
    
    os.makedirs(os.path.dirname(audit_png_path), exist_ok=True)
    
    print("1. Parsing GameBoy tiles from tiles.c...")
    tiles_data = parse_tiles_c(tiles_c_path)
    
    print("2. Loading original sprite sheet...")
    strike_img = Image.open(strike_png_path)
    
    # 4 columns, 8 rows of comparison blocks (each block is 256x128)
    grid_img = Image.new("RGB", (1024, 1024), (50, 50, 50))
    
    # Identify Background tiles (BGP palette) to distinguish from Sprites (OBP palette)
    # Background indices in tiles.c: 0..8 (Space, Wall, Door, Up, Down, Key, Food, Money, Bomb)
    # and 12..15 (Heart, Gen1, Gen2, Gen3)
    bg_indices = set(list(range(9)) + list(range(12, 16)))
    
    for i in range(32):
        # Crop original 16x16 tile and upscale 8x to 128x128
        orig_col = i % 16
        orig_row = i // 16
        orig_box = (orig_col * 16, orig_row * 16, (orig_col + 1) * 16, (orig_row + 1) * 16)
        orig_tile = strike_img.crop(orig_box)
        orig_tile_scaled = orig_tile.resize((128, 128), Image.NEAREST)
        
        # Decode GameBoy 8x8 tile and upscale 16x to 128x128
        gb_tile_bytes = tiles_data[i * 16 : (i + 1) * 16]
        is_sprite = i not in bg_indices
        gb_tile = decode_gb_tile(gb_tile_bytes, is_sprite=is_sprite)
        gb_tile_scaled = gb_tile.resize((128, 128), Image.NEAREST)
        
        # Paste into 4x8 grid
        grid_col = i % 4
        grid_row = i // 4
        cell_x = grid_col * 256
        cell_y = grid_row * 128
        
        grid_img.paste(orig_tile_scaled, (cell_x + 1, cell_y + 1))
        grid_img.paste(gb_tile_scaled, (cell_x + 129, cell_y + 1))
        
    print(f"3. Saving final audit image to {audit_png_path}...")
    grid_img.save(audit_png_path)
    print("Visual audit sheet generated successfully!")

if __name__ == "__main__":
    main()
```

### E. Exact Build Command & Verification Steps
The Worker should run the following commands on the GameBoy workspace to perform the full conversion, build, and validation cycle:

1.  **Extract Original Sprites**:
    ```bash
    ./dandy-gb/.venv/bin/python3 -c "import sys; sys.path.append('dandy-gb/tools'); from extract_original import extract_original_sprites; extract_original_sprites()"
    ```
    *Verification*: Confirm `dandy-gb/teamwork_graphics/strike_original.png` is generated and has dimensions 256x32.
2.  **Generate Visual Audit**:
    ```bash
    ./dandy-gb/.venv/bin/python3 dandy-gb/tools/verify_graphics.py
    ```
    *Verification*: Confirm `dandy-gb/teamwork_graphics/graphics_audit.png` is generated, has dimensions 1024x1024, and visually shows the original 16x16 sprites next to their decoded 8x8 GameBoy equivalents.
3.  **Compile ROM**:
    ```bash
    make -C dandy-gb clean && make -C dandy-gb
    ```
    *Verification*: Ensure the build completes with exit code `0` and generates `dandy-gb/bin/dandy.gb`.
4.  **Run Emulator E2E Tests**:
    ```bash
    make -C dandy-gb test_emu
    ```
    *Verification*: Ensure the PyBoy emulator-driven integration tests pass successfully.
