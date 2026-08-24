# Synthesized Test Coverage Gaps & Vulnerability Report

Following the independent adversarial test coverage audits performed by Challenger 1 and Challenger 2 in Milestone 5 (Iteration 1), we have synthesized their findings into this master report.

---

## 1. Proven Critical Vulnerability: Out-of-Bounds Read in `dandy_load_level`

### 1.1. Discovery & Proof
Both Challengers independently identified and empirically proved a **critical Out-of-Bounds Read (buffer over-read) vulnerability** in the level decompression function `dandy_load_level` inside `src/dandy_core.c`.

- **Root Cause**: The function `dandy_load_level` takes only a `level_idx` and reads bytes sequentially from `dandy_levels[level_idx]` using `*src++`. It decodes exactly 1,624 tiles of the inner map grid. However, **there is no bitstream length validation or bounds checking**. If a compressed level stream is truncated or malformed, the decompressor will continue to increment `src` and read bytes past the end of the array.
- **Empirical Proof**: The adversarial test `test_adv04_truncated_bitstream_oob_read` was added to `dandy-gb/tests/test_adversarial_compression.py`. It points `dandy_levels[0]` to a dynamically allocated 1500-byte block where only the first 10 bytes are `0x00` (Spaces) and the rest are `0xFF` (Generator 3 sentinels). The C decompressor successfully ran without bounds checks, decoding the first 80 tiles as spaces and the remaining 1,544 tiles as `TILE_GENERATOR3` from the out-of-bounds region, proving the vulnerability.
- **Safety Risk**: On the GameBoy, reading out-of-bounds of a level array reads adjacent ROM data, leading to corrupt map tiles or undefined behavior. On other platforms (like WebAssembly or native testing libraries), if the over-read crosses a page boundary into unmapped memory, it will trigger a Segmentation Fault (`SIGSEGV`) and crash the game.

### 1.2. Mitigation Requirements (Worker Task)
The Worker must implement a robust, size-bounded decompression mechanism:
1. **Generate Level Sizes**:
   - Modify the level compiler `dandy-gb/tools/convert_levels.py` to calculate the exact size of the compressed byte stream for each level.
   - Output an array of sizes `extern const uint16_t dandy_level_sizes[DANDY_NUM_LEVELS];` in `src/levels.h` and define it in `src/levels.c` (e.g., `const uint16_t dandy_level_sizes[DANDY_NUM_LEVELS] = { sizeof(dandy_level_0), sizeof(dandy_level_1), ... };`).
2. **Perform Bounds Checks in Decompressor**:
   - In `dandy-gb/src/dandy_core.c:dandy_load_level`, obtain the pointer `src` and the end pointer `src_end = src + dandy_level_sizes[level_idx]`.
   - On every cache refill or byte fetch from `src`, verify that `src < src_end`.
   - If `src >= src_end` (meaning the stream has been exhausted or truncated), the decompressor **must not** dereference `src`. Instead, it should safely return a default byte value (e.g. `0`, which decodes to `TILE_SPACE`) so the remaining tiles are decoded safely as spaces without any memory safety violations.
   - The implementation must be highly optimized for the GameBoy's Z80 CPU to minimize code footprint and execution overhead.

---

## 2. Boundary & Corner Case Coverage (Verified)

The Challengers successfully added and verified coverage for the following extreme scenarios:
1. **ADV-01: Extreme Map Layouts**:
   - `test_adv01_all_spaces_level`: Verified that a level with 100% spaces compresses and decodes perfectly.
   - `test_adv01_all_walls_level`: Verified that a level with 100% walls compresses and decodes perfectly.
   - `test_adv01_all_doors_level`: Verified that a level with 100% doors compresses and decodes perfectly.
2. **ADV-02: Bit Alignment & Padding**:
   - `test_adv02_padding_bits_ignored`: Verified that the decompressor stops exactly after 1,624 tiles, ignoring trailing padding bits in the final byte.
3. **ADV-03: Huffman Bitstream Corruption**:
   - `test_adv03_corrupted_all_ones_bitstream`: Verified that a corrupted stream of all `1`s is handled gracefully.
4. **Spawn Portal Fallback**:
   - `test_adv_no_spawn_portal_fallback`: Verified that when a level contains no `TILE_UP` spawn portal, the engine correctly falls back to placing the player at coordinates `(1, 2)`.

All of these new tests are successfully integrated into `dandy-gb/tests/test_adversarial_compression.py` and are currently passing.

---

## 3. Worker Implementation Verification

Once the Worker implements the mitigations:
- The adversarial test `test_adv04_truncated_bitstream_oob_read` should be updated to **assert that the OOB read no longer occurs** (i.e. the decompressor safely stops or decodes spaces instead of reading out-of-bounds bytes from the adjacent sentinel region).
- The total suite of **124 tests** must compile and pass successfully (`make test`).
- The build must satisfy all global project constraints: flat 32KB ROM (no MBC), exact 32,768-byte ROM size, and active code/data segment size < 28KB.
