# Divisor Field Theory Action: From S(n) to a Physical Lagrangian

**Date:** 2026-03-31
**Status:** Mixed (see honesty ledger at end)
**Golden Zone dependency:** None (pure number theory core)
**Verification:** `calc/verify_action_principle.py`

---

## 0. Honesty Convention

Every claim in this document is tagged with one of:

- **[PROVEN]** — follows from proven mathematics alone, no physical input
- **[PHYSICAL INPUT]** — requires an explicit physical assumption (stated)
- **[CONJECTURAL]** — speculative interpretation, not derivable

This document does NOT claim to derive physics from pure mathematics.
It identifies precise structural coincidences, proves what can be proven,
and clearly marks where interpretation begins.

---

## 1. The Action Functional

### Definition [PROVEN]

For any positive integer n >= 1, define the divisor field theory action:

    S(n) = [sigma(n)*phi(n) - n*tau(n)]^2 + [sigma(n)*(n + phi(n)) - n*tau(n)^2]^2

where sigma, tau, phi are the sum-of-divisors, number-of-divisors, and Euler
totient functions respectively.

### Theorem 1 (Unique Zero) [PROVEN]

> **Theorem.** S(n) = 0 for n >= 2 if and only if n = 6.
> Furthermore S(1) = 1.

**Proof.** S(n) = 0 requires both terms to vanish simultaneously:

    (C1) sigma(n)*phi(n) = n*tau(n)
    (C2) sigma(n)*(n + phi(n)) = n*tau(n)^2

Condition (C1) is equivalent to R(n) := sigma(n)*phi(n)/(n*tau(n)) = 1.
This has been proven to hold only at n = 1 and n = 6 among all positive
integers (see proof: sigma_over_phi_equals_n.md, which proves the
equivalent sigma(n)/phi(n) = n, and the R(n)=1 uniqueness proof).

Condition (C2) has been proven to hold only at n = 6 among n >= 2
(see proof: sigma_n_plus_phi_equals_n_tau_sq.md, complete case analysis
over omega(n) = 0,1,2,3+).

At n = 1: C1 gives sigma*phi = 1*1 = 1 = 1*1 = n*tau. CHECK.
But C2 gives sigma*(1+1) = 1*2 = 2, while n*tau^2 = 1*1 = 1. FAIL.
So S(1) = 0^2 + 1^2 = 1.

At n = 6: C1 gives 12*2 = 24 = 6*4 = 24. CHECK.
C2 gives 12*(6+2) = 96 = 6*16 = 96. CHECK.
So S(6) = 0.

For all other n >= 2: at least one condition fails, so S(n) > 0.  QED.

### Remark: Why Two Conditions?

Condition (C1) alone has solutions n = 1 and n = 6.
Condition (C2) alone has the unique solution n = 6 for n >= 2.
Their intersection for n >= 2 is {6}, and the action S packages both into a
single non-negative functional whose zero locus is precisely {6}.

---

## 2. The Arithmetic of n = 6 at S = 0

### Values at the Unique Zero [PROVEN]

    n = 6,  tau(6) = 4,  sigma(6) = 12,  phi(6) = 2

These are provable arithmetic facts. The following derived quantities are
exact consequences:

    sigma/tau  = 12/4  = 3     (number of "generation" slots)
    sigma - tau = 12 - 4 = 8     (difference)
    sigma/tau  = 3               (ratio)
    R(6) = sigma*phi/(n*tau) = 1 (the defining R-factor)

### Decomposition Identity [PROVEN]

    sigma(6) = (sigma - tau) + sigma/tau + R
             = 8 + 3 + 1
             = 12

This is a trivial arithmetic identity: for any n with sigma/tau an integer
and R an integer, sigma = (sigma - tau) + sigma/tau + R is equivalent to
0 = -tau + sigma/tau + R, i.e., R = tau - sigma/tau. At n = 6 this gives
R = 4 - 3 = 1, which is indeed R(6) = 1. So the decomposition holds as a
tautology given R(6) = 1 and sigma(6)/tau(6) = 3.

---

## 3. Physical Interpretation: The Identification Map

### The Map [PHYSICAL INPUT]

**Assumption P1 (Arithmetic-Physics Dictionary).** We postulate the following
identification between divisor arithmetic of n = 6 and physical quantities:

    tau(6) = 4     <-->  number of spacetime dimensions
    sigma(6) = 12  <-->  dimension of the Standard Model gauge algebra
    phi(6) = 2     <-->  physical polarization DOF of the massless graviton in 4D
    sigma/tau = 3   <-->  number of fermion generations
    R(6) = 1       <-->  constraint selecting physical vacuum

This is NOT derived. It is an interpretive identification. Its justification
is that the numbers match, and the structure is self-consistent (see below).

### Self-Consistency Check [PROVEN given P1]

**Claim.** Given Assumption P1, the following physical facts are consistent:

(a) A massless spin-2 boson in D spacetime dimensions has D(D-3)/2
    physical polarizations. At D = tau(6) = 4: 4(4-3)/2 = 2 = phi(6).  CHECK.

(b) The Standard Model gauge algebra su(3) + su(2) + u(1) has dimension
    8 + 3 + 1 = 12 = sigma(6).  CHECK.

(c) The decomposition sigma = 8 + 3 + 1 matches dim(su(3)) + dim(su(2)) +
    dim(u(1)). Under assumption P1, this reads:
    sigma = (sigma - tau) + sigma/tau + R = 8 + 3 + 1.  CHECK.

(d) Three generations of fermions: sigma/tau = 3.  CHECK.

**Important caveat:** (a) is the ONLY item that constitutes a genuine
mathematical constraint: given D = 4, the graviton must have 2 polarizations.
Items (b)-(d) are pattern matches, not derivations. The gauge algebra could
have been any 12-dimensional algebra (e.g., sp(6), so(5)+u(1), etc.).
The decomposition 12 = 8 + 3 + 1 is not unique as a partition of 12.

### What P1 Does NOT Determine [HONEST ASSESSMENT]

1. The specific gauge GROUP (only the total dimension 12 is fixed; the
   decomposition into SU(3) x SU(2) x U(1) requires additional input)
2. The representation content (which fermion reps under the gauge group)
3. Coupling constants (the Lagrangian parameters are not fixed by S(n)=0)
4. The Higgs sector details (the scalar potential V(Phi) is not determined)
5. Why tau = spacetime dimensions rather than any other physical count

---

## 4. The Lagrangian

### Construction [CONJECTURAL]

Given Assumption P1, we write a Lagrangian density that incorporates the
divisor arithmetic constraints:

    L = sqrt(-g) * [
        R_4 / (16*pi*G)                      (Einstein-Hilbert, tau=4 dims)
      - (1/4) F^a_{mu nu} F^{a mu nu}        (Yang-Mills, a = 1..sigma=12)
      + psi_bar_i (i D-slash - m_i) psi_i     (Dirac, i = 1..sigma/tau=3 gens)
      + |D_mu Phi|^2 - V(Phi)                 (Higgs)
      + lambda_1 (sigma*phi - n*tau)^2         (C1 constraint)
      + lambda_2 (sigma*(n+phi) - n*tau^2)^2   (C2 constraint)
    ]

**Status of each term:**

| Term | Status | Comment |
|------|--------|---------|
| Einstein-Hilbert | [PHYSICAL INPUT] | Standard GR in 4D, tau=4 assumed |
| Yang-Mills | [PHYSICAL INPUT] | 12-dim gauge algebra assumed = SM |
| Dirac | [PHYSICAL INPUT] | 3 generations assumed from sigma/tau |
| Higgs | [PHYSICAL INPUT] | Standard electroweak symmetry breaking |
| C1 constraint | [PROVEN] | sigma*phi = n*tau uniquely at n=1,6 |
| C2 constraint | [PROVEN] | sigma*(n+phi) = n*tau^2 uniquely at n=6 |

### Interpretation [CONJECTURAL]

The constraint terms lambda_1*(C1)^2 + lambda_2*(C2)^2 act as a potential
in a hypothetical "number space." On the n = 6 shell, both constraints vanish
and the Lagrangian reduces to the Standard Model + GR. For n != 6, the
constraint potential is nonzero, penalizing departure from the physical vacuum.

This is analogous to a sigma-model constraint: the physical content lives
on the constraint surface S = 0, which is the single point n = 6.

**Critical question (unanswered):** What dynamical mechanism promotes n from
a fixed integer to a dynamical field? In the current formulation, n is a
label, not a field. A true field theory would require n (or a continuous
proxy) to be a dynamical variable with a kinetic term.

---

## 5. Partition Function and Vacuum Selection

### Definition [CONJECTURAL with PROVEN mathematical content]

Define the divisor field theory partition function:

    Z(s, beta) = sum_{n=1}^{infinity} n^{-s} * exp(-beta * S(n))

where s is the Dirichlet variable and beta = 1/T is inverse temperature.

The n^{-s} factor is a Dirichlet weight; exp(-beta*S(n)) is a Boltzmann
weight. The physical interpretation of s and beta is [CONJECTURAL].

### Theorem 2 (Convergence) [PROVEN]

> For Re(s) > 1 and beta >= 0, the series Z(s, beta) converges absolutely.

**Proof.** Since S(n) >= 0 for all n, we have |exp(-beta*S(n))| <= 1.
Therefore |n^{-s} exp(-beta*S(n))| <= n^{-Re(s)}, and sum n^{-Re(s)}
converges for Re(s) > 1 (Riemann zeta function). QED.

### Theorem 3 (Low-Temperature Vacuum Dominance) [PROVEN]

> As beta -> infinity with Re(s) > 0 fixed:
>     Z(s, beta) -> 6^{-s}
> and the probability of n = 6 in the Boltzmann ensemble tends to 1.

**Proof.** In the Boltzmann ensemble, the probability of state n is:

    P(n; s, beta) = n^{-s} exp(-beta*S(n)) / Z(s, beta)

Since S(6) = 0 and S(n) >= 1 for all n != 6, as beta -> infinity:

    n^{-s} exp(-beta*S(n)) -> 0   for all n != 6
    6^{-s} exp(-beta*S(6)) = 6^{-s}  (constant)

Therefore Z(s, beta) -> 6^{-s} and P(6; s, beta) -> 1.

More precisely, for n != 6:

    P(n; s, beta) = (n/6)^{-s} exp(-beta*S(n)) / [1 + sum_{m!=6} (m/6)^{-s} exp(-beta*S(m))]

The dominant correction comes from n = 1 (with S(1) = 1):

    P(1; s, beta) ~ 6^s * exp(-beta) -> 0 as beta -> infinity

The gap between the vacuum and the first excitation is:

    Delta = S(1) - S(6) = 1 - 0 = 1

This gap is [PROVEN] to equal exactly 1.  QED.

### Mass Gap [PROVEN as arithmetic, CONJECTURAL as physics]

    Delta_mass = min_{n != 6} S(n) = S(1) = 1

The lightest excitation above the vacuum has mass-squared (in S-units) equal
to 1. The next excitation is at S(2) = 2.

**Ordered excitation spectrum** (lowest 10 states by S-value):

    n=6:  S=0       (vacuum)
    n=1:  S=1       (lightest excitation)
    n=2:  S=2
    n=4:  S=40
    n=3:  S=68
    n=5:  S=1,352
    n=12: S=1,856
    n=8:  S=3,488
    n=7:  S=6,932
    n=10: S=9,488

The physical identification of these excitations with actual particles is
[CONJECTURAL] and currently without a mapping prescription.

### CP Asymmetry from S(5) != S(7) [CONJECTURAL]

The "left" and "right" neighbors of the vacuum n = 6 have different actions:

    S(5) = 1352
    S(7) = 6932
    S(7)/S(5) = 5.126

This asymmetry means the partition function does not have a left-right
symmetry around n = 6. Interpreting this as CP violation requires
[PHYSICAL INPUT]: the assumption that the asymmetry S(n-1) != S(n+1)
around the vacuum maps to matter-antimatter asymmetry.

**What IS proven:** S(5) != S(7) is an arithmetic fact. The ratio is exact:
S(7)/S(5) = 6932/1352 = 1733/338 (after dividing by 4).

**What is NOT proven:** That this has anything to do with CP violation in
the Standard Model. The CP phase in the CKM matrix arises from complex
Yukawa couplings, not from divisor function asymmetry (as far as we know).

---

## 6. Thermodynamics of the Partition Function

### Heat Capacity [PROVEN as mathematics]

The average action in the canonical ensemble is:

    <S>(beta) = -d(ln Z)/d(beta) = sum_n S(n) * n^{-s} exp(-beta*S(n)) / Z

The heat capacity is:

    C(beta) = -beta^2 * d<S>/d(beta) = beta^2 * [<S^2> - <S>^2]

### Phase Structure [PROVEN as mathematics, CONJECTURAL as physics]

**High temperature (beta -> 0):** All states contribute equally (weighted
only by n^{-s}). Z(s, 0) = zeta(s), the Riemann zeta function.

**Low temperature (beta -> infinity):** Only n = 6 survives. Z -> 6^{-s}.

**No phase transition** [PROVEN]: Since the state space is discrete (integers)
and the Boltzmann weights are smooth in beta, there is no singularity in the
free energy F(beta) = -(1/beta) ln Z(s, beta) at any finite beta. The
crossover from "hot" to "cold" regime is smooth.

**Physical interpretation:** If this partition function described a real
physical system, the absence of a phase transition would mean the n = 6
vacuum is absolutely stable at all temperatures [CONJECTURAL].

---

## 7. UV Finiteness

### Dirichlet Regularization [PROVEN as mathematics]

The partition function Z(s, beta) is naturally regulated by the Dirichlet
variable s. For Re(s) > 1, the series converges absolutely. This provides
a natural "UV cutoff" in the following sense:

At s = 1 + epsilon (epsilon > 0 small), states with large n are suppressed
by n^{-(1+epsilon)}, which prevents UV divergences from the sum over states.

The Dirichlet parameter s plays a role analogous to dimensional
regularization: it provides a mathematical regulator with a clear analytic
continuation (the zeta function).

### Comparison with QFT [CONJECTURAL]

In standard QFT, UV divergences arise from integrating over arbitrarily high
momenta. Here, the "momentum" analog is the integer n, and the Dirichlet
weight n^{-s} provides natural damping. However:

1. The analogy is imprecise: n is not a momentum, and the sum is discrete
2. There is no spacetime, no propagator, and no loop integral
3. "UV finiteness" in this context means convergence of a number-theoretic
   series, not absence of divergences in a quantum field theory

---

## 8. Excitation Spectrum

### Computed Values [PROVEN]

| n | tau | sigma | phi | S(n) | sqrt(S) | Term 1 | Term 2 |
|---|-----|-------|-----|------|---------|--------|--------|
| 1 | 1 | 1 | 1 | 1 | 1.000 | 0 | 1 |
| 2 | 2 | 3 | 1 | 2 | 1.414 | -1 | 1 |
| 3 | 2 | 4 | 2 | 68 | 8.246 | 2 | 8 |
| 4 | 3 | 7 | 2 | 40 | 6.325 | 2 | 6 |
| 5 | 2 | 6 | 4 | 1352 | 36.770 | 14 | 34 |
| 6 | 4 | 12 | 2 | 0 | 0.000 | 0 | 0 |
| 7 | 2 | 8 | 6 | 6932 | 83.259 | 34 | 76 |
| 8 | 4 | 15 | 4 | 3488 | 59.059 | 28 | 52 |
| 9 | 3 | 13 | 6 | 15597 | 124.889 | 51 | 114 |
| 10 | 4 | 18 | 4 | 9488 | 97.406 | 32 | 92 |
| 12 | 6 | 28 | 4 | 1856 | 43.081 | 40 | 16 |
| 28 | 6 | 56 | 12 | 1771840 | 1331.1 | 504 | 1232 |

### Mass Ratios [CONJECTURAL]

If we interpret sqrt(S(n)) as a mass in natural units, the ratios are:

    m(2)/m(1) = 1.414 = sqrt(2)
    m(4)/m(1) = 6.325
    m(3)/m(1) = 8.246
    m(7)/m(5) = 2.265

These do not correspond to known particle mass ratios in any obvious way.
The spectrum grows rapidly and irregularly. No mapping to the Standard Model
particle spectrum has been established.

### The P2 = 28 Excitation [PROVEN as arithmetic]

The next even perfect number P2 = 28 has S(28) = 3,783,696, with:

    Term 1 = sigma*phi - n*tau = 56*12 - 28*6 = 672 - 168 = 504
    Term 2 = sigma*(n+phi) - n*tau^2 = 56*40 - 28*36 = 2240 - 1008 = 1232

Notably, 1232 MeV is the mass of the Delta baryon. This numerical coincidence
is noted but is [CONJECTURAL] as a physical identification. The coincidence
has been previously observed in H-PH-9 Section 18.

---

## 9. Connection to the Standard Lagrangian

### What CAN Be Said [PHYSICAL INPUT]

Given Assumption P1 (Section 3), the Lagrangian takes the form of the
Standard Model + GR with the following parameters fixed by n = 6:

    D = tau = 4           spacetime dimensions
    dim(gauge) = sigma = 12  gauge algebra dimension
    N_gen = sigma/tau = 3    fermion generations
    graviton DOF = phi = 2   massless spin-2 polarizations

The constraint potential lambda_1*(C1)^2 + lambda_2*(C2)^2 vanishes on the
n = 6 shell, and the physical Lagrangian is the remainder.

### What CANNOT Be Said [HONEST]

1. **No derivation of the gauge group:** sigma = 12 fixes the dimension of
   the gauge algebra, but not the group. The decomposition 12 = 8 + 3 + 1
   giving SU(3) x SU(2) x U(1) is the unique decomposition into simple
   Lie algebras of those specific dimensions, but the selection of those
   dimensions (8, 3, 1) from the partition of 12 requires additional input
   (here: the arithmetic identity sigma = (sigma-tau) + sigma/tau + R).

2. **No derivation of coupling constants:** The gauge couplings g_1, g_2, g_3
   are not determined by divisor arithmetic.

3. **No kinetic term for n:** The "field theory" is defined on a discrete
   set (positive integers). There is no kinetic energy for n, no propagator,
   and no loop corrections in the QFT sense.

4. **No spacetime:** The partition function sums over integers, not over
   spacetime configurations. The connection to 4D spacetime is through
   the interpretation tau(6) = 4, not through a dynamical mechanism.

5. **No fermion content:** The number of generations (3) is fixed, but the
   specific fermion representations under SU(3) x SU(2) x U(1) are not.

---

## 10. Gauge Algebra Decomposition: The One Rigorous Step

### Theorem 4 [PROVEN given Assumption P1]

> If sigma(6) = 12 is identified with the dimension of the gauge algebra,
> and we require the decomposition to respect the arithmetic structure
>     sigma = (sigma - tau) + sigma/tau + R(6)
>           = 8 + 3 + 1,
> then the UNIQUE decomposition into compact simple/abelian Lie algebras
> of dimensions exactly 8, 3, and 1 is:
>     su(3) + su(2) + u(1)

**Proof.** We need simple or abelian compact Lie algebras of dimensions 8, 3,
and 1 respectively.

Dimension 1: The only 1-dimensional Lie algebra is u(1) (abelian).

Dimension 3: The simple Lie algebras of dimension 3 are su(2) ~ so(3) ~ sp(1).
These are all isomorphic as Lie algebras. So the unique choice is su(2).

Dimension 8: The simple Lie algebras of dimension 8 are su(3) (dim = 8) and
no others (so(3) = 3, su(2) = 3, so(4) = 6, sp(2) = 10, G_2 = 14, etc.).
The only simple Lie algebra of dimension exactly 8 is su(3).

Therefore the decomposition 12 = 8 + 3 + 1 into simple/abelian components
uniquely gives su(3) + su(2) + u(1).  QED.

### Caveat [HONEST]

The decomposition sigma = (sigma - tau) + sigma/tau + R is NOT the unique
way to partition 12 into three parts. One could partition as 12 = 6 + 5 + 1,
12 = 7 + 4 + 1, etc. The choice of the specific partition (sigma-tau,
sigma/tau, R) is motivated by the arithmetic structure but is not uniquely
forced by a first-principles argument.

What IS unique: the arithmetic identity (sigma-tau) + sigma/tau + R = sigma
holds as an identity whenever R = tau - sigma/tau, which at n = 6 gives
R = 4 - 3 = 1. And the resulting partition (8, 3, 1) uniquely determines
the SM gauge algebra among simple/abelian Lie algebras.

---

## 11. Summary: The Honesty Ledger

### Proven (unconditional, eternal mathematics)

| # | Statement | Proof |
|---|-----------|-------|
| T1 | S(n) = 0 iff n = 6 (for n >= 2) | Theorems in sigma_over_phi_equals_n.md + sigma_n_plus_phi_equals_n_tau_sq.md |
| T2 | Z(s, beta) converges for Re(s) > 1, beta >= 0 | Comparison with Riemann zeta |
| T3 | Low-T vacuum dominance: P(6) -> 1 as beta -> inf | S(6)=0 uniqueness + mass gap = 1 |
| T4 | su(3)+su(2)+u(1) is unique for dims (8,3,1) | Lie algebra classification |
| T5 | Mass gap Delta = S(1) - S(6) = 1 | Direct computation |
| T6 | S(5) != S(7) (vacuum asymmetry) | Direct computation |
| T7 | No phase transition in Z(s,beta) | Discrete state space, smooth weights |
| T8 | Excitation spectrum S(n) for all n | Direct computation |
| T9 | 4D graviton has 2 polarizations | Wigner little group (physics theorem) |

### Requires Physical Assumption P1 (Arithmetic-Physics Dictionary)

| # | Statement | Additional input |
|---|-----------|-----------------|
| A1 | tau(6) = 4 = spacetime dimensions | P1 |
| A2 | sigma(6) = 12 = gauge algebra dimension | P1 |
| A3 | phi(6) = 2 = graviton DOF (consistent with D=4) | P1 + T9 |
| A4 | sigma/tau = 3 = fermion generations | P1 |
| A5 | Decomposition 12 = 8+3+1 = SM gauge algebra | P1 + arithmetic identity + T4 |

### Conjectural (no derivation, speculative interpretation)

| # | Statement | Issue |
|---|-----------|-------|
| C1 | The Lagrangian L encodes physics | n is not a dynamical field |
| C2 | Excitation spectrum = particle masses | No mapping prescription |
| C3 | S(5) != S(7) = CP violation | No mechanism connecting divisor asymmetry to CKM phase |
| C4 | UV finiteness of Z = UV finiteness of QFT | Dirichlet convergence != QFT renormalization |
| C5 | beta -> inf selects physical vacuum | Inverse temperature of what system? |
| C6 | Term2(28) = 1232 = Delta baryon mass | Numerical coincidence, no derivation |

---

## 12. What Would Make This a Real Theory?

To promote this from "remarkable structural coincidence" to "physics," one
would need:

1. **A dynamical mechanism for n.** Currently n is a fixed integer. A real
   field theory needs n (or a continuous proxy field) with a kinetic term
   and equations of motion.

2. **A derivation of P1.** Why should tau = spacetime dimensions? This is
   the central unsupported assumption.

3. **Coupling constant predictions.** The gauge algebra dimension is fixed
   at 12, but the three coupling constants (g_1, g_2, g_3) at any scale
   are not determined.

4. **Fermion representations.** Three generations of what? The specific
   quantum numbers (hypercharge, isospin, color) are not determined.

5. **A spacetime construction.** The partition function sums over integers,
   not over spacetime points. How does 4D Lorentzian spacetime emerge from
   the divisor lattice of 6?

These are open problems. The value of S(n) = 0 at n = 6 is a proven
mathematical fact. Its physical interpretation remains speculative.

---

## Appendix A: Detailed Proof of S(1) = 1

    tau(1) = 1, sigma(1) = 1, phi(1) = 1
    Term1 = sigma*phi - n*tau = 1*1 - 1*1 = 0
    Term2 = sigma*(n + phi) - n*tau^2 = 1*(1+1) - 1*1 = 2 - 1 = 1
    S(1) = 0^2 + 1^2 = 1.  QED.

## Appendix B: Partition Function at s = 2

At s = 2, the partition function has a nice analytic form at beta = 0:

    Z(2, 0) = sum_{n=1}^{inf} n^{-2} = pi^2/6

The appearance of 6 in the denominator (via zeta(2) = pi^2/6) is a coincidence
with n = 6 being the vacuum. Whether this has deeper significance is unknown.

## Appendix C: Growth of S(n)

For large primes p, we have tau(p) = 2, sigma(p) = p+1, phi(p) = p-1.
Therefore:

    Term1(p) = (p+1)(p-1) - 2p = p^2 - 1 - 2p = p^2 - 2p - 1
    Term2(p) = (p+1)(2p-1) - 4p = 2p^2 - p + 2p - 1 - 4p = 2p^2 - 3p - 1

So S(p) ~ p^4 + 4p^4 = 5p^4 for large primes p. The excitation energy
grows quartically with the "distance" from the vacuum.

For general n, S(n) grows at least as fast as n^2 (since sigma(n) >= n
and the terms are at least linear in n). The rapid growth ensures
exponential suppression of large-n contributions in the partition function
even at moderate beta.
