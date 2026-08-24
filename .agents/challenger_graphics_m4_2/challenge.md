# Challenge Report — Milestone 4 (Palette & Sprite Integration)

## Challenge Summary

**Overall risk assessment**: HIGH

While the core Downscale Compiler and Palette Integration codebases are exceptionally robust and pass all unit tests, the build system suffers from a critical parallel execution vulnerability. Furthermore, running multiple challenger agents concurrently in the same physical git workspace leads to a severe split-brain state corruption.

**Verdict**: **FAIL** (on Build System Robustness and Integration; PASS on Compiler Robustness and Temp Leak Checks).

---

## Challenges

### [Critical] Challenge 1: Parallel Build Race Condition (Makefile Vulnerability)

- **Assumption challenged**: The assumption that the Makefile prerequisites sequence `all: setup levels sprites $(BIN_DIR)/$(ROM_NAME)` guarantees sequential execution under all developer environments.
- **Attack scenario**: A developer (or CI system) runs `make -j8` after modifying level data or sprites.
- **Blast radius**: 
  1. **Stale Data Compilation**: The compilation of `obj/levels.o` and `obj/tiles.o` runs in parallel with the code generators `convert_levels.py` and `downscale_sprites.py`. Because `make clean` does not delete the generated files `src/levels.c`/`src/tiles.c`, the compiler silently compiles `obj/levels.o` using the **stale** levels from the previous build. The new levels are written afterwards, but `make` does not recompile them in future runs because the object files are newer than the source files! The developer gets a stale ROM without knowing why.
  2. **Compilation Failure**: Under clean parallel builds, the compilation of `obj_dark/main.o` can start before the `setup` target finishes running `mkdir -p obj_dark`, causing the compiler to fail with: `Failed to open output file 'obj_dark/main.asm' (No such file or directory)`.
- **Mitigation**:
  - Add explicit file-to-target dependencies in the `Makefile`:
    ```makefile
    # Ensure build directories exist before any object is compiled
    $(OBJS): | setup

    # Declare dependencies for generated files
    src/levels.c src/levels.h: levels
    src/tiles.c src/tiles.h: sprites

    # Object dependencies
    $(OBJ_DIR)/levels.o: src/levels.c src/levels.h
    $(OBJ_DIR)/tiles.o: src/tiles.c src/tiles.h
    ```
  - Modify `clean` target to delete all generated source/header files:
    ```makefile
    clean:
    	rm -rf obj obj_dark $(BIN_DIR)
    	rm -f src/levels.c src/levels.h src/tiles.c src/tiles.h
    ```

### [Critical] Challenge 2: Split-Brain Shared Workspace Corruption

- **Assumption challenged**: The assumption that multiple Stellar Teamwork agent instances can safely operate concurrently in a single shared git workspace.
- **Attack scenario**: The orchestrator spawns `challenger_graphics_m4_1` and `challenger_graphics_m4_2` concurrently. Both agents run `make clean`, `make`, and `make dark` in the same shared directory `/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb/`.
- **Blast radius**: Extreme flakiness and build corruption. One agent's `make clean` deletes directories (`obj_dark`, `obj`) while the other agent is compiling, leading to `No such file or directory` compiler crashes, undefined symbol linker warnings, and corrupted ROMs.
- **Mitigation**: The Stellar Teamwork orchestrator must isolate workspace directories for each concurrent agent (e.g. by cloning the repository to separate temporary directories for each agent run) or enforce strict serialized locking on the shared workspace.

---

## Stress Test Results

### 1. Build System Toggling
- **Scenario**: Clean build Classic DMG, then build Atmospheric Dark, modify `src/main.c`, and rebuild both.
- **Expected behavior**: Toggling between modes compiles objects in their respective directories (`obj/` vs `obj_dark/`) and only recompiles modified files.
- **Actual behavior**: **PASS** (when run sequentially without split-brain concurrency). Object directories are correctly separated. Modifying `src/main.c` only rebuilds `main.o` and relinks the ROM.

### 2. Downscale Compiler Robustness
- **Scenario**: Run `downscale_sprites.py` with out-of-bounds parameters, missing files, empty files, non-PNG text files, and wrong image dimensions.
- **Expected behavior**: Compiler rejects invalid inputs gracefully with a non-zero exit code and error messages.
- **Actual behavior**: **PASS**. The compiler successfully rejected all invalid inputs with exit code 1 and printed helpful error messages.

### 3. Clean Build Memory & Temp Leak Stress Test
- **Scenario**: Compile `make clean && make` 10 times in a loop, monitoring `/tmp` and the workspace.
- **Expected behavior**: No temporary files/directories leaked in `/tmp` or left untracked in the workspace after `make clean`.
- **Actual behavior**: **PASS**. 0 leaks detected in `/tmp` or the workspace over 10 clean builds.

### 4. Graphics Pipeline Test Suite & Temp Leaks
- **Scenario**: Run the entire 176-test suite (`make test`) and monitor `/tmp` for leaked directories.
- **Expected behavior**: All tests pass, and all temporary directories created in `/tmp` (e.g., `/tmp/tmp_lu53wnv/`) are cleaned up.
- **Actual behavior**: **PASS**. All 176 tests passed. All temporary directories in `/tmp` were successfully deleted on teardown.

---

## Unchallenged Areas

- **Emscripten / WebAssembly Pipeline**: The Emscripten compilation target (`make web`) was not stress-tested or compiled due to the lack of an `emcc` compiler in the local testing environment.
- **PyBoy Emulator Tests**: Emulator E2E tests (`make test_emu`) were not fully stress-tested in this run, as unit tests (`make test`) provided sufficient coverage of the graphics pipeline and parser.
