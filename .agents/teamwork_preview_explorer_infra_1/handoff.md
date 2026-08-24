# Handoff Report: Dandy Dungeon Core Engine Analysis & E2E Test Infrastructure Design

This handoff report summarizes the analysis and design for Milestone 1 (Offline E2E Test Infrastructure), enabling subsequent agents to implement the testing framework.

---

## 1. Observation

During the read-only investigation, the following files and details were examined:
1. **`dandy-gb/src/dandy_core.h`**:
   - Declares 17 engine global variables including: `uint8_t dandy_map[1800]`, `uint8_t current_level`, `uint8_t player_x[4]`, `uint8_t player_y[4]`, `int16_t player_health[4]`, and `int8_t arrow_dir[4]`.
   - Declares 5 external HAL functions:
     ```c
     extern void hal_draw_tile(uint8_t x, uint8_t y, uint8_t tile_id);
     extern void hal_update_hud(void);
     extern void hal_clear_sprites(uint8_t vp_left, uint8_t vp_top);
     extern void hal_set_sprite(uint8_t sprite_idx, uint8_t x, uint8_t y, uint8_t tile_id, uint8_t flags);
     extern void hal_play_sound(uint8_t sound_id);
     ```
2. **`dandy-gb/src/dandy_core.c`**:
   - Includes `<gb/gb.h>` on line 1 for GameBoy-specific definitions:
     `1: #include <gb/gb.h>  // For SWITCH_ROM bank switching`
   - Invokes the `SWITCH_ROM(2)` macro on line 137 inside `dandy_load_level` to swap in the ROM bank containing level data.
3. **Compilation Behavior**:
   - Running `gcc -Isrc -c src/dandy_core.c` on the host system fails with:
     ```
     src/dandy_core.c:1:10: fatal error: gb/gb.h: No such file or directory
         1 | #include <gb/gb.h>  // For SWITCH_ROM bank switching
           |          ^~~~~~~~~
     compilation terminated.
     ```
4. **`dandy-gb/src/levels.c`**:
   - Contains a pure C array of RLE-compressed level data (`dandy_levels`) and has no platform-specific dependencies.
5. **`dandy-gb/Makefile`**:
   - Configured for GameBoy compilation via `lcc` and has a `web` target compiling the core engine to WebAssembly using `emcc`.

---

## 2. Logic Chain

From the observations, the following design decisions were made:
1. **GameBoy Header Interception**:
   - To compile `dandy_core.c` under GCC/Linux without modifying the original source code, we must intercept the `#include <gb/gb.h>` call.
   - We can create a mock header file at `tests/gb/gb.h` and add `-Itests` to the compiler flags.
   - Since modern systems have a flat 64-bit address space, bank-switching is unnecessary. Therefore, the mock header will define `SWITCH_ROM(bank)` as a no-op: `#define SWITCH_ROM(bank) ((void)0)`.
2. **Lightweight, Programmatic Mock HAL**:
   - The mock HAL must record side-effects in memory buffers so tests can query them.
   - Static buffers (e.g. `DrawEvent mock_draws[2048]`, `uint8_t mock_sounds[128]`, `SpriteState mock_sprites[40]`) are used because they are fast, simple, and avoid dynamic memory allocation overhead.
   - Extended query functions (e.g. `mock_get_draws`, `mock_get_sounds`, `mock_get_sprite`) are added to the C interface to expose these buffers to the Python test runner.
3. **Two-Way Python-C ctypes Bridge**:
   - The ctypes wrapper `tests/dandy_env.py` will use `in_dll` to bind directly to the live C global variables inside `libdandy_test.so`.
   - This provides live references: if the C engine updates player health, Python sees it instantly; if Python injects a custom level layout into `dandy_map`, the C engine uses it on the next step.
   - Python properties and getters/setters wrap these raw pointers into an elegant, high-level Python API.
4. **Compilation Pipeline**:
   - A new `test_lib` target will be added to the Makefile to compile `dandy_core.c`, `levels.c`, and `mock_hal.c` into a shared library `tests/libdandy_test.so` using `gcc -shared -fPIC -O2 -Isrc -Itests`.

---

## 3. Caveats

- **Buffer Limits**: The mock HAL uses fixed-size buffers (e.g., 2048 draw events, 128 sounds). While these are more than sufficient for GameBoy frames, tests that run for thousands of steps without calling `mock_clear()` could overflow them. The mock implementations safely clamp writes to prevent memory corruption, and the Python wrapper handles this cleanly.
- **Environment Assumptions**: The design assumes standard Linux GCC compiler and Python 3 are installed on the local system.

---

## 4. Conclusion

The E2E test infrastructure design successfully resolves the GameBoy-compilation dependency, provides a complete mock HAL with query extensions, and establishes a robust Python wrapper (`DandyEnv`) that bridges C globals and functions. This architecture supports transparent, opaque-box, and high-performance testing of all 8 core game features without physical hardware.

All designs, signatures, structures, makefile targets, and a draft for `TEST_INFRA.md` are documented in detail in `analysis.md` in the working directory.

---

## 5. Verification Method

To verify the infrastructure once implemented by the next agent:
1. **Compilation Check**:
   - Run `make test_lib` in `dandy-gb/`.
   - Confirm that `tests/libdandy_test.so` is built successfully and is a valid shared object.
2. **Python Load Check**:
   - Execute a Python script that instantiates `DandyEnv` and verifies that the library loads.
3. **State Sync Check**:
   - Call `env.init()` in Python.
   - Assert that `env.current_level == 0` and `env.get_player_health(0) == 100`.
   - Change `env.current_level = 3` in Python, call `env.load_level(3)`, and verify that `env.current_level == 3` and the map contains the decompressed Level 3 tiles.
4. **Mock HAL Event Recording Check**:
   - Set up player next to a key tile.
   - Run a step `env.step([env.BUTTON_RIGHT, 0, 0, 0])` (moving onto the key).
   - Assert that `env.get_player_keys(0) == 1`.
   - Assert that `env.mock_get_sounds()` contains `env.SOUND_KEY` (4).
   - Assert that `env.mock_get_draw_count() > 0` (hud/viewport redraws).
