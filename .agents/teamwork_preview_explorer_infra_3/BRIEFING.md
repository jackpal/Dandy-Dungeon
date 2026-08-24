# BRIEFING — 2026-06-20T21:50:22Z

## Mission
Analyze the Dandy Dungeon core engine and design the offline E2E test infrastructure (Milestone 1).

## 🔒 My Identity
- Archetype: teamwork_preview_explorer
- Roles: Explorer
- Working directory: /usr/local/google/home/jackpal/Developer/Dandy-Dungeon/.agents/teamwork_preview_explorer_infra_3
- Original parent: c0a07f4a-93da-4e5b-b8e5-dd519af9093b
- Milestone: Milestone 1

## 🔒 Key Constraints
- Read-only investigation — do NOT implement or modify any source files or Makefiles.
- Only write analysis and designs to `analysis.md` (and `handoff.md`).
- Ensure designs are completely opaque-box and requirement-driven, supporting testing of game rules and mechanics without depending on internal implementation details of functions (other than global state variables).
- CODE_ONLY network mode: no external web/services. Use only `code_search` and `view_file` for search/retrieval.

## Current Parent
- Conversation ID: c0a07f4a-93da-4e5b-b8e5-dd519af9093b
- Updated: 2026-06-20T21:51:33Z

## Investigation State
- **Explored paths**:
  - `dandy-gb/src/dandy_core.h` and `dandy_core.c` (Core engine structures, globals, logic, and GameBoy-dependencies)
  - `dandy-gb/src/levels.h` (Levels database structure)
  - `dandy-gb/Makefile` (Existing ROM and WASM targets)
  - `PROJECT.md` and `SCOPE.md` (Scope, contract, and milestones)
- **Key findings**:
  - **Host GBDK Dependency**: `dandy_core.c` includes `<gb/gb.h>` and uses `SWITCH_ROM(2)`. Resolved via a compile-time Mock GBDK Include (`tests/mock_gb/gb/gb.h`) to allow host compilation with zero source code changes.
  - **Cross-Test Pollution**: Engine has internal static states (`rand_seed`, `old_buttons`) that persist across ticks and are not reset in `dandy_init()`. Resolved via a "Copy-on-Load" temporary file isolation strategy in `dandy_env.py`.
  - **Game Mechanics**: Identified exact mechanics for 8-way movement, 4-tick cooldown, slide paths, item effects, 8-way door flood-fill, arrow spawning and viewport constraints, LFSR random seed determinism, camera tracking, and spectator camera centroid calculation.
- **Unexplored areas**:
  - None.

## Key Decisions Made
- Chose Mock GBDK Include approach to maintain a strictly read-only and unmodified core codebase.
- Designed a "Copy-on-Load" temporary file mechanism in Python ctypes to ensure absolute state isolation between tests.
- Designed a dual-assertion strategy (asserting on both global states and mock HAL side effects) to guarantee test fidelity.

## Artifact Index
- ORIGINAL_REQUEST.md — Original request and objectives.
- progress.md — Real-time progress tracker.
- analysis.md — Complete analysis and E2E test infrastructure design report.
- handoff.md — Official Handoff Report following the Handoff Protocol.
