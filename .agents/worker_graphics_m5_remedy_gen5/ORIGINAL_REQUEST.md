## 2026-06-21T02:30:46Z

You are the teamwork_preview_worker (Worker) for Milestone 5 Graphics Remediation.
Your working directory is: `/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/.agents/worker_graphics_m5_remedy_gen5/`
Your task is to fix critical visual and mapping defects in the graphics conversion pipeline to resolve Reviewer 1's feedback:

1. Restore Wall Tile (Tile 1) to Diagonal Cross-Hatch:
   - The wall tile was incorrectly changed to a brick pattern, violating the requirement that it must remain a faithful reduction of the original cross-hatch/diagonal grid pattern.
   - Design:
     - In `dandy-gb/downscale/selector.py`, change the selection source for Tile 1 from `"mathematical"` to `"manual"`:
       `1: "manual",  # Wall`
     - In `dandy-gb/downscale/overrides.py`, implement a beautiful, tiling 8x8 diagonal cross-hatch pattern for Tile 1:
       ```python
       1: [
           "20002000",
           "02020202",
           "00200020",
           "02020202",
           "20002000",
           "02020202",
           "00200020",
           "02020202"
       ],
       ```

2. Fix Player Sprite Directions, Mapping, and Transparency:
   - The player sprites are currently mapped incorrectly in `overrides.py` (down is at 24, up at 25, left at 26, right at 27, and 28..31 are empty). Since the C engine expects Up at 24, Up-Right at 25, Right at 26, Down-Right at 27, Down at 28, Down-Left at 29, Left at 30, and Up-Left at 31, this caused the player to face the wrong directions or turn into solid black/gray blocks (which were mathematically downscaled empty padding).
   - Design:
     - In `dandy-gb/downscale/selector.py`, update tiles 28..31 to use `"manual"` overrides:
       `28: "manual",`
       `29: "manual",`
       `30: "manual",`
       `31: "manual"`
     - In `dandy-gb/downscale/overrides.py`, re-arrange the player sprites to align perfectly with the C engine's directional indices 24..31, and copy/draw the diagonal frames so they are beautiful and seamless:
       - `24`: `PLAYER_UP` (using the back of helmet/cape grid currently at 25)
       - `25`: `PLAYER_UP_RIGHT` (copy `PLAYER_RIGHT` grid)
       - `26`: `PLAYER_RIGHT` (using the right-facing shield grid currently at 27)
       - `27`: `PLAYER_DOWN_RIGHT` (copy `PLAYER_RIGHT` grid)
       - `28`: `PLAYER_DOWN` (using the front-facing visor grid currently at 24)
       - `29`: `PLAYER_DOWN_LEFT` (copy `PLAYER_LEFT` grid)
       - `30`: `PLAYER_LEFT` (using the left-facing shield grid currently at 26)
       - `31`: `PLAYER_UP_LEFT` (copy `PLAYER_LEFT` grid)
     - Double-check that all player sprite rows use color index `0` at the corners to ensure perfect GameBoy hardware sprite transparency (no solid square backgrounds).

3. Align Gold Dollar Sign (Tile 7) for Symmetry:
   - Make the gold dollar sign `$` (Tile 7) perfectly symmetrical and centered on the 8x8 grid to pass rubric point C3.
   - Design:
     - In `dandy-gb/downscale/overrides.py`, update Tile 7 to:
       ```python
       7: [
           "00020000", #     $     (Line top)
           "00222200", #   $$$$    (S top curve, perfectly centered)
           "02020000", #  $ $      (S left side + vertical line)
           "00222000", #   $$$     (S middle crossover, centered)
           "00020200", #     $ $   (Vertical line + S right side)
           "00222200", #   $$$$    (S bottom curve, perfectly centered)
           "00020000", #     $     (Line bottom)
           "00020000"  #     $     (Line bottom tail)
       ]
       ```

Verification steps you must perform:
- Run `make clean`.
- Run `make all` and `make dark` to verify compilation completes with zero errors and zero warnings.
- Run `make test` to regenerate the sprite/tile header files and comparison sheets (`teamwork_graphics/graphics_audit.png` and `graphics_audit_dark.png`).
- Run `make test_emu` to verify that all 176 unit tests and 4 emulator E2E tests pass.
- Write a detailed `changes.md` or `handoff.md` in your working directory summarizing:
  - The exact changes made to `selector.py` and `overrides.py`.
  - The verification outcomes.

MANDATORY INTEGRATION WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A Forensic Auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Please load the software-engineering skill located at:
`/google/src/files/head/depot/google3/learning/gemini/agents/skills/software_engineering/SKILL.md`
