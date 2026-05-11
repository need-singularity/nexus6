# Nexus Honesty Triad

> Deployed 2026-04-25 from CANON audit at:
> `~/core/canon/reports/sessions/omega-audit-nexus-honesty-triad-portability-2026-04-25.md`

## Three constraints

### (1) Promotion-counter banner
At session start, record `nxs_promotion_count: <N0>` (read from `state/proposals/inventory.json` length or [10*] count). At session end, assert `nxs_promotion_count: <N1> unchanged` (i.e., N1 == N0) UNLESS explicit promotion via atlas-agent occurred. The banner is a first-line filter against premature promotion.

Form: `nxs_promotion_count: N/N0 unchanged` in session report front-matter (analogous to n6's `millennium_resolved: 0/7 unchanged`).

### (2) Write-barrier
Session/research agents must NOT modify these paths:
- `~/core/nexus/n6/atlas.blowup.jsonl`
- `~/core/nexus/state/proposals/inventory.json`
- `~/core/nexus/state/atlas_health_timeline.jsonl`
- `~/core/nexus/state/agent_lock_ledger.jsonl`
- `~/core/nexus/lenses/omega_state_space_lens.hexa`
- `~/core/nexus/CLAUDE.md` (when active) and `~/core/nexus/project-claude/nexus.md`

Explicitly NOT in barrier (mutable session output):
- `state/` other than the listed files
- `tool/nxs_002_composite.py` (tool patches require this)
- `design/` (research notes)
- `reports/` (when created — currently absent)

Privileged-path-only: atlas-agent / growth-agent. Other agents must use proposal-inbox or inventory-add tooling.

### (3) No-fabrication guard
- DO NOT FABRICATE numerical values, file paths, tool names, citations, or measurement results.
- When data/tool is missing, return UNKNOWN / INCONCLUSIVE / TIMEOUT with diagnostic.
- Verified by past near-violations NV-1 (cycle-43 self-disclosure 6772aede) and NV-2 (cycle 47-51 root-cause chain).

## Use in agent prompts

Each session-agent prompt should include this preset (3 lines):

```
- Honesty: nxs_promotion_count unchanged this session.
- Write-barrier: do NOT modify atlas/state/inventory paths listed in design/honesty_triad.md. Session reports only.
- No-fabrication: UNKNOWN/INCONCLUSIVE > invented values. If tool/data missing, stop with diagnostic.
```

## Audit lineage
This triad is verified by 3-of-3 KEEP_AS_IS audits in CANON (2026-04-25):
- `reports/sessions/omega-audit-constraint-honesty-counter-2026-04-25.md`
- `reports/sessions/omega-audit-constraint-write-barrier-2026-04-25.md`
- `reports/sessions/omega-audit-constraint-no-fabrication-2026-04-25.md`

Plus nexus-side cross-repo audit verified KEEP/KEEP_BUT_ADAPT verdicts at:
- `reports/sessions/omega-audit-nexus-honesty-triad-portability-2026-04-25.md`

## hexa-lang exception (appended 2026-04-26, raw 77 audit-append-only)

The 4-repo Honesty triad ω-cycle preconditions {a git-tracked SSOT, b design corpus, c tool ecosystem, d atlas SSOT, e LLM agents indicator} score nexus / CANON / anima at 5/5. hexa-lang scores **4/5**, missing only (d).

**Decision: accept 4/5 as architectural ceiling — precondition (d) is N/A by role for hexa-lang.**

Reason: hexa-lang is a language implementation repo (parser, self-host, runtime), not a knowledge corpus. The atlas role is owned by nexus (`~/core/nexus/n6/atlas.n6`); cross-repo raw rules are owned by hive (`~/core/hive/.raw`); hexa-lang owns only an L0 parser-owner self-host SSOT (`~/core/hexa-lang/.raw`, 30 lines). Adding an atlas to hexa-lang would duplicate the L0 .raw or import nexus knowledge churn — both degrade the role separation that makes the triad legible.

Effective triad: 4 repos all at ceiling for their role.

Full decision doc: `~/core/nexus/design/hexa_sim/hexa_lang_atlas_ssot_decision.md`
