# Milestone 3 Analysis: Comparative Selection & Packing
**Project**: GameBoy Graphics Conversion Pipeline  
**Role**: Exploration Agent (`explorer_graphics_m3_3`)  
**Status**: Read-Only Design and Verification Planning Complete  

---

## Executive Summary
This report presents the architectural design and planning for **Milestone 3: Comparative Selection & Packing** of the Dandy Dungeon GameBoy Graphics Conversion Pipeline. 

We have discovered that a complete set of **32 hand-drawn native 8x8 pixel-art glyphs** already exists in the repository inside `dandy-gb/tools/compile_bmp_sprites.py`. This eliminates the need to author new sprite sheets or dictionaries from scratch. 

We propose a clean, decoupled architecture:
1. Refactor the hand-drawn glyphs into a dedicated package module `dandy-gb/downscale/overrides.py` as standard NumPy arrays.
2. Implement a selection registry and coordinator in `dandy-gb/downscale/selector.py` which allows per-tile specification of either `"mathematical"` (FHDA) or `"manual"` (hand-drawn override) sources.
3. Integrate this selector into the existing sprite compiler CLI `tools/downscale_sprites.py` to seamlessly pack the optimal tiles into GameBoy 2bpp format, outputting to the standard contract files `src/tiles.c` and `src/tiles.h`.
4. Run a comprehensive suite of unit and integration tests to verify the pipeline's absolute mathematical and visual integrity.

---

## 1. Observations (Codebase Investigation)

### A. GBDK 2bpp Packing Compiler
In `dandy-gb/downscale/compiler.py` (lines 4-112), we observed:
- A class `GameBoyCompiler` that provides a static method `pack_tile(tile_8x8: np.ndarray) -> list[int]`.
- It takes an 8x8 NumPy array with values in `0..3` and packs it row-by-row into **16 bytes of GameBoy 2bpp planar format** (low byte and high byte interleaved per row).
- It provides a class method `compile(tiles_8x8: list[np.ndarray], output_c_path: str, output_h_path: str)` which verifies that exactly 32 tiles are provided, packs them, and writes them to the target C and H files using a standard C99 character array declaration:
  ```c
  extern const unsigned char dandy_tiles[DANDY_NUM_TILES * DANDY_TILE_SIZE];
  ```

### B. Mathematical Downscaler Engine
In `dandy-gb/downscale/engine.py` (lines 6-49), we observed:
- A `DownscaleEngine` registry that manages strategies. It registers `nearest`, `bilinear`, `bicubic`, `box`, and `font-hinting` (`FontHintingDownscaler` in `downscale/algorithms/custom.py`).
- It downscales a single 16x16 tile to an 8x8 NumPy array via `downscale_tile(name, tile_16x16, **kwargs)`.

### C. Downscale CLI Entrypoint
In `dandy-gb/tools/downscale_sprites.py` (lines 25-125), we observed:
- A CLI tool that loads a 256x32 sprite sheet from disk via `SpriteSheetManager.load_and_slice` (which slices it into 32 tiles of 16x16 RGBA pixels).
- It runs the specified downscaling algorithm (defaulting to `font-hinting`) on all 32 tiles.
- It compiles the 32 resulting 8x8 tiles directly into `src/tiles.c` and `src/tiles.h` using `GameBoyCompiler.compile`.

### D. Pre-Existing Hand-Drawn Sprites (Critical Finding)
Upon searching the repository, we located a pre-existing file:
**Path**: `dandy-gb/tools/compile_bmp_sprites.py` (lines 21-298)
- It contains a dictionary `GLYPHS` with 32 hand-drawn 8x8 tiles represented as lists of 8 strings of 8 characters:
  ```python
  GLYPHS = {
      0: [
          "00000000",
          ...
      ],
      7: [ # TILE_MONEY ($)
          "00002000",
          "00222200",
          "00202000",
          "00022200",
          "00002020",
          "00222200",
          "00002000",
          "00002000"
      ],
      ...
  }
  ```
- These glyphs use character codes `'0'` (Transparent/Black), `'1'` (Dark Gray or White depending on palette), `'2'` (Light Gray or Dark Gray), and `'3'` (White or Black outline) to represent the 4-color index system.
- This is a complete, beautifully hand-crafted set of 32 tiles that are optimized for the GameBoy's low-resolution screen. They represent the perfect source of manual overrides!

---

## 2. Logic Chain & Architectural Proposal

### A. Logic Chain
1. **Observation A & B**: The existing mathematical downscaler (`FHDA`) and the GameBoy packing compiler (`GameBoyCompiler`) both operate on `(8, 8)` NumPy arrays containing integer values `0..3`.
2. **Observation D**: The pre-existing hand-drawn glyphs in `compile_bmp_sprites.py` are represented as lists of 8 strings, where each character represents a color index `0..3`.
3. **Inference 1**: We can easily convert these string-based glyphs into the identical `(8, 8)` NumPy array format using a simple character-to-integer conversion. This makes the hand-drawn overrides completely type-compatible with the output of the mathematical downscaler.
4. **Inference 2**: By introducing a selection registry (mapping each tile index `0..31` to either `"mathematical"` or `"manual"`), we can route each tile through either the downscaler or the overrides database, returning a unified list of 32 `(8, 8)` NumPy arrays.
5. **Inference 3**: This unified list of 32 arrays can be passed directly to `GameBoyCompiler.compile` without modifying the packing compiler or C code generator. This ensures complete backward-compatibility and zero risk of breaking the build.

### B. Architectural Proposal

We propose adding two new modules to the `downscale` package:

#### 1. `dandy-gb/downscale/overrides.py` (New Module)
This module will house the refactored hand-drawn glyphs, keeping the `downscale` package self-contained and avoiding dependencies on the `tools/` folder.

```python
import numpy as np

# Refactored from tools/compile_bmp_sprites.py
HAND_DRAWN_GLYPHS = {
    0: [
        "00000000",
        "00000000",
        "00000000",
        "00000000",
        "00000000",
        "00000000",
        "00000000",
        "00000000"
    ],
    # ... Include all 32 glyphs verbatim from compile_bmp_sprites.py ...
}

def get_override_tile(tile_idx: int) -> np.ndarray:
    """
    Retrieves the hand-drawn override for a given tile index as an 8x8 numpy array.
    """
    if tile_idx not in HAND_DRAWN_GLYPHS:
        raise KeyError(f"No override defined for tile index {tile_idx}")
    
    glyph = HAND_DRAWN_GLYPHS[tile_idx]
    # Convert 8 strings of 8 characters into a 8x8 numpy array of integers
    matrix = [[int(char) for char in row] for row in glyph]
    return np.array(matrix, dtype=np.uint8)
```

#### 2. `dandy-gb/downscale/selector.py` (New Module)
This module implements the selection configuration and coordination logic.

```python
import numpy as np
from .overrides import get_override_tile

# The Selection Registry
# Specifies on a per-tile basis (0..31) whether to use:
# - "mathematical": The custom Font-Hinted Downscaling Algorithm (FHDA) output
# - "manual": The hand-drawn override from overrides.py
TILE_SELECTION = {
    # Background Tiles
    0: "mathematical",  # Space (floor) - downscaled floor cracks are nice
    1: "mathematical",  # Wall - FHDA preserves brick patterns well
    2: "mathematical",  # Door
    3: "manual",        # Stairs Up - manual override preserves high-contrast readability
    4: "manual",        # Stairs Down - manual override preserves recessing pit depth
    5: "manual",        # Key - manual override is much cleaner than downscaled version
    6: "mathematical",  # Food
    7: "manual",        # Money/Gold - manual '$' sign is perfectly symmetric and crisp
    8: "mathematical",  # Bomb
    
    # Monsters (Sprites)
    9: "mathematical",  # Monster 1
    10: "mathematical", # Monster 2
    11: "mathematical", # Monster 3
    
    # Items & Generators
    12: "manual",       # Heart - manual flask is aesthetically superior
    13: "mathematical", # Generator 1
    14: "mathematical", # Generator 2
    15: "mathematical", # Generator 3
    
    # Arrows (Sprites)
    16: "manual",       # Arrow Down - manual arrows are perfectly aligned and sharp
    17: "manual",       # Arrow Up
    18: "manual",       # Arrow Left
    19: "manual",       # Arrow Right
    
    # Padding
    20: "mathematical",
    21: "mathematical",
    22: "mathematical",
    23: "mathematical",
    
    # Players (Sprites)
    24: "manual",       # Player Down - manual knight visor and outlines are superior
    25: "manual",       # Player Up
    26: "manual",       # Player Left
    27: "manual",       # Player Right
    
    # Padding
    28: "mathematical",
    29: "mathematical",
    30: "mathematical",
    31: "mathematical"
}

class TileSelector:
    """
    Coordinates the selection between mathematical downscaling and manual overrides.
    """
    def __init__(self, selection_map: dict[int, str] = None, force_mathematical: bool = False):
        self.selection_map = selection_map or TILE_SELECTION
        self.force_mathematical = force_mathematical
        self._validate_config()

    def _validate_config(self):
        # Ensure all 32 tiles are configured
        for i in range(32):
            if i not in self.selection_map:
                raise ValueError(f"Tile index {i} is missing from the selection configuration.")
            source = self.selection_map[i]
            if source not in ("mathematical", "manual"):
                raise ValueError(f"Invalid source '{source}' for tile {i}. Must be 'mathematical' or 'manual'.")

    def select_tile(self, tile_idx: int, downscaled_tile: np.ndarray) -> np.ndarray:
        """
        Returns either the downscaled tile or the manual override based on the configuration.
        """
        if self.force_mathematical:
            return downscaled_tile
            
        source = self.selection_map[tile_idx]
        if source == "manual":
            return get_override_tile(tile_idx)
        else:
            return downscaled_tile
```

---

## 3. Integration Plan

### A. Modifying `dandy-gb/tools/downscale_sprites.py`
We will integrate the `TileSelector` into the main compilation loop of the CLI tool. We will also add a `--no-overrides` command-line flag to bypass manual overrides (useful for audits and testing).

#### Proposed Changes in `tools/downscale_sprites.py`:
1. **Imports**:
   ```python
   from downscale.selector import TileSelector
   ```
2. **Arguments**:
   Add a new command-line argument:
   ```python
   parser.add_argument('--no-overrides', action='store_true',
                       help="Bypass manual overrides and force 100% mathematical downscaling.")
   ```
3. **Execution Loop**:
   Replace the processing loop in `main()` with:
   ```python
   # Initialize Selector
   selector = TileSelector(force_mathematical=args.no_overrides)
   
   # Process each tile
   tiles_8x8 = []
   for idx, tile in enumerate(tiles_16x16):
       # 1. Compute the mathematical downscaled tile
       ds_tile = engine.downscale_tile(
           name=args.algorithm,
           tile_16x16=tile,
           outline_thickness=args.outline_thickness,
           contrast_threshold=args.contrast_threshold,
           symmetry_weight=args.symmetry_weight,
           feature_weight=args.feature_weight,
           grid_snap=args.grid_snap
       )
       
       # 2. Select the optimal tile (either mathematical or manual override)
       selected_tile = selector.select_tile(idx, ds_tile)
       tiles_8x8.append(selected_tile)
   ```

### B. Makefile Integration
Since the `sprites` target in the `Makefile` already calls `tools/downscale_sprites.py` with all the necessary parameters, **no changes are required to the Makefile's rule signature**. 

Running:
```bash
make sprites
```
will automatically run the new selection logic, packing the final selected tiles into `src/tiles.c` and `src/tiles.h` and generating the preview sheet `teamwork_graphics/downscale_preview.png`.

---

## 4. Testing & Verification Plan

We will create a new test suite file: `dandy-gb/tests/test_graphics_selector.py` containing comprehensive unit and integration tests.

### A. Test Cases in `test_graphics_selector.py`
1. **`test_overrides_validity`**:
   - Loops through all 32 tiles in `overrides.py`.
   - Asserts that `get_override_tile(i)` returns a NumPy array of shape `(8, 8)`.
   - Asserts that every pixel value in the array is an integer in the range `0..3`.
2. **`test_selector_routing`**:
   - Instantiates a `TileSelector` with a mock configuration (e.g. tile 3 is `"manual"`, tile 4 is `"mathematical"`).
   - Generates a mock downscaled tile (e.g., all 1s).
   - Asserts that calling `select_tile(3, mock_downscaled)` returns the actual hand-drawn override for tile 3.
   - Asserts that calling `select_tile(4, mock_downscaled)` returns the mock downscaled tile (all 1s).
3. **`test_force_mathematical_flag`**:
   - Instantiates a `TileSelector` with `force_mathematical=True`.
   - Asserts that for all 32 tiles, calling `select_tile(i, mock_downscaled)` returns the mock downscaled tile, ignoring overrides.
4. **`test_packing_integration`**:
   - Runs the selector on a dummy set of tiles.
   - Packs the selected tiles using `GameBoyCompiler.pack_tile` and asserts that no `ValueError` is raised, certifying that the hand-drawn tiles are 100% compatible with the 2bpp packer.

### B. Pipeline and E2E Verification
Because the output files are written directly to `src/tiles.c` and `src/tiles.h` following the exact same structure as before:
1. **`verify_graphics.py` Compatibility**: The programmatic verification tool `tools/verify_graphics.py` will remain **100% compatible without modification**. Running `python3 tools/verify_graphics.py` will parse the new `src/tiles.c` and stitch the side-by-side comparisons into `graphics_audit.png`, displaying the manually-selected tiles next to the original 16x16 sprites.
2. **E2E Emulator Tests**: Running `make test_emu` will verify that the ROM compiles cleanly and passes all PyBoy E2E emulator test assertions.

---

## 5. Caveats & Assumptions
- **Pre-existing Glyphs Coverage**: We assume the 32 glyphs defined in `compile_bmp_sprites.py` are the correct hand-drawn assets. Upon inspection, they correspond perfectly to the 32 game tiles (Space, Wall, Door, Stairs, Items, Monsters, Arrows, Players, and Padding).
- **Index Alignment**: We assume the indexes in `compile_bmp_sprites.py` align perfectly with the target Game Boy tile indexes. This is confirmed by checking `compile_bmp_sprites.py`'s comments (e.g. Tile 7 is Money/Gold, which matches index 7 in `verify_graphics.py`'s `GB_TO_JS_MAPPING`).
- **No GUI / Visual editor**: We do not propose implementing a visual sprite editor in this milestone; editing overrides remains code-based via the `overrides.py` dictionary, which is highly robust, easily version-controlled, and matches the project's fast timeline.

---

## 6. Conclusion
The comparative selection mechanism is highly feasible and straightforward to implement. By leveraging the pre-existing hand-drawn glyphs inside `compile_bmp_sprites.py`, we can easily achieve maximum visual fidelity for complex sprites (like text characters, player tiles, and arrows) while retaining the mathematical FHDA outputs for textures (like floors and walls). The proposed design is fully decoupled, safe, and backwards-compatible.

---

## 7. Verification Method
The next worker agent can independently verify this design by executing the following steps:
1. **Code Inspection**:
   - Confirm that `dandy-gb/tools/compile_bmp_sprites.py` contains the `GLYPHS` dictionary with 32 hand-drawn 8x8 glyphs.
   - Confirm that `dandy-gb/downscale/compiler.py` and `dandy-gb/tools/downscale_sprites.py` compile tiles to `src/tiles.c`.
2. **Run Tests**:
   - Run the existing test suite using `make test` and ensure all tests pass before making changes.
   - Verify that running `python3 tools/verify_graphics.py` runs successfully and outputs a clean visual audit sheet.
