# T1-05: Perfect Fourth = 4/3 → ln(4/3) = Golden Zone Width

## Proposition

The frequency ratio 4/3 of the just intonation perfect fourth and the N=3 state Golden Zone width ln(4/3) originate from the same mathematical structure.

## Music Theory: Perfect Fourth

Perfect fourth in Pythagorean just intonation:

```
Frequency ratio = 4/3
```

This is one of the simplest frequency ratios (after the perfect fifth 3/2).

```
ln(4/3) = ln(4) - ln(3) = 1.386294 - 1.098612 = 0.287682
```

## Information Theory: Entropy Jump

Maximum entropy of an N-state system:

```
S_max(N) = ln(N)
```

Entropy increase during 3-state → 4-state transition:

```
ΔS = ln(4) - ln(3) = ln(4/3) = 0.287682
```

## Golden Zone Width Formula

Golden Zone width for N-state system:

```
Δ(N) = ln((N+1)/N)
```

When N = 3:

```
Δ(3) = ln(4/3) = 0.287682
```

## Music-Physics Correspondence

| Music | Information Theory | Value |
|------|----------|-----|
| Perfect Fourth (4/3) | 3→4 entropy jump | ln(4/3) = 0.2877 |
| Perfect Fifth (3/2) | 2→3 entropy jump | ln(3/2) = 0.4055 |
| Octave (2/1) | 1→2 entropy jump | ln(2) = 0.6931 |

General formula: Interval ratio (N+1)/N ↔ N→(N+1) state transition

## Comparison with Equal Temperament

Perfect fourth in 12-tone equal temperament:

```
2^(5/12) = 1.334840...  (≈ 4/3 = 1.333333...)
ln(2^(5/12)) = (5/12)·ln(2) = 0.288811
```

Difference from just intonation:

```
|0.288811 - 0.287682| = 0.001129
Relative error: 0.001129 / 0.287682 = 0.39%
```

Agreement within 0.39% error even in equal temperament.

## Numerical Verification Values

| Item | Value |
|------|-----|
| 4/3 | 1.333333333333333 |
| ln(4/3) | 0.287682072451781 |
| 2^(5/12) | 1.334839854170034 |
| ln(2^(5/12)) | 0.288811274553991 |
| Relative error | 0.39% |

## Significance

The interval ratio (N+1)/N can be interpreted as a physical manifestation of the Golden Zone width formula ln((N+1)/N). The mathematical structure of just intonation scales and information-theoretic state transitions share the same logarithmic structure.

## Basis

- Pythagoras (c. 500 BCE): Just intonation interval ratios
- Information theory: Maximum entropy S = ln(N)

## Related Hypotheses/Tools

- T0-05 (Jaynes equivalence: Entropy)
- T0-06 (Cusp phase transition)