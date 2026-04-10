# T1-03: G×I = D×P (Conservation Law)

## Proposition

From the definition G = D×P/I, it follows that G×I = D×P holds identically, forming a conserved quantity.

## Derivation

Starting from the definition:

```
G = (D × P) / I
```

Multiplying both sides by I:

```
G × I = D × P
```

This is an **identity** directly derived from the definition. ∎

## Meaning of Conserved Quantity

```
Q ≡ G × I = D × P = const  (when D, P fixed)
```

- When Genius(G) increases, Inhibition(I) decreases proportionally
- The product of Deficit(D) and Plasticity(P) is conserved
- Structurally similar to energy conservation (E_k + E_p = const)

## Numerical Verification

Verified with 10,000 random (D, P, I) triplets:

```
D, P, I ~ Uniform(0, 1)  independent draws
G = D × P / I
Verify: |G×I - D×P| < ε
```

| Item | Value |
|------|-------|
| Number of trials | 10,000 |
| Violations | 0 |
| Maximum absolute error | 1.11 × 10⁻¹⁶ |
| Mean absolute error | 3.2 × 10⁻¹⁷ |

Maximum error 1.11e-16 is smaller than IEEE 754 double-precision machine epsilon (2.22e-16).

## Identity vs Physical Law

This conservation law is an **identity by definition**, so:

- Cannot be refuted (mathematically true)
- Holds for all D, P, I > 0
- Unlike physical conservation laws, no experimental verification needed

However, in model interpretation:
- Makes the inverse relationship between G and I explicit
- Constrains system degrees of freedom (4 variables → 3 degrees of freedom)

## Basis

- Algebraic identity (directly derived from definition)
- IEEE 754 floating-point arithmetic standard

## Related Hypotheses/Tools

- T0-04 (Banach fixed point: I* = 1/3)
- T1-04 (G ~ Γ(α=2): distribution of conserved quantity)