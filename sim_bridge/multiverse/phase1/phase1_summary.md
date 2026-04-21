# NEXUS-6 ★18 Quantum Multiverse Interferometer Phase 1 — 20260416_031005

## Config
- M=15 universes, T=500 steps, dim=48, N_trial=10
- pairs/trial = 105
- total pairs pooled (per source × estimator) = 1050
- bytes/seed = 8220 (0.16 MB total)
- ANU source: first 64 bytes ANU QRNG per trial, rest urandom-extended
- theoretical finite-sample bias: plug-in 4-bin (B-1)/(2T) = 0.00300, ksg-lite 8-bin Miller-Madow corrected (residual ~0.00700)

## Phase 0 vs Phase 1
| metric | Phase 0 | Phase 1 |
|--------|---------|---------|
| M | 10 | 15 |
| T | 200 | 500 |
| dim | 64 | 48 |
| trials | 1 | 10 |
| pairs total | 45 | 1050 |
| plug-in bias (theor) | 0.0075 | 0.00300 |
| single KS p | 0.218 | 0.9920 (pooled plug-in) |

## Fisher combined p-values (N=10 trial KS p's)
| estimator | Fisher X² (scaled) | df | Fisher p (scaled) | Fisher p |
|-----------|--------------------|----|-------------------|----------|
| plug-in | 1936 | 20 | 1000 | 1.000000 |
| ksg-lite | 6520 | 20 | 999 | 0.999000 |

## Pooled KS (single large-sample test on all 1050 pairs)
| estimator | D | λ | p (scaled) | p |
|-----------|---|---|------------|---|
| plug-in | 0.0190 | 0.4350 | 992 | 0.9920 |
| ksg-lite | 0.0290 | 0.6640 | 778 | 0.7780 |

## Distribution statistics (pooled, scaled ×1000)

```json
{
  "anu_pool_plugin": {
    "n": 1050,
    "mean_scaled": 6.5,
    "std_scaled": 3.9,
    "skew": 0.9335,
    "min": -2,
    "max": 23
  },
  "prng_pool_plugin": {
    "n": 1050,
    "mean_scaled": 6.5,
    "std_scaled": 3.7,
    "skew": 0.8183,
    "min": -2,
    "max": 24
  },
  "anu_pool_ksg": {
    "n": 1050,
    "mean_scaled": -23.0,
    "std_scaled": 6.9,
    "skew": 0.8844,
    "min": -43,
    "max": 15
  },
  "prng_pool_ksg": {
    "n": 1050,
    "mean_scaled": -23.0,
    "std_scaled": 7.3,
    "skew": 1.1072,
    "min": -40,
    "max": 22
  }
}
```

## Interpretation
- Fisher(plug-in, N=10): p=1.0000 -> H0 maintain (noise)
- Fisher(ksg-lite, N=10): p=0.9990 -> H0 maintain (noise)
- Pooled KS(plug-in): p=0.9920 -> H0 maintain (noise)
- Pooled KS(ksg-lite): p=0.7780 -> H0 maintain (noise)

## Next phase recommendation
- Noise level. Phase 2: dynamic quantile binning (remove static 4-bin artifact), true KSG k-NN, M=200 T=10000 hetzner.

## 출력 파일
- `trials.jsonl` — per-trial KS 결과 (20 lines: N_trial × 2 estimators)
- `trial_stats.jsonl` — per-trial source stats (20 lines: N_trial × {anu,prng})
- `mi_distributions.csv` — all pairwise MI values (trial,source,estimator,value)
- `fisher_plugin.json`, `fisher_ksg.json` — Fisher 합성 p-value
- `pooled_ks_plugin.jsonl`, `pooled_ks_ksg.jsonl` — 풀드 KS 결과
- `dist_stats.json` — 풀 분포 통계 (mean/std/skew/min/max)
- `anu_pool_*.txt`, `prng_pool_*.txt` — 풀드 raw 값
- `trials/trial_<i>_<tag>_<est>.txt` — 각 trial MI 벡터
- `seeds/trial_<i>_<tag>.txt` — 각 trial seed (debugging/reproducibility)

## 제약 (honest)
- ANU 64-byte head-seed only (rate-limit 회피). "ANU vs PRNG" 실질은 "ANU-head+urandom-tail vs urandom-full".
- ksg-lite 는 rank-based 8-bin + Miller-Madow 보정 (참 KSG k-NN 아님). bias 특성은 plug-in 과 다르지만 완전 독립 validation 은 아님.
- N_trial=10 에서 Fisher 민감도 ~ 0.316, single KS 대비 3.2 배 gain.
- 메모리: 각 trial M × T = 7500 energy samples, 피크 <200MB.

## 실행시간
- 총 elapsed: 482s
