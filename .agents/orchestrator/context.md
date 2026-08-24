# Project Context: Dandy Dungeon Custom 2D Level Compression

## Background
Dandy Dungeon GameBoy port currently uses a 1D Run-Length Encoding (RLE) scheme to compress its 26 levels. Because the compressed levels exceed the capacity of a single 32KB GameBoy ROM, the build system was configured to use a bank-switching Memory Bank Controller (MBC1) with a 4-bank 64KB ROM layout. The levels are placed in Bank 2 and loaded on-the-fly via GBDK's `SWITCH_ROM(2)` function.

The goal of this project is to remove the bank-switching MBC1 chip and revert to a flat, single-bank 32KB ROM (no-MBC). This requires a highly efficient custom 2D compression algorithm to shrink the ROM footprint of the 26 levels so that the entire game (engine, font, sprites, sound driver, and compressed levels) fits within 32KB, with a target active code+data segment size under 28KB (leaving at least 4KB of free ROM headroom for safety).

## Core Technical Constraints
1. **ROM Budget**:
   - Total ROM file size: exactly 32,768 bytes.
   - Active code + data segments in map file: < 28,672 bytes (28 KB).
   - Flat 32KB ROM structure (no MBC, Bank 0 & 1 only).
2. **RAM & Hardware Limits**:
   - Zero dynamic RAM allocations (`malloc`/`free`).
   - Operating within GameBoy's strict 8KB Work RAM (WRAM) limit.
   - Game map buffer is `dandy_map` (1800 bytes, 60x30 tiles).
   - Decompressor must execute extremely quickly on the 8-bit Sharp LR35902 CPU (avoiding 32-bit math, floating-point, or deep recursion).
3. **Fidelity**:
   - Decompressed level maps must be 100% bit-for-bit identical to the original levels defined in `dandy-js/levels.js`.
4. **Integrity Mode**:
   - Development integrity rules apply. No cheating, no hardcoding of test results or fake implementations.

## Compression Analysis & Ideas
- **Original Levels**: 26 levels, each is 60 columns by 30 rows = 1800 bytes. Total raw size = 46.8 KB.
- **Current RLE**: Simple 1D RLE. If a tile repeats >= 4 times, it writes `[0xFF, run_len, tile_id]`.
- **2D Spatial Coherence**:
  - The levels have high spatial similarity. Walls often form continuous lines or solid blocks.
  - Large empty spaces (space tiles) and repetitive room structures.
- **Proposed Method: Meta-Tile Dictionary + RLE**:
  - Decompose the 60x30 map into 2x2 meta-tiles (or similar small blocks).
  - Since there is high repetition, the number of unique 2x2 blocks across all 26 levels is very small (e.g., 64 to 128 unique blocks).
  - We can build a global dictionary of unique 2x2 blocks (each block is 4 bytes).
  - Each level map is then represented as a grid of 30x15 meta-tile indices (each index is 1 byte, pointing to the dictionary).
  - This reduces the map size from 1800 bytes to 450 bytes.
  - We can compress the 450-byte index map using a simple 1D RLE.
  - Decompression: Read RLE stream of meta-tile indices. For each index, look up the 2x2 tiles in the dictionary, and write them to `dandy_map` at the correct 2D positions.
  - This requires zero dynamic allocation, uses extremely simple 8-bit calculations, and runs in a single pass.
