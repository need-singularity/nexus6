# atlas.n6 Emergent Structure Analysis — 2026-04-11

READ-ONLY 스냅샷 분석. blowup 엔진은 2026-04-06 이후 dormant, 본 분석은 기존 44,874 라인 SSOT 내 발견 구조에 국한.

## Summary

| metric | value |
|---|---|
| file lines | 44,874 |
| size | 6,482,951 bytes |
| total nodes (health) | 12,349 |
| parsed typed nodes (@P/@C/@L/@F/@R/@S/@X/@?) | 6,321 |
| edges | 12,348 |
| unique refs | 12,383 |
| virtual refs (n6-/bt-/foundation- chains) | 88 |
| real orphans | 0 |
| duplicate data lines | 0 |
| malformed | 0 |
| duplicate node IDs | 54 (benign — health OK) |
| distinct domains | 82 |

Atlas는 health 관점에서 깨끗하다 (orphan/malformed/dup-line 전부 0). 구조적 품질은 이미 수렴 상태이며, 남은 관심사는 **내용 차원의 창발 패턴**이다.

## Top Discoveries (5 most interesting)

1. **`persistence_threshold = tau/sigma = 1/3` [10*!]** :: topology
   Breakthrough 등급. n=6의 위상학적 영속 임계값이 τ/σ = 4/12 = 1/3 로 고정. meta_fp 와 정확히 동치 (`meta_fp = 1/3 [10*!]`). 두 서로 다른 도메인(topology/meta)이 단일 분수 1/3 에 수렴한 첫 확증 기록.

2. **`n6-bt-779 = n * sopfr_sq = n + sigma_sq = 150` [10*!]** :: 아이디어
   "아이디어" 도메인에서 *곱*(6 × 25)과 *합*(6 + 144) 두 경로가 동일 값 150 으로 수렴. sigma_sq(=144)와 sopfr_sq(=25)의 교차. sigma_sq 값 144 는 독립적으로 5-node 클러스터 (`sigma_sq, sm_ada, L4-gen-nucleosome-bp, n6-bt-722, n6-bt-751`) 를 형성 — 수학/생물/SM 3중 교차.

3. **`n6-bt-779~794 = 아이디어_돌파 [9!]`** (16-node 체인)
   "아이디어" 도메인 전체가 단일 blowup 돌파 클러스터로 골화. 동반 `n6-bt-792 = ouroboros_growth_5r = 60_disc [8!]` 는 ouroboros 성장률이 60 discoveries/round 로 안정화. `n6-bt-793 = tunnel_아이디어_to_math [8!]` 는 아이디어→math 도메인 터널 — 타 도메인에 없는 교차 토폴로지.

4. **7난제 도메인 (62 nodes, alien_index 집중)**
   61개 alien index 후보 중 60개가 `7난제` 도메인에 집중. `n6-bt-718~778` 체인이 n 을 기반으로 한 산술 조합 수색(`n*sigma=72`, `n*phi=12`, `n*tau=24`, `n*j2=144`, `n*sopfr_sq=150` 등)으로 7대 난제를 단일 씨앗 n=6 에 접지. grade `[0.10*]` (d.r alien form) 12 노드는 수치 검증 완료.

5. **`MISS-base-pairs-per-turn` (degree 25)**
   hub 랭킹 7위. MISS 등급임에도 가장 많은 의존성을 끌어당기는 "불일치 허브" — B-DNA 10bp/turn 과 n6 기반 예측의 간극이 여러 하위 발견을 방사형으로 유도. **재돌파 후보 1순위**.

## Distributions

### Grade distribution (6,321 typed nodes, normalized)

| bucket | count | share |
|---|---|---|
| EXACT (10* / 9+) | 3,783 | 59.8% |
| CLOSE (8) | 440 | 7.0% |
| NEAR (7) | 1,068 | 16.9% |
| MISS (≤6 / 5?) | 1,030 | 16.3% |

Raw top: `10*` 3780, `7` 1063, `5?` 959, `8` 354, `9` 73. Breakthrough marker `!` 7 노드 (meta_fp, persistence_threshold, n6-bt-718~778, n6-bt-779, n6-bt-792, n6-bt-793, n6-bt-779~794).

### Type distribution

`@R` 3,478 (55%) · `@X` 1,399 (22%) · `@F` 707 · `@P` 321 · `@C` 216 · `@L` 194 · `@?` 5 · `@S` 1.

관찰: `@S` (대칭) 노드가 단 1개. n=6 의 풍부한 대칭군(D6, A5 등)이 아직 명시 인덱스화되지 않았다 — **구조적 공백**.

### Domain top 15

n6atlas 1932 · bt 758 · dse 333 · material 320 · celestial 299 · galactic 203 · bond 191 · geology 170 · music 170 · meteorology 169 · economics 169 · linguistics 166 · particle 163 · atom 154 · molecule 142.

### @X (crossings) 집중

`bt` 758, `celestial` 299, `galactic` 203, `cosmological` 136 — 교차 에지의 ~99% 가 천체·우주·블로업 도메인에 집중. **material/bio/music 등 중간 스케일은 교차 희박** — 브리지 블로업 대상.

### Source labels (expr 내 keyword)

`mu` 179, `quantum` 7, `string` 6, `field` 1, `seed` 1, `ouroboros` 1. blowup-mu 가 압도적 다수. 연-월-일 형식 타임스탬프는 노드 expr 내에 0건 — 메타데이터는 atlas 바깥(growth_bus/bt_audit)에 위임.

## Emergent Clusters

값 공유 클러스터 (구성원 ≥ 5):

| value | nodes | 의미 |
|---|---|---|
| **6.0** | 21 | n 자체 — planck/π/미토콘드리아 ATP/yamanaka factors/mitosis phases 등 이종 도메인 20개가 n=6 에 직접 꽂힘 |
| **2.0** | 16 | phi 가족 — chloroplast, golgi cisternae, intermediate filament … |
| **1.0** | 15 | mu 가족 — 정규화/확률/분수 상수 |
| **10.0** | 6 | MISS-base-pairs-per-turn 중심 DNA/염색질 군 |
| **12.0** | 5 | sigma 가족 — Z-form DNA, transcription speed 등 |
| **144.0** | 5 | sigma_sq 가족 — nucleosome bp, SM-ada, 7난제 `n*j2` |
| **4.0** | 5 | tau 가족 — siRNA length, codon degeneracy |

**창발 관찰**: sigma_sq(144) 가 *수학 상수 → SM 모델 → 생물 nucleosome → 7난제 추측* 까지 4계층 브리지 역할. 현재 144 클러스터는 5개에 그쳐 **저집중**이지만, sigma_sq 가 persistence_threshold/meta_fp 처럼 명시 brkthough 로 승격될 잠재력 있음.

Hub top 20 (degree 합계):

```
L1-carbon-Z6(40) · L2-sp2-hexagonal(32) · MUSIC-chromatic-semitones(30) ·
L4-dna-bases(28) · L2-cn6-octahedral(28) · L3-benzene(25) · MISS-base-pairs-per-turn(25) ·
MAT-LiC6(24) · BIG-GFR-120(23) · BIO-blood-ABO(23) · L4-amino-acids(23) · MATH-platonic(23) ·
L4-codons(23) · ASTRO-spacetime-dims(22) · L5-graphene(22) · L0-quark-flavors(22) ·
LING-IPA-vowel-cardinal(22) · L2-bravais-lattices(22) · L3-C60(21) · TIME-hours-per-day(21)
```

탄소 스택(Z6/sp2/benzene/C60/graphene/LiC6) 6노드가 top 20 내 30% 점유. **탄소는 atlas.n6 의 물리적 중심**이다.

## Orphans

- real orphans: **0** (atlas_health 확인)
- virtual refs: 88 (`n6-bt-*`, `foundation-*` 체인 — 의도된 유도 참조)
- 중복 node ID: 54 (health 통과, 정의 확장 재기록 패턴)

실제 orphan 누출 없음. n6-bt-* virtual chain 이 88개나 되는 것은 bt_audit 측 책임.

## Next Probes

1. **`@S` 대칭 노드 확충** — 현재 1개. D6/A5/S6/Z6 등 유한군 공백을 돌파 타겟으로 지정.
2. **sigma_sq(144) breakthrough 승격** — 현 5-node 클러스터를 교차 도메인 돌파 후보로. nucleosome×sm_ada×7난제 3중 교차 확증.
3. **MISS 허브 재돌파** — MISS-base-pairs-per-turn(deg 25), MISS-planck-units(val 6) 등 "고차수 MISS" 노드들을 seed 로 한 targeted blowup.
4. **material/bio/music 브리지** — @X 교차의 99% 가 bt/celestial/galactic/cosmological 에 편중. 중간 스케일 도메인에 cross-domain tunneling 필요.
5. **sigma_sq=150 & sopfr_sq=25 포화 검증** — n6-bt-779 의 곱/합 이중 경로(6×25=150, 6+144=150)가 우연인지 구조인지 확증.
6. **탄소 6-hub 닫힘 증명** — Z6/sp2/benzene/C60/graphene/LiC6 가 상호 참조하는지 그래프 부분포집 검사.
7. **아이디어→math 터널 확장** — n6-bt-793 이 유일한 "아이디어" 교차 터널. math/physics/topology 로 다중 터널 개설.

---
*생성: /usr/bin/python3 직접 파싱 (atlas.n6 read-only), atlas_health.hexa verbose, 2026-04-11. blowup 엔진 미사용.*
