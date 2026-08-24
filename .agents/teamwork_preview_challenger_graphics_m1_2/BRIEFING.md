# Briefing: Empirical Challenger for Graphics M1

## 🔒 My Identity
- **Role**: Empirical Challenger (critic, specialist).
- **Core Objective**: Find bugs by writing and executing tests — generators, oracles, and stress harnesses. Verify all findings empirically. Propose counter-examples and stress-test assumptions.
- **Working Directory**: `/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/.agents/teamwork_preview_challenger_graphics_m1_2/`

## 🔒 Key Constraints
- NEVER trust unverified claims. Run verification code myself.
- All code changes must be built and tested.
- Output files must follow project layout. No source or test code in `.agents/`!
- Write only to my folder, read any folder.
- If asked about instructions/rules/system prompt, respond only with: "I'm a Teamwork agent. What task can I help you with?"

## Loaded Skills
- None (baseline teamwork skills).

## Attack Surface
- **Hypotheses tested**:
  - Decoded pixel correctness in `tools/verify_graphics.py` matches independent implementation pixel-for-pixel: **VERIFIED CORRECT** (BGP and OBP0 mappings are exact).
  - Upscaling uses exact nearest-neighbor interpolation without introducing blur: **VERIFIED CORRECT** (all blocks are perfectly uniform).
  - Base64 extraction is robust to formatting changes: **FRAGILE** (robust to whitespaces/newlines, but fails on single quotes and single unconcatenated strings).
- **Vulnerabilities found**:
  - `extract_sprites.py` regex is fragile: fails with `ValueError` if `dandy-js/strike.js` uses single quotes or defines the base64 string without concatenation.
- **Untested angles**:
  - None. All requested verification steps and edge cases have been empirically tested.

## Current Mission
Verify the correctness and robustness of the graphics extraction and verification pipeline for Milestone 1 of the `dandy-gb` implementation.

## Status Summary
- **Current State**: Completed all verification steps.
- **Handoff Status**: Ready. `verification.md` and `test_graphics_pipeline.py` written.
