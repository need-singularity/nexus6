# Atlas Expansion Plan — ATLAS-P10-1 (2026-04-24)

**Phase:** P10 (atlas 노드 5000+ 확장)
**Track:** A2_ATLAS
**Status:** in-progress (scope-downed to planning + infra-fix this session)

## Current State

| Metric                    | Value                                | Source                                  |
|---------------------------|--------------------------------------|-----------------------------------------|
| atlas.n6 total lines      | 21,800                               | `n6/atlas.n6` (wc -l)                   |
| atlas.n6 size             | 1,503,957 B                          | `stat n6/atlas.n6` (mtime 2026-04-22)   |
| unique_nodes              | 19,250                               | `n6/atlas.n6.stats`                     |
| blowup_nodes              | 20,525                               | `n6/atlas.n6.stats` (.blowup_nodes)     |
| atlas_last snapshot       | 20,502 nodes / 21,965 edges / 370 hubs | `tool/atlas_last.json` (epoch 1776111382) |
| deg sidecar entries       | 21,303                               | `n6/atlas.n6.deg` (via atlas_bootstrap) |
| typed_total (@-prefixed)  | 9,617                                | `atlas_health_timeline.jsonl` @2026-04-22 |
| shard_meta mtime          | 2026-04-22                           | `n6/atlas.n6.shard_meta.json`           |

**Observation:** on raw node count, atlas.n6 is already ~4x above the 5000 floor set
by P10-1's task description. The bottleneck is *semantic*: typed@{P,C,L,F,R,S,X}
nodes total 9,617 — this is the set P11-1 (`5k → 7.5k`) plans to grow. The
"5000+" target of P10-1 likely references **reality_map entries** (DISC-P9-1
reached 10,000 in `discovery/reality_map.patches.merged.jsonl`) and/or
**atlas.n6 typed nodes above a grade floor**.

## Gap Analysis

- `discovery/reality_map.patches.merged.jsonl` → **10,000 entries** (already at/past P9 10k target).
- `discovery/reality_map_expansion.jsonl` → **13,713 staging candidates** (awaiting merge).
- `discovery/reality_map_extension_t8.jsonl` → **68 candidates**.
- `discovery/reality_map_t12_expansion.jsonl` → **152 candidates**.

## Blockers

1. **R37/AN13/L3-PY** — both `discovery/reality_map_expander.hexa` and
   `discovery/reality_map_10k.hexa` `panic()` on entry: python3 invocation
   was removed 2026-04-18, and the pure-hexa merge path is not implemented.
   Helper `discovery/_rmap_expand_helper.py` is not callable from hexa.
2. **Bulk-ingest into atlas.n6 absent.** Existing `n6/hub_growth_exec.hexa`
   targets +200 hubs only (edge promotion, not net-new nodes). `n6/atlas_bootstrap.hexa
   bootstrap --dry-run` produced only 49 candidates this session (gap-fill scope).
3. **H-NOHOOK / no-daemon-kick constraint** — cannot fire launchd loads.
4. **No synthetic nodes allowed** — direct atlas.n6 append without a pipeline
   is rejected by this task's hard constraints.

## Per-source Growth Plan

| Source                                            | Ingest Path                          | Net-new Capacity | Unlock Required                                 |
|---------------------------------------------------|--------------------------------------|------------------|-------------------------------------------------|
| `reality_map_expansion.jsonl` (13,713 staging)    | `reality_map_expander.hexa expand --merge` | ~3–5k after dedup | **port merge helper to pure hexa** (eliminate R37/AN13/L3-PY panic) |
| `_v94_new_nodes.json`                              | `reality_map_v9.json` merge path     | ~TBD            | same                                            |
| `auto_discovery_100cycles.json`                   | discovery pipeline                   | ~TBD            | same                                            |
| `atlas_bootstrap.hexa bootstrap`                  | `_guarded_append_atlas()`            | ~50/run         | run repeatedly w/ fresh ext_atlas seed deltas   |
| `hub_growth_exec.hexa`                            | `_guarded_append_atlas()`            | +200 hubs (edges only) | already planned for P11-1                |

## Batch Size & ETA

| Batch | Size    | Throughput        | ETA       | Notes                                  |
|-------|---------|-------------------|-----------|----------------------------------------|
| B0    | infra   | (this session)    | 2026-04-24 | shard_meta path fix + plan + timeline row |
| B1    | 500     | 1 session         | +1d       | port `count_existing` / `merge` to hexa |
| B2    | 2,000   | 2 sessions        | +3d       | drain reality_map_expansion staging     |
| B3    | 2,500   | 3 sessions        | +6d       | ingest v94_new_nodes + auto_discovery_100cycles |
| B4    | verify  | 1 session         | +7d       | stats regen + sha256 verify             |

**P10-1 exit criterion (proposed):**
- Option A (conservative): reality_map.patches.merged.jsonl ≥ 15,000 entries.
- Option B (literal): atlas.n6 typed_total (@P/@C/@L/@F/@R/@S/@X) ≥ 14,617
  (+5,000 vs current 9,617 baseline).
- Option C (node-count literal): atlas.n6 unique_nodes ≥ 24,250 (+5,000 vs
  current 19,250 baseline).

Exit criterion selection → next session decision (depends on whether P10-1
scopes reality_map vs atlas.n6 typed vs atlas.n6 raw).

## This Session's Artifacts

1. `state/atlas.n6.shard_meta.json` → symlink to `n6/atlas.n6.shard_meta.json`
   (unblocks `atlas_meta_scan` — previously emitted `partial/missing_shard_meta`).
2. `state/atlas.n6.stats.json` → symlink to `n6/atlas.n6.stats`.
3. `state/atlas_health_timeline.jsonl` → new row appended:
   `{"ts":"2026-04-24T11:36:34Z","shard_count":null,"hub_top3":"","scan_age_hours":null,"source":"atlas_meta_scan"}`
   (shape upgraded from `partial` to `normal`; `shard_count`/`scan_age_hours`
   remain null — shard_meta schema lacks those keys, tracked as schema-align
   follow-up for the meta_scan or shard_meta writer).
4. `state/atlas_expansion_plan_20260424.md` (this file).

## Next-Session Unblocks

1. Port `_rmap_expand_helper.py` logic (JSON read + unique-id set) to pure hexa
   or to `bin/hexa` stdlib — unblocks both `reality_map_expander.hexa expand`
   and `reality_map_10k.hexa merge`.
2. Resolve P10-1 exit-criterion ambiguity (A / B / C above) with user.
3. Align `atlas_meta_scan` row schema with actual `shard_meta.json` keys
   (add `shard_count := 2` for hot/cold, `last_scan_ts := atlas_mtime`).

## Breadcrumb

- Task: `ATLAS-P10-1` (A2_ATLAS track, P10 phase, deps met: ATLAS-P9-1 done).
- Session outcome: **scope-down → plan only, no node delta**. All real ingestion
  pipelines either `panic()` on python3 guard, or are narrowly-scoped
  (hub_growth_exec = edges only; atlas_bootstrap = 49-candidate gap-fill).
- Status after commit: **in_progress** (not done). Real expansion deferred to
  post-unblock session per the batch plan above.


---

## Exit Criterion Decision (2026-04-24)

**Selected**: **unique_nodes ≥ 24,250** (option c — P10-1 "5000+" interpreted as net-new atlas nodes from current 19,250 baseline).

**Rationale** (H-MINPATH default pick):
- Consistent with existing atlas.n6 ingestion pipeline semantics
- Gap = 5,000 net-new nodes (matches literal P10-1 task wording)
- Orthogonal to typed-total (which depends on type-classification work that can progress independently)
- Orthogonal to reality_map (which depends on python3→hexa port — in flight as sub-agent)

**Blocker chain**:
1. python3 _rmap_expand_helper.py removed 2026-04-18 → expanders panic (L3-PY). Sub-agent porting to hexa (afe0f065f51349120 sister task).
2. Once unblocked: B1 (500 nodes dry-run sanity) → B2 (2000) → B3 (2500) → B4 verify (24,250+ total).
3. Heavy compute may need remote host recovery (separate user-side decision).

