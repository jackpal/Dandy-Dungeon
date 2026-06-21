# Default GBDKDIR to the user's local path if not set in the environment.
# GBDK-2020 requires GBDKDIR to end with a trailing slash to resolve sdcc correctly.
GBDKDIR ?= $(HOME)/Developer/gbdk/
export GBDKDIR

# Compiler and Linker
LCC = $(GBDKDIR)bin/lcc

# Target ROM Name & Directories configuration based on mode
ifeq ($(USE_BLACK_FLOOR),1)
ROM_NAME = dandy_dark.gb
OBJ_DIR = obj_dark
CFLAGS_MODE = -DUSE_BLACK_FLOOR
TILES_SRC = src/tiles_dark.c
TILES_HDR = src/tiles_dark.h
else
ROM_NAME = dandy.gb
OBJ_DIR = obj
CFLAGS_MODE =
TILES_SRC = src/tiles_light.c
TILES_HDR = src/tiles_light.h
endif


# Directories
SRC_DIR = src
BIN_DIR = bin
TOOLS_DIR = tools

# Source and Object Files
SRCS = $(SRC_DIR)/main.c $(SRC_DIR)/dandy_core.c $(SRC_DIR)/gameboy_hal.c
OBJS = $(OBJ_DIR)/main.o $(OBJ_DIR)/dandy_core.o $(OBJ_DIR)/gameboy_hal.o $(OBJ_DIR)/levels.o $(OBJ_DIR)/tiles.o

# Flags
# -Wa-l: Generate assembler list file
# -Wl-m: Generate linker map file
LCCFLAGS = -Wa-l -Wl-m -Wl-yo2

.PHONY: all clean levels sprites setup web dark

# Default target
all: setup $(BIN_DIR)/$(ROM_NAME)

# Dedicated target for Atmospheric Dark Mode
dark:
	$(MAKE) USE_BLACK_FLOOR=1 all

# Create necessary directories as actual file targets (parallel-safe)
$(OBJ_DIR) $(BIN_DIR) $(WEB_DIR):
	@mkdir -p $@

# Phony target for convenience
setup: $(OBJ_DIR) $(BIN_DIR) $(WEB_DIR)

# Link the ROM, ensuring bin directory exists
$(BIN_DIR)/$(ROM_NAME): $(OBJS) | $(BIN_DIR)
	$(LCC) $(LCCFLAGS) -o $@ $(OBJS)
	@echo "----------------------------------------"
	@echo "Build successful: $@"
	@echo "----------------------------------------"

# Compile C source files, ensuring object directory exists first
$(OBJS): | $(OBJ_DIR)

$(OBJ_DIR)/%.o: $(SRC_DIR)/%.c
	$(LCC) -Wf--opt-code-size $(CFLAGS_MODE) -c -o $@ $<


# Run the level converter tool (requires Python 3)
src/levels.c src/levels.h &: $(TOOLS_DIR)/convert_levels.py ../dandy-js/levels.js
	@echo "Converting levels from JS to C header..."
	flock .levels.lock python3 $(TOOLS_DIR)/convert_levels.py

levels: src/levels.c src/levels.h

# Bootstrap virtual environment for Python tools
.venv:
	@if [ ! -d ".venv" ]; then \
		echo "Creating virtual environment..."; \
		/usr/local/google/home/jackpal/.local/bin/uv venv && \
		/usr/local/google/home/jackpal/.local/bin/uv pip install --index-url https://pypi.org/simple --python .venv/bin/python numpy pillow pyboy; \
	fi

# Run the clean PNG sprite compiler for both light and dark assets (parallel-safe grouped targets)
src/tiles_light.c src/tiles_light.h &: teamwork_graphics/tiles_light.png | .venv
	@echo "Compiling light sprite assets..."
	flock .sprites.lock .venv/bin/python $(TOOLS_DIR)/compile_png_tiles.py --input $< --output-c src/tiles_light.c --output-h src/tiles_light.h --name dandy_tiles_light

src/tiles_dark.c src/tiles_dark.h &: teamwork_graphics/tiles_dark.png | .venv
	@echo "Compiling dark sprite assets..."
	flock .sprites.lock .venv/bin/python $(TOOLS_DIR)/compile_png_tiles.py --input $< --output-c src/tiles_dark.c --output-h src/tiles_dark.h --name dandy_tiles_dark

sprites: src/tiles_light.c src/tiles_dark.c


# WebAssembly Emscripten Compiler
EMCC = emcc
WEB_DIR = web
WEB_OUT = $(WEB_DIR)/dandy_web.js

# Compile Core C engine to WebAssembly
web: levels
	@if command -v $(EMCC) >/dev/null 2>&1; then \
		echo "Compiling WebAssembly core engine..."; \
		$(EMCC) $(SRC_DIR)/dandy_core.c $(SRC_DIR)/web_main.c \
			-I$(SRC_DIR) \
			-s WASM=1 \
			-s EXPORTED_FUNCTIONS="['_web_init', '_web_step', '_web_draw_viewports', '_web_get_current_level', '_web_get_num_players', '_web_get_map', '_malloc', '_free']" \
			-s EXPORTED_RUNTIME_METHODS="['ccall', 'cwrap', 'HEAPU8']" \
			-O2 \
			-o $(WEB_OUT); \
		echo "----------------------------------------"; \
		echo "WebAssembly compilation successful!"; \
		echo "Open $(WEB_DIR)/index.html via a local server to play."; \
		echo "E.g., python3 -m http.server -d $(WEB_DIR)"; \
		echo "----------------------------------------"; \
	else \
		echo "Error: Emscripten compiler '$(EMCC)' not found in PATH."; \
		echo "Please install Emscripten (emsdk) and source 'emsdk_env.sh'."; \
		echo "See README.md for detailed instructions."; \
		exit 1; \
	fi

$(OBJ_DIR)/levels.o: src/levels.c src/levels.h
	$(LCC) -Wf-bo1 $(CFLAGS_MODE) -c -o $@ $<

$(OBJ_DIR)/tiles.o: $(TILES_SRC) $(TILES_HDR)
	$(LCC) -Wf--opt-code-size $(CFLAGS_MODE) -c -o $@ $<

$(OBJ_DIR)/main.o: $(TILES_HDR)
$(OBJ_DIR)/dandy_core.o: src/levels.h


clean:
	rm -rf obj obj_dark bin
	rm -f src/levels.c src/levels.h src/tiles_light.c src/tiles_light.h src/tiles_dark.c src/tiles_dark.h
	rm -f *.lst *.map *.sym
	rm -rf tests/.temp_envs
	rm -f libdandy_test.so
	rm -f teamwork_graphics/graphics_audit.png teamwork_graphics/graphics_audit_dark.png
	rm -f .levels.lock .sprites.lock
	@echo "Clean complete."

# --- Host Compilation and Testing for Offline E2E Harness ---
.PHONY: test_lib test

test_lib: levels sprites
	gcc -fPIC -shared -O2 -Isrc -Itests/mock_gb -o libdandy_test.so \
		src/dandy_core.c \
		src/levels.c \
		tests/mock_hal.c

test: all test_lib | .venv
	.venv/bin/python -m unittest discover -s tests -p "test_*.py"

# --- Programmatic GameBoy ROM Emulator Testing (PyBoy) ---
.PHONY: test_emu

test_emu: all dark | .venv
	@echo "----------------------------------------"
	@echo "Running PyBoy automated emulator E2E tests: Classic DMG..."
	@echo "----------------------------------------"
	ROM_PATH=bin/dandy.gb .venv/bin/python -m unittest tests/verify_emulator.py
	@echo "----------------------------------------"
	@echo "Running PyBoy automated emulator E2E tests: Atmospheric Dark..."
	@echo "----------------------------------------"
	ROM_PATH=bin/dandy_dark.gb .venv/bin/python -m unittest tests/verify_emulator.py

