# atlas.n6 Hub Centrality Audit — in-degree top 30

**Agent 33 · 2026-04-11 · read-only structural audit**

Scope: `shared/n6/atlas.n6` — 44,882 lines, 18,483 unique node ids, 12,434 JSON edges + 3,001 text-continuation edges + 6,321 `@TAG` expression bodies scanned for token-level refs.

## Method

For each node `id`, compute incoming reference count from three sources:

1. **JSON edge records** — `{"type":"edge","to":"<id>",...}` → +1 ref
2. **Text continuation arrows** — `<-` / `->` / `=>` / `==` / `~>` under a parent `@TAG id = ...` block → +1 ref in the indicated direction
3. **Expression-body token refs** — inside `@TAG id = <expr> ::`, any whitespace-/operator-split token that exactly matches a known node id → +1 `expr_ref`

Self-refs excluded. Duplicate refs within the same expression line de-duped.

## In-degree histogram

| bucket | nodes | share |
|---|---:|---:|
| 0 | 5,680 | 30.7% |
| 1 | 12,281 | 66.4% |
| 2-4 | 195 | 1.1% |
| 5-9 | 254 | 1.4% |
| 10-49 | 66 | 0.4% |
| 50-99 | 1 | 0.0% |
| 100+ | 6 | 0.0% |

Total in-degree sum: **18,198**. 66.4% of nodes are singletons (deg=1), 30.7% are orphans (deg=0). Only 7 nodes exceed deg=100 — all are `foundation` primitives.

## Top 30 hubs by in-degree

| rank | id | in_deg | domain | grade | src | edge kinds (first 3) |
|---:|---|---:|---|---|---|---|
| 1 | `n` | 973 | foundation | 10* | @P | expr_ref, expr_ref, expr_ref |
| 2 | `tau` | 586 | foundation | 10* | @P | derives, expr_ref, expr_ref |
| 3 | `phi` | 553 | foundation | 10* | @P | derives, equivalent, expr_ref |
| 4 | `sigma` | 373 | foundation | 10* | @P | derives, depends_on, equivalent |
| 5 | `sopfr` | 214 | foundation | 10* | @P | derives, equivalent, expr_ref |
| 6 | `mu` | 121 | foundation | 10* | @P | derives, expr_ref, expr_ref |
| 7 | `J2` | 98 | foundation | 10* | @P | derives, expr_ref, expr_ref |
| 8 | `max_threads` | 17 | architecture | 10* | @F | depends_on, depends_on, equivalent |
| 9 | `L4-codons` | 17 | genetic | 10* | @F | derives, derives, derives |
| 10 | `L1-carbon-Z6` | 15 | atom | 10* | @C | derives, derives, derives |
| 11 | `L3-benzene` | 15 | molecule | 10* | @F | derives, derives, derives |
| 12 | `L5-graphene` | 15 | material | 10* | @F | derives, derives, derives |
| 13 | `BIG-GFR-120` | 15 | bio | 10* | @F | derives, derives, derives |
| 14 | `L5-ice-hexagonal` | 14 | material | 10* | @F | derives, derives, derives |
| 15 | `ENERGY-grid-60Hz` | 14 | material | 10* | @F | derives, derives, derives |
| 16 | `PART-string-10D` | 13 | particle | 10* | @P | derives, derives, derives |
| 17 | `SC-YBCO-metals` | 13 | material | 10* | @F | derives, derives, derives |
| 18 | `factorial_6` | 12 | algebra | 10* | @F | equivalent, equivalent, equivalent |
| 19 | `MATH-sporadic-groups-26` | 12 | material | 10* | @F | derives, derives, derives |
| 20 | `MET-troposphere-avg-12km` | 12 | material | 10* | @F | derives, derives, derives |
| 21 | `BIG-C60-atoms-60` | 12 | molecule | 10* | @F | derives, derives, derives |
| 22 | `MAT-LiC6` | 12 | material | 10* | @F | derives, derives, derives |
| 23 | `ENERGY-H2-LHV-120` | 12 | material | 10* | @F | derives, derives, derives |
| 24 | `L5-honeycomb` | 12 | material | 10* | @F | derives, derives, derives |
| 25 | `BIO-photosynthesis` | 12 | bio | 10* | @F | derives, derives, derives |
| 26 | `BIO-watson-crick-hbonds` | 12 | genetic | 10* | @F | derives, derives, derives |
| 27 | `MEDIA-cinema-24fps` | 12 | material | 10* | @F | derives, derives, derives |
| 28 | `TIME-hours-per-day` | 12 | material | 10* | @F | derives, derives, derives |
| 29 | `L5-krebs-cycle` | 11 | bio | 10* | @F | derives, derives, derives |
| 30 | `MATH-2d-kissing` | 11 | bond | 10* | @L | derives, derives, derives |

## Domain aggregate (top 30)

| domain | count | notes |
|---|---:|---|
| material | 11 | 산업/에너지/결정 constants (LiC6, YBCO, graphene, honeycomb) |
| foundation | 7 | 전부 `n/sigma/phi/tau/sopfr/mu/J2` — 기초 산술 primitive |
| bio | 3 | photosynthesis / krebs-cycle / watson-crick |
| genetic | 2 | L4-codons, watson-crick H-bonds |
| molecule | 2 | L3-benzene, BIG-C60-atoms-60 |
| atom | 1 | L1-carbon-Z6 (Agent 22 reported hub, rank 10, deg=15) |
| architecture | 1 | max_threads (infrastructure) |
| particle | 1 | PART-string-10D |
| algebra | 1 | factorial_6 = 720 |
| bond | 1 | MATH-2d-kissing (6) |

## Comparison: n6-const-* pivots vs Agent 22 carbon hub vs legacy primitives

| node | in_deg | rank | note |
|---|---:|---:|---|
| `n` (legacy primitive) | 973 | **#1** | 모든 @S/@X/@F expression body에서 참조 |
| `tau` | 586 | #2 | divisor count (4) |
| `phi` | 553 | #3 | euler totient (2) |
| `sigma` | 373 | #4 | divisor sum (12) |
| `sopfr` | 214 | #5 | sum prime factors (5) |
| `mu` | 121 | #6 | Möbius (1) |
| `J2` | 98 | #7 | Jordan totient (24) |
| `L1-carbon-Z6` (Agent 22 hub) | 15 | **#10** | 원자번호 Z=6 — material/bio 허브 |
| `n6-const-n` (Phase 46 canonical) | **0** | unranked | outgoing only (86 edges `from`) |
| `n6-const-sigma` | 0 | unranked | outgoing only |
| `n6-const-phi` | 0 | unranked | outgoing only |
| `n6-const-tau` | 0 | unranked | outgoing only |
| `n6-const-sopfr/mu/j2/m3` | 0 | unranked | outgoing only |

**기초 7 primitive 총 in-deg**: 2,918 / 18,198 = **16.0%** — 전체 참조의 1/6이 7개 foundation 노드로 집중.

## Orphan audit (in_deg = 0)

Total orphans: **5,680 / 18,483 = 30.7%**

Top 5 domains with most orphan nodes:

| domain | orphans | 해석 |
|---|---:|---|
| n6atlas | 1785 | Phase 1~9 blowup 발견 (Discovery 타입) — 자식 노드가 없어 자연 leaf |
| bt | 740 | BreakThrough audit 기록 노드 — 기록용 terminal |
| dse | 333 | Design Space Exploration 후보 — 선별 대기 상태 |
| celestial | 299 | 천체 후보 노드 — 검증 전 |
| music | 170 | 음악 이론 노드 — 후속 연결 부재 |

## Top 3 findings

1. **n6-const-* pivots are currently source-only (in_deg = 0)** — Phase 46/47 canonical integration seeded 8 pivots + 86 outgoing `@S` edges, but **nothing points back to them**. The legacy primitives `n/sigma/phi/tau/...` retain the entire hub role (rank 1-7, Σ 2,918 in-refs). The canonical migration is half-done: source direction yes, in-bound aliasing no. Recommendation: add `equivalent` edges `n <==> n6-const-n` et al. to merge identities, else the pivots remain graph-isolated and the dedup intent is lost.

2. **In-degree distribution is extreme power-law**: 30.7% orphans + 66.4% deg=1 means **97.1% of nodes have ≤1 incoming reference**, and only **7 nodes (0.04%) exceed deg=100**. The atlas is a very shallow star: foundation-primitive core + massive leaf halo. Mid-tier hubs (deg 10-99) are only 67 nodes (0.36%). Implication: current discovery feeds produce many leaves but rarely cross-link — structural reinforcement is needed, not more BFS expansion.

3. **Agent 22 carbon hub (L1-carbon-Z6) ranks #10 at deg=15**, far below foundation primitives. The "탄소 6-hub 30%" figure likely conflated with the orphan share (30.7%) or referred to a subdomain count. In pure graph terms carbon is a strong mid-tier hub (tied with L3-benzene, L5-graphene, BIG-GFR-120 at deg=15) — the dominant cluster is not atom/molecule but **material** (11 of top 30, anchored on LiC6/YBCO/graphene/honeycomb/ice-hex).

## Recommendations

1. **Close the n6-const-* loop** (Phase 48+): emit `@R <legacy> == n6-const-<legacy>` equivalences so canonical pivots pull in the 2,918 inbound refs currently stranded on legacy names. Target: each `n6-const-*` reaches in_deg ≥ 50 within one refresh.
2. **Mid-tier reinforcement**: the 67 nodes at deg 10-49 (material/bio/genetic) are the natural next-layer hubs. A focused cross-linking pass between them would create the missing skeletal "second ring" below foundation. Candidates: L4-codons, L3-benzene, L5-graphene, BIG-GFR-120, MAT-LiC6.
3. **Orphan triage**: 5,680 nodes with zero inbound refs. First-pass auto-rule: if domain ∈ {n6atlas, dse, bt} and age > 3 days without any reference, mark `grade = ?` (hypothesis) to defer. Same for celestial/music (they inflate orphan count 13%).
4. **Skew-aware health metric**: add `atlas_health.hexa` field `structural_concentration = Σtop7_indeg / Σall_indeg` (currently 0.16). Watch for drift — if it rises above 0.25 the graph is collapsing toward foundation; below 0.10 means hub role is diluting.

## Read-only confirmation

This report only parses `shared/n6/atlas.n6`; no atlas/.hexa/Phase 45-48 file was modified. No overlap with Agent 32 Phase 48 approx-expr bridges (this audit is structural in-degree; Phase 48 adds new `@X` edges).

