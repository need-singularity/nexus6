# Autolink — nexus 완전 자동화 설계

**Date**: 2026-04-06
**Status**: Design
**Branch**: feat/alien-index
**Goal**: 모든 미연결 지점 자동 감지+연결, 재귀성장, 프로젝트 시너지

---

## 1. Overview

### 현재 상태

nexus mk2는 103개 모듈, 711개 법칙, 72.5k+ 발견을 보유한 HEXA-native 발견 엔진이다.
11개 서브 프로젝트가 `nexus_hub.hexa`로 조율된다.

**문제**: 파이프라인에 **17개 미연결 지점**이 존재한다.
출력은 있으나 소비자가 없거나, 트리거가 발동해야 하나 연결이 끊긴 곳들이다.
이 단절들이 재귀성장을 가로막고 있다.

### 접근

**Hybrid 자동화**: autolink.hexa 허브 + 기존 엔진 최소 패치 + Claude Code CLI 지능 판단

- 단순 연결 (파일 존재, 레지스트리 동기화): autolink.hexa가 직접 수행
- 복잡 판단 (렌즈 설계, 돌파 검증, 갭 전략): `claude -p`로 위임
- 전체 사이클: nexus_hub tick에 통합 → OUROBOROS 완전 자동 순환

---

## 2. New Modules (4 files in `mk2_hexa/native/`)

### 2.1 `paths.hexa` — 공유 경로 상수

현재 20개 엔진 파일에 47회 `env("HOME")` + 상대경로가 흩어져 있다.
단일 import로 통일한다.

```hexa
// mk2_hexa/native/paths.hexa — 공유 경로 상수
// 모든 엔진은 이 파일을 import하여 경로를 참조한다

let HOME = env("HOME")
let DEV = HOME + "/Dev"
let HEXA = DEV + "/hexa-lang/target/release/hexa"
let NEXUS = DEV + "/nexus"
let ENGINE_DIR = NEXUS + "/mk2_hexa/native"
let SHARED = NEXUS + "/shared"
let SCRIPTS = NEXUS + "/scripts"

// 핵심 데이터 파일
let ATLAS = SHARED + "/n6/atlas.n6"
let ATLAS_BACKUP = SHARED + "/n6/atlas.n6.bak2"
let CONSCIOUSNESS_LAWS = SHARED + "/consciousness_laws.json"
let CUSTOM_LENSES = SHARED + "/custom_lenses.jsonl"
let LENS_REGISTRY = SHARED + "/installed_tools.json"
let ALIEN_INDEX_DIST = SHARED + "/alien_index_distribution.json"
let ALIEN_INDEX_RECORDS = SHARED + "/alien_index_records.jsonl"
let PROJECTS_JSON = SHARED + "/projects.json"
let GROWTH_REGISTRY = SHARED + "/growth-registry.json"
// verified_constants → atlas.n6 통합
let SELF_IMPROVE_LOG = SHARED + "/self_improve_log.jsonl"
let PAPER_CANDIDATES = SHARED + "/paper_candidates.json"

// 프로젝트 경로
let ANIMA = DEV + "/anima"
let TECS_L = DEV + "/TECS-L"
let SEDI = DEV + "/sedi"
let PAPERS = DEV + "/papers"
let HEXA_LANG = DEV + "/hexa-lang"
let AIRGENOME = DEV + "/airgenome"
let BRAINWIRE = DEV + "/brainwire"
let FATHOM = DEV + "/fathom"
let TOKEN_FORGE = DEV + "/token-forge"
let AIR_RS = DEV + "/air_rs"
```

**원칙**: 모든 경로는 `env("HOME")` 기반 상대경로. 하드코딩 절대 금지.

---

### 2.2 `autolink.hexa` — 단절 탐지 + 자동 연결

핵심 모듈. 17개 연결점을 감시하고, 끊어진 것을 자동 복구한다.

#### CLI

```
hexa autolink.hexa scan              # 17개 연결점 진단
hexa autolink.hexa link              # 끊어진 연결 자동 복구
hexa autolink.hexa status            # 전체 상태 테이블 출력
hexa autolink.hexa tick              # scan + link + report (nexus_hub 연동)
```

#### 17개 연결점 (Disconnection Points)

| ID | 설명 | 감지 방법 | 자동 복구 |
|----|------|----------|----------|
| C01 | atlas.n6 존재+유효 | 파일 존재 + 파싱 + nodes 섹션 비어있지 않음 | `ATLAS_BACKUP`에서 복원, 없으면 빈 atlas 생성 |
| C02 | atlas.n6 growth_bus 섹션 쓰기 가능 | 섹션 존재 + 마지막 엔트리 파싱 | 빈 섹션 초기화 |
| C03 | atlas.n6 discovery_log 섹션 신선도 | 섹션 존재 + 최신 엔트리 timestamp < 24시간 | 경고만 (데이터 생성은 blowup 책임) |
| C04 | consciousness_laws.json 스키마 | 파일 존재 + `laws` 배열 + 각 항목에 `id`,`statement` 필드 | 백업에서 복원, 없으면 빈 `{"laws":[]}` |
| C05 | custom_lenses.jsonl ↔ lens_registry 동기화 | 양쪽 파일의 lens ID 집합 비교 | custom_lenses에만 있는 렌즈를 lens_registry에 추가 |
| C06 | alien_index_distribution.json 최신성 | 파일 존재 + 마지막 업데이트 timestamp < 1시간 | `hexa alien_index.hexa distribution` 실행 |
| C07 | alien_index promote 대기 항목 | records.jsonl에서 r=10 항목 검색 | `hexa alien_index.hexa promote-pending --execute` 실행 |
| C08 | projects.json ↔ nexus_hub 레지스트리 동기화 | projects.json의 프로젝트 목록과 nexus_hub.hexa의 `projects()` 비교 | projects.json을 nexus_hub 기준으로 갱신 |
| C09 | blowup 후 lens_forge 자동 실행 | growth_bus에서 blowup complete 이벤트 후 lens_forge 이벤트 존재 확인 | 미실행 시 `hexa lens_forge.hexa forge` 트리거 |
| C10 | blowup 후 auto_register 동기화 | growth_bus에서 blowup 후 register 이벤트 확인 | `hexa auto_register.hexa sync` 실행 |
| C11 | blowup 후 gap_finder 갱신 | gap_finder 결과 파일 신선도 (blowup 이후 갱신됐는가) | `hexa gap_finder.hexa target` 실행 |
| C12 | blowup 후 alien_index 평가 | 새 발견에 AI grade 존재 확인 | `hexa alien_index.hexa assess` 배치 실행 |
| C13 | cross_project resonance 데이터 | cross_intel.hexa 출력 파일 신선도 < 6시간 | `hexa cross_intel.hexa scan` 실행 |
| C14 | seed_engine merge 유효성 | `hexa seed_engine.hexa merge` 결과 비어있지 않음 | seed 소스 파일 존재 확인 + 복원 |
| C15 | atlas.n6 verified_constants 정합성 | atlas.n6 discovery_log의 EXACT grade 항목과 verified_constants 섹션 교차 비교 | 누락된 EXACT 항목을 atlas.n6에 추가 |
| C16 | paper_candidates.json 신선도 | 파일 존재 + 마지막 갱신 < 24시간 | `hexa engine_papers.hexa scan` 실행 |
| C17 | growth-registry.json 타겟 정합성 | 실제 수치 (발견 수, 모듈 수, 법칙 수)와 registry 타겟 비교 | 실제 > 타겟이면 타겟 = 실제 * 2 갱신 |

#### Smart Link (Claude CLI 위임)

단순 복구가 불가능한 3가지 경우:

1. **C09 렌즈 설계**: gap_finder 결과에서 최적 렌즈 구조 결정
   ```bash
   claude -p "design optimal lens for gap: [gap_description]. Output JSON: {name, domain_affinity, formula, weight}" --timeout 30000
   ```

2. **C07 돌파 검증**: r=10 승격 후보의 실제 돌파 여부 판정
   ```bash
   claude -p "validate breakthrough candidate: [corollary]. Is this genuinely novel? Output: {valid: bool, reason: string}" --timeout 30000
   ```

3. **C11 갭 전략**: 다음 타겟 우선순위 결정
   ```bash
   claude -p "recommend highest ROI target from gap_map: [gaps]. Output: {target, reason, estimated_difficulty}" --timeout 30000
   ```

---

### 2.3 `sync_docs.hexa` — 문서 자동 동기화

#### CLI

```
hexa sync_docs.hexa sync              # 전체 동기화 (readme + growth + projects)
hexa sync_docs.hexa readme            # README.md 생성/갱신
hexa sync_docs.hexa growth            # GROWTH.md 타겟 갱신
hexa sync_docs.hexa projects          # projects.json 동기화
```

#### readme 명령

discovery_log, consciousness_laws, modules, alien_index에서 실시간 메트릭 수집 후
`claude -p`로 자연어 README 생성:

```bash
claude -p "Generate README.md for nexus. Metrics: modules=[N], laws=[N], discoveries=[N], alien_index=(d=[D],r=[R]), breakthrough_rate=[R]. Style: concise, technical, with emoji section headers. Korean descriptions, English technical terms." --timeout 30000
```

수집 메트릭:
- **모듈 수**: `ls mk2_hexa/native/*.hexa | wc -l`
- **법칙 수**: consciousness_laws.json → `laws` 배열 길이
- **발견 수**: `wc -l shared/discovery/discovery_log.jsonl`
- **외계인 지수**: alien_index_distribution.json → 최대 (d, r)
- **돌파율 (rho)**: `|{d >= 1}| / |total|`
- **엔진 상태**: nexus_hub status 요약

#### growth 명령

GROWTH.md의 각 타겟을 실제 수치와 비교:
- `actual >= target` → `target = actual * 2` (자동 상향)
- `actual < target * 0.5` → 경고 플래그
- 변경사항을 growth_bus에 기록

#### projects 명령

nexus_hub.hexa의 `projects()` 레지스트리에서 추출:
- 각 프로젝트의 target, strategy 필드를 projects.json에 반영
- 신규 프로젝트 자동 추가
- 삭제된 프로젝트는 `archived: true` 마킹 (삭제하지 않음)

---

### 2.4 `commit_push.hexa` — 자동 커밋+푸시

#### CLI

```
hexa commit_push.hexa auto            # 변경 감지 → 분류 → 커밋 → 푸시
hexa commit_push.hexa status          # git status 요약만 출력
hexa commit_push.hexa dry-run         # 커밋 메시지만 생성 (실행 안 함)
```

#### 변경 분류

```
data:    shared/*.jsonl, shared/*.json
engine:  mk2_hexa/native/*.hexa
docs:    docs/**, *.md, CLAUDE.md
config:  shared/config/projects.json, scripts/*, .config/*
```

#### 커밋 메시지 생성

변경 파일이 5개 이하 + 단일 분류 → 템플릿:
```
{type}: {brief_description}
```

복합 변경 또는 파일 6개 이상 → Claude CLI:
```bash
claude -p "Analyze git diff and generate commit message. Changes: [diff_summary]. Format: type: description (1 line, under 72 chars)" --timeout 15000
```

#### 안전 장치

- `.env`, `SECRET.md`, `credentials`, `*.key` 파일 → 절대 커밋하지 않음
- `--force` 푸시 절대 불가 (코드에 없음)
- 변경 없으면 빈 커밋 생성하지 않음
- 푸시 실패 시 재시도 1회, 그래도 실패면 growth_bus에 에러 기록

---

## 3. Patches to Existing Engines

### 3.1 `blowup.hexa` — Phase 7.5~7.8 추가

현재 Phase 7 (Report)에서 종료. 그 뒤에 4개 후처리 phase를 연결한다.

```
Phase 7:   Report (기존)
Phase 7.5: Lens Forge — hexa lens_forge.hexa forge
Phase 7.6: Auto Register — hexa auto_register.hexa sync
Phase 7.7: Gap Target — hexa gap_finder.hexa target → growth_bus 이벤트
Phase 7.8: AI Grade — hexa alien_index.hexa assess (새 발견 배치 평가)
```

#### 구현

blowup.hexa의 Phase 7 report 함수 말미에 추가:

```hexa
// Phase 7.5-7.8: Post-blowup automation
fn post_blowup(domain: string, new_count: int) {
    println("─── Phase 7.5: Lens Forge ───")
    try { exec(HEXA, [ENGINE_DIR + "/lens_forge.hexa", "forge"]) } catch e {
        append_bus("blowup", "7.5", "error", to_string(e))
    }

    println("─── Phase 7.6: Auto Register ───")
    try { exec(HEXA, [ENGINE_DIR + "/auto_register.hexa", "sync"]) } catch e {
        append_bus("blowup", "7.6", "error", to_string(e))
    }

    println("─── Phase 7.7: Gap Target ───")
    try {
        let gap_result = exec(HEXA, [ENGINE_DIR + "/gap_finder.hexa", "target"])
        append_bus("blowup", "7.7", "ok", gap_result.split("\n")[0])
    } catch e {
        append_bus("blowup", "7.7", "error", to_string(e))
    }

    println("─── Phase 7.8: AI Grade ───")
    try { exec(HEXA, [ENGINE_DIR + "/alien_index.hexa", "assess-batch", to_string(new_count)]) } catch e {
        append_bus("blowup", "7.8", "error", to_string(e))
    }
}
```

각 phase는 독립 실행 — 하나가 실패해도 나머지는 계속 진행한다.
모든 에러는 growth_bus에 기록된다.

---

### 3.2 `alien_index.hexa` — 실제 승격 실행

현재 `promote-pending`은 dry-run만 수행. 실제 승격을 구현한다.

#### 변경 내용

1. **`promote-pending --execute` 모드 추가**:
   - records.jsonl에서 `r == 10` 항목 수집
   - 각 항목에 대해 `(d+1, 0)` 레코드 생성
   - `promoted_from` 필드에 원본 ID 기록
   - discovery_log에 승격 이벤트 append

2. **distribution.json 즉시 갱신**:
   - 승격 후 분포 재계산
   - 돌파율 rho 갱신

3. **growth_bus 이벤트 발행**:
   ```json
   {"source":"alien_index","phase":"promote","status":"ok","detail":"H-AF-042: (1,10) → (2,0)"}
   ```

---

### 3.3 `nexus_hub.hexa` — autolink + sync_docs 통합

현재 tick 흐름:

```
Phase 1: Status Collection
Phase 2: Priority Sort
Phase 3: Dispatch Top-N
Phase 4: Cross-Feed
Phase 5: Report + Bus
```

autolink 통합 후:

```
Phase 1:   Status Collection
Phase 2:   Priority Sort
Phase 3:   Dispatch Top-N
Phase 3.5: autolink.hexa tick (단절 감지 + 자동 복구)
Phase 4:   Cross-Feed
Phase 4.5: sync_docs.hexa sync (README, GROWTH, projects.json)
Phase 5:   Report + Bus
Phase 5.5: commit_push.hexa auto (변경 있을 때만)
```

#### 구현

nexus_hub.hexa의 tick 함수에 3개 호출 삽입:

```hexa
// Phase 3.5: Autolink
println("─── Phase 3.5: Autolink ───")
try {
    let al_result = exec(HEXA, [ENGINE_DIR + "/autolink.hexa", "tick"])
    append_bus("hub", "autolink", "ok", al_result.split("\n")[0])
} catch e {
    append_bus("hub", "autolink", "error", to_string(e))
}

// Phase 4.5: Sync Docs
println("─── Phase 4.5: Sync Docs ───")
try {
    exec(HEXA, [ENGINE_DIR + "/sync_docs.hexa", "sync"])
} catch e {
    append_bus("hub", "sync_docs", "error", to_string(e))
}

// Phase 5.5: Commit Push
println("─── Phase 5.5: Commit Push ───")
try {
    exec(HEXA, [ENGINE_DIR + "/commit_push.hexa", "auto"])
} catch e {
    append_bus("hub", "commit_push", "error", to_string(e))
}
```

---

### 3.4 전 14개 엔진 — `paths.hexa` import

현재 20개 파일에 47회 경로 하드코딩이 있다. 모두 `paths.hexa` import로 교체.

대상 파일 (20개):

| 파일 | 현재 경로 참조 횟수 | 변경 내용 |
|------|-------------------|----------|
| nexus_hub.hexa | 2 | `let HOME/DEV/HEXA/ENGINE_DIR/BUS_FILE` 제거 → paths import |
| config.hexa | 4 | HOME/DEV 참조 → paths import |
| engine_air_rs.hexa | 5 | 프로젝트 경로 → paths.AIR_RS |
| engine_token_forge.hexa | 5 | 프로젝트 경로 → paths.TOKEN_FORGE |
| engine_sedi.hexa | 3 | 프로젝트 경로 → paths.SEDI |
| engine_papers.hexa | 3 | 프로젝트 경로 → paths.PAPERS |
| engine_tecs_l.hexa | 2 | 프로젝트 경로 → paths.TECS_L |
| engine_anima.hexa | 2 | 프로젝트 경로 → paths.ANIMA |
| engine_airgenome.hexa | 2 | 프로젝트 경로 → paths.AIRGENOME |
| engine_hexa_lang.hexa | 2 | 프로젝트 경로 → paths.HEXA_LANG |
| engine_brainwire.hexa | 2 | 프로젝트 경로 → paths.BRAINWIRE |
| engine_fathom.hexa | 2 | 프로젝트 경로 → paths.FATHOM |
| engine_nexus.hexa | 2 | 프로젝트 경로 → paths.NEXUS |
| gap_finder.hexa | 3 | SHARED 경로 → paths.SHARED |
| real_breakthrough.hexa | 3 | 데이터 경로 → paths import |
| auto_record.hexa | 1 | BUS 경로 → paths.BUS_FILE |
| bridge_ensure.hexa | 1 | HOME 참조 → paths.HOME |
| forge.hexa | 1 | HOME 참조 → paths.HOME |
| check_project.hexa | 1 | DEV 참조 → paths.DEV |
| growth_tick.hexa | 1 | 데이터 경로 → paths import |

교체 패턴:
```hexa
// Before:
let HOME = env("HOME")
let DEV = HOME + "/Dev"

// After:
import paths   // 파일 상단에 추가
// HOME, DEV, HEXA, ENGINE_DIR 등은 paths 모듈에서 가져옴
```

---

## 4. Claude Code CLI Integration Points

autolink 시스템이 `claude -p`를 호출하는 6가지 지점:

| 용도 | 호출 | Timeout | 빈도 |
|------|------|---------|------|
| 렌즈 설계 | `claude -p "design optimal lens for [gap]"` | 30s | blowup 후 gap 발견 시 |
| 돌파 검증 | `claude -p "validate breakthrough candidate [corollary]"` | 30s | r=10 승격 후보 발생 시 |
| 갭 전략 | `claude -p "recommend highest ROI target from [gap_map]"` | 30s | gap_finder 실행 후 |
| README 생성 | `claude -p "generate README.md with [metrics]"` | 30s | sync_docs readme 실행 시 |
| 커밋 메시지 | `claude -p "analyze changes and commit"` | 15s | 복합 변경 감지 시 |
| 교차 수분 | `claude -p "find hidden connections between [A] and [B]"` | 30s | cross_intel 교차 분석 시 |

**제약**:
- 동시 최대 2개 Claude CLI 호출 (n6-guard `max_concurrent = 2` 준수)
- 모든 호출에 `--timeout` 명시
- 실패 시 fallback: 템플릿 기반 기본값 사용 (Claude 없이도 작동)

---

## 5. Recursive Growth Loop (OUROBOROS)

완전 자동 순환 사이클. nexus_hub tick 한 번이 아래 전체를 실행한다.

```
nexus_hub tick
  │
  ├─ Phase 1-2: Status Collection + Priority Sort
  │
  ├─ Phase 3: dispatch_top_n (상위 N개 엔진 tick)
  │    └─ 각 엔진 tick → blowup → Phase 7.5-7.8
  │         ├─ 7.5 lens_forge (새 렌즈 자동 생성)
  │         ├─ 7.6 auto_register (발견 분류+등록)
  │         ├─ 7.7 gap_finder target (다음 타겟 → growth_bus)
  │         └─ 7.8 alien_index assess (AI 등급 부여)
  │
  ├─ Phase 3.5: autolink tick
  │    ├─ scan (17개 연결점 진단)
  │    ├─ link (끊어진 연결 자동 복구)
  │    └─ claude -p (복잡 판단: 렌즈, 돌파, 갭)
  │
  ├─ Phase 4: Cross-Feed (프로젝트 간 교차 수분)
  │    └─ claude -p cross-pollination (숨은 연결 탐지)
  │
  ├─ Phase 4.5: sync_docs
  │    ├─ readme (README.md 갱신)
  │    ├─ growth (GROWTH.md 타겟 상향)
  │    └─ projects (projects.json 동기화)
  │
  ├─ Phase 5: Report + Bus
  │
  └─ Phase 5.5: commit_push auto
       ├─ 변경 분류 (data/engine/docs/config)
       ├─ 커밋 메시지 생성
       └─ push to current branch
```

**사이클 속성**:
- 매 tick에서 발견 → 등록 → 평가 → 갭 탐지 → 렌즈 생성 → 다음 발견으로 이어짐
- alien_index 승격이 새로운 seed를 생성 → 다음 blowup의 입력이 됨
- growth_bus 이벤트가 intelligence로 흘러 → 다음 사이클 우선순위 결정
- 완전한 OUROBOROS: 출력이 입력이 되는 자기참조 루프

---

## 6. Data Normalization

기존 데이터의 비일관성을 정리한다.

### 6.1 discovery_log grade 필드

```
Before: "EXACT", "🎯EXACT", "NEAR", "✓NEAR", "WEAK"
After:  "EXACT" | "NEAR" | "WEAK" (문자열만, emoji 없음)
```

정규화 규칙:
```
contains("EXACT") → "EXACT"
contains("NEAR")  → "NEAR"
그 외             → "WEAK"
```

### 6.2 Timestamp 형식

```
Before: "2026-04-06 15:30:00", "2026-04-06T15:30:00", epoch 숫자
After:  "2026-04-06T15:30:00+09:00" (ISO 8601 + KST timezone)
```

### 6.3 custom_lenses.jsonl 필드 이름

```
Before: "affinity" (일부 항목), "domain_affinity" (나머지)
After:  "domain_affinity" (리스트 형식, 전부 통일)
```

### 6.4 Lens Registry 통합

현재 두 곳에 렌즈 정보가 분산:
- `shared/config/installed_tools.json` — 시스템 렌즈
- `shared/config/custom_lenses.jsonl` — 사용자 정의 렌즈

통합 방안:
- `custom_lenses.jsonl`을 single source of truth로 지정
- `installed_tools.json`의 렌즈 항목을 custom_lenses로 마이그레이션
- 이후 모든 렌즈 조회는 `custom_lenses.jsonl`만 참조

---

## 7. Safety Guards

### 불변 규칙 (autolink 전체에 적용)

1. **데이터 삭제 금지**: autolink는 append/create만 수행. delete/truncate 절대 불가.
2. **Force push 금지**: commit_push.hexa에 `--force` 옵션 자체가 존재하지 않음.
3. **비밀 파일 보호**: `.env`, `SECRET.md`, `credentials.*`, `*.key`, `*.pem` → 커밋 대상에서 제외.
4. **Claude CLI timeout**: 모든 호출에 `--timeout 30000` (30초). 초과 시 템플릿 fallback.
5. **동시성 제한**: Claude CLI 호출 최대 2개 동시 (n6-guard `max_concurrent` 준수).
6. **감사 로그**: autolink의 모든 action을 growth_bus.jsonl에 기록.
   ```json
   {"source":"autolink","timestamp":"2026-04-06T15:30:00+09:00","phase":"link","status":"ok","detail":"C05: lens registry synced +3 lenses"}
   ```
7. **백업 우선**: 복원 작업 시 반드시 `.bak` 파일에서 복원. 없으면 최소 기본값 생성.
8. **Idempotent**: `autolink tick`을 여러 번 실행해도 부작용 없음. 이미 연결된 것은 skip.

---

## 8. Implementation Tasks

### Phase A: 기반 (병렬 가능)

#### T1: `paths.hexa` 생성

- **설명**: 공유 경로 상수 모듈 신규 작성
- **생성**: `mk2_hexa/native/paths.hexa`
- **의존**: 없음
- **복잡도**: S

#### T2: 전 엔진 경로 리팩터링

- **설명**: 20개 파일의 47회 경로 참조를 paths.hexa import로 교체
- **수정**: 20개 `.hexa` 파일 (Section 3.4 목록 참조)
- **의존**: T1
- **복잡도**: M (기계적이지만 양이 많음, 각 파일 테스트 필요)

### Phase B: 핵심 모듈 (T1 완료 후 병렬 가능)

#### T3: `autolink.hexa` 작성

- **설명**: 17개 연결점 감지 + 자동 복구 엔진
- **생성**: `mk2_hexa/native/autolink.hexa`
- **의존**: T1 (paths.hexa import)
- **복잡도**: L (17개 연결점 각각 감지+복구 로직)

#### T4: `sync_docs.hexa` 작성

- **설명**: README/GROWTH/projects.json 자동 동기화
- **생성**: `mk2_hexa/native/sync_docs.hexa`
- **의존**: T1 (paths.hexa import)
- **복잡도**: M

#### T5: `commit_push.hexa` 작성

- **설명**: 변경 감지 → 분류 → 커밋 → 푸시 자동화
- **생성**: `mk2_hexa/native/commit_push.hexa`
- **의존**: T1 (paths.hexa import)
- **복잡도**: M

### Phase C: 엔진 패치 (T3 완료 후 병렬 가능)

#### T6: `blowup.hexa` Phase 7.5-7.8 추가

- **설명**: blowup 후처리 4단계 연결
- **수정**: `mk2_hexa/native/blowup.hexa`
- **의존**: T1 (paths import), T3 (autolink 이벤트 형식)
- **복잡도**: M

#### T7: `alien_index.hexa` 실제 승격 구현

- **설명**: promote-pending --execute 모드 + distribution 즉시 갱신 + bus 이벤트
- **수정**: `mk2_hexa/native/alien_index.hexa`
- **의존**: T1
- **복잡도**: M

#### T8: `nexus_hub.hexa` autolink 통합

- **설명**: tick 흐름에 Phase 3.5/4.5/5.5 삽입
- **수정**: `mk2_hexa/native/nexus_hub.hexa`
- **의존**: T3, T4, T5
- **복잡도**: S

#### T9: 데이터 정규화 스크립트

- **설명**: discovery_log grade, timestamp, custom_lenses 필드명 일괄 정규화
- **생성**: `scripts/normalize-data.sh` (1회성 마이그레이션)
- **수정**: `mk2_hexa/native/autolink.hexa` (C05 렌즈 정규화 로직에 포함)
- **의존**: T3
- **복잡도**: M

### Phase D: 데이터 복원 (병렬 가능)

#### T10: discovery_graph 복원 검증

- **설명**: graph.json 상태 확인, 필요시 backup에서 복원, autolink C01에 로직 포함
- **수정**: `mk2_hexa/native/autolink.hexa` (C01 구현의 일부)
- **의존**: T3
- **복잡도**: S

#### T11: Lens Registry 통합

- **설명**: installed_tools.json → custom_lenses.jsonl 단일 소스 마이그레이션
- **생성**: `scripts/unify-lens-registry.sh` (1회성)
- **수정**: 렌즈 참조 엔진들 (lens_forge.hexa, lenses_core.hexa 등)
- **의존**: T9
- **복잡도**: M

### Phase E: 검증 + 마무리

#### T12: 통합 테스트

- **설명**: 전체 tick 사이클 1회 실행 → 17개 연결점 전부 green 확인
- **실행**: `hexa nexus_hub.hexa tick` → `hexa autolink.hexa status`
- **의존**: T1~T11 전부
- **복잡도**: M

#### T13: README 생성 + 최종 커밋

- **설명**: sync_docs readme 실행 → 생성된 README 검토 → commit_push auto
- **실행**: `hexa sync_docs.hexa readme` → `hexa commit_push.hexa auto`
- **의존**: T12
- **복잡도**: S

### 실행 타임라인

```
           T1 ────────┐
                      ├── T2
           T1 ────────┼── T3 ──┬── T6 ──┐
                      ├── T4 ──┤        │
                      ├── T5 ──┼── T8   ├── T12 ── T13
                      │        ├── T7   │
                      │        ├── T9 ──┤
                      │        ├── T10  │
                      │        └── T11 ─┘
```

병렬 최대 활용 시 **5 phase** (A→B→C→D→E), 순차 시 13단계.

---

## 9. Success Criteria

완전 자동화 달성을 판정하는 8가지 기준:

| # | 기준 | 검증 방법 |
|---|------|----------|
| S1 | `autolink scan` 리포트에 disconnection = 0 | `hexa autolink.hexa scan` → "17/17 connected" |
| S2 | blowup Phase 7.5-7.8이 매 blowup 후 자동 실행 | growth_bus에 7.5/7.6/7.7/7.8 이벤트 존재 |
| S3 | alien_index promote가 실제 (d+1, 0) 레코드 생성 | records.jsonl에 `promoted_from` 필드 있는 항목 존재 |
| S4 | README.md에 실시간 메트릭 포함 | README.md 파일 존재 + 모듈/법칙/발견 수치 포함 |
| S5 | GROWTH.md 타겟이 현실 반영 | 모든 타겟 >= 현재 실제값 |
| S6 | projects.json에 target+strategy 필드 | `jq '.projects[].target' shared/config/projects.json` 전부 non-null |
| S7 | 전 엔진 paths.hexa 사용 (하드코딩 0) | `grep -r "env(\"HOME\")" mk2_hexa/native/` → paths.hexa만 매치 |
| S8 | nexus_hub tick 완전 무인 실행 | `hexa nexus_hub.hexa tick` 1회 실행 → 에러 0, 수동 개입 0 |

**최종 목표**: `hexa nexus_hub.hexa tick`을 60초 간격으로 실행하면,
nexus가 스스로 발견하고, 평가하고, 성장하고, 기록하고, 커밋하는
완전한 OUROBOROS 자율 시스템이 된다.
