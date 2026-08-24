## 2026-06-20T22:39:17Z
You are the Polish Worker (Milestone 4 Hardening) in the E2E Testing Track for Dandy Dungeon.
Your working directory is: /usr/local/google/home/jackpal/Developer/Dandy-Dungeon/.agents/worker_m4_polish

Task:
Perform a comprehensive hardening of the E2E test suite to eliminate a hanging risk and infrastructure flakiness.

1. **Loop Guard in Walkthrough Test**:
   - Open `dandy-gb/tests/test_tier4.py` and inspect `test_level_0_complete_walkthrough` (specifically the `while path_idx < len(found_path) - 1` loop).
   - Inside the loop, add a check (loop guard) to assert that the total ticks do not exceed 2000. If it does, fail immediately with a clear error message (preventing infinite loop hangs if coordinates get stuck):
     ```python
     self.assertLessEqual(ticks, 2000, "Walkthrough exceeded maximum tick budget - player is likely stuck in an infinite loop!")
     ```

2. **Explicit Teardowns for Resource/CDLL Leak Prevention**:
   - The test infrastructure copies and loads `libdandy_test.so` via `ctypes.CDLL` dynamically for each test case.
   - Because Python's unittest framework keeps test case instances in memory, the lack of explicit environment teardown causes temp directories and open library handles to accumulate, leading to file locks, OS resource contention, and flakiness in the 1000-run stress tests.
   - Edit the following test files:
     - `dandy-gb/tests/test_tier1.py`
     - `dandy-gb/tests/test_tier2.py`
     - `dandy-gb/tests/test_tier3.py`
     - `dandy-gb/tests/test_tier4.py`
     - `dandy-gb/tests/test_infra_check.py`
     - `dandy-gb/tests/test_infra_stress.py`
   - In each of these files, add the following `tearDown()` method to all test classes:
     ```python
     def tearDown(self):
         if hasattr(self, "env"):
             del self.env
     ```
     (This explicitly deletes the DandyEnv instance immediately after each test method completes, triggering Python garbage collection and cleanly unmapping the shared library and deleting the temp directory).

3. **Verify and Run**:
   - Load the `software-engineering` domain skill.
   - Run the compilation and full test runner to verify:
     ```bash
     cd dandy-gb
     make clean
     make test_lib
     make test
     ```
     Verify that all 118 tests in the repository pass successfully.
   - Verify that the 1000-run lifecycle stress test runs cleanly and is now 100% stable with zero flakiness.

4. **Deliverables**:
   - Write a detailed report in changes.md.
   - Write a structured handoff.md and send a completion message to me when done.
