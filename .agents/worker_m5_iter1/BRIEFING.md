# BRIEFING — 2026-06-20T22:47:00Z

## Mission
Implement a robust, size-bounded level decompressor to eliminate the critical Out-of-Bounds Read vulnerability in Dandy Dungeon.

## 🔒 My Identity
- Archetype: teamwork_preview_worker
- Roles: implementer, qa, specialist
- Working directory: /usr/local/google/home/jackpal/Developer/Dandy-Dungeon/.agents/worker_m5_iter1
- Original parent: 57415878-8f23-4ebd-8268-2bb9ef066e62
- Milestone: Milestone 5, Iteration 1

## 🔒 Key Constraints
- DO NOT CHEAT. All implementations must be genuine. No hardcoding test results or creating dummy/facade implementations.
- Active segment size must be under 28KB (28,672 bytes) in the linker map file.
- Final ROM file size must be exactly 32,768 bytes.
- Optimize boundary checks for Z80 execution speed and code size.
- Follow the minimal-change principle: make the smallest edit that achieves the goal.

## Current Parent
- Conversation ID: 57415878-8f23-4ebd-8268-2bb9ef066e62
- Updated: not yet

## Task Summary
- **What to build**: Size-bounded level decompressor. Level compiler must generate compressed stream sizes. Core decompressor must use them to bound reads, yielding 0 on OOB. Adversarial tests must verify truncated bitstream safety.
- **Success criteria**: All 124 E2E tests pass (`make clean && make test_lib && make test`). ROM verification script passes.
- **Interface contracts**: /usr/local/google/home/jackpal/Developer/Dandy-Dungeon/GEMINI.md (independent implementations named dandy-foo).
- **Code layout**: /usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb

## Key Decisions Made
- **Natural Space Propagation on OOB**: Decided to yield `0` when the compressed stream is exhausted or truncated. In Scheme B2, `0` represents a stream of `0` bits which decodes to `TILE_SPACE`. This allows the decompressor to naturally fill the rest of the map with spaces without complex branching or state tracking.
- **Unified Custom Level Mocking**: Updated `set_custom_compressed_level` in `test_adversarial_compression.py` to automatically update `self.dandy_level_sizes[level_idx]`. This ensures all custom adversarial tests maintain correct size limits and run securely without unexpected truncation or out-of-bounds reads.

## Artifact Index
- plan.md — Concrete, step-by-step plan for implementing the size-bounded level decompressor.

## Change Tracker
- **Files modified**:
  - `dandy-gb/tools/convert_levels.py`: Added generation of `dandy_level_sizes` containing exact compressed sizes of all levels.
  - `dandy-gb/src/dandy_core.c`: Implemented boundary checks at all 6 byte-reading sites, yielding `0` if `src >= src_end`.
  - `dandy-gb/tests/test_adversarial_compression.py`: Added binding to `dandy_level_sizes`, set correct sizes for custom levels, and updated the OOB read test to assert safety.
- **Build status**: Pass
- **Pending issues**: None

## Quality Status
- **Build/test result**: Pass (124 tests pass, including OOB mitigation validation)
- **Lint status**: Fully compliant
- **Tests added/modified**: Updated `test_adv04_truncated_bitstream_oob_read` to verify OOB read mitigation and ensure sentinel bytes are ignored.

## Loaded Skills
- **Source**: /google/src/files/head/depot/google3/research/omega/teamwork/playbooks/software_engineering/SKILL.md
- **Local copy**: skill_software_engineering.md
- **Core methodology**: Software engineering methodology for modifying, refactoring, and extending large production codebases.
