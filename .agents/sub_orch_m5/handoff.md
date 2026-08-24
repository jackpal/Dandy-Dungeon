# Handoff Report — Milestone 5: Adversarial Hardening & Final Audit

**Work Product**: Dandy Dungeon custom 2D level compression project  
**Milestone State**: **COMPLETED**  
**Forensic Auditor Verdict**: **CLEAN**  

---

## 1. Executive Summary

Milestone 5 has been successfully completed with zero remaining coverage gaps and a **CLEAN** forensic audit verdict. 

Through an inverted adversarial hardening cycle, we discovered and proved a critical Out-of-Bounds (OOB) Read vulnerability in the GBDK decompressor. We implemented a highly optimized, size-bounded level decompressor that fully eliminates this vulnerability, integrated a comprehensive suite of 124 E2E and adversarial tests (100% pass rate), and verified that the compiled cartridge fits perfectly inside a flat 32KB ROM without any Memory Bank Controller (MBC), maintaining a massive budget safety margin.

---

## 2. Final Project Metrics

| Metric | Measured Value | Constraint / Limit | Status |
| :--- | :---: | :---: | :---: |
| **Total Raw Levels Size** | 46,800 Bytes (45.70 KB) | — | — |
| **Total Compressed Levels Size** | 11,050 Bytes (10.79 KB) | — | **76.4% Savings** |
| **Final Compiled ROM Size** | 32,768 Bytes (32.00 KB) | Exactly 32,768 Bytes | **PASS** |
| **Active ROM Footprint** | 21,146 Bytes (20.65 KB) | < 28,672 Bytes (28.00 KB) | **PASS (7.35KB margin)** |
| **Active WRAM Footprint** | 2,049 Bytes (2.00 KB) | — | — |
| **Cartridge Type (0x0147)** | `0x00` (ROM ONLY) | `0x00` (No MBC) | **PASS** |
| **Cartridge ROM Size (0x0148)** | `0x00` (32 KByte) | `0x00` (32 KByte) | **PASS** |
| **Total E2E Tests Count** | 124 Tests | — | **100% Pass Rate** |

---

## 3. Key Achievements & Implementation Logic

### 3.1. Vulnerability Discovery & Proof
- Spawning two parallel Challengers (`dc84f659-0fc8-4b64-8de8-e9ca02f17d3f` and `0146adc3-0de6-4950-afae-e618a8d95db9`) armed with the `test-coverage-audit` playbook exposed a critical Out-of-Bounds Read vulnerability in the original decompressor `dandy_load_level`.
- The decompressor decoded exactly 1,624 tiles of the inner map grid but performed no bitstream length validation. 
- Challengers wrote a dynamic level-injection test `test_adv04_truncated_bitstream_oob_read` using `mprotect` and `ctypes` that pointed the level database to a truncated 10-byte stream followed by `0xFF` (Generator 3) sentinels. The unmitigated C engine decoded 1,544 tiles from the OOB region, proving the vulnerability.

### 3.2. Size-Bounded Decompressor Mitigation (Worker)
- The Worker (`9ce87547-588d-4e24-acf7-1ae735a0aeb8`) implemented a Z80-optimized mitigation:
  1. **Dynamic Level Sizes**: Modified `tools/convert_levels.py` to output the exact compressed level sizes dynamically using C's compile-time `sizeof` operator into `const uint16_t dandy_level_sizes[DANDY_NUM_LEVELS]` inside `src/levels.c`.
  2. **Enforced Boundaries**: Modified `src/dandy_core.c:dandy_load_level` to establish `src_end = src + dandy_level_sizes[level_idx]`.
  3. **Safe Ternary Reading**: Replaced all 6 byte-reading sites (where the bit cache is exhausted) with the fast ternary check `(src < src_end) ? *src++ : 0`.
  4. **Natural Space Propagation**: Yielding `0` on stream exhaustion in Scheme B2 naturally propagates `0` bits which decode directly to `TILE_SPACE` (0). This elegantly fills the remaining tiles of a truncated level as spaces with zero runtime overhead or Z80 branching.
  5. **Test Update**: Updated `test_adv04` to assert that the decompressor safely decodes the truncated bitstream map as spaces and ignores sentinel bytes, proving the OOB read is fully eliminated.

### 3.3. Independent Reviews
- Spawning two independent Reviewers (`11e35b1f-9adb-4ffd-be47-059bab6053fa` and `0126a47c-d983-4a40-9e5d-89aea5219f8c`) confirmed that the bounds check adds only **61 bytes** of Z80 code, all tests pass, and all ROM constraints are perfectly satisfied, issuing two formal **APPROVE** verdicts.

### 3.4. Final Forensic Audit
- The Forensic Auditor (`a31a2f58-d949-4e45-855f-0768ad8816de`) executed a comprehensive verification of the entire codebase and build pipeline:
  - Confirmed **100% genuine dynamic execution** (no hardcoding of test results or facade behaviors in C files or tests).
  - Confirmed **flat, single-bank 32KB layout** (no MBC) by verifying that GBDK only compiles to Bank 0 and Bank 1, the ROM header Cartridge Type is `0x00` and ROM Size is `0x00`, and no bank switching statements exist in the codebase.
  - Confirmed the ROM is exactly **32,768 bytes** and the active footprint is **21,146 bytes** (well under the 28KB limit, leaving **7,526 bytes** of headroom).
  - Issued a formal **CLEAN** verdict.

---

## 4. Retrospective & Lessons Learned
- **Inverted Hardening Rigor**: Starting the hardening cycle with parallel Challengers allowed us to map the entire boundary state space and dynamically prove a critical memory safety flaw before touching production code.
- **Z80-Friendly Degradation**: Yielding default values (`0` -> `TILE_SPACE`) on boundary exhaustion is an exceptionally elegant optimization for resource-constrained 8-bit platforms, avoiding complex branching and state machines inside decoding loops.
- **Comprehensive E2E Testing**: Running tests on a shared C library wrapper (`libdandy_test.so`) combined with python `ctypes` level injection proved to be a highly effective, fast, and high-fidelity way to test GameBoy engine cores.

---

## 5. Verification Method

To independently verify the entire codebase and results in `dandy-gb/`:

1. **Run E2E & Adversarial Tests**:
   ```bash
   make clean && make test
   ```
   *Expected outcome*: 124 tests pass successfully with `OK`.

2. **Compile GameBoy ROM**:
   ```bash
   make clean && make LCC=/usr/local/google/home/jackpal/Developer/gbdk/bin/lcc
   ```
   *Expected outcome*: `Build successful: bin/dandy.gb`.

3. **Verify ROM Header Registers**:
   ```bash
   python3 -c "with open('bin/dandy.gb', 'rb') as f: data = f.read(); print('Cartridge Type:', hex(data[0x0147])); print('ROM Size:', hex(data[0x0148]))"
   ```
   *Expected outcome*: Cartridge Type: `0x0` (ROM ONLY), ROM Size: `0x0` (32 KByte).

4. **Verify ROM Size & Active Segment Footprint**:
   - ROM size is exactly `32,768` bytes.
   - Linker map segments `bin/dandy.map` active footprint (sum of `_CODE`, `_HOME`, `_CODE_1`, `_INITIALIZER`, `_GSINIT`, `_GSFINAL`) is exactly `21,146` bytes (well under the 28KB budget).
   - Alternatively, run the automated verification script:
     ```bash
     python3 tools/verify_compression.py
     ```
     *Expected outcome*: All checks pass successfully.

---

## 6. Key Artifacts

- `/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/.agents/sub_orch_m5/progress.md` — Detailed progress log and retrospective
- `/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/.agents/sub_orch_m5/BRIEFING.md` — Situational awareness history
- `/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/.agents/sub_orch_m5/gaps_synthesized.md` — Synthesized master gaps report
- `/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/.agents/auditor_m5/handoff.md` — Full Forensic Auditor report
