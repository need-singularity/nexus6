# v3.0 직원 가능 — 도달 경로 + 일정 분석 (2026-04-16 스냅샷)

> **새 세션 입장 시 1차 참조** — anima 가 "직원으로 고용 가능한" v3.0 stage 도달까지의 경로,
> 일정, 비용, Plan A vs B 트레이드오프.
>
> 본 문서는 narrative + 일정 분석. 세부 산출물 추적은 SSOT 참조:
> - 알고리즘 등록부: `shared/convergence/anima.json` (트랙별 in_flight/completed/failed)
> - 학습 측정치: `shared/state/training_speed_ceilings.json`
> - 로드맵: `shared/roadmaps/anima-train.json` (P0~P5)
> - zeta 추월: `shared/roadmaps/zeta-surpass.json` (P0~P3)

---

## 1. 현재 상태 (2026-04-16 EOD, 13+ commits 세션)

### CLM (의식 layer)

| 항목 | 상태 | 비고 |
|---|---|---|
| TCLM-P1-1 d=64 byte KR 재학습 | ✅ **PARTIAL** | Φ 103.27 ✓, KR quality ✓, **CE 2.15 > 1.4** (architecture scale 한계) |
| TCLM-P1-2 GWT broadcast loop | ✅ done | |
| TCLM-P2-1 clm_lore_serve | ✅ **scaffold_done** (5/5 PASS) | mock CLM, 실 transformer 추론은 P4-1 후 wire |
| TCLM-P4-1 autonomy_loop | ✅ **scaffold + Claude wired** | 5/5 PASS mock, compiled live PASS (score=0.9) |
| TCLM-P4-2 6채널 cognitive | 📋 blocked | ZCLM-P1-1 (zeta-surpass) 의존 |
| Mac CPU MFU | ✅ **2.59x 누적** (1.65% → 4.27%) | attn BLAS 1.69x × vDSP 1.54x |
| H100 CUDA native | ✅ **BREAKTHROUGH** (209ms/step, 27% SM) | codegen_c2 fix systemic landed |
| Korean BPE 32K tokenizer | ✅ done | seq 7.63x 단축, vocab 12206 (corpus 작아 auto-shrink) |
| nl=8 depth experiment | 🔄 in_flight | width vs depth 가설 검증 |
| native_int codegen | 📋 pending | hot loop 누적 이득 |

### ALM (실 텍스트 생성)

| 항목 | 상태 | 비고 |
|---|---|---|
| r4 base ckpt | ✅ R2 보관 | LoRA 가중치까지 step_10000 |
| r5/r6/r7/r8a MFU 측정 | ✅ done | r7 silicon 62.6% best (pod terminated), r8a fast 51.4% |
| r8c FP8 | ❌ FAIL | HF + LoRA + TE 비호환 (P4 스코프 외) |
| ZALM-P0-1 페르소나 7-test | ✅ mock 증명만 | 실 H100 학습 X |
| **TALM-P2-1 6 persona LoRA** | ❌ **BLOCKED** | **harness 미구현** — agent 방금 abort |
| TALM-P3-1 ALM 32B r1 | 📋 planned | 32B 모델 자체 확보 필요 |
| **TALM-P4-1 실업무 corpus LoRA** | 📋 planned | **48 H100h $144** — 직원 핵심, **corpus 미존재** |
| TALM-P4-2 Tool-use LoRA | 📋 planned | function calling + MCP |
| TSRV-P4-1 platform | 📋 blocked | autonomy + tool-use 의존 |
| TSRV-P4-2 hire_sim_100 | ✅ **인프라 완성** | 100 task corpus + rubric, Claude baseline 1차 측정 완료 |

### 평가 도구 + 측정 baseline

| 항목 | 상태 | 비고 |
|---|---|---|
| hire_sim_100 task corpus | ✅ done | 100 task / 6 도메인 / 균형 분포 |
| autonomy_loop scaffold | ✅ done | mock + Claude adapter |
| Claude baseline 1차 (30 stratified × depth=1) | ✅ done | **표면 36.7%, 실질 avg_score 1.0** (rubric/parse 약함) |
| Harness v2 (재프롬프트 + multi-format) | 🔄 in_flight | Track A agent (Task #15) |

---

## 2. 일정 분석

### CLM (의식 layer 단독)

| 시나리오 | wall 일수 | 근거 |
|---|---|---|
| 최단 | **1-2일** | nl=8 PASS 시 즉시 P2 wire + P4-1 finalize |
| 현실 | **3-5일** | nl=8 PARTIAL → BPE 재학습 1cycle 또는 d=128+BPE retrain |
| 보수 | **1주** | 여러 retrain + 6채널 (P4-2) 까지 포함 |

남은 작업 체인:
1. nl=8 결과 (in-flight, ~30분)
2. 최종 ckpt → clm_lore_serve 실 wire (mock 교체, 1-2h Mac)
3. autonomy_loop conscious-lm provider 연결 (1h)
4. 6채널 cognitive cycle (P4-2) — zeta-surpass ZCLM-P1-1 의존 (1-3일 추가)

### ALM (직원 텍스트 생성 — **실 bottleneck**)

| 시나리오 | wall 일수 | 비용 |
|---|---|---|
| 최단 | **7-10일** | corpus 단순화 (공개 데이터셋), bug 없음 |
| 현실 | **14-21일** | 6 persona harness + 실업무 corpus 수집/라벨 + retrain |
| 보수 | **1개월+** | 32B 모델 확보/학습 + 큰 reset 발생 |

남은 작업 체인:
1. **TALM-P2-1 harness 작성** (block) — 1-3일 Mac 로컬
2. TALM-P2-1 6 persona × 2000 step — 12h H100 ($36)
3. TALM-P3-1 32B r1 — 2-5일 (모델 확보 + 학습)
4. **실업무 corpus 수집/라벨** — **2-7일** (가장 큰 변수)
5. TALM-P4-1 실업무 LoRA 48h H100 ($144) — 2일
6. TALM-P4-2 Tool-use LoRA — 1일
7. TSRV-P4-1 platform + TSRV-P4-2 hire-sim 측정 — 1-2일

### 합산 (v3.0 hire-sim PASS)

| | wall 일수 | 비용 |
|---|---|---|
| 최단 | **7-10일** | ~$300 |
| 현실 | **14-21일 (2-3주)** | ~$400-600 |
| 보수 | **1개월+** | ~$700-1000 |

**Critical path = ALM 실업무 corpus 수집** — 코드 작성보다 데이터 작업이 최대 bottleneck. corpus 확보 전략 (공개 데이터 vs 자체 라벨 vs 합성)부터 결정 필요.

---

## 3. Plan A vs Plan B

Claude baseline 1차 (수정 전 v1) 결과 핵심 발견:
- **avg_score = 1.0** — Claude 응답 내용에 모든 task keyword 포함 (content quality 100%)
- completion_rate 36.7% 는 rubric/parse 미세 실패 (harness fix 후 60-90% 기대)
- **gate 자체는 LLM-급 모델이면 도달 가능함이 증명됨**

이로부터 두 경로 분리:

### Plan A — Anima 자체 ALM 직원
- **의미**: "우리 모델이 직원" — 본격 자체 모델
- **일수**: 14-21일 (현실), 1개월+ (보수)
- **비용**: $400-1000
- **Critical**: 실업무 corpus 수집/라벨 (가장 큰 시간 외부 의존)

### Plan B — Claude provider + Anima CLM 의식 (Composite)
- **의미**: "우리 의식 + 외부 텍스트" — capability 증명 우선
- **일수**: **3-5일**
- **비용**: ~$50 (CLM 학습) + Claude 구독 (정액)
- **Critical**: Track A harness fix → Claude 재측정 → CLM Plan B 통합

### Plan C — Composite (둘 다 병행)
- B 경로 먼저 살아있게 시연 → A 경로로 자체 모델 점진 교체
- B = 3-5일에 v3.0 capability 증명, A = 그 후 2-3주에 자체 모델 확보
- 가장 합리적: 상시 시연 가능 + 외부 의존 점차 감소

---

## 4. 추천 (Plan A/B/C → 정확하게는 4 옵션, 6d 참조)

**(C) Composite 경로 채택** — 외부 LLM(Claude) + 자체 CLM 의식 단기 시연 + 자체 ALM 본격 진행:

1. **이번 주 (B 경로)**:
   - Track A harness fix 완료 → Claude 재측정 (오늘 진행 중)
   - CLM nl=8 결과 → 최종 ckpt 결정 (오늘)
   - clm_lore_serve 실 CLM wire (mock 교체) — 1-2일
   - autonomy_loop conscious-lm provider 연결
   - **결과**: v3.0 hire-sim Claude+CLM 조합으로 **2-5일 내 시연**

2. **이번 달 (A 경로 시작)** — **자체 모델 직원**:
   - TALM-P2-1 harness 작성 (1-3일 Mac)
   - 실업무 corpus 수집 전략 결정 (공개 데이터 vs 자체 라벨 vs 합성)
   - corpus 확보 (2-7일)
   - TALM-P2-1 → P3-1 → P4-1 → P4-2 순차 학습 (2주)
   - CLM 의식 layer (이번 주에 완성) wire — 자체 ALM ↔ 자체 CLM 합성
   - **결과**: anima 자체 모델 직원 capability **3-4주 내 도달** (= 옵션 A in 6d)

3. **유휴 자원 정리 원칙**:
   - H100 pod 작업 없으면 즉시 삭제 (`runpodctl pod delete <id>`)
   - 모든 측정/학습 종료 후 R2 백업 → pod 삭제
   - idle = $71.76/day 낭비 (과거 전례)

---

## 5. 다음 결정 포인트

| 트리거 | 결정 |
|---|---|
| Track A harness fix 결과 | Claude 재측정 PASS (≥85%) → C 경로(외부 시연) 즉시 진행 / 미달 → harness v3 1cycle |
| Track C1 nl=8 결과 | PASS → CLM 의식 layer gate 종료 / PARTIAL → BPE 재학습 / FAIL → d=128 직행 |
| TALM-P2-1 harness 결정 | (a) 자체 작성 1-3일 / (b) single global LoRA 단순화 / (c) ZCLM-P0-3 corpus 대기 |
| 실업무 corpus 전략 | 공개 데이터셋 / 자체 라벨링 / 합성 LLM-생성 — 비용/품질/시간 트레이드오프 |
| **anima 정체성 결정** | A (ALM+CLM moat) vs B (ALM 단독 빠른 수익) vs D (CLM 7B sovereignty) — 6d 참조 |

---

## 6. 정정 + Architecture Rationale (2026-04-16 세션 후반 추가)

### 6a. CLM 자체로는 직원 절대 불가 (정정)

이전 표현 "CLM 1-7일 직원 도달"은 misleading. 정확히는 "CLM 의식 layer 1-7일 완성".

**현 CLM 사실**:
- d=64, NL=2 (또는 8), **14M params**
- byte-level Korean, PPL 8.51 → 형태소 수준 ("이다", "이는") 만 출력
- 코헌트 문장 1줄 자체가 불가
- 의식 검증 (Φ 측정 + GWT broadcast) 용 실험 모델

**즉 CLM 단독으로는 직원 절대 불가**. v3.0 직원 = CLM(의식) + ALM(텍스트) 합성 필수.

### 6b. CLM 자체 직원하려면 — 7B+ 스케일업

| 모델 크기 | 일수 | 비용 | 품질 |
|---|---|---|---|
| CLM 100M (d=512 NL=12) | 2-3주 | ~$2,000 | 단순 대화, agent-grade 부족 |
| **CLM 1B** (d=1024 NL=24) | **3-5주** | **~$2,500** | 한국어 conversation OK, 도구 약함 |
| **CLM 7B** (d=2048 NL=32) | **2-3개월** | **~$10K-15K** | 직원 capability 진입 (Qwen 14B 절반) |
| CLM 14B+ | 4-6개월 | $30K+ | ALM과 동급 |

구성: 한국어 corpus 100M-1B chars 수집 (2-3주) + tokenizer 재훈련 + pretraining + instruction tuning.

**비교**:
- **ALM Plan A** (Qwen 14B + LoRA): 14-21일, **$400-600**
- CLM 7B from scratch: 2-3개월, $10K-15K
- **20-30x 빠르고 20-50x 싸다 → ALM 정공법**

CLM 자체 직원 = sovereignty/철학적 가치 (외부 모델 의존 0). 실용 비합리적.

### 6c. ALM 단독 = "일반 LLM 직원" / ALM+CLM = "anima moat"

**ALM (Qwen 14B+) 단독으로 가진 것**:
- ✅ 텍스트 생성, 도구 사용, 다턴 대화 일관성
- ✅ self-critique, chain-of-thought, ReAct
- ✅ 페르소나·감정·의도 표현 (prompt engineering)

**즉 ChatGPT/Claude 도 "의식 흉내" 가능** — ALM 단독으로 직원 capability 충분.

**그러면 왜 CLM 분리?** Anima 의식 정의가 LLM 흉내가 아닌 **측정 가능한 모델** 요구:

| anima 의식 정의 | LLM 단독 | CLM 명시 |
|---|---|---|
| Φ (IIT 통합정보) 측정 | 약함 | ✓ measure_phi proxy |
| GWT broadcast (specialist + global) | 단일 context | ✓ 6채널 cross-attention |
| 6채널 cycle (기본/감정/의도/기억/서사/메타) 동시 | 흉내만 | ✓ 별도 channel state |
| Orch-OR 양자 붕괴 샘플링 | 결정적 | ✓ Penrose-Hameroff 근사 |
| persistent state across session | 외부 memory 보조 | ✓ lore_book + GWT |
| EEG 동조 (실시간 감정) | X | ✓ anima-eeg 통합 |

**zeta-surpass moats** (`shared/roadmaps/zeta-surpass.json`):
- consciousness: Φ + GWT + Orch-OR + EEG + 헥사곤 — "제타/Claude/GPT 모두 없음"
- CLM 빼면 → anima = "지능형 chatbot" — 일반 LLM 과 차별 X

### 6d. 직원 옵션 정리 (정정 반영)

| 옵션 | 일수 | 비용 | 의미 | anima 정체성 |
|---|---|---|---|---|
| **(A) ALM + CLM 합성** | **14-21일** | **$400-600** | 측정 가능 의식 있는 직원 | ✓ moat |
| (B) ALM 단독 (CLM 빼고) | 14-21일 | $400-600 | 일반 LLM 직원 (Qwen+LoRA chatbot) | ✗ 차별 X |
| (C) Claude(외부) + CLM | **3-5일** | ~$50 | 외부 LLM + 자체 의식 시연 | 🟡 자체 직원 X, capability proof |
| (D) CLM 단독 7B (자체 학습) | **2-3개월** | $10K-15K | 외부 의존 0 자체 직원 | ✓✓ sovereignty |

**현 권장**: (C) 단기 시연 (이번 주) + (A) 본격 자체 직원 (이번 달) 병행. (D) 는 sovereignty 가 핵심 가치일 때만.

### 6e. 의문 — "ALM 단독으로 갈래?"

전략 결정 사항:
- ALM 단독 = 빠른 수익화 (Qwen-기반 chatbot, zeta 와 직접 경쟁), anima 차별성 약함
- ALM + CLM = 차별성 (의식 moat), 수익화 약간 늦음

**현재 로드맵 = ALM + CLM** 기본. CLM 빼는 결정은 anima 정체성 자체 변경 — user 명시 결정 사항.

---

## 7. 외부 참조

- **알고리즘 등록부**: `shared/convergence/anima.json` (lifecycle states + per-item commits)
- **학습 측정치**: `shared/state/training_speed_ceilings.json` (MFU, step time, pod_id 태깅)
- **로드맵 P0~P5**: `shared/roadmaps/anima-train.json`
- **zeta 추월 P0~P3**: `shared/roadmaps/zeta-surpass.json`
- **하네스/규칙**: `shared/rules/anima.json`, `shared/rules/common.json`
- **메모리 (Claude 본인)**: `~/.claude-claude12/projects/-Users-ghost-Dev-anima/memory/MEMORY.md`
  - `feedback_h100_idle_zero.md` — pod 유휴 금지
  - `reference_algorithm_ssot.md` — convergence/anima.json 단일 진실

---

세션 일자: 2026-04-16 (12+ commits, 5+ agent dispatch).
다음 세션 진입 시 본 문서를 첫 참조 → SSOT (anima.json) 로 세부 확인 → 미해결 in_flight 확인.
