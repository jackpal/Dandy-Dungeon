# Milestone 1 Code & Visual Review Report

**Verdict**: REQUEST_CHANGES

---

## Review Summary

The graphics extraction and verification implementation for Milestone 1 has been independently reviewed. While the pipeline successfully runs, builds the ROM, and generates the audit sheets, there are multiple critical and major failures in both the visual assets (direct violations of the Milestone 1 design criteria) and the verification tool's code correctness/robustness.

Specifically:
1. **Visual Audit Mismatches (FAIL)**:
   - **Wall Style Substitution (C1 violation)**: The wall tile is rendered as a brick pattern instead of the original blue/black diagonal cross pattern.
   - **Stairs & Door Style Mismatches (C1/C3 violation)**: Stairs Up is rendered as a hollow square and Stairs Down as concentric squares, rather than recognizable staircases.
   - **Contrast & Readability (C4 violation)**: In Classic DMG mode, sprites do not render as dark silhouettes, causing poor contrast against the White floor.
2. **Code Correctness & Robustness (FAIL)**:
   - `verify_graphics.py` silently accepts invalid hex tokens (e.g., `0xGG` is parsed as `0`) rather than raising an error, causing a unit test failure in the adversarial suite.
   - The script lacks graceful error handling for missing files, leaking raw Python tracebacks.

---

## Findings

### Critical Finding 1: Visual Audit Failure - Wall Style Substitution (C1 Violation)
- **What**: The GBDK Wall tile (Tile 1) is implemented as a running bond brick pattern.
- **Where**: `/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb/src/tiles.c` (Tile 1), compiled from `/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb/tools/compile_bmp_sprites.py` (lines 33-43).
- **Why**: Direct violation of the Milestone 1 rubric C1: *"The wall must match the original style (no brick pattern substitution)"*. The original style in `strike_original.png` (Tile 1) is a pattern of diagonal crosses.
- **Suggestion**: Re-design the Wall tile (Tile 1) in `compile_bmp_sprites.py` to match the original diagonal crosses pattern.

### Major Finding 2: Visual Audit Failure - Stairs Up and Stairs Down Mismatches (C1/C3 Violation)
- **What**: Stairs Up (Tile 3) is a hollow square outline and Stairs Down (Tile 4) is concentric squares, rather than recognizable staircases.
- **Where**: `/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb/src/tiles.c` (Tile 3, Tile 4), compiled from `compile_bmp_sprites.py` (lines 55-76).
- **Why**: Violates C1 (conceptual faithfulness) and C3 (recognizable shapes and symmetry on 8x8 grid).
- **Suggestion**: Re-design the stairs tiles to resemble actual staircases.

### Major Finding 3: Code Correctness - Silent Parsing of Invalid Hex Tokens in `verify_graphics.py`
- **What**: The parser `parse_tiles_c` silently accepts invalid hex tokens like `0xGG` and parses them as `0` instead of raising a `ValueError`.
- **Where**: `/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb/tools/verify_graphics.py`, line 76 (`re.findall(r"0[xX][0-9a-fA-F]+|\d+", array_content)`).
- **Why**: The regex sub-pattern `\d+` matches the `0` in `0xGG`, which is then converted to `0` by `int('0', 10)`. This allows corrupt or invalid asset source files to verify silently without warning.
- **Suggestion**: Update the token extraction logic or add validation to ensure that any parsed token is a fully valid hex or decimal string before appending it.

### Major Finding 4: Visual Contrast - Sprites not rendered as silhouettes in Classic DMG mode (C4 Violation)
- **What**: In Classic DMG mode (when `use_dark_floor` is False), sprites are rendered with White bodies and Black outlines. This is identical to Atmospheric mode, causing the sprite bodies to blend into the White floor (poor contrast and readability).
- **Where**: `/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb/tools/verify_graphics.py`, lines 95-106.
- **Why**: Direct violation of the C4 rubric: *"Classic DMG (default) must render floor as White and sprites as dark silhouettes."*
- **Suggestion**: Update the sprite decoding/rendering colors in `verify_graphics.py` to map sprites to dark silhouettes (e.g., Black or Dark Gray bodies) when `use_dark_floor` is False.

### Minor Finding 5: Code Quality - Lack of Graceful Failure / Traceback Leak
- **What**: If `src/tiles.c` or `strike_original.png` is missing, the tool throws a raw, unhandled Python traceback instead of exiting gracefully with a clean, user-friendly error message.
- **Where**: `/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb/tools/verify_graphics.py`, lines 57-58 and 194-195.
- **Why**: Violates robust CLI tool design principles.
- **Suggestion**: Wrap the file checks or the entire execution in a try-except block in `main`, print a clean message to stderr, and exit with `sys.exit(1)`.

---

## Verified Claims

- **ROM Compilation** → Verified via `make clean && make` using GBDK toolchain → **PASS** (ROM builds successfully as `bin/dandy.gb` with zero compiler warnings/errors).
- **Graphics Pipeline Unit Tests** → Verified via running `test_graphics_pipeline.py` → **PASS** (Independently decodes and verifies pixel-for-pixel match, and confirms perfect nearest-neighbor upscaling without anti-aliasing).
- **Adversarial Test Suite** → Verified via running `test_graphics_adversarial.py` → **FAIL** (`test_parse_tiles_c_invalid_hex_characters` failed because `verify_graphics.py` silently accepted `0xGG`).
- **Transparency Visualization** → Verified via `graphics_audit.png` inspection → **PASS** (Sprite tiles are correctly rendered over a transparent checkerboard grid, conforming to C5).
- **Symmetry** → Verified via inspecting symmetrical tiles (Stairs Up, Stairs Down, Door, Key, `$`) → **PASS** (Tiles are symmetric on the 8x8 grid, though their styles are conceptually unfaithful).

---

## Coverage Gaps

- **Sprite Sheet Layout Reordering** — Risk Level: Low. The mapping `GB_TO_JS_MAPPING` resolves the asset index reordering between the GBDK port and the original JS game, ensuring that the audit sheet compares the correct sprites side-by-side. The mapping is verified to be accurate.

---

## Unverified Items

- None. All visual elements, code correctness, and test files have been fully and independently verified.
