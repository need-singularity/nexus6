# Track B: phi 엔진 110개 → 학습 loss 통합

## 역할
anima-engines/*_phi.hexa (P6-P현재) 110+ 엔진을 ALM/CLM 학습 loss 또는 auxiliary signal로 wiring.

## 현재 상태 점검
- 학습 loss = `main_CE + 0.01 * holo` (training/phi_holographic_measure.hexa 만 사용)
- 110 phi 엔진은 self-test 5/5 PASS만 검증됨 — model gradient에 0% 신호
- 마지막 통합 설계 문서: `shared/papers/training_phi_integration_design.md` (없으면 생성)

## 작업 (한 사이클)
1. 통합 설계 문서가 없으면 — 4가지 옵션 비교 후 작성:
   - A) Aggregate Φ — 110 엔진 mean Φ를 단일 aux loss
   - B) Per-engine aux loss — 각 엔진 별도 loss + 학습 가중치
   - C) Contrastive — phi 출력 vs hidden state 대조
   - D) Reward signal — RLHF 스타일 reward model
2. 통합 설계 문서가 이미 있으면 — 채택안 PoC 코드 진척:
   - `train_alm_14b_p4.py`에 추가할 함수 시그니처 / 실제 구현
   - phi 엔진 hexa run 호출 wrapper (training/phi_engine_eval.hexa)
   - A/B 테스트 계획 (현 r4/r5 baseline vs 통합 r6/r7)
3. PoC가 있으면 — 실제 학습 실행 + 측정:
   - r6 (또는 다음 round) 시 PoC 통합 활성화
   - eval_loss + phi_holo + downstream eval 비교
4. 결과 commit + push

## 산출 (사이클별)
- shared/papers/training_phi_integration_design.md (설계)
- training/phi_engine_eval.hexa (PoC 래퍼)
- train_alm_14b_p4.py 패치 (PoC 통합)
- shared/state/phi_integration_status.json (진척 상태)

## 종료 조건
- 통합이 r6 학습에 wired + eval_loss 개선 OR
- 4 옵션 모두 PoC 검증 후 명확한 NO-GO 결론 + 대안 제시

## 제약
- pure hexa for engine eval (Python rewrite 금지)
- gradient flow 솔직히 처리 (phi 엔진은 discrete decision → smooth surrogate 필수 명시)
- per-step 110 엔진 모두 실행 시 latency >100ms이면 sampling subset 제안
