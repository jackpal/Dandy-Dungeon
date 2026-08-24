## 2026-06-21T01:09:12Z

You are a worker tasked with implementing **Milestone 3: Comparative Selection & Packing** for the Dandy Dungeon GameBoy Graphics Conversion Pipeline.

### Objectives & Strategy:
You will implement the elegant, decoupled selection and overrides architecture proposed by Explorer 3 in `/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/.agents/explorer_graphics_m3_3/analysis.md`.
Specifically, you will reuse the pre-existing 32 hand-drawn 8x8 glyphs that already exist in the repository to serve as our manual overrides.

### Step-by-Step Instructions:

1. **Create `dandy-gb/downscale/overrides.py`**:
   - Extract the entire `GLYPHS` dictionary from `dandy-gb/tools/compile_bmp_sprites.py` (lines 21 to 298 or wherever it ends).
   - In `overrides.py`, define the dictionary `HAND_DRAWN_GLYPHS` containing these 32 glyphs.
   - Implement a function `get_override_tile(tile_idx: int) -> np.ndarray` that retrieves the glyph, converts the 8 strings of 8 characters (consisting of '0'..'3') into an `(8, 8)` NumPy array of type `np.uint8` containing integer values `0..3`, and returns it.

2. **Create `dandy-gb/downscale/selector.py`**:
   - Define the `TILE_SELECTION` registry as proposed by Explorer 3. It should map tile indices 0..31 to either `"mathematical"` or `"manual"`.
     - Specifically, set background/structure tiles (0: Space, 1: Wall, 2: Door) and any unused padding tiles (20..23, 28..31) to `"mathematical"`.
     - Set all complex/readable tiles (Stairs, Key, Food, Money, Bomb, Monsters, Heart, Generators, Arrows, Players) to `"manual"` to use the beautifully hand-crafted overrides.
   - Implement the `TileSelector` class as designed by Explorer 3, with:
     - Initialization checking the `force_mathematical` flag.
     - Configuration validation ensuring all 32 tiles are configured with either `"mathematical"` or `"manual"`.
     - A method `select_tile(tile_idx: int, downscaled_tile: np.ndarray) -> np.ndarray` that routes the tile selection accordingly.

3. **Integrate into `dandy-gb/tools/downscale_sprites.py`**:
   - Import `TileSelector` from `downscale.selector`.
   - Add a new command-line flag: `--no-overrides` (action='store_true') to bypass manual overrides and force 100% mathematical downscaling.
   - In `main()`, instantiate `TileSelector(force_mathematical=args.no_overrides)`.
   - In the tile processing loop, for each tile index `idx`:
     - First, run the mathematical downscaler to compute `ds_tile`.
     - Second, run `selected_tile = selector.select_tile(idx, ds_tile)`.
     - Append `selected_tile` to the `tiles_8x8` list.
   - The rest of the pipeline (compilation to C/H, preview sheet, etc.) will automatically use this final selected list!

4. **Implement Unit Tests in `dandy-gb/tests/test_graphics_selector.py`**:
   - Implement the 4 comprehensive test cases outlined by Explorer 3:
     - `test_overrides_validity`: Verify all 32 overrides in `overrides.py` return `(8, 8)` arrays with values in `0..3`.
     - `test_selector_routing`: Verify selector correctly returns the override for `"manual"` and the mathematical tile for `"mathematical"` under a mock configuration.
     - `test_force_mathematical_flag`: Verify that setting `force_mathematical=True` forces mathematical tiles for all indices.
     - `test_packing_integration`: Verify that all overrides can be successfully packed by `GameBoyCompiler.pack_tile` without raising any exceptions.

5. **Verify and Compile**:
   - Run the full test suite using the virtualenv Python:
     `./.venv/bin/python -m unittest discover -s tests`
     Ensure all 176+ tests (including the new graphics selector tests) pass cleanly with 0 failures.
   - Perform a clean compilation of the ROM:
     `make clean && make`
     Ensure that the ROM compiles cleanly with zero warnings/errors.
   - Regenerate the visual audit sheets:
     `./.venv/bin/python tools/verify_graphics.py`
     `./.venv/bin/python tools/verify_graphics.py --dark-floor`
     Ensure that both audit sheets are successfully generated.

### MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A Forensic Auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Please write a detailed report of your changes in `changes.md` in your own agent folder, and report your findings and build/test logs in your handoff.
