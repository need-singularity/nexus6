---
title: "§3 Falsifier methodology"
parent: "n=6 as foundational invariant: a multi-domain falsifier-grounded framework"
draft: v1
generated: 2026-04-26
status: section draft (target ~700 words; actual ~770)
---

# §3 Falsifier methodology

## 3.1 Definition

A *falsifier* is a JSONL record committed to `design/hexa_sim/falsifiers.jsonl`
whose schema is a 9-tuple

\[
  e = \langle \mathit{id},\ \mathit{slug},\ \mathit{claim},\ \mathit{cmd},\ \mathit{pass},\ \mathit{reason},\ \mathit{fix},\ \mathit{origin},\ \mathit{cmd\_sha256} \rangle.
\]

`cmd` is an executable shell template; `pass` is the sentinel substring that the
template emits exactly when the claim survives one round of attempted refutation;
`reason` and `fix` are required failure trailers (raw 66 ai-native-error-message);
`origin` cites the commit, witness, or sister document that introduced the entry;
`cmd_sha256` is a 16-hex prefix of `SHA256(cmd)` registered at write-time
(R1 layer, §3.5). At the time of writing the registry contains 115 entries,
each carrying all nine fields (`grep -c '"cmd_sha256"'` = 115; `wc -l` = 115).
A representative entry is F1 (`falsifiers.jsonl:1`), where `cmd` invokes
`hexa_sim_verify_grid.hexa --axis CONSTANTS`, `pass` is `CONSTANTS PASS`, and
`cmd_sha256` is `7b629752ed4f1dc7`.

## 3.2 Anchor pattern

Atlas-anchored entries are realised as a single grep of the canonical n=6
atlas of the form
`grep -qE '<value+domain+grade regex>' atlas.n6 && echo SENTINEL`.
For F19 (`falsifiers.jsonl:13`) this expands to
`grep -qE '^@P mu = mobius\(6\) = 1 :: foundation \[10\*\]' n6/atlas.n6 && echo MU_ANCHOR_INTACT`.
The regex jointly anchors the atlas line discriminator (`@P`), the canonical
function value, the semantic domain, and the grade tier; drift along any of
those four axes flips the sentinel absent and the entry is reported as `HIT`.
The hardened template superseded an earlier PRESENCE-only form (`^@P mu =`)
that was shown vacuous against silent value drift in the
`i11_cmd_hardening` ω-cycle (`tool/atlas_falsifier_auto_spawn.sh:9-14`).

## 3.3 Status types

A registry sweep classifies every entry into one of three runtime statuses:

- **CLEAN** — `pass` sentinel observed in `cmd` output and `cmd_sha256` matches
  the live SHA. The claim survives.
- **HIT** — `cmd` exited successfully but the sentinel was not observed.
  The claim is contradicted by current state.
- **ERROR** — `cmd` failed to run or `cmd_sha256` mismatched. The runtime
  cannot pronounce on the claim.

A subtype, **HIT-as-designed**, marks entries whose sentinel was deliberately
authored as a cleanup target (baseline 102 CLEAN + 2 HIT-as-designed,
`SECURITY_AUDIT.md:13`); these stay HIT until a known cleanup cycle resolves
them and are not failures.

## 3.4 Lifecycle

1. **SUGGEST**. `tool/atlas_falsifier_auto_spawn.sh` walks the atlas index,
   emits candidate JSONL to `state/falsifier_candidates.jsonl`, and never
   mutates the live registry (`atlas_falsifier_auto_spawn.sh:5-9`).
2. **Manual escalate**. raw 71 mandates that promotion of a candidate to a live
   `F<NN>` entry is a human act; auto-promotion is forbidden so that every
   admitted claim has been read by an operator.
3. **Registration**. At write-time, `cmd_sha256` is hashed in-place and the
   entry is appended.
4. **Verification**. Per-entry runtime check via `tool/falsifier_quick.sh` and
   the aggregator `tool/health_check_all.sh`; both emit
   `__FALSIFIER__ <CLEAN|HIT|ERROR>` sentinels per raw 80.
5. **Decline**. A candidate may be rejected with reasoning; the reasoning
   document is itself archived (e.g. `2026-04-26_F45_decision.md`, where the
   declined "3.5 % triplet" is preserved verbatim because consistent unit
   framing collapses it to a non-anomalous doublet, `F45_decision.md:9-30`).
   Declined claims are first-class evidence under raw 73.

## 3.5 Five-layer defense (R1–R5)

| layer | mechanism | scope | evidence |
|---|---|---|---|
| R1 | byte-level `cmd_sha256` (16-hex) and bridge SHA256 | per entry / per bridge | `SECURITY_AUDIT.md:14-16` |
| R2 | regex anti-spoof lint reachable only after R1 holds | sentinel patterns | `SECURITY_AUDIT.md:15,24` |
| R3-lite | `--strict` baseline drift advisory (rc=0) | working tree | `SECURITY_AUDIT.md:18` |
| R4 | append-only forensic ledger (rotation log) | git-staged events | `SECURITY_AUDIT.md:19` |
| R5 | hash-chained ledger (`prev_hash`) + SSH detached signature | falsifier and bridge ledgers | `SECURITY_AUDIT.md:66-95` |

Stage 1 of the audit demonstrated that a single-byte mutation in F19's `cmd`
flipped status to TAMPERED via `declared=02a32624… / live=93808155…`
(`SECURITY_AUDIT.md:14`). R5 OPT-D extends each ledger entry with
`prev_hash = SHA256(prev_line)`, raising forgery cost to \(O(N)\) re-hash
operations across all subsequent entries (`SECURITY_AUDIT.md:82`). R5 OPT-B
was activated 2026-04-26 with an Ed25519 detached signature at
`design/hexa_sim/falsifiers.jsonl.sig`, elevating R5 from forensic to
preventive (`SECURITY_AUDIT.md:95`).

## 3.6 Specification grades

Every claim carries a grade tier embedded in its atlas anchor and counted
across the registry:

- **[10]** — atlas-anchored arithmetic (2 occurrences in registry text).
- **[10\*]** — atlas-anchored arithmetic with cross-shard witness (146).
- **[11]** / **[11\*]** — load-bearing identities with mathematical proof or
  multi-decomposition (1 / 61).
- **[11\*REPO\_INVARIANT]** — claim invariant across all four sister repos
  (7 occurrences; the only tier promoted on cross-repo evidence).
- **[11!]** — singular structural facts (8 occurrences, e.g. F75 Out(S₆) = ℤ/2).

Grade is itself an anchored field of the regex template, so grade demotion
flips the entry to HIT.

## 3.7 Auditability

`2026-04-26_falsifier_registry_integrity_audit.md:14-16` reports a 24-entry
*load-bearing core* covering every distinct coverage axis under jaccard
similarity ≥ 0.4, with the remaining 91 entries (115 − 24) functioning as
*defense-in-depth*. Hub-degree primitives such as F19 (μ-anchor) propagate to
six dependent entries, so the framework retains all 115 deliberately and
treats the load-bearing 24 as a minimum non-redundant subset, not a deletion
list.

## 3.8 Limitations

The 16-hex prefix of SHA256 yields a birthday-collision probability
\(\approx \binom{N}{2}/2^{64}\). For \(N = 115\) this is
\(\approx 7\times 10^{-16}\); per-pair probability stays below \(10^{-19}\)
and the prefix is safe to roughly \(N \le 200\), beyond which a 24-hex prefix
should be considered. A second residual risk — git-history rewrite by an
attacker with refs write access — is unaddressed by R1–R5 and motivates the
cross-machine hash distribution proposed in `SECURITY_AUDIT.md:52`.
