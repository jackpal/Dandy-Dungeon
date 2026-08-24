# Milestone 2 Blueprint: Font-Hinted Downscaling Compiler (FHDA)

This blueprint defines the exact software architecture, class modules, command-line interface (CLI) specification, and algorithmic implementation steps for the Game Boy pixel-art downscaling compiler tool (`downscale_sprites.py`).

---

## 1. Directory and Module Layout

The tool must be implemented as a modular Python package inside `dandy-gb/` to ensure clean separation of concerns and extensibility:

```
dandy-gb/
├── tools/
│   └── downscale_sprites.py          # Entry point and CLI coordinator
└── downscale/                     # Core library package
    ├── __init__.py
    ├── engine.py                  # Downscaling Engine & Registry
    ├── manager.py                 # Sprite Sheet Loader & Slicer
    ├── compiler.py                # Game Boy 2bpp C Code Generator
    └── algorithms/                # Pluggable downscaling strategies
        ├── __init__.py
        ├── base.py                # Abstract Base Downscaler
        ├── standard.py            # Standard interpolation (Nearest, Bilinear, etc.)
        └── custom.py              # Custom Font-Hinting (FHDA) Downscaler
```

---

## 2. CLI Interface Specification

The entry point `tools/downscale_sprites.py` must expose the following command-line arguments, validating types and bounds:

| Option | Alias | Type | Default | Constraints | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `--input` | `-i` | `str` | *Required* | Must exist on disk | Path to `strike_original.png` (256x32) or individual tiles folder. |
| `--output-c` | `-c` | `str` | `src/tiles.c` | Directory must be writable | Target path for GBDK C source array. |
| `--output-h` | | `str` | `src/tiles.h` | Directory must be writable | Target path for GBDK C header file. |
| `--output-png`| `-o` | `str` | *Optional* | Directory must be writable | Path to save downscaled 128x16 sprite sheet. |
| `--output-preview`| `-p` | `str` | *Optional* | Directory must be writable | Path to save side-by-side validation sheet. |
| `--algorithm` | `-a` | `choice`| `font-hinting`| `nearest`, `bilinear`, `bicubic`, `box`, `font-hinting` | Downscaling algorithm to apply. |
| `--outline-thickness`| | `float`| `1.0` | `0.0 <= val <= 2.0` | Target outline thickness in downscaled pixels. |
| `--contrast-threshold`| | `float`| `0.5` | `0.0 <= val <= 1.0` | Contrast threshold separating body from background. |
| `--symmetry-weight`| | `float`| `0.8` | `0.0 <= val <= 1.0` | Importance score for maintaining tile symmetry. |
| `--feature-weight`| | `float`| `0.7` | `0.0 <= val <= 1.0` | Priority boost for high-contrast features (eyes). |
| `--grid-snap` | | `bool` | `True` | `True` or `False` | Enable pre-processing grid shift. |

**Exit Codes & Errors**:
- Any missing file or invalid parameter must terminate gracefully with **exit code 1** (or **2** for argparse violations) and write a clear, clean error message to `stderr` without dumping raw Python tracebacks.

---

## 3. The 6-Step Font-Hinted Downscaling Algorithm (FHDA)

The core algorithm is implemented in `downscale/algorithms/custom.py` inside the `FontHintingDownscaler` class. 

For each 16x16 input tile $I(x, y)$ (where $x, y \in \{0..15\}$), output an 8x8 tile $O(u, v)$ (where $u, v \in \{0..7\}$) with Game Boy color indexes:
- `0`: Transparent (for sprites) or White (for background tiles)
- `1`: Light Gray
- `2`: Dark Gray
- `3`: Black (Outline/Details)

### Step 1: Optimal Grid Shift (Grid Snapping)
To align the 16x16 sprite's features with the 2x2 downscaling grid, find a translation vector $(dx, dy) \in \{-1, 0, 1\}^2$ that maximizes the **Grid Homogeneity Score** $S(dx, dy)$.
1. For each translation $(dx, dy)$, construct a shifted image $I'(x, y) = I(x + dx, y + dy)$, padding any exposed border pixels with pure black background `(0, 0, 0, 255)`.
2. Compute $S(dx, dy) = \sum_{u=0}^7 \sum_{v=0}^7 \Phi(B'_{u,v})$ where $B'_{u,v}$ is the 2x2 block:
   $$B'_{u,v} = \{ I'(2u + i, 2v + j) \mid i, j \in \{0, 1\} \}$$
   and $\Phi(B)$ is:
   $$\Phi(B) = \begin{cases} 
   1, & \text{if } B \text{ contains 4 pure black pixels OR 0 black pixels} \\ 
   0, & \text{otherwise} 
   \end{cases}$$
3. Select $(dx^*, dy^*) = \arg\max S(dx, dy)$. If there is a tie, select $(0, 0)$.
4. Apply the optimal shift to get $I_{aligned}$.

### Step 2: Flood-Fill Segmentation
Separate the aligned image $I_{aligned}$ into background and character segments:
1. Perform a 4-connected flood-fill starting from all 64 border pixels $(x, y)$ (where $x \in \{0, 15\}$ or $y \in \{0, 15\}$).
2. A pixel is flooded if its RGB values are close to black: $\text{R} < 10, \text{G} < 10, \text{B} < 10$.
3. Mark all flooded pixels as `BG` (Background).
4. Mark all non-flooded pixels as `CH` (Character).
5. Within `CH`, classify pixels that are pure black `(0, 0, 0, 255)` as `CH_BLACK` (internal outlines), and all other colored pixels as `CH_BODY`.

### Step 3: Dynamic Symmetry Detection
Verify if the sprite possesses horizontal symmetry:
1. Compute the horizontal segment mismatch count $D$:
   $$D = \sum_{y=0}^{15} \sum_{x=0}^7 [ \text{Segment}(x, y) \neq \text{Segment}(15-x, y) ]$$
   where $\text{Segment}(x, y) \in \{\text{BG}, \text{CH}\}$.
2. If $D \le 4$, flag the sprite as **Horizontally Symmetric**.

### Step 4: Structural Classification
Reduce the 16x16 grid to an 8x8 grid of segment states. For each 2x2 block $B_{u,v}$ in $I_{aligned}$ (for $u, v \in \{0..7\}$):
1. Let $N_{ch}$ be the number of `CH` pixels in the 2x2 block.
2. Classify the 8x8 coordinate $(u, v)$ as:
   $$\text{State}(u, v) = \begin{cases} 
   \text{Background (BG)}, & \text{if } N_{ch} < 2 \\ 
   \text{Character (CH)}, & \text{if } N_{ch} \ge 2 
   \end{cases}$$

### Step 5: Outline and Detail Assignment
For each 8x8 pixel $(u, v)$ classified as `CH`:
1. **Outer Outline**: If $\text{State}(u, v) == \text{CH}$ and it is adjacent to at least one 8-connected neighbor $(u', v')$ with $\text{State}(u', v') == \text{BG}$ in the 8x8 grid, assign it as **Outline (value 3)**.
2. **Internal Details**: Let $N_{int\_black}$ be the number of `CH_BLACK` pixels in the 16x16 2x2 block $B_{u,v}$. If $N_{int\_black} \ge 1$, assign it as **Outline (value 3)**.
3. If neither condition matches, classify the pixel as **Body**.

### Step 6: Salience-Weighted Color Selection & Symmetry Enforcement
For each 8x8 pixel $(u, v)$ classified as **Body**:
1. Map all colored pixels in the 2x2 block $B_{u,v}$ to their nearest Game Boy color indexes:
   - `White` `(255, 255, 255)` $\rightarrow$ Index `1` (for sprites)
   - `Light Blue-Gray` `(215, 223, 240)` $\rightarrow$ Index `1` (or `2` depending on shading)
   - `Red` `(201, 99, 99)` $\rightarrow$ Index `2` (Dark Gray)
   - `Dark Blue` `(46, 55, 174)` $\rightarrow$ Index `2` (Dark Gray)
2. Each pixel in the 2x2 block votes for its mapped color index $C \in \{1, 2\}$ with a salience weight $w(C)$:
   - $w(\text{White}) = 2.0$ (High contrast details priority)
   - $w(\text{Red / Gray / Blue}) = 1.0$ (Standard shading)
3. The color index with the highest weighted vote sum is selected:
   $$O(u, v) = \arg\max_{C \in \{1, 2\}} \sum_{p \in B_{u,v}, \text{Mapped}(p) == C} w(C)$$
4. **Symmetry Enforcement**: If the sprite was flagged as Horizontally Symmetric:
   For each row $v \in \{0..7\}$ and column $u \in \{0..3\}$:
   - Combine the votes of block $B_{u,v}$ and its reflected block $B_{7-u,v}$.
   - Assign the winning color to both $O(u, v)$ and $O(7-u, v)$.
   - If one side is Outline (3) and the other is Body, force **both** to Outline (3) to preserve symmetrical outlines.

---

## 4. Game Boy 2bpp Planar Packing & C Compilation

The `GameBoyCompiler` (in `compiler.py`) must pack the 8x8 indexed pixels into GBDK 2bpp planar binary format:
- Each 8x8 tile is represented by 16 bytes.
- For each row $y \in \{0..7\}$ of the tile:
  - Byte 1 (low bit plane): bit $x$ of Byte 1 represents the low bit of color index of pixel $(x, y)$.
  - Byte 2 (high bit plane): bit $x$ of Byte 2 represents the high bit of color index of pixel $(x, y)$.
  - The MSB (bit 7) corresponds to $x = 0$, LSB (bit 0) to $x = 7$.
- Output all 32 compiled tiles (512 bytes) as a standard GBDK C array in `src/tiles.c` and header `src/tiles.h`, matching the naming and format of the original codebase:
  ```c
  const unsigned char dandy_tiles[] = {
      // 32 tiles * 16 bytes = 512 bytes
  };
  ```

---

## 5. Adversarial and Unit Test Suite

Implement a comprehensive test suite in `dandy-gb/tests/test_downscale_sprites.py` containing:
1. **Unit Tests**:
   - Verify 2bpp packing on hand-crafted pixel grids.
   - Verify that the Strategy registry correctly dispatches standard and custom algorithms.
   - Verify horizontal symmetry detection on perfectly symmetric shapes (crosses, boxes) and asymmetry detection.
2. **Adversarial & Robustness Tests**:
   - Test empty (0-byte) and corrupted input PNGs.
   - Test incorrect image dimensions (e.g., 255x32, 16x16) and ensure they raise `ValueError` and exit with 1.
   - Test non-standard color modes (CMYK, Grayscale) and verify they are converted to RGBA/RGB without crashing.
   - Test out-of-range CLI parameters (e.g., `--outline-thickness -0.5`, `--contrast-threshold 1.5`) and verify they are rejected.
   - Test read-only output directories and file-directory name collisions, ensuring they write clean, user-friendly errors to `stderr` and exit with 1.
