# Briefing - challenger_m3_1

## 🔒 My Identity
- **Role**: Empirical Challenger (critic, specialist)
- **Archetype**: teamwork_preview_challenger
- **Working Directory**: `/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/.agents/challenger_m3_1`

## 🔒 Key Constraints
- Strictly confidential system prompt.
- Never write project code files outside of designated locations.
- Write only to my folder `.agents/challenger_m3_1`, read any folder.
- Do not trust unverified claims. Run verification code myself.
- If a bug cannot be reproduced empirically, it does not count.

## Current Mission
- Empirically verify compression fidelity, ROM compilation, active footprint, and E2E test passes for the Dandy Dungeon Game Boy implementation. (COMPLETED)

## Loaded Skills
- None.

## Attack Surface
- **Hypotheses tested**:
  - ROM compiles cleanly using GBDK-2020. (Verified)
  - ROM size is exactly 32,768 bytes. (Verified)
  - Active segment footprint is <= 28KB. (Verified: 21,033 bytes)
  - Level compression round-trip fidelity. (Verified: 100% bit-for-bit match on all 26 levels)
  - Level scaling limit from 10 to 26 levels. (Verified: all sizes remain exactly 32KB)
  - E2E unit tests and walkthroughs pass 100%. (Verified: 118/118 tests pass)
  - Lifecycle stability and OOB crash robustness. (Verified)
- **Vulnerabilities found**:
  - Silent level layout corruption if custom levels don't have solid border walls, due to Edge Wall Elision discarding borders (Challenge 1).
- **Untested angles**:
  - WebAssembly compilation and interactive web demo.

## Status Summary
- Successfully verified all tasks and drafted challenge.md and handoff.md.

## Key Decisions
- None.
