# Python Dandy Dungeon Port

This directory contains a Python 3.14 implementation of John Palevich's 2D arcade game *Dandy Dungeon*, utilizing the **Pygame-ce (Community Edition)** graphics framework and packaged using the **`uv`** dependency and environment management system.

---

## Game Features & Architecture

*   **Modular Architecture**: The application is organized into distinct, clean modules separating game constants, media loading, drawing utilities, map data, player/arrow entities, controls, and the core game loop.
*   **High-DPI & Retina Display Support**: Supports pixel-perfect rendering on Retina and High-DPI monitors. The retro gameplay viewport is rendered offscreen and scales using nearest-neighbor upscaling to preserve sharp pixel art edges when resized.
*   **Proportional Status HUD**: Displays scores, health, keys, and bombs for Player 1 and Player 2 in a dedicated status bar at the top of the screen. HUD text is rendered using a monospaced font, ensuring statistics stay aligned vertically in a perfect grid. The HUD text size and offsets scale proportionally whenever the window is resized.
*   **Dynamic Co-Op Hot-Joining**: Supports dynamic local cooperative multiplayer. Player 2 can join dynamically by pressing their mapped keys (W/A/S/D), spawning exactly 1 tile East of the level entrance (UP stairs). The scrolling viewport camera tracks the average Center of Gravity (COG) of all active players.
*   **CPU-Saving Sleep Mode**: Automatically enters an idle sleep state when the game is inactive (no player inputs, no active projectiles, camera settled, and viewport enemies blocked), dropping active CPU usage to strictly 0%. Any keyboard keypress or gamepad event wakes the engine instantly with zero input latency.
*   **Framerate Regulator**: Limits active loop iterations to exactly 60 Hz to ensure consistent, manageable gameplay and stepping speeds.
*   **Level Loader**: Seamlessly loads the 26 classic binary map files (A-Z) on floor transitions.

---

## Prerequisites

To run this application, you need the following tool installed on your system:

1. **uv**: A fast Python package resolver and environment manager. Install it using:
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```
   *Note: `uv` will automatically fetch and provision the required Python 3.14 compiler locally if it is not found on your system.*

---

## Getting Started

### 1. Navigate to Subproject
```bash
cd dandy-py
```

### 2. Synchronize the Environment
Create the local virtual sandbox and install dependencies:
```bash
uv sync
```
*Note: The lockfile `uv.lock` is ignored by Git to prevent staging index conflicts across development environments utilizing custom corporate package mirrors. Dependencies resolve dynamically from `pyproject.toml`.*

*(Optional): If you are building in a restricted environment that blocks public indices, bypass the proxy by passing public PyPI mirrors explicitly:*
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

The project includes an automated verification suite (`verify_game.py`) that initializes a headless SDL video driver to validate active loops, sleep states, Player 2 dynamic joins, and viewport scaling.

To run the validations:
```bash
uv run python verify_game.py
```
*(If inside a restricted environment, pass the PyPI index explicitly: `UV_INDEX_URL="" UV_INDEX="" uv run --default-index https://pypi.org/simple python verify_game.py`)*
