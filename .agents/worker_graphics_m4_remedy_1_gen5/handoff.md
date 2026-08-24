# Handoff Report: Milestone 4 Remediation (Build System Defects)

## 1. Observation
- Under the original `Makefile` (in `/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb/Makefile`), we observed:
  - `src/levels.c src/levels.h` depended on phony target `levels`:
    ```makefile
    src/levels.c src/levels.h: levels
    ```
  - `src/tiles.c src/tiles.h` depended on phony target `sprites`:
    ```makefile
    src/tiles.c src/tiles.h: sprites
    ```
  - Phony target `sprites` invoked `.venv/bin/python` without any check for `.venv` existence:
    ```makefile
    sprites:
    	@echo "Compiling downscaled sprite assets using FHDA..."
    	.venv/bin/python $(TOOLS_DIR)/downscale_sprites.py ...
    ```
  - Simulating a pristine checkout by renaming `.venv` to `.venv_backup` and running `make clean && make all` yielded:
    ```
    make: .venv/bin/python: No such file or directory
    make: *** [Makefile:72: sprites] Error 127
    ```
  - Running `make all` twice consecutively under the original configuration triggered the entire graphics and levels pipeline on both runs, even though no files had changed:
    ```
    Converting levels from JS to C header...
    python3 tools/convert_levels.py
    ...
    Compiling downscaled sprite assets using FHDA...
    .venv/bin/python tools/downscale_sprites.py ...
    ...
    /usr/local/google/home/jackpal/Developer/gbdk/bin/lcc ...
    ```

## 2. Logic Chain
- **Step 1 (Pristine Checkout Build Failure)**: The `sprites` target directly called `.venv/bin/python`. On a fresh checkout, `.venv` is missing. Hence, the command failed with Error 127 (Observation 1).
- **Step 2 (Bootstrapping Design)**: To fix this, a physical target `.venv` must be introduced to bootstrap the virtual environment. By making `src/tiles.c src/tiles.h` depend on `| .venv` (order-only), we ensure that the virtual environment is built if missing, but changes to `.venv`'s folder timestamp (e.g. installing packages) do not trigger rebuilds of the tiles.
- **Step 3 (Broken Incremental Compilation)**: GNU Make considers `.PHONY` targets to be always out-of-date. Since `src/levels.c src/levels.h` and `src/tiles.c src/tiles.h` depended on the phony targets `levels` and `sprites` respectively, GNU Make always considered the generated source/header files out-of-date (Observation 1). This forced full rebuilds on every invocation.
- **Step 4 (Incremental Compilation Fix)**: By mapping `src/levels.c src/levels.h` directly to their physical source files `$(TOOLS_DIR)/convert_levels.py` and `../dandy-js/levels.js`, and `src/tiles.c src/tiles.h` to `$(TOOLS_DIR)/downscale_sprites.py`, `teamwork_graphics/strike_original.png`, and `| .venv`, we restore correct dependency tracking. The phony targets `levels` and `sprites` are kept as convenience targets but are decoupled so they depend on the physical generated files instead of the other way around.
- **Step 5 (Dry / Clean Test Setup)**: Since `test` and `test_emu` both invoke `.venv/bin/python`, adding `| .venv` to their prerequisites ensures they run in a properly bootstrapped environment, removing redundant inline check blocks.

## 3. Caveats
No caveats. The build system behavior and E2E emulator test suite were fully verified.

## 4. Conclusion
The critical build system defects in `dandy-gb/Makefile` have been successfully fixed. A pristine checkout now bootstraps the virtual environment automatically and runs cleanly. Incremental compilation is 100% restored, ensuring that consecutive runs of `make` do not re-run scripts or rebuild files unless sources have actually changed.

## 5. Verification Method
Perform the following commands from `dandy-gb/` directory:
1. `make clean`
2. `rm -rf .venv` (to simulate pristine checkout)
3. `make all` (verifies that `.venv` is bootstrapped and the ROM `bin/dandy.gb` compiles successfully)
4. `make dark` (verifies that dark mode builds successfully)
5. `make` (incremental check: verifies that nothing is re-run or recompiled, producing no build output)
6. `touch ../dandy-js/levels.js && make` (verifies that only the levels are recompiled, followed by affected source files and re-linking)
7. `make test` (runs all unit tests; all 176 tests must pass)
8. `make test_emu` (runs all emulator tests; all 4 tests must pass)
