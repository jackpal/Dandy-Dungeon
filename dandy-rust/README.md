# Dandy Dungeon - Rust Web Port

A self-contained, web-playable WebAssembly (Wasm) port of the classic cooperative 2D overhead dungeon crawler **Dandy Dungeon** in Rust, served via **Trunk**.

The engine utilizes a **Shared Memory Platform-Independent Engine (SM-PIE)** architecture that separates the core gameplay simulation (written in pure Rust) from the platform-specific orchestration and event loop (written in JavaScript).

---

## Architecture & Design

### 1. Shared Memory Platform-Independent Engine (SM-PIE)
*   **Host Separation**: The Rust Wasm core contains zero browser or DOM-manipulation dependencies (`web-sys`). It functions as a pure mathematical and physical simulation.
*   **Zero-Copy Memory Sharing**: JavaScript instantiates standard typed arrays (`Uint8ClampedArray` for pixels, `Int32Array` for stats) directly over Wasm's linear memory buffer. HUD metrics and screen pixels are read directly from memory without JSON serialization or object allocation overhead.

### 2. Software Framebuffer Blitting
*   **Low-Level Blitting (`src/graphics.rs`)**: Sprites are decoded from the embedded 24-bit BGR spritesheet (`dandy.bmp`) at startup, respecting standard DWORD row padding strides.
*   ** continuous memory segment copying**: Rendering computes horizontal and vertical viewport clipping boundaries once per tile, copying continuous row byte slices to the framebuffer using Rust's `copy_from_slice` for SIMD compilation.
*   **Single-Blit Frame**: Rust renders the visible viewport to an internal flat `320x160` RGBA pixel buffer. The JavaScript shell draws this buffer to the canvas in a single `putImageData` call per frame.
*   **Viewport Scaling**: The canvas uses CSS `image-rendering: pixelated;` to scale the native `320x160` resolution to a sharp `640x320` display.

### 3. Event-Driven Sleep Mode (Idle Engine State)
To reduce CPU and GPU usage, the game engine exposes a `can_sleep() -> bool` method. The JavaScript loop suspends rendering frame updates when the gameplay is static:
*   **Sleep Criteria**: The game is eligible to sleep if:
    1.  No control keys are pressed.
    2.  No player arrows are in flight.
    3.  The camera coordinates have converged on the active players' Center of Gravity (COG) within a threshold of `< 0.1` pixels.
    4.  All visible ghosts inside the active viewport are blocked by map geometry or arrows.
    5.  All visible generators inside the active viewport are cardinally blocked from spawning.
*   **Synchronous Wakeup**: The JS shell suspends the `requestAnimationFrame` loop when sleep is active. Pressing a registered control key triggers the `keydown` event listener, which sets `sleeping = false` and immediately resumes the frame loop.
*   **Focus Safety**: A window `blur` event listener clears active input masks and keys on focus loss, preventing infinite walking loops.

### 4. Independent Projectiles & Teammate Resurrection
*   **Stateless Arrow Stepping**: Projectile movements (`step_arrow`) tick independently of player lifecycles. An arrow continues to fly and animate even if the owner dies or escapes.
*   **Self-Resurrection**: Level progression and restarts are deferred while active arrows are in flight. If a dead player's arrow hits a `HEART` tile, the shooter is revived to `50` health at the heart's location, preventing level reload and resuming gameplay.

### 5. Generalized Inputs & Spawning
*   **Input Bitmasks**: Wasm accepts abstract inputs as a `u8` bitmask per player (`set_action(player_idx, action, pressed)`) via a logical `PlayerAction` enum. Decouples Wasm from physical keyboard key names.
*   **Spawner Offsets**: Players spawn at designated cardinal directions adjacent to the level entrance `'U'` stairs tile (Player 1: North, Player 2: East, Player 3: South, Player 4: West).
*   **4-Player Extensibility**: Spawning, ghost AI targeting, and collision loops are generalized for 4 players, allowing P3 and P4 controls or gamepads to be mapped dynamically in JavaScript.

### 6. Subsystem Decomposition (Stateless Modules)
The codebase enforces the Single Responsibility Principle (SRP) across dedicated modules:
*   `src/lib.rs`: WASM entry point, memory accessors, and BGR parser.
*   `src/game.rs`: Loop coordinator managing clock ticks, dynamic joins, level load cycles, and progression checks.
*   `src/camera.rs`: Viewport camera offset calculations, active viewport rect bounds, and player COG math.
*   `src/physics.rs`: Stateless 8-way wall-sliding movements, lock unlocking, and arrow projectile/heart resurrection physics. Accepts disjoint references (`&mut Player`, `&mut Map`).
*   `src/ai.rs`: Stateless ghost pursues tracking AI, generator spawner spawning, and sleep blocked heuristics.
*   `src/rand.rs`: Host-independent custom Linear Congruential Generator (LCG) pseudo-random number generator (`LcgRng`).

---

## Prerequisites

Ensure you have the Rust toolchain installed. You will also need the WebAssembly Wasm32 target and the Trunk bundler.

1.  **Add the WASM Target**:
    ```bash
    rustup target add wasm32-unknown-unknown
    ```

2.  **Install Trunk**:
    ```bash
    cargo install trunk
    ```

---

## Build and Run

1.  Navigate to the `dandy-rust` directory:
    ```bash
    cd dandy-rust
    ```

2.  Build and serve the application locally:
    ```bash
    trunk serve
    ```

3.  Open your browser and navigate to:
    ```
    http://127.0.0.1:8080
    ```

Trunk will automatically watch your source files, compile Wasm, and reload the browser on any changes.

To compile static release deployment files (output to `dandy-rust/dist/`):
```bash
trunk build --release
```

---

## How to Play

*   **Player 1 (Arrows)**:
    *   `Arrow Keys`: Move / Slide diagonally around corners
    *   `Spacebar`: Shoot Arrow
    *   `B` / `b`: Smart Bomb (Clears all active monsters in view)
*   **Player 2 (WASD)**:
    *   *Pressing any WASD key dynamically joins P2 next to P1*
    *   `W`/`A`/`S`/`D`: Move / Slide diagonally
    *   `F`/`f`: Shoot Arrow
    *   `G`/`g`: Smart Bomb

---

## Running the Test Suite

To execute all **14 automated unit tests** (covering spawning, co-op dynamic joins, exit progress coordinations, level restarts, sleep mode thresholds, and heart resurrection):
```bash
cargo test
```

---

## Remote Play (SSH Port Forwarding)

If you are running the game on a headless Linux development server and want to play it from a local Mac client:

From your **Mac terminal**, run:
```bash
ssh -L 8080:localhost:8080 <username>@<linux_server_ip>
```

*   Replace `<username>` with your server username.
*   Replace `<linux_server_ip>` with the server's hostname or IP.
*   Keep the SSH session open.
*   On your Mac, open your browser and navigate to:
    `http://localhost:8080`
