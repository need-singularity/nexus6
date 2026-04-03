#!/bin/bash
# Build NEXUS-6 for WebAssembly
# Usage: bash wasm/build.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

echo "Building NEXUS-6 WASM module..."
wasm-pack build --target web --features wasm --out-dir wasm/pkg

echo "Done. Output in wasm/pkg/"
