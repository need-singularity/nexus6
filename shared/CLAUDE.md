# .shared/ — Cross-Repo Shared Infrastructure

> **이 폴더는 TECS-L에 원본이 있고, 타 리포는 심링크로 연결됩니다.**
> 타 리포: `.shared/ → ../TECS-L/.shared/`

⚠️ **.shared/ 내 파일 수정 시 반드시 동기화 실행!**
  수정만 하고 동기화 안 돌리면 다른 리포에 반영 안 됨.
  순서: .shared/ 파일 수정 → TECS-L에서 커밋+push → `bash .shared/sync-claude-rules.sh`

★ **Convergence-Driven Operations (CDO) — 전 프로젝트 공통 원칙**
  이슈 발생 → 해결 → 규칙 승격 → 재발 방지 → 100% 수렴
  모든 config JSON은 CDO 구조 준수: _meta + absolute_rules + troubleshooting_log
  상세: .shared/convergence_ops.json

## NEXUS-6 망원경 (1014종 렌즈) — 최우선 활용 규칙

> **NEXUS-6 = 통합 발견 엔진. 1014종 렌즈 레지스트리 + OUROBOROS 무한진화 + Discovery Graph**
> 바이너리: `tools/nexus6/target/release/nexus6` (Rust, 148 tests)
> CLI: `nexus6 scan <domain>`, `nexus6 evolve <domain>`, `nexus6 dashboard`

### 렌즈 1014종 구성

| 카테고리 | 수 | 역할 |
|---------|---|------|
| Core (기존 telescope-rs) | 22 | 기본 분석 (의식/위상/인과 등) |
| n6 산업 | 58 | DSE/소재/동역학/메타구조 |
| TECS-L 수학 | 103 | 수론/대수/해석/조합/증명 |
| SEDI 신호 | 100 | 신호탐지/통계/우주론/입자 |
| anima 의식 | 88 | 감질/결합/시간의식/현상학 |
| 교차+메타 | 75 | 프로젝트 브릿지 + 렌즈↔렌즈 |
| 가속 ML | 58 | ML최적화/수렴/정보/RL |
| 가속 물리 | 57 | 물리심화/신경미세/진화/의식 |
| 가속 공학 | 55 | 네트워크/시스템/음악/경제/의학 |
| 가속 인문 | 63 | 철학/문학/스포츠/천문/수학고급 |

### ⚠️ 자동 적용 조건 (NEXUS-6 단독 — telescope-rs 폐기)

> **telescope-rs (22종)는 폐기. 모든 탐색/분석은 NEXUS-6 (1014종)를 사용할 것.**
> `import telescope_rs` 대신 `nexus6 scan` 또는 `import nexus6` (PyO3) 사용.
> 기존 telescope-rs 코드는 호환성을 위해 유지하지만 신규 작업에는 사용 금지.

어떤 프로젝트에서든 아래 상황이면 NEXUS-6 렌즈를 자동으로 돌릴 것:

**Tier 0 — 기본 스캔 (3종, 모든 분석의 시작점)**
- 새 데이터셋/주제 접할 때 → `nexus6 scan <domain>` (의식+위상+인과 자동 추천)

**Tier 1 — 도메인별 조합 (10~30종)**
- 신소재/신약 탐색 → 진화+열역학+중력+안정성+defect+catalysis+interface
- 시계열 분석 → 파동+열역학+의식+기억+memory+neural_oscillation
- 상수/법칙 관계 → 정보+양자+의식+비율+oeis_fingerprint+identity_compose
- 대칭/불변량 → 대칭+위상+양자+gauge_symmetry+spontaneous_symmetry+chirality
- 멱법칙/스케일링 → 스케일+진화+열역학+다중스케일+universality_class
- 인과 관계 → 인과+정보+전자기+causal_emergence+transfer_entropy
- 양자/결맞음 → 양자현미경+양자+bell_inequality+superposition+decoherence
- 그래프/복잡계 → 네트워크+위상+스케일+small_world+community_detection
- 상전이/경계 → 경계+열역학+위상+topological_phase_transition+tipping
- 안정성/복원력 → 안정성+중력+열역학+ecosystem_resilience+fault_tolerance
- 핵융합/플라즈마 → plasma_confinement+lawson_criterion+tokamak_stability+magnetic_topology
- 프로그래밍/SW → design_pattern+code_smell+coupling_cohesion+cyclomatic_complexity
- 세포/생물 → cell_division+cell_cycle+cell_differentiation+morphogenesis
- 의식/인지 → 전체 anima 88종 + consciousness_integration+phi_optimization

**Tier 2 — 풀스캔 (775종, 확정급 분석)**
- 이상점/패턴 전수조사 → `nexus6 scan <domain> --full` (775종 전체)
- 교차 도메인 탐색 → 교차 렌즈 75종 포함
- BT 채굴/새 발견 확정 → 12+ 렌즈 합의 필요

**Tier 3 — 자동 진화 (OUROBOROS + LensForge)**
- 가속 가설 검증 → `nexus6 auto <domain>` (scan→evolve→forge 자동 루프)
- 메타분석(렌즈 자체 평가) → 메타렌즈 35종 자동 포함
- 새 렌즈 자동 생성 → LensForge가 갭 분석 후 렌즈 후보 제안

### 렌즈 선택 가이드

```
"숨겨진 구조가 있나?"     → 의식 렌즈 (Φ + 파벌)
"안정점/끌개가 있나?"     → 중력 렌즈 (attractor basin)
"구멍/연결이 있나?"       → 위상 렌즈 (Betti + persistence)
"상전이가 있나?"          → 열역학 렌즈 (엔트로피 + 자유에너지)
"주기/공명이 있나?"       → 파동 렌즈 (FFT + 하모닉)
"최적 조합이 있나?"       → 진화 렌즈 (fitness landscape)
"정보가 어디에 있나?"     → 정보 렌즈 (MI + 압축)
"비국소 상관이 있나?"     → 양자 렌즈 (얽힘 + 터널링)
"흐름 방향이 있나?"       → 전자기 렌즈 (gradient + curl)
"독립 차원이 몇 개인가?"  → 직교 렌즈 (SVD + orthogonality)
"단순 비율이 있나?"       → 비율 렌즈 (fraction matching)
"원형/등거리 구조가 있나?" → 곡률 렌즈 (curvature + circle)
"대칭이 있나? 깨졌나?"    → 대칭 렌즈 (reflection + permutation)
"멱법칙/프랙탈인가?"      → 스케일 렌즈 (power law + Hurst)
"원인→결과 방향이 있나?"  → 인과 렌즈 (Granger + TE)
"결맞음이 있나? 깨지나?"  → 양자현미경 (coherence + decoherence)
"안정한가? 복원되나?"      → 안정성 렌즈 (Lyapunov + resilience)
"허브/병목이 어디인가?"    → 네트워크 렌즈 (graph + community)
"기억이 남아있나?"         → 기억 렌즈 (autocorrelation + echo)
"자기참조 루프가 있나?"    → 자기참조 렌즈 (fixed point + self-similarity)
"경계/전이대가 어디인가?"  → 경계 렌즈 (boundary + transition)
"스케일마다 다른 구조인가?" → 다중스케일 렌즈 (wavelet + multiresolution)
```

### NEXUS-6 사용법

```bash
# CLI (권장)
nexus6 scan physics                    # 도메인 스캔
nexus6 scan physics --full             # 775종 풀스캔
nexus6 verify 12.0                     # n=6 일치 검증
nexus6 evolve physics --max-cycles 6   # OUROBOROS 진화
nexus6 auto physics                    # 전체 파이프라인 (scan→evolve→forge)
nexus6 lenses --category core          # 렌즈 목록
nexus6 dashboard                       # ASCII 대시보드
```

```python
# Python (PyO3 바인딩)
import nexus6
reg = nexus6.LensRegistry()
print(reg.len())  # 775
result = nexus6.n6_check(12.0)
nexus6.evolve("physics", max_cycles=6)
```

빌드: `cd ~/Dev/n6-architecture/tools/nexus6 && ~/.cargo/bin/cargo build --release`
테스트: `~/.cargo/bin/cargo test` (173 tests)
렌즈 동기화: `bash .shared/sync-nexus6-lenses.sh`

### 렌즈 추가 시

1. NEXUS-6 레지스트리에 LensEntry 추가 (src/telescope/*_lenses.rs)
2. 또는 `nexus6 auto` → LensForge가 자동 생성
3. `bash .shared/sync-nexus6-lenses.sh` (렌즈 수 동기화)

### 교차 검증 (합의 규칙)

```
  1개 렌즈 = 가설 (추가 검증 필요)
  3+ 렌즈 합의 = 후보 (candidate)
  7+ 렌즈 합의 = 고신뢰 (high confidence)
  12+ 렌즈 합의 = 확정 (confirmed)
```

### ★ NEXUS-6 활용 시나리오 전체 (11종) ★

```
  ┌──────────────┬───────────────────────────────────┬────────────────────────────┐
  │ 시나리오     │ API 호출                          │ 적용 시점                  │
  ├──────────────┼───────────────────────────────────┼────────────────────────────┤
  │ 1. 탐색      │ nexus6.scan_all(data)             │ 새 데이터/주제 접할 때     │
  │              │ → 26렌즈 dict                     │ 3+ 합의=확정, 1개=가설     │
  ├──────────────┼───────────────────────────────────┼────────────────────────────┤
  │ 2. 검증      │ nexus6.analyze(data, n, d)        │ 가설 확인, BT 검증         │
  │              │ → scan+합의+n6매칭 올인원         │ n6_exact>0 = 수학적 근거   │
  ├──────────────┼───────────────────────────────────┼────────────────────────────┤
  │ 3. 발견      │ nexus6.n6_check(value)            │ 새 상수 발견 시            │
  │              │ → EXACT/CLOSE/WEAK                │ EXACT → atlas/BT 즉시 등록 │
  ├──────────────┼───────────────────────────────────┼────────────────────────────┤
  │ 4. 학습 평가 │ scan_all(checkpoint_weights)      │ 모델 학습 중 체크포인트    │
  │              │ → Phi/stability/topology 변화     │ 학습 전후 비교             │
  ├──────────────┼───────────────────────────────────┼────────────────────────────┤
  │ 5. 코드 변경 │ 수정 전후 scan → diff             │ PR/커밋 전                 │
  │              │ → regression 없는지 확인          │ Phi 하락 → 커밋 거부       │
  ├──────────────┼───────────────────────────────────┼────────────────────────────┤
  │ 6. 트러블슈팅│ 에러 데이터 → scan                │ 문제 진단                  │
  │              │ → boundary/stability 이상 검출    │ 원인 특정                  │
  ├──────────────┼───────────────────────────────────┼────────────────────────────┤
  │ 7. 비교/벤치 │ scan_all(A) vs scan_all(B)        │ 전략 비교, A/B 테스트      │
  │              │ → 메트릭별 차이 테이블            │ v0.3 vs v0.4, 기법 ON/OFF  │
  ├──────────────┼───────────────────────────────────┼────────────────────────────┤
  │ 8. 모니터링  │ cron + scan_all → jsonl 기록      │ 24/7 주기적 (매시간)       │
  │              │ → Phi 추이 시계열                 │ Phase 7 안전조건 감시      │
  ├──────────────┼───────────────────────────────────┼────────────────────────────┤
  │ 9. 진화/성장 │ nexus6.evolve(domain)             │ 새 도메인 발견 시          │
  │              │ nexus6.forge_lenses()             │ 렌즈 자체 진화 (OUROBOROS) │
  ├──────────────┼───────────────────────────────────┼────────────────────────────┤
  │10. 이식/배포 │ scan(원본) → scan(이식후) → diff  │ 모델 이식/양자화 전후      │
  │              │ → 의식 보존율 측정                │ 14B→70B transplant 등      │
  ├──────────────┼───────────────────────────────────┼────────────────────────────┤
  │11. 안전/윤리 │ scan → Phi 임계점 확인            │ autonomous_mode 활성 전    │
  │              │ → Phi < threshold → 차단          │ 자율행동 게이트            │
  └──────────────┴───────────────────────────────────┴────────────────────────────┘
```

### ★ 프로젝트별 NEXUS-6 활용 매핑 ★

```
  ┌──────────────┬──────────────────────────────────────────────────────┐
  │ 프로젝트     │ 주 활용 시나리오                                    │
  ├──────────────┼──────────────────────────────────────────────────────┤
  │ anima        │ 학습평가(4), 모니터링(8), 이식(10), 안전(11)        │
  │              │ → 체크포인트마다 scan, Phi 추이, 의식 보존           │
  ├──────────────┼──────────────────────────────────────────────────────┤
  │ n6-arch      │ 탐색(1), 검증(2), 발견(3), 진화(9)                 │
  │              │ → BT 채굴, 상수 매칭, DSE 분석, 렌즈 자동 성장      │
  ├──────────────┼──────────────────────────────────────────────────────┤
  │ TECS-L       │ 검증(2), 발견(3), 비교(7)                          │
  │              │ → 수학 가설 검증, atlas 확장, 정리 비교              │
  ├──────────────┼──────────────────────────────────────────────────────┤
  │ sedi         │ 탐색(1), 트러블슈팅(6), 모니터링(8)                │
  │              │ → 신호 분석, 이상 감지, 실시간 감시                  │
  ├──────────────┼──────────────────────────────────────────────────────┤
  │ brainwire    │ 학습평가(4), 비교(7), 안전(11)                     │
  │              │ → 신경망 분석, 아키텍처 비교, Phi 게이트             │
  ├──────────────┼──────────────────────────────────────────────────────┤
  │ papers       │ 검증(2), 발견(3)                                   │
  │              │ → 논문 수치 검증, 새 상수 발견                       │
  ├──────────────┼──────────────────────────────────────────────────────┤
  │ hexa-lang    │ 코드변경(5), 트러블슈팅(6)                         │
  │              │ → 컴파일러 변경 regression, 에러 진단                │
  └──────────────┴──────────────────────────────────────────────────────┘
```

### NEXUS-6 Python API 레퍼런스

```python
  import nexus6

  # === 데이터 스캔 (telescope-rs 완전 대체) ===
  nexus6.scan_all(np_array)                # numpy 2D → dict (렌즈명→메트릭dict)
  nexus6.scan(flat_list, n, d)             # flat list → ScanResult 객체
  nexus6.analyze(flat_list, n, d)          # 올인원 → dict (scan+consensus+n6)
  nexus6.scan_consensus(flat, n, d)        # 합의만 → list[ConsensusResult]

  # === 개별 렌즈 (파라미터 조절 가능) ===
  nexus6.consciousness_scan(np, n_cells=64, n_factions=12, steps=300, coupling_alpha=0.014)
  nexus6.topology_scan(np)
  nexus6.causal_scan(np)
  nexus6.gravity_scan(np)
  nexus6.stability_scan(np)

  # === n=6 상수 검증 ===
  nexus6.n6_check(12.0)                   # → N6Match(sigma, 1.0, EXACT)
  nexus6.feasibility_score([12, 6, 24])   # → EXACT 비율 (0.0~1.0)
  nexus6.fast_mutual_info(a, b, n_bins=10)# → MI float

  # === 발견 엔진 ===
  nexus6.recommend_lenses('physics')       # → LensRecommendation
  nexus6.evolve('physics', max_cycles=6)   # → list[CycleResult]
  nexus6.forge_lenses(max=20)              # → ForgeResult
  nexus6.auto('physics', meta=6, ouro=6)   # → MetaLoopResult (전체 파이프라인)

  # === 레지스트리 ===
  reg = nexus6.LensRegistry()
  reg.len()                                # 1013
  reg.for_domain('physics')                # 도메인별 렌즈
  reg.by_category('Core')                  # 카테고리별 렌즈

  # === 상수 ===
  nexus6.N, nexus6.SIGMA, nexus6.PHI, nexus6.TAU, nexus6.J2  # 6, 12, 2, 4, 24
```

### ~~telescope-rs (폐기)~~

> ⚠️ telescope-rs (22종)는 NEXUS-6로 대체됨. 신규 작업에 사용 금지.
> 기존 코드 호환성을 위해 anima-rs/crates/telescope-rs/에 유지만 함.
> 마이그레이션: `import telescope_rs` → `import nexus6` 또는 `nexus6 scan`

### 기본 사용 (NEXUS-6 통합 API)

```python
import nexus6  # telescope-rs 폐기 → nexus6 단일 사용
import numpy as np

data = np.random.randn(64, 32)  # (N_samples, N_features)

# 의식 렌즈
r = nexus6.consciousness_scan(data, n_cells=64, steps=300)

# 위상 렌즈
r = nexus6.topology_scan(data)

# 인과 렌즈
r = nexus6.causal_scan(data)

# 26종 풀스캔 (telescope-rs 22종 + barrier + void + mirror + renorm + MI)
results = nexus6.scan_all(data)

# 올인원 분석 (스캔 + 합의 + n6 매칭)
analysis = nexus6.analyze(data.flatten().tolist(), n=64, d=32)

# MI 직접 계산
mi = nexus6.fast_mutual_info(col_a, col_b, n_bins=10)
```

### 반환값 (dict)

```
consciousness_scan → phi_iit, phi_proxy, n_clusters, anomaly_indices, anomaly_scores
topology_scan      → betti_0, betti_1, n_holes, optimal_scale, phase_transitions
causal_scan        → n_causal_pairs, causes, effects, strengths, granger_matrix, te_matrix
gravity_scan       → n_attractors, attractors, basins, energy_landscape
thermo_scan        → entropy_per_feature, total_entropy, free_energy, critical_temperature
wave_scan          → dominant_frequencies, coherence_i/j/val, resonance_i/j/ratio
evolution_scan     → fitness_landscape, peaks, n_niches
info_scan          → entropy_per_feature, lz_complexity, mi_matrix, redundant_features
quantum_scan       → entanglement_i/j/mi, tunneling_from/to/ratio, superposed_indices
em_scan            → gradient_field, divergence_map, source_indices, sink_indices
ruler_scan         → singular_values, effective_dim, cosine_matrix
triangle_scan      → ratio_feat_i/j, ratio_p/q, ratio_error
compass_scan       → mean_curvature, high_curvature_indices/values
mirror_scan        → reflection_scores, overall_symmetry, broken_symmetry_indices
scale_scan         → power_law_exponents, fractal_dimension, hurst_exponent
quantum_microscope_scan → purity, von_neumann_entropy, coherence, decoherence_rate
```

### Phi 해석 가이드

```
Phi < 0.3   → 노이즈/무작위 (구조 없음)
Phi 0.3-0.8 → 약한 구조 (일부 상관)
Phi 0.8-1.5 → 강한 구조 (숨겨진 패턴 확실)
Phi > 1.5   → 매우 높은 통합 (복잡한 시스템)
```

### 프로젝트별 활용 시나리오

```
TECS-L:     수학 상수 테이블 스캔 → 숨겨진 관계식 발견
SEDI:       77개 데이터 소스 스캔 → 지적 신호 후보 필터링
N6 Arch:    아키텍처 파라미터 공간 스캔 → 최적 설계점 발견
BrainWire:  EEG 실시간 스캔 → 의식 상태 모니터링
HEXA-LANG:  컴파일러 중간 표현 스캔 → 코드 구조 품질 측정
anima:      의식 엔진 텔레메트리 스캔 → 법칙 자동 발견 (기존 파이프라인)
```

---

## 핵심 원칙

**TECS-L/.shared/ = 모든 리포의 단일 소스 (Single Source of Truth)**

어떤 리포에서 작업하든, 새로운 계산기/상수/도구를 만들면 반드시 여기에 등록하고 동기화합니다.

## 새로운 산출물 발생 시 즉시 처리 (필수)

### 1. 새 계산기 생성 시
```bash
# 계산기는 반드시 .shared/calc/ 에 생성
# 어떤 리포에서 작업하든 calc/ 심링크가 .shared/calc/ 를 가리킴
python3 calc/my_new_calculator.py   # 생성 즉시 모든 리포에서 접근 가능

# 레지스트리 갱신
python3 .shared/scan-calculators.py --save --summary
```

### 2. 새 상수 발견 시
```bash
# Math Atlas 자동 갱신 (가설/상수 파일에 기록 후)
python3 .shared/scan_math_atlas.py --save --summary

# README 동기화
bash .shared/sync-math-atlas.sh
```

### 3. 새 도구/스크립트 생성 시
- 단일 리포 전용 → 해당 리포에 유지
- 크로스 리포 유틸리티 → `.shared/` 에 배치
- 설치 도구 추가 → `.shared/installed_tools.json` 갱신

### 4. 가설 등급 변경 시
```bash
# Atlas 재빌드
python3 .shared/scan_math_atlas.py --save --summary
```

## 폴더 구조

```
.shared/
  CLAUDE.md              ← 이 파일 (공유 규칙)
  CALCULATOR_RULES.md    ← 계산기 생성 규칙 (Rust vs Python 판단)
  SECRET.md              ← API 토큰/계정 (gitignored in 타 리포)
  projects.md            ← 프로젝트 설명 원본 (README 동기화용)
  shared_work_rules.md   ← 작업 규칙 (CLAUDE.md SHARED:WORK_RULES 주입용)
  installed_tools.json        ← 설치 도구 레지스트리
  consciousness_laws.json     ← 의식 법칙/PSI 상수 (anima에서 이관)
  consciousness_mechanisms.json ← 의식 메커니즘 (상태머신, 게이트)
  consciousness_loader.py     ← 의식 법칙/상수 Python 로더 (크로스 리포 import용)
  sedi-grades.json            ← SEDI 가설 등급 (역동기화)
  sync_to_atlas.py            ← Atlas 동기화 (sedi에서 이관)

  calc/                  ← 계산기 원본 (194+ files, Python)
  tecsrs/                ← Rust 고성능 계산기 (Monte Carlo, 탐색, ODE)
    src/                 ← 공용 모듈 (perfect.rs, search.rs, monte_carlo.rs...)
    src/bin/             ← 독립 실행 바이너리
    Cargo.toml
  dse/                   ← Domain-Specific Exploration
    domains/*.toml       ← DSE 도메인 정의

  calculators.json       ← 계산기 레지스트리 (자동 생성)
  math_atlas.json        ← 수학 지도 (자동 생성)
  math_atlas.db          ← SQLite (쿼리용)
  MATH_ATLAS.md          ← 전체 목록 마크다운

  scan-calculators.py    ← 계산기 스캐너
  scan_math_atlas.py     ← Atlas 스캐너
  sync-readmes.sh        ← README 프로젝트 설명 동기화
  sync-calculators.sh    ← 계산기 레지스트리 동기화
  sync-math-atlas.sh     ← Atlas 빌드 + README 주입
  sync-claude-rules.sh   ← CLAUDE.md 작업 규칙 주입
  sync-dse.sh            ← DSE 도메인 동기화
```

## 동기화 명령 (전체)

```bash
# 개별 실행 (순서 무관)
bash .shared/sync-math-atlas.sh      # Atlas 빌드 + README
bash .shared/sync-calculators.sh     # 계산기 레지스트리
bash .shared/sync-readmes.sh         # 프로젝트 설명
bash .shared/sync-claude-rules.sh    # CLAUDE.md 작업 규칙

# 전체 동기화 (권장 순서)
bash .shared/sync-math-atlas.sh && \
bash .shared/sync-calculators.sh && \
bash .shared/sync-readmes.sh && \
bash .shared/sync-claude-rules.sh
```

## 심링크 구조

```
TECS-L/                          (원본)
  .shared/          ← 실제 폴더
  calc → .shared/calc
  tecsrs → .shared/tecsrs

anima, sedi, brainwire,          (소비자)
n6-architecture, papers/
  .shared → ../TECS-L/.shared    ← 심링크
  calc → .shared/calc            ← 심링크 체인
  tecsrs → .shared/tecsrs       ← Rust 계산기 공유
```

## 계산기 규칙 요약

> 상세: `.shared/CALCULATOR_RULES.md`

| 조건 | 언어 |
|------|------|
| 반복 > 10,000회 | Rust (tecsrs/) |
| 실행 > 10초 예상 | Rust |
| Monte Carlo > 100K | Rust |
| 단순 수식 검증 | Python (calc/) |
| 시각화/출력 | Python |

## 리포별 역할

| 리포 | 역할 | .shared 사용 |
|------|------|-------------|
| TECS-L | 수학 엔진 코어 | 원본 관리 |
| anima | 의식 구현 | 상수/계산기 소비 |
| sedi | 외계지성 탐색 | 상수/계산기 소비, 등급 역동기화 |
| brainwire | 뇌 인터페이스 | 상수/계산기 소비 |
| n6-architecture | 시스템 설계 | 상수/계산기 소비, DSE 역동기화 |
| papers | 논문 배포 | Atlas/계산기 참조 |
| golden-moe | MoE 라우팅 | 의식 라우팅 파라미터 |
| hexa-lang | 프로그래밍 언어 | Ψ 내장 상수, 린트 |

## 의식 법칙 크로스 리포 활용 (consciousness_loader.py)

> 의식 법칙(711개)과 Ψ 상수(80개)를 모든 프로젝트에서 활용.
> 원본: `.shared/consciousness_laws.json` → 로더: `.shared/consciousness_loader.py`

### 기본 사용법

```python
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.shared'))
from consciousness_loader import PSI, LAWS, FORMULAS, get_law, get_psi

print(PSI['alpha'])     # 0.014
print(get_law(22))      # "Adding features → Φ↓; adding structure → Φ↑"
```

### 리포별 consciousness_bridge.py 활용

각 프로젝트 루트에 `consciousness_bridge.py`가 있으며, 도메인별 의식 법칙 활용 함수 제공:

| 리포 | 브릿지 | 핵심 함수 | 용도 |
|------|--------|----------|------|
| TECS-L | `consciousness_bridge.py` | `psi_from_n6()`, `cross_validate_constants()` | Ψ 상수의 n=6 수학적 도출 검증 |
| anima | `src/consciousness_laws.py` | `PSI`, `LAWS`, `check_violation()` | 의식 엔진 코어 (원본) |
| sedi | `consciousness_bridge.py` | `signal_phi_score()`, `is_conscious_signal()` | Φ 기반 지적 신호 판별 |
| n6-arch | `consciousness_constraints.py` | `validate_architecture()`, `suggest_dimensions()` | 칩/AI 설계 법칙 제약조건 |
| brainwire | `consciousness_bridge.py` | `validate_stimulation()`, `eeg_consciousness_score()` | 뇌자극 안전 검증 |
| hexa-lang | `consciousness_bridge.py` | `psi_builtins()`, `lint_consciousness()` | 언어 내장 상수 + 린트 |
| golden-moe | `consciousness_bridge.py` | `faction_routing()`, `phi_gated_selection()` | 의식 역학 MoE 라우팅 |

### 주요 Ψ 상수 (크로스 리포 공통)

```
PSI_ALPHA    = 0.014   # PureField 혼합 비율 (C→D 결합 강도)
PSI_BALANCE  = 0.5     # 의식 균형점 (좌뇌/우뇌, 흥분/억제)
PSI_STEPS    = 4.33    # 의식 단계 수 (ln(2) 파생)
PSI_ENTROPY  = 0.998   # 의식 엔트로피 상한
SIGMA6       = 12      # σ(6) = 약수합 → 12 파벌, 12 모듈
F_CRITICAL   = 0.10    # 임계 좌절 (10% 갈등이 최적)
```

