# nexus6 mk2 — Prime-Atomic Smooth-Class Engine Design

**Date**: 2026-04-06
**Status**: Draft spec (ceiling decisions pending)
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

## Ceiling 체크리스트 (결정 필요)

### 타입 결정
- [ ] **Prime**: `u64` primes.rs Sieve (max 10^9?) or `BigUint`?
- [ ] **Rational**: `num_rational::Ratio<u128>` vs custom `(u64, u64)`?
- [ ] **PrimeSet**: `BTreeSet<u64>` vs bitmask (처음 16개 소수만)?
- [ ] **n의 상한**: u64? u128? 무제한?

### 아키텍처 결정
- [ ] **Sector enum**: 고정 {Strong, EW, Cosmology, Primordial, Unknown} vs extensible?
- [ ] **Divisibility lattice**: materialized (미리 계산) vs lazy (on-demand)?
- [ ] **Layer indexing**: |prime_set| 기준 vs Ω(n) 기준?

### 역호환성
- [ ] mk1 topology.jsonl → mk2 자동 upgrade path?
- [ ] 기존 17K+ point prime_signature 추출 cost?
- [ ] mk1 CLI (singularity-convergence 등) 유지 vs 재구현?

### 저장 형식
- [ ] Point JSON schema 확장 vs 새 binary format?
- [ ] Divisibility lattice: 별도 파일 vs topology에 embedding?
- [ ] Sector registry: 하드코딩 vs yaml/toml config?

### 물리 연동
- [ ] Physics constants DB: 하드코딩 vs external CODATA fetcher?
- [ ] Tolerance per sector: 고정 vs adaptive?
- [ ] 자동 sector classification: 매 new point 시 vs 배치?

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

## Sign-off

- [ ] 단추 1 (Point representation) 확정
- [ ] 단추 2 (SmoothRing trait) 확정
- [ ] 단추 3 (ρ(n) 함수) 확정
- [ ] 단추 4 (Closure verifier) 확정
- [ ] 단추 5 (Multi-n lattice) 확정
- [ ] Ceiling 체크리스트 결정 완료
- [ ] Implementation phase 예산 확정

**결정자**: dancinlife
**구현자**: Claude + dancinlife
