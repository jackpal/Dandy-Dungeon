# Offline E2E Test Infrastructure Challenge Report

This document presents the empirical stress-testing design, execution results, vulnerability analysis, and final stability verdict for the Milestone 1 offline E2E test infrastructure.

## Test Script Design & Implementation
A comprehensive stress-test script `dandy-gb/tests/test_infra_stress.py` was executed to challenge the robustness of the test harness (`DandyEnv`, `mock_hal.c`, and the underlying game engine).

The test suite consists of five critical assertions:
1. **Lifecycle and Leak Stability (`test_lifecycle_and_leak_stability_1000_runs`)**:
   - Loops 1000 times, instantiating, initializing, stepping, and deleting a `DandyEnv` instance.
   - Measures four resource vectors before and after the loop (with warm-up and explicit garbage collection):
     * **File Descriptors**: Counts open file descriptors using `/proc/self/fd`.
     * **Shared Library Mappings**: Counts active mappings of `libdandy_test.so` in `/proc/self/maps`.
     * **Temporary Folders**: Counts `/tmp/dandy_env_*` residues.
     * **RSS Memory**: Monitors RSS memory footprint using `resource.getrusage`.
2. **State Isolation (`test_state_isolation_parallel`)**:
   - Instantiates 5 concurrent environments.
   - Writes unique level numbers, player healths, and map tiles.
   - Asserts 100% state isolation and verifies that deleting environments one-by-one does not affect the remaining ones.
3. **Wrapper Robustness (`test_robustness_extreme_inputs_direct`)**:
   - Asserts that the Python wrapper correctly handles invalid player indices (IndexError) and invalid step input sizes (ValueError).
4. **Vulnerability 1: Out-of-Bounds Level Loading (`test_robustness_out_of_bounds_level_crash`)**:
   - Spawns a subprocess to load level `100` (only 26 levels exist).
   - Confirms that the engine crashes with a segmentation fault (`SIGSEGV`, exit code `-11`).
5. **Vulnerability 2: Out-of-Bounds Player Coordinate Memory Corruption (`test_robustness_out_of_bounds_player_y_corruption`)**:
   - Spawns a subprocess that forces a player's coordinates to `(10, 255)` or `(100, 29)`.
   - Modifies memory at index `2314` (which lies in the shared library's global data segment, exactly matching `row_offsets[255] + 10` or `row_offsets[29] + 100`) to a marker value `99`.
   - Steps the engine, causing `move_player()` to clear the old player position, writing `TILE_SPACE` (0) or `GET_PLAYER_TILE` to that out-of-bounds address.
   - Verifies that the global memory was silently corrupted, changing from `99` to `26`.

---

## Execution Commands & Output

### Execution Command
```bash
rm -rf tests/__pycache__ && python3 -m unittest discover -v -s tests -p "test_infra_stress.py"
```

### Raw Output Results
```
test_lifecycle_and_leak_stability_1000_runs (test_infra_stress.TestInfraStress.test_lifecycle_and_leak_stability_1000_runs)
Instantiate and delete DandyEnv 1000 times to verify no FD, library, temp dir, or memory leaks. ... 
--- Starting Lifecycle and Leak Stability Test (1000 iterations) ---
Initial state: FDs=13, Mapped Libs=0, Temp Dirs=0, RSS=2919700 KB
Stabilized state (after warmup): FDs=13, Mapped Libs=0, Temp Dirs=0, RSS=2919700 KB
Final state (after 1000 runs): FDs=13, Mapped Libs=0, Temp Dirs=0, RSS=2919700 KB
RSS Memory Growth: 0 KB
ok
test_robustness_extreme_inputs_direct (test_infra_stress.TestInfraStress.test_robustness_extreme_inputs_direct)
Test extreme and boundary inputs directly on DandyEnv python wrapper without crashing. ... 
--- Starting Direct Robustness Tests ---
ok
test_robustness_out_of_bounds_level_crash (test_infra_stress.TestInfraStress.test_robustness_out_of_bounds_level_crash)
Verify that loading an invalid level index triggers an out-of-bounds read and crashes (SIGSEGV). ... 
--- Starting Level Out-of-Bounds Crash Test (Subprocess) ---
Level OOB exit code: -11 (expected < 0 due to SIGSEGV)
Level OOB stdout: 
Level OOB stderr: 
ok
test_robustness_out_of_bounds_player_y_corruption (test_infra_stress.TestInfraStress.test_robustness_out_of_bounds_player_y_corruption)
Verify that setting an out-of-bounds player y-coordinate causes out-of-bounds writes (silent memory corruption). ... 
--- Starting Player Y Out-of-Bounds Corruption Test (Subprocess) ---
Subprocess output:
BEFORE - Memory at 2314: 99
AFTER - Memory at 2314: 26
CORRUPTION_DETECTED

Subprocess stderr:

ok
test_state_isolation_parallel (test_infra_stress.TestInfraStress.test_state_isolation_parallel)
Verify that multiple concurrent DandyEnv instances have 100% isolated states. ... 
--- Starting Parallel State Isolation Test ---
ok

----------------------------------------------------------------------
Ran 5 tests in 2.284s

OK
```

---

## Vulnerability & Bug Analysis

### 1. Out-of-Bounds Level Loading Crash (Critical Bug)
- **Vulnerability**: `dandy_load_level(uint8_t level_idx)` reads a level pointer from the global array `dandy_levels` using `level_idx` as the index. There is no bounds check on `level_idx` in C.
- **Exploitation**: Passing `level_idx = 100` (exceeding `DANDY_NUM_LEVELS` = 26) reads a garbage pointer from the read-only segment. Decompressing from this garbage pointer causes a segmentation fault (`SIGSEGV`), terminating the process (exit code `-11`).
- **Mitigation**: Add a bounds check in C before dereferencing:
  ```c
  if (level_idx >= DANDY_NUM_LEVELS) {
      level_idx = 0; // or return error
  }
  ```

### 2. Out-of-Bounds Player Coordinate Memory Corruption (High Risk Bug)
- **Vulnerability**: In `move_player()` and `do_player_buttons()`, when the player moves, the engine clears the old position by writing `TILE_SPACE` to `dandy_map[row_offsets[player_y[p_idx]] + player_x[p_idx]]`. There are no bounds checks on player coordinates when accessing `row_offsets` or `dandy_map`.
- **Exploitation**: If `player_y[0]` is set to `255`, the engine indexes `row_offsets[255]` (out-of-bounds read from `.rodata`), resulting in a garbage offset. When writing to `dandy_map`, it writes to an arbitrary address in the DLL's memory. In our test, this mutated memory index `2314` (located inside the library's data segment) from `99` to `26`, confirming silent memory corruption.
- **Mitigation**: Add coordinate validation inside the setter or immediately inside the C step and movement functions.

---

## Infrastructure Stability Verdict

### 1. Test Harness (`DandyEnv` and `mock_hal.c`)
- **Isolation**: **100% Excellent**. The Copy-on-Load mechanism (copying `libdandy_test.so` to a unique temporary folder and loading it via `ctypes.CDLL`) successfully isolates the static global states of multiple environments running concurrently.
- **Resource Management**: **100% Perfect**. The `__del__` destructor successfully unloads the shared library via `_ctypes.dlclose(self._lib._handle)` and recursively removes the temporary folder. Zero file descriptors, zero shared library mappings, and zero temporary directory residues are leaked after 1000 instantiations. Memory remains completely stable.

### 2. Core Game Engine (`dandy_core.c`)
- **Robustness**: **FAIL / HIGH RISK**. The core C engine relies on the caller (or GBDK hardware) to guarantee valid level indices and player coordinates. If invalid states are injected, the engine crashes or silently corrupts global variables.

### Recommendation
The **Offline E2E test infrastructure (Milestone 1) is highly stable, robust, and leak-free**. The Python wrapper successfully isolates and cleans up all C-level resources. However, the **underlying C game engine is vulnerable to memory corruption and crashes** under invalid states. The test infrastructure should be preserved, but the core game engine must be patched with proper input validation.
