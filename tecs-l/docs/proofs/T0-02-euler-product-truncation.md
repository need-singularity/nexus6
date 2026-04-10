# T0-02: Euler Product Truncation at p=2,3 → Integer 2

## Proposition

Truncating the Euler product at primes p=2,3 yields a divisor function that produces exactly the integer 2, and this is the unique integer-producing combination.

## Euler Product Formula

Euler product representation of the Riemann zeta function:

```
ζ(s) = Π_p 1/(1 - p⁻ˢ)    (product over all primes p)
```

## Truncation at p=2,3 (s=1 form)

```
Π_{p∈{2,3}} 1/(1 - 1/p) = 1/(1 - 1/2) × 1/(1 - 1/3)
                          = 1/(1/2) × 1/(2/3)
                          = 2 × 3/2
                          = 3
```

## Divisor Function Form

σ₋₁(6) = Π_{p|6} (1 + 1/p):

```
(1 + 1/2)(1 + 1/3) = (3/2)(4/3) = 12/6 = 2
```

## Exhaustive Check of Other Prime Combinations

| Prime Set | Π(1+1/p) | Integer? |
|-----------|----------|----------|
| {2} | 3/2 = 1.500 | No |
| {3} | 4/3 = 1.333 | No |
| {2, 3} | **2.000** | **Yes** |
| {2, 5} | 9/5 = 1.800 | No |
| {2, 3, 5} | 12/5 = 2.400 | No |
| {2, 3, 7} | 16/7 = 2.286 | No |
| {2, 3, 5, 7} | 96/35 = 2.743 | No |

## Reason for Integer Result

```
Π_{p|n}(1 + 1/p) = σ₋₁(n)  (when n is squarefree)
σ₋₁(n) ∈ ℤ  ⟺  σ(n) ≡ 0 (mod n)  ⟺  n is a perfect number
2 × 3 = 6 = smallest perfect number
```

Therefore, the integer output at p=2,3 is a direct consequence of 6 being a perfect number.

## Numerical Verification Values

| Item | Value |
|------|-------|
| (1+1/2)(1+1/3) | 2.000000000000000 |
| (1+1/2)(1+1/3)(1+1/5) | 2.400000000000000 |
| (1+1/2)(1+1/3)(1+1/5)(1+1/7) | 2.742857142857143 |

## References

- Euler (1737): Euler product representation of the zeta function
- Multiplicative structure of perfect numbers

## Related Hypotheses/Tools

- T0-01 (σ₋₁(6) = 2)
- T1-01 (Perfectness)