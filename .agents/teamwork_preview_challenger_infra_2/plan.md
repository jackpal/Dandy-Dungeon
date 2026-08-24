# Stress Test Verification Plan

This plan outlines the steps to empirically verify the correctness, stability, and robustness of the offline E2E test infrastructure.

## Step 1: Design and Write the Stress-Test Script
We will write a comprehensive stress-test script `dandy-gb/tests/test_infra_stress.py` using Python's `unittest` framework.
The script will perform the following three categories of tests:

1. **Resource Leaks and Stability (`test_resource_stability`)**:
   - Instantiate and delete `DandyEnv` 1000 times in a loop.
   - Verify that:
     * Open file descriptors (via `/proc/self/fd`) do not leak and remain constant.
     * Shared library maps (via `/proc/self/maps`) do not leak or grow.
     * All temporary folders in `/tmp` prefixed with `dandy_env_` are successfully cleaned up.
     * Memory consumption (via `/proc/self/status` or `/proc/self/statm`) remains stable.

2. **State Isolation (`test_state_isolation_stress`)**:
   - Run concurrent/sequential instances of `DandyEnv`.
   - Write unique values to their global variables (e.g. `current_level`, `monster_rotor`, `dandy_map`).
   - Run them in parallel threads and verify that their states do not interfere (no cross-instance contamination).
   - Check that deleting one instance does not affect the others.

3. **Boundary and Extreme Inputs (`test_extreme_inputs`)**:
   - Inject extreme inputs:
     * Empty input lists, or invalid input list sizes to `step()` (should raise `ValueError`).
     * Out-of-bounds player index in accessors (should raise `IndexError` or `ValueError`).
     * Player coordinates set way out of bounds (e.g. `x=100`, `y=100`, negative coordinates).
     * Verify if the C engine or python wrapper crashes or exhibits memory corruption.
     * Place a monster at `y=0` and let it move up to see if it causes undefined behavior (indexing `row_offsets[-1]`).
     * Set health to 0, negative, or extremely large values.

## Step 2: Integrate and Run the Stress-Test
- Run the stress-test script using `python3 -m unittest dandy-gb/tests/test_infra_stress.py` or by adding it to the `Makefile` test suite.
- Verify if all tests pass. If any tests fail (e.g., due to memory leaks, file descriptor leaks, or crashes in the C engine), document them as empirical findings.

## Step 3: Analyze and Report Findings
- Document the stress-test design, commands, output, and final verdict in `challenge.md`.
- File a detailed handoff report `handoff.md`.
- Send a message to the parent agent.
