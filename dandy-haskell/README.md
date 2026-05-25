# Haskell Dandy Dungeon WASM Port

This directory contains a complete high-fidelity implementation of the Dandy Dungeon game ported to Haskell WebAssembly (Wasm).

## Architecture Summary
1. **Shared Memory Platform-Independent Engine (SM-PIE)**: Zero-copy structure sharing GHC Wasm heap pointers to the flat RGBA framebuffer and metrics array to browser shim inputs.
2. **Template Haskell Asset Injection**: Assets (levels A-Z and spritesheet `dandy.bmp`) are read at compile time and packed into the Wasm binary.
3. **4-Player Co-Op**: Dynamic hot-joining on any input tick for Players 2, 3, and 4.
4. **HTML5 Gamepad API & Controls**: Polled inside browser loops, mapping active controllers to Player 3 & 4, complete with analog stick deadzones. Responsive arcade HUD displays active statistics.
5. **Physical Engine**: Corner-sliding diagonal physics, self-resurrections via hearts, staggered rotor enemy AI updates, viewport smart bombs, and CPU-saving sleep mode.

## How to Build the Game
Execute the automated compilation script:
```bash
./build.sh
```
This compiles the reactor module and exports the optimized `dandy-haskell.wasm` to the web directory (`web/dandy-haskell.wasm`).

## How to Run the Web Game
Fire up a local HTTP server in the `web/` directory:
```bash
python3 -m http.server 8000 --directory web
```
Navigate to `http://localhost:8000/` in your browser.

## How to Run the Haskell Test Suite
We have built a comprehensive, high-fidelity standalone testing suite in `src/TestMain.hs`.

To compile and run:
1. Source GHC Wasm env:
   ```bash
   source ~/.ghc-wasm/env
   ```
2. Build the test target:
   ```bash
   wasm32-wasi-cabal build dandy-haskell-test
   ```
3. Execute it using Wasmtime:
   ```bash
   wasmtime $(wasm32-wasi-cabal list-bin exe:dandy-haskell-test)
   ```

All assertions will execute and pass cleanly:
```
Running Haskell Dandy Dungeon Test Suite...
PASS: Players count is 4
PASS: P1 active
...
PASS: can sleep when ghost is blocked
Tests Complete!
```
