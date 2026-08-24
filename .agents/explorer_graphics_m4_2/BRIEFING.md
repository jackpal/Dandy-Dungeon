# BRIEFING — 2026-06-21T01:23:12Z

## Mission
Perform a thorough technical exploration for Milestone 4 (Palette & Sprite Integration) of the graphics downscaling pipeline, focusing on Graphics Compiler & Overrides.

## 🔒 My Identity
- Archetype: teamwork_preview_explorer
- Roles: Read-only investigation, analyze problems, synthesize findings, produce structured reports
- Working directory: /usr/local/google/home/jackpal/Developer/Dandy-Dungeon/.agents/explorer_graphics_m4_2/
- Original parent: 70dff078-9042-4953-9690-351507da368f
- Milestone: Milestone 4 (Palette & Sprite Integration)

## 🔒 Key Constraints
- Read-only investigation — do NOT implement.
- Write files only to own working directory: /usr/local/google/home/jackpal/Developer/Dandy-Dungeon/.agents/explorer_graphics_m4_2/.
- Code-only network mode: no external web or services, only code_search and local file tools.
- Use Handoff Protocol and write handoff.md and analysis.md.

## Current Parent
- Conversation ID: 70dff078-9042-4953-9690-351507da368f
- Updated: 2026-06-21T01:23:12Z

## Investigation State
- **Explored paths**:
  - `dandy-gb/downscale/overrides.py`
  - `dandy-gb/downscale/selector.py`
  - `dandy-gb/downscale/compiler.py`
  - `dandy-gb/tools/downscale_sprites.py`
  - `dandy-gb/tools/verify_graphics.py`
  - `dandy-gb/tests/test_graphics_pipeline.py`
  - `dandy-gb/tests/test_graphics_selector.py`
  - `dandy-gb/tests/test_downscale_sprites.py`
- **Key findings**:
  - Almost all background tiles and sprites can be inverted using hardware palette register swaps (BGP, OBP0/1), keeping their 2bpp pixel data identical.
  - Tile 0 (floor) is the sole exception: Classic DMG requires subtle texture dots (value 1) on a White background (value 0) at (2,2) and (6,5). Atmospheric Dark requires solid Black (all 0s).
  - Propose wrapping Tile 0 in `#ifdef USE_BLACK_FLOOR` / `#else` / `#endif` inside the array initializer in `src/tiles.c` to conditionally compile the correct layout.
  - Discovered that adding `#ifdef` blocks inside `src/tiles.c` breaks the naive parsers in `verify_graphics.py` and `test_graphics_pipeline.py` (which expect exactly 512 raw tokens).
  - Designed a simple Python preprocessor emulation to resolve this collision and keep all tools and tests working.
- **Unexplored areas**: None

## Key Decisions Made
- Routed Tile 0 to `"manual"` in `selector.py` to ensure exact texture dot coordinates.
- Placed `#ifdef` blocks directly inside the array initializer in `src/tiles.c` to prevent duplicating the other 31 tiles.
- Emulated C preprocessor in Python tools and tests to prevent parser failures.

## Artifact Index
- `/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/.agents/explorer_graphics_m4_2/ORIGINAL_REQUEST.md` — Original request text.
- `/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/.agents/explorer_graphics_m4_2/analysis.md` — Detailed exploration findings and python modifications.
- `/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/.agents/explorer_graphics_m4_2/handoff.md` — Structured 5-component handoff report.
