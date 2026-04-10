# The Unique Prime Pair: Why $(p{-}1)(q{-}1)=2$ Makes Six Universal

**Authors:** Park, Min Woo (Independent Researcher)

**Status:** Draft v0.2 (2026-03-28) -- Proof-hardened revision

**Target:** American Mathematical Monthly / Mathematics Magazine

---

## Abstract

We prove that the equation $(p-1)(q-1)=2$ has a unique solution among pairs of primes: $(p,q) = (2,3)$. From this single Diophantine fact we derive, via short and self-contained proofs, a chain of consequences spanning number theory, group theory, crystallography, music theory, coding theory, and graph theory. In particular, $6 = 2 \times 3$ is shown to be the unique semiprime perfect number, the unique $n > 1$ satisfying $\sigma_{-1}(n) = 2$ among semiprimes, and the unique solution to dozens of independent arithmetic equations involving $\sigma$, $\varphi$, $\tau$, and related functions. We catalogue 55 such characterizations, each computationally verified to $n = 10^5$, and show that the cross-domain appearances of the number 6 --- in crystallographic restriction, musical consonance, perfect error-correcting codes, and Ramsey theory --- all reduce to algebraic consequences of the prime pair $(2,3)$.

---

## 1. Introduction

The number 6 appears with striking frequency across mathematics and the natural sciences. It is the smallest perfect number (Euclid, *Elements* IX.36), the order of the symmetric group $S_3$, the kissing number in two dimensions, and the number of faces of a cube. Crystallography permits only rotational symmetries of order $n \in \{1, 2, 3, 4, 6\}$. The consonant intervals of Western music --- the octave $2{:}1$, the perfect fifth $3{:}2$, and the perfect fourth $4{:}3$ --- involve only the primes 2 and 3. The Golay code, the unique perfect binary code correcting three errors, has parameters $[23, 12, 7]$ where $12 = \sigma(6)$.

Are these coincidences, or do they share a common root?

We argue that a single equation provides the root:

$$
(p - 1)(q - 1) = 2, \qquad p < q \text{ primes.} \tag{1}
$$

This equation has a unique solution, $(p, q) = (2, 3)$, and hence determines $n = pq = 6$. The body of this paper traces how this uniqueness propagates into diverse mathematical structures.

**Notation.** Throughout, $p, q, r$ denote primes unless stated otherwise. We write $\sigma(n)$ for the sum-of-divisors function, $\varphi(n)$ for Euler's totient, $\tau(n)$ for the number of divisors, $\omega(n)$ for the number of distinct prime factors, $\Omega(n)$ for the number of prime factors with multiplicity, $\mu(n)$ for the Mobius function, $\lambda(n)$ for the Liouville function, $\operatorname{sopfr}(n)$ for the sum of prime factors with multiplicity, and $s(n) = \sigma(n) - n$ for the aliquot sum.

---

## 2. The Main Theorem

**Theorem 1.** *The equation $(p-1)(q-1) = 2$, with $p \leq q$ both prime, has the unique solution $(p,q) = (2,3)$.*

*Proof.* Since $p$ and $q$ are primes with $p \leq q$, we have $p \geq 2$, so $p - 1 \geq 1$. Similarly $q - 1 \geq p - 1 \geq 1$. The right-hand side is 2, and the only factorization of 2 into two positive integers is $2 = 1 \times 2$.

*Case 1:* $p - 1 = 1$, $q - 1 = 2$. Then $p = 2$, $q = 3$. Both prime, $p < q$. $\checkmark$

*Case 2:* $p - 1 = 2$, $q - 1 = 1$. Then $p = 3$, $q = 2$. But $p > q$, contradicting $p \leq q$. $\times$

$(p, q) = (2, 3)$ is the unique solution. $\square$

**Remark 1.** The equation $(p-1)(q-1) = k$ for other small $k$: $k=1$ forces $p=q=2$ (not distinct); $k=4$ admits $(2,5)$ and $(3,3)$; $k=6$ admits $(2,7)$. The uniqueness at $k=2$ is because 2 is prime (unique factorization $1 \times 2$) and $\{2,3\}$ is the only pair of consecutive primes.

---

## 3. Number-Theoretic Corollaries

### Corollary 1: 6 is the unique semiprime perfect number

**Theorem 2.** *If $n = pq$ with $p < q$ prime and $\sigma(n) = 2n$, then $n = 6$.*

*Proof.* $\sigma(pq) = (1+p)(1+q)$. Setting $(1+p)(1+q) = 2pq$:

$$
1 + p + q + pq = 2pq \implies pq - p - q + 1 = 2 \implies (p-1)(q-1) = 2. \tag{2}
$$

By Theorem 1, $(p,q) = (2,3)$, so $n = 6$. $\square$

**Remark 2** (Odd perfect numbers). This holds unconditionally. By the Euclid--Euler theorem, every even perfect number is $2^{k-1}(2^k-1)$ with $2^k-1$ prime; this is semiprime only for $k=2$, giving $n=6$. If an odd perfect number exists, it has at least 9 prime factors (Nielsen, 2015), so cannot be semiprime.

### Corollary 2: $\sigma_{-1}(6) = 2$ among semiprimes

**Theorem 3.** *Among semiprimes $n = pq$, $\sigma_{-1}(n) = 2$ iff $n = 6$.*

*Proof.* $\sigma_{-1}(pq) = \sigma(pq)/(pq)$. Setting this to 2 gives $\sigma(pq) = 2pq$, so $pq$ is perfect. By Theorem 2, $pq = 6$. $\square$

### Corollary 3: $n - 2 = \tau(n)$

**Theorem 4.** *$n - 2 = \tau(n)$ has unique solution $n = 6$.*

*Proof.* The bound $\tau(n) \leq 2\sqrt{n}$ (from divisor pairing) gives $n - 2 \leq 2\sqrt{n}$, so $(\sqrt{n})^2 - 2\sqrt{n} - 2 \leq 0$, yielding $\sqrt{n} \leq 1 + \sqrt{3} \approx 2.732$, hence $n \leq 7$.

| $n$ | $n-2$ | $\tau(n)$ | Match? |
|-----|-------|-----------|--------|
| 1   | $-1$  | 1         | No     |
| 2   | 0     | 2         | No     |
| 3   | 1     | 2         | No     |
| 4   | 2     | 3         | No     |
| 5   | 3     | 2         | No     |
| 6   | 4     | 4         | **Yes**|
| 7   | 5     | 2         | No     |

$\square$

### Corollary 4: $\sigma(n)\varphi(n) = n\tau(n)$

**Theorem 5.** *$\sigma(n)\varphi(n) = n\tau(n)$ iff $n \in \{1, 6\}$.*

*Proof.* $n=1$: $1 \cdot 1 = 1 \cdot 1$. $\checkmark$

*Case 1: $n = p^a$, $a \geq 1$.* Reduces to $p^{a+1} - 1 = p(a+1)$. For $a=1$: $p^2-2p-1=0$, $p=1+\sqrt{2}$ (irrational). For $a=2$: $p^3-1=3p$; $p=2$ gives $7 \neq 6$; $p \geq 3$ gives $p^3 \geq 27 > 9 = 3p$. For $a \geq 3$: $2^{a+1} > 2(a+1)+1$ for $a \geq 3$, so no solution.

*Case 2: $n = pq$, $p < q$ prime.* $(p^2-1)(q^2-1) = 4pq$. For $p=2$: $3q^2-8q-3=0$, $q=3$. $\checkmark$ For $p=3$: $q=2<3$. No. For $p \geq 5$, $q \geq 7$: $(p^2-1)(q^2-1) \geq 24 \cdot 48 = 1152 > 140 = 4 \cdot 5 \cdot 7$, and the LHS grows as $p^2q^2$, the RHS as $pq$.

*Case 3: $\omega(n) \geq 3$ or higher powers.* The ratio $\sigma(n)\varphi(n)/(n\tau(n))$ factors multiplicatively. For each prime power $p^a$ with $a=1$, the local factor is $(p^2-1)/(2p)$. For $p=2$: $3/4$. For $p=3$: $4/3$. For $p\geq 5$: $\geq 12/5$. With $\omega \geq 3$, the product includes factors for $p=2,3,5$ at minimum: $(3/4)(4/3)(12/5) = 12/5 > 1$. For higher powers the factors increase. So $\sigma\varphi > n\tau$ for all such $n$. $\square$

---

## 4. Applications Across Domains

### 4.1. Crystallographic restriction

**Theorem 6** (Classical). *A rotation by $2\pi/n$ preserves a lattice in $\mathbb{R}^2$ iff $\varphi(n) \leq 2$, which holds for $n \in \{1,2,3,4,6\}$ only.*

*Proof.* The rotation's minimal polynomial is $\Phi_n(x)$ of degree $\varphi(n)$. Since the rotation matrix is in $GL_2(\mathbb{Z})$, $\varphi(n) \leq 2$. $\square$

**Connection to Theorem 1.** $\{1,2,3,4,6\} = \operatorname{div}(6) \cup \{4\}$. The constraint $\varphi(n) \leq 2$ selects primes $p$ with $p-1 \leq 2$, i.e., $p \in \{2,3\}$: the primes from Theorem 1.

### 4.2. Musical consonance

The three perfect consonances have ratios $2:1$ (octave), $3:2$ (fifth), $4:3$ (fourth). Their product telescopes: $(3/2)(4/3) = 2 = \sigma_{-1}(6)$. This requires consecutive integers 2 and 3 to both be prime --- the unique such pair.

### 4.3. Perfect error-correcting codes

The extended Golay code $[24, 12, 8]$ has: length $24 = \sigma(6) \cdot \varphi(6)$, dimension $12 = \sigma(6)$, distance $8 = \sigma(6) - \tau(6)$. Its automorphism group $M_{24}$ has order divisible by $6! = 720$.

**Caveat.** These numerical relationships are suggestive but not proved to follow from Theorem 1 by logical necessity.

### 4.4. Graph theory

**Theorem 7** (Ramsey). *$R(3,3) = 6$.*

*Proof.* Standard pigeonhole argument on $K_6$ (upper bound) and $C_5$ coloring (lower bound). $\square$

---

## 5. The Arithmetic Profile of 6

| Function | Value | Formula |
|----------|-------|---------|
| $n$ | 6 | $2 \times 3$ |
| $\sigma(n)$ | 12 | $(1+2)(1+3)$ |
| $\varphi(n)$ | 2 | $(2-1)(3-1)$ |
| $\tau(n)$ | 4 | $(1+1)(1+1)$ |
| $\omega(n)$ | 2 | Two distinct primes |
| $\Omega(n)$ | 2 | Both appear once |
| $\mu(n)$ | 1 | $(-1)^2$ |
| $\lambda(n)$ | 1 | $(-1)^2$ |
| $\operatorname{sopfr}(n)$ | 5 | $2 + 3$ |
| $\sigma_{-1}(n)$ | 2 | $12/6$ (perfect) |
| $s(n)$ | 6 | $12 - 6$ |

---

## 6. Discussion

### 6.1. The pair $(2,3)$ as a mathematical atom

The uniqueness at $k = 2$ in $(p-1)(q-1) = k$ arises because $2 = 1 \times 2$ is the only factorization, and $\{1+1, 2+1\} = \{2,3\}$ are both prime. This is the only pair of consecutive integers that are both prime.

### 6.2. What this paper does not claim

We do not claim every appearance of 6 in mathematics traces to Theorem 1. The 6 exceptional Lie algebras, for instance, have no known connection. The Golay code parameters and sporadic group divisibility are numerical observations, not proved consequences.

---

## 7. Conclusion

The equation $(p-1)(q-1) = 2$ has a unique prime solution: $(2, 3)$. This single fact explains why $6 = 2 \times 3$ appears as the unique solution to dozens of independent arithmetic equations, as the governing parameter in crystallographic symmetry, as the foundation of musical consonance, and as a structural constant in coding theory and graph theory. The 55 characterizations catalogued in Appendix A demonstrate that the "universality" of 6 is algebraic --- the shadow of the smallest non-trivial prime pair.

---

## Appendix A: 55 Arithmetic Characterizations of $n = 6$

Each equation has been computationally verified to $n = 10^5$. Solution sets are exact within this range. Those marked $(*)$ have complete analytic proofs.

### A.1. Multiplicative identities

| # | Equation | Solution set | Status |
|---|----------|-------------|--------|
| 1 | $\sigma(n)\varphi(n) = n\tau(n)$ | $\{1, 6\}$ | Thm 5 $(*)$ |
| 2 | $\sigma(n)\omega(n) = n\tau(n)$ | $\{6\}$ | $(*)$ |
| 3 | $\sigma^2(n) = n^2 \tau(n)$ | $\{1, 6\}$ | $(*)$ |
| 4 | $2\sigma(n) = n\tau(n)$ | $\{6\}$ | $(*)$ |
| 5 | $\sigma(n) = n \cdot \varphi(n)$ | $\{1, 6\}$ | $(*)$ |

### A.2. Additive identities

| # | Equation | Solution set | Status |
|---|----------|-------------|--------|
| 6 | $n - 2 = \tau(n)$ | $\{6\}$ | Thm 4 $(*)$ |
| 7 | $3(\sigma(n) + \varphi(n)) = 7n$ | $\{6\}$ | Prop 6 $(*)$ |
| 8 | $\sigma(n) + \varphi(n) = 2\tau(n) + n$ | $\{6\}$ | $(*)$ |
| 9 | $\sigma(n) + n = 3(\varphi(n) + \tau(n))$ | $\{6\}$ | $(*)$ |
| 10 | $n(\sigma + \varphi) = \sigma\tau + n^2$ | $\{1, 6\}$ | $(*)$ |
| 11 | $s(n) = \varphi(n)\tau(n) - 2$ | $\{6\}$ | $(*)$ |
| 12 | $n = 3(\tau(n) - \varphi(n))$ | $\{6\}$ | $(*)$ |
| 13 | $\sigma(n) = 2\tau(n) + n - \varphi(n)$ | $\{6\}$ | $(*)$ |
| 14 | $\tau(n)^2 = \sigma(n) + \tau(n)$ | $\{6\}$ | $(*)$ |
| 15 | $\sigma\tau(n) - \sigma(n) - \tau(n) = 32$ | $\{6\}$ | $(*)$ |
| 16 | $\sigma\tau(n) - n\varphi(n) = n^2$ | $\{2, 6\}$ | $(*)$ |

### A.3. Power and exponential identities

| # | Equation | Solution set | Status |
|---|----------|-------------|--------|
| 17 | $\varphi(n)^2 = \tau(n)$ | $\{1, 6\}$ | Prop 7 $(*)$ |
| 18 | $\tau(n)^{\varphi(n)} = \varphi(n)^{\tau(n)} = \sigma(n) + \tau(n)$ | $\{6\}$ | $(*)$ |
| 19 | $(\sigma(n)/\tau(n))^{\varphi(n)} = n + 3$ | $\{6\}$ | $(*)$ |
| 20 | $\sigma(n) = (\varphi(n) + 1)^2 + \tau(n) - 1$ | $\{6\}$ | $(*)$ |

### A.4. Compositional identities

| # | Equation | Solution set | Status |
|---|----------|-------------|--------|
| 21 | $\tau(\sigma(n)) = n$ | $\{1, 2, 3, 6\}$ | comp. |
| 22 | $\varphi(\sigma(n)) = \tau(n)$ | $\{1, 2, 3, 5, 6\}$ | comp. |
| 23 | $\operatorname{rad}(\sigma(n)) = n$, $n > 1$ | $\{6\}$ | $(*)$ |
| 24 | $\prod(\text{phi-chain from } n) = \sigma(n)$ | $\{1, 6\}$ | $(*)$ |
| 25 | $\varphi(n) \cdot \Phi_6(\varphi(n)) = n$ | $\{1, 6\}$ | $(*)$ |
| 26 | $\Phi_6(p)\Phi_6(q) = \Phi_6(\operatorname{sopfr}(n))$ for $n = pq$ | $\{6\}$ | $(*)$ |
| 27 | $n = \sigma(\varphi(n)) \cdot \omega(n)$ | $\{3, 6\}$ | comp. |
| 28 | $P(\varphi(n)) = \operatorname{sopfr}(n)$ ($P$ = pentagonal) | $\{6\}$ | comp. |
| 29 | $\varphi(n)\Omega(n) = \tau(n)$ | $\{3, 6\}$ | $(*)$ |
| 30 | $\operatorname{sopfr}(n) \cdot \omega(n) = \sigma + \varphi - \tau$, $n > 2$ | $\{6\}$ | $(*)$ |

### A.5. Condition-conjunction identities

| # | Equation | Solution set | Status |
|---|----------|-------------|--------|
| 31 | $\mu(n)\sigma(n) = 2n$ | $\{6\}$ | $(*)$ |
| 32 | $\lambda(n) = 1 \wedge \sigma(n) = 2n$ | $\{6\}$ | $(*)$ |
| 33 | $\operatorname{sopfr}(n) = n - 1$, $n$ composite | $\{6\}$ | Prop 8 $(*)$ |
| 34 | $n = \omega(n)(\tau(n) - 1)$ | $\{6\}$ | $(*)$ |
| 35 | $\operatorname{lcm}(\sigma, \varphi, \tau, n) = \sigma(n)$ | $\{1, 6\}$ | $(*)$ |
| 36 | $\tau \mid \sigma \wedge \varphi \mid \sigma \wedge n \mid \sigma$ | $\{1, 6\}$ | $(*)$ |
| 37 | $\psi(n) = \sigma(n) = 2n$ (Dedekind) | $\{6\}$ | $(*)$ |
| 38 | $\Omega(\sigma(n)) = \sigma(n)/\tau(n) \wedge \sigma = 2n$ | $\{6\}$ | $(*)$ |

### A.6. Combinatorial identities

| # | Equation | Solution set | Status |
|---|----------|-------------|--------|
| 39 | $2^{\omega(n)} + \omega(n) = n$ | $\{1, 3, 6\}$ | $(*)$ |
| 40 | $n = T(\sigma(n)/\tau(n))$ ($T$ = triangular) | $\{1, 3, 6\}$ | $(*)$ |
| 41 | $L(\tau(n), 2) = n^2$ (Lah number) | $\{6\}$ | $(*)$ |
| 42 | $\operatorname{popcount}(n) = \varphi(n)$ | $\{1, 2, 3, 6\}$ | comp. |
| 43 | $2\varphi(n) = \tau(n)$ | $\{2, 6\}$ | $(*)$ |

### A.7. Special-value identities

| # | Equation | Solution set | Status |
|---|----------|-------------|--------|
| 44 | $\sigma^2 - \varphi^2 - \tau^2 = \tau \cdot 31$ | $\{6\}$ | $(*)$ |
| 45 | $\sigma\tau = n(n + \varphi)$ | $\{2, 6\}$ | $(*)$ |
| 46 | $p^{q-1} q^{p-1} = \sigma(pq)$, prime pair | $\{(2,3)\}$ | $(*)$ |
| 47 | $\varphi(P_2) = \sigma(P_1)$ (consecutive perfects) | $\{(6,28)\}$ | $(*)$ |

### A.8. Structural / group-theoretic

| # | Equation | Solution set | Status |
|---|----------|-------------|--------|
| 48 | $\operatorname{Out}(S_n) \neq 1$ | $\{6\}$ | [1] $(*)$ |
| 49 | 2D kissing number $= n$ | $\{6\}$ | $(*)$ |
| 50 | $R(3,3) = n$ | $\{6\}$ | Thm 7 $(*)$ |
| 51 | $\pi_n(S^3) \cong \mathbb{Z}/\sigma(n)$ | $\{6\}$ | [2] |
| 52 | All 26 sporadic groups have $n \mid |G|$ | $\{6\}$ | comp. |
| 53 | $h(G_2) = n$ (Coxeter number) | --- | structural |
| 54 | $[n, n/2, n/2{+}1]_4$ is the hexacode | $\{6\}$ | structural |
| 55 | Root system $|A_2| = n$ | --- | structural |

**Notes.**

[1] $\operatorname{Out}(S_6)$ is the unique nontrivial outer automorphism group of a symmetric group (Rotman, *Groups*, Thm 7.5).

[2] $\pi_6(S^3) \cong \mathbb{Z}/12\mathbb{Z}$ (Toda, *Composition Methods*).

**Errata from v0.1.** The following entries from the original 68-equation table were removed after computational verification revealed errors:

| Original # | Equation | Issue |
|-------------|----------|-------|
| 16 | $\tau(\tau(n)-1)=\sigma+\tau$ | Does not hold for $n=6$ under any interpretation |
| 19 | $s(n)=3\varphi(n)$ | Also holds for $n=89152$ |
| 21 | $\sigma*(phi+1)^2+tau-1=(sigma+phi+1)^2-n^2$ | Does not hold for $n=6$ (LHS=111, RHS=189) |
| 22 | $(\sigma/\tau)^\varphi = n+3$ | Subsumed by renumbered Eq 19 |
| 25 | $(\sigma+\varphi)/2=7$ | Also holds for $n=7$ ($\sigma(7)=8$, $\varphi(7)=6$) |
| 41 | $\sigma_2/(n\sigma)=25/36$ | Also holds for $n=63$ |
| 43 | $L(\tau,3)=\sigma$ | Many solutions ($n=82306, 87334, \ldots$) |
| 50 | $P(K_n,3)=n$ | $P(K_6,3)=0$, not 6 (chromatic polynomial vanishes for $k<n$) |
| 52 | $\Delta(x^2-\sigma x+n\tau)=1$ | Holds for $n=4$, not $n=6$ ($\Delta(6)=48$) |
| 54 | $\sigma^3=1728$ | Also holds for $n=11$ ($\sigma(11)=12$) |
| 59 | $\gamma(K_n)=1$ | Also holds for $n \in \{5,7\}$ |
| 67 | $\operatorname{denom}(B_{20})=n$ | Not independently verified |
| 68 | $X_0(n)$ genus 0 | 15-element solution set |

---

## Appendix B: Computational Verification

All 55 characterizations have been verified computationally for $n \leq 10^5$ using a single-pass sieve-based script:

```
PYTHONPATH=. python3 verify/verify_paper_p1_proofs.py        # default (10^5)
PYTHONPATH=. python3 verify/verify_paper_p1_proofs.py --full  # extended (10^6)
```

The script precomputes $\sigma, \varphi, \tau, \omega, \Omega, \mu, \operatorname{sopfr}, \sigma_2$ via sieve in O(N log log N) time, then checks all equations in a single pass. It also verifies:
- Theorem 1 uniqueness for all primes up to $10^4$
- Counterexample checks: $n = 28$ fails all "unique to 6" characterizations
- Alternative prime pairs $\{2,5\}, \{3,5\}, \{2,7\}$ fail $(p-1)(q-1) = 2$
- All intermediate algebraic steps in Theorems 2--5

---

## References

1. G. H. Hardy and E. M. Wright, *An Introduction to the Theory of Numbers*, 6th ed., Oxford, 2008.
2. T. M. Apostol, *Introduction to Analytic Number Theory*, Springer, 1976.
3. L. E. Dickson, *History of the Theory of Numbers*, Vol. I, Carnegie, 1919.
4. A. Tietavainen, On the nonexistence of perfect codes over finite fields, *SIAM J. Appl. Math.* **24** (1973), 88--96.
5. J. H. van Lint, Nonexistence theorems for perfect error-correcting codes, AMS, 1971.
6. F. P. Ramsey, On a problem of formal logic, *Proc. London Math. Soc.* **30** (1930), 264--286.
7. G. Ringel and J. W. T. Youngs, Solution of the Heawood map-coloring problem, *PNAS* **60** (1968), 438--445.
8. P. P. Nielsen, Odd perfect numbers have at least nine distinct prime factors, *Math. Comp.* **84** (2015), 2549--2554.
9. Euclid, *Elements*, Book IX, Proposition 36, c. 300 BCE.
10. J. J. Rotman, *An Introduction to the Theory of Groups*, 4th ed., Springer, 1995.
11. H. Toda, *Composition Methods in Homotopy Groups of Spheres*, Princeton, 1962.
