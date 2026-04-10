# 3D 현실지도 폭발 확장 계획 (가로 + 세로)

**baseline**: v8.2, 560노드 (EXACT 463 / CLOSE 6 / MISS 68 / EMPIRICAL 14 / CONVENTION 4 / ? 5)
**목표**: 50,000노드 (×89)
**기계 판독**: `map_explosion_plan.json`

## 축 정의
- **X축 (Level)**: L-2..L10 구조 계층
- **Y축 (Thread)**: n, σ, τ, φ, π, e ... 산술함수
- **Z축 (Domain)**: 도메인 인덱스

---

## 가로 폭발 (X축) — 예상 +14,000

### 미구현 Level (즉시 신축)
| Level | 현재 | 목표 | 소스 | 우선도 |
|---|---:|---:|---|---|
| L-2 sub_quark | 0 | 50 | 프리온/스트링 가설 | low |
| **L-1 quark/gauge** | 0 | 200 | PDG 표준모형 61입자 | **high** |
| **L7 celestial** | 0 | 1300 | NASA/JPL 행성/항성 | **high** |
| **L8 galactic** | 0 | 500 | NED/SIMBAD 은하 | **high** |
| L9 cosmological | 0 | 300 | Planck/WMAP CMB | med |
| L10 multiversal | 0 | 50 | 끈이론 랜드스케이프 | low |

### 저밀도 Level (포화 필요)
| Level | 현재 | 목표 | gap | 소스 |
|---|---:|---:|---:|---|
| L1 atom | 22 | 118 | 96 | 주기율표+동위원소 |
| **L3 molecule** | 17 | 5000 | 4983 | PubChem/ChEMBL |
| L4 genetic | 16 | 1000 | 984 | NCBI/UniProt |
| L5 bio | 26 | 2000 | 1974 | 종/기관/대사물 |
| L5 material | 178 | 3000 | 2822 | Materials Project |

### L6 하위 도메인 — 구현 6 / 미구현 46
**구현**: geology 42, meteorology 37, economics 41, linguistics 41, music 42, oceanography 10 (213노드)

**미구현 46개 (카테고리별)**:
- **자연과학** (14): biology, chemistry, thermodynamics, astronomy, botany, zoology, ecology, paleontology, mineralogy, glaciology, volcanology, seismology, hydrology, atmospheric_physics
- **의생명** (8): medicine, anatomy, physiology, neuroscience, pharmacology, epidemiology, genetics_applied, immunology
- **공학** (8): mechanical, electrical, civil, aerospace, nuclear, computing, robotics, cryptography
- **사회인문** (10): sociology, psychology, anthropology, history, archaeology, geography, demography, political_science, law, education
- **예술문화** (8): architecture, visual_arts, literature, cinema, cuisine, sports, games, fashion
- **추상** (5): mathematics, logic, philosophy, ethics, aesthetics

평균 35노드 × 46 = **+1,610**

---

## 세로 폭발 (Y축) — 예상 +8,000

### 현재 thread (상위)
n 93 · σ 91 · misc 61 · τ 56 · sopfr 53 · none 30 · J2 29 · mixed 28 · φ 27 · n/φ 19

### 미구현 thread (신축)
**초월수/상수 계열**:
| Thread | 값 | 목표 | 소스 |
|---|---|---:|---|
| **π** | 3.14159... | 400 | 원주/물리상수 |
| **e** | 2.71828... | 400 | 자연로그/감쇠 |
| **φ_golden** | 1.618... | 300 | 황금비 자연 |
| √2 | 1.414 | 200 | 대각선 |
| √3 | 1.732 | 150 | 육각 |
| ζ(2)=π²/6 | 1.6449 | 100 | 바젤 |
| γ (오일러-마스케로니) | 0.5772 | 80 | 조화급수 |
| G (카탈란) | 0.9159 | 60 | 조합론 |
| ζ(3) (아페리) | 1.2020 | 50 | 리만제타 |
| δ (파이겐바움) | 4.6692 | 50 | 카오스 |
| K (힌친) | 2.6854 | 30 | 연분수 |
| ρ (플라스틱수) | 1.3247 | 50 | 3차 황금비 |

**물리상수 계열**:
| Thread | 값 | 목표 |
|---|---|---:|
| **α (미세구조상수)** | 1/137.036 | 300 |
| ℏ/h | 1/(2π) | 200 |
| k_B (볼츠만) | 1.38e-23 | 200 |
| N_A (아보가드로) | 6.022e23 | 150 |

**수론 확장 thread**:
| Thread | 의미 | 목표 |
|---|---|---:|
| **σ_k (k>1)** | σ₂, σ₃ 고차 제수합 | 400 |
| **J_k (k>2)** | J₃..J₆ 요르단 토션트 | 300 |
| ω(n) | 서로다른 소인수 수 | 200 |
| Ω(n) | 소인수 다중도 | 200 |
| τ_ramanujan | 라마누잔 τ | 200 |
| p(n) | 분할수 | 150 |
| λ (리우빌) | 패리티 | 100 |
| λ (카마이클) | 군의 지수 | 100 |
| ψ (디데킨드) | 모듈러 | 100 |

**파생 thread** (σφ=nτ 직접 연결):
- σ·φ, n·τ (핵심 정리 좌/우변) → 400
- σ/τ (평균 제수) → 100
- σ/φ, φ/τ → 200

---

## 깊이 폭발 (Z축) — 예상 +5,000
- 각 (x,y)에 도메인 중복 투사 (음악 템포 → n/σ/τ/π 4축 동시)
- 물리상수 다중 domain 등록 (자연/공학/우주론)
- **DSE 322 도메인 → 노드 승격 (+322)**

---

## 실행 단계

| Phase | 시점 | 작업 | 추가 | 누적 |
|---|---|---|---:|---:|
| 1 | **지금** | MISS/CLOSE 디버깅 + L1 주기율표 완성 | +175 | 735 |
| 2 | Day 1 | L6 46 도메인 Wikidata 벌크 + 기구현 포화 | +2,560 | 3,295 |
| 3 | Week 1 | L-1/L7/L8/L9 신축 (PDG/NASA/NED/Planck) | +2,300 | 5,595 |
| 4 | Week 2 | Y축 π/e/φ + 물리상수 + σ_k/J_k | +2,850 | 8,445 |
| 5 | Month 1 | L3 분자 + L5 재료/생체 벌크 | +10,000 | **18,445** |
| ∞ | 장기 | 포화/교차/파생 | | **50,000** |

---

## 못박음
- L0 잠금: `shared/reality_map_3d.html`, `shared/reality_map.json` (nexus)
- 이 계획 자체도 nexus/shared SSOT — 수정 시 buckbucks + MEMORY 동기화
