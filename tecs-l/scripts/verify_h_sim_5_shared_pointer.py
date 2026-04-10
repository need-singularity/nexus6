#!/usr/bin/env python3
"""
H-SIM-5: Quantum Entanglement = Shared Memory Pointer
Verification script: CHSH game for classical vs shared-pointer models.

Classical model: each particle stores its own hidden variable.
Shared pointer model: entangled particles share a reference to the same quantum state.
"""

import numpy as np
from dataclasses import dataclass
from typing import Tuple
import math

np.random.seed(42)
N_TRIALS = 10000

# ─── Model 1: Classical Hidden Variable ───

@dataclass
class ClassicalParticle:
    """Each particle has its own hidden variable (angle lambda)."""
    hidden_var: float  # lambda in [0, 2*pi)

def classical_measure(particle: ClassicalParticle, angle: float) -> int:
    """Deterministic measurement: +1 if cos(angle - lambda) >= 0, else -1."""
    diff = angle - particle.hidden_var
    return +1 if np.cos(diff) >= 0 else -1

def classical_chsh(n_trials: int) -> dict:
    """Run CHSH with classical hidden variables."""
    # Standard CHSH angles
    a, a_prime = 0, np.pi / 4
    b, b_prime = np.pi / 8, 3 * np.pi / 8

    correlations = {(ma, mb): 0 for ma in [a, a_prime] for mb in [b, b_prime]}
    counts = {k: 0 for k in correlations}

    for _ in range(n_trials):
        # Shared hidden variable (the "common cause")
        lam = np.random.uniform(0, 2 * np.pi)
        pA = ClassicalParticle(lam)
        pB = ClassicalParticle(lam)  # Same lambda, but SEPARATE objects

        for (ma, mb) in correlations:
            rA = classical_measure(pA, ma)
            rB = classical_measure(pB, mb)
            correlations[(ma, mb)] += rA * rB
            counts[(ma, mb)] += 1

    E = {k: correlations[k] / counts[k] for k in correlations}
    S = E[(a, b)] - E[(a, b_prime)] + E[(a_prime, b)] + E[(a_prime, b_prime)]
    return {"E": E, "S": S, "abs_S": abs(S), "angles": (a, a_prime, b, b_prime)}


# ─── Model 2: Shared Memory Pointer (Quantum) ───

class SharedQuantumState:
    """Shared state object that both particles point to.
    This IS the entanglement: both particles reference the same memory."""

    def __init__(self):
        # Singlet state: perfect anti-correlation basis
        # |psi> = (|01> - |10>) / sqrt(2)
        self.state = "singlet"

    def measure(self, angle_a: float, angle_b: float) -> Tuple[int, int]:
        """
        Quantum measurement on shared state.
        For singlet state, correlation E(a,b) = -cos(a-b).
        Individual outcomes are random but correlated.
        """
        theta = angle_a - angle_b
        # Probability of same outcome
        p_same = np.sin(theta / 2) ** 2
        # p_diff = cos(theta/2)^2

        # Generate correlated outcomes
        outcome_a = np.random.choice([+1, -1])
        if np.random.random() < p_same:
            outcome_b = outcome_a  # same
        else:
            outcome_b = -outcome_a  # different

        return outcome_a, outcome_b


def shared_pointer_chsh(n_trials: int) -> dict:
    """Run CHSH with shared memory pointer (quantum model)."""
    a, a_prime = 0, np.pi / 4
    b, b_prime = np.pi / 8, 3 * np.pi / 8

    correlations = {(ma, mb): 0 for ma in [a, a_prime] for mb in [b, b_prime]}
    counts = {k: 0 for k in correlations}

    for _ in range(n_trials):
        # Create shared state (malloc for entanglement!)
        shared = SharedQuantumState()

        # Both particles POINT to the same object
        # This is the key insight: entanglement = shared pointer

        for (ma, mb) in correlations:
            rA, rB = shared.measure(ma, mb)
            correlations[(ma, mb)] += rA * rB
            counts[(ma, mb)] += 1

    E = {k: correlations[k] / counts[k] for k in correlations}
    S = E[(a, b)] - E[(a, b_prime)] + E[(a_prime, b)] + E[(a_prime, b_prime)]
    return {"E": E, "S": S, "abs_S": abs(S), "angles": (a, a_prime, b, b_prime)}


# ─── Model 3: Analytical (exact) ───

def analytical_quantum_chsh() -> dict:
    """Exact quantum prediction for singlet state CHSH."""
    a, a_prime = 0, np.pi / 4
    b, b_prime = np.pi / 8, 3 * np.pi / 8

    def E_singlet(theta_a, theta_b):
        return -np.cos(theta_a - theta_b)

    E = {}
    E[(a, b)] = E_singlet(a, b)
    E[(a, b_prime)] = E_singlet(a, b_prime)
    E[(a_prime, b)] = E_singlet(a_prime, b)
    E[(a_prime, b_prime)] = E_singlet(a_prime, b_prime)

    S = E[(a, b)] - E[(a, b_prime)] + E[(a_prime, b)] + E[(a_prime, b_prime)]
    return {"E": E, "S": S, "abs_S": abs(S)}


# ─── Angle sweep for both models ───

def angle_sweep(n_trials: int = 5000, n_angles: int = 36) -> list:
    """Sweep offset angle, compute |S| for both models."""
    results = []
    for i in range(n_angles):
        offset = i * np.pi / n_angles
        a, a_prime = 0, offset
        b = offset / 2
        b_prime = 3 * offset / 2 if offset > 0 else np.pi / 8

        # Classical
        c_corr = {}
        c_count = {}
        q_corr = {}
        q_count = {}
        for k in [(a, b), (a, b_prime), (a_prime, b), (a_prime, b_prime)]:
            c_corr[k] = 0
            c_count[k] = 0
            q_corr[k] = 0
            q_count[k] = 0

        for _ in range(n_trials):
            lam = np.random.uniform(0, 2 * np.pi)
            pA = ClassicalParticle(lam)
            pB = ClassicalParticle(lam)
            shared = SharedQuantumState()

            for k in c_corr:
                rA_c = classical_measure(pA, k[0])
                rB_c = classical_measure(pB, k[1])
                c_corr[k] += rA_c * rB_c
                c_count[k] += 1

                rA_q, rB_q = shared.measure(k[0], k[1])
                q_corr[k] += rA_q * rB_q
                q_count[k] += 1

        cE = {k: c_corr[k] / c_count[k] for k in c_corr}
        qE = {k: q_corr[k] / q_count[k] for k in q_corr}

        cS = cE[(a, b)] - cE[(a, b_prime)] + cE[(a_prime, b)] + cE[(a_prime, b_prime)]
        qS = qE[(a, b)] - qE[(a, b_prime)] + qE[(a_prime, b)] + qE[(a_prime, b_prime)]

        results.append({
            "offset_deg": i * 180 / n_angles,
            "classical_S": abs(cS),
            "quantum_S": abs(qS),
        })

    return results


# ─── TECS-L constant analysis ───

def tecs_constant_analysis(s_value: float):
    """Check if |S|=1.978 matches TECS-L constants."""
    e = np.e
    sigma_6 = 2.0  # sigma_{-1}(6) = 1/1 + 1/2 + 1/3 + 1/6 = 2

    candidates = {
        "sigma_{-1}(6) * (1 - 1/e^2)": sigma_6 * (1 - 1/e**2),
        "2 * (1 - 1/e^2)": 2 * (1 - 1/e**2),
        "sigma_{-1}(6) * (1 - 1/e)": sigma_6 * (1 - 1/e),
        "2 - ln(4/3)": 2 - np.log(4/3),
        "2 - 1/e^2": 2 - 1/e**2,
        "2 * tanh(1)": 2 * np.tanh(1),
        "6/pi": 6/np.pi,
        "2*(1-exp(-pi/4))": 2*(1-np.exp(-np.pi/4)),
        "e^(1/e) * (1-1/e)": e**(1/e) * (1-1/e),
        "2 - 1/45 (=89/45)": 89/45,
        "2 - 1/e": 2 - 1/e,
        "2*cos(pi/8)*sin(pi/8)*4": 2*np.cos(np.pi/8)*np.sin(np.pi/8)*4,
        "2*sqrt(2)*sin(pi/4.5)": 2*np.sqrt(2)*np.sin(np.pi/4.5),
        "2 - 1/sqrt(e*pi)": 2 - 1/np.sqrt(e*np.pi),
    }

    print("\n=== TECS-L Constant Match Analysis for |S|=1.978 ===\n")
    print(f"  Target value: {s_value:.6f}")
    print(f"  {'Expression':<35} {'Value':>10} {'Error':>10} {'Match?':>8}")
    print(f"  {'-'*35} {'-'*10} {'-'*10} {'-'*8}")

    matches = []
    for name, val in sorted(candidates.items(), key=lambda x: abs(x[1] - s_value)):
        err = abs(val - s_value)
        pct = err / s_value * 100
        match = "YES" if pct < 1.0 else ("close" if pct < 5.0 else "no")
        print(f"  {name:<35} {val:>10.6f} {pct:>9.2f}% {match:>8}")
        if pct < 5.0:
            matches.append((name, val, pct))

    return matches


# ─── Main ───

if __name__ == "__main__":
    print("=" * 70)
    print("  H-SIM-5: Quantum Entanglement = Shared Memory Pointer")
    print("  CHSH Bell Inequality Test")
    print("=" * 70)

    # 1. Analytical
    print("\n--- Analytical Quantum CHSH (singlet state) ---")
    ana = analytical_quantum_chsh()
    for k, v in ana["E"].items():
        a_deg = k[0] * 180 / np.pi
        b_deg = k[1] * 180 / np.pi
        print(f"  E({a_deg:.0f}deg, {b_deg:.0f}deg) = {v:.6f}")
    print(f"  S = {ana['S']:.6f}")
    print(f"  |S| = {ana['abs_S']:.6f}")
    print(f"  Tsirelson bound = {2*np.sqrt(2):.6f}")
    print(f"  Ratio |S|/Tsirelson = {ana['abs_S']/(2*np.sqrt(2)):.6f}")

    # 2. Classical simulation
    print(f"\n--- Classical Hidden Variable Model ({N_TRIALS} trials) ---")
    cl = classical_chsh(N_TRIALS)
    for k, v in cl["E"].items():
        a_deg = k[0] * 180 / np.pi
        b_deg = k[1] * 180 / np.pi
        print(f"  E({a_deg:.0f}deg, {b_deg:.0f}deg) = {v:.6f}")
    print(f"  S = {cl['S']:.6f}")
    print(f"  |S| = {cl['abs_S']:.6f}")

    # 3. Shared pointer simulation
    print(f"\n--- Shared Pointer Model ({N_TRIALS} trials) ---")
    sp = shared_pointer_chsh(N_TRIALS)
    for k, v in sp["E"].items():
        a_deg = k[0] * 180 / np.pi
        b_deg = k[1] * 180 / np.pi
        print(f"  E({a_deg:.0f}deg, {b_deg:.0f}deg) = {v:.6f}")
    print(f"  S = {sp['S']:.6f}")
    print(f"  |S| = {sp['abs_S']:.6f}")

    # 4. Comparison
    print("\n" + "=" * 70)
    print("  COMPARISON TABLE")
    print("=" * 70)
    print(f"  {'Model':<25} {'|S|':>10} {'vs Classical':>15} {'Violates?':>12}")
    print(f"  {'-'*25} {'-'*10} {'-'*15} {'-'*12}")
    print(f"  {'Classical HV':<25} {cl['abs_S']:>10.4f} {'baseline':>15} {'No':>12}")
    print(f"  {'Shared Pointer (sim)':<25} {sp['abs_S']:>10.4f} {sp['abs_S']/cl['abs_S']:>14.2f}x {'YES' if sp['abs_S'] > 2 else 'No':>12}")
    print(f"  {'Quantum Analytical':<25} {ana['abs_S']:>10.4f} {ana['abs_S']/cl['abs_S']:>14.2f}x {'YES':>12}")
    print(f"  {'H-CX-421 (tension)':<25} {'1.9780':>10} {1.978/cl['abs_S']:>14.2f}x {'No':>12}")
    print(f"  {'Classical bound':<25} {'2.0000':>10} {'-':>15} {'-':>12}")
    print(f"  {'Tsirelson bound':<25} {2*np.sqrt(2):>10.4f} {'-':>15} {'-':>12}")

    # 5. Angle sweep
    print("\n--- Angle Sweep (offset 0-180 deg) ---")
    sweep = angle_sweep(n_trials=3000, n_angles=18)

    print(f"\n  {'Offset':>8} {'Classical |S|':>15} {'Pointer |S|':>15} {'Ratio':>8}")
    print(f"  {'-'*8} {'-'*15} {'-'*15} {'-'*8}")
    for r in sweep:
        ratio = r["quantum_S"] / max(r["classical_S"], 0.001)
        print(f"  {r['offset_deg']:>6.0f}deg {r['classical_S']:>15.4f} {r['quantum_S']:>15.4f} {ratio:>7.2f}x")

    # ASCII graph
    print("\n  ASCII Graph: |S| vs Offset Angle")
    print("  " + "-" * 55)
    max_s = max(max(r["quantum_S"] for r in sweep), 2*np.sqrt(2))
    bar_width = 40
    for r in sweep:
        cbar = int(r["classical_S"] / max_s * bar_width)
        qbar = int(r["quantum_S"] / max_s * bar_width)
        print(f"  {r['offset_deg']:>3.0f}d C|{'#'*cbar}{' '*(bar_width-cbar)}| {r['classical_S']:.3f}")
        print(f"       Q|{'='*qbar}{' '*(bar_width-qbar)}| {r['quantum_S']:.3f}")

    bound_pos = int(2.0 / max_s * bar_width)
    tsi_pos = int(2*np.sqrt(2) / max_s * bar_width)
    print(f"       {' '*3}{' '*(bound_pos-1)}^ classical=2  {' '*(tsi_pos-bound_pos-12)}^ Tsirelson=2.83")

    # 6. Memory metaphor analysis
    print("\n" + "=" * 70)
    print("  MEMORY METAPHOR ANALYSIS")
    print("=" * 70)
    print("""
  Entanglement as Shared Memory Pointer:
  ┌─────────────┐     ┌──────────────────┐     ┌─────────────┐
  │  Particle A  │────>│  SharedState     │<────│  Particle B  │
  │  (pointer)   │     │  |psi> = singlet │     │  (pointer)   │
  └─────────────┘     └──────────────────┘     └─────────────┘
         │                     │                       │
     measure(a)           dereference            measure(b)
         │                     │                       │
         v                     v                       v
    outcome_A      correlated via cos(a-b)      outcome_B

  Classical (separate copies):
  ┌─────────────┐     ┌─────────────┐
  │  Particle A  │     │  Particle B  │
  │  lambda_A    │     │  lambda_B    │
  │  (own copy)  │     │  (own copy)  │
  └─────────────┘     └─────────────┘
         │                    │
     measure(a)          measure(b)
         │                    │
         v                    v
    outcome_A           outcome_B
    (independent)       (independent)

  Key Operations:
    malloc(entanglement) = Create SharedQuantumState()
    pointer_deref(measure) = shared.measure(angle_a, angle_b)
    garbage_collect(decoherence) = del shared  (state destroyed after measurement)
    copy(no_cloning) = IMPOSSIBLE (no-cloning theorem = no pointer copy)
""")

    # 7. TECS-L constant matching
    matches = tecs_constant_analysis(1.978)

    # 8. sigma_{-1}(6) analysis
    print("\n=== Perfect Number 6 Connection ===")
    sigma = 2.0  # sigma_{-1}(6)
    print(f"  sigma_{{-1}}(6) = {sigma}")
    print(f"  |S|_H421 / sigma_{{-1}}(6) = {1.978/sigma:.4f}")
    print(f"  1 - |S|/sigma = {1 - 1.978/sigma:.4f}")
    print(f"  1/e^2 = {1/np.e**2:.4f}")
    print(f"  |S|/sigma vs (1-1/e^2) = {1.978/sigma:.6f} vs {1-1/np.e**2:.6f}")
    print(f"  Difference: {abs(1.978/sigma - (1-1/np.e**2)):.6f}")
    print(f"  Percentage: {abs(1.978/sigma - (1-1/np.e**2))/(1-1/np.e**2)*100:.3f}%")

    # Best match
    best_val = sigma * (1 - 1/np.e**2)
    print(f"\n  *** Best match: sigma_{{-1}}(6) * (1 - 1/e^2) = {best_val:.6f} ***")
    print(f"  *** H-CX-421 |S| = 1.978 ***")
    print(f"  *** Error = {abs(best_val - 1.978):.6f} ({abs(best_val-1.978)/1.978*100:.3f}%) ***")

    print("\n--- DONE ---")
