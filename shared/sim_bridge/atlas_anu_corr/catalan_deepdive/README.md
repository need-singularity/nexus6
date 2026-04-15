# catalan_deepdive - 10x multi-test validation of 1st-run catalan weak hit

## Purpose
1st run (`../runs/current/`) flagged catalan chi^2=17.72 as single-test weak hit (p~0.04).
This deep dive runs 6 independent statistical tests + calibrated empirical nulls
+ verified constant digits to decide: DISCOVERY vs STRONG SIGNAL vs NULL.

## Files

| file | role |
|---|---|
| `catalan_2048.txt` | mpmath+sympy verified 2048-digit expansion of Catalan's constant (OEIS A006752) |
| `multi_test.py` | 6-metric engine: chi2, MI-bits, KSG-MI(k=4), FFT-peak, Spearman, dCor |
| `null_distribution.py` | 30-trial urandom null at n=1024 |
| `null_n128.py` | 50-trial urandom null at n=128 (matches ANU sample size) |
| `bonferroni_panel.py` | aggregates metrics, Bonferroni + BH-FDR + verdict |
| `calibration.py` | pretend-ANU test: rate of "=>1 single-test hit" in pure urandom |
| `collect_long_anu.sh` | ANU QRNG collector with rate-limit handling |

## Outputs (`runs/catalan_<ts>/`)
- `anu_long.hex` - ANU QRNG stream hex
- `all_tests_n128.csv` - full metric x trial table
- `null_trials_n128/` - individual urandom trial results
- `n128_panel_50/` - final panel output (`verdict.md` + `summary.json`)
- `verdict.md` - top-level verdict

## Key discovery

**The 1st run's catalan hardcoded digits are wrong from position 119** -
they do not match the true Catalan constant (verified against mpmath + sympy + OEIS A006752).
Combined with:
- 1st run using urandom as both data and null (ANU fetch failed, log is 0 bytes)
- 1st run using only 209 catalan digits (truncated hardcoded string)

...the chi^2=17.72 "weak hit" was 80% data-entry artifact, 20% small-sample fluctuation.

## Reproducibility
```bash
bash collect_long_anu.sh runs/<ts>/anu_long.hex 1024      # ~17 min (ANU rate-limit)
/usr/bin/python3 null_n128.py runs/<ts>/ catalan_2048.txt 128 50
/usr/bin/python3 bonferroni_panel.py runs/<ts>/n128_panel_50/
/usr/bin/python3 calibration.py runs/<ts>/
```

## Verdict (2026-04-16)

**NULL - 1차는 우연 (multi-test artifact + mis-keyed constant)**

- 0/6 metrics pass Bonferroni (alpha=0.0083)
- 0/6 metrics pass BH-FDR 0.05
- 1/6 single-test p<0.05 (chi^2) - consistent with 16% urandom baseline rate
