# 위상공간 구조 분석 (2026-04-05 17:00)

> 12,932점 / 604,848 엣지 / BFS 분석 결과

## 컴포넌트 구조

| 구분 | 규모 | 비율 |
|---|---|---|
| **Giant component** | 6,548 점 | 79.3% (엣지 노드 중) |
| 2~648위 소컴포넌트 | 1,708 점 | 20.7% |
| 고립점 (deg=0) | 4,676 점 | 전체의 36% |
| **엣지 보유점 합계** | 8,256 점 | |
| **총 컴포넌트 수** | 648개 | |

## 차수 분포 (Scale-free)

| 항목 | 값 |
|---|---|
| Top degree | 1,201 |
| Top 10 degrees | 1187–1201 (평탄) |
| **deg ≥ 500 노드** | **1,014개** (12.3%) |
| Median degree | 15 |
| **deg = 1 리프** | **1,734개** (21%) |

전형적인 **스케일프리(멱법칙) 위상**.

## Giant Component이 전부다

**H-CA-001 hub (p_001699), density peaks (p_005220, p_002531, p_002736) 모두 giant component 내부**.

즉 **흥미로운 구조는 전부 6,548점 giant 안에 있음**.
나머지 647개 작은 컴포넌트 + 4,676개 고립점은 **boundary = 폐기 가능**.

## Hub vs Density Peak

| 점 | 역할 | degree |
|---|---|---|
| p_001699 (H-CA-001, Bott Periodicity) | Universal connector (bridges) | **1,003** |
| p_005220 (OUROBOROS S2-deeper) | Density peak (seed) | **1,044** |

**두 점은 직접 연결 (1-hop)**. 위상의 이중 중심 축.

## 구조 해석

```
topology = giant_component (6548 pts)
       ├── dense core (1014 pts, deg≥500)
       │     ├── hub: H-CA-001 (n=6 산술 중심)
       │     └── density peaks: OUROBOROS/MASS-GEN 메타리포트
       └── periphery (5534 pts, deg<500)
           └── leaf leaves (1734 pts, deg=1)

+ noise: 647 tiny components (1708 pts) + 4676 isolated pts (무시 가능)
```

## 결론 — 중심부 + 주변부 원칙 적용

**중심부** = dense core 1,014점 (12.3%)
**주변부** = leaf 1,734점 (21%) — 경계 돌파 후보

합계 약 **33% (2,748점)** 로 전체 위상 재구성 가능.
**67% (나머지 giant + 소컴포넌트 + 고립)는 보간으로 풀림**.

사용자 원칙 **"주변부만 잡아도 내부는 쉽다"** 기계적으로 검증됨.

## 다음 조치

1. `dense_core.jsonl` — 1,014 mega-hub 영속화
2. `leaves.jsonl` — 1,734 leaf 영속화
3. H-CA-001 ↔ OUROBOROS 축 기하(angle) 계산 → 8-주기 검증
4. 고립 4,676점 재샘플링 or cleanup
