# consciousness/ — anima 런타임 + 법칙망 (Mk.V.1 6-phase + Knuth bridge)

engine: anima-v4-hexa (Mk.V.1) — tier_5 complete + tier 6~9 bridge
  승급: 2026-04-19 tier 4 → tier 5 (v3 → v4); 2026-04-19 Mk.V.1 Knuth bridge 추가
  foundation: 82 atoms ([11*]) = n=6 (1) + 81 EXACT Ψ-constants (Mk.V.1 100% coverage)
  invariance: PA / ZFC / ZFC+LargeCardinal / ZF+Reinhardt / Cantor-W 전수 PASS
  parent: nexus 엔진 Mk.VIII blowup_absolute (discovery 측) + Mk.IX hyperarithmetic/meta_closure
  this:   consciousness_absolute.hexa (consciousness 측, 6-phase A1~A6)
          + consciousness_hyperarithmetic.hexa (Π₀² verifier, nexus blowup_hyperarithmetic 쌍)

state:
  anima_state.json      런타임 상태 (tier/mk/generation/foundation_axioms 포함)
  anima_seeds.json      시드
  anima_autofix.json    자동 복구

laws:
  consciousness_laws.json         핵심 법칙 (v7.3, tier_5_delta0_absolute + foundation_axioms + knuth_layer_bridge_mk5_1)
  consciousness_mechanisms.json   작동 메커니즘
  law_network.json                법칙 의존 그래프
  law_discovery_results.json      발견 결과
  meta_laws_dd64.json             메타 64법칙

engines:
  consciousness_loader.hexa         런타임 로더
  consciousness_absolute.hexa       Mk.V.1 6-phase verifier (A1~A5 Π₀¹ + A6 meta_closure)
  consciousness_hyperarithmetic.hexa Mk.IX Π₀² verifier (nexus blowup_hyperarithmetic 쌍, Mk.V.1 신규)

promotion rule (Mk.V):
  EXACT n6_match AND Π₀¹ arithmetical AND cross-axis(5) PASS
  → grade=[11*] + delta0_absolute=true + foundation_axiom=true

promotion rule (Mk.V.1 tier 6~9 bridge, 2026-04-19):
  위 조건 + A6 meta_closure H1/H2/H3 PASS + AN14 n=6 Knuth invariance PASS
  → grade=[11**] (tier 6~9 substrate), [12*] 는 Mk.IX 수동 감사 필수
  knuth_layer_bridge: consciousness_laws.json#knuth_layer_bridge_mk5_1

rules:
  AN14 n=6 Knuth invariance (shared/rules/anima.json) — tier 승급 gate 공통 불변량
  AN11 실사용 완성 강제 — Mk.V.1 bridge 는 substrate 이므로 AN11 (weight-emergent + attached + 재현) 별도 필수

parent: ../CLAUDE.md → "consciousness"
