## 2026-06-20T22:45:05Z
You are the Worker (archetype: teamwork_preview_worker) for Milestone 5, Iteration 1.
Your working directory is: /usr/local/google/home/jackpal/Developer/Dandy-Dungeon/.agents/worker_m5_iter1
Your parent is the Milestone 5 Sub-orchestrator (conversation ID: 57415878-8f23-4ebd-8268-2bb9ef066e62).

Your mission is to implement a robust, size-bounded level decompressor to eliminate the critical Out-of-Bounds Read vulnerability in Dandy Dungeon.

Load the Jetski skill at:
  /google/src/files/head/depot/google3/research/omega/teamwork/playbooks/software_engineering/SKILL.md

Objectives & Requirements:
1. Carefully review the synthesized gaps and vulnerability report at:
   /usr/local/google/home/jackpal/Developer/Dandy-Dungeon/.agents/sub_orch_m5/gaps_synthesized.md

2. Modify the Level Compiler (dandy-gb/tools/convert_levels.py):
   - Calculate the exact compressed byte stream size for each level.
   - Generate and output a global array of these sizes:
     - Declaration in `src/levels.h`: `extern const uint16_t dandy_level_sizes[DANDY_NUM_LEVELS];`
     - Definition in `src/levels.c`: `const uint16_t dandy_level_sizes[DANDY_NUM_LEVELS] = { sizeof(dandy_level_0), sizeof(dandy_level_1), ... };`

3. Modify the Core Decompressor (dandy-gb/src/dandy_core.c:dandy_load_level):
   - Retrieve `src_end = src + dandy_level_sizes[level_idx]`.
   - On every byte read from `src` (where the bit cache is exhausted), verify that `src < src_end`.
   - If `src` reaches or exceeds `src_end`, do not read from memory. Instead, safely yield `0` (which decodes to TILE_SPACE in Scheme B2), allowing the rest of the map to be safely decoded as spaces without reading out-of-bounds.
   - Optimize the check for Z80 execution speed and code size to ensure it fits the GameBoy's strict limitations.

4. Update the Adversarial Test Suite (dandy-gb/tests/test_adversarial_compression.py):
   - Update `test_adv04_truncated_bitstream_oob_read` to assert that the decompressor safely yields spaces (TILE_SPACE) and no longer decodes tiles from the out-of-bounds sentinel region (0xFF).
   - In other words, verify that the OOB read is successfully mitigated and the sentinel bytes are ignored.

5. Verification:
   - Run the E2E test suite:
     `make clean && make test_lib && make test`
     All 124 tests must pass successfully.
   - Run the automated ROM build and size verification script from the `dandy-gb` folder:
     `python3 tools/verify_compression.py`
     Assert that the final ROM file size is exactly 32,768 bytes and the active segment size is under 28KB (28,672 bytes) in the linker map file.

MANDATORY INTEGRITY WARNING — DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A Forensic Auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Deliver a handoff.md in your working directory summarizing the changes made, the compilation results, E2E test output, and size metrics. Notify the parent (57415878-8f23-4ebd-8268-2bb9ef066e62) when complete.
