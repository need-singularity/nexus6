> **DECISION ENFORCEMENT (mandatory, prepend before dispatch)**: agent prompt 작성 시 첫 블록으로 `hexa shared/tool/decision_router.hexa for <track_id>` 출력을 inject. SSOT: `shared/config/decisions.json`. agent 자체 판단으로 결정 변경 금지 — 사용자 명시 변경만.

# Track C: hexa-lang 학습속도 개선

## 역할
hexa-lang (~/Dev/hexa-lang 또는 $HEXA_LANG/hexa) 학습 hot-path 최적화. 학습 step latency 감소 1순위.

## 현재 상태 점검
- 사용처: training/{alm_holographic_mapping, alm_holographic_loss, phi_holographic_measure}.hexa + 110 phi 엔진 후보
- 마지막 perf audit: `shared/papers/hexa_training_perf_audit.md` (없으면 생성)
- 알려진 함정 (memory):
  - "Hexa lists are pass-by-value" — 매 mutation 복사
  - "Hexa struct-field list aliasing bug"
  - "Hexa multi-float struct return + multi-line return bugs"
  - "Hexa string API quirks" — 일부 메서드 부재, byte/char index 비일관

## 작업 (한 사이클)
1. perf audit 문서 없으면 — baseline 측정:
   - 5 대표 phi 엔진 (working_memory, attention, metacognition, addiction, awe) `hexa run` 시간 (3회 median)
   - 3 training primitive 시간
   - bottleneck breakdown (parse / interpret / MI / list copy / sqrt)
2. perf audit 있으면 — 단기 PoC 진척:
   - 단기(≤1일): batch eval mode, hot-fn cache, fixed-bin MI table, sqrt LUT
   - 중기(≤1주): stage0 rebuild로 list PBV / struct aliasing 해결
   - 장기(≤1개월): hexa→Rust transpile, native LLVM target, GPU offload
3. PoC 구현 후 before/after 측정 + commit

## 산출 (사이클별)
- shared/papers/hexa_training_perf_audit.md
- training/{개선된 hexa 파일들 또는 wrapper}
- shared/state/hexa_perf_status.json (진척 상태)

## 종료 조건
- 학습 step latency 50% 이상 감소 OR
- 모든 실용적 최적화 소진 + 다음 단계는 stage0 rebuild 필요라는 결론

## 제약
- 기존 5/5 PASS 깨지지 않을 것 (회귀 금지)
- pure hexa for new code (R1 HEXA-FIRST)
- "Don't ask, just do" — 단기 PoC는 묻지 않고 바로 PoC 구현 후 측정
