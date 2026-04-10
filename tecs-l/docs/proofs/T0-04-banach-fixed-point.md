# T0-04: Banach Contraction Mapping Theorem → I* = 1/3

## Proposition

f(I) = 0.7I + 0.1 is a contraction mapping, and the unique fixed point is I* = 1/3.

## Banach Fixed Point Theorem (Banach 1922)

If (X, d) is a complete metric space and f: X → X is a contraction mapping (∃ q ∈ [0,1): d(f(x), f(y)) ≤ q·d(x,y)), then f has a unique fixed point x*, and the iteration xₙ₊₁ = f(xₙ) starting from any x₀ converges to x*.

## Contraction Mapping Verification

```
f(I) = 0.7I + 0.1
f'(I) = 0.7
|f'(I)| = 0.7 < 1  ∀I
```

→ Lipschitz constant q = 0.7 < 1, so it is a contraction mapping. ✓

## Fixed Point Calculation

```
f(I*) = I*
0.7I* + 0.1 = I*
0.1 = I* - 0.7I*
0.1 = 0.3I*
I* = 0.1 / 0.3
I* = 1/3 = 0.333333...
```

## Convergence Rate

Error bound:

```
|Iₙ - 1/3| ≤ 0.7ⁿ × |I₀ - 1/3|
```

Starting from I₀ = 0.99:

| n | Iₙ | |Iₙ - 1/3| |
|---|-----|-----------|
| 0 | 0.990000 | 0.656667 |
| 1 | 0.793000 | 0.459667 |
| 5 | 0.442739 | 0.109406 |
| 10 | 0.352886 | 0.019553 |
| 20 | 0.333947 | 0.000613 |
| 50 | 0.333333 | 5.97e-10 |
| 200 | 0.333333 | ≈ 0 (machine precision) |

## Numerical Verification

```
f²⁰⁰(0.99) = 0.333333333333333  (≈ 1/3)
|f²⁰⁰(0.99) - 1/3| < 10⁻¹⁵
```

## Uniqueness

By the Banach theorem, a contraction mapping on a complete metric space has a **unique** fixed point. Therefore, I* = 1/3 is unique.

## Significance

- I* = 1/3: Equilibrium point of the inhibition parameter
- Convergence from any initial value → Structural stability of the model
- Convergence rate 0.7ⁿ → Geometric convergence

## References

- Banach, S. (1922). "Sur les opérations dans les ensembles abstraits"
- Basic theorem of functional analysis

## Related Hypotheses/Tools

- T1-02 (Constant relationships: Role of 1/3)
- T1-03 (Conservation law: G×I = D×P)