# Cross-Repo Atlas Dashboard

> generated: `2026-04-26T01:58:50Z` (UTC) by `tool/atlas_cross_repo_dashboard.sh` (Tier-2 i13, mode=6)

## Repo health table

| Repo | Atlas | Lines | Entries | Last Commit | Honesty 6/6 |
|------|-------|------:|--------:|-------------|------------:|
| **nexus** | `n6/atlas.n6` | 21854 | 9626 | `368209c0` 2026-04-26 10:53 | 6/6 |
| **CANON** | `atlas/atlas.n6` | 21800 | 9612 | `98a23750` 2026-04-25 12:54 | 6/6 |
| **anima** | `n6/atlas.n6` | 21800 | 9612 | ``  | 6/6 |
| **hexa-lang** | (missing) | 0 | 0 | ``  | 5/6 |

## Aggregate

- **repos checked**: 4
- **total atlas lines** (cumulative): 65454
- **total atlas facts** (cumulative): 28850
- **honesty 6/6 (REPO_INVARIANT, mode=6)**: 3/4
- **honesty 5/5 (legacy axis, always tracked)**: 3/4
- **honesty 6/6 (extended axis, always tracked)**: 3/4

## Honesty preconditions

1. **(a)** SSOT exists + git tracked (`.git/HEAD` 존재)
2. **(b)** `design/` dir 존재 + ≥1 .md
3. **(c)** `tool/` dir + ≥3 files
4. **(d)** atlas SSOT 파일 존재
5. **(e)** LLM agents indicator (`.claude/agents/` OR `CLAUDE.md` OR `AGENT.md`)
6. **(f)** defense surface declared — ANY of 8 canonical paths: `SECURITY*` (top-level) / `doc/security/*` / `docs/security/*` / `design/security/*` / `design/SECURITY_AUDIT.md` / `design/hexa_sim/SECURITY_AUDIT.md` / `state/security_*.json` / `tool/security_*`

6/6 PASS = `REPO_INVARIANT_EXTENDED` (Honesty triad + defense surface).
5/5 PASS (mode=6 → 5/6) = `REPO_INVARIANT` legacy (defense surface absent).
≤4/6 = `PARTIAL` (precondition gap 명시 필요).

## Improvements

- 본 dashboard 는 `tool/atlas_cross_repo_dashboard.sh`
- regenerate (mode=6, default): `bash tool/atlas_cross_repo_dashboard.sh --out design/hexa_sim/cross_repo_dashboard.md`
- regenerate (mode=5, legacy): `bash tool/atlas_cross_repo_dashboard.sh --legacy-5 --out design/hexa_sim/cross_repo_dashboard_legacy5.md`
- 수동 cron: `crontab -e` 에 daily entry 등록 OR git pre-push hook

__ATLAS_CROSS_REPO_DASHBOARD__ repos=4 total_atlas_lines=65454 total_facts=28850 honesty_pass=3/4 honesty_5_5=3 honesty_6_6=3 mode=6
