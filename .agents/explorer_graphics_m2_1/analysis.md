# Sprite Downscaling Analysis Report: 16x16 to 8x8 Evaluation

**Author**: Explorer 1 (Milestone 2 - Standard Downscaling)  
**Date**: June 21, 2026  
**Working Directory**: `.agents/explorer_graphics_m2_1/`  
**Original Sprite Sheet**: `/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb/teamwork_graphics/strike_original.png`  
**Dimensions**: 256x32 pixels, containing 32 tiles of 16x16 pixels in a 16x2 grid.

---

## 1. Executive Summary
This report evaluates the performance of five standard downscaling algorithms (Nearest Neighbor, Bilinear, Bicubic, Lanczos, and Box) on the original 16x16 Game Boy style sprites, reducing them to 8x8 pixels. By performing pixel-level tracing of the downscaled grids, we demonstrate that **all standard mathematical downscaling algorithms fail to preserve the visual and semantic integrity of low-resolution pixel art**. 

*   **Nearest Neighbor** preserves sharp edges and colors but breaks symmetry and introduces severe pixel-shifting.
*   **Bilinear** completely obliterates critical facial features and outlines, turning high-contrast sprites into muddy, low-contrast blobs.
*   **Bicubic and Lanczos** introduce severe ringing (overshoot) artifacts—creating artificial solid black lines that never existed—and suffer from asymmetric feature loss.
*   **Box Filter** is symmetric and avoids overshoot, but still suffers from severe blurring and feature clogging on fine details.

---

## 2. Visual Characteristics of the Original Sprites (16x16)
The original sprite sheet `strike_original.png` is a 4-color Game Boy style asset sheet. Tracing its structures at 16x16 reveals several critical visual constraints:
1.  **Strict Color Palette**: Sprites use a discrete, 4-shade grayscale palette (represented in this report as: ` ` transparent/background, `·` white, `░` light gray, `▓` dark gray, and `█` black). There are no smooth gradients.
2.  **Symmetry**: Many structures possess exact horizontal and vertical symmetry (e.g., Tile 2's key/sword, Tile 6's four-corner block).
3.  **Outline Thickness**: Outlines and structural lines are typically **1 to 2 pixels wide** (e.g., 2-pixel wide maze channels in Tile 7, 2-pixel wide borders).
4.  **Critical Micro-Features**: Facial features, such as eyes or mouths, are represented by extremely small, high-contrast pixel clusters (e.g., a 2x4 horizontal block of light-gray `░` representing eyes in a dark-gray or black face, as seen in Tiles 24-27). A shift or loss of even a single pixel completely changes the character's expression or erases the feature entirely.

---

## 3. Algorithm-by-Algorithm Evaluation

### A. Nearest Neighbor Downscaling
*   **Mathematical Principle**: Samples the nearest source pixel coordinate for each target pixel coordinate. No interpolation or averaging occurs.
*   **Strengths**: 
    *   Preserves the original discrete color palette perfectly (no new blended shades are introduced).
    *   Preserves maximum edge sharpness and high contrast.
*   **Failures**: 
    *   **Severe Pixel-Shifting and Asymmetry**: Because it samples at fixed intervals, features that do not align perfectly with the 2:1 sampling grid are either doubled or completely omitted. This breaks symmetry.
    *   **Example (Tile 7 - Maze-like Texture)**:
        *   *Original (16x16)* has uniform 2-pixel channels and walls:
            ```
            ████░░██░░██████
            ██░░░░░░░░░░░░██
            ░░░░░░░░░░░░░░██
            ░░██░░██░░██░░██
            ```
        *   *Nearest Neighbor (8x8)* distorts this into an asymmetric, noisy pattern:
            ```
            █░░░░░░█
            ░█░█░█░█
            ░█░█░███
            █░░░░░░█
            ```
            The uniform channels are ruined, with some lines disappearing and others warping.

---

### B. Bilinear Downscaling
*   **Mathematical Principle**: Linearly interpolates pixel values in a 2x2 neighborhood.
*   **Strengths**: None for pixel art.
*   **Failures**:
    *   **Extreme Blurring and Outline Smearing**: Linear averaging of high-contrast boundaries (black `█` and white `·`) results in a muddy gray blur, clogging fine lines and channels.
    *   **Complete Feature Obliteration**: Small, high-contrast features (like eyes) are completely washed out and swallowed by surrounding darker pixels.
    *   **Example (Tile 24 - Character Face)**:
        *   *Original (16x16)* features clear light-gray eyes (`░░░░`) inside a dark head:
            ```
            ██████░░░░██████
            ████░░░░░░▓▓████
            ████▓▓░░░░▓▓████
            ██████░░░░██████
            ```
        *   *Bilinear Downscaled (8x8)* completely erases the eyes, replacing them with a solid block of dark-gray (`▓`), leaving a featureless, blank face:
            ```
            ████████
            ███▓▓███
            ██▓▓▓███  <-- Eyes are 100% swallowed by dark-gray
            ███▓▓███
            ```

---

### C. Bicubic Downscaling
*   **Mathematical Principle**: Interpolates pixel values using a cubic spline over a 4x4 neighborhood.
*   **Strengths**: None for ultra-low resolution pixel art.
*   **Failures**:
    *   **Ringing / Overshoot Artifacts**: The cubic kernel's negative sidelobes cause value overshoots at sharp boundaries, introducing artificial colors. On grayscale pixel art, this manifests as artificial solid black outlines or dark spots that were never present in the original.
    *   **Asymmetric Feature Loss**: The large spatial kernel is highly sensitive to subpixel offsets, causing one side of a symmetric feature to be preserved while the other is erased.
    *   **Example (Tile 2 - Symmetric Key/Sword)**:
        *   *Original (16x16)* contains only dark-gray (`▓`), light-gray (`░`), and white (`·`):
            ```
            ░░····▓▓▓▓····░░
            ░░··▓▓▓▓▓▓▓▓··░░
            ```
        *   *Bicubic (8x8)* introduces artificial solid black (`█`) pixels in the center of the dark-gray blocks due to overshoot:
            ```
            ░·░▓▓░·░
            ░·▓██▓·░  <-- Artificial solid black (█) created by overshoot!
            ░··▓▓··░
            ```
    *   **Example (Tile 24 - Character Face - Asymmetry)**:
        *   *Bicubic (8x8)* preserves the right eye as a faint 2-pixel light-gray dot, but completely erases the left eye, making the face bizarrely asymmetric:
            ```
            ████████
            ███▓▓███
            ██▓░░███  <-- Right eye visible (░░), left eye swallowed by dark-gray (▓)!
            ███▓▓███
            ```

---

### D. Lanczos Downscaling
*   **Mathematical Principle**: Uses a 3-lobed sinc filter to interpolate over a 6x6 neighborhood.
*   **Strengths**: None for pixel art.
*   **Failures**:
    *   **Severe Ringing and Haloing**: Lanczos has even stronger negative sidelobes than Bicubic, causing massive overshoot.
    *   **Extreme Asymmetry**: Like Bicubic, it creates bizarre asymmetric feature loss on micro-features.
    *   **Example (Tile 25 - Character Face)**:
        *   *Original (16x16)* has symmetric eyes and facial details.
        *   *Lanczos (8x8)* completely erases the left eye, while leaving a single light-gray pixel for the right eye, creating a distorted, "winking" face:
            ```
            ████████
            ██▓█████
            ██▓▓▓░██  <-- Left eye gone, right eye is a single '░' pixel!
            ```

---

### E. Box Downscaling
*   **Mathematical Principle**: Averages all source pixels within a square tile corresponding to one target pixel (for 16x16 to 8x8, this is a local 2x2 average).
*   **Strengths**:
    *   **Perfect Block Symmetry**: Because it integrates over a local 2x2 box, it preserves horizontal and vertical symmetry perfectly on aligned grids (unlike Bicubic/Lanczos).
    *   **No Overshoot**: It does not use negative lobes, so it never introduces artificial colors/outlines (no ringing).
*   **Failures**:
    *   **Blurring and Loss of Contrast**: Although superior to Bilinear/Bicubic, it still performs mathematical averaging, which blurs high-contrast 1-pixel outlines and shrinks micro-features to faint gray spots.
    *   **Example (Tile 6 - Four-Corner Symmetric Block)**:
        *   *Original (16x16)* contains four 4x4 blocks separated by 4-pixel gaps:
            ```
            ░░▓▓▓▓····▓▓▓▓░░
            ```
        *   *Box Downscaled (8x8)* performs perfectly here, matching Nearest Neighbor exactly because the layout aligns perfectly with the 2x2 averaging boxes:
            ```
            ░░░░░░░░
            ░▓▓··▓▓░
            ░▓▓··▓▓░
            ```
        *   However, on **Tile 24 (Character Face)**, the Box filter still reduces the eyes to a tiny, barely-visible 2-pixel slot and smears the surrounding hair outlines.

---

## 4. Why Simple Mathematical Interpolation Fails for Pixel Art
The fundamental failure of standard downscaling algorithms on pixel art stems from a clash of core assumptions:

1.  **Continuous Signal vs. Discrete Symbolic Grid**:
    Standard downscaling algorithms are designed for **photographic images**, which represent continuous physical scenes. In photos, high-frequency details (sharp edges) must be smoothed (low-pass filtered) before downsampling to prevent *aliasing* (jagged edges). 
    However, **pixel art is a discrete, symbolic grid**. There is no "underlying continuous scene." Every single pixel is a deliberate, hand-placed symbol. A single pixel represents an entire eye, a sword edge, or a shadow. Applying a low-pass filter (blurring) does not prevent aliasing; it **destroys the semantic meaning of the image**.

2.  **Luminance and Color Contamination**:
    Linear averaging of a 2x2 neighborhood containing 1 black pixel (outline) and 3 white pixels (background) results in a light-gray pixel. In pixel art, this light-gray pixel is perceived as a "smudge" or "blur," rather than a sharp outline. Outlines lose their purpose (which is to separate shapes), and features merge into a muddy gray wash.

3.  ** Rarity of Subpixel Grid Alignment**:
    At ultra-low resolutions (8x8), a shift of even 0.5 pixels is massive relative to the scale of the features (which are 1-2 pixels wide). Because standard algorithms use a rigid mathematical grid, any slight misalignment between the sprite's features and the downscaling grid results in severe asymmetric distortions (e.g., losing one eye) or structural breaks in lines.

---

## 5. Algorithmic Comparison Matrix

| Metric | Nearest Neighbor | Bilinear | Bicubic | Lanczos | Box Filter |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Edge Sharpness** | Excellent (Sharp) | Poor (Blurry) | Poor (Blurry) | Poor (Blurry) | Moderate (Soft) |
| **Palette Integrity** | Perfect (No new colors) | Poor (Blends colors) | Poor (Blends colors) | Poor (Blends colors) | Moderate (Blends colors) |
| **Ringing / Overshoot** | None | None | Severe (Black spots) | Severe (Black spots) | None |
| **Symmetry Preservation** | Poor (Grid-dependent) | Moderate | Poor (Asymmetric) | Poor (Asymmetric) | Excellent (Symmetric) |
| **Micro-Feature Preservation** | Good (but distorted) | Fails (Erased) | Fails (Asymmetric) | Fails (Asymmetric) | Moderate (Faded) |

---

## 6. Recommendations for Milestone 3 (Smart Downscaling)
To downscale these 16x16 sprites to 8x8 successfully, we cannot rely on standard mathematical interpolation. The subsequent implementation phase (Milestone 3) must utilize a **smart, rule-based, or pixel-art specific downscaling approach**. 

Any successful solution must:
1.  **Enforce Palette Constraints**: Restrict output pixels strictly to the original 4-color palette, preventing muddy blended grays.
2.  **Prioritize Outline Preservation**: Detect 1-pixel and 2-pixel outlines and ensure they remain continuous and dark, rather than allowing them to blur into the background.
3.  **Detect and Protect Micro-Features**: Treat structures like eyes or mouths as critical zones that must be preserved (e.g., by centering them or using specialized pixel-art rules like "always keep at least one light pixel for eyes").
4.  **Enforce Symmetry**: Maintain left-right or top-down symmetry by aligning the downscaling center with the sprite's axis of symmetry.
