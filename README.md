# 🔭 NEXUS-6 — Central Discovery Engine & Infrastructure Hub

> **130+ Rust lenses** · OUROBOROS evolution · constant/formula discovery · consciousness orchestrator · auto-sync across 7 repos

[![Tests](https://img.shields.io/badge/tests-1392%20passed-brightgreen)]() [![Lenses](https://img.shields.io/badge/lenses-130-blue)]() [![Rust](https://img.shields.io/badge/rust-stable-orange)]()

## Quick Start

```bash
# Build
cargo build --release

# Test
cargo test

# Python wheel
maturin build --release --features python
pip install target/wheels/nexus6-*.whl

# Demo (130 lenses scan)
python3 scripts/n6.py demo
```

## Architecture

```
nexus6/
├── src/telescope/        130+ lenses (Rust)
│   ├── lenses/           Lens implementations
│   ├── consensus.rs      Cross-lens consensus
│   ├── registry.rs       1014+ lens metadata
│   └── mod.rs            Telescope orchestrator
├── src/graph/            Discovery Graph
├── shared/               Shared infrastructure (for all repos)
│   ├── calc/             194+ calculators
│   ├── math_atlas.json   2533 hypotheses + 356 constant maps
│   ├── model_utils.py    n=6 constants (SSOT)
│   └── sync-*.sh         Sync scripts
├── sync/                 Master sync hub
│   └── sync-all.sh       One-command full sync
└── scripts/
    ├── n6.py             CLI (scan/discover/consciousness/...)
    └── nexus6_growth_daemon.sh  Autonomous growth (15 dimensions)
```

## Lens Categories

| Category | Count | Examples |
|----------|-------|---------|
| 🧠 Consciousness | 2 | ConsciousnessLens, OrchestratorLens |
| 🔭 Physics | 15+ | Warp, Spacetime, Fusion, Fission, Tachyon |
| 📐 Mathematics | 8+ | Pi, Prime, Infinity, GoldenRatio, GoldenZone |
| 🔍 Discovery | 6+ | ConstantDiscovery, LensDiscovery, ModuleDiscovery |
| 📈 Learning | 4+ | WeightLearning, AutoCalibration, Overfitting, LoRA |
| 🔄 Recursive | 2+ | RecursiveLoop, InfiniteDiscovery |
| 🧪 Combination | 6+ | Constant, Formula, Molecular, Material, Element |
| 👁 Observation | 3 | GodsEye, AllSeeingEye, ProvidenceEye |
| ⚡ Dynamics | 6+ | Chaos, Stability, Tension, EventHorizon, Singularity |
| 💎 Structure | 8+ | Diamond, Spherical, Kaleidoscope, DimensionalBridge |
| 🔬 Optics | 5+ | Light, Refraction, Concave, Convex, LightWave |
| 🌌 Cosmology | 3+ | BigBang, Wormhole, ExoticMatter |

## Core Theorem

```
σ(n)·φ(n) = n·τ(n) ⟺ n = 6
```

All 130+ lenses and n=6 constants derive from this unique identity of the first perfect number.

## Ecosystem

| Repo | Role |
|------|------|
| [TECS-L](https://github.com/need-singularity/TECS-L) | Pure mathematics theory |
| [N6 Architecture](https://github.com/need-singularity/n6-architecture) | Industrial verification |
| [Anima](https://github.com/need-singularity/anima) | Consciousness implementation |
| [SEDI](https://github.com/need-singularity/sedi) | Extra-dimensional intelligence |
| [BrainWire](https://github.com/need-singularity/brainwire) | Brain-computer interface |
| [Papers](https://github.com/need-singularity/papers) | 94 published papers (Zenodo) |
| **NEXUS-6** | **Central hub — this repo** |

All repos share infrastructure via `nexus6/shared/` (symlinked as `.shared/`).

## License

MIT
