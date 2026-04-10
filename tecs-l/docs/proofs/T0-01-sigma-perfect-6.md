# T0-01: σ₋₁(6) = 2 (Divisor Reciprocal Sum of Perfect Number 6)

## Proposition

6 is a perfect number, and σ₋₁(6) = 2.

## Definition

σ₋₁(n) = Σ_{d|n} d⁻¹ (sum of reciprocals of divisors of n)

## Direct Calculation

Divisors of 6: {1, 2, 3, 6}

```
σ₋₁(6) = 1/1 + 1/2 + 1/3 + 1/6
        = 6/6 + 3/6 + 2/6 + 1/6
        = 12/6
        = 2
```

## Verification by Euler Product Formula

6 = 2 × 3 (prime factorization)

By multiplicative property:

```
σ₋₁(6) = σ₋₁(2) × σ₋₁(3)
        = (1 + 1/2) × (1 + 1/3)
        = (3/2) × (4/3)
        = 12/6
        = 2
```

## Relationship with Perfect Numbers

Perfect number definition: σ(n) = 2n (sum of divisors equals twice the number)

```
σ(6) = 1 + 2 + 3 + 6 = 12 = 2 × 6  ✓
```

Relationship between σ₋₁(n) and σ(n):

```
σ₋₁(n) = σ(n) / n
σ₋₁(6) = σ(6) / 6 = 12 / 6 = 2
```

Therefore σ₋₁(n) = 2 ⟺ σ(n) = 2n ⟺ n is a perfect number.

## Numerical Verification Values

| Item | Value |
|------|-------|
| σ₋₁(6) | 2.000000000000000 |
| σ(6) | 12 |
| 6 is a perfect number | True |

## References

- Euclid's Elements Book IX Proposition 36: 2^(p-1)(2^p - 1) is a perfect number (6 = 2¹ × 3 = 2¹(2² - 1))
- Euler: All even perfect numbers have Euclidean form

## Related Hypotheses/Tools

- T0-02 (Euler product truncation)
- T1-01 (Completeness: 1/2 + 1/3 + 1/6 = 1)