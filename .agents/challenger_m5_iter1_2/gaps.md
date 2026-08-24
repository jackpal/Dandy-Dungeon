# Test Coverage Audit: Scheme B2 Compression/Decompression Gaps

This report identifies the gaps in the test coverage of the custom 2D level compression/decompression implementation in **Dandy Dungeon** (`dandy-gb/tools/convert_levels.py` and `dandy-gb/src/dandy_core.c`).

---

## 1. Untested Code Blocks, Branches, or Conditions

In `dandy_load_level` (`src/dandy_core.c`), the decoding logic contains three main branches based on the Huffman prefix:
1.  **Branch 1**: Bit starts with `0` -> Space (`TILE_SPACE` / 0).
2.  **Branch 2**: Bit starts with `10` -> Wall (`TILE_WALL` / 1).
3.  **Branch 3**: Bit starts with `11` -> Other tiles (`TILE_DOOR` to `TILE_GENERATOR3` / 2 to 15), followed by 4-bit tile ID.

### Coverage Analysis
*   **Existing E2E Tests**: The existing 118 E2E tests run the game on the default 26 levels (`levels.c`). While these levels contain all tile types, they only test the *happy path* of valid, pre-compressed levels.
*   **Untested Branches/Conditions**:
    *   **Skip-Write Optimization**: When `TILE_WALL` is decoded, the decompressor skips writing to RAM because the map buffer is pre-filled with walls via `memset`. There is no test verifying that this optimization behaves correctly under arbitrary bitstream structures or that the pre-filling doesn't corrupt subsequent tile writes.
    *   **Decompressor Loop Termination**: The decompressor loops exactly `58 * 28 = 1624` times. There are no tests verifying that it terminates exactly at 1,624 tiles, ignoring padding bits in the final byte.

---

## 2. Boundary and Corner Cases Not Covered

The following extreme or unusual levels are not covered by any tests:
1.  **Minimal Level Compression (All Empty/Spaces)**:
    *   A map containing 1,624 spaces.
    *   This represents the absolute minimum compressed footprint (`1624` bits = `203` bytes).
2.  **Maximum Level Compression (All Walls)**:
    *   A map containing 1,624 walls.
    *   This represents a larger footprint using 2-bit codes (`3248` bits = `406` bytes).
3.  **Maximum Possible Footprint (All 6-bit Tiles)**:
    *   A map containing only "other" tiles (e.g., all doors or all generators).
    *   This represents the maximum possible compressed footprint (`9744` bits = `1218` bytes).
4.  **Bitstream Padding Alignment**:
    *   When the total number of encoded bits is not a multiple of 8, the last byte is padded with `0`s by the compressor.
    *   If the padding bits are decoded as extra tiles, it would indicate a loop control bug. We need to verify that the decompressor decodes exactly 1,624 tiles and ignores the padding.

---

## 3. Potential Vulnerabilities & Safety Risks

### A. Bitstream Buffer Overrun (Out-of-Bounds Read)
*   **Vulnerability**: The decompressor (`dandy_load_level`) setup is:
    ```c
    const uint8_t* src = dandy_levels[level_idx];
    ...
    bit_cache = *src++;
    ```
    There is **no length parameter** passed to `dandy_load_level`, nor is there any **bounds checking** on the `src` pointer.
*   **Risk**: If a compressed level stream is truncated or malformed such that it contains fewer than 1,624 encoded tiles, the decompressor will keep incrementing `src` and reading memory past the end of the compressed array.
*   **Impact**:
    *   **Information Disclosure**: Reading arbitrary bytes from the data segment and writing them to the map.
    *   **Denial of Service (Crash)**: If the out-of-bounds read crosses a page boundary into unmapped memory, it will trigger a Segmentation Fault (`SIGSEGV`) and crash the game.

### B. Lack of Validation of Decoded Tile IDs
*   **Vulnerability**: The 4-bit tile ID is decoded from the bitstream as:
    ```c
    uint8_t tile_id = 0;
    // Decode 4 bits...
    *dst = tile_id;
    ```
*   **Risk**: While a 4-bit value is naturally bounded to `[0, 15]`, which corresponds to the valid tile constants (`TILE_SPACE` to `TILE_GENERATOR3`), there is no validation of the decoded tile types. If future engine modifications introduce new tile constants or reduce the valid range, a malformed level could inject unexpected tiles.

---

## 4. Proposed Adversarial Test Plan

To address these gaps, we will implement a dedicated test suite `tests/test_adversarial_compression.py` that will:
1.  **Inject custom compressed levels** directly into the running C engine by binding to the global `dandy_levels` array using `ctypes`.
2.  **Verify Boundary Compression**: Test maps with 100% spaces, 100% walls, and 100% doors to verify correctness and footprint limits.
3.  **Verify Bitstream Padding**: Test a map with 1,623 spaces and 1 wall (requiring exactly 1625 bits, ending on a non-byte boundary) to verify that the decompressor ignores padding bits.
4.  **Expose Truncated Bitstream Vulnerability**: Test with a truncated level array (e.g., only 1 byte long) and show that the engine reads out-of-bounds, documenting the behavior.
