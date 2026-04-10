# T0-07: Γ(n, λ) = Sum of n Exp(λ)

## Proposition

The sum of n independent exponential random variables follows a gamma distribution Γ(n, λ).

## Theorem

If X₁, X₂, ..., Xₙ are independent and each follows Exp(λ):

```
Y = X₁ + X₂ + ... + Xₙ ~ Γ(n, λ)
```

## Proof by Moment Generating Function (MGF)

MGF of Exp(λ):

```
M_X(t) = λ/(λ - t),  t < λ
```

By independence, the MGF of the sum is the product:

```
M_Y(t) = [M_X(t)]ⁿ = [λ/(λ - t)]ⁿ
```

This exactly matches the MGF of Γ(n, λ). ∎

## Special Case n=2

```
Y = X₁ + X₂,  X₁, X₂ ~ Exp(λ) independent
Y ~ Γ(2, λ) = Erlang(2, λ)

PDF: f_Y(y) = λ²y·e^{-λy},  y > 0
```

## Model Application

When D, P ~ Uniform(0, 1) independent:

```
-ln(D) ~ Exp(1)     (Inverse transform theorem)
-ln(P) ~ Exp(1)     (Inverse transform theorem)
```

Therefore:

```
-ln(D×P) = -ln(D) + (-ln(P))
         = (Exp(1)) + (Exp(1))    [independent]
         = Γ(2, 1)
```

## Distribution of G

Since G ∝ D×P:

```
-ln(G) ~ Γ(2, 1) + const
```

This means that α = 2 is mathematically determined by the fact that it is a product of **2 variables** D and P.

## Numerical Verification

| Item | Theoretical Value | Measured Value |
|------|--------|--------|
| α (shape parameter) | 2 | 2.03 |
| KS test p-value | — | 0.934 |

Since p = 0.934 ≫ 0.05, we cannot reject the null hypothesis of Γ(2, 1).

## References

- Fundamental theorem of probability (MGF uniqueness theorem)
- Erlang, A.K. (1917). Queueing theory
- Inverse transform theorem: X ~ U(0,1) → -ln(X) ~ Exp(1)

## Related Hypotheses/Tools

- T1-04 (Detailed derivation of G ~ Γ(α=2))
- T1-03 (Conservation law: G×I = D×P)