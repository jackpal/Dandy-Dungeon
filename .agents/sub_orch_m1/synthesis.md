# Synthesis Report: GameBoy Build Revert & Verification Foundation

## Consensus
1. **GameBoy Makefile Revert (`dandy-gb/Makefile`)**:
   - Revert the link configuration from the 4-bank 64KB MBC1 layout to a flat 32KB ROM (no-MBC).
   - Remove the `-Wl-yo4` flag (or replace with `-Wl-yo2` to explicitly target 32KB flat ROM).
   - Remove the special compilation target for `levels.o` using `-Wf-bo2` and place it in the default Bank 1 (`-Wf-bo1` or generic rule).
2. **Platform Independence (`src/dandy_core.c`)**:
   - Remove the `#include <gb/gb.h>` and `SWITCH_ROM(2)` calls inside `dandy_load_level`.
   - This removes the GBDK/GameBoy dependency from `dandy_core.c`, restoring it to 100% platform-independent code that compiles cleanly under WebAssembly and native offline test frameworks.
3. **Linker Map Parsing**:
   - Parse `dandy.map` using memory address thresholds:
     - **ROM**: `Address < 0x8000` (Bank 0 & Bank 1)
     - **WRAM**: `0xC000 <= Address < 0xE000`
     - **HRAM**: `0xFF80 <= Address`
   - Sum the active segment sizes to report precise memory consumption and enforce a 28KB safe budget for ROM space.
4. **Critical Bank Overflow Risk & Mitigation**:
   - The current level database compressed with simple RLE is ~27.1KB.
   - A flat 32KB ROM has two 16KB banks (Bank 0 and Bank 1). A single object file (`levels.o`) must fit entirely within a single bank.
   - Because 27.1KB exceeds the 16KB bank limit, the build will fail immediately with a bank overflow error if we attempt to compile all 26 levels.
   - **Mitigation**: Temporarily modify `dandy-gb/tools/convert_levels.py` or the level pipeline to export only the first 5 levels (approx 5.2KB) during Milestones 1 and 2. Once the custom 2D meta-tile compressor is implemented in Milestone 3, all 26 levels will fit under 12KB, and the full level set can be restored.

## Resolved Conflicts
- **Linker Flags**: Explorer 2 suggested removing the bank flag entirely, while Explorer 3 suggested replacing `-Wl-yo4` with `-Wl-yo2`. Both achieve the same objective, but `-Wl-yo2` explicitly targets 2 banks (32KB). We will instruct the Worker to use the appropriate Makefile configuration and let the verification script assert that the final ROM size is exactly 32,768 bytes.

## Dissenting Views
- None. Both active Explorers independently identified the identical files, line numbers, segment map parsing logic, and the critical bank overflow risk with the same level-limiting mitigation.

## Gaps
- None. The target files, lines, risks, and verification script design are fully understood and documented.
