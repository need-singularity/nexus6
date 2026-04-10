# 3축 중심 구조 확정 (2026-04-05 17:40)

> 4.66M edges, 7258 노이즈 필터 후 3121 semantic 점 분석.

## 세 개의 독립 축

| 축 | 대표 점 | 역할 | 측정 방법 |
|---|---|---|---|
| **A. Cross-domain Bridge** | p_001699 H-CA-001 (Bott σ-τ=8) | 도메인 간 통로 | pairwise bridges (4/5 pair 최고) |
| **B. Semantic Mass** | p_004051 EVOL-031 (DNA=φ(6)=2) | 의미 중심 | semantic-to-semantic deg=843 |
| **C. Self-foundation** | p_003386 sigma-tau=8.0 상수 | 기반 상수 | eps=0.3 raw deg=1201 |

세 축은 서로 다른 질문에 답함:
- A: "도메인들을 **잇는** 것은?" → Bott Periodicity
- B: "의미적으로 **가장 많이 연결된** 가설은?" → DNA=2가닥
- C: "시스템이 **반복 발견하는** 상수는?" → σ(6)-τ(6)=8

## Top 15 Semantic Mass (deg 740–843)

**공통 테마: "생물학 + 음악이론 × n=6 산술"**

| Rank | Deg | 내용 |
|---|---|---|
| 1 | 843 | EVOL-031 DNA 2가닥 = φ(6)=2 |
| 2 | 819 | EVOL-001 대멸종 = 6 |
| 3 | 814 | CLEFNOTE-002 C음자리표 = sopfr |
| 4 | 809 | EVOL-088 줄기세포 5단계 |
| 5 | 792 | EVOL-005 생물 6계 |
| 6 | 791 | NOTESHAPE-001 채운음표 = τ(6)=4 |
| 7 | 788 | CLEFNOTE-007 음표 시가 6종 |
| 8 | 780 | EVOL-017 세포골격 3종 |
| 9 | 763 | EVOL-103 종분화 = τ(6)=4 |
| 10 | 762 | CLEFNOTE-009 음고류 = Z₁₂=Z_σ(6) |
| 11 | 752 | EVOL-014 감수분열 산물 = τ(6)=4 |
| 12 | 750 | EVOL-098 보체경로 3 |
| 13 | 743 | CRITEXP-001 임계지수 6 |
| 14 | 740 | EVOL-039 RNA 스플라이싱 2단계 |
| 15 | 740 | EVOL-070 폐엽 = sopfr(6)=5 |

**15/15 가 TECS-L 도메인**. **14/15가 EVOL/CLEFNOTE/NOTESHAPE/CRITEXP 계열**.

## 노이즈 분석 (필터된 7258점)

| 유형 | 개수 | 특성 |
|---|---|---|
| LOOP-010/012/014/018 | 784 | 자동 발견 루프 덤프 (각 ~260개) |
| MASS-GEN-* | 4 | 대량 생성 리포트 |
| OUROBOROS | 7 | 진화 리포트 |
| raw constants (discovery_log) | 6463 | 원시 상수 발견 (반복) |

**핵심**: 원시 상수 6463개는 의미적 가중치 없음. 반복되는 값을 **1 unique 상수**로 압축하면 진짜 structure 보임.

## 다음 실험

1. **유일 상수 압축**: `{(constant, value)}` 집합으로 discovery_log 6463 → ~30-50개 unique로 축소
2. **3축 간 geodesic**: A↔B, A↔C, B↔C 최단거리 측정
3. **EVOL 계열 sub-cluster**: 생물 vs 음악 vs 물리 세부 분리
4. **H-CA-001의 semantic deg 확인**: SEDI 도메인 내 순위
