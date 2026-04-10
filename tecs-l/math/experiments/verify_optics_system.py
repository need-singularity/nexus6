"""
Gravitational Lens System Verification
H-GEO-3, H-GEO-5, H-GEO-9

Computes:
1. Gap structure around perfect numbers
2. Arithmetic mass M(n) = |sigma(n)/n - 2|
3. Aberration profile
4. Einstein radius
5. 2D Gravity telescope F(s)
"""

import math
from sympy import divisor_sigma, totient, factorint, isprime, primerange
from collections import defaultdict

# ─── Helpers ──────────────────────────────────────────────────────────────────

def sigma(n):
    return int(divisor_sigma(n))

def sigma_k(n, k):
    return int(divisor_sigma(n, k))

def tau(n):
    return int(divisor_sigma(n, 0))

def phi(n):
    return int(totient(n))

def R(n):
    """Abundance ratio R(n) = sigma(n) / n"""
    return sigma(n) / n

def M(n):
    """Arithmetic mass M(n) = |sigma(n)/n - 2|"""
    return abs(sigma(n) / n - 2)

PERFECT = [6, 28, 496, 8128]

# ─── Section 1: Gap Structure ─────────────────────────────────────────────────

print("=" * 70)
print("## Section 1: Gap Structure Around Perfect Numbers")
print("=" * 70)
print()

# Precompute R(n) for n=1..50000
N_GAP = 50000
print(f"Computing R(n) for n=1..{N_GAP}... (this may take a moment)")
R_values = {}
for n in range(1, N_GAP + 1):
    R_values[n] = sigma(n) / n

sorted_R = sorted(R_values.values())

print()
print("| P_k  | R(P_k)   | δ⁺ (next higher) | δ⁻ (next lower) | f = δ⁺·δ⁻     | Coma δ⁻/δ⁺ |")
print("|------|----------|-------------------|------------------|----------------|-------------|")

gap_results = {}
for pk in PERFECT:
    rpk = R_values[pk]  # = 2.0 exactly for perfect numbers

    # find δ⁺ = min positive distance to another R value
    delta_plus = float('inf')
    delta_minus = float('inf')

    for n in range(1, N_GAP + 1):
        if n == pk:
            continue
        diff = R_values[n] - rpk
        if diff > 0 and diff < delta_plus:
            delta_plus = diff
        elif diff < 0 and abs(diff) < delta_minus:
            delta_minus = abs(diff)

    focal = delta_plus * delta_minus
    coma = delta_minus / delta_plus if delta_plus > 0 else float('nan')

    gap_results[pk] = {
        'R': rpk, 'delta_plus': delta_plus, 'delta_minus': delta_minus,
        'focal': focal, 'coma': coma
    }

    print(f"| {pk:<4} | {rpk:.6f} | {delta_plus:.2e}          | {delta_minus:.2e}         | {focal:.6e}  | {coma:.6f}  |")

print()

# ─── Section 2: Arithmetic Mass ──────────────────────────────────────────────

print("=" * 70)
print("## Section 2: Arithmetic Mass M(n) = |σ(n)/n - 2| for n=1..100")
print("=" * 70)
print()

mass_values = {}
for n in range(1, 101):
    mass_values[n] = M(n)

zero_mass = [n for n, m in mass_values.items() if m == 0.0]

print(f"**n values with M(n) = 0 (perfect numbers):** {zero_mass}")
print()

print("### Top 20 smallest M(n) (closest to perfect):")
print()
sorted_mass = sorted(mass_values.items(), key=lambda x: x[1])
print("| Rank | n  | σ(n)  | σ(n)/n  | M(n)     | Type              |")
print("|------|----|-------|---------|----------|-------------------|")
for rank, (n, mv) in enumerate(sorted_mass[:20], 1):
    s = sigma(n)
    ratio = s / n
    if mv == 0:
        ntype = "PERFECT"
    elif ratio < 2:
        ntype = "deficient"
    else:
        ntype = "abundant"
    print(f"| {rank:<4} | {n:<2} | {s:<5} | {ratio:.5f} | {mv:.6f} | {ntype:<17} |")

print()

# Full table 1..100 grouped
print("### Full M(n) table (n=1..100):")
print()
print("| n   | σ(n) | σ(n)/n  | M(n)     |")
print("|-----|------|---------|----------|")
for n in range(1, 101):
    s = sigma(n)
    ratio = s / n
    mv = abs(ratio - 2)
    marker = " ← PERFECT" if mv == 0.0 else ""
    print(f"| {n:<3} | {s:<4} | {ratio:.5f} | {mv:.6f} |{marker}")

print()

# ─── Section 3: Aberration Profile ───────────────────────────────────────────

print("=" * 70)
print("## Section 3: Aberration Profile")
print("=" * 70)
print()

# 3a. Chromatic aberration: R(p) for each prime factor, product vs R(n)
print("### 3a. Chromatic Aberration (prime factor R-product vs R(n))")
print()
print("| n   | Prime factors | R(n)     | ∏R(p_i)  | Ratio    | Match?  |")
print("|-----|---------------|----------|----------|----------|---------|")
for n in [6, 28, 496]:
    factors = list(factorint(n).keys())
    r_n = R(n)
    r_product = math.prod(R(p) for p in factors)
    ratio = r_n / r_product if r_product != 0 else float('nan')
    match = "YES" if abs(ratio - 1.0) < 0.001 else "NO"
    factors_str = "×".join(str(p) for p in factors)
    print(f"| {n:<3} | {factors_str:<13} | {r_n:.6f} | {r_product:.6f} | {ratio:.6f} | {match:<7} |")

print()
print("Note: Chromatic = prime factor R-values multiply to give R(n)?")
print()

# Also check with full prime factorization (with multiplicity)
print("### 3a-bis. With multiplicity (prime power factors)")
print()
print("| n   | Factorization | R(n)     | ∏R(p^e)  | Ratio    |")
print("|-----|---------------|----------|----------|----------|")
for n in [6, 28, 496]:
    factors = factorint(n)
    r_n = R(n)
    r_product = math.prod(R(p**e) for p, e in factors.items())
    ratio = r_n / r_product if r_product != 0 else float('nan')
    fact_str = "·".join(f"{p}^{e}" if e > 1 else str(p) for p, e in factors.items())
    print(f"| {n:<3} | {fact_str:<13} | {r_n:.6f} | {r_product:.6f} | {ratio:.6f} |")

print()

# 3b. Astigmatic: R(n)/S(n) where S(n) = sigma(n)*tau(n)/(n*phi(n))
print("### 3b. Astigmatic Ratio R(n)/S(n)")
print("S(n) = σ(n)·τ(n) / (n·φ(n))")
print()
print("| n   | R(n)     | σ(n) | τ(n) | φ(n) | S(n)     | R/S      |")
print("|-----|----------|------|------|------|----------|----------|")
for n in [6, 28, 496]:
    r_n = R(n)
    s_n = sigma(n)
    t_n = tau(n)
    p_n = phi(n)
    S = (s_n * t_n) / (n * p_n)
    ratio = r_n / S if S != 0 else float('nan')
    print(f"| {n:<3} | {r_n:.6f} | {s_n:<4} | {t_n:<4} | {p_n:<4} | {S:.6f} | {ratio:.6f} |")

print()

# 3c. Spherical: density ratio above vs below R(P_k) in ±0.5 interval
print("### 3c. Spherical Aberration (density above vs below R(P_k) in ±0.5)")
print()
print("| P_k  | R(P_k) | count_above | count_below | density_ratio (above/below) |")
print("|------|--------|-------------|-------------|----------------------------|")
for pk in [6, 28, 496]:
    rpk = R_values[pk]  # = 2.0
    lo = rpk - 0.5
    hi = rpk + 0.5
    count_above = sum(1 for n, rv in R_values.items() if rpk < rv <= hi)
    count_below = sum(1 for n, rv in R_values.items() if lo <= rv < rpk)
    density = count_above / count_below if count_below > 0 else float('nan')
    print(f"| {pk:<4} | {rpk:.4f} | {count_above:<11} | {count_below:<11} | {density:.6f}                   |")

print()

# ─── Section 4: Einstein Radius ───────────────────────────────────────────────

print("=" * 70)
print("## Section 4: Einstein Radius θ_E for Perfect Numbers")
print("=" * 70)
print()
print("θ_E(P_k) = sqrt(M(P_k) analog) = sqrt(δ⁺ · δ⁻)")
print("(Using focal length f = δ⁺·δ⁻ as the lensing strength)")
print()

# Also define via gap curvature
print("| P_k  | R(P_k) | δ⁺        | δ⁻        | f = δ⁺·δ⁻     | θ_E = √f      |")
print("|------|--------|-----------|-----------|----------------|---------------|")
for pk in PERFECT:
    g = gap_results[pk]
    f = g['focal']
    theta_e = math.sqrt(f)
    print(f"| {pk:<4} | {g['R']:.4f} | {g['delta_plus']:.4e}  | {g['delta_minus']:.4e}  | {f:.6e}  | {theta_e:.6e}  |")

print()

# Einstein radius interpretation
print("### Einstein Radius log-log scaling:")
print()
print("| P_k  | log(P_k)  | log(θ_E)  | θ_E/θ_E(6) |")
print("|------|-----------|-----------|------------|")
theta6 = math.sqrt(gap_results[6]['focal'])
for pk in PERFECT:
    theta = math.sqrt(gap_results[pk]['focal'])
    print(f"| {pk:<4} | {math.log(pk):.5f}  | {math.log(theta):.5f}   | {theta/theta6:.6f}  |")

print()

# ─── Section 5: 2D Gravity Telescope F(s) ─────────────────────────────────────

print("=" * 70)
print("## Section 5: 2D Gravity Telescope F(s) = Σ R(n)/n^s  (n=1..10000)")
print("=" * 70)
print()

N_TELE = 10000
print(f"Computing F(s) for n=1..{N_TELE}...")
print()

# Precompute R(n) for n=1..10000
R_tele = {}
for n in range(1, N_TELE + 1):
    R_tele[n] = sigma(n) / n

# Note: R(n)/n^s = sigma(n)/n^(s+1)
# This is related to Dirichlet series for sigma function
# F(s) = sum_{n=1}^{N} sigma(n)/n^{s+1}

s_values = [1.1, 1.5, 2.0, 3.0, 5.0, 10.0]

F_vals = {}
for s in s_values:
    total = sum(R_tele[n] / (n ** s) for n in range(1, N_TELE + 1))
    F_vals[s] = total

print("| s    | F(s) = Σ R(n)/n^s | Note                                     |")
print("|------|-------------------|------------------------------------------|")
for s in s_values:
    if s == 2.0:
        note = "≈ ζ(2)·ζ(3)/ζ(5)? or π²/6 related"
    elif s == 1.5:
        note = "Golden Zone lower ≈ 0.2123 × something"
    elif s == 1.1:
        note = "Near pole s=1 (diverges as s→1)"
    elif s == 3.0:
        note = "Compare ζ(3) (Apéry) ≈ 1.20206"
    elif s == 5.0:
        note = "Rapid convergence"
    elif s == 10.0:
        note = "≈ 1 (dominated by n=1 term)"
    else:
        note = ""
    print(f"| {s:<4} | {F_vals[s]:.8f}      | {note:<40} |")

print()

# Theoretical comparison
print("### Theoretical values for reference:")
print()
print("| Constant      | Value      |")
print("|---------------|------------|")
print(f"| ζ(2) = π²/6   | {math.pi**2/6:.8f} |")
print(f"| ζ(3) Apéry    | 1.20205691 |")
print(f"| ζ(4) = π⁴/90  | {math.pi**4/90:.8f} |")
print(f"| π              | {math.pi:.8f} |")
print(f"| e              | {math.e:.8f} |")
print(f"| 1/e            | {1/math.e:.8f} |")
print(f"| ln(4/3)        | {math.log(4/3):.8f} |")
print()

# Ratios between consecutive F(s)
print("### F(s) ratios F(s)/F(next_s):")
print()
print("| s₁   | s₂   | F(s₁)      | F(s₂)      | Ratio F(s₁)/F(s₂) |")
print("|------|------|------------|------------|-------------------|")
for i in range(len(s_values) - 1):
    s1, s2 = s_values[i], s_values[i+1]
    r = F_vals[s1] / F_vals[s2]
    print(f"| {s1:<4} | {s2:<4} | {F_vals[s1]:.6f}   | {F_vals[s2]:.6f}   | {r:.6f}          |")

print()

# F(s) for perfect numbers contribution
print("### Contribution of perfect numbers to F(s) (as fraction of total):")
print()
print("| s    | F(s) total  | F_perf(s) contrib | Fraction   |")
print("|------|-------------|-------------------|------------|")
for s in s_values:
    f_total = F_vals[s]
    f_perf = sum(R_tele.get(pk, 0) / (pk ** s) for pk in PERFECT if pk <= N_TELE)
    frac = f_perf / f_total if f_total != 0 else float('nan')
    print(f"| {s:<4} | {f_total:.8f} | {f_perf:.8e}      | {frac:.6e} |")

print()

# ─── Section 6: Summary / Pattern Detection ───────────────────────────────────

print("=" * 70)
print("## Section 6: Pattern Summary")
print("=" * 70)
print()

print("### Gap Symmetry (Coma ratio δ⁻/δ⁺):")
print()
print("Perfect lensing would give Coma = 1 (symmetric gap).")
print("Asymmetry indicates gravitational bias direction.")
print()
print("| P_k  | δ⁻/δ⁺    | Bias direction              |")
print("|------|----------|-----------------------------|")
for pk in PERFECT:
    g = gap_results[pk]
    coma = g['coma']
    if coma > 1:
        bias = f"deficient side closer (Δ={coma-1:.4f})"
    elif coma < 1:
        bias = f"abundant side closer (Δ={1-coma:.4f})"
    else:
        bias = "symmetric"
    print(f"| {pk:<4} | {coma:.6f} | {bias:<27} |")

print()

print("### Einstein Radius vs Perfect Number scaling:")
print()
print("If θ_E ~ P_k^α, fit log(θ_E) = α·log(P_k) + C")
print()
log_pks = [math.log(pk) for pk in PERFECT]
log_thetas = [math.log(math.sqrt(gap_results[pk]['focal'])) for pk in PERFECT]
# Simple linear regression
n_pts = len(PERFECT)
sum_x = sum(log_pks)
sum_y = sum(log_thetas)
sum_xx = sum(x**2 for x in log_pks)
sum_xy = sum(x*y for x, y in zip(log_pks, log_thetas))
alpha = (n_pts * sum_xy - sum_x * sum_y) / (n_pts * sum_xx - sum_x**2)
C = (sum_y - alpha * sum_x) / n_pts
print(f"Fitted exponent α = {alpha:.6f}")
print(f"Fitted constant C = {C:.6f}")
print(f"θ_E ~ P_k^{alpha:.4f}")
print()

print("### F(s) near-identity checks:")
print()
print(f"F(2.0) = {F_vals[2.0]:.6f}")
print(f"F(2.0) / ζ(2) = {F_vals[2.0] / (math.pi**2/6):.6f}  (ζ(2) = π²/6 = {math.pi**2/6:.6f})")
print(f"F(2.0) / ζ(3) = {F_vals[2.0] / 1.20205690:.6f}  (ζ(3) = 1.20205690)")
print(f"F(3.0) = {F_vals[3.0]:.6f}")
print(f"F(3.0) / ζ(3) = {F_vals[3.0] / 1.20205690:.6f}")
print(f"F(5.0) = {F_vals[5.0]:.6f}")
print(f"F(10.0) = {F_vals[10.0]:.6f}")
print()

# Check: does F(s) relate to known Dirichlet series?
# sigma(n) = sum_{d|n} d, so sum sigma(n)/n^s = zeta(s-1)*zeta(s)
# Therefore sum R(n)/n^s = sum sigma(n)/n^{s+1} = zeta(s)*zeta(s+1)
print("### Theoretical identity: F(s) = Σ σ(n)/n^{s+1} = ζ(s)·ζ(s+1)")
print()
# Verify with known zeta values
def zeta_partial(s, N=10000):
    return sum(1.0/n**s for n in range(1, N+1))

print("| s    | F(s) computed | ζ(s)·ζ(s+1) theoretical | Match? |")
print("|------|---------------|--------------------------|--------|")
for s in [2.0, 3.0, 5.0, 10.0]:
    zs = zeta_partial(s)
    zs1 = zeta_partial(s + 1)
    theoretical = zs * zs1
    ratio = F_vals[s] / theoretical if theoretical != 0 else float('nan')
    match = "YES" if abs(ratio - 1.0) < 0.01 else "APPROX" if abs(ratio - 1.0) < 0.05 else "NO"
    print(f"| {s:<4} | {F_vals[s]:.8f}    | {theoretical:.8f}           | {match:<6} |")

print()
print("(Both sums truncated at N=10000, so small discrepancy expected)")
print()
print("=" * 70)
print("## END OF VERIFICATION")
print("=" * 70)
