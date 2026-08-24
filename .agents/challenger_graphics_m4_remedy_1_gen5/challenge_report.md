# Milestone 4 Remediation: Build & Verification Stress-Test Challenge Report

**Overall Verdict**: **FAIL** (with 1 Critical Build Race Condition and 1 Minor Workspace Leak vulnerability found)
**Overall Risk Assessment**: **HIGH**

---

## 1. Executive Summary
As the `teamwork_preview_challenger (Challenger 1)`, I conducted an empirical, adversarial stress-testing campaign on the `dandy-gb` build system and test verification pipelines. The objective was to verify extreme robustness, parallel safety, incremental build correctness, and resource safety.

While individual sequential builds and incremental compilation dependencies are highly robust and correct, the build system **fails under concurrent/parallel execution of different target configurations** (Classic DMG vs. Atmospheric Dark Mode). A critical race condition was empirically reproduced, resulting in compiler failures. Additionally, minor workspace leaks (untracked generated images not cleaned up by `make clean`) were discovered.

---

## 2. Stress-Testing Methodology & Results

### 2.1 Concurrent & Parallel Build Stress-Testing
*   **Hypothesis**: Running parallel builds of the two ROM configurations (`make all` and `make dark`) concurrently or via a single command `make -j8 all dark` will succeed without race conditions or compiler errors.
*   **Methodology**:
    1.  **Single Parallel Build Test**: Run `make clean && make -j8 all` in a loop of 10 iterations to verify if a single parallel build is stable.
    2.  **Concurrent Parallel Build Test**: Run `make -j8 all` and `make -j8 dark` concurrently in the same workspace using a background process wrapper (`make -j8 all & make -j8 dark; wait`) for 10 iterations.
    3.  **Combined Parallel Build Test**: Run `make -j8 all dark` in a single Make invocation for 10 iterations.
*   **Empirical Results**:
    *   **Single Parallel Build (`make -j8 all`)**: **PASS** (10/10 successful iterations).
    *   **Concurrent Parallel Builds**: **FAIL** (failed consistently at iteration 1).
    *   **Combined Parallel Build (`make -j8 all dark`)**: **FAIL** (failed consistently at iteration 1).
*   **Failure Analysis & Logs**:
    During concurrent execution, both make processes attempt to run the generator scripts (`downscale_sprites.py` and `convert_levels.py`) in parallel, writing to the same shared files (`src/tiles.h`, `src/tiles.c`, `src/levels.h`, `src/levels.c`). While one process is truncating or writing to `src/tiles.h`, the compiler in the other process attempts to read it to compile `src/main.c`, resulting in compilation errors:
    ```
    /usr/local/google/home/jackpal/Developer/gbdk/bin/lcc -Wf--opt-code-size  -c -o obj/main.o src/main.c
    src/main.c:51: error 20: Undefined identifier 'DANDY_NUM_TILES'
    src/main.c:51: error 20: Undefined identifier 'dandy_tiles'
    src/main.c:51: warning 154: converting integral to pointer without a cast
    from type 'int fixed'
      to type 'const-unsigned-char generic* fixed'
    src/main.c:52: error 20: Undefined identifier 'DANDY_NUM_TILES'
    src/main.c:52: error 20: Undefined identifier 'dandy_tiles'
    src/main.c:52: warning 154: converting integral to pointer without a cast
    from type 'int fixed'
      to type 'const-unsigned-char generic* fixed'
    make: *** [Makefile:60: obj/main.o] Error 1
    ```
*   **Verdict**: **FAIL**. Parallel safety is compromised when building different configurations concurrently in the same workspace.

---

### 2.2 Robustness & Dependency Stress-Testing (Incremental Builds)
*   **Hypothesis**: The build system correctly tracks partial file modifications, and deleting or modifying a single generated source file only rebuilds the minimum set of dependents.
*   **Methodology**:
    1.  Perform a clean full build.
    2.  Delete a generated file (`src/tiles.c` or `src/levels.c`) and run `make all`.
    3.  Compare the timestamps of all object files before and after to verify that only the affected object files were rebuilt.
    4.  Touch multiple source files (`src/dandy_core.c` and `src/gameboy_hal.c`) and verify they are compiled in parallel.
*   **Empirical Results**:
    *   **Deleting `src/tiles.c`**: **PASS**.
        *   *Before timestamps*: All `.o` files at `1782006859`.
        *   *After timestamps*: `obj/tiles.o` and `obj/main.o` rebuilt (`1782006860`). `obj/dandy_core.o`, `obj/gameboy_hal.o`, and `obj/levels.o` remained unchanged at `1782006859`.
        *   *Reasoning*: `obj/main.o` correctly depends on `src/tiles.h` (which was regenerated when `src/tiles.c` was rebuilt), and `obj/tiles.o` depends on `src/tiles.c`. This is 100% correct.
    *   **Deleting `src/levels.c`**: **PASS**.
        *   *Before timestamps*: All `.o` files at `1782006859/6860`.
        *   *After timestamps*: `obj/levels.o` and `obj/dandy_core.o` rebuilt (`1782006874`). `obj/main.o`, `obj/gameboy_hal.o`, and `obj/tiles.o` remained unchanged.
        *   *Reasoning*: `obj/dandy_core.o` correctly depends on `src/levels.h`, and `obj/levels.o` depends on `src/levels.c`. This is 100% correct.
    *   **Parallel Compile on Touch**: **PASS**. Spawning `make -j8 all` after touching multiple C files successfully compiles both in parallel and links the ROM.

---

### 2.3 Test Suite Resource & Leak Audit
*   **Hypothesis**: Running the test suites (`make test` and `make test_emu`) repeatedly will not leak temporary files, workspace files, or subprocesses, and the tests are 100% stable.
*   **Methodology**:
    1.  Record the state of `/tmp`, running processes, and workspace files.
    2.  Run `make test` and `make test_emu` consecutively 5 times.
    3.  Check for leaks and stability.
*   **Empirical Results**:
    *   **Test Stability**: **PASS**. All 5 consecutive runs of both suites passed with 0 failures or flakiness.
    *   **Temporary File Leaks (`/tmp`)**: **PASS**. No leftover directories or files in `/tmp`.
    *   **Process Leaks**: **PASS**. No python or PyBoy processes were left running.
    *   **Workspace Leaks**: **FAIL** (Minor Bug).
        *   The asset pipeline compiler generates `dandy-gb/teamwork_graphics/downscale_preview.png`.
        *   The unit test suite generates audit sheets: `dandy-gb/teamwork_graphics/graphics_audit.png` and `dandy-gb/teamwork_graphics/graphics_audit_dark.png`.
        *   None of these three generated image files are deleted by `make clean`, leaving them as untracked files in the repository.

---

## 3. Detailed Challenges & Vulnerabilities Found

### [Critical] Challenge 1: Parallel Build Race Condition on Shared Generated Sources
*   **Assumption challenged**: The targets `all` and `dark` can be safely built in parallel or concurrently in the same workspace directory.
*   **Attack scenario**: A CI/CD pipeline or developer running `make -j8 all dark` or kicking off parallel jobs for Classic and Dark ROMs.
*   **Blast radius**: High. Truncated header/source files, corrupted builds, and compiler failures.
*   **Mitigation**:
    1.  Avoid spawning sub-make processes for `dark` that write to the same shared directory `src/` without synchronization.
    2.  Alternatively, place the generated files for different modes in mode-specific directories (e.g. `src_dark/` or `obj_dark/` for intermediate generated sources), or use file-locking (e.g. `flock`) in the generator scripts to prevent concurrent writes.
    3.  A simpler fix is to make the `dark` target depend on `all` sequentially, or structure the Makefile to serialize the generation of shared assets before compiling object files, though this might not prevent concurrent external make invocations.

### [Low] Challenge 2: Workspace Pollution (Missing Cleanup in `make clean`)
*   **Assumption challenged**: `make clean` returns the workspace to a pristine, untracked-free state.
*   **Attack scenario**: Repeated builds and tests pollute the developer's git tree with untracked binary image artifacts (`downscale_preview.png`, `graphics_audit.png`, `graphics_audit_dark.png`).
*   **Blast radius**: Low. Workspace clutter.
*   **Mitigation**: Update the `clean` rule in the Makefile to explicitly delete these three files:
    ```makefile
    clean:
        rm -rf obj obj_dark bin
        rm -f src/levels.c src/levels.h src/tiles.c src/tiles.h
        rm -f *.lst *.map *.sym
        rm -rf tests/mock_gb tests/.temp_envs
        rm -f libdandy_test.so
        rm -f teamwork_graphics/downscale_preview.png
        rm -f teamwork_graphics/graphics_audit.png teamwork_graphics/graphics_audit_dark.png
        @echo "Clean complete."
    ```

---

## 4. Unchallenged Areas
*   **Physical ROM Hardware compatibility**: I did not flash the generated ROMs onto physical GameBoy hardware to test performance, which was out of scope.
