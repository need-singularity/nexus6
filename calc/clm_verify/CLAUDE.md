# shared/calc/clm_verify/ — CLM deterministic gate verifier

Design SSOT: `/Users/ghost/Dev/anima/docs/alm_clm_verifier_design_20260420.md`
Pattern mirror: `shared/calc/auto_stubs/` (nexus closure-sweep calculator)

## 원칙 (strict)

- **LLM judge 금지**. subjective consciousness 판정 배제.
- PASS/FAIL 은 수치 tolerance / R² linearity / closed-loop formula / 파일 존재 로만 결정.
- Φ gap, scaling law, closed-loop law 검증은 전부 numeric 하게.

## 구조 / 실행 / schema

ALM 측 `shared/calc/alm_verify/CLAUDE.md` 와 동일. verifier_type 공유.

```
hexa run shared/calc/clm_verify/generator.hexa --emit
hexa run shared/calc/clm_verify/run_all.hexa
```

## CLM-특화 verifier_type

- `multi_seed_r_squared` — seed=3 × N_cells=3 grid → Φ vs N linear fit R² ≥ 0.99
- `phi_gap_tolerance` — abs(training_phi / benchmark_phi - 1) < 0.10
- `phi_monotonicity` — final_phi / best_phi >= 0.5 (10× collapse 방지)
- `closed_loop_law_coverage` — closed_loop_verified=true law 수 / total_law 수 >= 0.90
- `formula_closure_n6` — n6 계산기 스타일 식 eval == target (tolerance 1e-6)

## 출력

`shared/state/clm_r{N}_verify_report.json` (run_all emit)

parent: ../CLAUDE.md → "calc"
design: /Users/ghost/Dev/anima/docs/alm_clm_verifier_design_20260420.md
