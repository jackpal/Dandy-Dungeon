# Handoff Report: E2E Milestone 3 Testing Analysis & Case Designs

## 1. Observation
- **Core Engine Source Code**: Investigated `dandy-gb/src/dandy_core.c` and `dandy-gb/src/dandy_core.h`.
- **Test Runner and Tier 1 Tests**: Analyzed `dandy-gb/tests/dandy_env.py` and `dandy-gb/tests/test_tier1.py`.
- **Test Infrastructure Rules**: Analyzed `TEST_INFRA.md` at the repository root.
- **Specific Code Observations**:
  1. **Generator Spawning Edge Checks (F-08)**: Line 627 of `dandy_gb/src/dandy_core.c` reads:
     ```c
     uint16_t g_pos = row_offsets[my + dir_delta_y[check_dir]] + (mx + dir_delta_x[check_dir]);
     ```
     This does not perform boundary checks on `my + dir_delta_y[check_dir]` or `mx + dir_delta_x[check_dir]`, causing row wrapping on X-axis edges and OOB memory access on Y-axis edges.
  2. **Flood Fill Stack Size (F-04)**: Lines 98-101 of `dandy_gb/src/dandy_core.c` define:
     ```c
     #define FLOOD_STACK_SIZE 64
     static uint8_t flood_stack_x[FLOOD_STACK_SIZE];
     static uint8_t flood_stack_y[FLOOD_STACK_SIZE];
     static int8_t flood_stack_ptr = 0;
     ```
     Pushes beyond 64 are silently dropped in `flood_push()`, leaving door tiles locked in large networks.
  3. **Player Health Type (F-03)**: Lines 51 and 64 of `dandy_gb/src/dandy_core.h` define `player_health` as a signed 16-bit integer:
     ```c
     extern int16_t player_health[MAX_PLAYERS];
     ```
     Collecting food adds 100 without ceiling clamping:
     ```c
     player_health[p_idx] += 100;
     ```
     This can trigger a signed overflow when health exceeds `32767`, leading to negative health and instant death.

---

## 2. Logic Chain
1. **Target Feature F-08**: Without boundary checks, spawning at `mx = 59` (right edge) wraps to `mx = 0` (left edge) on the next row because the map array `dandy_map` is flat ($60 \times 30$). Similarly, at `my = 0` (top edge), spawning Up indexes `row_offsets[-1]` (underflows to `255`), attempting to read arbitrary memory before `row_offsets`.
2. **Target Feature F-09**: व्यूपोर्ट camera centering logic correctly clamps the viewport top-left to `(0, 0)` and `(40, 20)`. When the local player is dead, spectator mode averages coordinates of other joined and alive players. If all other players are dead, the divisor becomes 0, which is protected by `if (alive_count > 0)` and falls back to centering on the dead local player's coordinate.
3. **Target Feature F-10**: During a level warp, player starting coordinates are calculated by adding offsets to the portal tile (`TILE_UP`). If the portal is placed at `(0, 0)`, the offsets for Player 0 `(0, -1)` and Player 3 `(-1, 0)` both clamp to `(0, 0)`. Thus, Player 3's map tile overwrites Player 0's map tile at `(0, 0)` while both logically share the coordinate.
4. **Vulnerabilities**: These engine limitations (OOB wrapping, flood fill limit, health overflow) provide excellent corner-case scenarios. We incorporated them as Tier 2 tests to verify the engine's behavior under extreme boundaries.
5. **Double-Assert Coverage**: To meet the Double-Assert Rule, every designed test case specifies assertions for both C globals (e.g., coordinates, health, map values) and Mock HAL buffers (e.g., sound counts, draws, camera targets).

---

## 3. Caveats
- **Segfault on Invalid Level Index**: Programmatically calling `load_level(5)` indexes `dandy_levels[5]`. Since the array has only 5 elements, it will read a garbage pointer, resulting in a segmentation fault. We documented this as a boundary case but note that it will crash the process under test rather than fail a standard assertion.
- **LFSR Seed Reset**: The Galois LFSR seed is a local static variable (`static uint16_t rand_seed = 0xACE1;`) inside `move_monsters()`. Its state cannot be directly reset or read from Python. However, since the test runner creates a fresh `libdandy_test.so` copy for each test case, the seed is guaranteed to start at `0xACE1` on every run, enabling 100% deterministic spawning sequences.

---

## 4. Conclusion
We have completed a comprehensive read-only analysis and produced **49 Tier 2 (Boundary & Corner Cases) tests** and **8 Tier 3 (Cross-Feature Interactions) tests** (totaling 57 test designs), exceeding the Milestone 3 requirements ($\ge 40$ Tier 2 and $\ge 8$ Tier 3 tests). The complete designs, including name, setup, input, and double-assertions, are documented in `analysis.md`.

---

## 5. Verification Method
To verify the test designs and findings:
1. **Inspect Analysis File**: Review the complete specifications at `/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/.agents/explorer_e2e_m3_3_gen2/analysis.md`.
2. **Execute Existing Tier 1 Tests**: Run `make test` from the `dandy-gb/` directory to ensure the baseline test environment is fully functional:
   ```bash
   cd /usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb && make test
   ```
3. **Verify Vulnerabilities**: Check `dandy-gb/src/dandy_core.c` around line 627 (generator spawning), lines 98-107 (flood fill), and `dandy-gb/src/dandy_core.h` around line 51 (health type) to confirm the code matches the observations.
