#!/usr/bin/env python3
"""
H-SIM-6: Wavefunction Collapse = Lazy Evaluation
Verification script: lazy vs eager evaluation in simulated universe.

Lazy: compute amplitudes only, evaluate on measurement.
Eager: compute definite states at every step.
"""

import numpy as np
import time
import math
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

np.random.seed(42)

# ─── Lazy State Model ───

class LazyState:
    """Quantum-like lazy state: stores amplitudes, not values.
    Only evaluates when 'measured'."""

    def __init__(self, n_paths: int = 2):
        """Initialize with n_paths possible states (e.g., 2 slits)."""
        self.n_paths = n_paths
        # Complex amplitudes for each path
        self.amplitudes = np.ones(n_paths, dtype=complex) / np.sqrt(n_paths)
        self.evaluated = False
        self.result = None
        self._computation_count = 0

    def propagate(self, phase_shifts: np.ndarray):
        """Apply phase shifts (lazy: just update amplitudes, O(n_paths))."""
        self._computation_count += 1
        self.amplitudes *= np.exp(1j * phase_shifts)
        return self

    def interfere(self, detector_pos: float, slit_positions: np.ndarray, wavelength: float):
        """Compute interference at detector position (lazy: sum amplitudes)."""
        self._computation_count += 1
        # Phase from each slit to detector
        distances = np.abs(detector_pos - slit_positions)
        phases = 2 * np.pi * distances / wavelength
        self.amplitudes = np.exp(1j * phases) / np.sqrt(self.n_paths)
        return self

    def measure(self) -> int:
        """Force evaluation: collapse to one outcome. This is 'eager' trigger."""
        self._computation_count += 1
        probabilities = np.abs(self.amplitudes) ** 2
        probabilities /= probabilities.sum()  # normalize
        self.result = np.random.choice(self.n_paths, p=probabilities)
        self.evaluated = True
        return self.result

    def get_probability_distribution(self, detector_positions: np.ndarray,
                                      slit_positions: np.ndarray,
                                      wavelength: float) -> np.ndarray:
        """Get interference pattern (lazy: never collapse)."""
        pattern = np.zeros(len(detector_positions))
        for i, pos in enumerate(detector_positions):
            distances = np.abs(pos - slit_positions)
            phases = 2 * np.pi * distances / wavelength
            amplitude = np.sum(np.exp(1j * phases)) / np.sqrt(self.n_paths)
            pattern[i] = np.abs(amplitude) ** 2
        self._computation_count += len(detector_positions)
        return pattern


class EagerState:
    """Classical eager state: always has a definite value."""

    def __init__(self, n_paths: int = 2):
        self.n_paths = n_paths
        # Immediately decide which path (eager evaluation!)
        self.path = np.random.randint(0, n_paths)
        self.evaluated = True
        self._computation_count = 1  # Already computed at creation

    def propagate(self, phase_shifts: np.ndarray):
        """Propagate along the chosen path only."""
        self._computation_count += 1
        return self

    def measure(self) -> int:
        """Already evaluated, just return."""
        return self.path

    def get_probability_distribution(self, detector_positions: np.ndarray,
                                      slit_positions: np.ndarray,
                                      wavelength: float) -> np.ndarray:
        """No interference: just the path distribution."""
        # Each particle goes through one slit → no interference
        pattern = np.zeros(len(detector_positions))
        slit_pos = slit_positions[self.path]
        # Gaussian spread from chosen slit
        sigma = wavelength * 2
        pattern = np.exp(-0.5 * ((detector_positions - slit_pos) / sigma) ** 2)
        pattern /= pattern.sum()
        self._computation_count += len(detector_positions)
        return pattern


# ─── Double Slit Experiment ───

def double_slit_experiment(n_particles: int = 10000,
                           n_detectors: int = 100,
                           lazy: bool = True) -> dict:
    """Simulate double-slit experiment."""
    slit_positions = np.array([-0.5, 0.5])
    detector_positions = np.linspace(-3, 3, n_detectors)
    wavelength = 1.0

    total_pattern = np.zeros(n_detectors)
    total_computations = 0

    t_start = time.time()

    for _ in range(n_particles):
        if lazy:
            state = LazyState(n_paths=2)
            pattern = state.get_probability_distribution(
                detector_positions, slit_positions, wavelength)
            total_computations += state._computation_count
        else:
            state = EagerState(n_paths=2)
            pattern = state.get_probability_distribution(
                detector_positions, slit_positions, wavelength)
            total_computations += state._computation_count

        total_pattern += pattern

    t_elapsed = time.time() - t_start
    total_pattern /= total_pattern.sum()

    # Measure interference visibility
    max_val = total_pattern.max()
    min_val = total_pattern[n_detectors//4:3*n_detectors//4].min()
    visibility = (max_val - min_val) / (max_val + min_val) if (max_val + min_val) > 0 else 0

    return {
        "pattern": total_pattern,
        "positions": detector_positions,
        "visibility": visibility,
        "computations": total_computations,
        "time": t_elapsed,
        "mode": "lazy" if lazy else "eager"
    }


# ─── Computational Cost Analysis ───

def cost_analysis():
    """Compare computational costs for different N."""
    print("\n=== Computational Cost: Lazy vs Eager ===\n")

    n_values = [10, 50, 100, 500, 1000, 5000]
    results = []

    for n in n_values:
        lazy_r = double_slit_experiment(n_particles=n, n_detectors=50, lazy=True)
        eager_r = double_slit_experiment(n_particles=n, n_detectors=50, lazy=False)
        ratio = eager_r["time"] / max(lazy_r["time"], 1e-10)
        results.append({
            "N": n,
            "lazy_time": lazy_r["time"],
            "eager_time": eager_r["time"],
            "lazy_comp": lazy_r["computations"],
            "eager_comp": eager_r["computations"],
            "lazy_vis": lazy_r["visibility"],
            "eager_vis": eager_r["visibility"],
            "time_ratio": ratio
        })

    print(f"  {'N':>6} {'Lazy(s)':>10} {'Eager(s)':>10} {'Ratio':>8} {'Lazy Vis':>10} {'Eager Vis':>10}")
    print(f"  {'-'*6} {'-'*10} {'-'*10} {'-'*8} {'-'*10} {'-'*10}")
    for r in results:
        print(f"  {r['N']:>6} {r['lazy_time']:>10.4f} {r['eager_time']:>10.4f} "
              f"{r['time_ratio']:>7.2f}x {r['lazy_vis']:>10.4f} {r['eager_vis']:>10.4f}")

    return results


# ─── Tension as Evaluation Pressure ───

def tension_evaluation_pressure():
    """Model tension as the cost of maintaining superposition (lazy state)."""
    print("\n=== Tension = Evaluation Pressure ===\n")

    n_states_list = [2, 3, 5, 8, 13, 21, 34, 55]
    results = []

    for n in n_states_list:
        # Uniform superposition
        amplitudes = np.ones(n, dtype=complex) / np.sqrt(n)
        probs = np.abs(amplitudes) ** 2

        # Shannon entropy (= tension proxy)
        entropy = -np.sum(probs * np.log(probs + 1e-15))
        max_entropy = np.log(n)

        # "Evaluation cost" = number of amplitudes to track
        eval_cost = n  # O(n) for lazy
        eager_cost = 1  # O(1) after collapse

        # Tension = entropy / max_entropy (normalized)
        tension = entropy / max_entropy if max_entropy > 0 else 0

        # Savings from lazy evaluation
        savings = eval_cost / eager_cost

        results.append({
            "n_states": n,
            "entropy": entropy,
            "max_entropy": max_entropy,
            "tension": tension,
            "eval_cost": eval_cost,
            "savings": savings
        })

    print(f"  {'States':>8} {'Entropy':>10} {'H_max':>8} {'Tension':>10} {'Lazy Cost':>10} {'Savings':>10}")
    print(f"  {'-'*8} {'-'*10} {'-'*8} {'-'*10} {'-'*10} {'-'*10}")
    for r in results:
        print(f"  {r['n_states']:>8} {r['entropy']:>10.4f} {r['max_entropy']:>8.4f} "
              f"{r['tension']:>10.4f} {r['eval_cost']:>10} {r['savings']:>9.0f}x")

    # Universe scale
    print(f"\n  Universe Scale Analysis:")
    N_universe = 1e80
    print(f"  N particles ~ 10^80")
    print(f"  Lazy cost:  O(N) = O(10^80) per particle")
    print(f"  Eager cost: O(N^2) = O(10^160) for all interactions")
    print(f"  Savings factor: N = 10^80")
    print(f"  With entanglement: O(2^N) worst case for lazy (exponential!)")
    print(f"  This is why quantum simulation is hard: maintaining laziness is expensive")

    return results


# ─── Quantum Speedup Connection ───

def quantum_speedup_analysis():
    """Analyze connection between lazy evaluation and quantum speedups."""
    print("\n=== Lazy Evaluation ↔ Quantum Speedup ===\n")

    # Grover's algorithm: search N items in sqrt(N) steps
    # Interpretation: lazy eval of all N items simultaneously
    N_values = [4, 16, 64, 256, 1024, 4096]

    print(f"  {'N':>6} {'Classical':>12} {'Grover':>10} {'Speedup':>10} {'Lazy States':>12}")
    print(f"  {'-'*6} {'-'*12} {'-'*10} {'-'*10} {'-'*12}")
    for N in N_values:
        classical = N
        grover = int(np.sqrt(N))
        speedup = N / grover
        # Lazy: maintain N amplitude states
        lazy_states = N
        print(f"  {N:>6} {classical:>12} {grover:>10} {speedup:>9.1f}x {lazy_states:>12}")

    print(f"""
  Interpretation:
    Classical search = eager: check one item at a time → O(N)
    Grover search = lazy: maintain N amplitudes → interference → O(sqrt(N))
    The 'cost' of laziness: storing N complex amplitudes
    The 'benefit': interference cancels wrong answers

    Shor's factoring:
      Classical: O(exp(n^(1/3)))
      Quantum:   O(n^3)
      Lazy interpretation: QFT maintains all period candidates simultaneously
""")


# ─── Main ───

if __name__ == "__main__":
    print("=" * 70)
    print("  H-SIM-6: Wavefunction Collapse = Lazy Evaluation")
    print("  Double-Slit Simulation + Cost Analysis")
    print("=" * 70)

    # 1. Double-slit: lazy vs eager
    print("\n--- Double-Slit Experiment ---")
    lazy_result = double_slit_experiment(n_particles=5000, n_detectors=80, lazy=True)
    eager_result = double_slit_experiment(n_particles=5000, n_detectors=80, lazy=False)

    print(f"\n  Lazy (quantum-like):  visibility = {lazy_result['visibility']:.4f}")
    print(f"  Eager (classical):   visibility = {eager_result['visibility']:.4f}")
    print(f"  Visibility ratio: {lazy_result['visibility']/max(eager_result['visibility'],0.001):.2f}x")

    # ASCII graph: interference pattern
    print("\n  Lazy (interference pattern):")
    print("  " + "-" * 60)
    pattern = lazy_result["pattern"]
    positions = lazy_result["positions"]
    max_p = pattern.max()
    for i in range(0, len(pattern), 2):
        bar_len = int(pattern[i] / max_p * 50)
        pos_str = f"{positions[i]:>5.1f}"
        print(f"  {pos_str} |{'#' * bar_len}")

    print(f"\n  Eager (no interference):")
    print("  " + "-" * 60)
    pattern_e = eager_result["pattern"]
    max_pe = pattern_e.max()
    for i in range(0, len(pattern_e), 2):
        bar_len = int(pattern_e[i] / max_pe * 50)
        pos_str = f"{positions[i]:>5.1f}"
        print(f"  {pos_str} |{'=' * bar_len}")

    # 2. Cost analysis
    cost_results = cost_analysis()

    # ASCII graph: computation cost
    print("\n  ASCII Graph: Computations (Lazy vs Eager)")
    print("  " + "-" * 55)
    max_comp = max(r["lazy_comp"] for r in cost_results)
    for r in cost_results:
        lazy_bar = int(r["lazy_comp"] / max_comp * 40)
        eager_bar = int(r["eager_comp"] / max_comp * 40)
        print(f"  N={r['N']:>5} L|{'#'*lazy_bar}{' '*(40-lazy_bar)}| {r['lazy_comp']:>8}")
        print(f"         E|{'='*eager_bar}{' '*(40-eager_bar)}| {r['eager_comp']:>8}")

    # 3. Tension analysis
    tension_results = tension_evaluation_pressure()

    # ASCII graph: tension vs n_states
    print("\n  ASCII Graph: Tension (Evaluation Pressure) vs Number of States")
    print("  " + "-" * 55)
    for r in tension_results:
        bar = int(r["tension"] * 40)
        ebar = int(r["entropy"] / max(rr["entropy"] for rr in tension_results) * 40)
        print(f"  n={r['n_states']:>3} T|{'#'*bar}{' '*(40-bar)}| {r['tension']:.4f}")
        print(f"       H|{'='*ebar}{' '*(40-ebar)}| {r['entropy']:.4f}")

    # 4. Quantum speedup
    quantum_speedup_analysis()

    # 5. H-324 connection
    print("\n=== Connection to H-324: Entropy > Tension ===")
    print("""
  H-324 finding: entropy is better than tension for hallucination detection.

  Lazy evaluation interpretation:
    - Entropy = number of possible states (= lazy evaluation cost)
    - Tension = how 'conflicted' the state is (evaluation pressure)
    - High entropy, low tension = many states but low conflict → lazy is cheap
    - High entropy, high tension = many conflicting states → expensive lazy
    - Low entropy, any tension = few states → eager is fine

  H-324 says entropy > tension for hallucination:
    → Hallucination = too many lazy states (high entropy)
    → Not necessarily high conflict (tension can be low even when hallucinating)
    → The NUMBER of unevaluated possibilities matters more than their conflict

  Simulation interpretation:
    → Hallucination = simulator keeping too many paths alive
    → Collapse (measurement/attention) reduces paths → reduces hallucination
    → This matches: focused attention reduces model hallucination
""")

    # 6. Summary
    print("\n" + "=" * 70)
    print("  SUMMARY")
    print("=" * 70)
    print(f"""
  1. Double-slit:
     - Lazy eval → interference (visibility={lazy_result['visibility']:.4f})
     - Eager eval → no interference (visibility={eager_result['visibility']:.4f})
     - Wavefunction collapse = forcing eager evaluation

  2. Computational savings:
     - Lazy: O(N amplitudes) until measured
     - Eager: O(1) per particle but O(N^2) for interactions
     - Universe (N~10^80): savings factor ~10^80

  3. Tension = evaluation pressure:
     - Uniform superposition: tension = 1.0 (maximum laziness cost)
     - After measurement: tension = 0.0 (fully evaluated)
     - Partial measurement: 0 < tension < 1

  4. Quantum speedup = lazy evaluation benefit:
     - Grover: maintain N lazy states → sqrt(N) speedup
     - Shor: lazy QFT over all periods → polynomial speedup

  5. H-324 connection:
     - Entropy (lazy state count) > tension (conflict) for hallucination
     - Too many lazy paths = hallucination
     - Collapse/attention = forcing evaluation = reducing hallucination
""")

    print("--- DONE ---")
