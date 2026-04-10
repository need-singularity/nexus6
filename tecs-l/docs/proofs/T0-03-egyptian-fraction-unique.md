# T0-03: 5/6 = 1/2 + 1/3 Unique 2-term Egyptian Fraction Decomposition

## Proposition

The representation of 5/6 as a sum of 2 unit fractions 1/a + 1/b (2 ≤ a < b) has (a,b) = (2,3) as the unique solution.

## Exhaustive Search

Find integer solutions satisfying 5/6 = 1/a + 1/b. Condition: 2 ≤ a < b.

### a = 2

```
5/6 - 1/2 = 5/6 - 3/6 = 2/6 = 1/3
b = 3, a < b (2 < 3) ✓
```

### a = 3

```
5/6 - 1/3 = 5/6 - 2/6 = 3/6 = 1/2
b = 2, but violates a < b condition (3 < 2 false) ✗
```

### a = 4

```
5/6 - 1/4 = 10/12 - 3/12 = 7/12
b = 12/7 ≈ 1.714  (non-integer) ✗
```

### a = 5

```
5/6 - 1/5 = 25/30 - 6/30 = 19/30
b = 30/19 ≈ 1.579  (non-integer) ✗
```

### a ≥ 6

```
When 1/a ≤ 1/6:
1/a + 1/b < 1/6 + 1/7 = 13/42 ≈ 0.310 < 5/6 ✗
```

More precisely: if a ≥ 6, then 1/b = 5/6 - 1/a ≥ 5/6 - 1/6 = 4/6, so b ≤ 3/2, i.e., b = 1. But b > a ≥ 6 is required, which is a contradiction. ✗

## Conclusion

```
(a, b) = (2, 3) is the unique solution
5/6 = 1/2 + 1/3  ∎
```

## Verification

```
1/2 + 1/3 = 3/6 + 2/6 = 5/6 = 0.833333...  ✓
```

## Significance

- 5/6 has a unique 2-term Egyptian fraction representation
- This uniqueness constrains the choice of model constants {1/2, 1/3}
- Extends to 3 terms: 1/2 + 1/3 + 1/6 = 1 (completeness, T1-01)

## Evidence

- Egyptian fraction theory (Rhind Papyrus, c. 1650 BCE)
- Number theory of unit fraction decomposition

## Related Hypotheses/Tools

- T1-01 (Completeness: 1/2 + 1/3 + 1/6 = 1)
- T1-02 (Constant relations)