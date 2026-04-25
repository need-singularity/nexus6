# hexa-lang atlas-SSOT — decision

> Date: 2026-04-26
> Context: 4-repo Honesty triad ω-cycle — hexa-lang scores 4/5 (missing precondition (d) atlas SSOT).
> Sibling triad doc: `~/core/nexus/design/honesty_triad.md`

## 1. Structural claim

hexa-lang is a **language implementation** repo (parser, self-host, runtime), not a **knowledge corpus** repo. The 4-repo Honesty triad has a clean role split:

| Role | Repo | SSOT file |
|------|------|-----------|
| knowledge corpus (atlas) | nexus | `~/core/nexus/n6/atlas.n6` (1.5 MB, verified) |
| cross-repo raw rules | hive | `~/core/hive/.raw` (1653 lines, verified) |
| language L0 rules (parser-owner) | hexa-lang | `~/core/hexa-lang/.raw` (30 lines, scoped to self-host) |
| design corpus | n6-architecture | (this repo) |
| meta agents | anima | (this repo) |

Refinement vs the original premise: hexa-lang **does** carry a `.raw` of its own — but it is a 30-line L0 parser-owner SSOT scoped to self-host invariants, not a cross-repo rule corpus. The knowledge-corpus role (atlas) genuinely has no place in a language repo.

Verified non-atlas finding: `~/core/hexa-lang/tool/atlas_append_check.hexa` is a *guard tool* (raw#23 schema-guard-mandatory enforcer for external atlas appends). It is consumer-side tooling, not an atlas SSOT. No `atlas.*` data file exists under hexa-lang.

## 2. Options

- **OPT-A** — Accept hexa-lang 4/5 as architectural-correct. No atlas in language repo. 4/5 is the ceiling given the role split.
- **OPT-B** — Add minimal atlas to hexa-lang containing language invariants (stage tokens retired, interp dispatch only, grammar rules). Duplicates content already encoded in `.raw` + `tool/`.
- **OPT-C** — Symlink/mirror nexus atlas subset into hexa-lang. Couples the language repo to nexus knowledge churn; violates role separation.

## 3. Decision: **OPT-A** (accept 4/5 as ceiling)

Rationale: 4/5 here is the **strongest possible** score, not a deficit. Adding an atlas to a language repo would either (a) duplicate the existing `.raw` L0 spec and create dual-SSOT drift risk, or (b) import nexus knowledge churn into a parser repo, violating the role separation that makes the triad legible. Both OPT-B and OPT-C inflate the metric while degrading the architecture. The honest move is to mark precondition (d) as **N/A by role** for hexa-lang and report 4/4 effective.

Confirms user intuition.

## 4. Verification commands

```bash
# Confirm no atlas SSOT data file in hexa-lang
find ~/core/hexa-lang -maxdepth 4 \( -name 'atlas.*' -o -name 'atlas' \) -type f
# Expect: empty

# Confirm hive owns cross-repo raw rules SSOT
ls -la ~/core/hive/.raw && wc -l ~/core/hive/.raw
# Expect: ~1653 lines, single file

# Confirm nexus owns atlas knowledge corpus SSOT
ls -la ~/core/nexus/n6/atlas.n6
# Expect: present, ~1.5 MB

# Confirm hexa-lang's .raw is L0/self-host scoped (not cross-repo)
head -5 ~/core/hexa-lang/.raw
# Expect: comment header naming "L0 universal rules (parser-owner self-host)"

# Confirm atlas_append_check is a guard tool, not an SSOT
head -10 ~/core/hexa-lang/tool/atlas_append_check.hexa
# Expect: comment naming raw#23 schema-guard-mandatory enforcer
```

## 5. Score restatement

| repo | a git-SSOT | b design corpus | c tool ecosystem | d atlas SSOT | e LLM agents | score |
|------|-----------|-----------------|-------------------|--------------|--------------|-------|
| nexus | yes | yes | yes | yes (atlas.n6) | yes | 5/5 |
| n6-architecture | yes | yes | yes | yes | yes | 5/5 |
| anima | yes | yes | yes | yes | yes | 5/5 |
| hexa-lang | yes | yes | yes | **N/A by role** | yes | **4/4 effective** |

Effective Honesty triad: 4 repos, all at ceiling for their role.

## 6. Cross-references

- Sibling doc updated this cycle: `~/core/nexus/design/honesty_triad.md` (§ hexa-lang exception, appended per raw 77 audit-append-only).
- ω-cycle parent: `~/core/nexus/design/hexa_sim/2026-04-26_*_omega_cycle.json` series.
