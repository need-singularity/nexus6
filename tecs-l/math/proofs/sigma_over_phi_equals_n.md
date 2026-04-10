# Theorem: sigma(n)/phi(n) = n has solutions only at n = 1 and n = 6

**Status**: PROVEN
**Verification**: `calc/verify_sigma_phi_n.py` (brute-force to 10^6 + algebraic)
**Dependencies**: Elementary number theory (multiplicativity of sigma, phi)

---

## Statement

> **Theorem.** The equation sigma(n) = n * phi(n) holds for a positive integer n
> if and only if n in {1, 6}.

Equivalently: sigma(n)/phi(n) = n has exactly two solutions.

---

## Definitions and Setup

For a positive integer n with prime factorization n = p_1^{a_1} * ... * p_k^{a_k}:

- **sigma(n)** = sum of all divisors of n (multiplicative)
- **phi(n)** = Euler's totient function (multiplicative)
- **n** = the identity function (completely multiplicative)

Since sigma, phi, and n -> n are all multiplicative:

    sigma(n) = prod_{i=1}^{k} sigma(p_i^{a_i})

    n * phi(n) = prod_{i=1}^{k} p_i^{a_i} * phi(p_i^{a_i})

---

## Definition of f

**Definition.** For a prime power p^a (a >= 1), define:

    f(p^a) = sigma(p^a) / (p^a * phi(p^a))

Since both numerator and denominator are multiplicative functions of n,
the equation sigma(n) = n * phi(n) is equivalent to:

    prod_{p^a || n} f(p^a) = 1

where the product runs over prime powers exactly dividing n.

For n = 1 (empty product), this equals 1 trivially.

---

## Explicit Formula for f

**Lemma 1.** For a prime p and exponent a >= 1:

    sigma(p^a) = (p^{a+1} - 1) / (p - 1)
    phi(p^a) = p^{a-1} (p - 1)

Therefore:

    f(p^a) = (p^{a+1} - 1) / (p^{2a-1} (p-1)^2)

**Proof.** Standard formulas. For sigma: sum_{j=0}^{a} p^j = (p^{a+1}-1)/(p-1).
For phi: p^a - p^{a-1} = p^{a-1}(p-1). Then:

    f(p^a) = sigma(p^a) / (p^a * phi(p^a))
           = [(p^{a+1}-1)/(p-1)] / [p^a * p^{a-1}(p-1)]
           = (p^{a+1}-1) / [p^{2a-1}(p-1)^2]  QED.

**Specialization to a = 1:**

    f(p) = (p^2 - 1) / (p(p-1)^2) = (p+1)(p-1) / (p(p-1)^2) = (p+1) / (p(p-1))

---

## Key Values

| p^a | f(p^a) | Decimal  |
|-----|--------|----------|
| 2^1 | 3/2    | 1.500000 |
| 3^1 | 2/3    | 0.666667 |
| 5^1 | 3/10   | 0.300000 |
| 7^1 | 4/21   | 0.190476 |
| 2^2 | 7/8    | 0.875000 |
| 2^3 | 15/32  | 0.468750 |
| 3^2 | 13/54  | 0.240741 |

**Critical observation:** f(2) = 3/2 and f(3) = 2/3, so f(2) * f(3) = 1.
This is why n = 6 = 2 * 3 is a solution.

---

## Lemma 2: f(p) > 1 if and only if p = 2

**Proof.** For a = 1:

    f(p) = (p+1) / (p(p-1)) = (p+1) / (p^2 - p)

We need f(p) > 1, i.e., p + 1 > p^2 - p, i.e., p^2 - 2p - 1 < 0.

The quadratic p^2 - 2p - 1 = 0 has roots p = 1 +/- sqrt(2).
The positive root is 1 + sqrt(2) ~ 2.414.

So p^2 - 2p - 1 < 0 for 1 < p < 1 + sqrt(2), which among primes
includes only p = 2.

Check: f(2) = 3/2 > 1, f(3) = 2/3 < 1. QED.

---

## Lemma 3: f(2^a) < 1 for all a >= 2

**Proof.** We have:

    f(2^a) = (2^{a+1} - 1) / 2^{2a-1}

For a = 2: f(4) = 7/8 < 1.

For a >= 2, we show 2^{a+1} - 1 < 2^{2a-1}:

    2^{a+1} < 2^{2a-1}  iff  a+1 < 2a-1  iff  a > 2

For a = 2: 2^3 - 1 = 7 < 8 = 2^3. True.
For a >= 3: 2^{a+1} < 2^{2a-1} (since a+1 < 2a-1), so
2^{a+1} - 1 < 2^{a+1} < 2^{2a-1}. QED.

**Corollary.** f(2^a) is strictly decreasing for a >= 1 and tends to 0.

    f(2^a) = (2^{a+1} - 1)/2^{2a-1} < 2^{a+1}/2^{2a-1} = 4/2^a -> 0.

---

## Lemma 4: f(p^a) < 1 for all odd primes p and all a >= 1

**Proof.** For p >= 3 and a >= 1:

    f(p^a) = (p^{a+1} - 1) / (p^{2a-1}(p-1)^2)

For a = 1: f(p) = (p+1)/(p(p-1)). At p = 3: f(3) = 4/6 = 2/3 < 1.
Since f(p) is decreasing (Lemma 5 below), f(p) <= 2/3 < 1 for all p >= 3.

For a >= 2: f(p^a) < f(p) (Lemma 6 below), so f(p^a) < 1. QED.

---

## Lemma 5: f(p) is strictly decreasing for p >= 2

**Proof.** Consider g(x) = (x+1)/(x^2 - x) for real x > 1.

    g'(x) = [(x^2-x) - (x+1)(2x-1)] / (x^2-x)^2
           = [x^2 - x - 2x^2 - x + 1] / (x^2-x)^2
           = [-(x^2 + 2x - 1)] / (x^2-x)^2

For x >= 2: x^2 + 2x - 1 >= 4 + 4 - 1 = 7 > 0, so g'(x) < 0. QED.

---

## Lemma 6: f(p^a) < f(p) for all p >= 2, a >= 2

**Proof.** We use a direct bound on f(p^a).

    f(p^a) = (p^{a+1}-1) / (p^{2a-1}(p-1)^2)

Since p^{a+1}-1 < p^{a+1}:

    f(p^a) < p^{a+1} / (p^{2a-1}(p-1)^2) = p^{2-a} / (p-1)^2

For a >= 2, p >= 2: f(p^a) < p^{2-a}/(p-1)^2 <= p^0/(p-1)^2 = 1/(p-1)^2.

Now compare with f(p) = (p+1)/(p(p-1)):

    f(p^a) < 1/(p-1)^2,   f(p) = (p+1)/(p(p-1))

We need 1/(p-1)^2 <= (p+1)/(p(p-1)), i.e., p/(p-1) <= p+1, i.e.,
p <= (p+1)(p-1) = p^2-1. True for p >= 2.

So f(p^a) < 1/(p-1)^2 <= f(p) for all p >= 2, a >= 2. QED.

(Also verified computationally for all primes p <= 1000, a in [2, 10].)

---

## Lemma 7: f(p) < 2/3 for all odd primes p >= 5

**Proof.** We need (p+1)/(p(p-1)) < 2/3, equivalently:

    3(p+1) < 2p(p-1)
    3p + 3 < 2p^2 - 2p
    0 < 2p^2 - 5p - 3
    0 < (2p+1)(p-3)

For p >= 5: 2p + 1 >= 11 > 0 and p - 3 >= 2 > 0. QED.

**Note.** At p = 3: (2*3+1)(3-3) = 7*0 = 0, confirming f(3) = 2/3 exactly
(the boundary case).

---

## Main Proof

**Theorem.** sigma(n) = n * phi(n) if and only if n in {1, 6}.

**Proof.** The equation is equivalent to prod_{p^a || n} f(p^a) = 1.

**n = 1:** Empty product = 1. Solution.

**n > 1:** We case-split on the 2-adic valuation v_2(n).

### Case A: n is odd (v_2(n) = 0)

All prime factors p of n satisfy p >= 3, so f(p^a) < 1 by Lemma 4.
The product of finitely many values strictly less than 1 is strictly less
than 1. **No solution.**

### Case B: 4 | n (v_2(n) >= 2)

Write n = 2^a * m with a >= 2 and m odd.

By Lemma 3, f(2^a) < 1 for a >= 2.
By Lemma 4, f(p^b) < 1 for every odd prime power p^b dividing m.

All factors in the product are < 1, so the product < 1. **No solution.**

### Case C: n = 2m with m odd (v_2(n) = 1)

f(2) = 3/2. The product equation becomes:

    (3/2) * prod_{p^b || m} f(p^b) = 1

So:

    prod_{p^b || m} f(p^b) = 2/3

If m = 1: empty product = 1 != 2/3. No solution (n = 2).

If m > 1: all factors f(p^b) are < 1 (Lemma 4). We need their product
to equal exactly 2/3.

#### Sub-case C1: m = p (single odd prime, a = 1)

f(p) = 2/3 requires p = 3 (since f(3) = 2/3, and f(p) < 2/3 for p >= 5
by Lemma 7, and f is strictly decreasing by Lemma 5).

**n = 2 * 3 = 6 is a solution.**

#### Sub-case C2: m = p^a (single odd prime, a >= 2)

f(p^a) < f(p) <= f(3) = 2/3 (by Lemma 6 and Lemma 5).
Strict inequality: f(p^a) < 2/3. **No solution.**

#### Sub-case C3: m has at least 2 distinct odd prime factors

Write m = p_1^{b_1} * ... * p_s^{b_s} with s >= 2 and p_1 < p_2 < ... < p_s.

The product is:

    prod_{i=1}^{s} f(p_i^{b_i})

Each factor < 1. To maximize the product, take b_i = 1 (since f(p^a) < f(p)
for a >= 2 by Lemma 6) and take the smallest primes. The maximum is:

    f(3) * f(5) = (2/3)(3/10) = 1/5 < 2/3

With more factors, the product only decreases further. **No solution.**

### Summary

The only solutions are n = 1 (Case: empty product) and n = 6 (Case C1).

**QED.**

---

## Verification

Computationally verified for all n in [1, 10^6] by `calc/verify_sigma_phi_n.py`.
Every algebraic inequality verified symbolically and numerically.

The near-miss analysis shows the closest ratios sigma(n)/(n*phi(n)) for n != 1,6
are not close to 1, confirming the theorem is robust (no "near-solutions" exist).

---

## Remarks

1. **Why n = 6 is special.** The equation f(2)*f(3) = (3/2)(2/3) = 1 is a
   remarkable cancellation. The factor f(2) = 3/2 is the ONLY prime power
   with f > 1 (Lemma 2). The compensating factor 2/3 is achieved ONLY by
   p = 3 (Lemma 7 + monotonicity). This makes n = 6 = 2*3 the unique
   non-trivial solution.

2. **Connection to perfect numbers.** n = 6 is the smallest perfect number
   (sigma(6) = 2*6 = 12). The equation sigma(n) = n*phi(n) is NOT equivalent
   to perfectness, but n = 6 satisfies both. For n = 28 (next perfect number):
   sigma(28) = 56, phi(28) = 12, 28*12 = 336 != 56.

3. **Relation to sigma(n)/phi(n).** The ratio sigma(n)/phi(n) = n means the
   "arithmetic complexity" (sigma/phi) of n equals n itself -- a self-referential
   fixed point. Among all positive integers, only 1 and 6 achieve this.

4. **Strength of the result.** The proof is unconditional -- it depends only on
   elementary properties of sigma and phi (multiplicativity and explicit formulas
   for prime powers). No unproven conjectures are used.
