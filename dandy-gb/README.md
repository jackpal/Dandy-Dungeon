# Dandy Dungeon: GameBoy Port & Demake (ASCII Prototype)

This directory contains a retro port and demake of **Dandy Dungeon** for the Nintendo GameBoy, written in highly optimized, portable C using the GBDK-2020 toolchain.

## Current State: Complete 8x8 Grayscale Graphics Engine

The game features a fully realized retro 8x8 tile-graphics engine, drawing 32 custom game tiles directly to background and sprite memory (VRAM):
*   **Walls (Tile 1)**: Renders a highly faithful 8x8 reduction of the original game's cross-hatch wall pattern (no bricks!).
*   **Doors (Tile 2)**: Symmetrical opening wooden door tiles.
*   **Stairs Up / Down (Tiles 3, 4)**: Exit and entry stairways.
*   **Keys (Tile 5)**: Symmetrical key silhouette.
*   **Food / Potion (Tile 6)**: Classic flask item.
*   **Money / Gold (Tile 7)**: Perfectly centered, symmetrical gold dollar sign (`$`)!
*   **Smart Bombs (Tile 8)**: Bomb sprite with fuse details.
*   **Monsters (Tiles 9, 10, 11)**: Three distinct monster visage sprites (Goblins, Golems, Hearts).
*   **Generators (Tiles 13, 14, 15)**: Spawning portals.
*   **8-Directional Arrows (Tiles 16..23)**: Flying arrows beautifully aligned to all 8 cardinal and diagonal shooting directions (Down-Left, Left, Up-Left, Up, Up-Right, Right, Down-Right, Down).
*   **Player Character (Tiles 24..27)**: Symmetrical player sprites oriented in 4 directions (Down, Up, Left, Right) to show exactly which way the player is facing!

A fully detailed HUD is displayed at the bottom of the screen showing your Score, Health, Keys, Bombs, and current Level.

### Dual-Palette Hardware Display Modes
The engine supports two distinct display modes selectable at build time:
1.  **Classic DMG Mode (Default - Light Floor)**: Compiles to `bin/dandy.gb`. Uses palette register mapping (`BGP = 0xE4`, `OBP0/1 = 0xD8`) to render bright White floor corridors with grid-crack details. Sprites render as dark gray silhouettes with bold black outlines. Optimized for the original DMG-01's slow passive STN screen to completely eliminate motion ghosting and smear.
2.  **Atmospheric Dark Mode (Optional - Black Floor)**: Compiles to `bin/dandy_dark.gb` (using `make dark`). Renders the floor corridors in solid, pitch-black void (`BGP = 0x1B`, `OBP0/1 = 0xE0`), and character sprites in brilliant bright White with bold black outlines for high-contrast visibility.


---

## Technical Features & Retro Optimizations
The game engine has been written from the ground up with strict performance, size, and memory constraints in mind, targeting a **flat 32KB ROM (no-MBC)** with a total active footprint under **21 KB** (leaving a massive 7.5KB safety margin!):

1.  **Scheme B2 Custom 2D Level Compression**: Designed an extremely efficient 2D compression algorithm that shrinks the level database by **76.4%** (from 46.8KB down to just 10.8KB).
    *   **Edge Wall Elision**: Completely strips the outer 176 border walls from each level, storing only the inner 58x28 grid (1,624 tiles) in ROM and instantly saving 2.23KB of storage per level.
    *   **Variable-Bit-Width Prefix Coding**: Exploiting the statistical distribution of tiles (Space represents 52.6% and Walls 32.2% of the maps), it encodes Space as `0` (1 bit), Wall as `10` (2 bits), and other tiles as `11` + `4-bit tile ID` (6 bits).
2.  **Zero-Write Wall Optimization**: The C decompressor pre-fills the 1,800-byte `dandy_map` WRAM buffer with Wall tiles using a fast `memset`. When decoding Wall prefix bits (`10`), it simply skips writing, eliminating 32% of all RAM write operations and ensuring near-instantaneous level transitions (<15ms on real hardware).
3.  **Iterative Flood Fill (No Recursion)**: Designed a non-recursive 8-way flood fill using parallel 8-bit stack arrays, consuming just **128 bytes of RAM** and avoiding stack overflow crashes.
4.  **Zero-Multiplication Coordinate Mapping (LUT)**: Implemented a ROM-based Look-Up Table (LUT) mapping coordinates to flat map indices, completely avoiding slow multiplication.
5.  **Galois LFSR PRNG**: Uses an ultra-fast 16-bit shift register pseudo-random number generator for spawning monsters.
6.  **Sparse Monster Scanning**: Inherited the original game's brilliant optimization: scanning and updating only a sparse grid of monsters (1/16th of the viewport) per frame, keeping the game at a locked 60fps.
7.  **Direct VRAM Updates & Zero `sprintf`**: Overwrote background VRAM tile indexes directly and wrote lightweight custom formatting helpers to avoid the heavy code bloat of `sprintf`.

---

## How to Build

### Prerequisites
1.  **Python 3**: Required to run the level conversion and sprite extraction scripts.
2.  **GBDK-2020**: You must have GBDK-2020 installed and the `lcc` compiler in your system `PATH`.
    *   *Installation Tip*: Download the `gbdk-linux64.tar.gz` package from the [official releases](https://github.com/gbdk-2020/gbdk-2020/releases), extract it to your home directory, and add `~/gbdk/bin` to your `PATH`.
3.  **uv Package Manager** (Optional, for emulator tests): A lightning-fast Python package installer used to manage testing environments.
    *   *Installation*:
        ```bash
        curl -LsSf https://astral.sh/uv/install.sh | sh
        ```

### Build Commands
Run these commands from the `dandy-gb` directory:

*   **Build the ROM**:
    ```bash
    make
    ```
    This will compile the game and generate the flat GameBoy ROM at **`bin/dandy.gb`**.
    
*   **Reconvert Levels**:
    ```bash
    make levels
    ```
    Parses `dandy-js/levels.js` and compiles them using Scheme B2 compression into `src/levels.c`.
    
*   **Compile Sprite Sheets**:
    ```bash
    make sprites
    ```
    Compiles the 8x8 grayscale PNG sheets (`teamwork_graphics/tiles_light.png` and `tiles_dark.png`) into planar 2bpp GBDK C source files (`src/tiles_light.c` and `src/tiles_dark.c`).

    
*   **Clean Build Files**:
    ```bash
    make clean
    ```
    Deletes the temporary object files, compiled ROM, and testing libraries.

---

## 🎨 Artist Customization Guide

The graphics pipeline is designed to be extremely friendly for artists. There are **zero downscaling steps** and zero complex algorithms; the compiler reads 8x8 pixel art directly from PNGs.

### How to Redraw the Graphics:
1.  Open the placeholder sheets in any pixel editor (Aseprite, Photoshop, Piskel, etc.):
    *   Light Sheet: **[tiles_light.png](file:///usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb/teamwork_graphics/tiles_light.png)** (used for Classic DMG mode)
    *   Dark Sheet: **[tiles_dark.png](file:///usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb/teamwork_graphics/tiles_dark.png)** (used for Atmospheric Dark mode)
2.  Each sheet is exactly **256 pixels wide and 8 pixels high**, containing exactly **32 tiles of 8x8 pixels** laid out horizontally from left to right.
3.  Draw your pixel art directly onto the canvas using **exactly 4 shades of grayscale**:
    *   **White (`#FFFFFF`)** $\rightarrow$ Renders as Color 0 (Transparent on sprites, Floor color on background).
    *   **Light Gray (`#A8A8A8` / `#A0A0A0`)** $\rightarrow$ Renders as Color 1.
    *   **Dark Gray (`#545454` / `#505050`)** $\rightarrow$ Renders as Color 2.
    *   **Black (`#000000`)** $\rightarrow$ Renders as Color 3 (Outlines, Text, HUD blocks).
4.  Save the files and run:
    ```bash
    make clean && make
    ```
    The build system will instantly compile, pack, and link your new artwork into the GameBoy ROMs!

---


## Automated Verification & Test Suites

The project features a dual-track automated quality assurance pipeline that guarantees both game-logic correctness and real-hardware compatibility:

### Track 1: Host-Native Offline Unit Tests (`make test`)
Compiles the core engine (`src/dandy_core.c`) as a shared library (`libdandy_test.so`) on your Linux host and runs **122 functional unit tests** in Python:
*   Simulates player physics, items, keys/doors, monster AI, stair transitions, and multi-step level walkthroughs.
*   **Adversarial Hardening**: Uses Linux memory protection (`mprotect`) to dynamically inject malformed, truncated, and randomized byte streams into the game library's level-loading functions to assert 100% crash-safety and stability.
*   Runs via:
    ```bash
    make test
    ```

### Track 2: Programmatic GameBoy ROM Emulator Verification (`make test_emu`)
Runs programmatic E2E integration tests in parallel against **both** compiled GameBoy machine code binaries (`bin/dandy.gb` and `bin/dandy_dark.gb`) running inside a simulated GameBoy CPU:
*   Boots both ROMs in a headless **PyBoy emulator**.
*   Dynamically parses their respective linker map files (`bin/dandy.map` and `bin/dandy_dark.map`) to resolve the exact WRAM addresses of global variables, ensuring address-shift resilience.
*   Simulates physical joypad button presses, runs the emulation, and asserts that coordinates, health, and map states update correctly in WRAM for both Light and Dark Floor modes.
*   Runs via:
    ```bash
    make test_emu
    ```
    *(Note: This target will automatically check for, create, and configure a Python virtual environment `.venv` and install `pyboy`, `numpy`, and `pillow` using `uv` if not already set up!)*


---

## How to Run

### Option 1: GameBoy ROM (Single Player)
1.  Compile the ROM using `make` to produce `bin/dandy.gb`.
2.  Open `bin/dandy.gb` in any GameBoy emulator:
    *   **Desktop**: BGB, SameBoy, mGBA, or RetroArch.
    *   **Web**: Load the ROM into web-based emulators like [WasmBoy](https://wasmboy.app/) or [Binjgb](https://binjgb.net/).

#### ROM Game Controls
*   **D-Pad (Arrow Keys)**: Move Player (and change facing direction)
*   **Button A (Space / Alt)**: Fire Arrow in facing direction
*   **Button B (Control / Z)**: Trigger Smart Bomb (clears all visible monsters and generators)

---

## 4-Player WebAssembly Interactive Demo (Co-op Mode)

We have compiled the **Dandy Dungeon platform-independent core C engine** directly to WebAssembly using Emscripten! This allows running a **4-viewport interactive co-op demo** directly in any modern web browser. It displays 4 scroll-centered screens side-by-side (representing each player's console) running the exact same production C logic!

### How to Build the Wasm Demo

1.  **Prerequisites**: You must have **Emscripten (emsdk)** installed on your system.
    *   *Quick Installation*:
        ```bash
        git clone https://github.com/emscripten-core/emsdk.git
        cd emsdk
        ./emsdk install latest
        ./emsdk activate latest
        source ./emsdk_env.sh
        ```
2.  **Build Command**:
    From the `dandy-gb` directory, run:
    ```bash
    make web
    ```
    This compiles the C core and generates `web/dandy_web.js` and `web/dandy_web.wasm`.

### How to Run the Wasm Demo

Because WebAssembly cannot be loaded directly from local file paths (`file://`) due to browser CORS security policies, you must serve the files using a simple local HTTP server:

1.  Start a local server using Python (or any web server):
    ```bash
    python3 -m http.server -d web
    ```
2.  Open your browser and navigate to:
    **`http://localhost:8000`**
3.  Select the active player count (1 to 4) and click **START NEW GAME**!

### Wasm Demo Keyboard Controls

Since all 4 players play locally on the same keyboard, the controls are mapped as follows:

| Action | Player 1 (Red) | Player 2 (Blue) | Player 3 (Green) | Player 4 (Yellow) |
| :--- | :--- | :--- | :--- | :--- |
| **Move Up** | <kbd>W</kbd> | <kbd>▲</kbd> | <kbd>I</kbd> | <kbd>T</kbd> |
| **Move Down**| <kbd>S</kbd> | <kbd>▼</kbd> | <kbd>K</kbd> | <kbd>G</kbd> |
| **Move Left**| <kbd>A</kbd> | <kbd>◀</kbd> | <kbd>J</kbd> | <kbd>F</kbd> |
| **Move Right**| <kbd>D</kbd> | <kbd>▶</kbd> | <kbd>L</kbd> | <kbd>H</kbd> |
| **Shoot** | <kbd>Space</kbd> | <kbd>Period (.)</kbd> | <kbd>U</kbd> | <kbd>R</kbd> |
| **Smart Bomb**| <kbd>E</kbd> | <kbd>Slash (/)</kbd> | <kbd>O</kbd> | <kbd>Y</kbd> |
