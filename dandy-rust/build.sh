#!/usr/bin/env bash
set -euo pipefail

# Size Budget Ratchet (assets/WASM-BUDGETS-TEMPLATE.md)
# 2026-08-24: Baseline gzip budget: 30KB (current release: ~24.9KB gzip, 70.8KB raw)
MAX_GZIP_BYTES=$((30 * 1024))

echo "=== Building Dandy Dungeon WASM (Release) ==="
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

if curl -s -I http://127.0.0.1:8080/ >/dev/null 2>&1; then
    echo ""
    echo "=== Running Headless Multi-Browser WebRTC Multiplayer Gate ==="
    node test_headless_multiplayer.mjs
fi

echo ""
echo "=== Build and Parity Gate Successful ==="
