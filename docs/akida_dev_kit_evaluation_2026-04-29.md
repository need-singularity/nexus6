# Akida AKD1000 Dev Kit (RPi5) — nexus evaluation

@english-only-exempt(reason="nexus infra analysis language preservation per user primary language")

- **Date**: 2026-04-29
- **Vendor**: BrainChip Inc — `https://shop.brainchipinc.com/products/akida%E2%84%A2-development-kit-raspberry-pi-5-draft`
- **Price**: $1,495 USD (1회 capex)
- **Context**: nexus infra.state host pool 확장 후보 + atlas tier_1_promotions hardware-substrate evidence

## 디바이스 요약

- **칩**: Akida AKD1000 (neuromorphic, spike-event-based)
- **호스트**: Raspberry Pi 5 (BCM2712 quad-core A76 2.4GHz, 16GB LPDDR4)
- **인터페이스**: M.2 B+M Key (PCIe 2.0 single-lane), USB 3.0 ×2
- **SDK**: Meta TF (BrainChip 자체 framework, 일반 PyTorch 직접 사용 불가)
- **전력**: ~1W typical (vendor spec)

## nexus 직접 도움 3축

### 1. infra.state host pool 확장

현재 `~/core/.workspace` host pool:
- host.ubu1 (Ryzen 5 9600X + RTX 5070 12GB)
- host.ubu2 (Ryzen 5 9600X + RTX 5070 12GB open-driver)
- host.htz (Hetzner AX102, 32T CPU-only, 124GB)
- gpu.h100 (H100 ×4, RunPod/vast.ai dispatch)

**신규 등재 후보**: `host.rpi5-akida` (neuromorphic-class, ~1W, 16GB RAM, edge-inference 전용).

raw 40 external-host-dispatch-default 의 vendor diversity 확장 — 현재 4 host class (ubu/htz/gpu/mac) 가 전부 von Neumann CPU/GPU. neuromorphic class 첫 진입.

### 2. atlas tier_1_promotions hardware-substrate evidence

현재 atlas substrate witness 는 모두 cloud-API 경유 (IonQ / QuEra / BrainChip Cloud / etc).
이 dev kit = hardware-direct measurement → atlas tier_1 promotion evidence 의 cloud-dependency 0.

raw 47 cross-repo-trawl-witness 호환 — anima own 2 (b) substrate triangulation 과 nexus atlas 의 cross-link 첫 hardware anchor.

### 3. own 2 admin-block bypass (raw 104 'own' 경로)

own 2 strengthening 2026-04-28 status:
- Neuromorphic 0/3 sub-classes (admin-access blocked at all 3 vendors)
- Optical 0/3 sub-classes (admin-access blocked)

raw 104 design-means-end-decoupling-mandate 의 4 경로:
- own (소유): $1.5K capex 1회
- subscribe (구독): Akida Cloud $995/주
- partner-share: BrainChip 파트너십 — long-tail
- mock-deterministic: simulator only — hardware witness 미달

3주 이상 사용 시 own 회수. nexus 의 atlas tier_1 evidence chain 에서 capex amortization.

## nexus.workspace 등재 제안

```hexa
resource host.rpi5-akida "RPi5 + Akida AKD1000 — neuromorphic edge-inference (M.2 B+M, ~1W, 16GB)"
  owner    nexus
  kind     descriptor
  power    ~1W
  capacity ~1.2M neurons (AKD1000)
  host     local-edge (cable-tethered, no cloud)
```

추가 시점: dev kit 도착 + Meta TF 첫 변환 PASS 후 (event-driven 등재, 사전 등재 X per raw 91 C3 honest).

## 못 하는 것 (raw 91 honest C3)

- 학습 dispatch X (inference only) → gpu.h100 / RunPod H100 substitute 불가
- LLM forward X (16GB RAM) → Qwen-7B+ 못 올림
- 일반 PyTorch checkpoint 직접 사용 X (Meta TF quantize 필요)
- nexus kick ω-cycle 의 GPU dispatch path 와 별개 분기 (event-stream-only path)

## 비용 비교

| 옵션 | Capex | Opex | 회수 시점 |
|---|---|---|---|
| Dev Kit 구매 (own) | $1,495 | $0 | 즉시 |
| Akida Cloud 1주 | $0 | $995 | — |
| 1일 trial | $0 | $1 | 적합성 사전 확인용 |

## 결정 기준 (raw 167 multi-interpretation surfacing)

**구매 정당화 조건** (2 중 1+ 충족 시):
- (a) anima own 2 (b) 뉴로모픽 1/3 WITNESSED 가 30일 내 critical path (anima 측 결정 의존)
- (b) atlas tier_1 hardware-substrate evidence 가 Q2 cross-repo trawl 의 결정적 missing anchor

**구매 보류 조건**:
- anima 측 V_phen_GWT 변환 PASS 미확인
- atlas tier_1 cloud-dependency 가 현재 운영상 충분

## 권장 전 단계

1. Akida Cloud 1일 trial ($1) — V_phen_GWT 일부 모듈 변환 가능성 측정
2. BrainChip support 문의 — anima 12-tier backbone + Phi-vector 변환 가능 여부
3. anima 측 own 2 (b) 30일 critical path 진입 확인 후 dev kit 구매 진행

## Cross-link

- raw 40 external-host-dispatch-default (host pool extension)
- raw 47 cross-repo-trawl-witness (anima sister analysis cross-link)
- raw 104 design-means-end-decoupling-mandate (own/subscribe/partner/mock 경로 결정)
- raw 167 design-think-before-implementation-assumption-surfacing (decision criteria 명시)
- anima/docs/akida_dev_kit_evaluation_2026-04-29.md (sister analysis, research perspective)
- ~/core/.workspace `host.*` resource declarations
