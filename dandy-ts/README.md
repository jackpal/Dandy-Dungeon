# Dandy Dungeon (TypeScript Edition)

A modernized TypeScript port of the classic Atari 800 game Dandy Dungeon.

## Prerequisites

You need [Bun](https://bun.sh) installed on your system to build and run the development environment.

## Getting Started

1. **Install dependencies:**
   ```bash
   bun install
   ```

2. **Build the project:**
   This bundles the TypeScript modules into a single `dandy.js` file usable by the browser.
   ```bash
   bun build ./dandy.ts --outdir ./
   ```

3. **Run the game:**
   You can open `dandy.html` directly in your browser, or serve the directory using a local web server:
   ```bash
   bun x serve .
   ```

## Controls

| Key | Action |
| --- | --- |
| `Arrow Keys` | Move Player |
| `Space` | Fire Arrow |
| `B` | Smart Bomb |
| `F5` | Reload Level |

## Development

The project uses:
- **TypeScript**: For type-safe game logic.
- **Bun**: For dependency management and extremely fast bundling.
- **Canvas API**: For high-performance pixel-art rendering.

The game logic is encapsulated in the `DandyGame` class found in `dandy.ts`.