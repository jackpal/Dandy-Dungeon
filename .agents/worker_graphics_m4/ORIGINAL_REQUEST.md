## 2026-06-21T01:23:24Z

You are a teamwork_preview_worker agent.
Your working directory is: /usr/local/google/home/jackpal/Developer/Dandy-Dungeon/.agents/worker_graphics_m4/
Your mission is to implement Milestone 4 (Palette & Sprite Integration) based on the detailed plans and code patches prepared by the Explorers.

Please load and follow the software-engineering domain skill at:
  /google/src/files/head/depot/google3/learning/gemini/agents/skills/software_engineering/SKILL.md

### Step-by-Step Implementation Guide

1. **Read the Explorer Reports**:
   Read the detailed analysis and design reports from the three Explorers:
   - Explorer 1 (Engine/Palettes): `/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/.agents/explorer_graphics_m4_1/analysis.md`
   - Explorer 2 (Compiler/Overrides): `/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/.agents/explorer_graphics_m4_2/analysis.md`
   - Explorer 3 (Build/Verification): `/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/.agents/explorer_graphics_m4_3/analysis.md`

2. **Modify the Graphics Compiler and Overrides**:
   - Update `dandy-gb/downscale/overrides.py` to define the Classic DMG floor tile with dots at (2,2) and (6,5) for Tile 0.
   - Update `dandy-gb/downscale/selector.py` to configure Tile 0 as `"manual"`.
   - Update `dandy-gb/downscale/compiler.py` to generate the `#ifdef USE_BLACK_FLOOR` preprocessor block in `src/tiles.c` for Tile 0 (all 0s for black floor, dots for classic floor).

3. **Modify the Verification Tools & Tests**:
   - Update `dandy-gb/tools/verify_graphics.py` to make `parse_tiles_c` preprocessor-aware by emulating a preprocessor step before regex matching.
   - Update `dandy-gb/tests/test_graphics_pipeline.py` to make `test_independent_tile_decoding` preprocessor-aware and test both modes.
   - Update `dandy-gb/tests/verify_emulator.py` to support overriding the `ROM_PATH` via environment variables.

4. **Modify the GameBoy C Engine**:
   - Update `dandy-gb/src/main.c` to conditionally set `BGP_REG`, `OBP0_REG`, and `OBP1_REG` based on `#ifdef USE_BLACK_FLOOR`.
   - Update `dandy-gb/src/gameboy_hal.c` to implement the consistent Black HUD scoreboard background and text drawing across both modes (refer to Explorer 1's Proposal 5.3).

5. **Modify the Makefile**:
   - Update `dandy-gb/Makefile` to support:
     - Dynamic `ROM_NAME`, `OBJ_DIR`, and `CFLAGS` based on the `USE_BLACK_FLOOR` variable.
     - A `dark` target that runs `$(MAKE) USE_BLACK_FLOOR=1 all`.
     - Updating the `clean` target to clean both `obj` and `obj_dark`.
     - Updating the `test_emu` target to run E2E emulator tests on both `bin/dandy.gb` and `bin/dandy_dark.gb`.

6. **Build and Verify**:
   - Run `make sprites` to regenerate `src/tiles.c` and `src/tiles.h`.
   - Run `make test` to verify that all unit tests pass.
   - Compile both ROMs: `make clean && make` and `make dark`. Verify that both `bin/dandy.gb` and `bin/dandy_dark.gb` compile successfully with 0 warnings and 0 errors.
   - Run the E2E emulator tests: `make test_emu`. Verify that both test runs pass.
   - Generate both audit sheets by running `tools/verify_graphics.py` and `tools/verify_graphics.py --dark-floor`. Verify that `teamwork_graphics/graphics_audit.png` (Classic) and `teamwork_graphics/graphics_audit_dark.png` (Dark) are generated perfectly.

MANDATORY INTEGRITY WARNING — include this verbatim:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A Forensic Auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Deliver a detailed handoff report when you are finished.
