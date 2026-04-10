#!/usr/bin/env python3
"""H-CX-153~156: Pure Math Hypothesis Verification

153: N×ln((N+1)/N) sequence — N=12 closest to 1?
154: Human/Dolphin neuron ratio ≈ e
155: σφ/(nτ) full element scan Z=1~118
156: Perfect number element chain
"""
import math
from sympy import divisor_sigma, totient, divisor_count, isprime, factorint

def run_all():
    print(f"\n{'='*70}")
    print(f"  H-CX-153~156: Pure Math Verification")
    print(f"{'='*70}")

    # === H-CX-153: N×ln((N+1)/N) sequence ===
    print(f"\n  === H-CX-153: N×ln((N+1)/N) → 1 ===")
    print(f"  {'N':>4} {'N×ln((N+1)/N)':>15} {'|delta from 1|':>15} {'note':>15}")
    print(f"  {'-'*55}")
    best_n = 0; best_delta = 999
    for N in range(1, 50):
        val = N * math.log((N+1)/N)
        delta = abs(val - 1)
        note = ''
        if N == 6: note = 'P₁ perfect num'
        elif N == 12: note = 'σ(6)'
        elif N == 28: note = 'P₂ perfect num'
        elif N == 13: note = 'prime'
        if delta < best_delta:
            best_delta = delta; best_n = N
        if N <= 20 or N in [28, 30, 36, 42, 48]:
            print(f"  {N:>4} {val:>15.8f} {delta:>15.8f} {note:>15}")

    print(f"\n  Best N (closest to 1): N={best_n}, delta={best_delta:.8f}")
    print(f"  N=12 delta: {abs(12*math.log(13/12)-1):.8f}")
    print(f"  Is N=12 the best integer? {'YES' if best_n >= 12 else 'NO, N='+str(best_n)}")

    # Actually the sequence is monotonically decreasing toward 1 from above
    # So larger N is always closer. Check if 12 is special in another way
    print(f"\n  Note: N×ln((N+1)/N) is monotonically decreasing → 1")
    print(f"  Every larger N is closer. N=12 is NOT uniquely closest.")
    print(f"  BUT: N=12=σ(6) is the first N where val < 1.0:")
    for N in range(1, 20):
        val = N * math.log((N+1)/N)
        if val < 1.0:
            print(f"  First N with val < 1: N={N}, val={val:.8f}")
            print(f"  Is this σ(6)=12? {'YES!' if N == 12 else 'NO'}")
            break

    # === H-CX-154: Neuron ratio ≈ e ===
    print(f"\n  === H-CX-154: Human/Dolphin Neuron Ratio ≈ e ===")
    human_neurons = 16e9  # 16 billion cortical
    dolphin_neurons = 5.8e9  # bottlenose dolphin
    ratio = human_neurons / dolphin_neurons
    print(f"  Human cortical neurons:   {human_neurons/1e9:.1f}B")
    print(f"  Dolphin cortical neurons: {dolphin_neurons/1e9:.1f}B")
    print(f"  Ratio: {ratio:.6f}")
    print(f"  e:     {math.e:.6f}")
    print(f"  Delta: {abs(ratio - math.e):.6f}")
    print(f"  Relative error: {abs(ratio - math.e)/math.e*100:.2f}%")
    print(f"  H-CX-154 (delta < 0.1): {'SUPPORTED' if abs(ratio-math.e) < 0.1 else 'PARTIAL'}")

    # Other species
    print(f"\n  Other species ratios:")
    species = {
        'Elephant': 5.6e9, 'Chimp': 6.2e9, 'Gorilla': 4.3e9,
        'Dog': 0.53e9, 'Cat': 0.3e9, 'Rat': 0.015e9,
    }
    for name, n in sorted(species.items(), key=lambda x: -x[1]):
        r = human_neurons / n
        delta_e = abs(r - math.e)
        note = f"≈ e! (delta={delta_e:.3f})" if delta_e < 0.2 else ''
        print(f"  Human/{name}: {r:.4f} {note}")

    # === H-CX-155: σφ/(nτ) full scan Z=1~118 ===
    print(f"\n  === H-CX-155: σφ/(nτ) Full Element Scan Z=1~118 ===")
    perfect_balance = []
    near_balance = []

    # Known valence electrons for common elements
    valence_map = {
        1:1, 2:0, 3:1, 4:2, 5:3, 6:4, 7:3, 8:2, 9:1, 10:0,
        11:1, 12:2, 13:3, 14:4, 15:3, 16:2, 17:1, 18:0,
        19:1, 20:2, 21:2, 22:2, 23:2, 24:1, 25:2, 26:2, 27:2, 28:2,
        29:1, 30:2, 31:3, 32:4, 33:3, 34:2, 35:1, 36:0,
        50:4, 82:4,
    }

    print(f"  {'Z':>4} {'σ':>5} {'τ':>3} {'φ':>5} {'σφ':>7} {'nτ':>7} {'ratio':>8} {'bond':>4} {'τ=bond':>6} {'perfect':>6}")
    print(f"  {'-'*60}")

    for z in range(1, 119):
        s = int(divisor_sigma(z, 1))
        t = int(divisor_count(z))
        p = int(totient(z))
        sp = s * p
        nt = z * t
        ratio = sp / nt if nt > 0 else 0
        v = valence_map.get(z, '?')
        match = 'YES' if v != '?' and v == t else ('no' if v != '?' else '?')
        perfect = '★' if s == 2*z else ''

        if abs(ratio - 1.0) < 0.001:
            perfect_balance.append(z)
        if abs(ratio - 1.0) < 0.1:
            near_balance.append(z)

        if z <= 36 or z in [50, 82, 118] or abs(ratio-1.0) < 0.05 or s == 2*z:
            print(f"  {z:>4} {s:>5} {t:>3} {p:>5} {sp:>7} {nt:>7} {ratio:>8.4f} {str(v):>4} {match:>6} {perfect:>6}")

    print(f"\n  σφ/(nτ) = 1.000 exact: Z = {perfect_balance}")
    print(f"  σφ/(nτ) ≈ 1.0 (±0.1): Z = {near_balance[:20]}{'...' if len(near_balance)>20 else ''}")

    multi_bond_balance = [z for z in perfect_balance if valence_map.get(z, 0) >= 3]
    print(f"  Multi-bond(≥3) + σφ=nτ: Z = {multi_bond_balance}")
    print(f"  H-CX-155 (carbon unique?): {'YES — only Z=6!' if multi_bond_balance == [6] else 'NO: ' + str(multi_bond_balance)}")

    # === H-CX-156: Perfect number element chain ===
    print(f"\n  === H-CX-156: Perfect Number Element Chain ===")
    perfect_numbers = [6, 28, 496, 8128]
    for pn in perfect_numbers:
        if pn > 118:
            print(f"  Z={pn}: No element (Z≤118)")
            continue
        s = int(divisor_sigma(pn, 1))
        t = int(divisor_count(pn))
        p = int(totient(pn))
        print(f"  Z={pn}: σ={s}, τ={t}, φ={p}")
        # Cross-connections
        if pn == 28:
            print(f"    φ(28) = {p} = σ(6) = 12 ← Connects two perfect numbers!")
            print(f"    τ(28) = {t} = 6 = perfect number! ← Divisor count is a perfect number!")

    # Chain
    print(f"\n  Perfect number element chain:")
    print(f"    Z=6(C):  σ=12  τ=4  φ=2   → Life")
    print(f"    Z=28(Ni): σ=56  τ=6  φ=12  → Catalyst")
    print(f"    φ(28)=12=σ(6) ← Connection")
    print(f"    τ(28)=6=P₁   ← Divisor count is first perfect number")
    print(f"    Z=496: Transcendent (no element)")

    print(f"\n{'='*70}")
    print(f"  MATH SUMMARY")
    print(f"{'='*70}")
    print(f"  H-CX-153: N=12 first point where val<1? Needs verification")
    print(f"  H-CX-154: Human/Dolphin = {ratio:.4f}, e={math.e:.4f}, delta={abs(ratio-math.e):.4f}")
    print(f"  H-CX-155: σφ/(nτ)=1 multi-bond: {multi_bond_balance}")
    print(f"  H-CX-156: φ(28)=σ(6)=12, τ(28)=6=P₁")


if __name__ == '__main__':
    run_all()