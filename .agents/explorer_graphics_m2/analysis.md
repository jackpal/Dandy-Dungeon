# Dandy Dungeon Milestone 2: Graphics Downscaling Pipeline Design & Analysis

## Executive Summary
This report designs and evaluates a mathematical downscaling pipeline in Python to scale the original 16x16 pixel-art sprites from `strike_original.png` down to GameBoy-compatible 8x8 tiles. Our custom **Font-Hinting inspired Downscaling** algorithm successfully preserves critical outlines, maintains line connectivity (preventing sprites from being cut in half), keeps the dollar sign ($) highly recognizable, and strictly enforces left-right symmetry.

---

## 1. Analysis of the Original 16x16 Spritesheet
The original spritesheet `strike_original.png` is a 256x32 PNG containing 32 tiles arranged in a 16x2 grid. Each tile is 16x16 pixels.

### Color Mapping & Palette
Our programmatic analysis of the sheet revealed that it uses a strict **4-color palette** (excluding solid white placeholders at the end of the sheet):
1. **Black** `(0, 0, 0)`: Serves as the background for most tiles, representing transparency in sprites and floor details in background tiles.
2. **Blue** `(46, 55, 174)`: Serves as the primary color for walls, generator details, and parts of the player/monsters.
3. **Red** `(201, 99, 99)`: Serves as the detail color for stairs, money (dollar sign), keys, arrows, and player clothing.
4. **Light Blue/Gray** `(215, 223, 240)`: Serves as the highlight/face color for monsters and items.

### Mapping to GameBoy Palette Indices
On the GameBoy, tiles must be converted to 2bpp (2 bits per pixel) format, where each pixel is represented by a color index from `0` to `3`. We map the original colors to indices based on their relative brightness (luminance):
- **Index 0 (White / Lightest)** $\leftarrow$ Light Blue/Gray `(215, 223, 240)`
- **Index 1 (Light Gray / Medium-Light)** $\leftarrow$ Red `(201, 99, 99)`
- **Index 2 (Dark Gray / Medium-Dark)** $\leftarrow$ Blue `(46, 55, 174)`
- **Index 3 (Black / Darkest)** $\leftarrow$ Black `(0, 0, 0)`

---

## 2. Mathematical Downscaling Algorithms Design
Downscaling a 16x16 grid to an 8x8 grid represents a **2x reduction** in each dimension. Each 2x2 block in the original tile maps to a single pixel in the downscaled tile.

We designed and implemented three distinct downscaling pipelines in Python:

### A. Nearest-Neighbor (NN) Downscaling
- **Mechanism**: For each 2x2 block, we sample only the top-left pixel.
- **Limitations**: Severe aliasing. Since pixel-art outlines and details are often only 1 or 2 pixels wide, they frequently align poorly with the sampling grid, causing thin lines to be dropped entirely (gaps) or rendered asymmetrically.

### B. Box Majority Downscaling (with Dark Preference)
- **Mechanism**: We count the frequency of each color index within each 2x2 block. The majority color wins. Ties are broken in favor of the darker color (higher index, i.e., Black).
- **Limitations**: While better at capturing general shapes, it suffers from **foreground erosion**. For example, in a 2x2 block where a 2-pixel-wide Red foreground line sits on a Black background, we have 2 Red pixels and 2 Black pixels. The majority-vote tie-breaker favors Black, completely erasing the foreground detail. This causes thin strokes (like the bottom vertical lines of the dollar sign) to vanish.

### C. Font-Hinting inspired Downscaling
To solve the limitations of standard algorithms, we designed a pipeline inspired by digital typography font-hinting, incorporating three core principles:
1. **Tile-Specific Feature Weights**:
   Instead of a static tie-breaker, we assign weights to colors dynamically based on the tile type.
   - For **Sprites & Foreground Items** (Player, Monsters, Key, Money): The Black background (3) represents transparency/fill, while colors 0, 1, and 2 represent the active shape. We prioritize foreground colors in ties using weights `[2.0, 2.0, 2.0, 1.0]`. If a block has 2 foreground pixels and 2 background pixels, the foreground wins, preventing the sprite from shrinking or breaking.
   - For **Wall & Door Backgrounds**: Black (3) represents the mortar/cracks (structural details) and Blue (2) is the brick face. Here, Black is the detail we want to preserve. We use weights `[1.0, 1.0, 1.5, 2.5]`, ensuring cracks remain continuous.
   - For the **Dollar Sign ($)**: The Red (1) curve and vertical lines are critical. We use extreme weights `[1.0, 3.1, 1.0, 1.0]`, ensuring even a single Red pixel in a block is preserved if it forms part of a stroke.
2. **Symmetry-Aware Grid Snapping**:
   Symmetrical sprites (like the Player or Golem) can look deformed if one side downscales differently. We programmatically detect left-right symmetry in the 16x16 tile. If a tile is symmetric, we combine the pixel counts of symmetric 2x2 blocks on the left and right, make a joint decision, and mirror the result. This guarantees **perfect mathematical symmetry** in the 8x8 tile.
3. **Stroke-Continuity Hinting**:
   For glyph-like structures like the dollar sign, we add an explicit continuity constraint: if the vertical strokes at column 2 and 4 are active on row 6, they are programmatically extended to row 7. This prevents the vertical strokes from being cut off at the bottom.

---

## 3. Side-by-Side Text Comparisons of Critical Tiles
Below are the exact, verifiable text representations of the downscaled tiles generated by our Python script.
- `.` represents Light Blue/Gray (Color 0)
- `B` represents Red (Color 1)
- `R` represents Blue (Color 2)
- `K` represents Black (Color 3)

### Tile 1: Wall (Faithful Reduction of the Maze Pattern)
```
Original (16x16)   | NN (8x8) | Maj (8x8) | Hint (8x8)
-------------------+----------+----------+----------
RRRRRRRRRRRRRRRR   | RRRRRRRR | RRRRRRKR | RRRRRRKR
RRRRRRRRRRRRKKRR   | RKRKRRKR | RKRKRKKR | RKRKRKKR
RRKKRRKKRRRRKKRR   | RRKRRKRR | RRKRRKKR | RRKRRKKR
RRKKRRKKRRKKRRRR   | RRRRKRKR | RRRRKRKR | RRRRKRKR
RRRRKKRRRRKKRRRR   | RRRKRRRR | RKRKRRRR | RKRKRRRR
RRRRKKRRRRRRKKRR   | RKRRRKRR | RKKRRKRR | RKKRRKRR
RRRRRRRRKKRRKKRR   | RRKRKRKR | RKKRKRKR | RKKRKRKR
RRRRRRRRKKRRRRRR   | RKRRRRRR | RKRRRRRR | RKRRRRRR
```
- **Analysis**: Nearest-Neighbor (NN) drops many black pixels, leaving large gaps and breaking the woven diagonal pattern. Both Majority and Font-Hinted successfully preserve the full continuity of the diagonal black mortar lines, providing a beautiful, faithful reduction of the original 16x16 maze wall pattern.

### Tile 7: Money/Gold (The Dollar Sign $)
```
Original (16x16)   | NN (8x8) | Maj (8x8) | Hint (8x8)
-------------------+----------+----------+----------
KKKKBBKKBBKKKKKK   | KKBKBKKK | KKBKBKKK | KBBBBBBK
KKBBBBBBBBBBBBKK   | BBBBBBBK | BKBKBKBK | BBBBBBBK
BBBBBBBBBBBBBBKK   | BKBKBKKK | BKBKBKKK | BKBKBKKK
BBKKBBKKBBKKBBKK   | BBBBBBKK | KBBBBBKK | BBBBBBBK
BBKKBBKKBBKKKKKK   | KKBKBKBK | KKBKBKBK | KKBKBKBK
BBKKBBKKBBKKKKKK   | KKBKBKBK | KKBKBKBK | BKBKBKBK
BBBBBBBBBBBBKKKK   | BBBBBBBK | BBBBBBKK | BBBBBBBK
KKBBBBBBBBBBBBKK   | KKBKBKKK | KKKKKKKK | KKBKBKKK
```
- **Analysis**: 
  - **NN** produces a very thin S-curve with gaps on rows 3 and 5.
  - **Majority** completely erases the bottom vertical strokes (row 7 is all `KKKKKKKK`), leaving the dollar sign cut off.
  - **Font-Hinted** produces an exceptionally clear and bold dollar sign ($). The S-curve is completely continuous (cols 0 and 6 are preserved), and the vertical strokes at cols 2 and 4 are perfectly preserved and run all the way from row 0 to row 7.

### Tile 24: Player Down (No Gaps, Perfect Symmetry)
```
Original (16x16)   | NN (8x8) | Maj (8x8) | Hint (8x8)
-------------------+----------+----------+----------
KKKKKKRRRRKKKKKK   | KKKRRKKK | KKKRRKKK | KKKRRKKK
KKKKKKRRRRKKKKKK   | KKKKKKKK | KKKKKKKK | KKKBBKKK
KKKKKKKKKKKKKKKK   | KKBBBRKK | KKRBBRKK | KKRBBRKK
KKKKKKBBBBKKKKKK   | KKKBBKKK | KKKBBKKK | KRKBBKRK
KKKKBBBBBBRRKKKK   | KKKBBKKK | KKKBBKKK | KBBBBBBK
KKKKRRBBBBRRKKKK   | KKKKKKKK | KKKKKKKK | KKRKKRKK
KKKKKKBBBBKKKKKK   | KKRKKRKK | KKRKKRKK | KKRKKRKK
KKRRKKBBBBKKRRKK   | KKKKKKKK | KKKKKKKK | KRKKKKRK
```
- **Analysis**:
  - **NN & Majority**: The player is literally cut in half! Row 1 and Row 5 are completely empty (`KKKKKKKK`), leaving the head, body, and feet floating as disconnected segments. In addition, NN is asymmetrical on row 2 (`KKBBBRKK`).
  - **Font-Hinted**: By prioritizing foreground colors in ties, the body is connected to the head (row 1 `KKKBBKKK`) and to the legs (row 5 `KKRKKRKK`). The player is a single, continuous, highly recognizable figure. Furthermore, left-right symmetry is **perfectly preserved** across every single row.

---

## 4. Synthesis & Recommendation
The **Font-Hinting inspired Downscaling** algorithm is the clear winner. It outperforms standard downscaling techniques across all dimensions:
1. **Fidelity to Original Patterns**: It preserves the exact connectivity of the diagonal wall cracks and the dollar sign S-curve.
2. **Visual Continuity**: It prevents the classic "pixel disintegration" effect where sprites are sliced into floating pieces due to grid alignment.
3. **Glyph Recognition**: It maintains key structural components (like vertical strokes) of text-like sprites.
4. **Professionalism**: It guarantees mathematical symmetry for symmetric characters, eliminating lopsided or distorted renderings.

### Actionable Next Steps for Implementer
1. Integrate the `downscale_hinted` algorithm from `downscale_graphics.py` directly into the GameBoy asset build pipeline.
2. The python script can be run as part of the asset build step to automatically convert `strike_original.png` into the `tiles.c` file for compilation.
3. The generated sheets `mathematical_tiles_hinted_dmg.png` and `comparison_grid.png` are stored in the agent directory `/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/.agents/explorer_graphics_m2/` for immediate visual inspection.
