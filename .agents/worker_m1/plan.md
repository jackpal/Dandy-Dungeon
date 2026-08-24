# Implementation Plan - GameBoy Build System Revert & Verification Foundation

This plan outlines the steps to revert the GameBoy build system to a flat 32KB ROM, apply platform-independence to `dandy_core.c`, apply the level-limiting mitigation, and implement the automated verification pipeline.

## Step 1: Revert GameBoy Compilation and Build System
- **File**: `dandy-gb/Makefile`
- **Changes**:
  - Change GBDK link flag in `LCCFLAGS` from `-Wl-yo4` to `-Wl-yo2`.
  - Remove custom compilation target for `levels.o` (which uses `-Wf-bo2` to place it in Bank 2) and compile it into default Bank 1 (using `-Wf-bo1`).
- **Verification**:
  - Verify that the Makefile syntax is correct and the lines are modified exactly as required.

## Step 2: Restore Platform Independence to `dandy_core.c`
- **File**: `dandy-gb/src/dandy_core.c`
- **Changes**:
  - Remove `#include <gb/gb.h>` at the top of the file.
  - Remove `SWITCH_ROM(2);` inside `dandy_load_level`.
- **Verification**:
  - Verify that the code doesn't contain any references to `<gb/gb.h>` or `SWITCH_ROM`.

## Step 3: Apply 16KB Bank Overflow Mitigation
- **File**: `dandy-gb/tools/convert_levels.py`
- **Changes**:
  - Slice `levels` to the first 5 levels: `levels = levels[:5]` right after loading all levels.
- **Verification**:
  - Run `python3 tools/convert_levels.py` and verify it reports `Found 26 levels.` but only processes/converts 5 levels (e.g. outputs 5 levels to `src/levels.c` and `levels.h` has `DANDY_NUM_LEVELS` set to 5).

## Step 4: Implement Automated Verification Script
- **File**: `dandy-gb/tools/verify_compression.py`
- **Changes**:
  - Create the script based on `/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/.agents/explorer_m1_3/proposed_verify_compression.py`.
- **Verification**:
  - Run `python3 tools/verify_compression.py` to compile, verify ROM size, verify active ROM budget, and run round-trip level compression checks.
  - Ensure all checks pass.

## Step 5: Document Results and Handoff
- **Files**:
  - `changes.md` - Structured completion report listing files modified and build/test results.
  - `handoff.md` - Structured handoff report (Observation, Logic Chain, Caveats, Conclusion, Verification Method).
