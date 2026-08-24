# BRIEFING

## 🔒 My Identity
- **Role**: Empirical Challenger (critic, specialist)
- **Archetype**: teamwork_preview_challenger
- **Mission**: Verify the correctness, stability, and effectiveness of the Tier 1 Happy-Path test suite (`dandy-gb/tests/test_tier1.py`) using adversarial mutation testing and rigorous analysis.

## 🔒 Key Constraints
- Must write only to my workspace: `/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/.agents/teamwork_preview_challenger_tier1_1`
- Must not access external websites or services (CODE_ONLY network mode).
- Must run verification code myself.
- Must document all findings in `challenge.md` and report back to parent.

## Loaded Skills
- None.

## Attack Surface
- **Hypotheses tested**:
  - **Hypothesis**: The Tier 1 tests are tightly coupled and will fail if key game behaviors in `dandy_core.c` are broken.
    * **Result**: Proven. We temporarily broke food health increase, door unlocking keys, arrow flight, and generator spawning; the tests failed with high precision and zero false passes.
  - **Hypothesis**: Test flakiness on CDLL loading is caused by security agents intercepting writes to `/tmp`.
    * **Result**: Proven. Relocating temp environments to `tests/.temp_envs/` resulted in 100% test run stability (2,500 executions, 0 failures).
- **Vulnerabilities found**:
  - **Critical boundary access vulnerability** in `move_monsters` and generator spawning in `dandy_core.c`. Accessing `row_offsets` at indices `-1` or `30` when monsters/generators are at map edges causes out-of-bounds reads and silent memory corruption or crashes.
  - **/tmp shared library execution intercept flakiness** where corp workstation security agents truncate or lock newly copied `.so` files in `/tmp`.
- **Untested angles**:
  - Out-of-bounds behavior under custom non-happy-path scenarios, though this is mostly covered in tier 2/robustness tests.
