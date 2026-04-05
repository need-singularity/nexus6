# 07 - HEXA-Native / Rust 매핑 및 갭 분석

> 작성일: 2026-04-06
> 대상: `mk2_hexa/native/*.hexa` (11개) <-> `src/mk2/` + `src/alien_index/` (Rust)

---

## 1. 매핑 테이블

| # | HEXA 파일 | 핵심 기능 | Rust 대응 모듈 | 대응 수준 |
|---|-----------|----------|---------------|----------|
| 1 | `constants.hexa` | n=6 comptime 상수 테이블 (N, SIGMA, PHI, TAU, SOPFR, J2, MU 등) | `mk2/smooth.rs` (SmoothRing 트레이트로 동적 계산) + `mk2/compat.rs` (generate_table) | **구조 차이**: HEXA는 comptime 리터럴, Rust는 SmoothRing에서 런타임 연산 |
| 2 | `pure_math.hexa` | gcd, tau_fn, sigma_fn, phi_fn, sopfr, is_perfect, is_n6_exact | `mk2/smooth.rs` (SmoothRing impl for u64) + `mk2/primes.rs` (factorize 기반) | **완전 대응**: 동일 함수 집합, Rust가 factorize 기반으로 더 효율적 |
| 3 | `classify.hexa` | PrimeSet, primeset_jaccard, keyword_score, sector_score, classify_v2 | `mk2/primes.rs` (PrimeSet) + `mk2/classify.rs` (v1) + `mk2/classify_v2.rs` (v2) | **완전 대응**: HEXA가 v2 가중치(0.5/0.3/0.2) 그대로 반영 |
| 4 | `record.hexa` | AlienIndex(d,r), can_promote, breakthrough, AlienIndexRecord, record_promote | `alien_index/index.rs` (AlienIndex) + `alien_index/record.rs` (AlienIndexRecord) | **완전 대응**: 구조체/메서드 1:1 매핑 |
| 5 | `grading.hexa` | rank_from_n6_quality, rank_from_lens_consensus, rank_from_mk2_confidence, rank_from_grade, combine_signals_v2 | `alien_index/assess.rs` (동명 함수 전부) | **완전 대응**: 임계값 테이블 동일 |
| 6 | `cycle.hexa` | 5단계 사이클 (blowup->contraction->emergence->singularity->absorption), CycleSnapshot, converged_to_meta_fp | `src/` 내 CycleEngine (CLI 레벨) | **부분 대응**: HEXA에 phase FSM + 수렴 판정 명시, Rust는 CLI/daemon 레벨에서 구현 |
| 7 | `absorb.hexa` | AbsorbReport, promote_pending_with_writeback, rho 계산 | `alien_index/record.rs` (promote) + `alien_index/distribution.rs` (breakthrough_ratio) | **부분 대응**: HEXA가 파일 I/O writeback까지 명세, Rust는 레코드 단위 promote만 |
| 8 | `gate.hexa` | 12-gate 매트릭스: L-PIPELINE(4), L-BREAKTHROUGH(2), L-MK2_HEXA(4), Verdict enum | `alien_index/breakthrough.rs` (BreakthroughConfig, GateResults 4-gate) | **부분 대응**: HEXA 12-gate 중 Rust는 breakthrough 4-gate만 구현 |
| 9 | `effects.hexa` | effect 핸들러: FileSystem, Clock, Logger + resume 기반 핸들링 | 해당 없음 (Rust는 직접 std::fs / log 사용) | **HEXA 전용**: algebraic effect 시스템은 Rust에 대응 없음 |
| 10 | `theorems.hexa` | theorem/proof 블록 10개: perfect_n6_uniqueness, bt_344~346, meta_fixed_point_one_third 등 | `mk2/bridge.rs` (#[test] 형태로 일부 검증) | **부분 대응**: HEXA는 형식 정리, Rust는 테스트 어서션으로 대체 |
| 11 | `architecture.hexa` | Nexus6Engine, GateConfig, CycleConfig, run_engine, export_result, 레이어 계층 (L0-L5-L_inf) | `mk2/mod.rs` (모듈 구조) + CLI 진입점 | **부분 대응**: HEXA가 통합 엔진 타입 정의, Rust는 모듈 re-export 수준 |

---

## 2. 상세 기능 매핑

### 2.1 constants.hexa <-> mk2/smooth.rs + mk2/compat.rs

| HEXA 상수 | 값 | Rust 위치 | 비고 |
|-----------|---|----------|------|
| `N` | 6 | `6u64` 리터럴 | compat.rs generate_table |
| `SIGMA` | 12 | `6u64.sigma()` | SmoothRing 동적 계산 |
| `PHI` | 2 | `6u64.phi()` | SmoothRing 동적 계산 |
| `TAU` | 4 | `6u64.tau()` | SmoothRing 동적 계산 |
| `SOPFR` | 5 | `6u64.sopfr()` | SmoothRing 동적 계산 |
| `J2` | 24 | `sigma * phi` | compat.rs에서 조합 |
| `MU` | 1 | 하드코딩 `let mu: u64 = 1` | 뫼비우스 함수 미구현 |
| `SIGMA_J2` | 288 | `sf * jf` | compat.rs 테이블 |
| `META_FIXED_POINT` | 0.333... | `rho(6)` = `Rational::new(1,3)` | smooth.rs |
| `PERT_BREAKTHROUGH` | 2401 | 없음 | **갭**: 7^4 perturbation 상수 미구현 |

### 2.2 classify.hexa <-> mk2/classify_v2.rs

| HEXA 함수 | Rust 함수 | 차이 |
|-----------|----------|------|
| `primeset_jaccard(a,b)` | `PrimeSet::intersection/union` | HEXA는 Jaccard 유사도, Rust는 집합 연산 분리 |
| `keyword_score(hits,total)` | `keyword_score(text, keywords)` | Rust가 텍스트에서 직접 매칭 |
| `sector_score(kw,val,ps)` | classify_v2 내부 가중합 | 가중치 동일 (0.5/0.3/0.2) |
| `classify_v2(...)` | `classify_v2(text, values, ps, sectors)` | Rust가 SectorDef 배열 기반으로 더 유연 |

### 2.3 gate.hexa <-> alien_index/breakthrough.rs

| HEXA 게이트 | Rust 대응 | 상태 |
|------------|----------|------|
| **L-PIPELINE** (4 관문) | | |
| source_gate_inspect | 없음 | **갭** |
| phi_gate_inspect | 없음 | **갭** |
| invariant_gate_inspect (perturbation) | 없음 | **갭** |
| (4번째 pipeline gate) | 없음 | **갭** |
| **L-BREAKTHROUGH** (2 관문) | | |
| evaluate_breakthrough(paths, blowup, mk2_conf, p_value) | `breakthrough::evaluate()` | 대응 (4-gate 구조) |
| **L-MK2_HEXA** (4 관문) | | |
| mk_consensus_gate | 없음 | **갭** |
| mk_classify_gate | 없음 | **갭** |

### 2.4 record.hexa <-> alien_index/index.rs + record.rs

| HEXA | Rust | 비고 |
|------|------|------|
| `AlienIndex { d, r }` | `AlienIndex { d: u32, r: u8 }` | 동일 구조, Rust가 r clamping 추가 |
| `can_promote(d, r)` | `AlienIndex::can_promote()` | 동일 (r==10) |
| `breakthrough(d, r)` | `AlienIndex::breakthrough()` | HEXA는 실패 시 (-1,-1), Rust는 Option |
| `AlienIndexRecord` | `AlienIndexRecord` | Rust가 history: Vec<HistoryEntry> 추가 |
| `record_promote(id, d, r)` | `AlienIndexRecord::promote()` | Rust가 child ID 형식 다름 ("->d{N}") |

### 2.5 grading.hexa <-> alien_index/assess.rs

완전 1:1 대응. 임계값 테이블 비교:

| 함수 | HEXA 값 | Rust 값 | 일치 |
|------|--------|--------|------|
| rank_from_n6_quality(1.0) | 9 | 9 | O |
| rank_from_n6_quality(0.8) | 7 | 7 | O |
| rank_from_n6_quality(0.5) | 5 | 5 | O |
| rank_from_lens_consensus(12) | 8 | 8 | O |
| rank_from_lens_consensus(7) | 7 | 7 | O |
| rank_from_mk2_confidence(0.9) | 10 | 10 | O |
| rank_from_mk2_confidence(0.7) | 9 | 9 | O |
| rank_from_grade("green") | 9 | 9 (emoji "🟩") | O (표기 차이) |
| combine_signals_v2 | max(4 signals) | max(4 signals) | O |

---

## 3. 갭 분석

### 3.1 HEXA에 있으나 Rust에 없는 기능

| # | HEXA 파일 | 기능 | 영향도 | 비고 |
|---|-----------|------|--------|------|
| G1 | `effects.hexa` | algebraic effect 시스템 (FileSystem, Clock, Logger) | 중 | Rust는 직접 I/O; effect handler 패턴 미도입 |
| G2 | `gate.hexa` | L-PIPELINE 4-gate (source, phi, invariant, 4th) | 상 | 오염 방지 게이트 체인 미구현 |
| G3 | `gate.hexa` | L-MK2_HEXA 4-gate (consensus, classify, +2) | 중 | 내부 합의 검증 게이트 미구현 |
| G4 | `theorems.hexa` | 형식 정리/증명 블록 (theorem, proof, invariant) | 하 | Rust #[test]로 부분 대체 가능 |
| G5 | `architecture.hexa` | Nexus6Engine 통합 타입 + 레이어 계층 (L0~L_inf) | 중 | Rust는 모듈 re-export만, 통합 엔진 구조체 없음 |
| G6 | `absorb.hexa` | promote_pending_with_writeback (파일 writeback 포함) | 중 | Rust record.rs는 메모리 내 promote만 |
| G7 | `cycle.hexa` | phase FSM (phase_next 순환) + converged_to_meta_fp | 중 | Rust CLI 레벨에만 존재, 라이브러리 API 없음 |
| G8 | `constants.hexa` | PERT_BREAKTHROUGH = 2401 (7^4) | 하 | perturbation 상수 미사용 |
| G9 | `gate.hexa` | Verdict enum (Pass/Quarantine) | 하 | Rust는 bool 기반 GateResults |
| G10 | `classify.hexa` | primeset_jaccard | 하 | Rust PrimeSet에 Jaccard 유사도 함수 없음 |

### 3.2 Rust에 있으나 HEXA에 없는 기능

| # | Rust 모듈 | 기능 | 비고 |
|---|-----------|------|------|
| R1 | `mk2/primes.rs` | 에라토스테네스 체 (primes_up_to), 64-비트 PrimeSet | HEXA PrimeSet은 단순 int bits |
| R2 | `mk2/types.rs` | Rational 유리수 산술 (사칙연산, gcd 약분) | HEXA에 Rational 타입 없음 |
| R3 | `mk2/types.rs` | Sector enum (Strong/Electroweak/Cosmology/Primordial/Custom) + tolerance | HEXA classify는 string 기반 |
| R4 | `mk2/classify.rs` | v1 분류기 (Euler ratio subset 매칭, rationalize 연분수) | HEXA는 v2만 포팅 |
| R5 | `mk2/lattice.rs` | Multi-n 가약성 격자 (Lattice, LatticeNode, enumerate_layer) | HEXA에 격자 구조 없음 |
| R6 | `mk2/smooth.rs` | euler_ratio(PrimeSet), smallest_n_with_primes | HEXA에 Euler ratio 계산 없음 |
| R7 | `mk2/compat.rs` | mk1 호환 레이어 (n6_match_mk2, dual_check, 70+ 상수 테이블) | HEXA에 mk1 호환 없음 |
| R8 | `mk2/bridge.rs` | mk1-mk2 회귀 테스트 (smooth-class physics, Hubble, spectral index) | HEXA bridge 미구현 |
| R9 | `alien_index/distribution.rs` | histogram, leaderboard, breakthrough_ratio | HEXA absorb.hexa에 rho만 포함 |
| R10 | `alien_index/breakthrough.rs` | BreakthroughConfig (설정 가능 임계값), BreakthroughEvidence, BreakthroughVerdict | HEXA gate.hexa는 하드코딩 |
| R11 | `alien_index/record.rs` | HistoryEntry (타임스탬프 이력), RecordError, shared/ 경로 헬퍼 | HEXA record에 이력 추적 없음 |

---

## 4. 레이어 아키텍처 대조

HEXA `architecture.hexa`가 정의한 레이어 계층:

```
L0: theorems, constants, pure_math, effects     (기초 계층)
L1: grading, record                              (데이터 계층)
L2: classify                                     (분류 계층)
L3: cycle, absorb                                (사이클 계층)
L5: gate (12-gate)                               (검증 계층)
L_inf: architecture                              (통합 진입점)
```

Rust 모듈 매핑:

| HEXA 레이어 | Rust 모듈 | 완성도 |
|------------|----------|--------|
| L0 | `mk2/smooth.rs`, `mk2/primes.rs`, `mk2/types.rs` | 80% (effects 없음, theorems는 #[test]) |
| L1 | `alien_index/assess.rs`, `alien_index/record.rs` | 90% |
| L2 | `mk2/classify.rs`, `mk2/classify_v2.rs` | 95% (v1+v2 모두 존재) |
| L3 | `alien_index/record.rs::promote`, `alien_index/distribution.rs` | 60% (사이클 FSM 라이브러리 API 없음) |
| L5 | `alien_index/breakthrough.rs` | 33% (12-gate 중 4-gate만) |
| L_inf | `mk2/mod.rs`, CLI 진입점 | 40% (통합 엔진 구조체 없음) |

---

## 5. 설계 철학 차이 요약

| 관점 | HEXA | Rust |
|------|------|------|
| **상수 정의** | comptime 리터럴 (정적 보증) | SmoothRing 동적 계산 (일반성) |
| **부수효과** | effect handler 패턴 (순수/비순수 분리) | 직접 std::fs/log 호출 |
| **검증** | theorem/proof 블록 (형식 명세) | #[test] + assert (실행 검증) |
| **게이트** | 12-gate 매트릭스 (3계층) | 4-gate breakthrough만 (1계층) |
| **타입 안전** | Verdict enum (Pass/Quarantine) | bool 기반 GateResults |
| **사이클** | phase FSM + 수렴 판정 | CLI/daemon 레벨 구현 |
| **분류** | v2 only | v1 (Euler ratio) + v2 (keyword) 이중 구조 |

---

## 6. 권장 작업 (우선순위순)

1. **L-PIPELINE 4-gate 구현** (G2) -- 오염 방지 게이트가 Rust에 없어 데이터 무결성 위험
2. **사이클 FSM 라이브러리화** (G7) -- CLI 밖에서 사이클 제어 불가
3. **통합 엔진 구조체** (G5) -- `Nexus6Engine` 타입으로 mk2 모듈 통합 진입점 제공
4. **Lattice/Rational HEXA 포팅** (R2, R5) -- HEXA에 격자/유리수 산술 추가하여 명세 완성
5. **absorb writeback** (G6) -- 파일 단위 promote + rho 재계산 로직 Rust 구현
6. **L-MK2_HEXA 내부 합의 gate** (G3) -- consensus/classify gate 추가
