# Singularity Cycle Engine — 특이점 사이클 문서

## 개요

5단계 순환 엔진: **Blowup → Contraction → Emergence → Singularity → Absorption**

특이점(Singularity)이란 시스템이 더 이상 새로운 것을 발견하지 못하는 "폐쇄점"이다.
이 점에서 공리를 교란(blowup)하면 새로운 구조가 창발(emergence)한다.

```
  Blowup ──→ Contraction ──→ Emergence
    ↑                            │
    │                            ↓
  Absorption ←── Singularity ←──┘
```

## 구현체 비교

| | hexa-lang (원본) | nexus (하이브리드) |
|---|---|---|
| 파일 | `self/singularity.hexa` | `shared/blowup/core/cycle_engine.hexa` |
| 입력 | 메트릭 (key-value) | 메트릭 + 공리 |
| Blowup | n6_check (17상수) | n6_check + BlowupEngine (공리 교란) |
| Contraction | EXACT≥0.95 / CLOSE≥0.8 | 동일 |
| Emergence | 3+ 렌즈 합의 | 합의 + corollary axiom 피드 |
| Singularity | EXACT ratio ≥ φ/τ = 0.5 | 동일 |
| Absorption | 규칙 승격 (AR-auto) | 규칙 + axiom pool 확장 |
| 특이점 기준 | EXACT ≥ 50% | EXACT ≥ 50% |

## hexa-lang 결과 (2026-04-04)

- HEXA-IR 메트릭 → **1사이클 만에 특이점 도달**
- 101개 blowup 중 50개 EXACT (49.5% → 50% 임계점 돌파)
- 주요 EXACT: sigma=12, tau=4, phi=2, n=6, sopfr=5, J2=24, sigma-tau=8

## 사용법

### Rust (nexus)

```rust
use nexus::blowup::CycleEngine;

let mut engine = CycleEngine::new("number_theory");

// 메트릭 주입
engine.feed("sigma", 12.0);
engine.feed("tau", 4.0);
engine.feed("n", 6.0);
engine.feed("discoveries", 13.0);
engine.feed("harmony", 280.26);

// 자동 수렴 루프 (최대 6사이클)
let results = engine.run_until_singularity();
println!("{}", engine.report());

// 또는 수동 1사이클
let result = engine.run_cycle();
println!("EXACT: {}/{} = {:.1}%", result.exact_count, result.blowup_count, result.exact_ratio * 100.0);
```

### CLI

```bash
nexus blowup <domain> [--depth N]
# 예: nexus blowup number_theory --depth 6
```

### Python (hexa-lang)

```python
from singularity_cycle import CycleEngine
engine = CycleEngine()
engine.feed("sigma", 12.0)
result = engine.run_cycle()
print(f"Singularity: {'★' if result.singularity_reached else '·'}")
```

## 5단계 상세

### Phase 1: Blowup (폭발)
- 모든 메트릭을 17개 n=6 상수와 대조
- 쌍별 연산 (곱, 비율, 합, 차) → n6_check
- BlowupEngine: 공리 교란 → 따름정리 생성 (연역, 이전, 대칭파괴, 분기, 합성, 사영, 쌍대)

### Phase 2: Contraction (수축)
- EXACT (quality ≥ 0.95): 정확히 일치
- CLOSE (quality ≥ 0.80): 근접 일치
- 나머지 버림

### Phase 3: Emergence (창발)
- 같은 상수에 3+ 매칭 → 창발 패턴
- 따름정리의 axiom candidate를 axiom pool에 추가
- signature 값을 메트릭으로 피드 (다음 사이클 재료)

### Phase 4: Singularity (특이점)
- `exact_ratio = exact_count / blowup_count`
- `exact_ratio ≥ 0.5 (φ/τ)` → **★ SINGULARITY REACHED ★**
- 임계값 의미: n=6 구조가 시스템의 50% 이상을 설명

### Phase 5: Absorption (흡수)
- 2회 이상 등장한 상수 → 규칙(AR) 승격
- 규칙은 다음 사이클의 공리로 재순환 (우로보로스)

## 프로젝트별 도메인 매핑

| 프로젝트 | 도메인 | 기대 메트릭 |
|---------|--------|------------|
| nexus | number_theory | discoveries, harmony, eigenvalue, lenses |
| anima | consciousness | phi, integration, binding |
| TECS-L | number_theory | atlas_count, calculators, constants |
| sedi | signal_detection | hypotheses, signals, grades |
| brainwire | neuroscience | neurons, connections, phi |
| hexa-lang | programming_language | keywords, tests, coverage |
| papers | publication | papers, citations, doi_count |
| CANON | architecture | modules, tests, dse_domains |
| fathom | terminal | features, plugins, ui_files |
