> **DECISION ENFORCEMENT (mandatory, prepend before dispatch)**: agent prompt 작성 시 첫 블록으로 `hexa shared/tool/decision_router.hexa for <track_id>` 출력을 inject. SSOT: `shared/config/decisions.json`. agent 자체 판단으로 결정 변경 금지 — 사용자 명시 변경만.

# Track E: 실사용 모델 발전

## 역할
실사용 production 모델만 진척. **실험 체크포인트 / 디버그 / smoke run 제외**. R2 백업 필수.

## 정의: "실사용 모델"
- 가장 최신 골화된 stable 체크포인트 (예: animalm_14b_v06/final.pt)
- eval_loss + downstream 평가 통과
- R2 anima-models 버킷에 백업 완료
- 사용자에게 실제 서빙 가능한 후보

## 작업 (한 사이클)
1. 현 production 모델 식별:
   - `shared/state/production_model_status.json` 읽기 (없으면 생성)
   - 가장 최근 stable 체크포인트 찾기 (`models/`, `checkpoints/`, R2 inventory)
   - 후보 목록 + 각 모델의 quality 지표 (eval_loss, phi_holo, downstream score)
2. R2 백업 상태 확인:
   - rclone ls r2:anima-models | grep <current> — 누락 시 즉시 업로드
   - 체크섬 검증 (sha256 또는 R2 ETag)
3. quality 비교:
   - 새 체크포인트(예: r5 step_2000)가 이전 production을 능가하는지 — eval_loss + phi_holo + 한국어 대화 정성 평가
   - 능가하면 새 production 후보로 승격
4. 승격 결정 시:
   - shared/state/production_model_status.json 업데이트 (이전 → 신규)
   - R2 백업 검증 (필수)
   - 사용자에게 승격 보고 (이전 vs 신규 비교표)
5. commit + push

## 산출 (사이클별)
- shared/state/production_model_status.json (current production + history)
- R2 백업 상태 (해당 체크포인트가 anima-models에 있는지)
- production 승격 시 — 비교 보고 (eval_loss/phi_holo/qualitative)

## 종료 조건
- 새 production 모델 승격 + R2 백업 검증 OR
- 현 production이 여전히 최선 (새 후보 없음) → status 갱신만

## 제약 (절대 위반 금지)
- 실험 체크포인트 (smoke / debug / test run) 절대 production 승격 금지
- R2 백업 누락 상태로 production 승격 금지
- Web UI/API/배포 인프라 작업은 이 트랙 범위 아님 (별도 트랙)
- "no-quantization" — production 모델 양자화 금지
- "no-version-in-filename" — production 파일명에 v2/v15 등 금지

## 메모리 참조
- `feedback_r2_checkpoint.md` — 중요 구간 모델 체크포인트는 반드시 R2에 보관
- `feedback_no_quantization.md` — 모델 양자화 금지
- `project_v01_release.md` — v0.1 release plan (R2 업로드 + 다운로드 등록)
- `reference_r2_buckets.md` — anima-memory (state) + anima-models (checkpoints)
