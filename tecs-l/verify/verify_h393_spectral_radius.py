#!/usr/bin/env python3
"""
Verify H-393 spectral radius calculations for K5 circulant consciousness matrix.

M(alpha, beta) = beta * A_s - alpha * A_k

where A_s and A_k are K5 circulant adjacency matrices for the
Sangseang (generation) and Sanggeuk (overcoming) cycles.

Eigenvalues: lambda_k = beta * omega^k - alpha * omega^(2k)
where omega = exp(2*pi*i/5), k = 0,1,2,3,4

rho = max |lambda_k| over k=0..4
"""

import numpy as np

omega = np.exp(2j * np.pi / 5)

def spectral_radius(alpha, beta):
    """Compute rho = max|lambda_k| for k=0..4."""
    magnitudes = []
    for k in range(5):
        lam = beta * omega**k - alpha * omega**(2*k)
        magnitudes.append(abs(lam))
    return magnitudes, max(magnitudes)

substances = [
    ("Sober",           1.00, 1.00),
    ("THC",             0.50, 1.00),
    ("TTX",             1.00, 0.50),
    ("Meditation",      0.37, 0.37),
    ("Heavy sedation",  0.10, 0.10),
    ("Caffeine",        1.00, 1.30),
    ("MDMA",            0.50, 1.50),
    ("Psilocybin",      0.10, 1.20),
    ("Alcohol",         0.70, 0.70),
    ("Ketamine",        0.80, 0.20),
    ("Nicotine",        1.10, 1.00),
    ("SSRI",            0.90, 1.10),
    ("DMT peak",        0.05, 1.50),
]

claimed = {
    "Sober":          1.902,
    "THC":            1.618,
    "TTX":            1.176,
    "Meditation":     0.700,
    "Heavy sedation": 0.190,
    "Caffeine":       2.473,
    "MDMA":           2.058,
    "Psilocybin":     1.931,
}

print("=" * 80)
print("H-393 Spectral Radius Verification")
print("=" * 80)
print(f"\nomega = exp(2*pi*i/5)")
print(f"lambda_k = beta * omega^k - alpha * omega^(2k), k=0..4")
print(f"rho = max|lambda_k|\n")

print(f"{'Substance':<20} {'(alpha, beta)':<16} {'Claimed':>8} {'Actual':>8} {'Match?':>8}")
print("-" * 68)

for name, alpha, beta in substances:
    mags, rho = spectral_radius(alpha, beta)
    cl = claimed.get(name, None)
    if cl is not None:
        match = "OK" if abs(cl - rho) < 0.005 else f"WRONG"
        print(f"{name:<20} ({alpha:.2f}, {beta:.2f})    {cl:8.3f} {rho:8.3f} {match:>8}")
    else:
        print(f"{name:<20} ({alpha:.2f}, {beta:.2f})         --- {rho:8.3f}      ---")

# Detailed eigenvalue breakdown for THC and TTX
print("\n" + "=" * 80)
print("Detailed eigenvalue analysis: THC vs TTX")
print("=" * 80)

for name, alpha, beta in [("THC", 0.5, 1.0), ("TTX", 1.0, 0.5)]:
    mags, rho = spectral_radius(alpha, beta)
    print(f"\n{name} (alpha={alpha}, beta={beta}):")
    for k in range(5):
        lam = beta * omega**k - alpha * omega**(2*k)
        print(f"  k={k}: lambda = {lam.real:+.4f} {lam.imag:+.4f}i  |lambda| = {abs(lam):.4f}")
    print(f"  rho = {rho:.4f}")

# Demonstrate the K5 symmetry
print("\n" + "=" * 80)
print("K5 Circulant Symmetry Proof: swapping alpha<->beta")
print("=" * 80)
print("\nFor K5 circulant, omega^k and omega^(2k) are just permutations of each other")
print("(since 2 is a generator of Z/5Z). So swapping alpha and beta permutes the")
print("eigenvalues but preserves the set of magnitudes.")
print("\nVerification:")
for alpha, beta in [(0.5, 1.0), (1.0, 1.3), (0.5, 1.5), (0.1, 1.2)]:
    mags1, rho1 = spectral_radius(alpha, beta)
    mags2, rho2 = spectral_radius(beta, alpha)
    mags1_sorted = sorted(mags1)
    mags2_sorted = sorted(mags2)
    match = all(abs(a-b) < 1e-10 for a, b in zip(mags1_sorted, mags2_sorted))
    print(f"  ({alpha}, {beta}): rho={rho1:.4f}  |  ({beta}, {alpha}): rho={rho2:.4f}  | Same magnitudes: {match}")

# Generate corrected contour grid
print("\n" + "=" * 80)
print("Corrected Spectral Radius Contour Grid")
print("=" * 80)
print("\n  beta\\alpha  0.0    0.2    0.4    0.6    0.8    1.0")
for beta_val in [2.0, 1.8, 1.6, 1.4, 1.2, 1.0, 0.8, 0.6, 0.4, 0.2, 0.0]:
    row = f"  {beta_val:.1f}  |"
    for alpha_val in [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]:
        _, rho = spectral_radius(alpha_val, beta_val)
        row += f"  {rho:.1f} "
    print(row)

# Corrected eigenvalue magnitudes for all key substances
print("\n" + "=" * 80)
print("Corrected Eigenvalue Magnitudes for Key Substances")
print("=" * 80)

for name, alpha, beta in [("Sober", 1.0, 1.0), ("THC", 0.5, 1.0), ("TTX", 1.0, 0.5), ("Meditation", 0.368, 0.368)]:
    mags, rho = spectral_radius(alpha, beta)
    print(f"\n{name} (alpha={alpha}, beta={beta}):")
    for k in range(5):
        bar = "#" * int(mags[k] * 10)
        print(f"  k={k}: |lambda| = {mags[k]:.3f}  {bar}")
    print(f"  rho = {rho:.3f}")

print("\n" + "=" * 80)
print("CONCLUSION")
print("=" * 80)
print("""
1. THC rho = 1.435, NOT 1.618 (phi). The golden ratio claim is FALSE.
2. TTX rho = 1.435, SAME as THC (not 1.176). K5 symmetry ensures this.
3. Caffeine rho = 2.189, not 2.473.
4. MDMA rho = 1.927, not 2.058.
5. Psilocybin rho = 1.282, not 1.931.
6. Sober, Meditation, Heavy sedation values are correct (symmetric alpha=beta).

The "duality" between THC and TTX manifests in eigenvalue PHASES, not magnitudes.
Both have identical spectral radius due to K5 circulant symmetry.
""")
