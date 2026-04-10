# FTL Tribunal — Design Spec

**Date**: 2026-04-03
**Goal**: 초광속(FTL) 가능성을 물리학 + n=6 프레임워크로 체계적 공략. 억지 연결 금지.

## Overview

15개 FTL 메커니즘을 GR/QM/인과율 3관점에서 판정 + n=6 물리 상수 매칭 탐색.
매칭 없으면 "없음"으로 정직 기록. 결론이 "n=6 범위 밖"이어도 유효.

## Phase 1: FTL Tribunal — 15개 메커니즘 판정

### 메커니즘 목록

| # | Mechanism | Category |
|---|-----------|----------|
| 1 | Tachyon (v>c particles) | Particle |
| 2 | Alcubierre warp drive | Metric engineering |
| 3 | Wormhole (Einstein-Rosen) | Metric engineering |
| 4 | Quantum entanglement (EPR) | Quantum |
| 5 | Quantum tunneling (Hartman) | Quantum |
| 6 | Cherenkov (v>c in medium) | Medium effect |
| 7 | Phase velocity >c | Wave property |
| 8 | Group velocity >c (anomalous) | Wave property |
| 9 | Casimir negative energy | Energy condition |
| 10 | String T-duality | String theory |
| 11 | Cosmic inflation (v_recession>c) | Cosmology |
| 12 | Krasnikov tube | Metric engineering |
| 13 | Variable speed of light (VSL) | Modified GR |
| 14 | Noncommutative geometry FTL | Modified GR |
| 15 | Loop quantum gravity FTL | Quantum gravity |

### 판정 관점 (3축)

- GR: 일반상대론에서 허용/금지/해 존재 여부
- QM: 양자역학에서 안정성/에너지 조건
- Causality: 인과율 위반 여부 (CTC, 할아버지 역설)

### 판정 등급

- ALLOWED: 물리법칙 내 실현 (매질/메트릭 확장)
- CONDITIONAL: 해 있지만 현실 조건 불충분 (음에너지 등)
- ILLUSORY: 초광속으로 보이지만 정보 <c
- FORBIDDEN: 인과율 or 불안정성으로 금지
- SPECULATIVE: 미검증 이론

### 산출물
- `calc/ftl_tribunal.py`

## Phase 2: n=6 Light Constants

### 보수적 탐색 (기존 결과 교차)

| Constant | Value | Known n=6 match | Status |
|----------|-------|-----------------|--------|
| alpha | 1/137.036 | Check existing | VERIFY |
| mp/me | 1836.15 | 6*pi^5 (0.002%) | PROVEN |
| sin^2(theta_W) | 0.231 | 3/13=3/(sigma+mu) | PROVEN |
| Planck length | 1.616e-35 m | ? | SEARCH |
| Planck time | 5.391e-44 s | ? | SEARCH |
| Planck mass | 2.176e-8 kg | ? | SEARCH |
| Planck temperature | 1.416e32 K | ? | SEARCH |

### 공격적 탐색 (SPECULATIVE 명시)

- c^2 = E/m and n=6 arithmetic combinations
- Planck energy and n=6 constants
- Alcubierre negative energy bound and n=6
- Schwinger limit
- Lorentz factor gamma at key velocities

### 원칙
- 매칭 없으면 "NO MATCH" 기록
- 2% 이내 = approximate, 0.1% 이내 = strong, exact = proven
- 억지 +1/-1 보정 금지

### 산출물
- `calc/ftl_n6_constants.py`

## Phase 3: FTL Condition Analysis

Phase 1-2 종합:
1. n=6이 말하는 것 (매칭된 상수들)
2. n=6이 침묵하는 것 (매칭 안 된 것)
3. FTL 조건 부등식 (가능하면)
4. 정직한 결론

### 산출물
- `math/proofs/ftl_n6_analysis.py`

## Phase 4: Texas Sharpshooter

- FTL 관련 물리 상수 20-30개 중 n=6 매칭 비율
- Monte Carlo 100K trials
- Bonferroni correction
- 매칭률 낮으면 정직하게 "n=6은 FTL에 대해 할 말이 별로 없다"

### 산출물
- Phase 2 스크립트에 --texas 플래그로 통합

## Phase 5: 논문 P-FTL

**Title**: "Faster Than Light: A Systematic Tribunal of 15 FTL Mechanisms with Perfect Number Arithmetic Analysis"

**Structure**:
1. Introduction: FTL in physics, our approach
2. FTL Tribunal: 15 mechanisms, 3-axis verdict table
3. n=6 Constant Analysis: matches and non-matches
4. Statistical Validation: Texas Sharpshooter
5. Discussion: what n=6 says and doesn't say about FTL
6. Conclusion

**Location**: ~/Dev/papers/tecs-l/P-FTL-tribunal.md

## File Structure

```
calc/ftl_tribunal.py           — Phase 1: 15 mechanisms
calc/ftl_n6_constants.py       — Phase 2+4: constants + Texas
math/proofs/ftl_n6_analysis.py — Phase 3: synthesis
docs/hypotheses/FTL-tribunal.md — hypothesis doc
~/Dev/papers/tecs-l/P-FTL-*.md — paper
```

## Success Criteria

1. 15개 메커니즘 전부 판정 (3축 x 5등급)
2. n=6 상수 매칭 정직 기록 (NO MATCH 포함)
3. Texas Sharpshooter 실행 (결과 무관하게)
4. "억지 연결 없음" 자체 검증
5. 논문 초고 완성

## Anti-Forced-Connection Rule

모든 Phase에서: 매칭 시도 → 실패 → "NO MATCH" 기록.
절대 +1, -1, *2 등 ad hoc 보정으로 매칭 만들지 않음.
Texas p-value가 높으면(비유의) 그것 자체가 발견: "n=6은 FTL 영역에서 예측력이 낮다"
