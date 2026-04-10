# P-002: The Arithmetic Balance Ratio R(n) and Characterizations of n=6

## Target: American Mathematical Monthly (or similar expository journal)
## Status: Outline / Draft structure

## Abstract (draft)

We introduce the arithmetic balance ratio R(n) = σ(n)φ(n)/(nτ(n)) and develop
its theory. R is multiplicative on coprime integers with R(p^a) = (p^{a+1}-1)/(p(a+1)).
The number 6 is characterized as the unique non-trivial kernel element: R(n)=1 iff
n ∈ {1,6}. We prove that the spectrum Spec_R is discrete, establish that
σφf=1 iff n=6 (linking algebra to spectral geometry), and show that
φ/τ+τ/σ+1/n=1 iff n=6 (the arithmetic-function form of 1/2+1/3+1/6=1).

## Paper Structure

### 1. Introduction
- Define R(n) = σ(n)φ(n)/(nτ(n))
- Motivation: measuring "arithmetic balance" of n
- State main results (Theorems A-H)
- Historical context: σφ=nτ characterizes {1,6} (cite OEIS A066068)

### 2. Multiplicativity and Prime Decomposition
- **Theorem A**: R is multiplicative: R(mn) = R(m)R(n) for gcd(m,n)=1
- **Theorem B**: R(p^a) = (p^{a+1}-1)/(p(a+1)), closed form
- R(p) = (p²-1)/(2p) for primes
- Building blocks table

### 3. The Kernel and Identity Element
- **Theorem C**: ker(R) = {n : R(n)=1} = {1,6}
  - Proof: R(2)=3/4 is the unique sub-1 prime R value
  - Only R(3)=4/3 can complement it to 1
- **Theorem D**: R(6n) = R(n) for gcd(n,6)=1
  - Corollary: 6 acts as identity element under coprime multiplication
- **Theorem E**: R(p)R(q)=1 iff (p,q)=(2,3) [unique reciprocal pair]
  - Proof: Diophantine (p²-1)(q²-1)=4pq, discriminant method

### 4. The R-Spectrum
- **Theorem F**: Spec_R is discrete (no accumulation points)
  - Proof: R(p) > (p-1)/2 bounds prime factors
- **Theorem G**: Spec_R ∩ (3/4,1) = ∅ and Spec_R ∩ (1,7/6) = ∅ [Gap Theorem]
  - Proof: exhaustive case analysis by factorization type
- Refined structure: bottom 13 values listed explicitly
- **Theorem H**: R(n) < n/2 for all n ≥ 2 (tight: lim sup = 1/2)

### 5. The Topological Master Formula
- Define focal length f(n) = δ⁺(R(n)) · δ⁻(R(n)) in Spec_R
- **Theorem I**: σ(n)φ(n)f(n) = 1 iff n = 6
  - At n=6: δ⁺ = 1/6, δ⁻ = 1/4, f = 1/24 = 1/(σφ)
- Self-referential structure: R-neighbors of 6 are φ(6)=2 and τ(6)=4
  - R(φ(n)) = R(n) - 1/τ(n) iff n=6
  - R(τ(n)) = R(n) + 1/n iff n=6

### 6. The Completeness Identity
- **Theorem J**: φ(n)/τ(n) + τ(n)/σ(n) + 1/n = 1 iff n = 6
  - = 1/2 + 1/3 + 1/6 = 1 in arithmetic function form
  - Proof: cubic factorization for semiprimes 2q

### 7. Connections
- F(s) = Σ R(n)/n^s = ζ(s)ζ(s+1) [Dirichlet series]
- R(P_k) ∈ Z for even perfect numbers [Fermat's little theorem]
- Group structure: G = ⟨R(p)⟩ ≅ Z^{|primes|-1}
- Golden Zone Width W = |log R(2)| = ln(4/3)

### 8. Open Questions
- Exact asymptotic for π_R(x) = |Spec_R ∩ [0,x]|
- Average order of R(n)
- Is the set of integer R values related to known sequences?
- Characterize n with R(n) = k for each integer k

## Key References
- OEIS A066068: σ(n)φ(n)
- Perfect numbers and σ(n)=2n
- Multiplicative functions (Apostol, Introduction to Analytic Number Theory)
- Von Staudt-Clausen theorem (Bernoulli denominators)

## Figures
1. R-spectrum scatter plot (n vs R(n))
2. Gap structure around R=1
3. Self-referential loop diagram
4. Bottom 13 R values with gaps

## Length estimate: 10-12 pages
