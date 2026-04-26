# §6 Mathematical Singularity

The cross-domain anchors of §4 establish $n=6$ as a recurrent
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
Sloane, *Sphere Packings, Lattices and Groups*, §10, and Cameron,
*Permutation Groups* (1996), §6.4. The exception originates in the
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
uniqueness follows from a Möbius-inversion argument recorded in the
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

Cross-domain anchors (§4) are pattern-witnesses; they do not derive
$n=6$. F75 and F100 are by contrast *predictive*: any competing
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