# Project: Dandy Dungeon Custom 2D Level Compression

## Architecture
Dandy Dungeon is a 2D grid-based game designed to run on the Nintendo GameBoy. The project aims to fit the entire game, including 26 levels, into a flat, single-bank 32KB ROM (no-MBC) with a total active code/data segment footprint under 28KB.

The system is split into the following components:
1. **Level Compiler (`tools/convert_levels.py`)**: A Python script that parses `dandy-js/levels.js`, applies a custom 2D compression algorithm, and generates the C source/header files representing the level database.
2. **Core Engine (`src/dandy_core.c`, `src/dandy_core.h`)**: The platform-independent game logic that manages game state, player movement, collision, entity behavior, and level loading. It decompresses level data on-the-fly directly into the `dandy_map` RAM buffer.
3. **GameBoy HAL (`src/gameboy_hal.c`, `src/main.c`)**: GameBoy-specific implementation of the hardware drawing, input, HUD, and audio APIs using GBDK-2020.
4. **Automated Verification (`tools/verify_compression.py`)**: A Python verification script that performs round-trip decompression checks in Python, compiles the ROM, and asserts strict ROM and segment size constraints.
5. **Offline E2E Test Runner**: A test harness that links the core C engine (`dandy_core.c`) with a mock HAL, allowing programmatic simulation of player actions, level loading, and level transitions to verify game correctness.

```
+---------------------+
|  dandy-js/levels.js |
+----------+----------+
           | (Read)
           v
+--------------------------+
| tools/convert_levels.py  |  <-- Custom 2D Compressor (Python)
+----------+----------+
           | (Generates)
           v
+--------------------------+
| src/levels.c & levels.h  |  <-- Compressed Level Database (ROM)
+----------+----------+
           | (Compile)
           v
+--------------------------+
|    GBDK-2020 Compiler    |  <-- Flat 32KB ROM Build (no-MBC)
+----------+----------+
           | (Link)
           v
+--------------------------+      +-------------------------------+
|      bin/dandy.gb        | <--> |  tools/verify_compression.py  | (Validates size & fidelity)
+--------------------------+      +-------------------------------+
```

## Code Layout
- `dandy-gb/src/dandy_core.c`: Core engine logic, including `dandy_load_level` (decompressor).
- `dandy-gb/src/dandy_core.h`: Core engine declarations and definitions (e.g. `MAP_SIZE`, tile IDs).
- `dandy-gb/src/levels.h`: Level database declarations.
- `dandy-gb/src/levels.c`: Level database definition containing compressed level data.
- `dandy-gb/src/gameboy_hal.c`: GameBoy hardware abstraction layer.
- `dandy-gb/src/main.c`: Main entry point and game loop for the GameBoy ROM.
- `dandy-gb/tools/convert_levels.py`: Level converter and compressor.
- `dandy-gb/tools/verify_compression.py`: Automated build and size verification script.
- `dandy-gb/Makefile`: GameBoy ROM and WebAssembly compilation Makefile.

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M1 | Build Revert & Verification Foundation | Revert Makefile to flat 32KB (no-MBC, remove bank switching); remove `SWITCH_ROM(2)` in `dandy_core.c`; create `tools/verify_compression.py` skeleton to clean, compile, and assert ROM size. | None | DONE |
| M2 | Design 2D Compression & E2E Test Harness | Analyze 26 levels for 2D spatial coherence (meta-tiles, Fax MH/MR/MMR 2D run-length/delta tracking); evaluate 4-bit tile packing, edge wall elision, and variable-length coding; compile a comparative report evaluating decompressor size & CPU overhead; establish E2E offline test runner and write Tier 1 & 2 tests. | M1 | DONE |
| M3 | Implement 2D Compressor & Decompressor | Implement Python 2D compressor in `convert_levels.py` and GBDK C decompressor in `dandy_core.c` using the selected optimal scheme (incorporating 4-bit packing and edge wall elision); complete E2E Tiers 1-4 tests. | M2 | DONE |
| M4 | Integration & Size Optimization | Integrate pipeline; optimize decompressor speed and code size; tune compression to fit total active segments under 28KB; pass all E2E tests. | M3 | DONE |
| M5 | Adversarial Hardening & Final Audit | Run Tier 5 adversarial testing for coverage and edge cases; run forensic integrity auditor; final verification. | M4 | IN_PROGRESS |

## Interface Contracts
### 2D Level Database Interface
- **Compressed Levels Array**:
  `extern const uint8_t* const dandy_levels[DANDY_NUM_LEVELS];`
  Declared in `src/levels.h`, defined in `src/levels.c`. Points to the custom compressed byte stream of each level.
- **Level Load and Decompression**:
  `void dandy_load_level(uint8_t level_idx);`
  Declared in `src/dandy_core.h`, defined in `src/dandy_core.c`. Decodes `dandy_levels[level_idx]` directly into the global `uint8_t dandy_map[1800]` buffer.
- **Map Dimensions**:
  `DANDY_LEVEL_WIDTH = 60`
  `DANDY_LEVEL_HEIGHT = 30`
  `MAP_SIZE = 1800`

### Offline E2E Test Interface (Mock HAL)
To support offline E2E testing of the core engine, a mock HAL must implement:
- `void hal_draw_tile(uint8_t x, uint8_t y, uint8_t tile);`
- `void hal_update_hud(void);`
- `void hal_clear_sprites(uint8_t cam_x, uint8_t cam_y);`
- `void hal_set_sprite(uint8_t index, uint8_t x, uint8_t y, uint8_t tile, uint8_t flags);`
- `void hal_play_sound(uint8_t sound_id);`
These functions can be stubbed or record calls for assertions in E2E tests.
