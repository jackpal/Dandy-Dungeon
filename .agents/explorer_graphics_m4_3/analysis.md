# Milestone 4 Technical Exploration: Build System & E2E/Unit Verification
**Focus Area**: GBDK Build System Integration, Palette Mode Toggles, and Automated E2E Verification.

---

## 1. Executive Summary
This analysis presents the technical design for integrating the **Atmospheric Dark** rendering mode into the GameBoy version of Dandy Dungeon, configuring the build system to support compile-time mode switches cleanly, and establishing a robust E2E/Unit verification pipeline.

### Core Recommendations:
1.  **Macro-Conditioned Palettes**: Implement compile-time switching in `src/main.c` via `#ifdef USE_BLACK_FLOOR`.
2.  **Isolated Build Directories**: Configure `dandy-gb/Makefile` to compile object files into separate directories (`obj/` vs. `obj_dark/`) and generate separate ROMs (`dandy.gb` vs. `dandy_dark.gb`) depending on the build mode. This prevents object file collisions and avoids unnecessary full rebuilds.
3.  **Parameterized Emulator Tests**: Modify `tests/verify_emulator.py` to accept a `ROM_PATH` environment variable, enabling the same E2E suite to run against both the Classic and Atmospheric ROMs.
4.  **Unified Verification Target**: Automate the entire pipeline (unit testing, dual ROM compilation, dual emulator testing, and dual visual audit sheet generation) with a single command.

---

## 2. Assessment of GBDK Build System (`dandy-gb/Makefile`)
The current `Makefile` uses GBDK's `lcc` frontend to compile C sources into object files and then link them.
-   **Compilation Rule**:
    ```makefile
    $(OBJ_DIR)/%.o: $(SRC_DIR)/%.c
    	$(LCC) -Wf--opt-code-size -c -o $@ $<
    ```
-   **Linking Rule**:
    ```makefile
    $(BIN_DIR)/$(ROM_NAME): $(OBJS)
    	$(LCC) $(LCCFLAGS) -o $@ $(OBJS)
    ```
-   **Limitation**: If a user compiles with a compiler flag (e.g., `make USE_BLACK_FLOOR=1`) and then runs a standard `make`, the object files in `obj/` will **not** recompile because the source files themselves did not change. This leads to silent build corruption where the Classic ROM contains Dark Mode code, or vice versa, unless the user manually runs `make clean`.

---

## 3. Designing Makefile Mode Integration
To solve the compilation collision elegantly, we introduce separate object directories and ROM names for the Atmospheric Dark mode.

### Proposed Makefile Architecture
When `USE_BLACK_FLOOR=1` is specified:
1.  `OBJ_DIR` is set to `obj_dark`.
2.  `ROM_NAME` is set to `dandy_dark.gb`.
3.  `-DUSE_BLACK_FLOOR` is added to the preprocessor flags.

We also add a user-friendly `make dark` target which automatically runs the sub-make with the correct variables.

### Proposed Makefile Snippet
```makefile
# Target ROM Name & Directories configuration based on mode
ifeq ($(USE_BLACK_FLOOR),1)
ROM_NAME = dandy_dark.gb
OBJ_DIR = obj_dark
CFLAGS_MODE = -DUSE_BLACK_FLOOR
else
ROM_NAME = dandy.gb
OBJ_DIR = obj
CFLAGS_MODE =
endif

# Directories
SRC_DIR = src
# OBJ_DIR is set dynamically above
BIN_DIR = bin
TOOLS_DIR = tools
WEB_DIR = web

# Source and Object Files
SRCS = $(SRC_DIR)/main.c $(SRC_DIR)/dandy_core.c $(SRC_DIR)/gameboy_hal.c
OBJS = $(OBJ_DIR)/main.o $(OBJ_DIR)/dandy_core.o $(OBJ_DIR)/gameboy_hal.o $(OBJ_DIR)/levels.o $(OBJ_DIR)/tiles.o

# Flags
LCCFLAGS = -Wa-l -Wl-m -Wl-yo2
CFLAGS = -Wf--opt-code-size $(CFLAGS_MODE)

.PHONY: all clean levels sprites setup web dark test test_lib test_emu

# Default target (Classic DMG)
all: setup levels sprites $(BIN_DIR)/$(ROM_NAME)

# Dedicated target for Atmospheric Dark Mode
dark:
	$(MAKE) USE_BLACK_FLOOR=1 all

# Create necessary directories
setup:
	@mkdir -p $(OBJ_DIR)
	@mkdir -p $(BIN_DIR)
	@mkdir -p $(WEB_DIR)

# Link the ROM
$(BIN_DIR)/$(ROM_NAME): $(OBJS)
	$(LCC) $(LCCFLAGS) -o $@ $(OBJS)
	@echo "----------------------------------------"
	@echo "Build successful: $@"
	@echo "----------------------------------------"

# Compile C source files
$(OBJ_DIR)/%.o: $(SRC_DIR)/%.c
	$(LCC) $(CFLAGS) -c -o $@ $<

$(OBJ_DIR)/levels.o: $(SRC_DIR)/levels.c
	$(LCC) -Wf-bo1 $(CFLAGS_MODE) -c -o $@ $<

# Clean up all build artifacts
clean:
	rm -rf obj obj_dark $(BIN_DIR)
	rm -f $(WEB_DIR)/*.js $(WEB_DIR)/*.wasm
	rm -f *.lst *.map *.sym
	rm -rf tests/mock_gb tests/.temp_envs
	rm -f libdandy_test.so
	@echo "Clean complete."
```

---

## 4. Hardware Palette Integration (`src/main.c`)
The GameBoy's color rendering is controlled by three hardware registers:
1.  **`BGP_REG` (Background Palette)**: Maps tile color indices (0 to 3) to the four physical shades of gray.
2.  **`OBP0_REG` / `OBP1_REG` (Object Palettes 0 & 1)**: Maps sprite tile color indices (0 to 3) to shades of gray, where color index 0 is always transparent.

### Palette Byte Calculations

#### 1. Classic DMG Mode (Default)
*   **Background (BGP_REG = `0xE4`)**:
    *   Maps: Color 0 -> White (`00`), Color 1 -> Light Gray (`01`), Color 2 -> Dark Gray (`10`), Color 3 -> Black (`11`).
    *   Binary Layout: `[Color 3] [Color 2] [Color 1] [Color 0]` -> `11 10 01 00` = `0xE4`.
*   **Sprites (OBP0_REG / OBP1_REG = `0xD8`)**:
    *   Maps: Color 0 -> Transparent (`00`), Color 1 -> Dark Gray (`10`), Color 2 -> Light Gray (`01`), Color 3 -> Black (`11`).
    *   Binary Layout: `[Color 3] [Color 2] [Color 1] [Color 0]` -> `11 01 10 00` = `0xD8`.

#### 2. Atmospheric Dark Mode (`USE_BLACK_FLOOR`)
*   **Background (BGP_REG = `0x1B`)**:
    *   Maps: Color 0 -> Black (`11`), Color 1 -> Dark Gray (`10`), Color 2 -> Light Gray (`01`), Color 3 -> White (`00`).
    *   Binary Layout: `[Color 3] [Color 2] [Color 1] [Color 0]` -> `00 01 10 11` = `0x1B`.
*   **Sprites (OBP0_REG / OBP1_REG = `0xE0`)**:
    *   Maps: Color 0 -> Transparent (`00`), Color 1 -> White (`00`), Color 2 -> Dark Gray (`10`), Color 3 -> Black (`11`).
    *   Binary Layout: `[Color 3] [Color 2] [Color 1] [Color 0]` -> `11 10 00 00` = `0xE0`.

### Proposed C Code Modification in `src/main.c`
```c
    // Explicitly configure hardware palettes from our approved blueprint:
#ifdef USE_BLACK_FLOOR
    // Atmospheric Dark Mode:
    // BGP = 0x1B (00 01 10 11): BKG Color 0 is Black (floor), 1 is Dark Gray (walls), 2 is Light Gray, 3 is White (text)
    BGP_REG = 0x1B;
    // OBP0/1 = 0xE0 (11 10 00 00): Sprite Color 0 is Transparent, 1 is White (body), 2 is Dark Gray, 3 is Black (outlines)
    OBP0_REG = 0xE0;
    OBP1_REG = 0xE0;
#else
    // Classic DMG Mode (Default):
    // BGP = 0xE4 (11 10 01 00): BKG Color 0 is White (floor), 1 is Light Gray (dots), 2 is Dark Gray, 3 is Black (walls/text)
    BGP_REG = 0xE4;
    // OBP0/1 = 0xD8 (11 01 10 00): Sprite Color 0 is Transparent, 1 is Dark Gray (body), 2 is Light Gray, 3 is Black (outlines)
    OBP0_REG = 0xD8;
    OBP1_REG = 0xD8;
#endif
```

---

## 5. E2E/Unit Verification Design

### A. Code Pipeline Unit Tests (`tests/test_graphics_pipeline.py`)
Our inspection reveals that `tests/test_graphics_pipeline.py` already includes robust validation for **both** modes:
1.  **Light Mode Verification**: `test_independent_tile_decoding` decodes all 32 tiles using the Classic DMG palette and validates them pixel-for-pixel.
2.  **Dark Mode Verification**: The same test contains a dedicated segment that calls the decoder with `use_dark_floor=True` and validates against the Atmospheric palette pixel-for-pixel.
3.  **Audit Generation**: `test_nearest_neighbor_upscaling` runs the generator tool twice (with and without `--dark-floor`) and verifies that both `graphics_audit.png` and `graphics_audit_dark.png` are cleanly generated and use exact nearest-neighbor scaling (zero blur/antialiasing).

### B. Dynamic ROM E2E Tests (`tests/verify_emulator.py`)
To test that both compiled ROMs boot up, run, and accept inputs without crashing on actual emulator hardware, we propose parameterizing `tests/verify_emulator.py`.

#### Proposed Change in `tests/verify_emulator.py`:
Change lines 11-12 to:
```python
        # Resolve ROM path, allowing override via environment variable
        cls.rom_path = os.environ.get("ROM_PATH", os.path.normpath(os.path.join(cls.current_dir, "../bin/dandy.gb")))
        cls.map_path = os.path.splitext(cls.rom_path)[0] + ".map"
```
This single change allows running the exact same emulator test suite against either ROM by setting the `ROM_PATH` environment variable.

---

## 6. Step-by-Step Verification Pipeline Design
The step-by-step verification pipeline ensures complete build and test coverage for both modes with zero risk of regressions.

### Pipeline Execution Order:
1.  **Clean up previous builds**:
    ```bash
    make clean
    ```
2.  **Run Pipeline Unit Tests**:
    Extracts original sprites, parses `tiles.c`, verifies 2bpp decoding for both palettes, and generates both visual audit sheets:
    ```bash
    make test
    ```
    This verifies the Python pipeline and generates:
    -   `teamwork_graphics/graphics_audit.png` (Classic DMG sheet)
    -   `teamwork_graphics/graphics_audit_dark.png` (Atmospheric Dark sheet)

3.  **Compile Both ROMs**:
    -   Compile Classic DMG ROM:
        ```bash
        make
        ```
        Creates `bin/dandy.gb` using objects in `obj/`.
    -   Compile Atmospheric Dark ROM:
        ```bash
        make dark
        ```
        Creates `bin/dandy_dark.gb` using objects in `obj_dark/`.

4.  **Run Emulator E2E Tests on Both ROMs**:
    -   Test Classic DMG ROM:
        ```bash
        ROM_PATH=bin/dandy.gb .venv/bin/python -m unittest tests/verify_emulator.py
        ```
    -   Test Atmospheric Dark ROM:
        ```bash
        ROM_PATH=bin/dandy_dark.gb .venv/bin/python -m unittest tests/verify_emulator.py
        ```

### Automation Integration in `Makefile`
We can automate the emulator E2E step inside the `Makefile` by updating the `test_emu` target:
```makefile
test_emu: all dark
	@if [ ! -d ".venv" ]; then \
		echo "Creating virtual environment and installing PyBoy..."; \
		/usr/local/google/home/jackpal/.local/bin/uv venv && \
		/usr/local/google/home/jackpal/.local/bin/uv pip install --index-url https://pypi.org/simple --python .venv/bin/python pyboy numpy pillow; \
	fi
	@echo "----------------------------------------"
	@echo "Running PyBoy E2E tests: Classic DMG..."
	@echo "----------------------------------------"
	ROM_PATH=bin/dandy.gb .venv/bin/python -m unittest tests/verify_emulator.py
	@echo "----------------------------------------"
	@echo "Running PyBoy E2E tests: Atmospheric Dark..."
	@echo "----------------------------------------"
	ROM_PATH=bin/dandy_dark.gb .venv/bin/python -m unittest tests/verify_emulator.py
```

With this update, running `make test_emu` will:
1.  Compile `bin/dandy.gb` (Classic DMG) into `obj/`.
2.  Compile `bin/dandy_dark.gb` (Atmospheric Dark) into `obj_dark/`.
3.  Execute PyBoy E2E tests on `bin/dandy.gb`.
4.  Execute PyBoy E2E tests on `bin/dandy_dark.gb`.
This ensures robust, automated, zero-regression guarantees for both rendering modes!
