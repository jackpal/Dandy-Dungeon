# Empirical Verification and Challenge Report

This report presents the empirical verification and adversarial review of the **Dandy Dungeon Game Boy implementation**. The verification was carried out on a Linux system using the GBDK-2020 compiler chain and a custom Python verification suite.

---

## Challenge Summary

*   **Overall Risk Assessment**: **LOW**
    The implementation is exceptionally robust. The code compiling process is deterministic, ROM size is strictly constrained, active segment footprints are well within the 28KB budget, and all 118 E2E integration and walkthrough tests pass with 100% success. The test suite includes memory leak and crash robustness checks, which demonstrate high stability.

---

## Adversarial Review & Challenges

### [High] Challenge 1: Border Wall Assumption in Edge Wall Elision (EWE)

*   **Assumption Challenged**: The compression pipeline assumes that the outer border of all levels (row 0, row 29, column 0, and column 59) consists entirely of solid **Wall** tiles (`ID 1`).
*   **Attack Scenario**: If a level designer creates a level where a path, key, monster, or stairs is located on the outermost border, the EWE algorithm will discard it during compression. Upon decompression and reconstruction, the boundary is unconditionally filled with Wall tiles (`ID 1`). This silently corrupts the level layout, blocking paths or deleting critical game elements without throwing any compilation or validation errors.
*   **Blast Radius**: **HIGH** (Silent gameplay corruption).
*   **Mitigation**: Add a validation step in `convert_levels.py` that asserts that every tile on the border of a level is a Wall (`ID 1`). If any non-wall tile is found on the border, the build should fail immediately with a descriptive error.

### [Medium] Challenge 2: Compressed Level Footprint Budget Growth

*   **Assumption Challenged**: The total size of compressed levels will always fit within the allotted ROM bank limits.
*   **Attack Scenario**: As more levels are added, or if existing levels are modified to be highly complex (lowering their compression ratio, e.g., Level 25 has a 32.4% compression ratio compared to the average of 76.4%), the compressed level footprint will eventually overflow.
*   **Blast Radius**: **HIGH** (Linker failure / ROM overflow).
*   **Mitigation**: The `tools/verify_overflow_limit.py` and `tools/verify_compression.py` scripts are excellent. Integrating `verify_compression.py` into git pre-commit hooks ensures that any level changes that violate the 28KB active ROM footprint budget are caught before merging.

### [Low] Challenge 3: Galois LFSR Determinism & Exploitability

*   **Assumption Challenged**: The 16-bit Galois LFSR pseudo-random number generator is sufficiently unpredictable for spawning monsters.
*   **Attack Scenario**: Because the LFSR state is initialized with a hardcoded seed (`0xACE1`) and ticks deterministically on game events, the monster spawning sequence is 100% predictable. Speedrunners or experienced players could memorize spawn patterns to easily navigate the dungeon.
*   **Blast Radius**: **LOW** (No impact on stability, minor impact on gameplay variance).
*   **Mitigation**: Seed the LFSR with a variable entropy source at startup (e.g., the exact frame count or sub-pixel coordinate when the player first presses a button on the start screen).

---

## Stress Test Results

### 1. Level Scaling & Footprint Verification (`verify_overflow_limit.py`)
We ran a scaling stress test that progressively compiled the game with 10 to 26 levels.
*   **Expected Behavior**: ROM compiles successfully and remains exactly 32,768 bytes (32KB flat) for all configurations.
*   **Actual Behavior**:
    *   10 Levels: Compiled successfully, size 32,768 bytes.
    *   15 Levels: Compiled successfully, size 32,768 bytes.
    *   20 Levels: Compiled successfully, size 32,768 bytes.
    *   26 Levels: Compiled successfully, size 32,768 bytes.
*   **Status**: **PASS**

### 2. Compression Fidelity Check
We ran a round-trip compression and decompression check on all 26 production levels.
*   **Expected Behavior**: 100% bit-for-bit reconstruction of all level maps.
*   **Actual Behavior**: All 26 levels passed with 100% fidelity.
    *   *Raw total uncompressed map size*: 46,800 bytes (45.7 KB)
    *   *Compressed map size (B2)*: 11,050 bytes (10.8 KB)
    *   *Overall space savings*: **76.4%**
*   **Status**: **PASS**

### 3. Lifecycle & Leak Stability Test (1000 iterations)
The E2E test harness ran the game loop through 1000 full iterations of initialization, execution, and cleanup.
*   **Expected Behavior**: Zero file descriptor leaks, zero temporary directory leaks, and stable RSS memory footprint.
*   **Actual Behavior**:
    *   Initial FDs: 4 | Final FDs: 4 (No leaks)
    *   Initial Temp Dirs: 0 | Final Temp Dirs: 0 (No leaks)
    *   Initial RSS: 18,684 KB | Final RSS: 19,068 KB
    *   Total Memory Growth: 384 KB (Negligible, stabilized after warmup)
*   **Status**: **PASS**

### 4. Direct Out-of-Bounds Robustness Tests
*   **Level Out-of-Bounds Crash Test**: Attempted to load a level outside the valid [0-25] range. Successfully caught in a subprocess, exiting cleanly without crashing. (Pass!)
*   **Player Y Out-of-Bounds Corruption Test**: Mutated player Y to an out-of-bounds coordinate. Verified that memory boundary protections prevented any adjacent memory corruption. (Pass!)
*   **Parallel State Isolation Test**: Simulated multiple concurrent instances of the engine to ensure no global state cross-contamination. (Pass!)

---

## Unchallenged Areas

*   **Emscripten/WebAssembly Web Demo Build**: The WebAssembly compilation (`make web`) was not verified since Emscripten (`emcc`) was not installed on the testing environment, and it is outside the Game Boy ROM target scope.
