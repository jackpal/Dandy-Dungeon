# Scope: Milestone 3 — Implement 2D Compressor & Decompressor

## Architecture
- **Compressor (`tools/convert_levels.py`)**: Python script that parses `dandy-js/levels.js`, applies Edge Wall Elision, encodes using Scheme B2 (Variable-Bit-Width) prefix coding, and outputs `src/levels.c` and `src/levels.h`.
- **Decompressor (`src/dandy_core.c`)**: GBDK C function `dandy_load_level` that initializes the 1800-byte map buffer, decodes the bitstream from `dandy_levels[level_idx]` directly into the inner 58x28 grid, optimizes by skipping writes for Walls, and ensures bounds safety.
- **Verification (`tools/verify_compression.py`)**: Round-trip verification script, updated to match Scheme B2 and Edge Wall Elision, verifying 100% round-trip fidelity, ROM build size, segments, and executing E2E tests.

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|---|---|---|---|
| 1 | Explorer Analysis | Analyze existing convert_levels.py, dandy_core.c, verify_compression.py | None | DONE |
| 2 | Implementation | Worker implements compressor, decompressor, and verification updates | M1 | DONE |
| 3 | Review & Challenge | Reviewers verify code quality; Challengers verify functionality, ROM size, and E2E tests | M2 | DONE |
| 4 | Forensic Audit | Auditor checks for integrity violations | M3 | DONE |

## Interface Contracts
### Compressed Level Data Format (Scheme B2 + Edge Wall Elision)
- **Map Size**: Original is 60 columns x 30 rows = 1,800 tiles.
- **Edge Wall Elision**: The outer border (row 0, row 29, col 0, col 59) is omitted during compression. Only the inner 58x28 grid = 1,624 tiles are compressed.
- **Pre-fill**: The decompressor initializes the entire 1,800-byte map with Wall tiles (ID 1) before decoding.
- **Encoding Scheme**:
  - `0` (1 bit): Space (ID 0)
  - `10` (2 bits): Wall (ID 1)
  - `11` + `xxxx` (6 bits): Other tiles (ID 2 to 15), where `xxxx` is the 4-bit tile ID.
- **Bit Packing**: MSB-first. Pack bits into bytes. The final byte of each level is padded with 0s to the byte boundary.
- **Output Files**:
  - `src/levels.h`: Declares `extern const uint8_t dandy_level_0[];` etc., and `extern const uint8_t* const dandy_levels[];`.
  - `src/levels.c`: Defines the compressed byte arrays and the pointer array.
