# Implementation Plan - Graphics conversion pipeline fixes

This plan outlines the steps to resolve Reviewer 1's feedback on graphics conversion.

## Steps

1. **Modify `dandy-gb/downscale/selector.py`**:
   - Change selection source for Tile 1 from `"mathematical"` to `"manual"`.
   - Change selection source for Tiles 28, 29, 30, 31 from `"mathematical"` to `"manual"`.
   - Verify changes visually or by running python checks.

2. **Modify `dandy-gb/downscale/overrides.py`**:
   - Update Tile 1 (Wall) to use the beautiful tiling diagonal cross-hatch pattern.
   - Update Tile 7 (Gold Dollar Sign) to be perfectly symmetrical and centered.
   - Re-arrange player sprites at indices 24..31:
     - `24`: PLAYER_UP (using Cape grid from old 25)
     - `25`: PLAYER_UP_RIGHT (copy of Player Right)
     - `26`: PLAYER_RIGHT (using Shield Right grid from old 27)
     - `27`: PLAYER_DOWN_RIGHT (copy of Player Right)
     - `28`: PLAYER_DOWN (using Visor grid from old 24)
     - `29`: PLAYER_DOWN_LEFT (copy of Player Left)
     - `30`: PLAYER_LEFT (using Shield Left grid from old 26)
     - `31`: PLAYER_UP_LEFT (copy of Player Left)
   - Confirm all player sprite rows have `0` at their corners for GameBoy hardware transparency.

3. **Verify compilation and tests**:
   - Run `make clean` in the `dandy-gb` directory (or workspace root, depending on where the Makefile is).
   - Run `make all` and `make dark` to verify compilation.
   - Run `make test` to regenerate the sprite/tile header files and audit sheets.
   - Run `make test_emu` to run unit and E2E tests.

4. **Document and handoff**:
   - Update `BRIEFING.md` and `progress.md`.
   - Generate the final `handoff.md`.
