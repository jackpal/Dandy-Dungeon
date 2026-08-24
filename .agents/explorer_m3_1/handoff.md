# Handoff Report: Explorer Milestone 3 — 2D Compressor Design

## 1. Observation
- **File Paths and Lines**:
  - `dandy-gb/tools/convert_levels.py` (lines 53-55) contains a hardcoded limit restricting the build to the first 5 levels:
    ```python
    # Apply 16KB Bank Overflow Mitigation: limit to first 5 levels for Milestone 1 & 2
    levels = levels[:5]
    ```
  - `dandy-gb/src/dandy_core.c` (lines 135-154) contains the level loading function `dandy_load_level` which decodes the map using the old RLE format.
  - `/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/.agents/sub_orch_m3/SCOPE.md` (lines 17-28) defines the contracts for Scheme B2 + Edge Wall Elision:
    - **Map Size**: Original is 60 columns x 30 rows = 1,800 tiles.
    - **Edge Wall Elision**: Omitting the outer border (row 0, row 29, col 0, col 59) leaving the inner 58x28 grid = 1,624 tiles.
    - **Pre-fill**: Decompressor initializes the entire 1,800-byte map with Wall tiles (ID 1) before decoding.
    - **Encoding Scheme**:
      - `0` (1 bit): Space (ID 0)
      - `10` (2 bits): Wall (ID 1)
      - `11` + `xxxx` (6 bits): Other tiles (ID 2 to 15), where `xxxx` is the 4-bit tile ID.
    - **Bit Packing**: MSB-first, padded to byte boundary with 0s.

## 2. Logic Chain
- **Edge Wall Elision**: Omitting the 176 outer border tiles reduces the input size from 1,800 to 1,624 tiles (a ~9.7% reduction). Since the decompressor pre-fills the 1800-byte buffer with Wall (ID 1), any border wall is perfectly reconstructed. Slicing rows 1 to 28 (inclusive) and columns 1 to 58 (inclusive) extracts these inner 1,624 tiles in Python.
- **Scheme B2 Prefix Coding**: Variable-length coding assigns shorter codes to highly frequent tiles (floor = 1 bit, wall = 2 bits) and longer codes to rarer tiles (other = 6 bits). This reduces the average bit-width per tile to ~1.6 bits.
- **Bit Packing**: MSB-first packing places the first bit in bit 7 of the first byte, the second in bit 6, and so on. Padding the final byte with 0s ensures byte alignment.
- **26-Level ROM Footprint**: With Scheme B2 + Edge Wall Elision, all 26 levels compress to a total of ~8.5KB, which fits comfortably within a single 16KB GameBoy ROM bank. Thus, the 5-level mitigation limit in `convert_levels.py` can be safely removed, and the generator will output all 26 levels dynamically.

## 3. Caveats
- **Border Tile Homogeneity**: Assumes the outer border of all levels consists entirely of Wall (ID 1) tiles. If a level had a non-wall tile on the border, it would be lost during reconstruction. The verification script `tools/verify_compression.py` must run a full round-trip check on all 26 levels to guarantee 100% fidelity. If a mismatch occurs, it indicates a level violates this assumption (though inspection indicates they all comply).

## 4. Conclusion
- The Scheme B2 + Edge Wall Elision compression scheme is highly efficient, robust, and completely feasible. The Python-side implementation design is fully detailed in `analysis.md` and is ready for implementation by the Worker.

## 5. Verification Method
- **Implementation Verification**:
  1. Have the Worker integrate the compressor design from `analysis.md` into `tools/convert_levels.py` and remove the 5-level limit.
  2. Have the Worker update `tools/verify_compression.py` to match the new compression/decompression pipelines.
  3. Run the verification script:
     ```bash
     python3 tools/verify_compression.py
     ```
  4. Assert that the script reports:
     - `All 26 levels passed modular pipeline compression/decompression with 100% fidelity.`
     - Active ROM segment footprint is under 28KB.
