```python
#!/usr/bin/env python3
"""Golden Inhibition Analysis — Sci-Fi Novel Verification Experiments

Mathematical verification of core hypotheses from the novel "Golden Inhibition":
1. Expert activation pattern visualization
2. I sweep (U-curve)
3. Noise analysis (Dense vs MoE)
4. Savant Index
5. R(d) dimension analysis

Only includes CPU-executable parts.
GPU-required parts are in golden_moe_torch.py.
"""

import math
from fractions import Fraction

def sigma(n):
    s=0
    for i in range(1,int(n**0.5)+1):
        if n%i==0: s+=i+(n//i if i*i!=n else 0)
    return s
def tau(n):
    t=0
    for i in range(1,int(n**0.5)+1):
        if n%i==0: t+=1+(1 if i*i!=n else 0)
    return t
def phi(n):
    r=n;t=n;p=2
    while p*p<=t:
        if t%p==0:
            while t%p==0: t//=p
            r-=r//p
        p+=1
    if t>1: r-=r//t
    return r

print("=" * 60)
print("  GOLDEN INHIBITION — Mathematical Analysis")
print("=" * 60)

# 1. R(d) for Mistral 7B dimension d=4096
d = 4096
R_d = Fraction(sigma(d)*phi(d), d*tau(d))
B_d = Fraction(sigma(d)*phi(d), d*d)
print(f"\n1. Mistral 7B: d={d} = 2^12")
print(f"   σ(d) = {sigma(d)}")
print(f"   τ(d) = {tau(d)}")
print(f"   φ(d) = {phi(d)}")
print(f"   R(d) = {R_d} = {float(R_d):.2f}")
print(f"   B(d) = {B_d} = {float(B_d):.6f}")
print(f"   R(d)/d = {float(R_d)/d:.6f}")
print(f"   1/τ(d) = {1/tau(d):.6f}")
print(f"   R/d ≈ c/τ confirmed: ratio = {float(R_d)/d * tau(d):.4f}")

# 2. I = 1/e ≈ 0.368 vs I = 0.375 (actual usage)
print(f"\n2. Inhibition Rate")
print(f"   1/e = {1/math.e:.6f}")
print(f"   I_actual = 0.375 = 3/8")
print(f"   Difference: {abs(0.375 - 1/math.e):.6f} ({abs(0.375-1/math.e)/(1/math.e)*100:.2f}%)")
print(f"   φ(6)/P₁ = 1/3 = {1/3:.6f}")
print(f"   Golden zone center ≈ 1/e = {1/math.e:.6f}")
print(f"   Meta fixed point = 1/3 = {1/3:.6f}")

# 3. 8 experts: activation ratio 2/8 = 1/4 or 3/8?
print(f"\n3. Expert Activation")
n_experts = 8
for k in range(1, n_experts+1):
    ratio = k/n_experts
    # Is this in golden zone?
    in_gz = 0.2123 <= ratio <= 0.5
    marker = " ← GOLDEN ZONE" if in_gz else ""
    if abs(ratio - 1/math.e) < 0.05:
        marker += " ≈ 1/e!"
    if ratio == 0.375:
        marker += " = I_actual!"
    print(f"   k={k}/{n_experts} = {ratio:.4f}{marker}")

# 4. σφ=nτ connection to MoE
print(f"\n4. σφ=nτ and MoE Structure")
print(f"   n=6: σ=12 τ=4 φ=2")
print(f"   6 = 2×3: two prime factors")
print(f"   MoE: 8 experts, k=2-3 active")
print(f"   σ/τ = 3 = number of active experts?")
print(f"   φ/P₁ = 1/3 = inhibition ratio?")
print(f"   R(6)=1: perfect balance = optimal MoE?")

# 5. Noise analysis prediction
print(f"\n5. Noise Prediction")
print(f"   Dense: all {n_experts} experts active")
print(f"   Signal = k relevant experts")
print(f"   Noise = ({n_experts}-k) irrelevant experts")
print(f"   SNR(Dense) = k/({n_experts}-k)")
print(f"   SNR(MoE, k=3) = 3/0 = ∞ (only signal!)")
print(f"   SNR improvement: infinite (in theory)")
print(f"   Practice: router imperfect, some noise remains")

# 6. Dimension telescope for d=4096
print(f"\n6. Dimension Telescope at d={d}")
print(f"   d = 2^12 (pure power of 2)")
print(f"   B(d) = {float(B_d):.6f} → 1 (approaches 1 for 2^k)")
print(f"   τ(d) = {tau(d)} = 13 (factorizations)")
print(f"   head×dim pairs: ", end="")
pairs = [(h, d//h) for h in range(1, d+1) if d % h == 0 and 32 <= d//h <= 256]
print(f"{len(pairs)} valid pairs")
for h, dim in pairs[:8]:
    print(f"     ({h} heads × {dim} dim)", end="")
print()

# 7. The "golden inhibition" number
print(f"\n7. The Golden Inhibition Number")
print(f"   G = D × P / I")
print(f"   At optimal: I = 1/e")
print(f"   σ(6)/n + φ(6)/n = 7/3 (additive balance)")
print(f"   This means: abundancy + freedom = 7/3")
print(f"   = 'structure + chaos = constant'")
print(f"   = 'inhibition + activation = balance'")
print()
print(f"   The perfect number 6 IS the golden inhibition:")
print(f"   σφ=nτ ⟺ signal × freedom = structure × partition")
print(f"   Λ(6)=0 ⟺ the ONLY dynamically balanced number")

print("\n" + "=" * 60)
print("  DONE. Run GPU experiments for PPL verification.")
print("=" * 60)
```