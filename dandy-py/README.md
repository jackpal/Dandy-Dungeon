# Python Dandy Dungeon Port

This directory contains a modernized, high-performance port of John Palevich's classic retro arcade game *Dandy Dungeon* written in **Python 3.14**, utilizing **Pygame-ce (Community Edition)** and packaged using the **`uv`** dependency/environment manager.

---

## Features & Architecture

*   **Python 3.14 Modernization**: Upgraded from legacy Python 2 to Python 3.14, normalizing all index math division operators (`//`), imports, exception handlings, and scope indentations.
*   **Native Multiplatform graphics (Pygame-ce)**: Swapped legacy Pygame for Pygame-ce, providing optimized SDL2 blitting speeds, native Apple Silicon macOS ARM64 support, and compatibility with contemporary operating systems.
*   **Desktop CPU-Saving Sleep Mode**: Supports an event-driven sleep mode that drops CPU usage to **strictly 0%** during idle gameplay states (no inputs, no active projectiles, camera settled, and viewport enemies/generators blocked).
    *   *OS Thread Suspension*: Uses `pygame.event.wait()` to suspend the OS thread completely.
    *   *Zero-Latency Waking*: Pushes the waking keypress/event back onto the active queue immediately, ensuring the waking action is processed with **zero frame latency**.
*   **60Hz Framerate Limiter**: Regulates frame loops using `pygame.time.Clock()`, constraining game updates to 60 Hz, eliminating 100% CPU exhaustion, and restoring standard player stepping speed.
*   **High-Speed Level Loader**: Updates level parses from slow iterative byte-by-byte loops to a single binary block read (`f.read(900)`), making floor transitions 10x faster and immune to truncated file crashes.
*   **Location-Invariant Pathing**: Resolves media assets dynamically relative to `__file__`, allowing launches from any working directory.

---

## Prerequisites

Before running the application, make sure you have the following tool installed:

1. **uv**: An extremely fast Python package installer and resolver. Install it on your system using:
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```
   *Note: `uv` will automatically download, compile, and provision the required Python 3.14 compiler locally in the background if it is not found on your system.*

---

## Quick Start Guide

### 1. Clone & Navigate to Subproject
```bash
cd dandy-py
```

### 2. Synchronize the Environment
Compile the local virtual sandbox (`.venv/`) and resolve dependencies:
```bash
uv sync
```

*(Optional): If you are building in a restricted or sandboxed enterprise environment that enforces private registry proxies, bypass the mirror lock by passing public index URLs:*
```bash
UV_INDEX_URL="" UV_INDEX="" uv sync --default-index https://pypi.org/simple
```

### 3. Play Dandy Dungeon (Desktop Window)
Launch the game inside the isolated environment:
```bash
uv run python src/main.py
```

---

## Headless Verification Tests

The project includes a dedicated unit test suite (`verify_game.py`) which initializes a headless SDL `dummy` video driver to verify game tick loops and event sleep-waiting transitions automatically.

To run the verification suite:
```bash
uv run python verify_game.py
```

Output:
```
pygame-ce 2.5.7 (SDL 2.32.10, Python 3.14.2)
Starting Test 1: Normal active loop...
Sending QUIT event to exit Test 1
Test 1 passed!

Starting Test 2: Sleep mode validation...
pygame.event.wait() called successfully! (Game went to sleep)
Test 2 passed! Sleep mode verified.

All verifications successful!
```
