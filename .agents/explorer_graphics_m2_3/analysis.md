# Software Architecture, Validation Plan, and Test Design for the Mathematical Downscaling Tool

## Executive Summary
This document defines the software architecture, command-line interface (CLI) specification, visual and programmatic validation plan, and robust test suite for the Game Boy pixel-art downscaling tool (`downscale_sprites.py`). By employing a highly decoupled **Strategy Pattern** for pluggable downscalers and integrating an independent programmatic quality auditor into the existing `verify_graphics.py` pipeline, we establish a bulletproof, mathematically validated graphics compilation workflow.

---

## 1. Software Architecture of the Downscaling Compiler Tool

The downscaling compiler tool is designed as an extensible, modular command-line utility. Rather than hardcoding a single downscaling method, the architecture isolates the **downscaling algorithm** from the **file loading, palette reduction, and GBDK compilation** logic. This allows the system to easily swap, compare, and tune different mathematical downscaling strategies.

### 1.1 Class and Module Breakdown

The tool will be structured using the following decoupled modules and classes:

```
dandy-gb/tools/
├── downscale_sprites.py          # Entry point and CLI coordinator
└── downscale/                     # Core library package
    ├── __init__.py
    ├── engine.py                  # Downscaling Engine & Registry
    ├── manager.py                 # Sprite Sheet Loader & Slicer
    ├── compiler.py                # Game Boy 2bpp C Code Generator
    └── algorithms/                # Pluggable downscaling strategies
        ├── __init__.py
        ├── base.py                # Abstract Base Downscaler
        ├── standard.py            # Standard interpolation (Nearest, Bilinear, etc.)
        └── custom.py              # Custom Font-Hinting / Heuristic downscaler
```

#### A. `SpriteSheetManager` (in `manager.py`)
- **Responsibilities**:
  - Validates input file paths and image dimensions (e.g., verifying a 256x32 sheet containing 32 tiles of 16x16).
  - Supports loading either a single combined sprite sheet PNG or a directory containing individual 16x16 tile PNGs.
  - Slices the source image into discrete 16x16 pixel blocks.
  - Formats output images and arranges them into a consolidated downscaled sprite sheet (128x16 PNG for 32 tiles of 8x8).
- **Core Methods**:
  - `load_sheet(path: str) -> List[Image.Image]`
  - `load_individual_tiles(dir_path: str) -> List[Image.Image]`
  - `save_sheet(tiles: List[Image.Image], path: str)`

#### B. `DownscalingEngine` (in `engine.py`)
- **Responsibilities**:
  - Acts as a registry for all available downscaling algorithms.
  - Dispatches downscaling requests to the selected algorithm strategy.
  - Coordinates the execution of algorithm-specific parameters (e.g., outline thickness, contrast thresholds).
- **Core Methods**:
  - `register_algorithm(name: str, strategy: BaseDownscaler)`
  - `downscale(tiles: List[Image.Image], algorithm: str, params: dict) -> List[Image.Image]`

#### C. `BaseDownscaler` (in `algorithms/base.py`)
- **Responsibilities**:
  - Defines the interface contract that all downscaling strategies must implement.
  - Provides shared utility methods for pixel classification, color quantization, and palette alignment.
- **Core Methods**:
  - `downscale_tile(tile: Image.Image, params: dict) -> Image.Image` (Abstract)
  - `quantize_to_gb_palette(tile: Image.Image, is_sprite: bool) -> Image.Image` (Shared helper to map downscaled colors to the 4-color Game Boy palette: White, Light Gray, Dark Gray, Black, or Transparent).

#### D. `StandardInterpolationDownscaler` (in `algorithms/standard.py`)
- **Responsibilities**:
  - Implements standard mathematical downscaling methods using the Python Pillow library:
    - Nearest Neighbor
    - Bilinear
    - Bicubic
    - Lanczos
    - Box
  - Serves as a baseline to demonstrate interpolation failures (aliasing, outline degradation, and feature merging).

#### E. `FontHintingDownscaler` (in `algorithms/custom.py`)
- **Responsibilities**:
  - Implements the custom mathematical heuristic downscaling algorithm designed by **Explorer 2**.
  - Coordinates the following sub-pixel operations:
    - **Outline Preservation**: Identifies 1px black contours and snaps them to the new 8x8 boundaries.
    - **Symmetry Correction**: Enforces horizontal or vertical symmetry based on tile metadata.
    - **Feature Weighting**: Prioritizes high-contrast regions (like white eyes) to prevent them from being absorbed by dark outlines.
    - **Contrast Snapping**: Binarizes interpolation weights based on custom threshold parameters to ensure crisp pixel-art edges without anti-aliased blur.

#### F. `GameBoyCompiler` (in `compiler.py`)
- **Responsibilities**:
  - Converts the downscaled 8x8 tiles (in 4-color indexed palette format) into Game Boy 2bpp planar binary format (16 bytes per tile).
  - Formats the 512 bytes (32 tiles * 16 bytes) into a GBDK-compatible C source array (`tiles.c`) and C header file (`tiles.h`), duplicating the layout of `compile_bmp_sprites.py`.
- **Core Methods**:
  - `pack_tile_to_2bpp(tile: Image.Image) -> bytes`
  - `compile_to_c(tiles: List[Image.Image], output_c_path: str, output_h_path: str)`

---

### 1.2 Data Flow and Sequence

The data flow through the downscaling pipeline proceeds as follows:

```
[strike_original.png] (16x16 tiles)
         │
         ▼
 ┌───────────────┐
 │ SpriteSheet   │ ──► Slice into 32 discrete 16x16 PIL Images
 │ Manager       │
 └───────────────┘
         │
         ▼
 ┌───────────────┐
 │ Downscaling   │ ──► Select algorithm (e.g., --algorithm font-hinting)
 │ Engine        │     Pass parameters: outline-thickness, contrast-threshold, etc.
 └───────────────┘
         │
         ▼
 ┌───────────────┐
 │ Selected      │ ──► Run mathematical downscaling (16x16 -> 8x8)
 │ Downscaler    │     Apply symmetry, outline preservation, and feature weighting
 └───────────────┘
         │
         ▼
 ┌───────────────┐
 │ GameBoy       │ ──► Pack 8x8 tiles into 2bpp planar format
 │ Compiler      │     Write GBDK array to [src/tiles.c] / [src/tiles.h]
 └───────────────┘     Write consolidated downscaled [strike_downscaled.png]
```

---

## 2. CLI Interface Specification

The downscaling compiler tool provides a comprehensive command-line interface with rigorous input validation to ensure parameters remain within safe mathematical and architectural limits.

### 2.1 CLI Option Definitions

| Option | Alias | Type | Default | Constraints | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `--input` | `-i` | `str` | *Required* | Must be an existing file or directory | Path to `strike_original.png` (256x32 sheet) or a directory of 16x16 PNG tiles. |
| `--output-c` | `-c` | `str` | `src/tiles.c` | Directory must be writable | Output path for the GBDK C source file. |
| `--output-h` | | `str` | `src/tiles.h` | Directory must be writable | Output path for the GBDK C header file. |
| `--output-png`| `-o` | `str` | *Optional* | Directory must be writable | Output path for the downscaled 8x8 sprite sheet PNG. |
| `--output-preview`| `-p` | `str` | *Optional* | Directory must be writable | Output path to save the side-by-side validation sheet. |
| `--algorithm` | `-a` | `choice`| `font-hinting`| `nearest`, `bilinear`, `bicubic`, `box`, `font-hinting` | Mathematical downscaling algorithm to apply. |
| `--outline-thickness`| | `float`| `1.0` | `0.0 <= val <= 2.0` | Target outline thickness in downscaled pixels. |
| `--contrast-threshold`| | `float`| `0.5` | `0.0 <= val <= 1.0` | Brightness threshold separating foreground from background. |
| `--symmetry-weight`| | `float`| `0.8` | `0.0 <= val <= 1.0` | Importance score for maintaining perfect tile symmetry. |
| `--feature-weight`| | `float`| `0.7` | `0.0 <= val <= 1.0` | Priority boost for high-contrast features (e.g., eyes). |
| `--grid-snap` | | `bool` | `True` | `True` or `False` | Enable snapping of critical boundaries to the 8x8 grid. |

### 2.2 Example Command Invocations

#### A. Default Production Compilation (Font-Hinting Algorithm)
This command downscales the original sprite sheet using the custom font-hinting algorithm, compiles it directly to the Game Boy source files, and generates a visual preview sheet.
```bash
python3 tools/downscale_sprites.py \
  --input teamwork_graphics/strike_original.png \
  --output-c src/tiles.c \
  --output-h src/tiles.h \
  --output-preview teamwork_graphics/downscale_preview.png
```

#### B. Baseline Evaluation (Bicubic Interpolation)
For testing and visual comparison, this command uses standard bicubic downscaling and outputs only a downscaled PNG sheet.
```bash
python3 tools/downscale_sprites.py \
  --input teamwork_graphics/strike_original.png \
  --algorithm bicubic \
  --output-png teamwork_graphics/strike_bicubic.png
```

#### C. Hyperparameter Tuning
Compiling with customized thresholds to preserve thin details and enforce heavy grid-snapping.
```bash
python3 tools/downscale_sprites.py \
  --input teamwork_graphics/strike_original.png \
  --outline-thickness 0.8 \
  --contrast-threshold 0.4 \
  --feature-weight 0.9 \
  --grid-snap True
```

---

## 3. Visual and Programmatic Validation Plan

To guarantee that the downscaled Game Boy sprites maintain the aesthetic integrity, legibility, and physical constraints of the original 16x16 designs, we design a two-pronged validation plan: **Visual Inspection** and **Programmatic Quality Assertions**.

### 3.1 Visual Verification (Extending `verify_graphics.py`)

We propose extending the existing `verify_graphics.py` script to serve as the visual and diagnostic auditor for the downscaled tiles. The script will be enhanced with the following visualization options:

1. **Pixel-Grid Overlay**: Drawing light, semi-transparent grid lines on the upscaled 128x128 tiles (representing the 8x8 downscaled coordinates) to allow engineers to inspect sub-pixel alignments.
2. **Symmetry Axis Line**: Drawing a vertical/horizontal dashed line through the center of tiles that are designated as symmetric, highlighting any asymmetric defects.
3. **Difference Highlighting**: Pasting a red outline mask over the downscaled tile showing where pixels differ significantly in shape or aspect ratio from the original.
4. **Interactive CLI Controls**:
   - `--grid-lines`: Toggle pixel boundaries on the audit sheet.
   - `--show-symmetry`: Toggle symmetry lines for symmetric tiles.
   - `--diff-mask`: Highlight pixel deviations in red.

These extensions will be implemented within the `verify_graphics.py` layout rendering loop, keeping the visual auditor strictly independent of the compiler tool.

---

### 3.2 Programmatic Quality Assertions

We define a set of mathematical and logical rules that can be evaluated programmatically. These assertions will be integrated into `verify_graphics.py` under a new `--validate` flag, allowing automated CI pipelines to verify downscaled graphics without manual human inspection.

```
+-------------------------------------------------------------------------------+
|                       PROGRAMMATIC QUALITY ASSERTIONS                         |
+-------------------------------------------------------------------------------+
|  1. COLOR LIMITS:     Total Colors <= 4; Color 0 is Transparent (for Sprites).|
|  2. ASPECT RATIO:     abs(Downscaled_Aspect_Ratio - Original_Aspect_Ratio) < T|
|  3. SYMMETRY check:   H-Symmetry: P[x, y] == P[7-x, y]                        |
|                       V-Symmetry: P[x, y] == P[x, 7-y]                        |
|  4. OUTLINE CHAIN:    No diagonal or adjacent gaps in black boundary.        |
|  5. FEATURE GUARD:    Eye pixels (Color 1/2) never touch background directly  |
|                       without a separating black outline (Color 3).           |
+-------------------------------------------------------------------------------+
```

#### A. Color Count and Transparency Constraints
- **Mathematical Formula**:
  $$\text{UniqueColors}(Tile_{8\times8}) \le 4$$
- **Rule**: Every tile must contain 4 or fewer unique colors. For tiles classified as sprites (indices `9..11`, `16..19`, `24..27`), color index `0` must be fully transparent:
  $$\forall (x, y) \in Tile_{8\times8}, \quad P(x, y) \in \{\text{Color}_0, \text{Color}_1, \text{Color}_2, \text{Color}_3\}$$
  $$\text{If is\_sprite}(i) \implies P(x,y)_0 = (0, 0, 0, 0)$$

#### B. Aspect Ratio & Bounding Box Preservation
- **Mathematical Formula**:
  $$\text{BoundingBox}(Image) = (x_{min}, y_{min}, x_{max}, y_{max})$$
  $$AR_{orig} = \frac{x_{max\_orig} - x_{min\_orig} + 1}{y_{max\_orig} - y_{min\_orig} + 1}, \quad AR_{down} = \frac{x_{max\_down} - x_{min\_down} + 1}{y_{max\_down} - y_{min\_down} + 1}$$
  $$\left| AR_{orig} - AR_{down} \right| < \epsilon \quad (\text{where } \epsilon = 0.25)$$
- **Assertion**: Verifies that the shape of the active drawing area (excluding transparency/background) does not collapse horizontally or vertically during downscaling.

#### C. Symmetry Constraints
- **Horizontal Symmetry Assertion** (applied to symmetric tiles such as Player helmet, Dollar sign, Key head):
  $$\forall y \in [0, 7], \forall x \in [0, 3], \quad P(x, y) == P(7 - x, y)$$
- **Vertical Symmetry Assertion** (applied to arrows, stairs, etc.):
  $$\forall x \in [0, 7], \forall y \in [0, 3], \quad P(x, y) == P(x, 7 - y)$$
- **Rule**: If a tile is flagged as symmetric in the metadata, the downscaled tile must maintain mathematical symmetry. Any asymmetry raises a validation error.

#### D. Pixel Count Conservation (Outline Density)
- **Mathematical Formula**:
  $$\text{Ratio}_{orig} = \frac{\sum P_{orig\_outline}}{\sum P_{orig\_active}}, \quad \text{Ratio}_{down} = \frac{\sum P_{down\_outline}}{\sum P_{down\_active}}$$
  $$0.7 \times \text{Ratio}_{orig} \le \text{Ratio}_{down} \le 1.3 \times \text{Ratio}_{orig}$$
- **Assertion**: Assures that the outline does not swell to consume the entire sprite (over-density) or disappear completely (under-density).

#### E. Outline Continuity (Graph Connectivity)
- **Algorithm**:
  1. Extract all pixels mapped to the outline color (Color 3 for sprites).
  2. Treat these pixels as nodes in a graph where edges exist between 8-way adjacent pixels.
  3. Perform a Breadth-First Search (BFS) or Depth-First Search (DFS) to identify connected components.
  4. Compare the number of connected components in the downscaled tile to the original tile:
     $$\text{Components}(Down_{outline}) == \text{Components}(Orig_{outline})$$
- **Assertion**: Ensures that a continuous bounding line in the original sprite does not end up with gaps or broken segments in the downscaled sprite.

#### F. Contrast and Feature Separation
- **Rule**: High-contrast features (such as white eyes represented by Color 1 inside a sprite) must remain separated from the background (Color 0) by the outline (Color 3).
- **Assertion**:
  $$\forall (x, y) \in \text{FeaturePixels}, \quad \text{Neighbors}_{8\text{-way}}(x, y) \cap \text{BackgroundPixels} = \emptyset$$
  This asserts that small features do not leak into the transparent background, ensuring they remain cleanly enclosed by outlines.

---

## 4. Test Suite and Adversarial Test Cases

To verify the robustness, edge-case handling, and reliability of the downscaling script, we design a comprehensive test suite (`tests/test_downscale_sprites.py`).

### 4.1 Unit Test Cases

1. **Synthetic Shape Verification**:
   - Input: A perfectly drawn 16x16 hollow circle, a solid square, and a symmetrical cross.
   - Assert: The downscaler correctly outputs an 8x8 circle, square, and cross, preserving symmetry and connectivity.
2. **2bpp Packing Verification**:
   - Input: Hand-crafted 8x8 pixel arrays with known Game Boy color indices.
   - Assert: `pack_tile_to_2bpp` returns the exact expected 16 bytes, matching the Game Boy planar format.
3. **Strategy Dispatch Verification**:
   - Verify that selecting different algorithms (`nearest`, `box`, `font-hinting`) correctly routes the request to the corresponding strategy class.

### 4.2 Robustness and Adversarial Test Cases

We design specific adversarial test cases targeting extreme inputs, malformed CLI parameters, and environment bounds.

```
+---------------------------------------------------------------------------------+
|                            ADVERSARIAL TEST SUITE                               |
+---------------------------------------------------------------------------------+
|  1. CORRUPT FILES:     0-byte png, non-PNG text, wrong size (255x32, 16x16),    |
|                        non-standard color modes (CMYK, Grayscale).              |
|  2. CLI EDGE CASES:    Negative outline thickness, contrast threshold > 1.0,    |
|                        missing required inputs, invalid algorithm strings.      |
|  3. PARAMETER EXTREMES:Threshold = 0.0 (all black) vs 1.0 (all white),          |
|                        outline thickness = 0 (none) vs 4 (overflow).            |
|  4. ENV CONSTRAINTS:   Read-only directories, directory-file collision.         |
+---------------------------------------------------------------------------------+
```

#### A. File and Image Format Adversaries
- **Test Case A1: Missing Input File**
  - Input: `--input non_existent_file.png`
  - Expected: Terminate gracefully with exit code `1`, printing `Error: Input file not found`. No raw Python traceback.
- **Test Case A2: Corrupted/Empty PNG File**
  - Input: An empty 0-byte file named `corrupt.png`.
  - Expected: Terminate gracefully with exit code `1`, printing `Error: Invalid or corrupted image file`.
- **Test Case A3: Incorrect Image Dimensions**
  - Input: A valid PNG file with dimensions 255x32 or 16x16 (where 256x32 is expected).
  - Expected: Raise a `ValueError`, exit with `1`, printing `Error: Expected input dimensions 256x32, got WxH`.
- **Test Case A4: Non-Standard Color Modes**
  - Input: A 256x32 PNG saved in CMYK, grayscale, or 16-bit color.
  - Expected: The `SpriteSheetManager` must convert it to standard RGBA/RGB internally without crashing.

#### B. CLI Parameter Bounds and Type Violations
- **Test Case B1: Invalid Algorithm Option**
  - Input: `--algorithm deep-learning`
  - Expected: CLI parser catches the invalid choice, displays help, and exits with code `2`.
- **Test Case B2: Negative and Excessive Parameter Values**
  - Input: `--outline-thickness -1.5` or `--contrast-threshold 1.2` or `--symmetry-weight 5.0`
  - Expected: The parser must validate bounds and reject out-of-range inputs, exiting with code `2` or raising a detailed `ArgumentTypeError`.
- **Test Case B3: Conflicting Arguments**
  - Input: Specifying both `--output-c` and `--output-png` with the same path, or specifying invalid combinations.
  - Expected: Clean error handling preventing file collision.

#### C. Algorithmic and Mathematical Extremes
- **Test Case C1: Minimum and Maximum Contrast Thresholds**
  - Input: `--contrast-threshold 0.0` and `--contrast-threshold 1.0`
  - Expected: The script runs without mathematical errors (such as division by zero or NaN), generating solid-color or correctly thresholded outputs.
- **Test Case C2: Extreme Outline Thicknesses**
  - Input: `--outline-thickness 0.0` (disable outline) and `--outline-thickness 3.0` (excessive outline).
  - Expected: The custom algorithm handles the boundaries gracefully, clamping outputs or removing outlines cleanly without raising exceptions.

#### D. Operating System and File System Limits
- **Test Case D1: Read-Only Output Directory**
  - Input: `--output-c /sys/class/tiles.c` (or a directory with read-only permissions).
  - Expected: Terminate gracefully, printing `Error: Permission denied writing to path`.
- **Test Case D2: File-Directory Path Collisions**
  - Input: `--output-c tools/` (where `tools/` is an existing directory).
  - Expected: Catch the `IsADirectoryError`, exit gracefully with code `1`, printing a clear error message.

---

## 5. Implementation Blueprint

To guide the implementer agent, we provide a skeleton structure and class layout for the downscaling compiler tool.

### 5.1 `downscale_sprites.py` (CLI & Main Loop)
```python
#!/usr/bin/env python3
"""
downscale_sprites.py
CLI tool to mathematically downscale 16x16 sprites to 8x8 Game Boy tiles.
"""
import sys
import argparse
from downscale.manager import SpriteSheetManager
from downscale.engine import DownscalingEngine
from downscale.compiler import GameBoyCompiler
from downscale.algorithms.standard import StandardInterpolationDownscaler
from downscale.algorithms.custom import FontHintingDownscaler

def float_range(mini, maxi):
    """CLI type helper to enforce float ranges."""
    def check(arg):
        try:
            val = float(arg)
        except ValueError:
            raise argparse.ArgumentTypeError(f"Must be a float")
        if not (mini <= val <= maxi):
            raise argparse.ArgumentTypeError(f"Must be in range [{mini}, {maxi}]")
        return val
    return check

def main(argv=None):
    parser = argparse.ArgumentParser(description="Mathematical Game Boy Downscaling Compiler.")
    parser.add_argument("--input", "-i", required=True, help="Path to strike_original.png")
    parser.add_argument("--output-c", "-c", default="src/tiles.c", help="Output C source file")
    parser.add_argument("--output-h", default="src/tiles.h", help="Output C header file")
    parser.add_argument("--output-png", "-o", help="Optional downscaled sprite sheet PNG")
    parser.add_argument("--output-preview", "-p", help="Optional side-by-side audit PNG")
    parser.add_argument("--algorithm", "-a", default="font-hinting",
                        choices=["nearest", "bilinear", "bicubic", "box", "font-hinting"])
    
    # Mathematical Hyperparameters
    parser.add_argument("--outline-thickness", type=float_range(0.0, 2.0), default=1.0)
    parser.add_argument("--contrast-threshold", type=float_range(0.0, 1.0), default=0.5)
    parser.add_argument("--symmetry-weight", type=float_range(0.0, 1.0), default=0.8)
    parser.add_argument("--feature-weight", type=float_range(0.0, 1.0), default=0.7)
    parser.add_argument("--grid-snap", type=bool, default=True)

    args = parser.parse_args(argv)

    try:
        # 1. Load sprite sheet
        manager = SpriteSheetManager()
        tiles_16x16 = manager.load_sheet(args.input)

        # 2. Initialize engine and register strategies
        engine = DownscalingEngine()
        engine.register_algorithm("nearest", StandardInterpolationDownscaler("nearest"))
        engine.register_algorithm("bilinear", StandardInterpolationDownscaler("bilinear"))
        engine.register_algorithm("bicubic", StandardInterpolationDownscaler("bicubic"))
        engine.register_algorithm("box", StandardInterpolationDownscaler("box"))
        engine.register_algorithm("font-hinting", FontHintingDownscaler())

        # 3. Process tiles
        params = {
            "outline_thickness": args.outline_thickness,
            "contrast_threshold": args.contrast_threshold,
            "symmetry_weight": args.symmetry_weight,
            "feature_weight": args.feature_weight,
            "grid_snap": args.grid_snap
        }
        tiles_8x8 = engine.downscale(tiles_16x16, args.algorithm, params)

        # 4. Save PNG if requested
        if args.output_png:
            manager.save_sheet(tiles_8x8, args.output_png)

        # 5. Compile to GBDK C code
        compiler = GameBoyCompiler()
        compiler.compile_to_c(tiles_8x8, args.output_c, args.output_h)
        
        print("Downscaling and compilation completed successfully.")
        
    except FileNotFoundError as e:
        sys.stderr.write(f"Error: {e}\n")
        sys.exit(1)
    except ValueError as e:
        sys.stderr.write(f"Error: {e}\n")
        sys.exit(1)
    except PermissionError as e:
        sys.stderr.write(f"Error: Permission denied - {e}\n")
        sys.exit(1)
    except Exception as e:
        sys.stderr.write(f"Unexpected Error: {e}\n")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

### 5.2 `base.py` (Downscaler Strategy Contract)
```python
"""Abstract base downscaler class."""
from abc import ABC, abstractmethod
from PIL import Image

class BaseDownscaler(ABC):
    @abstractmethod
    def downscale_tile(self, tile: Image.Image, params: dict) -> Image.Image:
        """Downscale a single 16x16 image tile to an 8x8 image tile."""
        pass

    def quantize_to_gb_palette(self, tile: Image.Image, is_sprite: bool) -> Image.Image:
        """Common helper to map downscaled colors to Game Boy indexed colors."""
        # Custom color-reduction/mapping algorithm goes here
        # E.g. mapping to White, Light Gray, Dark Gray, Black, or Transparent
        pass
```

---

## 6. Synthesis and Integration

By adopting this modular and robust design:
- **Separation of Concerns**: The downscale script concentrates purely on generating the best downscaled tiles and compiling them. The verification script (`verify_graphics.py`) concentrates purely on auditing the compiled files against the original specifications.
- **Continuous Integration Ready**: Programmatic assertions allow us to run graphics quality validation automatically alongside standard unit tests, ensuring no bad tiles can ever be checked in.
- **Fail-Safe Robustness**: The extensive adversarial test cases ensure that the compiler tool remains stable under corrupt inputs, bad file systems, or malformed user parameters.
