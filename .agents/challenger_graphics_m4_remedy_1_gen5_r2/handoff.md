# Handoff Report: Milestone 4 Build System Remediation (Round 2)

This report provides the findings of the teamwork_preview_challenger (Challenger 1) on the second round of build system fixes in `dandy-gb/Makefile`.

## 1. Observation
We conducted multiple stress tests using an automated Python test harness (`tests/stress_test_parallel.py`). We observed the following:
- **Concurrent Build Failures (Scenario 2)**: Running `make -j8 all & make -j8 dark; wait` failed in 4 out of 10 iterations with the following errors in stderr:
  ```
  make: *** [Makefile:60: obj/dandy_core.o] Error 1
  ```
  and
  ```
  make: *** [Makefile:60: obj/main.o] Error 1
  make: *** Waiting for unfinished jobs....
  ```
  with `undefined identifier` warnings.
- **Git-Tracked File Deletion**: Running `make clean` deleted `tests/mock_gb/gb/gb.h`, which is a git-tracked asset in the repository.
- **Broken Test Dependency**: Running `make clean && make test` failed immediately with:
  ```
  ERROR: test_independent_tile_decoding (test_graphics_pipeline.TestGraphicsPipeline.test_independent_tile_decoding)
  FileNotFoundError: [Errno 2] No such file or directory: '/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb/src/tiles.c'
  ```
- **Grouped Target Parallelism Bug**: Even in a single parallel build invocation (`make -j8 all dark`), the converters for levels and sprites are executed twice concurrently:
  ```
  Converting levels from JS to C header...
  Converting levels from JS to C header...
  python3 tools/convert_levels.py
  python3 tools/convert_levels.py
  ```

## 2. Logic Chain
- **Scenario 2 Failure**:
  1. The `dark` target depends on `all`. Therefore, any invocation of `make -j8 dark` first runs `all` (default mode using `obj/` and compiling `bin/dandy.gb`).
  2. When run concurrently with `make -j8 all`, both top-level processes evaluate the dependency graph for `all` simultaneously.
  3. Both processes attempt to read, write, and compile the same files (`src/levels.c`, `src/tiles.c`, `obj/*.o`, `bin/dandy.gb`) concurrently without synchronization.
  4. This causes file truncation and partial write races, leading to compilation failures and undefined identifier errors.
- **Git-Tracked Deletion**:
  1. `make clean` executes `rm -rf tests/mock_gb tests/.temp_envs`.
  2. The file `tests/mock_gb/gb/gb.h` is a tracked asset.
  3. Thus, `make clean` deletes a tracked asset, leaving the git tree dirty.
- **Broken Test Dependency**:
  1. The `test` target depends on `test_lib`, which depends on `levels`.
  2. `test_lib` does NOT depend on `sprites`.
  3. However, the tests run by `make test` import `verify_graphics` which expects `src/tiles.c` and `src/tiles.h` to exist.
  4. Therefore, running `make clean && make test` crashes because `src/tiles.c` is never generated.

## 3. Caveats
- Testing was performed on a Linux system with 8 parallel jobs (`-j8`). Results could vary under different core counts or under slower/faster disk I/O, but the race condition is mathematically guaranteed due to the lack of lockfiles or file isolation.
- Web target WASM compilation was not parallel-tested in detail but uses the same shared files and would likely exhibit similar race conditions if built concurrently.

## 4. Conclusion
The second round of build system fixes **FAILS** the validation. The build system is not parallel-safe under concurrent invocations, deletes git-tracked assets during cleanup, and has broken dependencies that prevent running tests from a clean slate.

## 5. Verification Method
To reproduce these failures independently, run the following commands in `dandy-gb/`:

1. **Verify Concurrent Build Race**:
   ```bash
   # Run multiple times to trigger the race (usually fails within 1-3 attempts)
   make clean && (make -j8 all & make -j8 dark; wait)
   ```
2. **Verify Git-Tracked Asset Deletion**:
   ```bash
   make clean
   git status --porcelain | grep "D "
   # You will see 'D dandy-gb/tests/mock_gb/gb/gb.h' showing up as deleted
   ```
3. **Verify Test Dependency Failure**:
   ```bash
   make clean && make test
   # The test suite will fail to run with FileNotFoundError on src/tiles.c
   ```
