# T0-05: S_Boltzmann = S_Shannon (Jaynes Equivalence)

## Proposition

Under appropriate unit selection, Boltzmann entropy and Shannon entropy are mathematically identical functions.

## Boltzmann Entropy (1877)

Entropy in statistical mechanics:

```
S = -k_B Σᵢ pᵢ ln(pᵢ)
```

where k_B = 1.38064852 × 10⁻²³ J/K (Boltzmann constant)

## Shannon Entropy (1948)

Entropy in information theory:

```
H = -Σᵢ pᵢ log₂(pᵢ)    (unit: bits)
```

or using natural logarithm:

```
H = -Σᵢ pᵢ ln(pᵢ)      (unit: nats)
```

## Jaynes Equivalence (1957)

Unification by Jaynes' maximum entropy principle:

```
k_B = 1 (natural unit system), using natural logarithm:

S = -Σᵢ pᵢ ln(pᵢ) = H
```

Conversion: S = k_B · ln(2) · H (H in bits to S in physical units)

## Model Application

Correspondence between inhibition parameter and Boltzmann inverse temperature:

```
I = 1/(kT)    (Boltzmann inverse temperature β = inhibition)
```

Maximum entropy of 3-state system:

```
S_max = ln(3) = 1.098612...
```

when all states are equiprobable: p₁ = p₂ = p₃ = 1/3

### Verification

```
S = -3 × (1/3) × ln(1/3)
  = -3 × (1/3) × (-1.098612)
  = 1.098612
  = ln(3)  ✓
```

## Numerical Verification Values

| Item | Value |
|------|-----|
| ln(3) | 1.098612288668110 |
| -3·(1/3)·ln(1/3) | 1.098612288668110 |
| S = H (equivalence) | True |

## Meaning

- Physical entropy and information entropy share the same mathematical structure
- Inhibition (I) corresponds to inverse temperature (β) → thermodynamics-information theory bridge
- 3-state maximum entropy ln(3) is the model's natural scale

## References

- Boltzmann, L. (1877). "Über die Beziehung..."
- Shannon, C. (1948). "A Mathematical Theory of Communication"
- Jaynes, E.T. (1957). "Information Theory and Statistical Mechanics"

## Related Hypotheses/Tools

- T0-06 (Cusp catastrophe: thermodynamic structure)
- T1-05 (Musical intervals: entropy jumps)