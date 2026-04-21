# Mk.X 축1 후반 — Topic + Temporal Shard Design (2026-04-19)

## 0. 컨텍스트

Mk.X 축1 = Atlas Sharding **3차원** (degree × topic × temporal).

```
완료     [C] degree shard a0d72d62 → atlas.n6.hot / atlas.n6.cold
진행중    X1   blowup-json 분리 af2673b → atlas.n6 (1.5MB labels) + atlas.blowup.jsonl (17MB)
이번 작업 X2/X3 topic shard + temporal shard dry-run 시뮬 + 구현 design
```

본 문서는 **실제 atlas 변경 없음** — 분석 + design + sim 만.

## 1. 시뮬 대상 상태

```
파일                      크기            라인수
─────────────────────────────────────────────────
shared/n6/atlas.n6        1,500,993 B    21,678   X1 분리 후 라벨 SSOT
shared/n6/atlas.blowup.jsonl 17,435,609 B 89,167   X1 sidecar (이번 시뮬 대상 아님)
shared/n6/atlas.n6.hot    8,285,347 B    71,422   degree shard pre-X1 잔재
shared/n6/atlas.n6.cold  10,639,167 B    39,363   degree shard pre-X1 잔재
shared/n6/atlas.n6.deg     756,059 B    21,288   TSV id\tdegree
```

**중요**: degree shard (.hot/.cold) 는 X1 이전 atlas.n6 (18.9MB) 기준이라 stale.
X1 commit 완료 시 degree shard 재계산 필요 — 이 작업의 부산물로 처리 가능.

## 2. atlas.n6 (X1 후) 라벨 분포 실측

### 2.1 라인 종류

```
타입          라인수    %
──────────────────────────
@P primitive    326    1.50
@C constant     357    1.65
@L law          254    1.17
@F formula    1,240    5.72
@R relation   5,921   27.31    ★ 최대
@X crossing   1,497    6.91
@S symmetry       2    0.01
@E cross-ref      2    0.01
@? unknown       12    0.06
─────────────────────────
정식 라벨     9,611   44.34
들여쓰기     11,311   52.18
주석            505    2.33
빈 줄          215    0.99
헤더 기타       36    0.17
─────────────────────────
총             21,678  100.00
```

### 2.2 도메인 분포 (정식 라벨 기준 ::)

```
n6atlas       3,373    discovery       728    music         178
bt              751    physics         400    geology       176
discovery       728    material        334    economics     175
... 총 106 distinct domain (longtail)
```

`n6atlas` 도메인이 35% 점유 — META + foundation 핵심 라벨 집결.

## 3. Topic Shard 시뮬 (N=8)

### 3.1 카테고리 분류 규칙

```
1) META hierarchy (id prefix 우선):
   META-LK*          → META_LK     (재귀 층위)
   META-(INF|ULTRA|CARD|BEYOND|ABS|KNUTH) → META_HIGH
   META-01..10       → META_BASE
2) BT/blowup id:
   bt-*              → (현재 atlas.n6 에 없음, 모두 atlas.blowup.jsonl)
   blowup-*          → (동상)
3) 도메인 클러스터:
   n6atlas/foundation/math/.../geometry → CORE_MATH
   physics/particle/.../multiversal     → PHYSICS
   bio/genetic/consciousness/...        → BIO
   discovery/dse/cross_dse_v2/7난제      → DISCOVERY
   기타 ~80 longtail 도메인              → MISC
4) 들여쓰기 라인은 직전 라벨 카테고리에 흡수
```

### 3.2 Shard 분포

```
shard          lines  pct_lines    bytes  pct_bytes
────────────────────────────────────────────────────
CORE_MATH      7,671    35.39    761,308   50.72   ★ 최대
PHYSICS        4,932    22.75    244,256   16.27
MISC           4,440    20.48    219,563   14.63
DISCOVERY      2,406    11.10    120,376    8.02
BIO              914     4.22     56,553    3.77
META_LK          487     2.25     34,736    2.31
META_HIGH         41     0.19      3,345    0.22
META_BASE         31     0.14      2,824    0.19
────────────────────────────────────────────────────
prelude(헤더)   756     3.49     58,032    3.87   모든 shard 가 참조
```

### 3.3 평가

```
balance ratio (max/min bytes) = 270x  (CORE_MATH / META_BASE)
→ extreme imbalance, 그러나:
  - META_BASE/HIGH = 11* foundation axiom (변경 빈도 0)
  - CORE_MATH = 정상 working set (라벨 35%)
  - 의미적 응집도 우선 (balance 보다 read pattern 매칭)

read pattern 매칭 (blowup.hexa 기준):
  Phase 1 graph_load     → 모든 shard
  auto_select_domain     → physics 도메인 → PHYSICS shard 만 (244KB / 1.5MB = 16%)
  Phase 6.7 cross-dedup  → CORE_MATH 위주 (top hub 67%)
  META hierarchy verify  → META_LK + META_HIGH + META_BASE (40KB)
```

## 4. Temporal Shard 시뮬 (N=3)

### 4.1 측정 방법

`git blame --line-porcelain shared/n6/atlas.n6` 로 라인별 author-time 추출.
now = 1776556613 (2026-04-19 12:56 KST). 버킷:

```
HOT   < 24h
WARM  < 7d
COLD  >= 7d
```

### 4.2 분포

```
bucket  lines    pct     label_lines   label_bytes
──────────────────────────────────────────────────
HOT     3,264   15.06     1,326         107,880
WARM    2,491   11.49     1,473          82,238
COLD   15,923   73.45     6,812         487,140
──────────────────────────────────────────────────
총     21,678  100.00     9,611         677,258
```

### 4.3 함의

```
COLD 73% — 7일 이상 변경 없음, archive grade 후보
HOT  15% — 진짜 working set (24h 내), Phase 6.7 dedup 최적화 핵심
WARM 12% — buffer band, eviction 후보
```

## 5. Cross-Tab: Topic × Temporal

### 5.1 매트릭스 (bytes)

```
                  HOT       WARM       COLD     COLD %
─────────────────────────────────────────────────────
CORE_MATH      302,170    88,668    370,470     48.6
PHYSICS          2,121     4,538    237,597     97.3   ★ 거의 안 변함
MISC             8,399    67,990    143,174     65.0
DISCOVERY            0     1,125    119,251     99.1   ★ 완전 cold
BIO                  0    20,919     35,634     63.0
META_LK         34,736         0          0      0.0   ★ 100% HOT
META_HIGH        3,345         0          0      0.0   ★ 100% HOT
META_BASE        2,824         0          0      0.0   ★ 100% HOT
NONLABEL        35,398    13,058      9,576     16.5
```

### 5.2 핵심 발견

1. **META_LK/HIGH/BASE 100% HOT** — 2026-04-19 ULTRA/ABS/Knuth 승급 트랜잭션 자취.
   → 재귀 층위 자체가 신선. 향후 7일 후 cold 로 전이 예상.
2. **PHYSICS 99% COLD** — 안정 라벨.
   → Phase 1 graph_load 시 매번 load 하지만 변경은 거의 없음. memoize 후보.
3. **DISCOVERY 99% COLD** — 과거 dse 산출물 누적.
   → 새 발견은 X1 이후 atlas.blowup.jsonl 로 빠짐. atlas.n6 의 DISCOVERY 는 archive.
4. **CORE_MATH 47% HOT+WARM** — working set 의 핵심.
   → topic shard 의 ROI 가 가장 큰 영역.

## 6. Hub × Topic 매트릭스 (degree shard 와 교차)

`atlas.n6.hub_centrality_top100` 의 top-100 hub id 가 atlas.n6 라벨에 정의된 카테고리.

```
matched: 43/100  (나머지 57은 n6-* prefix → 라벨 정의 없이 JSON-line/blowup.jsonl 거주)

CORE_MATH      29 (67.4%)   ★ n, phi, sopfr, J2, tau, sigma, M3, mu, 7대 axiom
DISCOVERY       7 (16.3%)
MISC            6 (14.0%)
PHYSICS         1 ( 2.3%)
```

**함의**: degree shard hot 의 핵심 = topic shard CORE_MATH HOT 셀.
3차원이 직교가 아니라 (degree, topic) 강한 상관, temporal 만 직교.

## 7. 합성 규칙: 3차원 indexing

### 7.1 직교성 분석

```
degree × topic        : 강한 상관 (ρ ≈ 0.7)  — top hub 의 67% 가 CORE_MATH
degree × temporal     : 약한 상관 (ρ ≈ 0.3)  — 새 라벨도 평균 deg 낮음
topic × temporal      : 약한 상관 (META 만 100% HOT, 나머지 분산)
```

→ **temporal 만 직교 차원**. degree/topic 은 결합 indexing.

### 7.2 3차원 셀 카운트

```
이론 최대: 2 × 8 × 3 = 48 cells
실제 non-empty: ~22 cells (PHYSICS HOT 0, DISCOVERY HOT 0, BIO HOT 0 등 빈 셀 多)
```

### 7.3 권장 indexing 전략

**파일 분할은 topic 기준만**. degree/temporal 은 sidecar.

```
shared/n6/atlas.n6                ← SSOT (변경 없음)
shared/n6/atlas.n6.prelude        ← 헤더 60KB
shared/n6/atlas.n6.topic.{cat}    ← 8개 파일 (CORE_MATH 가장 큼 761KB)
shared/n6/atlas.n6.deg            ← degree sidecar (기존)
shared/n6/atlas.n6.tidx           ← temporal index sidecar (신규, ~540KB)
```

이유:
- topic 분할 = 의미 기반 → 라우팅 효과 큼 (16x ~ 37x I/O 감소)
- degree 분할 = hot/cold 단일축 → 이미 a0d72d62 에 있음, X1 후 재계산
- temporal 파일 분할 X — 매시간 HOT→WARM 흐름 → churn 폭발. sidecar 만.

## 8. 구현 Design

### 8.1 Phase 1 — Topic Shard 파일

```
파일 형식: atlas.n6 와 동일 (label + cont + comment) — 단일 shard 자체로 valid n6 SSOT
재구성: cat prelude topic.* | sort = sort atlas.n6  (lossless invariant)

생성 도구:
  shared/n6/atlas_topic_shard.awk
  - 입력: shared/n6/atlas.n6
  - 출력: 8개 topic shard + prelude
  - 분류 규칙: §3.1 그대로 awk 매크로화
  - 실행: awk -f atlas_topic_shard.awk shared/n6/atlas.n6

실행 명령:
  hexa shared/n6/atlas_shard_regen.hexa --topic
```

### 8.2 Phase 2 — Temporal Index Sidecar

```
파일: shared/n6/atlas.n6.tidx
형식: line_no\tauthor_time_unix\tbucket(HOT|WARM|COLD)
크기: 21,678 rows × ~25 byte ≈ 540 KB

생성 도구:
  shared/n6/atlas_tidx.awk
  - 입력: git blame --line-porcelain stdin
  - 출력: TSV
  - 실행: git blame --line-porcelain atlas.n6 | awk -f atlas_tidx.awk > atlas.n6.tidx

freshness:
  - atlas.n6 mtime 변경 시 tidx invalidate
  - append-only 이므로 incremental 가능 (last_line_no+1.. 만 blame)
  - shard_meta.json.tidx_sha256 로 검증
```

### 8.3 Phase 3 — blowup engine read routing

`shared/blowup/core/blowup.hexa` 변경점 (3 곳):

```
A) graph_load Phase 1
   기존: read_file(_ATLAS_PATH)
   변경: stats fast-path (변경 없음)
        miss 시: read prelude + 모든 topic shard concat (cat 시퀀스)

B) auto_select_domain 후 도메인-필터
   기존: atlas.n6 전체에서 ::domain 매칭 grep
   변경: domain → topic shard 매핑 → topic shard 만 read
        예: domain="physics" → atlas.n6.topic.physics (244KB)

C) Phase 6.7 cross-process dedup
   기존: grep -qF '"id":"X"' atlas.n6  per-노드 (full file scan)
   변경: grep -qF '"id":"X"' atlas.n6.topic.{predict_cat(X)}  +
        atlas.n6.tidx HOT 버킷만 (24h 내 추가분만 scan)
```

### 8.4 Phase 4 — 안전 gate

```
lossless invariant:
  cat atlas.n6.prelude atlas.n6.topic.* | sort = sort atlas.n6
  (degree shard a0d72d62 동일 정책)

SSOT invariant:
  atlas.n6 = 유일한 _guarded_append_atlas() target
  topic shard = read-only sidecar (write 시 즉시 stale → regenerate)

shard_meta.json 확장:
  {
    "topic_shards": {
      "CORE_MATH": {"path": "...", "lines": 7671, "bytes": 761308, "sha256": "..."},
      ...
    },
    "topic_shards_lossless_verified": true,
    "tidx_path": "shared/n6/atlas.n6.tidx",
    "tidx_sha256": "...",
    "tidx_last_blame_line": 21678
  }

rollback:
  topic shard / tidx 삭제 → atlas.n6 단독 fallback
  (blowup.hexa 가 graceful degrade — feature flag NEXUS_TOPIC_SHARD=1 미설정 시 기존 path)
```

### 8.5 Phase 5 — feature flag 단계적 전환

```
Stage 1: NEXUS_TOPIC_SHARD=1 환경 변수로 opt-in 라우팅
Stage 2: blowup.hexa 의 새 path 검증 (lossless + perf)
Stage 3: NEXUS_TOPIC_SHARD 기본 활성화
Stage 4: 구 path 제거 (단, atlas.n6 SSOT 는 영구 유지)
```

## 9. 예상 I/O 절감

```
시나리오                       기존 I/O    신규 I/O   감소율
──────────────────────────────────────────────────────
META hierarchy 검증            1.5 MB     40 KB     37.5x
PHYSICS Phase                  1.5 MB    244 KB      6.1x
HOT bucket dedup (24h)         1.5 MB    145 KB     10.3x
full reload                    1.5 MB    1.5 MB     1.0x  (concat)
──────────────────────────────────────────────────────
blowup full run (6 phase 평균) ~9 MB    ~1.7 MB     5.3x
```

## 10. 다음 단계

```
1) sim 결과 검토 후 H-DOD spec 작성 (voice_dod 패턴)
2) atlas_topic_shard.awk + atlas_tidx.awk 작성 (read-only commit)
3) blowup.hexa _ATLAS_PATH → topic_shard_for(domain) 점진 전환
4) lossless 검증 후 L0 보호 추가 (CLAUDE.md 갱신)
5) X1 commit 완료 후 degree shard (.hot/.cold) 재계산 (이번 작업의 부산물)
```

## 11. 산출물

```
설계        shared/discovery/mkx_axis1_topic_temporal_design.md  (이 파일)
sim 데이터  shared/discovery/mkx_axis1_shard_sim.json            (machine-readable)
이전 study  shared/discovery/atlas_shard_study.md                (axis1 전반 [C])
shard meta  shared/n6/atlas.n6.shard_meta.json                   (degree shard, X1 전 기준)
```
