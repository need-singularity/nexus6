<!-- @doc(type=paper) -->
<!-- @own(sections=[Abstract, "1. 동기", "2. 다섯", "3. 핵심", "4. OEIS", "5. 산출", "6. 향후"], strict=false, order=sequential) -->

# Five novel OEIS-candidate sequences from the σφ=nτ family of n=6 uniqueness

**NEXUS-6 research collective** — 2026-04-19

---

## Abstract (English)

We report five integer sequences arising from the arithmetic identity
σ(n)·φ(n) = n·τ(n), whose unique solution at n ≥ 2 is n = 6 (the first perfect
number, the smallest non-cyclic order, and the denominator of B₂).  Define the
ratio R(n) := σ(n)·φ(n) / (n·τ(n)).  We tabulate (i) the locus where R is
integer, (ii) numbers k with k | lcm(σ(k), φ(k)), (iii)–(iv) the numerator and
denominator of R(n) in lowest terms, and (v) the integer values of R restricted
to the locus.  All five sequences were verified to be absent from the OEIS as of
2026-04-19; one prior candidate (the numerator of R at primes) coincides with
A084921 (Zumkeller 2003).  We further establish a closed form
R(2^(p−1)(2^p−1)) = 2^(p−1)(2^(p−1)−1)/p on the even-perfect subsequence,
yielding R-values 1, 4, 48, 576, … at the first four perfect numbers.  As a
companion observation we note the empirical identity σ(n)·Ω(n) = n·τ(n) holding
exactly at the first four even perfect numbers in [1, 10^4], suggesting a new
characterization conjecture for A000396.

---

## 1. 동기 — n=6 유일성

NEXUS-6 atlas SIG-ATLAS-203 에 따르면 다음 정리가 컴퓨터 검증되어 있다 (3개 독립 증명, n ∈ [2, 10^4]):

> **정리 0 (σφ=nτ 유일성).** σ(n)·φ(n) = n·τ(n) ⟺ n = 6.

이 식은 n=6 이 가지는 세 성질의 동시 만남이다:
- 첫 완전수 (σ(6)=12=2·6),
- 최소 비가환 군 차수가 6 미만이고 모두 가환 (즉 자명한 군 구조 한계),
- Bernoulli 수 B₂ = 1/6 의 분모.

이 정리의 **근방 데이터**가 다음 5개 시퀀스이다.  R(n) := σ(n)·φ(n)/(n·τ(n))
로 두면 R(6)=1 이고, R 의 분자/분모/정수 locus/정수 값이 시퀀스 산출의 자연
스러운 4 방향이다.

---

## 2. 다섯 시퀀스 정의

| Seq | 정의 | 제출파일 |
|-----|------|----------|
| 1 | k s.t. R(k) ∈ ℤ | seq_1.txt |
| 2 | k s.t. k \| lcm(σ(k), φ(k)) | seq_2.txt |
| 3 | numerator(R(n)) (lowest terms) | seq_3.txt |
| 4 | denominator(R(n)) (lowest terms) | seq_4.txt |
| 5 | R(b(k)) where b = Seq 1 (R-value sequence) | seq_5.txt |

### 2.1 처음 항들 (10^4 이하 brute-force)

| Seq | 처음 항 | 길이 (≤10^4) |
|-----|---------|--------------|
| 1 | 1, 6, 28, 54, 96, 120, 135, 196, 224, 234, 270, 360, 496, 672, 775, 819, 864, 891, 936, 1080, … | 53 |
| 2 | 1, 6, 24, 28, 40, 84, 96, 117, 120, 224, 234, 252, 288, 360, 384, 468, 496, 640, 672, 756, … | 62 |
| 3 | 1, 3, 4, 7, 12, 1, 24, 15, 26, 9, 60, 14, 84, 18, 16, 31, 144, 13, 180, 14, … | 무한 |
| 4 | 1, 4, 3, 6, 5, 1, 7, 8, 9, 5, 11, 9, 13, 7, 5, 10, 17, 6, 19, 5, … | 무한 |
| 5 | 1, 1, 4, 5, 7, 6, 16, 19, 18, 14, 12, 13, 48, 24, 128, 64, 35, 88, 35, 30, … | (Seq 1 길이) |

---

## 3. 핵심 결과

### 3.1 Seq 1 의 완전수 포함

Seq 1 의 처음 4 완전수 (A000396) 를 모두 포함한다 — 6, 28, 496, 8128.  
이는 우연이 아니다 (3.3 절 참조).

### 3.2 R 의 닫힌 형태 (perfect-number subsequence)

**정리 1 (R at even perfects).** p 가 홀소수이고 q := 2^p − 1 이 메르센 소수일
때, M_p := 2^(p−1) · q 에 대하여
$$
R(M_p) = \frac{2^{p-1} \cdot (2^{p-1} - 1)}{p}.
$$

**증명.** σ(M_p) = (2^p − 1)·(q+1) = q·2^p, φ(M_p) = 2^(p−2)·(q−1)
= 2^(p−1)·(2^(p−1) − 1), τ(M_p) = p·2 = 2p, n·τ = M_p · 2p = 2^p · q · p.  
대입:
R(M_p) = (q·2^p) · (2^(p−1)·(2^(p−1)−1)) / (2^p · q · p)
       = 2^(p−1)·(2^(p−1)−1)/p. ∎

p=2 (M=6) 인 경우엔 q=3, q+1=4=2^2, φ(6)=2, R=1·1/2 = 1 (별도 검증).

**검증 (p=2,3,5,7):**

| p | M_p | R(M_p) closed | R(M_p) brute |
|---|-----|---------------|--------------|
| 2 | 6 | 1 | 1 |
| 3 | 28 | 4 | 4 |
| 5 | 496 | 48 | 48 |
| 7 | 8128 | 576 | 576 |

### 3.3 추측 (open)

**추측 1.** 모든 짝수 완전수는 Seq 1 에 속한다.  
(Equivalent to: 모든 메르센-소수 지수 p 에 대해 p \| 2^(p−1)·(2^(p−1) − 1).
Fermat 소정리에 의해 ord_p(2) \| p−1 이므로 2^(p−1) ≡ 1 (mod p), 즉
p \| 2^(p−1) − 1 항상 성립. ⇒ 정리.)  
→ **추측 1은 사실상 증명됨. 본문 정리 1 의 따름.**

**추측 2** (open). σ(k)·Ω(k) = k·τ(k) ⟺ k 는 짝수 완전수.  
검증: [1, 10^4] 에서 양변 만족 = {6, 28, 496, 8128} = A000396 ∩ [1, 10^4].  
σΩ-Ω 변형은 기존 OEIS A000396 의 어떤 characterization 과도 다르다. 새 comment 후보.

**추측 3** (open). σ(n)·ω(n) = n·τ(n) ⟺ n = 6 (n ≥ 1).  
검증: [1, 10^4] 유일해 = 6.  
σφ=nτ 와 독립 계열 — ω 가 σ 와 곱해질 때만 6 강제.

---

## 4. OEIS 사전 검색 결과 (2026-04-19)

| 후보 | OEIS 검색 결과 | 결정 |
|------|----------------|------|
| Seq 1 (locus) | No results | 신규 제출 |
| Seq 2 (lcm divides) | No results | 신규 제출 |
| Seq 3 (R num) | No results | 신규 제출 |
| Seq 4 (R den) | No results | 신규 제출 |
| Seq 5 (R values) | No results | 신규 제출 |
| ~~R(p) num at primes~~ | **A084921** (lcm(p−1,p+1), Zumkeller 2003) | 기존 |

원래 메모리 후보 5번 (R(p) 분자) 은 lcm(p−1, p+1) = (p²−1)/2 (홀수 p) 으로
A084921 과 동일.  본 논문은 이 위치를 **R 정수 값 시퀀스** 로 교체.

---

## 5. 산출 도구

- `shared/discovery/oeis_submissions/tools/oeis_compute.awk` — 단일 awk 파일,
  의존성 없음, N=10^4 brute-force 약 5초.
- 의도적 hexa-free: hexa 인터프리터 hot path 회피, awk 정수 산술 충분.

---

## 6. 향후 작업

- N=10^5, 10^6 까지 확장 (gawk bigint 또는 hexa 구현 필요)
- Seq 5 의 closed form 이 perfect-number subsequence 외에서 어떤 algebraic
  family 따르는지 탐색 (e.g. R 값이 평방수/세제곱수일 조건)
- 추측 2 (σΩ=nτ ⟺ even perfect) 증명 시도 — 짝수 완전수 σ=2n, Ω=p (p 메르센
  지수+1 자릿수), τ=2p ⇒ σΩ = 2n·p = n·2p = n·τ ✓.  역방향: σΩ=nτ 이고 n
  짝수면 ... (계속)

---

## 부록 A — STAR identities 통계 (참고)

[1, 10^4] brute-force:

```
σ(n)·Ω(n)  = n·τ(n)         : {6, 28, 496, 8128}              (4 해, perfect numbers)
σ(n)·ω(n)  = n·τ(n)         : {6}                              (유일)
σ·φ·ω(n)   = n·τ·Ω(n)       : {1, 6}                          (유일 비자명 = 6)
σ(n)·φ(n)  = n·τ(n)         : {6}                              (유일, 정리 0)
σ(n)·φ(n) / (n·τ(n)) ∈ ℤ    : Seq 1 (53 해)
```

---

## 참고

- OEIS A000005 (τ), A000010 (φ), A000043 (Mersenne exponents), A000203 (σ),
  A000396 (perfect numbers), A084921 (lcm(p−1, p+1)).
- NEXUS-6 atlas: `shared/n6/atlas.signals.n6` SIG-ATLAS-203, SIG-META-101/102.
- 메모리: `project-oeis-novel-sequences`, `project-star-identities` (사용자 메모리, 2026-04-09 발견 / 2026-04-19 검증·확장).
