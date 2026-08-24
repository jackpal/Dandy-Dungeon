## 2026-06-20T21:51:46Z

You are a Worker agent (archetype: teamwork_preview_worker).
Your working directory is: /usr/local/google/home/jackpal/Developer/Dandy-Dungeon/.agents/teamwork_preview_worker_infra_1
Your task is to implement the offline E2E test infrastructure (Milestone 1) for the Dandy Dungeon custom 2D level compression project.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A Forensic Auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Skill Path:
Please load and follow the Greenfield Development skill at:
/google/src/files/head/depot/google3/research/omega/teamwork/playbooks/greenfield_development/SKILL.md

Reference Designs:
You must read and synthesize the designs from the following Explorer reports:
- Explorer 1 Analysis: /usr/local/google/home/jackpal/Developer/Dandy-Dungeon/.agents/teamwork_preview_explorer_infra_1/analysis.md
- Explorer 3 Analysis: /usr/local/google/home/jackpal/Developer/Dandy-Dungeon/.agents/teamwork_preview_explorer_infra_3/analysis.md

Specifically, you MUST implement the "Copy-on-Load" library state isolation mechanism proposed by Explorer 3 to ensure 100% test isolation, preventing state pollution from C static variables (like rand_seed, old_buttons) between test cases.

Your Objectives:
1. Create `dandy-gb/tests/mock_hal.h` containing the mock HAL function signatures and mock query extensions.
2. Create `dandy-gb/tests/mock_hal.c` implementing the GameBoy drawing, sound, sprite, camera, and HUD functions, recording all calls in static internal buffers that are queryable by the mock extensions.
3. Create `dandy-gb/tests/dandy_env.py` implementing the Python `DandyEnv` class. This class must:
   - Perform the "Copy-on-Load" mechanism: copy the compiled `libdandy_test.so` to a unique temporary directory on creation, load the temp copy, and clean up the temp directory on destruction.
   - Bind all core engine C globals (dandy_map, current_level, player_x/y, player_health, player_keys, player_bombs, player_score, player_dir, arrow_x/y/dir, is_dirty) and functions (dandy_init, dandy_step, dandy_load_level, dandy_draw_viewport, dandy_join_player, dandy_is_player_joined) using `ctypes`.
   - Bind all mock HAL query extensions.
   - Expose C arrays as readable/writable properties or helper methods.
4. Modify `dandy-gb/Makefile` to:
   - Include a `test_lib` target that compiles `src/dandy_core.c`, `src/levels.c`, and `tests/mock_hal.c` with the host compiler (gcc/clang) and appropriate flags (-fPIC -shared -O2) into `libdandy_test.so`.
   - Solve the GameBoy header dependency by dynamically generating the mock `tests/mock_gb/gb/gb.h` header (which stubs out GBDK macros like SWITCH_ROM as no-ops) and adding `-Itests/mock_gb` to the host compilation flags.
   - Add a `test` target to run all Python tests in the `tests/` directory via `python3 -m unittest`.
   - Update the `clean` target to clean up the generated mock headers and the `.so` file.
5. Create `TEST_INFRA.md` in the project root (`/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/TEST_INFRA.md`) containing the E2E test architecture overview, the 10-feature inventory, and the coverage thresholds.
6. Verify your implementation:
   - Build the test library using `make test_lib` in `dandy-gb/`.
   - Write a simple verification test in `dandy-gb/tests/test_infra_check.py` utilizing the `unittest` framework to verify that `DandyEnv` loads, resets, and records HAL side effects correctly. Run it with `make test` and ensure all pass.

Deliverables:
In your working directory, write a report `changes.md` describing the files created/modified and their purposes, and a formal 5-component `handoff.md` summarizing the completed work, build/test results, and verification evidence.

When done, send a message to your parent (conversation ID: c0a07f4a-93da-4e5b-b8e5-dd519af9093b).
