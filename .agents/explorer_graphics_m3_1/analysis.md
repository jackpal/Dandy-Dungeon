# Milestone 3: Comparative Selection & Packing
## Architectural Design & Planning Report

### 1. Executive Summary
This report details the architectural design and integration plan for **Milestone 3: Comparative Selection & Packing** in the Dandy Dungeon GameBoy Graphics Conversion Pipeline.
The objective of this milestone is to introduce a robust mechanism that merges high-fidelity, manually redrawn 8x8 tiles with the mathematically downscaled (FHDA) tiles. This comparative selection allows the pipeline to use manually optimized overrides for complex tiles (such as text, player sprites, items, and directional arrows) while utilizing mathematical downscaling for standard background tiles. The selected tiles are then packed into GameBoy 2bpp planar format and compiled into the ROM.

---

### 2. Findings & Codebase Analysis

We analyzed the existing graphics pipeline components:
1.  **`dandy-gb/downscale/compiler.py`**: Contains `GameBoyCompiler` which packs 8x8 numpy arrays (values 0..3) into 16 bytes of GameBoy 2bpp planar format. It writes the compiled 512 bytes for all 32 tiles into `src/tiles.c` and `src/tiles.h`.
2.  **`dandy-gb/downscale/engine.py`**: Manages downscaling strategies (nearest, bilinear, bicubic, box, and the custom Font-Hinting Downscaling Algorithm).
3.  **`dandy-gb/downscale/manager.py`**: Slices the original 256x32 sprite sheet (`strike_original.png`) into 32 independent 16x16 tiles, and handles saving preview grids.
4.  **`dandy-gb/tools/downscale_sprites.py`**: The CLI entry point that orchestrates loading the original spritesheet, downscaling each tile mathematically, and compiling the output.
5.  **`dandy-gb/tools/verify_graphics.py`**: Parses `src/tiles.c`, decodes the 2bpp tiles, maps them back using the layout mapping dictionary `GB_TO_JS_MAPPING`, and generates `graphics_audit.png` and `graphics_audit_dark.png` comparing GBDK tiles side-by-side with original sprites.

#### Key Discovery: Pre-existing Redrawn Sprites
An exhaustive search of the repository confirms that **no pre-existing hand-drawn or redrawn 8x8 tiles exist**. Therefore, we must define the storage and representation format for these assets.

#### The Visual Asset Mismatch & Override Candidates
Based on the `GB_TO_JS_MAPPING` in `verify_graphics.py`, the 32 tiles correspond to specific in-game objects. Simple geometric textures like Space (0), Wall (1), and Door (2) scale down beautifully using the mathematical compiler. However, the following tiles suffer from severe readability loss under mathematical downscaling and are prime candidates for manual redrawing:
-   **Player Sprites (24..27)**: Player facing Down, Up, Left, Right. Complex features like eyes, mouth, and limbs become muddy blobs.
-   **Directional Arrows (16..19)**: Arrow Down, Up, Left, Right. Precise 1-pixel outlines are required for game clarity.
-   **Items & Pickups (5..8, 12)**: Key, Food, Money, Bomb, Heart. High-contrast, iconic representations are vital.
-   **Monsters (9..11)**: Ghost, Snake, Golem. Manual styling is needed to retain character at 8x8 resolution.
-   **Generators (13..15)**: Spawners with complex glyph symbols.

---

### 3. Architectural Proposal

To support manual overrides with a robust selection and packing pipeline, we propose the following components:

```
+-----------------------------------+     +-----------------------------------+
|      Original Sprite Sheet        |     |      Hand-Redrawn Sprite Sheet     |
|    strike_original.png (256x32)   |     |    redrawn_sprites.png (128x16)   |
+-----------------+-----------------+     +-----------------+-----------------+
                  |                                         |
                  v (SpriteSheetManager)                    v (SpriteSheetManager)
        [32x 16x16 RGBA Tiles]                    [32x 8x8 Grayscale Tiles]
                  |                                         |
                  v (DownscaleEngine: FHDA)                 v (Grayscale-to-2bpp Map)
        [32x 8x8 Math-Downscaled]                  [32x 8x8 Hand-Redrawn 2bpp]
                  |                                         |
                  +--------------------+--------------------+
                                       |
                                       v
                     +-----------------+-----------------+
                     |           TileSelector            | <--- TILE_SELECTION Registry
                     |  (Selects Math or Redrawn Tile)   |      (downscale/config.py)
                     +-----------------+-----------------+
                                       |
                                       v [32x 8x8 Final Selected Tiles]
                             (GameBoyCompiler)
                                       |
                                       +--------------------+
                                       |                    |
                                       v                    v
                                 [src/tiles.c]        [src/tiles.h]
```

#### A. Storage & Representation of Redrawn Tiles
We propose saving manually redrawn tiles in a single, standard image file:
-   **File Path**: `dandy-gb/teamwork_graphics/redrawn_sprites.png`
-   **Dimensions**: 128x16 pixels (32 tiles of 8x8, arranged in 2 rows of 16).
-   **Color Depth**: 8-bit Grayscale or 32-bit RGBA.
-   **Pixel-to-Color Mapping**:
    -   **Color 0 (White/Transparent)**: RGB (255,255,255) / Alpha = 0.
    -   **Color 1 (Light Gray)**: RGB (170,170,170) / Alpha > 0.
    -   **Color 2 (Dark Gray)**: RGB (85,85,85) / Alpha > 0.
    -   **Color 3 (Black)**: RGB (0,0,0) / Alpha > 0.

#### B. Selection Configuration: `dandy-gb/downscale/config.py`
We will introduce a python configuration file containing the selection registry:
```python
# dandy-gb/downscale/config.py

# Per-tile comparative selection registry:
# 'math'    -> Use mathematical downscaler output (FHDA)
# 'redrawn' -> Use manual override from redrawn_sprites.png
TILE_SELECTION = {
    0: 'math',     # Space
    1: 'math',     # Wall
    2: 'math',     # Door
    3: 'redrawn',  # Stairs Up
    4: 'redrawn',  # Stairs Down
    5: 'redrawn',  # Key
    6: 'redrawn',  # Food
    7: 'redrawn',  # Money/Gold
    8: 'redrawn',  # Bomb
    9: 'redrawn',  # Monster 1
    10: 'redrawn', # Monster 2
    11: 'redrawn', # Monster 3 (Golem)
    12: 'redrawn', # Heart
    13: 'redrawn', # Generator 1
    14: 'redrawn', # Generator 2
    15: 'redrawn', # Generator 3
    16: 'redrawn', # Arrow Down
    17: 'redrawn', # Arrow Up
    18: 'redrawn', # Arrow Left
    19: 'redrawn', # Arrow Right
    20: 'math',    # Unused Padding
    21: 'math',    # Unused Padding
    22: 'math',    # Unused Padding
    23: 'math',    # Unused Padding
    24: 'redrawn', # Player Down
    25: 'redrawn', # Player Up
    26: 'redrawn', # Player Left
    27: 'redrawn', # Player Right
    28: 'math',    # Unused Padding
    29: 'math',    # Unused Padding
    30: 'math',    # Unused Padding
    31: 'math'     # Unused Padding
}
```

#### C. Comparative Selection Logic: `dandy-gb/downscale/selector.py`
We will implement a `TileSelector` class responsible for merging the outputs:
```python
import logging
import numpy as np
from .config import TILE_SELECTION

class TileSelector:
    """
    Selects the highest-fidelity option per tile (mathematical vs manual override).
    """
    def __init__(self, selection_registry=None):
        self.registry = selection_registry or TILE_SELECTION

    def merge_tiles(self, math_tiles: list[np.ndarray], redrawn_tiles: list[np.ndarray]) -> list[np.ndarray]:
        """
        Merges mathematically downscaled tiles and manual redrawn overrides.
        Supports graceful fallback if redrawn assets are missing or invalid.
        """
        if len(math_tiles) != 32:
            raise ValueError(f"Expected 32 mathematical tiles, got {len(math_tiles)}")
            
        final_tiles = []
        for idx in range(32):
            mode = self.registry.get(idx, 'math')
            
            if mode == 'redrawn':
                # Graceful fallback: check if redrawn tile is available and valid
                if redrawn_tiles and idx < len(redrawn_tiles) and redrawn_tiles[idx] is not None:
                    final_tiles.append(redrawn_tiles[idx])
                else:
                    logging.warning(f"Tile {idx} configured as 'redrawn' but no redrawn tile was found. Falling back to 'math'.")
                    final_tiles.append(math_tiles[idx])
            else:
                final_tiles.append(math_tiles[idx])
                
        return final_tiles
```

#### D. Decoding Redrawn Sprites: `dandy-gb/downscale/manager.py`
We will add a new method to `SpriteSheetManager` to parse and decode the redrawn sheet:
```python
    @staticmethod
    def load_and_slice_redrawn(image_path: str) -> list[np.ndarray]:
        """
        Loads the 128x16 redrawn sheet and decodes pixels into 8x8 numpy arrays (values 0..3).
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Redrawn sprite sheet not found: {image_path}")
            
        try:
            with Image.open(image_path) as img:
                width, height = img.size
                if width != 128 or height != 16:
                    raise ValueError(f"Redrawn sprite sheet must be exactly 128x16, got {width}x{height}")
                    
                with img.convert('RGBA') as img_rgba:
                    img_arr = np.array(img_rgba)
                    tiles_8x8 = []
                    
                    # 2 rows, 16 columns of 8x8 tiles
                    for r in range(2):
                        for c in range(16):
                            tile_rgba = img_arr[r*8:(r+1)*8, c*8:(c+1)*8]
                            tile_indexed = np.zeros((8, 8), dtype=np.uint8)
                            
                            for y in range(8):
                                for x in range(8):
                                    pixel = tile_rgba[y, x]
                                    r_val, g_val, b_val, a_val = pixel
                                    
                                    # Color 0 mapping: Transparent (Alpha < 128) or White
                                    if a_val < 128 or (r_val > 220 and g_val > 220 and b_val > 220):
                                        color_idx = 0
                                    # Color 3 mapping: Black (Darkness threshold)
                                    elif r_val < 45 and g_val < 45 and b_val < 45:
                                        color_idx = 3
                                    # Color 2 mapping: Dark Gray (closer to 85)
                                    elif r_val < 128 and g_val < 128 and b_val < 128:
                                        color_idx = 2
                                    # Color 1 mapping: Light Gray (closer to 170)
                                    else:
                                        color_idx = 1
                                        
                                    tile_indexed[y, x] = color_idx
                            tiles_8x8.append(tile_indexed)
                            
                    return tiles_8x8
        except Exception as e:
            if isinstance(e, (ValueError, FileNotFoundError)):
                raise
            raise ValueError(f"Failed to parse redrawn image file: {e}")
```

---

### 4. Integration Plan

#### A. Modifying `dandy-gb/tools/downscale_sprites.py`
The CLI tool will be updated to orchestrate the selection process:
1.  **Add Arguments**:
    -   `--redrawn`: Path to the redrawn spritesheet (default: `teamwork_graphics/redrawn_sprites.png`).
    -   `--selection-config`: Path to a custom JSON selection registry (optional).
2.  **Orchestration Logic**:
    ```python
    # Load and downscale original mathematically (16x16 to 8x8)
    tiles_16x16 = SpriteSheetManager.load_and_slice(args.input)
    math_tiles_8x8 = []
    for tile in tiles_16x16:
        math_tiles_8x8.append(engine.downscale_tile(args.algorithm, tile, ...))

    # Load hand-drawn overrides if the file exists
    redrawn_tiles_8x8 = None
    if os.path.exists(args.redrawn):
        try:
            redrawn_tiles_8x8 = SpriteSheetManager.load_and_slice_redrawn(args.redrawn)
            print(f"Loaded manual overrides from {args.redrawn}")
        except Exception as e:
            print(f"Warning: Failed to load redrawn sheet, falling back to math. Error: {e}", file=sys.stderr)
    else:
        print(f"Note: Manual overrides sheet not found at {args.redrawn}. Using mathematical tiles.")

    # Merge tiles using TileSelector
    selector = TileSelector()
    final_tiles_8x8 = selector.merge_tiles(math_tiles_8x8, redrawn_tiles_8x8)

    # Compile final selection to C/H source files
    GameBoyCompiler.compile(final_tiles_8x8, args.output_c, args.output_h)

    # Preview and sheets will automatically reflect the final selection!
    if args.output_png:
        SpriteSheetManager.save_sprite_sheet(final_tiles_8x8, args.output_png)
    if args.output_preview:
        SpriteSheetManager.save_preview_sheet(tiles_16x16, final_tiles_8x8, args.output_preview)
    ```

#### B. Modifying `dandy-gb/Makefile`
Update the `sprites` target to support overrides. We will keep it robust: it will attempt to use the default `redrawn_sprites.png` but will compile cleanly even if the file is absent.
```makefile
sprites:
	@echo "Compiling downscaled sprite assets with manual overrides..."
	.venv/bin/python $(TOOLS_DIR)/downscale_sprites.py \
		--input teamwork_graphics/strike_original.png \
		--redrawn teamwork_graphics/redrawn_sprites.png \
		--output-c src/tiles.c \
		--output-h src/tiles.h \
		--output-preview teamwork_graphics/downscale_preview.png
```

---

### 5. Testing & Verification Plan

We outline a rigorous testing plan to ensure zero regressions and perfect visual outcomes.

#### A. New Unit Tests (`dandy-gb/tests/test_selection.py`)
A comprehensive unit test suite will be implemented to verify:
1.  **Redrawn Slicing Correctness**:
    -   `test_load_redrawn_success`: Assert that a dummy 128x16 PNG with solid color strips decodes to correct numpy index values (0..3).
    -   `test_load_redrawn_invalid_dimensions`: Pass a 128x32 or 64x16 PNG and assert that a `ValueError` is raised.
    -   `test_load_redrawn_missing_file`: Assert that `FileNotFoundError` is raised.
2.  **Selector Merging Logic**:
    -   `test_selector_all_math`: Configure registry to all `'math'` and assert the output is identical to the mathematical downscaled list.
    -   `test_selector_all_redrawn`: Configure registry to all `'redrawn'` and assert the output is identical to the redrawn list.
    -   `test_selector_mixed`: Configure a mixed registry and assert that index `i` matches redrawn/math accordingly.
    -   `test_selector_missing_redrawn_fallback`: Pass `None` as the redrawn list but set registry to `'redrawn'`. Verify that the selector logs a warning and gracefully falls back to mathematical tiles.
    -   `test_selector_invalid_registry_key`: Verify that missing keys default to `'math'`.

#### B. Integration and ROM Verification
To verify the pipeline end-to-end:
1.  **Local Compilation**:
    Run `make clean && make` to ensure:
    -   `downscale_sprites.py` executes successfully.
    -   `src/tiles.c` and `src/tiles.h` are successfully generated and contain valid 2bpp bytes.
    -   The GBDK compiler (`lcc`) links the object files and builds `bin/dandy.gb` with 0 warnings/errors.
2.  **PyBoy Emulator Tests**:
    Run `make test_emu` to run automated emulator integration checks. This ensures that the newly compiled tiles load into memory and render without causing emulator crashes or display corruptions.
3.  **Visual Audit Sheets**:
    Run `python3 tools/verify_graphics.py` and `python3 tools/verify_graphics.py --dark-floor` to generate the side-by-side audit sheets:
    -   `teamwork_graphics/graphics_audit.png`
    -   `teamwork_graphics/graphics_audit_dark.png`
    These sheets will display the original 16x16 tiles alongside our final merged 8x8 tiles (upscaled 8x using nearest-neighbor), allowing immediate verification of visual quality, transparency, and contrast.
