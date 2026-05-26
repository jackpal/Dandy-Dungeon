# Python Dandy Dungeon Port

This directory contains a Python 3.14 port of John Palevich's 2D arcade game *Dandy Dungeon*, using **Pygame-ce (Community Edition)** and the **`uv`** dependency and environment management system.

---

## Features & Implementation Details

*   **Python 3.14 Port**: Ported from legacy Python 2 to Python 3.14, resolving string/bytes decodings, obsolete generators (`xrange` replaced with `range`), mixed tab indentations, and updating float divisions (`/`) to integer floor divisions (`//`) to maintain integer states for coordinates.
*   **High-DPI & Retina Support**: Uses Pygame-ce for 2D graphics. Window mode is set to `pygame.SCALED | pygame.RESIZABLE` to support Retina and High-DPI backing scales, and automatically scale the retro aspect ratio cleanly when resized.
*   **Visual Text-Based HUD**: Reserves a 40px black bar at the top of the screen to render a monospaced text HUD displaying status statistics (score, health, keys, bombs) for Player 1 and Player 2.
*   **Player 2 Dynamic Hot-Joining**: Supports Player 2 dynamically joining the session on `W/A/S/D` keys, spawning adjacent to Player 1. Viewport camera tracking calculates coordinates based on the average Center of Gravity (COG) of active players.
*   **CPU-Saving Sleep Mode**: Enters an idle sleep state when the game is inactive (no inputs, no active projectiles, camera settled, and viewport enemies/generators blocked). The game loop suspends using `pygame.event.wait()` to block the thread (0% CPU) and wakes up immediately on keyboard/gamepad events.
*   **60Hz Frame Rate Regulator**: Constrains the active gameplay loop to exactly 60 Hz using `pygame.time.Clock()` to prevent CPU core exhaustion.
*   **Block Map Loader**: Loads 900-byte binary levels using a single block read (`f.read(900)`) and `enumerate` index parsing.
*   **Relative Path Resolution**: Resolves media assets relative to the script location (`__file__`) to allow execution from any working directory.

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

The project includes a verification suite (`verify_game.py`) that initializes a headless SDL `dummy` video driver to test game tick loops, sleep states, and Player 2 dynamic joins automatically.

To run the verifications:
```bash
uv run python verify_game.py
```
