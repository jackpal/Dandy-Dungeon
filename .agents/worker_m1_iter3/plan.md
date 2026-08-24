# Execution Plan — Milestone 1, Iteration 3

This plan outlines the step-by-step process to implement and verify the parser robustness and resource management fixes.

## Step 1: Fix C Parser Nested Comment Bug
- **Target**: `dandy-gb/tools/verify_graphics.py` -> `parse_tiles_c(tiles_c_path)`
- **Change**: Swap comment-stripping order. Strip single-line comments (`//...`) before stripping block comments (`/*...*/`).
- **Reasoning**: This ensures any single-line comments containing block-comment start tokens (e.g., `// comment with /*`) are completely removed *before* the block-comment stripper runs.
- **Verification**:
  - Run `verify_graphics.py` to ensure it still parses `tiles.c` correctly.
  - Create a temporary C file with the nested comment pattern and write a small test to verify the regex strips comments correctly.

## Step 2: Fix JS Parser Commented-out Assignments
- **Target**: `dandy-gb/tools/extract_sprites.py` -> `extract_base64_from_js(content)`
- **Change**: Strip all JS comments (single-line and block comments) from the JS file content *before* running the regular expression to extract the base64 string.
- **Reasoning**: Commented-out assignments preceding the active assignment will be removed, preventing the regex from matching them.
- **Verification**:
  - Run `extract_sprites.py` to ensure it still extracts the sprite sheet correctly.
  - Run with a modified `strike.js` containing commented-out assignments to verify it correctly ignores them.

## Step 3: Fix PIL Image Resource Leak
- **Target**: `dandy-gb/tools/verify_graphics.py` -> `main(argv=None)`
- **Change**:
  - Wrap `Image.open(strike_png_path)` in a `with` statement.
  - Wrap `Image.new("RGBA", ...)` for `audit_img` in a `with` statement.
  - Wrap the `audit_img.convert("RGB")` in a `with` statement and save from it.
- **Reasoning**: Ensures all file descriptors are closed and memory/resources are freed properly.
- **Verification**:
  - Run `verify_graphics.py` and verify it runs cleanly without exceptions.

## Step 4: Full Pipeline & Compilation Verification
- **Actions**:
  1. Run `dandy-gb/.venv/bin/python tools/extract_sprites.py` to regenerate the sprite sheet.
  2. Run `dandy-gb/.venv/bin/python tools/verify_graphics.py` to regenerate the audit sheet.
  3. Run `make clean && make` in `dandy-gb/` to verify ROM compilation.
- **Verification**:
  - Confirm `teamwork_graphics/graphics_audit.png` is successfully regenerated.
  - Confirm compilation finishes with zero warnings and zero errors.
