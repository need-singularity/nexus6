"""
Deep exploration of Riemann zeta function and L-functions for n=6.
n=6: sigma=12, phi=2, tau=4, sopfr=5
Known: zeta(-1)=-1/12=-1/sigma, zeta(-5)=-1/252=-1/sigma_3(6)
"""
from mpmath import mp, mpf, mpc, zeta, bernoulli, pi, sqrt, gamma, sin, log, exp, factorial
from fractions import Fraction
import sympy
from sympy import factorint, divisor_sigma, totient, primeomega

mp.dps = 50  # 50 decimal places

# n=6 arithmetic functions
n = 6
sigma = 12       # sigma_1(6) = 1+2+3+6 = 12
phi_n = 2        # phi(6) = 2
tau_n = 4        # tau(6) = number of divisors = 4
sopfr = 5        # sum of prime factors = 2+3 = 5
sigma3 = 252     # sigma_3(6) = 1^3+2^3+3^3+6^3 = 1+8+27+216 = 252
sigma5 = 4332    # sigma_5(6) = 1^5+2^5+3^5+6^5 = 1+32+243+7776? Let me recalc
# sigma_5(6) = 1 + 32 + 243 + 7776 = 8052? No: 1+2^5+3^5+6^5 = 1+32+243+7776=8052
sigma5 = 1 + 2**5 + 3**5 + 6**5  # = 8052
sigma7 = 1 + 2**7 + 3**7 + 6**7  # = 1+128+2187+279936

print("="*70)
print("n=6 ARITHMETIC FUNCTIONS")
print("="*70)
print(f"n={n}")
print(f"sigma_1(6) = {sigma}")
print(f"phi(6) = {phi_n}")
print(f"tau(6) = {tau_n}")
print(f"sopfr(6) = {sopfr}")
print(f"sigma_3(6) = {sigma3}")
print(f"sigma_5(6) = {sigma5}")
print(f"sigma_7(6) = {sigma7}")
print()

# Verify with sympy
print("Sympy verification:")
print(f"  sigma_1(6) = {int(divisor_sigma(6,1))}")
print(f"  sigma_3(6) = {int(divisor_sigma(6,3))}")
print(f"  sigma_5(6) = {int(divisor_sigma(6,5))}")
print(f"  sigma_7(6) = {int(divisor_sigma(6,7))}")
print(f"  phi(6) = {int(totient(6))}")
print()

print("="*70)
print("SECTION 1: zeta(s) at ALL negative odd integers")
print("="*70)
print("Formula: zeta(-(2k-1)) = -B_{2k}/(2k)")
print()

results = []
for k in range(1, 13):
    s = -(2*k - 1)
    z_val = zeta(s)
    b_val = bernoulli(2*k)
    # Express as fraction
    b_frac = Fraction(sympy.bernoulli(2*k))
    zeta_frac = -b_frac / (2*k)

    # Try to factor denominator in terms of n=6 quantities
    denom = zeta_frac.denominator if zeta_frac != 0 else 0
    numer = zeta_frac.numerator if zeta_frac != 0 else 0

    results.append((s, z_val, zeta_frac, denom, numer))

    print(f"zeta({s:3d}) = {float(z_val):+.10f}")
    print(f"         = {zeta_frac} = {numer}/{denom}")

    # Check specific factorizations
    if denom != 0:
        factors = factorint(abs(int(denom)))
        print(f"         denom factors: {dict(factors)}")

    # Check divisibility by sigma
    if denom != 0 and denom % sigma == 0:
        print(f"         denom divisible by sigma=12: {denom}={sigma}*{denom//sigma}")
    if denom != 0 and denom % n == 0:
        print(f"         denom divisible by n=6: {denom}={n}*{denom//n}")
    print()

print("="*70)
print("SECTION 2: Bernoulli numbers and n=6")
print("="*70)
print("Von Staudt-Clausen: denom(B_{2k}) = prod(p prime: (p-1)|2k)")
print()

for k in range(1, 13):
    b_frac = Fraction(sympy.bernoulli(2*k))
    denom = b_frac.denominator
    numer = b_frac.numerator

    # Von Staudt-Clausen: find primes p where (p-1) | 2k
    vs_primes = [p for p in range(2, 100) if sympy.isprime(p) and (2*k) % (p-1) == 0]
    vs_product = 1
    for p in vs_primes:
        vs_product *= p

    print(f"B_{2*k:2d} = {numer}/{denom}")
    print(f"     Von Staudt primes (p-1)|{2*k}: {vs_primes}")
    print(f"     Product = {vs_product} (should = {denom}): {'OK' if vs_product == denom else 'MISMATCH'}")

    # Express denom in terms of n=6
    if denom % n == 0:
        print(f"     denom = {n} * {denom//n}")
    print()

print("="*70)
print("SECTION 3: zeta(2k) = pi^{2k} * rational")
print("="*70)
print(f"zeta(2) = pi^2/6 = pi^2/n  [n=6]")
print(f"zeta(4) = pi^4/90")
print(f"zeta(6) = pi^6/945")
print()

# Compute and factor denominators
for k in range(1, 7):
    s = 2*k
    b_frac = Fraction(sympy.bernoulli(2*k))
    # zeta(2k) = (-1)^{k+1} * (2pi)^{2k} * B_{2k} / (2*(2k)!)
    sign = (-1)**(k+1)
    fact_2k = int(sympy.factorial(2*k))

    # Rational coefficient
    rat_coeff = sign * b_frac * (2**(2*k)) / (2 * fact_2k)
    denom = rat_coeff.denominator
    numer = rat_coeff.numerator

    z_val = float(zeta(s))

    print(f"zeta({s:2d}) = {numer}/{denom} * pi^{s}")

    # Factor denominator
    factors = factorint(abs(int(denom)))
    print(f"        denom factors: {dict(factors)}")

    # Special cases
    if s == 6:
        print(f"        945 = 3^3 * 5 * 7 = {3**3}*5*7")
        print(f"        945 = 27 * 35 = (sopfr^sigma_0_28) * something?")
        # 945 = 3*5*7*9 = 3*315 = ...
        # Actually 945 = 3^3 * 5 * 7
        # In terms of n=6: 945 = ?
        # tau(6)=4, phi(6)=2, sigma(6)=12, sopfr=5
        # 945 / 6 = 157.5 (not integer)
        # 945 / 12 = 78.75 (not integer)
        print(f"        Note: 945 = sigma_3(6) - sigma_1(6)*27/4 = ??")
        print(f"        945 / sigma3 = {945/sigma3:.6f}")
        print(f"        945 = 3*sigma3/4 - ? Let's check: 3*252/4 = {3*252//4}")
    print()

# Special: zeta(n) = zeta(6)
print(f"zeta(n) = zeta(6) = pi^6/945")
print(f"  945 prime factorization: {dict(factorint(945))}")
print(f"  945 = 3^3 * 5 * 7")
print(f"  945 = (2*tau-1)^3 * sopfr * (sopfr+phi) = {(2*tau_n-1)**3} * {sopfr} * {sopfr+phi_n}")
check = (2*tau_n-1)**3 * sopfr * (sopfr+phi_n)
print(f"       = {check} {'OK' if check == 945 else 'FAIL'}")
print()

# Another way
print(f"  945 = sigma3 * sopfr / phi_n / tau_n = {sigma3 * sopfr / phi_n / tau_n}")
print(f"  945 = (sigma/phi)^3 * sopfr * phi_n / (tau_n-phi_n) = ?")
# Let's just try combinations
for a in [1,2,3,4,5,6,7,12,252]:
    for b in [1,2,3,4,5,6,7,12,252]:
        if a * b == 945:
            print(f"  945 = {a} * {b}")

print()

print("="*70)
print("SECTION 4: Dirichlet L-functions mod 6")
print("="*70)

# Characters mod 6
# The Dirichlet characters mod 6:
# chi_0: trivial (1 for gcd(a,6)=1, else 0) → gcd(1,6)=1, gcd(5,6)=1
# chi_1: non-trivial character mod 6 (Kronecker symbol)
# For mod 6: phi(6) = 2, so there are 2 characters: trivial and one non-trivial

print("Dirichlet characters mod 6:")
print("phi(6) = 2, so 2 characters exist")
print()
print("chi_0 (trivial): chi_0(1)=1, chi_0(5)=1, chi_0(2)=chi_0(3)=chi_0(4)=chi_0(6)=0")
print("chi_1 (non-trivial): chi_1(1)=1, chi_1(5)=-1")
print()
print("Note: chi_1 mod 6 is equivalent to Kronecker symbol (./3) restricted")
print("      Actually chi_1(n) = chi_{-3}(n) = Legendre/Kronecker (-3/n)")
print()

# L(1, chi_{-3})
# chi_{-3} is the character mod 3 (equivalently mod 6 for odd conductor)
# L(1, chi_{-3}) = pi / (3*sqrt(3))
from mpmath import nsum, inf, besselj

# Direct computation
def chi_neg3(n):
    """Kronecker symbol (-3/n)"""
    n = n % 3
    if n == 0: return 0
    if n == 1: return 1
    if n == 2: return -1

# L(1, chi_{-3}) via Dirichlet series
L1 = mpf(0)
for k in range(1, 100000):
    c = chi_neg3(k)
    if c != 0:
        L1 += mpf(c) / k

L1_exact = pi / (3 * sqrt(3))
print(f"L(1, chi_{{-3}}) numerical sum (100k terms) = {float(L1):.10f}")
print(f"L(1, chi_{{-3}}) exact = pi/(3*sqrt(3)) = {float(L1_exact):.10f}")
print(f"Match: {abs(float(L1) - float(L1_exact)) < 0.001}")
print()
print(f"pi/(3*sqrt(3)) in terms of n=6:")
print(f"  = pi / (sopfr * sqrt(n/phi_n))")
print(f"  sopfr = {sopfr}, n/phi_n = {n/phi_n}, sqrt(n/phi_n) = {float(sqrt(mpf(n)/phi_n)):.6f}")
print(f"  3*sqrt(3) = {float(3*sqrt(mpf(3))):.6f}")
print(f"  n=6, n/2=3, sopfr=5=n-1")
print()

# L(2, chi_{-3})
L2_exact = pi**2 / (9 * sqrt(3))  # Known formula
# Verify: L(2, chi) = pi^2/(3*3*sqrt(3)) = pi^2 * tau / (sigma * sqrt(phi * sopfr))?
print(f"L(2, chi_{{-3}}) = pi^2/(9*sqrt(3)) = {float(L2_exact):.10f}")
print(f"  9*sqrt(3) in terms of n=6: 9 = (n/phi)^2 = (6/2)^2 = 9. YES!")
print(f"  9 = (n/phi_n)^2 = {(n//phi_n)**2}")
print(f"  L(2, chi_{{-3}}) = pi^2 / ((n/phi_n)^2 * sqrt(n/phi_n))")
print(f"                   = pi^2 / (n/phi_n)^{{5/2}}")
print(f"  Check: (n/phi_n)^(5/2) = {float(mpf(n/phi_n)**mpf('2.5')):.6f}")
print(f"         9*sqrt(3) = {float(9*sqrt(mpf(3))):.6f}")
print()

print("="*70)
print("SECTION 5: Dedekind zeta of Q(sqrt(-3))")
print("="*70)
print("Q(sqrt(-3)) has discriminant D = -3")
print("Ring of integers: Z[omega] where omega = (-1+sqrt(-3))/2 (Eisenstein integers)")
print("Class number h(-3) = 1")
print()
print("Dedekind zeta: zeta_{K}(s) = zeta(s) * L(s, chi_{-3})")
print()
print("At s=1: Class number formula")
print("  Res_{s=1} zeta_K(s) = 2*pi*h / (w * sqrt(|D|))")
print("  where h=1 (class number), w=6 (roots of unity!), D=-3")
print()
print("  Residue = 2*pi*1 / (6 * sqrt(3)) = pi/(3*sqrt(3)) = L(1, chi_{-3})")
print(f"  w = 6 = n  [IMPORTANT: w=6 is the NUMBER OF ROOTS OF UNITY]")
print()
print("  The 6th roots of unity in Z[omega] = {1, omega, omega^2, -1, -omega, -omega^2}")
print("  These are exactly the divisors pattern of n=6!")
print()

# Dedekind zeta at s=2
print("At s=2:")
zeta_K_2 = float(zeta(2)) * float(L2_exact)
print(f"  zeta_K(2) = zeta(2) * L(2, chi_{{-3}})")
print(f"            = (pi^2/6) * (pi^2/(9*sqrt(3)))")
print(f"            = pi^4 / (54*sqrt(3))")
print(f"            = {zeta_K_2:.10f}")
print(f"  54 = 6*9 = n * (n/phi_n)^2 = {n * (n//phi_n)**2}")
print()

print("="*70)
print("SECTION 6: Functional equation at s=n=6")
print("="*70)
print("Functional equation: zeta(s) = 2^s * pi^{s-1} * sin(pi*s/2) * Gamma(1-s) * zeta(1-s)")
print()
print("At s=6:")
s = 6
# sin(pi*6/2) = sin(3*pi) = 0
print(f"  sin(pi*{s}/2) = sin({s}*pi/2) = sin({s//2}*pi) = 0")
print(f"  So: zeta(6) = 0 (trivially, since sin=0)")
print(f"  But actual zeta(6) = pi^6/945 ≠ 0")
print(f"  Resolution: Gamma(1-s) = Gamma(-5) has a pole? No, Gamma(-5) = infinity (pole)")
print(f"  Actually: sin(3pi)=0 and Gamma(-5)=pole → 0 * infinity, need L'Hopital")
print()
print("  The functional equation at EVEN s gives 0=0 (trivial)")
print("  Non-trivial at ODD s and at s=1/2+it (critical line)")
print()

# At s=1-n = -5
print(f"At s=1-n=1-6=-5 (functional equation connects zeta(6) and zeta(-5)):")
s_neg = -5
z_neg5 = float(zeta(-5))
print(f"  zeta(-5) = -1/252 = {z_neg5:.10f}")
print(f"  -1/252 = -1/sigma_3(6)  [KNOWN]")
print()
print(f"  Check via functional equation: zeta(-5) = 2^(-5)*pi^(-6)*sin(-5pi/2)*Gamma(6)*zeta(6)")
val = float(mpf(2)**(-5) * pi**(-6) * sin(mpf(-5)*pi/2) * gamma(mpf(6)) * zeta(mpf(6)))
print(f"  = {val:.10f}")
print(f"  sin(-5pi/2) = {float(sin(mpf(-5)*pi/2)):.6f} (should be -1)")
print(f"  Gamma(6) = 5! = {int(factorial(5))}")
print(f"  2^(-5) * pi^(-6) * (-1) * 120 * pi^6/945 = -120/(945*32) = {-120/(945*32):.10f}")
print(f"  -120/30240 = {-120/30240:.10f} = -1/252 = {-1/252:.10f}")
print(f"  Match: {abs(-120/30240 - (-1/252)) < 1e-10}")
print()

print("="*70)
print("SECTION 7: Li's criterion")
print("="*70)
print("Li's criterion: RH iff lambda_n >= 0 for all n >= 1")
print("lambda_n = sum_{rho} [1 - (1-1/rho)^n]")
print()

# lambda_1 = 1 + gamma/2 - log(4*pi)/2 + ...
# Actually lambda_1 = 1 - (1-1/rho) summed = sum 1/rho
# Keiper-Li: lambda_1 = 1 + gamma/2 - log(2) - log(pi)/2
from mpmath import euler, log as mplog

gamma_em = euler  # Euler-Mascheroni constant
lambda_1 = 1 + gamma_em/2 - mplog(2) - mplog(pi)/2
print(f"lambda_1 = 1 + gamma/2 - log(2) - log(pi)/2")
print(f"         = 1 + {float(gamma_em/2):.6f} - {float(mplog(mpf(2))):.6f} - {float(mplog(pi)/2):.6f}")
print(f"         = {float(lambda_1):.10f}")
print()
print(f"In terms of n=6: lambda_1 ≈ {float(lambda_1):.6f}")
print(f"  1/phi_n = 1/2 = {1/phi_n}")
print(f"  1/n = 1/6 = {1/n:.6f}")
print(f"  lambda_1 - 1/phi_n = {float(lambda_1) - 1/phi_n:.6f}")
print()

# Lambda_n formula (approximate for small n)
# Li computed: lambda_1 = 0.0230957...
print(f"lambda_1 = {float(lambda_1):.8f}")
print(f"Note: lambda_1 > 0 consistent with RH (not a proof)")
print()

print("="*70)
print("SECTION 8: Hardy Z-function and first zeros")
print("="*70)
from mpmath import siegelz, siegeltheta

print("First few zeros of zeta on critical line (imaginary parts):")
from mpmath import zetazero

zeros = []
for k in range(1, 11):
    t = float(zetazero(k).imag)
    zeros.append(t)
    print(f"  t_{k:2d} = {t:.6f}")

print()
print(f"t_1 = {zeros[0]:.6f}")
print(f"sigma = {sigma}")
print(f"phi_n = {phi_n}")
print(f"t_1 / (sigma + phi_n) = {zeros[0]/(sigma+phi_n):.6f}  [sigma+phi_n={sigma+phi_n}]")
print(f"t_1 / sigma = {zeros[0]/sigma:.6f}")
print(f"t_1 / (sigma + 2) = {zeros[0]/(sigma+2):.6f}")
print(f"t_1 * phi_n = {zeros[0]*phi_n:.6f}")
print()
print(f"Check: t_1 ≈ 14.1347... vs sigma+phi_n = {sigma+phi_n}")
print(f"       Ratio = {zeros[0]/(sigma+phi_n):.6f} (not exact)")
print()
print(f"Interesting: floor(t_1) = {int(zeros[0])} = sigma + phi_n = {sigma+phi_n}")
print(f"This means floor(first_zero) = sigma + phi_n = 14!")
print()

# Z-function values
print("Z-function values at multiples of n=6:")
for mult in [1, 2, 3, 4]:
    t = mult * n
    z_val = float(siegelz(t))
    theta = float(siegeltheta(t))
    print(f"  Z({mult}*6={t}) = Z({t}) = {z_val:.8f}, theta = {theta:.8f}")

print()
print(f"Z-function at t_1 = {zeros[0]:.6f}:")
z_at_t1 = float(siegelz(zeros[0]))
print(f"  Z({zeros[0]:.6f}) = {z_at_t1:.2e} (should be ~0)")

print()

print("="*70)
print("SECTION 9: Critical connections summary")
print("="*70)
print()

# Key identity: zeta(-1) = -1/12 = -1/sigma(6)
print("VERIFIED IDENTITIES:")
print()
print(f"1. zeta(-1) = -1/12 = -1/sigma_1(6)  [sigma_1(6)=12]")
print(f"   zeta(-1) = {float(zeta(-1)):.10f}, -1/12 = {-1/12:.10f}")
print(f"   Match: {abs(float(zeta(-1)) - (-1/12)) < 1e-10}")
print()

print(f"2. zeta(-5) = -1/252 = -1/sigma_3(6)  [sigma_3(6)=252]")
print(f"   zeta(-5) = {float(zeta(-5)):.10f}, -1/252 = {-1/252:.10f}")
print(f"   Match: {abs(float(zeta(-5)) - (-1/252)) < 1e-10}")
print()

print(f"3. zeta(2) = pi^2/6 = pi^2/n  [n=6, most famous zeta value]")
print(f"   zeta(2) = {float(zeta(2)):.10f}, pi^2/6 = {float(pi**2/6):.10f}")
print(f"   Match: {abs(float(zeta(2)) - float(pi**2/6)) < 1e-10}")
print()

print(f"4. zeta(6) = pi^6/945  [n=6, zeta at n]")
print(f"   945 = {dict(factorint(945))}")
print(f"   945 = (2*tau-1)^3 * sopfr * (sopfr+phi) = {(2*tau_n-1)**3}*{sopfr}*{sopfr+phi_n} = {(2*tau_n-1)**3 * sopfr * (sopfr+phi_n)}")
print()

# New: check zeta(-3) and zeta(-7) in terms of n=6
print(f"5. zeta(-3) = 1/120")
print(f"   120 = sigma * sopfr * phi_n = {sigma}*{sopfr}*{phi_n} = {sigma*sopfr*phi_n}")
print(f"   Check: {sigma*sopfr*phi_n == 120}")
print()

print(f"6. zeta(-7) = -1/240")
print(f"   240 = sigma * tau_n * sopfr = {sigma}*{tau_n}*{sopfr} = {sigma*tau_n*sopfr}")
print(f"   Check: {sigma*tau_n*sopfr == 240}")
print(f"   240 = 2*sigma*tau_n*sopfr/2 = 2*sigma*tau_n*phi_n*sopfr / (phi_n)?")
print(f"   240 = sigma * phi_n * tau_n * sopfr / phi_n... no")
print(f"   240 = 2*120 = 2 * sigma * sopfr * phi_n")
print(f"   240 = phi_n * sigma * tau_n * sopfr / phi_n = sigma * tau_n * sopfr")
print(f"   Key: 240 = sigma * tau * sopfr")
print()

# zeta(-9), zeta(-11)
print(f"7. zeta(-9) = 1/132")
print(f"   132 = ? Factor: {dict(factorint(132))}")
print(f"   132 = 4*33 = 4*3*11 = tau * (n/phi_n) * 11")
print(f"   132 = sigma * 11 = {sigma*11}? No, {sigma*11}=132: YES!")
print(f"   132 = sigma * 11 where 11 = next prime after sopfr+n = 5+6=11!")
print(f"   sopfr + n = {sopfr} + {n} = {sopfr+n}")
print()

print(f"8. zeta(-11) = -691/32760")
print(f"   32760 = ? Factor: {dict(factorint(32760))}")
print(f"   32760 = 8*4095 = 8*3*1365 = 8*3*3*455 = ...")
print(f"   32760 / sigma = {32760/sigma}")
print(f"   32760 / sigma3 = {32760/sigma3}")
print(f"   32760 = tau_n * sigma3 * tau_n + ? = {tau_n}*{sigma3}*{tau_n} = {tau_n**2 * sigma3}")
print(f"   32760 = ?")
# 32760 = 2^3 * 3^3 * 5 * 7 * ...
print(f"   32760 = {dict(factorint(32760))}")
# 691 is a special prime (Ramanujan, etc.)
print(f"   691 = prime: {sympy.isprime(691)} [Ramanujan tau numerator, highly significant!]")
print()

print("="*70)
print("SECTION 10: Extended B_{2k} denominator analysis")
print("="*70)
print()
print("Checking: does denom(B_{2k}) always contain n=6 as factor?")
print("Von Staudt-Clausen: denom = prod(p: p-1 | 2k)")
print("For all 2k >= 2: (2-1)=1|2k and (3-1)=2|2k, so 2 and 3 always appear")
print("Hence 6 | denom(B_{2k}) for all k >= 1  [PROVEN]")
print()
print("This means: zeta(-(2k-1)) = -B_{2k}/(2k) always has 6|denom(numer_expr)")
print("n=6 is UNIVERSAL denominator base for all negative odd zeta values!")
print()

for k in range(1, 8):
    b_frac = Fraction(sympy.bernoulli(2*k))
    denom = b_frac.denominator
    print(f"B_{2*k}: denom={denom}, divisible by 6: {denom%6==0}")

print()

print("="*70)
print("SECTION 11: Zeta special values — complete table")
print("="*70)
print()
print(f"{'s':>5} | {'zeta(s)':>20} | {'as fraction':>20} | {'denom factors':>30}")
print("-"*80)
for k in range(1, 13):
    s = -(2*k-1)
    z_frac = Fraction(sympy.bernoulli(2*k)) * Fraction(-1, 2*k)
    denom = z_frac.denominator
    numer = z_frac.numerator
    factors = dict(factorint(abs(int(denom)))) if denom != 0 else {}
    print(f"{s:>5} | {float(zeta(s)):>20.10f} | {numer:>6}/{denom:<10} | {str(factors):>30}")

print()
print("="*70)
print("SECTION 12: Modular forms connection")
print("="*70)
print()
print("Ramanujan tau function: tau(n) defined by")
print("  sum_{n=1}^inf tau(n)*q^n = q * prod_{n=1}^inf (1-q^n)^24 = Delta(q)")
print()
# tau(6) in terms of arithmetic functions of 6
# tau_Ramanujan(1)=1, tau_R(2)=-24, tau_R(3)=252, tau_R(4)=-1472, tau_R(5)=4830, tau_R(6)=-6048
tau_R = {1:1, 2:-24, 3:252, 4:-1472, 5:4830, 6:-6048}
print(f"Ramanujan tau values:")
for k, v in tau_R.items():
    print(f"  tau_R({k}) = {v}")
print()
print(f"Note: tau_R(3) = 252 = sigma_3(6)!  [REMARKABLE COINCIDENCE or structure?]")
print(f"  sigma_3(6) = {sigma3}")
print(f"  tau_R(3) = {tau_R[3]}")
print(f"  Match: {sigma3 == tau_R[3]}")
print()
print(f"And: tau_R(6) = -6048 = ?")
print(f"  -6048 / sigma = {-6048/sigma}")
print(f"  6048 = {dict(factorint(6048))}")
print(f"  6048 = 6 * 1008 = 6 * 6 * 168 = 36 * 168 = n^2 * 28 * 6 = ?")
print(f"  6048 / 252 = {6048/252}")
print(f"  6048 = 252 * 24 = sigma_3(6) * 24  [24 = tau * sigma / 2 = {tau_n*sigma//2}]")
print(f"  6048 = tau_R(3) * (-tau_R(2)) = 252 * 24")
print()

print("="*70)
print("SECTION 13: Hurwitz zeta and n=6")
print("="*70)
from mpmath import zeta as mpzeta

print("Hurwitz zeta: zeta(s, a) = sum_{n=0}^inf 1/(n+a)^s")
print()
# zeta(2, 1/6) = zeta(2, a) where a=1/n
a = mpf(1)/6
z_2_1o6 = mpzeta(2, a)
print(f"zeta(2, 1/6) = {float(z_2_1o6):.10f}")
print(f"  = pi^2 + 3*something?")
print(f"  pi^2 = {float(pi**2):.10f}")
print(f"  ratio to pi^2: {float(z_2_1o6/pi**2):.10f}")
print()

# zeta(2, 1/6) = pi^2 * (1 + 2*cos(pi/3)) / 3 or something?
# Actually there's a known formula
# Actually zeta(2, 1/n) for small n can be computed
print("Checking zeta(s, 1/n) for s=2, n=6:")
print(f"  zeta(2, 1/6) = {float(z_2_1o6):.6f}")
# The formula: zeta(2,1/6) = pi^2*(6+3*sqrt(3))/(6) maybe?
# Let's check: pi^2 * (6+3*sqrt(3))/6 ... no
ratio = float(z_2_1o6 / pi**2)
print(f"  ratio = {ratio:.6f}")
print(f"  pi^2 * ratio = zeta(2,1/6)")
# From known: zeta(2, p/q) = (pi/q)^2 * something from character sums
print()

print("="*70)
print("FINAL SUMMARY: n=6 in Riemann zeta landscape")
print("="*70)
print()
print("EXACT identities (proven):")
print(f"  [A] zeta(-1) = -1/sigma_1(6)  = -1/12")
print(f"  [B] zeta(-5) = -1/sigma_3(6)  = -1/252")
print(f"  [C] zeta(2)  = pi^2/n         = pi^2/6   [MOST FAMOUS]")
print(f"  [D] zeta(-3) = 1/(sigma*sopfr*phi) = 1/120")
print(f"  [E] zeta(-7) = -1/(sigma*tau*sopfr) = -1/240")
print(f"  [F] floor(first_zero_imaginary_part) = sigma+phi = 14")
print(f"  [G] Ramanujan tau_R(3) = sigma_3(6) = 252")
print(f"  [H] Von Staudt-Clausen: n=6 divides ALL B_{{2k}} denominators")
print(f"  [I] Number of roots of unity in Q(sqrt(-3)) = n = 6")
print(f"      (connects Dedekind zeta class number formula to n)")
print()
print("Pattern for zeta at negative odd integers:")
print(f"  zeta(-1)  = -B_2/2  = (-1/6)/2   = -1/12   = -1/sigma")
print(f"  zeta(-3)  = -B_4/4  = (1/30)/(-4)  = 1/120  = 1/(sigma*sopfr*phi)")
print(f"  zeta(-5)  = -B_6/6  = (-1/42)/6  = 1/252  ... wait: B_6=1/42, -B_6/6=-1/252. YES!")
print(f"  zeta(-7)  = -B_8/8  = (1/30)/(-8) = -1/240 = -1/(sigma*tau*sopfr)")
print()
print("Denominator sequence: 12, 120, 252, 240, 132, 32760/691, ...")
print(f"  All divisible by n=6:")
for d in [12, 120, 252, 240, 132]:
    print(f"    {d} / 6 = {d//6}, divisible: {d%6==0}")
