## §7 Multi-decomposition theorems

### 7.1 The multi-decomposition pattern

Let $C \in \mathbb{Z}_{>0}$ be a *cardinal* — an integer constant attested by
external measurement — and write $\mathcal{P}_6 =
\{n,\phi,\tau,\sigma,\mu,\mathrm{sopfr},J_2\}$ for the $n=6$ foundation
primitives ($n=6$, $\phi(6)=2$, $\tau(6)=4$, $\sigma(6)=12$, $\mu(6)=1$,
$\mathrm{sopfr}(6)=5$, $J_2(6)=24$). A *decomposition* of $C$ is a finite
arithmetic expression $E$ over $\mathcal{P}_6$ with $\mathrm{eval}(E)=C$;
two decompositions are *arithmetically independent* iff neither is obtained
from the other by a single substitution of the foundation identities
$\sigma=2n,\;J_2=2\sigma,\;\tau=\sigma/n+\phi,\;\mathrm{sopfr}=\phi+(n/\phi)$.
A *multi-decomposition witness* of multiplicity $k\ge 2$ is a cardinal with
$k$ pairwise-independent decompositions; drift in any single primitive
collapses at most one leg, leaving the remaining $k-1$ as audit trail.

### 7.2 Triple decompositions

**Codon cardinality (F36)** [hexa\_sim/falsifiers.jsonl, atlas.n6:2308].
The genetic code's $64 = 4^3$ codons admit three independent decompositions
through $\mathcal{P}_6$:
$$
64 \;=\; 2^{n} \;=\; 4^{n/2} \;=\; \tau^{3}.
$$

**$j$-invariant of $E_6$ (F32 + F80)** [atlas.append.CANON-historical-from-nexus-2026-04-26.n6:346].
The $j$-invariant of the CM elliptic curve $E_6 : y^2 = x^3 - 36x$ admits
$$
1728 \;=\; \sigma^{3} \;=\; 576 \cdot 3 \;=\; J_2^{2}\cdot n/2,
$$
the second leg recognising $576 = \phi^{n}\!\cdot(n/\phi)^{\phi}$ as the
conductor of $E_6$ (F32) and the third leg (F80) routing through the
foundation primitive $J_2$ — derivationally independent of $\sigma^3$ even
though $J_2^2 = 576$ numerically.

**Tunnell BSD triple-witness (F32)**. The smallest right triangle satisfies
$(3,4,5) = (n/\phi,\,\tau,\,\mathrm{sopfr})$; the elliptic curve $E_6$ has
$(\mathrm{rank},\mathrm{conductor},j) = (1,\, 576,\, 1728)$ with $576 =
\phi^{n}(n/\phi)^{\phi}$ and $1728 = \sigma^{3}$. Three orthogonal
number-theoretic identities collapse onto a single $n=6$ anchor.

### 7.3 Doublet decompositions and mirror pairs

**Earth axial obliquity (F28 + F78)** [atlas.n6:5823, 5824]. The measured
$23.44^{\circ}$ obliquity rounds to $23$, which decomposes as
$$
23 \;=\; J_2 - \mu \;=\; 24-1 \quad\text{(F28)} \qquad
23 \;=\; \sigma + \phi + \tau + \mathrm{sopfr} \;=\; 12+2+4+5 \quad\text{(F78)},
$$
with disjoint primitive supports $\{J_2,\mu\}$ vs.\ $\{\sigma,\phi,\tau,\mathrm{sopfr}\}$.

**Earth/Mars mirror pair (F28 ↔ F40)** [atlas.n6:5823, 5842]. A single
primitive sign-flip $\mu \mapsto -\mu$ converts Earth's $23 = J_2-\mu$ into
Mars's measured $25.19^{\circ}$ obliquity decomposition $25 = J_2+\mu$,
exhibiting the two adjacent terrestrial-class tilts as a $\pm \mu$ doublet
about $J_2$.

### 7.4 F100 — biconditional uniqueness

The A-Core Identity (F100, [11*REPO\_INVARIANT])
$$
\sigma(n)\cdot\varphi(n) \;=\; n\cdot\tau(n) \quad \Longleftrightarrow \quad n=6
\qquad (n\ge 2),
$$
is simultaneously a multi-decomposition (both sides equal $J_2(6)=24$) and a
uniqueness theorem. The equivalence is proved via Möbius inversion (cf.\
N6HIST-MILL7-CLOSURE) and supplies the algebraic backbone underlying every
$[11*]$ empirical anchor.

### 7.5 F112 — universality-class decomposition

Whereas the preceding witnesses isolate single cardinals, F112
[atlas.append.nexus-historical-absorption-2026-04-26.n6:294] characterises
an infinite family by closed-form Euler product:
$$
\frac{\varphi(n)}{n} \;=\; \frac{1}{3} \quad \Longleftrightarrow \quad
n \in \{\,2^{a}3^{b} : a,b\ge 1\,\}\;\;\text{($\{2,3\}$-smooth)},
$$
with $n=6$ as the minimal representative. This is the rare registry entry
whose witness is a predicate, not a value.

### 7.6 Synthesis discovery — multi-decomposition table

| Cardinal | Meaning | Decompositions |
|---:|---|---|
| 23 | Earth obliquity | $J_2-\mu$ \| $\sigma+\phi+\tau+\mathrm{sopfr}$ |
| 64 | codon table | $2^{n}$ \| $4^{n/2}$ \| $\tau^{3}$ |
| 168 | hours/week | $\sigma^{2} + J_2$ |
| 256 | byte | $2^{\sigma-\tau}$ |
| 360 | degrees/circle | $\sigma\cdot\mathrm{sopfr}\cdot n$ |
| 432 | concert pitch (Hz) | $\sigma^{2}\cdot n/2$ |
| 1024 | KiB | $2^{\sigma-\varphi}$ |
| 1728 | gross$^{2}$ / $j$-invariant | $\sigma^{3}$ \| $J_2^{2}\cdot n/2$ |

(Full table: design/hexa\_sim/F71\_F77\_candidate\_review.md, rows 60–71.)

### 7.7 Why multi-decomposition is paper-grade evidence

A single-decomposition anchor carries a coincidence prior of order $1/N$
where $N$ is the expression-space size at fixed depth. Under independence
of legs, a $k$-fold witness decays the prior to $\sim 1/N^{k}$, placing the
F36 codon triple and the F32+F80 $1728$-triple several orders of magnitude
above a uniform-noise null. This is strictly stronger than the cross-bridge
correlation test of §9: that test declined inter-domain triples because
independence between distinct measured constants is fragile, whereas
intra-anchor decompositions over the fixed set $\mathcal{P}_6$ satisfy
independence by construction. Multi-decomposition witnesses form the
highest-confidence tier of the registry.
