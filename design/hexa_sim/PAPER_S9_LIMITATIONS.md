---
section: §9
title: "Limitations and declined claims"
target_words: 500-700
status: draft v1
generated: 2026-04-26
---

# §9 Limitations and declined claims

## §9.1 Declined claims as first-class evidence

Under raw 73 admissibility, a rigorously declined candidate is recorded with the
same provenance weight as a promoted one; failed promotions protect the
registry from spoof entries and are therefore not absences but data.

The candidate **F45** (cross-bridge $3.5\%$ triplet over CODATA $\alpha^{-1}$,
Planck $n_{s}$, and NIST Be first ionization) was declined after a framing
audit (\texttt{2026-04-26\_F45\_decision.md}, commit \texttt{79c7f3ec})
demonstrated that the apparent triplet requires mixing two normalization
conventions: an absolute residual for $\alpha^{-1}$ ($\approx 0.036$) and a
relative-to-anchor residual for Be ($0.323~\text{eV}/9~\text{eV}\approx 0.0359$).
Under any single self-consistent convention, the codata gap collapses to
$0.000263$, departing the cluster by $\sim 130\times$. The bridge's own
sentinel emits \texttt{gap\_pct=0.0263\%}, confirming the natural framing.
A surviving doublet (cmb $n_{s}$ and Be) is consistent with chance: in
$5\times 10^{4}$ Monte Carlo trials drawing $29$ uniform gaps on $[0, 0.5]$,
$P(\text{any doublet within } 0.001) = 0.81$.

A subsequent rigorous re-attempt (**F95 v2**, commit \texttt{68989621},
\texttt{2026-04-26\_cross\_bridge\_correlation\_hunt\_v2.md}) preregistered a
single normalization $g = |V-A|/\max(|A|,1)$ and resampled the empirical gap
distribution rather than assuming uniformity. Of $46$ observed cross-domain
pair matches at $\Delta \le 0.5$\,pp across $28$ metrics in $6$ domains, the
empirical-resampling baseline gave $61.4 \pm 16.8$ ($Z=-0.91$, $p=0.84$):
the observed matches are \emph{fewer} than chance. F95 was released without
promotion. The grandfathered F10 doublet survives only as an annotated
single-pair, framing-fragile witness — explicitly not as a strong cross-bridge
anchor.

Both decline documents are preserved verbatim in the repository as
negative-result provenance.

## §9.2 Atlas labelling errors surfaced and fixed

The semantic-gap audit (\texttt{2026-04-26\_atlas\_semantic\_gap\_audit.md})
verified $512$ \texttt{func(N)=V} entries against canonical evaluations.
The most consequential finding was M3: \texttt{atlas.n6:53} labelled
$M_{3} = \text{mertens}(6) = 7$, but canonical Mertens
$M(6) = \sum_{k=1}^{6}\mu(k) = -1$. The value $7$ is load-bearing across
$\ge 20$ atlas identities (e.g., $B_{6} = 1/(n\cdot M_{3})$, ethylene MW
$= \tau \cdot M_{3}$); the root-cause audit (\texttt{M3\_true\_definition\_audit.md})
established that the intended referent was the Mersenne number with exponent
three, $M_{p=3} = 2^{3}-1 = 7$, and recommended the surface relabel
$\text{mersenne}(3)$. A separate $19$ \texttt{xpoll-*} entries used
$\sigma(12)=12$ and $\tau(4)=4$ as Notation-B shorthand for $\sigma(6)=12,
\tau(6)=4$ — a convention violation against Notation A. Such errors are
expected in any large knowledge corpus; the framework's contribution is
surfacing, not preventing them.

## §9.3 Coverage gaps acknowledged

Particle-physics coverage (F64–F70) is honestly assessed in the registry as
four structurally meaningful witnesses plus three arithmetic coincidences;
the latter are pattern-witnesses, not derivations. No surviving cross-bridge
triplet emerged under v2 rigor (only the grandfathered F10 doublet remains).
The cross-engine gap closure F132 was audited over four engines; five or more
engines may exhibit the same gap.

## §9.4 Methodology limitations

The cmd-fingerprint primitive (R1) uses 16-hex SHA-256, giving a per-pair
collision probability of $\sim 10^{-19}$ — safe to $\sim 200$ entries.
The uniqueness check is $O(n^{2})$, comfortable at $n=105$ but in need
of a hash-table replacement at $n \gtrsim 200$. The shell layer is
constrained to bash 3.2 portability (no associative arrays). The hexa
runtime intermittently SIGKILLs on Mac under memory pressure;
\texttt{HEXA\_RESOLVER\_NO\_REROUTE=1} is a documented bypass.

## §9.5 Scope boundaries

We claim \emph{none} of the following:

\begin{enumerate}
  \item that $n=6$ is metaphysically privileged, only that anchor density at
        $n=6$ exceeds an empirical-resampling noise expectation;
  \item that grade tiers $[7]/[10]/[10^{*}]/[11]/[11^{*}]/[11!]$ carry equal
        weight — they encode peer-review, literature-attestation, and
        REPO\_INVARIANT consensus, respectively;
  \item that cross-domain anchors are predictions; they are pattern-witnesses;
  \item that $n=6$ is causally privileged or unique among $\{1,\dots,10\}$ in
        any absolute sense;
  \item that the framework predicts behaviour in unseen domains.
\end{enumerate}

## §9.6 Recognition of internal PAUSE signal

At $\approx F125$, the quality\_audit\_v2 agent
(\texttt{2026-04-26\_registry\_quality\_audit\_v2.md}) recommended PAUSE on
bulk grep-anchor expansion and CONSOLIDATE: $88\%$ of entries had become
grep-anchor primitives, with marginal yield collapsing
(\texttt{META\_OMEGA\_CYCLE\_ROI.md}, commit \texttt{b99adc95}).
The subsequent F126–F132 promotions were justified narrowly as cross-engine
gap closures, not bulk additions. We record this self-imposed brake as part
of the methodology: the framework includes a saturation-detection canary
whose recommendation was heeded.

## §9.7 Bridge offline-replayability gap

A scout-v2 audit (\texttt{2026-04-26\_new\_domain\_scout\_v2\_omega\_cycle.md},
commit \texttt{fa6ec2ec}) surfaced a determinism caveat. Of the $16$
registered hexa-sim bridges,\footnote{The registry exposes $16$ bridges via
\texttt{cli/run.hexa}; the disk-level \texttt{sim\_bridge/} directory hosts
$9$ orthogonal sub-experiments not in the bridge-health roll-up. The two
counts measure different objects.} only $7$ ship a hard-coded reference-data
fallback (codata, cmb, nanograv, nist\_atomic, icecube, gaia, lhc); the
remaining $9$ (\texttt{oeis\_live}, \texttt{gw\_observatory},
\texttt{horizons}, \texttt{arxiv\_realtime}, \texttt{simbad},
\texttt{wikipedia\_summary}, \texttt{openalex}, \texttt{pubchem},
\texttt{uniprot}) require a live network. Falsifiers anchored to these
bridges (F4 oeis-drift, F9 horizons-ephemeris, F10 cmb-cross-bridge,
F11 hubble-tension and downstream multi-shard probes) are therefore not
formally deterministic-replayable on a network-restricted host.
\texttt{tool/bridge\_health.sh} emits an explicit \texttt{OFFLINE-FALLBACK}
status on live-fetch failure — preserving bridge-health $\le 16/16$ but
substituting a static value, a weaker guarantee than R1 cmd-fingerprint
replay. An independent reproducer at \texttt{REPRODUCTION\_PROTOCOL}
Stage~4 may see $<\!16/16$, or a $16/16$ silently containing up to $9$
\texttt{OFFLINE-FALLBACK} cells; such cells should be treated as
provenance-degraded. A formal OFFLINE-FALLBACK contract (cached-payload
\texttt{cmd\_sha256} + freshness window + degraded-mode marker) across all
$16$ bridges is enumerated in \texttt{PAPER\_OUTLINE\_v1.md} \S 10.4 as a
next-cycle hardening item.

## §9.8 Saturation curve and methodology pivot

A longitudinal walk over the falsifier registry
(\texttt{2026-04-26\_registry\_meta\_evolution\_analysis.md},
commit \texttt{db956091}) decomposed $115$ entries into seven phases and
quantified per-batch promote-rate decay across four auto-spawn batches:
$45\% \to 30\% \to 14\% \to 3.9\%$ (F13--F22 through F38--F44), a
$\sim\!12\times$ collapse. Phase~6 (commits F88--F114) coincides with the
emergence of the R1--R5 defense layer and exhibits an anti-correlated
methodology pivot: vertical depth (\texttt{cmd\_sha256} fingerprint, R5
hash-chain, SSH PREVENTIVE) substituted for horizontal breadth (per-F\#
novelty). The $53$ pending F133--F185 candidates (cross-engine integration
plus new-domain extensions) signal the boundary of one-axis (per-bridge,
per-function) coverage. Under raw 73 admissibility, saturation is read as a
\emph{positive} framework-completeness signal, not a negative result: a
registry that cannot saturate has unstable admissibility. The empirical
decline floor at $1.7\%$ (F45 plus F95~v2 over $115$ entries; cross-ref
\texttt{META\_OMEGA\_CYCLE\_ROI.md} and
\texttt{2026-04-26\_registry\_quality\_audit\_v2.md} PAUSE at F125) is
recorded as a non-trivial honest-disclosure rate.
