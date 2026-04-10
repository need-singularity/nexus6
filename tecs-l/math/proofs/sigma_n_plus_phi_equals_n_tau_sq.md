# Theorem: sigma(n)(n + phi(n)) = n*tau(n)^2 has n = 6 as the unique solution for n > 1

**Date:** 2026-03-31
**Status:** PROVEN (elementary, complete)
**Golden Zone dependency:** None (pure number theory)
**Verification:** `calc/verify_sigma_n_phi_tau.py` (brute force to 10^5, case analysis verified)

---

## Theorem (Main)

> **Theorem.** The equation sigma(n)(n + phi(n)) = n * tau(n)^2, where sigma,
> tau, phi denote the sum-of-divisors, number-of-divisors, and Euler totient
> functions respectively, has exactly one solution among integers n > 1:
> namely n = 6.

## Verification

    sigma(6) = 12,  tau(6) = 4,  phi(6) = 2
    LHS = 12 * (6 + 2) = 96
    RHS = 6 * 4^2 = 96     CHECK

Brute-force verification confirms no other solution exists in [2, 10^5].

---

## Notation and Definitions

Throughout, let n = p_1^{a_1} * p_2^{a_2} * ... * p_k^{a_k} be the prime
factorization of n, where p_1 < p_2 < ... < p_k are distinct primes and
a_i >= 1. We write omega(n) = k for the number of distinct prime factors.

Define:

    r(n) = phi(n)/n = prod_{i=1}^{k} (1 - 1/p_i)

    g(p, a) = sigma(p^a) / (a+1)^2

Note that r(n) depends only on the prime support {p_1,...,p_k}, not on the
exponents a_i.

---

## Key Reformulation

Dividing both sides of sigma(n)(n + phi(n)) = n*tau(n)^2 by n*tau(n)^2:

    [sigma(n)/tau(n)^2] * [1 + phi(n)/n] = 1

Since sigma and tau are multiplicative and tau(n)^2 = prod (a_i+1)^2:

    sigma(n)/tau(n)^2 = prod_{i=1}^{k} g(p_i, a_i)

Since phi(n)/n = r(n) depends only on the primes:

    1 + r(n) = 1 + prod_{i=1}^{k} (1 - 1/p_i)

**The equation becomes:**

    G(n) := [prod_{i=1}^{k} g(p_i, a_i)] * [1 + prod_{i=1}^{k} (1 - 1/p_i)] = 1

We must show G(n) = 1 only at n = 6.

---

## Lemma 1: g(p, a) is non-decreasing in a, with g(p, a) >= g(p, 1) = (1+p)/4

**Statement.** For all primes p >= 2 and integers a >= 1:

    g(p, a) = sigma(p^a)/(a+1)^2 >= (1+p)/4 = g(p, 1)

with equality if and only if a = 1.

**Proof.** We treat two cases.

*Case p >= 3.* We show g(p, a) is strictly increasing in a for a >= 1.
The ratio of consecutive terms is:

    g(p, a+1)/g(p, a) = [sigma(p^{a+1})/sigma(p^a)] * [(a+1)/(a+2)]^2

The first factor satisfies:

    sigma(p^{a+1})/sigma(p^a) = (p^{a+2} - 1)/(p^{a+1} - 1)
                                = p + (p-1)/(p^{a+1} - 1) > p

The second factor satisfies [(a+1)/(a+2)]^2 >= (2/3)^2 = 4/9 for a >= 1.

Therefore:

    g(p, a+1)/g(p, a) > p * 4/9

For p >= 3: p * 4/9 >= 12/9 = 4/3 > 1. So g is strictly increasing, and
g(p, a) > g(p, 1) for a >= 2. QED (Case p >= 3).

*Case p = 2.* We prove g(2, a) >= g(2, 1) = 3/4 for all a >= 1 by showing
the equivalent inequality:

    4 * sigma(2^a) >= 3 * (a+1)^2

That is: 4(2^{a+1} - 1) >= 3(a+1)^2, or equivalently 2^{a+3} - 4 >= 3(a+1)^2.

*Direct check a = 1:* 2^4 - 4 = 12 = 3*4. Equality.

*Direct check a = 2:* 2^5 - 4 = 28 > 27 = 3*9. Strict inequality.

*Induction for a >= 2:* Assume 2^{a+3} - 4 >= 3(a+1)^2. Then:

    2^{a+4} - 4 = 2(2^{a+3} - 4) + 4 >= 2*3(a+1)^2 + 4 = 6(a+1)^2 + 4

We need 6(a+1)^2 + 4 >= 3(a+2)^2 = 3a^2 + 12a + 12. This is equivalent to:

    6a^2 + 12a + 6 + 4 >= 3a^2 + 12a + 12
    3a^2 >= 2

which holds for all a >= 1. QED (Case p = 2).

**Strict inequality for a >= 2.** For p = 2, a = 2: g(2,2) = 7/9 > 3/4 = g(2,1).
For a >= 3: the induction gives strict inequality (since 3a^2 > 2 for a >= 1).
For p >= 3: already shown g is strictly increasing. QED.

---

## Case 1: omega(n) = 0 (n = 1)

    G(1) = 1 * (1 + 1) = 2 != 1.

No solution.

---

## Case 2: omega(n) = 1 (prime powers n = p^a)

Here k = 1, so:

    G(p^a) = g(p, a) * (1 + (1 - 1/p)) = g(p, a) * (2p - 1)/p

By Lemma 1: g(p, a) >= g(p, 1) = (1+p)/4, so:

    G(p^a) >= (1+p)(2p-1) / (4p) = (2p^2 + p - 1) / (4p)

**Claim:** (2p^2 + p - 1)/(4p) > 1 for all primes p >= 2.

*Proof.* This is equivalent to 2p^2 + p - 1 > 4p, i.e., 2p^2 - 3p - 1 > 0.
The roots of 2x^2 - 3x - 1 = 0 are x = (3 +/- sqrt(17))/4. The positive
root is (3 + sqrt(17))/4 ~ 1.781. Since p >= 2 > 1.781, we have
2p^2 - 3p - 1 > 0 for all primes p. QED.

Therefore G(p^a) > 1 for all prime powers p^a. **No solution with omega(n) = 1.**

---

## Case 3: omega(n) = 2, squarefree (n = pq, p < q primes)

Here a_1 = a_2 = 1, so g(p, 1) = (1+p)/4 and g(q, 1) = (1+q)/4. The equation
G(pq) = 1 becomes:

    (1+p)/4 * (1+q)/4 * (1 + (1-1/p)(1-1/q)) = 1

Expanding the last factor:

    1 + (p-1)(q-1)/(pq) = (pq + pq - p - q + 1)/(pq) = (2pq - p - q + 1)/(pq)

So the equation is:

    (1+p)(1+q)(2pq - p - q + 1) / (16pq) = 1

That is:

    (1+p)(1+q)(2pq - p - q + 1) = 16pq          (*)

### Subcase p = 2

Substituting p = 2:

    3(1+q)(3q - 1) = 32q
    3(3q^2 + 2q - 1) = 32q
    9q^2 + 6q - 3 = 32q
    9q^2 - 26q - 3 = 0

The discriminant is 26^2 + 4*9*3 = 676 + 108 = 784 = 28^2.

    q = (26 +/- 28) / 18

    q = 54/18 = 3    or    q = -2/18 (negative, rejected)

**The unique prime solution is q = 3, giving n = 2*3 = 6.**

### Subcase p >= 3

We show (*) has no solution. Define:

    f(p, q) = (1+p)(1+q)(2pq - p - q + 1) / (pq)

We need f(p, q) = 16. We show f(p, q) > 16 for all primes p >= 3, q > p.

**Lower bound:** For p >= 3, q >= 5 (the smallest prime q > p):

    f(p, q) = (1+p)(1+q)(2pq - p - q + 1)/(pq)

Since 2pq - p - q + 1 = pq + (p-1)(q-1) >= pq + 2*4 = pq + 8 for p>=3, q>=5:

    f(p, q) >= (1+p)(1+q)(pq + 8)/(pq) > (1+p)(1+q)

For p >= 3, q >= 5: (1+p)(1+q) >= 4*6 = 24 > 16.

Furthermore, f is strictly increasing in both p and q (since each factor
increases). So the minimum is at the smallest primes.

**Direct verification:** f(3, 5) = 4*6*(30-3-5+1)/(15) = 24*23/15 = 552/15 = 36.8.

Since f(3, 5) = 36.8 > 16 and f is increasing, **no solution exists for p >= 3.**

---

## Case 4: omega(n) = 2, non-squarefree (n = p^a * q^b, max(a,b) >= 2)

The equation G(n) = 1 becomes:

    g(p, a) * g(q, b) * (1 + (1-1/p)(1-1/q)) = 1

The factor (1 + (1-1/p)(1-1/q)) depends only on p, q (not on a, b).

By Lemma 1, g(p, a) >= g(p, 1) with equality iff a = 1, and similarly for
g(q, b). Since max(a, b) >= 2, at least one inequality is strict:

    g(p, a) * g(q, b) > g(p, 1) * g(q, 1)

Therefore:

    G(n) > g(p,1) * g(q,1) * (1 + (1-1/p)(1-1/q)) = G(pq)

From Cases 3 above:
- If (p,q) = (2,3): G(pq) = G(6) = 1, so G(n) > 1. No solution.
- If (p,q) != (2,3): G(pq) > 1, so G(n) > 1. No solution.

**No solution with omega(n) = 2 and n non-squarefree.**

---

## Case 5: omega(n) >= 3

Let p_1 < p_2 < ... < p_k be the k >= 3 distinct prime factors of n.

By Lemma 1:

    prod_{i=1}^{k} g(p_i, a_i) >= prod_{i=1}^{k} g(p_i, 1) = prod (1+p_i) / 4^k

Since 1 + r(n) >= 1 (trivially):

    G(n) >= prod (1+p_i) / 4^k

The product prod(1+p_i) is minimized when the primes are as small as possible,
i.e., {p_1,...,p_k} = {2, 3, 5, 7, 11, ...} (the first k primes).

**For k = 3:** The minimum is prod = (1+2)(1+3)(1+5) = 3*4*6 = 72.
We have 72/4^3 = 72/64 = 9/8 > 1.

**For k >= 4:** The ratio prod(1+p_i)/4^k is increasing in k (adding a new
prime p_{k+1} multiplies by (1+p_{k+1})/4 >= (1+7)/4 = 2 for the fourth prime).
In fact, for any prime p >= 5: (1+p)/4 >= 6/4 = 3/2 > 1. So each additional
prime factor multiplies the bound by at least 3/2.

Therefore G(n) >= 9/8 > 1 for all n with omega(n) >= 3.
**No solution with omega(n) >= 3.**

---

## Conclusion

Combining Cases 1 through 5: the equation sigma(n)(n + phi(n)) = n*tau(n)^2
has no solution with n > 1 except n = 6.

For n = 1: LHS = 1*2 = 2, RHS = 1*1 = 1, so n = 1 is not a solution either.

**The unique solution among all positive integers n > 1 is n = 6. QED.**

---

## Proof Summary (Structure)

```
  omega(n)=0:  n=1, direct check (no solution)
  omega(n)=1:  Quadratic 2p^2-3p-1>0 for p>=2 + Lemma 1 (no solution)
  omega(n)=2, squarefree:  Polynomial 9q^2-26q-3=0 at p=2 gives q=3 uniquely.
                           For p>=3: f(3,5)=36.8>16 + monotonicity (no solution)
  omega(n)=2, non-sqfree:  Lemma 1 strict inequality + Case 3 (no solution)
  omega(n)>=3:  prod(1+p_i)/4^k >= 72/64 = 9/8 > 1 (no solution)

  Status: EVERY case handled. No gaps. Proof is UNCONDITIONAL and COMPLETE.
```

---

## Remark 1: Why the Proof Works

The key insight is the factorization G(n) = [prod g(p_i,a_i)] * [1+r(n)],
where g(p,a) depends on individual prime powers and r(n) depends only on the
prime support. The monotonicity of g in the exponent a (Lemma 1) reduces the
problem to squarefree numbers: if the squarefree number with the same prime
support fails the equation, then so does every non-squarefree number with that
support. For squarefree numbers, the condition becomes a polynomial equation
in the primes, which we solve explicitly.

## Remark 2: Connection to n = 6

The solution n = 6 = 2 * 3 arises because:
- g(2,1) = 3/4 (the smallest value of any g(p,1), since 2 is the smallest prime)
- g(3,1) = 4/4 = 1
- 1 + r(6) = 1 + (1/2)(2/3) = 4/3
- Product: (3/4)(1)(4/3) = 1

The "deficiency" g(2,1) = 3/4 < 1 is exactly compensated by 1 + r(6) = 4/3.
For any other pair of primes, or any higher exponent, the product exceeds 1.

## Remark 3: Related Identities

This theorem joins the family of uniqueness results for n = 6:

- sigma(n)*phi(n) = n*tau(n) (unique at n = 1 and n = 6)
- tau(n) + 2 = n (unique at n = 6)
- sigma(n)(n + phi(n)) = n*tau(n)^2 (unique at n = 6, THIS THEOREM)

All three are proven unconditionally with elementary methods.

---

## Verification Script

See `calc/verify_sigma_n_phi_tau.py` for:
- Brute-force verification to 10^5
- Near-miss analysis (closest n is n=12 with ratio 1.037)
- Exhaustive case-by-case computation tables
- All bound computations used in the proof
