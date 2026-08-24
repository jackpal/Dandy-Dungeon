# Empirical Verification Plan - Milestone 4 (Palette & Sprite Integration)

This plan details the steps to verify the correctness and stress-test the Milestone 4 implementation.

## Phase 1: Context & Inspection
1. **Inspect Codebase Changes**:
   - Inspect `dandy-gb/src/main.c` to check palette configuration.
   - Inspect `dandy-gb/tools/downscale_sprites.py` (or downscale package) to check compile pipeline.
   - Read the changes made to the Makefile for building normal and dark ROMs.

## Phase 2: Build System & Preprocessor Stress-Testing
1. **Recompilation Verification (Stale Objects Check)**:
   - Run `make clean`.
   - Run `make` (Classic DMG). Check the timestamp of object files in `obj/` and `bin/dandy.gb`.
   - Run `make dark` (Atmospheric Mode). Check that objects are built in `obj_dark/` and `bin/dandy_dark.gb` exists.
   - Modify a source file (e.g., add a comment in `src/main.c`), run `make`, verify ONLY files under `obj/` (and the final ROM) are rebuilt.
   - Run `make dark`, verify ONLY files under `obj_dark/` are rebuilt.
   - Verify that there is absolutely no pollution or stale object reuse between the two modes.
2. **Robustness against Corrupt/Invalid Inputs**:
   - Provide an invalid/corrupt image file as input to `downscale_sprites.py`.
   - Provide a non-existent file as input.
   - Provide an image of incorrect dimensions/format.
   - Verify that the tool returns a non-zero exit code and outputs a clear error message, rather than crashing or writing invalid files.
3. **Clean Build Stress Test (Leak Check)**:
   - Run a loop that compiles the project 10 times (`make clean && make && make dark`).
   - Monitor system resource usage or verify that no temporary directories or dangling files are left behind.
   - Specifically check for any memory leaks or high temp directory accumulation.

## Phase 3: Graphics Pipeline & Adversarial Stress-Testing
1. **Test for Temporary Directory Leaks**:
   - Check if the test suite or downscale tool leaks directories in `/tmp` or `tests/` (e.g. `.temp_envs`, `mock_gb`).
   - Run `make test` and check for created directories or files.
2. **Extreme / Adversarial Inputs**:
   - Examine `tests/test_graphics_adversarial.py` or similar to see what is already tested.
   - Run the adversarial tests specifically and verify their outcomes.
   - Inspect the generated audit or visual comparisons if possible.

## Phase 4: Final Verdict & Reporting
1. **Verification Verdict**: Determine PASS or FAIL.
2. **Generate Reports**:
   - `challenge.md` containing the detailed Challenge Report (Adversarial Review format).
   - `handoff.md` following the 5-component handoff report.
3. **Notify Parent**: Send message to original parent agent.
