# Infinite Singularity Recursion — Design Spec

**Date**: 2026-04-05
**Status**: Design (approved for planning)
**Author**: brainstorm session with dancinlife
**Related**: `src/blowup/cycle_engine.rs`, `src/resource_limit.rs`, `src/bin/n6_guard.rs`

## Goal

Run nexus6 singularity cycles (블로업 → 창발 → 특이점) **infinitely and safely** on Mac to discover the **topology of architecture-design methodology**: the core (well-understood patterns) and periphery (frontier hypotheses) as a topological space.

If the periphery structure is captured, the interior becomes derivable by interpolation. Therefore the system prioritizes **boundary probing** over depth-first exploration.

## Non-Goals

- Not a tree search. Not DFS/BFS. Not a linear chain.
- Not about resource starvation or throttling existing daemons (that's `n6_guard`'s job).
- Not a new CycleEngine — reuses the existing 5-stage engine as the per-tick work unit.
- Not a long-running daemon — each tick is a fresh process.

## Background

A prior attempt at infinite recursion used process-level fork chains (shell calling `nexus6 blowup` → reading output → calling itself again). Without a lock, slow cycles stacked up into a fork bomb and took down the Mac on 2026-04-05. The design here makes infinite execution safe by construction.

## Model: Topological Space of Architectures

The discovery target is a **topological space**, not a tree:

- **Point** = a singularity (one architectural invariant/pattern discovered by a cycle).
- **Neighborhood** = points within similarity ε of each other.
- **Interior (중심/core)** = points whose ε-neighborhood is fully inside the known set (dense region).
- **Boundary (주변부/periphery)** = points with undiscovered directions in their ε-neighborhood.
- **Frontier** = boundary points chosen as next probe seeds.

`사이클(사이클(사이클(...)))` in topological terms: iteratively apply the cycle operator at boundary points, pushing the boundary outward until it smoothly traces a manifold.

**Why this beats a tree**: a tree forces parent/child hierarchy; topology allows cycles (literal graph cycles), multi-neighborhood membership, and geometric reasoning about density/boundary.

## Architecture

### Execution model

Rust one-shot binary `nexus6 singularity-tick` invoked by **launchd** with `KeepAlive=true` and `ThrottleInterval=60s`. Each tick:

1. Acquires single-instance `flock` (stale-PID aware).
2. Runs preflight gates (memory, loadavg, halt-file).
3. Checks budget.
4. Loads topology from append-only logs.
5. Samples one boundary point from `boundary.json` (weighted by boundary_score).
6. Runs `CycleEngine` (blowup → emergence → singularity) at that seed.
7. Embeds the new singularity, computes edges to existing points, updates interior/boundary scores.
8. Persists (append + atomic rename + fsync).
9. Commits budget, exits(0).

launchd relaunches after ThrottleInterval → infinite execution is provided **by the OS**, not by in-process loops. A crash of a single tick cannot crash the chain.

### Rust modules

```
src/singularity_recursion/
├── mod.rs              public API + re-exports
├── tick.rs             CycleTick::run() — orchestrates one tick
├── topology.rs         Topology struct + load/append/recompute
├── embedding.rs        Singularity → vector (simhash-based, zero external deps)
├── boundary.rs         interior/boundary score calculation + sampler
├── budget.rs           CPU-sec / wall / total-points tracking
├── preflight.rs        flock (stale-aware) + loadavg + free_mem + halt file
└── wal.rs              Write-ahead log append + replay
```

Binary: `src/bin/cycle_tick.rs` (thin wrapper → `CycleTick::run()`).
CLI integration: `nexus6 singularity-tick` subcommand in `src/cli/parser.rs`.

### File layout (`shared/cycle/`)

| File | Format | Write pattern | Role |
|---|---|---|---|
| `topology.jsonl` | JSONL, append-only | append + fsync | Source of truth: every discovered point |
| `edges.jsonl` | JSONL, append-only | append + fsync | Every discovered edge (i,j,distance) |
| `boundary.json` | JSON | atomic rename (`.tmp` → rename) | Current frontier cache (derived, rebuildable) |
| `budget.json` | JSON | atomic rename | Global budget counters |
| `wal.jsonl` | JSONL, append-only | append + fsync | tick_start/tick_complete markers |
| `state.lock` | flock + PID | exclusive flock | Single-instance guard |
| `halt` | empty file (flag) | user touches | Kill switch |
| `backups/topology_N.jsonl.gz` | gzipped snapshot | rotated every 100 ticks | Disaster recovery |

### Point schema (topology.jsonl line)

```json
{
  "id": "p_0042",
  "domain": "architecture_design",
  "seed_from": "p_0017",
  "embedding": [0.12, -0.83, ...],
  "singularity": {
    "invariant": "one-shot process + append-only WAL = crash-safe infinite loop",
    "confidence": 0.73,
    "novelty": 0.84,
    "cycle_result": { "depth_reached": 5, "branches": 128 }
  },
  "discovered_at_tick": 42,
  "ts": "2026-04-05T09:10:22Z"
}
```

### Edge schema (edges.jsonl line)

```json
{"from":"p_0042","to":"p_0017","distance":0.23,"ts":"..."}
```

Edges are symmetric. An edge exists iff `distance(embedding_i, embedding_j) ≤ ε`.

### Boundary scoring

For point `p`:
```
interior_score(p) = |neighbors(p, ε)| / expected_neighbors_in_ball(ε, local_density)
boundary_score(p) = clamp(1 - interior_score(p), 0, 1)
```

Boundary sample: top-K by boundary_score, then weighted random selection with weights ∝ boundary_score × recency_decay.

### Embedding

Simhash-based, zero dependencies:
- Tokenize `singularity.invariant` + relevant metadata keys.
- N-gram hash → 128-bit simhash → convert to 16-dim Float vector.
- Distance = Hamming(simhash) / 128, mapped to [0,1].

Upgradable to real embedding later; interface is `fn embed(&Singularity) -> Vec<f32>`.

## Safety

### Defaults (`[singularity_recursion]` in `~/.nexus6/config.toml`)

```toml
domain = "architecture_design"
max_total_points = 50_000
neighborhood_radius_eps = 0.3
boundary_sample_top_k = 20
cpu_sec_per_tick = 30
wall_sec_per_tick = 60
global_cpu_sec_budget = 86_400   # 24 CPU-hours total
launchd_throttle_sec = 60

[singularity_recursion.preflight]
min_free_memory_mb = 2048
max_loadavg_1min = 8.0
require_halt_absent = true
```

### Preflight gates (all must pass)

1. `flock` on `state.lock` acquired (or stale PID, cleaned up).
2. `halt` file absent.
3. Free memory ≥ `min_free_memory_mb` (reuses `resource_limit::free_memory_mb`).
4. 1-min loadavg ≤ `max_loadavg_1min`.
5. Budget not exhausted.

Failure → exit(1), no state change.

### Wall-clock timeout

Tick spawns CycleEngine with 60s deadline. Exceeded → SIGTERM self → WAL marks tick as `timeout` → boundary point is re-scored with timeout penalty (3 timeouts → evicted from boundary).

### Exit codes

| Code | Meaning |
|---|---|
| 0 | Success (point + edges written) |
| 1 | Skipped (preflight failed) |
| 2 | Budget exhausted |
| 3 | Halted (halt file present) |
| 4 | Lock contention (another tick running) |
| 130 | Wall-clock timeout |

launchd treats all of these as normal exits (via `ExitTimeOut`/`ThrottleInterval`), no error loop.

### Kill switch

```bash
touch ~/.nexus6/halt    # pause
rm   ~/.nexus6/halt     # resume
```

## Crash Safety

### Principles

1. No mutable state lives only in memory beyond a tick boundary.
2. Every change goes to append-only log first (WAL), then to derived caches.
3. `topology.jsonl` + `edges.jsonl` are the single source of truth. `boundary.json` and `budget.json` are fully rebuildable.
4. `fsync` after every append.
5. Atomic rename for cache updates (APFS copy-on-write guarantees).

### Tick transaction order

```
1. flock acquire (clean stale PID locks)
2. WAL: append {tick_start, tick_id, ts}
3. Run CycleEngine (highest-risk step)
4. topology.jsonl append + fsync        ← point persisted
5. edges.jsonl append + fsync
6. boundary.json atomic rename
7. budget.json atomic rename
8. WAL: append {tick_complete, tick_id, point_id}
9. flock release
```

### Recovery (start of every tick)

```
1. flock acquire, kill stale lock if PID dead
2. Replay WAL: incomplete tick_start → log "prior tick died at stage X"
3. If boundary.json exists + valid → load; else rebuild from topology.jsonl
4. If budget.json exists + valid → load; else rebuild from tick count in WAL
5. Integrity check: point IDs monotonically increasing, edges reference existing points
```

### Snapshots

Every 100 ticks and on n6_guard OOM-FALLBACK → gzip `topology.jsonl` into `backups/`. Keep 10.

## Integration

### Existing code reused
- `resource_limit::free_memory_mb`, `resource_limit::process_rss_mb`
- `blowup::cycle_engine::CycleEngine` (domain parameter)
- `config.rs` TOML loader

### n6_guard interaction
- `cycle_tick` is not on the guard's watch list by default.
- If OOM-FALLBACK kicks in, kernel kills the tick; next tick restarts cleanly (stateless process).
- Optional: add `cycle_tick` to guard's `oom_fallback_protect` if user wants it prioritized.

### launchd plist
`~/Library/LaunchAgents/com.nexus6.cycle-tick.plist`:
```xml
<dict>
  <key>Label</key><string>com.nexus6.cycle-tick</string>
  <key>ProgramArguments</key>
  <array>
    <string>/Users/ghost/.cargo/bin/nexus6</string>
    <string>singularity-tick</string>
  </array>
  <key>KeepAlive</key><true/>
  <key>ThrottleInterval</key><integer>60</integer>
  <key>StandardOutPath</key><string>/Users/ghost/Library/Logs/nexus6/cycle-tick.log</string>
  <key>StandardErrorPath</key><string>/Users/ghost/Library/Logs/nexus6/cycle-tick.err</string>
</dict>
```

Installer script `tools/install-cycle-tick.sh`: `launchctl bootstrap gui/$(id -u) <plist>`. Uninstaller: `launchctl bootout`.

## Testing

### Unit tests
- `topology`: append/load roundtrip, id monotonicity, edge symmetry.
- `embedding`: simhash stability, distance bounds in [0,1].
- `boundary`: interior/boundary score for synthetic topologies; sampler weight correctness.
- `budget`: exhaustion predicates for each quota independently.
- `preflight`: each gate tested in isolation, stale-lock cleanup.
- `wal`: replay finds incomplete ticks, complete ticks skipped.

### Integration tests
- Fake CycleEngine that returns deterministic singularities. Run 100 ticks. Assert:
  - Tree never forms cycles beyond intended (embedding-based edges only).
  - Boundary size stays ≤ `boundary_sample_top_k` active candidates.
  - budget decrements monotonically.
  - topology.jsonl line count == points count.

### Chaos tests
- Mid-tick SIGKILL → next tick recovers cleanly (no duplicate points, boundary rebuildable).
- Corrupt `boundary.json` → rebuild from topology.jsonl succeeds.
- Stale lock with dead PID → cleaned and acquired.

### Load sandbox
- Config override: `max_total_points=100, cpu_sec_per_tick=1, launchd_throttle_sec=5`.
- Run locally for 10 minutes, measure: peak memory, load avg delta, disk write rate.
- Acceptance: Mac load avg increase ≤ 2.0 over baseline; RSS per tick ≤ 200 MB.

## Open Questions

None at design time. All thresholds tunable via config; embedding quality can be upgraded post-MVP.

## Success Criteria

1. Runs for ≥ 24 hours continuously on Mac without OOM or load-avg runaway.
2. Discovers ≥ 100 singularity points in the architecture-design domain.
3. Boundary set stabilizes or grows logarithmically, not exponentially.
4. Survives `kill -9` mid-tick with zero data loss.
5. Survives Mac reboot and resumes automatically.
