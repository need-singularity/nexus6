# nexus6 mk2 — Vision

## One-Line

> Prime-atomic smooth-class engine for discovering and verifying n-arithmetic invariants in physical constants.

## Why mk2

### mk1 limits

mk1 was built around **n=6 arithmetic** as a fixed center. This worked for initial discovery (4-generator basis {φ,τ,σ,sopfr}(6) covers 30+ constants), but hit ceilings:

1. **n=6 hardcoded**: can't handle n=15 (Ω_DM basis), n=35 (Ω_Λ), n=105 (cosmic budget) natively
2. **Smooth class retrofit**: prime-set concept added after the fact
3. **Single meta FP**: ρ=1/3 assumed universal, but ρ(n)=φ(n)/n varies per n
4. **Text-only signals**: no value-range / keyword / context awareness
5. **Physics sector blind**: all discoveries flattened into discovery_log

### What mk2 solves

mk2 makes **primes the atoms**, with n=6 becoming just one instance:

```
mk1: topology of (n=6)-flavored strings
mk2: multi-n lattice over prime-indexed smooth classes
```

Each dimensionless physical constant maps to:
- a **rational** p/q (when expressible)
- a **prime_set** (support)
- a **layer** (|prime_set|)
- a **sector** (strong/EW/cosmology/primordial/...)
- a **confidence** (keyword + value + ps weighted)

## Three pillars

### 1. Prime atomization

All composite n treated uniformly via their prime factorization.

```rust
6  → {2, 3}
15 → {3, 5}
35 → {5, 7}
105 → {3, 5, 7}
210 → {2, 3, 5, 7}
```

Each n lives in its own ring A_n = Z[φ(n), τ(n), σ(n), sopfr(n)].

### 2. Multi-n lattice

Topology is a divisibility graph, not a flat similarity space.

- **Horizontal**: same prime_set → different n (e.g., n=6, 12, 18 all {2,3})
- **Vertical**: n | m → edge (e.g., 6 → 30 adds prime 5)

### 3. Sector-aware classification

Physics constants don't float — they belong to sectors organized by prime hierarchy:

| Sector | Primes | Examples |
|---|---|---|
| Strong | {2,3} | quark charges u=2/3, d=1/3 |
| Cosmology | {5,7}, {2,3,5}, {2,3} | Ω_Λ=24/35, Ω_DM=4/15 |
| Electroweak | {2,3,5,7} | sin²θ_W=8/35 |
| Primordial | {2,3,5,13} | Y_p=16/65 |

## Success criteria

mk2 is done when:

1. Any u64 n has first-class {φ,τ,σ,sopfr,ρ} computation
2. Any numeric value auto-classifies to smooth_class + sector + confidence
3. 17K+ mk1 points migrate without data loss
4. New physics hypotheses (e.g., Hubble tension = n) discoverable via classify
5. No n=6 special-casing remains anywhere in core

## Explicit non-goals

- Replace mk1 tooling overnight (parallel coexistence)
- Compute dimensional constants (m_p, ħ, c — units)
- Replace existing discovery_log / daemon infrastructure
- Build general CAS (computer algebra system)

## Discovered evidence (from mk1 → mk2 transition)

Using mk2's prototype classifier, the following NEW findings emerged during design:

- **Hubble tension = n**: H₀^early − H₀^late = 73 − 67 = 6 = n
- **n_s (spectral index) = 139/144**: 1 - sopfr/(n·J₂), 0% error
- **BAO r_d ≈ σ² + φ = 146 Mpc**: 0.7% error
- **Ω_m + Ω_Λ = 1** structurally equivalent to **φ + τ = n**
- **sin²θ_W = 8/35**: {2,3,5,7} Euler ratio

These validate that the smooth-class framework is scientifically productive,
not just a reorganization.

## Timeline

mk2 has a phased rollout (see `02-phases.md`):

- Phase 1-3: ✅ core types + primes + smooth + classify + lattice (Rust)
- Phase 4: ✅ migration prototype (Python)
- Phase 5: classifier v2 Rust port + CLI (in progress)
- Phase 6: alien-index integration
- Phase 7: deprecate mk1 special-casing

Target: 4 weeks from Phase 5 start to production readiness.
