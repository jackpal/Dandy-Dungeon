# Handoff Report — Explorer 2 (Milestone 4)
**Milestone**: Milestone 4 (Complex Combat & Survival Scenarios)
**Task Status**: Complete (Hard Handoff)
**Working Directory**: `/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/.agents/explorer_m4_2`

---

## 1. Observation

We directly observed and analyzed the codebase to understand combat, generator spawning, and smart bomb mechanics.

### 1.1. Core Engine Mechanics in `dandy_core.c`
*   **Smart Bomb Area of Effect**:
    In `dandy_core.c` (lines 496-513):
    ```c
    static void do_bomb(uint8_t p_idx) {
        // Blow up monsters/generators in the visible viewport of player p_idx
        int16_t vp_left = clamp((int16_t)player_x[p_idx] - 10, 0, DANDY_LEVEL_WIDTH - 20);
        int16_t vp_top = clamp((int16_t)player_y[p_idx] - 5, 0, DANDY_LEVEL_HEIGHT - 10);
        
        for (uint8_t y = 0; y < 10; ++y) {
            uint16_t row_offset = row_offsets[vp_top + y];
            for (uint8_t x = 0; x < 20; ++x) {
                uint16_t pos = row_offset + (vp_left + x);
                uint8_t tile = dandy_map[pos];
                if ((tile >= TILE_MONSTER1 && tile <= TILE_MONSTER3) ||
                    (tile >= TILE_GENERATOR1 && tile <= TILE_GENERATOR3)) {
                    dandy_map[pos] = TILE_SPACE;
                }
            }
        }
        is_dirty = true;
    }
    ```
*   **Generator Spawning & LFSR**:
    In `dandy_core.c` (lines 622-642):
    ```c
                } else if (tile >= TILE_GENERATOR1 && tile <= TILE_GENERATOR3) {
                    static uint16_t rand_seed = 0xACE1;
                    uint8_t lsb = rand_seed & 1;
                    rand_seed >>= 1;
                    if (lsb) {
                        rand_seed ^= 0xB400u;
                    }
                    
                    if ((rand_seed & 7) < 4) {
                        uint8_t spawn_dir = (rand_seed & 3) * 2;
                        for (uint8_t dd = 0; dd < 8; dd += 2) {
                            uint8_t check_dir = (spawn_dir + dd) % 8;
                            uint16_t g_pos = row_offsets[my + dir_delta_y[check_dir]] + (mx + dir_delta_x[check_dir]);
                            if (dandy_map[g_pos] == TILE_SPACE) {
                                dandy_map[g_pos] = TILE_MONSTER1 + (tile - TILE_GENERATOR1);
                                is_dirty = true;
                                break;
                            }
                        }
                    }
                }
    ```
*   **Arrow Flight, Hit, and Degradation**:
    In `dandy_core.c` (lines 443-494), we observed that arrows move 1 tile per step, are bounded by the player's viewport (dying if they cross its edge), and damage entities:
    - Generators are killed in one hit (`replacement = TILE_SPACE`).
    - Monsters level 3 and 2 degrade (`replacement = tile_at_new - 1`).
    - Monsters level 1 are killed (`replacement = TILE_SPACE`).
    - Hitting destructibles plays `SOUND_HIT`.

### 1.2. LFSR Simulation
Running our local simulation script `lfsr_calc.py` (which mirrors the C engine's Galois LFSR math) yielded the following sequence of seeds, spawn decisions, and spawn directions starting from the initial `0xACE1`:
*   **Step 1**: Seed: `0xe270` | Spawn? **True** | Dir: **0** (Up)
*   **Step 2**: Seed: `0x7138` | Spawn? **True** | Dir: **0** (Up)
*   **Step 3**: Seed: `0x389c` | Spawn? **False** | Dir: **0** (Up)
*   **Step 4**: Seed: `0x1c4e` | Spawn? **False** | Dir: **4** (Down)
*   **Step 5**: Seed: `0xe27`  | Spawn? **False** | Dir: **6** (Left)
*   **Step 6**: Seed: `0xb313` | Spawn? **True** | Dir: **6** (Left)
*   **Step 7**: Seed: `0xed89` | Spawn? **True** | Dir: **2** (Right)
*   **Step 8**: Seed: `0xc2c4` | Spawn? **False** | Dir: **0** (Up)

---

## 2. Logic Chain

1.  **Isolated CDLL Loading**: The Python test wrapper `DandyEnv` copying the shared library `libdandy_test.so` to a unique temp directory (`self._temp_lib_path`) for each test run (observed in `dandy_env.py` lines 70-76) guarantees that the static variable `rand_seed` is always reset to its initial value of `0xACE1` at the start of every single test case.
2.  **Rotor Synchronization**: The sparse grid indexing (`monster_rotor` mod 4 and div 4) dictates that generators placed at `(mx, my)` where `mx % 4 == 1` and `my % 4 == 0` are ticked when `monster_rotor == 1`.
3.  **LFSR Progression**: Placing four generators at `(9, 8)`, `(13, 8)`, `(9, 12)`, and `(13, 12)` means they are processed row-by-row, column-by-column in the first tick (where `monster_rotor = 1`):
    - Gen 1 `(9, 8)` ticks on LFSR step 1 -> Spawns Level 1 monster at `(9, 7)`.
    - Gen 2 `(13, 8)` ticks on LFSR step 2 -> Spawns Level 2 monster at `(13, 7)`.
    - Gen 3 `(9, 12)` ticks on LFSR step 3 -> No spawn.
    - Gen 4 `(13, 12)` ticks on LFSR step 4 -> No spawn.
    - This creates a completely deterministic, reproducible swarm scenario that we can assert against.
4.  **AABB Boundary Proof**: Placing entities inside the player's 10x20 viewport `x` in `[0, 19]`, `y` in `[5, 14]`, and outside the viewport (e.g. `x=20`, `y=4`, `y=15`), and calling `do_bomb` allows us to verify that the smart bomb area-of-effect strictly adheres to the viewport dimensions.
5.  **Double-Assert Conformance**: Both scenarios verify internal C state (positions, tile IDs, health, and seeds) and retro-hardware registers (camera offsets, sprite tables, sound effect plays), fully complying with the Double-Assert Rule.

---

## 3. Caveats

*   **Rotor Initialization**: We assume `monster_rotor` starts at 0, which is guaranteed by `dandy_init()`. We explicitly set `self.env.monster_rotor = 0` in our test setup helper to be 100% safe.
*   **Viewport Size**: Viewport dimensions are assumed to be exactly 10x20, and the camera scrolling clamps to level dimensions (`60x30` tiles). Our design is fully scoped to this.
*   **No Other Generators**: We assume no other generators are present on the custom map other than the ones we explicitly place. This is guaranteed by our `helper_setup_clean_map` method which fills the map with `TILE_SPACE` before placing test-specific tiles.

---

## 4. Conclusion

We have successfully designed two comprehensive E2E test scenarios:
1.  **Scenario A (Generator & Monster Swarm)**: Verifies deterministic generator spawning, monster pathfinding, arrow flight, one-hit kills of generators, monster degradation, and sound effects under a complex combat and survival situation.
2.  **Scenario B (Smart Bomb Room Clear)**: Verifies the viewport-wide area-of-effect of the smart bomb and strict boundary immunity for entities outside the viewport.

These designs are fully detailed with step-by-step execution traces, expected C states, and retro-hardware HAL logs, and are ready for immediate implementation.

---

## 5. Verification Method

1.  **Inspect Analysis**: Read `/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/.agents/explorer_m4_2/analysis.md` to review the E2E test designs.
2.  **Run LFSR Calculation**: Execute `python3 .agents/explorer_m4_2/lfsr_calc.py` from the project root to verify the mathematical sequence of the Galois LFSR.
3.  **Code Implementation**: Once the next agent (Implementer) writes the code to a new test file under `dandy-gb/tests/` (e.g. `test_tier4_combat.py`), the suite can be executed using:
    ```bash
    python3 -m unittest dandy-gb/tests/test_tier4_combat.py
    ```
    Or by running the global test runner:
    ```bash
    make test
    ```
