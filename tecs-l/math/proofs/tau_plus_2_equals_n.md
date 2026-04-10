# Theorem: tau(n) + 2 = n has n = 6 as unique solution

**Date:** 2026-03-31
**Status:** PROVEN (elementary)
**Golden Zone dependency:** None (pure number theory)

---

## Theorem (Main)

> **Theorem.** The equation tau(n) + 2 = n, where tau(n) denotes the number
> of positive divisors of n, has exactly one solution among the positive
> integers: n = 6.

## Theorem (Corollary for Even Perfect Numbers)

> **Corollary.** Among all even perfect numbers, n = 6 is the unique solution
> to tau(n) + 2 = n.

---

## Preliminaries

**Definition.** For a positive integer n, the divisor function tau(n) counts
the number of positive divisors of n. Equivalently, if
n = p_1^{a_1} * p_2^{a_2} * ... * p_k^{a_k}, then
tau(n) = (a_1 + 1)(a_2 + 1)...(a_k + 1).

**Lemma 1 (Classical bound).** For all positive integers n >= 1,

    tau(n) <= 2 * sqrt(n).

*Proof.* Every divisor d of n satisfies either d <= sqrt(n) or n/d <= sqrt(n).
Pairing d with n/d, we see that the number of divisors is at most 2*sqrt(n).
(When n is a perfect square, sqrt(n) is counted once, which only helps.) QED

---

## Proof of the Main Theorem

We must find all positive integers n such that tau(n) = n - 2.

**Step 1. Apply the divisor bound to obtain a finite search range.**

Suppose tau(n) + 2 = n. Then tau(n) = n - 2. By Lemma 1:

    n - 2 = tau(n) <= 2 * sqrt(n).

Let x = sqrt(n) > 0. Then:

    x^2 - 2 <= 2x
    x^2 - 2x - 2 <= 0
    (x - 1)^2 <= 3
    |x - 1| <= sqrt(3)
    x <= 1 + sqrt(3) ~ 2.732

Since n = x^2, we get:

    n <= (1 + sqrt(3))^2 = 1 + 2*sqrt(3) + 3 = 4 + 2*sqrt(3) ~ 7.464

Therefore n <= 7.

**Step 2. Exhaustive verification for n = 1, 2, ..., 7.**

| n | divisors of n     | tau(n) | tau(n) + 2 | tau(n) + 2 = n? |
|---|-------------------|--------|------------|-----------------|
| 1 | {1}               |      1 |          3 | 3 != 1          |
| 2 | {1, 2}            |      2 |          4 | 4 != 2          |
| 3 | {1, 3}            |      2 |          4 | 4 != 3          |
| 4 | {1, 2, 4}         |      3 |          5 | 5 != 4          |
| 5 | {1, 5}            |      2 |          4 | 4 != 5          |
| 6 | {1, 2, 3, 6}      |      4 |          6 | 6 = 6  CHECK    |
| 7 | {1, 7}            |      2 |          4 | 4 != 7          |

The unique solution is n = 6. QED

---

## Proof of the Corollary (Even Perfect Numbers)

**Recall.** By the Euclid-Euler theorem, every even perfect number has the
form P_k = 2^{p-1} * (2^p - 1), where 2^p - 1 is a Mersenne prime (which
requires p to be prime).

For such P_k:

    tau(P_k) = tau(2^{p-1}) * tau(2^p - 1) = p * 2 = 2p

since 2^{p-1} contributes p divisors and the Mersenne prime 2^p - 1
contributes 2 divisors.

The equation tau(P_k) + 2 = P_k becomes:

    2p + 2 = 2^{p-1} * (2^p - 1).                     (*)

**Step 1. Verify p = 2.** LHS = 6, RHS = 2^1 * 3 = 6. Equation (*) holds.
This gives P_1 = 6.

**Step 2. Show (*) fails for all primes p >= 3.**

For p >= 3, we have 2^p - 1 >= 7, so:

    RHS = 2^{p-1} * (2^p - 1) >= 2^{p-1} * 7.

We claim 2^{p-1} * 7 > 2p + 2 for all p >= 3.

*Proof by direct check and induction.*

Base case p = 3: 2^2 * 7 = 28 > 8 = 2(3) + 2. True.

Inductive step: Assume 2^{p-1} * 7 > 2p + 2 for some p >= 3. Then:

    2^p * 7 = 2 * (2^{p-1} * 7) > 2 * (2p + 2) = 4p + 4.

We need 4p + 4 >= 2(p+1) + 2 = 2p + 4, which holds since 4p + 4 >= 2p + 4
iff 2p >= 0, always true. So 2^p * 7 > 2(p+1) + 2.

Therefore RHS > LHS for all p >= 3.

Since the Mersenne prime condition requires p prime, and p = 2 is the only
prime for which (*) holds, the unique even perfect number solving
tau(n) + 2 = n is P_1 = 6. QED

---

## Remark on Odd Perfect Numbers

No odd perfect number is known to exist. If an odd perfect number n existed,
it would satisfy n > 10^{1500} (Ochem-Rao, 2012). Since tau(n) <= 2*sqrt(n),
we would have tau(n) + 2 <= 2*sqrt(n) + 2, which is vastly less than n for
n > 10^{1500}. Therefore no odd perfect number (if any exist) can satisfy
tau(n) + 2 = n.

---

## Significance

The number 6 is characterized as the unique positive integer where the
divisor count falls exactly 2 short of the number itself. This is one of
many uniqueness properties of the first perfect number.

Combined with the identity sigma(6) = 12 = 2 * 6 (the defining property of
perfect numbers), we have the simultaneous system:

    tau(6) + 2 = 6
    sigma(6)   = 2 * 6

No other positive integer satisfies both equations, since no other integer
satisfies even the first.

---

## Verification

See `calc/verify_tau_plus_2.py` for computational verification up to 10^8.
