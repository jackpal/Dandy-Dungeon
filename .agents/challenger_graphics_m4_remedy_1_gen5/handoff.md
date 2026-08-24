# Handoff Report - Challenger 1 (graphics_m4_remedy)

## 1. Observation
- **Concurrent build race condition**:
  Running `make -j8 all dark` (or concurrent `make -j8 all & make -j8 dark; wait`) triggers consistent compiler errors:
  ```
  src/main.c:51: error 20: Undefined identifier 'DANDY_NUM_TILES'
  src/main.c:51: error 20: Undefined identifier 'dandy_tiles'
  make[1]: *** [Makefile:60: obj_dark/main.o] Error 1
  ```
  Both commands spawn concurrent compilations and executions of `downscale_sprites.py` and `convert_levels.py`, which write to the same shared files `src/tiles.c`, `src/tiles.h`, `src/levels.c`, and `src/levels.h`.
- **Incremental Compilation**:
  - Deleting `src/tiles.c` and running `make all` rebuilt only `obj/tiles.o` and `obj/main.o` (timestamps changed from `1782006859` to `1782006860`). Others (`obj/dandy_core.o`, etc.) remained at `1782006859`.
  - Deleting `src/levels.c` and running `make all` rebuilt only `obj/levels.o` and `obj/dandy_core.o` (timestamps changed to `1782006874`). Others remained at `1782006859/6860`.
- **Test Suite stability and leaks**:
  - 5 consecutive runs of `make test` and `make test_emu` all passed (100% stability, no flakiness).
  - No temporary file leaks in `/tmp` and no leaked python/pyboy processes.
  - Three generated files are left behind after `make clean`:
    `?? dandy-gb/teamwork_graphics/downscale_preview.png`
    `AM dandy-gb/teamwork_graphics/graphics_audit.png`
    `AM dandy-gb/teamwork_graphics/graphics_audit_dark.png`

## 2. Logic Chain
1. The compiler error "Undefined identifier 'DANDY_NUM_TILES'" occurs during compilation of `src/main.c` because the compiler read `src/tiles.h` while it was empty or partially written by another concurrent process (the concurrent `downscale_sprites.py` run from `make dark`).
2. Therefore, parallel compilation safety is violated when building the `all` and `dark` targets concurrently or through `make -j8 all dark`, since they both dynamically generate and write to the same shared files in `src/` without synchronization or isolation.
3. Timestamps of object files during incremental build testing show that only files directly depending on the modified/deleted source or header file are rebuilt. This proves that the dependency DAG in the Makefile is correct for incremental builds.
4. The presence of `downscale_preview.png`, `graphics_audit.png`, and `graphics_audit_dark.png` as untracked files in git status after running `make clean` shows that these build/test artifacts are omitted from the Makefile's `clean` target list.

## 3. Caveats
- I did not test ROM compatibility on real GameBoy hardware.
- I assumed the user wants clean builds of `all` and `dark` to be parallel-safe; if they are always run sequentially in different workspaces, the race condition will not occur, but for CI/CD pipelines this is a high-risk failure mode.

## 4. Conclusion
The `dandy-gb` build system is highly robust and correct for single parallel builds (e.g. `make -j8 all` or `make -j8 dark`) and incremental compilation. However, it is **unsafe for concurrent multi-target builds** due to a race condition on shared generated source files in `src/`. It also suffers from a minor workspace leak because generated preview/audit image files are not cleaned up.
Actionable mitigations:
1. Isolate target modes (e.g. write mode-specific generated assets to different folders, or use lockfiles during generation).
2. Update the `clean` rule in the Makefile to clean up all generated PNGs.

## 5. Verification Method
- **Verify Concurrent build race**: Run `make clean && make -j8 all dark` in `dandy-gb/`. It will fail with compile errors in `src/main.c`.
- **Verify Incremental builds**: Delete `src/tiles.c`, run `make all`, and verify only `obj/tiles.o` and `obj/main.o` are recompiled.
- **Verify Workspace leaks**: Run `make clean` and run `git status --ignored --porcelain` to check if `downscale_preview.png`, `graphics_audit.png`, or `graphics_audit_dark.png` are left behind.
