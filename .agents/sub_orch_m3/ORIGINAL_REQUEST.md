# Original User Request

## Initial Request — 2026-06-20T22:22:50Z

You are the Milestone 3 Sub-orchestrator (archetype: teamwork_preview_orchestrator) for the Dandy Dungeon custom 2D level compression project.

Your working directory is: /usr/local/google/home/jackpal/Developer/Dandy-Dungeon/.agents/sub_orch_m3
Your parent is: 6949b863-eafb-4fae-bca8-2c92c6ca9449 (the Project Orchestrator)
The global PROJECT.md is at: /usr/local/google/home/jackpal/Developer/Dandy-Dungeon/PROJECT.md
The comparative compression report defining the selected scheme is at: /usr/local/google/home/jackpal/Developer/Dandy-Dungeon/.agents/sub_orch_m2/COMPARATIVE_COMPRESSION_REPORT.md

Your mission is to execute Milestone 3: Implement 2D Compressor & Decompressor.

### Objectives:
1. **Implement the Python 2D Compressor (`tools/convert_levels.py`)**:
   - Update `tools/convert_levels.py` to compress all 26 levels from `dandy-js/levels.js`.
   - Apply **Edge Wall Elision**: Omit the outer 176 border walls of the 60x30 map, compressing only the inner 58x28 grid (1,624 tiles).
   - Apply **Scheme B2 (Variable-Bit-Width) prefix coding** on the inner grid:
     - Space (Empty Floor, ID 0) -> `0` (1 bit)
     - Wall (Solid, ID 1) -> `10` (2 bits)
     - Other tiles (ID 2 to 15) -> `11` + `xxxx` (6 bits total, where `xxxx` is the 4-bit tile ID).
   - Pack the bits MSB-first into bytes, pad the final byte of each level to byte boundary, and generate the C source/header files (`src/levels.c` and `src/levels.h`) containing the compressed level arrays and the `dandy_levels` pointer array.
   - Remove the temporary first-5-levels limit so all 26 levels are output.

2. **Implement the GBDK C Decompressor (`src/dandy_core.c`)**:
   - Modify `dandy_load_level(uint8_t level_idx)` in `src/dandy_core.c` (or in a dedicated module) to implement the designed Scheme B2 decompressor:
     - Initialize the 1,800-byte `dandy_map` buffer with Wall tiles (ID 1) using a fast `memset(dandy_map, 1, 1800)`.
     - Decode the compressed bitstream from `dandy_levels[level_idx]` directly into the inner 58x28 area of `dandy_map`, writing row-by-row, column-by-column at coordinates `y` from 1 to 28 and `x` from 1 to 58 (memory offset: `y * 60 + x`).
     - **Optimization**: If a tile is decoded as Wall (prefix `10`), do nothing and skip the map write (since the map is already pre-filled with Wall tiles). This saves ~32% of all write operations.
     - **Bounds Safety**: Ensure the write offset `y * 60 + x` is strictly bounds-safe. Include the active runtime guards developed in Milestone 1/3 E2E.
     - **Optimized for Z80**: Write clean, standard GBDK C that avoids heavy arithmetic or deep recursion.

3. **Verify Decompression Fidelity & Compilation**:
   - Integrate the new Edge Wall Elision and Scheme B2 decompressor layers into `tools/verify_compression.py`'s modular round-trip pipeline.
   - Run `tools/verify_compression.py` to assert:
     - 100% bit-for-bit round-trip decompression fidelity for all 26 levels.
     - The ROM compiles successfully with zero warnings and errors.
     - The output `bin/dandy.gb` is exactly 32,768 bytes.
     - The active code/data segments in `dandy.map` are measured and reported (targeting < 28KB).
   - Run the E2E test suite against the compiled core engine to ensure full gameplay correctness.

Apply the Orchestrator Procedure:
- Assess the complexity. Since this is an implementation phase, spawn specialized subagents (explorers, workers, reviewers, challengers, auditors) to perform the changes and verify them.
- Author your own BRIEFING.md, SCOPE.md, progress.md, and plan.md in your working directory.
- Ensure the worker runs builds and documents the commands and results.
- **MANDATORY INTEGRITY WARNING**: Include the DO NOT CHEAT warning verbatim in the Worker's dispatch prompt.
- When done, write handoff.md and send a completion message to the parent.

Please initialize your workspace and start immediately. Report back when you have initialized your plan.
