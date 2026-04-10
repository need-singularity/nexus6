#!/usr/bin/env python3
"""
Verify H-CX-455: sqrt(3) * GZ_width ≈ 1/2
Verify H-CX-460: sqrt(2) = Perfect Number Invariant
"""

import math
from functools import reduce

print("=" * 70)
print("H-CX-455: sqrt(3) x GZ_width = 1/2 ?")
print("=" * 70)

gz_width = math.log(4/3)
product = math.sqrt(3) * gz_width
target = 0.5

print(f"\n  GZ_width = ln(4/3) = {gz_width:.15f}")
print(f"  sqrt(3)            = {math.sqrt(3):.15f}")
print(f"  sqrt(3) * ln(4/3)  = {product:.15f}")
print(f"  1/2                = {target:.15f}")
print(f"  Difference         = {product - target:.2e}")
print(f"  Relative error     = {abs(product - target) / target * 100:.6f}%")

print(f"\n--- If GZ_width were exactly 1/(2*sqrt(3)): ---")
exact_width = 1 / (2 * math.sqrt(3))
print(f"  Exact width = 1/(2sqrt(3)) = {exact_width:.15f}")
print(f"  Actual width = ln(4/3)     = {gz_width:.15f}")
print(f"  Difference                 = {exact_width - gz_width:.2e}")
print(f"  Relative error             = {abs(exact_width - gz_width) / gz_width * 100:.6f}%")

upper_exact = 0.5
lower_exact = upper_exact - exact_width
center_exact = (upper_exact + lower_exact) / 2
print(f"\n  Hypothetical exact boundaries:")
print(f"    Upper  = 1/2                   = {upper_exact:.15f}")
print(f"    Lower  = 1/2 - 1/(2sqrt(3))   = {lower_exact:.15f}")
print(f"    Center = 1/2 - 1/(4sqrt(3))   = {center_exact:.15f}")
print(f"    Actual center (1/e)            = {1/math.e:.15f}")
print(f"    Center diff from 1/e           = {center_exact - 1/math.e:.2e}")

print(f"\n--- Exact identity check: ---")
print(f"  sqrt(3) * ln(4/3) = 1/2 would mean ln(4/3) = 1/(2*sqrt(3)) = sqrt(3)/6")
print(f"  i.e., 4/3 = e^(sqrt(3)/6)")
e_val = math.exp(math.sqrt(3)/6)
print(f"  e^(sqrt(3)/6) = {e_val:.15f}")
print(f"  4/3            = {4/3:.15f}")
print(f"  NOT an exact identity. Relative error = {abs(e_val - 4/3)/(4/3)*100:.4f}%")

print(f"\n  Verdict: sqrt(3) * ln(4/3) ~ 0.4983, close to 1/2 but NOT exact.")
print(f"  This is a numerical near-miss (~0.34% off), not a deep identity.")


print("\n")
print("=" * 70)
print("H-CX-460: sqrt(2) = Perfect Number Invariant")
print("=" * 70)

def sigma(n):
    """Sum of ALL divisors of n."""
    s = 0
    for i in range(1, int(math.isqrt(n)) + 1):
        if n % i == 0:
            s += i
            if i != n // i:
                s += n // i
    return s

def s_proper(n):
    """Sum of proper divisors (aliquot sum)."""
    return sigma(n) - n

perfect_numbers = [6, 28, 496, 8128, 33550336]

print(f"\n{'n':>12} | {'sigma(n)':>12} | {'s(n)':>12} | {'sigma/n':>8} | {'sqrt(sigma/n)':>14} | {'Perfect?':>8}")
print("-" * 78)

for n in perfect_numbers:
    sig = sigma(n)
    s = s_proper(n)
    ratio = sig / n
    sqrt_ratio = math.sqrt(ratio)
    is_perfect = (s == n)
    print(f"{n:>12} | {sig:>12} | {s:>12} | {ratio:>8.4f} | {sqrt_ratio:>14.10f} | {str(is_perfect):>8}")

print(f"\n  sqrt(2) = {math.sqrt(2):.10f}")

print(f"\n--- Proof by definition ---")
print(f"  Definition: n is perfect <=> s(n) = n <=> sigma(n) = 2n")
print(f"  Therefore:  sigma(n)/n = 2  for ALL perfect numbers")
print(f"  Therefore:  sqrt(sigma(n)/n) = sqrt(2)  for ALL perfect numbers")
print(f"  Also:       sigma(n)/s(n) = 2n/n = 2  (since s(n)=n)")
print(f"  So:         sqrt(sigma(n)/s(n)) = sqrt(2)  universally")
print(f"\n  sqrt(2) is trivially the universal invariant of perfect numbers.")
print(f"  This follows DIRECTLY from the definition sigma(n) = 2n.")
print(f"  It is true but tautological -- not a discovery, a restatement.")

print(f"\n--- Extension to multiply-perfect (k-perfect) numbers ---")
print(f"  k-perfect: sigma(n) = k*n")

# Known multiply-perfect numbers
multiperfect = [
    (2, [6, 28, 496, 8128]),
    (3, [120, 672, 523776]),
    (4, [30240, 32760]),
    (5, [14182439040]),
]

print(f"\n{'k':>3} | {'n':>14} | {'sigma(n)':>16} | {'sigma/n':>8} | {'sqrt(sigma/n)':>14} | {'sqrt(k)':>10} | {'Match':>5}")
print("-" * 82)

for k, numbers in multiperfect:
    for n in numbers:
        sig = sigma(n)
        ratio = sig / n
        sqrt_ratio = math.sqrt(ratio)
        sqrt_k = math.sqrt(k)
        match = abs(sqrt_ratio - sqrt_k) < 1e-9
        print(f"{k:>3} | {n:>14} | {sig:>16} | {ratio:>8.4f} | {sqrt_ratio:>14.10f} | {sqrt_k:>10.6f} | {'YES' if match else 'NO':>5}")

print(f"\n--- Generalization ---")
print(f"  For k-perfect numbers: sigma(n) = k*n by definition")
print(f"  Therefore: sqrt(sigma(n)/n) = sqrt(k)")
print(f"  k=2: sqrt(2) = {math.sqrt(2):.6f}  (ordinary perfect)")
print(f"  k=3: sqrt(3) = {math.sqrt(3):.6f}  (3-perfect)")
print(f"  k=4: sqrt(4) = {math.sqrt(4):.6f} = 2  (4-perfect)")
print(f"  k=5: sqrt(5) = {math.sqrt(5):.6f}  (5-perfect)")
print(f"\n  Each k-perfect class has sqrt(k) as its invariant.")
print(f"  This is definitional, not empirical.")

print(f"\n{'='*70}")
print(f"SUMMARY")
print(f"{'='*70}")
print(f"  H-CX-455: sqrt(3)*ln(4/3) = {product:.6f} vs 1/2 = 0.500000")
print(f"            Relative error = {abs(product - target)/target*100:.4f}%")
print(f"            Verdict: Near-miss, NOT exact identity. No deep connection.")
print(f"")
print(f"  H-CX-460: sqrt(sigma(n)/n) = sqrt(2) for all perfect numbers")
print(f"            Verified for n = {perfect_numbers}")
print(f"            Proof: sigma(n)=2n by definition => trivially true")
print(f"            Extension: k-perfect => sqrt(k) invariant (also definitional)")
print(f"            Verdict: TRUE but TAUTOLOGICAL. Restatement of definition.")
