# scale1k summary — 1000-mut Gödel-Q bootstrap (2026-04-16)

run_ids: `20260416-022606` (ANU) / `20260416-022636` (urandom)

## 100 vs 1000 비교

| 지표 | 100 mut (2026-04-16 MVP) | 1000 mut ANU | 1000 mut urandom |
|---|---|---|---|
| n_try | 100 | 1000 | 1000 |
| n_applied | 69 (69%) | 304 (30%) | 308 (31%) |
| parse_ok | 100 | 1000 | 1000 |
| n_metric_up | 31 | 21 | 39 |
| n_accept | 56 | 193 | 187 |
| anu_bytes | 400 | 4000 | 4000 (urandom) |
| unique output hash | 6 | 14 | 14 |
| max Δ | +496 | **+870** | **+870** |
| best_same_hash_run | 4 | **49** | 11 |
| fixed_point_iter | ∅ | **99** | **694** |
| 벽시계 | ~2m | ~13m | ~12m |

n_applied 비율이 100→30%로 떨어진 것은 ops 수가 3→7로 늘었고 신규 4종의 적용 제약(loop_unroll은 특정 while 패턴만, inline_const는 상수-바인딩 선행 ident 필요)이 까다로워서. 반대로 성공 시 구조 변형력은 훨씬 강함. accept hash 다양성 6→14 (2.3배↑).

## Fixed-point 도달

**도달**. ANU 런은 iter 99에서 연속 10 accept 동일 hash 임계값 돌파, iter 272까지 **49개 연속 accept 동일 hash** (baseline `95319207…`, metric=174) 확장. 원인: `rename_var`·`extract_var`의 86·58건 accept은 **출력 보존 변형** (순수 리팩토링) — 의미 보존 mutation 들이 basin 을 형성해서 hash attractor 에 안착. 이는 Schmidhuber 프레임에서 “self-referential improvement candidate 가 proof 없이 baseline-preserving 구조로만 누적되는 상태” = 진짜 `improvement proof` 없음을 의미.

구조적으로는 fixed-point 이지만 **metric 상승이 없는** 정체-점. 즉 baseline-attractor. 엔진은 50 회 가까이 accept 해도 새로운 계산 의미를 만들지 못했다. 이게 Gödel machine 이 해결해야 할 halting problem 의 경험적 증거.

## 흥미 mutation 3선 (공통 신기록 +870)

1. **iter 283 ANU / 181 UR — `let e = d * 2` → `let e = d * 12`** Δ=+870, metric 174→1044 (6배). tweak_const +10 이 compute 의 마지막 곱셈 상수를 5배 만들어 전체 `r3=score(8)` 누적 증폭. 이전 최고 +496 를 **1.75×** 갱신.
2. **iter 717 ANU / 961·641·106 UR — `let c = a - b` → `let c = a + b`** Δ=+504. swap_op 가 `compute` 의 부호를 뒤집어 음수→양수 flip, metric 3.9× 점프. 네 번 독립적으로 발견 — mutation space 의 "easy win" 고지대.
3. **iter 7 ANU — `compute(i, i + 1)` → `compute(i, i + 11)`** Δ=+256 (score loop payload). 이건 score 함수 내부 루프 페이로드를 건드려서 n=8 이터레이션 전체에 효과 증폭. 루프-scope 변형의 힘.

## ANU vs urandom 비교

| | ANU | urandom |
|---|---|---|
| 벽시계 | 13분 | 12분 |
| n_metric_up | 21 | 39 (1.85×) |
| best_same_hash_run | 49 | 11 |
| 캐시 재사용으로 인한 주기성 | 강함 | 없음 |

ANU는 60초 cache 로 인해 같은 blob 이 반복 consum 되어 **같은 mutation picker 출력을 연속 생성** → 동일 hash 런이 길어짐. urandom 은 매번 fresh 64B라 골고루 탐색해서 metric_up 이 1.85× 많음. 품질 측면에서 **urandom 이 exploration 에 유리**. ANU 는 fixed-point 탐지에 유리 (주기성 = 수렴 가속).

## 결론

**"1000 mut 에서 fixed-point 도달 확인 (ANU: 49 consecutive same-hash accepts @ baseline, metric stall 없음이 아닌 baseline-attractor 포획)".** metric 상승 없는 수렴 → Gödel machine 의 "proof-less improvement candidate" 현상 재현.
