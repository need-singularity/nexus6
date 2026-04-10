#!/usr/bin/env python3
"""H-EE-14: FFT-Mix windows = inverse of GZ hierarchy widths?
   H-EE-15: 4/3 = exp(GZ_width) — FFN expansion ratio = exponential of info deficit

Verification:
  H-EE-14: Check if {6,12,24} windows can be derived from 1/GZ_width,
           test tau-based and sigma/phi-based derivations,
           and run Texas Sharpshooter test on window triples.
  H-EE-15: Verify exp(width) = expansion ratio interpretation,
           build table of P_n -> compression vs standard 4x FFN.
"""
import math
import numpy as np
from itertools import product as iproduct

np.random.seed(42)

SEPARATOR = "=" * 70

# ============================================================
# Perfect numbers and their GZ widths
# ============================================================
perfect_numbers = [6, 28, 496]
# GZ width for P_n: ln((P_n/3 + 1) / (P_n/3))...
# Actually from the project: width_k = ln((k+1)/k) for states
# For P1=6: ln(4/3), P2=28: ln(6/5), P3=496: ln(10/9)
# These come from: P_n has tau(P_n)/2 states
# tau(6)=4 -> 4/2=2? No. Let me use the given values directly.

# Given in hypothesis:
gz_params = [
    {"P": 6,   "ratio_num": 4,  "ratio_den": 3,  "label": "P1=6"},
    {"P": 28,  "ratio_num": 6,  "ratio_den": 5,  "label": "P2=28"},
    {"P": 496, "ratio_num": 10, "ratio_den": 9,  "label": "P3=496"},
]

target_windows = [6, 12, 24]

def sigma(n):
    """Sum of divisors."""
    s = 0
    for i in range(1, n + 1):
        if n % i == 0:
            s += i
    return s

def tau(n):
    """Number of divisors."""
    t = 0
    for i in range(1, n + 1):
        if n % i == 0:
            t += 1
    return t

def phi(n):
    """Euler totient."""
    count = 0
    for i in range(1, n + 1):
        if math.gcd(i, n) == 1:
            count += 1
    return count


print(SEPARATOR)
print("H-EE-14: FFT-Mix windows = inverse of GZ hierarchy widths?")
print(SEPARATOR)

# Step 1: Compute GZ widths and their inverses
print("\n--- Step 1: GZ widths and inverses ---\n")
print(f"{'P_n':>6} | {'ratio':>8} | {'width=ln(r)':>12} | {'1/width':>10} | {'nearest_win':>11} | {'ratio_to_win':>12}")
print("-" * 75)

widths = []
inv_widths = []
for g in gz_params:
    ratio = g["ratio_num"] / g["ratio_den"]
    width = math.log(ratio)
    inv_w = 1.0 / width
    # Find nearest window
    nearest = min(target_windows, key=lambda w: abs(w - inv_w))
    ratio_to_win = nearest / inv_w
    widths.append(width)
    inv_widths.append(inv_w)
    print(f"{g['P']:>6} | {g['ratio_num']}/{g['ratio_den']:>5} | {width:>12.6f} | {inv_w:>10.4f} | {nearest:>11} | {ratio_to_win:>12.4f}")

# Step 2: Check scaling factor
print("\n--- Step 2: Scaling factor analysis ---\n")
for i, g in enumerate(gz_params):
    for w in target_windows:
        sf = w / inv_widths[i]
        sqrt3 = math.sqrt(3)
        close_sqrt3 = abs(sf - sqrt3) / sqrt3 < 0.05
        print(f"  window={w:>2} / (1/width_{g['P']}) = {w}/{inv_widths[i]:.4f} = {sf:.4f}"
              f"  {'~= sqrt(3)=1.732' if close_sqrt3 else ''}")

# Step 3: tau-based derivation
print("\n--- Step 3: tau-based derivation ---\n")
print(f"{'P_n':>6} | {'tau(P)':>6} | {'sigma(P)':>8} | {'phi(P)':>6}")
print("-" * 40)
for g in gz_params:
    p = g["P"]
    t = tau(p)
    s = sigma(p)
    ph = phi(p)
    print(f"{p:>6} | {t:>6} | {s:>8} | {ph:>6}")

print()
print("Check: windows {6,12,24} = {tau(6)*1.5, tau(6)*3, tau(6)*6}?")
t6 = tau(6)
for w, factor in zip(target_windows, [1.5, 3.0, 6.0]):
    val = t6 * factor
    match = "YES" if abs(val - w) < 0.01 else "NO"
    print(f"  tau(6) * {factor} = {t6} * {factor} = {val:.1f} -> window {w}? {match}")

# Step 4: Known derivation from sigma and phi
print("\n--- Step 4: Known derivation {P1, sigma(P1), sigma(P1)*phi(P1)} ---\n")
p1 = 6
s1 = sigma(p1)  # 12 (since 6 is perfect, sigma=2*6=12)
ph1 = phi(p1)   # 2
derived = [p1, s1, s1 * ph1]
print(f"  P1 = {p1}")
print(f"  sigma(P1) = sigma({p1}) = {s1}")
print(f"  phi(P1) = phi({p1}) = {ph1}")
print(f"  sigma(P1) * phi(P1) = {s1} * {ph1} = {s1 * ph1}")
print(f"  Derived windows: {derived}")
print(f"  Target windows:  {target_windows}")
match = derived == target_windows
print(f"  MATCH: {match}")

# Step 5: Can we ALSO derive from GZ widths?
print("\n--- Step 5: GZ width derivation attempt ---\n")
print("Checking various transformations of 1/width to reach {6, 12, 24}:")
attempts = []
for label, func_name, func in [
    ("round(1/w)",           "round",      lambda w: round(1/w)),
    ("ceil(1/w)",            "ceil",       lambda w: math.ceil(1/w)),
    ("round(2/w)",           "2/w round",  lambda w: round(2/w)),
    ("round(sqrt(3)/w)",     "sqrt3/w",    lambda w: round(math.sqrt(3)/w)),
    ("round(pi/w)",          "pi/w",       lambda w: round(math.pi/w)),
    ("round(2*pi/w)",        "2pi/w",      lambda w: round(2*math.pi/w)),
    ("round(e/w)",           "e/w",        lambda w: round(math.e/w)),
    ("6*round(1/w)",         "6*round",    lambda w: 6*round(1/w)),
    ("2^round(log2(1/w)+1)", "pow2",       lambda w: 2**round(math.log2(1/w)+1)),
]:
    results = [func(w) for w in widths]
    match = results == target_windows
    attempts.append((label, results, match))
    flag = " <-- MATCH!" if match else ""
    print(f"  {label:>25}: {results}{flag}")

any_match = any(m for _, _, m in attempts)
if not any_match:
    print("\n  No simple transformation of 1/width reproduces {6, 12, 24} exactly.")
    print("  The GZ width -> window connection requires ad-hoc scaling.")

# Step 6: Texas Sharpshooter test
print("\n--- Step 6: Texas Sharpshooter test ---\n")
print("Among all window triples {a,b,c} with a in [3..10], b in [8..20], c in [15..40],")
print("how many have a 'nice' relationship to GZ widths (within 10%)?")
print()

def check_nice_relationship(a, b, c, inv_ws):
    """Check if {a,b,c} relates to inv_widths via a consistent scaling factor."""
    # Check: all windows = k * 1/width for some constant k
    ratios = [a/inv_ws[0], b/inv_ws[1], c/inv_ws[2]]
    # Check if ratios are consistent (within 10%)
    mean_r = np.mean(ratios)
    if mean_r == 0:
        return False
    max_dev = max(abs(r - mean_r)/mean_r for r in ratios)
    if max_dev < 0.10:
        return True

    # Check: windows = integer * 1/width (within 10%)
    for k in range(1, 8):
        vals = [k * iw for iw in inv_ws]
        devs = [abs(v - w) / w for v, w in zip(vals, [a, b, c])]
        if all(d < 0.10 for d in devs):
            return True

    # Check: windows are related by a consistent ratio to 1/width
    # e.g., w_i = f(1/width_i) for f = multiply by sqrt(3)
    for factor in [math.sqrt(2), math.sqrt(3), math.pi/2, math.e/2, 2.0]:
        vals = [factor * iw for iw in inv_ws]
        devs = [abs(v - w) / max(w, 0.01) for v, w in zip(vals, [a, b, c])]
        if all(d < 0.10 for d in devs):
            return True

    return False

total_triples = 0
nice_triples = 0
nice_examples = []
target_is_nice = False

for a in range(3, 11):
    for b in range(8, 21):
        for c in range(15, 41):
            if a < b < c:
                total_triples += 1
                is_nice = check_nice_relationship(a, b, c, inv_widths)
                if is_nice:
                    nice_triples += 1
                    if len(nice_examples) < 10:
                        nice_examples.append((a, b, c))
                    if (a, b, c) == (6, 12, 24):
                        target_is_nice = True

print(f"  Total valid triples: {total_triples}")
print(f"  Triples with 'nice' GZ relationship: {nice_triples}")
print(f"  Fraction: {nice_triples/total_triples:.4f}")
print(f"  {{6,12,24}} is nice: {target_is_nice}")
if nice_examples:
    print(f"  Examples of nice triples: {nice_examples[:5]}")

# p-value: fraction of triples that are nice
p_value = nice_triples / total_triples if total_triples > 0 else 1.0
print(f"\n  Texas p-value (fraction with similar relationship): {p_value:.4f}")
if p_value < 0.01:
    print("  -> p < 0.01: STRUCTURAL (reject null)")
elif p_value < 0.05:
    print("  -> p < 0.05: WEAK EVIDENCE")
else:
    print("  -> p > 0.05: NOT SPECIAL (coincidence likely)")

# H-EE-14 verdict
print(f"\n{'=' * 70}")
print("H-EE-14 VERDICT")
print("=" * 70)
print()
known_match = derived == target_windows
print(f"  Known derivation {{P1, sigma(P1), sigma(P1)*phi(P1)}} = {{6, 12, 24}}: {known_match}")
print(f"  GZ width derivation (1/width): {[round(iw, 2) for iw in inv_widths]} != {target_windows}")
print(f"  Any simple transform of 1/width -> windows: {any_match}")
print(f"  Texas p-value: {p_value:.4f}")
if not any_match and p_value > 0.05:
    print("\n  CONCLUSION: The GZ width -> FFT window connection is FORCED/AD-HOC.")
    print("  The known derivation via sigma/phi is the natural one.")
    print("  Grade: likely WHITE (arithmetically interesting but not structural)")
elif any_match:
    print("\n  CONCLUSION: A transform exists. Check if it's ad-hoc or principled.")
else:
    print("\n  CONCLUSION: Relationship exists but is weak.")


print(f"\n\n{'=' * 70}")
print("H-EE-15: 4/3 = exp(GZ_width) — FFN expansion as information deficit")
print("=" * 70)

# Step 1: Trivial verification
print("\n--- Step 1: exp(ln(4/3)) = 4/3 (definitional) ---\n")
val = math.exp(math.log(4/3))
print(f"  exp(ln(4/3)) = exp({math.log(4/3):.6f}) = {val:.10f}")
print(f"  4/3 = {4/3:.10f}")
print(f"  Difference: {abs(val - 4/3):.2e} (numerical precision)")
print(f"  This is TRIVIALLY TRUE by definition of ln/exp.")

# Step 2: Interpretation table
print("\n--- Step 2: FFN expansion ratio for each perfect number ---\n")
print(f"{'P_n':>6} | {'GZ_width':>10} | {'exp(w)=FFN_ratio':>17} | {'vs 4x standard':>14} | {'compression':>11}")
print("-" * 72)

standard_ffn = 4.0
for g in gz_params:
    ratio = g["ratio_num"] / g["ratio_den"]
    width = math.log(ratio)
    ffn_ratio = math.exp(width)  # = ratio itself
    compression = ffn_ratio / standard_ffn
    print(f"{g['P']:>6} | {width:>10.6f} | {ffn_ratio:>17.6f} | {compression*100:>13.1f}% | {1/compression:>10.1f}x smaller")

# Step 3: Extended table with more perfect numbers
print("\n--- Step 3: Extended table (general N-state width = ln((N+1)/N)) ---\n")
print(f"{'N':>4} | {'ln((N+1)/N)':>12} | {'exp = (N+1)/N':>14} | {'FFN ratio':>10} | {'% of 4x':>8}")
print("-" * 58)
for n in [2, 3, 4, 5, 6, 8, 10, 15, 20, 50, 100]:
    width = math.log((n+1)/n)
    ffn = (n+1)/n
    pct = ffn / standard_ffn * 100
    print(f"{n:>4} | {width:>12.6f} | {ffn:>14.6f} | {ffn:>10.4f} | {pct:>7.1f}%")

# Step 4: Is the 4/3 ratio special among simple fractions?
print("\n--- Step 4: Is 4/3 special among small-integer ratios? ---\n")
print("Common FFN expansion ratios in practice:")
print(f"  {'Ratio':>8} | {'Value':>8} | {'= exp(ln(r))':>14} | {'Note':>30}")
print("-" * 70)
common = [
    (4, 3, "Transformer default (4/3 ~ 1.33)"),
    (8, 3, "LLaMA/Mistral (8/3 ~ 2.67)"),
    (4, 1, "Standard 4x expansion"),
    (2, 1, "Compact models"),
    (3, 2, "Moderate expansion"),
    (5, 3, "Some efficient nets"),
]
for num, den, note in common:
    r = num / den
    w = math.log(r)
    print(f"  {num}/{den:>5} | {r:>8.4f} | {w:>14.6f} | {note:>30}")

print("\n  Note: 4/3 is the FFN *intermediate/hidden* ratio only in specific designs.")
print("  Standard Transformer uses 4x expansion (d_model -> 4*d_model -> d_model).")
print("  The claim '4/3 = FFN expansion ratio' conflates different quantities.")

# Step 5: Does the GZ width predict ANYTHING about optimal FFN ratio?
print("\n--- Step 5: Predictive power check ---\n")
print("  For the GZ interpretation to be non-trivial, we need:")
print("  (a) exp(GZ_width) = 4/3 to predict FFN ratio, OR")
print("  (b) GZ_width to appear in some trainable parameter naturally")
print()
print("  Reality check:")
print("  - Standard Transformer FFN ratio = 4 (not 4/3)")
print("  - LLaMA FFN ratio = 8/3 = 2.667 (not 4/3)")
print("  - GPT-2 FFN ratio = 4 (not 4/3)")
print("  - 4/3 appears as width_ratio = ln(4/3), not as FFN ratio")
print("  - The interpretation reverses cause and effect:")
print("    GZ_width is DEFINED as ln(4/3), so exp(GZ_width)=4/3 is circular")

# H-EE-15 verdict
print(f"\n{'=' * 70}")
print("H-EE-15 VERDICT")
print("=" * 70)
print()
print("  1. exp(ln(4/3)) = 4/3 is TRIVIALLY TRUE (definition)")
print("  2. The interpretation 'FFN expansion = exp(information deficit)' is")
print("     circular: GZ_width is defined as ln(4/3), so exp recovers 4/3")
print("  3. 4/3 is NOT a standard FFN expansion ratio (standard = 4x)")
print("  4. No predictive power: the formula doesn't predict optimal FFN size")
print("  5. The hierarchy (4/3 -> 6/5 -> 10/9) correctly shows compression")
print("     for higher perfect numbers, but this follows from the definition")
print()
print("  Grade: The identity itself is trivially true (definitional).")
print("  The INTERPRETATION lacks predictive power and may conflate quantities.")
print("  Recommend: WHITE/GREY (true but non-informative)")

# Summary
print(f"\n\n{'=' * 70}")
print("SUMMARY")
print("=" * 70)
print()
print("  H-EE-14 (FFT-Mix windows = 1/GZ_width):")
print(f"    - 1/width values: {[round(iw, 3) for iw in inv_widths]}")
print(f"    - Target windows: {target_windows}")
print(f"    - No simple transform reproduces windows: {not any_match}")
print(f"    - Known derivation via sigma/phi works perfectly: {known_match}")
print(f"    - Texas p-value: {p_value:.4f}")
print()
print("  H-EE-15 (exp(GZ_width) = FFN expansion):")
print("    - Trivially true by definition of ln/exp")
print("    - Interpretation is circular (width defined as ln(4/3))")
print("    - 4/3 is not a standard FFN ratio")
print("    - No predictive power demonstrated")
print()
print("Done.")
