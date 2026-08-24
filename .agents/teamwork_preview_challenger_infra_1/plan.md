# Empirical Verification Plan: Offline E2E Test Infrastructure

This plan outlines the steps to verify the correctness, stability, and robustness of the `dandy-gb` offline E2E test infrastructure (Milestone 1).

## Step 1: Design the Stress-Test Script (`dandy-gb/tests/test_infra_stress.py`)
The stress-test script will contain three main parts:

### Part A: Resource Leak & Lifecycle Stability (1000 Iterations)
- Run a loop 1000 times. In each iteration:
  1. Record current open file descriptors (via `len(os.listdir('/proc/self/fd'))`).
  2. Record mapped library instances in memory (by parsing `/proc/self/maps` for `libdandy_test.so`).
  3. Record resident set size (RSS) memory consumption (via `resource.getrusage`).
  4. Instantiate `DandyEnv`.
  5. Call `env.init()` and perform a simple game step.
  6. Explicitly delete `env` (or let it go out of scope and run garbage collection via `gc.collect()`).
  7. Assert that:
     * No file descriptors are leaked (FD count remains constant or stable).
     * No memory mappings of `libdandy_test.so` are leaked (mapping count remains stable).
     * No temporary directories matching `dandy_env_*` are left in `/tmp`.
     * Memory consumption (RSS) does not grow unboundedly (remains stable across 1000 iterations).

### Part B: State Isolation Verification
- Instantiate multiple concurrent `DandyEnv` instances (e.g., `env1`, `env2`, `env3`).
- Initialize all of them.
- Mutate distinct global variables unique to each environment:
  * Set `env1.current_level = 5`, `env2.current_level = 12`, `env3.current_level = 2`.
  * Write unique maps to `env1.dandy_map`, `env2.dandy_map`, etc.
  * Set different player health values: `env1.set_player_health(0, 150)`, `env2.set_player_health(0, 50)`.
- Step each environment with different inputs.
- Assert that:
  * Modifications to one environment do not contaminate any other environment.
  * Deleting one environment does not affect the others.
  * Multiple sequential instantiations retain absolute isolation.

### Part C: Robustness & Adversarial Input Injection
Test extreme, out-of-bounds, and malformed inputs to see if the environment or C mock HAL crashes or exhibits undefined behavior:
1. **Invalid Player Indices**:
   - Call `env.is_player_joined(idx)`, `env.get_player(idx)`, `env.get_player_health(idx)`, `env.set_player_health(idx, val)` with `idx = -1`, `4`, `100`, `255`.
   - Call `env.draw_viewport(idx)` with `idx = -1`, `4`, `255`.
2. **Invalid Game Steps**:
   - Call `env.step(...)` with an empty list `[]`, a list of wrong size (e.g. `[1, 2]`), or containing invalid types/values.
3. **Out-of-Bounds Player Positions**:
   - Set player coordinates to `(255, 255)` or negative values (using ctypes/accessors) and call `env.step()` or `env.draw_viewport(0)` or `env.get_player(0)`.
4. **Extreme Player Health & Stats**:
   - Set player health to `0`, negative values (e.g., `-32768`), or extremely large values (e.g., `32767`). Step the game and verify behavior.
5. **Invalid Level Indices**:
   - Call `env.load_level(idx)` with `idx = 26` (since there are only 26 levels, 0-25), `100`, `255`. Note if it overflows, crashes, or corrupts memory.

## Step 2: Implement and Execute the Stress-Test
- Write `dandy-gb/tests/test_infra_stress.py`.
- Run the test using the Python unittest runner: `python3 -m unittest dandy-gb/tests/test_infra_stress.py`.
- If failures occur, analyze them, document them, and report them as findings (do not fix them ourselves, per constraints).

## Step 3: Adversarial Review & Reporting
- Compile findings into `challenge.md` inside our working directory.
- Complete the handoff report (`handoff.md`).
- Send the completion message to the parent agent.
