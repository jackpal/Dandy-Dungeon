# Verification Plan — Milestone 1 Graphics Extraction and Verification

This plan defines the steps to empirically verify and stress-test the graphics verification tool `dandy-gb/tools/verify_graphics.py`.

## 1. Baseline Verification & Execution
- Run `verify_graphics.py` under normal conditions.
- Confirm that both `strike_original.png` and `graphics_audit.png` are correctly generated.
- Inspect the output dimensions and content to ensure they are visually correct.

## 2. 2bpp Decoding Math Verification
- Write a standalone test script `test_2bpp_decoding.py` that:
  - Generates a known mock 2bpp tile byte array (e.g., checkerboard, solid colors, gradient).
  - Decodes it using both `verify_graphics.py`'s algorithm and an independent implementation of the Game Boy/GBDK 2bpp specification.
  - Verifies that the outputs match exactly.

## 3. Nearest-Neighbor Upscaling Verification
- Verify that `Image.NEAREST` upscaling preserves exact pixel boundaries without interpolation.
- Write a test in `test_2bpp_decoding.py` that checks the upscaled pixels of a single-pixel tile to ensure they form a perfect block of the expected scale (16x for GameBoy tile, 8x for original sprite).

## 4. Robustness and Adversarial Stress-Testing
- Write a test runner `test_robustness.py` to stress-test `verify_graphics.py` under the following scenarios:
  - **Scenario A: Missing Input Files** (rename/remove `strike.js` or `tiles.c`).
  - **Scenario B: Corrupt/Invalid Base64** in `strike.js` (e.g., non-base64 chars, invalid padding).
  - **Scenario C: Extra Double-Quoted Strings** in `strike.js` (e.g., `const title = "Dandy Dungeon";` or comments containing double quotes).
  - **Scenario D: Comments & Formatting in `tiles.c`** (e.g., block comments `/* ... */`, line comments `// ...`, extra whitespace, different variable definitions).
  - **Scenario E: Incorrect Tile Count** (e.g., 31 tiles or 33 tiles in `tiles.c`).
- Record how the script handles each failure mode (fails gracefully with user-friendly error vs. uncaught exception vs. silent corruption of output).

## 5. Resource Leak Checks
- Inspect the code for unclosed files or resources.
- Run the script while monitoring file descriptor usage using Python's `psutil` or system tools to ensure no leaks occur during execution.

## 6. Report Findings
- Document all findings, test results, and final verdict in `challenge.md`.
