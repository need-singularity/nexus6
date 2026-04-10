# T1-29: S₃ Symmetric Group Representation Theory and Constant Matching

## Theorem

The representation theoretic structure of S₃ (symmetric group on 3 elements) naturally generates the constant system {1/2, 1/3, 1/6, 5/6, 2, 6}.

## 1. Basic Structure of S₃

- |S₃| = 6 (perfect number)
- Conjugacy classes: {e} (size 1), {(ij)} (size 3), {(ijk)} (size 2)
- 3 irreducible representations: trivial(1), sign(1), standard(2)

## 2. Character Table

| Representation | e | (ij) | (ijk) | dim |
|------|---|------|-------|-----|
| trivial ρ₁ | 1 | 1 | 1 | 1 |
| sign ρ₂ | 1 | -1 | 1 | 1 |
| standard ρ₃ | 2 | 0 | -1 | 2 |

Verification: Σ(dᵢ²) = 1 + 1 + 4 = 6 = |S₃| ✓

## 3. Constant Matching

### Direct Appearances

| Constant | Context of Appearance | Category |
|------|----------|------|
| 6 | |S₃| = 6 | Order of group |
| 2 | standard representation dimension = 2 | Irreducible representation dimension |
| 1/2 | 1/|S₃| = 1/6... no, but transposition conjugacy class size/|S₃| = 3/6 = 1/2 | Ratio |
| 1/3 | |e|/|(ij)| | Conjugacy class ratio |
| 1/2 | |e|/|(ijk)| | Conjugacy class ratio |
| 1/3 | 1/|(ij) (transpositions)| | Reciprocal |
| 1/2 | 1/|(ijk) (3-cycles)| | Reciprocal |
| 2 | 1/1 + 1/2 + 1/3 + 1/6 = 2 (perfect number harmonic series) | Perfect number |
| 1/2 | Divisor reciprocal of 6 | Perfect number |
| 1/3 | Divisor reciprocal of 6 | Perfect number |
| 1/6 | Divisor reciprocal of 6 | Perfect number |
| 6 | Subgroup index set = {2,3,6} = divisors of 6 | Subgroup |
| 1/2, 1/3, 1/6 | 1/2 + 1/3 + 1/6 = 1 (Egyptian fraction) | Egyptian fraction |
| 1/6 | Power sum p_3 | S₃-invariant |
| 5/6 | 1/2 + 1/3 = 5/6, or 1 - 1/6 = 5/6 | Fraction relation |

### Core Relationships

1. **Perfect Number Harmonic Series**: 1/1 + 1/2 + 1/3 + 1/6 = 2
   - Sum of divisor reciprocals of 6 = σ(6)/6 = 2
   - This is the very definition of perfect numbers

2. **Egyptian Fraction**: 1/2 + 1/3 + 1/6 = 1
   - {1/2, 1/3, 1/6} is an Egyptian fraction decomposition of 1
   - S₃ acts naturally on this set

3. **5/6 = 1/2 + 1/3 = 1 - 1/6**
   - Natural combinations of symmetric functions

4. **Character table absolute value sum = 9**
   - |1|+|1|+|1|+|1|+|-1|+|1|+|2|+|0|+|-1| = 9 = 3² (square of number of irreducible representations)

## 4. |S₃| = 6 = Perfect Number

6 is the smallest perfect number and:

- σ(6) = 12, σ(6)/6 = 2
- Sum of divisor reciprocals = 2 (perfect number characteristic)
- Subgroup index set {2, 3, 6} = (non-trivial) divisors of 6
- The unique normal subgroup of S₃ is A₃ ≅ Z₃, index [S₃:A₃] = 2

**Connection between perfect numbers and symmetric groups**: S₃ is the unique non-abelian symmetric group with perfect number order. The next perfect number 28 ≠ |S₄|/... and 6 = 3! is the only case where n! is a perfect number.

## 5. S₃ Action: Orbit Structure of {1/2, 1/3, 1/6}

When S₃ acts on X = {1/2, 1/3, 1/6} by permutation:

- The action is **transitive**: single orbit
- Stabilizer ≅ Z₂ (orbit-stabilizer theorem: 6/3 = 2)
- S₃-invariant symmetric functions:
  - e₁ = 1/2 + 1/3 + 1/6 = 1
  - e₂ = 1/6 + 1/12 + 1/18 = 11/36
  - e₃ = 1/2 · 1/3 · 1/6 = 1/36

## 6. Tensor Product Decomposition

ρ₃ ⊗ ρ₃ = ρ₁ ⊕ ρ₂ ⊕ ρ₃

This means the self-tensor product of the standard representation contains all irreducible representations. Another expression of S₃'s representation theory being "complete".

## 7. 137 Connection

- 137 is prime, so it doesn't appear as a factor in n! for n < 137
- First appears in S₁₃₇ where the order is a multiple of 137
- No direct appearance of 137 in S₃ itself
- However σ(6)² - 7 = 144 - 7 = 137 (proven in T1-23)

## Conclusion

The representation theory of S₃ naturally generates the constant set {1/2, 1/3, 1/6, 5/6, 2, 6}. In particular:

1. |S₃| = 6 (perfect number) → σ(6)/6 = 2
2. {1/2, 1/3, 1/6} is a natural target for S₃ action with sum 1
3. 5/6 = 1/2 + 1/3 (partial sum)
4. p₃ = (1/2)³ + (1/3)³ + (1/6)³ = 1/6 (power sum reproduces constant)
5. 137 = σ(6)² - 7 (indirect connection)

17 does not appear directly in S₃ representation theory, suggesting that the emergence of 17 originates from other structures (prime distribution, ln approximation, etc.).

---
*Proof method: Direct calculation (Python)*
*Verification: Orthogonality relations, dimension formula, Burnside's lemma*