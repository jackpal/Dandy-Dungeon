# Dandy Dungeon Core Engine Analysis & E2E Test Infrastructure Design

This document details the analysis of the Dandy Dungeon core engine and the design of the offline E2E test infrastructure, fulfilling the requirements for Milestone 1.

---

## 1. Core Engine Analysis & Dependencies

### External HAL Functions
The core engine (`dandy_core.c`) is designed to be platform-independent but relies on a Hardware Abstraction Layer (HAL) to perform drawing, play sounds, manage hardware sprites, and update the HUD. The following external functions are declared in `dandy_core.h` and must be implemented by the test runner's mock HAL:

```c
extern void hal_draw_tile(uint8_t x, uint8_t y, uint8_t tile_id);
extern void hal_update_hud(void);
extern void hal_clear_sprites(uint8_t vp_left, uint8_t vp_top);
extern void hal_set_sprite(uint8_t sprite_idx, uint8_t x, uint8_t y, uint8_t tile_id, uint8_t flags);
extern void hal_play_sound(uint8_t sound_id);
```

### Engine Globals & State Variables
To allow programmatic assertion and manipulation of the game state, the following C global variables declared in `dandy_core.h` must be exposed to Python via the `ctypes` bridge:

| Variable Name | Type | Size / Dimensions | Description |
|---|---|---|---|
| `dandy_map` | `uint8_t` | `MAP_SIZE` (1800) | The active 60x30 tile grid of the current level. |
| `current_level` | `uint8_t` | Scalar | Index of the currently loaded level (0 to 25). |
| `monster_rotor` | `uint8_t` | Scalar | Sparse-grid scan index used to schedule monster ticks. |
| `player_joined` | `bool` | `MAX_PLAYERS` (4) | Active status of each player slot. |
| `local_player_idx` | `uint8_t` | Scalar | Index of the local player (typically 0). |
| `player_x` | `uint8_t` | `MAX_PLAYERS` (4) | X-coordinate of each player on the map. |
| `player_y` | `uint8_t` | `MAX_PLAYERS` (4) | Y-coordinate of each player on the map. |
| `player_health` | `int16_t` | `MAX_PLAYERS` (4) | Health points of each player. |
| `player_score` | `uint16_t` | `MAX_PLAYERS` (4) | Score of each player. |
| `player_bombs` | `uint8_t` | `MAX_PLAYERS` (4) | Number of smart bombs held by each player. |
| `player_keys` | `uint8_t` | `MAX_PLAYERS` (4) | Number of keys held by each player. |
| `player_dir` | `int8_t` | `MAX_PLAYERS` (4) | Facing direction (0..7) of each player. |
| `player_move_timer` | `uint8_t` | `MAX_PLAYERS` (4) | Move cooldown timer of each player. |
| `arrow_x` | `uint8_t` | `MAX_PLAYERS` (4) | X-coordinate of each player's active arrow. |
| `arrow_y` | `uint8_t` | `MAX_PLAYERS` (4) | Y-coordinate of each player's active arrow. |
| `arrow_dir` | `int8_t` | `MAX_PLAYERS` (4) | Direction of each player's active arrow (-1 if inactive). |
| `is_dirty` | `bool` | Scalar | Flag indicating that the screen needs to be redrawn. |

---

## 2. Mock HAL Design (`tests/mock_hal.h` & `tests/mock_hal.c`)

The mock HAL implements the external GameBoy HAL functions and records all their side effects into queryable buffers. It also includes mock control and query extensions designed for the Python test runner to inspect side effects and clear mock buffers.

### `tests/mock_hal.h`
```c
#ifndef MOCK_HAL_H
#define MOCK_HAL_H

#include "dandy_core.h"

/* Max buffer sizes for recorded events */
#define MAX_MOCK_DRAWS 2048
#define MAX_MOCK_SOUNDS 128
#define MAX_SPRITES 40

/* Struct representing a recorded tile draw event */
typedef struct {
    uint8_t x;
    uint8_t y;
    uint8_t tile_id;
} DrawEvent;

/* Struct representing a hardware sprite's state */
typedef struct {
    uint8_t x;
    uint8_t y;
    uint8_t tile_id;
    uint8_t flags;
    bool active;
} SpriteState;

/* Mock Control & Query Extensions (Exposed to Python Test Runner) */
void mock_clear_buffers(void);
int mock_get_draw_count(void);
void mock_get_draw(int idx, uint8_t* x, uint8_t* y, uint8_t* tile_id);
int mock_get_sound_count(void);
uint8_t mock_get_sound(int idx);
void mock_get_sprite(uint8_t sprite_idx, uint8_t* x, uint8_t* y, uint8_t* tile_id, uint8_t* flags);
bool mock_is_sprite_active(uint8_t sprite_idx);
void mock_get_viewport_camera(uint8_t* vp_left, uint8_t* vp_top);
int mock_get_hud_update_count(void);

#endif // MOCK_HAL_H
```

### `tests/mock_hal.c`
```c
#include "mock_hal.h"
#include <string.h>

/* Mock Storage Buffers */
static DrawEvent mock_draws[MAX_MOCK_DRAWS];
static int mock_draw_count = 0;

static uint8_t mock_sounds[MAX_MOCK_SOUNDS];
static int mock_sound_count = 0;

static SpriteState mock_sprites[MAX_SPRITES];
static uint8_t mock_vp_left = 0;
static uint8_t mock_vp_top = 0;

static int mock_hud_update_count = 0;

/* --- Standard HAL Implementation --- */

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
    mock_vp_left = vp_left;
    mock_vp_top = vp_top;
    for (int i = 0; i < MAX_SPRITES; ++i) {
        mock_sprites[i].active = false;
    }
}

void hal_set_sprite(uint8_t sprite_idx, uint8_t x, uint8_t y, uint8_t tile_id, uint8_t flags) {
    if (sprite_idx < MAX_SPRITES) {
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

/* --- Mock Control & Query Extensions --- */

void mock_clear_buffers(void) {
    mock_draw_count = 0;
    mock_sound_count = 0;
    mock_hud_update_count = 0;
    mock_vp_left = 0;
    mock_vp_top = 0;
    for (int i = 0; i < MAX_SPRITES; ++i) {
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
        *x = mock_draws[idx].x;
        *y = mock_draws[idx].y;
        *tile_id = mock_draws[idx].tile_id;
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
    if (sprite_idx < MAX_SPRITES) {
        *x = mock_sprites[sprite_idx].x;
        *y = mock_sprites[sprite_idx].y;
        *tile_id = mock_sprites[sprite_idx].tile_id;
        *flags = mock_sprites[sprite_idx].flags;
    }
}

bool mock_is_sprite_active(uint8_t sprite_idx) {
    if (sprite_idx < MAX_SPRITES) {
        return mock_sprites[sprite_idx].active;
    }
    return false;
}

void mock_get_viewport_camera(uint8_t* vp_left, uint8_t* vp_top) {
    *vp_left = mock_vp_left;
    *vp_top = mock_vp_top;
}

int mock_get_hud_update_count(void) {
    return mock_hud_update_count;
}
```

---

## 3. Python Ctypes Bridge & Environment Wrapper (`tests/dandy_env.py`)

This file implements the `DandyEnv` class. It loads the compiled C shared library (`libdandy_test.so`) via `ctypes`, defines the variable bindings and function signatures, and provides an idiomatic, clean Python API.

```python
import ctypes
import os

class DandyEnv:
    MAP_SIZE = 1800
    MAX_PLAYERS = 4
    
    # Button constants matching dandy_core.h
    BUTTON_LEFT = 1 << 0
    BUTTON_RIGHT = 1 << 1
    BUTTON_UP = 1 << 2
    BUTTON_DOWN = 1 << 3
    BUTTON_FIRE = 1 << 4
    BUTTON_BOMB = 1 << 5
    
    # Tile constants matching dandy_core.h
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
    TILE_PLAYER1 = 24

    # Retro Sound Effect IDs
    SOUND_SHOOT = 0
    SOUND_HIT = 1
    SOUND_FOOD = 2
    SOUND_BOMB = 3
    SOUND_KEY = 4
    SOUND_DIE = 5
    SOUND_WARP = 6

    def __init__(self, lib_path=None):
        if lib_path is None:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            lib_path = os.path.join(script_dir, "libdandy_test.so")
            
        if not os.path.exists(lib_path):
            # Fallback to current directory or parent directories if needed
            lib_path_fallback = os.path.abspath(os.path.join(os.getcwd(), "libdandy_test.so"))
            if os.path.exists(lib_path_fallback):
                lib_path = lib_path_fallback
            else:
                raise FileNotFoundError(f"Shared library not found at {lib_path}. Please build it first.")
        
        self.lib = ctypes.CDLL(lib_path)
        self._setup_bindings()
        
    def _setup_bindings(self):
        # --- Core Function Signatures ---
        self.lib.dandy_init.argtypes = []
        self.lib.dandy_init.restype = None

        self.lib.dandy_step.argtypes = [ctypes.POINTER(ctypes.c_uint8)]
        self.lib.dandy_step.restype = None

        self.lib.dandy_load_level.argtypes = [ctypes.c_uint8]
        self.lib.dandy_load_level.restype = None

        self.lib.dandy_draw_viewport.argtypes = [ctypes.c_uint8]
        self.lib.dandy_draw_viewport.restype = None

        self.lib.dandy_join_player.argtypes = [ctypes.c_uint8]
        self.lib.dandy_join_player.restype = None

        self.lib.dandy_is_player_joined.argtypes = [ctypes.c_uint8]
        self.lib.dandy_is_player_joined.restype = ctypes.c_bool
        
        # --- Mock Extension Signatures ---
        self.lib.mock_clear_buffers.argtypes = []
        self.lib.mock_clear_buffers.restype = None

        self.lib.mock_get_draw_count.argtypes = []
        self.lib.mock_get_draw_count.restype = ctypes.c_int

        self.lib.mock_get_draw.argtypes = [ctypes.c_int, ctypes.POINTER(ctypes.c_uint8), ctypes.POINTER(ctypes.c_uint8), ctypes.POINTER(ctypes.c_uint8)]
        self.lib.mock_get_draw.restype = None

        self.lib.mock_get_sound_count.argtypes = []
        self.lib.mock_get_sound_count.restype = ctypes.c_int

        self.lib.mock_get_sound.argtypes = [ctypes.c_int]
        self.lib.mock_get_sound.restype = ctypes.c_uint8

        self.lib.mock_get_sprite.argtypes = [ctypes.c_uint8, ctypes.POINTER(ctypes.c_uint8), ctypes.POINTER(ctypes.c_uint8), ctypes.POINTER(ctypes.c_uint8), ctypes.POINTER(ctypes.c_uint8)]
        self.lib.mock_get_sprite.restype = None

        self.lib.mock_is_sprite_active.argtypes = [ctypes.c_uint8]
        self.lib.mock_is_sprite_active.restype = ctypes.c_bool

        self.lib.mock_get_viewport_camera.argtypes = [ctypes.POINTER(ctypes.c_uint8), ctypes.POINTER(ctypes.c_uint8)]
        self.lib.mock_get_viewport_camera.restype = None

        self.lib.mock_get_hud_update_count.argtypes = []
        self.lib.mock_get_hud_update_count.restype = ctypes.c_int

        # --- Bind Live C Globals ---
        self._map = (ctypes.c_uint8 * self.MAP_SIZE).in_dll(self.lib, "dandy_map")
        self._current_level = ctypes.c_uint8.in_dll(self.lib, "current_level")
        self._monster_rotor = ctypes.c_uint8.in_dll(self.lib, "monster_rotor")
        self._player_joined = (ctypes.c_bool * self.MAX_PLAYERS).in_dll(self.lib, "player_joined")
        self._local_player_idx = ctypes.c_uint8.in_dll(self.lib, "local_player_idx")
        
        self._player_x = (ctypes.c_uint8 * self.MAX_PLAYERS).in_dll(self.lib, "player_x")
        self._player_y = (ctypes.c_uint8 * self.MAX_PLAYERS).in_dll(self.lib, "player_y")
        self._player_health = (ctypes.c_int16 * self.MAX_PLAYERS).in_dll(self.lib, "player_health")
        self._player_score = (ctypes.c_uint16 * self.MAX_PLAYERS).in_dll(self.lib, "player_score")
        self._player_bombs = (ctypes.c_uint8 * self.MAX_PLAYERS).in_dll(self.lib, "player_bombs")
        self._player_keys = (ctypes.c_uint8 * self.MAX_PLAYERS).in_dll(self.lib, "player_keys")
        self._player_dir = (ctypes.c_int8 * self.MAX_PLAYERS).in_dll(self.lib, "player_dir")
        self._player_move_timer = (ctypes.c_uint8 * self.MAX_PLAYERS).in_dll(self.lib, "player_move_timer")
        
        self._arrow_x = (ctypes.c_uint8 * self.MAX_PLAYERS).in_dll(self.lib, "arrow_x")
        self._arrow_y = (ctypes.c_uint8 * self.MAX_PLAYERS).in_dll(self.lib, "arrow_y")
        self._arrow_dir = (ctypes.c_int8 * self.MAX_PLAYERS).in_dll(self.lib, "arrow_dir")
        self._is_dirty = ctypes.c_bool.in_dll(self.lib, "is_dirty")

    # --- Live Global Property Accessors ---
    @property
    def map(self):
        return list(self._map)
    
    @map.setter
    def map(self, new_map):
        if len(new_map) != self.MAP_SIZE:
            raise ValueError(f"Map size must be exactly {self.MAP_SIZE}")
        for i in range(self.MAP_SIZE):
            self._map[i] = new_map[i]

    @property
    def current_level(self):
        return self._current_level.value

    @current_level.setter
    def current_level(self, val):
        self._current_level.value = val

    @property
    def monster_rotor(self):
        return self._monster_rotor.value

    @monster_rotor.setter
    def monster_rotor(self, val):
        self._monster_rotor.value = val

    @property
    def local_player_idx(self):
        return self._local_player_idx.value

    @local_player_idx.setter
    def local_player_idx(self, val):
        self._local_player_idx.value = val

    @property
    def is_dirty(self):
        return self._is_dirty.value

    @is_dirty.setter
    def is_dirty(self, val):
        self._is_dirty.value = val

    # --- Player State Array Accessors ---
    def get_player_x(self, p_idx):
        return self._player_x[p_idx]
    def set_player_x(self, p_idx, val):
        self._player_x[p_idx] = val

    def get_player_y(self, p_idx):
        return self._player_y[p_idx]
    def set_player_y(self, p_idx, val):
        self._player_y[p_idx] = val

    def get_player_health(self, p_idx):
        return self._player_health[p_idx]
    def set_player_health(self, p_idx, val):
        self._player_health[p_idx] = val

    def get_player_score(self, p_idx):
        return self._player_score[p_idx]
    def set_player_score(self, p_idx, val):
        self._player_score[p_idx] = val

    def get_player_bombs(self, p_idx):
        return self._player_bombs[p_idx]
    def set_player_bombs(self, p_idx, val):
        self._player_bombs[p_idx] = val

    def get_player_keys(self, p_idx):
        return self._player_keys[p_idx]
    def set_player_keys(self, p_idx, val):
        self._player_keys[p_idx] = val

    def get_player_dir(self, p_idx):
        return self._player_dir[p_idx]
    def set_player_dir(self, p_idx, val):
        self._player_dir[p_idx] = val

    def get_player_move_timer(self, p_idx):
        return self._player_move_timer[p_idx]
    def set_player_move_timer(self, p_idx, val):
        self._player_move_timer[p_idx] = val

    def is_player_joined(self, p_idx):
        return self._player_joined[p_idx]
    def set_player_joined(self, p_idx, val):
        self._player_joined[p_idx] = val

    # --- Arrow State Accessors ---
    def get_arrow_x(self, p_idx):
        return self._arrow_x[p_idx]
    def set_arrow_x(self, p_idx, val):
        self._arrow_x[p_idx] = val

    def get_arrow_y(self, p_idx):
        return self._arrow_y[p_idx]
    def set_arrow_y(self, p_idx, val):
        self._arrow_y[p_idx] = val

    def get_arrow_dir(self, p_idx):
        return self._arrow_dir[p_idx]
    def set_arrow_dir(self, p_idx, val):
        self._arrow_dir[p_idx] = val

    # --- Core Engine API Wrappers ---
    def init(self):
        self.lib.dandy_init()

    def step(self, inputs):
        """
        inputs: List or tuple of 4 integers representing button bitmasks for each player.
        """
        if len(inputs) != self.MAX_PLAYERS:
            raise ValueError(f"Inputs must be a list/tuple of size {self.MAX_PLAYERS}")
        arr = (ctypes.c_uint8 * self.MAX_PLAYERS)(*inputs)
        self.lib.dandy_step(arr)

    def load_level(self, level_idx):
        self.lib.dandy_load_level(level_idx)

    def draw_viewport(self, local_p_idx):
        self.lib.dandy_draw_viewport(local_p_idx)

    def join_player(self, p_idx):
        self.lib.dandy_join_player(p_idx)

    # --- Mock Query API Wrappers ---
    def mock_clear(self):
        self.lib.mock_clear_buffers()

    def mock_get_draw_count(self):
        return self.lib.mock_get_draw_count()

    def mock_get_draws(self):
        count = self.mock_get_draw_count()
        draws = []
        for i in range(count):
            x = ctypes.c_uint8()
            y = ctypes.c_uint8()
            tile_id = ctypes.c_uint8()
            self.lib.mock_get_draw(i, ctypes.byref(x), ctypes.byref(y), ctypes.byref(tile_id))
            draws.append((x.value, y.value, tile_id.value))
        return draws

    def mock_get_sound_count(self):
        return self.lib.mock_get_sound_count()

    def mock_get_sounds(self):
        count = self.mock_get_sound_count()
        return [self.lib.mock_get_sound(i) for i in range(count)]

    def mock_get_sprite(self, sprite_idx):
        x = ctypes.c_uint8()
        y = ctypes.c_uint8()
        tile_id = ctypes.c_uint8()
        flags = ctypes.c_uint8()
        self.lib.mock_get_sprite(sprite_idx, ctypes.byref(x), ctypes.byref(y), ctypes.byref(tile_id), ctypes.byref(flags))
        active = self.lib.mock_is_sprite_active(sprite_idx)
        return {
            "x": x.value,
            "y": y.value,
            "tile_id": tile_id.value,
            "flags": flags.value,
            "active": active
        }

    def mock_get_sprites(self):
        return [self.mock_get_sprite(i) for i in range(40)]

    def mock_get_viewport_camera(self):
        vp_left = ctypes.c_uint8()
        vp_top = ctypes.c_uint8()
        self.lib.mock_get_viewport_camera(ctypes.byref(vp_left), ctypes.byref(vp_top))
        return vp_left.value, vp_top.value

    def mock_get_hud_update_count(self):
        return self.lib.mock_get_hud_update_count()
```

---

## 4. Makefile Modifications & Compilation Pipeline

### The GameBoy Header Compilation Workaround (`tests/gb/gb.h`)
The core engine `dandy_core.c` includes `<gb/gb.h>` on line 1 and uses the GBDK-specific `SWITCH_ROM(2)` macro for GameBoy bank-switching.
To compile this code natively on Linux/GCC without editing the source file:
1. Create a dummy GameBoy header `tests/gb/gb.h` containing:
   ```c
   #ifndef MOCK_GB_H
   #define MOCK_GB_H
   // On modern OS/flat memory spaces, bank-switching is a no-op
   #define SWITCH_ROM(bank) ((void)0)
   #endif
   ```
2. Add `-Itests` to the compiler flags of GCC. The inclusion `<gb/gb.h>` will resolve to our mock header `tests/gb/gb.h` seamlessly!

### Recommended Makefile Changes
The following target and clean-up modifications should be appended to `dandy-gb/Makefile`:

```makefile
# --- Offline E2E Testing Target ---
CC = gcc
TEST_DIR = tests
TEST_LIB = $(TEST_DIR)/libdandy_test.so

.PHONY: test_lib

# Target to compile the shared library
test_lib: $(TEST_LIB)

$(TEST_LIB): $(SRC_DIR)/dandy_core.c $(SRC_DIR)/levels.c $(TEST_DIR)/mock_hal.c $(TEST_DIR)/gb/gb.h
	@mkdir -p $(TEST_DIR)
	$(CC) -shared -fPIC -O2 -I$(SRC_DIR) -I$(TEST_DIR) -o $@ \
		$(SRC_DIR)/dandy_core.c \
		$(SRC_DIR)/levels.c \
		$(TEST_DIR)/mock_hal.c
	@echo "----------------------------------------"
	@echo "Test library build successful: $@"
	@echo "----------------------------------------"

# Update existing clean rule to remove the test library
clean:
	rm -rf $(OBJ_DIR) $(BIN_DIR)
	rm -f $(WEB_DIR)/*.js $(WEB_DIR)/*.wasm
	rm -f *.lst *.map *.sym
	rm -f $(TEST_LIB)
	@echo "Clean complete."
```

---

## 5. Draft `TEST_INFRA.md` for Project Root

This is the proposed content for `TEST_INFRA.md`, defining the offline E2E test infrastructure.

```markdown
# Dandy Dungeon E2E Testing Infrastructure

This document details the offline End-to-End (E2E) testing framework for Dandy Dungeon. The framework compiles the core, platform-independent C engine with a mock Hardware Abstraction Layer (HAL) into a shared library, exposing the entire game state to a Python test harness.

## 1. Test Architecture

The offline testing infrastructure bypasses physical hardware or emulators, allowing tests to run programmatically in milliseconds.

```
+-------------------------------------------------------------+
|                     tests/test_suite.py                     |
|  - Write declarative test cases                             |
|  - Set map layouts, inject player inputs, step game loop    |
|  - Perform programmatic assertions on state & HAL effects   |
+------------------------------+------------------------------+
                               | (Calls Python API)
                               v
+-------------------------------------------------------------+
|                     tests/dandy_env.py                      |
|  - Python ctypes wrapper                                    |
|  - Connects Python properties to live C global variables    |
|  - Formats data structures (sprites, sound lists, etc.)     |
+------------------------------+------------------------------+
                               | (Loads Shared Library)
                               v
+-------------------------------------------------------------+
|               libdandy_test.so (C Shared Lib)               |
|  - src/dandy_core.c : Compiled game logic                   |
|  - src/levels.c     : Level database (RLE-compressed)       |
|  - tests/mock_hal.c : Records drawings, sounds, and sprites |
+-------------------------------------------------------------+
```

### Key Components:
- **`tests/mock_hal.c`**: Implements the drawing, sound, sprite, and HUD interfaces. Instead of writing to GameBoy VRAM or sound registers, it records all invocations in internal arrays (buffers) that are queryable via mock extension functions.
- **`tests/gb/gb.h`**: A mock header that stubs the GameBoy-specific GBDK `#include <gb/gb.h>` and makes the `SWITCH_ROM` bank-switching macro a no-op.
- **`tests/dandy_env.py`**: A `ctypes` bridge that loads the shared library and maps C globals (e.g. `dandy_map`, `player_health`) and engine control functions (e.g. `dandy_step`, `dandy_load_level`) to an idiomatic, high-level Python class `DandyEnv`.

---

## 2. Game Feature Inventory

The following 8 core engine features represent the functional scope of the Dandy Dungeon core engine. The test suite must comprehensively cover each of these:

1. **Level Loading & RLE Decompression**
   - Verification that `dandy_load_level` correctly decompresses the RLE byte stream (`0xFF, run_len, tile_id` or literal bytes) from `dandy_levels` into the `dandy_map` buffer.
   - Verification that player start positions are correctly offset relative to the location of the `TILE_UP` (entrance) tile.
2. **Player Movement & Slide Physics**
   - Joypad input mapping to player direction and coordinate updates.
   - Correct handling of physical collision with walls (`TILE_WALL`) and closed doors (`TILE_DOOR`).
   - The slide-around-obstacles mechanic: when blocked, the engine attempts to slide the player ±45 degrees in adjacent diagonals.
   - Move cooldown timer ticking.
3. **Item & Interactive Object Collection**
   - Collecting Keys (`TILE_KEY`), Money (`TILE_MONEY`), Smart Bombs (`TILE_BOMB`), and Food (`TILE_FOOD`) and asserting on appropriate inventory increment, sound trigger, and tile replacement.
   - Door Unlocking: consuming a key to unlock a door, and performing an iterative flood fill to unlock all interconnected door tiles (ensuring multi-tile doors open simultaneously).
4. **Combat, Shooting & Projectiles (Arrows)**
   - Firing arrows in the current facing direction using `BUTTON_FIRE`.
   - Restricting players to a single active arrow at a time.
   - Deactivating arrows when they hit solid obstacles, or when they leave the shooting player's visible viewport (10 tiles horizontal, 5 vertical camera boundary).
   - Arrow-entity collisions: damaging/destroying monsters (downgrading Monster 3 -> 2 -> 1 -> Space), turning hearts into Monster 3, and detonating bombs.
5. **Monster Behavior & AI**
   - Target selection: routing monsters to track the closest active, living player.
   - Pathfinding: moving towards players, utilizing slide physics around walls.
   - Monster-player collision: dealing damage based on monster level (`10 * monster_lvl`), clearing the monster, and triggering player death at 0 HP.
   - Sparse-grid execution: validating that monsters update on a rotating grid pattern governed by `monster_rotor` (1/16th of the map per tick).
   - Camera visibility freeze: verifying that monsters freeze (do not step/act) if they are outside of all active players' screen viewports.
6. **Generator Spawning**
   - Generator tiles (`TILE_GENERATOR1`..`TILE_GENERATOR3`) spawning corresponding monsters in adjacent empty spaces.
   - Freezing generators when they are off-screen.
7. **Level Transitions & Game Progression**
   - Stepping onto the exit tile (`TILE_DOWN`) triggering a warp sound and loading the next level index.
   - High-level progress check: advancing from Level 0 to Level 25.
   - Game Over: resetting all progress and inventory, reloading Level 0 when all players die.
8. **Cooperative Multiplayer & Viewport Camera**
   - Multi-player joining (up to 4 players) and separate coordinate/inventory tracking.
   - Dynamic camera centering: viewport camera following the active local player, or computing the centroid (average coordinates) of all active players.
   - Camera clamping: ensuring the viewport stays strictly within the 60x30 map boundaries.
   - Hardware Sprite rendering: rendering players, active arrows, and active monsters as hardware sprites via `hal_set_sprite` while drawing the underlying tile as empty space (`TILE_SPACE`) on the background layer.

---

## 3. Test Tiers & Coverage Thresholds

The test harness enforces a strict 4-tier testing hierarchy to guarantee engine stability.

| Tier | Type | Target Count | Objective |
|---|---|---|---|
| **Tier 1** | Happy-Path Features | >= 40 tests | Verifies standard, expected behavior for each of the 8 features. |
| **Tier 2** | Boundary & Corner Cases | >= 40 tests | Tests limits, collisions, blocked paths, edge coordinates, and level wraps. |
| **Tier 3** | Cross-Feature Interactions | >= 8 tests | Verifies cooperation/conflicts between systems (e.g. projectile detonating bomb next to a monster). |
| **Tier 4** | E2E Scenario Playthroughs | >= 5 tests | Simulates realistic player runs, cooperative sessions, and game-over loops. |

### Minimum Quality Gates:
- **Core Statement Coverage (`dandy_core.c`)**: **>= 95%**
- **Core Branch Coverage (`dandy_core.c`)**: **>= 90%**
- **Feature Coverage**: **100% of defined features**
```

---

## 6. Infrastructure Verification Plan

To verify that the designed E2E test infrastructure works correctly, the following verification plan should be executed once the files are implemented:

1. **Verify Header Interception**:
   - Compile `src/dandy_core.c` with GCC using `-Itests`.
   - Confirm that `<gb/gb.h>` resolves to `tests/gb/gb.h` and compiles without "header not found" errors.
2. **Verify Shared Library Compilation**:
   - Run `make test_lib` in the `dandy-gb` directory.
   - Verify that `tests/libdandy_test.so` is created successfully.
   - Run `file tests/libdandy_test.so` to confirm it is a valid ELF 64-bit shared object.
3. **Verify Ctypes Binding Loading**:
   - Run a short Python script to load `DandyEnv`:
     ```python
     from tests.dandy_env import DandyEnv
     env = DandyEnv()
     print("Shared library loaded successfully!")
     ```
4. **Verify Live Global Synchronization**:
   - In Python, call `env.init()`.
   - Assert that `env.current_level == 0`.
   - Assert that `env.get_player_health(0) == 100`.
   - Modify `env.current_level = 5` in Python.
   - Call `env.load_level(env.current_level)`.
   - Assert that `env.current_level == 5` and the map buffer `env.map` matches the decompressed Level 5 data.
5. **Verify Mock HAL side-effects recording**:
   - Set player 0's coordinate next to a key tile.
   - Run one step `env.step([env.BUTTON_RIGHT, 0, 0, 0])` (assuming right moves onto the key).
   - Assert that a sound was played: `env.mock_get_sounds()` contains `env.SOUND_KEY` (4).
   - Assert that `env.get_player_keys(0) == 1`.
   - Assert that `env.mock_get_draw_count() > 0`.
