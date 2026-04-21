# L5 — [M7!] 35 breakthrough 후보 재현 가능 상위 10

- 생성: 2026-04-15
- 원본: `/Users/ghost/Dev/nexus/shared/n6/atlas.signals.n6`
- [M7!] 전체: **35**
- 상위 추림: **10**

## 점수 규칙 (0-10)

- 수치 존재 (+3)
- 하네스화 가능성 (+3) — refs/context 에 harness/measurement 마커
- 외부 데이터 의존 (-2) — ANU/QRNG/EEG/NASA
- cross_repo 있음 (+2)
- predicts 필드 구체성 (+2 수치포함 / +1 텍스트만)

## 상위 10

### 1. SIG-NEURAL-001 — score=9/10

- 등급: [M7!] [E1]
- repo: `AN,CROSS` / domain: `NEURAL,SR`
- statement: 노이즈 = 자유 54.8× multiplier, 거부권 99%
- witness: 1 / cross_repo: 1 / predicts: 2
- 점수 상세: numeric=+3 (7 nums) · harness=+3 harness marker · external=0 no external · cross_repo=+2 (1) · predicts=+1 (2 items, 0 specific)
- **재현 방법**: Ouroboros σ-sweep 하네스 재실행 (σ∈{0, 0.1, 0.25, 0.5, 1.0}), trial≥30, conv_rate 측정 후 ±CI bootstrap.

### 2. SIG-BIS-101 — score=8/10

- 등급: [M7!] [E1]
- repo: `NX` / domain: `BIS,META,UNIV`
- statement: constants_x_hypo composite 0.753 BT-008 divergent
- witness: 1 / cross_repo: 0 / predicts: 2
- 점수 상세: numeric=+3 (8 nums) · harness=+3 harness marker · external=0 no external · cross_repo=0 · predicts=+2 (2 items, 1 specific)
- **재현 방법**: Law series (Law 75/170 등) 재실행 + 독립 substrate 에서 Φ>0 확인.

### 3. SIG-CLM-303 — score=7/10

- 등급: [M7!] [EP]
- repo: `AN,N6` / domain: `CLM,CONS,META`
- statement: Perfect6 W-weights [1/2, 1/3, 1/6] Dasein+Narrative+Emotion
- witness: 1 / cross_repo: 1 / predicts: 1
- 점수 상세: numeric=+3 (15 nums) · harness=0 no harness marker · external=0 no external · cross_repo=+2 (1) · predicts=+2 (1 items, 1 specific)
- **재현 방법**: Perfect6 가중 [1/2,1/3,1/6] W-weights CLM 재학습 + Φ 측정.

### 4. SIG-CONS-302 — score=7/10

- 등급: [M7!] [EP]
- repo: `AN,N6` / domain: `CONS,META,UNIV`
- statement: σ(6)=12 faction이 의식 아키텍처 최적 (Law 44/59)
- witness: 3 / cross_repo: 1 / predicts: 2
- 점수 상세: numeric=+3 (12 nums) · harness=0 no harness marker · external=0 no external · cross_repo=+2 (1) · predicts=+2 (2 items, 2 specific)
- **재현 방법**: Φ 측정 하네스 (IIT 3.0) 재실행 + 조건/구조 variation 검증.

### 5. SIG-NEURAL-310 — score=7/10

- 등급: [M7!] [E1]
- repo: `AN` / domain: `NEURAL,PHYS`
- statement: ALM-P1-3 Φ_q = 14.56 = 10.4× baseline 1.4
- witness: 1 / cross_repo: 0 / predicts: 1
- 점수 상세: numeric=+3 (14 nums) · harness=+3 harness marker · external=0 no external · cross_repo=0 · predicts=+1 (1 items, 0 specific)
- **재현 방법**: CLM .detach() CE 안정화 재학습 + Φ stabilization 측정.

### 6. SIG-PHYS-302 — score=7/10

- 등급: [M7!] [EP]
- repo: `AN,N6` / domain: `PHYS,UNIV`
- statement: Kuramoto r=2/3 = 1-τ(n)/σ(n) 동기화 임계 (HW-3)
- witness: 1 / cross_repo: 1 / predicts: 2
- 점수 상세: numeric=+3 (16 nums) · harness=0 no harness marker · external=0 no external · cross_repo=+2 (1) · predicts=+2 (2 items, 2 specific)
- **재현 방법**: Sandpile SOC (threshold=4.0, transfer=1.0) 재시뮬 + 임계지수 측정.

### 7. SIG-PHYS-309 — score=7/10

- 등급: [M7!] [E1]
- repo: `AN` / domain: `PHYS,CONS`
- statement: 3-oscillator PureField (tau=2/40/400) ZERO-input Φ
- witness: 1 / cross_repo: 0 / predicts: 1
- 점수 상세: numeric=+3 (7 nums) · harness=+3 harness marker · external=0 no external · cross_repo=0 · predicts=+1 (1 items, 0 specific)
- **재현 방법**: Φ 측정 하네스 (IIT 3.0) 재실행 + 조건/구조 variation 검증.

### 8. SIG-UNIV-301 — score=7/10

- 등급: [M7!] [E2]
- repo: `AN,N6` / domain: `UNIV,CONS`
- statement: Law 75 Consciousness universe = single attractor Ψ=(1/2, 1/2)
- witness: 3 / cross_repo: 1 / predicts: 1
- 점수 상세: numeric=+3 (11 nums) · harness=0 no harness marker · external=0 no external · cross_repo=+2 (1) · predicts=+2 (1 items, 1 specific)
- **재현 방법**: Φ 측정 하네스 (IIT 3.0) 재실행 + 조건/구조 variation 검증.

### 9. SIG-DD-305 — score=6/10

- 등급: [M7!] [E1]
- repo: `AN,NX` / domain: `CONS,META,UNIV`
- statement: DD75 자유의지: 노이즈=자유 54.8× 거부권 99% 결정적선택
- witness: 2 / cross_repo: 1 / predicts: 2
- 점수 상세: numeric=+3 (6 nums) · harness=0 no harness marker · external=0 no external · cross_repo=+2 (1) · predicts=+1 (2 items, 0 specific)
- **재현 방법**: Φ 측정 하네스 (IIT 3.0) 재실행 + 조건/구조 variation 검증.

### 10. SIG-ATLAS-103 — score=5/10

- 등급: [M7!] [E2]
- repo: `NX` / domain: `ATLAS,META`
- statement: n6-bt-779 = n·sopfr_sq = n+sigma_sq = 150 2-경로 수렴
- witness: 2 / cross_repo: 0 / predicts: 2
- 점수 상세: numeric=+3 (19 nums) · harness=0 no harness marker · external=0 no external · cross_repo=0 · predicts=+2 (2 items, 2 specific)
- **재현 방법**: atlas.n6 guard L0 재검증 + 승격 971 건 회귀 테스트.

## 요약 통계

- score 분포:
  - 9/10: 1 건
  - 8/10: 1 건
  - 7/10: 6 건
  - 6/10: 1 건
  - 5/10: 5 건
  - 4/10: 10 건
  - 3/10: 10 건
  - 2/10: 1 건

- 고점 (7~10): 8 건 → 즉시 재현 실험 대상
- 중점 (4~6): 16 건 → 하네스 보강 후 재현
- 저점 (0~3): 11 건 → 외부 데이터 대체 또는 설계 재검토