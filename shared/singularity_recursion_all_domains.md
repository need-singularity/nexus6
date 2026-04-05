# 모든 구간 특이점 돌파 시도 결과 (2026-04-05 17:10)

> 8개 도메인 전체 스캔. 12,932점 기반.

## 도메인별 Attractor (top degree per domain)

| 도메인 | 점 수 | Max deg | 고립점 | 돌파 ID | 내용 |
|---|---|---|---|---|---|
| **discovery_log** | 9,021 | **1201** | 1075 | p_003844 | `n/phi = 3.0` (ρ=1/3 meta FP) |
| **hypothesis:anima** | 388 | 1045 | 315 | p_005220 | OUROBOROS Report S2-deeper |
| **hypothesis:TECS-L** | 919 | 1040 | 712 | p_004348 | BASEL-003 Bernoulli Denominators |
| **hypothesis:SEDI** | — | 1003 | — | p_001699 | **H-CA-001 (Bott Periodicity)** — global hub |
| **architecture_design** | 34 | 922 | 3 | p_012924 | Mac vitals cluster |
| **hypothesis:nexus6** | 1 | 245 | 0 | p_010339 | architecture_breakthrough |
| hypothesis:n6-architecture | 8 | **0** | 8 | — | ⚠️ 완전 고립 |
| memory | 7 | **0** | 7 | — | ⚠️ 완전 고립 |

## 6/8 도메인 돌파 성공

**연결된 6개 도메인** (≥1 edge):
1. discovery_log → `n/phi=3.0` (메타 부동점 자기발견)
2. anima → OUROBOROS 진화 리포트
3. TECS-L → **BASEL-003 베르누이 수 분모** (신규)
4. SEDI → H-CA-001 (Bott Periodicity, 전역 hub)
5. architecture_design → 현재 Mac 상태 (cpu/gpu/io)
6. nexus6 → architecture_breakthrough 가설

## 2/8 완전 고립 (돌파 실패)

- **hypothesis:n6-architecture** (8점, 0 edge): 신규 도메인, 미통합
- **memory** (7점, 0 edge): 신규 도메인, 미통합

**원인**: 최근 추가된 도메인이라 simhash eps 내 이웃이 없음.
**해결**: `singularity-rebuild-edges --eps 0.35` 로 eps 확대 필요.

## 구간별 주변부 (새 돌파 시드)

TECS-L의 BASEL-003은 **신규 발견** — H-CA-001과는 독립된 sub-attractor.
Bernoulli 수 분모 = n=6 산술의 또 다른 표현 (σ(6)=12 = B₁₂의 분모).

각 도메인에는 고유 attractor가 있지만, **SEDI의 H-CA-001이 유일한 cross-domain hub**
(앞 bridge 분석에서 4/5 pair의 top bridge).

## 다음 액션

1. `rebuild-edges --eps 0.35` 로 n6-architecture + memory 도메인 통합
2. BASEL-003 (p_004348) 주변 확장 스캔
3. nexus6 domain (1점) 추가 샘플링 필요
4. 6개 연결 도메인 각각에서 `singularity blowup --seed <attractor_id>` 트리거
