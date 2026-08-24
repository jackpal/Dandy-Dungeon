# Scope: Milestone 2 — Design 2D Compression

## Architecture
Dandy Dungeon levels are 60x30 grids (1800 tiles). To fit all 26 levels inside a flat 32KB GameBoy ROM along with the core engine and HAL, we must compress the level database.
This milestone focuses on the analysis, research, and design of the custom 2D level compression scheme.
The input is `dandy-js/levels.js`. The outputs are the analysis data, comparative evaluation, and the final format and decompressor design.

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| 1 | Level Tile Analysis | Run comprehensive statistical analysis on the 26 levels (frequencies, edge wall elision, 4-bit packing, meta-tiles). | None | PLANNED |
| 2 | Scheme Research & Evaluation | Research and model compression ratios for Meta-Tile+RLE, MH, MR/MMR, and Variable-Length Coding. | M2.1 | PLANNED |
| 3 | Comparative Report Compilation | Synthesize findings into the Comparative Compression Report, evaluating ratio, code size, Z80 CPU overhead. | M2.2 | PLANNED |
| 4 | Binary Format & Decompressor Design | Define the optimal binary format and decompressor algorithm in pseudo-code / GBDK C. | M2.3 | PLANNED |

## Interface Contracts
### Level Data Input Contract
- Source: `dandy-js/levels.js` (or converted JSON equivalent) containing 26 levels of 60x30 tiles.
- Tile value range: 0 to 15 (representable in 4 bits).

### Compression Format Output Contract
- Target: Custom binary byte stream representing the level database, to be compiled into `src/levels.c`.
- Decompressor API Compatibility: Decodes on-the-fly into the global `uint8_t dandy_map[1800]` buffer inside `dandy_load_level`.
