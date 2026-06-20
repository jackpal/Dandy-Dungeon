# Dandy Dungeon: GameBoy Port & Demake (ASCII Prototype)

This directory contains a retro port and demake of **Dandy Dungeon** for the Nintendo GameBoy, written in highly optimized, portable C using the GBDK-2020 toolchain.

## Current State: Playable ASCII Prototype
To facilitate immediate testing of the core game engine without waiting for custom 8x8 pixel artwork, this prototype renders the game viewport using the GameBoy's built-in font as **ASCII art**:
*   **Walls** render as `*`
*   **Doors** render as `D` (which open recursively when you use a key!)
*   **Keys** render as `K`
*   **Food** (Health) renders as `F`
*   **Money** (Score) renders as `$`
*   **Smart Bombs** render as `B`
*   **Monsters** render as `1`, `2`, and `3` (representing different difficulty tiers)
*   **Generators** render as `g`, `o`, and `q` (which spawn monsters randomly)
*   **Player & Arrows** render as directional arrow characters (`^`, `>`, `v`, `<`) showing exactly which way you are facing!

A fully detailed HUD is displayed at the bottom of the screen showing your Score, Health, Keys, Bombs, and current Level.

---

## Technical Features & Retro Optimizations
The game engine has been written from the ground up with strict performance and memory constraints in mind, ideal for 8-bit CPUs (like the GameBoy's Sharp LR35902 and the NES/C64's 6502):
1.  **Iterative Flood Fill (No Recursion)**: Designed a non-recursive 8-way flood fill using parallel 8-bit stack arrays, consuming just **128 bytes of RAM** and avoiding stack overflow crashes.
2.  **Immediate Frontier Marking**: Optimized the DFS flood fill to mark tiles as visited immediately upon pushing, bounding stack size to the frontier perimeter rather than the fill area.
3.  **Zero-Multiplication Coordinate Mapping (LUT)**: Implemented a ROM-based Look-Up Table (LUT) mapping coordinates to flat map indices, completely avoiding slow multiplication.
4.  **Galois LFSR PRNG**: Uses an ultra-fast 16-bit shift register pseudo-random number generator for spawning monsters.
5.  **Sparse Monster Scanning**: Inherited the original game's brilliant optimization: scanning and updating only a sparse grid of monsters (1/16th of the viewport) per frame, keeping the game at a locked 60fps.
6.  **Direct VRAM Updates & Zero `sprintf`**: Overwrote background VRAM tile indexes directly and wrote lightweight custom formatting helpers to avoid the heavy code bloat of `sprintf`.

---

## How to Build

### Prerequisites
1.  **Python 3**: Required to run the level conversion and sprite extraction scripts.
2.  **GBDK-2020**: You must have GBDK-2020 installed and the `lcc` compiler in your system `PATH`.
    *   *Installation Tip*: Download the `gbdk-linux64.tar.gz` (or `gbdk-linux-arm64.tar.gz`) package from the [official releases](https://github.com/gbdk-2020/gbdk-2020/releases), extract it to your home directory, and add `~/gbdk/bin` to your `PATH`.

### Build Commands
Run these commands from the `dandy-gb` directory:

*   **Build the ROM**:
    ```bash
    make
    ```
    This will compile the game and generate the GameBoy ROM at **`bin/dandy.gb`**.
    
*   **Reconvert Levels**:
    ```bash
    make levels
    ```
    Parses `dandy-js/levels.js` and updates `src/levels.h` with the 26 level maps.
    
*   **Extract Sprites**:
    ```bash
    make sprites
    ```
    Decodes the base64 spritesheet from the JS version and saves it as a PNG reference at `assets/strike_original.png`.
    
*   **Clean Build Files**:
    ```bash
    make clean
    ```
    Deletes the temporary object files and compiled ROM.

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
