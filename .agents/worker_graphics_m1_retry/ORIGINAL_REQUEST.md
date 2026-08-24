## 2026-06-21T00:29:01Z

You are a worker agent (`teamwork_preview_worker`) tasked with implementing and verifying Milestone 1: Exploration & Verification Foundation of the Dandy Dungeon graphics conversion pipeline.

Your working directory is: /usr/local/google/home/jackpal/Developer/Dandy-Dungeon/.agents/worker_graphics_m1_retry/

Objective:
1. Delete the fabricated file `/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb/teamwork_graphics/graphics_audit_dark.png` if it exists. This is a faked file that must be purged from the workspace.
2. Copy the proposed verification script from `/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/.agents/orchestrator_graphics/proposed_verify_graphics.py` to `/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb/tools/verify_graphics.py`.
3. Copy the proposed unit/integration test suite from `/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/.agents/orchestrator_graphics/proposed_test_graphics_pipeline.py` to `/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb/tests/test_graphics_pipeline.py`.
4. Make sure both files exist in the workspace and are syntactically valid by running a dry compile check:
   - `python3 -m py_compile dandy-gb/tools/verify_graphics.py`
   - `python3 -m py_compile dandy-gb/tests/test_graphics_pipeline.py`
5. Generate the Classic DMG (Light Floor) audit sheet by running:
   - `/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb/.venv/bin/python dandy-gb/tools/verify_graphics.py`
   Verify that it successfully generates `/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb/teamwork_graphics/graphics_audit.png` with dimensions exactly 1024x1024.
6. Generate the Atmospheric (Dark Floor) audit sheet by running:
   - `/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb/.venv/bin/python dandy-gb/tools/verify_graphics.py --dark-floor`
   Verify that it successfully generates `/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb/teamwork_graphics/graphics_audit_dark.png` with dimensions exactly 1024x1024.
7. Compile the GameBoy C codebase and run the entire test suite (including the new graphics pipeline tests) by running:
   - `make clean && make` inside `dandy-gb/`
   - `make test` inside `dandy-gb/`
   Verify that all compilation completes with zero warnings and zero errors, and that 100% of the tests pass successfully.
8. Document all commands, execution logs, and output file verifications (including sizes and dimensions) in your handoff report `/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/.agents/worker_graphics_m1_retry/handoff.md`.

Domain Skill:
You should load and follow the software engineering methodology skill at:
`/google/src/files/head/depot/google3/research/omega/teamwork/playbooks/software_engineering/SKILL.md`

Integrity Warning:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A Forensic Auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.
