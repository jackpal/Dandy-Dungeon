## 2026-06-20T21:50:22Z
You are an Explorer agent (archetype: teamwork_preview_explorer).
Your working directory is: /usr/local/google/home/jackpal/Developer/Dandy-Dungeon/.agents/teamwork_preview_explorer_infra_3
Your task is to analyze the Dandy Dungeon core engine and design the offline E2E test infrastructure (Milestone 1).

Relevant Files:
- Global PROJECT.md: /usr/local/google/home/jackpal/Developer/Dandy-Dungeon/PROJECT.md
- Scope document: /usr/local/google/home/jackpal/Developer/Dandy-Dungeon/.agents/sub_orch_e2e/SCOPE.md
- Core engine files: /usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb/src/dandy_core.c and dandy_core.h
- Makefile: /usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb/Makefile

Your Objectives:
1. Analyze the core engine (`dandy_core.c` and `dandy_core.h`) to identify all external HAL functions and all global variables/state that need to be exposed to the test runner.
2. Design a mock HAL (`tests/mock_hal.c` and `tests/mock_hal.h`) that implements these external functions and records their invocations in queryable buffers (e.g. tiles drawn, sounds played, sprite states) to enable programmatic assertions.
3. Design the ctypes mapping and Python wrapper (`tests/dandy_env.py`) that loads the shared library and exposes the game state variables and functions to Python.
4. Design the Makefile changes needed to compile `src/dandy_core.c`, `src/levels.c`, and `tests/mock_hal.c` into a shared library `libdandy_test.so`.
5. Draft `TEST_INFRA.md` to be placed in the project root, detailing the E2E test architecture, a feature inventory of the game, and coverage thresholds.

Constraints:
- You are read-only. DO NOT write or modify any source files or Makefiles. Only write your analysis and designs to your handoff report (`analysis.md`) in your working directory.
- Ensure your designs are completely opaque-box and requirement-driven, supporting testing of game rules and mechanics without depending on internal implementation details of functions (other than global state variables).

Output:
Write a detailed report `analysis.md` in your working directory containing:
- Precise C signatures for the mock HAL and mock query extensions.
- Precise Python ctypes definitions for all exposed engine globals and functions.
- Recommended Makefile target and compilation flags for `libdandy_test.so`.
- Draft content for `TEST_INFRA.md`.
- Verification plan for the infrastructure.

When done, write the report and send a message to your parent (conversation ID: c0a07f4a-93da-4e5b-b8e5-dd519af9093b).
