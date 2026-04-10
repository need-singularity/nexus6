# Koide Formula K = 2/3 from R(6) = 1

## Statement

The Koide formula for charged lepton masses,

```
  K = (m_e + m_mu + m_tau) / (sqrt(m_e) + sqrt(m_mu) + sqrt(m_tau))^2 = 2/3
```

holds to 9 ppm experimentally (PDG 2024). We show that K = 2/3 arises as
a number-theoretic identity from the condition R(6) = 1 on the first
perfect number, and that the Koide angle delta_0 = 2/9 arises from the
same arithmetic. Together, K and delta_0 determine all three lepton masses
from a single input (m_tau), predicting m_e to 0.007% and m_mu to 0.006%.

**Status**: The derivation is EXACT within the divisor Koide functional
framework. The framework itself is a MODEL connecting number theory to
particle masses -- it is not derived from first principles.


## Definitions

Let n be a positive integer with standard arithmetic functions:

```
  tau(n)   = number of divisors of n
  sigma(n) = sum of divisors of n
  phi(n)   = Euler totient function
```

For n = 6 (first perfect number):

```
  tau(6)   = 4     (divisors: 1, 2, 3, 6)
  sigma(6) = 12    (1 + 2 + 3 + 6)
  phi(6)   = 2     (integers coprime to 6 in {1,...,5}: {1, 5})
```

**Definition 1** (Bridge Ratio).
```
  R(n) = sigma(n) * phi(n) / (n * tau(n))
```

**Definition 2** (Divisor Koide Functional).
```
  K(n) = n * tau(n)^2 / sigma(n)^2
```

**Definition 3** (Divisor Koide Angle).
```
  delta(n) = phi(n) * tau(n)^2 / sigma(n)^2
```


## Theorem 1: K(6) = 2/3  (Koide Formula)

**Proof.**

Step 1. Evaluate the Bridge Ratio at n = 6:

```
  R(6) = sigma(6) * phi(6) / (6 * tau(6))
       = 12 * 2 / (6 * 4)
       = 24 / 24
       = 1
```

This is PROVEN: R(n) = 1 has the unique solution n = 6 for n > 1
(established in H-CX-501, verified to n = 10^6).

Step 2. The condition R(6) = 1 means:

```
  sigma * phi = n * tau
  12 * 2 = 6 * 4 = 24
```

Step 3. Evaluate the divisor Koide functional:

```
  K(6) = n * tau^2 / sigma^2
       = 6 * 16 / 144
       = 96 / 144
       = 2/3                          QED
```

**Uniqueness.** K(n) = 2/3 has NO solution other than n = 6 in [1, 10000].
This was verified by exhaustive computation.


## Theorem 2: delta(6) = 2/9  (Koide Angle)

**Proof.**

```
  delta(6) = phi(6) * tau(6)^2 / sigma(6)^2
           = 2 * 16 / 144
           = 32 / 144
           = 2/9                       QED
```

**Relation to K.** Note that:

```
  delta(n) / K(n) = phi(n) / n
```

For n = 6: delta/K = phi(6)/6 = 2/6 = 1/3 (the meta fixed point).

**Non-uniqueness.** delta(n) = 2/9 also holds at n = 15 (tau=4, sigma=24,
phi=8). However, n = 15 has K(15) = 5/12 and R(15) = 16/5. The joint
condition K = 2/3 AND delta = 2/9 AND R = 1 is unique to n = 6.


## Theorem 3: K/K_min = phi(6)  (Cauchy-Schwarz Saturation)

**Proof.**

For N positive real numbers, the Cauchy-Schwarz inequality gives:

```
  (sum sqrt(m_i))^2 <= N * sum(m_i)
```

Applied to N = 3 charged leptons:

```
  K = sum(m_i) / (sum sqrt(m_i))^2 >= 1/N = 1/3
```

with equality iff all masses are equal.

Therefore:

```
  K / K_min = (2/3) / (1/3) = 2 = phi(6)
```

The Koide ratio sits exactly at twice the Cauchy-Schwarz lower bound,
and this factor of 2 equals the Euler totient phi(6). This means the
lepton mass spectrum is maximally non-degenerate within the Koide
framework, with the departure from degeneracy controlled by phi(6).


## Theorem 4: Lepton Mass Reconstruction

The standard Koide parametrization expresses three masses through two
parameters (A, delta_0):

```
  sqrt(m_k) = A * (1 + sqrt(2) * cos(2*pi*k/3 + delta_0))
```

for k = 0, 1, 2.

**Why K = 2/3 is automatic.** Using the trigonometric identities for
third-roots-of-unity phases:

```
  sum_{k=0}^{2} cos(2*pi*k/3 + delta_0) = 0           (for any delta_0)
  sum_{k=0}^{2} cos^2(2*pi*k/3 + delta_0) = 3/2       (for any delta_0)
```

we compute:

```
  sum m_k = A^2 * sum (1 + sqrt(2)*cos(theta_k))^2
          = A^2 * (3 + 2*sqrt(2)*0 + 2*(3/2))
          = 6 * A^2

  (sum sqrt(m_k))^2 = (3A)^2 = 9 * A^2

  K = 6*A^2 / (9*A^2) = 2/3
```

This holds for ANY value of delta_0. The Koide formula K = 2/3 is a
consequence of the Z_3 symmetry of the parametrization, not a constraint
on delta_0.

**The angle delta_0 = 2/9 determines the mass spectrum.** Setting
delta_0 = 2/9 (from Theorem 2) and using m_tau = 1776.86 MeV as a
single input:

```
  Assignment: tau (k=0), electron (k=1), muon (k=2)

  A = sqrt(m_tau) / (1 + sqrt(2) * cos(2/9))
    = 42.1527 / (1 + sqrt(2) * 0.97541)
    = 42.1527 / 2.37944
    = 17.7154 MeV^(1/2)
```

Then:

```
  sqrt(m_e)  = A * (1 + sqrt(2)*cos(2*pi/3 + 2/9)) = 0.7148 MeV^(1/2)
  sqrt(m_mu) = A * (1 + sqrt(2)*cos(4*pi/3 + 2/9)) = 10.279 MeV^(1/2)
```

Squaring:

```
  | Lepton   | Predicted (MeV) | Observed (MeV) | Error    |
  |----------|-----------------|----------------|----------|
  | electron | 0.51096         | 0.51100        | 0.007%   |
  | muon     | 105.652         | 105.658        | 0.006%   |
  | tau      | 1776.86 (input) | 1776.86        | (input)  |
```

This is a genuine 2-prediction from 1-input result. The only free
parameters are m_tau and delta_0 = 2/9, which is derived from n = 6
arithmetic. The scale parameter A is then fixed by m_tau.


## Theorem 5: Connection Between Theorems 1 and 4

The coincidence K = 2/3 appearing in both the divisor functional (Thm 1)
and the Koide parametrization (Thm 4) requires explanation.

In the parametrization, K = 2/3 follows from Z_3 symmetry of the
three-phase structure. The value 2/3 = 1 - 1/3 emerges because:

```
  K = 3 * <m> / (3 * <sqrt(m)>)^2 = <m> / (3 * <sqrt(m)>^2)
```

where <.> denotes the average. The factor 2/3 encodes the distinction
between the arithmetic mean of masses and the square of the arithmetic
mean of their square roots.

In the divisor functional, K(6) = n*tau^2/sigma^2 = 2/3 is a
number-theoretic fact about the first perfect number.

The MODEL claims these are the same 2/3, i.e., that the three-phase
structure of lepton masses reflects the divisor structure of n = 6.
This identification is NOT proven from first principles; it is the
central postulate.

What IS proven:
1. K(6) = 2/3 exactly (pure arithmetic)
2. K = 2/3 for any 3-phase Koide parametrization (pure algebra)
3. delta(6) = 2/9 exactly (pure arithmetic)
4. delta_0 = 2/9 gives me, mmu to 0.007% from mtau alone (empirical)
5. n = 6 is the UNIQUE integer with K(n) = 2/3 in [1, 10000]


## Appendix A: Koide Formula — Historical Context

Yoshio Koide discovered the formula in 1981. For 45 years it has
remained an unexplained empirical coincidence. The key difficulty:

1. The formula relates POLE masses, not running masses
2. It is exact to ~10 ppm, far beyond what radiative corrections suggest
3. No known symmetry of the Standard Model predicts K = 2/3
4. It involves sqrt(m), which has no natural role in the SM Lagrangian

The divisor Koide framework offers a possible explanation by connecting
K = 2/3 to the arithmetic of perfect numbers, but this connection
requires accepting the (unverified) hypothesis that perfect number
arithmetic governs particle physics parameters.


## Appendix B: What This Does NOT Prove

1. It does NOT prove that perfect numbers govern particle masses
2. It does NOT explain WHY the Koide parametrization should apply
3. It does NOT derive the Standard Model from number theory
4. The quark sector does NOT satisfy standard Koide (see koide_systematic.py)

The derivation shows: IF the divisor Koide functional is physically
relevant, THEN K = 2/3 and delta = 2/9 are uniquely determined by n = 6.
