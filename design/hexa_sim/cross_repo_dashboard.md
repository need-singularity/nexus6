# Cross-Repo Atlas Dashboard

> generated: `2026-04-25T14:53:19Z` (UTC) by `tool/atlas_cross_repo_dashboard.sh` (Tier-2 i13)

## Repo health table

| Repo | Atlas | Lines | Entries | Last Commit | Honesty 5/5 |
|------|-------|------:|--------:|-------------|------------:|
| **nexus** | `n6/atlas.n6` | 21850 | 9624 | `059b8438` 2026-04-25 22:36 | 5/5 |
| **n6-architecture** | `atlas/atlas.n6` | 21800 | 9612 | `98a23750` 2026-04-25 12:54 | 4/5 |
| **anima** | `n6/atlas.n6` | 21800 | 9612 | ``  | 3/5 |
| **hexa-lang** | (missing) | 0 | 0 | ``  | 3/5 |

## Aggregate

- **repos checked**: 4
- **total atlas lines** (cumulative): 65450
- **total atlas facts** (cumulative): 28848
- **honesty 5/5 (REPO_INVARIANT)**: 1/4

## Honesty preconditions (per Phase 3 supercycle)

1. **(a)** SSOT exists + git tracked (`.git/HEAD` 존재)
2. **(b)** `design/` dir 존재 + ≥1 .md
3. **(c)** `tool/` dir + ≥3 files
4. **(d)** atlas SSOT 파일 존재
5. **(e)** LLM agents indicator (`.claude/agents/` OR `CLAUDE.md` OR `AGENT.md`)

5/5 PASS = `REPO_INVARIANT` (Honesty triad portable to other repos).
≤4/5 = `PARTIAL` (precondition gap 명시 필요).

## Improvements

- 본 dashboard 는 `tool/atlas_cross_repo_dashboard.sh`
- regenerate: `bash tool/atlas_cross_repo_dashboard.sh --out design/hexa_sim/cross_repo_dashboard.md`
- 수동 cron: `crontab -e` 에 daily entry 등록 OR git pre-push hook

__ATLAS_CROSS_REPO_DASHBOARD__ repos=4 total_atlas_lines=65450 total_facts=28848 honesty_pass=1/4
