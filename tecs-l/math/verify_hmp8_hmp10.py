#!/usr/bin/env python3
"""
Verify H-MP-8 (R-factor Dirichlet series) and H-MP-10 (Asymptotic of Σ R(n))

R(n) = σ(n)·φ(n) / (n·τ(n))
"""

import math
from fractions import Fraction
import numpy as np
from scipy.optimize import curve_fit

# ─── Arithmetic functions ───

def sigma(n):
    """Sum of divisors"""
    s = 0
    for i in range(1, int(math.isqrt(n)) + 1):
        if n % i == 0:
            s += i
            if i != n // i:
                s += n // i
    return s

def phi(n):
    """Euler's totient"""
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

def tau(n):
    """Number of divisors"""
    count = 0
    for i in range(1, int(math.isqrt(n)) + 1):
        if n % i == 0:
            count += 1
            if i != n // i:
                count += 1
    return count

def R_float(n):
    return sigma(n) * phi(n) / (n * tau(n))

def R_frac(n):
    return Fraction(sigma(n) * phi(n), n * tau(n))

def is_squarefree(n):
    p = 2
    while p * p <= n:
        if n % (p * p) == 0:
            return False
        p += 1
    return True

def factorize(n):
    factors = {}
    d = 2
    while d * d <= n:
        while n % d == 0:
            factors[d] = factors.get(d, 0) + 1
            n //= d
        d += 1
    if n > 1:
        factors[n] = factors.get(n, 0) + 1
    return factors

# ─── Primes up to limit ───

def sieve(limit):
    is_prime = [True] * (limit + 1)
    is_prime[0] = is_prime[1] = False
    for i in range(2, int(math.isqrt(limit)) + 1):
        if is_prime[i]:
            for j in range(i*i, limit + 1, i):
                is_prime[j] = False
    return [p for p in range(2, limit + 1) if is_prime[p]]

print("=" * 70)
print("H-MP-8: R-factor Dirichlet Series F(s) = Σ R(n)·n^{-s}")
print("=" * 70)

# ─── 1. Convergence check ───
print("\n--- 1. Convergence: partial sums F_N(s) for s=1.5, 2, 3 ---\n")

Ns = [100, 500, 1000, 5000, 10000]
s_values = [1.0, 1.5, 2.0, 3.0]

print(f"{'N':>7} | {'s=1.0':>12} | {'s=1.5':>12} | {'s=2.0':>12} | {'s=3.0':>12}")
print("-" * 60)

partial_sums = {s: [] for s in s_values}
for N in Ns:
    row = f"{N:>7} |"
    for s in s_values:
        total = sum(R_float(n) / n**s for n in range(1, N + 1))
        partial_sums[s].append(total)
        row += f" {total:>12.6f} |"
    print(row)

print("\nConvergence analysis:")
for s in s_values:
    vals = partial_sums[s]
    if len(vals) >= 2:
        ratio = abs(vals[-1] - vals[-2]) / abs(vals[-2] - vals[-3]) if len(vals) >= 3 and abs(vals[-2] - vals[-3]) > 1e-15 else float('inf')
        converging = abs(vals[-1] - vals[-2]) < abs(vals[-2] - vals[-3]) if len(vals) >= 3 else None
        status = "CONVERGING" if converging else ("DIVERGING" if converging is False else "UNKNOWN")
        print(f"  s={s}: last two partials = {vals[-2]:.6f}, {vals[-1]:.6f}, diff={abs(vals[-1]-vals[-2]):.2e}, {status}")

# ─── 2. Compare F(2) with zeta products ───
print("\n--- 2. Compare F(2) with products of zeta values ---\n")

# Compute zeta values numerically (N=50000 terms + Euler-Maclaurin)
def zeta_approx(s, terms=100000):
    """Approximate zeta(s) by partial sum + integral tail"""
    total = sum(1.0 / n**s for n in range(1, terms + 1))
    # Integral tail: ∫_{N}^∞ x^{-s} dx = N^{1-s}/(s-1)
    total += terms**(1-s) / (s - 1)
    return total

z2 = zeta_approx(2)
z3 = zeta_approx(3)
z4 = zeta_approx(4)
z5 = zeta_approx(5)
z6 = zeta_approx(6)

F2 = sum(R_float(n) / n**2 for n in range(1, 10001))

print(f"  F(2) [N=10000]     = {F2:.8f}")
print(f"  ζ(2)               = {z2:.8f}")
print(f"  ζ(3)               = {z3:.8f}")
print(f"  ζ(4)               = {z4:.8f}")
print(f"  ζ(2)²/ζ(4)        = {z2**2/z4:.8f}")
print(f"  ζ(3)/ζ(6)          = {z3/z6:.8f}")
print(f"  ζ(2)/ζ(4)          = {z2/z4:.8f}")
print(f"  ζ(2)·ζ(3)/ζ(6)    = {z2*z3/z6:.8f}")
print(f"  6/π²·ζ(2)          = {6/math.pi**2 * z2:.8f}")
print(f"  ζ(2)²/ζ(3)        = {z2**2/z3:.8f}")
print(f"  ζ(3)²/ζ(6)        = {z3**2/z6:.8f}")

# Try more combinations
print("\n  Systematic search for F(2) ≈ ζ(a)^α · ζ(b)^β / ζ(c)^γ:")
candidates = []
for a in [2,3,4,5,6]:
    for b in [2,3,4,5,6]:
        for c in [2,3,4,5,6]:
            for alpha in [-2,-1,0,1,2]:
                for beta in [-2,-1,0,1,2]:
                    for gamma in [-2,-1,0,1,2]:
                        if alpha == 0 and beta == 0 and gamma == 0:
                            continue
                        zvals = {2:z2, 3:z3, 4:z4, 5:z5, 6:z6}
                        try:
                            val = zvals[a]**alpha * zvals[b]**beta / (zvals[c]**gamma if gamma != 0 else 1)
                            if gamma == 0:
                                val = zvals[a]**alpha * zvals[b]**beta
                            else:
                                val = zvals[a]**alpha * zvals[b]**beta * zvals[c]**(-gamma)
                            if abs(val) > 1e-10 and abs(val - F2) / abs(F2) < 0.005:
                                candidates.append((abs(val - F2)/abs(F2), a, alpha, b, beta, c, gamma, val))
                        except:
                            pass

candidates.sort()
if candidates:
    print(f"  {'rel_err':>10} | expression | value")
    for err, a, alpha, b, beta, c, gamma, val in candidates[:10]:
        print(f"  {err:>10.6f} | ζ({a})^{alpha}·ζ({b})^{beta}·ζ({c})^{-gamma} = {val:.8f}")
else:
    print("  No close match found among simple zeta products (within 0.5%)")

# ─── 3. R on squarefree numbers ───
print("\n--- 3. R(n) for squarefree n: multiplicativity check ---\n")

print("  For squarefree n = p1·p2·...·pk:")
print("  R(n) should equal Π R(pi) = Π (pi²-1)/(2pi)")
print()

# Check a few squarefree numbers
test_sqfree = [6, 10, 15, 30, 42, 70, 105, 210]
print(f"  {'n':>6} | {'R(n) exact':>20} | {'Π(p²-1)/(2p)':>20} | match?")
print("  " + "-" * 70)
for n in test_sqfree:
    r_exact = R_frac(n)
    facts = factorize(n)
    product = Fraction(1)
    for p in facts:
        product *= Fraction(p*p - 1, 2*p)
    match = "YES" if r_exact == product else "NO"
    print(f"  {n:>6} | {str(r_exact):>20} | {str(product):>20} | {match}")

# Also check non-squarefree
print("\n  Non-squarefree check (should NOT match the squarefree formula):")
test_nonsqfree = [4, 8, 9, 12, 18, 36]
for n in test_nonsqfree:
    r_exact = R_frac(n)
    facts = factorize(n)
    # Compute actual multiplicative R at prime powers
    product = Fraction(1)
    for p, e in facts.items():
        pe = p**e
        product *= R_frac(pe)
    match = "YES" if r_exact == product else "NO"
    print(f"  {n:>6} | R(n)={str(r_exact):>15} | Π R(p^e)={str(product):>15} | multiplicative: {match}")

# ─── 4. Euler product for squarefree part ───
print("\n--- 4. Euler product Π_p (1 + (p²-1)/(2p^{s+1})) for s=2 ---\n")

primes = sieve(100000)
print(f"  Using {len(primes)} primes up to {primes[-1]}")

for s in [1.5, 2.0, 3.0]:
    product = 1.0
    for p in primes:
        factor = 1.0 + (p*p - 1) / (2.0 * p**(s + 1))
        product *= factor
    print(f"  s={s}: Euler product (squarefree) = {product:.10f}")

# Compare with full Dirichlet sum
print(f"\n  Compare with full F(s) partial sums [N=10000]:")
for s in [1.5, 2.0, 3.0]:
    Fs = sum(R_float(n) / n**s for n in range(1, 10001))
    # Squarefree part only
    Fs_sqfree = sum(R_float(n) / n**s for n in range(1, 10001) if is_squarefree(n))
    print(f"  s={s}: F(s)={Fs:.8f}, F_sqfree(s)={Fs_sqfree:.8f}, ratio={Fs/Fs_sqfree:.6f}")

# ─── 5. Full Euler product (all prime powers) ───
print("\n--- 5. Full Euler product for F(s) ---\n")
print("  F(s) = Π_p (1 + R(p)/p^s + R(p²)/p^{2s} + R(p³)/p^{3s} + ...)")

for s in [2.0, 3.0]:
    product = 1.0
    for p in primes[:5000]:  # enough primes
        local = 1.0
        pe = p
        for e in range(1, 20):
            pe_val = p**e
            r_pe = R_float(pe_val) if pe_val < 10**8 else 0
            term = r_pe / pe_val**s
            if abs(term) < 1e-15:
                break
            local += term
            pe_val *= p
        product *= local
    print(f"  s={s}: Full Euler product = {product:.10f}")

Fs_direct = sum(R_float(n) / n**s for n in range(1, 10001))
print(f"  s=2: Direct sum [N=10000] = {sum(R_float(n) / n**2 for n in range(1, 10001)):.10f}")
print(f"  s=3: Direct sum [N=10000] = {sum(R_float(n) / n**3 for n in range(1, 10001)):.10f}")


print("\n" + "=" * 70)
print("H-MP-10: Asymptotic of S(x) = Σ_{n≤x} R(n)")
print("=" * 70)

# ─── 6. Compute S(x) ───
print("\n--- 6. Compute S(x) for various x ---\n")

x_values = [100, 500, 1000, 5000, 10000, 50000]

# Precompute R values up to max x
max_x = max(x_values)
print(f"  Precomputing R(n) for n=1..{max_x}...")

# For efficiency, precompute sigma, phi, tau arrays via sieve
def compute_arithmetic_arrays(N):
    """Sieve-based computation of sigma, phi, tau for 1..N"""
    sig = [0] * (N + 1)
    ph = list(range(N + 1))
    ta = [0] * (N + 1)

    # sigma: sum of divisors
    for i in range(1, N + 1):
        for j in range(i, N + 1, i):
            sig[j] += i

    # phi: Euler totient via sieve
    for i in range(2, N + 1):
        if ph[i] == i:  # i is prime
            for j in range(i, N + 1, i):
                ph[j] -= ph[j] // i

    # tau: number of divisors
    for i in range(1, N + 1):
        for j in range(i, N + 1, i):
            ta[j] += 1

    return sig, ph, ta

sig_arr, phi_arr, tau_arr = compute_arithmetic_arrays(max_x)
print("  Done.")

R_arr = [0.0] * (max_x + 1)
for n in range(1, max_x + 1):
    R_arr[n] = sig_arr[n] * phi_arr[n] / (n * tau_arr[n])

# Cumulative sum
S_arr = [0.0] * (max_x + 1)
for n in range(1, max_x + 1):
    S_arr[n] = S_arr[n - 1] + R_arr[n]

print(f"\n  {'x':>7} | {'S(x)':>14} | {'log S(x)':>10} | {'log x':>8} | {'S(x)/x':>10} | {'S(x)/x²':>12} | {'S(x)·ln(x)/x²':>14}")
print("  " + "-" * 95)
for x in x_values:
    Sx = S_arr[x]
    logSx = math.log(Sx) if Sx > 0 else 0
    logx = math.log(x)
    print(f"  {x:>7} | {Sx:>14.4f} | {logSx:>10.4f} | {logx:>8.4f} | {Sx/x:>10.4f} | {Sx/x**2:>12.8f} | {Sx*logx/x**2:>14.8f}")

# ─── 7. Power law fit ───
print("\n--- 7. Power law fit: log S(x) = α·log(x) + β ---\n")

log_x = np.array([math.log(x) for x in x_values])
log_S = np.array([math.log(S_arr[x]) for x in x_values])

# Linear regression
coeffs = np.polyfit(log_x, log_S, 1)
alpha_fit = coeffs[0]
beta_fit = coeffs[1]
c_fit = math.exp(beta_fit)

print(f"  α (slope) = {alpha_fit:.6f}")
print(f"  β (intercept) = {beta_fit:.6f}")
print(f"  c = e^β = {c_fit:.6f}")
print(f"  → S(x) ≈ {c_fit:.4f} · x^{alpha_fit:.4f}")

# Residuals
print(f"\n  {'x':>7} | {'S(x) actual':>14} | {'S(x) fitted':>14} | {'rel error':>10}")
print("  " + "-" * 55)
for x in x_values:
    actual = S_arr[x]
    fitted = c_fit * x**alpha_fit
    rel_err = abs(actual - fitted) / actual
    print(f"  {x:>7} | {actual:>14.4f} | {fitted:>14.4f} | {rel_err:>10.4%}")

# ─── 8. Test S(x) ~ x²/(2 ln x) hypothesis ───
print("\n--- 8. Test S(x) ~ c·x²/ln(x) ---\n")

print(f"  {'x':>7} | {'S(x)':>14} | {'x²/(2ln x)':>14} | {'ratio':>10} | {'S(x)·ln(x)/x²':>14}")
print("  " + "-" * 70)
for x in x_values:
    Sx = S_arr[x]
    logx = math.log(x)
    model = x**2 / (2 * logx)
    ratio = Sx / model
    normed = Sx * logx / x**2
    print(f"  {x:>7} | {Sx:>14.4f} | {model:>14.4f} | {ratio:>10.6f} | {normed:>14.8f}")

# ─── 9. More refined: fit S(x) = c · x^α / (ln x)^β ───
print("\n--- 9. Refined fit: S(x) = c · x^α / (ln x)^β ---\n")

def model_func(log_x, alpha, beta, log_c):
    return log_c + alpha * log_x - beta * np.log(log_x)

try:
    popt, pcov = curve_fit(model_func, log_x, log_S, p0=[2.0, 1.0, 0.0])
    alpha_r, beta_r, logc_r = popt
    c_r = math.exp(logc_r)
    print(f"  α = {alpha_r:.6f}")
    print(f"  β = {beta_r:.6f}")
    print(f"  c = {c_r:.6f}")
    print(f"  → S(x) ≈ {c_r:.4f} · x^{alpha_r:.4f} / (ln x)^{beta_r:.4f}")

    print(f"\n  {'x':>7} | {'S(x) actual':>14} | {'S(x) refined':>14} | {'rel error':>10}")
    print("  " + "-" * 55)
    for x in x_values:
        actual = S_arr[x]
        fitted = c_r * x**alpha_r / math.log(x)**beta_r
        rel_err = abs(actual - fitted) / actual
        print(f"  {x:>7} | {actual:>14.4f} | {fitted:>14.4f} | {rel_err:>10.4%}")
except Exception as e:
    print(f"  Fit failed: {e}")

# ─── 10. Average of R(n) ───
print("\n--- 10. Average behavior of R(n) ---\n")

print(f"  {'x':>7} | {'avg R(n)':>12} | {'x/ln(x)':>12} | {'ratio':>10}")
print("  " + "-" * 50)
for x in x_values:
    avg = S_arr[x] / x
    x_over_logx = x / math.log(x)
    ratio = avg / x_over_logx if x_over_logx > 0 else 0
    print(f"  {x:>7} | {avg:>12.4f} | {x_over_logx:>12.4f} | {ratio:>10.6f}")

# ─── 11. Exact fractions for small n ───
print("\n--- 11. R(n) exact values for n=1..30 ---\n")

print(f"  {'n':>4} | {'σ(n)':>6} | {'φ(n)':>6} | {'τ(n)':>5} | {'R(n)':>20} | {'R(n) float':>12} | sqfree?")
print("  " + "-" * 75)
for n in range(1, 31):
    s = sigma(n)
    p = phi(n)
    t = tau(n)
    r = R_frac(n)
    sqf = "Y" if is_squarefree(n) else "N"
    print(f"  {n:>4} | {s:>6} | {p:>6} | {t:>5} | {str(r):>20} | {float(r):>12.6f} | {sqf}")

# ─── 12. Abscissa of convergence ───
print("\n--- 12. Abscissa of convergence estimate ---\n")
print("  Testing s values near 1 to find where divergence begins:")

for s in [0.5, 0.8, 0.9, 0.95, 1.0, 1.05, 1.1, 1.2, 1.5]:
    # Use precomputed R_arr
    partial = sum(R_arr[n] / n**s for n in range(1, 50001))
    partial_half = sum(R_arr[n] / n**s for n in range(1, 25001))
    growth = partial - partial_half
    print(f"  s={s:.2f}: F_50000={partial:>14.4f}, F_25000={partial_half:>14.4f}, tail={growth:>12.4f}")

print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)
print("""
H-MP-8 conclusions:
  - Check convergence table above: F(s) should converge for s>1, diverge at s=1
  - Compare Euler product vs direct sum for consistency
  - R(n) multiplicativity on squarefree n verified if all matches = YES
  - Zeta product identification: see search results above

H-MP-10 conclusions:
  - Power law fit gives α ≈ ? (hypothesis claims ~1.9)
  - Compare simple x^α vs x²/ln(x) models
  - Refined 3-parameter fit gives best model
""")

print("Done.")
