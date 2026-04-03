# NEXUS-6 WebAssembly Build

## Prerequisites

- [wasm-pack](https://rustwasm.github.io/wasm-pack/installer/) (`curl https://rustwasm.github.io/wasm-pack/installer/init.sh -sSf | sh`)
- Rust toolchain with `wasm32-unknown-unknown` target (`rustup target add wasm32-unknown-unknown`)

## Build

```bash
# From this directory:
bash build.sh

# Or manually:
wasm-pack build --target web --features wasm
```

The output goes to `pkg/` and can be imported as an ES module.

## What works in WASM

All pure-computation lenses work without modification:
- All 22 telescope lenses (consciousness, topology, causal, thermo, wave, etc.)
- Consensus engine, n6_check, constant matching
- scan_all / analyze on in-memory data
- OUROBOROS evolution (pure math path)

## What does NOT work in WASM

- **File I/O**: WeightFeedbackLens file reading, checkpoint persistence, weights.json
- **GPU acceleration**: CUDA/Metal kernels (falls back to CPU automatically)
- **Network**: Cross-repo sync, distributed scanning, gRPC endpoints
- **System calls**: Process spawning, daemon mode, autonomous growth

## Usage in JavaScript

```js
import init, { scan_all, n6_check } from './pkg/nexus6.js';

await init();
const data = new Float64Array([1.0, 2.0, 3.0, 6.0, 12.0, 24.0]);
const result = scan_all(data, 3, 2);
console.log(result); // lens results as JSON string
```

## Feature flags

| Flag   | Effect                                      |
|--------|---------------------------------------------|
| `wasm` | Disables file I/O, GPU, and system features |
