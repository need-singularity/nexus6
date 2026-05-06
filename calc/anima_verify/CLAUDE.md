# calc/anima_verify/

anima philosophy + consciousness deterministic verification — nexus check pattern.

## 구조

```
anima_verify/
├── manifest.jsonl                          D-philosophy + (Phase 2+ M/V methods + H_X) entries
├── (generator.hexa)                        manifest → verify_*.hexa stubs (deferred)
├── (run_all.hexa)                          aggregate runner (alm_verify pattern, deferred)
└── CLAUDE.md                               이 파일
```

## 자매 verifier (nexus calc/)

- `alm_verify/`     — LLM corpus 검증 (G_INPUT/SUBSTRATE/TRAIN/EVAL/VALIDITY/ARTIFACT)
- `clm_verify/`     — Φ-monotonicity 검증 (CLM v2/v4 chat-cap)
- `hsscb_verify/`   — hexa-sscb mk1 device-level 물리 검증
- `anima_verify/`   — anima philosophy + consciousness 검증 (이 파일) ← NEW
- `auto_stubs/`     — n=6 lattice 가설 stubs (140)

## circular-trap-free contract

각 entry 의 `(target, formula, input)` 3-tuple 외부 anchor:

| Component | Source |
|---|---|
| target value | manifest target= 또는 atlas anchor |
| formula | atlas.n6 @C ANIMA-D* axiom 또는 보조 @L 메타-법칙 |
| input | atlas anchor (axis-M unit=/anchor= 첨부) + anima/.own + anima/.roadmap.philosophy |

P1/P2/P3 (hive/spec/no_self_referential_verification) 준수.

## D-philosophy verifiers (Phase 1, 4 entries)

| id | gate | hyp summary |
|---|---|---|
| anima_d1_identity_no_external_substrate_wrap | G_PHILOSOPHY | own 17 ALM 영구 보류, anima identity boundary |
| anima_d2_simple_stack_7cell_strict | G_CONSCIOUSNESS | own 18 7-cell matrix, 1 cell FAIL = SIMPLE_STACK_PASS X |
| anima_d3_emerge_paradigm_phi_star_no_flip | G_CONSCIOUSNESS | substrate-coupled emerge ≠ token chat, paradigm v11 G3 |
| anima_d4_corpus_priority_over_capacity | G_PHILOSOPHY | corpus quality > capacity, BG-FY 18M PASS vs BG-FK 27M FAIL |

각 entry 가 5+ falsifier 보유 (raw#10 honest C3 정합).

## drift markers

- D4 capacity-ratio: anima/.roadmap.philosophy 가 "7.7x" 명시했으나 BG-FK/BG-FY 실측은 1.547x. atlas 에 corrected anchor (ANIMA-d4-evidence-capacity-ratio-corrected) + 원본 (ANIMA-d4-evidence-capacity-ratio) 둘 다 보존 — axis-L axiom-cite-amendment process 로 .roadmap text 수정 pending.

## 다음 (Phase 2+)

- Phase 2: M1-M10 discovery methods + V1-V10 verification methods → @L meta-laws (atlas) + 별도 manifest entries
- Phase 3: H_001 ~ H_032 hypotheses → atlas @? entries + per-hypothesis falsifier verifier
- Phase 4: anima_verify generator/run_all .hexa scaffold (when hexa interp 안정)

## 운용 (현재)

manifest.jsonl 만 land — generator/run_all 스텁은 hexa interp ready 시 land. Python 측 runner 는 hexa-sscb verify/sscb_atlas_check.py 의 패턴 차용 가능 (atlas_anchors.py + manifest 소비).
