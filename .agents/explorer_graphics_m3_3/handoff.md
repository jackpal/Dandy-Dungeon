# Milestone 3 Handoff: Comparative Selection & Packing Design
**Sender**: `explorer_graphics_m3_3` (teamwork_preview_explorer)  
**Recipient**: `parent` (orchestrator_graphics)  
**Task Status**: Complete (Hard Handoff)  

---

## 1. Observation
We conducted a thorough, read-only investigation of the graphics pipeline codebase and discovered the following:

1. **Planar 2bpp Packing**: In `dandy-gb/downscale/compiler.py` (lines 4-112), the class `GameBoyCompiler` contains `pack_tile(tile_8x8)` which packs an 8x8 NumPy array into 16 bytes:
   ```python
   low_byte |= (bit0 << (7 - x))
   high_byte |= (bit1 << (7 - x))
   ```
   And `compile(tiles_8x8, output_c_path, output_h_path)` writes the 512 bytes array declaration to `src/tiles.c`/`tiles.h`.
2. **Mathematical Downscaler**: In `dandy-gb/downscale/engine.py` (lines 6-49), the `DownscaleEngine` manages and executes downscaling strategies on single 16x16 tiles, returning 8x8 NumPy arrays.
3. **Pre-Existing Hand-Drawn Glyphs**: In `dandy-gb/tools/compile_bmp_sprites.py` (lines 21-298), a dictionary `GLYPHS` contains a complete set of 32 beautifully hand-drawn 8x8 pixel-art tiles. Each tile is represented as a list of 8 strings of 8 characters, representing color indices `0..3`. For example, Tile 7 (Money/Gold):
   ```python
   7: [
       "00002000",
       "00222200",
       "00202000",
       "00022200",
       "00002020",
       "00222200",
       "00002000",
       "00002000"
   ]
   ```
4. **Current CLI Tool**: In `dandy-gb/tools/downscale_sprites.py` (lines 25-126), the CLI tool processes 32 tiles by downscaling them mathematically and directly writing them to C source files.
5. **Existing Verification Suite**: In `dandy-gb/tools/verify_graphics.py` (lines 17-50) and `dandy-gb/tests/test_graphics_pipeline.py` (lines 18-246), a robust verification harness parses `src/tiles.c`, decodes the GBDK planar bytes, and stitches them into a side-by-side verification sheet `graphics_audit.png` (using `GB_TO_JS_MAPPING`).

---

## 2. Logic Chain
- **Step 1 (Consistency of Types)**: The mathematical downscaler outputs `(8, 8)` NumPy arrays with integer values `0..3` (from `engine.py`). The hand-drawn glyphs in `compile_bmp_sprites.py` are lists of strings representing the same `0..3` color indices.
- **Step 2 (Type Compatibility)**: We can write a simple converter in `downscale/overrides.py` to parse the string lists into `(8, 8)` NumPy arrays. Thus, both the mathematical downscaler outputs and the hand-drawn overrides share the identical interface contract, making them perfectly interchangeable.
- **Step 3 (Selection Decoupling)**: By introducing a registry mapping each tile `0..31` to either `"mathematical"` or `"manual"` (in a new module `downscale/selector.py`), we can dynamically route each tile through the appropriate generator at compile-time.
- **Step 4 (Zero-Risk Integration)**: Because the selected list of 32 `(8, 8)` tiles is passed to the unchanged `GameBoyCompiler.compile` method, the compilation pipeline remains completely backwards-compatible. The `Makefile` target `sprites` requires no signature changes, eliminating any risk of breaking existing build structures.
- **Step 5 (Automatic Verification)**: Because the packing output writes to the standard `src/tiles.c` contract, the existing `verify_graphics.py` and `test_graphics_pipeline.py` will automatically parse and verify the final selected tiles without needing any code changes.

---

## 3. Caveats
- **Manual Adjustments**: The hand-drawn glyphs are assumed to be correct and complete. Any future adjustments to these sprites must be done directly in the Python source code of `downscale/overrides.py` rather than a visual PNG editor, which is highly suited for this developer-led codebase.
- **Alternative Asset Sources**: We did not find any external PNG sheets for overrides, so we exclusively rely on the glyphs from `compile_bmp_sprites.py`.

---

## 4. Conclusion
We have designed a highly modular, safe, and backwards-compatible selection and packing architecture for Milestone 3. By refactoring the pre-existing hand-drawn glyphs from `compile_bmp_sprites.py` into a new package `downscale/overrides.py` and introducing a selector in `downscale/selector.py`, we can achieve optimal visual fidelity for complex tiles (e.g. players, arrows, key, stairs) while keeping floor/wall textures mathematically downscaled.

---

## 5. Verification Method
The next implementer or auditor agent can verify this design using the following steps:
1. **Locate Hand-Drawn Glyphs**: Verify that `dandy-gb/tools/compile_bmp_sprites.py` contains the `GLYPHS` dictionary with 32 hand-drawn tiles.
2. **Inspect Codebases**: Confirm that `dandy-gb/downscale/compiler.py` compiles the tiles into `src/tiles.c` and that the existing test suite `make test` runs successfully.
3. **Verify Audit Generation**: Verify that `python3 tools/verify_graphics.py` generates the `graphics_audit.png` visual sheet without errors.
4. **Implement New Test Suite**: Write the unit tests in `tests/test_graphics_selector.py` to assert that:
   - All overrides in `overrides.py` are valid `(8, 8)` matrices in range `0..3`.
   - The `TileSelector` routes `"mathematical"` and `"manual"` tiles correctly.
   - The `--no-overrides` flag successfully bypasses overrides.
