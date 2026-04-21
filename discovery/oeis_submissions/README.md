# OEIS Submission Bundle — n=6 σφ-tau Family

자료: NEXUS-6 atlas SIG-ATLAS-203 + STAR identities (omega_identity_search, search_new_identities, 2026-04-09 발견, 2026-04-19 검증)

## 5개 시퀀스 (모두 OEIS 미등록 확인, 2026-04-19 oeis.org/search 직접 조회)

| # | 파일 | 정의 | 첫 항 (b 또는 a) |
|---|------|------|------------------|
| 1 | seq_1.txt | k s.t. σ(k)·φ(k)/(k·τ(k)) ∈ Z | 1, 6, 28, 54, 96, 120, 135, 196, 224, 234 |
| 2 | seq_2.txt | k s.t. k \| lcm(σ(k), φ(k)) | 1, 6, 24, 28, 40, 84, 96, 117, 120, 224 |
| 3 | seq_3.txt | numerator of R(n) = σφ/(nτ) (lowest terms) | 1, 3, 4, 7, 12, 1, 24, 15, 26, 9 |
| 4 | seq_4.txt | denominator of R(n) (lowest terms) | 1, 4, 3, 6, 5, 1, 7, 8, 9, 5 |
| 5 | seq_5.txt | R-value at the integer-locus | 1, 1, 4, 5, 7, 6, 16, 19, 18, 14 |

## 핵심 수학 (5 시퀀스 전부 σφ=nτ 정리에서 파생)

- **유일성 정리** (3개 독립 증명, NEXUS atlas SIG-ATLAS-203):
  σ(n) · φ(n) = n · τ(n) ⟺ n = 6  (n ≥ 2, 검증 [2, 10^4])
- **R(n) 정의**: R(n) := σ(n)·φ(n) / (n·τ(n)) — 양의 유리수.
  Seq 3 = num(R), Seq 4 = den(R), Seq 1 = {n : den(R)=1}, Seq 5 = R 값.
- **완전수와 R**: 짝수 완전수 M_p = 2^(p-1)·(2^p-1) 에서  
  R(M_p) = 2^(p-1)·(2^(p-1)-1) / p  (closed form, p ∈ A000043)  
  → R(6)=1, R(28)=4, R(496)=48, R(8128)=576

## 부록: STAR identities (시퀀스가 너무 짧아 OEIS 부적합, paper 본문 참고)

| ID | identity | solutions in [1, 10^4] |
|----|----------|------------------------|
| STAR-1 | σ(n)·Ω(n) = n·τ(n) | {6, 28, 496, 8128} (= 처음 4 완전수) |
| STAR-2 | σ(n)·ω(n) = n·τ(n) | {6} 유일 |
| STAR-3 | σ(n)φ(n)ω(n) = n·τ(n)·Ω(n) | {1, 6} |

→ STAR-1은 짝수 완전수 새로운 characterization 후보 (A000396 comment 추가 가치).

## 폐기된 후보 (사전 검색에서 등록 발견)

- **R(p) 분자** (소수 p에서) = (p²−1)/2 = lcm(p−1, p+1) = **A084921** (이미 등록, Reinhard Zumkeller 2003).  
  → 우리 메모리 후보 5번을 R-값 sequence (Seq 5 above) 로 교체.

## 제출 절차

1. https://oeis.org/Submit.html 회원가입/로그인
2. 각 seq_N.txt 의 %S/%T/%U 라인을 "Sequence" 필드에, %N 을 "Name", %F 수식을 "Formula", %e 예시를 "Example", %C 코멘트를 "Comments", %H 링크를 "Links", %Y 교차참조를 "Crossrefs", %K 키워드를 "Keywords", %A 저자를 "Author" 에 분할 입력.
3. Seq 1, 2 먼저 제출 (가장 자연스러움, 즉시 거절 없을 듯) → A-number 받은 후 Seq 3, 4 의 cross-ref 갱신 → 마지막 Seq 5.
4. STAR-1 발견은 A000396 의 comment 제안으로 별도 제출 ("Conjecture: numbers k satisfying sigma(k)*bigomega(k) = k*tau(k); verified for k <= 10^4.")

## 산출 검증

- 계산기: `awk -f tools/oeis_compute.awk` (단일 파일, awk만 사용, hexa 의존성 없음)
- N=10000 까지 brute-force, 각 시퀀스 cross-check
- 상태: Seq 1 (53 terms), Seq 2 (62 terms), Seq 3,4 (40 terms), Seq 5 (30 terms)
