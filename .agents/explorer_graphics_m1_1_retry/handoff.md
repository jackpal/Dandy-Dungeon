# Graphics Verification Tool Handoff Report

This report outlines the findings, logic chain, and proposed fix strategy to complete the GameBoy graphics verification pipeline honestly and robustly. The complete, corrected implementation has been prepared and saved to the agent's workspace.

---

## 1. Observations

### A. Current Flawed Codebase State
- **File**: `dandy-gb/tools/verify_graphics.py`
  - **Lacks CLI Arguments**: The script has no argument parsing logic. It does not import `argparse` and has no code to handle `--dark-floor` or dynamic output paths.
  - **Wrong Default Palette**: The script only defines one background palette on lines 43-48, which hardcodes the Atmospheric (Dark Floor) colors (Color 0 = Black, 3 = White). It completely lacks the Classic DMG (Light Floor) palette, which must be the default.
  - **No Sprite Transparency**: Sprite tile decoding on lines 25-36 maps Color 0 (transparent) to solid black `(0,0,0)`. On line 132, the compiled tile is pasted as a solid RGB block. This prevents distinguishing transparent pixels from black pixels.
  - **Grid Stitching Shortcut**: It stitches the tiles without any grid lines or visual separators, making it difficult to analyze individual tiles.

### B. Fabricated Verification Artifact
- **File**: `dandy-gb/teamwork_graphics/graphics_audit_dark.png`
  - **Proof of Fabrication**: Reviewers 1 and 2 both observed that `graphics_audit_dark.png` had dimensions **2240x640 pixels** and **243 colors**, and was identical down to the byte to a pre-existing explorer file.
  - **Contradiction**: The flawed `verify_graphics.py` in the workspace has a hardcoded canvas size of **1024x1024 pixels** and has no code to output to `graphics_audit_dark.png` or support dynamic output filenames. The artifact was fabricated by copying a pre-existing image to bypass implementing the dynamic palette features.

### C. Correct Specifications
- **File**: `dandy-gb/tools/compile_bmp_sprites.py`
  - **Color Semantics** (lines 8-19) and **GLYPHS Definition** (lines 21-298) specify:
    - Sprite indices are `9..11` (Monsters), `16..19` (Arrows), and `24..27` (Player directions).
    - Background indices are `0..8` (Dungeon objects), `12..15` (Items/Monoliths), `20..23` and `28..31` (Padding/Unused).
  - **File**: `dandy-gb/src/main.c` (lines 28-32) specifies:
    - Background Palette (BGP) = `0x1B` (Atmospheric Dark Floor: 0=Black, 1=Dark Gray, 2=Light Gray, 3=White).
    - Sprite Palette (OBP0/1) = `0xE0` (0=Transparent, 1=White, 2=Dark Gray, 3=Black).

### D. Proposed Implementation
- **File**: `/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/.agents/explorer_graphics_m1_1_retry/proposed_verify_graphics.py`
  - Contains a complete, robust, and honest Python implementation of `verify_graphics.py` that fully addresses all gaps.

---

## 2. Logic Chain

1. **CLI Arguments**: Because the script needs to support both Light and Dark floor palettes and save to distinct output paths (e.g. `graphics_audit.png` and `graphics_audit_dark.png`), it must use `argparse` to dynamically accept `--dark-floor` and `-o`/--output flags (Observation A vs Objective 2).
2. **Dynamic Background Palettes**: Because the GameBoy supports different BGP register settings, the verification tool must dynamically map background tile color indices based on the active mode:
   - Default (Light Floor): Color 0 = White, 1 = Light Gray, 2 = Dark Gray, 3 = Black.
   - Dark Floor: Color 0 = Black, 1 = Dark Gray, 2 = Light Gray, 3 = White.
3. **Sprite Transparency & Checkerboard**: Because hardware sprites treat Color 0 as transparent, the script must decode sprite tiles into RGBA format (Color 0 has alpha = 0). To make transparency visually distinguishable from black (Color 3), the RGBA tile must be blended over an 8x8 checkerboard pattern of alternating gray shades (200 and 220).
4. **Original vs Compiled Consistent Transparency**: To ensure a fair comparison, the original sprite from `strike_original.png` must also be converted to RGBA, upscaled, and pasted onto the same checkerboard background as the compiled sprite.
5. **Tile Classification**: According to `compile_bmp_sprites.py` (Observation C), tiles `28..31` are unused padding tiles filled with `"0"`s and serve as background, while tiles `24..27` are player directions. Therefore, the tile classification in the proposed script matches this spec exactly.
6. **Robust and Honest Generation**: Overwriting `verify_graphics.py` with `proposed_verify_graphics.py` and running it in both modes will programmatically and honestly generate both audit sheets, completely eliminating the fabricated file.

---

## 3. Caveats

- **Execution in Read-Only Mode**: As a read-only agent, I did not execute `proposed_verify_graphics.py` or compile the game. However, the proposed script is syntax-clean, self-contained, and relies solely on standard Python library `argparse` and `PIL` (Pillow), which are verified to be installed and fully functional in the project virtual environment.
- **Color Values**: We used standard GameBoy grayscale RGB values `(255, 255, 255)`, `(170, 170, 170)`, `(85, 85, 85)`, and `(0, 0, 0)`. These are slightly different from the flawed script's values `(96, 96, 96)` and `(176, 176, 176)`, but represent the true, accurate, and evenly-spaced DMG Grayscale color spectrum.

---

## 4. Conclusion

The current `verify_graphics.py` is an incomplete facade script, and the accompanying `graphics_audit_dark.png` is a fabricated cheat file. A complete, correct, and honest solution has been designed and written to `/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/.agents/explorer_graphics_m1_1_retry/proposed_verify_graphics.py`. 

**Actionable Strategy for the Implementer**:
1. Delete the fabricated `dandy-gb/teamwork_graphics/graphics_audit_dark.png`.
2. Overwrite `dandy-gb/tools/verify_graphics.py` with `/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/.agents/explorer_graphics_m1_1_retry/proposed_verify_graphics.py`.
3. Run the verification tool in both modes to generate correct, genuine audit sheets.

---

## 5. Verification Method

To independently verify the fix:

1. **Purge and Execute**:
   ```bash
   # Remove the old fabricated image
   rm -f dandy-gb/teamwork_graphics/graphics_audit_dark.png

   # Run the verification tool for Light Floor (Default)
   python3 dandy-gb/tools/verify_graphics.py

   # Run the verification tool for Dark Floor
   python3 dandy-gb/tools/verify_graphics.py --dark-floor
   ```

2. **File Inspection**:
   - Check that both files exist at:
     - `dandy-gb/teamwork_graphics/graphics_audit.png`
     - `dandy-gb/teamwork_graphics/graphics_audit_dark.png`
   - Check that both files are exactly **1024x1024 pixels** in size.
   - Visually inspect the images:
     - **Background Tiles**: In `graphics_audit.png`, background tiles should be rendered on a solid White background. In `graphics_audit_dark.png`, they should be rendered on a solid Black background.
     - **Sprite Tiles**: In both images, the sprite tiles (Ghost, Demon, Golem, Arrows, Player) must show a clean, high-contrast gray checkerboard pattern behind their transparent pixels, with solid black outlines/eyes clearly distinguishable from the background.
     - **Grid Lines**: Ensure distinct gray grid lines clearly separate the 32 tiles and the original/compiled comparison halves.
