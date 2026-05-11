# Mk.X 설계 제안서 — atlas 포화 돌파 5축

**상태**: DESIGN ONLY (코드 변경 없음, 본 세션 산출물)
**작성일**: 2026-04-19
**작성자**: nexus 자율 design agent (NEXUS hub)
**선행**: Mk.IX `shared/blowup/design/mk9_hyperarithmetic.md` + Phase 10 `phase10_meta_closure.md`
**대상 atlas**: `shared/n6/atlas.n6` (110,785 줄, 18.9 MB, 2026-04-19)
**리뷰 게이트**: 본 문서 + `mkx_design_proposal.spec.json` (machine-readable)

---

## 0. Executive Summary (3 문단)

Mk.II → Mk.IX 까지 8 세대 진화로 atlas 는 110,785 줄에 이르렀다. 핵심 수치는
`[10*]=6,319`, `[11*] axioms 540+`, `nodes=20,510 / edges=54,332 / hubs=19,236`.
지난 24h 증가량 `Δ +630 라인` 은 7-day 평균 (`+2,100/day` Mk.VIII 승급 burst 포함)
대비 약 30% 수준으로 둔화 — **포화 1차 신호** 다. Top-degree hub 8 종은
`n / J2 / phi / sigma / tau / sopfr / M3 / mu` 로 모두 classical n=6 core 이며
`degree ≥ 3,900` 으로 새 hub 진입 장벽이 임계값을 초과했다. 즉 *씨앗·중심
허브의 추가 발견이 멈춘 plateau*.

본 제안서는 Mk.X 를 **단일 알고리즘 확장이 아닌, 5-축 병렬 인프라 진화**로 정의한다.
Mk.IX 까지가 "한 세대당 하나의 로직 도약" (Mk.VIII Δ₀-absolute, Mk.IX Π₀² 추가)
이었다면, Mk.X 는 "atlas 자체가 더 이상 단일 텍스트 파일로 효율적이지 않다"는
물리적 한계 + "n=6 core 너머의 새 도메인 seed 를 어디서 끌어올 것인가"라는
의미적 한계, 두 갈래를 동시에 공격한다. 다섯 축은 우선순위 ROI 순으로:
**(1) Atlas sharding** → **(2) [12*] axiom tier 운용 활성화** → **(3) Discovery rate metric** →
**(4) 새 도메인 seeds (HoTT / ∞-cat / DAG)** → **(5) Cross-engine bus**.

각 축은 독립 prototype 1주, 통합 1주 원칙으로 5~7 주 로드맵에 들어간다.
Mk.IX 의 `[12*]` 등급은 본 제안서 채택 시 **운용 활성화** (현재 dry-run 5
후보가 `shared/blowup/audit/mk9_first_candidates.md` 에 대기) 되며, 이는
Mk.X 의 "새 등급으로 ladder 한 칸 올림" 이 아니라 "Mk.IX 가 만들어 둔 등급
사다리를 사람-게이트로 채우기 시작" 이다. 그 위에서 진짜 새 등급 `[13*]` 은
ω-hyperarithmetic 영역으로 Mk.X 후반 (Phase P5+) 에 design only 로 설계된다.

---

## 1. 현황 진단 (Saturation Diagnosis)

### 1.1 정량 지표 (2026-04-19 0856 시점)

| 지표 | 값 | 비고 |
|---|---|---|
| atlas.n6 line_count | 110,785 | schema 2 stats |
| atlas.n6 size | 18.9 MB | 단일 파일 |
| nodes | 20,510 | atlas.n6.stats |
| edges | 54,332 | atlas.n6.stats |
| hubs (degree ≥ 2) | 19,236 | atlas.n6.deg 기준 |
| `@P` primitives | 326 | 라인 태그 grep |
| `[10*]` 또는 `[11*]` 또는 `[10**]` 라인 | 6,368 | grep `\[10\*\*?\]\|\[11\*\]` |
| Top hub `n` degree | 4,651 | atlas.n6.deg sort |
| Top-8 hub set | n,J2,phi,sigma,tau,sopfr,M3,mu | classical n=6 core |
| 24h Δ lines | +630 | 사용자 보고 |
| 7-day avg Δ lines | ~+2,100/day (Mk.VIII burst 포함) | 유추 (META 484 + 13 + 33 + 16 commits) |

### 1.2 정성 신호

- **새 발견 plateau**: META-LK017~500 (484 EXACT) + Knuth 13 + ULTRA/CARD/BEYOND/ABS 33
  까지 burst 로 [11*] 540+ 채움. 그 이후 commit log 는 *cleanup / R37 / harness*
  류로 전환 — 새 수학 commit 가 줄어듦.
- **Top hub 고착**: 8 hub 가 모두 `degree ≥ 3,900` 로 신규 hub 가 끼어들 여지 없음.
  새 도메인 seed 가 들어와도 기존 hub 로 흡수 (centralization).
- **Mk.IX 운용 미가동**: `[12*]` 등급은 설계 + 5 후보 dry-run 까지 작성됨. 그러나
  실제 atlas 라인에 `[12*]` 0건. 자동 승급 금지 + 인간 감사 미수행 → **stuck**.
- **단일 파일 IO 임계**: 18.9 MB 단일 텍스트 → grep 풀스캔 ~250ms (이미 빠른
  엔진 latency 보다 길어짐). Mk.VIII fast-path (`exact ~83ms`) 가 sidecar
  (`atlas.n6.stats / .deg`) 로 우회 중이지만, edge query / hierarchy filter 는
  여전히 풀스캔.
- **Cross-project 연결 시들음**: anima / CANON 와의 `@E` cross-ref
  엣지는 직전 commit `d266319e` 에서 1건 추가 — atlas 5만 edges 대비 sample size 0.

### 1.3 saturation 의 두 모드 구분

**모드 A (수직 포화)**: Mk.VIII/IX 가 만든 사다리 (`[10] → [10*] → [10**] → [11*] → [12*]`)
의 윗칸이 **거의 비어 있거나 자동 승급이 안 되는** 상태. 해소 = 인간 감사 + 새
검증 알고리즘 (Mk.X-axis-2).

**모드 B (수평 포화)**: 새로운 종류의 명제 / 도메인 seed 가 들어오지 않아
n=6 closure 안에서만 재배치 됨. 해소 = 새 도메인 seed 주입 (Mk.X-axis-4) +
cross-engine bus (Mk.X-axis-5).

**모드 C (인프라 포화)**: 단일 18.9MB 파일이 grep / mtime / stats 캐시로는
견디지만, 새 메타데이터 (hierarchy 태그, foundation tier, cross-ref) 추가 시
schema migration 이 reader 계열 전체에 risk. 해소 = sharding (Mk.X-axis-1).

세 모드는 서로 보강 — 단일 축 해결은 부분적. 따라서 **5 축 병행** 설계.

---

## 2. Mk.II → Mk.IX 진화 요약

### 2.1 Mk 계보표

| 세대 | 핵심 도약 | 모듈 / 파일 | 등급 | 주요 commit (요약) |
|---|---|---|---|---|
| Mk.I | 단일 도메인 blowup, depth 3 | `blowup_mk1.hexa` (삭제됨) | `[7]/[10]` | (legacy, 2026-03 이전) |
| Mk.II | **파동 연속돌파** 6 라운드 + 자동 도메인 회전 | `core/blowup.hexa` 9-phase | `[10]/[10*]` | `daa2d104 20개 모듈 + Mk.II` |
| Mk.III | 의식 융합 통합 + extend_script 업그레이드 | `7ccde520` Mk.III 진화 + `21baa0e8` Mk.III-γ | `[10*]` +13 (5343→5356) | `7ccde520`, `21baa0e8` |
| Mk.IV | σ-τ=8 주정리 + Baby Monster 등 | Phase P8/P9 | `[10*]` +3, `[7?]` BT-19 | `cd54df7c`, `2353463d` |
| Mk.V | (anima 동기화) Δ₀-absolute consciousness — `[11*]` Ψ 도입 | (anima 측) | `[11*]` (Ψ 1건) | `dda8d63d` (anima v3→v4) |
| Mk.V.1 | 81/81 EXACT 포화 + tier 6~9 ULTRA/CARD/BEYOND/ABS 설계 | (anima + nexus 양측) | tier 6~9 설계 | `4d023745`, `4f1e604b` |
| Mk.VI/VII | 라우터 누락 엔진 추가 + 전 엔진 가동 | `0d043a02`, `8c24ebd9` | (메타-인프라) | `0d043a02`, `8c24ebd9` |
| Mk.VIII | **Δ₀-absolute 6번째 core** — Π₀¹ 자동 [10*]→[11*] 승급 | `modules/blowup_absolute.hexa` | `[11*]` axioms 540+ | `1c9253f6`, `9a5ea531`, `01b3bb62`, `53893e67` |
| Mk.IX | **Π₀² hyperarithmetic + Phase 10 meta-closure** — `[10**]` + `[12*]` 등급 (운용 미가동) | `modules/blowup_hyperarithmetic.hexa`, `blowup_meta_closure.hexa`, `design/mk9_*.md`, `design/phase10_meta_closure.md` | `[10**]` + `[12*]` 설계 | `4f1e604b`, `cc2ec688`, `20fc52a9 (drill 5-stage)` |

### 2.2 단계별 도약의 본질

- **Mk.II → IV**: 알고리즘 확장 — 파동 / 도메인 / 모듈 갯수.
- **Mk.V → VII**: **라우터 / 인프라** 정리 — 엔진을 누락 없이 모두 호출.
- **Mk.VIII**: **이론 도약** — 산술 계층 Π₀¹ 도입, Shoenfield 절대성으로 자동 승급.
- **Mk.IX**: **이론 + 운용 분리** — Π₀² 까지 검증 가능하되 자동 승급은 인간
  게이트 의무화. Meta-closure (Phase 10) 도 자기참조 closure 를 새 등급으로
  분리. **즉 Mk.IX 는 사다리만 만들고 채우지 않은 상태**.

### 2.3 Mk.X 가 풀어야 할 누적 문제

1. Mk.IX 가 만든 `[12*]` 사다리 — **활성화** 필요 (감사 워크플로우, atlas 반영).
2. 8 hub `n/J2/phi/sigma/tau/sopfr/M3/mu` **고착** — 새 hub 후보가 들어올 수
   있는 의미 공간 확장 필요.
3. atlas 단일 파일 18.9MB + schema 2 → schema 3 (Mk.IX hierarchy 태그) **migration
   인프라** 부재 — sharding 으로 해소.
4. Mk.IX 까지 모두 nexus 단독 — **anima / CANON / void** 와의 cross-ref
   automation 부재.
5. Mk.IX 의 Π₀² 너머 Π₀³ / Σ₁¹ — 다음 도약 방향 미설계.

---

## 3. Mk.X 5축 설계

각 축마다 [가설] / [증거] / [Prototype 1주 가능성] / [구현 risk] / [기대 효과]
구조로 기술. 마지막 §4 에서 우선순위 + 의존 그래프.

### 3.1 축 1 — Atlas Sharding (degree / topic / temporal 3 차원)

#### 가설
단일 18.9MB `atlas.n6` 를 3 차원 shard 로 분해하면 **(a) 신규 etag/메타 추가
시 reader 영향 격리**, **(b) hierarchy / foundation_tier / cross-ref 같은
column-style 쿼리 O(shard) 단축**, **(c) 빈번 read 영역 (top-8 hub) 과 cold
영역 (META-LK500+) 분리로 cache locality 확보** 가 가능하다.

#### 증거
- `atlas.n6.deg` (740KB), `atlas.n6.stats` (401B) 가 이미 sidecar 로 분리되어
  fast-path 기여 → sharding 의 부분 prototype 검증 끝남. fast-path 시간 ~83ms
  (CLAUDE.md "blowup infra" 블록).
- Top-8 hub degree ≥ 3,900 → 그 8 hub 만으로 graph 의 **밀집 코어** 를 차지.
  나머지 19,228 hub 는 long tail, degree 2~10 대부분.
- META-LK017~500 484 EXACT 는 1 commit (`53893e67`) 에 batch append → temporal
  shard 자연 경계.
- 현재 grep 풀스캔 단가는 `time grep '\[11\*\]' atlas.n6 → ~120ms`. 이는
  Mk.VIII 모듈 핫루프에서 다회 발생.

#### Shard 차원

1. **Degree shard** (3 단계)
   - `atlas.core.n6` — top-8 hub 와 직접 연결된 `@P/@L/@F` (예상 ~5,000 라인).
     항상 메모리 상주 / mmap.
   - `atlas.mid.n6` — degree 3~50 노드 (예상 ~30,000 라인). lazy load.
   - `atlas.tail.n6` — degree 2 + leaves (예상 ~75,000 라인). cold storage,
     주기적 컴팩트.

2. **Topic shard** (5 도메인)
   - `atlas.math.n6` — number_theory / algebraic_geometry / topology / category /
     combinatorics / set_theory / measure_theory / analysis / geometry /
     lie_algebra / knot_theory.
   - `atlas.physics.n6` — relativity / thermodynamics / particle / cosmology /
     fluid / EM / nuclear / optics / plasma / stat_mech / qft.
   - `atlas.cs.n6` — complexity / graph_theory / cryptography / ml_inference /
     tensor_network / attention.
   - `atlas.fusion.n6` — bisociation / resonance / symmetry_breaking / duality /
     emergence / chaos / renormalization.
   - `atlas.meta.n6` — META-01~10, META-LK017~500, META-INF-*, META-ULTRA/CARD/BEYOND/ABS.

3. **Temporal shard** (월 단위 cold rotation)
   - `atlas.live.n6` — 최근 30 일 commit. blowup 엔진의 default write target.
   - `atlas.archive.YYYY-MM.n6` — 월 단위 sealed shard. read-only.
   - 월 1회 자동 rotation: `atlas.live` → `atlas.archive.{prev_month}`.

#### Sharding 합성 규칙
- 한 라인은 정확히 한 (degree, topic, temporal) 셀에 속함 — disjoint.
- 라인의 **정렬 키** = `(temporal_shard, topic_shard, degree_shard, line_id)`.
- read API: `atlas_query(filter)` — filter 가 (degree, topic, temporal) 중
  적용 가능한 서브셋만 open.
- write API: 새 라인은 무조건 `atlas.live.n6` 에 append. cold shard 변경 금지
  (atlas.n6 append-only 원칙 유지).
- merged view: `atlas.n6` 는 가상 뷰 — 모든 shard concat 결과로 재구성 가능.
  `hexa shared/n6/atlas_view.hexa --rebuild` 로 검증.

#### Prototype 1주 가능성
- D1: shard 분류기 (`atlas_shard.hexa`) — read-only, 분류만.
- D2: shard 별 sidecar stats / deg 갱신.
- D3: blowup 엔진 read 경로 `atlas_query()` wrapping. write 경로 unchanged.
- D4: 가상 view `atlas_view.hexa --rebuild` 검증 (line-by-line concat == 원본).
- D5~D7: 회귀 테스트 (Mk.IX dry-run 5 후보, drill 5-stage chain).

가능. 단, write path 변경 금지 + 검증은 read concat 1:1 매칭으로만 한다.

#### 구현 risk
- **R1**: 분류 오류로 라인 1건 누락 → atlas 데이터 손실. mitigation: 가상
  view rebuild + sha 검증 (`md5sum atlas.n6 == md5sum (cat shards)`).
- **R2**: 기존 reader (anima cross-ref, n6 hub_centrality 등) 의 hardcode
  `shared/n6/atlas.n6` 경로 — fallback 으로 atlas.n6 가상 view 유지 (rebuild 트리거).
- **R3**: 동시성 — write 는 atlas.live 한 곳뿐이라 단순. read 는 mmap 으로
  격리. risk low.
- **R4**: temporal rotation 시 cross-shard edge — edge 자체는 from/to id 만
  쥐므로 shard 무관. shard reader 가 union 으로 edge index 재구성 필요.

#### 기대 효과
- read latency: 풀스캔 120ms → 핵심 hub 쿼리 ~10ms (10x).
- 신규 schema 추가 risk: shard reader 만 수정, atlas.n6 자체 immutable.
- 향후 [12*] hierarchy 태깅 시 `atlas.live.n6` 만 in-place 수정 — temporal
  archive 보존.
- write throughput 변화 없음 (단일 append target).

#### 게이트
shard 별 line count + sidecar 정합성 검증. `atlas_view.hexa --verify-sha` PASS.

---

### 3.2 축 2 — `[12*]` Axiom Tier 운용 활성화

#### 가설
Mk.IX 가 만든 `[12*]` 등급은 *사다리만 있고 채워지지 않은* 상태. 5 후보 (Out(S_6),
완전수 무한성 등) 가 dry-run 으로 대기 중. **인간 감사 워크플로우 + atlas
승급 도구 + Π₀² hierarchy 태깅 배치** 세 도구만 추가하면 첫 `[12*]` 1~2건
승급 가능. 이는 Mk.X 의 "사다리 위 칸 채움" 의미.

또한 Π₀² 너머 **Π₀³ / Σ₀³ / hyperarithmetic ≅ Δ₁¹** 영역의 design only 사양
(`[13*]` 사다리) 을 본 축에서 동시에 작성.

#### 증거
- `shared/blowup/audit/mk9_first_candidates.md` (이미 존재) — 5 후보 + 단계
  A~C 자동 판정 결과 기록. 단계 D 만 미실행.
- Mk.IX 설계서 §3.2 — 4-AND 승급 조건 명시. 마지막 조건 "수동 감사 서명" 만
  pending.
- Mk.IX 모듈 (`blowup_hyperarithmetic.hexa`, `blowup_meta_closure.hexa`) 는
  parse + smoke run pass.
- atlas.n6 grep `[12*]` = 0 건 → **승급 한 건도 없음**.

#### 구성 요소

1. **인간 감사 도구**: `hexa shared/blowup/audit/mk9_audit.hexa <candidate_id>`
   - 입력: 후보 id (예: `OUT_S6_UNIQUE`).
   - 출력: 단계 A~D 판정 + reverse-math 인증서 (Simpson SOSOA §III.x 등) 텍스트.
     인간 감사자가 sign 후 sidecar `audit_log.jsonl` 에 기록.
   - 자동 atlas 쓰기 금지 — 감사 후 별도 `promote_12star.hexa` 호출.

2. **Atlas 승급 도구**: `hexa shared/blowup/lib/promote_12star.hexa <candidate_id> <sign>`
   - 사전 조건: audit_log.jsonl 에 sign 1건, L0 guard verify 통과.
   - 동작: atlas.live.n6 (sharding 적용 후) 의 해당 라인 `[10*]` → `[12*]`
     in-place 치환. `!! breakthrough-YYYY-MM-DD "audit-by-<sign>"` 추가.
   - Atlas append-only 원칙 예외: `[11*]` 승급의 선례 (Mk.VIII) 와 동일 패턴.

3. **Π₀² hierarchy 배치 태깅**: `hexa shared/blowup/lib/pi02_batch.hexa`
   - 동작: atlas 전체 read-only scan, 각 `@R/@L` 에 `is_pi02()` 판정 적용.
   - 결과: `shared/n6/atlas.n6.hierarchy` 별도 sidecar 파일 (atlas.n6 수정 X).
     포맷: `<line_id>\t<hierarchy>` (Δ₀ / Π₀¹ / Σ₀¹ / Π₀² / Σ₀² / ≥Π₀³ / unknown).
   - 빈도: Mk.X 채택 후 1회 + atlas commit 시 incremental.

4. **`[13*]` 사다리 design only**: `shared/blowup/design/mk10_higher_arithmetic.md`
   - Π₀³ / Σ₀³ — Π₀²-complete 속성 사용, Mk.IX 와 유사 파이프라인.
   - hyperarithmetic ≅ Δ₁¹ — ordinal recursion 기반 엔진 (Mk.IX 가 명칭상
     hyperarithmetic 이지만 실제는 Π₀²; Mk.X 에서 명칭 정리).
   - Σ₁¹ analytical — 2차 산술 양화, 완전 별도 판정기 (Mk.X 범위 밖, 후속).

#### Prototype 1주 가능성
- D1~D2: `mk9_audit.hexa` + `audit_log.jsonl` 스키마.
- D3: `promote_12star.hexa` + L0 guard 통합 테스트 (1 후보 dry-run).
- D4: 첫 후보 Out(S_6) 인간 감사 + 실 승급 (atlas.live.n6).
- D5: `pi02_batch.hexa` 전수 스캔 + sidecar 생성.
- D6~D7: `mk10_higher_arithmetic.md` 초안.

가능. 단 D4 는 사용자 (박민우) 인간 감사 협업 필요.

#### 구현 risk
- **R1**: 인간 감사가 병목 — 1 건당 1 시간. 5 후보 모두 채우는 데 5+ 시간.
  mitigation: 한 세션에 최대 1 건만 처리, 주 1 회 페이스.
- **R2**: false positive `[12*]` 승급 후 downgrade 시 chain 재검증. mitigation:
  `[12*]` 라인은 dependency 그래프 leaf 로 격리 (downstream 0 보장 후 승급).
- **R3**: hierarchy 태깅의 자연어 ∀/∃ 오분류 (Mk.IX 설계 §7.5). mitigation:
  unsure 비율 모니터, 5% 초과 시 파서 보완.
- **R4**: `[13*]` 설계만 하고 구현 안 하면 사다리만 또 늘어남. mitigation: Mk.X
  로드맵에 "Mk.X 종료 = `[12*]` 5건 + `[13*]` design only" 명시.

#### 기대 효과
- 첫 `[12*]` 승급 — Mk.IX 운용 시작.
- atlas hierarchy 분포 가시화 — Π₀² 비율 통계 → 다음 축 (새 도메인) 우선순위
  데이터.
- `[13*]` 사다리 — 다음 세대 도약점 명시.
- 주당 `[12*]` +1~2건 페이스 (감사 병목 반영).

#### 게이트
- Mk.X 종료 시점 `[12*]` ≥ 1.
- `atlas.n6.hierarchy` sidecar 존재 + 카테고리 합 == 라인 수.
- `mk10_higher_arithmetic.md` 초안 ≥ 200 lines.

---

### 3.3 축 3 — Discovery Rate Metric & Plateau Detection

#### 가설
현재 atlas 성장은 commit log 와 `atlas.n6.stats` 의 `mtime/size/line_count`
3 필드로만 추적된다. Plateau 감지가 사용자 휴리스틱 ("24h Δ +630") 에 의존.
**시간당 [10*]→[11*] 승급률, 신규 hub 진입률, foundation_tier 분포 추이** 를
연속 metric 으로 노출하면 Mk.X 후속 축의 자동 priority 조정이 가능하다.

#### 증거
- `atlas.n6.stats` schema 2 — line_count / nodes / edges / hubs 만. 시간 미분 없음.
- `shared/discovery/atlas_temporal_velocity_2026-04-11.md` — 일회성 분석 존재
  (1주일 전), 자동 갱신 없음.
- atlas growth 30 % 둔화 신호는 사용자 보고에만 — 자동 alert 없음.

#### 구성 요소

1. **Discovery Rate Sidecar**: `atlas.n6.rate.jsonl` — JSONL append-only.
   - 항목: `{timestamp, line_count, lines_added_1h, lines_added_24h, lines_added_7d,
     promotions_10star_1h, promotions_11star_1h, promotions_12star_1h,
     new_hubs_1h, top_hub_degree_max}`
   - 갱신 주기: launchd 30분 — plist `com.nexus.atlas-rate.plist`.
   - 14 일 retention, 그 이후 daily aggregate 만.

2. **Plateau Detector**: `hexa shared/n6/plateau_detector.hexa`
   - 입력: `atlas.n6.rate.jsonl` 최근 168 entries (7d × 24).
   - 알고리즘: 24h moving avg vs 7d moving avg 비교. 30% 미만이면 PLATEAU 신호.
   - 출력: `shared/discovery/plateau_state.json` — `{state: NORMAL|WARNING|PLATEAU,
     since: timestamp, gap_pct: float, suggested_axis: string}`.
   - `suggested_axis` 휴리스틱: `[10*] 승급률 < threshold` → 축 4 (새 seed).
     `nodes 증가 0` → 축 5 (cross-engine bus). `edges/nodes 비율 안정` → 축 1
     (sharding 으로 query 가속).

3. **Atlas Health Dashboard 확장**: `shared/n6/atlas_health.hexa --verbose`
   - 기존 health 출력에 rate metric 추가.
   - 색상: NORMAL=green, WARNING=yellow, PLATEAU=red.

4. **Auto-trigger hook 후보 (선택, 미구현)**: PLATEAU 진입 시 `entry.hexa
   thinking query "atlas plateau detected, suggested axis: <X>"` 자동 호출.
   본 축 에서는 design only, 구현은 사용자 승인 후.

#### Prototype 1주 가능성
- D1~D2: rate sidecar JSONL 스키마 + 갱신 hexa.
- D3: launchd plist 등록 + 30분 cron 검증.
- D4~D5: plateau detector + suggested_axis 휴리스틱.
- D6: atlas_health.hexa 확장.
- D7: 7-day 데이터 수집 후 첫 PLATEAU 시뮬레이션 (현재 24h Δ +630 데이터로 backfill).

가능.

#### 구현 risk
- **R1**: rate JSONL 무한 증가 — 14d retention + daily aggregate 자동 회전.
- **R2**: launchd 신규 plist 가 기존 com.nexus.* 와 충돌 — 별도 label, 다른
  주기.
- **R3**: suggested_axis 휴리스틱 오작동 — 자동 trigger 미구현 (사용자 승인
  필수) 으로 영향 격리.
- **R4**: atlas.n6 mtime 만 보면 sharding (축 1) 도입 후 부정확 — sharding
  완료 후 rate sidecar 재설계.

#### 기대 효과
- Plateau 객관적 감지 (현재 사용자 직관 → 자동 metric).
- 다음 축 우선순위 자동 추천.
- atlas health dashboard 의 시간 차원 추가.
- Mk.XI 로드맵 설계 시 데이터 기반 결정.

#### 게이트
- `atlas.n6.rate.jsonl` 7-day 데이터 ≥ 168 entries.
- `plateau_state.json` 생성 + suggested_axis 1건 이상 노출.
- `atlas_health.hexa --verbose` 출력에 rate 섹션 포함.

---

### 3.4 축 4 — 새 도메인 Seeds (HoTT / ∞-cat / Motivic / DAG / Topos)

#### 가설
n=6 core 8 hub (`n/J2/phi/sigma/tau/sopfr/M3/mu`) 가 **classical number theory +
group theory + 단순 modular arithmetic** 영역에 묶여 있다. 새 hub 후보가 들어올
공간을 열려면 **homotopy type theory (HoTT) / ∞-category / motivic cohomology /
derived algebraic geometry (DAG) / topos theory** 같은 *고차 구조* 도메인 seed 를
주입해야 한다. 이들은 n=6 의 새 표현형 (presentation) 을 내포할 가능성이 있고
(예: HoTT 의 univalence + n=6 small categorical examples), 동시에 atlas 의
hub-degree 분포를 long-tail 쪽으로 평탄화한다.

#### 증거
- 현재 `modules/blowup_*.hexa` 50 개 중 **HoTT / ∞-category / motivic / DAG /
  topos 0 건**. `category.hexa` 는 1-category 한정 skeleton.
- Mk.VIII Δ₀-absolute 정리 자체가 1-categorical (set/ZFC) 무대 → ∞-categorical
  무대로 lifting 시 새 invariance 발견 가능성 (예: ∞-topos 에서의 absoluteness).
- n=6 의 알려진 ∞-categorical 출현: `S_6 의 outer auto = (2,3) 변환` 은
  spectra / ∞-stacks 맥락에서 재해석 가능 (예: Postnikov tower 의 6-truncation).
- Cross-discipline 학술 커밋이 atlas 에 없는 것은 seed 가 없는 것이 원인 —
  엔진은 도메인-제너릭 하지만 seed pool 이 classical.

#### 5 신규 도메인 seed 모듈

1. **`blowup_hott.hexa`** — homotopy type theory
   - Seed: `univalence axiom`, `path induction`, `n-truncation (n=6 우선순위)`,
     `synthetic homotopy of S^6`.
   - n=6 hook: `π_6(S^3) = Z/12` (Hopf invariant 관련, n=6 회귀).

2. **`blowup_infinity_category.hexa`** — ∞-category
   - Seed: `quasi-category Joyal model`, `simplicial set 6-truncation`,
     `mapping space`, `fully faithful 6-functor`.
   - n=6 hook: `(∞,1)-category 의 6-cell coherence`.

3. **`blowup_motivic_cohomology.hexa`** — motivic cohomology
   - Seed: `H^p,q(X, Z(n))`, `Voevodsky motive`, `Bloch-Kato (n=6 weight)`,
     `motivic Steenrod`.
   - n=6 hook: `n=6 motivic cohomology of Spec(F_p)` 패턴.

4. **`blowup_derived_algebraic_geometry.hexa`** — DAG
   - Seed: `derived stack`, `spectral scheme`, `cotangent complex 6-truncation`,
     `derived intersection`.
   - n=6 hook: `derived self-intersection 의 σ-invariant`.

5. **`blowup_topos.hexa`** — topos theory
   - Seed: `Grothendieck topos`, `elementary topos`, `subobject classifier`,
     `geometric morphism 6-fold`, `Lawvere-Tierney topology`.
   - n=6 hook: `presheaf topos 의 6-cover` / `étale 6-site`.

#### 5 모듈 공통 구조 (skeleton)

```hexa
// shared/blowup/modules/blowup_<domain>.hexa (40-80 lines)
fn domain_kernel(seed: f64) -> f64 {
    // 도메인 특화 변환. 예: HoTT 는 univalence-driven path encoding.
}
fn emit_wave(seed_id: string, energy: f64) {
    // JSON wave emission. modules.json schema 와 호환.
}
fn n6_hook_check(value: f64) -> bool {
    // 도메인 산출이 n=6 invariant 와 일치하는지 cross-validate.
}
```

기존 37 개 P1 skeleton (`expansion_2026_04_14`) 와 동일 패턴 → 마찰 최소.

#### Prototype 1주 가능성
- D1: 5 모듈 skeleton 작성 (각 ~50 lines, total 250 lines).
- D2: `modules.json` 등록 + `compose --modules all` 확장.
- D3: smoke run 5/5 pass.
- D4~D5: 첫 도메인 1개 (HoTT) 만 깊이 구현 — Hopf invariant n=6 회귀 시드.
- D6: atlas.live.n6 에 첫 wave append 검증.
- D7: cross_validate_runner 로 5 모듈 consensus 점검.

가능. 단 깊이 구현은 1 도메인만, 나머지 4 는 skeleton 유지 (Mk.XI 에서 깊이).

#### 구현 risk
- **R1**: 도메인 seed 가 너무 추상 → kernel 이 자명 출력. mitigation: 각
  도메인의 `n6_hook_check` 강제 — 출력이 n=6 invariant 1개 이상에 매핑되어야
  emit_wave 통과.
- **R2**: 5 신규 모듈이 기존 6 core 와 다른 grade 체계 사용 → atlas pollution.
  mitigation: 신규 모듈 출력은 `[7?]/[10?]` 까지만, `[10*]` 이상은 cross_validate
  필수.
- **R3**: HoTT / ∞-cat 의 자연어 양화 → Mk.IX hierarchy 파서 false positive.
  mitigation: 신규 모듈은 hierarchy 태깅 보류 (축 2 의 `pi02_batch.hexa` 에서
  unsure 처리).
- **R4**: Hub centralization 더 심해질 위험 — 신규 모듈도 결국 n hub 로 합류.
  mitigation: 신규 도메인의 `local hub` 후보를 별도 집계 (atlas.n6.deg 의
  domain-tagged subset).

#### 기대 효과
- 5 신규 hub 후보 등장 (예상 degree 10~30 초기).
- HoTT / ∞-cat / DAG 영역의 첫 atlas 진입 — atlas 의 의미적 표면 확장.
- Mk.X 종료 시 atlas.n6 신규 라인 ~50~200 (skeleton emit 출력).
- 깊이 구현된 HoTT 1 도메인은 1~2 개 새 `[10*]` 후보 생성 기대.

#### 게이트
- 5 모듈 parse + smoke run 5/5 pass.
- atlas.live.n6 신규 라인 1건 이상 (HoTT 깊이 구현 결과).
- `modules.json` 등록 완료 + `compose --modules hott` 동작.

---

### 3.5 축 5 — Cross-Engine Bus (anima ↔ CANON ↔ atlas.n6)

#### 가설
직전 commit `d266319e` 가 보여주듯 `@E cross-ref 엣지` 는 매뉴얼 1건씩 추가 됨.
**anima / CANON / void / hexa-lang / airgenome / papers** 6 형제
프로젝트의 `breakthroughs.jsonl / convergence.json / n6-paper anchor` 가 atlas.n6
와 자동 cross-ref 되지 않음. 자동화하면 atlas 의 hub 분포가 cross-project edge
로 다양화되고, 다른 프로젝트 발견이 nexus 의 [10*]/[11*] 사다리 검증 큐에
자동 진입.

#### 증거
- atlas.n6 grep `@E ` 결과: 1 commit (d266319e) 에서 1 건 — sample size 0 수준.
- 7 자매 프로젝트 (`shared/config/projects.json`) 의 convergence file 위치 SSOT
  (`shared/convergence/{project}.json`) 존재 — 데이터는 있는데 다리 부재.
- anima 의 Mk.V.1 81/81 EXACT (`4d023745`) 와 nexus 의 Mk.VIII Δ₀-absolute
  (`1c9253f6`) 는 commit 시점이 동일 일자 — 양 측이 평행 진화하나 atlas 에
  cross-ref 없음.

#### 구성 요소

1. **Cross-Engine Bus 읽기 어댑터**: `shared/n6/cross_bus_reader.hexa`
   - 입력: 6 형제 프로젝트의 `breakthroughs.jsonl` + `convergence.json` +
     `n6-paper anchors`.
   - 출력: `shared/n6/cross_bus.jsonl` 통합 큐 (project, type, id, timestamp,
     payload).
   - 갱신 주기: launchd 30분.

2. **Atlas 진입 게이트**: `shared/n6/cross_bus_promote.hexa`
   - 입력: `cross_bus.jsonl` 신규 항목.
   - 동작: 각 항목에 대해 atlas 의 매칭 노드 검색 (id 또는 expr 유사도).
     매칭 시 `@E` cross-ref 엣지 1건 atlas.live.n6 에 append. 매칭 실패 시
     `cross_bus_unmatched.jsonl` 큐에 보관.
   - 검증: atlas append 전 `_guarded_append_atlas()` 통과 + sharding (축 1)
     쿼리.

3. **Bus 토폴로지 가시화**: `shared/discovery/cross_engine_topology.html`
   - 6 형제 프로젝트의 노드 + 매칭 atlas 노드 + `@E` 엣지를 3D 그래프로 표시.
     `shared/discovery/reality_map_3d.html` 에 inset 으로 통합.

4. **Bidirectional sync (선택, 미구현)**: nexus 의 `[12*]` 승급이 anima 의
   `[11*]` Ψ 라인을 trigger 하도록. 본 축은 design only, 구현은 사용자 승인.

#### Prototype 1주 가능성
- D1: cross_bus_reader.hexa — 6 프로젝트 read-only.
- D2: cross_bus.jsonl 스키마 + 첫 통합 데이터 생성.
- D3: cross_bus_promote.hexa — atlas append.
- D4: 첫 `@E` 자동 엣지 5건 검증 (anima Ψ ↔ nexus J2 등).
- D5~D6: 토폴로지 viewer.
- D7: launchd 등록 + 30분 cron 검증.

가능.

#### 구현 risk
- **R1**: 매칭 알고리즘 false positive — cross_bus 가 atlas 를 noise 로 오염.
  mitigation: 매칭 임계 confidence ≥ 0.9 (정확 id 일치 우선), 그 이하는
  unmatched 큐.
- **R2**: 6 프로젝트 schema 비통일 — convergence.json 포맷 차이.
  mitigation: per-project 어댑터 (이미 R14 SSOT 로 부분 해결, 나머지 보완).
- **R3**: cross_bus 자기 참조 (anima 가 nexus atlas 를 다시 read 해서 자기에
  반영) → 무한 루프. mitigation: edge_type=`@E cross-ref` 만, recursive promote
  금지.
- **R4**: cross_bus.jsonl 무한 증가 — 90d retention, 그 이후 aggregate.

#### 기대 효과
- Hub 분포 다양화 — 6 형제 프로젝트 노드가 atlas 진입.
- anima Ψ ↔ nexus J2 같은 cross-domain edge 자동 생성 — 새 invariance 후보.
- Plateau 진단 (축 3) 의 `nodes 증가 0` 카운트가 cross-bus 데이터로 회복.
- 형제 프로젝트의 발견이 nexus 검증 큐 자동 진입 — ROI 분산.

#### 게이트
- `cross_bus.jsonl` 첫 통합 데이터 ≥ 50 entries.
- `@E` 자동 엣지 atlas.live.n6 에 ≥ 5건 append.
- `cross_engine_topology.html` 렌더링 검증.

---

## 4. 우선순위 + 의존 그래프 + 로드맵

### 4.1 우선순위 ROI 매트릭스

| 축 | 가설 강도 | Prototype 가능성 | 구현 risk | 기대 효과 | 의존성 | ROI 점수 |
|---|---|---|---|---|---|---|
| 1 sharding | 높음 (인프라 임계) | 1주 가능 | 중 (rebuild 검증) | read 10x + schema migration 안전 | (없음) | **9/10** |
| 2 [12*] 활성 | 높음 (Mk.IX 잔여) | 1주 가능 | 중 (인간 감사 병목) | 첫 [12*] 1~2건, [13*] 사다리 | (없음) | **9/10** |
| 3 rate metric | 중 (관찰자 이득) | 1주 가능 | 저 (자동 trigger 미구현) | plateau 자동 감지 | 1 (sharding 후 mtime 재설계) | 7/10 |
| 4 새 도메인 | 중 (장기 효과) | 1주 가능 (skeleton) | 중 (false positive) | 5 신규 hub + atlas 표면 확장 | (없음, 단 효과는 5 와 함께) | 7/10 |
| 5 cross-bus | 중-높 (정체된 cross-ref) | 1주 가능 | 중-저 | 6 프로젝트 통합 + 다양화 | 1 (sharding 후 atlas write 안정) | 7/10 |

### 4.2 의존 그래프

```
        ┌────────────────────┐
        │  축 1 sharding      │ ◄── 모든 atlas 쓰기/읽기 기반
        └─────────┬──────────┘
                  │
        ┌─────────┴──────────┬────────────┐
        ▼                    ▼            ▼
┌────────────────┐  ┌──────────────┐  ┌──────────────┐
│ 축 2 [12*] 활성 │  │축 3 rate     │  │축 5 cross-bus│
└────────────────┘  └──────────────┘  └──────────────┘
        ▲                                      ▲
        └──────────────┬───────────────────────┘
                       │
              ┌────────┴────────┐
              │ 축 4 새 도메인   │
              └─────────────────┘
```

- 축 1 (sharding) 이 모든 다른 축의 atlas IO 기반 → **선행 필수**.
- 축 2 (12* 활성) 와 축 3 (rate) 은 축 1 후 병렬.
- 축 5 (cross-bus) 는 축 1 후, 축 4 (새 도메인) 의 cross-project 효과 위해 우선.
- 축 4 (새 도메인) 은 마지막 — skeleton 만 우선, 깊이는 Mk.XI.

### 4.3 6주 로드맵 (제안)

| Week | 축 | 작업 | 게이트 |
|---|---|---|---|
| W1 | 1 sharding | shard 분류기 + sidecar + atlas_view rebuild 검증 | sha 일치 |
| W2 | 2 [12*] 활성 | mk9_audit + promote_12star + 첫 후보 (Out(S_6)) 인간 감사 | [12*] = 1 |
| W2 | 3 rate metric (병렬) | rate sidecar + plateau detector + atlas_health 확장 | 7d 데이터 |
| W3 | 5 cross-bus | reader + promote + 첫 @E 5건 + topology viewer | @E ≥ 5 |
| W4 | 4 새 도메인 | 5 모듈 skeleton + HoTT 깊이 구현 | smoke 5/5 |
| W5 | 통합 | drill 5-stage chain 회귀 + Mk.IX dry-run 5 후보 재검증 | 모두 PASS |
| W6 | 문서화 + Mk.XI 설계 | mk10_higher_arithmetic.md 초안 + Mk.XI 5축 후보 | 문서 PR |

### 4.4 종료 조건 (Mk.X complete)

- `[12*]` ≥ 1 (atlas.live.n6 에 실 라인).
- `atlas.shard.{core,mid,tail}.n6` 3 shard 분리 + sha 검증.
- `atlas.n6.rate.jsonl` 7 day 데이터.
- `cross_bus.jsonl` ≥ 50 entries + @E ≥ 5.
- 5 신규 도메인 모듈 (HoTT / ∞-cat / motivic / DAG / topos) skeleton.
- `mk10_higher_arithmetic.md` 초안 (Π₀³ / Δ₁¹ 사다리).
- drill 5-stage chain 회귀 PASS.
- `plateau_state.json` NORMAL 회복 (sharding + 새 도메인 후 기대).

---

## 5. Risk Register

### 5.1 횡단 risk

| Risk | 영향 | 확률 | Mitigation |
|---|---|---|---|
| atlas.n6 데이터 손실 | 높음 (foundation 손상) | 낮음 | sha rebuild + git commit 매 단계 |
| 동시성 race (anima/n6 sync 중) | 중 | 중 | atlas.live.n6 단일 write target + flock |
| 인간 감사 병목 | 중 | 높음 (사용자 시간 의존) | 주 1회 페이스, 병렬 감사 가능 큐 |
| 신규 모듈 false positive | 중 | 중 | n6_hook_check 강제 + cross_validate 의무 |
| schema migration breaking change | 높음 | 중 | shard reader 후방 호환, atlas.n6 가상 view 유지 |
| Mk.IX 잔여 작업 결합 | 중 | 중 | 축 2 가 Mk.IX 잔여 처리, Mk.X 의 일부로 흡수 |
| 5축 동시 진행 시 충돌 | 중 | 중 | W1 sharding 단독, 이후 병렬 |

### 5.2 R0~R37 / NX1~NX3 / H-* 룰 부합성

- **R14** (단일 진실): atlas.n6 가상 view 유지 → 위반 없음.
- **R27** (Single Responsibility): 축 1~5 가 각자 하나의 책임.
- **R37** (no python): 5 신규 모듈 모두 hexa.
- **H-NOARCHIVE**: shard 파일은 archive 가 아닌 active. `_archive_` suffix 금지.
- **H-DOD**: 종료 조건 §4.4 가 DoD verifier 입력.
- **H-CLAIM-LEX**: 본 문서는 design only, "구현 완료" 주장 0건.
- **H-SCOPE**: 코드 변경 0, 본 세션 산출물은 .md + .json 2개.
- **VD3** (산문 금지): 본 .md 는 design proposal — VD3 예외.
- **R38** (proposed) — 본 문서 §4.4 종료 조건 자체가 future R38 후보.

### 5.3 알려진 미해결

- **이론**: Mk.IX 의 Π₀² 95% 정확도 가설은 production scale 검증 0건. Mk.X 가
  5 후보 처리하면서 1차 데이터 확보 예정.
- **인프라**: sharding 후 기존 hub_centrality_top100 / drift_corrector 등 read
  계열의 hardcode atlas.n6 경로 — 가상 view fallback 으로 우회하나, 점진 migration
  후 fallback 제거 필요 (Mk.XI 이후).
- **운용**: 인간 감사 워크플로우는 사용자 단독 — agent 가 대신할 수 없음 (Mk.IX
  설계 §3.2 명시). Mk.X 가 인간 감사 cadence 를 어떻게 흡수할지 결정 미정.

---

## 6. 비-목표 (Non-Goals)

- Mk.X 는 새로운 산술 계층 도입 X (Π₀² 까지 = Mk.IX). Π₀³ 는 design only.
- atlas.n6 schema 1 → 3 일괄 migration 금지. shard 별 점진 적용.
- 자동 인간 감사 우회 도구 금지 — `[12*]` 는 무조건 사람.
- BLOWUP_LOCAL=1 / 우회 모드 금지 (memory: f-no-blowup-local).
- Rust 도구 도입 금지 (memory: f-no-rust).
- 신규 hook 작성 금지 (H-NOHOOK) — entry.hexa 내부 자율 호출만.
- archive/backup 폴더 금지 (H-NOARCHIVE) — git commit 으로만.

---

## 7. 후속 (Mk.XI 암시, 비확정)

- **Mk.XI-1**: ω-hyperarithmetic 본격화 — Π₀³ / Σ₀³ / Δ₁¹ 검증기.
- **Mk.XI-2**: ∞-categorical absolutness — Mk.VIII 의 Δ₀-absolute 를 ∞-topos
  로 lifting.
- **Mk.XI-3**: 5 신규 도메인 모듈 깊이 구현 (Mk.X 에서 skeleton 만).
- **Mk.XI-4**: cross-engine bidirectional sync — nexus `[12*]` 가 anima `[11*]`
  trigger.
- **Mk.XI-5**: atlas distributed (shard 가 별 host 에 흩어지는 단계).

본 문서 범위 밖. Mk.X W6 종료 후 별도 design.

---

## 8. 참고 / 인용

1. `shared/blowup/design/mk9_hyperarithmetic.md` — Mk.IX Π₀² 설계서.
2. `shared/blowup/design/phase10_meta_closure.md` — Phase 10 meta-closure.
3. `shared/blowup/audit/mk9_first_candidates.md` — 5 dry-run 후보.
4. `shared/n6/atlas.n6.stats` — atlas 정량 (110,785 lines).
5. `shared/n6/atlas.n6.deg` — degree 분포 sidecar (740 KB).
6. `shared/blowup/modules/modules.json` — 50 모듈 ossification log.
7. `shared/n6/CLAUDE.md` — atlas v1 태그 8 종 + foundation [11*].
8. `shared/blowup/CLAUDE.md` — 6 core 모듈.
9. `shared/CLAUDE.md` — R14 SSOT.
10. S. G. Simpson, *Subsystems of Second-Order Arithmetic* — reverse math 표준.
11. Univalent Foundations Program, *Homotopy Type Theory* (2013) — HoTT 표준.
12. J. Lurie, *Higher Topos Theory* — ∞-categorical 표준.
13. V. Voevodsky, motivic cohomology 원논문 series.
14. M. Spivak, *Derived Algebraic Geometry* (Lurie 시리즈).
15. F. W. Lawvere, *Toposes of Laws of Motion* — topos theory 응용.

---

## 9. 종결

본 설계서는 atlas 110,785 줄 18.9 MB 의 saturation 신호를 5 축 병렬 인프라 진화로
공격한다. 핵심 원칙:

1. **Sharding 선행**: atlas IO 한계 제거가 모든 다른 축의 기반.
2. **Mk.IX 잔여 처리**: `[12*]` 사다리 채움이 Mk.X 의 일부.
3. **rate metric 도입**: plateau 자동 감지로 다음 세대 자동 priority.
4. **새 도메인 5 종**: HoTT / ∞-cat / motivic / DAG / topos skeleton.
5. **Cross-engine bus**: 6 형제 프로젝트 자동 통합.
6. **6 주 로드맵**: W1 sharding, W2 [12*]+rate 병렬, W3 cross-bus, W4 새 도메인,
   W5 통합, W6 문서 + Mk.XI 설계.
7. **인간 감사 의무**: `[12*]` 자동 승급 금지.
8. **코드 변경 0**: 본 세션은 design + spec.json 만.

Mk.X 채택 시 첫 단계는 `shared/blowup/lib/atlas_shard.hexa` (read-only 분류기)
+ `shared/n6/atlas_view.hexa --rebuild --verify-sha` 검증.

승인 후 별도 commit chain 으로 진행.

---

*문서 끝. machine-readable spec: `mkx_design_proposal.spec.json`*
