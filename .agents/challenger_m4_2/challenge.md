# Adversarial Challenge Report - Tier 4 E2E Tests

## Challenge Summary

**Overall risk assessment**: **MEDIUM**

The newly implemented Tier 4 E2E tests in `dandy-gb/tests/test_tier4.py` are exceptionally well-written, showing strong coverage of complex game mechanics (coop movement, spectator centroid centering, viewport boundary clamping, smart bombs, and full-level walkthroughs).

Through rigorous **mutational testing**, we verified that the tests successfully catch core C engine and mock HAL bugs (preventing false positives). However, we identified one **critical hanging vulnerability** in the level walkthrough and two **flakiness risks** in the test infrastructure (which can produce false negatives/pipeline hangs).

---

## Attack Surface & Hypotheses Tested

We compiled a mutated copy of the C library (`libdandy_test.so`) with injected bugs to stress-test the E2E assertions:

1. **Hypothesis: Disabling Camera X Clamping**
   - *Mutation*: Removed coordinate clamping for the camera viewport left-boundary (`vp_left = target_x - 10;` instead of clamped).
   - *Result*: **SUCCESS**. The bug was immediately caught by `test_scenario_a_coop_and_viewport`. The camera X coordinate resolved to an out-of-bounds value (e.g. 251 due to underflow) and failed the assertion.
2. **Hypothesis: Breaking Spectator Centroid Camera Centering**
   - *Mutation*: Changed the camera centroid calculation to return the raw sum of coordinates without dividing by the active player count.
   - *Result*: **SUCCESS**. The bug was immediately caught by `test_scenario_b_spectator_and_game_over` when asserting the centroid camera coordinates for dead/spectated players.
3. **Hypothesis: Smart Bomb Affecting the Entire Map**
   - *Mutation*: Modified the smart bomb `do_bomb` function to clear monsters and generators globally across the entire 60x30 map instead of clamping to the 20x10 viewport.
   - *Result*: **SUCCESS**. The bug was caught by `test_scenario_b_smart_bomb_room_clear`, which asserted that monsters and generators placed just outside the viewport boundary remained intact.
4. **Hypothesis: Player Movement Coordinates Offset Bug**
   - *Mutation*: Injected a coordinate offset bug that forced the player's updated X coordinate to be offset by +1 tile on every successful move.
   - *Result*: **VULNERABILITY FOUND (HANG)**. The E2E walkthrough test `test_level_0_complete_walkthrough` hung in an infinite loop instead of failing cleanly, exposing a critical CI/CD pipeline hazard.
5. **Hypothesis: Disabling Generator Spawning**
   - *Mutation*: Modified the generator spawning logic to never spawn monsters (effectively silencing the LFSR generator spawn rotor).
   - *Result*: **SUCCESS**. The bug was caught by `test_scenario_a_generator_monster_swarm`, which asserted that a monster spawned at (9,7) on the first step.

---

## Challenges & Vulnerabilities Found

### [High] Challenge 1: Infinite Loop Hang in Level Walkthrough
- **Assumption challenged**: The walkthrough test assumes that the player will always either reach the exit portal or diverge far enough (`dist > 2`) to trigger an immediate assertion abort.
- **Attack scenario**: If a bug is introduced in the C engine that causes the player's coordinates to be slightly offset, blocked, or shifted (e.g., our coordinate offset mutation) but they remain within 2 tiles of the optimal path:
  - The distance check `dist <= 2` passes, preventing an assertion abort.
  - The player's coordinates do not match the target, so `path_idx` is **not incremented**.
  - The `while` loop continues to execute step inputs forever, trying to reach the same coordinate.
- **Blast radius**: The test runner hangs indefinitely (infinite loop), consuming 100% CPU and blocking the CI/CD pipeline or local testing without producing any test failure message.
- **Mitigation**: Introduce a **tick limit / loop guard** to the walkthrough loop. For example, track the total steps or ticks taken, and assert that the walkthrough completes within a reasonable budget (e.g., `max_ticks = 2000`). If exceeded, raise a clear `AssertionError("Walkthrough exceeded maximum tick budget - player is likely stuck!")` to fail the test cleanly and immediately.

### [Medium] Challenge 2: Test Infrastructure Garbage Collection Flakiness
- **Assumption challenged**: The lifecycle stability stress test `test_lifecycle_and_leak_stability_1000_runs` assumes that the number of temp directories after a 5-run warmup phase will exactly match the number of temp directories after 1000 runs.
- **Attack scenario**: Because Python's `__del__` is not guaranteed to be called immediately when an object is deleted (garbage collection timing is non-deterministic), some `DandyEnv` instances from previous tests (e.g. `TestInfraCheck`) might still reside in memory during the warmup measurement, resulting in `stable_temp_dirs = 1`. After 1000 iterations and multiple GC passes, these instances are finally collected, resulting in `end_temp_dirs = 0`.
- **Blast radius**: False negative (the test fails with `AssertionError: 0 != 1 : Temp directory leak detected!` even though there is no directory leak).
- **Mitigation**: The test should assert that the final temp directory count is exactly `0` (or at least, no new directories are leaked relative to a baseline that has been fully garbage-collected), rather than asserting it is exactly equal to `stable_temp_dirs`.

### [Low] Challenge 3: Test Infrastructure "File Too Short" CDLL Load Failure
- **Assumption challenged**: The test suite assumes that copying the shared library concurrently or repeatedly during the 1000 runs stress test will always succeed.
- **Attack scenario**: When running the full test suite (`test_*.py`), we observed a race where `libdandy_test.so` became 0 bytes (truncated) during the copy, leading to `OSError: file too short` on CDLL load.
- **Blast radius**: False negative (test fails due to library loading flakiness).
- **Mitigation**: Add retry logic or ensure that the source library is not touched/locked, or copy with safe file locking.

---

## Stress Test Results

| Scenario / Mutation | Expected Behavior | Actual/Predicted Behavior | Pass/Fail |
|---|---|---|---|
| Mutation 1 (Disable Camera Clamp) | Test fails | `test_scenario_a_coop_and_viewport` failed as expected | **PASS** |
| Mutation 2 (Break Spectator Centroid) | Test fails | `test_scenario_b_spectator_and_game_over` failed as expected | **PASS** |
| Mutation 3 (Smart Bomb Affects All) | Test fails | `test_scenario_b_smart_bomb_room_clear` failed as expected | **PASS** |
| Mutation 4 (Move Coordinates Offset) | Test fails | Test hung in infinite loop (CI/CD hazard) | **FAIL (Warning)** |
| Mutation 5 (Disable Generator Spawn) | Test fails | `test_scenario_a_generator_monster_swarm` failed as expected | **PASS** |

---

## Unchallenged Areas

- **C Engine memory layout**: We did not challenge the exact bit-packing of levels in `levels.c` beyond verifying that the border walls are intact. This was deemed out of scope for Tier 4 E2E testing.
- **Mock GameBoy registers**: The mock GameBoy hardware register emulation (in `tests/mock_gb/gb/gb.h`) was not challenged, as it is a minimal stub for offline compilation.
