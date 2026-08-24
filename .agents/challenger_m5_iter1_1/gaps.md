# Test Coverage Audit: Custom 2D Level Compression (Scheme B2)

This report details the adversarial test coverage audit of the Dandy Dungeon custom 2D level compression implementation (`tools/convert_levels.py` and `src/dandy_core.c:dandy_load_level`).

## 1. Untested Code Blocks, Branches, or Conditions

### 1.1. Compressor Edge Cases & Invalid Inputs (`tools/convert_levels.py`)
- **No tests for custom layouts**: The existing E2E tests only load the pre-compiled 26 levels. The compressor itself is never tested on arbitrary or dynamically generated level layouts.
- **Untested Branch in `char_to_tile_id`**: The `ValueError` exception handler in `char_to_tile_id` (which catches characters not in `ENCODING = " *DudKF$i123mnop"` and maps them to space/0) is never exercised by any test.
- **Unverified Bit Packing & Padding**: The bit-packing function `pack_bits_to_bytes` has never been tested to verify it correctly pads non-byte-aligned bitstreams with trailing zeros.

### 1.2. Decompressor Inner Loop Branches (`src/dandy_core.c`)
- **Optimized Skip-Write Branch**: The decompressor optimization for Tile ID 1 (Wall):
  ```c
  // '10' -> Wall (ID 1)
  // Skip-write optimization: the buffer is already pre-filled with TILE_WALL (1).
  // We do not write anything to *dst, saving a RAM write.
  ```
  The correct behavior of this skip-write branch (i.e. that it leaves the pre-filled `TILE_WALL` intact without writing) is only implicitly tested by loading the pre-compiled levels.
- **Unrolled Bit Decoding Branch**: The unrolled 4-bit decoding for other tile types (`11` prefix) is never systematically tested across all possible 4-bit values (`2` to `15`) in a controlled test case to ensure no bit-shifting or bit-extraction errors exist.

---

## 2. Boundary / Corner Cases Not Covered

- **Minimal Levels (All Space/All Wall)**: Levels containing only a single tile type (e.g. all space tiles `0` or all wall tiles `1`) are not tested. These represent the extreme limits of the Scheme B2 encoding (1 bit/tile and 2 bits/tile respectively).
- **Maximum Size Levels (All Generator/Other)**: A level where every tile belongs to the `11` prefix class (tile IDs 2..15). This represents the worst-case compression ratio (6 bits/tile), resulting in the largest possible compressed stream size (1218 bytes).
- **Bit Alignment & Padding Boundaries**: Variations of levels that result in total compressed bit lengths of `N * 8 + k` where `k` ranges from `0` to `7`. This tests whether the compressor pads correctly and whether the decompressor stops decoding exactly after `1624` tiles without incorrectly reading an extra byte when `k > 0`.
- **No Spawn Portal (`TILE_UP`)**: If a level contains no `TILE_UP` tile, the decompressor must fall back to placing players at default coordinates `(1, 2)`. This fallback path is completely untested.

---

## 3. Potential Vulnerabilities & Security Risks

### 3.1. Out-of-Bounds Read / Buffer Over-read in `dandy_load_level`
- **Vulnerability Description**: The decompressor `dandy_load_level` decodes exactly `1624` tiles by looping through the inner grid. It reads bits from the source pointer `src` by incrementing it whenever the 8-bit cache is exhausted. However, **the decompressor has no concept of the input stream's size or bounds**.
- **Impact**: If a compressed level stream is corrupted, malicious, or truncated (shorter than the number of bits required to decode 1624 tiles), `dandy_load_level` will continue to read bytes from `src` past the end of the level's array. On modern operating systems, if this over-read crosses a page boundary, it will cause a segmentation fault (`SIGSEGV`), crashing the game. On the GameBoy, it will read adjacent ROM data, leading to undefined map layouts.
- **Root Cause**: The function signature `void dandy_load_level(uint8_t level_idx)` does not pass the size of the compressed array, and the compressed format does not include a length header or end-of-stream sentinel.
