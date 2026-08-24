# Plan: Milestone 3 — Implement 2D Compressor & Decompressor

## Step 1: Explorer Analysis
- **Goal**: Analyze the current codebase and map out the exact code changes needed.
- **Tasks**:
  1. Spawn 3 `teamwork_preview_explorer` subagents to review:
     - `tools/convert_levels.py` (current implementation, level list, bit packing mechanism).
     - `src/dandy_core.c` (how levels are loaded, `dandy_map` layout, memory structures, bounds safety, Z80 optimization constraints).
     - `tools/verify_compression.py` (how verification is conducted, how it integrates with the pipeline).
  2. Synthesize Explorer reports into a unified strategy.

## Step 2: Worker Implementation
- **Goal**: Implement the Python compressor, GBDK C decompressor, and update verification.
- **Tasks**:
  1. Spawn 1 `teamwork_preview_worker` (armed with `software-engineering` and `greenfield-development`).
  2. Implement Edge Wall Elision and Scheme B2 prefix coding in `tools/convert_levels.py` to output all 26 levels to `src/levels.c`/`src/levels.h`.
  3. Implement Scheme B2 decoding with fast memset pre-fill and skip-write optimization in `src/dandy_core.c`. Ensure robust bounds checking.
  4. Update `tools/verify_compression.py` to support Edge Wall Elision and Scheme B2.
  5. Run local builds and verify that ROM compiles and runs tests.
  6. Document all commands and results in the worker's handoff.

## Step 3: Review and Challenge
- **Goal**: Empirically and theoretically verify the solution.
- **Tasks**:
  1. Spawn 2 `teamwork_preview_reviewer` subagents to review the changes for correctness, robustness, style, and Z80 optimizations.
  2. Spawn 2 `teamwork_preview_challenger` subagents (armed with `solution-stress-testing` or `test-coverage-audit`) to:
     - Run `tools/verify_compression.py` and verify 100% round-trip fidelity.
     - Compile the ROM, assert it is exactly 32,768 bytes, and analyze segment sizes in `dandy.map` (< 28KB target).
     - Run the E2E test suite against the compiled core engine.

## Step 4: Forensic Audit
- **Goal**: Ensure absolute integrity of the implementation.
- **Tasks**:
  1. Spawn 1 `teamwork_preview_auditor` to audit the code for cheating (e.g., hardcoded test results, facade implementations, bypassed checks).

## Step 5: Gate Verdict and Handoff
- **Goal**: Synthesize results, confirm pass criteria, and report to the Project Orchestrator.
- **Tasks**:
  1. Evaluate all verdicts (Worker, Reviewer, Challenger, Auditor).
  2. Confirm 100% test pass, ROM size 32,768 bytes, and clean audit.
  3. Update `progress.md` and write `handoff.md`.
  4. Send completion message to parent.
