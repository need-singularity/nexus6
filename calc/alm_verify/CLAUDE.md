# shared/calc/alm_verify/ — ALM deterministic gate verifier

Design SSOT: `/Users/ghost/Dev/anima/docs/alm_clm_verifier_design_20260420.md`
Pattern mirror: `shared/calc/auto_stubs/` (nexus closure-sweep calculator)

## 원칙 (strict)

- **LLM judge 금지**. Claude/Qwen 등이 "맞다/틀리다" 판정 구조 전면 배제.
- 모든 PASS/FAIL 은 regex / jq / 수치 비교 / hash / 고정 benchmark set 으로만 결정.
- `serving/hire_sim_judge_lenient.hexa` 는 **DEPRECATED** — 이 verifier 체계가 canonical.

## 구조

```
CLAUDE.md                  — 이 파일
manifest.jsonl             — 1 line = 1 claim (SSOT)
generator.hexa             — manifest → verify_<id>.hexa emit
run_all.hexa               — 전체 실행 + aggregate
verify_<id>.hexa           — per-claim deterministic verifier (auto-generated)
```

## manifest schema

```json
{
  "id": "alm_rN_gate_claim",
  "round": "rN",
  "gate": "G_INPUT|G_SUBSTRATE|G_TRAIN|G_EVAL|G_VALIDITY|G_ARTIFACT|G_DECISION",
  "hyp": "한 줄 설명",
  "target": "목표값 or 조건",
  "expr": "측정식 or 규칙",
  "closure": "PASS 조건",
  "input_path": "파일/리소스 경로",
  "verifier_type": "corpus_regex_ratio|jsonl_schema_valid|log_grep_exact|numeric_descent|numeric_threshold|numeric_tolerance|hash_match|file_exists|r2_object_exists|benchmark_fixed_set|formula_closure|multi_seed_r_squared|coherence_check"
}
```

## 실행

```
# manifest → verify_<id>.hexa 자동 emit
hexa run shared/calc/alm_verify/generator.hexa --emit

# 상태 확인 (manifest 라인 vs stub 파일 수)
hexa run shared/calc/alm_verify/generator.hexa --status

# 전체 실행 + aggregate 리포트
hexa run shared/calc/alm_verify/run_all.hexa

# 특정 gate 만 실행
hexa run shared/calc/alm_verify/run_all.hexa --gate G_INPUT

# 새 claim 추가 (manifest append + stub emit)
hexa run shared/calc/alm_verify/generator.hexa --append '{"id":"...","round":"..."}'
```

## 출력 sentinel

각 verify_<id>.hexa 의 stdout 마지막 줄:
```
__VERIFY_RESULT__ <id> PASS|FAIL <actual> vs <target>
```

run_all.hexa 는 이 sentinel 을 pipe 에서 수집 → aggregate.

## 판정 저장

- 개별 결과: 개별 verify 실행 stdout
- 집계: `shared/state/alm_r{N}_verify_report.json` (run_all 이 emit)
- Gate breakdown + overall decision (KEEP / DISCARD) 포함

## 추가 시 주의

- manifest.jsonl append 만 (기존 라인 수정 금지 — id 변경 = 새 claim)
- deprecation 필요 시 manifest line 에 `"deprecated": true` 필드 추가 (run_all 이 skip)
- verifier_type template 은 generator.hexa 에 정의. 새 type 추가 시 generator 확장 선행.

parent: ../CLAUDE.md → "calc"
design: /Users/ghost/Dev/anima/docs/alm_clm_verifier_design_20260420.md
