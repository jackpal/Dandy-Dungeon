# Dandy Dungeon GameBoy Makefile
# Requires GBDK-2020 (lcc compiler) in PATH

# Compiler and Linker
LCC = lcc

# Target ROM Name
ROM_NAME = dandy.gb

# Directories
SRC_DIR = src
OBJ_DIR = obj
BIN_DIR = bin
TOOLS_DIR = tools

# Source and Object Files
SRCS = $(SRC_DIR)/main.c $(SRC_DIR)/dandy_core.c $(SRC_DIR)/gameboy_hal.c
OBJS = $(OBJ_DIR)/main.o $(OBJ_DIR)/dandy_core.o $(OBJ_DIR)/gameboy_hal.o

# Flags
# -Wa-l: Generate assembler list file
# -Wl-m: Generate linker map file
LCCFLAGS = -Wa-l -Wl-m

.PHONY: all clean levels sprites setup web

# Default target
all: setup levels $(BIN_DIR)/$(ROM_NAME)

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
	$(LCC) -c -o $@ $<

# Run the level converter tool (requires Python 3)
levels:
	@echo "Converting levels from JS to C header..."
	python3 $(TOOLS_DIR)/convert_levels.py

# Run the sprite extractor tool (requires Python 3)
sprites:
	@echo "Extracting original spritesheet..."
	python3 $(TOOLS_DIR)/extract_sprites.py

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

# Clean intermediate and output files
clean:
	rm -rf $(OBJ_DIR) $(BIN_DIR)
	rm -f $(WEB_DIR)/*.js $(WEB_DIR)/*.wasm
	rm -f *.lst *.map *.sym
	@echo "Clean complete."
