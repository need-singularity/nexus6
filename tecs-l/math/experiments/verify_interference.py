"""
H-GEO-10: Multi-Lens Interference System Verification
======================================================
Verifies the hypothesis that R(n) = sopfr(n)/Omega(n) density distribution
shows interference-like fringes, with perfect numbers acting as optical lenses.

R(n) = sopfr(n) / Omega(n)
  sopfr(n) = sum of prime factors with repetition
  Omega(n) = number of prime factors with multiplicity

Perfect numbers as lenses:
  P1 = 6  -> R(6) = (2+3)/2 = 2.5
  P2 = 28 -> R(28) = (2+2+7)/3 = 11/3 ≈ 3.667
  P3 = 496 -> R(496) = (2+2+2+2+31)/5 = 39/5 = 7.8

Predicted: fringes at M≈2 between P1-P2, spacing delta+(6) = 1/4
"""

import sys
import math
import numpy as np
from collections import Counter

print("=" * 70)
print("H-GEO-10: Multi-Lens Interference System Verification")
print("=" * 70)
print()

# ─────────────────────────────────────────────────────────────────────────────
# Helper: sopfr and Omega via trial division (fast, avoids sympy overhead)
# ─────────────────────────────────────────────────────────────────────────────

def factorize(n):
    """Return prime factorization as list of primes (with repetition)."""
    factors = []
    d = 2
    while d * d <= n:
        while n % d == 0:
            factors.append(d)
            n //= d
        d += 1
    if n > 1:
        factors.append(n)
    return factors

def R(n):
    """R(n) = sopfr(n) / Omega(n).  Returns None for n=1 (no prime factors)."""
    if n <= 1:
        return None
    factors = factorize(n)
    return sum(factors) / len(factors)

# ─────────────────────────────────────────────────────────────────────────────
# Section 0: Perfect-number lens values
# ─────────────────────────────────────────────────────────────────────────────
perfect_numbers = [6, 28, 496, 8128]
R_perfect = {}
for p in perfect_numbers:
    r = R(p)
    R_perfect[p] = r
    factors = factorize(p)
    print(f"  R({p}) = sopfr/Omega = {sum(factors)}/{len(factors)} = {r:.6f}")
    print(f"    factors: {factors}")

R_P1 = R_perfect[6]    # 2.5
R_P2 = R_perfect[28]   # ~3.6667
R_P3 = R_perfect[496]  # 7.8

print()
print(f"  R(P2) - R(P1) = {R_P2 - R_P1:.6f}")
print(f"  R(P3) - R(P2) = {R_P3 - R_P2:.6f}")
print(f"  R(P3) - R(P1) = {R_P3 - R_P1:.6f}")
print()

# ─────────────────────────────────────────────────────────────────────────────
# Section 1: Compute R(n) for n = 2..50000
# ─────────────────────────────────────────────────────────────────────────────
N_MAX = 50000
print(f"Computing R(n) for n=2..{N_MAX}  (this may take ~30s) ...")
R_values = []
for n in range(2, N_MAX + 1):
    r = R(n)
    if r is not None:
        R_values.append(r)

R_arr = np.array(R_values)
print(f"  Total values: {len(R_arr)}")
print(f"  Min R: {R_arr.min():.4f}  Max R: {R_arr.max():.4f}")
print(f"  Mean: {R_arr.mean():.4f}  Std: {R_arr.std():.4f}")
print()

# ─────────────────────────────────────────────────────────────────────────────
# Section 2: Histogram (1000 bins, range [0, 10])
# ─────────────────────────────────────────────────────────────────────────────
print("=" * 70)
print("SECTION 1: R Density Distribution — Histogram")
print("=" * 70)

BINS = 1000
HIST_RANGE = (0, 10)
counts, bin_edges = np.histogram(R_arr, bins=BINS, range=HIST_RANGE)
bin_centers = 0.5 * (bin_edges[:-1] + bin_edges[1:])
bin_width = bin_edges[1] - bin_edges[0]  # 0.01

print(f"\nHistogram: {BINS} bins in range {HIST_RANGE}, bin_width={bin_width:.4f}")
print()

# Show top-20 most dense bins
sorted_idx = np.argsort(counts)[::-1]
print("| Rank | R center | Count | Note |")
print("|------|----------|-------|------|")
notes = {
    R_P1: "R(P1=6)",
    R_P2: "R(P2=28)",
    R_P3: "R(P3=496)",
}
for rank, idx in enumerate(sorted_idx[:20], 1):
    rc = bin_centers[idx]
    note = ""
    for rv, label in notes.items():
        if abs(rc - rv) < 0.02:
            note = label
    print(f"| {rank:4d} | {rc:8.4f} | {counts[idx]:5d} | {note} |")

# ASCII histogram for R in [2, 8]
print()
print("ASCII Histogram of R density (R in [2.0, 8.0]):")
mask = (bin_centers >= 2.0) & (bin_centers <= 8.0)
sub_centers = bin_centers[mask]
sub_counts = counts[mask]
max_count = sub_counts.max()
bar_width = 40
print(f"  (max count per bin = {max_count})")
# Sample every 10th bin for readability
for i in range(0, len(sub_centers), 10):
    rc = sub_centers[i]
    c = sub_counts[i]
    bar_len = int(bar_width * c / max_count)
    bar = "#" * bar_len
    # Mark lens positions
    mark = ""
    if abs(rc - R_P1) < 0.06: mark = " <-- R(P1)"
    elif abs(rc - R_P2) < 0.06: mark = " <-- R(P2)"
    elif abs(rc - R_P3) < 0.06: mark = " <-- R(P3)"
    print(f"  R={rc:.2f} | {bar:<40s} | {c:4d}{mark}")

print()

# ─────────────────────────────────────────────────────────────────────────────
# Section 3: FFT of R density
# ─────────────────────────────────────────────────────────────────────────────
print("=" * 70)
print("SECTION 2: FFT of R Density Histogram")
print("=" * 70)
print()

# Use full histogram counts (BINS=1000 bins over [0,10])
fft_input = counts.astype(float)
fft_result = np.fft.fft(fft_input)
fft_mag = np.abs(fft_result)
freqs = np.fft.fftfreq(BINS, d=bin_width)  # cycles per unit of R

# Only positive frequencies
pos_mask = freqs > 0
pos_freqs = freqs[pos_mask]
pos_mag = fft_mag[pos_mask]

# Find dominant frequencies (top 20)
sorted_fft = np.argsort(pos_mag)[::-1]

print("Dominant FFT frequencies in R density (positive freqs only):")
print(f"  DC component (freq=0) magnitude: {fft_mag[0]:.2f}")
print()
print("| Rank | Frequency (cycles/R) | Period (R units) | Magnitude | Predicted? |")
print("|------|---------------------|-----------------|-----------|------------|")

# Predicted interference frequencies from hypothesis
# delta+(6) = 1/4 = 0.25  -> frequency = 1/0.25 = 4 cycles per R unit
# R(P2)-R(P1) = 11/3 - 5/2 = 22/6 - 15/6 = 7/6 ≈ 1.1667 -> freq ≈ 0.857
# M=2 fringes between P1-P2 -> spacing ≈ (7/6)/2 ≈ 0.583 -> freq ≈ 1.714
# slit spacing / wavelength -> check for harmonics of freq=4

predicted_freqs = {
    4.0: "delta+(6)=1/4 fundamental",
    8.0: "2nd harmonic",
    12.0: "3rd harmonic",
    0.857: "(P2-P1) spacing",
    1.714: "M=2 fringe",
    3.428: "M=4 fringe",
    2.0: "1/2 period",
}

for rank, idx in enumerate(sorted_fft[:20], 1):
    f = pos_freqs[idx]
    period = 1.0 / f if f > 0 else float('inf')
    mag = pos_mag[idx]
    # Check if near a predicted frequency
    pred = ""
    for pf, label in predicted_freqs.items():
        if abs(f - pf) / pf < 0.05:  # within 5%
            pred = label
            break
    print(f"| {rank:4d} | {f:19.4f} | {period:15.4f} | {mag:9.2f} | {pred} |")

print()

# Check specifically for the predicted frequencies
print("Targeted check for predicted interference frequencies:")
print()
print("| Predicted freq | Label | Nearest actual freq | Magnitude | Ratio |")
print("|---------------|-------|--------------------|-----------|----|")
for pf, label in sorted(predicted_freqs.items()):
    # Find nearest freq in FFT
    nearest_idx = np.argmin(np.abs(pos_freqs - pf))
    nearest_f = pos_freqs[nearest_idx]
    nearest_mag = pos_mag[nearest_idx]
    ratio = nearest_f / pf if pf > 0 else float('nan')
    print(f"| {pf:13.4f} | {label[:30]:30s} | {nearest_f:18.4f} | {nearest_mag:9.2f} | {ratio:.4f} |")

print()

# ─────────────────────────────────────────────────────────────────────────────
# Section 4: Density between perfect number lenses
# ─────────────────────────────────────────────────────────────────────────────
print("=" * 70)
print("SECTION 3: Density Between Perfect Number Lenses")
print("=" * 70)
print()

# Count R values in intervals [R(Pi) ± 0.5]
print("R(n) count in [R(Pi) ± 0.5] windows:")
print()
print("| Perfect Number Pi | R(Pi) | [R(Pi)-0.5, R(Pi)+0.5] | Count | Density |")
print("|------------------|-------|------------------------|-------|---------|")
total_n = len(R_arr)
for p in perfect_numbers:
    rp = R_perfect[p]
    lo, hi = rp - 0.5, rp + 0.5
    cnt = np.sum((R_arr >= lo) & (R_arr < hi))
    density = cnt / (total_n * 1.0)  # fraction of all values
    print(f"| P={p:5d}           | {rp:.4f} | [{lo:.4f}, {hi:.4f}]     | {cnt:5d} | {density:.4f} |")

print()

# Local density at each 0.1 interval from R(P1) to R(P2)
print(f"Local density at 0.1 intervals between R(P1)={R_P1:.4f} and R(P2)={R_P2:.4f}:")
print()
interval_start = math.floor(R_P1 * 10) / 10  # 2.5
interval_end = math.ceil(R_P2 * 10) / 10     # 3.7

intervals = np.arange(interval_start, interval_end + 0.1, 0.1)

print("| Interval [lo, lo+0.1) | Count | Density | ASCII bar |")
print("|----------------------|-------|---------|-----------|")
interval_counts = []
for lo in intervals:
    hi = lo + 0.1
    cnt = np.sum((R_arr >= lo) & (R_arr < hi))
    interval_counts.append(cnt)

max_ic = max(interval_counts) if interval_counts else 1
for lo, cnt in zip(intervals, interval_counts):
    hi = lo + 0.1
    density = cnt / (total_n * 0.1)
    bar_len = int(20 * cnt / max_ic)
    bar = "#" * bar_len
    # Mark lens positions
    mark = ""
    if abs(lo - R_P1) < 0.15:
        mark = " <-R(P1)"
    elif abs(lo - R_P2) < 0.15:
        mark = " <-R(P2)"
    print(f"| [{lo:.1f}, {hi:.1f})             | {cnt:5d} | {density:.4f}  | {bar:<20s}{mark} |")

print()

# Extend to R(P3) to check for periodic fringes
print(f"Local density (0.1 intervals) between R(P1)={R_P1:.4f} and R(P3)={R_P3:.4f}:")
print()
intervals_full = np.arange(2.0, R_P3 + 0.1, 0.1)
full_counts = []
for lo in intervals_full:
    hi = lo + 0.1
    cnt = np.sum((R_arr >= lo) & (R_arr < hi))
    full_counts.append(cnt)

max_fc = max(full_counts) if full_counts else 1
print("| R range    | Count | Bar (scaled) |")
print("|------------|-------|--------------|")
for lo, cnt in zip(intervals_full, full_counts):
    hi = lo + 0.1
    bar_len = int(30 * cnt / max_fc)
    bar = "#" * bar_len
    mark = ""
    if abs(lo - R_P1) < 0.06: mark = " P1"
    elif abs(lo - R_P2) < 0.06: mark = " P2"
    elif abs(lo - R_P3) < 0.06: mark = " P3"
    print(f"| [{lo:.1f},{hi:.1f}) | {cnt:5d} | {bar:<30s}{mark} |")

print()

# Fringe analysis: check for periodicity in the density pattern
print("Fringe analysis (auto-correlation of density in [2.0, R(P3)+1.0]):")
print()
# Compute density array for range [2.0, 9.0] at 0.1 resolution
lo_range = 2.0
hi_range = 9.0
step = 0.1
bins_fine = np.arange(lo_range, hi_range, step)
fine_counts = np.array([
    np.sum((R_arr >= lo) & (R_arr < lo + step))
    for lo in bins_fine
])

# Auto-correlation
fine_centered = fine_counts - fine_counts.mean()
autocorr = np.correlate(fine_centered, fine_centered, mode='full')
autocorr = autocorr[len(autocorr)//2:]  # keep lags >= 0
autocorr_norm = autocorr / autocorr[0]

print("Auto-correlation of density (lag in units of 0.1 R):")
print()
print("| Lag (R units) | Auto-corr | Bar |")
print("|--------------|-----------|-----|")
for lag_idx in range(0, min(40, len(autocorr_norm))):
    lag_r = lag_idx * step
    ac = autocorr_norm[lag_idx]
    bar_len = int(20 * max(ac, 0))
    bar = "#" * bar_len
    if lag_idx == 0:
        bar = "(self)"
    mark = ""
    # check if lag corresponds to predicted fringe spacing
    # Predicted fringe spacing from M=2 between P1-P2: (R_P2-R_P1)/2 ≈ 0.583
    fringe_spacing = (R_P2 - R_P1) / 2
    if abs(lag_r - fringe_spacing) < 0.06:
        mark = f" <-- predicted M=2 fringe ({fringe_spacing:.3f})"
    elif abs(lag_r - (R_P2 - R_P1)) < 0.06:
        mark = f" <-- P2-P1 spacing ({R_P2 - R_P1:.3f})"
    elif abs(lag_r - 0.25) < 0.06:
        mark = " <-- delta+(6)=1/4"
    print(f"| {lag_r:12.2f} | {ac:9.4f} | {bar:<20s}{mark} |")

print()

# ─────────────────────────────────────────────────────────────────────────────
# Section 5: Resonance Verification
# ─────────────────────────────────────────────────────────────────────────────
print("=" * 70)
print("SECTION 4: Resonance Verification")
print("=" * 70)
print()

# Exact fractions
# R(6) = (2+3)/2 = 5/2
# R(28) = (2+2+7)/3 = 11/3
# R(496) = (2+2+2+2+31)/5 = 39/5
# R(8128) = factors of 8128?

factors_8128 = factorize(8128)
print(f"8128 factors: {factors_8128}")
R_8128 = sum(factors_8128) / len(factors_8128)
print(f"R(8128) = {sum(factors_8128)}/{len(factors_8128)} = {R_8128:.6f}")
print()

from fractions import Fraction
R_P1_frac = Fraction(5, 2)
R_P2_frac = Fraction(11, 3)
R_P3_frac = Fraction(39, 5)

diff_P2_P1 = R_P2_frac - R_P1_frac
diff_P3_P2 = R_P3_frac - R_P2_frac
diff_P3_P1 = R_P3_frac - R_P1_frac

print(f"Exact fractions:")
print(f"  R(P1) = {R_P1_frac} = {float(R_P1_frac):.6f}")
print(f"  R(P2) = {R_P2_frac} = {float(R_P2_frac):.6f}")
print(f"  R(P3) = {R_P3_frac} = {float(R_P3_frac):.6f}")
print()
print(f"  R(P2) - R(P1) = {diff_P2_P1} = {float(diff_P2_P1):.6f}")
print(f"  R(P3) - R(P2) = {diff_P3_P2} = {float(diff_P3_P2):.6f}")
print(f"  R(P3) - R(P1) = {diff_P3_P1} = {float(diff_P3_P1):.6f}")
print()

# Check: R(P2)-R(P1) = 3 = 12*(1/4)?
print("Resonance checks:")
print()
delta_plus_6 = Fraction(1, 4)  # hypothesis: delta+(6) = 1/4

check1_val = diff_P2_P1
check1_div = check1_val / delta_plus_6
print(f"  Check 1: R(P2)-R(P1) = {check1_val} = {float(check1_val):.6f}")
print(f"    / delta+(6)={delta_plus_6} = {check1_div} = {float(check1_div):.4f}")
print(f"    Is integer multiple of 1/4? {check1_div.denominator == 1}")
print(f"    Value = {float(check1_val):.4f}, predicted '= 3'? {abs(float(check1_val)-3) < 0.001}")
print(f"    Value = {float(check1_val):.4f}, predicted '= 12*(1/4)=3'? {abs(float(check1_val) - 3) < 0.001}")
print()

check2_val = diff_P3_P2
check2_div = check2_val / delta_plus_6
print(f"  Check 2: R(P3)-R(P2) = {check2_val} = {float(check2_val):.6f}")
print(f"    / delta+(6)={delta_plus_6} = {check2_div} = {float(check2_div):.4f}")
print(f"    Is integer multiple of 1/4? {check2_div.denominator == 1}")
print(f"    Value = {float(check2_val):.4f}, predicted '= 44 = 176*(1/4)'? {abs(float(check2_val)-44) < 0.001}")
print()

# Actual values
print("  Summary table:")
print()
print("| Gap | Exact fraction | Decimal | / delta+(6) | Integer mult? | Predicted? |")
print("|-----|---------------|---------|-------------|--------------|------------|")
gaps = [
    ("P2-P1", diff_P2_P1),
    ("P3-P2", diff_P3_P2),
    ("P3-P1", diff_P3_P1),
]
for label, gap in gaps:
    div = gap / delta_plus_6
    is_int = div.denominator == 1
    print(f"| {label} | {gap} | {float(gap):.4f} | {div} = {float(div):.4f} | {is_int} | - |")

print()

# Is 1/4 = delta+(6) a fundamental wavelength?
# Check: is R(P2)-R(P1) expressible as simple multiple of 1/4?
print("Fundamental wavelength analysis (delta+(6)=1/4):")
print()
ratio_12 = diff_P2_P1 / delta_plus_6
ratio_23 = diff_P3_P2 / delta_plus_6
print(f"  (R(P2)-R(P1)) / (1/4) = {ratio_12} = {float(ratio_12):.4f}")
print(f"  (R(P3)-R(P2)) / (1/4) = {ratio_23} = {float(ratio_23):.4f}")
print()

# Alternative: check with other "fundamental" values
print("Alternative fundamental candidates:")
print()
candidates = {
    "1/6 (curiosity)": Fraction(1, 6),
    "1/4 (delta+)": Fraction(1, 4),
    "1/3 (meta FP)": Fraction(1, 3),
    "1/2 (Riemann)": Fraction(1, 2),
    "ln(4/3) ≈ 0.2877": None,  # irrational, handle separately
    "7/6 (P2-P1)": diff_P2_P1,
}
print("| Fundamental lambda | R(P2)-R(P1) / lambda | R(P3)-R(P2) / lambda |")
print("|-------------------|---------------------|---------------------|")
for name, lam in candidates.items():
    if lam is None:
        lam_f = math.log(4/3)
        r1 = float(diff_P2_P1) / lam_f
        r2 = float(diff_P3_P2) / lam_f
        print(f"| {name:18s} | {r1:19.4f} | {r2:19.4f} |")
    else:
        r1 = diff_P2_P1 / lam
        r2 = diff_P3_P2 / lam
        print(f"| {name:18s} | {r1} = {float(r1):8.4f} | {r2} = {float(r2):8.4f} |")

print()

# ─────────────────────────────────────────────────────────────────────────────
# Section 6: Interference Intensity Matrix
# ─────────────────────────────────────────────────────────────────────────────
print("=" * 70)
print("SECTION 5: Interference Intensity Matrix")
print("=" * 70)
print()
print("I(Pi, Pj) = 1 / (R(Pj) - R(Pi))  for i < j")
print()

perf_list = [(6, R_P1_frac), (28, R_P2_frac), (496, R_P3_frac)]
labels = ["P1=6", "P2=28", "P3=496"]

print("| Source \\ Target |", " | ".join(labels), "|")
print("|" + "---|" * (len(labels)+1))

for i, (pi, ri) in enumerate(perf_list):
    row_cells = [f"**{labels[i]}**"]
    for j, (pj, rj) in enumerate(perf_list):
        if i == j:
            row_cells.append("---")
        elif i < j:
            diff = rj - ri
            intensity = Fraction(1, 1) / diff
            row_cells.append(f"{intensity} = {float(intensity):.4f}")
        else:
            diff = ri - rj
            intensity = Fraction(1, 1) / diff
            row_cells.append(f"-{intensity} = {-float(intensity):.4f}")
    print("| " + " | ".join(row_cells) + " |")

print()

# Numerical intensity matrix
print("Numerical intensity matrix (absolute values):")
print()
print("| i\\j |", " | ".join([f"R({p})={float(r):.4f}" for p, r in perf_list]), "|")
print("|-----|" + "------|" * len(perf_list))

for i, (pi, ri) in enumerate(perf_list):
    row_cells = [f"R({pi})={float(ri):.4f}"]
    for j, (pj, rj) in enumerate(perf_list):
        if i == j:
            row_cells.append("  ∞   ")
        else:
            diff = abs(float(rj) - float(ri))
            intensity = 1.0 / diff
            row_cells.append(f"{intensity:6.4f}")
    print("| " + " | ".join(row_cells) + " |")

print()

# Commentary: which pair shows strongest interference (highest intensity)?
intensities = []
for i, (pi, ri) in enumerate(perf_list):
    for j, (pj, rj) in enumerate(perf_list):
        if i < j:
            diff = abs(float(rj) - float(ri))
            intensities.append((pi, pj, float(ri), float(rj), diff, 1.0/diff))

intensities.sort(key=lambda x: x[5], reverse=True)
print("Pair intensities (sorted by intensity):")
print()
print("| P_i | P_j | R(Pi) | R(Pj) | |R(Pj)-R(Pi)| | Intensity I |")
print("|-----|-----|-------|-------|--------------|-------------|")
for pi, pj, ri, rj, diff, intensity in intensities:
    print(f"| {pi:4d} | {pj:4d} | {ri:.4f} | {rj:.4f} | {diff:.4f}       | {intensity:.4f}     |")

print()

# ─────────────────────────────────────────────────────────────────────────────
# Section 7: Summary and Verdict
# ─────────────────────────────────────────────────────────────────────────────
print("=" * 70)
print("SECTION 6: Summary and Verdict")
print("=" * 70)
print()

print("| Claim | Predicted Value | Actual Value | Match? |")
print("|-------|----------------|-------------|--------|")

# Claim 1: R(P2)-R(P1) = 7/6
actual_diff_12 = float(diff_P2_P1)
print(f"| R(P2)-R(P1) | 7/6 ≈ 1.1667 | {actual_diff_12:.6f} | {abs(actual_diff_12 - 7/6) < 0.0001} |")

# Claim 2: R(P3)-R(P2) = 172/15
actual_diff_23 = float(diff_P3_P2)
pred_diff_23 = float(Fraction(39,5) - Fraction(11,3))
print(f"| R(P3)-R(P2) | {diff_P3_P2} ≈ {pred_diff_23:.4f} | {actual_diff_23:.6f} | {abs(actual_diff_23 - pred_diff_23) < 0.0001} |")

# Claim 3: R(P2)-R(P1) = 3 (from hypothesis text)
print(f"| R(P2)-R(P1) = 3 (hypothesis) | 3 | {actual_diff_12:.6f} | {abs(actual_diff_12 - 3) < 0.001} |")

# Claim 4: R(P3)-R(P2) = 44 (from hypothesis text)
print(f"| R(P3)-R(P2) = 44 (hypothesis) | 44 | {actual_diff_23:.6f} | {abs(actual_diff_23 - 44) < 0.001} |")

# Claim 5: (R(P2)-R(P1)) / (1/4) is integer
div_12 = diff_P2_P1 / delta_plus_6
is_int_12 = div_12.denominator == 1
print(f"| (P2-P1)/delta+ integer | True | {div_12} (denom={div_12.denominator}) | {is_int_12} |")

# Claim 6: (R(P3)-R(P2)) / (1/4) is integer
div_23 = diff_P3_P2 / delta_plus_6
is_int_23 = div_23.denominator == 1
print(f"| (P3-P2)/delta+ integer | True | {div_23} (denom={div_23.denominator}) | {is_int_23} |")

print()
print("Key exact fractions:")
print(f"  R(P1=6)   = 5/2 = {float(R_P1_frac):.6f}")
print(f"  R(P2=28)  = 11/3 = {float(R_P2_frac):.6f}")
print(f"  R(P3=496) = 39/5 = {float(R_P3_frac):.6f}")
print()
print(f"  R(P2)-R(P1) = 11/3 - 5/2 = {diff_P2_P1} = {float(diff_P2_P1):.6f}")
print(f"  R(P3)-R(P2) = 39/5 - 11/3 = {diff_P3_P2} = {float(diff_P3_P2):.6f}")
print(f"  R(P3)-R(P1) = 39/5 - 5/2 = {diff_P3_P1} = {float(diff_P3_P1):.6f}")
print()
print(f"  delta+(6) = 1/4 = {float(delta_plus_6):.6f}")
print(f"  (P2-P1) / delta+ = {div_12} = {float(div_12):.6f}")
print(f"  (P3-P2) / delta+ = {div_23} = {float(div_23):.6f}")
print()

# Final verdict
print("VERDICT:")
if abs(actual_diff_12 - 3) < 0.001:
    print("  [CONFIRMED] R(P2)-R(P1) = 3")
else:
    print(f"  [REFUTED] R(P2)-R(P1) != 3 (actual: {actual_diff_12:.6f} = {diff_P2_P1})")

if abs(actual_diff_23 - 44) < 0.001:
    print("  [CONFIRMED] R(P3)-R(P2) = 44")
else:
    print(f"  [REFUTED] R(P3)-R(P2) != 44 (actual: {actual_diff_23:.6f} = {diff_P3_P2})")

if is_int_12:
    print(f"  [CONFIRMED] (P2-P1)/delta+ = {div_12} is an integer")
else:
    print(f"  [PARTIAL] (P2-P1)/delta+ = {div_12} is not an integer (denom={div_12.denominator})")

if is_int_23:
    print(f"  [CONFIRMED] (P3-P2)/delta+ = {div_23} is an integer")
else:
    print(f"  [PARTIAL] (P3-P2)/delta+ = {div_23} is not an integer (denom={div_23.denominator})")

print()
print("Done.")
