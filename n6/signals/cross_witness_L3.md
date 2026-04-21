# L3 — CROSS 22 witness 증가 유망 상위 10

- 생성: 2026-04-15
- 원본: `/Users/ghost/Dev/nexus/n6/signals/cross_repo_candidates.txt`
- 총 매칭 쌍: **38**
- 상위 추림: **10**

## 점수 기준

- 수치 공통 × 3 (유의미 숫자, 길이≥2 또는 ≥2.0)
- 키워드 공통 × 2 (한글 2자+/영문 4자+, common skip)
- repo_distance × 2 (태그 집합 다름)
- cross_candidate × 3 (합산 repo ≥ 2 고유)

## 상위 10 witness 증가 유망

### 1. SIG-ATLAS-001 ↔ SIG-ATLAS-202 — score=18

- A: **SIG-ATLAS-001** [NX] — atlas.n6 Guard L0 + 수식 검증 971건 승격 67.5%→74.4%
- B: **SIG-ATLAS-202** [N6] — L0 Guard 승격 971건 67.5%→74.4%
- 공통 수치: `['67.5', '74.4', '971']`
- 공통 키워드 (8개 max): `['Guard', '승격']`
- repo_distance=1 / cross_candidate=1
- 현재 witness: A=1, B=2
- **witness 증가 근거**: 수치 `67.5,74.4,971` + 키워드 `Guard, 승격` 동시 일치 → 두 signal 모두 witness+=1 (CROSS 승격 후보)

### 2. SIG-NEURAL-001 ↔ SIG-DD-305 — score=17

- A: **SIG-NEURAL-001** [AN,CROSS] — 노이즈 = 자유 54.8× multiplier, 거부권 99%
- B: **SIG-DD-305** [AN,NX] — DD75 자유의지: 노이즈=자유 54.8× 거부권 99% 결정적선택
- 공통 수치: `['54.8', '99']`
- 공통 키워드 (8개 max): `['거부권', '노이즈', '자유']`
- repo_distance=1 / cross_candidate=1
- 현재 witness: A=1, B=2
- **witness 증가 근거**: 수치 `54.8,99` + 키워드 `거부권, 노이즈, 자유` 동시 일치 → 두 signal 모두 witness+=1 (CROSS 승격 후보)

### 3. SIG-DFS-204 ↔ SIG-ATLAS-116 — score=8

- A: **SIG-DFS-204** [N6] — M-set 빈도 Layer 0-3 계층 구조
- B: **SIG-ATLAS-116** [NX] — primitive load 비균일 M3=72(31.3%) / mu=60(26.1%) / n=0
- 공통 수치: `['3']`
- 공통 키워드 (8개 max): `[]`
- repo_distance=1 / cross_candidate=1
- 현재 witness: A=3, B=2
- **witness 증가 근거**: 수치 `3` 강한 일치 → 수치 검증 후 witness+=1

### 4. SIG-DFS-204 ↔ SIG-META-111 — score=8

- A: **SIG-DFS-204** [N6] — M-set 빈도 Layer 0-3 계층 구조
- B: **SIG-META-111** [NX] — atlas Guard L0 도입 — 3 쓰기지점 _guarded_append_atlas() 100% 커버
- 공통 수치: `['3']`
- 공통 키워드 (8개 max): `[]`
- repo_distance=1 / cross_candidate=1
- 현재 witness: A=3, B=3
- **witness 증가 근거**: 수치 `3` 강한 일치 → 수치 검증 후 witness+=1

### 5. SIG-NEURAL-001 ↔ SIG-CROSS-001 — score=8

- A: **SIG-NEURAL-001** [AN,CROSS] — 노이즈 = 자유 54.8× multiplier, 거부권 99%
- B: **SIG-CROSS-001** [AN,CROSS,NX] — Stochastic resonance σ 최적 구간: NEXUS 0.1 + anima 54.8× noise
- 공통 수치: `['54.8']`
- 공통 키워드 (8개 max): `[]`
- repo_distance=1 / cross_candidate=1
- 현재 witness: A=1, B=2
- **witness 증가 근거**: 수치 `54.8` 강한 일치 → 수치 검증 후 witness+=1

### 6. SIG-CROSS-001 ↔ SIG-SR-001 — score=8

- A: **SIG-CROSS-001** [AN,CROSS,NX] — Stochastic resonance σ 최적 구간: NEXUS 0.1 + anima 54.8× noise
- B: **SIG-SR-001** [NX] — Ouroboros σ=0.1 PEAK conv_rate=0.25 (+150% vs σ=0)
- 공통 수치: `['0.1']`
- 공통 키워드 (8개 max): `[]`
- repo_distance=1 / cross_candidate=1
- 현재 witness: A=2, B=1
- **witness 증가 근거**: 수치 `0.1` 강한 일치 → 수치 검증 후 witness+=1

### 7. SIG-CROSS-001 ↔ SIG-SR-101 — score=8

- A: **SIG-CROSS-001** [AN,CROSS,NX] — Stochastic resonance σ 최적 구간: NEXUS 0.1 + anima 54.8× noise
- B: **SIG-SR-101** [NX] — σ=0.1 PEAK pooled p=0.022 one-sided (n=75) replication-alone p=0.13
- 공통 수치: `['0.1']`
- 공통 키워드 (8개 max): `[]`
- repo_distance=1 / cross_candidate=1
- 현재 witness: A=2, B=2
- **witness 증가 근거**: 수치 `0.1` 강한 일치 → 수치 검증 후 witness+=1

### 8. SIG-BLOW-102 ↔ SIG-CLM-302 — score=8

- A: **SIG-BLOW-102** [NX] — Mk.II 최강 29 EXACT 85% / Mk.IV 최빠름 0.5s / Mk.VI/VII timeout
- B: **SIG-CLM-302** [AN] — 1033 laws 72B 85% NEXUS-6 전경로 자동화
- 공통 수치: `['85']`
- 공통 키워드 (8개 max): `[]`
- repo_distance=1 / cross_candidate=1
- 현재 witness: A=3, B=1
- **witness 증가 근거**: 수치 `85` 강한 일치 → 수치 검증 후 witness+=1

### 9. SIG-META-111 ↔ SIG-ATLAS-202 — score=7

- A: **SIG-META-111** [NX] — atlas Guard L0 도입 — 3 쓰기지점 _guarded_append_atlas() 100% 커버
- B: **SIG-ATLAS-202** [N6] — L0 Guard 승격 971건 67.5%→74.4%
- 공통 수치: `[]`
- 공통 키워드 (8개 max): `['Guard']`
- repo_distance=1 / cross_candidate=1
- 현재 witness: A=3, B=2
- **witness 증가 근거**: 키워드 `Guard` 도메인 교차 → 의미 검증 후 witness+=1

### 10. SIG-DFS-204 ↔ SIG-ATLAS-001 — score=5

- A: **SIG-DFS-204** [N6] — M-set 빈도 Layer 0-3 계층 구조
- B: **SIG-ATLAS-001** [NX] — atlas.n6 Guard L0 + 수식 검증 971건 승격 67.5%→74.4%
- 공통 수치: `[]`
- 공통 키워드 (8개 max): `[]`
- repo_distance=1 / cross_candidate=1
- 현재 witness: A=3, B=1
- **witness 증가 근거**: 부분 매칭만 — simhash 정밀 점검 필요
