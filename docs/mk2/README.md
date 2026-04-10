# nexus mk2 documentation

## Read in order

1. **[00-vision.md](00-vision.md)** — Why mk2, what it solves, success criteria
2. **[01-architecture.md](01-architecture.md)** — Module design, data flow, interfaces
3. **[02-phases.md](02-phases.md)** — Phased rollout plan, risks, DoD

## Related

- **Design spec**: `../superpowers/specs/2026-04-06-nexus-mk2-design.md`
- **Code**: `src/mk2/`
- **Migration tool**: `tools/mk2_migrate.py`, `tools/mk2_classify_v2.py`
- **Sector config**: `shared/discovery/cycle/sectors.yaml`

## Quick reference

```rust
use nexus::mk2::*;

// Arithmetic on any n
assert_eq!(6u64.phi(), 2);
assert_eq!(105u64.sigma(), 192);

// Meta fixed point
assert_eq!(rho(6), Rational::new(1, 3));
assert_eq!(rho(35), Rational::new(24, 35));

// Euler ratio for a prime set
let ps = prime_set_of(35); // {5, 7}
assert_eq!(euler_ratio(&ps), Rational::new(24, 35));

// Classify a value
let result = classify(0.6847, None);
// → euler_match: ({5,7}, 24/35, err 0.0015)
// → sector: Cosmology
```

## Key insights discovered during mk2 design

| Finding | Formula |
|---|---|
| Hubble tension | 73 − 67 = 6 = n |
| Spectral index n_s | 1 − sopfr/(n·J₂) = 139/144 |
| BAO sound horizon | σ² + φ = 146 Mpc |
| Cosmic density sum | 4/15 + 24/35 + 1/21 = 1 |
| Weinberg angle | 8/35 = euler_ratio({2,3,5,7}) |
| Y_p (Helium) | 16/65 = euler_ratio({2,3,5,13}) |

All discovered by **iterating classifier prototype → finding misclassifications → refining spec**.

## Design principles

1. **Prime atoms, not n=6**: All composite n equal-footing.
2. **Type safety > text matching**: Rational arithmetic enforces claims.
3. **Keyword + value + prime_set**: single signal always incomplete.
4. **Self-correcting spec**: each prototype round refines the design.
5. **Minimal dependencies**: serde + stdlib only.
6. **Parallel with mk1**: no big-bang migration.
