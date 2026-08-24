# Handoff Report — Milestone 4 (Palette & Sprite Integration)

## 1. Observation
- **Concurrent Processes**: Running `ps -ef` revealed another agent instance (`challenger_graphics_m4_1`) running concurrent build and test commands in the same git repository:
  ```
  jackpal  4147558   12281  0 01:27 pts/2    00:00:00 python3 /usr/local/google/home/jackpal/Developer/Dandy-Dungeon/.agents/challenger_graphics_m4_1/run_isolated_tests.py
  jackpal  4154969 4147558  0 01:30 pts/2    00:00:00 make dark
  ```
- **Intermittent Build Failures**: Under concurrent execution, compiling in Atmospheric Dark mode (`make dark`) repeatedly failed with:
  ```
  src/dandy_core.c:101: error 257: Failed to open output file 'obj_dark/dandy_core.asm' (No such file or directory)
  ```
  and
  ```
  src/main.c:94: error 257: Failed to open output file 'obj_dark/main.asm' (No such file or directory)
  ```
  Additionally, linking sometimes failed with undefined symbols from `levels.c`:
  ```
  ?ASlink-Warning-Undefined Global '_dandy_levels' referenced by module 'dandy_core'
  ```
- **Parallel Build Sequence**: Running `make clean && make -j8` succeeded, but the compiler commands for object files ran in parallel with the code generators:
  ```
  Converting levels from JS to C header...
  Compiling downscaled sprite assets using FHDA...
  python3 tools/convert_levels.py
  .venv/bin/python tools/downscale_sprites.py ...
  /usr/local/google/home/jackpal/Developer/gbdk/bin/lcc -Wf--opt-code-size  -c -o obj/main.o src/main.c
  ...
  Reading levels from ...
  Writing C source to .../src/levels.c...
  Conversion complete!
  ```
- **Makefile Analysis**: The `Makefile` defines `all: setup levels sprites $(BIN_DIR)/$(ROM_NAME)`, but does not define any dependency rules between the object files (`$(OBJS)`) and the code generation targets (`levels`, `sprites`) or directory creation (`setup`).
- **Clean Target**: The `Makefile`'s `clean` target deletes `obj`, `obj_dark`, and `bin/`, but does NOT delete the generated files `src/levels.c`, `src/levels.h`, `src/tiles.c`, or `src/tiles.h`.
- **Compiler Robustness**: Running `python3 tests/test_downscale_robustness.py` succeeded and outputted:
  ```
  PASS: outline-thickness 2.5 rejected with exit code 1. Error: Error: --outline-thickness must be between 0.0 and 2.0, got 2.5
  PASS: wrong dimension PNG rejected with exit code 1. Error: Error: Image dimensions must be multiples of 16, got 10x10
  Robustness verification PASSED!
  ```
- **Clean Build Stress Test**: Running `python3 -u tests/test_build_stress.py` compiled successfully 10 times in a loop with output:
  ```
  PASS: No temporary files/directories leaked in /tmp.
  PASS: No leaked files in workspace after make clean.
  Stress test PASSED successfully!
  ```
- **Test Suite Temp Leak Check**: Running `make test` executed 176 tests successfully and left no temporary directories (like `/tmp/tmp_lu53wnv/`) behind.

---

## 2. Logic Chain
1. **Observation**: The `Makefile` defines no dependencies between `$(OBJS)` and the generation targets (`levels`, `sprites`).
2. **Logic**: When running a parallel build (e.g. `make -j8`), GNU Make compiles the object files in parallel with generating `src/levels.c` and `src/tiles.c`.
3. **Observation**: `make clean` does not delete the generated `src/levels.c`/`src/tiles.c` files.
4. **Logic**: If those files exist from a previous build, `make` compiles the object files using the *stale* versions of `src/levels.c`/`src/tiles.c` before the new generators finish overwriting them. Once the generators finish, the new source files exist on disk, but `make` does not recompile them because the object files are already considered up to date.
5. **Conclusion**: This results in a silent correctness bug where the final ROM contains stale level/sprite data.
6. **Observation**: Multiple agent instances were running concurrently in the same git repository.
7. **Logic**: Since both agents execute destructive build commands (like `make clean`) and compile in the same shared directory, their commands overlap. For example, one agent's `make clean` deletes `obj_dark` while the other is compiling, causing `No such file or directory` compiler errors, or one overwrites `src/levels.c` while the other is compiling `levels.o`, causing undefined symbol warnings.
8. **Conclusion**: Running concurrent agents in a shared physical workspace leads to split-brain state corruption.

---

## 3. Caveats
- **Emscripten compilation**: We did not verify the Emscripten compilation pipeline (`make web`) because `emcc` is not installed on the system.
- **PyBoy Emulator tests**: We did not stress-test emulator E2E tests (`make test_emu`) in a loop.

---

## 4. Conclusion
- The Downscale Compiler and Palette hardware configurations are correct, robust, and leak-free.
- The build system (Makefile) has a **Critical parallel build vulnerability** that compiles stale level/sprite data under parallel execution (`make -j`) and can cause compilation crashes.
- The teamwork environment suffers from **Split-Brain Workspace Corruption** when multiple agents run concurrently in a shared directory.
- **Verdict**: **FAIL** (due to Makefile parallel build bugs and split-brain environment corruption; the Downscale Compiler itself is highly robust).

---

## 5. Verification Method
- **Verify Parallel Build Bug**:
  1. Clean the build: `make clean`
  2. Run a parallel build: `make -j8`
  3. Observe the output: compilation of `obj/levels.o` will start before `convert_levels.py` prints `Conversion complete!`.
- **Verify Robustness**:
  Run the robustness script: `python3 tests/test_downscale_robustness.py` (should print `Robustness verification PASSED!`).
- **Verify Leaks**:
  Run the stress test script: `python3 tests/test_build_stress.py` (should print `Stress test PASSED successfully!`).
