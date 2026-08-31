#!/usr/bin/env bash
set -euo pipefail

# Size Budget Ratchet (assets/WASM-BUDGETS-TEMPLATE.md)
# 2026-08-24: Baseline gzip budget: 33KB (current release with 4P WebRTC rollback + POKEY audio + desync guard + joiner copy link: ~31.3KB gzip, 90.9KB raw)
MAX_GZIP_BYTES=$((33 * 1024))

echo "=== Building Dandy Dungeon WASM (Release) ==="
GIT_REV=$(git rev-parse --short HEAD 2>/dev/null || date +%s)
echo "Stamping build version: ${GIT_REV}..."
sed -i -E "s/window\.dandyBuildVersion\s*=\s*\"[^\"]+\";/window.dandyBuildVersion = \"${GIT_REV}\";/g" index.html

trunk build --release

echo "Compressing artifacts..."
for f in dist/*_bg.wasm; do
    gzip -9 -k -f "$f"
    raw_size=$(stat -c%s "$f")
    gz_size=$(stat -c%s "${f}.gz")
    echo "Artifact size: $(basename "$f") -> ${raw_size} B raw, ${gz_size} B gzip"
    if [ "$gz_size" -gt "$MAX_GZIP_BYTES" ]; then
        echo "FATAL: Size budget exceeded! ${gz_size} B > ${MAX_GZIP_BYTES} B limit." >&2
        exit 1
    fi
done

echo ""
echo "=== Running Headless Built-Artifact Parity Gate ==="
node test_artifact_parity.mjs

if [ -x "/google/bin/releases/gemini-agents-gbrowser/gbrowser" ] || command -v gbrowser >/dev/null 2>&1; then
    echo ""
    echo "=== Running Headless End-to-End Game Smoke Gate ==="
    node test_game_e2e.mjs

    echo ""
    echo "=== Running Headless Multi-Browser WebRTC Multiplayer Gate ==="
    node test_headless_multiplayer.mjs
fi

echo ""
echo "=== Build and Parity Gate Successful ==="
