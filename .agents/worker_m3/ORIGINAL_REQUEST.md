## 2026-06-20T22:24:32Z

You are worker_m3 (archetype: teamwork_preview_worker).
Your working directory is: /usr/local/google/home/jackpal/Developer/Dandy-Dungeon/.agents/worker_m3

Objective: Implement Milestone 3: Python 2D level compressor, GBDK C decompressor (Scheme B2 + Edge Wall Elision), and updated verification script.

Loaded Skills:
- software-engineering (/google/src/files/head/depot/google3/learning/gemini/agents/skills/software_engineering/SKILL.md)
- greenfield-development (/google/src/files/head/depot/google3/learning/gemini/agents/skills/greenfield_development/SKILL.md)

Detailed Designs:
Please read and follow the detailed designs produced by the Explorers:
- Python Compressor: /usr/local/google/home/jackpal/Developer/Dandy-Dungeon/.agents/explorer_m3_1/analysis.md
- GBDK C Decompressor: /usr/local/google/home/jackpal/Developer/Dandy-Dungeon/.agents/explorer_m3_2/analysis.md
- Verification Script: /usr/local/google/home/jackpal/Developer/Dandy-Dungeon/.agents/explorer_m3_3/analysis.md

Tasks:
1. Update tools/convert_levels.py to compress all 26 levels from dandy-js/levels.js using Edge Wall Elision (EWE) and Scheme B2 (Variable-Bit-Width) prefix coding. Pack MSB-first, pad to byte boundary, and generate src/levels.c/src/levels.h. Make sure to remove the temporary 5-levels limit so all 26 levels are processed and output.
2. Modify dandy_load_level(uint8_t level_idx) in src/dandy_core.c (or dedicated module) to:
   - Pre-fill the 1800-byte dandy_map buffer with TILE_WALL (1) using memset.
   - Decode the compressed bitstream from dandy_levels[level_idx] into the inner 58x28 grid (using row-major, row-by-row, column-by-column coordinates y=1..28, x=1..58).
   - Use the skip-write optimization (if decoded tile is TILE_WALL, skip writing it to RAM).
   - Use sequential pointer dst++ increment to avoid 16-bit multiplication.
   - Ensure absolute bounds safety and include active runtime guards from Milestone 1.
   - Ensure standard GBDK C optimized for the Z80 (no division/modulo, no heavy math, clean register alignment).
3. Update tools/verify_compression.py to:
   - Perform the Python-side round-trip validation using the same EWE + Scheme B2 logic.
   - Automatically execute the host-side E2E test suite (make test_lib && make test) as part of the verification pipeline and check its exit code.
4. Run compilation, verification, and tests:
   - Compile the ROM: make clean && make
   - Verify ROM size: must be exactly 32768 bytes.
   - Verify ROM active segment footprint (from bin/dandy.map): must be <= 28672 bytes (28KB).
   - Run the updated verification script: python3 tools/verify_compression.py
   - Ensure 100% round-trip fidelity, ROM checks pass, and all 117+ E2E tests pass successfully.
5. Write a detailed summary of changes to /usr/local/google/home/jackpal/Developer/Dandy-Dungeon/.agents/worker_m3/changes.md and a handoff.md containing the exact commands run and their outputs.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A Forensic Auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Send a message back to the parent (conversation ID: d1f31846-5dd2-4d37-aeb0-b69a2dcd8a16) when you are done. Include paths to your files.
