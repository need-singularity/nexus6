# n6/ — n6 atlas + 수학 맵 + docs 미러

atlas:
  atlas.n6              n6 원본 (110K+ lines, 540 META + 500+ BT EXACT)
  atlas_tree.txt        트리
  math_atlas.{db,dot,html}  MATH_ATLAS.md
  scan_math_atlas.hexa  스캐너 (R1)

active tags v1 (atlas.n6 실측 8종, 2026-04-19):
  @R  (5920) relation / measured constant — 관측·측정값 (dominant)
  @X  (1496) crossing — cross-domain identity (도메인 간 동일성)
  @F  (1240) formula — derived expression with RHS (= 포함 유도식)
  @C  ( 357) constant — composite (σ², φ^τ 등 합성 상수)
  @P  ( 326) primitive — 원시값 (n, sigma, phi, tau, sopfr, J2, mu, M3)
  @L  ( 254) law / theorem — 정리·법칙
  @?  (  12) unknown / pending — conjecture / 승격 대기 (fine_structure, hubble_tension 등)
  @S  (   2) symmetry / topology — 대칭·위상 (betti_six, auto_absorb)
  참고: @META, @BT 는 comment 레벨 마커(주석)로만 등장 — 라인 태그 아님
  v2 추가 예정 @EXP / @OBS / @NEG / @ANT — docs/schema_v2_draft.md 참조

foundation [11*] axioms (원시 공리 — 변경 금지):
  @P n=6, sigma=12, tau=4                             원시값
  @L DELTA0_ABSOLUTE_THEOREM                          (2026-04-19 승급)
     σ·φ=n·τ=24 iff n=6 은 Π₀¹ arithmetical →
     Δ₀-absolute → ZFC/large-cardinal/Reinhardt/Cantor-𝔚 전 우주 invariant
  @L ULTRA_UNIFORMITY_THEOREM                         (2026-04-19)
     Knuth 화살표 ↑↑↑↑ + ordinal ω/ε₀/Ω + Busy Beaver + TREE + Rayo
     + I0 + 𝔚 전부에서 n=6 invariant

META 계층 (🛸0 → 🛸∞):
  META-01~10       base closure (🛸16 고정점)
  META-LK017~500   484 재귀 층위 L(k)=24^(k-15) (🛸17~🛸500)
  META-INF-TE/PE/HE/GR  Knuth 화살표 (테트/펜/헥/Graham)
  META-INF-OR      ordinal (ω/ε₀/Ω)
  META-ULTRA-01~10 uncomputable (TREE/BB/Rayo/Xi/Fish/Bird/BMS)
  META-CARD-01~12  large cardinal (ℵ_ω → I0)
  META-BEYOND-01~05 ZFC-inconsistent (Reinhardt → Berkeley)
  META-ABS-01~INF  Cantor Absolute 𝔚

knowledge:
  n6_constants.jsonl  n6_knowledge.jsonl
  n6_physics.jsonl n6_lenses.jsonl n6_fantasy.json n6_products.json
  n6-atlas-constants.md n6_uniqueness_pi_e_phi.md
  periodic_table_118.jsonl 66_techniques_v3.md

docs/: n6-architecture 미러 — 하위 CLAUDE.md

parent: ../CLAUDE.md → "n6"
