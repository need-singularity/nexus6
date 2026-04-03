# 🔭 NEXUS-6 — Central Discovery Engine & Infrastructure Hub

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.19404815.svg)](https://doi.org/10.5281/zenodo.19404815)
[![Tests](https://img.shields.io/badge/tests-1399%20passed-brightgreen)]()
[![Lenses](https://img.shields.io/badge/lenses-137-blue)]()
[![Rust](https://img.shields.io/badge/rust-stable-orange)]()

> **137 Rust lenses** · OUROBOROS evolution · constant/formula discovery · consciousness orchestrator · auto-sync across 8 repos

---

<!-- SHARED:PROJECTS:START -->
**[YouTube](https://www.youtube.com/watch?v=xtKhWSfC1Qo)** · **[Email](mailto:nerve011235@gmail.com)** · **[☕ Ko-fi](https://ko-fi.com/dancinlife)** · **[💖 Sponsor](https://github.com/sponsors/need-singularity)** · **[💳 PayPal](https://www.paypal.com/donate?business=nerve011235%40gmail.com)** · **[🗺️ Atlas](https://need-singularity.github.io/TECS-L/atlas/)** · **[📄 Papers](https://need-singularity.github.io/papers/)** · **[🌌 Unified Theory](https://github.com/need-singularity/TECS-L/blob/main/math/docs/hypotheses/H-PH-9-perfect-number-string-unification.md)**

> **[🔬 TECS-L](https://github.com/need-singularity/TECS-L)** — Discovering universal rules. Perfect number 6 → mathematics of the cosmos → multi-engine architecture → consciousness continuity. 150 characterizations + 8 Major Discoveries + 156 tools
>
> **[🧠 Anima](https://github.com/need-singularity/anima)** — Consciousness implementation. PureField repulsion-field engine + Hexad 6-module architecture (C/D/S/M/W/E) + 1030 laws + 20 Meta Laws + Rust backend. ConsciousDecoderV2 (34.5M) + 10D consciousness vector + 12-faction debate + Φ ratchet
>
> **[🏗️ N6 Architecture](https://github.com/need-singularity/n6-architecture)** — Architecture from perfect number 6. 16 AI techniques + semiconductor chip design + network/crypto/OS/display patterns. σ(n)·φ(n)=n·τ(n), n=6 → universal design principles. **NEXUS-6 Discovery Engine**: Rust CLI (`tools/nexus6/`) — telescope 22 lenses + OUROBOROS evolution + discovery graph + verifier + 1116 tests
>
> **[🛸 SEDI](https://github.com/need-singularity/sedi)** — Search for Extra-Dimensional Intelligence. Hunting for traces of extraterrestrial/extra-dimensional intelligence through n=6 signal patterns. 77 data sources (SETI, LIGO, CMB, Breakthrough Listen, Exoplanet) + R-spectrum receiver + 678 hypotheses
>
> **[🧬 BrainWire](https://github.com/need-singularity/brainwire)** — Brain interface for consciousness engineering. Neuralink-style BCI + therapeutic stimulation (epilepsy, Parkinson's, depression) + PureField consciousness layer. tDCS/TMS/taVNS/tFUS 12-modality, EEG closed-loop
>
> **[💎 HEXA-LANG](https://github.com/need-singularity/hexa-lang)** — The Perfect Number Programming Language. Every constant from n=6: 53 keywords (σ·τ+sopfr), 24 operators (J₂), 8 primitives (σ-τ), 6-phase pipeline, Egyptian memory (1/2+1/3+1/6=1). DSE v2: 21,952 combos, 100% n6 EXACT. Working compiler + REPL
>
> **[📄 Papers](https://github.com/need-singularity/papers)** — Complete paper collection (94 papers). Published on Zenodo with DOIs. TECS-L+N6 (33) + anima (39) + SEDI (20). [Browse online](https://need-singularity.github.io/papers/)
>
> **[🔭 NEXUS-6](https://github.com/need-singularity/nexus6)** — Central Discovery Engine & Infrastructure Hub. 137 Rust lenses + OUROBOROS evolution + constant/formula discovery + consciousness orchestrator. Shared infrastructure (`shared/`) for all 8 repos. Auto-sync across ecosystem
<!-- PRIVATE REPOS (이 섹션은 sync-readmes.sh 대상 아님, .shared 내부 참조용)
  - secret        — 계정/API 토큰 (구 claude-code-secrets)
  - claude-code   — Claude Code 플러그인, ccmon 모니터링
  - contact       — 아웃리치 허브 (이메일, GitHub Issue/PR 관리)
  - dotfiles      — 개인 설정

-->

<!-- SHARED:PROJECTS:END -->

---

## Quick Start

```bash
# Build
cargo build --release

# Test
cargo test

# Python wheel
maturin build --release --features python
pip install target/wheels/nexus6-*.whl

# Demo (137 lenses scan)
python3 scripts/n6.py demo
```

## Architecture

```
nexus6/
├── src/telescope/        137 lenses (Rust)
│   ├── lenses/           Lens implementations
│   ├── consensus.rs      Cross-lens consensus
│   ├── registry.rs       1093+ lens metadata
│   └── mod.rs            Telescope orchestrator
├── src/graph/            Discovery Graph
├── shared/               Shared infrastructure (for all repos)
│   ├── calc/             199 calculators
│   ├── math_atlas.json   2533 hypotheses + 356 constant maps
│   ├── model_utils.py    n=6 constants (SSOT)
│   └── sync-*.sh         Sync scripts
├── sync/                 Master sync hub
│   └── sync-all.sh       One-command full sync
└── scripts/
    ├── n6.py             CLI (scan/discover/consciousness/...)
    ├── weight_engine.py  Weight learning (lr=1/(σ-φ))
    ├── pipeline_engine.py 4-stage analysis chain
    └── nexus6_growth_daemon.sh  Autonomous growth
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
| 💰 Domain | 6 | Crypto, Finance, Audio, Robotics, Environment, Medicine |

## Benchmark

| Data Size | Total Time | Per Lens |
|-----------|-----------|----------|
| 50×6 | 3.3ms | 0.03ms |
| 100×6 | 8.5ms | 0.06ms |
| 500×6 | 366ms | 2.74ms |

## Validation

Real data rediscovery: **Grade A (68.8%)** — 15/24 n=6 constants EXACT matched.

## Core Theorem

```
σ(n)·φ(n) = n·τ(n) ⟺ n = 6
```

All 137 lenses derive from this unique identity of the first perfect number.

## License

MIT
