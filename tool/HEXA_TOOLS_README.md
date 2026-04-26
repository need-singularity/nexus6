# Hexa-only tool catalog (본 세션 12개)

> 사용자 "hexa로만 작성" 정책 (raw 9 hexa-only-suffix) 적용 후 본 세션에서
> 작성한 hexa-native 도구. self-host avoid 패턴 회피 — `.sh` 도구 의존 없이
> hexa runtime 안에서 직접 동작.
>
> 모두 ~100-150L bash 3.2 + python3 stdlib 없이 hexa runtime + shell `exec()` 만.

## Quick start

```bash
# 본 세션 ecosystem 1-line snapshot (12 metric 한 줄):
hexa run tool/session_overview.hexa --quiet

# 개별 도구 도움말:
HEXA_ARGV='--help' hexa run tool/<name>.hexa
```

모든 도구는 공통 `_argv()` helper 사용 — `HEXA_ARGV` env var로 args 전달.

## Tool index

| # | 도구 | 1줄 설명 | sentinel |
|---|------|----------|----------|
| 1 | `defense_smoke.hexa` | 5-layer (R1+R2+R3-lite+R4+R5) defense smoke | `__DEFENSE_SMOKE__ <PASS\|FAIL>` |
| 2 | `falsifier_quick.hexa` | registry id/grade/type lookup | `__FALSIFIER_QUICK__` |
| 3 | `pending_actions.hexa` | 5 user-go items status | `__PENDING_ACTIONS__` |
| 4 | `session_overview.hexa` | 11-tool sentinel 종합 패널 (자기 빼고) | `__SESSION_OVERVIEW__` |
| 5 | `falsifier_id_gaps.hexa` | F# slot gap 자동 식별 + provenance label | `__FALSIFIER_ID_GAPS__` |
| 6 | `bridge_quick.hexa` | bridge_sha256.tsv lookup + live SHA verify | `__BRIDGE_QUICK__` |
| 7 | `atlas_quick.hexa` | atlas_sha256.tsv lookup + live SHA verify | `__ATLAS_QUICK__` |
| 8 | `honesty_quick.hexa` | 4-repo Honesty mode-6 quick check | `__HONESTY_QUICK__` |
| 9 | `commit_stats.hexa` | git log session commit + LoC + category | `__COMMIT_STATS__` |
| 10 | `hexa_tool_inventory.hexa` | 자기-반사적 hexa 도구 카탈로그 | `__HEXA_TOOL_INVENTORY__` |
| 11 | `omega_cycle_count.hexa` | design/ ω-cycle witness 카운트 | `__OMEGA_CYCLE_COUNT__` |
| 12 | `uniqueness_check.hexa` | id/slug/cmd_sha256 중복 자동 감지 | `__UNIQUENESS_CHECK__` |

## Common patterns

**args parsing** (모든 도구 공통):
```hexa
fn _argv() -> array {
    let raw = to_string(exec("printf '%s' \"${HEXA_ARGV:-}\""))
    let parts = split(raw, " ")
    ...
}
```

**JSON whitespace-tolerant `_jget`** (`feedback_hexa_sim_falsifier_parser_quirks` 메모리 적용):
- `"key":"v"` (compact) + `"key": "v"` (python json.dumps) 둘 다 매치

**`--quiet` mode**: `exec 3>&1 1>/dev/null` 트릭으로 stdout suppress + sentinel만 fd 3로 emit.
일부 도구만 적용 (status_all 패턴; 신규 도구는 점진 적용).

**TSV parsing**: `#` prefix line skip + blank skip. column header도 별도 skip 필요한 case (atlas_quick).

## Composition

`session_overview.hexa`는 11개 도구 sentinel을 한 번에 호출하여 종합:

```
__SESSION_OVERVIEW__ <PASS|WARN|FAIL>
  defense=<PASS|FAIL>
  falsifiers=<N>
  bridges=<N>/<T>_tampered
  atlas=<N>/<T>_tampered
  honesty=<5_5>/<6_6>
  pending_ready=<R>/<C>
  next_f=F<N>
  commits=<N>
  hexa_tools=<N>
  omegas=<N>
  unique=<PASS|FAIL>
```

매 commit 후 1-cmd 전체 ecosystem health 확인 가능.

## raw compliance

모든 도구가 raw 9/71/73/80 준수:
- **raw 9** hexa-only-suffix: `.hexa` 확장자 + `// @tool(slug=..., desc=...)` annotation
- **raw 71** report-only: 자동 mutation 없음 (registry_sign / sha256_rotate 같은 1st-class operation 도구 외)
- **raw 73** admissibility: 각 도구 NON-TRIVIAL 검사 (단일 file_exists 같은 trivial check 회피)
- **raw 80** sentinel: stdout 마지막 1라인 `__NAME__ <STATUS> key=val ...` 형식

## 활용 시나리오

- **매 commit 후**: `hexa run tool/session_overview.hexa --quiet` → 1라인 health
- **registry 변경 시**: `hexa run tool/uniqueness_check.hexa` (collision 자동 감지)
- **F# 추가 시**: `hexa run tool/falsifier_id_gaps.hexa` (next-available 확인)
- **사용자 결정 필요 시**: `hexa run tool/pending_actions.hexa` (5 user-go items)
- **cross-repo health**: `hexa run tool/honesty_quick.hexa` (mode-6)
- **본 세션 통계**: `hexa run tool/commit_stats.hexa` (LoC delta + category)

## Bash counterparts

본 세션 hexa-only 정책 이전 작성한 .sh 도구 (self-host avoid 패턴 시기):
- `falsifier_health.sh` / `falsifier_health_parallel.sh`
- `bridge_health.sh` / `bridge_health_parallel.sh`
- `atlas_health.sh` / `atlas_sha256_rotate.sh` / `bridge_sha256_rotate.sh`
- `ledger_verify.sh` / `registry_sign.sh`
- `atlas_status_all.sh` / `health_check_all.sh` / `timeline_rotate.sh`
- `atlas_witness_registry.sh` / `atlas_cross_repo_dashboard.sh`
- `atlas_index.sh` / `atlas_search.sh` / `atlas_falsifier_auto_spawn.sh`

이들은 hexa runtime down 시 fallback. 정책 변경 후 신규 도구는 `.hexa` 우선.

## See also

- `design/hexa_sim/README.md` — corpus navigation
- `design/hexa_sim/INDEX.md` — full file inventory (auto-gen via `hexa_sim_index_gen.sh`)
- `design/hexa_sim/SECURITY_AUDIT.md` — defense system audit
- `design/hexa_sim/META_OMEGA_CYCLE_ROI.md` — session ROI analysis
- `design/hexa_sim/NEXT_SESSION_HANDOFF_v3.md` — 5 user-go pending items
