# Scope: Milestone 1 - Exploration & Verification Foundation

## Architecture
- **Data Flow**:
  1. Extract Base64 from `dandy-js/strike.js` -> Decode to PNG -> Save `dandy-gb/teamwork_graphics/strike_original.png`.
  2. Parse GBDK 2bpp array from `dandy-gb/src/tiles.c` -> Decode to raw pixels.
  3. Load `strike_original.png` -> Split into 16x16 tiles.
  4. Compare corresponding tiles side-by-side (upscaled 8x using nearest-neighbor) -> Save to `dandy-gb/teamwork_graphics/graphics_audit.png`.
  5. Compile GBDK GameBoy C codebase using `make` in `dandy-gb/` -> Verify clean build with zero warnings/errors.

## Milestones / Tasks
| # | Name | Scope | Dependencies | Status |
|---|---|---|---|---|
| T1 | Extract & Decode Sprite Sheet | Extract base64 from `dandy-js/strike.js`, decode, verify 256x16 PNG, save to `dandy-gb/teamwork_graphics/strike_original.png` | none | PLANNED |
| T2 | Develop Verification Script | Create `dandy-gb/tools/verify_graphics.py` to parse GBDK 2bpp from `tiles.c`, decode, upscale 8x, and compare side-by-side with original. | T1 | PLANNED |
| T3 | GBDK Project Compilation | Run `make clean && make` in `dandy-gb/` to verify clean compilation. | none | PLANNED |
| T4 | Run Audit & Verification | Execute the script, generate `dandy-gb/teamwork_graphics/graphics_audit.png`, and confirm matches. | T2, T3 | PLANNED |

## Interface Contracts
### GBDK 2bpp Format ↔ Pixel Decoder
- GBDK 2bpp tiles are 8x8 pixels. Each pixel has 2 bits (4 colors).
- Each tile takes 16 bytes: 2 bytes per row.
  - Byte 1: Low bit of color index for 8 pixels.
  - Byte 2: High bit of color index for 8 pixels.
- The decoder must reconstruct 8x8 pixel blocks and arrange them to match the original 16x16 layout (a 16x16 sprite is composed of four 8x8 tiles in a specific order, e.g., Top-Left, Top-Right, Bottom-Left, Bottom-Right, or as defined in `tiles.c`).
