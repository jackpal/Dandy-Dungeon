## 2026-06-20T22:10:43Z
You are a Worker agent (archetype: teamwork_preview_worker).
Your task is to implement the E2E test suite hardening and C engine memory safety fixes for Milestone 3 of the Dandy Dungeon Testing Track.

Your working directory is: /usr/local/google/home/jackpal/Developer/Dandy-Dungeon/.agents/worker_e2e_hardening_gen2/

Please perform the following steps:
1. Load and follow the software-engineering domain skill at:
   `/google/src/files/head/depot/google3/research/omega/teamwork/playbooks/software_engineering/SKILL.md`
2. Read the synthesized hardening plan at:
   `/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/.agents/sub_orch_e2e/synthesis_hardening.md`
3. Implement all requested changes across the C engine, mock HAL, Python bridge, and E2E test files:
   - **Phase 1: C Engine Fix**: In `dandy-gb/src/dandy_core.c`, change `flood_stack_ptr` to `int16_t`.
   - **Phase 2: Mock HAL & Bridge**: Modify `dandy-gb/tests/mock_hal.h`, `dandy-gb/tests/mock_hal.c`, and `dandy-gb/tests/dandy_env.py` to implement, expose, and reset the `mock_sprite_oob_error` flag.
   - **Phase 3: E2E Test Hardening**: Modify `dandy-gb/tests/test_tier2.py` and `dandy-gb/tests/test_tier3.py` to:
     - Tighten the stack overflow test assertion to expect exactly 418 doors.
     - Add sprite OOB error check to the sprite cap test.
     - Assert player coordinates after level transition warps.
     - Retrofit all 37 weak test cases with appropriate mock HAL assertions (sound playbacks, camera scrolls, drawn viewport cells) to fully satisfy the Double-Assert Rule.
4. Compile and verify your changes from the `dandy-gb/` directory:
   ```bash
   make test_lib
   make test
   ```
   Confirm that all 112 tests compile and pass successfully with zero failures.
5. Write a detailed completion report (`handoff.md`) in your working directory summarizing:
   - The files modified and the exact modifications made.
   - The build and test execution outputs.
6. When complete, send a message to your parent (conversation ID: 1270ca6b-5147-4ec8-a7b8-2387eb40165b) with the path to your report.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A Forensic Auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.
