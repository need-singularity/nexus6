# 특이점 돌파 로드맵 — mk1+mk2 조립

**Date**: 2026-04-05
**Status**: Active
**Goal**: mk1의 17개 모듈을 mk2 엔진 위에 조립 → d=2 돌파

---

## 현재 상태

| 지표 | 값 |
|------|-----|
| 총 레코드 | 100,938 |
| (1,10) | 100,893 (99.96%) |
| (0,0) | 34 |
| (0,8) | 11 |
| max d | 1 |
| 돌파율 ρ | 0.9996 |
| 메타 FP 목표 | 1/3 |

**문제**: d=1 레코드가 r=10에 고착 → d=2 승격 메커니즘 없음.
r=10 도달 기준이 자동 할당(verified_constants 일괄)이라 **진짜 검증 없이 천장에 도달**.

---

## 돌파 전략: 3단계

### Phase 1: 잔여 정리 + 검증 강화

**목표**: (0,0)/(0,8) → (0,10) → (1,0) 승격 + 기존 (1,10) 검증 재확인

| 모듈 | 역할 | 연결 |
|------|------|------|
| `verifier/n6_check` | 값 검증 → quality 점수 | assess.rs 입력 |
| `alien_index/assess` | quality→r 변환 | combine_signals_v2 |
| `mk2/classify_v2` | sector+confidence→r | combine_signals_v2 4번째 신호 |
| `calibration` | lens 정확도 가중치 | consensus 품질 보정 |

**작업**:
1. (0,0) 34개 → n6_match + mk2 classify → r 재계산
2. (0,8) 11개 → 추가 lens consensus 확보 → r=10 시도
3. (1,10) 무작위 100개 샘플링 → 실제 r 재계산 → 부풀려진 등급 탐지

### Phase 2: d=2 돌파 기준 정의 + 파이프라인 구축

**목표**: (1,10) → (2,0) 승격에 필요한 **제2사이클 닫기** 조건 정의

현재 `breakthrough()`는 r=10이면 기계적으로 승격하지만, d=2는 **질적으로 다른 검증**이 필요:

```
d=0: 값이 n6 상수와 일치하는가? (n6_match)
d=1: mk2 smooth-class로 유도 가능한가? (classify_v2)
d=2: 독립 경로 2개 이상이 같은 값에 수렴하는가? (교차검증)
```

**조립할 모듈:**

| 모듈 | d=2 역할 |
|------|---------|
| `telescope` (1013 lenses) | 독립 경로 생성기 — 서로 다른 렌즈가 같은 값 발견 |
| `blowup` | 공리 교란 → 새 추론 → 기존 값 재발견 여부 |
| `ouroboros` | 진화 루프 — 수렴 정체 감지 = 특이점 후보 |
| `mk2/lattice` | cross-layer edge — n|m 관계로 독립 확인 |
| `science/simulate` | Monte Carlo 검증 — 우연 확률 추정 |
| `dream` | 과거 발견 재조합 → 같은 값 독립 유도 |

**d=2 승격 기준 (제안)**:
```rust
fn can_promote_to_d2(record: &AlienIndexRecord) -> bool {
    let independent_paths >= 3;       // 3개 이상 독립 렌즈가 같은 값
    let blowup_rediscovery == true;   // 블로업에서 재발견
    let mk2_confidence >= 0.7;        // mk2 분류 고신뢰
    let monte_carlo_p < 0.01;         // 우연일 확률 < 1%
    independent_paths && blowup_rediscovery && mk2_confidence && monte_carlo_p
}
```

### Phase 3: 자동 돌파 사이클

**목표**: 파이프라인 자동화 → `nexus6 breakthrough --target d2`

```
┌─────────────────────────────────────────────────────┐
│                  돌파 파이프라인                       │
│                                                     │
│  telescope ──┐                                      │
│  (1013 lens) │                                      │
│              ├──→ 후보 수집 ──→ 교차검증 ──→ 판정    │
│  blowup ─────┤       │            │          │      │
│  (6-depth)   │       │            │          │      │
│              │   mk2 classify  science    alien-idx │
│  dream ──────┤   + n6_check    simulate   promote   │
│  (recombine) │       │            │          │      │
│              │       ▼            ▼          ▼      │
│  ouroboros ──┘   sector+conf   p-value    (d+1,0)  │
│                                                     │
│  growth ← 진행 추적    reward ← 발견 보상 신호      │
│  meta_gate ← 파라미터 최적화                         │
│  genetic_prog ← 렌즈 진화                           │
└─────────────────────────────────────────────────────┘
```

**모듈 조립 순서:**

| 순서 | 조립 | 파일 | 비고 |
|------|------|------|------|
| 1 | n6_check + mk2 classify_v2 + assess_v2 | `alien_index/assess.rs` | ✅ 완료 |
| 2 | blowup → mk2 classify | `blowup/corollary.rs` | ✅ 완료 (이번 세션) |
| 3 | topology → mk2 classify | `singularity_recursion/topology.rs` | ✅ 완료 (이번 세션) |
| 4 | telescope → mk2 sector 필터 | `telescope/` | 미구현 |
| 5 | d=2 판정기 구현 | `alien_index/breakthrough.rs` (신규) | 미구현 |
| 6 | science/simulate → p-value | `science/` | 미구현 |
| 7 | dream → mk2 재조합 | `dream/` | 미구현 |
| 8 | CLI: `nexus6 breakthrough` | `cli/parser.rs + runner.rs` | 미구현 |
| 9 | growth 통합 | `growth/` | 미구현 |
| 10 | 자동 루프 | `nexus6 daemon --breakthrough` | 미구현 |

---

## 성공 기준

1. **(0,*) → (1,0)**: 잔여 45개 전부 승격 (ρ_d0 = 1.0)
2. **(1,10) → (2,0)**: 최소 1개 레코드가 d=2 돌파 (교차검증 통과)
3. **ρ(전체)**: 돌파율이 메타 FP 1/3에 수렴하기 시작
4. **자동화**: `nexus6 breakthrough` 한 줄로 실행 가능

---

## 즉시 실행 가능한 작업

1. **Phase 1 잔여 정리**: (0,0) 34개의 n6_match + mk2 classify 실행
2. **d=2 판정기 프로토타입**: `alien_index/breakthrough.rs` 구현
3. **telescope mk2 필터**: 렌즈 스캔 결과에 sector 자동 태깅
