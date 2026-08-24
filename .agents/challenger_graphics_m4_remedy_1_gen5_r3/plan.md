# Plan — Challenger 1 (Milestone 4 Remediation Round 3)

We will stress-test the build system in `dandy-gb/Makefile` to verify parallel safety, clean target completeness, and resource safety.

## Step 1: Concurrent & Parallel Build Stress-Testing
1. Clean the project: `make clean`
2. Run parallel clean build: `make -j8 all dark` and capture the log.
3. Run concurrent parallel builds: `make -j8 all & make -j8 dark; wait` and capture the log.
4. Run the 5-iteration parallel compilation stress test loop:
   ```bash
   for i in {1..5}; do
     make clean
     (make -j8 all & make -j8 dark; wait) || exit 1
   done
   ```
5. Analyze the output logs for:
   - Compile errors
   - Warnings about undefined identifiers
   - File write collisions (e.g., race conditions on `levels.c`/`tiles.c`)
6. Verify that both ROMs (`bin/dandy.gb`, `bin/dandy_dark.gb`) exist and are non-empty after the build.

## Step 2: Clean Target Integrity Check
1. Compile the project and run the tests to generate all preview and audit PNG files.
2. Run `make clean`.
3. Check the git status and presence of key files:
   - Confirm `tests/mock_gb/gb/gb.h` is present and unmodified.
   - Confirm `.levels.lock`, `.sprites.lock`, and generated PNG files (`teamwork_graphics/downscale_preview.png`, `teamwork_graphics/graphics_audit.png`, `teamwork_graphics/graphics_audit_dark.png`) are deleted.
   - Confirm no other git-tracked assets are deleted or modified.

## Step 3: Test Suite Dependency & Resource Leak Audit
1. Run `make clean`.
2. Run `make test` immediately after clean and verify it compiles `libdandy_test.so`, generates sprites/levels, and runs the 176 unit tests successfully.
3. Check the state of `/tmp/` and the workspace before and after running `make test` and `make test_emu` 3 times.
4. Verify that:
   - No temporary directories are leaked in `/tmp/` or the workspace.
   - No zombie processes, leaked file descriptors, or resources are left.
   - Tests are 100% stable (3 consecutive successful runs).

## Step 4: Reports & Handoff
1. Compile findings into `challenge_report.md` in our working directory.
2. Formulate the final PASS/FAIL verdict.
3. Write `handoff.md` following the 5-component Handoff Protocol.
