#!/usr/bin/env bash
set -euo pipefail

# Size Budget Ratchet (assets/WASM-BUDGETS-TEMPLATE.md)
# 2026-08-24: Baseline gzip budget: 30KB (current release: ~24.9KB gzip, 70.8KB raw)
MAX_GZIP_BYTES=$((30 * 1024))

echo "=== Building Dandy Dungeon WASM (Release) ==="
trunk build --release

WASM_OPT="${WASM_OPT:-$(command -v wasm-opt 2>/dev/null || find ~/.cache/trunk -name wasm-opt -type f 2>/dev/null | head -n 1)}"
if [ -n "$WASM_OPT" ] && [ -x "$WASM_OPT" ]; then
    for f in dist/*_bg.wasm; do
        if [ -f "$f" ]; then
            echo "Running wasm-opt -Oz on $f..."
            "$WASM_OPT" -Oz \
                --enable-bulk-memory \
                --enable-mutable-globals \
                --enable-nontrapping-float-to-int \
                --enable-sign-ext \
                --enable-reference-types \
                --enable-multivalue \
                "$f" -o "$f"
        fi
    done
fi

echo "Compressing artifacts..."
for f in dist/*_bg.wasm; do
    gzip -k -f "$f"
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

echo ""
echo "=== Build and Parity Gate Successful ==="
