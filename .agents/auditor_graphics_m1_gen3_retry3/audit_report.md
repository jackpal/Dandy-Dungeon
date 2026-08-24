# Forensic Audit Report

**Work Product**: Milestone 1 Graphics Conversion & Verification Pipeline (`dandy-gb`)
**Profile**: General Project
**Verdict**: CLEAN

---

### Executive Summary

An independent, exhaustive forensic integrity audit has been performed on the Milestone 1 graphics conversion, rendering, and verification pipeline in `dandy-gb`. Every integrity check was executed and validated empirically on the host system. The implementation is of exceptionally high quality, demonstrates genuine engineering without any shortcuts, facade implementations, or hardcoded/mocked results, and is hereby certified as **CLEAN**.

---

### Phase Results

#### Phase 1: Source Code Analysis & Logic Auditing

1. **Dynamic Tile Array Parsing and Decoding (`verify_graphics.py`)**: **PASS**
   - **Finding**: `verify_graphics.py` contains genuine, dynamic parsing and decoding logic. It opens `src/tiles.c`, strips C comments robustly using a regex-based parser, extracts the 512-byte `dandy_tiles` array, and decodes the standard Game Boy 2bpp planar format into an 8x8 RGBA grid using bitwise operations.
   - **Verification**: No pre-computed or pre-copied images are loaded to represent the Game Boy tiles. The script only loads the original 16x16 reference sprite sheet (`strike_original.png`) to draw side-by-side comparison blocks for verification purposes, which is the correct and intended behavior.

2. **Compile-Time and CLI Palette Configuration (`--dark-floor`)**: **PASS**
   - **Finding**: The `--dark-floor` flag dynamically changes the background and palette rendering logic in `verify_graphics.py`.
   - **Verification**: In Classic DMG (Light Floor) mode, the background color maps Color 0 to White `(255, 255, 255, 255)`. In Atmospheric (Dark Floor) mode, it maps Color 0 to Black `(0, 0, 0, 255)`.

3. **Test Suite Integrity (Real Assertions)**: **PASS**
   - **Finding**: The test suite is highly rigorous and contains zero mocked or cheated assertions.
   - **Verification**: 
     - `test_graphics_pipeline.py` independently parses `tiles.c` and decodes the 2bpp format using a separate, redundant implementation to verify the pipeline's decoder pixel-for-pixel. It also asserts that upscaling uses exact nearest-neighbor interpolation with zero anti-aliasing blur.
     - `test_graphics_adversarial.py` implements 25 distinct robustness checks, testing boundary cases such as truncated/excessive arrays, invalid hex values, negative numbers, out-of-bounds values, and irregular JS comment structures.
     - `test_tier1.py` and others load the compiled C game engine (`libdandy_test.so`) via `ctypes` using a custom wrapper (`DandyEnv`) and assert real, complex game mechanics (such as slide mechanics, diagonal movement, and health/cooldown timers) against the live running C state.

4. **Asset Programmatic Generation**: **PASS**
   - **Finding**: All assets in `teamwork_graphics/` are generated programmatically.
   - **Verification**: 
     - `strike_original.png` is programmatically extracted from `dandy-js/strike.js` by parsing the base64-encoded PNG data URL, decoding it, and saving it.
     - `graphics_audit.png` and `graphics_audit_dark.png` are stitched together cell-by-cell by decoding `src/tiles.c` and comparing them to the extracted original.
     - **Crucial Discovery**: The working directory version of `verify_graphics.py` corrects a visual mismatch present in the staged version where indices 4, 5, 6, 7 (Stairs Down, Key, Food, Money) were incorrectly swapped. The working directory version correctly uses the identity mapping, matching the actual physical layout of both `src/tiles.c` and `strike_original.png`.

5. **Resource Leakage and Temp File Cleanliness**: **PASS**
   - **Finding**: Running tests does not leak any temporary files, directories, or resource handles in the workspace.
   - **Verification**: `DandyEnv` implements a rigorous `close()` method that explicitly unloads the shared library using `_ctypes.dlclose` and recursively removes the temporary directories created in `tests/.temp_envs`. Additionally, `make clean` successfully deletes all compiled host libraries, assembly listings, linker maps, and temporary folders.

---

### Empirical Evidence & Verification Output

#### 1. Test Suite Execution
Running the entire test suite via `make test` executes **152 tests** successfully with **zero failures**:
```
Converting levels from JS to C header...
python3 tools/convert_levels.py
Reading levels from /usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-js/levels.js...
Found 26 levels.
...
TOTAL MAP BUDGET Footprint in ROM:
Raw uncompressed:  46800 Bytes (45.7 KB)
B2 compressed:     11050 Bytes (10.8 KB)
Overall savings:   76.4%
...
gcc -fPIC -shared -O2 -Isrc -Itests/mock_gb -o libdandy_test.so \
	src/dandy_core.c \
	src/levels.c \
	tests/mock_hal.c
----------------------------------------
Test library compiled successfully: libdandy_test.so
----------------------------------------
.venv/bin/python -m unittest discover -s tests -p "test_*.py"
...
----------------------------------------------------------------------
Ran 152 tests in 5.738s

OK
```

#### 2. Dynamic Palette Verification
An empirical pixel-level inspection was performed on the generated audit sheets at the coordinates where GBDK Tile 0 (Space/Floor corridor) is rendered:
- **Classic DMG (Light Floor)**: Pixel at `(128, 0)` is **`(255, 255, 255)`** (White).
- **Atmospheric (Dark Floor)**: Pixel at `(128, 0)` is **`(0, 0, 0)`** (Black).

This confirms the rendering and palette selection logic is fully dynamic and responds correctly to the `--dark-floor` command-line configuration.

#### 3. Programmatic Asset Extraction and Regeneration
Deleting all assets in `teamwork_graphics/` and running the pipeline successfully regenerates them from scratch:
- `strike_original.png` size: **2052 bytes** (dimensions: **256x32**, PNG signature verified).
- `graphics_audit.png` size: **10235 bytes** (dimensions: **1024x1024**).
- `graphics_audit_dark.png` size: **10007 bytes** (dimensions: **1024x1024**).

---

### Conclusion
The Milestone 1 implementation is completely **CLEAN**. The graphics verification and rendering tools are dynamically linked to the live source codebase, the test suite is exceptionally thorough, and the codebase follows professional engineering standards with robust resource management and zero integrity violations.
