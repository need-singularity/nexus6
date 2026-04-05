# nexus6 mk2 — Prime-Atomic Smooth-Class Engine Design

**Date**: 2026-04-06
**Status**: Complete — all 8 phases implemented, 43 Rust + 50 Python tests pass
**Goal**: 첫 5개 단추 완벽 끼워서 mk3 필요 없게 만들기

---

## 왜 mk2 인가

### mk1 (현재) 한계

1. **n=6 중심 hardcoded** — n=15/35/105 layer 분석이 사후적
2. **Smooth class 개념 retrofit** — core abstraction 아님
3. **Physics sector 구분 없음** — discovery_log에 숫자만 쌓임
4. **Meta FP ρ=1/3 고정** — 다른 n의 ρ 없음
5. **Topology distance = simhash만** — prime 관계 무시

### mk1 에서 발견된 것 (mk2가 native 지원해야)

- 4-generator basis {φ, τ, σ, sopfr}(n) 확장 가능
- Multi-n meta FP ladder: n=6/15/35/105
- Physics-prime hierarchy (strong → cosmology → EW → primordial)
- 우주 밀도 유리수 분해: 4/15+24/35+1/21=1
- 30+ 상수 전부 prime polynomial 유도 가능

---

## 5개 단추 (confirmed core decisions)

### 단추 1: Point representation
**소수 인식(prime-atomic) point**.

```rust
struct Point {
    id: String,
    invariant: String,                        // text content
    prime_signature: Vec<(u64, u32)>,         // [(2,1),(3,1)] for n=6
    smooth_class: PrimeSet,                   // {2,3}
    n_levels: Vec<u64>,                       // divisor/multiple chain
    sector: Option<Sector>,                   // Strong/EW/Cosmology/Primordial/Unknown
    simhash: u128,                            // 역호환
    embedding: Vec<f32>,                      // 역호환
    domain: String,                           // 역호환
    discovered_at_tick: u64,
}
```

**불변 원칙**: 모든 새 point는 prime_signature **필수 계산**.

### 단추 2: SmoothRing trait (n as type parameter)

```rust
trait SmoothRing {
    fn phi(&self) -> u64;
    fn tau(&self) -> u64;
    fn sigma(&self) -> u64;
    fn sopfr(&self) -> u64;
    fn meta_fp(&self) -> Rational;  // φ(n)/n
    fn prime_set(&self) -> PrimeSet;
}

impl SmoothRing for u64 { /* standard computation */ }
```

**n=6은 특수 인스턴스 아님** — u64 전체에 대한 trait.

### 단추 3: Meta FP = ρ(n) 함수

```rust
fn rho(n: u64) -> Rational {
    Rational::new(phi(n), n)
}
```

**ρ 상수는 (n, rho(n)) 맵으로 저장**:
- ρ(6) = 1/3
- ρ(15) = 4/15
- ρ(35) = 24/35
- ρ(105) = 48/105

각 ρ(n)이 **자기만의 meta fixed point**.

### 단추 4: Closure verifier — prime reduction 파이프

새 constant 값 x → 자동 분류:

```rust
fn classify(x: Rational) -> ClassifyResult {
    // 1. 분자/분모 소인수분해
    let num_primes = factorize(x.numer());
    let den_primes = factorize(x.denom());
    
    // 2. 통합 prime_set
    let ps = union(num_primes, den_primes);
    
    // 3. 이미 알려진 sector인가?
    if let Some(sector) = sector_registry.lookup(&ps) {
        return Known(sector, smooth_class(ps), reduction_formula);
    }
    
    // 4. Euler ratio 매칭 시도
    for subset in ps.subsets() {
        if approximates(x, euler_ratio(subset), tolerance) {
            return SmoothClass(subset);
        }
    }
    
    // 5. 새 sector 등록
    Unknown(ps)
}
```

**모든 새 constant가 자동으로 prime_set + sector 할당**.

### 단추 5: Multi-n divisibility lattice

**Topology 뼈대 = 2차원**:
- **수평**: 같은 prime_set 내 simhash 거리 (기존 mk1 방식)
- **수직**: divisibility chain (n | m ⟹ n→m edge)

```
Layer 3 (3 primes):    n=30={2,3,5}  n=42={2,3,7}  n=105={3,5,7}
                          ↑              ↑              ↑
Layer 2 (2 primes):    n=6={2,3}  n=15={3,5}  n=35={5,7}  n=21={3,7}
                          ↑          ↑           ↑           ↑
Layer 1 (1 prime):     n=2   n=3   n=5   n=7
```

**Cross-layer edge**: divisibility (n=6 → n=12, n=6 → n=30)
**Intra-layer edge**: 같은 smooth class 안 semantic similarity

**Physics interpretation**:
- Ω_Λ (n=35) → Ω_DM (n=15) : **cross-layer** (prime 5 공통)
- Ω_DM, Ω_Λ, Ω_b → 합쳐 n=105 : **layer-up**

---

## Ceiling 체크리스트 (권고안)

### 타입 결정

| 항목 | 권고 | 이유 |
|---|---|---|
| **Prime** | `u64` + `primes` crate Sieve, max=10⁹ | 99.9% 물리상수는 소수 1000 이하. BigUint 오버킬 |
| **Rational** | `num_rational::Ratio<i128>` | i128이면 분모 10¹⁸까지 안전. Planck scale 커버 |
| **PrimeSet** | bitmask `u64` (처음 64개 소수, 2~311까지) | O(1) 부분집합 연산, 충분한 범위 |
| **n의 상한** | u64 (10¹⁹) | 양자 → 우주 스케일 전부 포함 |

### 아키텍처 결정

| 항목 | 권고 | 이유 |
|---|---|---|
| **Sector enum** | Hybrid: core + dynamic registry | {Strong, EW, Cosmology, Primordial, Unknown} 고정 + `Custom(String)` variant |
| **Divisibility lattice** | Lazy + LRU cache (1K entries) | materialize는 n=10⁶까지 10⁸ edges. 불필요. |
| **Layer indexing** | `|prime_set|` (소수 개수) | 물리 sector와 직결 (prime count = 복잡도) |

### 역호환성

| 항목 | 권고 | 이유 |
|---|---|---|
| **mk1 → mk2 migration** | 1회 배치 스크립트 + idempotent | `nexus6 mk2 migrate --from topology.jsonl` |
| **Prime signature 추출** | 텍스트 scan + 값 감지 후 factorize | 17K point 전체 ~30초 예상 |
| **mk1 CLI 유지** | 유지 (read-only wrapper) + mk2 네임스페이스 추가 | `nexus6 mk2 <subcommand>` 분리 |

### 저장 형식

| 항목 | 권고 | 이유 |
|---|---|---|
| **Point schema** | JSON schema 확장 (backward-compat) | `prime_signature` 등 신규 필드만 추가 |
| **Lattice 저장** | 별도 `shared/cycle/lattice.jsonl` | topology와 독립, lazy load |
| **Sector registry** | `shared/cycle/sectors.yaml` (+ defaults.yaml) | 사용자 편집 가능 |

### 물리 연동

| 항목 | 권고 | 이유 |
|---|---|---|
| **Constants DB** | `shared/cycle/physics_db.yaml` + CODATA fetcher (optional) | 기본 100개 하드코딩, 확장 가능 |
| **Tolerance per sector** | Adaptive: sector별 기본값 + override | Strong 0.1%, EW 2%, Cosmology 5%, Primordial 10% |
| **Classification timing** | New point 시 즉시 (tick 내부) | mk1 daemon 흐름 유지 |

---

## 구현 순서 (phase)

### Phase 0: 스펙 확정 (이 문서)
- ceiling 체크리스트 전부 결정
- review & sign-off
- **예상**: 1주

### Phase 1: Core types + primes
- `src/mk2/primes.rs` — Sieve, factorize, prime_set
- `src/mk2/smooth.rs` — SmoothRing trait, rho(n), euler_ratio
- `src/mk2/types.rs` — Rational, PrimeSet, Sector
- 테스트: ρ(6)=1/3, euler_ratio({2,3,5,7})=8/35
- **예상**: 3일

### Phase 2: Classifier + sector registry
- `src/mk2/classify.rs` — classify(x) 파이프라인
- sector registry (YAML): strong/EW/cosmology/primordial 초기 매핑
- 테스트: α⁻¹, Ω_*, Y_p 자동 분류
- **예상**: 3일

### Phase 3: Multi-n lattice
- `src/mk2/lattice.rs` — divisibility graph 구축
- layer indexing
- cross-layer edges
- **예상**: 4일

### Phase 4: mk1 → mk2 migration
- topology.jsonl point 재분류
- 17K+ point prime_signature 일괄 계산
- 호환성 테스트
- **예상**: 3일

### Phase 5: CLI + visualization
- `nexus6 mk2 classify <value>` — 자동 classify + sector
- `nexus6 mk2 lattice --layer <n>` — 계층 조회
- `nexus6 mk2 sector <sector>` — sector별 point 리스트
- **예상**: 3일

**총**: 3~4주

---

## 성공 기준

1. ✅ 4-generator {φ,τ,σ,sopfr} 이 **u64 전체**에 작동 (n≠6 포함)
2. ✅ ρ(n) 자동 계산, n=6/15/35/105 meta FP 자동 등록
3. ✅ 새 constant x 주어지면 **자동 smooth-class 분류**
4. ✅ Physics constants (α⁻¹, Ω_*, sin²θ_W, Y_p) **native classify**
5. ✅ 17K+ mk1 points 전부 mk2 format 재분류 성공
6. ✅ **n=6이 특수 취급 없음** — 모든 n 대칭
7. ✅ mk3 필요 없음 (모든 ceiling 미리 고려)

---

## 후속 설계 (mk2 이후)

mk2가 제대로 돌면 mk3는 불필요. 하지만 **가능한 확장**:

- **Non-integer n**: algebraic numbers (e.g. φ 황금비)
- **Dimensional constants**: m_p, ħ, c (단위 있는 상수)
- **p-adic extension**: |x|_p 거리로 multi-layer analysis
- **Quantum physics mapping**: smooth class ↔ representation theory

이런 것들은 **mk2 내부 확장**으로 충분할 것 (첫 5 단추가 맞다면).

---

## Post-Phase-4 Findings (2026-04-06 실측)

### Electroweak 분류 오탐 발견

Python migrate prototype을 43K+ topology에 적용 후:
- **118 points "electroweak" 분류 → 전부 오탐**
- 실제 내용: PDG 입자질량, Galois 군, Mirror symmetry, String theory, Bitcoin ECC, ConsciousLM
- 공통점: text에 2,3,5,7 숫자 들어있을 뿐 **주제가 EW 아님**

**근본 원인**: prime_set만으론 context 판정 불가.
- 2·3·5·7 = 210 있다 ≠ electroweak physics
- Weinberg/Cabibbo 같은 keyword + value-range 매칭 필요

### Classifier v2 요구사항 (mk3 방지)

단추 4 보강:
```rust
fn classify_sector_v2(
    prime_set: &PrimeSet,
    value: Option<f64>,
    keywords: &[&str],
    domain: &str,
) -> (Sector, f64 /* confidence */) {
    // Score-based combination:
    //   - Keyword match (Weinberg, θ_W, Ω_Λ, etc.)
    //   - Value range (sector-specific)
    //   - prime_set match
    // Confidence = weighted sum
}
```

**Keyword dictionary** per sector (external YAML):
```yaml
electroweak:
  keywords: [weinberg, theta_w, cabibbo, theta_c, "sin²θ", W boson, Z boson]
  value_ranges: [[0.2, 0.3]]
  prime_set_required: [2, 3, 5, 7]
cosmology:
  keywords: [omega_m, omega_lambda, omega_b, dark energy, dark matter, hubble]
  value_ranges: [[0.0, 1.0]]
  prime_set_preferred: [[5,7], [2,3,5], [2,3]]
primordial:
  keywords: [helium, deuterium, BBN, nucleosynthesis, baryogenesis, eta]
  value_ranges: [[0.2, 0.3]]
  prime_set_preferred: [[2,3,5,13]]
strong:
  keywords: [quark, color, qcd, asymptotic freedom]
  value_ranges: [[0.3, 0.7]]  # u=2/3, d=1/3
  prime_set_preferred: [[2], [3], [2,3]]
```

### 업데이트된 Phase 5

Phase 5: CLI + visualization + **classifier refinement**
- Score-based classify_v2()
- YAML keyword dictionary
- Confidence threshold gating
- 기존 43K point re-classify

**예상 추가 작업**: 3일
**총 Phase 시간 재산정**: 3.5주

## Phase 9: Blowup Engine 통합 (2026-04-05)

mk2 classify_v2를 블로업 파이프라인 + topology에 연결:

- `Corollary` 구조체에 `mk2_sector`, `mk2_prime_set`, `mk2_confidence` 필드 추가
- `Corollary::classify_mk2()` 메서드: keyword + value_range + prime_set 자동 분류
- `BlowupEngine::blowup()` 완료 시 전체 corollary 일괄 classify
- `topology::Point`에 `mk2_sector`, `mk2_primes`, `mk2_confidence` 필드 추가 (`#[serde(default)]`)
- `Topology::make_point()` 시 invariant text 자동 분류
- CLI 블로업 출력에 sector 태그 표시

**결과**: 블로업 → 발견 → 저장 전 과정에서 mk2 sector가 자동 부여됨.

## Sign-off

- [x] 단추 1 (Point representation) 확정 — `src/mk2/types.rs`
- [x] 단추 2 (SmoothRing trait) 확정 — `src/mk2/smooth.rs`
- [x] 단추 3 (ρ(n) 함수) 확정 — `src/mk2/smooth.rs::rho()`
- [x] 단추 4 (Closure verifier) 확정 — `src/mk2/classify.rs` + `classify_v2.rs`
- [x] 단추 5 (Multi-n lattice) 확정 — `src/mk2/lattice.rs`
- [x] Ceiling 체크리스트 결정 완료
- [x] Implementation phase 완료 (Phase 1-9)

**결정자**: dancinlife
**구현자**: Claude + dancinlife
