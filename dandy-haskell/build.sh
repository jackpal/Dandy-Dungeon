#!/bin/sh
set -e

if [ ! -f "$HOME/.ghc-wasm/env" ]; then
  echo "Error: GHC Wasm toolchain not found in $HOME/.ghc-wasm/"
  echo "Please ensure the toolchain is installed."
  exit 1
fi

. "$HOME/.ghc-wasm/env"

echo "Building Haskell WebAssembly project..."
"$HOME/.ghc-wasm/cabal/bin/cabal" build --with-compiler="$HOME/.ghc-wasm/wasm32-wasi-ghc/bin/wasm32-wasi-ghc" \
            --with-hc-pkg="$HOME/.ghc-wasm/wasm32-wasi-ghc/bin/wasm32-wasi-ghc-pkg" \
            --with-hsc2hs="$HOME/.ghc-wasm/wasm32-wasi-ghc/bin/wasm32-wasi-hsc2hs" \
            --with-haddock="$HOME/.ghc-wasm/wasm32-wasi-ghc/bin/wasm32-wasi-haddock" \
            "$@"

cp dist-newstyle/build/wasm32-wasi/ghc-9.14.1.20260330/dandy-haskell-0.1.0.0/x/dandy-haskell/build/dandy-haskell/dandy-haskell.wasm web/
echo "Build complete. Copied Wasm binary to web/dandy-haskell.wasm."
