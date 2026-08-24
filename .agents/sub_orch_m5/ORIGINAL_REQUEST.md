# Original User Request

## Initial Request — 2026-06-20T22:41:30Z

You are the Milestone 5 Sub-orchestrator (archetype: teamwork_preview_orchestrator) for the Dandy Dungeon custom 2D level compression project.

Your working directory is: /usr/local/google/home/jackpal/Developer/Dandy-Dungeon/.agents/sub_orch_m5
Your parent is: 6949b863-eafb-4fae-bca8-2c92c6ca9449 (the Project Orchestrator)
The global PROJECT.md is at: /usr/local/google/home/jackpal/Developer/Dandy-Dungeon/PROJECT.md
The E2E test suite confirmation is at: /usr/local/google/home/jackpal/Developer/Dandy-Dungeon/TEST_READY.md

Your mission is to execute Milestone 5: Adversarial Hardening & Final Audit (Phase 2 of the Project Pattern).

### Objectives:
1. **Adversarial Coverage Hardening (Tier 5)**:
   - Run the white-box coverage audit loop to identify and eliminate any coverage gaps or potential edge-case bugs in the newly implemented compressor (`tools/convert_levels.py`) and decompressor (`src/dandy_core.c`, specifically `dandy_load_level`).
   - Spawn **2 Challengers** (using `teamwork_preview_challenger`). Armed with the **test-coverage-audit** playbook at:
     `/google/src/files/head/depot/google3/research/omega/teamwork/playbooks/test_coverage_audit/SKILL.md`
     The Challengers must analyze the source code and existing 118 E2E tests to identify untested code paths, boundary conditions, or vulnerabilities in our Scheme B2 implementation, and generate a gap report + adversarial test cases.
   - Spawn a **Worker** (using `teamwork_preview_worker` armed with the `software-engineering` playbook) to integrate the new adversarial tests and fix any exposed bugs in the compressor or decompressor.
   - Spawn **Reviewers** to verify correctness and passing tests.
   - Repeat the Challenger -> Worker -> Reviewer loop until the Challengers report **zero remaining gaps** or you reach a hard limit of iterations.

2. **Final Forensic Audit**:
   - Spawn the **Forensic Auditor** (using `teamwork_preview_auditor`) to perform a final, comprehensive integrity audit of the entire codebase and build pipeline.
   - The auditor must verify:
     - Absolute correctness and dynamic execution (no hardcoding of test results or fake implementations).
     - Flat 32KB compilation without MBC (only Bank 0 and Bank 1 enabled in GBDK Makefile).
     - Strict size constraints (exact 32,768-byte ROM size, active segment size < 28KB).
     - The auditor must issue a **CLEAN** verdict. A VIOLATION verdict immediately fails the gate and requires rolling back and fixing the issue.

3. **Compile Final Metrics**:
   - Record the final statistics of the project:
     - Total raw levels size (bytes).
     - Total compressed levels size in ROM (bytes and KB, showing exact savings).
     - Final compiled ROM file size (must be exactly 32,768 bytes).
     - Final active code and data segment footprint in the linker map file (must be < 28,672 bytes / 28 KB).
     - Total number of tests in the suite and their pass rate (must be 100%).

Apply the Orchestrator Procedure recursively, authoring your own BRIEFING.md, progress.md, and plan.md. When done, write a comprehensive handoff.md containing all final metrics and the CLEAN audit verdict, and notify the parent.

Please initialize your workspace and start immediately. Report back when you have initialized your plan.
