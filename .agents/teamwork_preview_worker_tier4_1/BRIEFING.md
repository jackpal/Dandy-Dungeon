# BRIEFING — 2026-06-20T22:24:45Z

## Mission
Implement the Tier 4 Real-World Play Scenarios test suite (Milestone 4) for Dandy Dungeon (specifically in dandy-gb/) based on the three Explorer reports from explorer_m4_1, explorer_m4_2, and explorer_m4_3.

## 🔒 My Identity
- Archetype: teamwork_preview_worker
- Roles: implementer, qa, specialist
- Working directory: /usr/local/google/home/jackpal/Developer/Dandy-Dungeon/.agents/teamwork_preview_worker_tier4_1
- Original parent: c0a07f4a-93da-4e5b-b8e5-dd519af9093b
- Milestone: Milestone 4 - Tier 4 Real-World Play Scenarios

## 🔒 Key Constraints
- DO NOT CHEAT. No hardcoding of test results or dummy implementations.
- Every test must follow the Double-Assert Rule (assert engine globals state AND mock HAL side effects).
- Edge Wall Elision reconstruction must be verified via `self.env.assert_outer_border_walls(self)` on every level load or transition.
- Must run `make clean && make test_lib && make test` in `dandy-gb/` and ensure all 117+ tests pass.

## Current Parent
- Conversation ID: 4cdfadfb-6fb3-407c-93f5-8ddbf8005b56
- Updated: 2026-06-20T22:23:20Z

## Task Summary
- **What to build**: Python unit test suite at `dandy-gb/tests/test_tier4.py` implementing the 5 specific E2E test cases designed by the Explorers:
  1. `test_level_0_complete_walkthrough` (optimal 216-step Level 0, BFS pathfinder, Double-Assert)
  2. `test_scenario_a_generator_monster_swarm` (LFSR seed progression, pathfinding, combat)
  3. `test_scenario_b_smart_bomb_room_clear` (smart bomb radius check and boundary immunity)
  4. `test_scenario_a_coop_and_viewport` (2-player join/movement, camera clamping/scrolling, sprite filter)
  5. `test_scenario_b_spectator_and_game_over` (spectator mode camera centroid, game over reset)
- **Success criteria**: All tests in `test_tier4.py` pass and all 117+ tests in the repo pass; Double-Assert Rule and Edge Wall Elision checks implemented.
- **Interface contracts**: As defined in the Explorer reports and existing test suites in `dandy-gb/tests/`.
- **Code layout**: Test file at `dandy-gb/tests/test_tier4.py`.

## Key Decisions Made
- Unified clean map setup helper to guarantee Edge Wall Elision across all scenarios.
- Split movement turn and fire into separate ticks to resolve the C engine's firing-before-direction-update ordering.
- Updated map tiles during player warps to ensure sprites render correctly in the viewport.

## Artifact Index
- `ORIGINAL_REQUEST.md` — Original request description and parent updates.
- `BRIEFING.md` — Active briefing and state tracking.
- `changes.md` — Test coverage report.
- `handoff.md` — 5-component handoff report.

## Change Tracker
- **Files modified**: `dandy-gb/tests/test_tier4.py` — created test suite covering all 5 scenarios.
- **Build status**: Pass.
- **Pending issues**: None.

## Quality Status
- **Build/test result**: Pass (all 117 tests passing successfully).
- **Lint status**: Pass.
- **Tests added/modified**: `dandy-gb/tests/test_tier4.py` (added 5 comprehensive play scenario tests).

## Loaded Skills
- **Source**: /google/src/files/head/depot/google3/learning/gemini/agents/skills/software_engineering/SKILL.md
- **Local copy**: skill_software_engineering.md (not found on disk, followed unit-test and best practices instead).
- **Core methodology**: Production-grade software engineering practices, testing, and implementation.
