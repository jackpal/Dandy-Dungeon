# Milestone 3 Implementation Changes

We have successfully implemented **Milestone 3: Comparative Selection & Packing** for the Dandy Dungeon GameBoy Graphics Conversion Pipeline.

## Created Files

### 1. `dandy-gb/downscale/overrides.py`
- Houses the 32 hand-drawn native 8x8 GameBoy glyphs (extracted verbatim from `dandy-gb/tools/compile_bmp_sprites.py`) in the `HAND_DRAWN_GLYPHS` dictionary.
- Implements the `get_override_tile(tile_idx: int) -> np.ndarray` function which retrieves a glyph, converts its 8 strings of 8 character codes (`'0'..'3'`) into an `(8, 8)` NumPy array of type `np.uint8` with values in `0..3`, and returns it.

### 2. `dandy-gb/downscale/selector.py`
- Establishes the `TILE_SELECTION` registry mapping tile indices `0..31` to either `"mathematical"` or `"manual"` sources.
  - Background/structure tiles (0: Space, 1: Wall, 2: Door) and unused padding tiles (20..23, 28..31) are routed to `"mathematical"` (using the Font-Hinted Downscaling Algorithm / FHDA).
  - Complex/readable tiles (Stairs Up/Down, Key, Food, Money, Bomb, Monsters, Heart, Generators, Arrows, Players) are routed to `"manual"` (using the hand-drawn overrides).
- Implements the `TileSelector` class, validating the configuration mapping on initialization (ensuring all 32 tiles are configured) and routing tile requests via `select_tile(tile_idx, downscaled_tile)`.

### 3. `dandy-gb/tests/test_graphics_selector.py`
- Implements 4 robust, comprehensive test cases:
  - `test_overrides_validity`: Verifies that all 32 overrides in `overrides.py` are present and return `(8, 8)` arrays of type `np.uint8` containing only valid pixel values in `0..3`.
  - `test_selector_routing`: Verifies that `TileSelector` correctly routes `"manual"` tiles to the hand-drawn overrides and `"mathematical"` tiles to the downscaled arrays under a mock registry configuration.
  - `test_force_mathematical_flag`: Verifies that setting `force_mathematical=True` forces all tiles to bypass overrides and return mathematical downscaled tiles.
  - `test_packing_integration`: Verifies that all 32 overrides can be successfully packed by `GameBoyCompiler.pack_tile` without raising any exceptions, producing exactly 16 bytes of GameBoy 2bpp format.

## Modified Files

### 1. `dandy-gb/tools/downscale_sprites.py`
- Imported `TileSelector` from `downscale.selector`.
- Added the `--no-overrides` command-line flag (`action='store_true'`) to bypass manual overrides and force 100% mathematical downscaling.
  - *Bug Fix*: Escaped the percent character (`%` -> `%%`) in the argument parser's help string (`force 100%% mathematical downscaling`) to prevent an `argparse` `ValueError` (unsupported format character) caused by string interpolation in `ArgumentDefaultsHelpFormatter`.
- Instantiated `TileSelector(force_mathematical=args.no_overrides)` in `main()`.
- Updated the tile processing loop to pass each mathematically downscaled tile `ds_tile` through `selector.select_tile(idx, ds_tile)` before appending it to `tiles_8x8`.

## Verification & Build Summary

1. **Clean ROM Compilation**:
   - Running `make clean && make` compiles sprites using the integrated selector, packs them into GBDK format, writes `src/tiles.c` and `src/tiles.h`, and compiles the final GameBoy ROM (`bin/dandy.gb`) successfully with zero warnings/errors.
2. **Unit & Integration Tests**:
   - Running `./.venv/bin/python -m unittest discover -s tests` runs all 176 tests successfully with 0 failures and 0 errors.
   - The 4 new tests in `test_graphics_selector.py` pass cleanly in 0.039s.
3. **Visual Audit Sheets**:
   - Running `tools/verify_graphics.py` and `tools/verify_graphics.py --dark-floor` successfully regenerates both audit sheets (`teamwork_graphics/graphics_audit.png` and `graphics_audit_dark.png`), rendering the manual overrides and FHDA background tiles side-by-side with original sprites.
