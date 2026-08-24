# Briefing - Challenger 2 (Milestone 4)

## 🔒 My Identity
- **Role**: Challenger 2 (critic, specialist)
- **Mission**: Adversarially challenge and stress-test the Tier 4 E2E tests in `dandy-gb/tests/test_tier4.py`.
- **Task**: Verify no false positives (tests fail on engine/HAL bugs), no false negatives (no flakiness/races), pathfinder robustness, and viewport/scrolling correctness.

## 🔒 Key Constraints
- Working directory: `/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/.agents/challenger_m4_2`
- Do not modify real source files in `src/` directly in a way that breaks the main build.
- Do not write code/tests in `.agents/` that violates the layout compliance (only metadata/reports in `.agents/`, but we can write temporary mutational scripts/harnesses in `/tmp/`).
- All communications with parent must use `send_message`.

## Loaded Skills
- None (no external Jetski skill paths provided in prompt)

## Attack Surface
- **Hypotheses tested**:
  - *Camera Clamping*: Mutated camera clamp -> Caught successfully by `test_scenario_a_coop_and_viewport`.
  - *Spectator Centroid*: Mutated spectator centroid averaging -> Caught successfully by `test_scenario_b_spectator_and_game_over`.
  - *Smart Bomb Viewport Boundary*: Mutated smart bomb to clear entire map -> Caught successfully by `test_scenario_b_smart_bomb_room_clear`.
  - *Player Movement Coordinates*: Mutated player movement to always offset by 1 -> Walkthrough test HUNG infinitely.
- **Vulnerabilities found**:
  - **Walkthrough Infinite Loop Hang**: `test_level_0_complete_walkthrough` contains a `while path_idx < len(found_path) - 1:` loop that has no loop guard/tick limit. If the player gets stuck or offset slightly (such that `(new_x, new_y) != (next_x, next_y)` but `dist <= 2`), the loop will continue infinitely, hanging the test runner.
- **Untested angles**:
  - Generator spawn probability / LFSR logic (Mutation 5).
