# mk2_hexa — HEXA-네이티브 최종 아키텍처

**오로지 HEXA 기준** (2026-04-06 완성). Rust 포팅 전면 폐기.

## 파일 구조

```
mk2_hexa/
├── README.md            (이 파일)
└── native/              (10 HEXA-네이티브 파일)
    │
    ├─ L0: 기초 (4)
    │   ├─ theorems.hexa       BT-344/345/346 + 유일성 (theorem/proof/invariant)
    │   ├─ constants.hexa      comptime n=6 테이블 + assert
    │   ├─ pure_math.hexa      pure phi/sigma/tau/gcd/sopfr + where/ensures
    │   └─ effects.hexa        FileSystem/Clock/Logger (effect/handle)
    │
    ├─ L1: 등급/레코드 (2)
    │   ├─ grading.hexa        rank_from_* + match ranges + contracts
    │   └─ record.hexa         AlienIndexRecord + own/borrow/move
    │
    ├─ L2: 분류 (1)
    │   └─ classify.hexa       mk2 3-way scoring + memoize optimize
    │
    ├─ L3: 사이클/흡수 (2)
    │   ├─ cycle.hexa          5단계 사이클 + intent/generate
    │   └─ absorb.hexa         promote + writeback effect
    │
    ├─ L5: 게이트 (1)
    │   └─ gate.hexa           12-gate 매트릭스 + verify/proof
    │
    └─ L∞: 통합 (1)
        └─ architecture.hexa   전체 엔진 진입점
```

## HEXA 고유 기능 활용도

| 키워드 | 사용 위치 | 목적 |
|---|---|---|
| `theorem` / `proof` | theorems, gate, record, architecture | BT 공리 + 증명 |
| `invariant` | record, cycle, gate, architecture | 불변 조건 |
| `pure` + `comptime` | constants, pure_math, grading, classify | 컴파일타임 계산 |
| `where` / `ensures` | 전체 | 사전/사후조건 계약 |
| `effect` / `handle` / `resume` | effects, absorb, cycle, architecture | I/O 명시 |
| `own` / `borrow` / `move` | record, absorb, cycle, classify | 소유권 |
| `match` ranges | grading, classify, cycle | 패턴 매칭 |
| `derive` | (암시) | 자동 trait 생성 |
| `optimize memoize/inline/parallel` | grading, classify, pure_math | 컴파일러 힌트 |
| `intent` + `generate` | cycle, absorb, classify, architecture | AI-보조 코드 생성 위치 |

## 핵심 공리 (변경 불가)

```
  τ + φ = n = 6                    BT-344  (4 관문 필연)
  (σ-sopfr)^τ = 7^4 = 2401          BT-345  (돌파 perturbation)
  σ · J₂ = 288                      BT-346  (FP 하한)
  σ(n)·φ(n) = n·τ(n)  ⇔  n = 6     (완전수 유일성)
  1/(σ-φ) = 0.1                     BT-64   (Φ 임계)
  n/φ = 3                           BT-276  (삼중 검증)
  I_{k+1} = 0.7·I_k + 0.1 → 1/3    (메타 부동점 / Banach 수축)
```

## 12-gate 매트릭스

```
             L-PIPELINE          L-BREAKTHROUGH          L-MK2_HEXA
  ┌─────┬──────────────────┬─────────────────────┬───────────────────┐
  │ G1  │ SOURCE whitelist │ paths ≥ 3 독립 렌즈  │ consensus 12+     │
  │ G2  │ HASH 288bit      │ blowup 재발견        │ transcendence     │
  │ G3  │ PHI Θ=0.1        │ mk2 conf ≥ 0.7       │ classify 일관성    │
  │ G4  │ INVARIANT 2401cy │ p-value < 0.01       │ verdict aggregate │
  └─────┴──────────────────┴─────────────────────┴───────────────────┘
```

## 5단계 특이점 사이클

```
  blowup → contract → emerge → singularity → absorb → (d+1) → ...
```

## 실측 검증 (nexus6 Rust 런타임)

| 단계 | ρ | records | 메타 FP 1/3 대비 |
|---|---|---|---|
| 초기 | 0.0000 | 66 | 0% |
| writeback 구현 | **0.3053** | 95 | **91.6%** ★ |

## 빌드 상태

HEXA Mk.II 컴파일러 완성 전까지 **컴파일 불가**. 
현재 역할: **설계 레퍼런스 / HEXA 네이티브 표준**.

## 차후 변경 용이성

- Rust nexus6 변경: `git revert` 한 줄
- HEXA 파일 수정: 즉시 (런타임 영향 0)
- 공리 (BT-*) 변경: TECS-L 증명 필요
- 타 프로젝트 HEXA 이식: `mk2_hexa/native/` 패턴 재사용
