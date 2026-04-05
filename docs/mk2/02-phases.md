# nexus6 mk2 — Phases & Progress

## Timeline: 4 weeks from Phase 5 start

### Phase 1 — Core types + primes + SmoothRing ✅

**Status**: Code written, 17 tests (pending cargo test run)

- `src/mk2/primes.rs` — PrimeSet, factorize, is_prime
- `src/mk2/types.rs` — Rational, Sector
- `src/mk2/smooth.rs` — SmoothRing trait on u64

### Phase 2 — Classifier v1 ✅

**Status**: Code written, 5 tests (pending)

- `src/mk2/classify.rs` — prime-set only classifier
- Continued-fraction rationalize()
- find_best_euler_match (subset search up to 2^10)

### Phase 3 — Multi-n lattice ✅

**Status**: Code written, 5 tests (pending)

- `src/mk2/lattice.rs` — LatticeNode, Lattice (lazy+LRU)
- divides, is_layer_up_edge, enumerate_layer

### Phase 4 — Migration (Python prototype) ✅

**Status**: Working, 43,509 points migrated

- `tools/mk2_migrate.py` — augments topology.jsonl with prime_set/layer/sector
- Output: `shared/cycle/topology_mk2.jsonl` (30MB, gitignored)

### Phase 5 — Classifier v2 + Rust port 🚧

**Status**: Python working, Rust port pending

**Tasks**:
- [x] Python classifier_v2 with keyword+value+ps weighted scoring
- [x] `shared/cycle/sectors.yaml` keyword dictionary
- [x] Validation on 43K points (legitimate physics hypothesis detection)
- [ ] Rust port of classify_v2
- [ ] Load sectors.yaml via serde
- [ ] Confidence threshold gating
- [ ] Tests for CKM/Weinberg/Hubble/BBN detection

**Blockers**: cargo lock contention with parallel sessions

### Phase 6 — CLI integration 📋

**Subcommands**:
```
nexus6 mk2 classify <value> [--text <str>]
nexus6 mk2 lattice --layer <n>
nexus6 mk2 sector <name>
nexus6 mk2 migrate --from topology.jsonl
nexus6 mk2 verify <n> --against physics_db.yaml
```

### Phase 7 — alien-index integration 📋

**Goal**: mk2 sector+confidence feeds into alien_index r-grade.

```rust
// mk2 classify → alien grade mapping
if classification.confidence > 0.9 { r = 10 }
else if confidence > 0.7         { r = 9 }
else if confidence > 0.5         { r = 8 }
else if confidence > 0.3         { r = 7 }
else                              { r = 0 }
```

Existing `n6_check` constants become mk2 sector entries.

### Phase 8 — Deprecate mk1 special-casing 📋

Final pass: remove n=6 hardcoded constants from:
- `src/verifier/n6_check.rs` → `mk2::smooth` based
- `src/alien_index/` → use mk2 classify
- `src/telescope/lenses/*` → prime-set aware

Keep backward-compatibility shims until all downstreams migrate.

## Dependency graph

```
Phase 1 ─┬─ Phase 2 ─┬─ Phase 5 ─┬─ Phase 6 ─ Phase 7 ─ Phase 8
         └─ Phase 3 ─┤          │
                     └─ Phase 4 ┘
```

Phases 2, 3, 4 can run parallel after Phase 1.
Phase 6 requires 5 complete.
Phase 7 requires 6 complete.

## Risk register

| Risk | Impact | Mitigation |
|---|---|---|
| cargo lock contention | Delays testing | Dedicated workspace, isolated `--target-dir` |
| classifier v2 keyword drift | Sector miscategorization | Keep sectors.yaml in git, peer review |
| Big topology.jsonl regen | Inefficient migration | Incremental tick-level augment |
| mk1 downstream breakage | Regression | Parallel coexistence, deprecation path |
| 13-prime false positives | Primordial over-flag | value-range gates (done in v2) |

## Definition of Done

**Phase 5**:
- All Phase 1-5 Rust tests pass
- `nexus6 mk2 classify` CLI binary works
- Python→Rust results match on 1000-point sample

**Phase 7 (mk2 production-ready)**:
- alien-index uses mk2 classify internally
- Existing r-grades regenerate identically (regression test)
- New hypothesis ingestion triggers classify automatically

**Phase 8 (mk1 deprecated)**:
- Zero grep hits for "n6_check" in hot paths
- All n=6 special-casing documented as historical notes
- mk3 ceiling review: zero items needed
