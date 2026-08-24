# Handoff Report: Offline E2E Test Infrastructure Design
**Milestone 1: Test Infrastructure & Runner Design**

This handoff report summarizes the technical findings and architectural designs for the Dandy Dungeon offline E2E test infrastructure. It is fully self-contained, providing the next agent (implementer) with all necessary instructions and designs to build the mock HAL, ctypes wrapper, and Makefile targets.

---

## 1. Observation
1. **Source Code Dependencies**: In `dandy-gb/src/dandy_core.c`, GBDK-2020 dependencies are limited to:
   - Line 1: `#include <gb/gb.h>  // For SWITCH_ROM bank switching`
   - Line 137: `SWITCH_ROM(2);`
   - No other platform-specific functions or macros from GBDK are used in the core engine logic.
2. **Global State Variables**: In `dandy-gb/src/dandy_core.h`, the game state is managed via 17 global variables/arrays:
   - Map buffer: `uint8_t dandy_map[MAP_SIZE]` (line 42)
   - Game parameters: `current_level`, `monster_rotor`, `player_joined`, `local_player_idx`, `is_dirty` (lines 43-46, 62)
   - Player state arrays: `player_x`, `player_y`, `player_health`, `player_score`, `player_bombs`, `player_keys`, `player_dir`, `player_move_timer` (lines 49-56)
   - Arrow state arrays: `arrow_x`, `arrow_y`, `arrow_dir` (lines 58-60)
3. **Core Functions**: In `dandy-gb/src/dandy_core.h`, the engine exposes:
   - `dandy_init`, `dandy_step`, `dandy_load_level`, `dandy_draw_viewport`, `dandy_join_player`, `dandy_is_player_joined` (lines 65-70)
4. **Hardware Abstraction Layer**: The core engine declares 5 external HAL functions to be implemented by the platform (lines 74-78):
   - `hal_draw_tile`, `hal_update_hud`, `hal_clear_sprites`, `hal_set_sprite`, `hal_play_sound`
5. **Makefile Structure**: In `dandy-gb/Makefile`, we observed:
   - GBDK-specific compiler is `lcc` (line 5).
   - Clean targets remove `OBJ_DIR` and `BIN_DIR` completely (lines 89-94).
   - No host-compilation targets exist for GCC/Clang.
6. **Level Database**: In `dandy-gb/src/levels.c`, level data is stored as raw compressed byte arrays (e.g. `dandy_level_0`) without any platform-specific header dependencies, including only `"levels.h"`.

---

## 2. Logic Chain
1. **Compilation Feasibility on Host**: Since GBDK dependencies in `dandy_core.c` are limited to including `<gb/gb.h>` and calling `SWITCH_ROM(2)` (Observation 1), we can compile the file on a standard Linux host without modifying the source code by providing a dummy `gb/gb.h` header in the host include path that defines `SWITCH_ROM(bank)` as `((void)0)`.
2. **State and Control Exposure**: Because the engine uses standard global C variables for state tracking (Observation 2) and standard C functions for stepping (Observation 3), compiling these files into a host shared library (`.so`) allows Python's `ctypes` module to directly bind to, read, and write these memory addresses.
3. **Programmatic Assertion of Side Effects**: The 5 external HAL functions (Observation 4) represent the only side effects of the game loop (VRAM writes, audio, HUD updates). By implementing a mock version of these functions in `mock_hal.c` that records parameters in static arrays, we can expose simple C query functions (e.g., `mock_get_draw`) to let Python assert that visual tiles were drawn and sounds were played.
4. **Makefile Integration**: Since the existing `clean` target in `dandy-gb/Makefile` removes `BIN_DIR` (Observation 5), compiling the shared library into `bin/libdandy_test.so` ensures it is cleanly integrated and automatically wiped during clean cycles.
5. **Requirements Scoping**: Combining the 8 core features of the engine (drawn from code analysis) with structured testing tiers (Tiers 1-4) establishes a rigorous verification path, mapped out in the new `TEST_INFRA.md`.

---

## 3. Caveats
- **Galois LFSR Seed**: The monster generator uses a static LFSR seed (`rand_seed = 0xACE1`) in `dandy_core.c:616` to determine spawning. Tests that assert exact spawning sequences must account for this deterministic PRNG state. Since `rand_seed` is static inside `move_monsters`, it cannot be reset via ctypes without restarting the shared library or modifying the C code. However, because it is deterministic, test runs starting from a fresh `dandy_init()` will always produce the exact same sequence of spawns, making them fully reproducible.
- **Shared Library Caching**: Python's `ctypes` caches loaded shared libraries in memory. In multi-test suites, state must be reset programmatically using `env.init()` and `env.clear_mock_buffers()` rather than relying on reloading the library.

---

## 4. Conclusion
We have designed a robust, non-intrusive offline E2E test infrastructure that compiles the GameBoy core engine unchanged on the host system. The design consists of:
1. **Host-compilable Mock HAL** (`tests/mock_hal.c/h`) and dummy GameBoy header (`tests/mock_headers/gb/gb.h`) that completely mock VRAM/Audio and record all engine side effects.
2. **Clean Python Ctypes Wrapper** (`tests/dandy_env.py`) that maps all 17 engine globals and provides high-level Pythonic APIs for assertions.
3. **Host Shared Library Target** added to `dandy-gb/Makefile` under `test_lib` compiling with `-fPIC` and `-shared`.
4. **Draft `TEST_INFRA.md`** defining the 8 core features, E2E architecture, and coverage thresholds.

All design details, code listings, and signatures are written to the main report:
**Path**: `/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/.agents/teamwork_preview_explorer_infra_2/analysis.md`

---

## 5. Verification Method

### How to Verify the Design (Verification Plan)
The implementer can independently verify this infrastructure design by performing the following steps:

1. **Setup Mock Headers and HAL**:
   Create a dummy `tests/mock_headers/gb/gb.h` containing:
   ```c
   #ifndef MOCK_GB_H
   #define MOCK_GB_H
   #define SWITCH_ROM(bank) ((void)0)
   #endif
   ```
   Implement `tests/mock_hal.c` and `tests/mock_hal.h` based on the signatures in `analysis.md`.
2. **Build the Shared Library**:
   Run the following command in the `dandy-gb` directory:
   ```bash
   make test_lib
   ```
   *Verification condition: The command completes successfully and `bin/libdandy_test.so` is created.*
3. **Verify Python Integration**:
   Create a simple script `tests/verify_run.py`:
   ```python
   from dandy_env import DandyEnv
   env = DandyEnv()
   env.init()
   assert env.current_level == 0
   assert env.player_health[0] == 100
   print("Verification SUCCESS: Game initialized and globals verified!")
   ```
   Run with:
   ```bash
   PYTHONPATH=tests python3 tests/verify_run.py
   ```
   *Verification condition: Script runs without error and prints the success message.*
