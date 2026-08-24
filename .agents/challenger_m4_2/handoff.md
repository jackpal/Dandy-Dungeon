# Handoff Report - Challenger 2 (Milestone 4)

## 1. Observation
- **Test File under Review**: `dandy-gb/tests/test_tier4.py` containing the newly implemented Tier 4 E2E tests.
- **Mutational Testing Execution**: We executed a custom mutational testing script `/tmp/run_mutations.py` which compiled a copy of the C library with 5 distinct injected bugs and ran the Tier 4 tests. The outputs were:
  - **Mutation 1 (Camera X Clamping bug)**: Failed as expected.
    ```
    FAILED (failures=1)
    ```
  - **Mutation 2 (Spectator Centroid bug)**: Failed as expected.
    ```
    FAILED (failures=1)
    ```
  - **Mutation 3 (Smart Bomb Viewport Boundary bug)**: Failed as expected.
    ```
    FAILED (failures=1)
    ```
  - **Mutation 4 (Player Movement Coordinate Offset bug)**: The test `test_level_0_complete_walkthrough` hung in an infinite loop and timed out after 5 seconds (previously hung for over 11 minutes until killed).
    ```
    Result: HANG! Test timed out (infinite loop detected).
    ```
  - **Mutation 5 (Generator Spawning disabled)**: Failed as expected.
    ```
    FAILED (failures=1)
    ```
- **Walkthrough Loop Structure**: In `dandy-gb/tests/test_tier4.py` lines 161-208:
  ```python
  while path_idx < len(found_path) - 1:
      # ...
      if (new_x, new_y) == (next_x, next_y):
          path_idx += 1
      else:
          # Allow recovery if player slid slightly due to dynamic monster collisions
          dist = abs(new_x - next_x) + abs(new_y - next_y)
          self.assertLessEqual(dist, 2, f"Player diverged too far at step {path_idx}")
  ```
- **Test Infrastructure Leak Assertion**: In `dandy-gb/tests/test_infra_stress.py` line 106:
  ```python
  self.assertEqual(end_temp_dirs, stable_temp_dirs, f"Temp directory leak detected! Leftover: {get_temp_env_dirs()}")
  ```
  During the full test suite run, this produced a false failure:
  ```
  AssertionError: 0 != 1 : Temp directory leak detected! Leftover: []
  ```

## 2. Logic Chain
- **Walkthrough Hanging**: 
  1. The walkthrough test uses a `while` loop that terminates only when `path_idx` reaches the end of the path.
  2. `path_idx` is only incremented when the player's coordinate exactly matches the target `(next_x, next_y)`.
  3. If a bug (like Mutation 4) causes the player to continuously fail to reach the exact coordinate, but stay within a distance of 2 tiles from it, the `dist <= 2` assertion passes.
  4. Because the assertion passes but `path_idx` is not incremented, the loop executes again for the same target, leading to an **infinite loop hang**.
- **Infra Stress Leak Flakiness**:
  1. `stable_temp_dirs` measures temp directories after a 5-run warmup.
  2. If Python's garbage collector hasn't immediately called `__del__` on previously deleted `DandyEnv` instances (e.g. from `TestInfraCheck` which runs right before), one temp directory remains, so `stable_temp_dirs = 1`.
  3. By the end of the 1000 runs, the garbage collector has run multiple times, collecting all instances, so `end_temp_dirs = 0`.
  4. The assertion `0 == 1` fails, creating a false negative.

## 3. Caveats
- We did not modify the actual source code files in `src/` or `tests/` in the repository, adhering strictly to the constraint not to break the main build.
- We used a temporary mutational testing script in `/tmp/` and compiled temporary libraries in `/tmp/dandy_mutations` to keep the workspace completely clean and compliant.

## 4. Conclusion
- The Tier 4 E2E tests are **highly robust and correct** in verifying the game mechanics, camera scrolling, spectator centering, and viewport logic under normal and bugged states (no false positives).
- However, there is a **critical hanging risk** in `test_level_0_complete_walkthrough` due to the lack of a loop guard/tick budget.
- The test infrastructure contains **flakiness** in its temp directory leak check due to non-deterministic garbage collection timing.
- **Actionable Recommendations**:
  1. Add a loop guard/ticks budget to the level walkthrough loop in `test_level_0_complete_walkthrough` to prevent infinite hangs (raise an error if exceeded).
  2. Fix the leak check assertion in `test_infra_stress.py` to check for `end_temp_dirs == 0` rather than comparing it to the unstable `stable_temp_dirs`.

## 5. Verification Method
- **To reproduce the mutational tests and verify robustness**:
  1. View the challenge report in `.agents/challenger_m4_2/challenge.md`.
  2. Run the mutational testing suite using:
     ```bash
     python3 /tmp/run_mutations.py
     ```
  3. Observe that all mutations are caught successfully, and Mutation 4 is caught via a 5-second timeout (hang).
