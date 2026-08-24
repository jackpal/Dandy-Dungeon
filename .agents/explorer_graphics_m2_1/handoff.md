# Handoff Report: Sprite Downscaling Analysis (16x16 to 8x8)

**Agent**: Explorer 1 (Milestone 2 - Standard Downscaling)  
**Working Directory**: `/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/.agents/explorer_graphics_m2_1/`  
**Status**: Task Complete (Hard Handoff)

---

## 1. Observation
I analyzed the original 16x16 sprite sheet and evaluated standard downscaling algorithms by executing a custom Python evaluation script.

### A. Core Assets and Paths
*   **Original Sprite Sheet**: `/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb/teamwork_graphics/strike_original.png` (dimensions 256x32, 32 tiles of 16x16 pixels).
*   **Complete Pixel-Level Analysis Log**: `/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/.agents/explorer_graphics_m2_1/raw_ascii_grids.txt`
*   **Generated Spritesheet Assets (in `/tmp/`)**:
    *   `/tmp/downscale_eval/comparison_grid.png` (a consolidated side-by-side comparison sheet, with all tiles upscaled by 8x using Nearest Neighbor for easy human inspection).
    *   `/tmp/downscale_eval/strike_8x8_nearest.png` (8x8 spritesheet generated via Nearest Neighbor).
    *   `/tmp/downscale_eval/strike_8x8_bilinear.png` (8x8 spritesheet generated via Bilinear).
    *   `/tmp/downscale_eval/strike_8x8_bicubic.png` (8x8 spritesheet generated via Bicubic).
    *   `/tmp/downscale_eval/strike_8x8_lanczos.png` (8x8 spritesheet generated via Lanczos).
    *   `/tmp/downscale_eval/strike_8x8_box.png` (8x8 spritesheet generated via Box).

### B. Execution Command
The evaluation and report generation were performed using:
```bash
/usr/local/google/home/jackpal/.local/bin/uv run --default-index https://pypi.org/simple --with pillow python3 /tmp/generate_text_report.py
```
This executed cleanly with no errors.

### C. Direct Pixel-Level Observations
Verbatim extracts from the generated `raw_ascii_grids.txt` log show clear structural failures across different tile types:

1.  **Tile 2 (R0, C2) - Symmetric Key/Sword - Overshoot/Ringing in Bicubic/Lanczos**:
    *   *Original (16x16)* contains only dark-gray (`▓`), light-gray (`░`), and white (`·`):
        ```
        ░░····▓▓▓▓····░░
        ░░··▓▓▓▓▓▓▓▓··░░
        ```
    *   *Bicubic (8x8)* introduces artificial solid black (`█`) pixels in the center of the dark-gray blocks:
        ```
        ░·░▓▓░·░
        ░·▓██▓·░  <-- Artificial solid black (█) created by overshoot!
        ```

2.  **Tile 24 (R1, C8) - Character Face - Complete Feature Loss in Bilinear**:
    *   *Original (16x16)* features clear light-gray eyes (`░░░░`) inside a dark head:
        ```
        ██████░░░░██████
        ████░░░░░░▓▓████
        ████▓▓░░░░▓▓████
        ```
    *   *Bilinear (8x8)* completely erases the eyes, replacing them with a solid block of dark-gray (`▓`), leaving a featureless, blank face:
        ```
        ████████
        ███▓▓███
        ██▓▓▓███  <-- Eyes are 100% swallowed by dark-gray
        ```

3.  **Tile 24 (R1, C8) - Character Face - Asymmetry in Bicubic/Lanczos**:
    *   *Bicubic/Lanczos (8x8)* preserves the right eye as a faint 2-pixel light-gray dot, but completely erases the left eye, making the face asymmetric:
        ```
        ████████
        ███▓▓███
        ██▓░░███  <-- Right eye visible (░░), left eye swallowed by dark-gray (▓)!
        ```

---

## 2. Logic Chain
My step-by-step reasoning from observations to conclusions is as follows:

1.  **Averaging Causes Contrast/Outline Loss**: In **Tile 1** and **Tile 7**, bilinear/bicubic/lanczos downscaling averages 1-pixel and 2-pixel wide high-contrast lines with their surrounding lighter/background pixels. Because mathematical downscaling is linear, this averaging shifts the resulting color values toward a mid-gray. This obliterates high-contrast outlines, creating muddy, low-contrast blobs.
2.  **Averaging Causes Feature Obliteration**: In **Tile 24**, the character's eyes are represented by a tiny cluster of light-gray pixels (`░░░░`). When downscaled to 8x8, a 2x2 neighborhood is compressed into a single pixel. Averaging a small light cluster with a larger surrounding dark-gray/black region pushes the average luminance below the threshold for light-gray, completely swallowing the feature and turning the face blank.
3.  **Spline Kernels Cause Ringing (Overshoot)**: In **Tile 2**, bicubic and Lanczos downscaling show solid black (`█`) pixels in the center of the sprite. Because these algorithms use cubic/sinc interpolation functions with negative sidelobes, crossing a sharp high-contrast boundary (white `·` to dark-gray `▓`) causes the interpolation to overshoot, producing values darker than the source dark-gray. This introduces artificial solid black outlines/spots.
4.  **Spatial Grid Alignment Causes Asymmetric Distortion**: Nearest Neighbor selects single pixels at fixed grid intervals. If a symmetric feature (like the maze in **Tile 7**) is slightly misaligned with the grid, Nearest Neighbor samples one side and misses the other, causing severe asymmetric warping. Similarly, in **Tiles 24-26**, the larger spatial kernels of Bicubic and Lanczos are highly sensitive to subpixel phase shifts, resulting in one eye being preserved as a single pixel while the other is completely erased.
5.  **Box Filter Prevents Overshoot but Blurs**: The Box filter integrates over local 2x2 blocks. Because it has no negative sidelobes, it never overshoots (preserving color integrity without ringing) and preserves symmetry perfectly on perfectly-aligned grids (like the corner blocks in **Tile 6**). However, on complex features like faces (**Tile 24**), it still performs averaging and thus suffers from severe blurring and feature clogging.

---

## 3. Caveats
*   **No Implementation**: I did not write or test any custom/smart downscaling algorithms, as this is the objective of the subsequent Milestone 3.
*   **Palette Assumptions**: I assumed that the output must conform to the original 4-shade Game Boy grayscale palette. If a different color space or palette is introduced, the visual mapping will change, though the structural downscaling failures will remain identical.

---

## 4. Conclusion
Standard mathematical downscaling algorithms (Nearest Neighbor, Bilinear, Bicubic, Lanczos, and Box) are **completely unsuitable** for downscaling ultra-low resolution pixel art (16x16 to 8x8). 

*   Nearest Neighbor is the only standard algorithm that preserves color and sharpness, but it is unusable due to breaking symmetry and causing pixel-shifting.
*   Bilinear, Bicubic, and Lanczos are completely disqualified because they destroy outlines, obliterate facial features (eyes), and introduce ringing (overshoot) artifacts and asymmetric distortions.
*   Box filter is symmetric and ringing-free, but still blurs fine details and clogs channels.

**Actionable Scope for Milestone 3 (Smart Downscaling)**:
We must implement a custom, rule-based downscaling pipeline that:
1.  **Enforces Palette Integrity**: Maps output pixels strictly to the 4-color palette, avoiding blurred grays.
2.  **Preserves Outlines**: Detects outline pixels and ensures they remain continuous and high-contrast.
3.  **Protects Key Features**: Detects and preserves micro-features (like eyes) by centering or using dedicated feature-preservation rules.
4.  **Enforces Symmetry**: Detects the axis of symmetry and aligns the downscaling kernel center to prevent asymmetric warping.

---

## 5. Verification Method

### A. Visual Verification
To verify the visual results, inspect the generated comparison sheets and spritesheets:
*   Open `/tmp/downscale_eval/comparison_grid.png` to view the side-by-side comparison of all tiles upscaled by 8x.
*   Open `/tmp/downscale_eval/strike_8x8_nearest.png`, `/tmp/downscale_eval/strike_8x8_bilinear.png`, `/tmp/downscale_eval/strike_8x8_bicubic.png`, `/tmp/downscale_eval/strike_8x8_lanczos.png`, and `/tmp/downscale_eval/strike_8x8_box.png` to inspect the raw 8x8 spritesheets.

### B. Textual/Pixel-Level Verification
Inspect the complete pixel-by-pixel ASCII comparisons in `/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/.agents/explorer_graphics_m2_1/raw_ascii_grids.txt`. 
You can search for specific tiles (e.g., `TILE INDEX 2` or `TILE INDEX 24`) to verify the exact character mappings and traces documented in this report.

### C. Invalidation Conditions
If the original sprite sheet `/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb/teamwork_graphics/strike_original.png` is modified, or if a different color palette is applied to the source, the generated reports and assets must be regenerated. To regenerate them, run:
```bash
/usr/local/google/home/jackpal/.local/bin/uv run --default-index https://pypi.org/simple --with pillow python3 /tmp/generate_text_report.py
```
And check that the output matches the new source.
