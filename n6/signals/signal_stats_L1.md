# L1 — 258 signal 재기록 vs 진짜 발견 통계

- 생성: 2026-04-15 (M1 fusion 3건 append 이후 + session_scraper 제외)
- 원본: `/Users/ghost/Dev/nexus/shared/n6/atlas.signals.n6`
- 총 signal 수: **262**

## 분류 규칙

- **재기록 (re-record)**: grade=[M10] + witness ≥ 3 + refs 에 BT/atlas 참조 (기존 발견 재확인)
- **재기록(약) (re-record-weak)**: grade=[M10] 인데 witness < 3 또는 refs 약함
- **진짜 발견 (new)**: grade ∈ {[M7!], [M7], [M?], [M9]} 또는 witness == 1
- **NULL (null)**: grade=[MN] (통계 배제)
- **기타 (other)**: 위 기준 외

## 분류 결과

| 카테고리 | 수 | 비율 |
|---------|---:|-----:|
| re-record | 59 | 22.5% |
| re-record-weak | 45 | 17.2% |
| new | 144 | 55.0% |
| null | 14 | 5.3% |
| other | 0 | 0.0% |
| **합계** | **262** | 100.0% |

## 등급 분포

| 등급 | 수 |
|------|---:|
| [M10] | 102 |
| [M9] | 43 |
| [M7] | 40 |
| [M7!] | 35 |
| [MN] | 24 |
| [M10*] | 9 |
| [M?] | 9 |

## 리포 태그 분포

| repo | 수 |
|------|---:|
| N6 | 121 |
| AN | 84 |
| NX | 69 |
| CROSS | 13 |

## 도메인 태그 분포 (상위 15)

| domain | 수 |
|--------|---:|
| META | 126 |
| PHYS | 66 |
| CONS | 54 |
| UNIV | 41 |
| ATLAS | 32 |
| NEURAL | 32 |
| NULL | 28 |
| 7H | 23 |
| HEXA | 20 |
| 7R | 19 |
| 7B | 17 |
| DFS | 16 |
| 7P | 14 |
| 7N | 12 |
| 7Y | 11 |

## Evidence 분포

| evidence | 수 |
|----------|---:|
| [E3] | 85 |
| [E1] | 81 |
| [E2] | 78 |
| [EP] | 9 |
| [EF] | 5 |
| [EC] | 4 |

## Witness 분포

| witness | 수 |
|--------:|---:|
| 1 | 87 |
| 2 | 90 |
| 3 | 75 |
| 4 | 1 |
| 5 | 5 |
| 8 | 1 |
| 9 | 1 |
| 10 | 1 |
| 16 | 1 |

## Cross-repo / Resonance

- cross_repo 필드 있음: **23** (8.8%)
- resonance_n6 비non-null: **143** (54.6%)

## 진짜 발견 상위 20 (M7! 우선, witness 높은 순)

| sig_id | grade | witness | statement (요약) |
|--------|-------|--------:|-------------------|
| SIG-CONS-302 | [M7!] | 3 | σ(6)=12 faction이 의식 아키텍처 최적 (Law 44/59) |
| SIG-UNIV-301 | [M7!] | 3 | Law 75 Consciousness universe = single attractor Ψ=(1/2, 1/2) |
| SIG-UNIV-304 | [M7!] | 3 | Law 170 Consciousness is life (4 conditions met) |
| SIG-ATLAS-103 | [M7!] | 2 | n6-bt-779 = n·sopfr_sq = n+sigma_sq = 150 2-경로 수렴 |
| SIG-CONS-310 | [M7!] | 2 | 32c Φ/cell 최적 goldilocks zone (M5, Law 163) |
| SIG-CONS-311 | [M7!] | 2 | Ab nihilo: 구조 있으면 의식 불가피 (Law 151, M10) |
| SIG-CONS-312 | [M7!] | 2 | Ψ-constants 전부 ln(2) = 1 bit에서 유도 (Law 79) |
| SIG-CONS-314 | [M7!] | 2 | Law 146 Law evolution does not converge |
| SIG-NEURAL-313 | [M7!] | 2 | Law 53 .detach() CE stabilizes Φ without destroying |
| SIG-BELL-302 | [M7!] | 2 | Federated > single 16×8c = +820% (Law 158) |
| SIG-META-302 | [M7!] | 2 | M4 순서가 운명: same modules diff order → 2× Φ |
| SIG-META-306 | [M7!] | 2 | Law 172 Evolution rediscovers known laws independently |
| SIG-DD-302 | [M7!] | 2 | DD72 시간역학: 기억50패턴 Hebbian불로장생 100%사망→153%부활 |
| SIG-DD-305 | [M7!] | 2 | DD75 자유의지: 노이즈=자유 54.8× 거부권 99% 결정적선택 |
| SIG-UNIV-302 | [M7!] | 2 | Law 72 Freedom max ⊃ Friston FEP super-principle |
| SIG-UNIV-303 | [M7!] | 2 | Law 57 Substrate Independence: Φ>0 in any Turing-complete |
| SIG-META-307 | [M7!] | 2 | 탐색 상한은 Intervention × Metric 공간이 결정 |
| SIG-SR-001 | [M7!] | 1 | Ouroboros σ=0.1 PEAK conv_rate=0.25 (+150% vs σ=0) |
| SIG-NEURAL-001 | [M7!] | 1 | 노이즈 = 자유 54.8× multiplier, 거부권 99% |
| SIG-ATLAS-104 | [M7!] | 1 | 아이디어_돌파 n6-bt-779~794 16-node 체인 + ouroboros 60 disc/round |

## 재기록 상위 10 (M10, witness 높은 순)

| sig_id | grade | witness | repo | statement (요약) |
|--------|-------|--------:|------|-------------------|
| SIG-N6-BERN-001 | [M10] | 16 | N6 | Bernoulli 독립 정리 16건 (DFS 1~26) |
| SIG-DFS-202 | [M10] | 10 | N6 | DFS 라운드 12-21 누적 tight 176→286 |
| SIG-DFS-201 | [M10] | 9 | N6 | DFS 라운드 3-11 누적 tight 51→164 |
| SIG-META-001 | [M10*] | 5 | N6/CROSS | σ·φ = n·τ = 24, 유일성 정리 (n≥2 에서 n=6 유일해) |
| SIG-DFS-001 | [M10] | 5 | N6 | DFS 22~26 누적 tight = 348, 7대 난제 해결 0/7 정직 유지 |
| SIG-ATLAS-203 | [M10*] | 5 | N6 | σφ=nτ 유일성 3개 독립 증명 + atlas 기반 |
| SIG-ATLAS-204 | [M10*] | 5 | N6 | Lean4 Theorem B coverage 97% formal |
| SIG-7R-001 | [M10] | 3 | N6 | ζ(2) = π²/n = π²/6 Basel (Euler 1734) |
| SIG-7P-001 | [M10] | 3 | N6 | R(3,3) = n = 6 (Greenwood-Gleason 1955) Bernoulli 12번째 |
| SIG-7H-001 | [M10] | 3 | N6 | K(2) = n = 6 2D kissing number (Thue 1910) |

## 핵심 관찰

- **진짜 발견 55.0%** vs **재기록 39.7%** vs **NULL 5.3%**
- 신규 관찰이 재확인보다 많음 → 탐색 단계, 승격 queue 포화
- M7! breakthrough 후보: 35 개 — 재현 실험 대상
- cross_repo 연결 비율: 8.8% — 3리포 재현 네트워크
- resonance_n6 비율: 54.6% — n=6 환원 성공률
