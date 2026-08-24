# Audit Plan: Milestone 3 Forensic Verification

This plan outlines the step-by-step forensic checks to verify the integrity and correctness of the Milestone 3 deliverables.

## Step 1: Engine Memory Safety Verification
- **Goal**: Verify that the C engine memory safety bug in `dandy-gb/src/dandy_core.c` was correctly fixed.
- **Verification Method**:
  1. Open `dandy-gb/src/dandy_core.c` and search for `flood_stack_ptr`.
  2. Verify that its data type is `int16_t` (or similar signed 16-bit integer).
  3. Inspect all operations on `flood_stack_ptr` (increments, decrements, array indexing, and bounds checks) to ensure signed overflow or out-of-bounds access is impossible.
  4. Perform static analysis on how the stack bounds are checked during flood fill operations.

## Step 2: Mock HAL Sprite OOB Check Verification
- **Goal**: Verify that `mock_sprite_oob_error` is correctly implemented and exposed.
- **Verification Method**:
  1. Inspect `dandy-gb/tests/mock_hal.h` to see how `mock_sprite_oob_error` (and related structures/functions) is declared.
  2. Inspect `dandy-gb/tests/mock_hal.c` to see how sprite writes are validated (e.g., checking if the sprite index is >= 40) and how `mock_sprite_oob_error` is set when an OOB write occurs.
  3. Inspect `dandy-gb/tests/dandy_env.py` to ensure that `mock_sprite_oob_error` is correctly exposed to Python (via `ctypes` or another interface) and can be queried or reset.
  4. Verify that the OOB error state is properly checked or asserted in tests when OOB sprite operations are expected or checked.

## Step 3: Double-Assert Conformance
- **Goal**: Verify that all 112 E2E tests strictly conform to the Double-Assert Rule.
- **Verification Method**:
  1. Write and run a helper python script (or use grep/regex) to scan all test cases in `dandy-gb/tests/test_tier1.py`, `dandy-gb/tests/test_tier2.py`, and `dandy-gb/tests/test_tier3.py`.
  2. For every test, confirm it asserts both:
     - **C Engine Globals**: Core engine state variables (e.g., player x/y, keys, game state, map cell types).
     - **Mock HAL Side-Effects**: Mock hardware state (e.g., sprite position, sprite tiles, scroll register values, sound registers, screen updates).
  3. Confirm the total test count is exactly 112 (or as expected).

## Step 4: No Cheating / Hardcoding Detection
- **Goal**: Detect any facade implementations, hardcoded test results, or bypasses.
- **Verification Method**:
  1. Inspect the Makefile and verify the test execution commands.
  2. Check if the python tests use any global try-except blocks that swallow failures or intercept assertions.
  3. Verify that the C mock HAL functions are not faking results or returning hardcoded expected outputs without executing the mock logic.
  4. Run a general search for prohibited patterns (e.g., `return 1` or `pass` in assertions).

## Step 5: Compile and Execute
- **Goal**: Compile the shared library and run the E2E test suite to verify authentic passing status.
- **Verification Method**:
  1. Run `make test_lib` in `/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb/` and verify successful compilation.
  2. Run `make test` in `/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb/` and verify that all tests pass.
  3. Capture and analyze the test output.
