# Plan for Tier 1 Test Suite Validation

This plan outlines the systematic analysis and adversarial mutation testing to verify the robustness of `dandy-gb/tests/test_tier1.py`.

## Steps

1. **Baseline Execution**: Run the existing test suite (`test_tier1.py`) to confirm 100% of the 50 tests pass under normal conditions.
2. **Mutation Testing - Phase A (Food Health Increase)**:
   - Mutate `dandy_core.c` to disable health increase when collecting food.
   - Compile the library using `make`.
   - Run `python3 -m unittest tests/test_tier1.py`.
   - Verify specific test failures (e.g., `test_f03_collect_food`, `test_f03_collect_multiple_items`).
   - Revert the mutation and verify tests pass again.
3. **Mutation Testing - Phase B (Door Key Decrement)**:
   - Mutate `dandy_core.c` to disable key decrement when opening a door.
   - Compile the library.
   - Run `python3 -m unittest tests/test_tier1.py`.
   - Verify specific test failures (e.g., `test_f04_door_unlock_single`, `test_f04_door_flood_fill_horizontal`, `test_f04_door_flood_fill_large_network`).
   - Revert the mutation and verify tests pass again.
4. **Mutation Testing - Phase C (Arrow Flight)**:
   - Mutate `dandy_core.c` to disable arrow coordinate updates / movement.
   - Compile the library.
   - Run `python3 -m unittest tests/test_tier1.py`.
   - Verify specific test failures (e.g., `test_f05_arrow_flight`, `test_f05_arrow_hit_wall`).
   - Revert the mutation and verify tests pass again.
5. **Mutation Testing - Phase D (Generator Spawning)**:
   - Mutate `dandy_core.c` to disable generator spawning completely.
   - Compile the library.
   - Run `python3 -m unittest tests/test_tier1.py`.
   - Verify specific test failures (e.g., `test_f08_generator_spawn_level1`, `test_f08_generator_spawn_level3`, `test_f08_generator_spawn_dir_blocked`, `test_f08_generator_no_spawn_on_fail_tick`).
   - Revert the mutation and verify tests pass again.
6. **Assertion Tightness & Coupling Analysis**:
   - Analyze how well the assertions check both the global C state and the HAL side effects (e.g. sprite and sound buffers).
7. **Reporting & Handoff**:
   - Write the final `challenge.md` containing the findings.
   - Send the message to the parent agent.
