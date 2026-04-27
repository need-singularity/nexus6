# n6_arithmetic

Canonical arithmetic SSOT for the n6 codebase. Replaces ~14 kLOC of scattered
ad-hoc reimplementations of `sigma`, `tau`, `sopfr`, `euler_phi`, etc.

Stdlib-only. No sympy, no numpy. Doctest-verified.

## Import

```python
from n6_arithmetic import (
    divisors, sigma, tau, euler_phi, min_prime_factor,
    sopfr, jordan_totient_2, mobius, is_perfect,
    n6_constants, assert_n6_master_identity,
    oeis_seq, perfect_number_search,
)

assert sigma(6) == 12
assert tau(6) == 4
assert euler_phi(6) == 2
assert sigma(6) * euler_phi(6) == 6 * tau(6) == 24   # n=6 master identity
```

## API

| function | OEIS | description |
|---|---|---|
| `divisors(n)`            | A000027 (ordered) | sorted positive divisors |
| `sigma(n, k=1)`          | A000203 (k=1)     | sigma_k(n) = sum d^k for d|n |
| `tau(n)`                 | A000005           | number of divisors (= sigma(n,0)) |
| `euler_phi(n)`           | A000010           | Euler totient |
| `min_prime_factor(n)`    | —                 | smallest prime factor (n >= 2) |
| `sopfr(n, with_mult=True)` | A001414 / A008472 | sum of prime factors |
| `jordan_totient_2(n)`    | A007434           | J_2(n) = n^2 prod (1 - 1/p^2) |
| `mobius(n)`              | A008683           | Mobius function |
| `is_perfect(n)`          | —                 | sigma(n) == 2n |
| `n6_constants()`         | —                 | canonical {sigma:12, tau:4, phi:2, sopfr:5, J2:24, ...} |
| `assert_n6_master_identity()` | — | raises if sigma(6)*phi(6) != 6*tau(6) |
| `oeis_seq(name, n_max=12)` | — | first n_max terms of A000005/010/203/008683/001414 |
| `perfect_number_search(upper=1_000_000)` | — | sanity helper, returns [6, 28, 496, 8128, ...] |

## Self-test

```
python3 lib/n6_arithmetic/n6_arith.py --self-test
```

Runs:
1. doctest sweep (every public function)
2. n=6 master identity assertion
3. perfect_number_search(10000) == [6, 28, 496, 8128]
4. sigma(10**6) benchmark (must be < 200 ms)
5. oeis_seq("A000203", 12) regression check

Prints `__N6_ARITH__ PASS` on success.

## Benchmark (laptop reference)

| call              | first-time | cached |
|---|---|---|
| `sigma(10**6)`    | < 5 ms     | < 1 us |
| `sigma(10**9)`    | < 50 ms    | < 1 us |
| `tau(10**6)`      | < 5 ms     | < 1 us |

`sigma`, `tau`, `divisors`, `euler_phi`, `sopfr`, and the private
`_prime_factorization` are memoized via `functools.lru_cache(maxsize=10000)`.

## n=6 master identity

The unique solution n >= 2 of  sigma(n) * phi(n) == n * tau(n)  is n=6:

```
sigma(6) = 1 + 2 + 3 + 6 = 12
phi(6)   = |{1, 5}|       = 2
tau(6)   = |{1, 2, 3, 6}| = 4
J_2(6)   = 36 * (1 - 1/4) * (1 - 1/9) = 24

12 * 2 == 6 * 4 == J_2(6) == 24
```

Falsifies cleanly at the first three other perfect numbers (28, 496, 8128).

## Migration plan (not done in this commit)

The four scattered copies still exist and are NOT touched:

- `n6/n6_constants.hexa`
- `n6/n6_constants.jsonl`
- `cli/blowup/lib/n6_constants_loader.hexa`
- `calc/n6_new_constants.json`

A later sweep will rewrite each to delegate to `n6_arithmetic.n6_constants()`.

## HEXA wrapper

`n6_arith.hexa` ships the SSOT-mirrored constants and `assert_master_identity`.
Full delegation to the Python API is gated on a hexa<->python bridge
convention that does not yet exist; see the file's `TODO(bridge)` block.
