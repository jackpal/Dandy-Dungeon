# M5 Handoff Report: E2E Verification & Visual Graphics Audit

This is a **Hard Handoff** summarizing the final technical verification and visual graphics audit of the GameBoy port in `dandy-gb/`.

---

## 1. Observation

- **Clean Build Command & Output**:
  Ran `make clean && make all && make dark` in `dandy-gb/`.
  - Cleaned up object files, locks, logs, and compiled binaries:
    `rm -rf obj obj_dark bin`
  - Recompiled levels, sprite assets, and ROMs successfully with zero errors and zero warnings:
    `Build successful: bin/dandy.gb`
    `Build successful: bin/dandy_dark.gb`
- **ROM Sizing**:
  Ran `ls -l bin/dandy.gb bin/dandy_dark.gb`. Both ROM files are exactly 32,768 bytes in size:
  ```
  -rw-r--r-- 1 jackpal primarygroup 32768 Jun 21 02:27 bin/dandy_dark.gb
  -rw-r--r-- 1 jackpal primarygroup 32768 Jun 21 02:27 bin/dandy.gb
  ```
- **Unit Test Execution**:
  Ran `make test`. All 176 tests completed successfully:
  ```
  Ran 176 tests in 6.146s
  OK (expected failures=3)
  ```
  This command also generated:
  - `dandy-gb/teamwork_graphics/graphics_audit.png`
  - `dandy-gb/teamwork_graphics/graphics_audit_dark.png`
- **Emulator E2E Tests**:
  Ran `make test_emu`. All tests passed successfully:
  ```
  Running PyBoy automated emulator E2E tests: Classic DMG...
  Ran 2 tests in 0.159s
  OK
  Running PyBoy automated emulator E2E tests: Atmospheric Dark...
  Ran 2 tests in 0.159s
  OK
  ```
- **Source Code Inspections**:
  - `dandy-gb/src/tiles.c` (Lines 96–107) shows Tiles 28–31 are hardcoded as solid light/dark gray blocks:
    ```c
    /* Tile 28 */
    0xFF, 0x00, 0xFF, 0x00, 0xFF, 0x00, 0xFF, 0x00,
    0xFF, 0x00, 0xFF, 0x00, 0xFF, 0x00, 0xFF, 0x00,
    ```
  - `dandy-gb/downscale/overrides.py` (Lines 231–279) shows only 4 player sprite directions are defined, and they are mapped incorrectly to indices 24–27, while 28–31 are left as padding:
    - 24: `TILE_PLAYER1_DOWN`
    - 25: `TILE_PLAYER1_UP`
    - 26: `TILE_PLAYER1_LEFT`
    - 27: `TILE_PLAYER1_RIGHT`
  - `dandy-gb/downscale/selector.py` (Lines 46–55) maps player tiles 28..31 to `"mathematical"`, causing the empty space in the original sheet to compile directly to the solid blocks seen in `tiles.c`.
  - `dandy-gb/src/dandy_core.c` (Lines 24–41) maps buttons to 8 directions (0 to 7):
    - `0001 (Left) -> 6` (Direction 6 maps to Tile 30)
    - `0010 (Right) -> 2` (Direction 2 maps to Tile 26)
    - `0100 (Up) -> 0` (Direction 0 maps to Tile 24)
    - `1000 (Down) -> 4` (Direction 4 maps to Tile 28)
  - `dandy-gb/src/dandy_core.c` (Line 80) defines the player tile as:
    `#define GET_PLAYER_TILE(p_idx, dir) (TILE_PLAYER1 + ((p_idx) << 3) + (dir))`
- **Visual Audit Sheets**:
  Inspected `graphics_audit.png` and `graphics_audit_dark.png` using `view_file`.
  - Row 1 Col 4 (Wall tile) is a running bond brick texture instead of the original blue cross-hatch/diagonal grid.
  - Rows 7 and 8 (Player tiles) show Tiles 28–31 as solid gray squares (Light Gray in Light Floor, Dark Gray in Black Floor).
- **Adversarial Runtime Verification**:
  Wrote and ran a custom PyBoy emulator script (`check_oam.py`) that simulated buttons and dumped active sprite coordinates and tile indices from the GameBoy's hardware OAM memory (`0xFE00`–`0xFE9F`):
  - Under `BOOT` (Initial state, Dir 0 - Up): Sprite 2 Tile = 152 (128 + 24, Player Down).
  - After `UP` (Dir 0 - Up): Sprite 2 Tile = 152 (128 + 24, Player Down).
  - After `RIGHT` (Dir 2 - Right): Sprite 2 Tile = 154 (128 + 26, Player Left).
  - After `DOWN` (Dir 4 - Down): Sprite 2 Tile = 156 (128 + 28, Solid Block 28).
  - After `LEFT` (Dir 6 - Left): Sprite 2 Tile = 158 (128 + 30, Solid Block 30).

---

## 2. Logic Chain

1. The clean build successfully compiles both ROMs, and the automated tests pass, demonstrating that the technical build pipeline and core engine mechanics work correctly in memory.
2. However, the automated emulator E2E tests only assert that the player's coordinates in WRAM change upon button presses; they do not verify the visual contents of the tiles rendered on screen.
3. By comparing `dandy_core.c`'s mapping logic (`GET_PLAYER_TILE` with direction indices 0..7) to the compiled tile data in `tiles.c` and manual overrides in `overrides.py`, we find that:
   - Directions 4 (Down), 5 (Down-Left), 6 (Left), and 7 (Up-Left) map directly to Tiles 28–31.
   - Tiles 28–31 are compiled as solid blocks (`0xFF, 0x00`).
   - Directions 0 (Up) and 2 (Right) map to Tiles 24 (knight facing Down) and 26 (knight facing Left).
4. Our independent runtime OAM verification confirmed that when moving Down and Left, the GameBoy hardware indeed loads OAM tiles 156 (Tile 28) and 158 (Tile 30), meaning the player sprite renders as a solid, non-transparent white/gray square block.
5. Additionally, the Wall tile (Tile 1) manual override has substituted a generic brick pattern in place of the original blue cross-hatch/diagonal grid pattern.
6. This constitutes a **Critical Integrity Violation** (facade implementation to pass tests while leaving the visual game broken) and multiple high-fidelity visual rubric failures (C1, C2, C3, C4, C5).

---

## 3. Caveats

- We did not write code changes to fix these graphics errors because our role is strictly **review-only** (as per key constraints).
- We assumed the original sprite sheet `strike_original.png` is the ground truth for the 5-point rubric.

---

## 4. Conclusion

The GameBoy port successfully compiles and passes automated tests, but is visually broken. The player turns into solid blocks when moving Down or Left, faces the wrong way when moving Up or Right, and the wall graphics violate the conceptual design constraints. This is a **facade implementation** designed to bypass visual verification.

**Verdict: REQUEST_CHANGES (INTEGRITY VIOLATION)**

---

## 5. Verification Method

To independently verify these findings:
1. Run a clean build and verify file sizes:
   `cd dandy-gb && make clean && make all && make dark && ls -l bin/dandy.gb bin/dandy_dark.gb`
2. View the generated audit sheets:
   - `dandy-gb/teamwork_graphics/graphics_audit.png`
   - `dandy-gb/teamwork_graphics/graphics_audit_dark.png`
   Observe the solid blocks in rows 7 and 8 (columns 2, 4, 6, 8) and the brick pattern in row 1 column 4.
3. Inspect `dandy-gb/src/tiles.c` around lines 96–107 to confirm Tiles 28–31 are hardcoded to `0xFF, 0x00` solid bytes.
4. Inspect `dandy-gb/downscale/overrides.py` to confirm only 4 directions of player are defined and mapped incorrectly.
