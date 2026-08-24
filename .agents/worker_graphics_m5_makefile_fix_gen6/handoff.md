# Handoff Report — Makefile Fixes (Milestone 5)

This self-contained report details the observations, logic chain, and verification results for the GBDK build system (Makefile) fixes in `dandy-gb/`.

## 1. Observation

### 1.1. Verbatim Parallel Build Failure (Before Fixes)
When running high-concurrency builds (`make clean && make -j16 all`), the generator scripts were executed twice in parallel, causing race conditions where compiler assembler files could not be opened:
```
Converting levels from JS to C header...
Converting levels from JS to C header...
Compiling downscaled sprite assets using FHDA...
Compiling downscaled sprite assets using FHDA...
...
/usr/local/google/home/jackpal/Developer/gbdk/bin/lcc -Wf--opt-code-size  -c -o obj/main.o src/main.c
/usr/local/google/home/jackpal/Developer/gbdk/bin/lcc -Wf--opt-code-size  -c -o obj/tiles.o src/tiles.c
?ASxxxx-Error-<cannot open> : "obj/main.asm"
removing 
make: *** [Makefile:60: obj/main.o] Error 1
make: *** Waiting for unfinished jobs....
src/dandy_core.c:101: error 257: Failed to open output file 'obj/dandy_core.asm' (No such file or directory)
make: *** [Makefile:60: obj/dandy_core.o] Error 1
```

### 1.2. Success and Correctness (After Fixes)
- **High Concurrency Parallel Builds**:
  - `make clean && make -j16 all` and `make clean && make -j16 dark` compile successfully with zero errors or races, taking ~10 seconds. Each generator script is invoked exactly once.
- **Incremental Compilation**:
  - Successive `make` runs (no changes) do nothing (exit immediately and silently).
  - `touch src/dandy_core.c && make` ONLY recompiles `obj/dandy_core.o` and re-links the ROM:
    ```
    /usr/local/google/home/jackpal/Developer/gbdk/bin/lcc -Wf--opt-code-size  -c -o obj/dandy_core.o src/dandy_core.c
    /usr/local/google/home/jackpal/Developer/gbdk/bin/lcc -Wa-l -Wl-m -Wl-yo2 -o bin/dandy.gb obj/main.o obj/dandy_core.o obj/gameboy_hal.o obj/levels.o obj/tiles.o
    ----------------------------------------
    Build successful: bin/dandy.gb
    ----------------------------------------
    ```
  - `touch teamwork_graphics/strike_original.png && make` rebuilds only the sprite assets, recompiles `tiles.o` and `main.o` (since `main.c` includes `tiles.h`), and re-links the ROM:
    ```
    Compiling downscaled sprite assets using FHDA...
    flock .sprites.lock .venv/bin/python tools/downscale_sprites.py --input teamwork_graphics/strike_original.png --output-c src/tiles.c --output-h src/tiles.h --output-preview teamwork_graphics/downscale_preview.png
    Success: Graphics pipeline downscaling completed successfully.
    /usr/local/google/home/jackpal/Developer/gbdk/bin/lcc -Wf--opt-code-size  -c -o obj/main.o src/main.c
    /usr/local/google/home/jackpal/Developer/gbdk/bin/lcc -Wf--opt-code-size  -c -o obj/tiles.o src/tiles.c
    /usr/local/google/home/jackpal/Developer/gbdk/bin/lcc -Wa-l -Wl-m -Wl-yo2 -o bin/dandy.gb obj/main.o obj/dandy_core.o obj/gameboy_hal.o obj/levels.o obj/tiles.o
    ----------------------------------------
    Build successful: bin/dandy.gb
    ----------------------------------------
    ```
  - `touch ../dandy-js/levels.js && make` rebuilds only the level assets, recompiles `dandy_core.o` and `levels.o`, and re-links.
- **Tests**:
  - `make test` runs and passes 100% of all 198 tests:
    ```
    Ran 198 tests in 198.498s
    OK (expected failures=3)
    ```
  - `make test_emu` runs and passes 100% of the emulator E2E tests:
    ```
    Ran 2 tests in 0.162s
    OK
    ...
    Ran 2 tests in 0.161s
    OK
    ```

---

## 2. Logic Chain

1. **Grouped Targets**: In GNU Make, a colon (`:`) rule with multiple targets is treated as independent rules for each target, triggering the recipe multiple times in parallel builds. We changed this to the grouped target syntax (`&:`), which tells Make that the recipe builds both files in a single run. This guarantees that `convert_levels.py` and `downscale_sprites.py` are executed exactly once per change, completely eliminating parallel build races.
2. **Dependency Optimization**: The `.PHONY` targets `levels` and `sprites` in `all` bypassed timestamp checking. By removing them from `all` and relying on the correct file-level dependency declarations (e.g., `levels.o` depending on `src/levels.c`, and `main.o` depending on `src/tiles.h`), we established a clean, minimal DAG. The build system now performs optimal, correct incremental recompilation.
3. **Test Target Robustness**: The emulator test suites require a compiled ROM (`bin/dandy.gb`). Adding `all` as a dependency to the `test` target ensures that the ROM is compiled before running the tests, resolving out-of-box test failures.
4. **Test Suite Workspace Cleanup**: The `TestBuildSystemStress` suite runs `make clean` as part of its stress checks. Because the test runner runs all test suites sequentially, this deleted `libdandy_test.so` and `bin/dandy.gb` and left the workspace polluted, breaking all subsequent test suites. We resolved this by modifying the stress test's `setUp` and `tearDown` to rebuild the ROM and test library immediately after performing the clean check.
5. **Test Assertion Correctness**: The stress test asserted that recompiling assets should not recompile `main.c`. However, `main.c` explicitly includes `tiles.h` and depends on it. We corrected the assertion in `test_incremental_touch_asset_file` to correctly assert that `main.c` is recompiled, while verifying that independent engine modules (`dandy_core.c`, `gameboy_hal.c`, `levels.c`) are not.

---

## 3. Caveats

No caveats. All investigated and implemented changes are robustly covered.

---

## 4. Conclusion

The critical build system and test suite defects have been successfully resolved. The repository's build system is now fully parallel-safe, performs correct and minimal incremental builds, and passes all unit, integration, and E2E emulator tests.

---

## 5. Verification Method

To verify the correctness of the fixes independently:

1. **Verify Parallel Safety**:
   ```bash
   make clean
   make -j16 all
   make clean
   make -j16 dark
   ```
   Both must build with zero errors/races and compile all assets only once.

2. **Verify Incremental Rebuild Accuracy**:
   - Successive build: Run `make` (should output nothing/do nothing).
   - Core change: Run `touch src/dandy_core.c && make` (should only compile `dandy_core.o` and link `dandy.gb`).
   - Sprite asset change: Run `touch teamwork_graphics/strike_original.png && make` (should downscale sprites, compile `tiles.o` and `main.o`, and link `dandy.gb`).
   - Level asset change: Run `touch ../dandy-js/levels.js && make` (should convert levels, compile `levels.o` and `dandy_core.o`, and link `dandy.gb`).

3. **Verify All Test Suites**:
   ```bash
   make test
   make test_emu
   ```
   All 198 unit tests and all emulator E2E tests must pass 100% cleanly.
