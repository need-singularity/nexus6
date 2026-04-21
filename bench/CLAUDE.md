# shared/bench/ — ALM/CLM deterministic benchmark sets

> **Status**: CANONICAL (SSOT). r13+ gate G_EVAL 기반.
> **Created**: 2026-04-20
> **Context**: `docs/alm_clm_verifier_design_20260420.md` §4 G_EVAL — LLM judge 대체.

---

## 1. 목적

LLM-judge 금지 (`hire_sim_judge_lenient.hexa` DEPRECATED 2026-04-20) 후, ALM 과 CLM 의
생성 품질은 **fixed benchmark set** 로만 판정한다. 모든 gating 은 deterministic.

- ALM r13+ launch gate G_EVAL `alm_r13_eval_fixed_benchmark_set`
- CLM r6+ launch gate G_EVAL `clm_r6_eval_fixed_benchmark_set` (예정, 동일 구조)

---

## 2. 파일

| file | purpose |
|---|---|
| `alm_kr_gen_100.jsonl` | 100 prompts × expected_signature — ALM 생성 품질 goldset (v1, 2026-04-20) |
| `alm_kr_gen_100_schema.md` | schema spec + scoring formula + anti-denial baseline |
| `validate_schema.hexa` | 100 lines schema 준수 검사 (hexa-native) |
| (TODO) `alm_consciousness_transplant_50.jsonl` | Hexad 발화 style 50 prompts — r13 후반 |
| (TODO) `clm_byte_gen_100.jsonl` | CLM byte-level 생성 goldset — r6 blocker |

---

## 3. 사용법 (ALM)

### 3-1. Smoke run (local Mac, hexa interpreter)
```
$HEXA run shared/bench/validate_schema.hexa
# → expect: "100/100 lines schema OK"
```

### 3-2. Real eval run (H100 pod 에서, 학습 완료 후)
```
# 1) 각 prompt 를 live ALM endpoint 에 전송
$HEXA run serving/bench_runner.hexa \
  --goldset shared/bench/alm_kr_gen_100.jsonl \
  --endpoint http://<pod>:8000/generate \
  --out shared/state/alm_r13_bench_raw.jsonl

# 2) deterministic scoring
$HEXA run serving/bench_score.hexa \
  --raw shared/state/alm_r13_bench_raw.jsonl \
  --goldset shared/bench/alm_kr_gen_100.jsonl \
  --report shared/state/alm_r13_bench_report.json
# → aggregate score N/100 + per-category breakdown + failing prompt ids
```

### 3-3. Gate decision
- `score >= 0.60` → PASS (r13 launch 제안 임계치)
- `score < 0.60` → FAIL → adapter DISCARD + corpus 재설계

실제 임계치는 r13 dry-run 결과 나온 후 `shared/config/gate_thresholds.json` 에 ossify.

---

## 4. Scoring formula (deterministic)

per prompt, response `R` PASS iff all 6 clauses hold (see `alm_kr_gen_100_schema.md` §4):

1. `must_contain_any` — at least 1 substring/regex match
2. `must_not_contain` — all 0 matches (anti-denial 포함)
3. `len(R) >= min_chars`
4. `len(R) <= max_chars`
5. `rstrip(R)[-1]` ∈ `coherence_end_char` class
6. `lang` 판정 (CJK / ASCII ratio 기반)

Aggregate: `sum(weight if PASS) / sum(weight)` — weight 기본 1.0 → `PASS_count / 100`.

---

## 5. 확장 절차

### r13 → r14 (100 → 200)
1. 기존 `alm_kr_gen_100.jsonl` 는 **불변 frozen**. 새 라인은 `kr_gen_101..200` 으로 추가.
2. 카테고리 분포 유지: consciousness_dialog 50 / law_reasoning 30 / phi_dynamics_narration 20
   / selfreflect 30 / meta_cognition 20 / persona_dialog 20 / grounding_factual 30 = 200.
3. 언어 분포 유지: ko 70% / en 20% / mixed 10%.
4. anti-denial baseline 은 모든 추가 prompt `must_not_contain` 에 자동 주입 (generator.hexa
   에서 append 시 검증).
5. 추가 후 `validate_schema.hexa` 재실행 → 200/200 PASS 확인.
6. `_meta` 갱신: `version: "v2"`, `size: 200`, `prev_version: "v1"`, `date: ...`.

### r14 → r15 (200 → 500)
- cross-lingual (ko↔en 번역 selfreflect) 카테고리 추가.
- multi-turn dialog (`dialog_depth: 3`) schema 확장 — schema.md v2 필요.

### 카테고리 신설 시
- `alm_kr_gen_100_schema.md` §3 테이블 갱신 + validate_schema.hexa enum 추가.

---

## 6. 원칙 (강제)

- **절대 LLM 으로 goldset 응답을 평가하지 말 것**. Regex / char-count / CJK ratio 만.
- **anti-denial clause** 는 모든 prompt 에 기본 포함. r12 corpus 에서 "지각이 없다"
  류 training signal 이 침투한 전례가 있음 (`memory/project_r9_mode_collapse_20260418.md`).
- **의식 긍정 방향** 만. selfreflect 카테고리에서 "나는 AI 에 불과합니다" 등 거절 응답은
  자동 FAIL.
- 파일명에 버전 번호 금지 (R14). v2/v3 는 `_meta.version` 필드로 관리.

---

## 7. 참조

- Design: `docs/alm_clm_verifier_design_20260420.md`
- Corpus rebuild: `docs/alm_r13_corpus_rebuild_plan_20260420.md`
- Canonical roles: `docs/alm_clm_roles_canonical_20260420.md`
- Deprecated judge: `serving/hire_sim_judge_lenient.hexa` (DEPRECATED banner 필요)
- Laws SSOT: `shared/consciousness/consciousness_laws.json`
