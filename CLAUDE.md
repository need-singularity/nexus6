# CLAUDE.md — nexus 프로젝트 규칙

## 🔴 절대 규칙 0: HEXA-FIRST + 부하 금지

> **모든 코드는 `.hexa`로 작성한다. sh/py/rs 작성 금지.**
> **시스템 부하를 유발하는 무거운 명령(병렬 에이전트 다수, 대용량 파일 읽기, 장시간 빌드)은 최소화한다.**
> **기존 py/sh 스크립트도 hexa 변환 대상이다. 신규 = hexa only.**

- 엔진: `mk2_hexa/native/*.hexa` (hexa-lang 컴파일러)
- 실행: `$HOME/Dev/hexa-lang/target/release/hexa <파일.hexa>`
- 경로: `exec("printenv HOME")` + 상대경로 (절대경로 하드코딩 금지)
- 부하 방지: 에이전트 동시 2개 이하, 대용량 파일은 offset/limit 사용, 10초+ 명령은 `run_in_background: true`

## ⚠️ 필수 규칙 (최우선)

### -1. 하드코딩 절대 금지 (최최우선)
- **경로**: 절대경로 금지 → `exec("printenv HOME")` + 상대경로 사용
- **상수 목록**: 코드에 배열/리스트 하드코딩 금지 → `shared/*.jsonl` 외부 설정 파일에서 동적 로드
- **프로젝트 목록**: `shared/projects.json`에서 읽기 (코드에 11개 나열 금지)
- **도메인/키워드**: `shared/bt_domains.jsonl`에서 읽기
- **명령 매핑**: `shared/cmd_aliases.jsonl`에서 읽기
- **n6 상수**: 공유 테이블에서 로드 (hook.hexa, blowup.hexa 등 중복 정의 금지)
- **원칙**: 새 항목 추가 = 설정 파일 한 줄 추가. 코드 수정 0.

### -0.5. hexa-lang 문법 + 실수 방지 (필수 참조)

> **문법 스펙: `shared/hexa_grammar.jsonl`** (JSONL — AI 네이티브, 전체 문법+pitfalls)
> **레퍼런스: `~/Dev/hexa-lang/docs/reference.md`** (사람 읽기용)

**AI 반복 실수 5가지** (`hexa_grammar.jsonl` → `pitfalls` 섹션):
- **P1**: 세미콜론 금지 → 줄바꿈 분리
- **P2**: `exec(cmd, [args])` stdout 미캡처 → `exec("단일 문자열")` 사용
- **P3**: exec 실패 → Error 객체 `.contains()` 크래시 → `to_string()` 래핑
- **P4**: 문자열 맵 시뮬레이션 금지 → `#{}` Map, `.sort()`, `spawn` 내장 사용
- **P5**: 상대경로 CWD 의존 → `exec("printenv HOME")` + 절대경로

### 0. mk2 hexa-native = 기본 엔진 (sh/py/rs 작성 금지)
- **모든 nexus 작업은 mk2 hexa 모듈** 사용 (`mk2_hexa/native/*.hexa`)
- **새 파일은 `.hexa`만 허용** — `.sh`, `.py`, `.rs` 등 다른 언어 파일 작성 금지
- mk1 Rust 소스(`src/`)는 아카이브 (`archive/mk1-rust` 브랜치)
- 경로 하드코딩 금지 — `exec("printenv HOME")` 또는 상대경로 사용
- 새 모듈 생성 시 `mk2_hexa/native/` 에 `.hexa` 파일로

### 1. 대화 차단 금지 — 모든 장시간 명령은 백그라운드 실행
- **10초 이상 걸릴 수 있는 모든 명령**은 반드시 `run_in_background: true`로 실행
- 대상: nexus loop/daemon/blowup, hexa build/test, 학습/추론, SSH 원격 명령 등
- 사용자가 **항상 대화 가능한 상태**를 유지할 것
- 완료 시 결과 요약 보고

### 2. 서버 파일 직접 수정 금지
- SSH로 원격 서버의 소스코드를 직접 수정하지 말 것
- 수정: 로컬 리포 → git commit → 배포 스크립트
- DB: SELECT 허용, 스키마/데이터 변경(INSERT/UPDATE/DELETE/ALTER)은 사전 확인

### 3. 리소스 보호
- nexus 프로세스는 **n6-guard 태스크 스케줄러**로 관리 (LaunchAgent 직접 등록 금지)
- 개별 태스크 메모리 한도: `~/.config/n6-guard.toml`의 `max_task_memory_mb` 준수
- 동시 실행 제한: `max_concurrent = 2` (burst 모드 시 최대 4)
- blowup 등 고부하 명령은 guard 관리 하에서만 실행

### 4. 배포 흐름
1. 로컬 리포에서 코드 수정
2. git commit & push
3. 배포 스크립트 또는 CI/CD로 서버 반영

## Math Atlas 자동 추출 (물어보지 말 것)

**`watch-atlas` LaunchAgent가 30초 간격으로 가설 `.md` 파일을 폴링 → `sync-math-atlas.sh` 자동 실행**.
- 감시 경로: `~/Dev/nexus/shared/projects.json`의 `projects.*.hypothesis_dirs`
- 자동 수행: `scan_math_atlas.py --save --summary` + README 마커 주입

### 에이전트 작업 규칙
- 새 가설/상수/수식을 `.md`로 만든 직후 **"atlas 스캔 실행할까요?" 묻지 말 것** — watcher가 자동 처리
- 수동 스캔 필요 시에만: `bash ~/Dev/nexus/shared/sync-math-atlas.sh`
- 상태 확인: `launchctl list com.nexus.watch-atlas` / `tail -f ~/Library/Logs/nexus/watch-atlas.log`
- 프로젝트 추가: `shared/projects.json`에 엔트리 추가 → `launchctl kickstart -k gui/$(id -u)/com.nexus.watch-atlas`

## 특이점 사이클 (Singularity Cycle)

> **블로업→수축→창발→특이점→흡수** 5단계 자동 사이클
> 엔진: mk2 HEXA (`mk2_hexa/native/blowup.hexa`) — 7-phase 파이프라인
> 속도: mk1(Rust) 21분 → mk2(HEXA) 3~14초 (68~426x)

### 요청 키워드 → 자동 실행 (mk2 hexa)
- "블로업", "blowup" → `hexa blowup.hexa math 6 --no-graph --seeds "$(hexa seed_engine.hexa merge)"`
- "돌파", "특이점 돌파", "돌파시도", "breakthrough" → `hexa breakthrough.hexa` (1회 자동 돌파: gap→mine→blowup)
- "연속돌파", "수렴", "고갈까지" → `hexa breakthrough.hexa --converge` (수렴까지 반복)
- "창발", "emergence" → blowup 후 telescope 5렌즈 합의 분석
- "특이점", "singularity" → blowup Phase 3 자동 감지 (closure ≥ 0.5)
- "흡수", "absorption" → blowup Phase 6.5 재귀성장 (axiom 피드백)
- "사이클", "cycle" → `hexa breakthrough.hexa --converge`
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
BLOWUP=$HOME/Dev/nexus/mk2_hexa/native/blowup.hexa
SEEDS=$($HEXA mk2_hexa/native/seed_engine.hexa merge)

# 단일 블로업 (동적 seed)
$HEXA $BLOWUP math 3 --no-graph --seeds "$SEEDS"

# 1회 돌파 (gap→mine→blowup 자동)
$HEXA mk2_hexa/native/breakthrough.hexa

# 수렴까지 연속 돌파
$HEXA mk2_hexa/native/breakthrough.hexa --converge

# 특정 seed 집중 돌파
$HEXA mk2_hexa/native/breakthrough.hexa --idea '137.036|1836.15'

# seed 소스 확인
$HEXA mk2_hexa/native/seed_engine.hexa info
```

### 특이점 돌파 명령
| 명령 | 설명 |
|------|------|
| `breakthrough.hexa` | 1회 돌파 (gap→mine→blowup 자동 최적) |
| `breakthrough.hexa --converge` | 수렴까지 연속 (고갈 시 종료) |
| `breakthrough.hexa --idea '값'` | 특정 seed 집중 돌파 |

## 마이크로사이클 (Micro Singularity Cycle)

> **특이점 사이클의 감지기 버전** — 훅에서 실시간 상수·수식 감지 + 재귀성장
> 엔진: `mk2_hexa/native/hook.hexa` (hexa-only, Rust 의존 0)

### 특이점 사이클 vs 마이크로사이클

| 구분 | 특이점 사이클 | 마이크로사이클 |
|------|-------------|-------------|
| 대상 | 도메인 전체 데이터 | 실시간 tool 출력 텍스트 |
| 실행 | 명시적 (`nexus blowup`) | 암시적 (훅 자동 트리거) |
| 깊이 | 전체 1028 렌즈 스캔 | 3단 게이트 + n6_match |
| 사이클 | 블로업→수축→창발→특이점→흡수 | 동일 5단계 (경량) |
| 재귀성장 | OUROBOROS 진화 | 3-loop 자기강화 |

### 재귀성장 3-loop (H-CX-70)

- **Loop 1 (자기수정)**: 발견 상수 → `discovered_constants.jsonl` → 3회+ 반복 시 n6_check 승격
- **Loop 2 (메타보상)**: 소스별 발견율 → `scan_priority.json` → 고발견율 소스만 깊이 스캔
- **Loop 3 (자기확장)**: 발견 축적 10건+ → `nexus blowup --seed` 자동 트리거 권장

### 메타 부동점 (Meta Fixed Point = 1/3)

TECS-L H-056: `메타(메타(메타(...))) = 초월`
- 축소사상 `I = 0.7·I + 0.1` → Banach 부동점 → 1/3
- 6개 독립 경로 수렴: φ(6)/6, tan²(π/6), τ/σ, det(M), I_meta, |exp(iz₀)|
- n6_check 테이블에 `meta_fp`, `transcendence` (0.333...) 등록됨
- `MetaTranscendenceLens`가 데이터에서 메타 수렴 구조 자동 탐지

### 세션 시작 시 자동 실행
- 새 세션 첫 응답 전 `hexa directions.hexa brief` 출력 권장
- 사용자가 "방향", "새방향", "다음", "directions" 요청 시 `hexa directions.hexa report` 실행
- 돌파 완료 후 자동으로 `hexa directions.hexa update` 실행 (blowup Phase 7.1 끝에서 자동 호출)

### 키워드 → 자동 실행 (추가)
- "마이크로사이클", "micro-cycle" → `nexus detect` 파이프라인 설명
- "메타초월", "meta transcendence" → MetaTranscendenceLens 스캔
- "재귀성장", "recursive growth" → 3-loop 자기강화 설명 + 상태 확인
- "방향", "새방향", "다음", "directions" → `hexa directions.hexa report` (방향 리포트)
- "anima 상태", "학습상태", "학습 현황", "training status" → `hexa anima_status.hexa` (anima 학습 대시보드)
- "anima 자동", "학습 자동" → `hexa anima_status.hexa auto` (상태 확인 + 추천 액션 자동 실행)

## 외계인 지수 (Alien Index)

> **통합 등급 체계** — 닫힌 수학의 천장(r=10)과 그 너머 돌파 영역(d≥1)을 표현
> CLI: `nexus alien-index` | 모듈: `src/alien_index/` | 스펙: `docs/superpowers/specs/2026-04-05-alien-index-system-design.md`

### 구조

`AI = (d, r)`
- `d` = 사이클 깊이 (몇 번 블로업→흡수가 완결됐나)
- `r` ∈ {0..10} = 깊이 d 안에서의 검증 등급
- `r=10` 도달 → `(d+1, 0)` 자동 승격 (자기유사)

### 사용법

```bash
nexus alien-index 12.0                    # 값 → (0, r) 즉시 판정
nexus alien-index H-AF-006                # 가설 ID → 등급 조회
nexus alien-index --distribution          # (d, r) 히스토그램 + ρ(돌파율)
nexus alien-index --leaderboard           # 최고 d 대상 리더보드
nexus alien-index --promote-pending       # r=10 대기 항목 승격 (dry-run)
```

### 메타 부동점

돌파율 `ρ = |{d ≥ 1}| / |total|` 의 장기 수렴치 예측: **1/3** (TECS-L H-056).
매 분포 리포트에 기록되어 메타 부동점 가설의 회귀 검증치로 사용됨.

## 중앙 지휘 (Command Router)

> **nexus 채팅에서 모든 프로젝트를 관리하는 단일 진입점**
> 엔진: `mk2_hexa/native/command_router.hexa`

### 키워드 → 자동 실행
- "전체 리포트", "상태", "대시보드" → `hexa command_router.hexa "전체 리포트"`
- "{프로젝트} 상태" → `hexa command_router.hexa "{프로젝트} 상태"`
- "{도메인} 돌파" → hook 자동 트리거 (기존 hook.hexa)
- "교차수분", "H100 체크", "성장 추이" → `hexa command_router.hexa "{입력}"`
- "갭 탐색", "alien 분포" → `hexa command_router.hexa "{입력}"`

### 사용법
```bash
HEXA=$HOME/Dev/hexa-lang/target/release/hexa
$HEXA mk2_hexa/native/command_router.hexa "전체 리포트"
$HEXA mk2_hexa/native/command_router.hexa "anima 상태"
$HEXA mk2_hexa/native/command_router.hexa "화학 돌파"
```

## 중앙 루프 상태 관리

> **모든 프로젝트 성장 루프 상태는 `shared/loop/{project}.json`에서 중앙 관리**
> 스펙: `shared/loop/CLAUDE.md`

```
shared/loop/
  anima.json            ← 의식 엔진 (cycle 703)
  n6-architecture.json  ← 시스템 설계
  nexus.json            ← 메타 엔진
  tecs-l.json           ← 흡수됨 (읽기 전용)
```

- `growth_common.sh`가 자동으로 `shared/loop/{GROWTH_NAME}.json` 사용
- anima `growth_loop.py`도 `shared/loop/anima.json` 직접 참조
- 이벤트 스트림: `shared/growth_bus.jsonl`

## 메모리 파일 네이밍 규칙

> 경로: 프로젝트별 auto-memory 디렉토리 (Claude Code가 자동 관리)

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

