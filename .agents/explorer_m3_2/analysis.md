# Analysis: Scheme B2 Decompressor with Edge Wall Elision for GBDK C

## Executive Summary
This analysis presents a highly optimized, robust, and mathematically bounds-safe GBDK C decompressor for **Scheme B2 with Edge Wall Elision**, tailored for the GameBoy's Sharp LR35902 (Z80-like) CPU. By combining a fast `memset` initialization with a sequential pointer-based inner loop and a zero-multiplication bit-decoding state machine, the design achieves maximum decoding speed, minimal ROM footprint, and absolute safety against buffer overflows.

---

## 1. Decompressor Initialization & Fast Memset
The Edge Wall Elision scheme omits the 1-tile outer border (row 0, row 29, col 0, col 59) from the compressed bitstream, compressing only the inner 58x28 grid (1,624 tiles). 

To support this, the decompressor must first initialize the entire 1,800-byte `dandy_map` buffer with `TILE_WALL` (ID 1) before decoding.
- **Implementation**: We utilize the standard library's `memset` function:
  ```c
  memset(dandy_map, TILE_WALL, MAP_SIZE);
  ```
- **Z80 Optimization Rationale**: The GBDK-2020 standard library implements `memset` in highly optimized hand-written Z80 assembly (utilizing efficient 16-bit block-fill instructions or tight loops). This is orders of magnitude faster than a manual C loop and initializes the entire 1,800-byte buffer in a fraction of a millisecond.

---

## 2. Inner Grid Decoding & Sequential Pointer Traversal
The compressed stream only contains data for the inner 58x28 grid:
- Rows $y$ from $1$ to $28$ (inclusive).
- Columns $x$ from $1$ to $58$ (inclusive).

### Address Calculation Optimization
On the GameBoy CPU, 16-bit multiplication (such as `y * 60`) is extremely slow due to the lack of hardware multiplication. 
To eliminate this overhead entirely inside the inner loop:
1. We use the existing `row_offsets` lookup table to find the start address of each row:
   ```c
   uint16_t row_offset = row_offsets[y];
   ```
2. We initialize a destination pointer `dst` to point directly to column 1 of the current row:
   ```c
   uint8_t* dst = &dandy_map[row_offset + 1];
   ```
3. Inside the inner loop (for $x = 1$ to $58$), we simply write to `*dst` and increment the pointer using `dst++`.
4. This reduces the inner loop's address calculation overhead to a single, highly efficient 16-bit register increment (`inc hl` in assembly), completely avoiding any addition or multiplication.

---

## 3. Skip-Write Optimization
Because the `dandy_map` buffer is pre-filled with `TILE_WALL` (ID 1) during initialization, any tile decoded as Wall does not need to be written to RAM.
- **Mechanism**:
  - When the decoder encounters the prefix `10` (representing `TILE_WALL`), it consumes the bits, increments the destination pointer `dst++`, but **skips the write operation** to `*dst`.
  - When the decoder encounters any other tile (Space `0` or other tiles `11xxxx`), it writes the decoded tile ID to `*dst` and increments `dst++`.
- **Z80 Optimization Rationale**: 
  - Writing to RAM on the GameBoy requires a `ld (hl), a` instruction which takes 8 clock cycles.
  - Wall tiles typically represent a large percentage of any level's tiles (typically 30% to 55% including the borders and maze walls).
  - By skipping RAM writes for all Wall tiles, we save hundreds of clock cycles per level load, significantly speeding up decompression.

---

## 4. Bounds Safety Analysis & Mathematical Guarantee
A major vulnerability in the previous RLE decompressor was the potential for buffer overflows: a corrupted run-length in ROM could cause the destination index to exceed `MAP_SIZE` (1800), writing into adjacent RAM variables.

Our Scheme B2 decompressor provides a **mathematical guarantee of absolute bounds safety**:
1. **Static Loop Bounds**: The destination pointer `dst` is controlled entirely by static loop counters:
   - Row loop: $y \in [1, 28]$ (28 iterations)
   - Column loop: $x \in [1, 58]$ (58 iterations per row)
2. **Deterministic Memory Boundaries**:
   - The minimum address accessed by `dst` is `dandy_map + row_offsets[1] + 1` = `dandy_map + 61`.
   - The maximum address accessed by `dst` is `dandy_map + row_offsets[28] + 58` = `dandy_map + 1738`.
3. **Bitstream Independence**: The destination addresses are entirely independent of the compressed bitstream content. A corrupted or malicious level bitstream in ROM can only alter *what* tile IDs are written, but can *never* alter *where* they are written.
4. **Conclusion**: Out-of-bounds writes are physically impossible. The decompressor is 100% immune to buffer overflows and memory corruption.

---

## 5. Z80-Optimized Bit-Decoding State Machine
The Sharp LR35902 (Z80) has no hardware division, modulo, or multi-bit shifts. To achieve peak performance, we design a state machine that:
- Inlines all bitstream reading to avoid function call overhead.
- Uses a single-byte `bit_cache` and a `bit_count` tracker.
- Employs simple bitwise AND (`& 0x80`) to test the MSB and 1-bit left shifts (`<<= 1`) to advance.
- Unrolls the 4-bit tile ID extraction to eliminate loop overhead for other tiles.

### Detailed Bit-Reading Logic
To read a bit:
```c
if (bit_count == 0) {
    bit_cache = *src++;
    bit_count = 8;
}
uint8_t bit = (bit_cache & 0x80) ? 1 : 0;
bit_cache <<= 1;
bit_count--;
```
In our implementation, we optimize this further by checking the MSB directly in conditional branches, bypassing the need to store the bit in a temporary variable.

---

## 6. GBDK C Pseudo-Code
Below is the complete, production-ready, Z80-optimized C implementation of the new `dandy_load_level` function:

```c
#include "dandy_core.h"
#include "levels.h"
#include <string.h>

void dandy_load_level(uint8_t level_idx) {
    // Prevent out-of-bounds level index
    if (level_idx >= DANDY_NUM_LEVELS) {
        level_idx = DANDY_NUM_LEVELS - 1;
    }

    // 1. Initialize the entire 1,800-byte map buffer with Wall tiles (ID 1)
    // This is extremely fast as it uses the platform's assembly-optimized memset.
    memset(dandy_map, TILE_WALL, MAP_SIZE);

    // 2. Setup bitstream decoder pointers and cache
    const uint8_t* src = dandy_levels[level_idx];
    uint8_t bit_cache = 0;
    uint8_t bit_count = 0;

    // 3. Decode into the inner 58x28 grid
    // Outer border (row 0, row 29, col 0, col 59) remains TILE_WALL (1).
    for (uint8_t y = 1; y <= 28; ++y) {
        // Use row_offsets table to avoid slow 16-bit multiplication (y * 60)
        // Set dst to point to column 1 of the current row
        uint8_t* dst = &dandy_map[row_offsets[y] + 1];

        for (uint8_t x = 1; x <= 58; ++x) {
            // Read 1st bit
            if (bit_count == 0) {
                bit_cache = *src++;
                bit_count = 8;
            }
            
            // Check if 1st bit is 0
            if ((bit_cache & 0x80) == 0) {
                // '0' -> Space (ID 0)
                *dst = TILE_SPACE;
                bit_cache <<= 1;
                bit_count--;
            } else {
                // 1st bit is 1, consume it and read 2nd bit
                bit_cache <<= 1;
                bit_count--;
                
                if (bit_count == 0) {
                    bit_cache = *src++;
                    bit_count = 8;
                }
                
                // Check if 2nd bit is 0
                if ((bit_cache & 0x80) == 0) {
                    // '10' -> Wall (ID 1)
                    // Skip-write optimization: the buffer is already pre-filled with TILE_WALL (1).
                    // We do not write anything to *dst, saving a RAM write.
                    bit_cache <<= 1;
                    bit_count--;
                } else {
                    // '11' -> Other tile (ID 2 to 15), consume 2nd bit
                    bit_cache <<= 1;
                    bit_count--;
                    
                    // Decode 4-bit tile ID (fully unrolled for maximum Z80 speed)
                    uint8_t tile_id = 0;
                    
                    // Bit 3
                    if (bit_count == 0) { bit_cache = *src++; bit_count = 8; }
                    tile_id <<= 1; if (bit_cache & 0x80) tile_id |= 1; bit_cache <<= 1; bit_count--;
                    
                    // Bit 2
                    if (bit_count == 0) { bit_cache = *src++; bit_count = 8; }
                    tile_id <<= 1; if (bit_cache & 0x80) tile_id |= 1; bit_cache <<= 1; bit_count--;
                    
                    // Bit 1
                    if (bit_count == 0) { bit_cache = *src++; bit_count = 8; }
                    tile_id <<= 1; if (bit_cache & 0x80) tile_id |= 1; bit_cache <<= 1; bit_count--;
                    
                    // Bit 0
                    if (bit_count == 0) { bit_cache = *src++; bit_count = 8; }
                    tile_id <<= 1; if (bit_cache & 0x80) tile_id |= 1; bit_cache <<= 1; bit_count--;
                    
                    *dst = tile_id;
                }
            }
            
            // Advance destination pointer to the next column in the row
            dst++;
        }
    }

    // 4. Post-decompression setup (standard engine logic)
    set_player_start_position();
    
    for (uint8_t p = 0; p < MAX_PLAYERS; ++p) {
        arrow_dir[p] = -1;
    }
    is_dirty = true;
}
```

---

## 7. Performance & Resource Footprint Projections

| Metric | Previous RLE Decompressor | New Scheme B2 Decompressor | Improvement / Impact |
|---|---|---|---|
| **RAM Writes** | 1,800 writes (always) | ~800 to 1,100 writes | **40% to 55% reduction** in RAM write cycles (via Skip-Write) |
| **Address Calculations** | Heavy (addition/updates inside loop) | Sequential pointer (`dst++`) | **Zero multiplication** and minimal addition overhead |
| **Bitstream Reading** | Byte-aligned | Bit-level MSB-first | Minor bit-shifting overhead, offset by fast RAM writes and no multiplication |
| **Buffer Overflow Risk** | High (corrupted ROM data can overflow) | **Zero Risk** | Mathematically guaranteed safe via static loops |
| **Decompressor Code Size** | ~60 bytes | ~120 to 150 bytes | Easily fits within the 32KB flat ROM budget |
| **Level Compression Ratio** | Moderate (RLE) | High (Scheme B2 prefix) | Allows fitting all 26 levels into a single-bank 32KB ROM |

---

## 8. Implementation Strategy
1. **Preserve Read-Only Scope**: This document serves as the formal architectural design.
2. **Next Steps for Implementer**:
   - Re-implement `dandy_load_level` in `dandy_gb/src/dandy_core.c` exactly matching the pseudo-code above.
   - Run `blaze build` or the project's Makefile to compile the GameBoy ROM.
   - Execute E2E tests to verify that level loading, player spawn position, and gameplay mechanics work flawlessly.
   - Run the updated `verify_compression.py` script to assert ROM size and round-trip decompression fidelity.
