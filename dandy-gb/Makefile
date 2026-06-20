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

.PHONY: all clean levels sprites setup

# Default target
all: setup levels $(BIN_DIR)/$(ROM_NAME)

# Create necessary directories
setup:
	@mkdir -p $(OBJ_DIR)
	@mkdir -p $(BIN_DIR)

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

# Clean intermediate and output files
clean:
	rm -rf $(OBJ_DIR) $(BIN_DIR)
	rm -f *.lst *.map *.sym
	@echo "Clean complete."
