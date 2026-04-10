"""
H-EN-9 + H-EN-6: Nuclear Energy and R-Spectrum Connection
R(n) = sigma(n)*phi(n) / (n*tau(n))

Investigates whether the arithmetic function R(n) correlates with nuclear
binding energy per nucleon (B/A), and whether the TECS-L master formula
(perfect number 6) encodes nuclear structure constants.
"""

import math
from fractions import Fraction
from typing import Optional

# ─── Arithmetic Functions ──────────────────────────────────────────────────

def divisors(n: int) -> list[int]:
    d = []
    for i in range(1, int(n**0.5) + 1):
        if n % i == 0:
            d.append(i)
            if i != n // i:
                d.append(n // i)
    return sorted(d)

def sigma(n: int) -> int:
    """Sum of divisors."""
    return sum(divisors(n))

def phi(n: int) -> int:
    """Euler totient."""
    if n == 1:
        return 1
    result = n
    p = 2
    temp = n
    while p * p <= temp:
        if temp % p == 0:
            while temp % p == 0:
                temp //= p
            result -= result // p
        p += 1
    if temp > 1:
        result -= result // temp
    return result

def tau(n: int) -> int:
    """Number of divisors."""
    return len(divisors(n))

def R(n: int) -> float:
    """R(n) = sigma(n)*phi(n) / (n*tau(n))"""
    return sigma(n) * phi(n) / (n * tau(n))

def R_fraction(n: int) -> Fraction:
    """R(n) as exact fraction."""
    return Fraction(sigma(n) * phi(n), n * tau(n))

def is_perfect(n: int) -> bool:
    return sigma(n) == 2 * n

# ─── Bethe-Weizsacker Semi-Empirical Mass Formula ─────────────────────────

def valley_of_stability_Z(A: int) -> int:
    """Approximate Z at valley of stability."""
    # Z ≈ A / (2 + 0.0153 * A^(2/3))   (from dB/dZ = 0)
    Z = A / (2.0 + 0.0153 * A**(2.0/3.0))
    return max(1, min(int(round(Z)), A - 1))

def bethe_weizsacker(Z: int, A: int) -> float:
    """
    Bethe-Weizsacker binding energy B(Z,A) in MeV.
    Returns 0 if unphysical.
    """
    if A <= 0 or Z <= 0 or Z >= A:
        return 0.0
    a_v  = 15.56
    a_s  = 17.23
    a_c  = 0.700
    a_a  = 23.29
    N = A - Z

    # Pairing term
    if A % 2 == 1:
        delta = 0.0
    elif Z % 2 == 0:          # even-even
        delta = +12.0 / math.sqrt(A)
    else:                     # odd-odd
        delta = -12.0 / math.sqrt(A)

    B = (a_v * A
         - a_s * A**(2.0/3.0)
         - a_c * Z * (Z - 1) / A**(1.0/3.0)
         - a_a * (A - 2*Z)**2 / A
         + delta)
    return max(B, 0.0)

def best_binding(A: int) -> tuple[int, float, float]:
    """Find Z that maximises B(Z,A); return (Z, B, B/A)."""
    Z0 = valley_of_stability_Z(A)
    best_Z, best_B = Z0, 0.0
    for dz in range(-3, 4):
        z = Z0 + dz
        if 1 <= z < A:
            b = bethe_weizsacker(z, A)
            if b > best_B:
                best_B = b
                best_Z = z
    return best_Z, best_B, best_B / A if A > 0 else 0.0

# ─── Pearson correlation ──────────────────────────────────────────────────

def pearson(xs: list[float], ys: list[float]) -> float:
    n = len(xs)
    mx, my = sum(xs)/n, sum(ys)/n
    num = sum((x-mx)*(y-my) for x,y in zip(xs,ys))
    dx  = math.sqrt(sum((x-mx)**2 for x in xs))
    dy  = math.sqrt(sum((y-my)**2 for y in ys))
    return num / (dx * dy) if dx * dy else 0.0

# ─── ASCII plot ──────────────────────────────────────────────────────────

def ascii_dual_plot(ns, r_vals, ba_vals, width=70, height=20):
    """Two-panel ASCII plot: R(n) top, B/A bottom, same x-axis."""
    def scale_series(vals, h):
        lo, hi = min(vals), max(vals)
        if hi == lo:
            return [h // 2] * len(vals)
        return [int((v - lo) / (hi - lo) * (h - 1)) for v in vals]

    r_rows  = scale_series(r_vals,  height)
    ba_rows = scale_series(ba_vals, height)

    def render(rows, label, vals):
        grid = [[' '] * width for _ in range(height)]
        step = max(1, len(ns) // width)
        col = 0
        for i in range(0, len(ns), step):
            if col >= width:
                break
            r = height - 1 - rows[i]
            grid[r][col] = '*'
            col += 1
        lines = []
        lo, hi = min(vals), max(vals)
        for r, row in enumerate(grid):
            if r == 0:
                prefix = f"{hi:5.3f} |"
            elif r == height - 1:
                prefix = f"{lo:5.3f} |"
            else:
                prefix = "      |"
            lines.append(prefix + ''.join(row))
        lines.append("      +" + '-' * width)
        lines.append(f"       {label}   n=1 → 240")
        return lines

    print("\n".join(render(r_rows,  "R(n)  ", r_vals)))
    print()
    print("\n".join(render(ba_rows, "B/A   ", ba_vals)))

# ─── Main ─────────────────────────────────────────────────────────────────

def main():
    print("=" * 72)
    print("H-EN-9 + H-EN-6: Nuclear Energy and R-Spectrum Connection")
    print("=" * 72)

    N_MAX = 240

    # ── 1. Compute R(n) and B/A for n = 1..240 ───────────────────────────
    ns      = list(range(1, N_MAX + 1))
    r_vals  = [R(n)         for n in ns]
    ba_data = [best_binding(A) for A in ns]
    ba_vals = [x[2] for x in ba_data]

    # ── 2. Pearson correlation ────────────────────────────────────────────
    # Skip A=1 (B/A=0, trivial)
    r2  = r_vals[1:]
    ba2 = ba_vals[1:]
    corr = pearson(r2, ba2)

    print(f"\n## Pearson Correlation  R(A) vs B(A)/A  [A=2..240]")
    print(f"   r = {corr:.6f}")

    # ── 3. ASCII dual plot ────────────────────────────────────────────────
    print("\n## ASCII Plot: R(n) and B/A vs mass number A")
    ascii_dual_plot(ns, r_vals, ba_vals)

    # ── 4. CNO cycle / triple-alpha verification ──────────────────────────
    print("\n## Verification: Perfect Number 6 encodes nuclear constants")
    print()
    s6, p6, t6 = sigma(6), phi(6), tau(6)
    print(f"   sigma(6) = {s6}    phi(6) = {p6}    tau(6) = {t6}")
    print()
    print(f"   Triple-alpha: 3 * He-4 → C-12")
    print(f"   He-4 mass = tau(6) = {t6}  {'✓' if t6 == 4 else '✗'}")
    print(f"   C-12 mass = sigma(6) = {s6}  {'✓' if s6 == 12 else '✗'}")
    print(f"   3 * tau(6) = {3*t6}  ==  sigma(6) = {s6}  {'✓' if 3*t6 == s6 else '✗'}")
    print()
    print(f"   CNO cycle base isotopes: C-12 = sigma(6), N-14, O-16")
    print(f"   N-14:  14 = sigma(6) + phi(6) = {s6+p6}  {'✓' if s6+p6 == 14 else '✗'}")
    print(f"   O-16:  16 = sigma(6) + tau(6) = {s6+t6}  {'✓' if s6+t6 == 16 else '✗'}")
    print()
    print(f"   Master formula: sigma(6)*phi(6) = {s6*p6} = 24 = {s6}*{p6}")
    print(f"   24 = proton count in Carbon x2, or Mg-24, or...")

    # sigma iterate sigma^4(6)
    val = 6
    chain = [val]
    for _ in range(4):
        val = sigma(val)
        chain.append(val)
    print()
    print(f"   sigma iterate chain from 6: {' → '.join(map(str, chain))}")
    print(f"   sigma^1(6)={chain[1]}, sigma^2(6)={chain[2]}, sigma^3(6)={chain[3]}, sigma^4(6)={chain[4]}")

    # ── 5. Fe-56 analysis ─────────────────────────────────────────────────
    print("\n## Fe-56 Analysis (most tightly bound nucleus)")
    A56 = 56
    s56, p56, t56 = sigma(A56), phi(A56), tau(A56)
    r56 = R_fraction(A56)
    Z56, B56, BA56 = best_binding(A56)
    print()
    print(f"   sigma(56) = {s56}")
    print(f"   phi(56)   = {p56}")
    print(f"   tau(56)   = {t56}")
    print(f"   R(56)     = {s56}*{p56} / ({A56}*{t56}) = {s56*p56}/{A56*t56} = {r56} ≈ {float(r56):.6f}")
    print()
    print(f"   sigma^4(6) = {chain[4]}  ==  sigma(56) = {s56}  {'✓' if chain[4] == s56 else '✗'}")
    print(f"   sigma(6)*phi(6) = {s6*p6}  ==  phi(56) = {p56}  {'✓' if s6*p6 == p56 else '✗'}")
    print()
    print(f"   Best Z for A=56: Z={Z56}")
    print(f"   B(56)/A = {BA56:.4f} MeV")
    print(f"   R(56)   = {float(r56):.6f}")

    # ── 6. Magic numbers ──────────────────────────────────────────────────
    MAGIC = [2, 8, 20, 28, 50, 82, 126]
    print("\n## Magic Numbers vs R(n)")
    print()
    print(f"| M   | sigma(M) | phi(M) | tau(M) | R(M) exact    | R(M) float | integer? | B/A (MeV) |")
    print(f"|-----|----------|--------|--------|---------------|------------|----------|-----------|")
    for m in MAGIC:
        sm, pm, tm = sigma(m), phi(m), tau(m)
        rm_frac = R_fraction(m)
        rm_f    = float(rm_frac)
        is_int  = rm_frac.denominator == 1
        _, _, ba_m = best_binding(m)
        flag = "YES" if is_int else f"1/{rm_frac.denominator}"
        print(f"| {m:<3} | {sm:<8} | {pm:<6} | {tm:<6} | {str(rm_frac):<13} | {rm_f:<10.6f} | {flag:<8} | {ba_m:<9.4f} |")

    # ── 7. Where R(A) is integer AND B/A near maximum ─────────────────────
    print("\n## A where R(A) is integer AND B/A in top-10%")
    ba_threshold = sorted(ba_vals, reverse=True)[len(ba_vals)//10]
    print(f"   B/A threshold (top 10%): {ba_threshold:.4f} MeV")
    print()
    print(f"| A   | R(A) | B/A (MeV) | Notes                  |")
    print(f"|-----|------|-----------|------------------------|")
    found = []
    for n in ns:
        rf = R_fraction(n)
        if rf.denominator == 1:
            _, _, ba_n = best_binding(n)
            if ba_n >= ba_threshold:
                note = ""
                if is_perfect(n):
                    note = "PERFECT NUMBER"
                elif n in MAGIC:
                    note = "MAGIC NUMBER"
                found.append((n, int(rf), ba_n, note))
    if found:
        for a, rv, ba_n, note in found:
            print(f"| {a:<3} | {rv:<4} | {ba_n:<9.4f} | {note:<22} |")
    else:
        print("| (none found) |")

    # ── 8. Full table A=1..60 ─────────────────────────────────────────────
    print("\n## R(A) and B/A full table, A=1..60")
    print()
    print(f"| A  | sigma | phi | tau | R(A) frac    | R(A)   | B/A MeV | Z_stab | notes        |")
    print(f"|----|-------|-----|-----|--------------|--------|---------|--------|--------------|")
    for n in range(1, 61):
        sm, pm, tm = sigma(n), phi(n), tau(n)
        rf = R_fraction(n)
        Z_s, _, ba_n = best_binding(n)
        notes = []
        if is_perfect(n):       notes.append("perfect")
        if n in MAGIC:          notes.append("magic")
        if rf.denominator == 1: notes.append(f"R=int({int(rf)})")
        print(f"| {n:<2} | {sm:<5} | {pm:<3} | {tm:<3} | {str(rf):<12} | {float(rf):<6.4f} | {ba_n:<7.4f} | {Z_s:<6} | {', '.join(notes):<12} |")

    # ── 9. R-spectrum statistical summary ────────────────────────────────
    print("\n## R-Spectrum Statistical Summary (A=1..240)")
    print()
    int_count = sum(1 for n in ns if R_fraction(n).denominator == 1)
    print(f"   Total n in range:          {N_MAX}")
    print(f"   R(n) is integer:           {int_count} ({100*int_count/N_MAX:.1f}%)")
    print(f"   R(n) min: {min(r_vals):.6f}  max: {max(r_vals):.6f}  mean: {sum(r_vals)/len(r_vals):.6f}")
    print()
    # Perfect numbers in range
    perfs = [n for n in ns if is_perfect(n)]
    print(f"   Perfect numbers in 1..{N_MAX}: {perfs}")
    for p in perfs:
        rf = R_fraction(p)
        print(f"     R({p}) = {rf} = {float(rf):.6f}  (integer: {rf.denominator==1})")

    # ── 10. Connection summary ────────────────────────────────────────────
    print("\n## Connection Summary: TECS-L Master Formula ↔ Nuclear Physics")
    print()
    rows = [
        ("Triple-alpha He→C",  "3*tau(6) = sigma(6)",       f"3*{t6} = {s6} = C-12 mass",      "✓"),
        ("CNO N-14",           "sigma(6)+phi(6) = 14",      f"{s6}+{p6} = {s6+p6} = N-14",     "✓" if s6+p6==14 else "✗"),
        ("CNO O-16",           "sigma(6)+tau(6) = 16",      f"{s6}+{t6} = {s6+t6} = O-16",     "✓" if s6+t6==16 else "✗"),
        ("Fe-56 sigma",        "sigma^4(6) = sigma(56)",    f"{chain[4]} = {sigma(56)}",         "✓" if chain[4]==sigma(56) else "✗"),
        ("Fe-56 phi",          "sigma(6)*phi(6) = phi(56)", f"{s6*p6} = {phi(56)}",              "✓" if s6*p6==phi(56) else "✗"),
        ("R(6) = 1",           "R(6)=1 (perfect number)",   f"R(6)={float(R_fraction(6)):.4f}", "✓" if R_fraction(6)==1 else "✗"),
    ]
    print(f"| Claim                  | Formula                    | Numeric check          | Status |")
    print(f"|------------------------|----------------------------|------------------------|--------|")
    for claim, formula, numeric, status in rows:
        print(f"| {claim:<22} | {formula:<26} | {numeric:<22} | {status:<6} |")

    print("\n" + "=" * 72)
    print("Done.")
    print("=" * 72)

if __name__ == "__main__":
    main()
