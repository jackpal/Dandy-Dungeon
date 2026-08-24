# Execution Plan — Size-Bounded Level Decompressor

This plan outlines the steps to implement a robust, size-bounded level decompressor in Dandy Dungeon, eliminating the Out-of-Bounds Read vulnerability while adhering to strict GameBoy size and performance constraints.

## Step 1: Update the Level Compiler (`tools/convert_levels.py`)
- Modify `tools/convert_levels.py` to calculate the exact compressed size of each level.
- Declare `extern const uint16_t dandy_level_sizes[DANDY_NUM_LEVELS];` in `src/levels.h`.
- Define `const uint16_t dandy_level_sizes[DANDY_NUM_LEVELS] = { sizeof(dandy_level_0), sizeof(dandy_level_1), ... };` in `src/levels.c`.
- **Verification**: Run `python3 tools/convert_levels.py` and inspect `src/levels.h` and `src/levels.c` to confirm correct syntax and sizes.

## Step 2: Implement Boundary Checks in the Core Decompressor (`src/dandy_core.c`)
- Retrieve the level's end pointer: `const uint8_t* src_end = src + dandy_level_sizes[level_idx];`.
- On every byte read (`bit_count == 0` check), verify if `src < src_end`.
- If `src < src_end`, load the next byte with `*src++`.
- If `src >= src_end` (end-of-stream / truncation), do not read from memory and set `bit_cache = 0`.
- Implement this check efficiently at all 6 byte-reading sites in `dandy_load_level`.
- **Verification**: Run `make clean && make test_lib` to verify that it compiles cleanly with gcc.

## Step 3: Update the Adversarial Test Suite (`tests/test_adversarial_compression.py`)
- Bind to the new global array `dandy_level_sizes` in `setUp()` using `ctypes`.
- Make the memory page containing `dandy_level_sizes` writable using `mprotect`.
- Update `test_adv04_truncated_bitstream_oob_read`:
  - Set `self.dandy_level_sizes[0] = 10`.
  - Assert that all inner tiles are safely decoded as `TILE_SPACE` (0) and no tiles are decoded as `TILE_GENERATOR3` (15) from the out-of-bounds region.
- **Verification**: Run `make test` to verify all 124 tests pass, especially `test_adv04_truncated_bitstream_oob_read`.

## Step 4: Full Build and E2E Verification
- Run the full GameBoy ROM compilation: `make clean && make`.
- Verify the build results and run the E2E verification pipeline:
  `python3 tools/verify_compression.py`
- Assert that:
  - The ROM compiles successfully.
  - The ROM size is exactly 32,768 bytes.
  - The active ROM segment footprint is under 28KB (28,672 bytes).
  - All E2E tests pass successfully.
