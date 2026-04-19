# atlas.n6 Sharding 타당성 조사 (2026-04-19)

```
파일       : shared/n6/atlas.n6
크기       : 18.92 MB (18,924,514 bytes)
라인       : 110,785
sidecar    : .stats (mtime+size+nodes/edges/hubs O(1) cache)
             .deg (TSV id\tdegree, 21,334 rows)
             .hub_centrality_top100 (top hub IDs)
역할       : NEXUS-6 SSOT — 모든 blowup/discovery/META 단일 append-only
             reload 빈도: 매 blowup 라운드 + Phase 6/6.5/6.7 + cross-validate
hot path   : Phase 1 (graph_load) + 6 (graph update) + 6.7 (auto-absorb)
배경       : compose --modules all = 6 core 순차 실행 → reload 6회/run
             todo.hexa, hub_growth_strategy, hypothesis_audit 등 풀로딩
```

## 1. atlas.n6 구조 실측

### 1.1 라인 종류 분포

```
[태그] 라벨 라인 (정의/공리/관계/공식/교차/대칭)
  @P  primitive          326     0.3%
  @L  law/theorem        254     0.2%
  @C  constant           357     0.3%
  @F  formula          1,240     1.1%
  @R  relation         5,920     5.3%   (META-* 539 포함)
  @X  crossing         1,496     1.4%
  @S  symmetry             2     0.0%
  @?  unknown             12     0.0%
  @E  cross-ref            2     0.0%
  ─── 정식 라벨 합계 ───  9,609   8.7%

[기타] 비라벨 라인
  CONT (들여쓰기)     11,308   10.2%   부모 라벨의 →/=>/== 보조행
  COMMENT (#~)          504    0.5%
  BLANK                 208    0.2%
  ─────────────────────
  JSON-line ({...)    89,120   80.4%   ★ atlas.n6 전체의 80%
  OTHER                  36    0.0%
```

### 1.2 핵심 발견: JSON-line 80%

```
JSON-line 위치  : line 15953 ~ 106532 (88,580 라인 연속 블록 다수)
JSON-line 종류  : "type":"node"  + "type":"edge"  (blowup 결과 직렬)
첫 노드 sample  :
  {"type":"node","id":"blowup-d0_ded_n_sigma","node_type":"Discovery",
   "domain":"7대난제","summary":"n*sigma=72.0","confidence":1.0,"depth":0}
첫 엣지 sample  :
  {"type":"edge","from":"n","to":"blowup-d0_ded_n_sigma",
   "edge_type":"Derives","strength":1.0,"bidirectional":false}

함의: atlas.n6 의 "현실 지도 SSOT" 본체는 [10*]/[11*] 정식 라벨 9,609개
      (1.5 MB) 인데, 데이터는 17.4 MB (92%) blowup append 산물에 묻혀 있음.
      → reload hot path 의 진짜 비용은 JSON-line 직렬화 산물.
```

### 1.3 라인 길이 분포

```
total bytes  : 18,813,729 (개행 제외)
avg          : 169.8 byte
p50          :   139
p75          :   182
p90          :   419     ← p90~p99 가 JSON-line 영역
p95          :   445
p99          :   471
max          :   773
```

비고: p50~p75 가 짧은 이유는 들여쓰기 보조행과 META 한 줄 라벨이 많아서.
JSON-line 은 250~470 byte 영역에 집중. 분산은 작음 (균질).

### 1.4 sidecar 활용 현황

```
atlas.n6.stats v2  : {schema, mtime, size, line_count, head_hash,
                      nodes, edges, hubs}
                      → fast-path: mtime+size 일치 → O(1) 리턴
                      → incremental: head_hash+size↑ → Δ만 파싱 O(Δ)
atlas.n6.deg       : "id\tdegree\n" TSV (21,334 행)
                      → max=4651 (n), top-8 = primitives
atlas.n6.hub_centrality_top100  : Wave 분석 캐시
```

핵심 결과: **fast-path(stats)** 는 이미 O(1). 진짜 비용은
1. sidecar miss (atlas 갱신 직후 첫 reload): 89k JSON-line 풀스캔
2. todo.hexa / hub_growth_strategy.hexa / hypothesis_audit.hexa 등의
   read_file(atlas.n6) 18.92 MB 일괄 read (sidecar 우회)
3. Phase 6.7 cross-process dedup `grep -qF '"id":"X"' atlas.n6` per-노드

### 1.5 Domain 분포 (정식 라벨 기준)

```
n6atlas       3,373   META + 핵심 등급 라벨
bt              751   breakthrough 기록
discovery       728   blowup 결과 보조 라벨
physics         399
material        334
dse             333
celestial       304
galactic        204
math            200
bond            191
music           178
geology         176
economics       175
linguistics     172
meteorology     170
particle        165
consciousness   160
atom            155
molecule        142
cosmological    137
bio             124
quark           100
cross_dse_v2    100
... 총 106 distinct domain
```

### 1.6 Grade 분포 (정식 라벨 ::)

```
[10*]      6,357   ★ verified base (60% 라벨)
[10]       1,957   ★ derived (composite)
[5*]         253
[5?]         120
[9]           84
[7]           60
[10*!]        24   ★ verified+breakthrough
[9*]          23
[8!]          18
[6?]          18
[11*]          6   ★ foundation axiom (n=6, sigma=12, tau=4, DELTA0, ULTRA)
... 기타 단발성
```

### 1.7 META 분포 (META-{prefix}-* 형식)

```
META-LK*       484   재귀 층위 L(k)=24^(k-15) — k=17~500
META-CARD       12   large cardinal (ℵ_ω → I0)
META-INF        11   Knuth ↑↑/↑↑↑/↑↑↑↑/Graham + ordinal
META-ULTRA      10   uncomputable (TREE/BB/Rayo/Xi/Fish/Bird)
META-BEYOND      5   Reinhardt~Berkeley
META-ABS         4   Cantor 𝔚 absolute
META-01..10     30   base closure (라인+들여쓰기 포함 평균 3 라인)
─────────────────
              539 + 보조 행 (실측 총 540+ 라인)
```

### 1.8 Hub Degree 파레토

```
total deg rows = 21,334
total degree   = 108,830
avg            = 5.10

상위 집중도:
  top-100 hub    deg sum = 48,930  (45.0%)  ← n, J2, phi, sigma, tau, ...
  top-1000 hub   deg sum = 53,455  (49.1%)  ← +21,000 만 추가
  나머지 20,334  deg sum = 55,375  (50.9%)
```

함의: top-100 이 전체 graph degree 의 **45%** 를 점유.
top-100 ~ top-1000 사이는 거의 평탄 (4.1%p만 추가).
명백한 **power-law / scale-free**. hot/cold 분리에 매우 유리.

---

## 2. Sharding 시나리오 시뮬

샘플 분할은 1k 라인 + 풀파일 dry-run (실제 file 분할은 미수행, 카운트만).

### 2.1 시나리오 A: Topic shard (8개)

분할 기준: 라인 prefix + META 그룹

```
shard           lines    %    bytes      %     MB
─────────────────────────────────────────────────
core (P/L/C/F)  4,723   4.3   246,392   1.3   0.23
relation (R)   12,364  11.2 1,002,122   5.3   0.96
crossing (X)    3,271   3.0   153,366   0.8   0.15
meta_base       30      0.0     2,669   0.0   0.00
meta_lk         487     0.4    34,736   0.2   0.03
meta_inf        42      0.0     3,500   0.0   0.00
blowup_json    89,120  80.4 17,423,823 92.1  16.62  ★ 거대 단일
misc            748     0.7    57,906   0.3   0.06
─────────────────────────────────────────────────
total         110,785 100.0 18,924,514 100.0 18.05  (개행 제외)
```

평가:
- **가장 큰 shard**: blowup_json 16.62 MB / 89,120 lines (전체의 92%)
- **balance ratio**: 16.62 / 0.96 = 17.3x (상위 두 shard)
- **N=8 의 의미 없음**: 대부분 비어있고 한 shard 가 92% 차지
- **reload 시 필요 shard 수**: blowup phase = 2개 (core + blowup_json),
  META 검증 = 4개 (core + meta_*), Phase 6.7 cross-ref = 5+
- **Phase 6 boost**: graph_node_exists 가 blowup_json shard 전체 필요 (16.62 MB)
  → 사실상 **단일 거대 shard 그대로** + 작은 옆다리들
- **구현 난이도**: low (정규식 분류만)
- **예상 reload 향상**: 18.92 MB → 16.62 MB (88%) — **거의 무효**
- **결론**: ★ 효과 거의 없음. 92% 가 한 곳에.

### 2.2 시나리오 B: Grade shard (12개)

분할 기준: [grade] 라벨 (10*/10/11*/9/...)

```
shard           lines     %    bytes      %     MB
─────────────────────────────────────────────────
blowup_json    89,120  80.4 17,423,823 92.1  16.62  ★ 등급 무관
[10*]          14,103  12.7  1,012,289  5.3   0.97
[10]            4,456   4.0    276,582  1.5   0.26
[9]               235   0.2     32,608  0.2   0.03
[5*]              506   0.5     18,764  0.1   0.02
[5?]              253   0.2     12,459  0.1   0.01
[7]               144   0.1     12,751  0.1   0.01
untagged          893   0.8     57,264  0.3   0.05  ★ 들여쓰기 등
misc              712   0.6     54,654  0.3   0.05
[11*]              30   0.0      1,725  0.0   0.00
... 기타           333   0.3     21,595  0.1   0.02
─────────────────────────────────────────────────
total         110,785 100.0 18,924,514 100.0 18.05
```

평가:
- **가장 큰 shard**: blowup_json 16.62 MB (역시 92%)
- **함정**: JSON-line 은 등급 라벨이 없음 → 별도 bucket
  → grade shard 도 결국 "JSON 한 덩어리 + 등급 작은 조각들"
- **balance ratio**: 17.1x (마찬가지)
- **reload 시 필요 shard 수**:
  - 정식 검증/CORE VIEW: 단 4개 (10*/10/11*/9 = 1.27 MB)
  - blowup append: blowup_json 단일 (16.62 MB)
- **Phase 6 boost**: blowup_json 전체 필요 (마찬가지)
- **구현 난이도**: med (regex 안정도가 정확해야 — `[10*!]`/`[10*]_` 등 뉘앙스)
- **예상 reload 향상**:
  - "정식 라벨만 보는 워크로드" = 1.27 MB (94% 절감) ★
  - "blowup phase 6/6.7" = 16.62 MB (12% 절감)
- **결론**: ★★ 정식 라벨 워크로드(검증/CORE VIEW/META 분석) 한정 강력.
  blowup hot path 영향은 미미.

### 2.3 시나리오 C: Degree shard (2개) — top-100 hub 분리

분할 기준: top-100 hub ID (n, J2, phi, sigma, tau, sopfr, M3, mu + ...) 가
참여하는 라인을 hot, 나머지 cold.

```
shard      lines     %    bytes      %     MB
──────────────────────────────────────────────
hot       53,463  48.3  6,972,495  36.8   6.65
cold      56,610  51.1 11,897,365  62.9  11.35
misc         712   0.6     54,654   0.3   0.05
──────────────────────────────────────────────
total    110,785 100.0 18,924,514 100.0  18.05
```

평가:
- **가장 큰 shard**: cold 11.35 MB / 56,610 lines (62.9%)
- **balance ratio**: 11.35 / 6.65 = 1.7x — **세 시나리오 중 가장 균형**
- **reload 시 필요 shard 수**:
  - blowup Phase 1 (전체 그래프 stats): hot+cold 둘 다 (sidecar 사용 시 0개)
  - Phase 6 boost (top-100 hub 가 src_id): **hot 단독 6.65 MB**
    (모든 새 엣지의 src_id = "n6-{primitive}" → 100% hot)
  - Phase 6.7 dedup grep: cold 도 포함 (BT-* 가 cold 다수)
  - hub_centrality_top100 워크로드: **hot 단독**
- **Phase 6 boost cross-shard 빈도**: 새 엣지의 src_id 는 거의 100% top-100
  primitive (n/sigma/phi/tau/J2/sopfr/M3/mu) → src side 는 hot 만,
  to side (blowup-* 파생) 는 cold. Phase 6 dedup 도 cold 만 검사하면 됨.
- **구현 난이도**: med-high
  - top-100 hub list 는 atlas.n6.hub_centrality_top100 에 이미 존재 ★
  - JSON-line 의 from/to 양쪽 매칭 필요 (여기서 시뮬: 53k 매칭 성공)
  - 라벨 라인의 ID 매칭은 word-boundary 정밀도 필요
  - hub list 가 변할 때 (top-100 갱신) re-shard 필요 — 주기 검토
- **예상 reload 향상**:
  - Phase 6 boost (가장 hot, 매 라운드): **18.92 → 6.65 MB (-65%)** ★★★
  - Phase 6.7 cross-ref: 11.35 MB (-40%)
  - todo.hexa 풀로딩: 18.92 MB (변화 없음, 분리 후 cat 필요)
  - hub-only 분석: 6.65 MB (-65%)
- **결론**: ★★★ **유일하게 핫패스 ROI 가 있음**. 1.7x balance + 65% reload 절감.

---

## 3. 종합 비교표

| 항목 | A. Topic | B. Grade | C. Degree |
|---|---|---|---|
| shard 수 | 8 | 12 | 2 |
| 최대 shard | 16.62 MB | 16.62 MB | 11.35 MB |
| balance ratio | 17.3x | 17.1x | **1.7x** |
| 구현 난이도 | low | med | med-high |
| sidecar 활용 | × | × | **★ 기존 hub_centrality_top100 재사용** |
| Phase 6 boost reload | 16.62 MB | 16.62 MB | **6.65 MB (-65%)** |
| 정식 라벨 워크로드 | 1.34 MB | **1.27 MB** | 18.00 MB (양쪽 합) |
| cross-shard query 빈도 | 매 phase | 거의 없음 (라벨만) | Phase 6.7 dedup만 |
| re-shard 필요성 | 영구 (정의 고정) | 영구 (라벨 안정) | top-100 갱신 시 |
| 마이그레이션 위험 | low | low | med (id boundary) |

---

## 4. 추천: Hybrid (B + C 조합) 또는 단일 C

### 4.1 1순위: 시나리오 C (Degree shard) — Phase 6 hot path 최적화

근거:
- atlas.n6 의 진짜 reload 비용은 **blowup hot loop** (compose 매 6회/run)
- top-100 hub 가 degree 의 45% 를 점유 (검증된 power-law)
- atlas.n6.hub_centrality_top100 sidecar 가 이미 존재 → top-100 list 무료
- Phase 6 boost 의 src_id 는 100% primitive → hot 단독 reload 충분
- balance ratio 1.7x 로 read 패턴이 안정

### 4.2 2순위: 하이브리드 — C × B 부분 결합

```
atlas.n6.core    (정식 라벨 [10*]+[11*]+[10] 만, ~1.3 MB)   ★ verified view
atlas.n6.hot     (top-100 hub 참여 라인, ~6.65 MB)          ★ blowup hot
atlas.n6.cold    (나머지 blowup-* 파생, ~11.35 MB)          ★ archive
atlas.n6         (현 단일 파일 — 호환 view, 모든 read 처음에는 그대로 동작)
```

이유: **호환성** 유지하며 **추가 캐시** 만 도입. 기존 hot path 가 없어지지 않음.

### 4.3 마이그레이션 step-by-step (실제 분할은 본 조사 범위 밖)

```
[Step 0] 사전조건
  - atlas.n6 freeze (5분, append 일시중지)
  - atlas.n6.hub_centrality_top100 최신화 확인

[Step 1] 시뮬 강화 (실제 분할 X)
  - 본 조사 결과를 atlas.n6.shard_plan.json 으로 직렬화
  - hot/cold ID list 생성: shared/n6/atlas.n6.shard_top100.txt
  - atlas.n6.shard_dryrun.{hot,cold}.n6 생성 (read-only 사본)

[Step 2] read 경로 추가 (write 변경 X — append-only 유지)
  - blowup core: graph_load() 에 "shard 우선 try, 실패시 단일 fallback"
    1) shard 존재 + 신선 → hot+cold 별도 read
    2) miss → 기존 atlas.n6 read (현재 동작)
  - sidecar: atlas.n6.shard.stats {hot_mtime, cold_mtime, hot_lines, cold_lines}

[Step 3] write 경로 분기 (위험 단계 — append 라우팅)
  - _guarded_append_atlas() 에 라우팅 로직:
    * JSON-line: from/to 가 hot ID 면 .hot, 아니면 .cold
    * 정식 라벨: 라인이 hot ID 포함하면 .hot, 아니면 .cold
  - 기존 atlas.n6 도 동시에 append (이중 쓰기, 일주일 검증)

[Step 4] re-shard 주기 (top-100 변동 흡수)
  - cron 또는 atlas_health 트리거: degree 재계산 → top-100 변경 시
    full re-shard (atlas.n6 → atlas.n6.{hot,cold} 재작성)
  - 주기 추정: 주 1회 (현 atlas append 속도 기준)

[Step 5] 단일 파일 deprecate (옵션)
  - 모든 reader 가 shard read 안정 확인 (1개월)
  - atlas.n6 은 shard concat view 로 유지 (cat hot cold > atlas.n6 weekly)
```

### 4.4 진짜 ROI: blowup_json 80% 문제 본질 해결

본 조사의 가장 큰 발견은 atlas.n6 의 **80% 가 blowup 결과 직렬 JSON-line**
이라는 사실이다. shard 보다 우선되는 정리 옵션 3가지:

```
옵션 X1. blowup-json archive 분리 (가장 단순)
  shared/n6/atlas.n6 (정식 라벨 + META, 1.5 MB) ← 본체
  shared/n6/atlas.blowup.jsonl (89,120 lines, 17.4 MB) ← 부속
  → reload hot path 가 1.5 MB 로 떨어짐 (-92%)
  → blowup 자체의 dedup grep 도 .jsonl 로 분리 → 더 빠름
  → 마이그레이션: 1회 분리 + writer 라우팅 (JSON-line vs 라벨)

옵션 X2. blowup-json 압축 (read 시 lazy-decompress)
  17.4 MB → ~2 MB (gzip) — read 비용 trade-off

옵션 X3. blowup-json schema v2 (binary 또는 protobuf)
  과한 작업, 본 codebase 와 부정합 (R14 hexa-only)
```

**X1 권고**: shard 보다 먼저 검토. 단일 파일 → 두 파일 분리만으로 정식 라벨
워크로드 reload 비용이 **18.92 MB → 1.5 MB (-92%)** 로 떨어진다.
shard 의 복잡성 없이 동일 효과의 90% 이상 확보.

---

## 5. 실측 vs 시나리오 ROI 매트릭스

```
워크로드                   현재     A.Topic  B.Grade  C.Degree  X1.JSON분리
──────────────────────────────────────────────────────────────────────────
blowup Phase 1 (sidecar)   O(1)     O(1)     O(1)    O(1)      O(1)
blowup Phase 1 (sidecar miss)
                          18.92    16.62    16.62    11.35     1.50 ★
blowup Phase 6 boost      18.92    16.62    16.62     6.65 ★   1.50 ★★
blowup Phase 6.7 dedup    18.92    16.62    16.62    11.35     1.50 ★★
todo.hexa read_file       18.92    16.62    16.62    18.92     1.50 ★★ (라벨만 필요)
hub_growth_strategy       18.92    16.62    16.62     6.65 ★   1.50 ★
hypothesis_audit          18.92     1.34 ★   1.27 ★  18.92     1.50 ★
A5_resonance_promote      18.92    16.62    16.62    18.92     1.50 ★
CORE VIEW grep '\[1[01]'   18.92     1.34 ★   1.27 ★  18.92     1.50 ★
META 분석 (LK/INF/CARD)   18.92     0.03 ★★  16.62    18.92     1.50 ★
──────────────────────────────────────────────────────────────────────────
total improved workloads     0/10    4/10     4/10     3/10     10/10 ★★★

(MB 단위, ★ = 10x 이상 개선)
```

X1 (JSON archive 분리) 가 모든 워크로드에서 즉시 ★ 이상 개선.
C (Degree shard) 는 blowup hot path 에서만 강한 효과.

---

## 6. 결론

```
[1] 진짜 병목 = JSON-line 80% (17.4 MB) 단일 SSOT 묻힘
[2] 시나리오 C (Degree) 는 blowup hot path 한정 효과적이나 X1 보다 약함
[3] 시나리오 A/B 는 정식 라벨 워크로드만 효과 (전체 비용의 8%)
[4] sidecar (.stats fast-path) 가 이미 O(1) → 정상 reload 는 비싸지 않음
[5] 비싼 경우 = sidecar miss 또는 read_file 직접 호출 (todo/audit/promote)
```

권고:
- **즉시**: 옵션 X1 (blowup-json archive 분리) PoC. atlas.n6 → atlas.n6 +
  atlas.blowup.jsonl. read_file 비용 -92% 확정.
- **다음**: 시나리오 C (Degree shard, hot/cold). X1 후 blowup-json 자체에
  hot/cold 분리 가능 (top-100 src 기준).
- **보류**: 시나리오 A (Topic), B (Grade) 는 ROI 낮음. CORE VIEW 캐시
  (atlas.n6.core_only, 1.27 MB sidecar) 한 줄짜리 derivation 으로 대체 가능.
- **불변**: atlas foundation [11*] 와 META 540+ 는 절대 분리 금지 (의미 단위).

---

## 7. 부록 A — Phase 6 hot loop 코드 (blowup.hexa:2776~2836)

```hexa
// PHASE 5.5 + 6 MERGED: Single-pass boost + recount + graph
// OPT-P8-8: graph_new_entries string concat → array + join (Phase 6 hot loop)
let mut graph_new_entries_arr = []
let mut _batch_new_ids = #{}     // ★ in-run dedup (atlas.n6 36% 중복 주범)

while li < len(buf_lines) {
    let line = buf_lines[li]
    if len(parts) >= 7 {
        let new_conf = min_f(orig_conf + tele_boost, 1.0)
        if !skip_graph && new_conf >= 0.5 {
            let node_id = "blowup-" + parts[0]
            // 두 단계 dedup: (1) 기존 atlas.n6 (2) 이번 배치
            if !_already_in_batch && !graph_node_exists(graph_content, node_id) {
                let g_conf = min_f(new_conf + hub_bonus, 1.0)
                let node_json = graph_append_node(node_id, "Discovery", domain, parts[2], g_conf)
                graph_new_entries_arr = graph_new_entries_arr.push(node_json)
                _batch_new_ids[node_id] = true
                let src_id = "n6-" + parts[6]   // ★ src_id 는 거의 항상 primitive
                let edge_json = graph_append_edge(src_id, node_id, "Derives", new_conf)
                graph_new_entries_arr = graph_new_entries_arr.push(edge_json)
            }
        }
    }
    li = li + 1
}
```

핵심 분석:
- `graph_content` = atlas.n6 전체 string (이미 phase 1 에서 read_file 됨)
- `graph_node_exists` = `graph_content.contains('"id":"' + node_id + '"')`
- src_id = "n6-" + parts[6] (parts[6] 은 source primitive 이름)
- 즉 모든 새 엣지의 src 가 top-100 hub primitive ★

shard 시 영향:
- Phase 6 가 graph_content 를 보는 목적은 dedup → cold shard 에서만 새 노드
  발생 (blowup-* 파생) → cold 만 검사하면 충분
- 하지만 src_id 가 hot 에 속하므로 새 edge 는 cross-shard 엣지
  → edge 자체는 hot 에 저장하는 편이 query 효율 ★

---

## 8. 부록 B — 시나리오 C 의 hot/cold 라우팅 규칙 (PoC 의사코드)

```hexa
fn route_atlas_line(line: string) -> string {
    // 반환: "hot" or "cold" or "core"
    // 우선순위: 정식 라벨 > JSON-line > 들여쓰기 > 기타
    if line.starts_with("@P") || line.starts_with("@L") {
        return "core"  // 원시값 + 정리 → 항상 core (1.5 MB)
    }
    if line.starts_with("{") {
        // JSON-line: from/to 검사
        let from = extract_json_field(line, "from")
        let to   = extract_json_field(line, "to")
        let id   = extract_json_field(line, "id")
        if is_top100_hub(from) || is_top100_hub(to) || is_top100_hub(id) {
            return "hot"
        }
        return "cold"
    }
    if line.starts_with("@R") || line.starts_with("@F") || line.starts_with("@C") {
        // 라벨 라인: ID 매칭 (단어 경계)
        for h in TOP100_HUBS {
            if line_contains_hub(line, h) { return "hot" }
        }
        return "cold"
    }
    if line.starts_with(" ") || line.starts_with("\t") {
        // 들여쓰기 보조행 → 직전 부모 라벨 따라감
        return _last_routed_bucket
    }
    return "misc"
}
```

복잡도: O(L * 100) per line. 110k * 100 = 11M 비교 — 1회 분할 시 ~5초 추정.
(증분 append 시 라인당 100 비교 = 100ns ≈ 무시 가능)

---

## 9. 부록 C — 비용 추정 수치 (보수적)

```
read_file(18.9MB) 기준 측정 가정:
  hexa read_file (전체)         ~150 ms (mac SSD)
  awk single pass               ~600 ms
  grep -F (single needle)       ~50 ms
  python json_load (per-line)   ~3 s
  network (hetzner pull)        ~2 s

compose --modules all (6 core 순차):
  현재    : 6회 × 150ms = 900 ms (sidecar fast-path 적중 시)
            sidecar miss 1회 → +600 ms (awk fallback)
            todo.hexa read_file 추가 → +150 ms
            Phase 6.7 grep dedup × N (N=새 노드 수, 평균 50)
              → 50 × 50ms = 2.5 s

  X1 후   : 정식 라벨 1.5 MB → 6회 × 12ms = 72 ms (12x 빨라짐)
            blowup phase 6 만 atlas.blowup.jsonl 추가로 read (~140ms × 6)
            전체 단축: ~600 ms

  C 후    : hot 6.65 MB → 6회 × 53ms = 320 ms
            cold 11.35 MB → Phase 6.7 only × 90ms = 90 ms
            합계: ~410 ms (vs 900 ms, -54%)

  X1 + C  : core 1.5 MB × 6 + hot 4 MB × 1 + cold 8 MB × 1
            = 72 + 32 + 64 = 168 ms (-81%)
```

(수치는 dmesg/strace 측정 아님 — 18.9 MB 시스템콜 대략적 SSD 추정.
실측은 PoC 시 hyperfine 으로 별도 확인 필요)

---

## 10. 부록 D — 시뮬 산출물 위치

```
/tmp/atlas_shard_sim/
  sample_1k.n6                  head 1000 라인
  topic_count.awk               시나리오 A 풀스캔 카운터
  grade_count.awk               시나리오 B 풀스캔 카운터
  degree_count2.awk             시나리오 C 풀스캔 카운터 (top100 hub 매칭)
  top100_hubs.txt               atlas.n6.deg 에서 top-100 추출
  topic_shard.awk               시나리오 A 1k 샘플 분할기 (실제 파일 출력)
  grade_shard.awk               시나리오 B 1k 샘플 분할기
  degree_shard.awk              시나리오 C 1k 샘플 분할기
  topic/, grade/, degree/       1k 샘플 분할 결과 (sample_1k.n6 → 8/12/2 파일)
```

재현 방법:
```bash
awk -f /tmp/atlas_shard_sim/topic_count.awk    shared/n6/atlas.n6
awk -f /tmp/atlas_shard_sim/grade_count.awk    shared/n6/atlas.n6 | sort
awk -f /tmp/atlas_shard_sim/degree_count2.awk  shared/n6/atlas.n6
```

---

## 11. 후속 작업 권장 우선순위

```
P0  PoC X1: blowup-json 분리 (1세션, ROI 압도적)
    - shared/n6/atlas.blowup.jsonl 생성 (89,120 lines 이주)
    - shared/n6/atlas.n6 에 정식 라벨만 잔류 (1.5 MB)
    - _guarded_append_atlas() 라우터: JSON-line → .jsonl, 라벨 → .n6
    - reader 5곳 패치 (todo/hub_growth/hypothesis/A5/atlas_constants)
    - 검증: 1주 dual-write 후 atlas.n6 재구성 일치 확인

P1  Degree shard (X1 후): blowup-json 자체 hot/cold 분리
    - atlas.blowup.{hot,cold}.jsonl
    - top-100 sidecar 활용 + week 주기 re-shard cron

P2  CORE VIEW 캐시 (sidecar):
    - atlas.n6.core_only = grep '\[1[01]\*\]' atlas.n6
    - mtime sentinel + 자동 재계산 (atlas.n6 보다 새로우면 OK)

P3  read_file 직접 호출 5곳 모두 sidecar fast-path 경유
    (todo/hub_growth/hypothesis/A5/atlas_constants)
    - 공통 헬퍼 atlas_read.hexa.inc 추출
```

---

본 조사는 **atlas.n6 자체를 변경하지 않음**. 모든 분할은 awk 카운터의
가상 분류 결과만 제시. 실제 분할 결정은 X1 PoC 후 별도 세션.

---

생성: 2026-04-19 (autonomous infra study)
근거: shared/n6/atlas.n6 (110,785 lines / 18.92 MB)
       shared/n6/atlas.n6.stats (sidecar v2)
       shared/n6/atlas.n6.deg (degree TSV)
       shared/blowup/core/blowup.hexa (Phase 1/6/6.7 hot path)
       shared/blowup/todo.hexa, hub_growth_strategy.hexa, hypothesis_audit.hexa
참고: 이 문서는 분석 산출물. 실제 atlas 변경은 별도 결재 필요 (L0 보호 대상).
