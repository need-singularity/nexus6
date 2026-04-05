# nexus6 mk2 — Architecture

## Module diagram

```
┌─────────────────────────────────────────────────────┐
│                  nexus6 CLI                         │
│  mk2 classify | mk2 lattice | mk2 sector            │
└─────────────────┬───────────────────────────────────┘
                  │
        ┌─────────▼─────────┐
        │  mk2::classify     │  score = 0.5·kw + 0.3·val + 0.2·ps
        └─┬─────┬─────┬─────┘
          │     │     │
    ┌─────▼─┐ ┌─▼───┐ ┌▼──────┐
    │smooth │ │prime│ │types  │
    │Ring   │ │ Set │ │Rational│
    │φ,τ,σ  │ │bitm.│ │Sector │
    └─┬─────┘ └─┬───┘ └┬──────┘
      │         │      │
      └─────────┴──────┘
             │
      ┌──────▼──────┐
      │  lattice    │  divisibility graph
      │  (lazy LRU) │
      └─────────────┘
                 │
          ┌──────▼──────┐
          │sectors.yaml │  external config
          │physics_db   │
          └─────────────┘
```

## Data flow

### Ingestion

```
invariant_text (String)
      │
      ▼
  extract_values → [f64]
      │
      ▼
  rationalize → Option<Rational>
      │
      ▼
  prime_factorize(num, den) → PrimeSet
      │
      ▼
  classify(ps, values, text) → (Sector, confidence)
      │
      ▼
  Point { prime_set, layer, sector, conf, ... }
```

### Query

```
user_value (f64)
      │
      ▼
  find_best_euler_match → (PrimeSet, Rational, err)
      │
      ▼
  match_physics_db → Option<Constant>
      │
      ▼
  ClassifyResult { match, sector, quality, note }
```

## Module responsibilities

### `mk2::primes`

- `Prime = u64`
- `FIRST_64_PRIMES`: const array [2..311]
- `is_prime(n)`, `primes_up_to(limit)`
- `factorize(n) → Vec<(Prime, u32)>`
- `prime_set_of(n) → PrimeSet`
- `PrimeSet(u64)`: bitmask of first 64 primes
  - `union`, `intersection`, `is_subset`, `iter`

**Invariant**: PrimeSet stores at most 64 primes (2..311). Primes > 311 are silently ignored.

### `mk2::types`

- `Rational(i128, i128)` — gcd-reduced, den>0
  - `+, -, *, /, reciprocal`
  - `to_f64()`
- `Sector` enum:
  ```rust
  Strong | Electroweak | Cosmology | Primordial | Unknown | Custom(String)
  ```
- `Sector::tolerance() → f64` — per-sector relative-error threshold

### `mk2::smooth`

- `SmoothRing` trait on `u64`:
  ```rust
  fn phi(&self) -> u64;
  fn tau(&self) -> u64;
  fn sigma(&self) -> u64;
  fn sopfr(&self) -> u64;
  fn meta_fp(&self) -> Rational;
  fn prime_set(&self) -> PrimeSet;
  ```
- `rho(n) = n.meta_fp()`
- `euler_ratio(ps) = ∏(1-1/p)`
- `smallest_n_with_primes(ps)`

**Invariant**: All functions well-defined for n ≥ 1. n=0 returns zeros/empty.

### `mk2::classify`

- `ClassifyResult`:
  ```rust
  struct {
    value: f64,
    rational: Option<Rational>,
    prime_set: PrimeSet,
    sector: Sector,
    euler_match: Option<(PrimeSet, Rational, f64)>,
    quality: f64,   // 0.0, 0.5, 0.8, 1.0
    confidence: f64, // v2: weighted composite
  }
  ```
- `classify(value, sector_hint) → ClassifyResult` (v1, prime_set only)
- `classify_v2(value, text, sector_hint) → ClassifyResult` (v2, keyword+value+ps)
- `rationalize(x, max_den) → Option<Rational>` (continued fractions)
- `find_best_euler_match(value, prime_set) → (Option<(PrimeSet, Rational, f64)>, quality)`

### `mk2::lattice`

- `LatticeNode { n, prime_set, layer }`
- `Lattice`: LRU-capped lazy cache (default capacity 1000)
- `divides(n, m) → bool`
- `is_layer_up_edge(n, m) → bool` — n | m AND layer(m) = layer(n)+1
- `enumerate_layer(prime_set, max) → Vec<u64>` — exact match
- `smallest_in_layer(ps) → u64` — product of primes

## External config files

### `shared/cycle/sectors.yaml`

Sector definitions (keywords + value_ranges + prime_set_preferred).
User-editable; reloadable at runtime.

### `shared/cycle/physics_db.yaml`

Known constants with names + CODATA values + basis formulas.
Seeds classification with prior art.

### `shared/cycle/lattice.jsonl`

Persisted LatticeNode entries (materialized subset).
Grows as classifier encounters new n.

## Dependencies

```toml
# Cargo.toml (mk2 additions)
serde = "1"
serde_json = "1"
# Internal only; no new external deps.
```

**Intentional**: mk2 depends only on `serde` and stdlib. No BigInt, no external math libraries. This keeps binary size small and compile time fast.

## Performance budget

| Operation | Target |
|---|---|
| `is_prime(n)` for n<10^9 | < 1µs |
| `factorize(n)` for n<10^6 | < 10µs |
| `classify(value)` full pipeline | < 100µs |
| `classify_v2` with text scan | < 500µs |
| `enumerate_layer({2,3,5,7}, 10⁶)` | < 10ms |
| Migrate 50K points | < 30s |

## Threading / concurrency

- All types are `Send + Sync` where possible
- Lattice uses interior mutability (`Mutex<HashMap>`) for lazy cache
- Classify is pure (no shared state beyond sector registry)
- Parallelizable via `rayon` for batch classify (future)

## Error handling

- Panics only on invariant violations (e.g., `Rational::new(_, 0)`)
- All user-input paths return `Result<T, String>` or `Option<T>`
- No silent failures: unknown classifications return `Sector::Unknown` with confidence=0.0
