# Dandy Dungeon Offline E2E Test Infrastructure

This document describes the design, architecture, and usage of the Dandy Dungeon offline E2E test harness. The test harness compiles the core platform-independent game engine alongside a mock Hardware Abstraction Layer (HAL) to enable rapid, deterministic, and headless testing of game mechanics and rules.

## 1. Architecture Overview

The offline testing pipeline runs entirely on the host machine (e.g., Linux x86_64). It bypasses the GameBoy GBDK compiler and emulators, enabling test suites to run in milliseconds.

```
[tests/test_suite.py (Python Unittest)]
       |
       v (Programmatic Control & Assertions)
[tests/dandy_env.py (ctypes wrapper)]
       |
       v (Loads unique copy)
[libdandy_test.so (C Shared Library)]
  ├── src/dandy_core.c (Platform-independent Game Logic)
  ├── src/levels.c (Decompressed Level Database)
  └── tests/mock_hal.c (Mock Graphics/Audio/Sprites logging calls)
```

### Key Highlights:
1. **Mock GBDK Headers**: A mock `<gb/gb.h>` header is dynamically generated at compile-time to stub out GameBoy-specific compiler features (like ROM bank switching) as no-ops.
2. **Strict State Isolation**: The Python wrapper (`dandy_env.py`) creates a unique temporary copy of `libdandy_test.so` on disk for every test case. This ensures that internal static variables (like the random seed and button history) are reset to their compile-time default values before each test runs.
3. **Double Assertion Coverage**: Tests assert both on the engine's internal global variables (e.g., coordinates, health, inventory) and the mock HAL's logged side-effects (e.g., specific tile drawing calls, registered hardware sprites, played audio tracks).

---

## 2. Quick Start

### 2.1 Compile the Test Library
To compile `libdandy_test.so` from the `dandy-gb/` directory:
```bash
make test_lib
```

### 2.2 Run the Test Suite
To run all tests in the `tests/` directory:
```bash
make test
```
This runs the Python `unittest` framework to discover and execute all `test_*.py` suites.

---

## 3. Core Feature Inventory & Rules

The game engine is evaluated against 10 core features, divided into distinct behaviors for precise testing.

| Feature ID | Feature Name | Description | Key Game Rules to Verify |
|---|---|---|---|
| **F-01** | Movement & Timing | 8-way player movement and grid alignment. | - Moving into `TILE_SPACE` updates coordinates.<br>- `player_move_timer` acts as a 4-tick cooldown; holding inputs moves the player exactly once every 4 ticks.<br>- Unjoined or dead players do not process inputs. |
| **F-02** | Slide Mechanics | Sliding around solid obstacles. | - If a diagonal/cardinal move is blocked, the engine automatically checks direction $\pm 1$ and moves there if free.<br>- If all three are blocked, the player remains stationary. |
| **F-03** | Item Collection | Consuming items scattered on the map. | - Walking onto `TILE_FOOD` increases health by 100, plays `SOUND_FOOD`. Health can exceed 100.<br>- Walking onto `TILE_MONEY` increases score by 100, plays `SOUND_KEY`.<br>- Walking onto `TILE_KEY` increments keys by 1, plays `SOUND_KEY`.<br>- Walking onto `TILE_BOMB` increments bombs by 1, plays `SOUND_KEY`. |
| **F-04** | Door & Key Mechanics | Locked doors requiring keys to unlock. | - Moving onto `TILE_DOOR` with 0 keys is blocked.<br>- Moving onto `TILE_DOOR` with $\ge 1$ keys decrements keys by 1, plays `SOUND_KEY`, and triggers an 8-way flood fill that turns all connected door tiles into `TILE_SPACE`. |
| **F-05** | Combat & Projectiles | Firing arrows to defeat enemies. | - Pressing `BUTTON_FIRE` when `arrow_dir == -1` fires an arrow in the player's direction and plays `SOUND_SHOOT`. Space is checked in the same tick.<br>- An arrow travels 1 tile per tick in its direction.<br>- Arrows only exist inside the player's viewport (10x20 area); leaving the viewport destroys the arrow.<br>- Hitting solid obstacles destroys the arrow.<br>- Hitting destructible targets destroys the arrow, plays `SOUND_HIT`, and applies effects:<br>  * `TILE_BOMB`: Triggers a smart bomb.<br>  * `TILE_HEART`: Degrades into `TILE_MONSTER3`.<br>  * `TILE_MONSTER3`/`TILE_MONSTER2`: Degrades by 1 level (`tile - 1`).<br>  * `TILE_MONSTER1` or any Generator: Replaced by `TILE_SPACE`. |
| **F-06** | Smart Bomb Action | Visual viewport-wide explosion. | - Pressing `BUTTON_BOMB` with $\ge 1$ bombs decrements bombs by 1, plays `SOUND_BOMB`, and clears all monsters and generators within the player's 10x20 viewport.<br>- Monsters and generators outside the viewport are unaffected. |
| **F-07** | Monster Behavior | AI movement and attacks. | - Monsters are updated on a 16-tick sparse grid (monster rotor) and are frozen if they are not visible in any active player's viewport.<br>- Visible monsters track the nearest active player (Manhattan distance) and move towards them.<br>- Colliding with a player deals $10 \times (\text{monster\_level})$ damage, plays `SOUND_HIT` (or `SOUND_DIE` if player dies), and removes the monster.<br>- Player death clears their tile from the map immediately. |
| **F-08** | Generator Spawning | Enemy factories spawning monsters. | - Generators update on the 16-tick sparse grid and freeze if off-screen.<br>- Every active tick, they use a deterministic LFSR random seed; if `(seed & 7) < 4`, they try to spawn a monster.<br>- They attempt to spawn in adjacent cardinal directions starting at `(seed & 3) * 2` clockwise, spawning a monster matching the generator's level in the first empty space. |
| **F-09** | Multiplayer & Viewport | Cooperative multiplayer support. | - Multiple players can join via `dandy_join_player()`. They spawn around the portal.<br>- Viewport centers on the local player, clamped to map boundaries ($60 \times 30$).<br>- Spectator Mode: If the local player is dead, the camera centers on the centroid of the remaining alive players. |
| **F-10** | Level Transitions | Advancing through the levels. | - Moving onto `TILE_DOWN` (stairs) triggers `next_level()`, which loads the next level, plays `SOUND_WARP`, and resets player coordinates to the new level's starting portal (`TILE_UP`). |

---

## 4. Test Tiers & Coverage Thresholds

To achieve robust verification, the test suite must implement tests across five hierarchical tiers, maintaining strict minimum count and coverage thresholds.

### 4.1 Tier 1: Happy-Path Feature Coverage (Target: $\ge 40$ Tests)
- **Scope**: Verifies basic, isolated functionality of each of the 10 core features in a clean map setting.
- **Examples**: Single step movement, collecting one of each item, unlocking a single door, shooting an arrow into empty space.

### 4.2 Tier 2: Boundary & Corner Cases (Target: $\ge 40$ Tests)
- **Scope**: Evaluates edge values, out-of-bounds inputs, and maximum capacity limits.
- **Examples**: Walking into map boundaries, hitting walls, shooting arrows off-viewport, multi-level health clamping, flood-filling massive or circular door networks.

### 4.3 Tier 3: Cross-Feature Interactions (Target: $\ge 8$ Tests)
- **Scope**: Tests scenarios where multiple systems interact simultaneously.
- **Examples**: An arrow hitting a bomb tile to trigger a viewport explosion; a monster attacking a player on the exact frame the player collects food; shooting an arrow at a monster that is moving toward the player.

### 4.4 Tier 4: Real-World Scenarios (Target: $\ge 5$ Tests)
- **Scope**: Multi-step playthroughs simulating actual game runs.
- **Examples**: Loading Level 0, navigating a maze of walls, collecting keys, unlocking doors, shooting a spawning monster, and reaching the stairs to advance to Level 1.

### 4.5 Tier 5: Adversarial & Stress Testing (Target: $\ge 5$ Tests)
- **Scope**: Extravagant inputs, concurrent multi-player inputs, and extreme state situations.
- **Examples**: All 4 players joining and pressing directions simultaneously; inputs injected for dead players; spectator mode camera centering with multiple alive/dead player configurations.

## 5. Quality & Assertion Standards

- **Double-Assert Rule**: Every test case must verify state changes in BOTH the engine's globals (e.g., `player_x`, `player_health`) and the mock HAL logs (e.g., `mock_get_sound_count()`, `mock_get_draws()`).
- **Deterministic Spawning**: Tests for F-08 (Generator Spawning) must leverage the fresh-load environment to guarantee identical LFSR state, asserting the exact ticks and directions that monsters are spawned.
