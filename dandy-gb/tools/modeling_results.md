# Dandy Dungeon Level Compression Modeling & Comparative Report

This report presents the comparative performance analysis of the candidate compression schemes designed to compress all 26 levels of Dandy Dungeon. The primary architectural objective is to enable the entire game to compile into a single, flat **32KB GameBoy ROM (no bank-switching MBC chip)**, with a strict active ROM budget under **28KB**.

## Executive Summary & Recommendation

Based on our rigorous mathematical simulations across all 26 levels, we have identified **Scheme B2: Hand-crafted Variable-Bit-Width (VBW) Coding** as the **optimal recommended compression scheme** for Dandy Dungeon's GameBoy port.

### Key Findings:
1. **Redundancy Exploitation**: The tile frequency analysis revealed that Empty Space (ID 0) and Wall (ID 1) account for **84.78%** of the map tiles. Scheme B2 directly exploits this by encoding Empty Space in **1 bit** (`0`), Wall in **2 bits** (`10`), and other tiles in **6 bits** (`11` + 4-bit raw ID).
2. **Outstanding Compression**: Scheme B2 achieves a total level database size of **11,050 bytes** (10.79 KB) for all 26 levels, which is a **76.39%** reduction compared to the 46,800-byte raw 8-bit map, and a **47.66%** reduction compared to the 21,112-byte 4-bit packed border-elided map.
3. **Zero ROM Overhead**: Since the prefix code is hardcoded in the C decoder, Scheme B2 requires **zero bytes of ROM overhead** for lookup tables or dictionaries, unlike Huffman (32 bytes) or 2x2 Meta-tile dictionaries (128 to 512 bytes).
4. **Z80-Friendly Performance**: Standard Huffman decoding requires traversing a tree bit-by-bit, which is relatively slow on the 8-bit Z80. Scheme B2's hardcoded prefix code can be decoded using extremely fast nested `if-else` blocks and simple bit-shifts. Furthermore, because ~85% of the tiles are Space or Wall, the decoder will execute the fast 1-bit or 2-bit paths in the vast majority of cases, resulting in near-instantaneous level load times.

---

## Comparative Analysis Table

| Rank | Scheme Name | Avg Level Size (Bytes) | Total DB Size (Bytes)* | Compression Ratio (vs Raw) | Compression Ratio (vs Packed) | Est. C Decoder Code Size (Bytes) | CPU Execution Overhead | Recommendation / Notes |
|:---:|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---|
| 1 | Scheme B2: Hand-crafted VBW Coding | 425.0 | 11,050 | 76.4% | 52.8% | 90 | Low-Medium | **Winner**. Best balance of high compression, zero overhead, and fast execution. |
| 2 | Scheme D: 2D Predictor / Copy-Neighbor Coding | 463.1 | 12,041 | 74.3% | 48.5% | 160 | High | Highest compression ratio, but extremely high CPU overhead due to 2D neighbor lookups. |
| 3 | Scheme B1: Global Huffman Coding | 388.2 | 10,094 | 78.4% | 56.9% | 180 | Medium | Excellent compression, but bit-by-bit tree traversal is slower than B2 and has 32B table overhead. |
| 4 | Scheme C: Meta-Tile 2x2 Dict (N=256) | 463.3 | 12,046 | 74.3% | 48.5% | 150 | Low-Medium | Good compression, but dictionary table adds 512 bytes of ROM overhead. |
| 5 | Scheme C: Meta-Tile 2x2 Dict (N=128) | 500.4 | 13,010 | 72.2% | 44.4% | 150 | Low-Medium | Sub-optimal. |
| 6 | Scheme C: Meta-Tile 2x2 Dict (N=64) | 553.7 | 14,396 | 69.2% | 38.5% | 150 | Low-Medium | Sub-optimal. |
| 7 | Scheme A: 4-Bit Packing with Edge Wall Elision | 812.0 | 21,112 | 54.9% | 9.8% | 60 | Low | Simple baseline, but total size (21.1 KB) leaves very little headroom for engine code. |
| 8 | Scheme E1: 4-Bit Nibble RLE (0xF Marker) | 514.9 | 13,388 | 71.4% | 42.8% | 100 | Low-Medium | Sub-optimal. |
| 9 | Scheme E2: 8-Bit RLE with Border Elision | 988.1 | 25,690 | 45.1% | -9.8% | 80 | Low | Sub-optimal. |
| 10 | Scheme E3: Traditional 8-Bit RLE (Full Map Baseline) | 1067.4 | 27,752 | 40.7% | -18.6% | 70 | Low | Current game baseline. Extremely poor compression, cannot fit all 26 levels in 32KB ROM. |

\* *Note: Total DB Size includes level data + any ROM overhead (dictionaries or lookup tables).*

---

## Detailed Analysis of Candidate Schemes

### Scheme A: 4-Bit Packing with Edge Wall Elision (Baseline)

- **Description**: Omit the 176 border walls. Pack the remaining 1624 tiles as 4-bit nibbles (two per byte).
- **Mathematical Performance**: Exactly **812 bytes** per level. Total database size: **21,112 bytes** (20.62 KB).
- **Decompressor Complexity**: Extremely low. Reconstructs borders in a simple loop, then copies 812 bytes from ROM, splitting each byte into two 4-bit nibbles. No bit-level shifting across byte boundaries is required.
- **Z80 CPU Overhead**: **Low**. The fastest possible decompressor that still achieves some savings.
- **Verdict**: Too large. 20.62 KB for levels leaves only ~6.9 KB for the entire game engine, graphics, and sound driver, which is extremely tight and risky.

### Scheme B: Variable-Bit-Width (VBW) / Huffman Coding

#### Scheme B1: Global Huffman Coding
- **Description**: Build an optimal binary Huffman tree based on the global tile frequencies of all inner tiles across all 26 levels.
- **Mathematical Performance**: Average level size: **388.2 bytes**. Total database size: **10,094 bytes** (9.86 KB) including 32 bytes of tree/table overhead. This is a **78.4%** savings over raw, and **56.9%** over packed.
- **Decompressor Complexity**: Medium. Needs a bit-by-bit reading helper and a tree traversal loop.
- **Z80 CPU Overhead**: **Medium**. Shifting bits one-by-one is relatively expensive on Z80 because it lacks a hardware barrel shifter.

#### Scheme B2: Hand-crafted VBW Coding
- **Description**: A simplified prefix code optimized for the 84.78% frequency of Space and Wall tiles:
  - Space (ID 0): `0` (1 bit)
  - Wall (ID 1): `10` (2 bits)
  - Other 14 tiles: `11` + 4-bit raw tile ID (6 bits total)
- **Mathematical Performance**: Average level size: **425.0 bytes**. Total database size: **11,050 bytes** (10.79 KB). This is only **956 bytes larger** than the mathematically optimal Global Huffman, but requires **zero bytes of table overhead**.
- **Decompressor Complexity**: Low-Medium. The decoder does not need to traverse a tree. It can be implemented using extremely fast nested `if` checks in C:
  ```c
  if (read_bit() == 0) {
      tile = 0; // Space
  } else if (read_bit() == 0) {
      tile = 1; // Wall
  } else {
      tile = read_bits(4); // Other tiles
  }
  ```
- **Z80 CPU Overhead**: **Low-Medium**. Since ~85% of tiles take the 1-bit or 2-bit path, bit shifting is minimized, and no memory reads for tree traversal are needed. This is exceptionally fast.
- **Verdict**: **Recommended Winner**.

### Scheme C: Meta-Tile 2x2 Dictionary with Escape Coding

- **Description**: Partition the 58x28 inner map into 406 non-overlapping 2x2 blocks. Store the $N$ most frequent blocks in a ROM dictionary. Represent blocks in the dictionary as a 1-byte index, and other blocks as an escape byte followed by 2 bytes of raw 4-bit tile IDs.
- **Performance by Dictionary Size $N$**:
  - **$N = 64$**: Avg level size: **553.7 bytes**. Total DB size: **14,396 bytes** (14.06 KB) including 128 bytes of dictionary overhead.
  - **$N = 128$**: Avg level size: **500.4 bytes**. Total DB size: **13,010 bytes** (12.71 KB) including 256 bytes of dictionary overhead.
  - **$N = 256$** (specifically, $N = 255$ + 1 escape): Avg level size: **463.3 bytes**. Total DB size: **12,046 bytes** (11.76 KB) including 512 bytes of dictionary overhead.
- **Decompressor Complexity**: Medium. Requires dictionary lookup, 2x2 block coordinate mapping, and unpacking tiles.
- **Z80 CPU Overhead**: **Low-Medium**. Byte-aligned operations (no bit-shifting across byte boundaries, except simple nibble unpacking) make it very fast, but writing to a 2x2 block structure requires coordinate calculations in C.
- **Verdict**: Good, but Scheme B2 achieves significantly better compression (11,050 B vs 12,046 B) with much simpler code and zero dictionary overhead.

### Scheme D: 2D Predictor / Copy-Neighbor Coding

- **Description**: For each tile, check if it matches the tile directly above (Copy Above: `0`, 1 bit), or to the left (Copy Left: `10`, 2 bits). Otherwise, write new tile (`11` + 4-bit ID, 6 bits).
- **Mathematical Performance**: Average level size: **463.1 bytes**. Total database size: **12,041 bytes** (11.76 KB).
- **Decompressor Complexity**: High. The decoder must keep track of coordinates and look up previously decompressed tiles in the `dandy_map` RAM buffer for both the row above and the column to the left.
- **Z80 CPU Overhead**: **High**. Every single tile requires coordinate-based buffer lookups and bit-by-bit stream parsing. Doing this for 1,624 tiles per level will introduce noticeable loading delays on an 8-bit CPU.
- **Verdict**: Strong compression, but the CPU execution overhead is too high for the performance-constrained GameBoy, and it is outperformed by both Scheme B1 and B2 in overall database size once tree/code overhead is taken into account.

### Scheme E: 1D Run-Length Encoding (RLE)

- **Scheme E1 (4-Bit Nibble RLE)**: Avg level size: **514.9 bytes**. Total DB size: **13,388 bytes** (13.07 KB).
- **Scheme E2 (8-Bit RLE with Border Elision)**: Avg level size: **988.1 bytes**. Total DB size: **25,690 bytes** (25.09 KB).
- **Scheme E3 (Traditional 8-Bit RLE - Full Map)**: Avg level size: **1067.4 bytes**. Total DB size: **27,752 bytes** (27.10 KB).
- **Verdict**: 4-Bit Nibble RLE (E1) performs reasonably well but is vastly outperformed by Scheme B2. Traditional 8-bit RLE (E2/E3) is completely inadequate as it exceeds the 28KB target for levels alone, demonstrating why a custom 2D/entropy scheme is mandatory.

---

## Detailed Level-by-Level Size Comparison (Bytes)

| Level | Raw 8-Bit | RLE (Full) | 4-Bit Packed | VBW (B2) | Huffman (B1) | Dict 256 (C) | 2D Pred (D) | Nibble RLE (E1) |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| Level 00 | 1800 | 1019 | 812 | 357 | 337 | 420 | 433 | 486 |
| Level 01 | 1800 | 1051 | 812 | 323 | 309 | 426 | 360 | 500 |
| Level 02 | 1800 | 753 | 812 | 391 | 373 | 442 | 352 | 356 |
| Level 03 | 1800 | 1683 | 812 | 383 | 347 | 412 | 691 | 809 |
| Level 04 | 1800 | 1476 | 812 | 656 | 644 | 446 | 707 | 720 |
| Level 05 | 1800 | 1164 | 812 | 610 | 494 | 494 | 477 | 561 |
| Level 06 | 1800 | 934 | 812 | 409 | 400 | 448 | 400 | 438 |
| Level 07 | 1800 | 897 | 812 | 390 | 379 | 446 | 335 | 418 |
| Level 08 | 1800 | 1292 | 812 | 492 | 441 | 440 | 499 | 611 |
| Level 09 | 1800 | 1563 | 812 | 358 | 362 | 428 | 827 | 765 |
| Level 10 | 1800 | 967 | 812 | 292 | 293 | 422 | 365 | 455 |
| Level 11 | 1800 | 635 | 812 | 354 | 333 | 432 | 303 | 316 |
| Level 12 | 1800 | 1356 | 812 | 383 | 376 | 450 | 478 | 645 |
| Level 13 | 1800 | 1109 | 812 | 449 | 424 | 464 | 387 | 546 |
| Level 14 | 1800 | 1125 | 812 | 389 | 366 | 446 | 409 | 558 |
| Level 15 | 1800 | 1121 | 812 | 370 | 312 | 428 | 390 | 544 |
| Level 16 | 1800 | 1369 | 812 | 304 | 291 | 436 | 504 | 647 |
| Level 17 | 1800 | 1092 | 812 | 452 | 399 | 462 | 411 | 512 |
| Level 18 | 1800 | 915 | 812 | 288 | 278 | 430 | 335 | 419 |
| Level 19 | 1800 | 771 | 812 | 304 | 290 | 436 | 340 | 366 |
| Level 20 | 1800 | 497 | 812 | 425 | 377 | 422 | 419 | 296 |
| Level 21 | 1800 | 1430 | 812 | 398 | 392 | 444 | 1037 | 706 |
| Level 22 | 1800 | 876 | 812 | 338 | 303 | 422 | 343 | 406 |
| Level 23 | 1800 | 915 | 812 | 316 | 302 | 428 | 389 | 433 |
| Level 24 | 1800 | 1005 | 812 | 403 | 409 | 490 | 427 | 490 |
| Level 25 | 1800 | 737 | 812 | 1216 | 831 | 520 | 423 | 385 |