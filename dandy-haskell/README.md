# Haskell Dandy Dungeon WASM Port

This directory contains a complete high-fidelity implementation of the Dandy Dungeon game ported to Haskell WebAssembly (Wasm).

## Architecture Summary
1. **Shared Memory Platform-Independent Engine (SM-PIE)**: Zero-copy structure sharing GHC Wasm heap pointers to the flat RGBA framebuffer and metrics array to browser shim inputs.
2. **Template Haskell Asset Injection**: Assets (levels A-Z and spritesheet `dandy.bmp`) are read at compile time and packed into the Wasm binary.
3. **4-Player Co-Op**: Dynamic hot-joining on any input tick for Players 2, 3, and 4.
4. **HTML5 Gamepad API & Controls**: Polled inside browser loops, mapping active controllers to Player 3 & 4, complete with analog stick deadzones. Responsive arcade HUD displays active statistics.
5. **Physical Engine**: Corner-sliding diagonal physics, self-resurrections via hearts, staggered rotor enemy AI updates, viewport smart bombs, and CPU-saving sleep mode.

## Prerequisites

To build and run the Haskell WebAssembly target and its standalone test suite, you need the GHC Wasm toolchain installed in your user space.

### 1. System Dependencies (Linux/Debian/Ubuntu)
Ensure you have the necessary system utilities and compiler tools installed:
```bash
sudo apt install build-essential curl libffi-dev libffi8 libgmp-dev libgmp10 libncurses-dev libncurses6 libtinfo6 pkg-config jq unzip zstd git
```

### 2. Install GHCup
If you don't have GHCup installed, install it in minimal mode:
```bash
export BOOTSTRAP_HASKELL_NONINTERACTIVE=1
export BOOTSTRAP_HASKELL_MINIMAL=1
curl --proto '=https' --tlsv1.2 -sSf https://get-ghcup.haskell.org | sh
source ~/.ghcup/env
```

### 3. Install GHC Wasm Toolchain
Clone and run the `ghc-wasm-meta` installer script to set up GHC WASM bindists, wasi-sdk, cabal wrappers, and Wasmtime under `~/.ghc-wasm/`:
```bash
git clone https://gitlab.haskell.org/ghc/ghc-wasm-meta.git
cd ghc-wasm-meta
./setup.sh
```
*Note: You can set the GHC version using `export FLAVOUR=9.8` before running `./setup.sh` for a very stable target, or let it default to GHC 9.14.*

After successful installation, add the Wasm tools to your environment path:
```bash
source ~/.ghc-wasm/env
```

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

### Remote Development (SSH Port Forwarding)
If you are building on a remote Linux machine but want to play the game in a browser on your local computer (e.g., a Mac), you can forward the port over SSH. It is highly recommended to use `127.0.0.1` instead of `localhost` for the remote target, as `localhost` might resolve to IPv6 (`::1`) on the remote host while the Python server binds to IPv4 (`0.0.0.0`):
```bash
ssh -L 8000:127.0.0.1:8000 username@remote-linux-box-ip
```
Once connected, you can open and play the game at `http://localhost:8000/` on your local browser.

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
