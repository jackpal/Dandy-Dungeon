# Adversarial Challenge Report: Milestone 4 (Tier 4 E2E Tests)

## Challenge Summary

**Overall risk assessment**: **LOW** (after our hardening and test additions). Originally **MEDIUM** due to a critical test gap in the LFSR generator spawn direction logic and flakiness in the infrastructure leak test.

Through a fully automated mutation testing harness, we subjected the newly implemented Tier 4 E2E tests to 7 adversarial mutations of the core C engine. The tests proved to be remarkably robust, catching 6 out of 7 mutations immediately. We identified one key testing gap (the LFSR spawn direction logic) and one infrastructure flakiness source (leftover environments in garbage collection), and successfully patched both.

---

## Key Findings & Challenges

### 🔴 [High] Challenge 1: LFSR Generator Spawn Direction Blindspot (Vulnerability Caught & Fixed)
- **Assumption Challenged**: The generator spawn tests assume that checking a single generator spawn on Tick 1 is sufficient to verify the correctness of the LFSR random direction generator.
- **Attack Scenario**: If a bug is introduced in `dandy_core.c` that forces the generator spawn direction to always be `0` (Up) (e.g., `uint8_t spawn_dir = 0;`), all existing tests in `test_tier4.py` and `test_tier2.py` still pass.
- **Why it occurred**: On Tick 1, the LFSR seed `0xACE1` updates to `0xE270`. The formula `(rand_seed & 3) * 2` evaluates to `0` (Up). Since both the buggy and correct engines chose `0` (Up) on this tick, the tests did not notice the difference. Furthermore, even in tests where Up was blocked, the engine's clockwise fallback search ordered Up -> Right -> Down -> Left, causing it to spawn Right, which again matched the expected fallback of the correct engine.
- **Blast Radius**: Large. A completely broken random direction generator (which always spawns monsters in a single direction) would go undetected, drastically simplifying the game's difficulty and breaking the original mechanics.
- **Mitigation/Fix**: We designed and added `test_scenario_c_lfsr_multi_direction` to `test_tier4.py`. This test places 6 generators matching the same rotor index in the player's viewport. On a single step, they tick sequentially, updating the shared `static rand_seed` 6 times. The 6th generator is expected to spawn a monster **Left** (direction 6, position (4,9)). If the engine is buggy and always spawns Up, the monster spawns Up (position (5,8)) instead. This test successfully caught the mutation and hardened the suite.

### 🟡 [Medium] Challenge 2: Infrastructure Leak Test Flakiness (False Negatives Fixed)
- **Assumption Challenged**: The leak stability test (`test_lifecycle_and_leak_stability_1000_runs`) assumes that the count of temp directories in `.temp_envs` after 1000 runs must *exactly* equal the count measured in the stabilized state after warmup.
- **Attack Scenario**: If a previous test class (like `TestInfraCheck`) created `DandyEnv` instances that were not immediately garbage-collected by Python, they remain in memory. When the stress test runs, it cleans up all directories. During the 1000 stress runs, Python's GC eventually runs and collects these leftover instances, which deletes their directories. This causes the final directory count to decrease (e.g., from 2 to 1), leading to an assertion failure (`1 != 2`) and a false negative (flaky failure).
- **Blast Radius**: Medium. Causes pipeline flakiness and developer distraction due to false memory/directory leak reports.
- **Mitigation/Fix**: We changed the temp directory assertion in `test_infra_stress.py` from `assertEqual(end_temp_dirs, stable_temp_dirs)` to `assertLessEqual(end_temp_dirs, stable_temp_dirs)`. This ensures that a decrease in the directory count (which is a cleanup, not a leak) is correctly accepted, while any increase (which is a real leak) is still caught.

---

## Mutation Stress Test Results

We compiled copies of the core C engine with specific injected mutations and ran the E2E tests against them using our automated harness `run_mutations.py`.

| Mutation | Description | Target Test | Expected Behavior | Actual Behavior | Pass/Fail |
|---|---|---|---|---|---|
| **Mutation 1** | Disable camera clamping (remove `clamp` from `vp_left`/`vp_top`) | `test_scenario_a_coop_and_viewport` | Test fails due to camera offsets wrapping/going OOB | Caught: `AssertionError: 251 != 0` | **PASS** |
| **Mutation 2** | Mess up spectator centroid averaging (omit division) | `test_scenario_b_spectator_and_game_over` | Test fails due to incorrect spectator camera centering | Caught: `AssertionError: 40 != 15` | **PASS** |
| **Mutation 3** | Disable outer border walls reconstruction (fill with space on load) | `test_level_0_complete_walkthrough` | Test fails during outer border integrity assertion | Caught: `AssertionError: 0 != 1` | **PASS** |
| **Mutation 4** | Corrupt LFSR generator spawn direction (always spawn Up) | `test_scenario_c_lfsr_multi_direction` | Test fails because Gen 6 spawns Up instead of Left | Caught: `AssertionError: 0 != 9` | **PASS** (Initially failed, now passes) |
| **Mutation 5** | Disable arrow hitting entities (arrows pass through) | `test_scenario_a_generator_monster_swarm` | Test fails because generators and monsters are not destroyed | Caught: `AssertionError: 19 != 0` | **PASS** |
| **Mutation 6** | Disable monster degradation (kill instantly instead of degrading) | `test_scenario_a_generator_monster_swarm` | Test fails because monster tile disappears instead of degrading | Caught: `AssertionError: 0 != 9` | **PASS** |
| **Mutation 7** | Smart bomb does not clear generators (only clears monsters) | `test_scenario_b_smart_bomb_room_clear` | Test fails because generator remains after bomb detonation | Caught: `AssertionError: 13 != 0` | **PASS** |

**Harness Command**: `python3 run_mutations.py` (run from the working directory).

---

## Unchallenged Areas

- **C-based WebAssembly bindings** (`src/web_main.c`): Out of scope for the offline GameBoy E2E Python harness, but critical for the web build.
- **Physical GameBoy ROM Execution**: The tests run against the core C engine compiled as a shared library (`libdandy_test.so`) with a mock HAL, not the actual GameBoy ROM. Any bugs in the GameBoy-specific HAL (`src/gameboy_hal.c`) or compiler-specific quirks of the GBDK-2020 compiler (`lcc`) are out of scope for these tests.
