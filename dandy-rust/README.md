# Dandy Dungeon - Rust Web & Online P2P Multiplayer Port

A high-performance, web-playable WebAssembly (WASM) port of the classic cooperative 2D overhead dungeon crawler **Dandy Dungeon** in Rust, served via **Trunk**.

Features full **4-player serverless P2P co-op** powered by **WebRTC DataChannels** and a **deterministic rollback netcode engine** built from scratch in Rust with zero runtime heap allocations.

---

## Features & Architecture

### 1. Shared Memory Platform-Independent Engine (SM-PIE)
*   **Pure Rust Simulation**: The simulation core has zero browser or DOM dependencies (`web-sys` is isolated to entry points).
*   **Zero-Copy Memory Sharing**: JavaScript reads pixel buffers and HUD statistics directly from WASM linear memory (`Uint8ClampedArray` over `wasmInstance.memory.buffer`) without heap churn or serialization overhead.
*   **Sub-Microsecond Frame Latency**: Simulation throughput exceeds **17,500 FPS** (`~56 µs/frame`), with zero-copy blit rendering taking just `0.28 µs/frame`.

### 2. Serverless 4-Player P2P Co-op & Rollback Netcode
*   **4-Player Characters**:
    *   **P1**: Ruby (Red)
    *   **P2**: Sapphire (Blue)
    *   **P3**: Topaz (Yellow)
    *   **P4**: Emerald (Green)
*   **Deterministic Rollback Engine (`src/netcode.rs`)**:
    *   Maintains a 256-frame input ring buffer and 64-frame snapshot history.
    *   Zero-allocation stack snapshots (`GameSnapshot` and `Map` derive `Copy`).
    *   Predicts remote player inputs during network jitter and automatically rewinds/re-simulates ticks when late or out-of-order UDP packets arrive.
*   **Zero-Infrastructure WebRTC Lobby**:
    *   Direct peer-to-peer data channels via public Google STUN (`stun:stun.l.google.com:19302`).
    *   Shareable room URLs (`#room=...`) for one-click pairing.
    *   Host-relayed star topology for 3–4 player sessions.
    *   Manual SDP copy-paste fallback for symmetric corporate NATs.

### 3. Mobile & Touch Friendly
*   **Virtual Multi-Touch D-Pad**: High-responsiveness on-screen D-pad and action buttons for phones and tablets.
*   **Adaptive Viewport**: Uses CSS `image-rendering: pixelated;` to scale native retro resolution cleanly across any screen size.
*   **Event-Driven Idle Sleep**: Automatically suspends frame rendering when game state is static, conserving battery on mobile devices.

---

## Prerequisites

Ensure you have the Rust toolchain, Node.js (for parity tests), and Trunk installed:

1.  **Add the WASM Target**:
    ```bash
    rustup target add wasm32-unknown-unknown
    ```

2.  **Install Trunk**:
    ```bash
    cargo install trunk
    ```

3.  *(Optional but recommended)* **Install `wasm-opt`** (Binaryen) for release size optimizations:
    ```bash
    # Debian/Ubuntu:
    sudo apt install binaryen
    # macOS:
    brew install binaryen
    ```

---

## Build and Run

### Local Development Server

1.  Navigate to the `dandy-rust` directory:
    ```bash
    cd dandy-rust
    ```

2.  Start the live development server:
    ```bash
    trunk serve
    ```

3.  Open your browser at:
    ```
    http://127.0.0.1:8080
    ```

Trunk will watch your source files, recompile WASM, and hot-reload on changes.

### Release Build with Size Ratchet Gate

To build the production distribution and run all automated size and parity checks:
```bash
bash build.sh
```

Static build artifacts are written to `dist/` and compressed to under **30 KB gzip**.

---

## How to Play

### Dynamic Relative Key Controls (Local & Online)

On any device (Host or Joiner), controls are dynamically assigned **relative to the local player order on that client**:

| Local Player Role | Movement (8-way) | Fire Arrow | Smart Bomb | Mobile / Touch |
|---|---|---|---|---|
| **Primary Local Player** (P1 on Host, or assigned slot on Joiner) | `Arrow Keys` | `Spacebar` | `B` | Virtual D-Pad / FIRE / BOMB Buttons |
| **2nd Local Player** (Local Hot-Join) | `W` / `A` / `S` / `D` | `F` | `G` | — |
| **3rd Local Player** (Local Hot-Join) | `I` / `J` / `K` / `L` | `O` | `P` | — |
| **4th Local Player** (Local Hot-Join) | `Numpad 8` / `4` / `5` / `6` | `Num 0` | `Num .` | — |

*Pressing any unassigned local scheme key (e.g. WASD on a Joiner who controls Sapphire via Arrow keys) dynamically hot-joins the next available room slot on that device.*

---

### HTML5 Gamepad & Controller Support (USB & Bluetooth)

Full **HTML5 Gamepad API** integration allows plug-and-play controller support across desktop and mobile browsers:

| Gamepad Input | In-Game Action | Standard Controller Mapping |
|---|---|---|
| **D-Pad (Buttons 12–15)** | Movement (8-way) | Up / Down / Left / Right directional pad |
| **Left Analog Stick (Axes 0 & 1)** | Movement (8-way) | 360° Analog control with `0.25` deadzone filtering |
| **Button 0 (A / Cross)** or **Button 7 (Right Trigger / RT / R2)** | Fire Arrow | Bottom face button or right trigger |
| **Button 1 (B / Circle)** or **Button 2 (X / Square)** | Smart Bomb | Right face button or left face button |

*   **Multi-Gamepad Local Co-op**: Connect up to 4 gamepads to a single computer. Gamepad 0 maps to Local Player 1, Gamepad 1 maps to Local Player 2, etc.
*   **Adaptive HUD & Legend Badges**: The Controls section updates dynamically upon `gamepadconnected` and `gamepaddisconnected` events (e.g. `🎮 Gamepad 1 Active`).
*   **Rollback Netcode Synchronization**: Gamepad inputs synthesize directly into local player bitmasks and synchronize peer-to-peer across WebRTC DataChannels with sub-frame determinism.

---

### Online 4-Player Co-op Instructions

#### Hosting a Game
1. Click **Host Game** in the top multiplayer bar.
2. Copy the generated **Room Link** or **Room Code** and send it to your friends.
3. As players connect, their slot cards (P2 Sapphire, P3 Topaz, P4 Emerald) will turn active in real-time.
4. Play! The rollback engine keeps all player simulations perfectly synchronized.

#### Joining a Game
1. Open the **Room Link** shared by the host, or paste the **Room Code** into the input box and click **Join Room**.
2. You will be automatically assigned the next available character slot.

#### Manual SDP Fallback (Strict Firewalls)
If playing across strict corporate firewalls where direct STUN hole-punching fails:
1. Click **Manual SDP**.
2. Follow the prompt to copy/paste the session offer and answer strings between peers.

#### In-Game Diagnostics HUD
*   **Slot Cards (P1–P4)**: Displays active player health, score, keys, and bombs.
*   **Ping (ms)**: Real-time round-trip latency to peers.
*   **Rollbacks**: Counter showing total jitter re-simulations smoothly handled by the netcode engine.

---

## Running Tests & Benchmarks

### 1. Automated Rust Unit Tests
Runs 21 unit tests covering spawning, 4-player dynamic hot-joins, level transitions, resurrection, snapshot parity, and rollback netcode:
```bash
cargo test
```

### 2. Headless Parity & Determinism Gate
Runs multi-instance headless lockstep parity verification over 1,000 frames:
```bash
node test_artifact_parity.mjs
```

### 3. Throughput & Boundary Benchmarks
Measures pure simulation speed and zero-copy boundary view access:
```bash
node bench.mjs
node abba_bench.mjs
```

---

## Remote Play (SSH Port Forwarding)

If you are running the game on a headless remote server (e.g. Cloudtop or VPS) and want to play from your local computer:

```bash
ssh -L 8080:localhost:8080 <username>@<server_host>
```

Then open `http://localhost:8080` in your local browser.
