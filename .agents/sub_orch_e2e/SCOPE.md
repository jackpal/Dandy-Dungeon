# Scope: E2E Testing Track

## Architecture
The E2E Testing Track runs completely offline. It compiles the core platform-independent game engine (`src/dandy_core.c`, `src/levels.c`) with a custom mock Hardware Abstraction Layer (`tests/mock_hal.c`) into a shared library (`libdandy_test.so`).
A Python test harness (`tests/dandy_env.py`) loads this library via `ctypes`, allowing test cases (`tests/test_suite.py`) to programmatically set map states, inject player inputs, step the game loop, and assert on engine variables and HAL side effects (sounds, drawings).

```
[tests/test_suite.py (Python)]
       |
       v (Calls)
[tests/dandy_env.py (ctypes)]
       |
       v (Loads)
[libdandy_test.so (C Shared Lib)]
  ├── src/dandy_core.c (Engine Logic)
  ├── src/levels.c (Compressed Levels)
  └── tests/mock_hal.c (Mock Graphics/Audio/Sprites)
```

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|---|---|---|---|
| M1 | Test Infrastructure & Runner | Create `tests/mock_hal.c`, `tests/dandy_env.py`, add `libdandy_test.so` target to `Makefile`, write `TEST_INFRA.md`. | None | DONE |
| M2 | Tier 1 Feature Coverage | Implement >= 40 tests covering happy-path scenarios of all 8 core features. | M1 | DONE |
| M3 | Tier 2 & 3 Boundary & Interactions | Implement >= 40 boundary/corner tests (Tier 2) and >= 8 cross-feature tests (Tier 3). | M2 | DONE (112 tests passing, engine hardened) |
| M4 | Tier 4 Real-World Scenarios | Implement >= 5 real-world play scenarios and level playthroughs. | M3 | PLANNED |
| M5 | Final Verification & Publish | Run Forensic Auditor, resolve any issues, write and publish `TEST_READY.md`. | M4 | PLANNED |

## Interface Contracts
### Mock HAL Interface (`tests/mock_hal.c`)
- `void hal_draw_tile(uint8_t x, uint8_t y, uint8_t tile_id);`
- `void hal_update_hud(void);`
- `void hal_clear_sprites(uint8_t vp_left, uint8_t vp_top);`
- `void hal_set_sprite(uint8_t sprite_idx, uint8_t x, uint8_t y, uint8_t tile_id, uint8_t flags);`
- `void hal_play_sound(uint8_t sound_id);`
- **Mock Query Extensions** (for Python assertions):
  - `void mock_clear_buffers(void);`
  - `int mock_get_draw_count(void);`
  - `void mock_get_draw(int idx, uint8_t* x, uint8_t* y, uint8_t* tile_id);`
  - `int mock_get_sound_count(void);`
  - `uint8_t mock_get_sound(int idx);`
  - `void mock_get_sprite(uint8_t sprite_idx, uint8_t* x, uint8_t* y, uint8_t* tile_id, uint8_t* flags);`

### Python Ctypes Bridge (`tests/dandy_env.py`)
- Exposes all core C globals: `dandy_map` (1800 bytes), `player_x`, `player_y`, `player_health`, `player_score`, `player_bombs`, `player_keys`, `player_dir`, `player_move_timer`, `arrow_x`, `arrow_y`, `arrow_dir`.
- Exposes functions: `dandy_init()`, `dandy_step()`, `dandy_load_level()`, `dandy_join_player()`.
- Provides Python wrappers for resetting and querying the mock HAL buffers.
