# Original User Request

## Initial Request — 2026-06-20T21:49:00Z

You are the E2E Testing Orchestrator (archetype: teamwork_preview_orchestrator) for the Dandy Dungeon custom 2D level compression project.

Your working directory is: /usr/local/google/home/jackpal/Developer/Dandy-Dungeon/.agents/sub_orch_e2e
Your parent is: 6949b863-eafb-4fae-bca8-2c92c6ca9449 (the Project Orchestrator)
The global PROJECT.md is at: /usr/local/google/home/jackpal/Developer/Dandy-Dungeon/PROJECT.md

Your mission is to establish the E2E Testing Track:
1. Decompose the E2E testing scope into feature areas and test tiers (Tiers 1-4).
2. Create and maintain TEST_INFRA.md in the project root defining the test architecture, feature inventory, and coverage thresholds.
3. Design and implement an offline E2E test runner (C/Python) that links the core C engine (src/dandy_core.c) with a mock HAL, allowing programmatic execution of game ticks and assertions.
4. Implement test cases covering Tier 1 (Feature Coverage), Tier 2 (Boundary & Corner Cases), Tier 3 (Cross-Feature Combinations), and Tier 4 (Real-World Application Scenarios), meeting the minimum threshold of ~11 * N + max(5, N/2) test cases.
5. Publish TEST_READY.md in the project root once the test suite is fully complete and passing.

Since this is a large task, you should apply the Orchestrator Procedure:
- Assess the complexity.
- Decompose the testing track into sub-milestones (e.g. Test Infrastructure, Tier 1, Tier 2, Tier 3, Tier 4).
- Author your own BRIEFING.md, SCOPE.md, progress.md, and plan.md in your working directory.
- Spawn specialized subagents (explorers, workers, reviewers, challengers) to implement the test runner and test cases.
- Monitor their progress, update progress.md, and ensure rigorous verification.
- When done, write handoff.md and send a completion message to the parent (Project Orchestrator).

Please initialize your workspace and start immediately. Report back when you have initialized your plan and are ready to execute.

## Follow-up — 2026-06-20T22:03:05Z

Resume work at /usr/local/google/home/jackpal/Developer/Dandy-Dungeon/.agents/sub_orch_e2e. Read handoff.md, BRIEFING.md, ORIGINAL_REQUEST.md, and progress.md for current state.
Your parent is 6949b863-eafb-4fae-bca8-2c92c6ca9449 — use this ID for all escalation and status reporting (send_message).

## Follow-up — 2026-06-20T22:11:53Z

**Context**: New Architectural Directives & E2E Testing Impact

**Content**:
The user has provided critical architectural directives for the level compression:
1. **Edge Wall Elision**: The outer border walls of every 60x30 map (first/last rows and columns) will be omitted from the compressed stream and reconstructed on-the-fly on level load.
2. **4-bit packing** (nibble-level packing) and Fax-like MR/MMR delta tracking will be evaluated in Milestone 2.

For E2E Testing: Please ensure your test cases (especially Tier 1 Feature Coverage and Tier 2 Boundary Cases) explicitly assert that after calling `dandy_load_level`, the outer borders of the `dandy_map` (first row, last row, first column, last column) are 100% correctly reconstructed as solid wall tiles (tile ID 1). This is a crucial validation check for Edge Wall Elision.

**Action**: Incorporate the outer border wall reconstruction assertions into your test cases.

