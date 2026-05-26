# Python Dandy Dungeon Port

This directory contains a Python 3.14 port of John Palevich's 2D arcade game *Dandy Dungeon*, using **Pygame-ce (Community Edition)** and the **`uv`** dependency and environment management system.

---

## Features & Implementation Details

*   **Python 3.14 Port & Modularization**: Ported from legacy Python 2 to Python 3.14. The monolithic codebase has been modularized into 8 cohesive modules under `src/` (constants, media, strike, map, entities, controls, game, and main), keeping the main `src/main.py` as a re-exporting facade.
*   **High-DPI & Retina Vector HUD**: Window display is initialized at a native physical resolution of `640x560` using `pygame.RESIZABLE` (no `pygame.SCALED` flag). HUD text is rendered directly onto the physical window screen surface at native resolution using `antialias=True` and monospaced **Courier Bold** system fonts, ensuring perfectly sharp, readable, and vertically aligned columns at all window scales.
*   **Scaled Retro Viewport**: The core game coordinates blit onto an offscreen `320x240` gameplay surface. The draw loop dynamically upscales this virtual surface to fit the window area (minus HUD height) using nearest-neighbor scaling (`pygame.transform.scale`), keeping retro pixel art edges crisp and blocky.
*   **Player 2 Dynamic Hot-Joining**: Supports Player 2 dynamically joining the session on `W/A/S/D` keys, spawning exactly 1 tile East of the UP stairs ("U" symbol). Viewport camera tracking calculates coordinates based on the average Center of Gravity (COG) of active players.
*   **Hardened 0% CPU Sleep Mode**: Enters an idle sleep state when the game is inactive. Achieving strictly 0% CPU utilization using a defense-in-depth solution:
    *   *OS-Level Event Whitelisting*: Blocks all unused events (including `pygame.MOUSEMOTION`) at the OS level using `pygame.event.set_blocked(None)`, preventing mouse hover cues from waking the thread.
    *   *Analog Deadzone*: Ignores analog joystick drift (`pygame.JOYAXISMOTION`) below an absolute deadzone threshold of `0.15`.
    *   *OS Thread Suspension*: Calls `pygame.event.wait()` to suspend the thread completely. Wakeups on significant inputs are prepended back to the queue to ensure zero-frame input latency.
*   **60Hz Frame Rate Regulator**: Constrains the active gameplay loop to exactly 60 Hz using `pygame.time.Clock()` to prevent CPU core exhaustion.
*   **Block Map Loader**: Loads 900-byte binary levels using a single block read (`f.read(900)`) and `enumerate` index parsing.
*   **Relative Path Resolution**: Resolves media assets relative to the script location (`__file__`) using `pathlib.Path`.

---

## Prerequisites

1. **uv**: A Python package resolver and compiler. Install it using:
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```
   *Note: `uv` will fetch and provision the required Python 3.14 compiler locally if it is not found on your system.*

---

## Getting Started

### 1. Navigate to Subproject
```bash
cd dandy-py
```

### 2. Synchronize the Environment
Resolve dependencies and compile the local virtual environment:
```bash
uv sync
```
*Note: The lockfile `uv.lock` is ignored by Git to prevent conflicts across environments using custom package registry mirrors (such as Google's staging mirror). Dependencies resolve dynamically from `pyproject.toml`.*

*(Optional): If you are building in a restricted environment enforcing private registry proxies, bypass the proxy by passing public indexes:*
```bash
UV_INDEX_URL="" UV_INDEX="" uv sync --default-index https://pypi.org/simple
```

### 3. Run the Game
Launch the game window inside the virtual environment:
```bash
uv run python src/main.py
```

---

## Headless Verification Tests

The project includes a verification suite (`verify_game.py`) that initializes a headless SDL `dummy` video driver to test game tick loops, sleep states, Player 2 dynamic joins, and viewport scaling automatically.

To run the verifications:
```bash
uv run python verify_game.py
```
*(If inside a restricted environment, pass PyPI index explicitly: `UV_INDEX_URL="" UV_INDEX="" uv run --default-index https://pypi.org/simple python verify_game.py`)*
