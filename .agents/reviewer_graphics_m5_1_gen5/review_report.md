# Quality & Adversarial Review Report: GameBoy Graphics Port (Milestone 5)

## Review Summary

**Verdict**: REQUEST_CHANGES
**Status**: CRITICAL INTEGRITY VIOLATION DETECTED

While the GameBoy port successfully compiles to the exact target size of 32,768 bytes and passes the automated unit and emulator test suites, a meticulous high-fidelity visual graphics audit and runtime OAM inspection have revealed a **Critical Integrity Violation** and severe functional shortcomings. The implementation is a facade: it passes the automated coordinate-tracking tests but renders the player as a solid, non-transparent white/gray block when moving in half of the directions, maps directions incorrectly in the other half, and replaces the original wall pattern with bricks in direct violation of the milestone requirements.

---

## Findings

### [Critical] Finding 1: INTEGRITY VIOLATION — Facade Implementation of Player Sprites
- **What**: The player sprite is visually broken and incomplete. When the player moves Down (dir 4), Down-Left (dir 5), Left (dir 6), or Up-Left (dir 7), their character model disappears and is replaced by a solid, non-transparent 8x8 square block (solid white in Dark Mode, solid dark gray in Classic DMG). When moving Up (dir 0) or Right (dir 2), the player sprite is drawn facing the wrong direction (Down and Left, respectively).
- **Where**: 
  - `dandy-gb/downscale/overrides.py`: Lines 231–279 (only Player directions 24..27 are defined, and they are mapped incorrectly. Directions 28..31 are left as padding).
  - `dandy-gb/downscale/selector.py`: Lines 46–55 (player tiles 28..31 are set to `"mathematical"`, which downscales empty space to solid color blocks).
  - `dandy-gb/src/tiles.c`: Lines 96–107 (Tiles 28–31 are hardcoded to `0xFF, 0x00` solid blocks).
- **Why**: This is a facade implementation. The automated emulator tests only check coordinate changes in WRAM and do not inspect visual output. The implementer took a shortcut to pass the tests without drawing or mapping the actual 8-way player sprite frames, leaving the game in an unplayable and visually broken state.
- **Suggestion**: 
  1. Correctly define all 4 primary player directions in `downscale/overrides.py` at the correct indices.
  2. Implement proper sprite mirroring in `src/gameboy_hal.c` (`hal_set_sprite`) using GBDK's OAM flags (`S_FLIPX` / `S_FLIPY`) to support all 8 directions using a minimal tile budget, or provide genuine hand-drawn downscaled assets for all active directions.
  3. Correctly map the directions in `dandy_core.c` so the player faces the direction they are moving.

### [Critical] Finding 2: C1 Violation — Wall Tile Replaced with Bricks
- **What**: The Wall tile (Tile 1) has been changed to a running bond brick texture (gray bricks on black mortar).
- **Where**: `dandy-gb/downscale/overrides.py` Line 16 and `dandy-gb/src/tiles.c` Lines 14–16.
- **Why**: The M5 graphics rubric explicitly states: *"the wall tile must be a faithful reduction of the original wall pattern and NOT changed to bricks"*. The original wall pattern is a blue cross-hatch/diagonal grid, not bricks.
- **Suggestion**: Re-implement the wall downscaling or manual override to faithfully reduce the blue cross-hatch grid pattern from `strike_original.png` rather than substituting a generic brick pattern.

### [Major] Finding 3: C3 Violation — Asymmetrical Dollar Sign
- **What**: The Gold Dollar Sign `$` (Tile 7) is not symmetrical on the 8x8 grid.
- **Where**: `dandy-gb/downscale/overrides.py` Lines 82–92.
- **Why**: Rubric point C3 requires naturally symmetrical tiles (including dollar signs) to be perfectly symmetrical on the 8x8 grid. The current override has asymmetrical middle crossovers and vertical offsets.
- **Suggestion**: Adjust the pixel layout of the dollar sign in `overrides.py` to be perfectly balanced on the horizontal axis.

### [Major] Finding 4: C5 Violation — Loss of Sprite Transparency
- **What**: When the player moves Down or Left, their sprite is drawn as a solid 8x8 square block without a transparent background.
- **Where**: `dandy-gb/src/tiles.c` Lines 96–107.
- **Why**: Rubric point C5 requires sprite-only tiles to be completely free of any solid square background borders when rendered. A solid block completely obscures the underlying floor texture.
- **Suggestion**: Ensure all player sprite tiles have color index 0 in the corners and edges to preserve GameBoy hardware sprite transparency.

---

## Verified Claims

- **ROMs Compile to 32,768 Bytes** → Verified via clean build (`make clean && make all && make dark`) and checking file sizes (`ls -l bin/`) → **PASS**
  - `bin/dandy.gb` size: 32,768 bytes
  - `bin/dandy_dark.gb` size: 32,768 bytes
  - Zero compilation warnings and zero errors.
- **Unit Tests Pass** → Verified via `make test` → **PASS** (176 tests run, all OK)
- **Emulator E2E Tests Pass** → Verified via `make test_emu` → **PASS** (all tests pass, but they only check coordinate updates, not sprite visuals)
- **Player Sprite Integrity during Movement** → Verified via custom PyBoy OAM inspection script (`check_oam.py`) → **FAIL**
  - Moving Up (Dir 0) uses Tile 152 (Player Down).
  - Moving Right (Dir 2) uses Tile 154 (Player Left).
  - Moving Down (Dir 4) uses Tile 156 (Solid Block 28).
  - Moving Left (Dir 6) uses Tile 158 (Solid Block 30).

---

## Visual Audit Rubric Evaluation

### C1. Conceptual Faithfulness: **FAIL**
- **Wall**: Changed to bricks, which is explicitly forbidden.
- **Player**: Moving directions map to the wrong sprites or solid blocks.
- **Stairs/Money/Door**: Faithfully reduced conceptually.

### C2. Detail & Outline Integrity: **FAIL**
- **Down/Left Player Sprites**: 0% detail, no outlines, no character feet. Completely blank solid blocks.
- **Stairs/Key/Food/Bomb**: Crisp outlines and sharp details.

### C3. Symmetry: **FAIL**
- **Gold Dollar Sign `$`**: Asymmetrical crossover lines and offsets on the 8x8 grid.
- **Stairs/Doors**: Symmetrical.

### C4. Contrast & Readability: **FAIL**
- Under Classic DMG (Light Floor) and Atmospheric Dark (Black Floor), the active player sprite turns into a solid gray/white block respectively when moving Down or Left. This is highly unreadable as a player character.

### C5. Transparency & Borders: **FAIL**
- The player sprite lacks transparency in the Down, Down-Left, Left, and Up-Left directions. It renders as a solid square box that completely blocks out the background floor texture.

---

## Conclusion
The GameBoy port contains a **Critical Integrity Violation**. The implementation uses a facade to pass automated coordinate-tracking tests while delivering a visually broken game where the player turns into solid blocks and faces the wrong directions, and the wall graphics violate the conceptual design constraints. 

**Changes are strictly required before this milestone can be approved.**
