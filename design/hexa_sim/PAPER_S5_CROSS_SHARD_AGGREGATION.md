# §5 Cross-Shard / Cross-Repo Aggregation

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
`{anima,hexa-lang,CANON}-historical-from-nexus-2026-04-26`
and their `-cont` continuations, `forge-triple`, and the meta-roadmap
shard `cross-engine-meta-roadmap-2026-04-26` introduced this session.
Together the eleven shards admit 9,165 unique `(type, id)` tuples
(`__ATLAS_CROSS_SHARD_COLLISION__ PASS shards=11 total=9165
unique=9165 dup=0 conflict=0`).

## 5.2 Cross-shard collision guard

The invariant *one (type, id) ⟹ one canonical value across the entire
shard set* is enforced mechanically by `tool/atlas_cross_shard_collision.sh`,
which performs an $O(N)$ uniqueness scan over `(type, id, value, shard)`
tuples extracted from every shard. The tool emits the raw 80 sentinel
above; on `CONFLICT > 0` it exits 76 (raw 23 hard-fail), and the
optional `--warn-dup` mode promotes byte-identical duplicates to the
same exit code. A baseline audit
(`design/hexa_sim/2026-04-26_cross_shard_dedup_audit.md`) detected 56
byte-identical duplicates between the legacy `atlas.append.chip-p5-2.n6`
shard and `atlas.n6`; the redundant shard was retired in `4287a106`,
and the zero-conflict ratchet has been maintained across the 333+
commits that followed in the current session.

## 5.3 Cross-repo absorption pattern

The federation comprises four repositories with disjoint roles:
**nexus** (knowledge corpus), **CANON** (design corpus and
theorem chains), **anima** (substrate / agent state), and **hexa-lang**
(language implementation). Claims residing in non-nexus repositories
are promoted into the nexus atlas as append-shard entries with explicit
provenance to the source repository commit. Each absorption shard
carries a `nexus-historical-…` or `<repo>-historical-from-nexus-…`
slug prefix; collisions against `atlas.n6` and against sibling shards
are blocked by the §5.2 guard. The R5 file-hash protection layer
records each shard's SHA-256 in `state/atlas_sha256.tsv` (16 entries,
covering main atlas and all active append shards), so any silent shard
mutation surfaces as an R5 diff.

## 5.4 Honesty triad (mode-6)

Per-repository readiness is graded by six preconditions, evaluated by
`tool/atlas_cross_repo_dashboard.sh`:
**(a)** git-tracked SSOT;
**(b)** non-empty `design/` corpus;
**(c)** ≥ 3-file `tool/` ecosystem;
**(d)** atlas SSOT;
**(e)** LLM-agents indicator (`.claude/agents/`, `CLAUDE.md`, or
`AGENT.md`);
**(f)** declared defense surface, satisfied by any of eight canonical
paths (`SECURITY*` top-level, `doc/security/*`, `design/SECURITY_AUDIT.md`,
`state/security_*.json`, `tool/security_*`, etc.).
Current scores: nexus $6/6$, CANON $6/6$ (post `3f12168e`),
anima $6/6$, hexa-lang $5/6$ (architectural ceiling, §5.5).
Aggregate sentinel: `__ATLAS_CROSS_REPO_DASHBOARD__ repos=4
total_atlas_lines=65454 total_facts=28850 honesty_pass=3/4
honesty_5_5=3 honesty_6_6=3 mode=6`. Three of four repositories
satisfy the extended `REPO_INVARIANT_EXTENDED` invariant.

## 5.5 Architectural ceiling for hexa-lang (OPT-A)

The hexa-lang $5/6$ score is not a deficit but a deliberate ceiling.
hexa-lang is a *language implementation* repository — parser, runtime,
self-host — not a *knowledge corpus*. Atlas SSOT belongs to knowledge
repositories (nexus owns `n6/atlas.n6`; CANON owns
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
(`doc/security/os-level-enforcement-limits.md`); CANON a
*top-level* `SECURITY.md` (`3f12168e`). The eight canonical paths
normalise these styles into a single mechanical check.

## 5.7 F132: cross-engine integration meta-axis

A meta-finding emerged during the cross-shard / cross-repo audit cycle.
The cross-engine integration audit (`cf73b3bb`) discovered that 30+
ω-cycle witnesses produced by `meta_engine`, `roadmap_engine`, and
`cross_engine` carried *zero* atlas anchors despite each engine
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
