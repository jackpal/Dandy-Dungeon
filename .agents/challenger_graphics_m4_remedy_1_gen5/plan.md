# Stress-Testing and Empirical Challenge Plan

This plan details the steps to stress-test and challenge the robustness, parallel safety, and resource safety of the `dandy-gb` build system and test suites.

## 1. Infrastructure & Baseline Verification
- **Goal**: Establish that the environment, compiler, and tests function correctly under sequential/normal conditions.
- **Verification Steps**:
  1. Check for `gbdk` compiler presence at `~/Developer/gbdk/bin/lcc`.
  2. Run `make clean && make all` to verify classic ROM build.
  3. Run `make clean && make dark` to verify dark ROM build.
  4. Run `make test` and `make test_emu` once to ensure tests pass as a baseline.

## 2. Concurrent & Parallel Build Stress-Testing
- **Goal**: Stress-test parallel safety under high job counts and concurrent target invocations.
- **Verification Steps**:
  1. Test `make -j8 all` and `make -j8 dark` sequentially but with high parallelism to ensure internal targets (e.g. `levels` vs `sprites`) don't race.
  2. Test **concurrent execution** of `make -j8 all` and `make -j8 dark` simultaneously in the same workspace directory.
     - Since they both generate files in `src/` (`src/levels.c`, `src/tiles.c`), we expect a possible collision if they run simultaneously. We will write a wrapper script to run both in parallel and analyze whether they collide, corrupt the files, or fail.
     - Check if `obj/` and `obj_dark/` directories/targets collide or interfere.

## 3. Robustness & Dependency Stress-Testing (Incremental Builds)
- **Goal**: Verify exact dependency tracking and incremental compilation behavior.
- **Verification Steps**:
  1. Build everything.
  2. Delete `src/tiles.c` and run `make`. Verify only `src/tiles.c` is regenerated, and `obj/tiles.o` is recompiled and linked. No other `.o` files (e.g. `main.o`, `dandy_core.o`) should be recompiled.
  3. Delete `src/levels.c` and run `make`. Verify only `src/levels.c` is regenerated, and `obj/levels.o` (and dependent objects if any) are recompiled.
  4. Touch `src/dandy_core.c` and `src/gameboy_hal.c` concurrently, run `make -j8`, and verify parallel compilation.

## 4. Test Suite Resource & Leak Audit
- **Goal**: Audit `make test` and `make test_emu` for stability, flakiness, and leaks.
- **Verification Steps**:
  1. Run `make test` 5 times consecutively.
  2. Run `make test_emu` 5 times consecutively.
  3. Monitor `/tmp/` and the workspace before and after for any leftover directories or files.
  4. Audit for leaked file descriptors, subprocesses, or memory.
  5. Check for any flakiness in emulator tests.

## 5. Report & Verdict
- **Goal**: Document the results and issue a PASS/FAIL verdict.
- **Verification Steps**:
  1. Write a detailed `challenge_report.md` in the working directory.
