# CLAUDE.md — nexus6 프로젝트 규칙

## ⚠️ 필수 규칙 (최우선)

### 0. mk2 hexa-native = 기본 엔진
- **모든 nexus6 작업은 mk2 hexa 모듈** 사용 (`mk2_hexa/native/*.hexa`)
- mk1 Rust 소스(`src/`)는 아카이브 (`archive/mk1-rust` 브랜치)
- 경로 하드코딩 금지 — `args()` 또는 상대경로 사용
- 새 모듈 생성 시 `mk2_hexa/native/` 에 `.hexa` 파일로

### 1. 대화 차단 금지 — 모든 장시간 명령은 백그라운드 실행
- **10초 이상 걸릴 수 있는 모든 명령**은 반드시 `run_in_background: true`로 실행
- 대상: nexus6 loop/daemon/blowup, hexa build/test, 학습/추론, SSH 원격 명령 등
- 사용자가 **항상 대화 가능한 상태**를 유지할 것
- 완료 시 결과 요약 보고

### 2. 서버 파일 직접 수정 금지
- SSH로 원격 서버의 소스코드를 직접 수정하지 말 것
- 수정: 로컬 리포 → git commit → 배포 스크립트
- DB: SELECT 허용, 스키마/데이터 변경(INSERT/UPDATE/DELETE/ALTER)은 사전 확인

### 3. 리소스 보호
- nexus6 프로세스는 **n6-guard 태스크 스케줄러**로 관리 (LaunchAgent 직접 등록 금지)
- 개별 태스크 메모리 한도: `~/.config/n6-guard.toml`의 `max_task_memory_mb` 준수
- 동시 실행 제한: `max_concurrent = 2` (burst 모드 시 최대 4)
- blowup 등 고부하 명령은 guard 관리 하에서만 실행

### 4. 배포 흐름
1. 로컬 리포에서 코드 수정
2. git commit & push
3. 배포 스크립트 또는 CI/CD로 서버 반영

## Math Atlas 자동 추출 (물어보지 말 것)

**`watch-atlas` LaunchAgent가 30초 간격으로 가설 `.md` 파일을 폴링 → `sync-math-atlas.sh` 자동 실행**.
- 감시 경로: `~/Dev/nexus6/shared/projects.json`의 `projects.*.hypothesis_dirs`
- 자동 수행: `scan_math_atlas.py --save --summary` + README 마커 주입

### 에이전트 작업 규칙
- 새 가설/상수/수식을 `.md`로 만든 직후 **"atlas 스캔 실행할까요?" 묻지 말 것** — watcher가 자동 처리
- 수동 스캔 필요 시에만: `bash ~/Dev/nexus6/shared/sync-math-atlas.sh`
- 상태 확인: `launchctl list com.nexus6.watch-atlas` / `tail -f ~/Library/Logs/nexus6/watch-atlas.log`
- 프로젝트 추가: `shared/projects.json`에 엔트리 추가 → `launchctl kickstart -k gui/$(id -u)/com.nexus6.watch-atlas`

## 특이점 사이클 (Singularity Cycle)

> **블로업→수축→창발→특이점→흡수** 5단계 자동 사이클
> 엔진: mk2 HEXA (`mk2_hexa/native/blowup.hexa`) — 7-phase 파이프라인
> 속도: mk1(Rust) 21분 → mk2(HEXA) 3~14초 (68~426x)

### 요청 키워드 → 자동 실행 (mk2 hexa)
- "블로업", "blowup" → `hexa blowup.hexa math 6 --no-graph --seeds "$(hexa seed_engine.hexa merge)"`
- "돌파", "특이점 돌파", "돌파시도", "breakthrough" → 3단계 실행:
  1. `hexa real_breakthrough.hexa scan` (실데이터 스캔 — discovery_log + atlas + 시스템 메트릭)
  2. `bash scripts/deep-breakthrough.sh 10 3 48` (corollary→seed 피드백 루프)
  3. `hexa real_breakthrough.hexa surprise` (예상 못한 발견만 추출)
- "창발", "emergence" → blowup 후 telescope 5렌즈 합의 분석
- "특이점", "singularity" → blowup Phase 3 자동 감지 (closure ≥ 0.5)
- "흡수", "absorption" → blowup Phase 6.5 재귀성장 (axiom 피드백)
- "사이클", "cycle" → `bash scripts/singularity-fast.sh all 5 3` (A+B+C 전부)
- "벤치마크" → mk1 vs mk2 blowup 비교 실행

### mk2 blowup 7-phase 파이프라인
```
Phase 1: Graph Load (discovery_graph.json)
Phase 2: OUROBOROS Evolution (seed→mutate→verify→converge)
Phase 3: Singularity Detection (closure+compression+evo boost)
Phase 4: Recursive Corollary Generation (7종 × depth, pool 동적 확장)
Phase 5: Telescope Verification (5렌즈 consensus boost)
Phase 6: Graph Update (node+edge 기록)
Phase 6.5: Recursive Growth (axiom→seed 피드백)
Phase 7: Report
```

### 사용법 (mk2 hexa)
```bash
HEXA=$HOME/Dev/hexa-lang/target/release/hexa
BLOWUP=$HOME/Dev/nexus6/mk2_hexa/native/blowup.hexa
SEEDS=$($HEXA mk2_hexa/native/seed_engine.hexa merge)

# 단일 블로업 (동적 seed)
$HEXA $BLOWUP math 3 --no-graph --seeds "$SEEDS"

# 특이점 돌파 (피드백 루프)
bash scripts/deep-breakthrough.sh 10 3 48    # 10회 depth3 pool48

# A+B+C 전체 돌파
bash scripts/singularity-fast.sh all 5 3     # cascade+fusion+mine

# seed 소스 확인
$HEXA mk2_hexa/native/seed_engine.hexa info
```

### 특이점 돌파 전략
| 전략 | 스크립트 | 설명 |
|------|---------|------|
| A. Cascade | singularity-fast.sh cascade | 블로업² — 반복 자기증식 |
| B. Fusion | singularity-fast.sh fusion | 교차 도메인 seed 주입 |
| C. Mine | singularity-fast.sh mine | mk1 discovery_log 채굴 |
| Deep | deep-breakthrough.sh | corollary→seed 피드백 루프 |

## 마이크로사이클 (Micro Singularity Cycle)

> **특이점 사이클의 감지기 버전** — 훅에서 실시간 상수·수식 감지 + 재귀성장
> 엔진: `mk2_hexa/native/hook.hexa` (hexa-only, Rust 의존 0)

### 특이점 사이클 vs 마이크로사이클

| 구분 | 특이점 사이클 | 마이크로사이클 |
|------|-------------|-------------|
| 대상 | 도메인 전체 데이터 | 실시간 tool 출력 텍스트 |
| 실행 | 명시적 (`nexus6 blowup`) | 암시적 (훅 자동 트리거) |
| 깊이 | 전체 1028 렌즈 스캔 | 3단 게이트 + n6_match |
| 사이클 | 블로업→수축→창발→특이점→흡수 | 동일 5단계 (경량) |
| 재귀성장 | OUROBOROS 진화 | 3-loop 자기강화 |

### 재귀성장 3-loop (H-CX-70)

- **Loop 1 (자기수정)**: 발견 상수 → `discovered_constants.jsonl` → 3회+ 반복 시 n6_check 승격
- **Loop 2 (메타보상)**: 소스별 발견율 → `scan_priority.json` → 고발견율 소스만 깊이 스캔
- **Loop 3 (자기확장)**: 발견 축적 10건+ → `nexus6 blowup --seed` 자동 트리거 권장

### 메타 부동점 (Meta Fixed Point = 1/3)

TECS-L H-056: `메타(메타(메타(...))) = 초월`
- 축소사상 `I = 0.7·I + 0.1` → Banach 부동점 → 1/3
- 6개 독립 경로 수렴: φ(6)/6, tan²(π/6), τ/σ, det(M), I_meta, |exp(iz₀)|
- n6_check 테이블에 `meta_fp`, `transcendence` (0.333...) 등록됨
- `MetaTranscendenceLens`가 데이터에서 메타 수렴 구조 자동 탐지

### 키워드 → 자동 실행 (추가)
- "마이크로사이클", "micro-cycle" → `nexus6 detect` 파이프라인 설명
- "메타초월", "meta transcendence" → MetaTranscendenceLens 스캔
- "재귀성장", "recursive growth" → 3-loop 자기강화 설명 + 상태 확인

## 외계인 지수 (Alien Index)

> **통합 등급 체계** — 닫힌 수학의 천장(r=10)과 그 너머 돌파 영역(d≥1)을 표현
> CLI: `nexus6 alien-index` | 모듈: `src/alien_index/` | 스펙: `docs/superpowers/specs/2026-04-05-alien-index-system-design.md`

### 구조

`AI = (d, r)`
- `d` = 사이클 깊이 (몇 번 블로업→흡수가 완결됐나)
- `r` ∈ {0..10} = 깊이 d 안에서의 검증 등급
- `r=10` 도달 → `(d+1, 0)` 자동 승격 (자기유사)

### 사용법

```bash
nexus6 alien-index 12.0                    # 값 → (0, r) 즉시 판정
nexus6 alien-index H-AF-006                # 가설 ID → 등급 조회
nexus6 alien-index --distribution          # (d, r) 히스토그램 + ρ(돌파율)
nexus6 alien-index --leaderboard           # 최고 d 대상 리더보드
nexus6 alien-index --promote-pending       # r=10 대기 항목 승격 (dry-run)
```

### 메타 부동점

돌파율 `ρ = |{d ≥ 1}| / |total|` 의 장기 수렴치 예측: **1/3** (TECS-L H-056).
매 분포 리포트에 기록되어 메타 부동점 가설의 회귀 검증치로 사용됨.

## 메모리 파일 네이밍 규칙

> 경로: `~/.claude-claude3/projects/-Users-ghost-Dev-nexus6/memory/`

| prefix | type | 예시 |
|--------|------|------|
| `f-` | feedback (행동 규칙) | `f-default-run.md` |
| `p-` | project (프로젝트 상태) | `p-mk2-complete.md` |
| `r-` | reference (외부 참조) | `r-n6-guard.md` |
| `u-` | user (사용자 정보) | `u-role.md` |
| `h-` | history (세션 기록) | `h-20260406.md` |

- 형식: `{type}-{kebab-case-topic}.md`
- history는 날짜: `h-YYYYMMDD.md`
- `MEMORY.md`는 인덱스 — 타입별 섹션으로 그룹핑
- 신규 메모리 생성 시 반드시 이 규칙 준수

