# Briefing - Empirical Challenger

## 🔒 My Identity
- **Role**: Empirical Challenger (critic, specialist)
- **Objective**: Verify correctness, stability, and effectiveness of the Tier 1 Happy-Path test suite (`dandy-gb/tests/test_tier1.py`) via adversarial mutation testing of `dandy-gb/src/dandy_core.c`.
- **Workspace**: `/usr/local/google/home/jackpal/Developer/Dandy-Dungeon`
- **Agent Directory**: `/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/.agents/teamwork_preview_challenger_tier1_2`

## 🔒 Key Constraints
- Never delete or rewrite the append-only sections (🔒).
- Do not make changes to production game code without reverting them completely.
- Use only the local workspace files and standard tools.
- Never write source code, tests, or data files inside the `.agents/` directory.

## Loaded Skills
- None yet.

## Attack Surface
- **Hypotheses tested**:
  - *Hypothesis 1 (Food Health)*: Disabling health increase on food causes food-related tests to fail. **[PASSED]** (Failed as expected)
  - *Hypothesis 2 (Door Keys)*: Disabling key decrement on doors causes door-related tests to fail. **[PASSED]** (Failed as expected, but revealed a minor assertion gap)
  - *Hypothesis 3 (Arrow Flight)*: Disabling arrow movement causes arrow-related tests to fail. **[PASSED]** (Failed as expected)
  - *Hypothesis 4 (Slide Mechanics)*: Disabling player slide mechanics causes slide-related tests to fail. **[PASSED]** (Failed as expected)
  - *Hypothesis 5 (Monster Behavior)*: Disabling monster movement/damage causes monster-related tests to fail. **[PASSED]** (Failed as expected)
  - *Hypothesis 6 (Spectator Mode)*: Disabling camera centroid tracking in spectator mode causes spectator-related tests to fail. **[PASSED]** (Failed as expected)
- **Vulnerabilities found**:
  - *Assertion Gap*: `test_f04_door_flood_fill_diagonal` does not assert key decrement (`self.assertEqual(self.env.get_player_keys(0), 0)`), leading to a potential false pass if key decrement is broken.
  - *Host Compile Disk Flush Latency*: Running `make test` immediately after modifying/compiling the shared library can occasionally result in a 0-byte file read by Python, leading to `OSError: file too short` (a transient build/test infra issue).
- **Untested angles**: None. The 50 core Tier 1 test cases have been thoroughly analyzed.

## Current State
- **Phase**: Documenting results
- **Next Step**: Write `challenge.md` and `handoff.md`, and notify parent.
