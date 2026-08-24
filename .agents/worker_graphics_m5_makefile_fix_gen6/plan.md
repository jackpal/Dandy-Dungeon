# Implementation Plan - Makefile Fixes

This plan outlines the steps to fix the GBDK build system defects in `dandy-gb/Makefile` and verify the changes.

## Step 1: Implement Grouped Targets (`&:`)
- Modify the rule for `src/levels.c src/levels.h` to use grouped targets syntax:
  ```makefile
  src/levels.c src/levels.h &: $(TOOLS_DIR)/convert_levels.py ../dandy-js/levels.js
  ```
- Modify the rule for `src/tiles.c src/tiles.h` to use grouped targets syntax:
  ```makefile
  src/tiles.c src/tiles.h &: $(TOOLS_DIR)/downscale_sprites.py teamwork_graphics/strike_original.png | .venv
  ```

## Step 2: Optimize Target Dependencies
- Remove the redundant `.PHONY` targets `levels` and `sprites` from the default `all` target dependencies:
  Change:
  ```makefile
  all: setup levels sprites $(BIN_DIR)/$(ROM_NAME)
  ```
  To:
  ```makefile
  all: setup $(BIN_DIR)/$(ROM_NAME)
  ```
- Keep the standalone `levels` and `sprites` targets so they can still be run manually.

## Step 3: Verify Parallel Build Safety
- Run `make clean` and then run parallel builds: `make -j16 all` and `make -j16 dark`.
- Verify they compile successfully with zero errors or races.
- Run multiple times to ensure 100% parallel safety.

## Step 4: Verify Incremental Compilation Correctness
- Run `make` successively with no changes. Verify it outputs `Nothing to be done for 'all'` and does not run any scripts or compile any C files.
- Touch `src/dandy_core.c` and run `make`. Verify it ONLY recompiles `dandy_core.o` and re-links the ROM.
- Touch `teamwork_graphics/strike_original.png` and run `make`. Verify it rebuilds `src/tiles.c`, compiles `tiles.o`, compiles `main.o` (since main.o depends on `src/tiles.h`), and re-links the ROM. Verify it does NOT compile `dandy_core.c` or `gameboy_hal.c`.

## Step 5: Run Unit and Emulator E2E Tests
- Run `make test` and verify 100% pass.
- Run `make test_emu` and verify 100% pass.

## Step 6: Documentation and Handoff
- Document all changes in `changes.md`.
- Write `handoff.md`.
- Send message to parent orchestrator.
