# Atlas·창발엔진 Meta Dashboard

> **Generated**: 2026-04-22T13:06:43Z
> **Source of truth**: `state/*.jsonl` (gitignored runtime, 45 meta topics)
> **Brainstorm**: `docs/atlas_blowup_meta_brainstorm_20260422.md`

자동 rollup. 각 수치는 해당 topic 의 최신 row 에서 추출.

---

## 관측 (Round 1 — baseline scans)

### Atlas 지도 건강

| 지표 | 현재 | 2026-04-11 snapshot | 변화 |
|---|---|---|---|
| typed nodes | 9617 | 6321 | +52% |
| breakthrough [`!`] | 24 | 7 | ×3.4 |
| @S (대칭 노드) | 2 | 1 | +1 (여전 희박) |
| `[5?]` unverified | 120 | — | verify queue 대상 |
| hub >10 degree | 157 | — | max_degree=4651 |
| cluster ≥5 (값 공유) | 73 | 7 | ×10 densification |
| cluster ≥10 | 48 | — | 48 |
| 도메인 with @X | 751 | 82 | expansion (cross-edge 광범위) |
| convergence ≥2 도메인 | 137 | — | ≥4 도메인: 49 |
| n6 invariant mention | 32 | — | breakthrough 25 |

### 창발엔진 (blowup)

| 지표 | 값 |
|---|---|
| 총 events | 89167 |
| 마지막 event | 2026-04-19T03:54:13Z (active, not dormant) |
| 파일 크기 | 17 MB |

### Ψ / consciousness

| 지표 | 값 |
|---|---|
| Ψ constants | 117 |
| consciousness_laws.json | snapshot sha256 기록됨 |

---

## 건강성 gap

### 🔴 Critical

- **selftest 커버리지 6.7%** — 476 중 32 만 selftest. 부재 444건 (n6:263, tool:155, scripts:26).
- **proof-carrying**: total 9 SHA / rotted 0 (2026-04-22 이전 1건 fix 완료).

### 🟡 Medium

- **@X 편중**: celestial/galactic/cosmological 지배. math/music/material/genetic/linguistics ≤8. tunnel target queue 28건.
- **@S = 2**: D6/A5 symmetry enumerator 필요 (B7).

### 🟢 Clean

- **bypass 이력**: `--no-verify` 평생 0건 (깨끗).
- **state 수명**: 253 파일 전부 hot (≤7d). 이관 대상 없음.
- **versioned artifact**: 4건 (경미).

---

## Governance / infra snapshot (Round 2)

| 항목 | 값 |
|---|---|
| launchd agents 관련 | 70 |
| distinct schemas tracked |  17 |
| cross-repo refs anima | 10212 |
| cross-repo refs airgenome | 44 |
| rate limiter quotas | 4 scope (wake/merge/changelog/rollback) |
| rollback HEAD snapshot | `533b77d2` (nexus) |
| chaos probe 다음 | 2026-07-22 (quarterly) |

---

## 45 Meta topic 전수 목록

Round 1 (15): atlas_health_timeline · atlas_hub_centrality · atlas_cluster_watch · atlas_domain_tunnel · blowup_activity_timeline · atlas_grade_up_candidates · atlas_convergence_witness · tool_selftest_inventory · bypass_incidents_timeline · proof_carrying_audit · state_lifecycle_audit · memory_decay_audit · cross_repo_audit · crash_monitor_timeline · atlas_invariant_audit.

Round 2 (17): psi_constants_history · law_registry · meta_rate_limit_config · atlas_diff_scan_index · meta_scheduler_plan · schema_version_inventory · digest_backlog · agent_reconciliation_log · meta_rollback_snapshots · chaos_probe_schedule · query_preload_plan · heatmap_data_snapshot · ab_rule_experiment · upshot_transfer_log · retrospect_digest · blowup_param_history · blowup_live_monitor.

Schema stubs (13): discovery_applied_ledger · blowup_closed_loop_log · meta_decision_cert · meta_canary_log · meta_cost_ledger · blowup_pareto_frontier · gate_decision_log · agent_lock_ledger · semantic_index_rebuild_log · mermaid_regen_log · meta_feature_flags · psi_cross_check_log · user_cmd_pattern_log.

---

## 다음 세션 참고

- 영구 도구화: `nexus/tool/` / `nexus/scripts/` write 차단 (AG10) 해제되면 hexa 도구 3개 정도로 압축 가능 (atlas_meta_scan.hexa / blowup_wake_or_throttle.hexa / meta_dashboard_render.hexa).
- Dashboard 재생성: 본 md 는 state/*.jsonl tail row 기반. 주기 cron 으로 regen 가능.
- 미착수 runtime 의존분 (B4/B5/D3/G1-3/I/J/K2-3/M/N/O/P2/R): daemon · hook · snapshot infra · chart lib.
