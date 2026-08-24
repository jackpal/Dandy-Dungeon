# Milestone 3 Handoff: Comparative Selection & Packing

This report details the findings and plans for Milestone 3, structured in accordance with the 5-component Handoff Protocol.

---

## 1. Observation

During our systematic investigation of the repository, we observed the following:

1.  **Codebase Layout and Compiler API:**
    *   `dandy-gb/downscale/compiler.py` defines the C code generator:
        ```python
        extern const unsigned char dandy_tiles[DANDY_NUM_TILES * DANDY_TILE_SIZE];
        ```
        It packs 8x8 numpy arrays containing values `0..3` into 16-byte Game Boy 2bpp planar tiles.
    *   `dandy-gb/downscale/engine.py` manages a registry of downscaling strategies, including standard interpolation methods and the custom `font-hinting` strategy (FHDA).
    *   `dandy-gb/tools/downscale_sprites.py` currently downscales the original sprite sheet into 8x8 tiles using a single chosen mathematical algorithm.
2.  **No Pre-existing Redrawn Sprites:**
    *   A search of all codebase files for keywords like `override`, `redrawn`, `8x8`, and `matrix` returned 0 occurrences in `index.html` or other project files. The only occurrence of `redrawn` in the repository was found in `dandy-gb/docs/architectural_review.md` and `dandy-gb/tests/test_tier4.py` in the context of viewport rendering, not asset overrides.
3.  **Tile Reordering and Categories:**
    *   `dandy-gb/tools/verify_graphics.py` defines `GB_TO_JS_MAPPING` to handle tile index mapping. It categorizes the 32 tiles into:
        *   **Background tiles:** `bg_indices = set(list(range(9)) + list(range(12, 16)) + list(range(20, 24)) + list(range(28, 32)))`
        *   **Sprite tiles:** `sprite_indices = set(list(range(9, 12)) + list(range(16, 20)) + list(range(24, 28)))`
4.  **Makefile Targets:**
    *   `dandy-gb/Makefile` defines the `sprites` target:
        ```makefile
        sprites:
        	@echo "Compiling downscaled sprite assets using FHDA..."
        	.venv/bin/python $(TOOLS_DIR)/downscale_sprites.py --input teamwork_graphics/strike_original.png --output-c src/tiles.c --output-h src/tiles.h --output-preview teamwork_graphics/downscale_preview.png
        ```

---

## 2. Logic Chain

1.  **Need for Overrides:**
    *   Mathematical downscaling (even FHDA) struggles to maintain optimal readability on complex sprites, such as character orientations (arrows at indices 16..19, player directions at indices 24..27) and small items (key, food). Manual 8x8 overrides are necessary for these specific tiles (Observation 3).
2.  **Representation of Overrides:**
    *   Since no pre-existing hand-drawn overrides exist (Observation 2), we must define a format. A 128x16 PNG file (`teamwork_graphics/redrawn_sprites.png`) containing 32 tiles of 8x8 pixels is the most standard, visual, and artist-friendly representation.
3.  **Unified Selection Config:**
    *   Rather than applying an all-or-nothing choice, we should support selecting a source per tile. A JSON configuration (`downscale_config.json`) mapping tile index strings to either a specific mathematical algorithm name or `"redrawn"` provides perfect granular control.
4.  **CLI Tool Integration:**
    *   Updating `downscale_sprites.py` to accept `--config` and `--redrawn` arguments, and instantiating a new `TileSelector` class to process selection before compiling, resolves the selection requirement. 
    *   By defaulting the selector to `args.algorithm` when no config is provided, we preserve 100% backward-compatibility (Observation 4).
5.  **Robust Color Mapping:**
    *   When loading the redrawn PNG, we must map arbitrary pixel colors to GameBoy color indices `0..3`. Mapping transparent pixels (alpha < 128) to index 0, and mapping opaque pixels to their nearest grayscale level using midpoint brightness boundaries ensures that the output is always valid, even if the PNG colors are slightly off-shade.

---

## 3. Caveats

1.  **Off-Shade Colors in Redrawn PNG:**
    *   If an artist uses non-standard colors in `redrawn_sprites.png`, the tool will automatically map them to the closest GameBoy grayscale index using brightness thresholds. While this prevents build failures, it could result in slight visual differences from the artist's original intent if the colors are highly off-shade.
2.  **Strict Mode for Missing Assets:**
    *   If a tile is configured to use `"redrawn"`, but the redrawn PNG is missing, the tool raises a `FileNotFoundError`. This is safe and prevents silent failures in the build pipeline.

---

## 4. Conclusion

Milestone 3 is highly structured and can be implemented with minimal footprint and zero breaking changes.
*   **Actionable Plan:** Create `downscale/selector.py` with the `TileSelector` class, update `downscale_sprites.py` to integrate it, update the `Makefile` target, and create a comprehensive unit test suite in `tests/test_selection_pipeline.py`.
*   **Scope:** Confined entirely to the Python downscaling compiler packages, helper CLI tool, and test files. No production C runtime changes are required.

---

## 5. Verification Method

To independently verify the implementation, the following checks must be executed:

1.  **Run Unit Tests:**
    Execute the new unit test suite:
    ```bash
    .venv/bin/python -m unittest tests/test_selection_pipeline.py
    ```
    All tests (covering color mapping, config loading, overrides, and error cases) must pass cleanly.
2.  **Verify GBDK Compilation:**
    Run the compiler:
    ```bash
    make clean && make
    ```
    The build must succeed with 0 warnings/errors, producing the `bin/dandy.gb` ROM.
3.  **Run E2E Emulator Tests:**
    Execute the PyBoy automated E2E tests:
    ```bash
    make test_emu
    ```
    This verifies that the packed tiles are binary-compatible and function correctly inside the GameBoy VRAM.
4.  **Inspect the Audit Sheet:**
    Generate and inspect the visual audit sheet:
    ```bash
    python3 tools/verify_graphics.py --output teamwork_graphics/graphics_audit.png
    ```
    Confirm that tiles marked `"redrawn"` are correctly loaded from `redrawn_sprites.png` and displayed side-by-side with their original 16x16 counterparts.
