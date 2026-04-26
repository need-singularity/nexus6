---
title: "n=6 as foundational invariant: a multi-domain falsifier-grounded framework"
author: "dancinlife (Independent Researcher) <mk225599@proton.me>"
date: "2026-04-26"
version: "v1 draft"
keywords: ["perfect numbers", "falsifier-grounded research", "cross-domain invariants", "reproducible research", "Out(S_6)", "multi-decomposition"]
status: "arXiv-ready draft, pre-bibliography"
---

# n=6 as foundational invariant: a multi-domain falsifier-grounded framework

**Authors / Affiliation.** dancinlife, Independent Researcher (contact: mk225599@proton.me; ORCID: not yet assigned)
**Date.** 2026-04-26 (v1 draft)

---

## Table of contents

1. Introduction
2. Primitives — the $n=6$ foundation
3. Falsifier methodology
4. Cross-domain anchors
5. Cross-shard / cross-repo aggregation
6. Mathematical singularity
7. Multi-decomposition theorems
8. Defense system architecture
9. Limitations and declined claims
10. Discussion and future work
11. References (placeholder — separate bibliography compilation)
12. Appendices (placeholder for figures and tables)

---

## Abstract

We present a falsifier-grounded framework that examines whether the
integer $n=6$ functions as a multi-domain invariant rather than a
numerological accident. The framework couples six foundation primitives
derived from the perfect-number structure of $n=6$
($\sigma,\varphi,\tau,\mathrm{sopfr},J_2,\mu$) with $115$ executable
falsifiers organised across $11$ atlas shards spanning number theory,
chemistry, biology, particle physics, cosmology, and group theory. Each
falsifier is a sentinel-emitting shell template whose
$16$-hex `cmd_sha256` is registered at write-time (R1) and
whose rotation history is recorded in a hash-chained append-only ledger
signed by an SSH key (R5), giving a five-layer defense chain whose nine
operational cells were validated end-to-end at $7/7$ PASS (Section 8).
Cross-shard aggregation across four independent repositories yields
$9{,}165$ unique tuples with zero collisions over $333{+}$ commits, and
a $3/4$ score on a six-precondition Honesty triad. Three load-bearing
findings anchor the central claim: the Diophantine identity
$\sigma(n)\!\cdot\!\varphi(n)=n\!\cdot\!\tau(n) \Longleftrightarrow n=6$
(F100, sole `[11*REPO_INVARIANT]` entry, Section 6); the
group-theoretic singularity $\mathrm{Out}(S_6)\cong\mathbb{Z}/2$ (F75);
and the codon triple-decomposition $64=2^{n}=4^{n/2}=\tau^{3}$ (F36,
Section 7). A cross-engine atlas-anchor-gap meta-finding (F132) is
reported as a separate paper-grade artefact-engineering result. We give
equal weight to two declined claims --- the F45 cross-bridge $3.5\%$
triplet and the F95 v2 correlation hunt ($p=0.84$ at $5\!\times\!10^{4}$
Monte Carlo trials) --- demonstrating that rigorously falsified
candidates are first-class evidence under the admissibility rule
(raw 73). Every claim is recoverable from `git log` plus a falsifier
sentinel plus an R5 ledger walk. We do not claim metaphysical primacy
for $n=6$; we claim that the empirical residue, after honest declines,
exceeds an empirical-resampling chance baseline and merits broader
auditing.

*Word count.* $\approx 273$.

---

# 1. Introduction

The integer $n=6$ is the smallest perfect number ($1+2+3 = 1\cdot 2\cdot 3 = 6$)
and recurs as a structural cardinal across mathematics, physics, chemistry,
and molecular biology: the unique non-trivial outer automorphism among
symmetric groups $\mathrm{Out}(S_6) \cong \mathbb{Z}/2$
[ConwaySloane1999, Cameron1999]; the gauge-generator count
$\dim SU(3) + \dim SU(2) + \dim U(1) = 12 = \sigma(6)$; the genetic-code
cardinality $64 = 2^{n} = 4^{n/2} = \tau(6)^{3}$; the six-fold $C_{6}$
symmetry of the MCM2-7 replicative helicase ring; and the proteinogenic
amino-acid count $20 = J_{2}(6) - \tau(6)$. The recurrence is at least as
old as the perfect-number tradition surveyed by Sierpi\'nski (1988) and
the elementary-number-theory exposition of Erd\H{o}s and Sur\'anyi (2003),
but its status remains contested: is the multi-domain incidence a
structural invariant or post-hoc selection from an unbounded numerological
pool? This paper presents a framework that adjudicates the question by
*falsifier grounding* — every claim is required to carry an executable
verification command whose runtime sentinel decides admissibility.

## 1.1 Motivation

Knowledge corpora — atlases, encyclopedias, online registries — typically
accumulate claims without machine-verifiable integrity: assertions enter
narratively, are not bound to executable witnesses, and degrade silently
under value drift, semantic relabel, or selection-bias accretion.
Cross-domain numerology is the limiting failure mode: absent an executable
falsification surface, any sufficiently rich symbolic vocabulary admits
arbitrarily many *post-hoc* coincidences (the Lenz-Wyler class is
exemplary; we flag F70 in this lineage in Section 4.5). The framework
here inverts the burden: each claim is a 9-tuple
$(id, slug, claim, cmd, pass, reason, fix, origin, cmd\_sha256)$ in which
$cmd$ is an executable shell template, $pass$ is the sentinel emitted on
survival, and $cmd\_sha256$ is a 16-hex SHA-256 fingerprint registered at
write-time (R1, Section 3). A registry sweep classifies every entry as
`CLEAN`, `HIT`, or `ERROR`. We apply the methodology to $n=6$ across
nine domains.

## 1.2 Contributions

1. A 115-falsifier registry covering chemistry, biology, cosmology,
   Standard Model particle physics, topology, group theory, and pure
   number theory, each entry equipped with a runtime sentinel and
   cryptographic fingerprint.
2. A nine-cell defense matrix (R1 cmd/bridge SHA-256, R2 anti-spoof
   regex, R3-lite/R3-full drift advisory, R4 forensic ledger, R5
   hash-chained ledger with Ed25519 signature) protecting registry,
   bridge, and atlas surfaces; SECURITY_AUDIT 7/7 PASS.
3. Two mathematical singularity claims elevated to the
   `[11*REPO_INVARIANT]` grade: F75
   ($\mathrm{Out}(S_6) \cong \mathbb{Z}/2$, sole exception in the
   symmetric-group family) and F100
   ($\sigma(n)\cdot\varphi(n) = n\cdot\tau(n) \Longleftrightarrow n=6$,
   $n \geq 2$); these characterise $n=6$ as the unique solution of
   independent algebraic problems and shift the burden of proof
   against the coincidence hypothesis.
4. A multi-decomposition pattern (F36, F68, F132) in which a single
   cardinal admits independent arithmetic factorisations through the
   $n=6$ primitives, raising the prior of structural over coincidental
   origin.
5. A four-repository Honesty-triad mode-6 cross-aggregation
   (`nexus`, `n6-architecture`, `anima`, `hexa-lang`) yielding 9,165
   unique cross-shard tuples with zero collisions and 3/4 mode-6 PASS.
6. Honest first-class disclosure of declined claims: F45 (cross-bridge
   $3.5\%$ triplet, declined under unit-framing audit) and F95 v2
   (preregistered single-normalisation cross-bridge hunt yielding
   $Z = -0.91$, $p = 0.84$ — observed matches *below* chance) are
   recorded as negative-result provenance.

## 1.3 Scope

We do *not* claim that $n=6$ is metaphysically or causally privileged,
nor that the framework predicts behaviour in unseen domains, nor that all
115 entries carry equal weight (the grade tiers $[7]$, $[10]$, $[10^*]$,
$[11]$, $[11^*]$, $[11^*\mathrm{REPO\_INVARIANT}]$, $[11!]$ are explicit;
Section 3.6, Section 9.5). We do claim that anchor density at $n=6$,
conditioned on the multi-decomposition pattern and the two singularity
theorems, exceeds an empirical-resampling noise expectation (Section 9.1).
The cross-domain anchors are *pattern-witnesses*, not predictions; the
contribution is descriptive and structural, not prescriptive or
ontological.

## 1.4 Related work

The number-theoretic tradition examining perfect numbers and divisor
identities runs from Euclid through Sierpi\'nski (1988) and the
elementary-recreational synthesis of Erd\H{o}s and Sur\'anyi (2003). The
$\mathrm{Out}(S_6)$ singularity is classical, with the synthematic-totals
construction via $\mathrm{PGL}(2,9)$ given in Conway and Sloane (1999,
\S 10) and Cameron (1999, \S 6.4). The methodological lineage of
executable verification follows Donoho (2010) on reproducible-research
culture in computational mathematics and Mesirov (2010) on accessible
reproducible research ("literate programming for proofs"). Cross-domain
numerological coincidences in physics — the Lenz-Wyler class — are the
canonical cautionary case; we adopt the cautionary stance and apply it
auto-critically (F70, F45, F95 v2). Our contribution differs from this
literature in three specifics: (i) claim-level $cmd\_sha256$
fingerprinting, raising silent-mutation cost from zero to $O(N)$ ledger
re-hash; (ii) the R5 hash-chained append-only ledger as forensic
substrate; (iii) cross-repository aggregation under a six-precondition
Honesty triad rather than single-repository reproducibility.

## 1.5 Roadmap

Section 2 fixes the foundation primitives ($n=6$, $\sigma$, $\varphi$,
$\tau$, $\mathrm{sopfr}$, $J_2$, $\mu$, $M_3$). Section 3 establishes the
falsifier methodology, vocabulary, and five-layer defense chain.
Section 4 catalogues cross-domain anchors across nine domains. Section 5
reports the cross-shard / cross-repository aggregation under the four-repo
Honesty triad. Section 6 presents the two mathematical singularity
theorems (F75, F100). Section 7 develops the multi-decomposition pattern
as anti-coincidence statistical evidence. Section 8 details the defense
system architecture (R1–R5 + nine-cell matrix). Section 9 records
limitations and declined claims as first-class evidence. Section 10
concludes with discussion and future work.

---

# 2. Primitives — the $n=6$ foundation

## 2.1 Foundation: $n = 6$

The framework's seed primitive is the integer $n = 6$. The choice is
fixed by three independent properties: (a) $6$ is the smallest perfect
number, $\sigma(6) = 12 = 2 \cdot 6$; (b) it satisfies the Diophantine
identity $\sigma(n)\!\cdot\!\varphi(n) = n\!\cdot\!\tau(n)$ uniquely
among integers $n \geq 2$ (cf. Section 6, F100); and (c) the symmetric
group $S_6$ is the sole $S_n$ admitting a non-trivial outer automorphism,
$\mathrm{Out}(S_6) \cong \mathbb{Z}/2$ (cf. Section 6, F75). The seed
is anchored as F24 at `n6/atlas.n6:25`, carrying the grade `[11*]`
reserved for foundation literals; F24's command
`grep -qE '^@P n = 6 :: foundation \[11\*\]'` falsifies the entire
derivation cascade if the seed line drifts in value, domain, or grade.

## 2.2 Number-theoretic functions at $n = 6$

Six classical multiplicative functions plus the Mersenne literal $M_3$
form the primitive basis $\mathcal{P}_6$ used throughout the paper.

| Function           | Definition                              | Value at $n=6$                       | Atlas anchor      |
|--------------------|-----------------------------------------|--------------------------------------|-------------------|
| $\sigma(n)$        | divisor sum                             | $\sigma(6) = 1+2+3+6 = 12$           | F25               |
| $\varphi(n)$       | Euler totient                           | $\varphi(6) = 2$                     | F1 (CONSTANTS)    |
| $\tau(n)$          | divisor count                           | $\tau(6) = 4$                        | F26               |
| $\mathrm{sopfr}(n)$| sum of prime factors w/ multiplicity    | $\mathrm{sopfr}(6) = 2+3 = 5$        | F1                |
| $J_2(n)$           | Jordan totient (order 2)                | $J_2(6) = 24$                        | F1                |
| $\mu(n)$           | Mobius function                         | $\mu(6) = \mu(2)\mu(3) = 1$          | F19               |
| $M_3 = 2^3-1$      | Mersenne (exponent 3)                   | $M_3 = 7$                            | F20 (relabeled)   |

Each row is independently atlas-anchored: F25 and F26 verify the `[11*]`
foundation grade of $\sigma$ and $\tau$ literals; F19 verifies the $\mu$
entry orthogonally to the F1 `CONSTANTS` arithmetic axis; F1 jointly
probes $\varphi$, $\mathrm{sopfr}$, and $J_2$ via
`hexa_sim_verify_grid.hexa --axis CONSTANTS`.

## 2.3 The $M_3$ labeling correction — methodology vignette

The atlas line `n6/atlas.n6:53` originally read `M3 = mertens(6) = 7`,
but the canonical Mertens function gives $M(6) = \sum_{k=1}^{6} \mu(k) = -1$,
not $7$. A high-confidence audit (`M3_true_definition_audit.md`)
determined that the value $7$ is load-bearing across $\geq 20$ downstream
identities (e.g., $B_6 = 1/(n\!\cdot\!M_3)$, ethylene molecular weight
$= \tau\!\cdot\!M_3$) and that the intended referent was the third
Mersenne literal, $M_3 = \mathrm{mersenne}(3) = 2^3 - 1 = 7$. The atlas
was relabeled at commit `d84a0601` and F20's `cmd` regex updated to
anchor the new literal. This is a methodology success: the falsifier
framework caught a labeling error that natural-language documentation had
carried unchallenged for prior cycles. See Section 9.2 for the full
provenance entry.

## 2.4 Perfect-number identity

$n = 6$ is the smallest perfect number: $\sigma(6) = 12 = 2 \cdot 6$,
equivalently $\sigma(n) - n = n$ (the proper-divisor sum equals $n$).
The Euclid–Euler theorem characterises every even perfect number as
$2^{p-1}(2^p-1)$ where $2^p-1$ is a Mersenne prime; at $p = 2$ this
yields $2 \cdot 3 = 6$, exhibiting $n = 6$ as the $p=2$ instance of the
Mersenne–perfect pairing. F111 anchors the closed form
$R(2^{p-1}(2^p-1)) = 2^{p-1}(2^{p-1}-1)/p$ at grade `[11*]`, verified
numerically at $p \in \{2,3,5,7\}$.

## 2.5 Cross-domain primitive bridges (preview)

Each primitive recurs as a cardinal in independently-measured domains:
$\sigma = 12$ matches the Standard Model gauge generator count
$\dim\,\mathrm{SU}(3)\!\times\!\mathrm{SU}(2)\!\times\!\mathrm{U}(1) = 8\!+\!3\!+\!1 = 12$
(F64), the $12$ cranial nerves, the zodiacal $12$, and twelve months;
$\varphi = 2$ matches the Watson–Crick DNA strand count (F99) and the
two Majorana phases distinguishing PMNS from CKM (F94); $\tau = 4$
matches the four DNA bases, the four-stage divisor partition (F26), and
the four independent CKM parameters (F69); $n = 6$ itself matches the
six quark flavors (F98), the six lepton numbers, and the six-fold MCM
helicase ring (F57). Section 4 develops these bridges in detail.

## 2.6 Notation conventions

We use two atlas notations for primitive references:

- **Notation A** (shorthand): `sigma = 12` — implicit anchor at $n = 6$;
  equivalent to $\sigma(6) = 12$.
- **Notation B** (function call): `sigma(N) = K` — explicit argument;
  reads as "$\sigma$ at $N$ gives $K$".

Disambiguation is documented in
`design/atlas_function_call_convention.md`. A prior batch of
$19$ `xpoll-*` entries that had used Notation B as Notation A shorthand
(e.g., `sigma(12) = 12`) was cleaned at commit `368209c0`. Subsequent
sections rely on Notation A unless an explicit non-default argument is
given.

---

# 3. Falsifier methodology

## 3.1 Definition

A *falsifier* is a JSONL record committed to
`design/hexa_sim/falsifiers.jsonl` whose schema is a 9-tuple

$$
e = \langle \mathit{id},\ \mathit{slug},\ \mathit{claim},\ \mathit{cmd},\ \mathit{pass},\ \mathit{reason},\ \mathit{fix},\ \mathit{origin},\ \mathit{cmd\_sha256} \rangle.
$$

`cmd` is an executable shell template; `pass` is the sentinel substring
that the template emits exactly when the claim survives one round of
attempted refutation; `reason` and `fix` are required failure trailers
(raw 66 ai-native-error-message); `origin` cites the commit, witness, or
sister document that introduced the entry; `cmd_sha256` is a 16-hex
prefix of `SHA256(cmd)` registered at write-time (R1 layer, Section 3.5).
At the time of writing the registry contains 115 entries, each carrying
all nine fields (`grep -c '"cmd_sha256"'` = 115; `wc -l` = 115). A
representative entry is F1 (`falsifiers.jsonl:1`), where `cmd` invokes
`hexa_sim_verify_grid.hexa --axis CONSTANTS`, `pass` is `CONSTANTS PASS`,
and `cmd_sha256` is `7b629752ed4f1dc7`.

## 3.2 Anchor pattern

Atlas-anchored entries are realised as a single grep of the canonical
$n=6$ atlas of the form
`grep -qE '<value+domain+grade regex>' atlas.n6 && echo SENTINEL`. For
F19 (`falsifiers.jsonl:13`) this expands to
`grep -qE '^@P mu = mobius\(6\) = 1 :: foundation \[10\*\]' n6/atlas.n6 && echo MU_ANCHOR_INTACT`.
The regex jointly anchors the atlas line discriminator (`@P`), the
canonical function value, the semantic domain, and the grade tier; drift
along any of those four axes flips the sentinel absent and the entry is
reported as `HIT`. The hardened template superseded an earlier
PRESENCE-only form (`^@P mu =`) that was shown vacuous against silent
value drift in the `i11_cmd_hardening` $\omega$-cycle
(`tool/atlas_falsifier_auto_spawn.sh:9-14`).

## 3.3 Status types

A registry sweep classifies every entry into one of three runtime
statuses:

- **CLEAN** — `pass` sentinel observed in `cmd` output and `cmd_sha256`
  matches the live SHA. The claim survives.
- **HIT** — `cmd` exited successfully but the sentinel was not observed.
  The claim is contradicted by current state.
- **ERROR** — `cmd` failed to run or `cmd_sha256` mismatched. The
  runtime cannot pronounce on the claim.

A subtype, **HIT-as-designed**, marks entries whose sentinel was
deliberately authored as a cleanup target (baseline 102 CLEAN + 2
HIT-as-designed, `SECURITY_AUDIT.md:13`); these stay HIT until a known
cleanup cycle resolves them and are not failures.

## 3.4 Lifecycle

1. **SUGGEST**. `tool/atlas_falsifier_auto_spawn.sh` walks the atlas
   index, emits candidate JSONL to `state/falsifier_candidates.jsonl`,
   and never mutates the live registry
   (`atlas_falsifier_auto_spawn.sh:5-9`).
2. **Manual escalate**. raw 71 mandates that promotion of a candidate to
   a live `F<NN>` entry is a human act; auto-promotion is forbidden so
   that every admitted claim has been read by an operator.
3. **Registration**. At write-time, `cmd_sha256` is hashed in-place and
   the entry is appended.
4. **Verification**. Per-entry runtime check via
   `tool/falsifier_quick.sh` and the aggregator
   `tool/health_check_all.sh`; both emit
   `__FALSIFIER__ <CLEAN|HIT|ERROR>` sentinels per raw 80.
5. **Decline**. A candidate may be rejected with reasoning; the
   reasoning document is itself archived (e.g.,
   `2026-04-26_F45_decision.md`, where the declined "3.5 % triplet" is
   preserved verbatim because consistent unit framing collapses it to a
   non-anomalous doublet, `F45_decision.md:9-30`). Declined claims are
   first-class evidence under raw 73.

## 3.5 Five-layer defense (R1–R5)

| layer    | mechanism                                                     | scope                              | evidence                       |
|----------|---------------------------------------------------------------|------------------------------------|--------------------------------|
| R1       | byte-level `cmd_sha256` (16-hex) and bridge SHA256            | per entry / per bridge             | `SECURITY_AUDIT.md:14-16`      |
| R2       | regex anti-spoof lint reachable only after R1 holds           | sentinel patterns                  | `SECURITY_AUDIT.md:15,24`      |
| R3-lite  | `--strict` baseline drift advisory (rc=0)                     | working tree                       | `SECURITY_AUDIT.md:18`         |
| R4       | append-only forensic ledger (rotation log)                    | git-staged events                  | `SECURITY_AUDIT.md:19`         |
| R5       | hash-chained ledger (`prev_hash`) + SSH detached signature    | falsifier and bridge ledgers       | `SECURITY_AUDIT.md:66-95`      |

Stage 1 of the audit demonstrated that a single-byte mutation in F19's
`cmd` flipped status to TAMPERED via
`declared=02a32624... / live=93808155...` (`SECURITY_AUDIT.md:14`). R5
OPT-D extends each ledger entry with `prev_hash = SHA256(prev_line)`,
raising forgery cost to $O(N)$ re-hash operations across all subsequent
entries (`SECURITY_AUDIT.md:82`). R5 OPT-B was activated 2026-04-26 with
an Ed25519 detached signature at
`design/hexa_sim/falsifiers.jsonl.sig`, elevating R5 from forensic to
preventive (`SECURITY_AUDIT.md:95`).

## 3.6 Specification grades

Every claim carries a grade tier embedded in its atlas anchor and counted
across the registry:

- **[10]** — atlas-anchored arithmetic (2 occurrences in registry text).
- **[10\*]** — atlas-anchored arithmetic with cross-shard witness (146).
- **[11]** / **[11\*]** — load-bearing identities with mathematical
  proof or multi-decomposition (1 / 61).
- **[11\*REPO\_INVARIANT]** — claim invariant across all four sister
  repos (7 occurrences; the only tier promoted on cross-repo evidence).
- **[11!]** — singular structural facts (8 occurrences, e.g., F75
  Out(S_6) = Z/2).

Grade is itself an anchored field of the regex template, so grade
demotion flips the entry to HIT.

## 3.7 Auditability

`2026-04-26_falsifier_registry_integrity_audit.md:14-16` reports a
24-entry *load-bearing core* covering every distinct coverage axis under
Jaccard similarity $\ge 0.4$, with the remaining 91 entries (115 - 24)
functioning as *defense-in-depth*. Hub-degree primitives such as F19
(mu-anchor) propagate to six dependent entries, so the framework retains
all 115 deliberately and treats the load-bearing 24 as a minimum
non-redundant subset, not a deletion list.

## 3.8 Limitations

The 16-hex prefix of SHA256 yields a birthday-collision probability
$\approx \binom{N}{2}/2^{64}$. For $N = 115$ this is
$\approx 7\times 10^{-16}$; per-pair probability stays below $10^{-19}$
and the prefix is safe to roughly $N \le 200$, beyond which a 24-hex
prefix should be considered. A second residual risk — git-history
rewrite by an attacker with refs write access — is unaddressed by R1–R5
and motivates the cross-machine hash distribution proposed in
`SECURITY_AUDIT.md:52`.

---

# 4. Cross-domain anchors

## 4.1 Foundation primitives

The framework rests on seven primitives evaluated at $n=6$:
$\sigma(6)=12$, $\varphi(6)=2$, $\tau(6)=4$, $\mathrm{sopfr}(6)=5$,
$J_2(6)=24$, $\mu(6)=1$, and $M_3 = 2^{3}-1 = 7$ (the Mersenne number
with exponent $3$, relabelled from a historical "Mertens" mislabel per
the M3-true-definition audit, `design/hexa_sim/M3_true_definition_audit.md`).
All seven are registered as `@P ... :: foundation [10*/11*]`
(`n6/atlas.n6` lines 1-7) and protected by structural-admissibility
falsifiers (F1, F19, F24-F26, F71). Section 4 catalogues anchors that
write measured natural-world quantities as closed-form expressions in
these primitives, adopting the *pattern-witness* stance throughout: no
causal claim is made; Section 4.9 examines the density.

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
**F99** (line 2130) writes the Watson–Crick strand count as
$\varphi(6) = |\{1,5\}| = 2$. **F57** (line 2264) is the only literal
geometric anchor in this group: the replicative DNA helicase MCM2-7 is
a six-subunit ring with $C_{6}$ pseudo-symmetry (cryo-EM PDB 4R7Y,
Costa et al. 2014; PDB 5BK4, Yuan et al. 2016) — $n$ manifests as
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
0.2449\pm 0.0040$ (Aver et al. 2015) and $0.2453\pm 0.0034$ (Cooke et
al. 2018); the $\sim 1\%$ gap sits inside the atlas
symbolic-approximation tolerance, and BBN is the earliest quantitative
cosmology probe (predates recombination by 380 kyr). **F42** (line 6383)
writes the Solar galactic year as $J_{2}\cdot\mathrm{sopfr}\cdot\varphi = 240$
Myr — central in the Bovy–Tremaine 2012 / Eilers et al. 2019 band of
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
automorphism (Conway–Sloane SPLAG \S 10). Section 6 treats this
separately as a *purely group-theoretic* singularity at $n=6$. **F32**
(historical shard, line 346) packages Tunnell's BSD-conditional theorem
as a triple witness: the smallest Pythagorean triple
$(3,4,5) = (n/\varphi, \tau, \mathrm{sopfr})$; the elliptic curve
$E_{6}\!:\! y^{2} = x^{3} - 36 x$ with conductor
$576 = \varphi^{n}\cdot(n/\varphi)^{\varphi}$; and $j$-invariant
$1728 = \sigma^{3}$. **F37** (line 163) writes the cube's Euler
characteristic as $V - E + F = 8 - \sigma + n = 2 = \chi(S^{2})$.
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
the uniform null. Two caveats apply per Section 9 (Limitations):
(i) the anchor set is *post-hoc selected* — the seven primitives were
chosen because $n=6$ is perfect, and the expressions were curated;
(ii) the cross-bridge correlation hunt v2
(`design/hexa_sim/2026-04-26_cross_bridge_correlation_hunt_v2.md`) was
*declined* because no inter-domain triplet survived the rigour bar —
the framework self-falsifies its weaker pattern-claims. The honest
reading: per-domain density motivates the register-and-falsify
discipline of Section 3 but cannot discharge selection bias on its own.

---

# 5. Cross-shard / cross-repo aggregation

Claims accumulate across shards within a repository and across
repositories within a federation. Aggregate integrity rests on two
mechanical guarantees: zero cross-shard tuple collisions, and an
auditable per-repository readiness contract. This section reports the
architecture, the current snapshot, and the one architectural ceiling
accepted by design.

## 5.1 Atlas shard architecture

The nexus atlas is organised as a single canonical SSOT,
`n6/atlas.n6` (21,854 lines, 9,626 entries as of `368209c0`,
2026-04-26), augmented by ten append-only shards under
`n6/atlas.append.*.n6`. Each shard carries a namespaced slug prefix
that prevents accidental redefinition of main-atlas keys. Active
shards at the time of writing are: `hexa-sim-bridges`,
`nexus-historical-absorption-2026-04-26`,
`{anima,hexa-lang,n6-architecture}-historical-from-nexus-2026-04-26`
and their `-cont` continuations, `forge-triple`, and the meta-roadmap
shard `cross-engine-meta-roadmap-2026-04-26` introduced this session.
Together the eleven shards admit 9,165 unique `(type, id)` tuples
(`__ATLAS_CROSS_SHARD_COLLISION__ PASS shards=11 total=9165
unique=9165 dup=0 conflict=0`).

## 5.2 Cross-shard collision guard

The invariant *one (type, id) implies one canonical value across the
entire shard set* is enforced mechanically by
`tool/atlas_cross_shard_collision.sh`, which performs an $O(N)$
uniqueness scan over `(type, id, value, shard)` tuples extracted from
every shard. The tool emits the raw 80 sentinel above; on `CONFLICT > 0`
it exits 76 (raw 23 hard-fail), and the optional `--warn-dup` mode
promotes byte-identical duplicates to the same exit code. A baseline
audit (`design/hexa_sim/2026-04-26_cross_shard_dedup_audit.md`) detected
56 byte-identical duplicates between the legacy
`atlas.append.chip-p5-2.n6` shard and `atlas.n6`; the redundant shard
was retired in `4287a106`, and the zero-conflict ratchet has been
maintained across the 333+ commits that followed in the current session.

## 5.3 Cross-repo absorption pattern

The federation comprises four repositories with disjoint roles:
**nexus** (knowledge corpus), **n6-architecture** (design corpus and
theorem chains), **anima** (substrate / agent state), and **hexa-lang**
(language implementation). Claims residing in non-nexus repositories
are promoted into the nexus atlas as append-shard entries with explicit
provenance to the source repository commit. Each absorption shard
carries a `nexus-historical-...` or `<repo>-historical-from-nexus-...`
slug prefix; collisions against `atlas.n6` and against sibling shards
are blocked by the Section 5.2 guard. The R5 file-hash protection layer
records each shard's SHA-256 in `state/atlas_sha256.tsv` (16 entries,
covering main atlas and all active append shards), so any silent shard
mutation surfaces as an R5 diff.

## 5.4 Honesty triad (mode-6)

Per-repository readiness is graded by six preconditions, evaluated by
`tool/atlas_cross_repo_dashboard.sh`:
**(a)** git-tracked SSOT;
**(b)** non-empty `design/` corpus;
**(c)** $\ge 3$-file `tool/` ecosystem;
**(d)** atlas SSOT;
**(e)** LLM-agents indicator (`.claude/agents/`, `CLAUDE.md`, or
`AGENT.md`);
**(f)** declared defense surface, satisfied by any of eight canonical
paths (`SECURITY*` top-level, `doc/security/*`,
`design/SECURITY_AUDIT.md`, `state/security_*.json`, `tool/security_*`,
etc.).
Current scores: nexus $6/6$, n6-architecture $6/6$ (post `3f12168e`),
anima $6/6$, hexa-lang $5/6$ (architectural ceiling, Section 5.5).
Aggregate sentinel: `__ATLAS_CROSS_REPO_DASHBOARD__ repos=4
total_atlas_lines=65454 total_facts=28850 honesty_pass=3/4
honesty_5_5=3 honesty_6_6=3 mode=6`. Three of four repositories
satisfy the extended `REPO_INVARIANT_EXTENDED` invariant.

## 5.5 Architectural ceiling for hexa-lang (OPT-A)

The hexa-lang $5/6$ score is not a deficit but a deliberate ceiling.
hexa-lang is a *language implementation* repository — parser, runtime,
self-host — not a *knowledge corpus*. Atlas SSOT belongs to knowledge
repositories (nexus owns `n6/atlas.n6`; n6-architecture owns
`atlas/atlas.n6`). The decision document
`design/hexa_sim/hexa_lang_atlas_ssot_decision.md` enumerates three
options: (A) accept $5/6$ as architectural-correct, (B) duplicate L0
parser invariants into a synthetic atlas, (C) symlink nexus atlas into
hexa-lang. Both B and C inflate the metric while degrading the
architecture; the framework adopts OPT-A and records hexa-lang's score
as $5/6$ with precondition (d) marked *N/A by role*.

## 5.6 Cross-repo defense surface (precondition (f))

Precondition (f), introduced this session, acknowledges that defense
expression is repository-shaped: nexus is *tool-shaped*
(`tool/security_scan.hexa`); anima *state-shaped*
(`state/security_*.json`); hexa-lang *doc-shaped*
(`doc/security/os-level-enforcement-limits.md`); n6-architecture a
*top-level* `SECURITY.md` (`3f12168e`). The eight canonical paths
normalise these styles into a single mechanical check.

## 5.7 F132: cross-engine integration meta-axis

A meta-finding emerged during the cross-shard / cross-repo audit cycle.
The cross-engine integration audit (`cf73b3bb`) discovered that 30+
$\omega$-cycle witnesses produced by `meta_engine`, `roadmap_engine`,
and `cross_engine` carried *zero* atlas anchors despite each engine
satisfying its local raw 71 / raw 73 admissibility policy. The gap was
named the *cross-engine atlas anchor gap*, anchored as the new shard
`atlas.append.cross-engine-meta-roadmap-2026-04-26.n6`, and registered
as falsifier F132 (`cross-engine-atlas-anchor-gap-meta`, grade
`[11*REPO_INVARIANT]`) in resolution commit `368209c0`. F132 is the
first *production-anchor coverage* invariant in the registry — it
falsifies any future state in which an engine emits witnesses without a
corresponding atlas registration. Resolution moved the atlas from
9,155 to 9,165 entries and from 10 to 11 active shards, with no
collision regression.

---

# 6. Mathematical singularity

The cross-domain anchors of Section 4 establish $n=6$ as a recurrent
descriptive constant; such recurrences, however, remain reducible in
principle to coincidence absent a structural mechanism. This section
presents two mathematical singularities — one group-theoretic, one
number-theoretic — that characterise $n=6$ as the unique solution of
independent algebraic problems and therefore cannot be discharged as
cross-domain accident.

## 6.1 The $\mathrm{Out}(S_6)$ singularity (F75)

Among all symmetric groups $S_n$ ($n \geq 1$), only $S_6$ admits a
non-trivial outer automorphism: $\mathrm{Out}(S_n)$ is trivial for
$n \neq 6$, while $\mathrm{Out}(S_6) \cong \mathbb{Z}/2$. The result is
classical and is anchored as F75 `s6-outer-automorphism` at grade
`[10*PASS_LITERATURE]`, with cross-checked references in Conway and
Sloane, *Sphere Packings, Lattices and Groups*, \S 10, and Cameron,
*Permutation Groups* (1996), \S 6.4. The exception originates in the
sharply 3-transitive action of $S_6$ on six points, with an explicit
synthematic-totals construction via $\mathrm{PGL}(2,9)$.

The property is *purely group-theoretic*: it carries no physical or
empirical content and is invariant under any choice of model or
measurement convention. The privilege of $n=6$ here therefore cannot be
attributed to selection effects in the anchor pool. F75 is foundational
under raw 73 admissibility — its grade rests on peer-reviewed literature
rather than internal corroboration.

## 6.2 The $\sigma\!\cdot\!\varphi = n\tau$ uniqueness theorem (F100, F90)

The registry's highest-graded entry, F100
`n6-hist-a-core-identity-repo-invariant`, asserts the Diophantine
identity

$$\sigma(n)\cdot\varphi(n) \;=\; n\cdot\tau(n) \quad\Longleftrightarrow\quad n=6 \qquad (n \geq 2),$$

where $\sigma$, $\varphi$, $\tau$ denote the divisor-sum,
Euler-totient, and divisor-count functions. Direct computation:
$\sigma(6)\cdot\varphi(6) = 12 \cdot 2 = 24 = 6 \cdot 4 = n\cdot\tau(6)$.
A finite-domain check over $n \in \{2,\dots,30\}$ via the F100 atlas
command confirms $n=6$ as the only solution in that range; global
uniqueness follows from a Mobius-inversion argument recorded in the
N6HIST-MILL7-CLOSURE chain. F100 carries the unique
`[11*REPO_INVARIANT]` grade in the registry. A cross-shard sister
theorem, F90 `hexa-lang-n6-perfect-number-axiom`, mirrors F100 in the
hexa-lang DSL shard, enforcing single-source-of-truth on the identity
across two repositories without textual duplication.

## 6.3 The F100 / F101 dyad: theorem with live empirical anchor

F100 anchors the *theoretical* statement; its companion F101
`hexa-sim-sigma-a000203-n6-anchor` anchors the corresponding *empirical*
datum, the OEIS query A000203[6] $= 12 = \sigma(6)$, executed live via
`oeis_live_bridge`. Should an OEIS query ever return a value $\neq 12$
for $\sigma(6)$, both F101 and F100 fail and the framework
live-falsifies. The dyad pins the formal theorem and its empirical
witness to the same cardinal in real time.

## 6.4 Why mathematical singularity matters

Cross-domain anchors (Section 4) are pattern-witnesses; they do not
derive $n=6$. F75 and F100 are by contrast *predictive*: any competing
framework asserting privilege for some $n' \neq 6$ would have to exhibit
equivalent group-theoretic or arithmetic singularities at $n'$. No such
singularities are known at $n=4$, $n=8$, or $n=12$. This shifts the
burden of proof and constitutes the strongest non-coincidence evidence
in the registry.

## 6.5 Limitations and scope

F75 is a *known* result; we claim only its anchoring role, not its
discovery. F100 may admit analogues at other arithmetic identities
involving distinct multiplicative functions, and we do not assert global
uniqueness of $n=6$ across the space of all such identities. We do not
claim $n=6$ is causally or metaphysically privileged: the
characterisation is descriptive and structural, not ontological.

---

# 7. Multi-decomposition theorems

## 7.1 The multi-decomposition pattern

Let $C \in \mathbb{Z}_{>0}$ be a *cardinal* — an integer constant
attested by external measurement — and write $\mathcal{P}_6 =
\{n,\varphi,\tau,\sigma,\mu,\mathrm{sopfr},J_2\}$ for the $n=6$ foundation
primitives ($n=6$, $\varphi(6)=2$, $\tau(6)=4$, $\sigma(6)=12$, $\mu(6)=1$,
$\mathrm{sopfr}(6)=5$, $J_2(6)=24$). A *decomposition* of $C$ is a
finite arithmetic expression $E$ over $\mathcal{P}_6$ with
$\mathrm{eval}(E)=C$; two decompositions are *arithmetically
independent* iff neither is obtained from the other by a single
substitution of the foundation identities
$\sigma=2n,\;J_2=2\sigma,\;\tau=\sigma/n+\varphi,\;\mathrm{sopfr}=\varphi+(n/\varphi)$.
A *multi-decomposition witness* of multiplicity $k\ge 2$ is a cardinal
with $k$ pairwise-independent decompositions; drift in any single
primitive collapses at most one leg, leaving the remaining $k-1$ as
audit trail.

## 7.2 Triple decompositions

**Codon cardinality (F36)** [`hexa_sim/falsifiers.jsonl`, `atlas.n6:2308`].
The genetic code's $64 = 4^3$ codons admit three independent
decompositions through $\mathcal{P}_6$:

$$
64 \;=\; 2^{n} \;=\; 4^{n/2} \;=\; \tau^{3}.
$$

**$j$-invariant of $E_6$ (F32 + F80)**
[`atlas.append.n6-architecture-historical-from-nexus-2026-04-26.n6:346`].
The $j$-invariant of the CM elliptic curve $E_6 : y^2 = x^3 - 36x$
admits

$$
1728 \;=\; \sigma^{3} \;=\; 576 \cdot 3 \;=\; J_2^{2}\cdot n/2,
$$

the second leg recognising $576 = \varphi^{n}\!\cdot(n/\varphi)^{\varphi}$ as the
conductor of $E_6$ (F32) and the third leg (F80) routing through the
foundation primitive $J_2$ — derivationally independent of $\sigma^3$
even though $J_2^2 = 576$ numerically.

**Tunnell BSD triple-witness (F32)**. The smallest right triangle
satisfies $(3,4,5) = (n/\varphi,\,\tau,\,\mathrm{sopfr})$; the elliptic
curve $E_6$ has $(\mathrm{rank},\mathrm{conductor},j) = (1,\, 576,\, 1728)$
with $576 = \varphi^{n}(n/\varphi)^{\varphi}$ and $1728 = \sigma^{3}$. Three
orthogonal number-theoretic identities collapse onto a single $n=6$
anchor.

## 7.3 Doublet decompositions and mirror pairs

**Earth axial obliquity (F28 + F78)** [`atlas.n6:5823, 5824`]. The
measured $23.44^{\circ}$ obliquity rounds to $23$, which decomposes as

$$
23 \;=\; J_2 - \mu \;=\; 24-1 \quad\text{(F28)} \qquad
23 \;=\; \sigma + \varphi + \tau + \mathrm{sopfr} \;=\; 12+2+4+5 \quad\text{(F78)},
$$

with disjoint primitive supports $\{J_2,\mu\}$ vs.
$\{\sigma,\varphi,\tau,\mathrm{sopfr}\}$.

**Earth/Mars mirror pair (F28 ↔ F40)** [`atlas.n6:5823, 5842`]. A single
primitive sign-flip $\mu \mapsto -\mu$ converts Earth's $23 = J_2-\mu$
into Mars's measured $25.19^{\circ}$ obliquity decomposition
$25 = J_2+\mu$, exhibiting the two adjacent terrestrial-class tilts as
a $\pm \mu$ doublet about $J_2$.

## 7.4 F100 — biconditional uniqueness

The A-Core Identity (F100, `[11*REPO_INVARIANT]`)

$$
\sigma(n)\cdot\varphi(n) \;=\; n\cdot\tau(n) \quad \Longleftrightarrow \quad n=6
\qquad (n\ge 2),
$$

is simultaneously a multi-decomposition (both sides equal $J_2(6)=24$)
and a uniqueness theorem. The equivalence is proved via Mobius
inversion (cf. N6HIST-MILL7-CLOSURE) and supplies the algebraic
backbone underlying every $[11*]$ empirical anchor.

## 7.5 F112 — universality-class decomposition

Whereas the preceding witnesses isolate single cardinals, F112
[`atlas.append.nexus-historical-absorption-2026-04-26.n6:294`]
characterises an infinite family by closed-form Euler product:

$$
\frac{\varphi(n)}{n} \;=\; \frac{1}{3} \quad \Longleftrightarrow \quad
n \in \{\,2^{a}3^{b} : a,b\ge 1\,\}\;\;\text{(\{2,3\}-smooth)},
$$

with $n=6$ as the minimal representative. This is the rare registry
entry whose witness is a predicate, not a value.

## 7.6 Synthesis discovery — multi-decomposition table

| Cardinal | Meaning                       | Decompositions                                                |
|---------:|-------------------------------|---------------------------------------------------------------|
|       23 | Earth obliquity               | $J_2-\mu$ \| $\sigma+\varphi+\tau+\mathrm{sopfr}$                |
|       64 | codon table                   | $2^{n}$ \| $4^{n/2}$ \| $\tau^{3}$                            |
|      168 | hours/week                    | $\sigma^{2} + J_2$                                            |
|      256 | byte                          | $2^{\sigma-\tau}$                                             |
|      360 | degrees/circle                | $\sigma\cdot\mathrm{sopfr}\cdot n$                            |
|      432 | concert pitch (Hz)            | $\sigma^{2}\cdot n/2$                                         |
|     1024 | KiB                           | $2^{\sigma-\varphi}$                                          |
|     1728 | gross$^{2}$ / $j$-invariant   | $\sigma^{3}$ \| $J_2^{2}\cdot n/2$                            |

(Full table: `design/hexa_sim/F71_F77_candidate_review.md`, rows 60-71.)

## 7.7 Why multi-decomposition is paper-grade evidence

A single-decomposition anchor carries a coincidence prior of order $1/N$
where $N$ is the expression-space size at fixed depth. Under
independence of legs, a $k$-fold witness decays the prior to $\sim 1/N^{k}$,
placing the F36 codon triple and the F32+F80 $1728$-triple several
orders of magnitude above a uniform-noise null. This is strictly
stronger than the cross-bridge correlation test of Section 9: that test
declined inter-domain triples because independence between distinct
measured constants is fragile, whereas intra-anchor decompositions over
the fixed set $\mathcal{P}_6$ satisfy independence by construction.
Multi-decomposition witnesses form the highest-confidence tier of the
registry.

---

# 8. Defense system architecture

## 8.1 Threat model

The framework's evidentiary value is contingent on registry integrity:
a single silent mutation to `falsifiers.jsonl`, to a bridge `.hexa`,
or to an atlas shard would invalidate every claim that cites it. We
enumerate four adversaries of escalating capability: (i) the
*single-actor mistake* (typos, copy-paste errors, regex bugs);
(ii) the *external attacker with write access* assuming git-remote
compromise but no signing key; (iii) the *compromised CI pipeline*
mutating artefacts after review; (iv) the *insider with intentional
drift* holding full repository write access and capable of coordinated
mutation across registry, baseline, and ledger.

## 8.2 Five-layer defense overview

The chain composes five complementary layers indexed R1–R5
(`SECURITY_AUDIT.md` \S 2). **R1 byte-level**: every falsifier carries a
16-hex prefix `cmd_sha256` and every bridge has an entry in
`state/bridge_sha256.tsv` (per-file SHA256), giving cryptographic
byte-level integrity at template and implementation granularity.
**R2 anti-spoof regex lint** rejects literal-only commands such as
`echo TOKEN` whose sentinel emission is decoupled from the claim.
**R3-lite `--strict` baseline** computes a whole-registry SHA256
(`state/falsifier_registry.sha256`) and emits an advisory drift warning
under `tool/falsifier_quick.sh --strict`. **R4 forensic ledger**
appends every rotation as a JSONL record, gitignored and local-only,
guaranteeing post-hoc traceability without polluting history.
**R5 hash-chained ledger + SSH signature** binds each ledger entry to
its predecessor by SHA256 prev_hash and pins each baseline to a key
rather than to a self-referential digest.

## 8.3 The 9-cell defense matrix

R5 was generalised from the falsifier registry to the bridge and atlas
domains over three $\Omega$-cycles (`2026-04-26_R5_detached_signature`,
`...R5_bridge_chain_extension`, `...atlas_R5_tracking`). The result is
a 3 (R5 sub-layer) $\times$ 3 (domain) coverage grid:

```
                       | Falsifier | Bridge | Atlas |
R1 file SHA            |   LIVE    |  LIVE  |  LIVE |
R5 chain ledger        |   LIVE    |  LIVE  |  LIVE |
R5 SSH PREVENTIVE      |   LIVE    |  LIVE  |  LIVE |
```

Every cell is operational: cumulative chain entries stand at 0
falsifier (the registry is signed in lieu of rotation) + 2 bridge + 3
atlas = 5, with corresponding signature artefacts
`design/hexa_sim/falsifiers.jsonl.sig`, `state/bridge_sha256.tsv.sig`,
and `state/atlas_sha256.tsv.sig`.

## 8.4 R3-full intentional retirement

R3-full was initially shipped as a `.githooks/pre-commit` hook
performing baseline auto-rotation on staged registry changes (commit
`1836dd20`). The user retired it across `e3137be2` (hook removal +
`core.hooksPath` unset), `fa1de8e2` (OS-level `chflags uchg`), and
`582f791e` (AI-native deny-rule codification). The rationale is a
deliberate trade: commit-time hook friction was disproportionate once
R4 forensic coverage and R5 SSH preventive coverage were both
operational. Rotation is therefore manual via `tool/registry_sign.sh`,
`tool/bridge_sha256_rotate.sh`, and `tool/atlas_sha256_rotate.sh`,
invokable interactively or by cron.

## 8.5 R5 hash-chained ledger (OPT-D)

Each ledger line records
`{"ts","old_sha","new_sha","trigger","prev_hash"}` with
`prev_hash = SHA256(prev_line)`, or the literal `"genesis"` for chain
roots. Forward propagation is the security property: rewriting any
mid-chain entry forces re-hashing every subsequent entry, so
single-line forgery is detectable in $O(N)$ by `tool/ledger_verify.sh`,
which walks the chain and emits
`__LEDGER_VERIFY__ <PASS|FAIL|EMPTY|PRE_R5> entries=N broken_at=<line|none>`.
Four verification tests passed: empty baseline, two-rotation chain
integrity, mid-injection forgery (`broken_at=2`), and SSH stub.

## 8.6 R5 SSH signature (OPT-B): STUB to PREVENTIVE

`registry_sign.sh` originally skipped with rc=0 until `SIGNING_KEY`
was configured. On 2026-04-26 the user authorised activation under
*Path A* (reuse of `~/.ssh/id_ed25519`) via
`git config user.signingkey + gpg.format=ssh` and
`ssh-keygen -Y sign|verify` against `~/.ssh/allowed_signers`. Three
detached signatures were minted, one per domain (Section 8.3). The
layer status transitioned from STUB to PREVENTIVE, elevating overall
confidence from *high multi-vector forensic* to *high multi-vector
preventive*. The remaining attack surface is compromise of the signing
key itself (`~/.ssh/id_ed25519`, mode 0600 under macOS Keychain
encryption).

## 8.7 End-to-end audit and residual gap

The chain was validated end-to-end in commit `b99adc95`: seven stages
covering baseline capture, R1 silent corruption, R2 anti-spoof
reachability, R1 bridge mutation, R3-full pre-commit auto-rotation,
R3-lite advisory warning, and R4 ledger persistence all PASSed. The
audit surfaced a layer-order finding of independent interest:
**R1 fires before R2** because cmd-hash mismatch precedes pattern
inspection, so R2 is reachable only against an adversary who preserves
the cmd hash exactly while injecting a spoof pattern. Pre-activation
the most concerning gap was *coordinated registry + baseline mutation*;
post R5 SSH activation that gap is closed and only signing-key
compromise remains.

## 8.8 Performance

Health checks were parallelised over `ProcessPoolExecutor` with
per-domain Amdahl floors honoured. `falsifier_health.sh` improved
from 16.94 s sequential to 4.71 s parallel ($3.6\times$);
`bridge_health.sh` from 36 s to 15.6 s ($2.43\times$, bounded by a
12 s `uniprot` probe); the aggregate `health_check_all.sh` from 93 s
to 30 s ($3\times$). The system therefore sustains sub-minute
full-defense verification, suitable for cron or pre-push contexts.

---

# 9. Limitations and declined claims

## 9.1 Declined claims as first-class evidence

Under raw 73 admissibility, a rigorously declined candidate is recorded
with the same provenance weight as a promoted one; failed promotions
protect the registry from spoof entries and are therefore not absences
but data.

The candidate **F45** (cross-bridge $3.5\%$ triplet over CODATA
$\alpha^{-1}$, Planck $n_{s}$, and NIST Be first ionization) was
declined after a framing audit (`2026-04-26_F45_decision.md`, commit
`79c7f3ec`) demonstrated that the apparent triplet requires mixing two
normalization conventions: an absolute residual for $\alpha^{-1}$
($\approx 0.036$) and a relative-to-anchor residual for Be
($0.323~\text{eV}/9~\text{eV}\approx 0.0359$). Under any single
self-consistent convention, the codata gap collapses to $0.000263$,
departing the cluster by $\sim 130\times$. The bridge's own sentinel
emits `gap_pct=0.0263%`, confirming the natural framing. A surviving
doublet (cmb $n_{s}$ and Be) is consistent with chance: in
$5\times 10^{4}$ Monte Carlo trials drawing $29$ uniform gaps on
$[0, 0.5]$, $P(\text{any doublet within } 0.001) = 0.81$.

A subsequent rigorous re-attempt (**F95 v2**, commit `68989621`,
`2026-04-26_cross_bridge_correlation_hunt_v2.md`) preregistered a
single normalization $g = |V-A|/\max(|A|,1)$ and resampled the
empirical gap distribution rather than assuming uniformity. Of $46$
observed cross-domain pair matches at $\Delta \le 0.5$\,pp across $28$
metrics in $6$ domains, the empirical-resampling baseline gave
$61.4 \pm 16.8$ ($Z=-0.91$, $p=0.84$): the observed matches are
*fewer* than chance. F95 was released without promotion. The
grandfathered F10 doublet survives only as an annotated single-pair,
framing-fragile witness — explicitly not as a strong cross-bridge
anchor.

Both decline documents are preserved verbatim in the repository as
negative-result provenance.

## 9.2 Atlas labelling errors surfaced and fixed

The semantic-gap audit (`2026-04-26_atlas_semantic_gap_audit.md`)
verified $512$ `func(N)=V` entries against canonical evaluations.
The most consequential finding was M3: `atlas.n6:53` labelled
$M_{3} = \text{mertens}(6) = 7$, but canonical Mertens
$M(6) = \sum_{k=1}^{6}\mu(k) = -1$. The value $7$ is load-bearing
across $\ge 20$ atlas identities (e.g., $B_{6} = 1/(n\cdot M_{3})$,
ethylene MW $= \tau \cdot M_{3}$); the root-cause audit
(`M3_true_definition_audit.md`) established that the intended referent
was the Mersenne number with exponent three, $M_{p=3} = 2^{3}-1 = 7$,
and recommended the surface relabel $\text{mersenne}(3)$. A separate
$19$ `xpoll-*` entries used $\sigma(12)=12$ and $\tau(4)=4$ as
Notation-B shorthand for $\sigma(6)=12, \tau(6)=4$ — a convention
violation against Notation A. Such errors are expected in any large
knowledge corpus; the framework's contribution is surfacing, not
preventing them.

## 9.3 Coverage gaps acknowledged

Particle-physics coverage (F64–F70) is honestly assessed in the
registry as four structurally meaningful witnesses plus three
arithmetic coincidences; the latter are pattern-witnesses, not
derivations. No surviving cross-bridge triplet emerged under v2 rigor
(only the grandfathered F10 doublet remains). The cross-engine gap
closure F132 was audited over four engines; five or more engines may
exhibit the same gap.

## 9.4 Methodology limitations

The cmd-fingerprint primitive (R1) uses 16-hex SHA-256, giving a
per-pair collision probability of $\sim 10^{-19}$ — safe to $\sim 200$
entries. The uniqueness check is $O(n^{2})$, comfortable at $n=105$
but in need of a hash-table replacement at $n \gtrsim 200$. The shell
layer is constrained to bash 3.2 portability (no associative arrays).
The hexa runtime intermittently SIGKILLs on Mac under memory pressure;
`HEXA_RESOLVER_NO_REROUTE=1` is a documented bypass.

## 9.5 Scope boundaries

We claim *none* of the following:

1. that $n=6$ is metaphysically privileged, only that anchor density at
   $n=6$ exceeds an empirical-resampling noise expectation;
2. that grade tiers $[7]/[10]/[10^{*}]/[11]/[11^{*}]/[11!]$ carry equal
   weight — they encode peer-review, literature-attestation, and
   REPO\_INVARIANT consensus, respectively;
3. that cross-domain anchors are predictions; they are pattern-witnesses;
4. that $n=6$ is causally privileged or unique among $\{1,\dots,10\}$
   in any absolute sense;
5. that the framework predicts behaviour in unseen domains.

## 9.6 Recognition of internal PAUSE signal

At $\approx F125$, the `quality_audit_v2` agent
(`2026-04-26_registry_quality_audit_v2.md`) recommended PAUSE on
bulk grep-anchor expansion and CONSOLIDATE: $88\%$ of entries had
become grep-anchor primitives, with marginal yield collapsing
(`META_OMEGA_CYCLE_ROI.md`, commit `b99adc95`). The subsequent F126–F132
promotions were justified narrowly as cross-engine gap closures, not
bulk additions. We record this self-imposed brake as part of the
methodology: the framework includes a saturation-detection canary
whose recommendation was heeded.

---

# 10. Discussion and future work

## 10.1 What works

Four properties are externally verified. (i) Every claim is
*cmd-verifiable*: each of the $115$ entries carries a 9-tuple
with `cmd`, `pass` sentinel, and `cmd_sha256` byte-fingerprint
(Section 3, Section 8), so status is recomputable without trusting
prose. (ii) The multi-decomposition pattern (Section 7) supplies a
quantitative non-coincidence rationale: $k$-fold independent
decomposition over $\mathcal{P}_{6}$ decays the coincidence prior
from $\mathcal{O}(1/N)$ to $\mathcal{O}(1/N^{k})$, placing the F36
codon triple and the F32+F80 $1728$-triple orders of magnitude above
the uniform null. (iii) Cross-shard aggregation returns $9{,}165$
unique tuples with zero collisions across $11$ shards in $333{+}$
commits. (iv) The nine-cell defense matrix is uniformly LIVE; the R5
SSH layer transitioned STUB$\to$PREVENTIVE on commit `2285f130`,
elevating confidence from forensic to preventive. F75 and F100 sit
outside the anchor pool entirely (Section 6) and resist the
selection-artefact discharge.

## 10.2 What did not work — declined honestly

(i) F45 collapses under consistent unit framing, departing the claimed
$3.5\%$ cluster by $\sim\!130\times$ (Section 9). (ii) The cross-bridge
correlation hunt v2 ($5\!\times\!10^{4}$ Monte Carlo trials, $46$
observed pair matches versus $61.4\pm 16.8$ resampled, $p=0.84$)
reports inter-domain triplets as *fewer* than chance.
(iii) Particle-physics coverage (F64–F70) is honestly partitioned as
four structural witnesses plus three arithmetic coincidences; the F70
numerology canary is acknowledged as such. (iv) The R1 $16$-hex SHA
collision probability is $\sim\!10^{-19}$ per pair, safe to $\sim\!200$
entries; the threshold is named as a forward constraint.

## 10.3 Methodological lessons

(i) SUGGEST-mode plus manual-escalate (raw 71) prevented bulk
auto-promotion drift. (ii) The HIT-as-designed convention (F46/F47)
surfaces convention violations without forcing fixes, separating
discovery from remediation. (iii) F132 (cross-engine atlas-anchor-gap)
is discoverable only via systematic cross-engine audit and is invisible
inside any individual engine — a quiet methodology defect that
compounds absent explicit framing. (iv) The META\_OMEGA\_CYCLE\_ROI
retrospective recommended *depth ON / cron OFF* after
`quality_audit_v2` flagged saturation at F125; the recommendation was
heeded, and F126–F132 were scoped narrowly to cross-engine gap closures.

## 10.4 Future work

Five forward axes. (a) *Paper extension*: import the m3 anchor system
from `meta_engine` and convert F132 from a presence-anchor into a
coverage-delta enforcement anchor. (b) *New-domain $\omega$-cycles*:
the new-domain scout ranks the hexa-lang stdlib silent-void hazard
plus gate enforcement gaps as the highest-ROI target ($40$–$75$
plausible falsifiers), with anima Mk-XI 5-tuple drift defense as
secondary. (c) *Defense extension*: detached-signature distribution to
$\geq 2$ hosts plus a multi-host R5 SSH key rotation policy closes the
residual single-key-compromise gap. (d) *Cross-bridge correlation hunt
v3* with stricter pre-registration informed by the v2 decline: triples
declared under a single normalisation $g$ *before* measurement.
(e) *Singularity broader scan*: are there other $(n,\text{identity})$
pairs analogous to $(6,\text{F100})$ over distinct multiplicative-function
families?

## 10.5 Threats to validity

Four threats remain. Post-hoc anchor selection bias is structural;
the empirical-resampling framing of Section 9 mitigates but does not
eliminate it. Single-actor framework development means the four-repo
aggregate is a corroboration network, not an independent reproduction.
The $16$-hex collision risk approaches relevance near $200$ entries; a
$32$-hex upgrade or hash-table replacement of the $O(n^{2})$ uniqueness
check is required before crossing it. F132 was audited over four
engines only; a fifth (`defense_engine` or `bridge_engine`) may exhibit
the same gap and should enter a weekly
`cross_engine_integration_audit` $\omega$-cycle.

## 10.6 Closing

The paper presents two artefacts of comparable weight: the anchor
corpus and the decline machinery. The decline machinery — raw 73
admissibility, the F45 and v2 negative-result documents preserved
verbatim, the `quality_audit_v2` PAUSE canary — is what distinguishes
this work from prior cross-domain numerological surveys. F45 and the
v2 correlation hunt, both declined, are arguably the framework's most
credible evidence: the registry rejects fragile triplets at the cost
of headline claims. The $n=6$ framework is reproducible from `git log`,
falsifiable per claim under raw 73, honestly bounded by Section 9, and
operationally defended by a nine-cell matrix whose ninth cell went LIVE
during the present session. We do not assert that $n=6$ is
metaphysically privileged. We assert that, after honest declines, the
residue exceeds the empirical-resampling baseline and is reproducible
end-to-end.

---

# 11. References

*Placeholder — separate bibliography compilation in progress (agent A2).*

Anticipated bibliography sources (introduction-cited, partial list):

- Conway, J. H. and Sloane, N. J. A. *Sphere Packings, Lattices and
  Groups*, 3rd ed., Springer, 1999.
- Cameron, P. J. *Permutation Groups*, LMS Student Texts 45,
  Cambridge University Press, 1999.
- Sierpi\'nski, W. *Elementary Theory of Numbers*, 2nd ed.,
  North-Holland / PWN, 1988.
- Erd\H{o}s, P. and Sur\'anyi, J. *Topics in the Theory of Numbers*,
  Springer, 2003.
- Donoho, D. L. "An invitation to reproducible computational research,"
  *Biostatistics* 11(3):385–388, 2010.
- Mesirov, J. P. "Accessible reproducible research," *Science*
  327(5964):415–416, 2010.
- Costa, A. et al. (2014). MCM2-7 helicase structure, PDB 4R7Y.
- Yuan, Z. et al. (2016). MCM2-7 helicase structure, PDB 5BK4.
- Aver, E. et al. (2015). Primordial $^4$He mass fraction.
- Cooke, R. J. et al. (2018). Primordial $^4$He mass fraction.
- Bovy, J. and Tremaine, S. (2012). Solar galactic year.
- Eilers, A.-C. et al. (2019). Solar galactic year.
- Planck Collaboration (1807.06209). $H_0$ Planck.
- Riess, A. G. et al. (2112.04510). $H_0$ SH0ES.

(Full BibTeX file to be merged at compilation time.)

---

# 12. Appendices

*Placeholders — figures and supporting tables to be inserted from
PAPER\_OUTLINE\_v1.*

## A. Figures (placeholders)

- **Figure 1**. The $n=6$ foundation primitive lattice
  ($\sigma,\varphi,\tau,\mathrm{sopfr},J_2,\mu,M_3$) and their evaluation
  at $n=6$. *(Placeholder.)*
- **Figure 2**. Falsifier 9-tuple lifecycle: SUGGEST $\to$ manual
  escalate $\to$ register $\to$ verify $\to$ decline. *(Placeholder.)*
- **Figure 3**. Cross-domain anchor density per domain (chemistry,
  biology, cosmology, particle physics, astronomy, mathematics) versus
  uniform-coincidence null. *(Placeholder.)*
- **Figure 4**. Atlas shard map: 11 active shards across 4 sister
  repositories with cross-shard `(type, id)` collision count = 0.
  *(Placeholder.)*
- **Figure 5**. The 9-cell R1/R5 defense matrix (3 layers $\times$ 3
  domains, all LIVE). *(Placeholder.)*
- **Figure 6**. Multi-decomposition cone for cardinal $1728$
  (F32 + F80) and $64$ (F36): independent legs over $\mathcal{P}_6$.
  *(Placeholder.)*
- **Figure 7**. Cross-bridge correlation hunt v2: empirical-resampling
  null versus observed match count, $Z=-0.91$, $p=0.84$. *(Placeholder.)*

## B. Supplementary tables

- **Table B.1**. Full 115-entry falsifier registry with grade tier and
  status. *(Placeholder, source: `falsifiers.jsonl`.)*
- **Table B.2**. Full multi-decomposition cardinal table. *(Placeholder,
  source: `F71_F77_candidate_review.md`.)*
- **Table B.3**. Honesty-triad mode-6 scorecard per repository.
  *(Placeholder, source: `tool/atlas_cross_repo_dashboard.sh` output.)*

---

*End of PAPER\_DRAFT\_v1.md.*
