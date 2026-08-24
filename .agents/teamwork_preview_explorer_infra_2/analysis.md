# Technical Design & Analysis Report: Offline E2E Test Infrastructure
**Milestone 1: E2E Test Runner and Architecture Design**

This document details the architecture, interfaces, and build integration design for the offline End-to-End (E2E) testing track of Dandy Dungeon. Since the core game logic in `dandy_core.c` is written in platform-independent C, we can compile it with a mock Hardware Abstraction Layer (HAL) on a host system (e.g. Linux) to test the entire game engine programmatically in Python via `ctypes`.

---

## 1. Core Engine Analysis

### 1.1 GBDK & Hardware Dependencies
The core game engine (`dandy_core.c`) is designed for the GameBoy using GBDK-2020. However, its hardware dependencies are minimal and strictly confined to:
1. `#include <gb/gb.h>`: The GBDK system header containing GameBoy-specific hardware control functions.
2. `SWITCH_ROM(2);`: A macro used in `dandy_load_level` to switch to ROM bank 2, where the compressed levels array (`dandy_levels`) resides.

**Host Compilation Solution (Zero Code Modification)**:
To compile `dandy_core.c` on the host system without making any changes to the GameBoy source code, we will introduce a dummy header directory `tests/mock_headers/` containing a mock GameBoy header `gb/gb.h`.
```c
/* tests/mock_headers/gb/gb.h */
#ifndef MOCK_GB_H
#define MOCK_GB_H

/* No-op bank switching on host since all code/data reside in the host address space */
#define SWITCH_ROM(bank) ((void)0)

#endif /* MOCK_GB_H */
```
By adding `-Itests/mock_headers` to the compiler include path, the host compiler will resolve `<gb/gb.h>` to this dummy header, rendering `SWITCH_ROM(2)` a harmless no-op.

### 1.2 State Globals & Functions to Expose
The following engine state variables and functions are declared in `dandy_core.h` and must be exposed in the shared library `libdandy_test.so` for ctypes mapping.

#### Exposed C Globals
- `uint8_t dandy_map[1800]`: Grid map representation of the current level (60 columns × 30 rows).
- `uint8_t current_level`: Index of the currently loaded level (0 to 25).
- `uint8_t monster_rotor`: Rotor value (0 to 15) determining sparse monster ticks.
- `bool player_joined[4]`: Active join status of the 4 supported players.
- `uint8_t local_player_idx`: Index of the local player (normally 0).
- `uint8_t player_x[4]` / `uint8_t player_y[4]`: Coordinates of the 4 players.
- `int16_t player_health[4]`: Health levels of the 4 players.
- `uint16_t player_score[4]`: Score values of the 4 players.
- `uint8_t player_bombs[4]`: Smart bomb inventories.
- `uint8_t player_keys[4]`: Key inventories.
- `int8_t player_dir[4]`: Player direction values (0 to 7).
- `uint8_t player_move_timer[4]`: Input movement cooldown timers.
- `uint8_t arrow_x[4]` / `uint8_t arrow_y[4]`: Coordinates of active arrows.
- `int8_t arrow_dir[4]`: Directions of active arrows (-1 if inactive, 0 to 7 if active).
- `bool is_dirty`: Boolean flag indicating if a screen redraw is pending.

#### Exposed C Functions
- `void dandy_init(void);`
- `void dandy_step(const uint8_t player_inputs[4]);`
- `void dandy_load_level(uint8_t level_idx);`
- `void dandy_draw_viewport(uint8_t local_p_idx);`
- `void dandy_join_player(uint8_t p_idx);`
- `bool dandy_is_player_joined(uint8_t p_idx);`

---

## 2. Mock HAL Design (`tests/mock_hal.h` & `tests/mock_hal.c`)

The mock Hardware Abstraction Layer implements the drawing, sound, sprite, and HUD functions that `dandy_core.c` expects from the hardware platform. Rather than writing to GameBoy VRAM or sound registers, it records all invocations in queryable buffers so that Python tests can verify the visual and auditory side effects of player actions.

### 2.1 Interface Definition (`tests/mock_hal.h`)
```c
#ifndef MOCK_HAL_H
#define MOCK_HAL_H

#include <stdint.h>
#include <stdbool.h>

#define MAX_MOCK_DRAWS  1024
#define MAX_MOCK_SOUNDS 256
#define MAX_SPRITES     40

/* Structures to capture HAL side effects */
typedef struct {
    uint8_t x;
    uint8_t y;
    uint8_t tile_id;
} MockDrawCall;

typedef struct {
    uint8_t x;
    uint8_t y;
    uint8_t tile_id;
    uint8_t flags;
    bool active;
} MockSpriteState;

/* Mock Control and Query API for Python Test Runner */
void mock_clear_buffers(void);
int mock_get_draw_count(void);
void mock_get_draw(int idx, uint8_t* x, uint8_t* y, uint8_t* tile_id);
int mock_get_sound_count(void);
uint8_t mock_get_sound(int idx);
void mock_get_sprite(uint8_t sprite_idx, uint8_t* x, uint8_t* y, uint8_t* tile_id, uint8_t* flags);
bool mock_is_sprite_active(uint8_t sprite_idx);
int mock_get_hud_update_count(void);
void mock_get_viewport_scroll(uint8_t* vp_left, uint8_t* vp_top);

#endif /* MOCK_HAL_H */
```

### 2.2 Implementation (`tests/mock_hal.c`)
```c
#include "dandy_core.h"
#include "mock_hal.h"
#include <string.h>

/* Internal State Buffers */
static MockDrawCall mock_draws[MAX_MOCK_DRAWS];
static int mock_draw_count = 0;

static uint8_t mock_sounds[MAX_MOCK_SOUNDS];
static int mock_sound_count = 0;

static MockSpriteState mock_sprites[MAX_SPRITES];

static int mock_hud_update_count = 0;
static uint8_t last_vp_left = 0;
static uint8_t last_vp_top = 0;

/* --- Standard HAL Implementations (Expected by dandy_core.c) --- */

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
    last_vp_left = vp_left;
    last_vp_top = vp_top;
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

/* --- Mock Query and Control Extensions (Exposed to Python) --- */

void mock_clear_buffers(void) {
    mock_draw_count = 0;
    mock_sound_count = 0;
    mock_hud_update_count = 0;
    last_vp_left = 0;
    last_vp_top = 0;
    memset(mock_draws, 0, sizeof(mock_draws));
    memset(mock_sounds, 0, sizeof(mock_sounds));
    memset(mock_sprites, 0, sizeof(mock_sprites));
}

int mock_get_draw_count(void) {
    return mock_draw_count;
}

void mock_get_draw(int idx, uint8_t* x, uint8_t* y, uint8_t* tile_id) {
    if (idx >= 0 && idx < mock_draw_count) {
        *x = mock_draws[idx].x;
        *y = mock_draws[idx].y;
        *tile_id = mock_draws[idx].tile_id;
    } else {
        *x = 0;
        *y = 0;
        *tile_id = 0;
    }
}

int mock_get_sound_count(void) {
    return mock_sound_count;
}

uint8_t mock_get_sound(int idx) {
    if (idx >= 0 && idx < mock_sound_count) {
        return mock_sounds[idx];
    }
    return 0xFF; /* Sentinel representing invalid index */
}

void mock_get_sprite(uint8_t sprite_idx, uint8_t* x, uint8_t* y, uint8_t* tile_id, uint8_t* flags) {
    if (sprite_idx < MAX_SPRITES) {
        *x = mock_sprites[sprite_idx].x;
        *y = mock_sprites[sprite_idx].y;
        *tile_id = mock_sprites[sprite_idx].tile_id;
        *flags = mock_sprites[sprite_idx].flags;
    } else {
        *x = 0;
        *y = 0;
        *tile_id = 0;
        *flags = 0;
    }
}

bool mock_is_sprite_active(uint8_t sprite_idx) {
    if (sprite_idx < MAX_SPRITES) {
        return mock_sprites[sprite_idx].active;
    }
    return false;
}

int mock_get_hud_update_count(void) {
    return mock_hud_update_count;
}

void mock_get_viewport_scroll(uint8_t* vp_left, uint8_t* vp_top) {
    *vp_left = last_vp_left;
    *vp_top = last_vp_top;
}
```

---

## 3. Python Ctypes Wrapper Design (`tests/dandy_env.py`)

The Python wrapper `dandy_env.py` abstracts the ctypes bindings. It loads `libdandy_test.so`, defines appropriate C-compatible signatures, and maps C arrays directly to mutable properties. This allows tests to modify level maps directly, trigger steps, and inspect mock buffers with native Python structures.

```python
# tests/dandy_env.py
import ctypes
import os

# ==============================================================================
# Game Engine Constants
# ==============================================================================
MAP_WIDTH = 60
MAP_HEIGHT = 30
MAP_SIZE = 1800
MAX_PLAYERS = 4

# Tile ID Definitions
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

# Input Button Masks
BUTTON_LEFT = 1 << 0
BUTTON_RIGHT = 1 << 1
BUTTON_UP = 1 << 2
BUTTON_DOWN = 1 << 3
BUTTON_FIRE = 1 << 4
BUTTON_BOMB = 1 << 5

# Retro Sound IDs
SOUND_SHOOT = 0
SOUND_HIT = 1
SOUND_FOOD = 2
SOUND_BOMB = 3
SOUND_KEY = 4
SOUND_DIE = 5
SOUND_WARP = 6


class DandyEnv:
    """Python environment wrapper wrapping libdandy_test.so via ctypes."""

    def __init__(self, lib_path=None):
        if lib_path is None:
            # Locate library in bin/ relative to the project root
            project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            lib_path = os.path.join(project_dir, "bin", "libdandy_test.so")
            if not os.path.exists(lib_path):
                lib_path = "./libdandy_test.so"

        self.lib = ctypes.CDLL(lib_path)
        self._bind_globals()
        self._bind_functions()

    def _bind_globals(self):
        """Bind global variables directly from the shared library."""
        self._dandy_map = (ctypes.c_uint8 * MAP_SIZE).in_dll(self.lib, "dandy_map")
        self._current_level = ctypes.c_uint8.in_dll(self.lib, "current_level")
        self._monster_rotor = ctypes.c_uint8.in_dll(self.lib, "monster_rotor")
        self._player_joined = (ctypes.c_bool * MAX_PLAYERS).in_dll(self.lib, "player_joined")
        self._local_player_idx = ctypes.c_uint8.in_dll(self.lib, "local_player_idx")
        self._is_dirty = ctypes.c_bool.in_dll(self.lib, "is_dirty")

        # Player arrays
        self._player_x = (ctypes.c_uint8 * MAX_PLAYERS).in_dll(self.lib, "player_x")
        self._player_y = (ctypes.c_uint8 * MAX_PLAYERS).in_dll(self.lib, "player_y")
        self._player_health = (ctypes.c_int16 * MAX_PLAYERS).in_dll(self.lib, "player_health")
        self._player_score = (ctypes.c_uint16 * MAX_PLAYERS).in_dll(self.lib, "player_score")
        self._player_bombs = (ctypes.c_uint8 * MAX_PLAYERS).in_dll(self.lib, "player_bombs")
        self._player_keys = (ctypes.c_uint8 * MAX_PLAYERS).in_dll(self.lib, "player_keys")
        self._player_dir = (ctypes.c_int8 * MAX_PLAYERS).in_dll(self.lib, "player_dir")
        self._player_move_timer = (ctypes.c_uint8 * MAX_PLAYERS).in_dll(self.lib, "player_move_timer")

        # Arrow arrays
        self._arrow_x = (ctypes.c_uint8 * MAX_PLAYERS).in_dll(self.lib, "arrow_x")
        self._arrow_y = (ctypes.c_uint8 * MAX_PLAYERS).in_dll(self.lib, "arrow_y")
        self._arrow_dir = (ctypes.c_int8 * MAX_PLAYERS).in_dll(self.lib, "arrow_dir")

    def _bind_functions(self):
        """Configure arguments and return types for DLL functions."""
        self.lib.dandy_init.argtypes = []
        self.lib.dandy_init.restype = None

        self.lib.dandy_step.argtypes = [ctypes.POINTER(ctypes.c_uint8 * MAX_PLAYERS)]
        self.lib.dandy_step.restype = None

        self.lib.dandy_load_level.argtypes = [ctypes.c_uint8]
        self.lib.dandy_load_level.restype = None

        self.lib.dandy_draw_viewport.argtypes = [ctypes.c_uint8]
        self.lib.dandy_draw_viewport.restype = None

        self.lib.dandy_join_player.argtypes = [ctypes.c_uint8]
        self.lib.dandy_join_player.restype = None

        self.lib.dandy_is_player_joined.argtypes = [ctypes.c_uint8]
        self.lib.dandy_is_player_joined.restype = ctypes.c_bool

        # Mock HAL Query Bindings
        self.lib.mock_clear_buffers.argtypes = []
        self.lib.mock_clear_buffers.restype = None

        self.lib.mock_get_draw_count.argtypes = []
        self.lib.mock_get_draw_count.restype = ctypes.c_int

        self.lib.mock_get_draw.argtypes = [
            ctypes.c_int,
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.POINTER(ctypes.c_uint8)
        ]
        self.lib.mock_get_draw.restype = None

        self.lib.mock_get_sound_count.argtypes = []
        self.lib.mock_get_sound_count.restype = ctypes.c_int

        self.lib.mock_get_sound.argtypes = [ctypes.c_int]
        self.lib.mock_get_sound.restype = ctypes.c_uint8

        self.lib.mock_get_sprite.argtypes = [
            ctypes.c_uint8,
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.POINTER(ctypes.c_uint8)
        ]
        self.lib.mock_get_sprite.restype = None

        self.lib.mock_is_sprite_active.argtypes = [ctypes.c_uint8]
        self.lib.mock_is_sprite_active.restype = ctypes.c_bool

        self.lib.mock_get_hud_update_count.argtypes = []
        self.lib.mock_get_hud_update_count.restype = ctypes.c_int

        self.lib.mock_get_viewport_scroll.argtypes = [
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.POINTER(ctypes.c_uint8)
        ]
        self.lib.mock_get_viewport_scroll.restype = None

    # ==============================================================================
    # Properties for Direct C Array Access
    # ==============================================================================
    @property
    def map(self):
        """Exposes map buffer directly. Supports index access: env.map[idx] = tile_id."""
        return self._dandy_map

    @property
    def current_level(self):
        return self._current_level.value

    @current_level.setter
    def current_level(self, value):
        self._current_level.value = value

    @property
    def monster_rotor(self):
        return self._monster_rotor.value

    @monster_rotor.setter
    def monster_rotor(self, value):
        self._monster_rotor.value = value

    @property
    def player_joined(self):
        return self._player_joined

    @property
    def local_player_idx(self):
        return self._local_player_idx.value

    @local_player_idx.setter
    def local_player_idx(self, value):
        self._local_player_idx.value = value

    @property
    def is_dirty(self):
        return self._is_dirty.value

    @is_dirty.setter
    def is_dirty(self, value):
        self._is_dirty.value = value

    # State Array Getters (exposing raw ctypes array supporting read/write)
    @property
    def player_x(self): return self._player_x

    @property
    def player_y(self): return self._player_y

    @property
    def player_health(self): return self._player_health

    @property
    def player_score(self): return self._player_score

    @property
    def player_bombs(self): return self._player_bombs

    @property
    def player_keys(self): return self._player_keys

    @property
    def player_dir(self): return self._player_dir

    @property
    def player_move_timer(self): return self._player_move_timer

    @property
    def arrow_x(self): return self._arrow_x

    @property
    def arrow_y(self): return self._arrow_y

    @property
    def arrow_dir(self): return self._arrow_dir

    # ==============================================================================
    # High-level Python Wrappers
    # ==============================================================================
    def init(self):
        """Resets engine to level 0 and configures initial player 1 state."""
        self.lib.dandy_init()

    def step(self, inputs=[0, 0, 0, 0]):
        """Steps the game loop.
        inputs: list of 4 button bitmasks representing inputs for players 1 to 4.
        """
        c_inputs = (ctypes.c_uint8 * MAX_PLAYERS)(*inputs)
        self.lib.dandy_step(ctypes.byref(c_inputs))

    def load_level(self, level_idx):
        """Loads and decompresses level from levels array."""
        self.lib.dandy_load_level(level_idx)

    def draw_viewport(self, local_p_idx=0):
        """Updates rendering viewport based on specified player's location."""
        self.lib.dandy_draw_viewport(local_p_idx)

    def join_player(self, p_idx):
        """Instructs engine to join player at index p_idx (0 to 3)."""
        self.lib.dandy_join_player(p_idx)

    def is_player_joined(self, p_idx):
        return self.lib.dandy_is_player_joined(p_idx)

    # ==============================================================================
    # Mock HAL Utility Methods
    # ==============================================================================
    def clear_mock_buffers(self):
        """Clears draw calls, sound registers, HUD counts, and resets active sprites."""
        self.lib.mock_clear_buffers()

    def get_draws(self):
        """Returns a list of dicts of recorded draw calls: [{'x': x, 'y': y, 'tile_id': t}, ...]."""
        draws = []
        count = self.lib.mock_get_draw_count()
        for i in range(count):
            x = ctypes.c_uint8()
            y = ctypes.c_uint8()
            tile_id = ctypes.c_uint8()
            self.lib.mock_get_draw(i, ctypes.byref(x), ctypes.byref(y), ctypes.byref(tile_id))
            draws.append({'x': x.value, 'y': y.value, 'tile_id': tile_id.value})
        return draws

    def get_sounds(self):
        """Returns a list of integer retro sound IDs recorded during step execution."""
        sounds = []
        count = self.lib.mock_get_sound_count()
        for i in range(count):
            sounds.append(self.lib.mock_get_sound(i))
        return sounds

    def get_sprite(self, sprite_idx):
        """Returns hardware sprite information at sprite_idx (0 to 39)."""
        x = ctypes.c_uint8()
        y = ctypes.c_uint8()
        tile_id = ctypes.c_uint8()
        flags = ctypes.c_uint8()
        self.lib.mock_get_sprite(sprite_idx, ctypes.byref(x), ctypes.byref(y), ctypes.byref(tile_id), ctypes.byref(flags))
        active = self.lib.mock_is_sprite_active(sprite_idx)
        return {
            'active': active,
            'x': x.value,
            'y': y.value,
            'tile_id': tile_id.value,
            'flags': flags.value
        }

    def get_active_sprites(self):
        """Returns list of active hardware sprites: [{'index': i, 'x': x, 'y': y, ...}]."""
        sprites = []
        for i in range(40):
            sprite = self.get_sprite(i)
            if sprite['active']:
                sprites.append({'index': i, **sprite})
        return sprites

    def get_hud_update_count(self):
        """Returns the number of HUD updates performed since the last clear."""
        return self.lib.mock_get_hud_update_count()

    def get_viewport_scroll(self):
        """Returns (vp_left, vp_top) representing the current camera top-left position."""
        vp_left = ctypes.c_uint8()
        vp_top = ctypes.c_uint8()
        self.lib.mock_get_viewport_scroll(ctypes.byref(vp_left), ctypes.byref(vp_top))
        return vp_left.value, vp_top.value
```

---

## 4. Makefile Integration Design (`dandy-gb/Makefile`)

To build `libdandy_test.so`, we will add the following target to `dandy-gb/Makefile`.
- Since GameBoy compilation uses GBDK's `lcc` cross-compiler, we will define a host compiler variable (`HOST_CC`) to use the host's native `gcc` or `clang` for the testing track.
- We compile using `-fPIC` (Position Independent Code) and link using `-shared`.
- We add `-Itests/mock_headers` to supply the mock `<gb/gb.h>` header.

### 4.1 Makefile Additions
```makefile
# ==============================================================================
# Host E2E Testing Target (libdandy_test.so)
# ==============================================================================
HOST_CC = gcc
HOST_CFLAGS = -fPIC -Wall -Wextra -O2 -Isrc -Itests/mock_headers
TEST_LIB = $(BIN_DIR)/libdandy_test.so

.PHONY: test_lib

# Build host-compilable shared library for E2E offline testing
test_lib: setup levels
	@echo "Compiling E2E testing shared library on host..."
	$(HOST_CC) $(HOST_CFLAGS) -shared -o $(TEST_LIB) \
		src/dandy_core.c \
		src/levels.c \
		tests/mock_hal.c
	@echo "----------------------------------------"
	@echo "E2E test library build successful: $(TEST_LIB)"
	@echo "----------------------------------------"
```

---

## 5. Draft Content for `TEST_INFRA.md`

We draft the following documentation to be created at `/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/TEST_INFRA.md` to guide testing practices.

```markdown
# Dandy Dungeon: E2E Testing Infrastructure Reference

This document describes the design, API, and coverage requirements of the offline End-to-End (E2E) testing framework for Dandy Dungeon.

## 1. Architectural Overview

Since the Dandy Dungeon core game engine (`dandy_core.c`) is platform-independent, we verify its correctness entirely offline on a host system. 
We compile the core engine and level database together with a **Mock Hardware Abstraction Layer (HAL)** into a shared library (`libdandy_test.so`). 
A Python environment wrapper (`tests/dandy_env.py`) loads this shared library via `ctypes`, providing direct programmatic control over the game loop.

```
+-----------------------------------------------------------+
|                   tests/test_suite.py                     |  <-- Python E2E Tests
+----------------------------+------------------------------+
                             | (Uses API)
                             v
+-----------------------------------------------------------+
|                    tests/dandy_env.py                     |  <-- Python Ctypes Wrapper
+----------------------------+------------------------------+
                             | (Loads via ctypes)
                             v
+-----------------------------------------------------------+
|                     libdandy_test.so                      |  <-- Host C Shared Lib
|                                                           |
|   +-------------------+  +----------------------------+   |
|   | src/dandy_core.c  |  |     tests/mock_hal.c       |   |  <-- Mock VRAM/Audio
|   |  (Game Logic)     |  | (Captures drawing/sounds)  |   |
|   +---------+---------+  +----------------------------+   |
|             |                                             |
|             v (Uses level maps)                           |
|   +-------------------+                                   |
|   |    src/levels.c   |                                   |  <-- RLE Level ROM Data
|   +-------------------+                                   |
+-----------------------------------------------------------+
```

## 2. Core Game Feature Inventory

The test suite must cover the following 8 core features of Dandy Dungeon:

1. **Level Loading and Decompression**:
   - RLE decompression from `dandy_levels[level_idx]` into the `dandy_map` RAM buffer (1800 bytes).
   - Scanning the decompressed map to find the level entrance (`TILE_UP`).
   - Placing players at pre-calculated spawn offsets relative to the entrance.

2. **Player Movement & Mechanics**:
   - 8-way movement based on button input masks.
   - Movement cooldowns (`TICKS_PER_MOVE = 4`).
   - **Smart Sliding**: when colliding with an obstacle, the player slides/deflects to the left/right of their movement direction if those tiles are empty.

3. **Inventory & Consumables**:
   - Picking up food (`TILE_FOOD`) increments health by 100.
   - Picking up keys (`TILE_KEY`) increments key count.
   - Picking up money (`TILE_MONEY`) increments score by 100.
   - Picking up bombs (`TILE_BOMB`) increments bomb count.
   - Asserting sound effects played (e.g. `SOUND_FOOD` vs `SOUND_KEY`).

4. **Combat (Arrow Shooting)**:
   - Shooting arrows using `BUTTON_FIRE` in the player's current direction.
   - Arrow-monster collisions (damaging/demoting monsters: Monster 3 -> Monster 2 -> Monster 1 -> Space).
   - Arrow-heart collisions (spawns a level-3 monster).
   - Arrow-bomb collisions (ignites the bomb).
   - Limits: Only 1 active arrow per player.

5. **Smart Bomb Mechanic**:
   - Using a bomb via `BUTTON_BOMB` or shooting a bomb tile with an arrow.
   - Blows up (replaces with `TILE_SPACE`) all monsters and generators within the player's visible viewport.
   - Consumes 1 bomb from inventory (if triggered by button).

6. **Door & Lock Mechanic (Flood Fill)**:
   - Moving into a door tile (`TILE_DOOR`) with keys.
   - Consumes 1 key.
   - Triggers an **iterative 8-way flood fill** that converts all contiguous door tiles to spaces, opening double doors or gates with a single key.

7. **Monsters and Spawning (Generators)**:
   - Generators (`TILE_GENERATOR1..3`) spawn monsters (`TILE_MONSTER1..3`) at adjacent tiles based on a Galois LFSR pseudo-random number generator.
   - Monsters pathfind towards the nearest active player (using an 8-way pathfinding grid with sliding rules).
   - Monsters damage players on contact (10, 20, or 30 damage depending on monster level).
   - **Off-screen Freezing**: Monsters and generators only tick if they are inside at least one player's visible viewport.

8. **Viewports & Camera Scrolling**:
   - Camera follows the local player, keeping them centered (viewport size: 20x10, level size: 60x30).
   - Camera clamps to level boundaries.
   - Spectator mode: when the local player dies, the camera centers on the centroid of the remaining active players.
   - Map rendering: static tiles drawn, dynamic entities (players, monsters, arrows) rendered as hardware sprites (up to 40 sprites).

## 3. Test Coverage Thresholds

To guarantee engine correctness, the implementation track must maintain these thresholds:

| Coverage Metric | Target | Scope |
|---|---|---|
| **Statement Coverage** | `>= 95%` | Statements in `dandy_core.c` |
| **Branch Coverage** | `>= 90%` | Decisional branches in `dandy_core.c` |
| **Level Integrity** | `100%` | Verification that all 26 levels compress/decompress without corruption |
| **Tier 1 (Happy-Path)** | `>= 40 tests` | Basic happy-path tests covering all 8 features |
| **Tier 2 (Boundaries)** | `>= 40 tests` | Extreme values, invalid inputs, overflow checks |
| **Tier 3 (Interactions)** | `>= 8 tests` | Interactive systems (e.g. shooting bombs near player) |
| **Tier 4 (Real scenarios)** | `>= 5 tests` | Full level walkthroughs with predefined button inputs |
```

---

## 6. Verification Plan

To verify that the offline E2E test infrastructure behaves exactly as designed, the following verification plan is recommended.

### 6.1 Recommended Verification Commands
To build the shared library, compile a tiny test driver, or run a test runner, the following commands should be executed:
1. **Clean and Build**:
   ```bash
   make clean
   make test_lib
   ```
   *Assert: `bin/libdandy_test.so` is created.*
   
2. **Import and Initialize Check**:
   Create a temporary file `tests/check_env.py` to assert that Python can load the library and initialize the game state:
   ```python
   # tests/check_env.py
   from dandy_env import DandyEnv, TILE_SPACE
   
   env = DandyEnv()
   env.init()
   
   print("Current Level:", env.current_level)
   print("Player 1 X:", env.player_x[0])
   print("Player 1 Y:", env.player_y[0])
   print("Player 1 Health:", env.player_health[0])
   
   # Assertions
   assert env.current_level == 0
   assert env.player_health[0] == 100
   assert env.player_joined[0] == True
   assert env.player_joined[1] == False
   print("Infrastructure verification PASSED!")
   ```
   Run with:
   ```bash
   PYTHONPATH=tests python3 tests/check_env.py
   ```
   *Assert: Output prints "Infrastructure verification PASSED!".*

### 6.2 Invalidation Conditions
The verification should be considered failed if:
- `libdandy_test.so` fails to compile because the host compiler cannot resolve `<gb/gb.h>`.
- `ctypes` fails to load the library due to unresolved symbols (e.g., missing HAL functions).
- Game variables mapped via `ctypes` are not writable or do not reflect changes made in C.
