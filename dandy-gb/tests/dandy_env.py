import ctypes
import os
import shutil
import sys
import tempfile
import _ctypes

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
            # 1. Try relative to this script
            script_dir = os.path.dirname(os.path.abspath(__file__))
            lib_path = os.path.abspath(os.path.join(script_dir, "../libdandy_test.so"))
            
        if not os.path.exists(lib_path):
            # 2. Try current working directory
            lib_path_fallback = os.path.abspath(os.path.join(os.getcwd(), "libdandy_test.so"))
            if os.path.exists(lib_path_fallback):
                lib_path = lib_path_fallback
            else:
                # 3. Try another common fallback
                lib_path_fallback2 = os.path.abspath(os.path.join(os.getcwd(), "dandy-gb/libdandy_test.so"))
                if os.path.exists(lib_path_fallback2):
                    lib_path = lib_path_fallback2
                else:
                    raise FileNotFoundError(
                        f"Shared library not found at '{lib_path}'. "
                        f"Please run 'make test_lib' first to compile it."
                    )
        
        # Create unique temp library copy to achieve 100% state isolation
        script_dir = os.path.dirname(os.path.abspath(__file__))
        temp_base = os.path.join(script_dir, ".temp_envs")
        os.makedirs(temp_base, exist_ok=True)
        self._temp_dir = tempfile.mkdtemp(prefix="dandy_env_", dir=temp_base)
        self._temp_lib_path = os.path.join(self._temp_dir, "libdandy_test.so")
        shutil.copy(lib_path, self._temp_lib_path)
        
        # Load the unique library copy
        try:
            # Check file existence and size
            if not os.path.exists(self._temp_lib_path):
                print(f"[DandyEnv] ERROR: Temp lib file does not exist at {self._temp_lib_path} right after copy!")
            else:
                size = os.path.getsize(self._temp_lib_path)
                if size == 0:
                    print(f"[DandyEnv] ERROR: Temp lib file at {self._temp_lib_path} is 0 bytes! Source was {lib_path} ({os.path.getsize(lib_path)} bytes)")
            self._lib = ctypes.CDLL(self._temp_lib_path)
        except Exception as e:
            if os.path.exists(self._temp_lib_path):
                print(f"[DandyEnv] CDLL load failed. Temp lib size: {os.path.getsize(self._temp_lib_path)} bytes.")
            else:
                print(f"[DandyEnv] CDLL load failed. Temp lib does not exist anymore.")
            raise e
        self._setup_bindings()
        
    def _setup_bindings(self):
        # --- Core Function Signatures ---
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
        
        # --- Mock Extension Signatures ---
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

        self._lib.mock_get_sprite_oob_error.argtypes = []
        self._lib.mock_get_sprite_oob_error.restype = ctypes.c_bool

        self._lib.mock_get_hud_update_count.argtypes = []
        self._lib.mock_get_hud_update_count.restype = ctypes.c_int

        self._lib.mock_get_camera.argtypes = [
            ctypes.POINTER(ctypes.c_uint8), 
            ctypes.POINTER(ctypes.c_uint8)
        ]
        self._lib.mock_get_camera.restype = None

        # --- Bind Live C Globals ---
        self._dandy_map = (ctypes.c_uint8 * self.MAP_SIZE).in_dll(self._lib, "dandy_map")
        self._current_level = ctypes.c_uint8.in_dll(self._lib, "current_level")
        self._monster_rotor = ctypes.c_uint8.in_dll(self._lib, "monster_rotor")
        self._player_joined = (ctypes.c_bool * self.MAX_PLAYERS).in_dll(self._lib, "player_joined")
        self._local_player_idx = ctypes.c_uint8.in_dll(self._lib, "local_player_idx")
        self._is_dirty = ctypes.c_bool.in_dll(self._lib, "is_dirty")
        self._dandy_num_levels = ctypes.c_uint8.in_dll(self._lib, "dandy_num_levels")
        
        self._player_x = (ctypes.c_uint8 * self.MAX_PLAYERS).in_dll(self._lib, "player_x")
        self._player_y = (ctypes.c_uint8 * self.MAX_PLAYERS).in_dll(self._lib, "player_y")
        self._player_health = (ctypes.c_int16 * self.MAX_PLAYERS).in_dll(self._lib, "player_health")
        self._player_score = (ctypes.c_uint16 * self.MAX_PLAYERS).in_dll(self._lib, "player_score")
        self._player_bombs = (ctypes.c_uint8 * self.MAX_PLAYERS).in_dll(self._lib, "player_bombs")
        self._player_keys = (ctypes.c_uint8 * self.MAX_PLAYERS).in_dll(self._lib, "player_keys")
        self._player_dir = (ctypes.c_int8 * self.MAX_PLAYERS).in_dll(self._lib, "player_dir")
        self._player_move_timer = (ctypes.c_uint8 * self.MAX_PLAYERS).in_dll(self._lib, "player_move_timer")
        
        self._arrow_x = (ctypes.c_uint8 * self.MAX_PLAYERS).in_dll(self._lib, "arrow_x")
        self._arrow_y = (ctypes.c_uint8 * self.MAX_PLAYERS).in_dll(self._lib, "arrow_y")
        self._arrow_dir = (ctypes.c_int8 * self.MAX_PLAYERS).in_dll(self._lib, "arrow_dir")

    def close(self):
        """
        Explicitly unloads the shared library and deletes the temporary directory,
        handling exceptions gracefully.
        """
        if hasattr(self, "_lib"):
            try:
                _ctypes.dlclose(self._lib._handle)
            except Exception:
                pass
            del self._lib
        if hasattr(self, "_temp_dir") and os.path.exists(self._temp_dir):
            try:
                shutil.rmtree(self._temp_dir)
            except Exception as e:
                print(f"Warning: Failed to remove temp directory {self._temp_dir}: {e}", file=sys.stderr)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def __del__(self):
        self.close()

    # --- Live Global Property Accessors ---
    @property
    def num_levels(self):
        return self._dandy_num_levels.value

    @property
    def dandy_map(self):
        return list(self._dandy_map)
    
    @dandy_map.setter
    def dandy_map(self, new_map):
        if len(new_map) != self.MAP_SIZE:
            raise ValueError(f"Map size must be exactly {self.MAP_SIZE}")
        for i in range(self.MAP_SIZE):
            self._dandy_map[i] = new_map[i]

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

    # --- Player State Array Accessors (Explorer 1 Style) ---
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

    # --- Arrow State Accessors (Explorer 1 Style) ---
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

    # --- Unified Player State Accessor (Explorer 3 Style) ---
    def get_player(self, p_idx):
        if p_idx < 0 or p_idx >= self.MAX_PLAYERS:
            raise IndexError("Player index out of bounds")
        return {
            'joined': self._player_joined[p_idx],
            'x': self._player_x[p_idx],
            'y': self._player_y[p_idx],
            'health': self._player_health[p_idx],
            'score': self._player_score[p_idx],
            'bombs': self._player_bombs[p_idx],
            'keys': self._player_keys[p_idx],
            'dir': self._player_dir[p_idx],
            'move_timer': self._player_move_timer[p_idx],
            'arrow': {
                'x': self._arrow_x[p_idx],
                'y': self._arrow_y[p_idx],
                'dir': self._arrow_dir[p_idx]
            }
        }

    def set_player_position(self, p_idx, x, y):
        self._player_x[p_idx] = x
        self._player_y[p_idx] = y

    # --- Core Engine API Wrappers ---
    def init(self):
        self._lib.dandy_init()

    def step(self, inputs):
        """
        inputs: List or tuple of 4 integers representing button bitmasks for each player.
        """
        if len(inputs) != self.MAX_PLAYERS:
            raise ValueError(f"Inputs must contain exactly {self.MAX_PLAYERS} items")
        arr = (ctypes.c_uint8 * self.MAX_PLAYERS)(*inputs)
        self._lib.dandy_step(arr)

    def load_level(self, level_idx):
        self._lib.dandy_load_level(level_idx)

    def draw_viewport(self, local_p_idx):
        self._lib.dandy_draw_viewport(local_p_idx)

    def join_player(self, p_idx):
        self._lib.dandy_join_player(p_idx)

    # --- Mock HAL Query API Wrappers ---
    def mock_clear(self):
        self._lib.mock_clear_buffers()

    def clear_mock_buffers(self):
        self._lib.mock_clear_buffers()

    def mock_get_draw_count(self):
        return self._lib.mock_get_draw_count()

    def get_draw_count(self):
        return self._lib.mock_get_draw_count()

    def mock_get_draws(self):
        count = self.mock_get_draw_count()
        draws = []
        x = ctypes.c_uint8()
        y = ctypes.c_uint8()
        tile_id = ctypes.c_uint8()
        for i in range(count):
            self._lib.mock_get_draw(i, ctypes.byref(x), ctypes.byref(y), ctypes.byref(tile_id))
            draws.append((x.value, y.value, tile_id.value))
        return draws

    def get_draws(self):
        count = self.mock_get_draw_count()
        draws = []
        x = ctypes.c_uint8()
        y = ctypes.c_uint8()
        tile_id = ctypes.c_uint8()
        for i in range(count):
            self._lib.mock_get_draw(i, ctypes.byref(x), ctypes.byref(y), ctypes.byref(tile_id))
            draws.append({'x': x.value, 'y': y.value, 'tile_id': tile_id.value})
        return draws

    def mock_get_sound_count(self):
        return self._lib.mock_get_sound_count()

    def mock_get_sounds(self):
        count = self.mock_get_sound_count()
        return [self._lib.mock_get_sound(i) for i in range(count)]

    def get_sounds(self):
        count = self._lib.mock_get_sound_count()
        return [self._lib.mock_get_sound(i) for i in range(count)]

    def mock_get_sprite(self, sprite_idx):
        x = ctypes.c_uint8()
        y = ctypes.c_uint8()
        tile_id = ctypes.c_uint8()
        flags = ctypes.c_uint8()
        self._lib.mock_get_sprite(sprite_idx, ctypes.byref(x), ctypes.byref(y), ctypes.byref(tile_id), ctypes.byref(flags))
        active = self._lib.mock_is_sprite_active(sprite_idx)
        return {
            "x": x.value,
            "y": y.value,
            "tile_id": tile_id.value,
            "flags": flags.value,
            "active": active
        }

    def mock_get_sprites(self):
        return [self.mock_get_sprite(i) for i in range(40)]

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

    def mock_get_viewport_camera(self):
        cam_x = ctypes.c_uint8()
        cam_y = ctypes.c_uint8()
        self._lib.mock_get_camera(ctypes.byref(cam_x), ctypes.byref(cam_y))
        return cam_x.value, cam_y.value

    def get_camera(self):
        cam_x = ctypes.c_uint8()
        cam_y = ctypes.c_uint8()
        self._lib.mock_get_camera(ctypes.byref(cam_x), ctypes.byref(cam_y))
        return cam_x.value, cam_y.value

    def mock_get_hud_update_count(self):
        return self._lib.mock_get_hud_update_count()

    def get_hud_update_count(self):
        return self._lib.mock_get_hud_update_count()

    def get_sprite_oob_error(self):
        return self._lib.mock_get_sprite_oob_error()

    def assert_outer_border_walls(self, test_case):
        """
        Asserts that the entire outer border of the 60x30 dandy_map consists
        of solid wall tiles (TILE_WALL / ID 1).
        """
        current_map = self.dandy_map
        # Top row (y = 0)
        for x in range(60):
            tile = current_map[0 * 60 + x]
            test_case.assertEqual(tile, self.TILE_WALL, f"Top row border wall missing at x={x}")
        # Bottom row (y = 29)
        for x in range(60):
            tile = current_map[29 * 60 + x]
            test_case.assertEqual(tile, self.TILE_WALL, f"Bottom row border wall missing at x={x}")
        # Left column (x = 0)
        for y in range(30):
            tile = current_map[y * 60 + 0]
            test_case.assertEqual(tile, self.TILE_WALL, f"Left column border wall missing at y={y}")
        # Right column (x = 59)
        for y in range(30):
            tile = current_map[y * 60 + 59]
            test_case.assertEqual(tile, self.TILE_WALL, f"Right column border wall missing at y={y}")
