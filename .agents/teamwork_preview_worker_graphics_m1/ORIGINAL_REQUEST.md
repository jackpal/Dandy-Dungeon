You are a Worker tasked with implementing the graphics extraction and verification pipeline for Milestone 1 of the Dandy Dungeon graphics conversion pipeline.

Your working directory is: /usr/local/google/home/jackpal/Developer/Dandy-Dungeon/.agents/teamwork_preview_worker_graphics_m1/

Please perform the following steps:
1. Read the scope document `/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/.agents/sub_orch_graphics_m1_gen2/SCOPE.md`.
2. Review the findings of the Explorers in:
   - `/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/.agents/teamwork_preview_explorer_graphics_m1_1/analysis.md`
   - `/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/.agents/teamwork_preview_explorer_graphics_m1_2/analysis.md`
   - `/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/.agents/teamwork_preview_explorer_graphics_m1_3/analysis.md`
3. Implement the extraction script:
   - Create the file `/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb/tools/extract_sprites.py`.
   - This script must read `/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-js/strike.js`, extract the base64 sprite sheet string assigned to `strike.src` (concatenated from multiple lines), decode it, and save it to `/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb/teamwork_graphics/strike_original.png`.
   - Ensure the script verifies that the output image is valid and has dimensions exactly 256x32 (the Explorers proved it is 256x32 containing 32 tiles, not 256x16).
4. Implement the verification script:
   - Create the file `/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb/tools/verify_graphics.py`.
   - This script must:
     a. Load `/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb/teamwork_graphics/strike_original.png`.
     b. Parse the 512-byte GBDK 2bpp tile array `dandy_tiles` from `/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb/src/tiles.c`.
     c. Decode the GBDK 2bpp format back to 8x8 pixels.
     d. Map the 2bpp color indices (0..3) to RGB colors using the standard hardware palettes:
        - Background tiles (indices 0..8, 12..15, 20..23, 28..31): 0 -> Black `(0,0,0)`, 1 -> Dark Gray `(96,96,96)`, 2 -> Light Gray `(176,176,176)`, 3 -> White `(255,255,255)`.
        - Sprite tiles (indices 9..11, 16..19, 24..27): 0 -> Transparent (draw as solid Black `(0,0,0)` in the audit sheet for contrast), 1 -> White `(255,255,255)`, 2 -> Dark Gray `(96,96,96)`, 3 -> Black `(0,0,0)`.
     e. Stitch a side-by-side comparison sheet:
        - Arrange the 32 tiles in a grid (e.g. 8 columns and 4 rows, or 4 columns and 8 rows).
        - For each tile, display the original 16x16 sprite on the left and the decoded 8x8 Game Boy tile on the right.
        - To make comparison clean, upscale the original 16x16 sprite 8x (to 128x128) and the Game Boy 8x8 tile 16x (to 128x128) using nearest-neighbor interpolation, making them the same size side-by-side. Or upscale original 4x (to 64x64) and Game Boy tile 8x (to 64x64). Ensure they are rendered side-by-side at a matched size.
        - Save the result as `/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb/teamwork_graphics/graphics_audit.png`.
5. Execute and verify the scripts using the local virtual environment Python interpreter:
   - Run: `dandy-gb/.venv/bin/python3 dandy-gb/tools/extract_sprites.py`
   - Run: `dandy-gb/.venv/bin/python3 dandy-gb/tools/verify_graphics.py`
   - Confirm that both run without errors.
6. Verify GBDK compilation:
   - Run `make clean && make` in `dandy-gb/`.
   - Ensure the build completes successfully with zero warnings/errors, and the ROM file `dandy-gb/bin/dandy.gb` is generated.
7. Verify that all output files exist, contain actual data, and match the requirements.
8. Write a detailed handoff report `handoff.md` in your working directory summarizing your actions, commands run, and verification results.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A Forensic Auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Use the skills:
- software-engineering: /google/src/files/head/depot/google3/learning/gemini/agents/skills/software_engineering/SKILL.md
- greenfield-development: /google/src/files/head/depot/google3/research/omega/teamwork/playbooks/greenfield_development/SKILL.md
