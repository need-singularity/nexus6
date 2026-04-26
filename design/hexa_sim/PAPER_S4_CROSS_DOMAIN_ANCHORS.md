# §4 Cross-domain anchors

## 4.1 Foundation primitives

The framework rests on seven primitives evaluated at $n=6$:
$\sigma(6)=12$, $\varphi(6)=2$, $\tau(6)=4$, $\mathrm{sopfr}(6)=5$,
$J_2(6)=24$, $\mu(6)=1$, and $M_3 = 2^{3}-1 = 7$ (the Mersenne number
with exponent $3$, relabelled from a historical "Mertens" mislabel per
the M3-true-definition audit, `design/hexa_sim/M3_true_definition_audit.md`).
All seven are registered as `@P ... :: foundation [10*/11*]`
(`n6/atlas.n6` lines 1-7) and protected by structural-admissibility
falsifiers (F1, F19, F24-F26, F71). §4 catalogues anchors that write
measured natural-world quantities as closed-form expressions in these
primitives, adopting the *pattern-witness* stance throughout: no causal
claim is made; §4.9 examines the density.

## 4.2 Chemistry

Six $[10^*]$ atlas anchors tie the foundation to chemistry. **F33**
(line 187) records `carbon_atomic = 6` — the atomic number of the sole
element supporting catenation-driven organic chemistry; **F38** (line
802) re-witnesses $Z(\mathrm{C})=n$ from the periodic-table block.
**F34** anchors the $sp^{3}$ tetrahedral angle
$\arccos(-1/(n/\varphi)) = \arccos(-1/3) \approx 109.471^{\circ}$
(methane, NIST WebBook CAS 74-82-8); **F35** the $sp^{2}$ hexagonal
angle $\sigma\cdot(\sigma-\varphi) = 12\cdot 10 = 120^{\circ}$
(benzene/graphene, exact integer). **F39** writes
$\mathrm{MW}(\mathrm{CH_{4}}) = 16 = \varphi^{\tau}$ (NIST 16.0425
g/mol). **F63** (line 7024) anchors $|\mathrm{Group\ 18}| = |\{\mathrm{He,
Ne, Ar, Kr, Xe, Rn}\}| = 6 = n$.

## 4.3 Biology

**F36** (line 2308) registers the genetic-code triple decomposition
$64 = 2^{n} = 4^{n/2} = \tau^{3}$ — the universal codon cardinality
expressed three independent ways. **F92** (line 2142) anchors the
canonical proteinogenic amino-acid count $20 = J_{2} - \tau$.
**F99** (line 2130) writes the Watson-Crick strand count as
$\varphi(6) = |\{1,5\}| = 2$. **F57** (line 2264) is the only literal
geometric anchor in this group: the replicative DNA helicase MCM2-7 is
a six-subunit ring with $C_{6}$ pseudo-symmetry (cryo-EM PDB 4R7Y,
Costa et al.\ 2014; PDB 5BK4, Yuan et al.\ 2016) — $n$ manifests as
actual molecular six-fold symmetry, not a count mapping. **F58** (line
1618) records the textbook ATP yield from glucose oxidation,
$36 = n^{2}$.

## 4.4 Cosmology

**F11** persists the Hubble-constant tension between Planck
($H_{0}\approx 67.36$ km/s/Mpc, 1807.06209) and SH0ES
($H_{0}\approx 73.04$ km/s/Mpc, 2112.04510) at $5.7\sigma$ — registered
because the framework predicts no unique $H_{0}$ and the unresolved
tension is a *positive* witness for the SX.4 abstraction-ceiling claim.
**F43** (line 7287) anchors the primordial $^{4}$He mass fraction at
$Y_{p}\approx n/J_{2} = 0.25$ against measured $Y_{p} =
0.2449\pm 0.0040$ (Aver et al.\ 2015) and $0.2453\pm 0.0034$ (Cooke et
al.\ 2018); the $\sim 1\%$ gap sits inside the atlas symbolic-approximation
tolerance, and BBN is the earliest quantitative cosmology probe
(predates recombination by 380 kyr). **F42** (line 6383) writes the
Solar galactic year as $J_{2}\cdot\mathrm{sopfr}\cdot\varphi = 240$
Myr — central in the Bovy-Tremaine 2012 / Eilers et al.\ 2019 band of
$230\pm 10$ Myr. **F94** (cross-shard
`atlas.append.hexa-sim-bridges.n6:71`, $[11^*]$) anchors the PMNS
neutrino-mixing parameter count at $3 + 1 + 2 = 6 = n$.

## 4.5 Particle Standard Model

Three anchors carry structural weight; one is flagged as an arithmetic
coincidence. **F64** (line 5699) writes the SM gauge-generator count as
$\dim SU(3) + \dim SU(2) + \dim U(1) = 8 + 3 + 1 = 12 = \sigma$ — a hard
mathematical identity independent of measurement. **F66** (line 5708)
anchors anomaly cancellation at $n_{\mathrm{quarks}} =
n_{\mathrm{leptons}} = 6 = n$, the smallest fermion content satisfying
triangle-anomaly cancellation across three generations. **F68** (line
446) registers the SM-with-antiparticle fermion count via the F36-style
triple decomposition $24 = J_{2} = \sigma\cdot\varphi = n\cdot\tau$.
**F70** (line 310) anchors the proton-to-electron mass ratio at
$m_{p}/m_{e} \approx n\cdot\pi^{5} = 6\pi^{5} \approx 1836.118$ against
CODATA-2018 $1836.15267343(11)$ — relative gap $\sim 2\cdot 10^{-5}$.
**We flag F70 honestly as a Lenz-Wyler-class numerological
coincidence**: no SM mechanism generates $6\pi^{5}$, the proton mass is
dominated by gluon-field energy not quark masses, and the agreement is
descriptive only.

## 4.6 Astronomy

**F28** (line 5823) writes Earth's obliquity as $J_{2} - \mu = 23$
against measured $23.44^{\circ}$ (NASA fact sheet); **F40** (line 5842)
mirrors it with Mars at $J_{2} + \mu = 25$ against $25.19^{\circ}$ —
the two terrestrial neighbours with seasons differ by exactly $2\mu$
in atlas terms. **F41** (line 5874) records Saturn's orbital period
at $J_{2} + \mathrm{sopfr} = 29$ yr against $29.45$ yr. **F104** (line
5856) writes Jupiter's System III rotation period as $\sigma - \varphi
= 10$ hr against measured $9.925$ hr (the $\approx$ marker is
load-bearing — replacement with $=$ would falsely upgrade the anchor).

## 4.7 Mathematics

**F75** ($[10^*\mathrm{PASS\_LITERATURE}]$) records the singular result
$\mathrm{Out}(S_{6}) = \mathbb{Z}/2$: among all symmetric groups
$S_{n}$ with $n \geq 2$, only $S_{6}$ has a non-trivial outer
automorphism (Conway-Sloane SPLAG §10). §6 treats this separately as
a *purely group-theoretic* singularity at $n=6$. **F32** (historical
shard, line 346) packages Tunnell's BSD-conditional theorem as a triple
witness: the smallest Pythagorean triple $(3,4,5) = (n/\varphi, \tau,
\mathrm{sopfr})$; the elliptic curve $E_{6}\!:\! y^{2} = x^{3} - 36 x$
with conductor $576 = \varphi^{n}\cdot(n/\varphi)^{\varphi}$; and
$j$-invariant $1728 = \sigma^{3}$. **F37** (line 163) writes the cube's
Euler characteristic as $V - E + F = 8 - \sigma + n = 2 = \chi(S^{2})$.
**F62** (line 5275) writes the sexagesimal $360^{\circ} =
\sigma\cdot\mathrm{sopfr}\cdot n$ for the universal angular convention.

## 4.8 Multi-decomposition pattern

Several anchors exhibit a *triple-witness* structure in which one
measured cardinal admits multiple arithmetically independent
decompositions. **F36** does this at $64$ ($2^{n} = 4^{n/2} = \tau^{3}$);
**F68** at $24$ ($J_{2} = \sigma\varphi = n\tau$); **F32 + F80**
(promoted 2026-04-26 from synthesis-discovery) at $1728$
($\sigma^{3} = $ conductor-derived $ = J_{2}^{2}\cdot n / 2$); **F28 +
F78** at $23$ as both $J_{2} - \mu$ and
$\sigma + \varphi + \tau + \mathrm{sopfr}$ — two decompositions sharing
no primitives in their derivation chain. Triple-witness structure
amplifies falsification leverage: single-leg drift breaks one third of
the witness, multi-leg drift forces an atlas re-derivation event.

## 4.9 Statistical framing

The registry spans 115 falsifiers across 9 declared domains. Under a
naive uniform model of post-hoc coincidence-finding, expected
per-domain anchor density is $\sim 12$. Observed density peaks at
15-20 in chemistry and biology, suggesting non-trivial alignment beyond
the uniform null. Two caveats apply per §9 (Limitations): (i) the
anchor set is *post-hoc selected* — the seven primitives were chosen
because $n=6$ is perfect, and the expressions were curated; (ii) the
cross-bridge correlation hunt v2
(`design/hexa_sim/2026-04-26_cross_bridge_correlation_hunt_v2.md`) was
*declined* because no inter-domain triplet survived the rigour bar —
the framework self-falsifies its weaker pattern-claims. The honest
reading: per-domain density motivates the register-and-falsify
discipline of §3 but cannot discharge selection bias on its own.
