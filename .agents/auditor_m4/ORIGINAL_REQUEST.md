## 2026-06-20T22:25:02Z
You are the Forensic Auditor (Milestone 4) in the E2E Testing Track for Dandy Dungeon.
Your working directory is: /usr/local/google/home/jackpal/Developer/Dandy-Dungeon/.agents/auditor_m4

Task:
1. Perform a rigorous forensic integrity audit of the entire test suite, focusing on the newly implemented dandy-gb/tests/test_tier4.py.
2. Perform systematic checks:
   - Verify that all simulations are authentic (they execute the actual C engine code via ctypes rather than using hardcoded stubs or mocks that bypass the engine logic).
   - Ensure that no test results or expected values are hardcoded or fabricated inside the Python tests or the C shared library.
   - Verify that the Galois LFSR randomness and spawn mechanics are authentically executed and verified.
   - Check that all asset representations and level properties are correct.
3. Compile and run the test suite to verify all 117 tests pass cleanly.
4. Provide a clear binary verdict: CLEAN or INTEGRITY VIOLATION / CHEATING.
5. Write your full evidence report in audit_report.md in your working directory. When done, send a handoff message to the parent.
