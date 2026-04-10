# T2-03: Hypothesis 261 — Congruence Subgroup Classification Computation Analysis

> **Hypothesis 261**: The invariant system of Gamma_0(N) (index mu, elliptic points e2/e3, cusps c, genus g) is
> structurally connected to arithmetic functions like sigma(N), tau(N), phi(N) through
> a "forcing chain". In particular, for squarefree N, mu(N) = sigma(N) holds exactly.

**Verification Status**: 🟩 (pure arithmetic theorem) + 🟧 (chain structure observation)
**Golden Zone Dependence**: None (pure number theory/modular form theory)
**Tools**: `congruence_chain_engine.py`, `analyze_h261.py`

---

## 1. Background and Context

Gamma_0(N) is a congruence subgroup of the modular group SL(2,Z), a core object in number theory and modular forms.
For each N, the following invariants are determined:

- **mu(N)**: Index [SL(2,Z) : Gamma_0(N)] = N * prod_{p|N} (1 + 1/p)
- **c(N)**: Number of cusps = sum_{d|N} phi(gcd(d, N/d))
- **e2(N)**: Number of order-2 elliptic points
- **e3(N)**: Number of order-3 elliptic points
- **g(N)**: Genus = 1 + mu/12 - e2/4 - e3/3 - c/2

Hypothesis 261 classifies how these invariants connect with sigma(N), tau(N), etc. from a "forcing chain"
perspective.

---

## 2. Comprehensive Arithmetic Functions for Genus-0 N

Genus-0 N corresponds to rational modular curves parameterized by the j-invariant.
From N=1..100, **15** have genus 0:

```
  N = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 13, 16, 18, 25}
```

### Genus-0 Invariant Table

```
   N |    mu | sigma |      tau(N) |   phi | d(N) | mu=sig? | mu%12
  ----+-------+-------+-------------+-------+------+---------+------
   1 |     1 |     1 |           1 |     1 |    1 |   YES   |    1
   2 |     3 |     3 |         -24 |     1 |    2 |   YES   |    3
   3 |     4 |     4 |         252 |     2 |    2 |   YES   |    4
   4 |     6 |     7 |       -1472 |     2 |    3 |         |    6
   5 |     6 |     6 |        4830 |     4 |    2 |   YES   |    6
   6 |    12 |    12 |       -6048 |     2 |    4 |   YES   |    0
   7 |     8 |     8 |      -16744 |     6 |    2 |   YES   |    8
   8 |    12 |    15 |       84480 |     4 |    4 |         |    0
   9 |    12 |    13 |     -113643 |     6 |    3 |         |    0
  10 |    18 |    18 |     -115920 |     4 |    4 |   YES   |    6
  12 |    24 |    28 |     -370944 |     4 |    6 |         |    0
  13 |    14 |    14 |     -577738 |    12 |    2 |   YES   |    2
  16 |    24 |    31 |      987136 |     8 |    5 |         |    0
  18 |    36 |    39 |     2727432 |     6 |    6 |         |    0
  25 |    30 |    31 |   -25499225 |    20 |    3 |         |    6
```

**Observation**: mu = sigma for N = {1, 2, 3, 5, 6, 7, 10, 13} — exactly the squarefree ones.

---

## 3. Core Theorem: If N is squarefree, then mu(N) = sigma(N)

### Theorem (Pure Arithmetic, 🟩)

> If N is squarefree, then the index mu(N) of Gamma_0(N) equals the divisor sum sigma(N).

**Proof**:

Let N = p1 * p2 * ... * pk (each pi distinct primes).

```
  mu(N) = N * prod_{p|N} (1 + 1/p)
        = (p1 * p2 * ... * pk) * prod((1 + 1/pi))
        = prod(pi) * prod((pi + 1)/pi)
        = prod(pi + 1)

  sigma(N) = prod_{p|N} (1 + p)    [since squarefree, divisor sum of each prime = 1+p]
           = prod(pi + 1)

  Therefore mu(N) = sigma(N).  QED
```

**Verification**: All 61 squarefree N=1..100 match, all 39 non-squarefree don't match.
This is a 100% exact arithmetic theorem.

---

## 4. N with e2 > 0 AND e3 > 0 (both elliptic points exist)

Only **6** from N=1..100:

```
   N |    mu |   g |  e2 |  e3 | lcm(iso) | N mod 12
  ----+-------+-----+-----+-----+----------+---------
   1 |     1 |   0 |   1 |   1 |        6 |        1
  13 |    14 |   0 |   2 |   2 |        6 |        1
  37 |    38 |   2 |   2 |   2 |        6 |        1
  61 |    62 |   4 |   2 |   2 |        6 |        1
  73 |    74 |   5 |   2 |   2 |        6 |        1
  97 |    98 |   7 |   2 |   2 |        6 |        1
```

**Pattern**: N = 1 or N = prime and N ≡ 1 (mod 12).

**Reason** (provable):
- e2 > 0 ⟹ N has no factor of 4, and for each odd prime factor p, (-1/p) = 1 ⟹ p ≡ 1 (mod 4)
- e3 > 0 ⟹ N has no factor of 9, and for each prime factor p ≠ 3, (-3/p) = 1 ⟹ p ≡ 1 (mod 3)
- Chinese Remainder Theorem: p ≡ 1 (mod 4) AND p ≡ 1 (mod 3) ⟹ **p ≡ 1 (mod 12)**

**Conclusion**: lcm(isotropic orders) = lcm(1,2,3) = **6 = first perfect number**. All are squarefree so mu = sigma holds too.

---

## 5. N with mu(N) divisible by 12

From N=1..100, **65** have mu(N) ≡ 0 (mod 12).

Genus-0 with mu%12=0:

```
  N = {6, 8, 9, 12, 16, 18}  — all composite
  N=6:  mu=12, sigma=12, perfect number!
  N=8:  mu=12, sigma=15
  N=9:  mu=12, sigma=13
  N=12: mu=24, sigma=28
  N=16: mu=24, sigma=31
  N=18: mu=36, sigma=39
```

**Interpretation**: mu/12 is the "basic contribution" term in the genus formula. If mu%12=0, the genus formula cleanly yields an integer (even without other correction terms).

---

## 6. First Cusp Form Weight Pattern

```
  k = 12:  1   N = {1}      ← Delta(z), Ramanujan discriminant
  k =  8:  1   N = {2}
  k =  6:  2   N = {3, 4}
  k =  4: 11   N = {5,6,7,8,9,10,12,13,16,18,25}  ← remaining genus-0
  k =  2: 85   N = {11, 14, 15, ...}               ← genus >= 1
```

**ASCII Graph — First Cusp Weight Distribution**:

```
  k=2  |████████████████████████████████████████████████████  85
  k=4  |██████                                                11
  k=6  |█                                                      2
  k=8  |                                                       1
  k=12 |                                                       1
       +-----+-----+-----+-----+-----+-----+-----+-----+---
       0    10    20    30    40    50    60    70    80   90
```

**Interpretation**: Only N=1 has its first cusp form at k=12 — this is the Ramanujan Delta function.
Genus-0 N have k >= 4, genus >= 1 N have k = 2 (dim S_2 = g >= 1).

---

## 7. Forcing Chain Quality Grades

Grade criteria:
- **A**: lcm(iso) * cusps = sigma(N) exact match
- **B**: mu(N) = sigma(N) (squarefree) or lcm*d(N) = mu
- **C**: mu%12 = 0 and partial relations exist
- **D**: No special relations

### Genus-0 Grade Table

```
   N | mu  |  c | lcm | sig | d(N) | lcm*c | lcm*d | Grade | Rationale
  ----+-----+----+-----+-----+------+-------+-------+-------+------------------
   1 |   1 |  1 |   6 |   1 |    1 |     6 |     6 |   B   | mu=sig
   2 |   3 |  2 |   2 |   3 |    2 |     4 |     4 |   B   | mu=sig
   3 |   4 |  2 |   3 |   4 |    2 |     6 |     6 |   B   | mu=sig
   4 |   6 |  3 |   1 |   7 |    3 |     3 |     3 |   D   | weak relation
   5 |   6 |  2 |   2 |   6 |    2 |     4 |     4 |   B   | mu=sig
   6 |  12 |  4 |   1 |  12 |    4 |     4 |     4 |   B   | mu=sig + mu%12=0
   7 |   8 |  2 |   3 |   8 |    2 |     6 |     6 |   B   | mu=sig
  10 |  18 |  4 |   2 |  18 |    4 |     8 |     8 |   B   | mu=sig
  13 |  14 |  2 |   6 |  14 |    2 |    12 |    12 |   B   | mu=sig
   8 |  12 |  4 |   1 |  15 |    4 |     4 |     4 |   C   | mu/12=1
   9 |  12 |  4 |   1 |  13 |    3 |     4 |     3 |   C   | mu/12=1
  12 |  24 |  6 |   1 |  28 |    6 |     6 |     6 |   C   | mu/12=2
  16 |  24 |  6 |   1 |  31 |    5 |     6 |     5 |   C   | mu/12=2
  18 |  36 |  8 |   1 |  39 |    6 |     8 |     6 |   C   | mu/12=3
  25 |  30 |  6 |   1 |  31 |    3 |     6 |     3 |   D   | weak relation
```

### Grade Distribution

```
  Grade A: 0  (lcm*c = sigma exact match — none in genus-0)
  Grade B: 8  N = {1, 2, 3, 5, 6, 7, 10, 13} — squarefree genus-0
  Grade C: 5  N = {8, 9, 12, 16, 18}          — non-squarefree but mu%12=0
  Grade D: 2  N = {4, 25}                      — weak relations
```

**ASCII Grade Distribution**:

```
  B |████████  8 (squarefree genus-0)
  C |█████     5 (non-sqfree, mu%12=0)
  D |██        2 (weak relations)
  A |          0
    +----+----+----+----+
    0    2    4    6    8
```

---

## 8. Special Properties of N=13

N=13 is the only **prime** that is genus-0 with e2>0 AND e3>0:

```
  N=13: mu=14, sigma=14, g=0, e2=2, e3=2
  Isotropic orders = {1, 2, 3}, lcm = 6
  13 ≡ 1 (mod 12)
  lcm(iso) * cusps = 6 * 2 = 12 = sigma(6)  ← divisor sum of perfect number 6!
```

It's notable that "12" appears naturally at N=13.
This is the same value as the denominator 12 in the genus formula.

---

## 9. Ratio of sigma(N) to mu(N) (non-squarefree)

Ratios for non-squarefree genus-0 N:

```
  N=4:  mu/sigma = 6/7  = 0.857
  N=8:  mu/sigma = 12/15 = 4/5 = 0.800
  N=9:  mu/sigma = 12/13 = 0.923
  N=12: mu/sigma = 24/28 = 6/7 = 0.857
  N=16: mu/sigma = 24/31 = 0.774
  N=18: mu/sigma = 36/39 = 12/13 = 0.923
  N=25: mu/sigma = 30/31 = 0.968
```

**Pattern**: mu/sigma = prod_{p^e || N, e>=2} p^e/(p^e + p^{e-1} + ... + 1).
This is because the "high power contribution" of prime factors is added only to sigma.

---

## 10. Limitations and Verification Directions

### Limitations
1. "Forcing chain" is still an exploratory concept without rigorous definition
2. Grade A (lcm*c = sigma exact match) doesn't appear in genus-0 — need wider range search
3. Direct relation between Ramanujan tau(N) and invariants was not found in this computation

### Verification Directions
1. Extend to N=1..1000 range to check if Grade A exists
2. Generalize to other congruence subgroups like Gamma_1(N), Gamma(N)
3. Monster group connection: Check if genus-0 N correspond to McKay-Thompson series
4. Analyze forcing chain at N=28 (second perfect number) (g=2, non-genus-0)

### Perfect Number 28 Cross-Verification

```
  N=28: mu=48, sigma=56, g=2, e2=0, e3=0, lcm(iso)=1
  mu/sigma = 48/56 = 6/7
  mu%12 = 0, mu/12 = 4
  Grade: C (mu%12=0 but lcm=1 prevents chain)
```

Perfect number 28 has genus 2 and no elliptic points, so forcing chain doesn't operate.
This contrasts with N=6 (genus 0, mu=sigma=12).

---

## 11. Conclusion

| Discovery | Grade | Rationale |
|-----------|-------|-----------|
| squarefree N ⟺ mu(N) = sigma(N) | 🟩 Proven | Direct arithmetic proof |
| e2>0 ∧ e3>0 ⟺ N≡1 (mod 12) (prime) | 🟩 Proven | Quadratic residue + CRT |
| e2>0 ∧ e3>0 ⟹ lcm(iso) = 6 (perfect number) | 🟩 Proven | Trivial from definition |
| genus-0 + squarefree ⟹ Grade B | 🟧 Observed | 8/8 match, structural |
| lcm*cusps = 12 for N=13 | 🟧 Observed | Individual case |
| Direct relation to Ramanujan tau | ⚪ Not found | Need further exploration |

**Key Achievement**: mu(N) = sigma(N) ⟺ N squarefree is established as a pure arithmetic theorem (🟩).
Perfect number 6 and constant 12 naturally emerge at the intersection of genus-0 classification and arithmetic functions.