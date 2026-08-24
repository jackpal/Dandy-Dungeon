# Handoff Report: Offline E2E Test Infrastructure Design (Milestone 1)

## 1. Observation

- **Core Engine Files**:
  - `dandy_core.h` is located at `/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb/src/dandy_core.h`. It declares the Game State Globals (lines 41-62) and Core Functions (lines 64-70) and HAL Helper Functions (lines 72-78).
    - Verbatim Game State Globals:
      ```c
      extern uint8_t dandy_map[MAP_SIZE];
      extern uint8_t current_level;
      extern uint8_t monster_rotor;
      extern bool player_joined[MAX_PLAYERS];
      extern uint8_t local_player_idx;
      ...
      extern bool is_dirty;
      ```
    - Verbatim Core Functions:
      ```c
      void dandy_init(void);
      void dandy_step(const uint8_t player_inputs[MAX_PLAYERS]);
      void dandy_load_level(uint8_t level_idx);
      void dandy_draw_viewport(uint8_t local_p_idx);
      void dandy_join_player(uint8_t p_idx);
      bool dandy_is_player_joined(uint8_t p_idx);
      ```
    - Verbatim HAL Helpers:
      ```c
      extern void hal_draw_tile(uint8_t x, uint8_t y, uint8_t tile_id);
      extern void hal_update_hud(void);
      extern void hal_clear_sprites(uint8_t vp_left, uint8_t vp_top);
      extern void hal_set_sprite(uint8_t sprite_idx, uint8_t x, uint8_t y, uint8_t tile_id, uint8_t flags);
      extern void hal_play_sound(uint8_t sound_id);
      ```
  - `dandy_core.c` is located at `/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb/src/dandy_core.c`.
    - Line 1 contains a GameBoy-specific include: `#include <gb/gb.h>`.
    - Line 137 contains a GameBoy ROM bank switching macro: `SWITCH_ROM(2);`.
    - Line 616 contains a static global seed: `static uint16_t rand_seed = 0xACE1;`.
    - Line 330 contains static input history: `static uint8_t old_buttons[MAX_PLAYERS] = {0, 0, 0, 0};`.

- **Makefile**:
  - Located at `/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb/Makefile`.
  - It compiles GameBoy targets using GBDK's `lcc` compiler (lines 37-45).
  - It has a `web` target compiling the engine to WebAssembly using `emcc` (lines 63-83).
  - It has a `levels` target to generate the C levels file (lines 48-50).

---

## 2. Logic Chain

1. **Host Compilation Feasibility**:
   - Compiling `dandy_core.c` directly on a host machine using `gcc` will fail because `<gb/gb.h>` is a GameBoy-specific header not present in standard host compiler include paths.
   - To compile without modifying the game engine source code (preserving the read-only constraint), we can intercept the include by creating a mock header `tests/mock_gb/gb/gb.h` and passing `-Itests/mock_gb` as a compiler flag.
   - Inside `tests/mock_gb/gb/gb.h`, we can define a dummy `#define SWITCH_ROM(bank) ((void)0)` macro. This makes host compilation of `dandy_core.c` succeed perfectly without altering its code.

2. **State Isolation**:
   - `dandy_core.c` contains static globals (`rand_seed`, `old_buttons`, `flood_stack_*`) that are not cleared or reset in `dandy_init()`.
   - Running multiple tests sequentially in the same process would lead to test-to-test pollution, where the seed or input state of one test case affects subsequent test cases.
   - To guarantee perfect test isolation, we design a **Copy-on-Load** mechanism in the Python ctypes wrapper (`dandy_env.py`).
   - For each test case, the Python wrapper copies `libdandy_test.so` to a unique temporary file, loads it via `ctypes.CDLL`, and deletes it on destruction. This ensures each test starts with a completely fresh, isolated memory space.

3. **Requirement-Driven Assertions (Opaque Box)**:
   - To verify game rules (such as drawing, sounds, and sprite registers) without depending on internal implementation details, the Mock HAL must record all engine side-effects in queryable buffers.
   - By logging `hal_draw_tile`, `hal_set_sprite`, and `hal_play_sound` calls, the Python test suite can easily perform double-assertions: checking both the game state (e.g. coordinates and inventory) and the mock HAL logs (e.g. specific sounds played and drawings made).

---

## 3. Caveats

- **No Emulator Integration**: This offline test infrastructure operates strictly at the C logic level on the host system. It does not run inside a GameBoy emulator. Any bugs arising from compiler-specific codegen bugs (e.g., GBDK-specific optimizer issues) or hardware timing nuances will not be caught.
- **Levels Compilation**: The shared library target `libdandy_test.so` depends on `src/levels.c` being present. Since `src/levels.c` is dynamically generated, `make test_lib` must depend on the `levels` target to prevent compilation failures.
- **Network Restrictions**: In compliance with the `CODE_ONLY` network mode, no external packages (such as pip libraries or external test runners) are introduced. Only the standard Python `unittest` library and standard `gcc` are utilized.

---

## 4. Conclusion

Milestone 1 is fully designed. We have provided:
1. Complete, production-grade C code for `tests/mock_hal.h` and `tests/mock_hal.c`.
2. Complete Python ctypes wrapper `tests/dandy_env.py` featuring unique "Copy-on-Load" state isolation.
3. Precise Makefile target (`libdandy_test.so` and `test`) and compiler flags.
4. Comprehensive draft for `TEST_INFRA.md` containing a complete game feature inventory and coverage tier targets.
5. A rigorous verification plan to validate the infrastructure.

All designs are non-intrusive: they require absolutely **zero modifications** to the core game engine source files.

---

## 5. Verification Method

To verify the test infrastructure once implemented:
1. **Compilation**: Run `make test_lib` to verify successful compilation of `libdandy_test.so` without any warnings/errors, and check that `tests/mock_gb/gb/gb.h` is correctly generated.
2. **Dynamic Symbol Table**: Run `nm -D libdandy_test.so` to confirm that all required core globals (e.g., `dandy_map`, `current_level`) and functions (e.g., `dandy_init`, `mock_get_draw_count`) are publicly exported.
3. **Run Test Harness**: Put a dummy test case in `tests/test_infra.py` and run `make test`. Ensure that it executes cleanly in under 50ms and reports success.
