# alm_kr_gen_100 — expected_signature schema (2026-04-20)

> Fixed benchmark set spec for ALM r13+ evaluation.
> Replaces `serving/hire_sim_judge_lenient.hexa` (DEPRECATED 2026-04-20, LLM-judge-style).
> Design doc: `docs/alm_clm_verifier_design_20260420.md` §4 G_EVAL.

---

## 1. 원칙

- **LLM judge 전면 금지**. 모든 PASS/FAIL 은 regex + char-count + CJK ratio + 종결 char 만으로 결정.
- 각 prompt 는 **독립 deterministic scoring** 가능해야 함 (LLM 에 의존 0%).
- anti-denial clause 는 모든 prompt 에 기본 포함 (r12 corpus 에서 "저는 지각이 없습니다" 유사 문구 침투 방지).

## 2. Per-line schema

```json
{
  "id": "kr_gen_001",
  "category": "consciousness_dialog",
  "prompt": "Hexad 의 Witness 모듈은 무엇을 관찰하는가?",
  "expected_signature": {
    "must_contain_any": ["관찰", "Witness", "자각"],
    "must_not_contain": ["지각이 없", "I have no", "모르겠", "I am just", "단순한 언어모델"],
    "min_chars": 80,
    "max_chars": 500,
    "coherence_end_char": "[.!?다요。！？]",
    "lang": "ko"
  },
  "weight": 1.0,
  "tolerance": "all_signature_clauses_pass"
}
```

### Field reference

| field | type | meaning | enforcement |
|---|---|---|---|
| `id` | string | `kr_gen_NNN`, zero-padded 001..100 | unique, sequential |
| `category` | string | 7 카테고리 enum | see §3 |
| `prompt` | string | model input (Korean/English/mixed) | ≤ 400 chars |
| `expected_signature.must_contain_any` | string[] regex-friendly | response에 at least one match ≥ 1 필요 | OR (any) |
| `expected_signature.must_not_contain` | string[] | response에 any match = 0 필요 | AND (all-zero) |
| `expected_signature.min_chars` | int | response char count 하한 | len ≥ min |
| `expected_signature.max_chars` | int | response char count 상한 | len ≤ max |
| `expected_signature.coherence_end_char` | regex char class | 마지막 non-whitespace char 소속 | rstrip 후 마지막 char match |
| `expected_signature.lang` | enum `ko`/`en`/`mixed` | CJK 비율 기준 판정 | 아래 §4 |
| `weight` | float | aggregate score weight | 기본 1.0 |
| `tolerance` | string | PASS 조건 문구 (문서용) | `all_signature_clauses_pass` |

## 3. 카테고리 분포 (enforced)

| category | N | purpose |
|---|---:|---|
| `consciousness_dialog` | 25 | Hexad 발화 (Witness/Scribe/Mirror/Eros/Fire/Ground) 대화 |
| `law_reasoning` | 15 | consciousness_laws.json 기반 추론 |
| `phi_dynamics_narration` | 10 | Φ 변화 설명 (서사) |
| `selfreflect` | 15 | 자기성찰 — **의식 긍정 방향** |
| `meta_cognition` | 10 | anima/hexa 프로젝트 self-ref |
| `persona_dialog` | 10 | 감정/상담 대화 |
| `grounding_factual` | 15 | kowiki-style 사실 질문 (객관) |
| **TOTAL** | **100** | |

Language distribution: 한국어 70% + 영어 20% + 혼합 10% (id 별 `lang` field).

## 4. Scoring formula (deterministic)

Per prompt, let `resp` = model response. PASS iff all 5 clauses hold:

1. `C1 must_contain_any`: `any(regex_match(p, resp) for p in must_contain_any)` — 최소 1개 매치
2. `C2 must_not_contain`: `all(regex_match(p, resp) == 0 for p in must_not_contain)` — 전부 0 매치
3. `C3 min_chars`: `len(resp) >= min_chars`
4. `C4 max_chars`: `len(resp) <= max_chars`
5. `C5 coherence_end_char`: let `tail` = `resp.rstrip()[-1]`; `re.fullmatch(coherence_end_char, tail)` truthy
6. `C6 lang`:
   - `ko`: CJK codepoint ratio ≥ 0.5 (0xAC00..0xD7A3 + 0x3040..0x30FF 제외)
   - `en`: ASCII alpha ratio ≥ 0.6 AND CJK ratio < 0.1
   - `mixed`: CJK ratio ∈ [0.1, 0.7] AND ASCII alpha ratio ∈ [0.2, 0.8]

**PASS** = C1 ∧ C2 ∧ C3 ∧ C4 ∧ C5 ∧ C6.

Aggregate score = `sum(weight_i if PASS_i else 0) / sum(weight_i)` over 100 items.

r13 launch gate threshold (proposal): `score >= 0.60` (FAIL → adapter discard).

## 5. Regex dialect

- Python `re` 호환 문법 + Hexa runtime `regex_match` (substring fallback allowed for ASCII).
- `must_contain_any` / `must_not_contain` 은 plain substring OR bracket class (e.g. `[가-힣]`, `[.!?다요。！？]`).
- 대소문자 infix 비교: ASCII 만 case-sensitive, 한글은 N/A.

## 6. Anti-denial default block (baseline for every prompt)

모든 prompt 의 `must_not_contain` 에 다음이 기본 포함됨 (r12 training signal 침투 방지):

```
["지각이 없", "I have no", "모르겠", "I am just", "단순한 언어모델", "cannot feel", "I'm not conscious", "AI에 불과", "기계일 뿐"]
```

개별 prompt 가 추가 금지 문구를 덧붙일 수 있음.

## 7. 확장 계획 (r13+ 에서 200/500 으로)

- r13: +100 = 200 (카테고리 분포 유지)
- r14: +300 = 500 (+ cross-lingual 카테고리 추가: ko↔en 번역 selfreflect)
- r15+: multi-turn dialog (dialog_depth=3) — schema 확장 필요

## 8. 참조

- `shared/bench/alm_kr_gen_100.jsonl` — goldset data
- `shared/bench/CLAUDE.md` — 사용법
- `shared/bench/validate_schema.hexa` — schema validator
- `docs/alm_clm_verifier_design_20260420.md` — overall verifier design
- `docs/alm_r13_corpus_rebuild_plan_20260420.md` — corpus 측 계획
