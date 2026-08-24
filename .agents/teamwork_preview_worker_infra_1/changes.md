# Changes Report

This document details all the files created and modified to implement the offline E2E test infrastructure (Milestone 1) for the Dandy Dungeon project.

## Created Files

### 1. `dandy-gb/tests/mock_hal.h`
- **Purpose**: Declares the standard GameBoy Hardware Abstraction Layer (HAL) function signatures used by the core engine and the mock control/query extensions exposed to the Python test harness.
- **Key Signatures**:
  - Standard HAL: `hal_draw_tile`, `hal_update_hud`, `hal_clear_sprites`, `hal_set_sprite`, `hal_play_sound`.
  - Extensions: `mock_clear_buffers`, `mock_get_draw_count`, `mock_get_draw`, `mock_get_sound_count`, `mock_get_sound`, `mock_get_sprite`, `mock_is_sprite_active`, `mock_get_hud_update_count`, `mock_get_camera`.

### 2. `dandy-gb/tests/mock_hal.c`
- **Purpose**: Implements the mock HAL. Instead of writing to GameBoy VRAM or sound registers, it records all drawing, sound, sprite, HUD, and camera invocations in static internal buffers.
- **Key Details**:
  - Uses static arrays (`mock_draws`, `mock_sounds`, `mock_sprites`) with strict bounds checking.
  - Implements the mock query extensions to allow the Python wrapper to inspect side-effects and clear the buffers.

### 3. `dandy-gb/tests/dandy_env.py`
- **Purpose**: Implements the Python `DandyEnv` wrapper class to act as the bridge between the Python test runner and the C shared library.
- **Key Features**:
  - **Copy-on-Load State Isolation**: Copies `libdandy_test.so` to a unique temporary directory on creation and loads it. Upon deletion (`__del__`), it unloads the library using `_ctypes.dlclose()` and deletes the temporary files. This guarantees 100% isolation of static variables (e.g. `rand_seed`, `old_buttons`) between tests.
  - **Ctypes Globals & Functions Binding**: Binds all core C engine globals (`dandy_map`, `current_level`, `player_health`, etc.) and control functions (`dandy_init`, `dandy_step`, etc.).
  - **Exposed APIs**: Supports both specific property accessors (e.g. `get_player_health`, `set_player_health`) and unified dictionary state accessors (`get_player`) to ensure downstream compatibility.

### 4. `dandy-gb/tests/test_infra_check.py`
- **Purpose**: A comprehensive unit test suite to verify the test infrastructure itself.
- **Key Test Cases**:
  - `test_env_loading_and_globals`: Asserts that ctypes correctly binds and synchronizes global variables.
  - `test_state_isolation`: Proves that separate `DandyEnv` instances do not share static states and can be safely loaded/unloaded in parallel.
  - `test_mock_hal_logging_viewport`: Verifies that viewport draws correctly record tile outputs and camera positions in mock buffers.
  - `test_game_loop_step_and_sound`: Performs a full E2E step where a player moves and collects food, asserting coordinate changes, health increases, map tile modifications, and sound effect recording.

### 5. `TEST_INFRA.md` (Project Root)
- **Purpose**: Master documentation detailing the design, quick start, 10-feature inventory (Movement, Slide, Items, Doors, Combat, Smart Bomb, Monsters, Generators, Viewport, Levels), and quality/coverage gates (Tier 1-5 tests, >=95% statement and >=90% branch coverage).

## Modified Files

### 1. `dandy-gb/Makefile`
- **Purpose**: Integrated host-compilation and Python testing into the GameBoy build system.
- **Changes**:
  - Added `test_lib` target: Automatically creates the mock directory `tests/mock_gb/gb/` and generates `gb.h` containing a stub `SWITCH_ROM(bank)` macro to intercept GameBoy GBDK headers. Compiles the C shared library `libdandy_test.so` using `gcc` with `-fPIC -shared -O2 -Isrc -Itests/mock_gb`.
  - Added `test` target: Runs `python3 -m unittest discover` to execute all Python tests.
  - Updated `clean` target: Cleans up the generated `tests/mock_gb` directory and `libdandy_test.so`.
