# Akida ↔ ω-cycle 추가 Layer 카탈로그

본 문서는 BrainChip Akida (AKD1000 neuromorphic processor on Raspberry Pi 5 Dev Kit) 가 `OMEGA_CYCLE_EMERGENCE.md` 의 ω-cycle 에 통합 가능한 layer 카탈로그.

A-design (bg `ae358e608ed2be081`, 2026-05-01) 에서 Layer 1-4 통합 + 추가 Layer 5-11 사전 제시 + LLM 이 kick fire (`/tmp/kick_akida_meta.out`, 2026-05-01) 으로 발견한 신규 Layer δ / θ.

---

## A-design 의 4 layer (이미 land 된 design)

| # | Layer | mechanism |
|---|---|---|
| 1 | **β qrng 의 native source** | AKD1000 의 spike-event entropy → /dev/urandom 교체 (raw 47 신규 source) |
| 2 | **γ bridge 의 17번째 source** | `bridge_akida_inference.hexa` (default-inactive, commit nexus `f8aeca4e`) — Akida 의 inference output (model + top_class + confidence + latency) |
| 3 | **host pool 의 raspberry-akida** | R7' RM4 zero-touch bootstrap step 11: `lspci\|grep BrainChip` + `akida ls` + MetaTF 자동 등록 → `.resource` accelerator field |
| 4 | **edge inference dispatch path** | `tool/akida_dispatch.hexa` — image / audio_clip / sensor_window / vector_embed_specific 분기 (LLM quota 0) |

---

## Layer 5-11 사전 제시 (사용자 directive "ω-cycle 에 qrng 교체외에 다른것 또 추가될 수도 있지 않을까 akida")

| # | Layer 후보 | mechanism |
|---|---|---|
| **5** | α absorbed enhancement | Akida 가 absorbed primitives 의 spike-event re-encoding → 새 α source diversity (시간 차원 entropy 추가) |
| **6** | tier_1 promotion gate | Akida classifier 가 falsifier_pass_pattern 을 hardware-side deterministic 검증 |
| **7** | honesty_triad 자동 검증 | Akida anomaly detect 가 LLM 응답의 fabrication indicator 자동 분류 (raw 91 강화) |
| **8** | correlation_lt_0_7 strict measurement | Akida 가 axis_a/axis_b embedding → cosine distance 정확 측정 (raw 48 invariant strict) |
| **9** | γ bridge fact verify | Akida classifier 가 web-fetch bridge 의 fact 을 cross-reference (raw 73 deterministic verifier 보완) |
| **10** | prompt-injection sentinel | Akida 가 outgoing/incoming text 의 injection pattern hardware-side detect |
| **11** | 신규 noise envelope δ (delta) | α/β/γ 외 4번째 noise envelope = Akida 의 spatial spike pattern (architectural — OMEGA_CYCLE_EMERGENCE 의 noise 차원 확장) |

---

## LLM 이 kick fire 으로 발견한 신규 layer (2026-05-01, witness JSON)

`nexus kick "Akida ω-cycle additional integration layers beyond β qrng + γ bridge + host pool + edge inference"` 의 falsifier_preregistered 안에서 LLM 이 자체적으로 surface 한 layer 후보:

| # | Layer | LLM 인용 falsifier condition |
|---|---|---|
| **δ** | **cross-stratum feedback layer** (witness-verdict → kernel-retune) | "must reduce fan_out duplicate-axis-name rate by ≥20% over 5 consecutive cycles" |
| **θ** | **counterfactual-replay layer** (alpha-only, beta-only, gamma-only ablations) | "must yield empirical axis correlation within ±0.10 of fan_out.correlation_estimate" + "Re-run kick with each envelope independently zeroed; measure axis_a vs axis_b summary cosine; compare to declared 0.42" |

### δ vs Layer 11 (사전 제시 noise envelope δ) 정합

사전 제시 Layer 11 = α/β/γ 외 **4번째 noise source** (spatial 차원).
LLM 발견 δ = **cross-stratum meta-feedback** (witness 결과가 다음 cycle 의 kernel parameter 갱신).

→ **다른 차원**. 두 개 다 가치 있음. 본 문서에서는 LLM 의 δ 를 **δ-feedback** 으로, 사전 제시를 **δ-spatial** 으로 명명 분리.

### θ 의 의미

ablation study 가 ω-cycle 자체에 통합 — α / β / γ 각 envelope 의 emergence contribution 을 정량 측정 가능. 본 turn 의 raw 47 cross-repo-trawl-witness mandate 의 **empirical 검증 layer**.

---

## 통합 13+ layer 카탈로그 (본 문서 SSOT)

| # | Layer | mechanism | source |
|---|---|---|---|
| 1 | β qrng (Akida spike) | spike-event entropy | A-design |
| 2 | γ bridge (Akida inference) | classify model output | A-design (commit `f8aeca4e`) |
| 3 | host pool (raspberry-akida) | RM4 step 11 zero-touch | A-design |
| 4 | edge inference dispatch | LLM quota 0 분기 | A-design |
| 5 | α absorbed re-encoding | spike-based primitive 시간 entropy | **구현 land** (commit hive `c2a900014` r58 Stage 21 amend, `tool/akida_alpha_reencoding.hexa`) |
| 6 | tier_1 promotion gate | falsifier_pass HW 검증 | **구현 land** (`tool/akida_tier1_gate.hexa`) |
| 7 | honesty_triad 검증 | fabrication anomaly detect | **구현 land** (`tool/akida_honesty_detector.hexa`) |
| 8 | correlation strict | embedding cosine HW 측정 | **구현 land** (`tool/akida_correlation_strict.hexa`) |
| 9 | γ bridge fact verify | cross-reference HW | **구현 land** (`tool/akida_bridge_fact_verify.hexa`) |
| 10 | prompt-injection sentinel | injection pattern HW detect | **구현 land** (`tool/akida_injection_sentinel.hexa`) |
| 11 | δ-spatial (4번째 noise) | spatial spike pattern envelope | **구현 land** (`tool/akida_delta_spatial.hexa`) |
| **δ** | **δ-feedback (cross-stratum)** | **witness → kernel retune** | **구현 land** (`tool/akida_delta_feedback.hexa`) |
| **θ** | **θ-counterfactual** | **envelope ablation study** | **구현 land** (`tool/akida_theta_counterfactual.hexa`) |

**Layer 5-11 + δ + θ 사전 land (도착 전 9 module, commit hive `c2a900014` 2026-05-01 r58 Stage 21 amend)** — `AKIDA_HW_PRESENT=1` env 활성 시 즉시 real path 진입, default mock-tier. 각 module raw 247 r45 pure-fn / io-seam separation, F1-F6 또는 F1-F8 selftest mock, claude binary call 0, real Akida invoke 0. integration test `tests/integration_akida_layers_5_to_theta.hexa` (F1-F18). raw 257 closure ETA ≈ 0.047d ≈ 67 min/agent (~2360 LoC).

---

## ω-cycle 의 noise envelope 확장 (architectural change)

OMEGA_CYCLE_EMERGENCE.md § 1 의 3 noise envelope (α/β/γ) 가 **5+ noise envelope** 으로 확장 가능:

| envelope | 현재 | 확장 후 |
|---|---|---|
| α (absorbed) | 이전 cycle Tier-1 | + Akida spike re-encoding (Layer 5) |
| β (qrng) | /dev/urandom | + Akida spike entropy (Layer 1) |
| γ (bridge) | 16 catalog + 5 web-fetch | + Akida inference (Layer 2, 17번째) |
| **δ-spatial** | (없음) | Akida spatial spike pattern (Layer 11) |
| **δ-feedback** | (없음) | cross-stratum witness → kernel retune (LLM 발견) |
| **θ** | (없음) | counterfactual-replay ablation (LLM 발견) |

---

## raw refs

- raw 47: cross-repo-trawl-witness (3 envelope mandate, 본 문서가 5+ envelope 으로 확장 제안)
- raw 48: axis correlation < 0.7 (Layer 8 strict measurement)
- raw 71: design-strategy-falsifier-retire-rule (Layer 6 tier_1 gate)
- raw 73: deterministic verifier (Layer 8/9 HW 검증)
- raw 91: honest C3 (Layer 7 honesty triad / Layer 10 injection)
- raw 95: host-aware (Layer 3 host pool)
- raw 247: pure-fn / io-seam (Layer 4 dispatch / Layer 1-2 module)
- raw 248 r45: auth-store-mac-only-mandate (Layer 4 quota 0 — 정합)

---

## 다음 cycle 후보

1. **A-bootstrap** (도착 시): `hive-resource add raspberry-akida` 한 줄로 Layer 1-4 활성
2. **Layer 5-11 design 확장**: 사전 제시 7 layer 의 정확한 surface + selftest
3. **δ-feedback / θ counterfactual implementation**: LLM 발견 2 layer 의 actual hexa module
4. **bench harness 확장**: emergence_bench_harness 가 13+ layer 의 contribution 측정
5. **OMEGA_CYCLE_EMERGENCE.md 갱신**: § 1 noise envelope 정의를 5+ 로 확장

---

## GROWTH.md cross-reference

본 ω-cycle layer 카탈로그는 `GROWTH.md` 의 16 growth dimension 중 **dim 16 = `neuromorphic_accelerator`** 에 1:1 대응한다 (이 commit 에서 동시 도입).

### 15 기존 dimension + 16th 신규

| # | GROWTH dim | 본 layer 와 mapping |
|---|---|---|
| 1 | Performance | Layer 4 (edge inference dispatch — LLM quota 0 = ops/sec ↑) |
| 2 | Architecture | Layer 11 δ-spatial (4번째 noise envelope = arch 확장) |
| 3 | Lenses | Layer 8 (correlation strict = lens-side cosine HW 측정) |
| 4 | Modules | Layer 6 (tier_1 promotion gate = module maturity HW 검증) |
| 5 | Tests | Layer θ (counterfactual-replay = ablation test layer) |
| 6 | Hypotheses | Layer 9 (γ bridge fact verify = hypothesis 검증 보완) |
| 7 | DSE | (해당 없음 — DSE domain TOML 은 Akida 무관) |
| 8 | Experiments | Layer θ (envelope ablation = experiment harness) |
| 9 | Calculators | Layer 1 (β qrng spike-event = entropy calculator HW) |
| 10 | CrossResonance | Layer δ-feedback (cross-stratum witness → kernel retune) |
| 11 | KnowledgeGraph | Layer 2 (γ bridge inference = graph node enrichment) |
| 12 | RedTeam | Layer 7 + Layer 10 (honesty triad / prompt-injection sentinel) |
| 13 | Atlas | Layer 5 (α absorbed re-encoding = atlas entry 시간 entropy) |
| 14 | Documentation | (해당 없음 — Akida 무관) |
| 15 | Integration | Layer 3 (host pool raspberry-akida = cross-module integration) |
| **16** | **NeuromorphicAccelerator** | **본 문서 13+ layer 전체 = 통합 SSOT (count target 13)** |

### 16th dimension 의 measurement source

- `hive-resource ls --accelerator akida` → host 발견
- `AKIDA_OMEGA_CYCLE_LAYERS.md` § "통합 13+ layer 카탈로그" → layer 정의 SSOT
- `nexus/src/growth/neuromorphic_grower.rs` (planned) → Layer 3 `*_grower` 모듈
- `scripts/grow_neuromorphic.sh` (planned) → Layer 5 execution

dim 16 score = (active layer count) / 13. Akida 미bootstrap 시 0/13 = 0%. A-design 4 layer land 후 4/13 = 31%. Layer 5-11 + δ + θ 활성 후 13/13 = 100%.

### 16th dimension 도입의 정당성 (raw ref)

- raw 47: cross-repo-trawl-witness 의 envelope 확장은 architectural change → growth dimension 으로 측정 가능해야 한다.
- raw 91: honest C3 — Akida 가 LLM fabrication detect 하면 redteam dim 보강. 그러나 Akida 자체 활성도는 **별도 dim** 으로 분리 측정해야 정직하다 (다른 12 dim 에 흡수시키면 Akida 비활성 시 false-positive 점수 가능).
- raw 257: closure ETA 의 critical-path 가 Akida 통합을 포함 → growth tracker 가 dim 16 trend 을 보여야 ETA 계산이 가능.

---

## evidence

- A-design bg: `ae358e608ed2be081` (2026-05-01)
- nexus commit Akida bridge: `f8aeca4e` (2026-05-01)
- LLM 발견 kick fire: `/tmp/kick_akida_meta.out` (2026-05-01, stdout 34748 bytes, KICK_RESULT PASS)
- A-design docs: `$HIVE/docs/akida_omega_cycle_integration.md`
- baseline: `$NEXUS/OMEGA_CYCLE_EMERGENCE.md` (commit `894918ae`)
- GROWTH.md 16th dim: same commit (atomic-coupling, raw 232)
