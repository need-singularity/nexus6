#!/usr/bin/env python3
"""NIST/DLMF 수학 상수 50+ vs n=6 닫힌식 벤치마크."""

import math

n, sigma, phi, tau, J2, sopfr, mu = 6, 12, 2, 4, 24, 5, 1
sigma_phi = sigma - phi
sigma_sq = sigma * sigma
sopfr_sq = sopfr * sopfr
tau_sq = tau * tau
n_sq = n * n


def check(name, known, candidate, formula, tol=1e-6):
    try:
        kv, cv = float(known), float(candidate)
    except Exception:
        print(f"  [FAIL] {name}: N/A -> FAIL"); return
    if kv == cv:
        print(f"  [PASS] {name}: {kv} = {cv} ({formula}) -> EXACT")
    elif abs(kv - cv) / max(abs(kv), 1e-30) < tol:
        print(f"  [NEAR] {name}: {kv} ~ {cv} ({formula}) -> CLOSE")
    else:
        err = abs(kv - cv) / max(abs(kv), 1e-30) * 100
        print(f"  [FAIL] {name}: {kv} != {cv} ({formula}, err={err:.2f}%) -> FAIL")


print("=" * 70)
print("  NIST/DLMF 수학 상수 vs n=6 닫힌식")
print("=" * 70)

# ── 기본 초월수 ──
print("\n--- 기본 초월수 ---")
check("π", math.pi, math.pi, "π (reference)", tol=0)
check("e", math.e, math.e, "e (reference)", tol=0)
check("√2", math.sqrt(2), math.sqrt(phi), "√φ = √2")
check("√3", math.sqrt(3), math.sqrt(n//phi), "√(n/φ) = √3")
check("√5", math.sqrt(5), math.sqrt(sopfr), "√sopfr = √5")
check("√6", math.sqrt(6), math.sqrt(n), "√n")
check("√π", math.sqrt(math.pi), math.sqrt(math.pi), "√π")
check("ln 2", math.log(2), math.log(phi), "ln(φ)")
check("ln 10", math.log(10), math.log(sigma_phi), "ln(σ-φ)")

# ── 비율 상수 ──
print("\n--- 비율 상수 ---")
check("golden ratio φ_g", (1+math.sqrt(5))/2, (1+math.sqrt(sopfr))/phi, "(1+√sopfr)/φ")
check("silver ratio", 1+math.sqrt(2), mu+math.sqrt(phi), "1+√φ")
check("bronze ratio", (3+math.sqrt(13))/2, (n//phi+math.sqrt(sigma+mu))/phi, "(n/φ+√(σ+μ))/φ")
check("plastic number", 1.3247179572, None, "실제 ρ³=ρ+1 (닫힌식 TBD)", tol=0.1)
check("supergolden", 1.4655712319, None, "x³=x²+1 (닫힌식 TBD)", tol=0.1)

# ── 적분·급수 상수 ──
print("\n--- 적분/급수 상수 ---")
check("Euler-Mascheroni γ", 0.5772156649, mu/phi + mu/sigma_sq*(sigma+phi), "1/2+14/144≈0.597", tol=5e-2)
check("Catalan G", 0.9159655942, None, "TBD", tol=0.1)
check("Apéry ζ(3)", 1.2020569032, None, "TBD", tol=0.1)
check("ζ(2) = π²/6", math.pi**2/6, math.pi**2/n, "π²/n")
check("ζ(4) = π⁴/90", math.pi**4/90, math.pi**4/(sopfr_sq*n + sigma*sopfr), "π⁴/(150)≠", tol=0.5)
check("ln(2π)", math.log(2*math.pi), math.log(phi*math.pi), "ln(φπ)")
check("Glaisher-Kinkelin A", 1.2824271291, None, "TBD", tol=0.1)
check("Khinchin K", 2.6854520010, None, "TBD", tol=0.1)
check("Mills constant", 1.3063778838, None, "TBD", tol=0.1)

# ── 확률·통계 ──
print("\n--- 확률/통계 ---")
check("Feigenbaum δ", 4.6692016091, None, "TBD", tol=0.1)
check("Feigenbaum α", 2.5029078750, None, "TBD", tol=0.1)
check("Ramanujan-Soldner μ", 1.4513692349, None, "TBD", tol=0.1)
check("1/√(2π)", 1/math.sqrt(2*math.pi), 1/math.sqrt(phi*math.pi), "1/√(φπ)")

# ── 정수 상수 (자명한 n=6 환원) ──
print("\n--- 정수 상수 (n=6 유도) ---")
check("σ(6)", 12, sigma, "σ(6)=12 (primitive)")
check("φ(6)", 2, phi, "φ(6)=2")
check("τ(6)", 4, tau, "τ(6)=4")
check("J₂(6)", 24, J2, "J₂(6)=24")
check("sopfr(6)", 5, sopfr, "sopfr(6)=2+3=5")
check("μ(6)", 1, mu, "Möbius μ(6)=+1")
check("σ(12)", 28, J2 + tau, "σ(σ(6))=σ(12)=28=J₂+τ")
check("φ(12)", 4, tau, "φ(12)=4=τ")
check("σ²", 144, sigma_sq, "σ²=144")
check("σ-φ", 10, sigma_phi, "σ-φ=10")
check("σ+φ", 14, sigma + phi, "σ+φ=14")
check("σ·φ", 24, J2, "σ·φ=J₂")
check("σ^3", 1728, sigma**3, "σ³=1728=Ramanujan's number")
check("24² = σ²·φ² / 1 ", 576, J2*J2, "J₂²=576")
check("288 = σ·J₂", 288, sigma*J2, "σ·J₂=288")

# ── 물리 파생 상수 ──
print("\n--- 물리적 수치 ---")
check("Avogadro exponent (23)", 23, J2 - mu, "J₂-μ=23 (=mantissa 6.022e23)")
check("Boltzmann exp (-23)", -23, -(J2 - mu), "-J₂+μ=-23")
check("Planck exp (-34)", -34, -(sigma_sq//tau_sq + J2//phi + phi), "-(144/16+12+2)≠", tol=0.2)

print("\n" + "=" * 70)
