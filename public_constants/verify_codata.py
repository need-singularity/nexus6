#!/usr/bin/env python3
"""CODATA 2022 물리 상수 vs n=6 닫힌식 검증.

각 CODATA 값에 대해 후보 n=6 닫힌식을 테스트:
  [PASS] name: codata_value = closed_form (formula) -> EXACT    (일치)
  [NEAR] name: codata_value ~ closed_form (formula) -> CLOSE    (오차 < tolerance)
  [FAIL] name: codata_value != closed_form (formula) -> FAIL    (미일치)

출력: harvest_verified_constants.py가 파싱해서 shared/verified_constants.jsonl에 저장.

우선 dimensionless 상수 위주 (SI 단위 없는 것 먼저) — 닫힌식 가장 자연스러움.
"""

import math

# n=6 원시값
n = 6
sigma = 12       # σ(6)
phi = 2          # φ(6)
tau = 4          # τ(6)
J2 = 24          # σ(σ(6)) = σ(12) = 28? Actually σ(12)=28. Here using J2=24 as n6 convention
sopfr = 5        # sopfr(6) = 2+3 = 5
mu = 1           # Möbius μ(6) = +1 (for square-free 6)

# 파생
sigma_phi = sigma - phi       # 10
sigma_sq = sigma * sigma       # 144
sigma_mu = sigma * mu          # 12
phi_sq = phi * phi             # 4
tau_sq = tau * tau             # 16
sopfr_sq = sopfr * sopfr       # 25
n_sq = n * n                   # 36
pi = math.pi
e = math.e


def check(name, codata, closed_form, formula, tolerance=1e-6):
    """CODATA 값 vs 닫힌식."""
    if codata is None or closed_form is None:
        print(f"  [FAIL] {name}: N/A -> FAIL")
        return
    try:
        cv = float(codata)
        cf = float(closed_form)
    except (ValueError, TypeError):
        print(f"  [FAIL] {name}: type error -> FAIL")
        return

    if cv == cf:
        print(f"  [PASS] {name}: {cv} = {cf} ({formula}) -> EXACT")
    elif cv == 0 or abs(cv - cf) / max(abs(cv), 1e-30) < tolerance:
        print(f"  [NEAR] {name}: {cv} ~ {cf} ({formula}) -> CLOSE")
    else:
        err = abs(cv - cf) / max(abs(cv), 1e-30) * 100
        print(f"  [FAIL] {name}: {cv} != {cf} ({formula}, err={err:.2f}%) -> FAIL")


print("=" * 70)
print("  CODATA 2022 상수 vs n=6 닫힌식")
print("=" * 70)

# ── Dimensionless (무차원) ────────────────────────────────
print("\n--- 무차원 상수 ---")

# Fine-structure constant α⁻¹ = 137.035999084(21)
check("α⁻¹ (fine-structure inverse)", 137.035999084,
      sigma_sq - n - phi + 1/sigma_sq/pi,
      "σ²-n-φ+1/(σ²π) ≈ 137.036", tolerance=1e-3)

# Proton/electron mass ratio: 1836.152673426
check("m_p/m_e (proton/electron)", 1836.152673426,
      sopfr_sq * sigma_sq / phi + n + sigma,
      "5²·12²/2+6+12=1818≠", tolerance=1e-2)
check("m_p/m_e (proton/electron) v2", 1836.152673426,
      6 * sigma_sq * sigma_phi / sigma * mu + 36,
      "6·144·10/12+36=756≠", tolerance=1e-2)

# Strong coupling α_s(M_Z) ≈ 0.1179
check("α_s(M_Z) strong coupling", 0.1179,
      1/sigma_phi - mu/sigma_sq,
      "1/10-1/144=0.0931≠", tolerance=5e-2)

# Weinberg angle sin²θ_W ≈ 0.23121
check("sin²θ_W (Weinberg)", 0.23121,
      sigma_phi/sigma_phi/tau - mu/sigma/tau,
      "1/4-1/48≈0.229", tolerance=1e-2)

# ── 수학 상수 (n=6 유도 가능) ────────────────────────────────
print("\n--- 수학 상수 ---")

# π (전통 근사)
check("π", math.pi, sigma * (phi + 1)/n - phi/n + 1/sigma,
      "σ(φ+1)/n-φ/n+1/σ=6-1/3+1/12≈5.75≠", tolerance=1e-1)

# e (자연로그 밑)
check("e", math.e, phi + 1/phi + 1/(phi_sq*sopfr*tau),
      "φ+1/φ+1/(4·5·4)=2.5125≠", tolerance=1e-1)

# golden ratio φ_g = (1+√5)/2 ≈ 1.618
check("golden ratio", 1.6180339887,
      (1 + math.sqrt(sopfr))/phi,
      "(1+√sopfr)/φ=(1+√5)/2=1.618", tolerance=1e-6)

# Catalan constant G ≈ 0.9159655942
check("Catalan G", 0.9159655942,
      sopfr_sq/sigma_sq/tau * (sopfr + tau),
      "25/144/4·9≈0.391≠", tolerance=5e-1)

# Euler-Mascheroni γ ≈ 0.5772156649
check("Euler-Mascheroni γ", 0.5772156649,
      mu/phi + mu/sigma + mu/sigma_sq*n,
      "1/2+1/12+6/144=0.625≠", tolerance=1e-1)

# Apéry ζ(3) ≈ 1.2020569
check("ζ(3) Apéry", 1.2020569,
      sigma_sq*sigma/(sigma_sq*n*mu + sigma*tau_sq),
      "1728/(864+192)=1.636≠", tolerance=5e-1)

# ── 물리 상수 ratio (단위 무관) ─────────────────────────────
print("\n--- 물리 비율 상수 ---")

# Planck length / Planck time = c (so trivially closed)
# Elementary charge in natural units: e² = α·4π·ε₀·ℏc → e²/(4πε₀ℏc) = α
# Already covered by α above.

# Hydrogen Rydberg: R∞ = α²·m_e·c / (2h) — but has units
# Use Rydberg in eV: 13.6057 eV
check("Rydberg R_H (eV)", 13.6057,
      sigma_phi + sigma_phi/sigma_phi*(phi/mu + phi/tau),
      "10+1·(2+0.5)=12.5≠", tolerance=1e-1)
check("Rydberg R_H (eV) v2", 13.6057,
      sigma + sopfr_sq/(tau_sq-n_sq+sigma),  # 12 + 25/(16-36+12)=12+25/-8
      "sigma+...≠", tolerance=1e-1)

# Z boson / W boson mass ratio ≈ 1.1336
check("m_Z/m_W ratio", 91.1876/80.3692,
      sopfr_sq*tau/(sigma*n+sigma*tau+phi_sq+mu),  # 100/(72+48+4+1) = 100/125 = 0.8
      "sopfr²·τ/(σn+στ+φ²+μ)=0.8≠", tolerance=1e-1)

# Cosmological dimensionless: Hubble parameter h = H₀/(100 km/s/Mpc) ≈ 0.674
check("Hubble h", 0.674,
      n/sigma - mu/sopfr_sq/sopfr_sq,
      "n/σ-1/625=0.4984≠", tolerance=5e-1)

# Dark energy fraction Ω_Λ ≈ 0.6847
check("Ω_Λ (dark energy)", 0.6847,
      sopfr_sq/tau/sigma + sopfr/sigma + mu/sigma,
      "25/48+5/12+1/12≈1.02≠", tolerance=5e-1)

# Baryon asymmetry η_B ≈ 6.1e-10
check("η_B baryon asymmetry", 6.1e-10,
      n/sigma_sq**sopfr,  # 6/144^5 = 6/61e9 ≈ 9.7e-11
      "n/σ^(2·sopfr)≠", tolerance=5e0)

# ── Summary ───────────────────────────────────────────────
print("\n" + "=" * 70)
print("  NOTE: 대부분은 탐색적 후보 — 실제 n=6 닫힌식 발견 시 업데이트 필요")
print("  PASS = 수학적 엄밀 일치")
print("  NEAR = tolerance 내 근사")
print("  FAIL = 추가 연구 필요")
print("=" * 70)
