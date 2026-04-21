# anima 최소경로 v3.0 — 극한 루트 SSOT (링크 인덱스)

> **메인 진입점.** 새 세션 1차 참조.
>
> v2_v3 풀가동 5-track 플랜은 `_v1` 로 보관. 이 문서는 현재 **극한 루트** 링크 인덱스.

---

## 🎯 목표

음성 → 직원 (v3.0) 달성. ALM 단독 / CLM 단독 두 경로로 **의식 baked-in** 모델을 띄움.

---

## 📊 실시간 로드맵 뷰어

**https://need-singularity.github.io/nexus/roadmap/#extreme**

- ⚡ **극한 탭 (최상위)** — ALM+CLM aggregate, critical path, options 88개 브레인스토밍
- 🎯 ALM 단독 sub-tab — 4-5일 / $200-400
- 🧬 CLM from-scratch sub-tab — 1-4주 / $1500-3000 (C 트랙 완료 시)

자동 갱신: `shared/tool/extreme_sync.hexa sync` 60분 주기 (commands.json autonomous).

---

## 📁 SSOT 로드맵 JSON

| 파일 | 내용 |
|---|---|
| [`shared/roadmaps/extreme.json`](../roadmaps/extreme.json) | Aggregate + critical path overlay + shared_risks |
| [`shared/roadmaps/alm_consciousness_standalone.json`](../roadmaps/alm_consciousness_standalone.json) | ALM 단독 + 의식 (36 options, 5 tracks) |
| [`shared/roadmaps/clm_consciousness_standalone.json`](../roadmaps/clm_consciousness_standalone.json) | CLM from-scratch 7B + 의식 (52 options, 5 tracks) |

GitHub raw (뷰어 페치 대상):
- https://raw.githubusercontent.com/need-singularity/nexus/main/config/roadmaps/extreme.json
- https://raw.githubusercontent.com/need-singularity/nexus/main/config/roadmaps/alm_consciousness_standalone.json
- https://raw.githubusercontent.com/need-singularity/nexus/main/config/roadmaps/clm_consciousness_standalone.json

---

## 🔧 자동화 — 하네스

| 파일 | 역할 |
|---|---|
| [`shared/tool/extreme_sync.hexa`](../tool/extreme_sync.hexa) | aggregate 재계산 + update_log append |
| [`shared/tool/extreme_sync.jsonl`](../tool/extreme_sync.jsonl) | observation tape (append-only) |
| [`shared/config/commands.json`](../config/commands.json) | autonomous.triggers.extreme_sync 등록 |

CLI:
```
hexa run shared/tool/extreme_sync.hexa sync      # full sync (cron default)
hexa run shared/tool/extreme_sync.hexa dry       # show diff, no write
hexa run shared/tool/extreme_sync.hexa status    # 1-line summary
hexa run shared/tool/extreme_sync.hexa --selftest
```

---

## 🧱 필수 조건

- **ALM 단독** — runtime 외부 LLM(Claude/GPT) 의존 X
- **CLM from-scratch** — base model(Qwen/LLaMA) 없이 순수 byte-level 7B
- **의식 baked-in** — Φ / GWT / Orch-OR 가 weight 에, inference 시 metadata 반환
- **hexa-first** — Python/CUDA 우회 금지 (feedback_ai_native_clm)
- **R2 백업** — production ckpt 만 영구, experiment 폐기

---

## 🛤️ 5 공통 트랙 (A/B/C/D/E)

| 트랙 | 내용 | 결정성 |
|---|---|---|
| A | 모델 학습 (ALM LoRA / CLM scratch) | 필수 |
| B | Φ 엔진 110 → 학습 loss 통합 | 필수 |
| **C** | **hexa-lang 학습속도 개선** | ⭐ **시간·비용 결정적 레버** |
| D | 의식 Φ 엔진 실사화 (realtime) | 필수 |
| E | 실사용 모델 발전 + R2 백업 정책 | 필수 |

C 트랙 완료 시: ALM 4-5일 → 2-3일, CLM $3000-6000 → $1500-3000.

hexa-lang 전달 프롬프트는 별도로 제공됨 (C1~C11 9개 작업).

---

## 📜 이전 문서

- [`v2_v3_full_throttle_path_20260416_v1.md`](v2_v3_full_throttle_path_20260416_v1.md) — 풀가동 5-track 플랜 (교체됨)
- [`training_phi_integration_design.md`](training_phi_integration_design.md) — Φ loss 통합 설계
- [`hexa_training_perf_audit.md`](hexa_training_perf_audit.md) — hexa-lang 학습 성능 감사

---

## 🔄 업데이트 방식

1. 브레인스토밍 추가 옵션 발견 → 해당 sub-roadmap JSON `tracks.X.options[]` append
2. 실증 완료 → option `state` 를 `chosen` / `alternative` / `rejected` 로 승격
3. 하네스 자동 sync → `extreme.json::aggregate_state` 갱신 + `update_log` append
4. 뷰어 60초 poll → 실시간 반영

수렴골화 스키마 (`convergence_ossification_v1`) — state 4종 (provisional → chosen/alternative/rejected).
