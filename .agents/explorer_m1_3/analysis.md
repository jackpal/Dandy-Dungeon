# Analysis Report: Dandy Dungeon Graphics Conversion (Milestone 1)

**Prepared by**: Explorer 3 (Milestone 1)  
**Date**: 2026-06-21T00:21:21Z  
**Status**: COMPLETE  

---

## Executive Summary
This investigation analyzed the graphics pipeline for the Dandy Dungeon GameBoy port, focusing on the extraction of the base64-encoded sprite sheet, the structure of the compiled 2bpp tiles, the build system integration, and the mapping between the original 16x16 sprites and the GameBoy 8x8 tiles.

Our core findings include:
1. **Pristine Reference Sprite Sheet**: The base64-encoded sprite sheet in `dandy-js/strike.js` decodes to a **256x32** PNG image (not 256x16 as stated in the scope document), containing two rows of sixteen 16x16 sprites. Row 0 contains background tiles and monsters; Row 1 contains directional arrows and player sprites.
2. **GameBoy Asset Representation**: GameBoy tiles are stored in `dandy-gb/src/tiles.c` as a 512-byte array of thirty-two 8x8 tiles in GBDK 2bpp planar format. These tiles are programmatically compiled from character-art grids in `dandy-gb/tools/compile_bmp_sprites.py`.
3. **Critical Mapping & Logic Discrepancies**:
   - **Arrow Mismatch**: The core engine (`dandy_core.c`) generates 8-way arrow tiles (IDs 16..23), but the GameBoy tiles only define 4 cardinal direction arrows (IDs 16..19). This results in incorrect or blank arrow sprites during gameplay.
   - **Player Direction & Invisible Sprite Bug**: The core engine rotates the player tile dynamically from `24 + dir` (where `dir` is 0..7). However, GBDK tiles 24..27 represent the four cardinal directions of Player 1, and tiles 28..31 are empty. Consequently:
     - Dirs 0..3 draw the player incorrectly rotated (e.g. facing Down when moving Up).
     - Dirs 4..7 map to empty tiles, making the player **completely invisible**.
     - All players are mapped to Player 1's tiles, making multiplayer characters look identical.
4. **Successful Verification Prototyping**: We successfully designed, implemented, and ran a prototype verification script `verify_graphics_proto.py` using the virtual environment interpreter, generating `graphics_audit.png` which visually proves these mismatches.

---

## Detailed Investigation Findings

### 1. Base64-Encoded Sprite Sheet (`dandy-js/strike.js`)
- **Variable**: The base64 string is assigned to the `src` property of a global `strike` Image object:
  ```javascript
  const strike = new Image();
  strike.src = "data:image/png;base64," + "iVBORw0...";
  ```
- **Exact Format**: A standard Base64-encoded PNG image.
- **True Dimensions**: **256x32 pixels** (consisting of two rows of sixteen 16x16 sprites).
- **Layout**:
  - **Row 0 (Tiles 0..15)**: Static elements (0: Space, 1: Wall, 2: Door, 3: Up, 4: Down, 5: Key, 6: Food, 7: Money, 8: Bomb, 9..11: Monsters 1..3, 12: Heart, 13..15: Generators 1..3).
  - **Row 1 (Tiles 16..31)**: Dynamic elements (16..23: Arrows in 8 directions, 24..27: Player 1 to 4 static sprites, 28..31: Unused/empty).

### 2. GBDK 2bpp Format Structure (`dandy-gb/src/tiles.c`)
- **Structure**: Stored in `tiles.c` as a single flat array:
  ```c
  const unsigned char dandy_tiles[] = { ... };
  ```
  It contains exactly 32 tiles * 16 bytes per tile = 512 bytes.
- **2bpp Planar Format Details**:
  - Each 8x8 tile is represented by 8 rows of 2 bytes each.
  - The first byte of each row represents the LSB (Bit 0) of the color index for the 8 pixels.
  - The second byte of each row represents the MSB (Bit 1) of the color index.
  - Pixels are packed MSB-first (left-to-right, i.e., bit 7 of the bytes corresponds to the leftmost pixel).
  - Color index for pixel `x` (0..7) is `(bit1 << 1) | bit0`, which maps to one of 4 colors in the GameBoy palette registers (`BGP_REG`, `OBP0_REG`, `OBP1_REG`).
- **Tile Asset Origins**:
  The tiles in `tiles.c` are compiled from native 8x8 text-art definitions defined in `dandy-gb/tools/compile_bmp_sprites.py`. For example, Player 1 Down (Tile 24) is defined as:
  ```python
  24: [
      "00333300", #    ####    (Helmet top)
      "03111130", #   #WWWW#   (Face visor)
      "31311313", #  W#W##W#W  (Visor slit & eyes)
      "31111113", #  WWWWWWWW  (Shield shoulder)
      "03222230", #   #DDDD#   (Metal chest plate)
      "03111130", #   #WWWW#   (White tunic)
      "00311300", #    #WW#    (Legs)
      "00333300"  #    ####    (Boots)
  ]
  ```

### 3. GameBoy Build Process (`dandy-gb/Makefile`)
- **Key Compiler**: GBDK's `lcc` compiler is used, referencing the `GBDKDIR` directory.
- **Dependencies & Build Pipeline**:
  - `all` depends on `setup`, `levels`, `sprites`, and `bin/dandy.gb`.
  - `levels` target: Runs `python3 tools/convert_levels.py` to compile level files.
  - `sprites` target: Runs `python3 tools/compile_bmp_sprites.py` to regenerate `tiles.h` and `tiles.c` from the text-art definitions.
  - `bin/dandy.gb` linking: Compiles `main.c`, `dandy_core.c`, `gameboy_hal.c`, `levels.c`, and `tiles.c`, and links them using:
    ```makefile
    $(LCC) $(LCCFLAGS) -o $@ $(OBJS)
    ```
    with flags `-Wa-l -Wl-m -Wl-yo2`.
  - `test` target: Compiles a mock HAL dynamic library `libdandy_test.so` and runs Python unittests.
  - `test_emu` target: Spawns a virtual environment, installs PyBoy/NumPy/Pillow, and runs ROM-level E2E emulator tests.

---

## Detailed Mapping and Logic Analysis

### The Mapping Discrepancy Matrix
By generating and reviewing the `graphics_audit.png` comparison sheet, we uncovered the following complete evidence chain:

| Tile ID | JS Reference Sprite (16x16) | GBDK Tile Art (8x8) | Status / Discrepancy |
| :---: | :--- | :--- | :--- |
| **0** | Empty Space | Solid Black | Perfect 1:1 Match |
| **1** | Blue Checkered Wall | Grayscale Brick Wall | Artistic Redesign (Correct) |
| **2** | Blue Door with Frame | Vertical Iron Grate | Artistic Redesign (Correct) |
| **3** | Pink Stairs Up 'U' | Staircase Railing Outline | Artistic Redesign (Correct) |
| **4** | Pink Stairs Down 'D' | Receding Steps into Pit | Artistic Redesign (Correct) |
| **5** | Pink Key | Grayscale Key | Perfect 1:1 Match |
| **6** | Blue Cross (Food) | Roast Leg of Meat | Artistic Redesign (Correct) |
| **7** | Pink Dollar Sign | Grayscale Dollar Sign | Perfect 1:1 Match |
| **8** | White Bomb | Grayscale Bomb with Spark | Artistic Redesign (Correct) |
| **9** | Ghost Monster | Ghost Head | Perfect 1:1 Match |
| **10** | Smiley Face Monster | Demon/Imp Head | Artistic Redesign (Correct) |
| **11** | Boxy Red-Eyed Monster | Rocky Golem Head | Artistic Redesign (Correct) |
| **12** | Pink Heart | Heart Flask Potion | Artistic Redesign (Correct) |
| **13** | One Skull Nest | Twig Nest | Artistic Redesign (Correct) |
| **14** | Two Skull Nest | Nest with Skull | Perfect 1:1 Match |
| **15** | Heavy Skull Nest | Monolith Spawner | Artistic Redesign (Correct) |
| **16** | **Arrow Diagonal Down-Left** | **Arrow Down** | **MISMATCH (Bug in Arrow Rendering)** |
| **17** | **Arrow Left** | **Arrow Up** | **MISMATCH (Bug in Arrow Rendering)** |
| **18** | **Arrow Diagonal Up-Left** | **Arrow Left** | **MISMATCH (Bug in Arrow Rendering)** |
| **19** | **Arrow Up** | **Arrow Right** | **MISMATCH (Bug in Arrow Rendering)** |
| **20..23** | **Diagonal Arrows** | **Solid Black (Empty)** | **MISMATCH (Blank Arrows)** |
| **24** | **Player 1 (Facing Down)** | **Player 1 Down** | Perfect 1:1 Match |
| **25** | **Player 2 (Facing Down)** | **Player 1 Up** | **MISMATCH (Cycles Player Sprites)** |
| **26** | **Player 3 (Facing Down)** | **Player 1 Left** | **MISMATCH (Cycles Player Sprites)** |
| **27** | **Player 4 (Facing Down)** | **Player 1 Right** | **MISMATCH (Cycles Player Sprites)** |
| **28..31** | **Unused / Empty** | **Solid Black (Empty)** | **MISMATCH (Invisible Player Bug)** |

### Logical Proof of the Player Invisible Sprite Bug
1. **Core Engine Input**: In `dandy_core.c` line 431, when a player moves, the core updates the map with:
   ```c
   dandy_map[pos] = GET_PLAYER_TILE(p_idx, player_dir[p_idx]);
   ```
   For Player 1 (`p_idx = 0`), this generates tile IDs in the range `24..31` corresponding to directions `0..7` (0: Up, 1: Up-Right, 2: Right, 3: Down-Right, 4: Down, 5: Down-Left, 6: Left, 7: Up-Left).
2. **HAL Mapping Logic**: In `dandy-gb/src/gameboy_hal.c`, the functions `hal_draw_tile` and `hal_set_sprite` map player tile IDs using:
   ```c
   tile_id = TILE_PLAYER1 + ((tile_id - TILE_PLAYER1) & 7);
   ```
   Since `TILE_PLAYER1` is 24, this maps the player tiles to `24 + dir`.
3. **GBDK Tile Inventory**: `tiles.c` only defines assets for tiles 24 to 27 (Down, Up, Left, Right). Tiles 28 to 31 are empty padding (all zeros).
4. **Behavior Analysis**:
   - **Direction 0 (Up)** -> Maps to Tile 24 (`TILE_PLAYER1_DOWN`). Player faces Down while moving Up.
   - **Direction 1 (Up-Right)** -> Maps to Tile 25 (`TILE_PLAYER1_UP`). Player faces Up while moving Up-Right.
   - **Direction 2 (Right)** -> Maps to Tile 26 (`TILE_PLAYER1_LEFT`). Player faces Left while moving Right.
   - **Direction 3 (Down-Right)** -> Maps to Tile 27 (`TILE_PLAYER1_RIGHT`). Player faces Right while moving Down-Right.
   - **Directions 4..7 (Down, Down-Left, Left, Up-Left)** -> Map to Tiles 28..31. **The player completely disappears from the screen!**

### Resolution Plan
To resolve the player and arrow mismatches:
1. **Player Rendering Fix**: Since the sprite assets only support 4 cardinal directions, the GameBoy HAL should map the player's 8-way direction to one of the 4 cardinal tiles (24: Down, 25: Up, 26: Left, 27: Right).
   We can define a static lookup table in `gameboy_hal.c`:
   ```c
   static const uint8_t dir_to_cardinal[8] = {
       1, // 0: Up         -> Tile 25 (Player Up)
       1, // 1: Up-Right   -> Tile 25 (Player Up)
       3, // 2: Right      -> Tile 27 (Player Right)
       0, // 3: Down-Right -> Tile 24 (Player Down)
       0, // 4: Down       -> Tile 24 (Player Down)
       2, // 5: Down-Left  -> Tile 26 (Player Left)
       2, // 6: Left       -> Tile 26 (Player Left)
       1  // 7: Up-Left    -> Tile 25 (Player Up)
   };
   ```
   And apply it in `hal_draw_tile` and `hal_set_sprite`:
   ```c
   if (tile_id >= TILE_PLAYER1 && tile_id <= TILE_PLAYER1 + 31) {
       uint8_t dir = (tile_id - TILE_PLAYER1) & 7;
       tile_id = TILE_PLAYER1 + dir_to_cardinal[dir];
   }
   ```
   This keeps all players visible and properly oriented!

2. **Arrow Rendering Fix**: Similarly, arrows are 8-way in the core but have only 4 tiles (16: Down, 17: Up, 18: Left, 19: Right). Note that Tile 16 in GBDK is Down, and 17 is Up, which is inverted compared to standard directions.
   We can define a static lookup table for arrows:
   ```c
   static const uint8_t arrow_dir_to_tile[8] = {
       1, // 0: Up         -> Tile 17 (Arrow Up)
       1, // 1: Up-Right   -> Tile 17 (Arrow Up)
       3, // 2: Right      -> Tile 19 (Arrow Right)
       0, // 3: Down-Right -> Tile 16 (Arrow Down)
       0, // 4: Down       -> Tile 16 (Arrow Down)
       2, // 5: Down-Left  -> Tile 18 (Arrow Left)
       2, // 6: Left       -> Tile 18 (Arrow Left)
       1  // 7: Up-Left    -> Tile 17 (Arrow Up)
   };
   ```
   And in `hal_draw_tile`/`hal_set_sprite`:
   ```c
   if (tile_id >= TILE_ARROW && tile_id <= TILE_ARROW + 7) {
       uint8_t dir = (tile_id - TILE_ARROW) & 7;
       tile_id = TILE_ARROW + arrow_dir_to_tile[dir];
   }
   ```

---

## Verification Script Design (`verify_graphics.py`)

We designed and successfully verified a Python-based script `verify_graphics.py` to automate this audit. The script executes the following steps:
1. **File Parsing**: Reads `dandy-gb/src/tiles.c` and extracts the 512 bytes representing the thirty-two 2bpp tiles.
2. **2bpp Decoding**: Unpacks each pair of bytes in the planar format to construct the 8x8 index grid.
3. **Reference Image Loading**: Decodes the Base64 sprite sheet from `strike.js`, saving the reference PNG (256x32), and cropping it into thirty-two 16x16 reference tiles.
4. **Rescaling & Alignment**:
   - Resizes each 16x16 reference tile 8x to 128x128.
   - Converts the decoded GBDK tile to a color-mapped image, resizing it 8x to 64x64.
   - Pastes both tiles side-by-side in a 272x4096 audit sheet (`graphics_audit.png`).
5. **Output**: Saves the comparison sheet, allowing instant visual validation of the compiled GameBoy assets.
