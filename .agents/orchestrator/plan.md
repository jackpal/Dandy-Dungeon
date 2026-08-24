# Project Plan: Dandy Dungeon Custom 2D Level Compression

This plan outlines the dual-track development process to implement a highly efficient custom 2D level compression scheme for Dandy Dungeon, enabling the game to compile into a flat 32KB GameBoy ROM with an active footprint under 28KB.

---

## Dual-Track Architecture

```
                       +----------------------------------+
                       |       Project Orchestrator       |
                       +----------------+-----------------+
                                        |
                 +----------------------+----------------------+
                 | (Parallel Track)                            | (Parallel Track)
                 v                                             v
  +--------------+---------------+              +--------------+---------------+
  |    E2E Testing Orchestrator   |              |   Implementation Track      |
  +--------------+---------------+              +--------------+---------------+
                 |                                             |
                 |                                             v
                 |                              +--------------+---------------+
                 |                              | Milestone 1: Revert & Verify |
                 |                              +--------------+---------------+
                 |                                             |
                 |                                             v
                 |                              +--------------+---------------+
                 |                              | Milestone 2: Design 2D Algo  |
                 |                              +--------------+---------------+
                 |                                             |
                 v                                             v
  +--------------+---------------+              +--------------+---------------+
  |   Tiers 1-4 Test Suite Ready |              | Milestone 3: Implement C/Py  |
  +--------------+---------------+              +--------------+---------------+
                 |                                             |
                 +----------------------+----------------------+
                                        | (Integration)
                                        v
                        +---------------+---------------+
                        | Milestone 4: Size Tuning      |
                        +---------------+---------------+
                                        |
                                        v
                        +---------------+---------------+
                        | Milestone 5: Adversarial &   |
                        |              Forensic Audit   |
                        +-------------------------------+
```

---

## Parallel Track: E2E Testing Track
The E2E Testing Track runs in parallel with the Implementation Track. It designs an opaque-box test suite based on the game's requirements and compiles a platform-independent E2E test runner linking `src/dandy_core.c` with a mock HAL.

### Test Coverage Tiers
- **Tier 1 - Feature Coverage**: Verifies that every feature works in isolation (loading all 26 levels, spawning player, moving player, picking up items, using keys on doors, triggering smart bombs, killing monsters, level transitions).
- **Tier 2 - Boundary & Corner Cases**: Verifies empty levels, max entities, player at map edges, key usage with zero keys, spawning monsters at capacity, and extreme cases.
- **Tier 3 - Cross-Feature Combinations**: Verifies interactions like shooting an arrow at a bomb tile, player moving while monsters are pathfinding, and multi-player interactions.
- **Tier 4 - Real-World Application Scenarios**: Verifies complete playthrough simulations of selected levels from start to exit.
- **Tier 5 - Adversarial Testing (Implementation Track Phase 2)**: White-box testing that reads implementation code, identifies untested branches/gaps, and stress-tests them.

---

## Implementation Track: Milestones

### Milestone 1: Build Revert & Verification Foundation
- **Goal**: Revert the build configuration to flat 32KB (no-MBC) and establish the automated verification script.
- **Tasks**:
  1. Modify `dandy-gb/Makefile` to:
     - Remove `-Wl-yo4` from `LCCFLAGS`.
     - Remove bank-switching compile flags (`-Wf-bo2` or similar) for `levels.c`.
     - Set compiler output to target flat 32KB (no MBC configuration).
  2. Modify `dandy-gb/src/dandy_core.c`:
     - Remove `SWITCH_ROM(2)` from `dandy_load_level`.
  3. Create `dandy-gb/tools/verify_compression.py`:
     - Run clean and rebuild using `make`.
     - Assert that the output `bin/dandy.gb` exists and is exactly 32,768 bytes.
     - Parse the compiler/linker map file to sum up all active code/data segments, asserting that the total size is less than 28,672 bytes (28 KB) or another appropriate threshold for the baseline (since the baseline with RLE may exceed 28KB, we must handle this gracefully, e.g., by reporting the baseline size and setting the strict 28KB check once the custom compressor is integrated).
- **Verification**: Run `verify_compression.py` and confirm the build succeeds with flat 32KB constraints.
- **Gate Criteria**:
  - ROM compiles successfully without bank switching.
  - Verification script successfully runs, measures ROM size, and parses map segments.
  - Active segment size is documented.

### Milestone 2: Design 2D Compression
- **Goal**: Perform comprehensive research and frequency analysis of the levels, evaluate multiple 2D compression algorithms (including traditional Fax MH/MR/MMR schemes), and select the optimal design for the 8-bit GameBoy.
- **Tasks**:
  1. Write a Python analysis script to analyze the 26 levels from `dandy-js/levels.js`:
     - **Tile Frequency Analysis**: Enumerate tile frequencies across all levels. Identify the most common tiles (e.g., spaces and walls) to evaluate variable-length coding.
     - **Edge Wall Elision Analysis**: Quantify the storage savings of omitting the outer border walls (first/last rows and columns, saving 176 tiles per level) and reconstructing them on-the-fly.
     - **4-Bit Tile Packing Evaluation**: Evaluate the baseline savings of packing 4-bit tile IDs (0-15) two-per-byte.
     - **Spatial Repetition**: Measure occurrence rates of 2x2, 2x3, and 4x4 meta-tiles.
  2. Perform research and comparative analysis of candidate compression schemes:
     - **Meta-Tile Dictionary + RLE**: Dictionary-based block indexing.
     - **Modified Huffman (MH)**: 1D run-length encoding with Huffman codes for run lengths.
     - **Modified READ (MR) & Modified Modified READ (MMR)**: 2D line-to-line delta-tracking schemes, encoding tile transition coordinates relative to the row directly above.
     - **Variable-Bit-Width / Variable-Length Coding**: Encoding common tiles with 1-2 bits and rarer tiles with longer sequences.
  3. Compile a **Comparative Compression Report** evaluating:
     - Compression ratio and total level database size.
     - GBDK C decompressor code size.
     - CPU execution overhead and complexity on the 8-bit Z80/GB CPU (e.g., bit-shifts, division, stack depth).
     - Trade-offs and selection of the optimal scheme.
  4. Design the selected optimal compression binary format and GBDK C decompressor algorithm.
- **Verification**: 
  - Write a prototype Python compressor/decompressor for the candidate schemes and verify 100% bit-for-bit decompression fidelity for all 26 levels.
  - Complete the Comparative Compression Report with verified numbers.
- **Gate Criteria**:
  - Comparative report is compiled and selection is justified based on GameBoy constraints.
  - Python prototype achieves 100% round-trip fidelity on all 26 levels.
  - Selected scheme's decompression algorithm is fully specified in pseudo-code.

### Milestone 3: Implement 2D Compressor & Decompressor
- **Goal**: Implement the selected optimal 2D compression pipeline in Python and the on-the-fly decompressor in GBDK C, incorporating 4-bit packing and edge wall elision.
- **Tasks**:
  1. Implement the custom 2D compressor in `dandy-gb/tools/convert_levels.py`:
     - Read `dandy-js/levels.js`.
     - Apply **Edge Wall Elision** (omit the outer 176 border tiles per level).
     - Apply **4-bit packing** (two tiles/symbols per byte) and the selected 2D/delta/entropy compression scheme on the remaining inner 58x28 grid.
     - Output the compressed levels and lookup tables/dictionaries into `src/levels.c` and `src/levels.h`.
  2. Implement the highly optimized C decompressor in `dandy-gb/src/dandy_core.c` (or a dedicated module):
     - Automatically write solid wall tiles (ID 1) into the border coordinates of `dandy_map` (first/last rows and columns) on level load.
     - Decode the compressed 4-bit packed stream directly into the inner 58x28 area of the `dandy_map` buffer.
     - Minimize emulated arithmetic, avoid dynamic RAM allocation, and ensure zero recursion.
- **Verification**:
  - Run `verify_compression.py` to assert 100% bit-for-bit round-trip fidelity for all 26 levels.
  - Clean compilation of the GameBoy ROM using the GBDK compiler (`lcc`).
- **Gate Criteria**:
  - Python round-trip verification passes successfully with 100% correctness.
  - GameBoy ROM compiles with zero errors and zero warnings.

### Milestone 4: Integration & Size Optimization
- **Goal**: Integrate the decompressor into the game, run E2E tests, and optimize for the 28KB size budget.
- **Tasks**:
  1. Run the offline E2E test suite (Tiers 1-4) against the C core engine to ensure full gameplay correctness.
  2. Run `verify_compression.py` to check the compiled ROM size and active segments.
  3. If active segments >= 28KB, perform size optimizations:
     - Optimize the Python compressor to find better meta-tile dictionaries.
     - Optimize decompressor C code size (using GBDK compiler optimizations, minimizing duplicate code, using smaller data types).
     - Identify and eliminate unused functions or assets in the game engine.
- **Verification**:
  - 100% pass rate on E2E Tiers 1-4.
  - `verify_compression.py` reports active segment size < 28KB (28,672 bytes).
- **Gate Criteria**:
  - Both correctness (E2E tests) and size constraints (< 28KB) are fully satisfied.

### Milestone 5: Adversarial Hardening & Final Audit
- **Goal**: Run adversarial tests (Tier 5), perform a forensic integrity audit, and prepare the final report.
- **Tasks**:
  1. Spawn Challengers to perform white-box analysis of the implementation:
     - Identify untested code paths in the decompressor or level loader.
     - Generate adversarial inputs/tests to stress-test the implementation.
     - Fix any uncovered issues.
  2. Spawn the Forensic Auditor to independently verify that:
     - No test results are hardcoded.
     - No dummy/facade implementations exist.
     - The compilation is genuinely flat 32KB without MBC.
     - Code behaves authentically.
  3. Compile final project metrics (compression ratio, exact ROM size, active segment sizes).
- **Verification**: Passing audit verdict from Forensic Auditor, 100% E2E test pass, size constraints met.
- **Gate Criteria**:
  - Forensic Auditor verdict is CLEAN (no integrity violations).
  - Active segment size is verified < 28KB.
  - All tests pass.
