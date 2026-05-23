# Dandy Dungeon - Rust Web Port

This is a self-contained, web-playable port of the classic cooperative 2D overhead dungeon crawler **Dandy Dungeon** in Rust, compiled to WebAssembly (Wasm).

The implementation is designed for simplicity and maintains strict architectural symmetry with the existing JavaScript (`dandy-js`) and Python (`dandy-py`) ports.

## Tech Stack & Architecture

*   **Language**: Rust (compiled to Wasm via the `wasm32-unknown-unknown` target).
*   **Bundler/Build Tool**: [Trunk](https://trunkrs.dev/) (a WASM web application bundler for Rust).
*   **Graphics/Rendering**: HTML5 Canvas (2D Context) accessed via `web-sys` and `wasm-bindgen`.
*   **Asset Handling**: Sprite sheet (`dandy.bmp`) and level maps (LEVEL.A-Z binary files) are **statically embedded** into the compiled WebAssembly binary using `include_bytes!`, making the deployment completely self-contained.
*   **BMP Parser**: Custom synchronous 24-bit BGR BMP decoder with standard DWORD stride alignment, pre-rendered onto an offscreen canvas to prevent asynchronous loading flashes or race conditions.
*   **Flood-Fill**: Iterative, stack-safe Depth-First Search (DFS) for door unlocking, preventing Wasm call-stack overflows.
*   **Camera**: Smooth sub-pixel linear interpolation camera that dynamically follows the active players' Center of Gravity (COG) at 60 FPS.
*   **Co-op Mechanics**: Dynamic Player 2 keyboard hot-joining and arrow-heart teammate resurrection.

---

## Prerequisites

Ensure you have the Rust toolchain installed. You will also need to install the WebAssembly target and the Trunk bundler.

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

Trunk will automatically watch your source files, rebuild, and reload the browser on any changes.

To build static release files (output to `dandy-rust/dist/`):
```bash
trunk build --release
```

---

## How to Play

*   **Player 1 (Arrows)**:
    *   `Arrow Keys`: Move / Slide diagonally
    *   `Spacebar`: Shoot Arrow
    *   `B`: Smart Bomb (Explodes all active monsters in view)
*   **Player 2 (WASD)**:
    *   *Pressing any WASD key dynamically joins P2 next to P1*
    *   `W`/`A`/`S`/`D`: Move / Slide diagonally
    *   `F`: Shoot Arrow
    *   `G`: Smart Bomb

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
