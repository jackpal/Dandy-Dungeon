# Plan: E2E Testing Track Implementation

This plan outlines the design, implementation, and execution of the offline E2E testing track for the Dandy Dungeon Custom 2D Level Compression project.

## 1. Problem Classification & Complexity Assessment
- **Category**: SWE / Project (Greenfield test harness + comprehensive test suite)
- **Complexity**: High (Requires linking C engine with a mock HAL, exposing state via C/Python bridge, implementing 90+ test cases covering Tiers 1-4, and maintaining strict opaque-box requirements).
- **Strategy**: Decompose the task into 5 logical milestones. Spawn a sub-orchestrator or specialized subagent for each milestone to maintain clean boundaries and focus.

---

## 2. Milestones & Decomposition

### Milestone 1: Test Infrastructure & Runner
- **Objective**: Design and build the C/Python testing harness.
  1. Create a mock HAL in C (`tests/mock_hal.c`) that implements the `hal_*` functions required by `dandy_core.h`, recording calls (sounds played, tiles drawn, sprites set) to a queryable buffer.
  2. Compile the core C engine (`src/dandy_core.c`, `src/levels.c`) along with `tests/mock_hal.c` into a shared library (`libdandy_test.so`) using a new target in the Makefile.
  3. Create a Python wrapper (`tests/dandy_env.py`) using `ctypes` to load the shared library, expose all global variables (`dandy_map`, `player_x`, `player_health`, etc.), and provide helper functions to initialize, tick (`dandy_step`), and inspect state.
  4. Write `TEST_INFRA.md` in the project root detailing the test runner architecture, feature inventory, and coverage thresholds.
- **Verification**: Ensure the shared library compiles successfully and a simple Python script can load it, call `dandy_init()`, step the engine, and read back state.

### Milestone 2: Tier 1 Feature Coverage Tests
- **Objective**: Implement >= 5 tests per feature for all 8 core features (total 40+ tests).
  - Happy-path scenarios: basic movement, collecting items, shooting, monster spawning, etc.
- **Verification**: Run the test suite and verify 100% pass rate.

### Milestone 3: Tier 3 & Tier 2 Boundary, Corner, & Interaction Tests
- **Objective**: Implement >= 5 tests per feature for boundary/corner cases (Tier 2, total 40+ tests) and pairwise cross-feature combination tests (Tier 3, total 8+ tests).
  - Edge cases: moving out of bounds, taking damage at 0 health, shooting at map boundaries, maximum players, overflowing score, multiple monsters colliding, etc.
  - Cross-features: shooting a monster while moving, picking up key and opening door in same tick, etc.
- **Verification**: Run the test suite and verify 100% pass rate.

### Milestone 4: Tier 4 Real-World Application Scenarios
- **Objective**: Implement >= 5 complex real-world play scenarios (Tier 4).
  - Full-level play-through simulations (e.g., player navigates a maze, fights monsters, collects keys, unlocks doors, and transitions via stairs).
  - Regression testing on actual levels (`levels.c`) to verify they are navigable and beatable.
- **Verification**: Run the complete test suite (Tiers 1-4) and verify all pass.

### Milestone 5: Verification, Audit, & TEST_READY.md
- **Objective**: Perform final verification and publish `TEST_READY.md`.
  - Run the `teamwork_preview_auditor` to verify integrity and correctness.
  - Publish `TEST_READY.md` containing the test runner invocation command, tier coverage counts, and feature checklist.
  - Handoff clean, verified state to the parent Project Orchestrator.

---

## 3. Detailed Architectural Design of Test Runner

```
+-----------------------------------------------------------------+
|                         Python Test Suite                       |
|  - Uses unittest / pytest                                       |
|  - Defines 90+ test cases (Tiers 1-4)                          |
|  - Imports dandy_env.py                                         |
+--------------------------------+--------------------------------+
                                 | (ctypes Calls)
                                 v
+-----------------------------------------------------------------+
|                         tests/dandy_env.py                      |
|  - Loads libdandy_test.so via ctypes                            |
|  - Exposes C globals (dandy_map, player_x, player_health, etc.) |
|  - Provides high-level helpers (load_custom_map, tick, assert) |
+--------------------------------+--------------------------------+
                                 | (Dynamic Link)
                                 v
+-----------------------------------------------------------------+
|                         libdandy_test.so                        |
|                                                                 |
|   +-----------------------+         +-----------------------+   |
|   |  dandy_core.c         | <-----> |  tests/mock_hal.c     |   |
|   |  (Game Engine Logic)  |         |  (Records drawings,   |   |
|   |                       |         |   sounds, sprites)    |   |
|   +-----------------------+         +-----------------------+   |
+-----------------------------------------------------------------+
```

### Mock HAL Interface (`tests/mock_hal.h` & `tests/mock_hal.c`)
To enable rich assertions on output effects, the mock HAL will:
- Record every tile draw (`hal_draw_tile`) in a circular buffer with struct `{x, y, tile_id}`.
- Record every sound played (`hal_play_sound`) in a list of sound IDs.
- Keep track of active sprites (`hal_set_sprite`, `hal_clear_sprites`).
- Expose functions to clear these recording buffers so tests can assert on effects produced during a specific tick.

---

## 4. Execution Strategy & Subagent Dispatch
We will spawn specialized subagents to perform the actual implementation, exploration, and review, keeping our own role strictly limited to orchestration and quality gates.

1. **For Milestone 1**:
   - Spawn an **Explorer** (`teamwork_preview_explorer`) to analyze the core engine code (`dandy_core.c` and `dandy_core.h`) and specify the exact ctypes mapping and mock HAL requirements.
   - Spawn a **Worker** (`teamwork_preview_worker`) with the `greenfield-development` skill to implement `tests/mock_hal.c`, update the `Makefile`, and write `tests/dandy_env.py`.
   - Spawn a **Reviewer** (`teamwork_preview_reviewer`) to verify compilation and basic loading.

2. **For Milestones 2-4**:
   - Spawn **Workers** to write the test cases in Python under `tests/test_suite.py`.
   - Spawn **Challengers** (`teamwork_preview_challenger`) to stress-test the test runner and verify that the test assertions are robust and do not produce false positives/negatives.

3. **For Milestone 5**:
   - Spawn a **Forensic Auditor** (`teamwork_preview_auditor`) to verify the integrity of the tests (no hardcoding, authentic simulation).
   - Spawn a **Worker** to generate `TEST_INFRA.md` and `TEST_READY.md`.
