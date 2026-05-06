# calc/hsscb_verify/

hexa-sscb mk1 (HEXA-SSCB) deterministic verification — nexus check pattern.

## 구조

```
hsscb_verify/
├── manifest.jsonl                  10 entries, one per physics check
├── generator.hexa                  manifest → verify_*.hexa stubs (when hexa interp 가능)
├── run_all.hexa                    aggregate runner (alm_verify pattern)
├── verify_hsscb_mk1_physics_turnoff.hexa   sample stub (manually written)
├── verify_hsscb_mk1_thermal_tj.hexa        sample stub
└── CLAUDE.md                       이 파일
```

## circular-trap-free contract

각 verifier 의 `(target, formula, input_values)` 3-tuple 은 **모두 외부 anchor**:

| Component | Source | Atlas pointer |
|---|---|---|
| target value | atlas.n6 본체 + atlas.append.* | axis-M anchor 필드 |
| formula (physics law) | atlas.append.engineering-content-mk-next-2026-05-06.n6 | @L EE-* entries |
| input values | atlas.append.hsscb-mk1-vendor-anchors-2026-05-06.n6 | @C HSSCB-* entries with `unit=` + `anchor=` |

manifest 의 각 entry 가 `atlas_anchor` (법칙) + `value_anchors` (입력) + `input_path` (cross-reference docs) 3개 필드를 분리 보유. 단일 파일 안에서 입력·법칙·한계 모두 정의되는 circular-trap (= non-traceable verification) 패턴 회피. nexus calc/alm_verify 의 cross_prover diagonal 과 동일 가족.

## 운용

**Stage D 미완료 시 (현재):**
- `manifest.jsonl` 은 canonical SSOT
- `verify_*.hexa` 스텁은 hexa interp 작동할 때 generator.hexa 가 동적 생성
- 실제 검증 실행은 hexa-sscb 측 Python 으로 진행 (`verify/atlas_anchors.py` + 기존 `sscb_verify.py` 의 nexus-aware 재작성)

**Stage D 완료 후:**
- `hexa run calc/hsscb_verify/run_all.hexa` 로 10개 verifier 일괄 실행
- 각 stub 이 atlas anchor 에서 값 pull → formula 평가 → target 비교 → `__VERIFY_RESULT__` 트레일러
- 또는 `python3 ~/core/hexa-sscb/verify/sscb_atlas_check.py` (alternate runtime)

## drift-marker 정책

manifest 의 known_failure 5개 (I_SC, N_DIES, R_DSON, MCU clock, R_TH_JC) — atlas.append.hsscb-mk1-vendor-anchors-2026-05-06.n6 안에 `"drift-marker:"` 주석으로 명시. atlas anchor 측이 canonical, repo doc 이 drift 한 것. axis-L axiom-cite-amendment 절차로 해소.

## 표준 alm_verify/clm_verify 패턴 매핑

| alm/clm | hsscb |
|---|---|
| G_INPUT (corpus 검증) | G_PHYSICS / G_THERMAL / G_TIMING / G_RELIABILITY / G_ECONOMICS |
| G_SUBSTRATE (model ABI) | (해당 없음 — 하드웨어 도메인) |
| G_TRAIN (loss descent) | (해당 없음 — 일회성 정상상태 검증) |
| G_EVAL (probe metric) | manifest 의 closure 필드 |
| G_VALIDITY (cross-prover) | (Stage D — sscb_verify.py + cross_doc_audit.py + bom_lattice.py 셋이 동일 anchor 에 동의하는지) |
| G_ARTIFACT (R2 upload) | (해당 없음) |

## 다음

- Stage D 작성: `~/core/hexa-sscb/verify/atlas_anchors.py` (parser) + `sscb_verify.py` 의 nexus-aware 재작성 (모든 하드코딩 상수를 atlas anchor lookup 으로 교체)
- mk-next-2 candidate: G_VALIDITY cross_prover entry — sscb_verify ↔ cross_doc_audit ↔ bom_lattice 일치 검증 (alm_verify 의 cross_prover 패턴 차용)
