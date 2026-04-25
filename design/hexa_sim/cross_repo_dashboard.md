# Cross-Repo Atlas Dashboard

> generated: `2026-04-26T08:30Z` (UTC) — Honesty-triad ω-cycle refresh + precondition (f) extension
> tool: `tool/atlas_cross_repo_dashboard.sh` (Tier-2 i13, mode=6 default; `--legacy-5` for prior axis)
> origin: `2026-04-26_honesty_triad_refresh_omega_cycle.json` + `2026-04-26_precondition_f_defense_surface_omega_cycle.json`

## Repo health table (ω-cycle re-run, mode=6 default)

| Repo | Atlas | Lines | Entries | Last Commit (atlas) | Honesty 6/6 | Δ vs prior 5/5 |
|------|-------|------:|--------:|---------------------|------------:|----------------|
| **nexus** | `n6/atlas.n6` | 21850 | 9624 | `d84a0601` 2026-04-26 01:09 | 6/6 | 5/5 → 6/6 (+1 via (f)) |
| **n6-architecture** | `atlas/atlas.n6` | 21800 | 9612 | `98a23750` 2026-04-25 12:54 | 5/6 | 5/5 → 5/6 (defense gap) |
| **anima** | `n6/atlas.n6` (symlink → n6-arch) | 21800 | 9612 | (symlink target) | 6/6 | 5/5 → 6/6 (+1 via (f)) |
| **hexa-lang** | (no atlas SSOT) | 0 | 0 | — | 5/6 | 4/5 → 5/6 (+1 via (f), still PARTIAL — OPT-A ceiling) |

**Aggregate (mode=6)**: repos=4, atlas_lines=65450, atlas_facts=28848, **honesty_6_6=2/4**, **honesty_5_5=3/4** (legacy axis, always tracked).

## 6-precondition × 4-repo matrix (direct verification)

| Precondition | nexus | n6-arch | anima | hexa-lang |
|--------------|:-----:|:-------:|:-----:|:---------:|
| (a) git-tracked SSOT | PASS (`.git/HEAD` + `n6/atlas.n6` ls-files) | PASS (`atlas/atlas.n6` ls-files) | PASS (`n6/atlas.n6` symlink ls-files) | PASS (`.git/HEAD`) |
| (b) design corpus (md ≥1) | PASS (design 61, docs 51, papers 10, reports 1) | PASS (docs 7, papers 176, reports 423) | PASS (docs 959) | PASS (docs 16) |
| (c) tool ecosystem (≥3 files) | PASS (tool 3662, scripts 77, bin 35) | PASS (tool 29, scripts 24, bin 3) | PASS (tool 337, scripts 69, bin 15) | PASS (tool 293, bin 7) |
| (d) atlas SSOT exists | PASS (`n6/atlas.n6` 21850 L) | PASS (`atlas/atlas.n6` 21800 L) | PASS (symlink → n6-arch 21800 L) | **FAIL** (none of `n6/atlas.n6`, `atlas/atlas.n6`, `atlas.n6`) |
| (e) LLM agents indicator | PASS (`.claude/agents/`) | PASS (`.claude/agents/`) | PASS (`CLAUDE.md`) | PASS (`.claude/agents/`) |
| (f) defense surface declared | PASS (`design/hexa_sim/SECURITY_AUDIT.md` + `tool/security_scan.hexa`) | **FAIL** (none of 8 canonical paths) | PASS (`state/security_roi_audit.json`) | PASS (`doc/security/os-level-enforcement-limits.md`) |
| **TOTAL** | **6/6** | **5/6** | **6/6** | **5/6** |

## Per-precondition: which repos satisfy

- (a) git-tracked SSOT: **all 4** (nexus, n6-arch, anima, hexa-lang)
- (b) design corpus: **all 4**
- (c) tool ecosystem: **all 4**
- (d) atlas SSOT: **3** (nexus, n6-arch, anima — anima via git-tracked symlink)
- (e) LLM agents indicator: **all 4**
- (f) defense surface declared: **3** (nexus, anima, hexa-lang — n6-arch only gap)

## Precondition (f) Defense Surface Declared

**Definition**: a repo PASSES (f) if ANY of 8 canonical defense-surface paths exists:

1. `<repo>/SECURITY*` (top-level — e.g. `SECURITY.md`, `SECURITY_AUDIT.md`)
2. `<repo>/doc/security/*` (any file)
3. `<repo>/docs/security/*` (any file)
4. `<repo>/design/security/*` (any file)
5. `<repo>/design/SECURITY_AUDIT.md`
6. `<repo>/design/hexa_sim/SECURITY_AUDIT.md` (nexus pattern)
7. `<repo>/state/security_*.json` (anima pattern)
8. `<repo>/tool/security_*` (nexus tool/security_scan.hexa pattern)

**Rationale**: After the 2026-04-26 honesty-triad refresh ω-cycle, `find -iname 'SECURITY*'` revealed each repo expresses defense differently — tool-shaped (nexus scanner), state-shaped (anima ROI audit), doc-shaped (hexa-lang enforcement-limits doc). A normalized 6th precondition gives the dashboard a security-readiness signal the original Honesty triad underweighted.

**raw 73 admissibility**: surveys 8 canonical paths across 6 conventions (top-level / doc / docs / design / state / tool) — non-trivial, no single-file shortcut.

**Per-repo (f) result**:

| Repo | Defense surface evidence | (f) verdict |
|------|--------------------------|:-----------:|
| nexus | `tool/security_scan.hexa` (Hexa scanner) + `design/hexa_sim/SECURITY_AUDIT.md` (recent commit) | PASS |
| n6-architecture | (none of 8 paths) | **FAIL** |
| anima | `state/security_roi_audit.json` (ROI-shaped audit state) | PASS |
| hexa-lang | `doc/security/os-level-enforcement-limits.md` (raw 66 enforcement-layer doc) | PASS |

**n6-architecture caveat (raw 71 + cross-repo write policy)**: the missing defense surface is **observed**, not **prescribed**. Cross-repo write to add a SECURITY.md in n6-architecture requires explicit approval — this dashboard surfaces the gap; remediation is a separate decision the user owns.

## Backward-compat: `--legacy-5` mode

For consumers that depend on the prior N/5 score (e.g. older sentinel parsers), `tool/atlas_cross_repo_dashboard.sh --legacy-5` preserves the original axis:

```
__ATLAS_CROSS_REPO_DASHBOARD__ repos=4 total_atlas_lines=65450 total_facts=28848 honesty_pass=3/4 honesty_5_5=3 honesty_6_6=2 mode=5
```

Both `honesty_5_5` and `honesty_6_6` fields are emitted in **both** modes — only `honesty_pass` and `mode` differ. raw 80 backward-compat: existing pipelines reading `honesty_pass` continue to work; new pipelines should read `honesty_6_6` (or both for transition).

## Dashboard-vs-reality drift

| Finding | Status |
|---------|--------|
| Dashboard repo health table accuracy | Accurate. All 4 PASS counts (mode=6: 6/6, 5/6, 6/6, 5/6) match direct verification. |
| Dashboard "Last Commit" blank for anima | Cosmetic gap (carried over). anima `n6/atlas.n6` is a symlink → `~/core/n6-architecture/atlas/atlas.n6`; `git log -- n6/atlas.n6` from inside anima returns empty because the symlink target is in another repo. The aggregate count is unaffected; only the display row is empty. |
| Dashboard precondition (a) check | Only checks `.git/HEAD` not actual git ls-files of the SSOT. All 4 happen to PASS direct ls-files verification anyway, so no false-positive emerges this cycle. Latent risk queued. |
| 24h activity since prior reading | nexus 246 commits, anima 146, n6-arch 29, hexa-lang 41 — high churn but no precondition flips beyond the new (f) extension. |
| New atlas in hexa-lang? | No. `find -name '*.n6' -maxdepth 3` returns 0 hits. OPT-A architectural ceiling holds. |

## hexa-lang ceiling reconfirm (OPT-A)

Per `design/hexa_sim/hexa_lang_atlas_ssot_decision.md`, OPT-A (no atlas SSOT in hexa-lang; toolchain repo by design) was selected as the architectural decision. Reconfirmed this cycle:

- 41 commits in last 24h, none introduced an atlas.n6 file at any candidate path
- `state/` directory contains telemetry JSONs (hx_*.json, convergence.jsonl, cross_repo_links.jsonl) but none are atlas-SSOT-shaped
- (f) defense surface PASS via `doc/security/os-level-enforcement-limits.md` lifts hexa-lang from 4/5 → 5/6 numerator-wise, but it remains **PARTIAL** by the (d) ceiling.

## Cross-repo defense-doc scan summary

| Repo | Defense artifact | Shape |
|------|------------------|-------|
| nexus | `design/hexa_sim/SECURITY_AUDIT.md` + `tool/security_scan.hexa` | doc + tool |
| n6-architecture | (none) | — |
| anima | `state/security_roi_audit.json` | state |
| hexa-lang | `doc/security/os-level-enforcement-limits.md` | doc |

3-of-4 repos satisfy (f) under the canonical-paths definition. n6-architecture is the unique gap — observed but not prescribed.

## Improvements / next ω-cycles

- (latent) Tighten precondition (a) in `tool/atlas_cross_repo_dashboard.sh` to also `git ls-files | grep -q <SSOT>` — prevents future false-positive when SSOT is on disk but un-tracked.
- (cosmetic) Dashboard "Last Commit" for symlink SSOTs: dereference symlink before `git log` so anima row shows the n6-arch target's commit.
- (extension done) ✓ Precondition (f) defense surface declared landed this cycle.
- (extension candidate) Optional 7th precondition (g) "atlas-tracked @F security_* facts" — could distinguish *declared* defense surface from *atlas-tracked* defense facts (deeper integration with Honesty triad's F-fact ontology).

---

__ATLAS_CROSS_REPO_DASHBOARD__ repos=4 total_atlas_lines=65450 total_facts=28848 honesty_pass=2/4 honesty_5_5=3 honesty_6_6=2 mode=6
