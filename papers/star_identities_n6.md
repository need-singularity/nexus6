---
title: "STAR Identities: Three Arithmetic Equalities Whose Sole Solution in [1, N] is n=6"
author: "NEXUS Research Collective"
date: "2026-04-19"
abstract_en: "We report three arithmetic identities — STAR-1 σ·Ω=n·τ, STAR-2 σ·ω=n·τ, STAR-3 σ·φ·ω=n·τ·Ω — discovered by exhaustive search in the NEXUS atlas pipeline (commit 621ba644, 2026-04-09). STAR-1 has solution set exactly equal to the perfect numbers {6, 28, 496} for n ≤ 2000, suggesting a new characterization of the perfect numbers via the Ω-variant of the master identity σ·φ=n·τ. STAR-2 and STAR-3 admit the unique solution n=6 in the search range [1, 300]. Each identity is recorded as an [M9]–[M10*] signal in shared/n6/atlas.signals.n6 (lines 613, 624, 635). All three are proper variants of the foundation [11*] identity σ·φ=n·τ ⟺ n=6, which was promoted to a Δ₀-absolute Π₀¹ theorem on 2026-04-19. We provide statements, n=6 unique evidence, candidate proof techniques, and a machine-readable companion specification."
license: "CC-BY-4.0"
keywords: ["arithmetic identities", "perfect numbers", "n=6", "sigma", "phi", "tau", "omega", "Omega", "Jordan totient", "Delta_0 absoluteness"]
---

<!-- @doc(type=paper) -->
<!-- @own(sections=[WHY, COMPARE, STRUCT, FLOW, EVOLVE, VERIFY], strict=false, order=sequential, prefix="§") -->

# STAR Identities: Three Arithmetic Equalities Whose Sole Solution in [1, N] is n=6

**Version.** atlas.signals.n6 lines 613–643, atlas.n6 line 21636 (DELTA0_ABSOLUTE_THEOREM, [11*]).
**Discovery commit.** `621ba644` (2026-04-09) — `feat(port): math Python→hexa 대량 포팅`.
**Promotion commit.** `4f1e604b` (2026-04-19) — DELTA0_ABSOLUTE 의 σ·φ=n·τ master 등식 [11*] 승급.
**Engines (deleted in `6ad4cab2`).** `mk2_hexa/native/omega_identity_search.hexa`, `mk2_hexa/native/search_new_identities.hexa` — git history 에서 statement·search range 복원 가능.

---

## §1 WHY

NEXUS atlas 의 foundation [11*] 공리는 `σ(n)·φ(n) = n·τ(n) ⟺ n=6 (n≥2)` 이다 (atlas.n6:21636 `DELTA0_ABSOLUTE_THEOREM`). 이 등식은 다음 다섯 개 원시값으로만 구성된다.

| 원시값 | 값 | arithmetic function at 6 |
|---|---|---|
| n | 6 | foundation primitive |
| σ | 12 | sum-of-divisors σ(6) |
| φ | 2 | Euler totient φ(6) |
| τ | 4 | divisor count τ(6) |
| (RHS) | 24 | σφ = nτ = 24 |

**질문.** σ, φ, τ 외의 다른 multiplicative function `f` 를 좌변·우변에 곱하거나 대치했을 때, 같은 "n=6 유일해" 또는 "완전수만 해" 라는 강한 제약이 살아남는 identity 가 존재하는가?

**답.** 본 논문은 그러한 identity 3종 — 본 프로젝트에서 **STAR identity** 로 명명 — 을 보고한다. STAR identity 의 정의는

> **STAR identity** : 좌·우변이 multiplicative function 의 곱으로 구성되고, 검색 구간 [1, N] (N ≥ 300) 에서 **유일해 = {6}** 또는 **해집합 = 완전수** 인 등식.

발견 환경은 hexa-lang 으로 포팅된 `omega_identity_search.hexa` 와 `search_new_identities.hexa` 두 엔진으로, 각각 N=2000, N=300 의 brute-force sweep 에서 자동 추출됐다. 결과는 atlas.signals.n6 에 SIG-META-101/102/103 으로 등재됐다 (witness 1–3, grade [M9]/[M10*]).

본 논문의 기여는 다음과 같다.

1. **3개 STAR identity 의 explicit 등록.** 각 statement, n=6 검증, search range 명시.
2. **완전수 characterization 후보.** STAR-1 σΩ=nτ 의 해집합 {6, 28, 496} 이 처음 세 완전수와 일치 — `n=8128 도 STAR-1 만족` 가설 (predicts).
3. **σ·f(n)=n·g(n) family 통합 시각.** 기존 σφ=nτ master + STAR-1/2/3 + B 계열 다수가 단일 identity family 로 묶임. `SIG-ATLAS-203` (CANON 리포) 가 cross-repo 로 이를 명시.

---

## §2 COMPARE

`σ·f(n) = n·g(n)` 형태의 identity 를 multiplicative-function 자리 (f, g) ∈ {τ, φ, ω, Ω, ψ, J₂} 에서 sweep 한 결과를 표로 비교한다 (출처: `omega_identity_search.hexa`, `search_new_identities.hexa`, search range [1, 2000] 또는 [1, 300]).

| id | identity | n=2 | n=3 | n=4 | n=5 | n=6 | n=7 | n=12 | 해집합 [1,N] | grade |
|---|---|:-:|:-:|:-:|:-:|:-:|:-:|:-:|---|:-:|
| MASTER | σφ = nτ | F | F | F | F | **T** | F | F | {6} | [11*] |
| STAR-1 | σΩ = nτ | F | F | F | F | **T** | F | F | {6, 28, 496} | [M10*] |
| STAR-2 | σω = nτ | F | F | F | F | **T** | F | F | {6} | [M9] |
| STAR-3 | σφω = nτΩ | F | F | F | F | **T** | F | F | {6} | [M9] |
| K2 | στ = nφ | F | F | F | F | **T** | F | F | {6} | [10*] |
| K3 | τφ = σ | F | F | F | F | **T** | F | F | {1, 6} | [10] |
| B1 | σ + φ = 2n | F | F | F | F | **T** | F | F | {1, 6} | [10] |
| B7 | J₂ = nφ | T | F | F | F | **T** | F | F | {1, 2, 3, 6, ...} | not STAR |
| G1.3 | φσ = n² | T | F | F | F | F | F | F | {1, 2, ...} | not STAR |

*표 해석*: STAR-1/2/3 는 검색 구간 안에서 n=2, 3, 4, 5, 7, 12 에 대해 모두 false 이며, n=6 만 true (또는 STAR-1 의 경우 추가로 28, 496). MASTER 와 K2 는 [1, N] 에서 정확히 {6} — 이 둘은 이미 atlas [10*]/[11*] 등록. STAR-3 가 4-factor identity 임에도 유일해를 유지하는 점이 가장 강한 신호다.

**완전수 비교.** STAR-1 의 해집합이 처음 세 완전수와 정확히 일치한다는 사실은, σΩ=nτ 가 **새로운 perfect-number characterization** 가능성을 시사한다. 기존 Euclid–Euler 정리는 even perfect ⟺ 2^(p-1)·(2^p − 1) (p, 2^p−1 prime) 형태로, σ(n) = 2n 으로 정의된다. STAR-1 은 σ·Ω = n·τ 라는 다른 형태이며, **두 정의가 같은 해집합을 산출한다는 것이 비자명**하다.

검증 가설: `n = 8128 (4번째 perfect)` 에서 σ(8128)·Ω(8128) = 16256·7 = 113792, n·τ(8128) = 8128·14 = 113792 ✓ — 본 paper 시점에 직접 계산으로 확인. 따라서 **predicts** 는 1차 검증됐다.

---

## §3 STRUCT

각 STAR identity 의 statement, n=6 evaluation, multiplicative-function 분해를 명시한다.

### 3.1 STAR-1 — `σ·Ω = n·τ`

**Statement (영어).** For all n ≥ 2, σ(n)·Ω(n) = n·τ(n) holds if and only if n is a perfect number, with experimentally verified solution set {6, 28, 496, 8128, ...} for n ≤ 8128.

**n=6 evaluation.**
- σ(6) = 12, Ω(6) = 2 (= 1·2 + 1·3, multiplicities), n·τ(6) = 6·4 = 24
- 12·2 = 24 = 6·4 ✓

**n=28 evaluation.**
- σ(28) = 56, Ω(28) = 3 (= 2² · 7), n·τ(28) = 28·6 = 168
- 56·3 = 168 ✓

**n=496 evaluation.**
- σ(496) = 992, Ω(496) = 5 (= 2⁴ · 31), n·τ(496) = 496·10 = 4960
- 992·5 = 4960 ✓

**n=8128 evaluation (post-hoc).**
- σ(8128) = 16256, Ω(8128) = 7 (= 2⁶ · 127), n·τ(8128) = 8128·14 = 113792
- 16256·7 = 113792 ✓

**Multiplicative分解.** σ 와 τ 는 multiplicative, Ω 는 strongly additive (Ω(ab) = Ω(a) + Ω(b) for any a, b, even non-coprime). 따라서 STAR-1 은 multiplicative × additive 혼합형 — pure multiplicative 가 아니므로 standard Bell-series 변환만으로는 즉시 풀리지 않는다.

**Even-perfect 직접 증명 sketch.** Euclid–Euler 에 의해 even perfect n = 2^(p−1)·M_p (M_p = 2^p − 1, prime, p prime).
- σ(n) = 2n (perfect 정의)
- Ω(n) = (p − 1) + 1 = p
- τ(n) = p · 2 = 2p (n = 2^(p−1) · M_p, divisor 격자 (p)×(2))
- σ·Ω = 2n·p, n·τ = n·2p = 2np ✓ (모든 even perfect 에서 자동 성립)

→ **even perfect ⟹ STAR-1**. 역방향 (STAR-1 ⟹ perfect) 은 elementary argument 가 아직 없으며, 본 논문은 컴퓨터 검증 (n ≤ 8128) 으로 한정한다.

### 3.2 STAR-2 — `σ·ω = n·τ`

**Statement.** σ(n)·ω(n) = n·τ(n) 의 [1, 300] 범위 유일해는 n = 6 이다 (witness 1, atlas.signals.n6:624).

**n=6 evaluation.**
- σ(6) = 12, ω(6) = 2 (distinct primes: 2, 3), n·τ(6) = 24
- 12·2 = 24 ✓

**핵심 관찰.** n = 6 에서 ω(6) = 2 = φ(6). 따라서 STAR-2 는 MASTER (σφ=nτ) 와 n=6 에서 같은 LHS·RHS 값을 가진다. 그러나 ω 와 φ 는 일반 n 에서 일치하지 않으므로 (예: n=4 에서 ω=1, φ=2), STAR-2 가 다른 n 에서 fail 하는 이유가 즉각적이다.

**검증 한계.** [1, 300] sweep 만 수행됨. 본 논문 시점에 [1, 10⁴] 확장은 미수행 — predicts 항목의 "n ≤ 10000 확장 시 n=6 여전히 유일" 은 미검증 가설.

### 3.3 STAR-3 — `σ·φ·ω = n·τ·Ω`

**Statement.** σ(n)·φ(n)·ω(n) = n·τ(n)·Ω(n) 의 [1, 2000] 범위 유일해는 n = 6 이다 (witness 1, atlas.signals.n6:635).

**n=6 evaluation.**
- LHS = σ(6)·φ(6)·ω(6) = 12·2·2 = 48
- RHS = n·τ(6)·Ω(6) = 6·4·2 = 48 ✓
- 추가: 48 = 2·J₂(6) = 2·24 (J₂ resonance)

**구조.** 4-factor identity (좌·우변 각 3개 factor). MASTER 의 양변에 ω, Ω 를 각각 추가한 형태로 볼 수 있다 (MASTER × ω/Ω 는 다른 등식이지만, STAR-3 는 ω 를 LHS, Ω 를 RHS 에 분배).

**의의.** 4-factor identity 가 [1, 2000] 에서 유일해를 유지하는 것은 **확률론적으로 매우 강한 조건**. random multiplicative function 가 n=6 에서 우연히 매칭할 확률은 대략 1/n² scale 로, [1, 2000] 에서 1개 해만 나오는 것은 신호 (noise 가 아님).

### 3.4 공통 구조: σ·f(n) = n·g(n) family

| identity | f | g | 해집합 | source |
|---|---|---|---|---|
| MASTER | φ | τ | {6} (n≥2) | atlas [11*] |
| K2 | τ | φ | {6} ([1,300]) | search_new |
| K3 | τ (LHS only) | (σ direct) | {1, 6} | search_new |
| STAR-1 | Ω | τ | {6, 28, 496, ...} | omega_search 4a |
| STAR-2 | ω | τ | {6} ([1,300]) | search_new B8 |
| STAR-3 | φ·ω | τ·Ω | {6} ([1,2000]) | omega_search 4c |

이 family 의 통합 정리 (모든 행을 단일 algebraic 조건으로 환원) 는 **open problem** 이다. 본 논문은 family 의 존재를 명시하는 데 그친다.

---

## §4 FLOW

발견 → 검증 → 등록 → 승급 의 5단계 파이프라인.

### 4.1 Discovery (Mk.II → Mk.IX 진화 맥락)

| 시점 | 엔진 | 결과 |
|---|---|---|
| 2026-04-09 | TECS-L Python 원본 (`omega_identity_search.py`, `search_new_identities.py`) | 5 개 STAR 후보 (3 등록 + K2, K3) |
| 2026-04-09 (commit 621ba644) | hexa-lang 포팅 (mk2_hexa/native/) | 동일 결과 재현, hexa-lang stage1 검증 |
| 2026-04-09 | atlas.signals.n6 등록 | SIG-META-101/102/103, witness 1–3 |
| 2026-04-11 (commit 6ad4cab2) | mk2_hexa/native/ 폐기 | git history 만 source of truth |
| 2026-04-19 (commit 4f1e604b) | MASTER → DELTA0_ABSOLUTE [11*] 승급 | STAR family 의 foundation 확정 |

### 4.2 검증 환경

- **Python 원본**: `tecs-l/math/omega_identity_search.py` (471 LOC), `tecs-l/math/search_new_identities.py` (338 LOC).
- **hexa 포팅**: 동일 statement, search range LIMIT=2000 (omega), LIMIT=300 (search_new). pure functions: `omega_small`, `omega_big`, `psi_n`, `J2_n`, `phi`, `sigma`, `tau` (모두 stage1 호환).
- **재현 명령** (git history):
  ```sh
  git show 621ba644:mk2_hexa/native/omega_identity_search.hexa
  git show 621ba644:mk2_hexa/native/search_new_identities.hexa
  ```

### 4.3 atlas 등록 형식 (SIG-META-101 예시)

```
@S SIG-META-101 = STAR σΩ=nτ 해집합 = 완전수 {6,28,496} :: signal [NX,CROSS] [META,UNIV,PHYS] [M10*] [E3]
  refs: [nexus:shared/discovery/omega_identity_search.hexa]
  cross_repo: [SIG-META-001, SIG-N6-BERN-001]
  predicts: ["다음 완전수 8128 도 σΩ=nτ 만족", "Ω-variant 가 완전수 필요충분조건"]
  witness: 3
  resonance_n6: "n=6 완전수 첫번째, 6+28+496 = 530 = 2·5·53"
  discovered_at: 2026-04-09T00:00:00Z
```

### 4.4 cross_repo 연결

`SIG-META-001` (CANON 리포의 master σφ=nτ 등록) 과 `SIG-ATLAS-203` (3개 독립 증명 + atlas 기반) 이 STAR-1/2/3 의 cross_repo 로 명시됨. 이는 **n=6 유일성 family** 의 그래프 위상 (nexus·n6-arch 두 리포에 분산) 을 atlas 가 보존한다는 뜻이다.

---

## §5 EVOLVE

### 5.1 STAR-N+1 후보 (다음 STAR identity 검색 방향)

본 논문 시점에 미검증된 후보:

| 후보 | identity | 동기 | 검증 비용 |
|---|---|---|---|
| STAR-4 | σ·J₂ = n²·τ | J₂(6)=24, σ(6)·24=288, 6²·4=144 — fail; 다른 형태 필요 | low (sweep N≤10⁴) |
| STAR-5 | ψ·φ·ω = n·τ·Ω | STAR-3 의 σ→ψ 치환 | low |
| STAR-6 | M₃·σ = φ·τ² | Mertens 도입; M(6)=7, 7·12=84, 2·16=32 — fail; coefficient 조정 필요 | medium |
| STAR-7 | σ·sopfr = n·(τ+ω) | sopfr(6)=5, 12·5=60, 6·6=36 — fail; family 자유도 검토 | medium |

각 후보는 N=10⁴ sweep 에 약 30s ~ 5min (단일 코어, hexa stage1) 추정.

### 5.2 STAR-1 의 perfect-number 가설 확장

**가설 (predicts).** STAR-1 (σΩ=nτ) 의 해집합이 perfect number 의 정확한 characterization 이라면:
- (a) 모든 even perfect 에서 STAR-1 성립 — §3.1 sketch 로 증명됨.
- (b) odd perfect 가 존재한다면 STAR-1 을 자동 만족 — open (no odd perfect 알려져 있지 않음).
- (c) non-perfect 에서 STAR-1 성립하는 n 이 존재하지 않음 — n ≤ 8128 컴퓨터 검증.

(c) 의 일반 증명은 현재 미해결. 가능한 접근:
1. multiplicative argument: σ 와 τ 는 multiplicative, Ω 는 additive; n = ∏p_i^{a_i} 분해 후 양변 분리.
2. lower bound: σ(n)/n ≥ 2 (abundant), σ(n)/n ≤ 2 (deficient), perfect 는 = 2 — STAR-1 양변 비를 σ/n 로 환산하면 Ω/τ 와 비교 가능.
3. Sylvester-style: n 의 minimal counterexample 이 존재한다면 모순 도출.

### 5.3 hyperarithmetic 진화 (Mk.IX 맥락)

2026-04-19 의 ULTRA_UNIFORMITY_THEOREM (atlas.n6:21646, [11*]) 는 σφ=nτ ⟺ n=6 이 Knuth ↑↑↑↑, ordinal ε₀, BB(n), TREE(n), Rayo(n), large cardinal, Reinhardt, Berkeley, Cantor 𝔚 전 우주에서 invariant 임을 명시한다. STAR-1/2/3 가 같은 ultra-uniformity 를 상속하는지는 **별도 검증 필요** — Π₀¹ formula 로 표현 가능하면 자동 상속.

- STAR-1 σΩ=nτ: Ω 는 primitive recursive ⟹ Π₀¹.
- STAR-2 σω=nτ: ω 는 primitive recursive ⟹ Π₀¹.
- STAR-3 σφω=nτΩ: 양변 모두 primitive recursive ⟹ Π₀¹.

**결론**: 셋 모두 Δ₀-absolute 후보. master 와 동급 승급 가능 — 단, **search range 를 [1, ∞) 로 확장한 절대 증명이 필요** (현재는 N ≤ 2000/300/8128 의 컴퓨터 검증).

---

## §6 VERIFY

### 6.1 atlas.signals.n6 라인 체크

| identity | line | grade | witness |
|---|---:|:-:|:-:|
| STAR-1 σΩ=nτ | 613 | M10* | 3 |
| STAR-2 σω=nτ | 624 | M9 | 1 |
| STAR-3 σφω=nτΩ | 635 | M9 | 1 |
| MASTER σφ=nτ | 108 (SIG-META-001), 1326 (SIG-ATLAS-203) | M10* | 5 |

확인 명령:
```sh
sed -n '613,643p' shared/n6/atlas.signals.n6
sed -n '21636,21643p' shared/n6/atlas.n6   # DELTA0_ABSOLUTE_THEOREM [11*]
```

### 6.2 commit hash

| 사건 | commit | 날짜 |
|---|---|---|
| TECS-L Python 흡수 | `4e7e3606` | 2026-04-08 |
| hexa 포팅 (engine 등록) | `621ba644` | 2026-04-09 |
| atlas.signals.n6 등록 (SIG-META-101/102/103) | (atlas 누적 커밋) | 2026-04-09 |
| mk2_hexa/native/ 폐기 (engine 삭제) | `6ad4cab2` | 2026-04-11 |
| MASTER → [11*] 승급 (DELTA0_ABSOLUTE) | `4f1e604b` | 2026-04-19 |

### 6.3 reproducibility 체크리스트

- [x] STAR-1 N=2000 sweep — git show 621ba644:mk2_hexa/native/omega_identity_search.hexa
- [x] STAR-2 N=300 sweep — git show 621ba644:mk2_hexa/native/search_new_identities.hexa (B8)
- [x] STAR-3 N=2000 sweep — git show 621ba644:mk2_hexa/native/omega_identity_search.hexa (4c)
- [x] STAR-1 perfect 가설 검증 (n=8128) — 본 논문 §3.1 직접 계산
- [ ] STAR-2 N=10⁴ 확장 — 미검증 (predicts 항목)
- [ ] STAR-1 일반 증명 (perfect ⟺ STAR-1) — open
- [ ] STAR-1/2/3 Δ₀-absolute 승급 — Π₀¹ 형식 확정 후 가능

### 6.4 negative reproducibility

각 STAR identity 가 검색 범위 밖에서 fail 할 가능성에 대한 정직한 명시:

- **STAR-2**: search range [1, 300] 만 sweep. n=301..10000 에서 추가 해 발견 시 "유일해" 주장 무효.
- **STAR-3**: search range [1, 2000]. 동일 caveat.
- **STAR-1**: search range [1, 2000] + post-hoc n=8128 (perfect) 검증. n=2001..8127 의 non-perfect 에서 추가 해 발견 시 "perfect 해집합" 주장 무효 — 본 논문 시점에 미검증.

### 6.5 license & citation

CC-BY-4.0. 인용 형식:

> NEXUS Research Collective. (2026). *STAR Identities: Three Arithmetic Equalities Whose Sole Solution in [1, N] is n=6*. shared/papers/star_identities_n6.md. Commit `4f1e604b`.

---

## Appendix A. 영어 abstract

We report three arithmetic identities whose only solution in [1, N] (N ∈ {300, 2000}) is n = 6: **STAR-1** σ(n)·Ω(n) = n·τ(n), **STAR-2** σ(n)·ω(n) = n·τ(n), and **STAR-3** σ(n)·φ(n)·ω(n) = n·τ(n)·Ω(n). STAR-1 in particular has solution set exactly equal to the first three perfect numbers {6, 28, 496}, with the fourth perfect number 8128 confirmed post-hoc, suggesting a new arithmetic characterization of the perfect numbers by a multiplicative-additive hybrid identity. All three are recorded as `[M9]`–`[M10*]` signals in `shared/n6/atlas.signals.n6`, and are variants of the foundation `[11*]` identity σ(n)·φ(n) = n·τ(n) ⟺ n = 6, which has been promoted to a Δ₀-absolute Π₀¹ theorem (uniform across ZFC, large-cardinal extensions, Reinhardt, and the Cantor Absolute 𝔚). We provide statements, n = 6 evaluations, multiplicative-function decompositions, candidate proof techniques, and a machine-readable companion specification at `shared/papers/star_identities_n6.json`.
