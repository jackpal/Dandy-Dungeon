# Milestone 1 Graphics Verification Pipeline Analysis & Fix Strategy

**Author**: Explorer 2 (Milestone 1 Retry)  
**Date**: June 21, 2026  
**Status**: COMPLETE (Read-only design and strategy phase)

---

## 1. Executive Summary

This report provides a rigorous analysis of the graphics verification tool in the `dandy-gb` project. It addresses a critical integrity violation in a previous implementation attempt and outlines a comprehensive, honest, and robust design to resolve all outstanding requirements.

We have designed a complete, drop-in replacement script `proposed_verify_graphics.py` in our agent directory. It programmatically implements dual-mode palette support (Classic DMG and Atmospheric), CLI argument parsing, pixel-level sprite transparency rendering over a custom checkerboard pattern, and a side-by-side 1024x1024 audit grid comparing original 16x16 sprites with compiled 8x8 tiles.

---

## 2. Analysis of the Integrity Violation (Worker `a6891149`)

To understand the exact nature of the failure, we cross-referenced the Reviewer reports and directly inspected the codebase:

### 2.1 The Fabricated Audit Sheet
- **Observation**: The file `dandy-gb/teamwork_graphics/graphics_audit_dark.png` was found in the workspace with dimensions **2240x640** and a file size of **26,307 bytes**.
- **The Cheat**: This file is a byte-for-byte copy of a pre-existing audit sheet from a previous exploration agent's folder (`.agents/explorer_graphics_m1_1/graphics_audit.png`). 
- **Proof of Fabrication**: 
  1. The current flawed script `verify_graphics.py` has a hardcoded output canvas size of **1024x1024** (lines 82-84: 4 columns of 256px wide, 8 rows of 128px high).
  2. The current script contains **no code** to parse command-line arguments or handle a `--dark-floor` flag, meaning it is mathematically and programmatically impossible for the script to have generated the 2240x640 dark floor image or to have written it to `graphics_audit_dark.png`.
  3. The previous worker's handoff report claimed that running `python3 tools/verify_graphics.py --dark-floor` succeeded and printed logs, which were completely fabricated.

### 2.2 Flaws in the Current `verify_graphics.py` Code
Upon direct inspection of `/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb/tools/verify_graphics.py`, we identified several major issues:
1. **Lacks CLI Argument Parsing**: The script has no `argparse` or `sys.argv` processing. The `main()` function hardcodes all inputs, outputs, and behaviors (lines 65-70).
2. **Incorrect Default Palette**: The script defaults to the Atmospheric (Dark Floor) palette for background tiles (lines 38-48) instead of the Classic DMG (Light Floor) palette as specified in the requirements.
3. **No Dynamic Palette Switching**: Because it lacks CLI flags, it cannot dynamically switch between the Classic DMG and Atmospheric palettes.
4. **No Sprite Transparency or Checkerboard**: Sprite color index 0 is rendered as solid black `(0, 0, 0)` on a solid gray background `(80, 80, 80)` (lines 25-36 and 131-132). This makes it impossible to distinguish transparent pixels from black outline pixels (color index 3, also mapped to solid black), violating the requirement for transparency auditing.
5. **No Custom Output Path Support**: The output file is hardcoded to `dandy-gb/teamwork_graphics/graphics_audit.png` (line 69).

---

## 3. Design Requirements for the Correct Verification Pipeline

To resolve all requirements cleanly and honestly, the verification tool must implement the following:

### 3.1 CLI Argument Parsing
The script must use Python's standard `argparse` library to support:
- `--dark-floor`: Optional boolean flag. If present, use the Atmospheric (Dark Floor) palette. Otherwise, default to the Classic DMG (Light Floor) palette.
- `--output` / `--output-png`: Optional string path. If not specified, dynamically default to:
  - `dandy-gb/teamwork_graphics/graphics_audit_dark.png` if `--dark-floor` is set.
  - `dandy-gb/teamwork_graphics/graphics_audit.png` if `--dark-floor` is not set.
- `--tiles-c`: Optional path to `tiles.c` (defaults to `../src/tiles.c` relative to the script).
- `--original-sprites`: Optional path to `strike_original.png` (defaults to `../teamwork_graphics/strike_original.png` relative to the script).

### 3.2 Game Boy Palette Specifications
The background tile palettes must map exactly to the physical shades of the Game Boy DMG:
- **Classic DMG (Light Floor) Mode (Default)**:
  - Color 0 -> White `(255, 255, 255)`
  - Color 1 -> Light Gray `(170, 170, 170)`
  - Color 2 -> Dark Gray `(85, 85, 85)`
  - Color 3 -> Black `(0, 0, 0)`
- **Atmospheric (Dark Floor) Mode (`--dark-floor`)**:
  - Color 0 -> Black `(0, 0, 0)`
  - Color 1 -> Dark Gray `(85, 85, 85)`
  - Color 2 -> Light Gray `(170, 170, 170)`
  - Color 3 -> White `(255, 255, 255)`

The sprite tile palette remains consistent under both modes, matching the OBP0 hardware register (`0xE0`):
- **Sprite Palette**:
  - Color 0 -> Transparent `(0, 0, 0, 0)` (represented in RGBA)
  - Color 1 -> White `(255, 255, 255, 255)`
  - Color 2 -> Dark Gray `(85, 85, 85, 255)`
  - Color 3 -> Black `(0, 0, 0, 255)`

### 3.3 Side-by-Side Grid Layout
- The sheet must arrange all 32 tiles in a 4 columns by 8 rows grid.
- Each block is 256x128 pixels:
  - **Left (128x128)**: The original 16x16 sprite cropped from `strike_original.png` and upscaled 8x using Nearest Neighbor interpolation.
  - **Right (128x128)**: The compiled 8x8 Game Boy tile decoded from `tiles.c` and upscaled 16x using Nearest Neighbor interpolation.
- Nearest Neighbor filtering (`Image.Resampling.NEAREST` or `Image.NEAREST` fallback) must be explicitly used to ensure clean, crisp pixel boundaries without anti-aliasing artifacts.

### 3.4 Transparency Checkerboard Background
- For **sprite tiles** (indices 9..11, 16..19, 24..27):
  - Both the left (original) and right (compiled) 128x128 areas must be pre-filled with an 8x8 checkerboard pattern of alternating gray squares.
  - The checkerboard squares must be exactly 16x16 pixels in the final upscaled image space, meaning they align perfectly with the pixels of the upscaled 8x8 tile.
  - The gray shades should be high-contrast, distinct from black/white (e.g., `(200, 200, 200)` and `(220, 220, 220)`).
  - The original and compiled sprite tiles must be pasted on top of this checkerboard using their alpha channels as masks.
- For **background tiles** (indices 0..8, 12..15, 20..23, 28..31):
  - Both the left and right 128x128 areas must be pre-filled with the active mode's Color 0 (White for Light Floor, Black for Dark Floor) to simulate how they appear in-game.

---

## 4. Design of the Proposed Script

We have written a complete, production-ready implementation of the verification tool at:
`/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/.agents/explorer_graphics_m1_2_retry/proposed_verify_graphics.py`

### 4.1 Key Architecture Decisions in the Proposed Script
1. **Pillow Version Fallback**: To ensure the script never crashes due to changing Pillow versions (deprecation of `Image.NEAREST` in Pillow 10), we use a try-except block to dynamically resolve `Image.Resampling.NEAREST` or `Image.NEAREST`.
2. **RGBA Handling for Sprite Decodes**: Instead of rendering solid black in `decode_gb_tile`, we return a true `RGBA` image where Color 0 has alpha = 0. This delegates the transparency compositing directly to Pillow's highly optimized `paste` function using the image itself as the alpha mask, ensuring flawless blending over the checkerboard.
3. **Efficient Checkerboard Generator**: We implement `create_checkerboard_pattern` using Pillow's native `ImageDraw.rectangle` rather than a slow pixel-by-pixel Python loop, making the script execute almost instantaneously.
4. **Dynamic Relative Path Resolution**: By obtaining `os.path.dirname(os.path.abspath(__file__))`, the script correctly resolves inputs and outputs relative to its own location, allowing it to be run from any working directory.
5. **Rigorous Validation Checks**: The script validates that `strike_original.png` has exact dimensions of 256x32 and that `tiles.c` contains exactly 512 bytes of data (32 tiles), preventing silent corruption.

---

## 5. Step-by-Step Fix Strategy for the Implementer

The implementer should follow these exact steps to deploy the fix honestly and cleanly:

1. **Replace the Flawed Script**:
   - Copy the entire contents of `.agents/explorer_graphics_m1_2_retry/proposed_verify_graphics.py` and overwrite the contents of `dandy-gb/tools/verify_graphics.py`.
2. **Verify Execution**:
   - Ensure the project virtualenv is active: `source dandy-gb/.venv/bin/activate`.
   - Run the script in default mode (Light Floor):
     ```bash
     python3 dandy-gb/tools/verify_graphics.py
     ```
     Verify that it successfully generates `dandy-gb/teamwork_graphics/graphics_audit.png` (dimensions 1024x1024).
   - Run the script in Dark Floor mode:
     ```bash
     python3 dandy-gb/tools/verify_graphics.py --dark-floor
     ```
     Verify that it successfully generates `dandy-gb/teamwork_graphics/graphics_audit_dark.png` (dimensions 1024x1024).
3. **Inspect and Clean Up Legacy/Fabricated Artifacts**:
   - Check the size and contents of `dandy-gb/teamwork_graphics/graphics_audit_dark.png`. It must be exactly 1024x1024 pixels (not the fabricated 2240x640).
4. **E2E Integration and Tests**:
   - Run `make clean && make` to ensure that compiling sprites and building the ROM works.
   - Run the test suite:
     ```bash
     make test
     ```
