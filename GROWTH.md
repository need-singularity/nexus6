# NEXUS Growth System

Autonomous self-improvement engine for the NEXUS Discovery Engine.
Measures, tracks, plans, and executes growth across 16 dimensions.

## Architecture (5 Layers)

```
  Layer 5: Execution     scripts/*.sh         Claude CLI drives plans
  Layer 4: Planning      planner, architect   Synthesize prioritized actions
  Layer 3: Analysis      *_grower (7 modules) Domain-specific gap assessment
  Layer 2: Tracking      tracker, registry    History, snapshots, dashboards
  Layer 1: Measurement   metrics, benchmark   Collect health + performance data
```

Data flows upward: measurement feeds tracking, tracking feeds analysis,
analysis feeds planning, planning feeds execution. Each execution cycle
loops back to measurement for the next iteration.

## 16 Growth Dimensions

| # | Dimension       | Target    | Unit    | Weight | Description                                         |
|---|-----------------|-----------|---------|--------|-----------------------------------------------------|
| 1 | Performance     | 10000     | ops/sec | 0.08   | Telescope scan throughput and latency                |
| 2 | Architecture    | 100%      | percent | 0.09   | Module structure completeness, no orphans/stubs      |
| 3 | Lenses          | 200       | count   | 0.09   | Implemented Lens trait impls (from ~24)              |
| 4 | Modules         | 4.0/5.0   | score   | 0.04   | Mean module maturity level                           |
| 5 | Tests           | 1000      | count   | 0.11   | Total test count across all modules                  |
| 6 | Hypotheses      | 150       | count   | 0.07   | Breakthrough theorem count                           |
| 7 | DSE             | 322       | count   | 0.06   | DSE domain TOML coverage                             |
| 8 | Experiments     | 50        | count   | 0.05   | Verification experiment count                        |
| 9 | Calculators     | 50        | count   | 0.04   | Rust/Python calculator count                         |
|10 | CrossResonance  | 100       | count   | 0.05   | Cross-domain resonance discoveries                   |
|11 | KnowledgeGraph  | 500       | count   | 0.05   | Graph nodes in knowledge base                        |
|12 | RedTeam         | 100       | count   | 0.06   | Adversarial challenge count                          |
|13 | Atlas           | 2000      | count   | 0.05   | Math atlas constant entries                          |
|14 | Documentation   | 90%       | percent | 0.03   | Doc coverage and quality                             |
|15 | Integration     | 50        | count   | 0.07   | Cross-module integration tests                       |
|16 | NeuromorphicAccelerator | 13 | count   | 0.06   | Akida-backed ω-cycle layers active (1-11 + δ + θ)    |

### Dimension 16 — `neuromorphic_accelerator`

**Mechanism**: BrainChip Akida (AKD1000 on Raspberry Pi 5 Dev Kit) provides
hardware-side spike-event entropy, inference, anomaly detection, and
counterfactual replay primitives. Each integrated layer (β qrng, γ bridge,
host pool, edge dispatch, α absorbed re-encoding, tier_1 promotion gate,
honesty_triad verify, correlation strict, γ fact verify, prompt-injection
sentinel, δ-spatial noise, δ-feedback cross-stratum, θ counterfactual)
contributes one count unit toward the 13-layer target.

**Measurement metric**:
- Count of `bridge_*.hexa` / `*_grower.rs` modules wired to a `raspberry-akida`
  resource entry (`hive-resource ls --accelerator akida`).
- Cross-validated against `AKIDA_OMEGA_CYCLE_LAYERS.md` § "통합 13+ layer 카탈로그".
- Floor: 0 (Akida absent / not bootstrapped). Ceiling: 13+ as new layers surface.

**analysis_grower candidate modules** (Layer 3 placement):
- `neuromorphic_grower.rs` (new) — `NeuromorphicState`, `LayerStatus`,
  `NeuromorphicGrowthPlan`. Scans `.resource` for `accelerator: akida` host,
  enumerates bridge modules, classifies each as `Active` / `DefaultInactive` /
  `Planned` / `Missing`, and emits per-layer activation actions.
- Reuses `module_grower.rs` maturity classifier for the per-layer modules.
- Drives `scripts/grow_neuromorphic.sh` (planned) for kick-fire activation.

**Cross-ref**: `AKIDA_OMEGA_CYCLE_LAYERS.md` (companion doc, this commit).

## Rust Modules (14 files in `src/growth/`)

| File                   | Key Types                                          | Purpose                                |
|------------------------|----------------------------------------------------|----------------------------------------|
| `mod.rs`               | (re-exports)                                       | Module root with architecture overview |
| `metrics.rs`           | `NexusMetrics`, `MetricsDelta`                     | System health snapshot collection      |
| `benchmark.rs`         | `BenchmarkResult`, `BenchmarkSuite`                | Micro-benchmark core operations        |
| `tracker.rs`           | `GrowthTracker`, `GrowthTargets`, `GrowthTrend`   | History tracking and trend analysis    |
| `planner.rs`           | `GrowthPlan`, `GrowthAction`                       | Synthesize prioritized action plans    |
| `registry.rs`          | `GrowthRegistry`, `GrowthDimension`, `DimensionState` | Central 15-dimension registry      |
| `architect.rs`         | `ArchGap`, `ArchPlan`, `ModuleStatus`              | Structural gap discovery               |
| `lens_grower.rs`       | `LensGrowthState`, `LensGrowthPlan`, `LensToImplement` | Lens implementation gap analysis  |
| `module_grower.rs`     | `ModuleMaturity`, `ModuleInfo`, `ModuleGrowthPlan` | Module maturity classification         |
| `hypothesis_grower.rs` | `BTState`, `BTCandidate`, `BTGrowthPlan`           | BT gap analysis and candidate gen      |
| `experiment_grower.rs` | `ExperimentState`, `ExperimentToCreate`             | Experiment coverage planning           |
| `resonance_grower.rs`  | `ResonanceState`, `ResonanceSearch`                | Cross-domain resonance expansion       |
| `atlas_grower.rs`      | `AtlasState`, `AtlasEntry`, `AtlasGrowthPlan`     | Math atlas coverage expansion          |
| `redteam_grower.rs`    | `RedTeamState`, `ChallengeToCreate`                | Red team challenge coverage            |

## Shell Scripts (16 files in `scripts/`)

| Script                     | Usage                                                      | Description                              |
|----------------------------|------------------------------------------------------------|------------------------------------------|
| `auto_grow.sh`             | `./auto_grow.sh [--cycles N] [--dry-run] [--skip-commit]` | Main auto-growth loop                    |
| `nexus_growth_daemon.sh`  | `./nexus_growth_daemon.sh [--interval MIN] [--max-cycles N] [--dimension DIM] [--dry-run]` | Master coordinator for all 15 dimensions |
| `grow_lens.sh`             | `./grow_lens.sh <lens_name>`                               | Implement a single lens via Claude CLI   |
| `grow_lenses.sh`           | `./grow_lenses.sh [--batch N] [--dry-run]`                 | Batch lens implementation                |
| `grow_modules.sh`          | `./grow_modules.sh [--target MODULE] [--upgrade-all-stubs] [--dry-run]` | Module maturity upgrade        |
| `grow_architecture.sh`     | `./grow_architecture.sh [--dry-run] [--max-actions N]`     | Architecture gap repair                  |
| `grow_tests.sh`            | `./grow_tests.sh [module_name]`                            | Add tests to under-tested modules        |
| `measure.sh`               | `./measure.sh`                                             | Collect metrics as JSON                  |
| `growth_dashboard.sh`      | `./growth_dashboard.sh [--live] [--last N]`                | ASCII dashboard of all dimensions        |
| `growth_report.sh`         | `./growth_report.sh [--last N]`                            | Growth history trend table               |
| `growth_daily_report.sh`   | `./growth_daily_report.sh [--days N] [--output FILE]`      | Daily summary from growth log            |
| `growth_intelligence.sh`   | (called by daemon)                                         | Adaptive strategy from past patterns     |
| `growth_notify.sh`         | `./growth_notify.sh "message" [--level info\|warn\|error]` | macOS/terminal/log notification          |
| `health_check.sh`          | `./health_check.sh [--quiet] [--start-if-dead]`            | Daemon liveness check                    |
| `install_autonomous.sh`    | `./install_autonomous.sh [--uninstall]`                    | Install launchd + cron + git hooks       |
| `troubleshoot_update.sh`   | `./troubleshoot_update.sh --record-failure\|--auto-fix\|--report` | Auto-record and fix failures       |

## Quick Start

```bash
# NEXUS HEXA 엔진
# mk2_hexa/native/*.hexa — HEXA 네이티브 실행

# Check current health
./scripts/measure.sh | python3 -m json.tool

# View growth dashboard
./scripts/growth_dashboard.sh

# Run one growth cycle (dry run)
./scripts/auto_grow.sh --cycles 1 --dry-run

# Start the daemon (30-min intervals, max 10 cycles)
./scripts/nexus_growth_daemon.sh --interval 30 --max-cycles 10

# Install full autonomous setup (launchd + cron)
./scripts/install_autonomous.sh
```

## Troubleshooting

| Problem                          | Solution                                                |
|----------------------------------|---------------------------------------------------------|
| Daemon not running               | `./scripts/health_check.sh --start-if-dead`             |
| Claude CLI not found             | `export CLAUDE_CLI=/path/to/claude` before running      |
| Tests fail after growth          | `./scripts/troubleshoot_update.sh --auto-fix`           |
| Cargo build fails                | `cd tools/nexus && ~/.cargo/bin/cargo check 2>&1`      |
| Growth log missing               | Created automatically on first `measure.sh` run         |
| Dimension stuck at 0%            | Check daemon logs: `tail -20 scripts/growth_log.jsonl`  |
| Too many warnings                | `./scripts/grow_architecture.sh --max-actions 6`        |
