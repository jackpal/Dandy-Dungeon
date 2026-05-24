# Dandy Dungeon - Rust Wasm Port (SM-PIE Architecture)

This is a high-performance, self-contained, web-playable WebAssembly (Wasm) port of the classic cooperative 2D overhead dungeon crawler **Dandy Dungeon** in Rust, served via **Trunk**.

The codebase has been extensively re-engineered using the **Shared Memory Platform-Independent Engine (SM-PIE)** model, stripping away all browser-coupled APIs (`web-sys`) to establish a pure, highly performant, and portable game loop simulation.

---

## Architectural Pillars

### 1. Zero Wasm-to-DOM Coupling
The Rust engine is compiled as a pure simulation core, completely isolated from the browser environment. Wasm no longer calls DOM element lookups, text updates, or event listeners directly.
*   **Zero-Copy memory sharing**: JavaScript instantiates standard typed arrays (`Uint8ClampedArray` and `Int32Array`) directly over the shared Wasm linear memory buffer, reading statistics and frame buffers instantly with zero allocation or garbage collection overhead.

### 2. Software Framebuffer Blitting (99.5% Render Call Reduction)
Instead of issuing 200+ expensive JavaScript Native Interface (JSNI) drawing calls per frame (e.g., drawing individual sprite coordinates on a 20x10 viewport canvas), the Rust core blits pixels internally:
*   **Dedicated Blitter (`src/graphics.rs`)**: Statically decodes the uncompressed 24-bit BGR spritesheet (`dandy.bmp`) with spec-compliant DWORD row strides and BGR-RGBA conversions, caching it inside Wasm memory on load.
*   **Vectorized Row Blitting (SIMD Optimized)**: Decouples loops inside `blit_tile` to calculate horizontal and vertical viewport clipping boundaries strictly **once** per tile, hoisting loop-invariant calculations outside the inner loop. Row segments are copied into the framebuffer via continuous memory blits using Rust's vector-optimized **`copy_from_slice`** (equivalent to optimized CPU `memcpy`), unlocking hardware SIMD execution.
*   **Single-Blit Frame**: During ticks, Rust blits pixels directly to a flat local screen buffer (`Vec<u8>` representing native `320x160` pixels). The JS shell draws the entire scene on the browser canvas using **exactly one** `putImageData` call per frame.
*   **Crisp Retro Upscaling**: The native `320x160` buffer is upscaled to a sharp `640x320` window using browser-level hardware-accelerated CSS (`image-rendering: pixelated;`).

### 3. Event-Driven Sleep Mode (Idle Engine State)
To save CPU and GPU resources in web environments, Wasm exposes a `can_sleep() -> bool` API that suspends the browser loop when the game state becomes completely static:
*   **Sleep Conditions**: The game sleeps if:
    1.  No keys/logical buttons are pressed.
    2.  No projectile arrows are in flight.
    3.  The viewport camera has fully converged on the players' Center of Gravity (COG) within a threshold of `< 0.1` pixels.
    4.  All visible ghosts inside the active viewport are blocked (no valid pathfinding headings available or frozen by arrows).
    5.  All visible generators inside the active viewport are cardinally blocked (no adjacent open `SPACE` tiles).
*   **Resumption**: The JS shell terminates the animation frame rendering when sleep is triggered. The window `keydown` listener captures user input, sets `sleeping = false`, and **synchronously resumes** the `requestAnimationFrame` loop instantly.
*   **Sticky Keys Mitigation**: A window `blur` listener clears active input lists on tab focus loss, avoiding infinite walking loops during sleep transitions.

### 4. Decoupled Arrow Projectiles & Cooperative Self-Resurrection
*   **Independent Projectiles**: Projectile stepping (`step_arrow`) is decoupled from player input loops. If a player fires an arrow and dies, the arrow continues to fly and animate in flight unconditionally.
*   **Self-Resurrection Edge Case**: Centralized progression checks defer level reloads and failures while active arrows are in flight. If a dead player's arrow collides with a `HEART` tile, they are resurrected to `health = 50` at the heart's coordinate, avoiding level reloads and seamlessly continuing active dungeon play.

### 5. Logical Controls Bitmasking & Generalization
*   Wasm is completely decoupled from physical hardware keyboard strings (e.g., `"ArrowLeft"`, `"w"`).
*   Inputs are mapped to a logical `PlayerAction` enum and fed to Wasm as abstract bitmask flags (`set_action(player_idx, action, pressed)`).
*   This cleanly generalizes dyn-joining and cardinal spawning offsets for all 4 players (P1: North, P2: East, P3: South, P4: West), allowing P3/P4 bindings or Gamepads to be registered instantly in the JS shell.

### 6. Host-Independent LCG Pseudo-Randomness
Replaced all host Web API browser calls (`js_sys::Math::random()`) with a deterministic, platform-agnostic custom **Linear Congruential Generator (LCG)** PRNG (`next_random()`), ensuring 100% portability of ghost AI and spawner ticks.

### 7. Zero-Clone Borrow checking
Wasm loops are structured to satisfy Rust borrow-checker rules by reading primitive coordinates at block scopes, completely avoiding redundant `Player::clone()` allocations during frame ticks.

### 8. Stateless Modular Architecture (SRP Decoupling)
To satisfy the Single Responsibility Principle (SRP) and maximize code legibility and testability, the monolithic engine has been decomposed into decoupled, cohesive modules:
*   `src/game.rs`: Streamlined loop orchestrator managing ticks, level loads, and coop progress checks.
*   `src/camera.rs`: Viewport offset calculations, active rect clipping, and player Center of Gravity (COG) math.
*   `src/physics.rs`: Stateless 8-way wall-sliding physics, door unlocking, and arrow projectile/heart resurrection mechanics (accepts direct `&mut Player` and `&mut Map` disjoint references, resolving borrow collisions).
*   `src/ai.rs`: Stateless ghost Manhattan chaser pathfinding, generator spawner spawning, and monster sleep blocked heuristics.
*   `src/rand.rs`: Stateless host-independent custom LCG pseudo-random number generator.

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

Trunk will automatically watch your source files, rebuild, compile Wasm, and reload the browser on any changes.

To compile static release deployment files (output to `dandy-rust/dist/`):
```bash
trunk build --release
```

---

## How to Play

*   **Player 1 (Arrows)**:
    *   `Arrow Keys`: Move / Slide diagonally around walls
    *   `Spacebar`: Shoot Arrow
    *   `B` / `b`: Smart Bomb (Wipes all active monsters in view)
*   **Player 2 (WASD)**:
    *   *Pressing any WASD key dynamically joins P2 next to P1*
    *   `W`/`A`/`S`/`D`: Move / Slide diagonally
    *   `F`/`f`: Shoot Arrow
    *   `G`/`g`: Smart Bomb

---

## Running the Test Suite

The Rust core has a rigorous test suite covering player spawning direction, co-op dynamic hot-joins, multi-player exit coordinations, level restarts, sleep parameters, and co-op arrow self-resurrections.

To execute all **13 automated unit tests** locally:
```bash
cargo test
```

---

## Viewing the Web Page Remotely (SSH Port Forwarding)

If you are running the game on a headless Linux development server and want to play it from a local client machine (e.g., a Mac), you can set up an SSH tunnel.

### Local Port Forwarding (Mac -> Linux)

From your **local client terminal (e.g., Mac)**, run:
```bash
ssh -L 8080:localhost:8080 <username>@<linux_server_ip>
```

*   Replace `<username>` with your server LDAP/username.
*   Replace `<linux_server_ip>` with the server's hostname or IP address.
*   Once connected, keep the SSH session open.
*   On your Mac, open your browser and navigate to:
    `http://localhost:8080`
