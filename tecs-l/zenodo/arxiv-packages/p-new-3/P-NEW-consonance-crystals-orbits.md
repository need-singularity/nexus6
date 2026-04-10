# Consonance, Crystals, and Orbits: The $\varphi(n) \leq 2$ Filter Across Domains

**Authors:** Park, Min Woo (Independent Researcher)

**Status:** Draft v0.1 (2026-03-28)

**Target:** American Journal of Physics / The Mathematical Intelligencer

---

## Abstract

Why can crystals display only 1-, 2-, 3-, 4-, and 6-fold rotational symmetry? Why do the perfect consonances of Western music use only the frequency ratios 1:1, 2:1, 3:2, and 4:3? Why does the chromatic scale have 12 notes? These three questions, drawn from solid-state physics, psychoacoustics, and music theory, appear to have nothing in common. We show that they share a single number-theoretic answer: the Euler totient condition $\varphi(n) \leq 2$, which selects precisely the set $\{1, 2, 3, 4, 6\}$. The crystallographic restriction demands that $2\cos(2\pi/n)$ be an integer, which is equivalent to the cyclotomic polynomial $\Phi_n(x)$ having degree at most 2, i.e., $\varphi(n) \leq 2$. Musical consonance, in the Helmholtz--Euler tradition, privileges small-integer frequency ratios, and the ratios built from the divisors of 6 are exactly those with numerator and denominator in $\{1,2,3,4,6\}$. The number $12 = \mathrm{lcm}(2,3,4,6)$ then emerges as the smallest period accommodating all consonant intervals. We further observe that the perfect-number identity $\sigma_{-1}(6) = 2$ encodes the factorization of the octave as fifth $\times$ fourth: $(3/2)(4/3) = 2$. A weaker but suggestive connection links the same set to the innermost stable circular orbit (ISCO) in Schwarzschild spacetime at $r = 6M$, where $6 = 2 \times 3$ and $L^2_{\text{ISCO}} = 12M^2$. The unifying algebraic object is the prime pair $(2,3)$, uniquely characterized by $(p-1)(q-1) = 2$, which forces $\varphi(pq) = 2$ and makes $pq = 6$ the largest member of the $\varphi(n) \leq 2$ family. All proofs are elementary and self-contained.

---

## 1. Introduction

Consider three questions from three different fields:

1. **Crystallography.** Why do two-dimensional lattices admit only rotational symmetries of order 1, 2, 3, 4, and 6 --- but never 5, 7, 8, or any higher order?

2. **Music theory.** Why are the "perfect" consonances --- unison, octave, fifth, and fourth --- built from the ratios $1\!:\!1$, $2\!:\!1$, $3\!:\!2$, and $4\!:\!3$, using only the numbers 1 through 4 (and, by extension, 6)?

3. **Scale construction.** Why does virtually every tuning tradition converge on a division of the octave into 12 semitones?

At first glance these appear to be entirely separate phenomena. The crystallographic restriction is a consequence of lattice geometry. Consonance is grounded in the physiology of the auditory system. And the 12-note chromatic scale is, one might assume, a historical accident of Western music.

We will show that all three phenomena are controlled by the same number-theoretic filter: the condition $\varphi(n) \leq 2$ on the Euler totient function, which admits precisely the integers $n \in \{1, 2, 3, 4, 6\}$. The argument requires nothing beyond elementary number theory and linear algebra.

We also discuss a fourth, more speculative connection: the innermost stable circular orbit (ISCO) in Schwarzschild general relativity occurs at $r = 6M$, and the critical angular momentum satisfies $L^2 = 12M^2 = \mathrm{lcm}(2,3,4,6) \cdot M^2$. While the ISCO derivation does not directly invoke the totient condition, the appearance of the same numbers is at least noteworthy.

**Outline.** Section 2 proves the totient filter theorem. Sections 3, 4, and 5 apply it to crystallography, music, and orbital mechanics respectively. Section 6 identifies the algebraic root: the prime pair $(2,3)$. Section 7 discusses scope and limitations.

---

## 2. The $\varphi(n) \leq 2$ Theorem

### 2.1. Statement and proof

**Theorem 1.** *The Euler totient function satisfies $\varphi(n) \leq 2$ if and only if $n \in \{1, 2, 3, 4, 6\}$.*

*Proof.* Direct computation gives:

| $n$ | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 12 |
|-----|---|---|---|---|---|---|---|---|---|----|----|
| $\varphi(n)$ | 1 | 1 | 2 | 2 | 4 | 2 | 6 | 4 | 6 | 4 | 4 |

So the "if" direction is immediate. For the "only if," we must show $\varphi(n) \geq 3$ for all $n \geq 7$.

Write $n = p_1^{a_1} \cdots p_k^{a_k}$ with $p_1 < \cdots < p_k$. Then

$$
\varphi(n) = \prod_{i=1}^{k} p_i^{a_i - 1}(p_i - 1).
$$

**Case 1: $n = p^a$ is a prime power.**
Then $\varphi(n) = p^{a-1}(p-1)$. For $p \geq 5$: $\varphi(p) = p - 1 \geq 4 > 2$. For $p = 3$, $a \geq 2$: $\varphi(9) = 6 > 2$. For $p = 2$, $a \geq 3$: $\varphi(8) = 4 > 2$. The only prime powers with $\varphi \leq 2$ are $2^1 = 2$, $2^2 = 4$, $3^1 = 3$.

**Case 2: $n$ has at least two distinct prime factors.**
Then $\varphi(n) = \prod p_i^{a_i-1}(p_i - 1)$ with at least two terms in the product. Each factor $p_i - 1 \geq 1$, and the product of all $(p_i - 1)$ terms is at least $(p_1 - 1)(p_2 - 1)$.

- If $p_1 = 2, p_2 = 3$: $(p_1 - 1)(p_2 - 1) = 2$, so $\varphi(n) \geq 2$. But if any $a_i \geq 2$ or there is a third prime factor $p_3 \geq 5$, additional factors push $\varphi(n) \geq 4$. So $\varphi(n) = 2$ requires $n = 2^1 \cdot 3^1 = 6$.
- If $p_1 = 2, p_2 \geq 5$: $(p_1 - 1)(p_2 - 1) \geq 4 > 2$.
- If $p_1 \geq 3, p_2 \geq 5$: $(p_1 - 1)(p_2 - 1) \geq 8 > 2$.

Combining all cases, $\varphi(n) \leq 2$ if and only if $n \in \{1, 2, 3, 4, 6\}$. $\square$

### 2.2. Connection to cyclotomic polynomials

The $n$-th cyclotomic polynomial $\Phi_n(x)$ is the minimal polynomial of $e^{2\pi i/n}$ over $\mathbb{Q}$, and $\deg \Phi_n = \varphi(n)$. Therefore:

$$
\varphi(n) \leq 2 \quad \Longleftrightarrow \quad \Phi_n(x) \text{ is linear or quadratic over } \mathbb{Q}.
$$

Explicitly:

| $n$ | $\Phi_n(x)$ | $\deg$ |
|-----|-------------|--------|
| 1   | $x - 1$    | 1      |
| 2   | $x + 1$    | 1      |
| 3   | $x^2 + x + 1$ | 2   |
| 4   | $x^2 + 1$  | 2      |
| 6   | $x^2 - x + 1$ | 2   |

For $n \geq 7$, $\Phi_n$ has degree $\geq 4$, and in particular $\cos(2\pi/n)$ is not a rational number. This is the algebraic fact underlying the crystallographic restriction.

---

## 3. Application 1: Crystallographic Restriction

### 3.1. The constraint

A rotation by angle $\theta = 2\pi/n$ is compatible with a two-dimensional lattice if and only if the rotation matrix

$$
R = \begin{pmatrix} \cos\theta & -\sin\theta \\ \sin\theta & \cos\theta \end{pmatrix}
$$

maps lattice vectors to lattice vectors. Since lattice vectors form a $\mathbb{Z}$-module of rank 2, the matrix $R$ must have integer trace when expressed in a lattice basis. The trace is basis-independent, so:

$$
\mathrm{tr}(R) = 2\cos(2\pi/n) \in \mathbb{Z}.
$$

### 3.2. Why this is $\varphi(n) \leq 2$

The number $2\cos(2\pi/n)$ is an algebraic integer of degree $\varphi(n)/2$ when $\varphi(n)$ is even, and degree $(\varphi(n)+1)/2$ otherwise. (More precisely, it is a root of the minimal polynomial of $\zeta_n + \zeta_n^{-1}$ over $\mathbb{Q}$, whose degree is $\varphi(n)/2$ for $n \geq 3$.)

For $2\cos(2\pi/n)$ to be a rational integer, it must have degree 1 over $\mathbb{Q}$, which requires $\varphi(n)/2 \leq 1$, i.e., $\varphi(n) \leq 2$.

By Theorem 1, the allowed orders are $n \in \{1, 2, 3, 4, 6\}$, giving:

```
  n :   1     2     3     4     6
  theta: 360   180   120   90    60   degrees
  tr(R):  2    -2    -1     0     1
```

This is the **crystallographic restriction theorem**. It explains why snowflakes are hexagonal ($n=6$), why square and hexagonal tilings exist but pentagonal ones do not, and why the 32 crystallographic point groups in 3D are built from these rotational orders.

### 3.3. Figure: the five allowed symmetries

```
     n=1          n=2          n=3          n=4          n=6

      *           * *          *            *  *        * * *
                               * *          *  *       *     *
                                *            **        * * *

   identity     180 flip    triangle      square      hexagon
   trivial      inversion   tiling ok     tiling ok   tiling ok
```

The five-fold case $n=5$ fails because $2\cos(72°) = (\sqrt{5}-1)/2 \approx 0.618$ is irrational.

---

## 4. Application 2: Musical Consonance

### 4.1. The Helmholtz--Euler theory

Helmholtz (1863) and Euler (before him) recognized that the ear perceives two tones as consonant when their frequency ratio is a ratio of small integers [1]. The ranking of intervals by consonance is approximately:

| Interval | Ratio | Consonance rank |
|----------|-------|-----------------|
| Unison | 1:1 | 1 (most consonant) |
| Octave | 2:1 | 2 |
| Perfect fifth | 3:2 | 3 |
| Perfect fourth | 4:3 | 4 |
| Major sixth | 5:3 | 5 |
| Major third | 5:4 | 6 |
| Minor third | 6:5 | 7 |

The top four --- the **perfect consonances** recognized since antiquity --- use only the integers $\{1, 2, 3, 4\}$ in their ratios, all of which are divisors of 6. The remaining "imperfect" consonances require the prime 5.

### 4.2. The divisors of 6 and frequency ratios

The divisors of 6 are $\{1, 2, 3, 6\}$, or equivalently $\{1, 2, 3, 4, 6\}$ if we include $4 = 2^2$ (powers of the prime factors). Every ratio $a:b$ with $a, b \in \{1, 2, 3, 4, 6\}$ and $a > b$ reduces to one of:

```
  Ratios from {1, 2, 3, 4, 6}:

    2/1 = 2.000   octave
    3/2 = 1.500   perfect fifth
    4/3 = 1.333   perfect fourth
    3/1 = 3.000   octave + fifth
    4/1 = 4.000   two octaves
    6/1 = 6.000   two octaves + fifth
    4/2 = 2/1     (duplicate)
    6/2 = 3/1     (duplicate)
    6/3 = 2/1     (duplicate)
    6/4 = 3/2     (duplicate)
```

The **distinct reduced ratios** within one octave are precisely: $2/1$, $3/2$, $4/3$ --- the three nontrivial perfect consonances. The set $\{1,2,3,4,6\}$ generates exactly the intervals that every musical tradition treats as most consonant.

### 4.3. The octave identity and $\sigma_{-1}(6) = 2$

The sum of reciprocals of the divisors of 6 is:

$$
\sigma_{-1}(6) = \frac{1}{1} + \frac{1}{2} + \frac{1}{3} + \frac{1}{6} = 2.
$$

This is the defining property of a perfect number: $\sigma_{-1}(n) = 2$ if and only if $\sigma(n) = 2n$.

Now observe that the product of the two nontrivial consonances within one octave is:

$$
\frac{3}{2} \times \frac{4}{3} = \frac{12}{6} = 2 = \text{octave}.
$$

That is, the **fifth composed with the fourth equals the octave**. This is a basic identity in music theory, but we can rewrite it arithmetically. The proper divisors of 6 are $\{1, 2, 3\}$, and:

$$
\sigma_{-1}(6) = \sum_{d \mid 6} \frac{1}{d} = \frac{1}{1} + \frac{1}{2} + \frac{1}{3} + \frac{1}{6} = 2.
$$

The "musical" decomposition is:

$$
\sigma_{-1}(6) = 1 + \frac{1}{6} + \frac{1}{2} + \frac{1}{3} = 1 + \frac{1}{6} + \frac{5}{6}
$$

but more revealingly, the two interior ratios formed by consecutive divisors (ordered $1, 2, 3, 6$) are $2/1$, $3/2$, and $6/3 = 2/1$, whose nontrivial piece is $3/2$. The complementary ratio within the octave is $2/(3/2) = 4/3$.

The identity $\text{fifth} \times \text{fourth} = \text{octave}$, i.e., $(3/2)(4/3) = 2$, is therefore a restatement of the perfect-number condition $\sigma_{-1}(6) = 2$. The number 6 is the **unique** number (among all positive integers, if one restricts to even perfect numbers) whose divisor structure simultaneously generates all perfect consonances and closes them into the octave.

### 4.4. Why 12 notes?

The chromatic scale divides the octave into 12 equal semitones. Why 12?

In just intonation, the basic intervals are generated by the ratios $2/1$ (octave), $3/2$ (fifth), and $4/3$ (fourth). The question is: what is the smallest number $N$ such that $N$ equal divisions of the octave can approximate all consonant intervals with good accuracy?

Algebraically, we want $N$ such that $2^{k/N} \approx 3/2$ for some integer $k$, i.e., $k/N \approx \log_2(3/2) \approx 0.58496$. The convergents of this continued fraction are $1/2, 3/5, 7/12, 24/41, \ldots$

The convergent $7/12$ gives the extraordinary approximation $2^{7/12} = 1.49831 \approx 1.5 = 3/2$, an error of only 0.11%. This is why 12 works.

But there is a cleaner number-theoretic explanation:

$$
12 = \mathrm{lcm}(2, 3, 4, 6) = \mathrm{lcm}\{n : \varphi(n) \leq 2\} \setminus \{1\}.
$$

The number 12 is the least common multiple of all nontrivial members of the $\varphi(n) \leq 2$ family. It is the smallest period that is simultaneously compatible with all the allowed symmetry orders. In music, 12 is the smallest number of subdivisions that accommodates cycles of 2, 3, 4, and 6 simultaneously --- which is precisely why it can approximate all consonant intervals built from these numbers.

### 4.5. Figure: the circle of fifths

```
         C
      F     G
    Bb        D
   Eb          A
    Ab        E
      Db    B
        Gb/F#

  12 notes arranged by fifths (interval 3:2)
  7 semitones per fifth: 7/12 of an octave
  12 fifths ~ 7 octaves: (3/2)^12 ~ 2^7
  Pythagorean comma: (3/2)^12 / 2^7 = 531441/524288 ~ 1.0136
```

The 12-note chromatic scale is the unique equal temperament that gives the best simultaneous approximation to intervals generated by the primes 2 and 3 --- the two primes whose product is 6.

---

## 5. Application 3: Orbital Stability (Weaker Connection)

### 5.1. The Schwarzschild ISCO

In general relativity, a test particle orbiting a Schwarzschild black hole of mass $M$ moves in the effective potential:

$$
V_{\text{eff}}(r) = -\frac{M}{r} + \frac{L^2}{2r^2} - \frac{ML^2}{r^3}
$$

where $L$ is the specific angular momentum (we use units with $G = c = 1$).

Circular orbits exist where $V_{\text{eff}}'(r) = 0$:

$$
\frac{M}{r^2} - \frac{L^2}{r^3} + \frac{3ML^2}{r^4} = 0 \implies L^2 = \frac{Mr^2}{r - 3M}.
$$

A circular orbit is stable if $V_{\text{eff}}''(r) > 0$. The innermost stable circular orbit (ISCO) occurs where stability is marginal, $V_{\text{eff}}''(r) = 0$:

$$
V_{\text{eff}}''(r) = -\frac{2M}{r^3} + \frac{3L^2}{r^4} - \frac{12ML^2}{r^5} = 0.
$$

Substituting the expression for $L^2$ and simplifying yields the ISCO condition:

$$
r^2 - 6Mr + 9M^2 - 3M^2 = 0 \implies r(r - 6M) = 0.
$$

Therefore:

$$
\boxed{r_{\text{ISCO}} = 6M, \qquad L^2_{\text{ISCO}} = 12M^2.}
$$

### 5.2. The numbers 6 and 12 again

The ISCO radius is $6M$ and the critical angular momentum squared is $12M^2$. These are exactly the numbers that appear in the totient filter ($\max\{n : \varphi(n) \leq 2\} = 6$) and the chromatic scale ($\mathrm{lcm}(2,3,4,6) = 12$).

**We must be honest about the status of this connection.** The ISCO derivation is a specific calculation in Schwarzschild geometry involving the interplay of Newtonian gravity ($1/r$), centrifugal repulsion ($1/r^2$), and the relativistic correction ($1/r^3$). The number 6 arises from the algebraic structure of a cubic equation, not from a totient condition. The factorization $6 = 2 \times 3$ appears because the GR correction term has a coefficient of 3 (the factor $3ML^2/r^3$), and the interplay with the Newtonian factor of $M$ produces the factor 6.

What we can say is:

1. The number 6 appears as a stability boundary in GR, just as it appears as the largest lattice-compatible symmetry order.
2. The number 12 appears as $L^2_{\text{ISCO}}/M^2$, just as it appears as the natural chromatic period.
3. Both 6 and 12 are built exclusively from the primes 2 and 3.

Whether there is a deeper connection --- perhaps through the fact that stability analysis in any potential with polynomial structure tends to produce small-integer boundaries built from the smallest primes --- remains an open question. We flag this connection as **suggestive but not proven** to share the totient origin of the other two applications.

### 5.3. Figure: the effective potential

```
  V_eff
   |
   |         *
   |        * *
   |       *   *           unstable (r < 6M)
   |      *     *
   |     *       *-------  ISCO at r = 6M (inflection)
   |    *         *
   |   *            *
   |  *               *         stable (r > 6M)
   | *                    *
   |*                          *
   +-------|--------|-----------|-----> r/M
   0       3        6          12

   r = 3M:  photon sphere (unstable null orbits)
   r = 6M:  ISCO (marginally stable timelike orbits)
   r = 12M: where L^2_ISCO intersects Newtonian prediction
```

---

## 6. The Unifying Object: The Prime Pair (2, 3)

### 6.1. The unique pair with $(p-1)(q-1) = 2$

**Theorem 2.** *The primes $p = 2$ and $q = 3$ are the unique pair of distinct primes satisfying $(p-1)(q-1) = 2$.*

*Proof.* Let $p < q$ be distinct primes. Then $p \geq 2$ and $q \geq 3$, so $(p-1)(q-1) \geq 1 \cdot 2 = 2$. Equality holds iff $p-1 = 1$ and $q-1 = 2$, i.e., $p = 2, q = 3$. $\square$

Since $\varphi(pq) = (p-1)(q-1)$ for distinct primes, this immediately gives:

**Corollary.** *$n = 6 = 2 \cdot 3$ is the unique squarefree semiprime with $\varphi(n) \leq 2$, and consequently the largest element of $\{n : \varphi(n) \leq 2\}$.*

### 6.2. Why (2, 3) controls everything

The prime pair $(2, 3)$ sits at the foundation of three structures:

| Structure | Role of 2 | Role of 3 | Combined |
|-----------|-----------|-----------|----------|
| Lattice symmetry | $C_2$ reflection | $C_3$ triangular | $C_6$ hexagonal |
| Musical interval | Octave (2:1) | Fifth-related (3:2) | All perfect consonances |
| Orbital mechanics | Binary (attract/repel) | GR cubic correction | ISCO at $r = 6M$ |
| Arithmetic | First prime | Second prime | $\varphi(6) = 2$ (perfect number) |

The pair $(2,3)$ is special because it is the only consecutive integer pair that is also a prime pair, and $2 \cdot 3 = 6$ is the only number that is both a primorial ($p_2\#$) and a perfect number.

### 6.3. The role of $\sigma_{-1}(6) = 2$

The sum of reciprocal divisors ties the arithmetic to the applications:

$$
\sigma_{-1}(6) = \frac{1}{1} + \frac{1}{2} + \frac{1}{3} + \frac{1}{6} = 2.
$$

Decompose this as:

$$
\underbrace{\frac{1}{1}}_{\text{unison}} + \underbrace{\frac{1}{2}}_{\text{octave}^{-1}} + \underbrace{\frac{1}{3}}_{\text{twelfth}^{-1}} + \underbrace{\frac{1}{6}}_{\text{product}} = 2 = \text{octave}.
$$

Or rearranging the divisor pairs: $(1, 6)$ and $(2, 3)$ give the ratios $6/1 = 6$ and $3/2$, and

$$
\frac{6}{1} = \frac{3}{2} \times \frac{4}{3} \times \frac{3}{1} \quad \text{(factored through consonances)}.
$$

The identity $1/2 + 1/3 + 1/6 = 1$ (the sum of proper reciprocal divisors) means that the "cost" of each consonance (measured as a fraction of the octave) adds up exactly to the whole. This additive closure is unique to 6 among all positive integers.

---

## 7. Discussion

### 7.1. What the totient filter explains

The condition $\varphi(n) \leq 2$ provides a **uniform explanation** for:

1. The crystallographic restriction (lattice compatibility requires integer trace, which requires rational $\cos(2\pi/n)$, which requires $\varphi(n) \leq 2$).
2. The primacy of perfect consonances (the "simplest" frequency ratios use only numbers from $\{1,2,3,4,6\}$, the totient-filtered set).
3. The 12-note chromatic scale ($12 = \mathrm{lcm}$ of the filtered set).
4. The octave identity ($\sigma_{-1}(6) = 2$ encodes fifth $\times$ fourth $=$ octave).

### 7.2. What it does not explain

The ISCO connection remains **correlational rather than causal**. The number 6 in $r_{\text{ISCO}} = 6M$ arises from the specific algebraic structure of the Schwarzschild effective potential, not from a totient condition on rotation orders. While it is true that the GR correction introduces a $1/r^3$ term (the "3" in $3ML^2/r^3$) and the resulting algebra produces $6 = 2 \times 3$, this is a different mechanism from the crystallographic argument.

A genuine unification would require showing that the Schwarzschild effective potential's stability analysis is an instance of some general "periodic-system constraint" that reduces to the totient condition. We are not aware of such a result, and we do not claim one.

### 7.3. Pedagogical value

The $\varphi(n) \leq 2$ filter is valuable as a teaching tool because:

- It connects three subjects (crystallography, music theory, number theory) with a single two-line proof.
- It demonstrates how the same algebraic constraint can manifest in physically distinct domains.
- It gives students a concrete example of "unreasonable effectiveness of mathematics" without requiring advanced machinery.
- The proof is accessible to anyone who knows the definition of the Euler totient function.

### 7.4. Relation to prior work

The crystallographic restriction theorem is classical (Hauy 1822, Frankenheim 1842) and appears in every solid-state physics textbook [2, 3]. Its connection to cyclotomic polynomials is well known in algebra [4]. The Helmholtz theory of consonance dates to 1863 [1]. The observation that $\sigma_{-1}(6) = 2$ encodes the octave decomposition appears to be less widely noted, though the arithmetic of perfect numbers has been studied for millennia [5].

What is new here is the explicit identification of $\varphi(n) \leq 2$ as the **single condition** underlying all three domains, and the observation that $\sigma_{-1}(6) = 2$ gives a number-theoretic expression of the fundamental identity of Western harmony.

---

## 8. Summary

We have shown that the Euler totient condition $\varphi(n) \leq 2$, which selects the set $\{1, 2, 3, 4, 6\}$, is the common root of the crystallographic restriction theorem, the theory of perfect musical consonance, and the 12-note chromatic scale. The algebraic engine is the prime pair $(2,3)$, uniquely characterized by $(p-1)(q-1) = 2$, whose product $6$ is both the largest totient-filtered integer and the first perfect number. The identity $\sigma_{-1}(6) = (3/2)(4/3) = 2$ equates the perfect-number condition with the octave decomposition into fifth and fourth. A weaker but suggestive parallel links the same numbers to the ISCO in Schwarzschild spacetime. The entire argument is elementary, self-contained, and accessible to undergraduates.

---

## References

[1] H. von Helmholtz, *On the Sensations of Tone as a Physiological Basis for the Theory of Music* (1863; English trans. A. J. Ellis, 1875).

[2] N. W. Ashcroft and N. D. Mermin, *Solid State Physics* (Harcourt, 1976), Ch. 7.

[3] C. Kittel, *Introduction to Solid State Physics*, 8th ed. (Wiley, 2004), Ch. 1.

[4] S. Lang, *Algebra*, 3rd ed. (Springer, 2002), Ch. IV.

[5] G. H. Hardy and E. M. Wright, *An Introduction to the Theory of Numbers*, 6th ed. (Oxford, 2008), Ch. XVIII.

[6] S. Carroll, *Spacetime and Geometry: An Introduction to General Relativity* (Cambridge, 2019), Ch. 5.

[7] L. Euler, "De numeris amicabilibus," *Opera Omnia*, Ser. I, Vol. 2.

[8] H. Weyl, *Symmetry* (Princeton, 1952).

---

## Appendix A: Computational Verification

```python
from math import gcd
from functools import reduce

def euler_totient(n):
    """Compute phi(n) by definition."""
    return sum(1 for k in range(1, n+1) if gcd(k, n) == 1)

def sigma_neg1(n):
    """Compute sigma_{-1}(n) = sum of 1/d for d|n."""
    return sum(1/d for d in range(1, n+1) if n % d == 0)

def lcm(a, b):
    return a * b // gcd(a, b)

# Verify phi(n) <= 2 filter
print("n : phi(n) : phi<=2?")
for n in range(1, 25):
    phi = euler_totient(n)
    flag = "  <-- PASS" if phi <= 2 else ""
    print(f"{n:2d}: {phi:5d}   {flag}")

# Verify sigma_{-1}(6) = 2
print(f"\nsigma_{{-1}}(6) = {sigma_neg1(6)}")

# Verify LCM
filtered = [2, 3, 4, 6]
L = reduce(lcm, filtered)
print(f"lcm(2,3,4,6) = {L}")

# Output:
#  1:     1    <-- PASS
#  2:     1    <-- PASS
#  3:     2    <-- PASS
#  4:     2    <-- PASS
#  5:     4
#  6:     2    <-- PASS
#  7:     6
#  8:     4
#  ...
# sigma_{-1}(6) = 2.0
# lcm(2,3,4,6) = 12
```

---

## Appendix B: The 32 Crystallographic Point Groups

The 32 point groups in three dimensions are generated by rotations of order $n \in \{1, 2, 3, 4, 6\}$ combined with reflections and inversions. They organize into 7 crystal systems:

```
  Crystal System    Required Symmetry    Allowed n
  ─────────────     ─────────────────    ─────────
  Triclinic         C_1 or C_i           1
  Monoclinic        C_2 axis             2
  Orthorhombic      3 mutually perp C_2  2
  Tetragonal        C_4 axis             4, 2
  Trigonal           C_3 axis             3
  Hexagonal         C_6 axis             6, 3, 2
  Cubic             4 C_3 axes           3, 2
```

Every entry in the "Allowed $n$" column is a member of $\{1, 2, 3, 4, 6\}$. The 230 space groups in 3D (Fedorov 1891, Schoenflies 1891) are obtained by combining these point groups with the 14 Bravais lattices, and no additional rotational orders appear.
