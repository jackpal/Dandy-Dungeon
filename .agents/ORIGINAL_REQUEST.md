# Original User Request

## Initial Request — 2026-06-20T21:47:49Z

Research, design, and implement a highly efficient custom 2D compression algorithm for Dandy Dungeon's 26 levels. The goal is to shrink the ROM footprint of the level database sufficiently to compile the entire game (engine + graphics + compressed levels) into a single, flat 32KB GameBoy ROM (no bank-switching MBC chip required), with a target total ROM size of less than 28 KB.

Working directory: ~/teamwork_projects/dandy_compression
Integrity mode: development

## Requirements

### R1. Custom 2D Level Compressor (Python 3)
Implement a Python 3 compression compiler (integrated into tools/convert_levels.py) that analyzes the 26 levels from dandy-js/levels.js. It must exploit 2D spatial coherence (e.g., line-to-line similarities, 2D run-length-encoding, dictionary-based tile structures, or quadtree-like subdivision) to compress the level maps far more efficiently than the current 1D RLE scheme. The output must be formatted as C header/source files.

### R2. Custom 2D Level Decompressor (GBDK C)
Implement a highly optimized C decompression function in the GameBoy engine (src/dandy_core.c or a dedicated module). The decompressor must decode the custom compressed level data on-the-fly directly into the dandy_map RAM buffer (1800 bytes) on level load. It must:
1. Use zero dynamic RAM allocations (malloc/free), operating within the GameBoy's strict 8KB WRAM limit.
2. Be highly optimized for the 8-bit Z80/GB CPU (avoiding heavy 32-bit math, floating-point operations, or deep recursive call stacks).
3. Execute extremely quickly to ensure instantaneous level transitions.

### R3. Flat 32KB ROM Compilation (No-MBC)
Revert the build system and memory map from the 4-bank 64KB MBC1 layout back to a single, flat 32KB ROM (no-MBC, Bank 0 and Bank 1 only). The compiled ROM must contain all engine code, default text fonts, graphics assets, sound driver, and the new compressed level data.

### R4. Automated Verification Script
Create a Python verification script (tools/verify_compression.py) that programmatically validates the entire pipeline:
1. Decompression Fidelity: Compresses all 26 levels, decompresses them back in Python, and asserts they are 100% bit-for-bit identical to the raw original levels.
2. GameBoy ROM Compilation: Automatically cleans the build and compiles the GameBoy ROM using the local GBDK compiler (lcc).
3. Strict Size Budget: Asserts that the compiled bin/dandy.gb size is exactly 32,768 bytes, and the actual active code+data segment size in the map file is less than 28,672 Bytes (28 KB), ensuring safety headroom.

## Acceptance Criteria

### Correctness & Fidelity
- The automated verification script runs successfully and reports 100% bit-for-bit identity for all 26 levels.
- Compiling the GameBoy ROM completes with zero errors and zero warnings.

### ROM Size Constraints
- The compiled GameBoy ROM bin/dandy.gb is a flat, single-bank 32KB ROM (no bank-switching or MBC1 configurations).
- The compiled ROM file size is exactly 32,768 bytes.
- The total active code and data segments in the linker map file sum to less than 28,672 bytes (28 KB), leaving at least 4KB of free ROM headroom.

### Performance & Memory
- The C decompressor uses only static/global RAM buffers (specifically, writing directly into dandy_map) and requires zero dynamic heap allocations.
- The decompressor is written in standard, clean GBDK C without heavy emulated arithmetic, ensuring optimal execution speed on 8-bit hardware.

## Follow-up — 2026-06-21T00:18:01Z

Research, design, and implement a mathematically sound, historically faithful graphics conversion pipeline to downscale Dandy Dungeon's original 16x16x4 color tiles to 8x8x4 tiles/sprites for the GameBoy port. The pipeline must stay strictly faithful to the original artwork (without arbitrary changes) and preserve thin details and symmetry, leveraging techniques inspired by font-hinting and small-scale typography literature.

Working directory: /usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb/teamwork_graphics
Integrity mode: demo

## Requirements

### R1. Font-Hinting Inspired Downscaling Pipeline (Python 3)
Implement a Python 3 graphics compiler (integrated into the build system) that reads the original 16x16x4 color `strike_original.png` asset and downscales it to 8x8x4 tiles. The pipeline must:
1. Research and apply concepts from font-hinting and type-rendering literature (rendering vector/large glyphs to extremely small pixel grids).
2. Implement mathematical algorithms (e.g. sub-pixel grid alignment, edge/feature weight preservation, or directional hinting markers) to ensure that thin 1px lines, outlines, and symmetry are preserved.
3. Stay strictly faithful to the original artwork concepts (e.g. the wall tile must be a faithful reduction of the original 16x16 wall pattern, and must NOT be changed to a different pattern like bricks; the money tile must remain a clear dollar sign).

### R2. Comparative Asset Generation & Selection
In parallel with mathematical downscaling, the pipeline must:
1. Explore redrawing the 8x8 tiles programmatically or generating them to preserve the original glyph concepts (the gold `$`, the key silhouette, the flask, the monster/player visages).
2. Systematically compare the mathematically downscaled tiles against the redrawn/regenerated tiles.
3. Select the highest-fidelity result for each individual tile to form the final 32-tile set.

### R3. GameBoy Palette & Sprite Transparency Integration
The final 8x8 tiles must be packed into GBDK's standard 16-byte 2bpp binary format, outputting `src/tiles.c` and `src/tiles.h`. The team must configure the GameBoy's hardware palette registers in `src/main.c` (`BGP_REG`, `OBP0_REG`, `OBP1_REG`) to perfectly handle:
1. **Background Tiles (BKG):** Empty floor corridors (`Tile 0`) and empty tile borders must render as a solid Black void. Walls and static items must render in high-contrast Dark Gray/Light Gray/White.
2. **Sprite Tiles (OBJ):** Sprites (player, monsters, arrows) must render with perfect transparency (no solid square background blocks), a brilliant bright White body, Dark Gray details, and sharp Black outlines.

### R4. Automated Build & E2E Verification
Integrate the graphics compiler script into the project's `Makefile`. Compiling the project must build the GameBoy ROM `bin/dandy.gb` successfully with zero errors and zero warnings, and the compiled ROM must pass the existing PyBoy E2E automated emulator test suite (`tests/verify_emulator.py`).

---

## Acceptance Criteria

### 1. Build & E2E Correctness
- [ ] Compiling the project via the local GBDK compiler (`lcc`) completes with zero errors and zero warnings.
- [ ] The compiled GameBoy ROM size is exactly 32,768 bytes (flat 32KB cart).
- [ ] Running the E2E automated emulator test suite (`verify_emulator.py`) passes successfully with 100% correctness.

### 2. High-Fidelity Graphics Audit (5/5 Pass)
The team must write a verification script (`tools/verify_graphics.py`) that renders a visual comparison sheet (`graphics_audit.png`) showing all 32 original 16x16 tiles side-by-side with the new 8x8 tiles (upscaled 8x using nearest-neighbor for crisp viewing). An independent auditor agent must review the comparison sheet and certify that the graphics pass all 5 points of the following quality rubric:
- [ ] **C1. Conceptual Faithfulness:** All tiles remain strictly faithful to the original 16x16 artwork. The wall tile is a faithful reduction of the original wall pattern (not changed to bricks), the money is a clear dollar sign ($), and the key/flask/monsters have correct, recognizable shapes.
- [ ] **C2. Detail & Outline Integrity:** Thin 1px outlines, character feet, and borders are 100% complete and sharp. There is zero clipping, zero disconnected lines, and zero missing rows (e.g. the bottom step of the stairs \"U\" is fully drawn).
- [ ] **C3. Symmetry:** Naturally symmetrical tiles (stairs, doors, shields, keys, dollar signs) are perfectly symmetrical on the 8x8 pixel grid.
- [ ] **C4. Contrast & Readability:** The player sprite has a brilliant, bright white body and a bold black outline that pops clearly against the black floor. Walls are instantly distinguishable from empty floor corridors and characters.
- [ ] **C5. Transparency & Borders:** Sprite-only tiles (player, monsters, flying arrows) are completely free of any solid square background borders when rendered in the gameplay viewport.

## Follow-up — 2026-06-21T00:23:12Z

High-Priority Aesthetic & Architectural Update:

The user has approved our first-principles graphics plan with a critical decision:
1. Make the **Classic DMG Light/White Floor the default rendering mode** for the game.
2. Provide the **Atmospheric Dark/Black Floor as a compile-time configuration option** (e.g. via a `#define USE_BLACK_FLOOR` or similar macro in the source code).

Please update the project plan, BRIEFING.md, and instruct the Project Orchestrator (d71284e8-6d12-48b1-bcfc-faa3be95a040) and sub-orchestrators to implement this architecture:

### A. Default Mode: Classic DMG (Light/White Floor)
*   **Aesthetics:** Floor corridors are White, decorated with sparse, subtle Light Gray dots/tile-cracks to represent texture (similar to Zelda/Pokemon). Sprites (player, monsters) are dark silhouettes (Dark Gray bodies, Black outlines, White eyes) to stand out sharply against the white ground.
*   **BKG Palette (BGP):** Maps Color 0 -> White, 1 -> Light Gray, 2 -> Dark Gray, 3 -> Black (standard 0xE4).
*   **OBJ Palette (OBP0/1):** Maps Color 0 -> Transparent, 1 -> Dark Gray, 2 -> Light Gray, 3 -> Black (or similar to guarantee the dark silhouettes are crisp and readable).

### B. Optional Mode: Atmospheric (Dark/Black Floor)
*   **Aesthetics:** Floor corridors are solid Black. Sprites have bright White bodies, Dark Gray details, and Black outlines.
*   **BKG Palette (BGP):** Maps Color 0 -> Black, 1 -> Dark Gray, 2 -> Light Gray, 3 -> White (0x1B).
*   **OBJ Palette (OBP0/1):** Maps Color 0 -> Transparent, 1 -> White, 2 -> Dark Gray, 3 -> Black (0xE0).

### C. Implementation Requirements:
1.  **Macro-Conditioned Compilation:** The graphics compiler (tools/compile_bmp_sprites.py) and the hardware registers setup in src/main.c must dynamically switch their tile packing and palette configurations based on the compile-time macro.
2.  **Verification Audit:** Ensure the graphics verification script (tools/verify_graphics.py) and comparison sheet (graphics_audit.png) verify that the default Light Floor mode is visually stunning, sharp, and passes all C1-C5 criteria.
