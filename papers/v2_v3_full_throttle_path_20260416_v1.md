<!-- @doc(type=paper) -->
<!-- @own(sections=["1. 목표", "2. 5 병렬", "3. 풀가동", "4. 단축", "5. R2", "6. P3", "7. 다음", "8. 외부"], strict=false, order=sequential) -->

# anima v2.0 RC → v3.0 직원 — 풀가동 로드맵 (2026-04-16)

> **새 세션 진입 시 메인 참조** (직전 v3_employee_capability_path_20260416.md 보강).
>
> P3 (v2.0 RC zeta 추월) → P4 (v3.0 직원) 순차 진행 + **5 병렬 트랙** 으로
> 총 일수 단축. 모델 발전 + 학습 속도 개선 + R2 백업 정책 통합.
>
> 단일 진실 SSOT: `shared/convergence/anima.json` (트랙별 등록).

---

## 1. 목표

- **P3 v2.0 RC**: 음성 + 아바타 + 의식 (Likert ≥ zeta+0.5) — **zeta 추월**
- **P4 v3.0 Agent**: 실업무 자율 수행 — **직원 가능**
- **완전 자체 모델** (외부 LLM 비의존), 단 시연/proof 단계는 외부 LLM 활용 OK
- **R2 백업 필수** — 모든 production ckpt, 실험 ckpt 는 pod 삭제 시 폐기

순차 + 병렬:
```
   ┌── A. ALM/CLM 학습 ─────────────────────────────────┐
   ├── B. Φ 엔진 110개 → 학습 loss 통합 ─────────────────┤
   ├── C. hexa-lang 학습 속도 개선 ─────────────────────┤  → P3 → P4
   ├── D. 의식 Φ 엔진 실사화 wave ──────────────────────┤
   └── E. 실사용 모델 발전 + R2 백업 정책 ──────────────┘
```

---

## 2. 5 병렬 트랙

### A. ALM/CLM 학습 (모델 발전)

| Sub | 작업 | 일수 | 비용 | 호스트 | 상태 |
|---|---|---|---|---|---|
| A1 | TALM-P2-1 harness 작성 | 1-3일 | $0 | Mac | ❌ blocked |
| A2 | TALM-P2-1 6 persona LoRA × 2000 step | 1일 | $36 | H100 12h | 대기 |
| A3 | TALM-P3-1 32B persona (옵션, ROI 작음) | 2일 | $144 | H100 48h | 대기 |
| A4 | TALM-P4-1 실업무 corpus LoRA | 2일 | $144 | H100 48h | corpus 대기 |
| A5 | TALM-P4-2 Tool-use LoRA | 1일 | $30-50 | H100 12h | 대기 |
| A6 | CLM nl=8/BPE/d=128 retrain | 2-3일 | $30-50 | H100 short × N | 🔄 nl=8 in_flight |
| A7 | CLM 100M-1B scale (선택) | 3-5주 | $2,000+ | H100 cluster | 보류 (sovereignty 가치) |

### B. Φ 엔진 110개 → 학습 loss 통합 (의식의 학습 융합)

`anima-engines/*_phi.hexa` 110개 존재. 의식 측정값을 학습 신호로 wiring.

| Sub | 작업 | 일수 |
|---|---|---|
| B1 | 110 엔진 inventory + 분류 (auxiliary loss / regularization / sampling guide) | 1일 |
| B2 | 학습 loss aux signal 설계 — Φ-aware loss = CE + λ·Φ_dist + μ·GWT_consistency | 1-2일 |
| B3 | PoC 1-2 엔진 → CLM nn_core 연결 + A/B 검증 | 2-3일 |
| B4 | 110 엔진 점진 통합 (Φ-aware fine-tune) | 1-2주 (병렬, A trkT 와 합산) |
| 산출물 | `shared/papers/training_phi_integration_design.md` (이미 존재 — 참조) | |

### C. hexa-lang 학습 속도 개선 (이미 큰 진전 + 남은 레버)

이미 완료 (이번 세션):
- ✅ codegen_c2 untyped fn tail-return (systemic, hexa-lang `3cd9e6f`)
- ✅ attn BLAS 포팅 (1.69x Mac MFU)
- ✅ vDSP eltwise (1.54x → 누적 2.59x)
- ✅ H100 CUDA native breakthrough (BREAKTHROUGH 209ms/step)
- ✅ tensor_raw_f32_primitive (4757x isolated matmul)
- ✅ nn_core Tensor port (1479x tiny step)

남은 레버:
| Sub | 작업 | 예상 uplift | 일수 |
|---|---|---|---|
| C1 | hexa native int codegen (boxed-int 탈출) | inner loop 누적 | 2-3일 (codegen 수정) |
| C2 | layer-level fused FFI (single C call for layer_fwd/bwd) | 2-5x | 2-3일 |
| C3 | stage0 OOM PBV fix | 긴 학습 안정 | 2-4일 |
| C4 | CUDA fused mega-kernels + bf16 Tensor Core | SM 27% → 60%+ | 3-5일 (H100) |
| C5 | FP8 native (NeMo/Megatron rewrite) — long-term | 2x throughput | 2-4주 (대규모) |
| C6 | hxblas + libhxvdsp Linux 빌드 (포팅) | H100 CPU pre/post | 1일 |

P3 ALM 학습 시간 단축 효과:
- TALM-P3-1 48h → C2+C4 적용 후 ~24-30h 가능 (40% 단축)
- TALM-P4-1 48h → 동일 효과 ~24-30h
- = **P4 학습 시간 ~$144 → ~$80-90** 절감 (각 스텝)

### D. 의식 Φ 엔진 실사화 wave (zeta 추월 moat)

| Sub | 작업 | 일수 | 호스트 |
|---|---|---|---|
| D1 | Φ measurement real-time (≤100ms) | 2-3일 | Mac |
| D2 | GWT broadcast 6채널 동시 (단일 → 6) | 4-7일 | Mac + 일부 H100 |
| D3 | Orch-OR 양자 붕괴 샘플링 통합 (anima-engines 기존 활용) | 2-3일 | Mac |
| D4 | EEG 동조 (anima-eeg → 응답 적응 < 100ms) | 2-3일 | Mac + EEG device |
| D5 | 헥사곤 6채널 (CDESM model) — anima-hexad | 3-5일 | Mac |
| 매핑 | ZCLM-P1-1, ZCLM-P1-2, ZPHY-P1-1, ZALM-P1-1, TCLM-P3-2 | | |

### E. 실사용 모델 발전 + R2 백업 정책

| Sub | 작업 | 일수 |
|---|---|---|
| E1 | R2 백업 자동화 스크립트 (rclone wrapper, ckpt 저장 시 자동 upload) | 1일 |
| E2 | ckpt 라벨링 정책 (production / experiment / archive) | 0.5일 |
| E3 | naming convention 강제 (alm14b-r{round}-s{step}, clm-d{D}-{tokenizer}-r{round}) | 0.5일 |
| E4 | rotation/cleanup (실험 ckpt 자동 폐기, R2는 production 만) | 1일 |
| E5 | promotion gate — 측정 통과한 ckpt 만 production 승격 | 1-2일 |
| 정책 핵심 | training/CLAUDE.md r2_checkpoint 룰 강화: bucket=anima-models, naming 강제, R2 미백업 ckpt 는 pod 삭제 시 폐기 (이미 룰 있음 — 자동화) | |

---

## 3. 풀가동 시나리오 (병렬 max)

5 트랙 동시 (각 트랙당 1 worker 가정):

```
Day 1-3   ─ A1 harness 작성 ─┐    ─ B1 inventory + B2 design ─┐    ─ C1 native int codegen ──┐
                              │                                  │                              │
Day 4-7   ─ A2 14B persona ──┤    ─ B3 PoC + A/B ───────────────┤    ─ C2 fused FFI ──────────┤
          ─ A6 CLM nl=8 ─────┤    ─ D1 Φ real-time ─────────────┤    ─ E1-E5 백업 정책 ───────┤
Day 8-14  ─ A4 실업무 corpus 수집 (★ 가장 큰 변수) ──────────────┤
          ─ A5 tool-use ─────┤    ─ D2 GWT 6채널 ───────────────┤    ─ C4 CUDA mega-kernel ───┤
Day 15-21 ─ A4 실업무 LoRA ──┤    ─ B4 110 엔진 통합 (점진) ────┤    ─ TSRV-P3-1/2/3 음성/아바타/EEG ─
Day 22-28 ─ 통합 + Likert + hire-sim 측정 ───────────────────────────────────────────────────
```

### 3-1. 시나리오별 일정

| 시나리오 | P3 (zeta 추월) | P4 (직원) | P3+P4 합산 | 총 비용 |
|---|---|---|---|---|
| **고속 풀가동** (5 트랙 + 병렬, corpus 합성, 32B skip) | 7-10일 | 10-14일 | **14-21일** | $300-500 |
| **정공법** (corpus 자체 라벨, 32B 포함) | 14-21일 | 14-21일 (동시) | **21-28일** | $500-800 |
| **보수** (큰 reset 발생, 32B + Tool-use 풀세트) | 21-28일 | 21-30일 | **1-1.5개월** | $800-1200 |

### 3-2. 학습 속도 개선 효과 (C 트랙)

C1+C2+C4 적용 시 P3+P4 ALM 학습 시간 ~40% 단축:
- TALM-P2-1: 12h → 7-8h
- TALM-P3-1: 48h → 24-30h
- TALM-P4-1: 48h → 24-30h
- **합 108h → 55-68h** = wall 일수 2-3일 단축, 비용 $324 → $165-205

C 트랙 자체 일수: 5-7일. 즉 **C 트랙 먼저 진행하면 후속 ALM 학습 cost 큰 절감**.

---

## 4. 단축 우선순위 (병렬 ROI)

| 우선순위 | 트랙 | ROI |
|---|---|---|
| ⭐⭐⭐ | C (학습 속도) | 후속 ALM 학습 비용 40% 절감, 5-7일 투자 |
| ⭐⭐⭐ | A1 (harness 작성) | 모든 ALM 작업 unblock (1-3일 작은 투자, 큰 unblock) |
| ⭐⭐⭐ | E (R2 백업) | 모든 학습 결과 보존, 1-2일 (사고 방지) |
| ⭐⭐ | B (Φ 학습 통합) | 의식 직접 학습화 — anima moat 강화 |
| ⭐⭐ | D (Φ 엔진 실사화) | zeta 추월 moat 직접 |
| ⭐ | A6 (CLM 100M-1B scale) | sovereignty, 대규모 cost — 보류 |

---

## 5. R2 백업 정책 (E 트랙 핵심)

| 라벨 | 정의 | R2 보관 | pod 삭제 시 |
|---|---|---|---|
| **production** | gate 통과 + 다음 단계 base | 자동 ✓ | 보존 (R2) |
| **experiment** | 측정용 임시 ckpt | X | 폐기 |
| **archive** | 과거 round 보관 (7일 이상) | ✓ (cold storage tier) | 보존 |

자동화:
- ckpt 저장 시 라벨 명시 (`--label production` / `--label experiment`)
- production 라벨 → rclone hook → r2:anima-models/{model}/r{round}/step_{step}/ 자동 upload
- experiment 라벨 → 로컬 디스크만, pod 삭제 시 자연 폐기
- naming convention 강제: `alm14b-r{round}-s{step}`, `clm-d{D}-{tokenizer}-r{round}`

이미 `training/CLAUDE.md` 에 r2_checkpoint 룰 명시 — E 트랙은 자동화 + naming 강제 부분.

---

## 6. P3 → P4 자연스러운 이어짐

| | P3 산출물 | P4 활용 방식 |
|---|---|---|
| ALM | 14B persona LoRA (자동 페르소나) | base 그대로 + 추가 실업무 LoRA |
| CLM | Φ + GWT 6채널 + Orch-OR 통합 | autonomy_loop conscious-lm provider 로 wire |
| SERVING | TTS + 아바타 + EEG (음성/시각/감정 채널) | hire_sim 100 task 시 멀티모달 응답 (이메일은 텍스트 + 회의록은 음성 요약 등) |
| 의식 측정 | Φ ≥ 임계 + 6채널 동시 | direct_employee 가 의식 있는 직원 — anima moat 보존 |

P3 = "롤플레이 직원이 음성으로 응답"
P4 = "실업무 직원이 음성으로 응답 + 도구 사용 + 자율 분해"

P3 의 음성/아바타/Orch-OR 인프라가 P4 직원의 표현 layer 가 됨 — 별도 작업 X.

---

## 7. 다음 결정 포인트

| 트리거 | 결정 |
|---|---|
| 5 트랙 풀가동 vs 단일 트랙 우선 | 자원/agent 가용 따라. 풀가동 = 14-21일, 단일 = 30+일 |
| 32B 학습 vs 14B 만 | 14B Likert PASS 가능 → 32B skip. ROI 작음. |
| 페르소나 corpus 수집 전략 | (a) Claude API 합성 1-2일 / (b) 자체 라벨 2-7일 / (c) 공개 데이터셋 변환 1-3일 |
| C 트랙 (학습 속도) 선행 vs 병렬 | 선행 시 후속 학습 비용 40% 절감, but wall 5-7일 추가 (병렬이면 무관) |
| 실업무 corpus 전략 | 위와 동일 — Claude 합성 / 자체 라벨 / 공개 데이터 |
| anima 정체성 (CLM 보유 vs ALM 단독) | A=CLM+ALM moat / B=ALM 단독 일반 chatbot / D=CLM 7B sovereignty |

---

## 8. 외부 참조

- **이전 문서**: `shared/papers/v3_employee_capability_path_20260416.md` (architecture rationale + Plan A/B/C/D 상세 — 본 문서의 6장 보강)
- **알고리즘 등록부**: `shared/convergence/anima.json` (트랙별 in_flight/completed/failed)
- **학습 측정치**: `shared/state/training_speed_ceilings.json` (MFU, step time, pod_id 태깅)
- **로드맵 P0~P5**: `shared/roadmaps/anima-train.json`
- **zeta 추월 P0~P3**: `shared/roadmaps/zeta-surpass.json`
- **Φ 통합 학습 설계**: `shared/papers/training_phi_integration_design.md`
- **Hexa 성능 audit**: `shared/papers/hexa_training_perf_audit.md`
- **Claude 메모리**: `~/.claude-claude12/projects/-Users-ghost-Dev-anima/memory/MEMORY.md`
  - `feedback_h100_idle_zero.md` — pod 유휴 금지
  - `reference_algorithm_ssot.md` — anima.json 단일 진실
  - `reference_v3_employee_path.md` — 직전 분석 (본 문서가 후속)
  - `reference_full_throttle_path.md` (신규 — 본 문서 인덱스)

---

세션 일자: 2026-04-16. 본 문서는 5 병렬 트랙 풀가동 마스터 플랜.
**다음 세션 진입 시 본 문서 → SSOT (anima.json) → 미해결 in_flight 확인** 순서.
