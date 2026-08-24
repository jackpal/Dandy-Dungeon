# Original User Request

## Initial Request — 2026-06-20T21:49:00Z

You are the Milestone 1 Sub-orchestrator (archetype: teamwork_preview_orchestrator) for the Dandy Dungeon custom 2D level compression project.

Your working directory is: /usr/local/google/home/jackpal/Developer/Dandy-Dungeon/.agents/sub_orch_m1
Your parent is: 6949b863-eafb-4fae-bca8-2c92c6ca9449 (the Project Orchestrator)
The global PROJECT.md is at: /usr/local/google/home/jackpal/Developer/Dandy-Dungeon/PROJECT.md

Your mission is to execute Milestone 1: Build Revert & Verification Foundation.
1. Revert the GameBoy compilation and build system in dandy-gb/Makefile from the 4-bank 64KB MBC1 layout back to a single, flat 32KB ROM (no-MBC, Bank 0 and Bank 1 only). Remove all bank-switching link/compile flags (-Wl-yo4, -Wf-bo2 for levels.c).
2. Modify src/dandy_core.c to remove the SWITCH_ROM(2) call in dandy_load_level.
3. Create the automated verification script tools/verify_compression.py (integrated into the build pipeline) that:
   a. Automatically cleans and compiles the GameBoy ROM using lcc (make clean && make).
   b. Asserts that the compiled ROM bin/dandy.gb exists and is exactly 32,768 bytes.
   c. Parses the linker map file (dandy.map) to sum up all active code and data segments, asserting that the active size is below a safe budget (or reporting the baseline size for now, as with the original levels it might exceed 28KB. Establish the size measurement and reporting framework).
   d. Run a simple round-trip test of levels (compress/decompress in Python) as a skeleton.

Apply the Orchestrator Procedure:
- Assess the complexity. Since this is relatively straightforward, it may fit a single Explorer -> Worker -> Reviewer cycle, or you can decompose if needed.
- Author your own BRIEFING.md, SCOPE.md, progress.md, and plan.md in your working directory.
- Spawn specialized subagents (explorers, workers, reviewers, challengers) to perform the changes and verify them.
- Ensure the worker runs builds and documents the commands and results.
- When done, write handoff.md and send a completion message to the parent.

Please initialize your workspace and start immediately. Report back when you have initialized your plan.
