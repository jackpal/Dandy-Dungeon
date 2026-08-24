# Milestone 4 Build System Remediation (Round 2) - Adversarial Stress Test Report

**Overall Verdict**: **FAIL**

This report summarizes the empirical stress-testing and adversarial review of the second round of build system fixes in `dandy-gb/Makefile`. While some improvements were made (e.g., using separate object directories `obj` and `obj_dark` to avoid object file collisions between normal and dark modes), the build system still suffers from critical parallel build races, clean target integrity violations, and broken test dependencies.

---

## 1. Stress-Testing Methodology

To rigorously evaluate the build system, a Python stress-testing harness (`tests/stress_test_parallel.py`) was implemented and executed for 10 iterations across the following scenarios:

1. **Scenario 1 (Parallel Clean Build)**: `make clean && make -j8 all dark`
   - Evaluates whether a single parallel build invocation correctly manages internal dependencies and compiles both ROMs without race conditions or compiler collisions.
2. **Scenario 2 (Concurrent Parallel Build)**: `make clean && (make -j8 all & make -j8 dark; wait)`
   - Evaluates whether concurrent top-level `make` processes running in the same directory collide on shared intermediate files (`src/levels.c`, `src/tiles.c`, etc.) or object directories.
3. **Clean Target Integrity Check**:
   - Compiles the project, runs the tests to generate all three PNG assets (`downscale_preview.png`, `graphics_audit.png`, `graphics_audit_dark.png`), executes `make clean`, and verifies that:
     - All three generated files are successfully deleted.
     - No git-tracked assets are deleted or modified.
4. **Test Suite Dependency & Resource Leak Audit**:
   - Runs `make test` and `make test_emu` repeatedly (3 consecutive times) starting from a clean state, checking for stability, temporary file/directory leaks in `/tmp`, and process leaks (e.g., orphaned `pyboy` or `python` processes).

---

## 2. Detailed Findings & Vulnerabilities

### 🔴 Finding 1: Critical Race Conditions & Write Collisions in Concurrent Builds (Scenario 2)
- **Severity**: **CRITICAL**
- **Symptom**: Under concurrent parallel builds (`make -j8 all & make -j8 dark`), the build fails in **40% of the iterations** with compiler errors and undefined identifier warnings.
- **Attack Scenario**: Two concurrent top-level make invocations write to the same intermediate source/header files (`src/tiles.h`, `src/levels.h`) and object files in `obj/` at the same time.
- **Impact**: One process truncates/writes to `src/tiles.h` while the other is compiling `src/main.c`. This causes the compiler to read a partially written header, resulting in syntax errors or `undefined identifier` errors.
- **Evidence (Verbatim Logs)**:
  - *Iteration 2*:
    ```
    make: *** [Makefile:60: obj/dandy_core.o] Error 1
    ROMs built: dandy.gb=True, dandy_dark.gb=False (Dark ROM failed to build!)
    ```
  - *Iteration 3*:
    ```
    make: *** [Makefile:60: obj/main.o] Error 1
    make: *** Waiting for unfinished jobs....
    Errors: ['(?i)undefined identifier']
    ```
- **Analysis**:
  - The `dark` target is defined as:
    ```makefile
    dark: all
    	$(MAKE) USE_BLACK_FLOOR=1 all
    ```
    When running `make -j8 dark`, it first builds the dependency `all`. Therefore, it runs a full compilation of `all` using the default mode (writing to `obj/` and compiling `bin/dandy.gb`).
    At the same time, `make -j8 all` is running. Both processes are compiling the exact same files into the exact same paths concurrently.
    Furthermore, GNU Make rules with multiple targets like `src/levels.c src/levels.h: ...` are treated as two separate rules. Thus, even a single parallel `make -j8` invocation runs the Python converter script twice concurrently. While a single invocation got lucky and succeeded, under concurrent builds this exacerbates the race.

### 🟡 Finding 2: Clean Target Integrity Violation (Deletes Git-Tracked Assets)
- **Severity**: **MEDIUM**
- **Symptom**: `make clean` deletes a git-tracked asset (`tests/mock_gb/gb/gb.h`), leaving the git repository dirty with deleted files.
- **Impact**: Any attempt to build or run tests after `make clean` will fail or be forced to regenerate/restore the file, violating the rule that `make clean` must only remove generated artifacts and never delete tracked source files.
- **Evidence (Verbatim Status)**:
  ```
  FAIL: Git-tracked files were deleted: [' D dandy-gb/src/levels.c', ' D dandy-gb/src/levels.h', ' D dandy-gb/src/tiles.c', ' D dandy-gb/src/tiles.h', ' D dandy-gb/tests/mock_gb/gb/gb.h']
  ```
- **Analysis**:
  - The `clean` target in the Makefile contains:
    ```makefile
    clean:
    	...
    	rm -rf tests/mock_gb tests/.temp_envs
    ```
    This recursively deletes the entire `tests/mock_gb` directory, which contains the checked-in file `tests/mock_gb/gb/gb.h`.

### 🟡 Finding 3: Broken Dependency in Test Target (`make clean && make test` fails)
- **Severity**: **MEDIUM**
- **Symptom**: Running `make clean && make test` fails immediately on a clean repository.
- **Impact**: Users or automated CI pipelines cannot run tests immediately after cleaning or cloning without running a full build first, due to missing dependencies.
- **Evidence (Verbatim Logs)**:
  ```
  ERROR: test_independent_tile_decoding (test_graphics_pipeline.TestGraphicsPipeline.test_independent_tile_decoding)
  FileNotFoundError: [Errno 2] No such file or directory: '/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb/src/tiles.c'
  ```
- **Analysis**:
  - In `Makefile`, `test_lib` only depends on `levels` but not `sprites`:
    ```makefile
    test_lib: levels
    	...
    ```
    However, the graphics tests require `src/tiles.c` and `src/tiles.h` to exist. Because `test_lib` does not depend on `sprites`, `src/tiles.c` is not generated during `make test`, causing the tests to crash.

---

## 3. Stress Test Results Summary

| Scenario | Iterations | Pass Rate | Observed Failure Modes | Verdict |
|---|---|---|---|---|
| **Scenario 1**: `make clean && make -j8 all dark` | 10 | 100% | None (lucky synchronization in single sub-make sequence) | **PASS** |
| **Scenario 2**: `make -j8 all & make -j8 dark; wait` | 10 | 60% | Compiler errors (`Error 1`), `undefined identifier` warnings, missing `dandy_dark.gb` | **FAIL** |
| **Test 3**: Clean Target Integrity | 1 | 0% | Deletion of git-tracked `tests/mock_gb/gb/gb.h` | **FAIL** |
| **Test 4**: Test Suite Leak & Stability | 3 | 0% | Crashes immediately on clean run due to missing `sprites` dependency | **FAIL** |

---

## 4. Suggested Mitigations

1. **Resolve Multiple-Target Parallelism Rule**:
   - Use grouped targets (supported in GNU Make 4.3+) or a pattern rule to ensure multiple outputs of the python scripts are treated as a single recipe execution:
     ```makefile
     src/levels.c src/levels.h &: $(TOOLS_DIR)/convert_levels.py ../dandy-js/levels.js
     	python3 $(TOOLS_DIR)/convert_levels.py
     ```
     Or use a sentinel/stamp file to serialize them safely.
2. **Prevent Concurrent Build Collision**:
   - Eliminate the top-level dependency of `dark` on `all` if possible, or use a lockfile (e.g., using `flock` or a directory-based lock) to serialize concurrent builds when they run in the same workspace.
   - Alternatively, make `dark` build everything in a separate build workspace or use unique target names.
3. **Fix Clean Target**:
   - Do not delete `tests/mock_gb` entirely. Instead, only delete the files generated by the Makefile, or avoid checking in `tests/mock_gb/gb/gb.h` if it is meant to be generated.
4. **Fix Test Dependencies**:
   - Update `test_lib` to depend on both `levels` and `sprites`:
     ```makefile
     test_lib: levels sprites
     ```
