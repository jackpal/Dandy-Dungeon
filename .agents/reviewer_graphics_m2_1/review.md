# Review Report: Milestone 2 Graphics Downscaling Pipeline

## Review Summary

**Verdict**: **PASS**

The mathematical downscaling pipeline is implemented to an exceptionally high standard. The custom Font-Hinted Downscaling Algorithm (FHDA) matches the 6-step blueprint exactly, handles all edge cases and boundary conditions correctly, and preserves vertical and horizontal symmetries beautifully. The test suite is comprehensive and passes perfectly, and the GameBoy GBDK ROM compiles with **zero warnings and zero errors**. The visual audit sheets were generated successfully and demonstrate flawless downscaling quality.

A major code quality finding regarding Pillow Image resource management has been identified and should be addressed, but it does not block the correctness or usability of the compiler pipeline.

---

## Findings

### [Major] Finding 1: Pillow Image Resource Leaks

- **What**: Pillow `Image` contexts are not managed using `with` blocks or explicit `close()` calls, leading to potential unclosed file handles.
- **Where**: `dandy-gb/downscale/manager.py` (line 22) and `dandy-gb/downscale/algorithms/standard.py` (line 73)
- **Why**: In `SpriteSheetManager.load_and_slice`, `Image.open(image_path)` is called, but the file handle is never explicitly closed. This keeps the file open in memory until the object is garbage collected, which can lead to resource leaks in longer-running processes.
- **Suggestion**: Use a `with` block or an explicit `try...finally` block to ensure images are closed. For example:
  ```python
  with Image.open(image_path) as img:
      img_rgba = img.convert('RGBA')
      # Perform processing...
  ```

### [Minor] Finding 2: Lack of Explicit Alpha Check in CH_BLACK Classification

- **What**: The custom FHDA `_flood_fill_segmentation` classifies internal outlines (`CH_BLACK`) checking only RGB color values without verifying the alpha channel.
- **Where**: `dandy-gb/downscale/algorithms/custom.py` (line 158)
- **Why**: The blueprint specifies that `CH_BLACK` are pixels that are pure black `(0, 0, 0, 255)`. The implementation does `if r == 0 and g == 0 and b == 0:`. While this is functionally correct for the current assets since transparent pixels are already flooded and masked out in `bg_mask`, any internal transparent pixel (if present in future assets) would be incorrectly classified as `CH_BLACK` instead of transparent.
- **Suggestion**: Add an explicit alpha channel check:
  ```python
  if r == 0 and g == 0 and b == 0 and tile[y, x][3] == 255:
  ```

---

## Verified Claims

- **Claim**: The custom FHDA algorithm matches the 6-step blueprint.
  - **Verification method**: Code inspection of `dandy-gb/downscale/algorithms/custom.py`.
  - **Result**: **PASS**. The implementation maps perfectly to all 6 steps (Grid Snapping, Flood-Fill, Symmetry Detection, Structural Classification, Outline Assignment, Salience-Weighted Color Selection & Symmetry Enforcement).
- **Claim**: The compiler generates valid GameBoy 2bpp planar binary format.
  - **Verification method**: Code inspection of `dandy-gb/downscale/compiler.py` and running the unit tests in `dandy-gb/tests/test_downscale_sprites.py`.
  - **Result**: **PASS**. All 2bpp packing tests passed successfully.
- **Claim**: The GameBoy ROM compiles cleanly with zero warnings and zero errors.
  - **Verification method**: Ran `make clean && make` in `dandy-gb/`.
  - **Result**: **PASS**. The ROM compiled cleanly and successfully produced `bin/dandy.gb`.
- **Claim**: The visual verification tool successfully generates audit sheets that are visually correct.
  - **Verification method**: Ran `verify_graphics.py` and `verify_graphics.py --dark-floor`, and visually inspected `graphics_audit.png` and `graphics_audit_dark.png`.
  - **Result**: **PASS**. The output images are perfectly aligned, crisp, outline-continuous, and symmetrical.

---

## Coverage Gaps

None. The review covered all source files in the `downscale` package, the CLI coordinator `downscale_sprites.py`, the test suite `test_downscale_sprites.py`, the GBDK compilation flow, and the visual verification output.

---

## Unverified Items

None. All key requirements, claims, and visual outputs have been fully verified.
