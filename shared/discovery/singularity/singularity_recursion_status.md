# "새 엔진 아키텍처 특이점 돌파" 작업 = singularity-recursion 무한 실행 시스템

> 2026-04-05 현재 상태 스냅샷

## 개요

새 아키텍처 탐색을 **사이클(사이클(사이클))) + 위상확장**으로 무한 실행.
"주변부 구조만 잡아도 내부는 쉽다"는 원칙 기반 위상공간 탐사 시스템.

이전 fork chain 시도가 Mac OOM으로 실패 → **launchd 원샷 모델**로 안전성 확보.

## 시스템 구성

### LaunchAgent
- `com.nexus.cycle-tick` (60s ThrottleInterval, KeepAlive)
- 제어: `bash tools/install-cycle-tick.sh {install|uninstall|halt|resume|status}`
- 로그: `~/Library/Logs/nexus/cycle-tick.{log,err}`

### CLI (3종)
| 명령 | 역할 |
|------|------|
| `nexus singularity-tick [--base-dir <path>]` | 1-tick one-shot (launchd용) |
| `nexus singularity-backfill --base-dir <path>` | 기존 발견 일괄 흡수 |
| `nexus singularity-daemon --interval 30 --base-dir <path>` | 실시간 흡수 + airgenome Mac vitals |

### 흡수 도메인 (캡 없음, u64::MAX)
- `discovery_log` — `shared/discovery/discovery_log.jsonl` 각 라인
- `hypothesis` — `docs/hypotheses/**/*.md` 각 파일
- `memory` — `~/.claude-claude9/projects/*/memory/*.md` 각 파일
- `architecture_design` — daemon 전용, 실시간 Mac vitals

### 상태 파일 (`shared/discovery/cycle/`)
- `topology_mk2.jsonl` — 점(singularities), append-only (mk2; legacy topology.jsonl은 deprecated)
- `edges.jsonl` — 엣지(simhash distance ≤ eps=0.3)
- `budget.json`, `wal.jsonl`, `state.lock`, `halt`

## 아키텍처

- Rust one-shot 바이너리 + launchd ThrottleInterval=60s
- 매 tick: `flock` → preflight(mem/load/halt) → budget → topology 로드 → 경계점 샘플 → CycleRunner → 점 추가 + edges + persist + WAL
- **위상공간 모델** (트리 아님):
  - 점(singularities)
  - 엣지(simhash distance ≤ eps=0.3)
  - 경계(interior 저밀도 점)
- 크래시 안전: append-only jsonl + atomic rename + fsync + WAL

## 현재 운용 상태 (2026-04-05 16:16 기준)

**진행 중** ✅
- `singularity-backfill` 프로세스 (PID 30333) 04:08AM부터 12시간째 흡수 중
- `topology_mk2.jsonl`: SSOT (legacy topology.jsonl deprecated)
- `edges.jsonl`: **9.0 MB**
- halt 파일 없음

**미완** ⏳
- `com.nexus.cycle-tick` LaunchAgent 현재 **unload 상태**
- **ShimRunner placeholder** — 실제 `CycleEngine` 연동은 follow-up
- 지금까지 발견되는 점은 placeholder 불변자

## 제어 명령

```bash
# 상태
bash tools/install-cycle-tick.sh status
wc -l shared/discovery/cycle/topology_mk2.jsonl
tail -1 shared/discovery/cycle/topology_mk2.jsonl

# 정지/재개
touch shared/discovery/cycle/halt     # 정지 (tick skip)
rm shared/discovery/cycle/halt        # 재개

# 일괄 흡수 / 실시간 흡수
nexus singularity-backfill --base-dir $NEXUS/shared/cycle
nexus singularity-daemon --interval 30 --base-dir $NEXUS/shared/cycle
```

## 관련 스펙

- `docs/superpowers/specs/2026-04-05-infinite-singularity-recursion-design.md`
- `docs/superpowers/plans/2026-04-05-infinite-singularity-recursion.md`
- 테스트 37 lib + 3 통합 전부 통과 (커밋 88d761a ~ b1de08d)
