# Monte Carlo v6.0 Rerun

- date: 2026-04-09 19:39
- data: reality_map_live.json (v9.4, 3847 nodes)
- natural int targets: 1555 (unique 311)
- N=1000

## n=2..12 (unique targets)

| n | constants | reach | hits | hit% | eff | z_hit | z_eff | z_sm | p_bonf |
|---|-----------|-------|------|------|-----|-------|-------|------|--------|
| 2 | [1, 2, 3] | 9 | 9 | 2.9% | 1.000 | -4.59 | +4.33 | +0.00 | 0.0000 |
| 3 | [1, 2, 3, 4, 8] | 25 | 22 | 7.1% | 0.880 | -2.86 | +2.37 | +0.00 | 0.1430 |
| 4 | [1, 2, 3, 4, 7, 12] | 39 | 34 | 10.9% | 0.872 | -1.25 | +2.24 | +0.64 | 0.1650 |
| 5 | [1, 2, 4, 5, 6, 24] | 41 | 34 | 10.9% | 0.829 | -1.25 | +1.54 | +0.46 | 0.9020 |
| 6 | [1, 2, 4, 5, 6, 12, 24] | 51 | 40 | 12.9% | 0.784 | -0.45 | +0.81 | +0.28 | 1.0000 |
| 7 | [1, 2, 6, 7, 8, 48] | 39 | 34 | 10.9% | 0.872 | -1.25 | +2.24 | +0.64 | 0.1650 |
| 8 | [1, 4, 6, 8, 15, 48] | 52 | 41 | 13.2% | 0.788 | -0.32 | +0.88 | +0.37 | 1.0000 |
| 9 | [1, 3, 6, 9, 13, 72] | 50 | 41 | 13.2% | 0.820 | -0.32 | +1.39 | +0.75 | 1.0000 |
| 10 | [1, 4, 7, 10, 18, 72] | 52 | 42 | 13.5% | 0.808 | -0.19 | +1.19 | +0.65 | 1.0000 |
| 11 | [1, 2, 10, 11, 12, 120] | 41 | 32 | 10.3% | 0.780 | -1.52 | +0.75 | -0.20 | 1.0000 |
| 12 | [1, 4, 6, 7, 12, 28, 96] | 66 | 48 | 15.4% | 0.727 | +0.62 | -0.12 | +0.06 | 1.0000 |

## Special sets

| set | reach | hits | z_eff |
|-----|-------|------|-------|
| primes | 67 | 44 | -1.27 |
| fib | 41 | 32 | +0.75 |
| pow2 | 49 | 42 | +2.00 |

## Origin stats

| origin | targets | unique | n6_hits | rate |
|--------|---------|--------|---------|------|
| convention | 272 | 48 | 244 | 89.7% |
| derived | 3 | 3 | 1 | 33.3% |
| engineering | 158 | 84 | 94 | 59.5% |
| natural | 1555 | 311 | 1049 | 67.5% |

## Verdict

- **best z = +0.809**
- **z>3: NO**
- n=6 eff rank: 9/11
- p_bonf: 1.0000
- prev best z_eff=2.03 vs current +0.809

## z>3 gap analysis

n=6 reach=51, natural targets=1555, all=1988

### Cause 1: reach size bias
n=6 constants max=24, random 1-30 similar range -> high overlap.

### Cause 2: target distribution
targets<=24: 960/1555 (61.7%)
Small integers dominate -> all small-number sets perform well.

### Cause 3: 2-op limit
6 ops x 49 pairs -> ~51 unique reach. Limited discrimination.

### Cause 4: multiple comparisons
n=2..12 (11 candidates) -> Bonferroni: p_adj = p*11
z=2.03->p=0.021->p_adj=0.23 (not significant after correction).

### Solutions
1. 3-op extension: (a op b) op c
2. Match random range to max(constants)
3. Use unique targets only (deduplicated)
4. Filter STRUCTURAL/CAUSAL only (exclude CONVENTION)
5. Combined z_eff + z_size_matched metric