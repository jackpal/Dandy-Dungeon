#!/bin/bash
set -euo pipefail

echo "Building Dandy Dungeon WASM (Release)..."
trunk build --release

WASM_OPT="${WASM_OPT:-$(command -v wasm-opt 2>/dev/null || find ~/.cache/trunk -name wasm-opt -type f 2>/dev/null | head -n 1)}"
if [ -n "$WASM_OPT" ] && [ -x "$WASM_OPT" ]; then
    for f in dist/*_bg.wasm; do
        if [ -f "$f" ]; then
            echo "Running wasm-opt -Oz on $f using $WASM_OPT..."
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

echo "Build complete. Artifacts in dist/:"
ls -lh dist/
gzip -k -f dist/*_bg.wasm
ls -lh dist/*_bg.wasm.gz
