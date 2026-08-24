# Analysis & Infrastructure Design: Offline E2E Test Harness

This document provides the complete, production-grade design for the Dandy Dungeon offline E2E test infrastructure (Milestone 1). It has been designed from a requirement-driven, opaque-box testing perspective to ensure high-fidelity verification of the game's mechanics without modifying the core engine source code.

---

## 1. Core Engine Analysis

### 1.1 Expose Strategy (Globals & API)
The core engine (`dandy_core.c`) is platform-independent but includes GameBoy-specific headers (`<gb/gb.h>`) and compiler macros (`SWITCH_ROM`) for ROM banking. 
To compile this code on a host machine (Linux x86_64) as a shared library (`libdandy_test.so`) without altering the core codebase, we introduce a **Mock GBDK Header** strategy:
- We create a mock header `tests/mock_gb/gb/gb.h` which stub out `SWITCH_ROM` as a no-op.
- We add `-Itests/mock_gb` to the compiler's include path.
This permits clean compilation on the host with zero changes to `src/dandy_core.c`.

### 1.2 State Isolation Strategy (Python ctypes)
The game engine maintains internal static variables that persist across ticks and tests:
- `static uint16_t rand_seed` (for LFSR random generation of spawns).
- `static uint8_t old_buttons[MAX_PLAYERS]` (for edge-triggering inputs like bombs).
- `static uint8_t flood_stack_*` and `flood_stack_ptr` (for non-recursive flood fill).

To guarantee **perfect test isolation** and prevent test ordering dependencies, the Python test environment (`dandy_env.py`) will employ a **Copy-on-Load** mechanism:
1. Every time a new `DandyEnv` instance is created, the Python runner creates a unique temporary copy of `libdandy_test.so` in a temp directory.
2. It loads that unique copy using `ctypes.CDLL`.
3. Upon destruction of the environment (e.g., at the end of a test case), the temporary library is unloaded and its file is deleted.
This ensures all static and global variables are completely reset to their default compiled states at the start of every single test case.

---

## 2. Mock HAL and Query Extensions

We implement a mock Hardware Abstraction Layer (`tests/mock_hal.c` and `tests/mock_hal.h`) that logs all drawing calls, sprite updates, sound effects, HUD updates, and camera movements in internal ring buffers. These logs can be programmatically queried by the Python test runner to assert correct side-effects.

### 2.1 Header: `tests/mock_hal.h`
```c
#ifndef MOCK_HAL_H
#define MOCK_HAL_H

#include <stdint.h>
#include <stdbool.h>

/* Mock Query Extensions for Test Assertions */
void mock_clear_buffers(void);

int mock_get_draw_count(void);
void mock_get_draw(int idx, uint8_t* x, uint8_t* y, uint8_t* tile_id);

int mock_get_sound_count(void);
uint8_t mock_get_sound(int idx);

void mock_get_sprite(uint8_t sprite_idx, uint8_t* x, uint8_t* y, uint8_t* tile_id, uint8_t* flags);
bool mock_is_sprite_active(uint8_t sprite_idx);

int mock_get_hud_update_count(void);
void mock_get_camera(uint8_t* cam_x, uint8_t* cam_y);

#endif /* MOCK_HAL_H */
```

### 2.2 Source: `tests/mock_hal.c`
```c
#include "mock_hal.h"
#include "../src/dandy_core.h"
#include <string.h>

#define MAX_MOCK_DRAWS 2048
#define MAX_MOCK_SOUNDS 256

typedef struct {
    uint8_t x;
    uint8_t y;
    uint8_t tile_id;
} DrawCall;

typedef struct {
    uint8_t x;
    uint8_t y;
    uint8_t tile_id;
    uint8_t flags;
    bool active;
} SpriteState;

static DrawCall mock_draws[MAX_MOCK_DRAWS];
static int mock_draw_count = 0;

static uint8_t mock_sounds[MAX_MOCK_SOUNDS];
static int mock_sound_count = 0;

static SpriteState mock_sprites[40];
static int mock_hud_update_count = 0;

static uint8_t mock_camera_x = 0;
static uint8_t mock_camera_y = 0;

/* --- Game Engine HAL Implementation --- */

void hal_draw_tile(uint8_t x, uint8_t y, uint8_t tile_id) {
    if (mock_draw_count < MAX_MOCK_DRAWS) {
        mock_draws[mock_draw_count].x = x;
        mock_draws[mock_draw_count].y = y;
        mock_draws[mock_draw_count].tile_id = tile_id;
        mock_draw_count++;
    }
}

void hal_update_hud(void) {
    mock_hud_update_count++;
}

void hal_clear_sprites(uint8_t vp_left, uint8_t vp_top) {
    mock_camera_x = vp_left;
    mock_camera_y = vp_top;
    for (int i = 0; i < 40; ++i) {
        mock_sprites[i].active = false;
    }
}

void hal_set_sprite(uint8_t sprite_idx, uint8_t x, uint8_t y, uint8_t tile_id, uint8_t flags) {
    if (sprite_idx < 40) {
        mock_sprites[sprite_idx].x = x;
        mock_sprites[sprite_idx].y = y;
        mock_sprites[sprite_idx].tile_id = tile_id;
        mock_sprites[sprite_idx].flags = flags;
        mock_sprites[sprite_idx].active = true;
    }
}

void hal_play_sound(uint8_t sound_id) {
    if (mock_sound_count < MAX_MOCK_SOUNDS) {
        mock_sounds[mock_sound_count] = sound_id;
        mock_sound_count++;
    }
}

/* --- Mock Query Extensions --- */

void mock_clear_buffers(void) {
    mock_draw_count = 0;
    mock_sound_count = 0;
    mock_hud_update_count = 0;
    mock_camera_x = 0;
    mock_camera_y = 0;
    for (int i = 0; i < 40; ++i) {
        mock_sprites[i].x = 0;
        mock_sprites[i].y = 0;
        mock_sprites[i].tile_id = 0;
        mock_sprites[i].flags = 0;
        mock_sprites[i].active = false;
    }
}

int mock_get_draw_count(void) {
    return mock_draw_count;
}

void mock_get_draw(int idx, uint8_t* x, uint8_t* y, uint8_t* tile_id) {
    if (idx >= 0 && idx < mock_draw_count) {
        if (x) *x = mock_draws[idx].x;
        if (y) *y = mock_draws[idx].y;
        if (tile_id) *tile_id = mock_draws[idx].tile_id;
    } else {
        if (x) *x = 0;
        if (y) *y = 0;
        if (tile_id) *tile_id = 0;
    }
}

int mock_get_sound_count(void) {
    return mock_sound_count;
}

uint8_t mock_get_sound(int idx) {
    if (idx >= 0 && idx < mock_sound_count) {
        return mock_sounds[idx];
    }
    return 0xFF;
}

void mock_get_sprite(uint8_t sprite_idx, uint8_t* x, uint8_t* y, uint8_t* tile_id, uint8_t* flags) {
    if (sprite_idx < 40) {
        if (x) *x = mock_sprites[sprite_idx].x;
        if (y) *y = mock_sprites[sprite_idx].y;
        if (tile_id) *tile_id = mock_sprites[sprite_idx].tile_id;
        if (flags) *flags = mock_sprites[sprite_idx].flags;
    } else {
        if (x) *x = 0;
        if (y) *y = 0;
        if (tile_id) *tile_id = 0;
        if (flags) *flags = 0;
    }
}

bool mock_is_sprite_active(uint8_t sprite_idx) {
    if (sprite_idx < 40) {
        return mock_sprites[sprite_idx].active;
    }
    return false;
}

int mock_get_hud_update_count(void) {
    return mock_hud_update_count;
}

void mock_get_camera(uint8_t* cam_x, uint8_t* cam_y) {
    if (cam_x) *cam_x = mock_camera_x;
    if (cam_y) *cam_y = mock_camera_y;
}
```

---

## 3. Python Ctypes Bridge (`tests/dandy_env.py`)

The python bridge is implemented as an environment class `DandyEnv` that completely manages library loading, unloading, property wrappers, and convenience methods.

```python
import ctypes
import os
import shutil
import tempfile

# Engine Constants
MAP_SIZE = 1800
MAX_PLAYERS = 4

# Tile ID Constants
TILE_SPACE = 0
TILE_WALL = 1
TILE_DOOR = 2
TILE_UP = 3
TILE_DOWN = 4
TILE_KEY = 5
TILE_FOOD = 6
TILE_MONEY = 7
TILE_BOMB = 8
TILE_MONSTER1 = 9
TILE_MONSTER2 = 10
TILE_MONSTER3 = 11
TILE_HEART = 12
TILE_GENERATOR1 = 13
TILE_GENERATOR2 = 14
TILE_GENERATOR3 = 15
TILE_ARROW = 16

# Button Masks
BUTTON_LEFT = 1 << 0
BUTTON_RIGHT = 1 << 1
BUTTON_UP = 1 << 2
BUTTON_DOWN = 1 << 3
BUTTON_FIRE = 1 << 4
BUTTON_BOMB = 1 << 5

# Retro Sound Effect IDs
SOUND_SHOOT = 0
SOUND_HIT = 1
SOUND_FOOD = 2
SOUND_BOMB = 3
SOUND_KEY = 4
SOUND_DIE = 5
SOUND_WARP = 6

class DandyEnv:
    """
    Python wrapper for Dandy Dungeon core engine.
    Utilizes unique copy-on-load to achieve 100% state isolation for tests.
    """
    def __init__(self, lib_path="./libdandy_test.so"):
        if not os.path.exists(lib_path):
            raise FileNotFoundError(f"Shared library not found at '{lib_path}'. Run 'make test_lib' first.")
        
        # Create unique temp library copy
        self._temp_dir = tempfile.mkdtemp(prefix="dandy_env_")
        self._temp_lib_path = os.path.join(self._temp_dir, "libdandy_test.so")
        shutil.copy(lib_path, self._temp_lib_path)
        
        # Load DLL
        self._lib = ctypes.CDLL(self._temp_lib_path)
        self._setup_bindings()
        
    def _setup_bindings(self):
        # Functions
        self._lib.dandy_init.argtypes = []
        self._lib.dandy_init.restype = None
        
        self._lib.dandy_step.argtypes = [ctypes.POINTER(ctypes.c_uint8)]
        self._lib.dandy_step.restype = None
        
        self._lib.dandy_load_level.argtypes = [ctypes.c_uint8]
        self._lib.dandy_load_level.restype = None
        
        self._lib.dandy_draw_viewport.argtypes = [ctypes.c_uint8]
        self._lib.dandy_draw_viewport.restype = None
        
        self._lib.dandy_join_player.argtypes = [ctypes.c_uint8]
        self._lib.dandy_join_player.restype = None
        
        self._lib.dandy_is_player_joined.argtypes = [ctypes.c_uint8]
        self._lib.dandy_is_player_joined.restype = ctypes.c_bool
        
        # Mock Extensions
        self._lib.mock_clear_buffers.argtypes = []
        self._lib.mock_clear_buffers.restype = None
        
        self._lib.mock_get_draw_count.argtypes = []
        self._lib.mock_get_draw_count.restype = ctypes.c_int
        
        self._lib.mock_get_draw.argtypes = [
            ctypes.c_int,
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.POINTER(ctypes.c_uint8)
        ]
        self._lib.mock_get_draw.restype = None
        
        self._lib.mock_get_sound_count.argtypes = []
        self._lib.mock_get_sound_count.restype = ctypes.c_int
        
        self._lib.mock_get_sound.argtypes = [ctypes.c_int]
        self._lib.mock_get_sound.restype = ctypes.c_uint8
        
        self._lib.mock_get_sprite.argtypes = [
            ctypes.c_uint8,
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.POINTER(ctypes.c_uint8)
        ]
        self._lib.mock_get_sprite.restype = None
        
        self._lib.mock_is_sprite_active.argtypes = [ctypes.c_uint8]
        self._lib.mock_is_sprite_active.restype = ctypes.c_bool
        
        self._lib.mock_get_hud_update_count.argtypes = []
        self._lib.mock_get_hud_update_count.restype = ctypes.c_int
        
        self._lib.mock_get_camera.argtypes = [
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.POINTER(ctypes.c_uint8)
        ]
        self._lib.mock_get_camera.restype = None
        
        # Globals
        self._dandy_map_ref = (ctypes.c_uint8 * MAP_SIZE).in_dll(self._lib, "dandy_map")
        self._current_level_ref = ctypes.c_uint8.in_dll(self._lib, "current_level")
        self._monster_rotor_ref = ctypes.c_uint8.in_dll(self._lib, "monster_rotor")
        self._player_joined_ref = (ctypes.c_bool * MAX_PLAYERS).in_dll(self._lib, "player_joined")
        self._local_player_idx_ref = ctypes.c_uint8.in_dll(self._lib, "local_player_idx")
        self._is_dirty_ref = ctypes.c_bool.in_dll(self._lib, "is_dirty")
        
        self._player_x_ref = (ctypes.c_uint8 * MAX_PLAYERS).in_dll(self._lib, "player_x")
        self._player_y_ref = (ctypes.c_uint8 * MAX_PLAYERS).in_dll(self._lib, "player_y")
        self._player_health_ref = (ctypes.c_int16 * MAX_PLAYERS).in_dll(self._lib, "player_health")
        self._player_score_ref = (ctypes.c_uint16 * MAX_PLAYERS).in_dll(self._lib, "player_score")
        self._player_bombs_ref = (ctypes.c_uint8 * MAX_PLAYERS).in_dll(self._lib, "player_bombs")
        self._player_keys_ref = (ctypes.c_uint8 * MAX_PLAYERS).in_dll(self._lib, "player_keys")
        self._player_dir_ref = (ctypes.c_int8 * MAX_PLAYERS).in_dll(self._lib, "player_dir")
        self._player_move_timer_ref = (ctypes.c_uint8 * MAX_PLAYERS).in_dll(self._lib, "player_move_timer")
        
        self._arrow_x_ref = (ctypes.c_uint8 * MAX_PLAYERS).in_dll(self._lib, "arrow_x")
        self._arrow_y_ref = (ctypes.c_uint8 * MAX_PLAYERS).in_dll(self._lib, "arrow_y")
        self._arrow_dir_ref = (ctypes.c_int8 * MAX_PLAYERS).in_dll(self._lib, "arrow_dir")

    def __del__(self):
        # Force garbage collection to release DLL handle, then remove temp files
        if hasattr(self, "_lib"):
            del self._lib
        if hasattr(self, "_temp_dir") and os.path.exists(self._temp_dir):
            shutil.rmtree(self._temp_dir)

    # Globals Properties
    @property
    def dandy_map(self):
        return list(self._dandy_map_ref)
    
    @dandy_map.setter
    def dandy_map(self, val):
        if len(val) != MAP_SIZE:
            raise ValueError(f"Map size must be exactly {MAP_SIZE} bytes")
        for i, b in enumerate(val):
            self._dandy_map_ref[i] = b
            
    @property
    def current_level(self):
        return self._current_level_ref.value
    
    @current_level.setter
    def current_level(self, val):
        self._current_level_ref.value = val
        
    @property
    def monster_rotor(self):
        return self._monster_rotor_ref.value
    
    @monster_rotor.setter
    def monster_rotor(self, val):
        self._monster_rotor_ref.value = val
        
    @property
    def local_player_idx(self):
        return self._local_player_idx_ref.value
    
    @local_player_idx.setter
    def local_player_idx(self, val):
        self._local_player_idx_ref.value = val
        
    @property
    def is_dirty(self):
        return self._is_dirty_ref.value
    
    @is_dirty.setter
    def is_dirty(self, val):
        self._is_dirty_ref.value = val

    # Helper for player state arrays
    def get_player(self, p_idx):
        if p_idx < 0 or p_idx >= MAX_PLAYERS:
            raise IndexError("Player index out of bounds")
        return {
            'joined': self._player_joined_ref[p_idx],
            'x': self._player_x_ref[p_idx],
            'y': self._player_y_ref[p_idx],
            'health': self._player_health_ref[p_idx],
            'score': self._player_score_ref[p_idx],
            'bombs': self._player_bombs_ref[p_idx],
            'keys': self._player_keys_ref[p_idx],
            'dir': self._player_dir_ref[p_idx],
            'move_timer': self._player_move_timer_ref[p_idx],
            'arrow': {
                'x': self._arrow_x_ref[p_idx],
                'y': self._arrow_y_ref[p_idx],
                'dir': self._arrow_dir_ref[p_idx]
            }
        }
        
    def set_player_joined(self, p_idx, joined):
        self._player_joined_ref[p_idx] = joined
        
    def set_player_position(self, p_idx, x, y):
        self._player_x_ref[p_idx] = x
        self._player_y_ref[p_idx] = y
        
    def set_player_health(self, p_idx, health):
        self._player_health_ref[p_idx] = health
        
    def set_player_keys(self, p_idx, keys):
        self._player_keys_ref[p_idx] = keys
        
    def set_player_bombs(self, p_idx, bombs):
        self._player_bombs_ref[p_idx] = bombs
        
    def set_player_score(self, p_idx, score):
        self._player_score_ref[p_idx] = score

    # Engine API wrappers
    def init(self):
        self._lib.dandy_init()
        
    def step(self, inputs):
        if len(inputs) != MAX_PLAYERS:
            raise ValueError(f"Inputs must contain exactly {MAX_PLAYERS} items")
        arr = (ctypes.c_uint8 * MAX_PLAYERS)(*inputs)
        self._lib.dandy_step(arr)
        
    def load_level(self, level_idx):
        self._lib.dandy_load_level(level_idx)
        
    def draw_viewport(self, local_p_idx):
        self._lib.dandy_draw_viewport(local_p_idx)
        
    def join_player(self, p_idx):
        self._lib.dandy_join_player(p_idx)
        
    def is_player_joined(self, p_idx):
        return self._lib.dandy_is_player_joined(p_idx)

    # Mock HAL query helpers
    def clear_mock_buffers(self):
        self._lib.mock_clear_buffers()
        
    def get_draw_count(self):
        return self._lib.mock_get_draw_count()
    
    def get_draws(self):
        draws = []
        count = self._lib.mock_get_draw_count()
        x = ctypes.c_uint8()
        y = ctypes.c_uint8()
        tile_id = ctypes.c_uint8()
        for i in range(count):
            self._lib.mock_get_draw(i, ctypes.byref(x), ctypes.byref(y), ctypes.byref(tile_id))
            draws.append({'x': x.value, 'y': y.value, 'tile_id': tile_id.value})
        return draws
    
    def get_sounds(self):
        sounds = []
        count = self._lib.mock_get_sound_count()
        for i in range(count):
            sounds.append(self._lib.mock_get_sound(i))
        return sounds
    
    def get_sprites(self):
        sprites = {}
        x = ctypes.c_uint8()
        y = ctypes.c_uint8()
        tile_id = ctypes.c_uint8()
        flags = ctypes.c_uint8()
        for i in range(40):
            if self._lib.mock_is_sprite_active(i):
                self._lib.mock_get_sprite(i, ctypes.byref(x), ctypes.byref(y), ctypes.byref(tile_id), ctypes.byref(flags))
                sprites[i] = {
                    'x': x.value,
                    'y': y.value,
                    'tile_id': tile_id.value,
                    'flags': flags.value
                }
        return sprites

    def get_camera(self):
        cam_x = ctypes.c_uint8()
        cam_y = ctypes.c_uint8()
        self._lib.mock_get_camera(ctypes.byref(cam_x), ctypes.byref(cam_y))
        return (cam_x.value, cam_y.value)
    
    def get_hud_update_count(self):
        return self._lib.mock_get_hud_update_count()
```

---

## 4. Makefile Additions

The compilation target `libdandy_test.so` is compiled with host `gcc`.
We add variables and targets to compile the shared library and run the Python tests automatically.

```makefile
# --- HOST COMPILATION AND TESTING FOR OFFLINE E2E HARNESS ---
HOST_CC = gcc
HOST_CFLAGS = -fPIC -shared -O2 -Wall -Wextra -Isrc -Itests/mock_gb
TEST_DIR = tests
TEST_OUT = libdandy_test.so
MOCK_GB_DIR = $(TEST_DIR)/mock_gb

.PHONY: test_lib test

# Build target for the shared library (depends on generated levels)
test_lib: levels
	@mkdir -p $(MOCK_GB_DIR)/gb
	@echo "#ifndef MOCK_GB_H" > $(MOCK_GB_DIR)/gb/gb.h
	@echo "#define MOCK_GB_H" >> $(MOCK_GB_DIR)/gb/gb.h
	@echo "#define SWITCH_ROM(bank) ((void)0)" >> $(MOCK_GB_DIR)/gb/gb.h
	@echo "#endif" >> $(MOCK_GB_DIR)/gb/gb.h
	$(HOST_CC) $(HOST_CFLAGS) \
		src/dandy_core.c \
		src/levels.c \
		$(TEST_DIR)/mock_hal.c \
		-o $(TEST_OUT)
	@echo "----------------------------------------"
	@echo "Test library compiled successfully: $(TEST_OUT)"
	@echo "----------------------------------------"

# Run all offline E2E tests via Python
test: test_lib
	python3 -m unittest discover -s $(TEST_DIR) -p "test_*.py"
```

Also, update the `clean` target in the Makefile to wipe the mock directory and the `.so` file:
```makefile
clean:
	rm -rf $(OBJ_DIR) $(BIN_DIR)
	rm -f $(WEB_DIR)/*.js $(WEB_DIR)/*.wasm
	rm -f *.lst *.map *.sym
	rm -rf $(MOCK_GB_DIR)
	rm -f $(TEST_OUT)
	@echo "Clean complete."
```

---

## 5. Draft Content for `TEST_INFRA.md`

This draft is to be placed at the project root `TEST_INFRA.md`.

```markdown
# Dandy Dungeon Offline E2E Test Infrastructure

This document describes the design, architecture, and usage of the Dandy Dungeon offline E2E test harness. The test harness compiles the core platform-independent game engine alongside a mock Hardware Abstraction Layer (HAL) to enable rapid, deterministic, and headless testing of game mechanics and rules.

## 1. Architecture Overview

The offline testing pipeline runs entirely on the host machine (e.g. Linux x86_64). It bypasses the GameBoy GBDK compiler and emulators, enabling test suites to run in milliseconds.

```
[tests/test_suite.py (Python Unittest)]
       |
       v (Programmatic Control & Assertions)
[tests/dandy_env.py (ctypes wrapper)]
       |
       v (Loads unique copy)
[libdandy_test.so (C Shared Library)]
  ├── src/dandy_core.c (Platform-independent Game Logic)
  ├── src/levels.c (Decompressed Level Database)
  └── tests/mock_hal.c (Mock Graphics/Audio/Sprites logging calls)
```

### Key Highlights:
1. **Mock GBDK Headers**: A mock `<gb/gb.h>` header is dynamically generated at compile-time to stub out GameBoy-specific compiler features (like ROM bank switching) as no-ops.
2. **Strict State Isolation**: The Python wrapper (`dandy_env.py`) creates a unique temporary copy of `libdandy_test.so` on disk for every test case. This ensures that internal static variables (like the random seed and button history) are reset to their compile-time default values before each test runs.
3. **Double Assertion Coverage**: Tests assert both on the engine's internal global variables (e.g., coordinates, health, inventory) and the mock HAL's logged side-effects (e.g., specific tile drawing calls, registered hardware sprites, played audio tracks).

---

## 2. Quick Start

### 2.1 Compile the Test Library
To compile `libdandy_test.so` from the project root:
```bash
make test_lib
```

### 2.2 Run the Test Suite
To run all tests in the `tests/` directory:
```bash
make test
```
This runs the Python `unittest` framework to discover and execute all `test_*.py` suites.

---

## 3. Core Feature Inventory & Rules

The game engine is evaluated against 10 core features, divided into distinct behaviors for precise testing.

| Feature ID | Feature Name | Description | Key Game Rules to Verify |
|---|---|---|---|
| **F-01** | Movement & Timing | 8-way player movement and grid alignment. | - Moving into `TILE_SPACE` updates coordinates.<br>- `player_move_timer` acts as a 4-tick cooldown; holding inputs moves the player exactly once every 4 ticks.<br>- Unjoined or dead players do not process inputs. |
| **F-02** | Slide Mechanics | Sliding around solid obstacles. | - If a diagonal/cardinal move is blocked, the engine automatically checks direction $\pm 1$ and moves there if free.<br>- If all three are blocked, the player remains stationary. |
| **F-03** | Item Collection | Consuming items scattered on the map. | - Walking onto `TILE_FOOD` increases health by 100, plays `SOUND_FOOD`. Health can exceed 100.<br>- Walking onto `TILE_MONEY` increases score by 100, plays `SOUND_KEY`.<br>- Walking onto `TILE_KEY` increments keys by 1, plays `SOUND_KEY`.<br>- Walking onto `TILE_BOMB` increments bombs by 1, plays `SOUND_KEY`. |
| **F-04** | Door & Key Mechanics | Locked doors requiring keys to unlock. | - Moving onto `TILE_DOOR` with 0 keys is blocked.<br>- Moving onto `TILE_DOOR` with $\ge 1$ keys decrements keys by 1, plays `SOUND_KEY`, and triggers an 8-way flood fill that turns all connected door tiles into `TILE_SPACE`. |
| **F-05** | Combat & Projectiles | Firing arrows to defeat enemies. | - Pressing `BUTTON_FIRE` when `arrow_dir == -1` fires an arrow in the player's direction and plays `SOUND_SHOOT`. Space is checked in the same tick.<br>- An arrow travels 1 tile per tick in its direction.<br>- Arrows only exist inside the player's viewport (10x20 area); leaving the viewport destroys the arrow.<br>- Hitting solid obstacles destroys the arrow.<br>- Hitting destructible targets destroys the arrow, plays `SOUND_HIT`, and applies effects:<br>  * `TILE_BOMB`: Triggers a smart bomb.<br>  * `TILE_HEART`: Degrades into `TILE_MONSTER3`.<br>  * `TILE_MONSTER3`/`TILE_MONSTER2`: Degrades by 1 level (`tile - 1`).<br>  * `TILE_MONSTER1` or any Generator: Replaced by `TILE_SPACE`. |
| **F-06** | Smart Bomb Action | Visual viewport-wide explosion. | - Pressing `BUTTON_BOMB` with $\ge 1$ bombs decrements bombs by 1, plays `SOUND_BOMB`, and clears all monsters and generators within the player's 10x20 viewport.<br>- Monsters and generators outside the viewport are unaffected. |
| **F-07** | Monster Behavior | AI movement and attacks. | - Monsters are updated on a 16-tick sparse grid (monster rotor) and are frozen if they are not visible in any active player's viewport.<br>- Visible monsters track the nearest active player (Manhattan distance) and move towards them.<br>- Colliding with a player deals $10 \times (\text{monster\_level})$ damage, plays `SOUND_HIT` (or `SOUND_DIE` if player dies), and removes the monster.<br>- Player death clears their tile from the map immediately. |
| **F-08** | Generator Spawning | Enemy factories spawning monsters. | - Generators update on the 16-tick sparse grid and freeze if off-screen.<br>- Every active tick, they use a deterministic LFSR random seed; if `(seed & 7) < 4`, they try to spawn a monster.<br>- They attempt to spawn in adjacent cardinal directions starting at `(seed & 3) * 2` clockwise, spawning a monster matching the generator's level in the first empty space. |
| **F-09** | Multiplayer & Viewport | Cooperative multiplayer support. | - Multiple players can join via `dandy_join_player()`. They spawn around the portal.<br>- Viewport centers on the local player, clamped to map boundaries ($60 \times 30$).<br>- Spectator Mode: If the local player is dead, the camera centers on the centroid of the remaining alive players. |
| **F-10** | Level Transitions | Advancing through the levels. | - Moving onto `TILE_DOWN` (stairs) triggers `next_level()`, which loads the next level, plays `SOUND_WARP`, and resets player coordinates to the new level's starting portal (`TILE_UP`). |

---

## 4. Test Tiers & Coverage Thresholds

To achieve robust verification, the test suite must implement tests across five hierarchical tiers, maintaining strict minimum count and coverage thresholds.

### 4.1 Tier 1: Happy-Path Feature Coverage (Target: $\ge 40$ Tests)
- **Scope**: Verifies basic, isolated functionality of each of the 10 core features in a clean map setting.
- **Examples**: Single step movement, collecting one of each item, unlocking a single door, shooting an arrow into an empty space.

### 4.2 Tier 2: Boundary & Corner Cases (Target: $\ge 40$ Tests)
- **Scope**: Evaluates edge values, out-of-bounds inputs, and maximum capacity limits.
- **Examples**: Walking into map boundaries, hitting walls, shooting arrows off-viewport, multi-level health clamping, flood-filling massive or circular door networks.

### 4.3 Tier 3: Cross-Feature Interactions (Target: $\ge 8$ Tests)
- **Scope**: Tests scenarios where multiple systems interact simultaneously.
- **Examples**: An arrow hitting a bomb tile to trigger a viewport explosion; a monster attacking a player on the exact frame the player collects food; shooting an arrow at a monster that is moving toward the player.

### 4.4 Tier 4: Real-World Scenarios (Target: $\ge 5$ Tests)
- **Scope**: Multi-step playthroughs simulating actual game runs.
- **Examples**: Loading Level 0, navigating a maze of walls, collecting keys, unlocking doors, shooting a spawning monster, and reaching the stairs to advance to Level 1.

### 4.5 Tier 5: Adversarial & Stress Testing (Target: $\ge 5$ Tests)
- **Scope**: Extravagant inputs, concurrent multi-player inputs, and extreme state situations.
- **Examples**: All 4 players joining and pressing directions simultaneously; inputs injected for dead players; spectator mode camera centering with multiple alive/dead player configurations.

## 5. Quality & Assertion Standards

- **Double-Assert Rule**: Every test case must verify state changes in BOTH the engine's globals (e.g., `player_x`, `player_health`) and the mock HAL logs (e.g., `mock_get_sound_count()`, `mock_get_draws()`).
- **Deterministic Spawning**: Tests for F-08 (Generator Spawning) must leverage the fresh-load environment to guarantee identical LFSR state, asserting the exact ticks and directions that monsters are spawned.
```

---

## 6. Infrastructure Verification Plan

To verify that the offline test infrastructure is correct and fully functional, the following verification plan is designed. These verification steps should be executed by the implementer upon putting the code in place:

1. **Host Compilation Check**:
   - Run `make test_lib`.
   - Verify that `libdandy_test.so` is built without any errors or warnings.
   - Verify that the folder `tests/mock_gb/gb/` was correctly created and contains `gb.h` with the mock macro `SWITCH_ROM(bank)`.
2. **Symbol Export Check**:
   - Run `nm -D libdandy_test.so | grep dandy_` and `nm -D libdandy_test.so | grep mock_`.
   - Verify that all core engine functions (e.g., `dandy_init`, `dandy_step`, `dandy_load_level`) and mock query functions (e.g., `mock_get_draw_count`, `mock_clear_buffers`) are exported as public symbols.
3. **Perfect Isolation Test**:
   - Write a simple test that loads a `DandyEnv`, sets `current_level = 10` and `monster_rotor = 5`, and then deletes the environment.
   - Load a second `DandyEnv` and verify that `current_level` is back to `0` and `monster_rotor` is `0`.
   - This verifies that the "Copy-on-Load" state isolation is functioning perfectly.
4. **Mock HAL Logging Check**:
   - Load an environment, initialize it, and call `env.draw_viewport(0)`.
   - Query `env.get_draw_count()` and verify that it is exactly 200 (since a viewport draw is a 20x10 tile sweep).
   - This verifies that `hal_draw_tile` and the drawing log are functioning correctly.
5. **Fresh Execution Run**:
   - Run `make test`.
   - Verify that the Python test runner discovers the test suite, runs successfully, and reports 0 failures.
