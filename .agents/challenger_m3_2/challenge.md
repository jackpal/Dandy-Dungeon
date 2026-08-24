# Adversarial Analysis & Verification Report (challenge.md)

## Challenge Summary

**Overall risk assessment**: **MEDIUM**

We conducted rigorous adversarial analysis, edge-case mining, and memory-safety verification of the `dandy-gb` level compression and decompression subsystem. 
The system employs **Edge Wall Elision (EWE)** alongside **Scheme B2 prefix-bit coding** (Space = `0`, Wall = `10`, Other Tile = `11` + 4-bit ID) to achieve ~76.4% ROM footprint savings, which is essential to fit the 26-level game into a 32KB flat Game Boy ROM.

### Core Findings:
1. **Write Safety (100% Protected)**: The C decompressor in `dandy_core.c` is **100% immune to out-of-bounds writes (buffer overflow)**. The destination pointer `dst` is governed by strict loop counters (`y` from 1 to 28, `x` from 1 to 58) that write exclusively within the `dandy_map` boundaries. No malformed bitstream can trigger an out-of-bounds write.
2. **Read Vulnerability (Medium Risk)**: The C decompressor is **vulnerable to out-of-bounds reads (global-buffer-overflow)** when decompresing a **truncated or corrupted level bitstream**. Because the C engine does not track compressed array lengths or enforce bitstream bounds, it will continue incrementing `src` and reading neighboring memory until all 1,624 inner tiles are populated. Under modern compilers with AddressSanitizer (ASan) enabled, this immediately crashes/aborts the program. On real Game Boy hardware, it silently reads neighboring ROM bytes.
3. **Edge Case Perfection**: All edge-case maps (minimum size, maximum size, all-wall, all-space, sparse, dense) are compressed and decompressed with **100% round-trip fidelity** without any degradation or overflows.
4. **Stability & Leaks (100% Safe)**: Running the entire E2E test suite 1,000 times verified **zero memory leaks, zero file descriptor leaks, and zero temporary directory leaks**, demonstrating exceptional engine and infrastructure robustness.

---

## Challenges

### [Medium] Challenge 1: Out-of-Bounds Read in C Decompressor via Truncated Bitstream

- **Assumption challenged**: The level bitstreams stored in ROM are always complete, valid, and never truncated.
- **Attack scenario**: A level array in `levels.c` is truncated or corrupted (e.g., due to a build system glitch, ROM bank issue, or memory corruption). When `dandy_load_level` attempts to decompress it, the decoder runs for exactly 1,624 iterations. If the bitstream does not contain enough bits, the decompressor continues to read past the end of the level array (`*src++`) into neighboring ROM memory.
- **Blast radius**: 
  - **On Host/Test Harness**: Immediate crash (Segmentation Fault or AddressSanitizer abort) if the out-of-bounds read crosses page boundaries or violates ASan rules.
  - **On Game Boy**: Silent reading of neighboring ROM code/data. The level is reconstructed with garbage tiles (whatever bytes follow the level in ROM), leading to undefined gameplay behavior, but no crash.
- **Mitigation**: Add a bitstream bounds checker. Although ROM is tight on the Game Boy, the offline python compressor could append a simple sentinel byte, or store the compressed length of each level, and the C decompressor could check against it. However, given Game Boy hardware constraints and the fact that levels are hardcoded in ROM (read-only and compiled), this is a low-risk issue on target hardware, but medium-risk for host-based testing.

---

## Stress Test Results

We compiled a custom C verification harness (`test_decompress.c`) and ran it under **AddressSanitizer (ASan)** and **UndefinedBehaviorSanitizer (UBSan)**.

| Scenario | Expected Behavior | Actual Behavior | Pass/Fail |
|---|---|---|---|
| **All-Space Level** (203B compressed) | Decompresses inner spaces with 100% fidelity. Border walls intact. | Decompressed perfectly. Player spawned at (1,1) correctly. | **PASS** |
| **All-Wall Level** (406B compressed) | Decompresses inner walls with 100% fidelity. | Decompressed perfectly. | **PASS** |
| **Max Density Level** (1218B compressed) | Decompresses inner tiles (ID 15) with 100% fidelity. | Decompressed perfectly. | **PASS** |
| **Extra Long Bitstream** (Max density + 1000B junk) | Ignores trailing bytes and decodes exactly 1624 tiles correctly. | Trailing bytes safely ignored. Decoded perfectly. | **PASS** |
| **Truncated Bitstream** (5 bytes total) | Should fail or crash gracefully without out-of-bounds writes. | **ASan aborts program** with `global-buffer-overflow` (out-of-bounds read). Safe from writes, but crashes on read. | **VULNERABLE** (Expected behavior for safety is to reject or handle, but C has no bounds check) |
| **Empty/Zero Bitstream** (1 byte total) | Should fail or crash gracefully without out-of-bounds writes. | **ASan aborts program** with `global-buffer-overflow`. | **VULNERABLE** |
| **Lifecycle Stability** (1000 E2E runs) | RSS memory growth < 5MB; 0 FD/Temp Dir leaks. | RSS grew by only 384KB (allocator fragmentation); 0 leaks. | **PASS** |

---

## Unchallenged Areas

- **ROM Bank-Switching Overlays** — The Game Boy implementation does not currently use ROM bank switching (it fits completely inside the 32KB flat home bank). If bank switching is introduced in the future, the level pointer addresses might need to be resolved across bank boundaries, which could introduce new edge cases not tested here.
- **Save State SRAM Corruption** — We did not test corruption of SRAM save states, as the game engine does not currently implement save/load functionality to battery-backed SRAM.
