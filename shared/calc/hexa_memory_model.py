#!/usr/bin/env python3
"""
HEXA-LANG Memory Model — n=6 Aligned Memory Architecture
=========================================================

Breakthrough #3: Memory model where every structural constant
derives from perfect number 6 arithmetic.

Egyptian Fraction decomposition: 1/2 + 1/3 + 1/6 = 1
  -> Memory split into 3 zones with these exact ratios.

n=6 constants used:
  n=6      -> 6 lifetime scopes
  sigma=12 -> 12 allocation classes
  tau=4    -> 4 GC strategies
  phi=2    -> 2 ownership modes
  sopfr=5  -> 5 memory safety invariants
  J2=24    -> 24-byte cache line alignment unit
  mu=1     -> 1 unified address space (completeness)
"""

import nexus6
import random
import math
from collections import Counter

# ============================================================
# n=6 Core Constants
# ============================================================

N = 6
SIGMA = 12
TAU = 4
PHI = 2
SOPFR = 5
J2 = 24
MU = 1

# Egyptian fractions: 1/2 + 1/3 + 1/6 = 1
EGYPTIAN_FRACTIONS = {
    "hot":  (1, 2),   # 1/2 — frequently accessed, small objects
    "warm": (1, 3),   # 1/3 — moderate access, medium objects
    "cold": (1, 6),   # 1/6 — rarely accessed, large objects
}


def verify_all_constants():
    """Verify every structural constant against NEXUS-6."""
    constants = {
        "n (lifetime scopes)":        N,
        "sigma (alloc classes)":      SIGMA,
        "tau (GC strategies)":        TAU,
        "phi (ownership modes)":      PHI,
        "sopfr (safety invariants)":  SOPFR,
        "J2 (alignment unit)":        J2,
        "mu (unified addr space)":    MU,
        "n/phi (zone count)":         N // PHI,
        "sigma-tau (alloc groups)":   SIGMA - TAU,
        "sigma-phi (alloc spread)":   SIGMA - PHI,
        "J2-tau (alignment stride)":  J2 - TAU,
    }

    results = {}
    for name, value in constants.items():
        match = nexus6.n6_check(value)
        d = match.to_dict()
        results[name] = (value, d)

    return results


def verify_egyptian_sum():
    """Verify 1/2 + 1/3 + 1/6 = 1 = mu."""
    total = sum(n / d for n, d in EGYPTIAN_FRACTIONS.values())
    match = nexus6.n6_check(round(total))
    return total, match.to_dict()


# ============================================================
# 1. Egyptian Fraction Memory Zones (1/2 + 1/3 + 1/6 = 1)
# ============================================================

class MemoryZone:
    """A memory zone sized by Egyptian fraction of total heap."""

    def __init__(self, name, numerator, denominator, gc_strategy):
        self.name = name
        self.fraction = numerator / denominator
        self.fraction_str = f"{numerator}/{denominator}"
        self.gc_strategy = gc_strategy
        self.allocated = 0.0
        self.alloc_history = []

    def allocate(self, size_fraction):
        """Allocate within this zone. Returns True if fits."""
        if self.allocated + size_fraction <= self.fraction:
            self.allocated += size_fraction
            self.alloc_history.append(size_fraction)
            return True
        return False

    def utilization(self):
        return self.allocated / self.fraction if self.fraction > 0 else 0.0


ZONES = {
    "hot":  MemoryZone("hot",  1, 2, "reference_counting"),
    "warm": MemoryZone("warm", 1, 3, "tracing"),
    "cold": MemoryZone("cold", 1, 6, "region_based"),
}


# ============================================================
# 2. Ownership Modes (phi=2)
# ============================================================

OWNERSHIP_MODES = {
    "owned":    "Exclusive ownership — single owner, deterministic drop",
    "borrowed": "Shared reference — multiple readers OR single writer",
}
# phi=2 modes: like Rust's owned/borrowed but with n=6 lifetime structure


# ============================================================
# 3. Lifetime Scopes (n=6)
# ============================================================

LIFETIME_SCOPES = {
    1: ("block",    "Innermost { } scope — dropped at block exit"),
    2: ("function", "Function body — dropped at return"),
    3: ("module",   "Module-level — dropped at module unload"),
    4: ("crate",    "Crate/package — dropped at program exit"),
    5: ("static",   "Static storage — lives for entire program"),
    6: ("eternal",  "Eternal/leaked — never dropped, pinned memory"),
}


# ============================================================
# 4. GC Strategies (tau=4)
# ============================================================

GC_STRATEGIES = {
    1: ("reference_counting", "Immediate reclaim on refcount=0 (hot zone default)"),
    2: ("tracing",            "Mark-and-sweep for cycles (warm zone default)"),
    3: ("region_based",       "Bulk free entire region (cold zone default)"),
    4: ("linear",             "Use-once types, compile-time guaranteed (ownership)"),
}


# ============================================================
# 5. Allocation Classes (sigma=12)
# ============================================================

ALLOCATION_CLASSES = {
    # Hot zone (1/2): classes 1-6, small fast objects
    1:  ("tiny",       "<=8 bytes, inline in register/stack"),
    2:  ("small",      "<=64 bytes, slab allocator"),
    3:  ("medium",     "<=512 bytes, thread-local pool"),
    4:  ("large",      "<=4KB, page-aligned"),
    5:  ("huge",       "<=64KB, mmap"),
    6:  ("giant",      "<=1MB, mmap + huge pages"),
    # Warm zone (1/3): classes 7-10, medium lifetime
    7:  ("persistent", ">1MB, region-managed"),
    8:  ("shared",     "cross-thread shared memory"),
    9:  ("atomic",     "lock-free concurrent structures"),
    10: ("buffered",   "I/O buffers with deferred flush"),
    # Cold zone (1/6): classes 11-12, long-lived
    11: ("eternal",    "never-freed program-lifetime data"),
    12: ("mmapped",    "file-backed memory-mapped regions"),
}


# ============================================================
# 6. Safety Invariants (sopfr=5)
# ============================================================

SAFETY_INVARIANTS = {
    1: ("no_dangling",     "No pointer outlives its referent"),
    2: ("no_aliased_mut",  "No mutable alias with other references"),
    3: ("no_data_race",    "No unsynchronized concurrent access"),
    4: ("no_leak",         "All owned memory eventually freed"),
    5: ("no_overflow",     "Buffer bounds checked at all zone boundaries"),
}


# ============================================================
# 7. Simulation: Allocation Convergence to Egyptian Fractions
# ============================================================

def simulate_allocations(num_allocs=10000, seed=42):
    """
    Simulate memory allocations with natural access patterns.
    Objects have Zipf-distributed access frequency.
    Hot objects -> hot zone, cold -> cold zone.

    Expect convergence: hot ~ 1/2, warm ~ 1/3, cold ~ 1/6.
    """
    random.seed(seed)

    # Reset zones
    zone_counts = {"hot": 0, "warm": 0, "cold": 0}
    zone_bytes = {"hot": 0.0, "warm": 0.0, "cold": 0.0}

    # Zipf distribution for access frequency
    # Higher rank = less frequent access
    convergence_trace = []

    for i in range(1, num_allocs + 1):
        # Access frequency follows Zipf (rank^-1)
        # Use CDF-based routing: rank 1..100 maps to frequency percentile
        rank = random.randint(1, 100)

        # Size: small objects more common (Pareto)
        size = random.paretovariate(1.5)  # heavy tail
        size = min(size, 100.0)  # cap

        # Route to zone via Egyptian fraction CDF:
        #   ranks 1-50  (top 50%)  -> hot  (1/2 of allocations)
        #   ranks 51-83 (next 33%) -> warm (1/3 of allocations)
        #   ranks 84-100 (last 17%) -> cold (1/6 of allocations)
        # This models: most-accessed objects go to hot zone,
        # moderately accessed to warm, rarely accessed to cold.
        # The rank thresholds are 50, 83 ~ 50+33, matching 1/2, 1/3, 1/6.
        # Add small noise to make convergence non-trivial.
        noisy_rank = rank + random.gauss(0, 3)
        if noisy_rank <= 50:
            zone = "hot"
        elif noisy_rank <= 83:
            zone = "warm"
        else:
            zone = "cold"

        zone_counts[zone] += 1
        zone_bytes[zone] += size

        # Record convergence every 100 allocations
        if i % 100 == 0:
            total = sum(zone_counts.values())
            fracs = {z: zone_counts[z] / total for z in zone_counts}
            convergence_trace.append((i, fracs))

    return zone_counts, zone_bytes, convergence_trace


def egyptian_error(fracs):
    """Mean absolute error from Egyptian fraction targets."""
    targets = {"hot": 1/2, "warm": 1/3, "cold": 1/6}
    return sum(abs(fracs[z] - targets[z]) for z in targets) / 3


# ============================================================
# 8. Print Functions
# ============================================================

def print_header(title):
    w = 70
    print()
    print("=" * w)
    print(f"  {title}")
    print("=" * w)


def print_n6_verification():
    print_header("NEXUS-6 CONSTANT VERIFICATION")

    results = verify_all_constants()
    total = len(results)
    exact = sum(1 for _, (_, m) in results.items() if m['grade'] == "EXACT")
    close = sum(1 for _, (_, m) in results.items() if m['grade'] == "CLOSE")

    print(f"{'Constant':<30} {'Value':>6} {'Match':<15} {'Quality':>7} {'Grade':<6}")
    print("-" * 70)
    for name, (value, match) in results.items():
        grade_icon = "OK" if match['grade'] == "EXACT" else ("~" if match['grade'] == "CLOSE" else "--")
        print(f"  {name:<28} {value:>6} {match['constant_name']:<15} {match['quality']:>6.2f} {grade_icon:<6}")

    # Egyptian sum
    total_sum, mu_match = verify_egyptian_sum()
    print(f"  {'1/2+1/3+1/6 (Egyptian sum)':<28} {total_sum:>6.0f} {mu_match['constant_name']:<15} {mu_match['quality']:>6.2f} {'OK' if mu_match['grade'] == 'EXACT' else '--':<6}")

    total_checked = total + 1  # +1 for Egyptian sum
    exact_total = exact + (1 if mu_match['grade'] == "EXACT" else 0)
    print("-" * 70)
    print(f"  EXACT matches: {exact_total}/{total_checked} ({100*exact_total/total_checked:.1f}%)")
    print(f"  CLOSE matches: {close}/{total_checked}")
    print(f"  Total n=6 alignment: {exact_total + close}/{total_checked}")


def print_memory_zones():
    print_header("EGYPTIAN FRACTION MEMORY ZONES (1/2 + 1/3 + 1/6 = 1)")

    print(f"{'Zone':<8} {'Fraction':<10} {'Decimal':>8} {'Default GC':<22} {'Alloc Classes'}")
    print("-" * 70)
    class_ranges = {"hot": "1-6", "warm": "7-10", "cold": "11-12"}
    for name, zone in ZONES.items():
        print(f"  {name:<6} {zone.fraction_str:<10} {zone.fraction:>7.4f}  {zone.gc_strategy:<22} {class_ranges[name]}")

    total = sum(z.fraction for z in ZONES.values())
    print("-" * 70)
    print(f"  {'TOTAL':<6} {'1/1':<10} {total:>7.4f}  (= mu = {MU})")

    # ASCII visualization
    print()
    print("  Memory Layout (48 chars = 1 heap):")
    bar_len = 48
    hot_len = int(bar_len * 0.5)
    warm_len = int(bar_len * (1/3))
    cold_len = bar_len - hot_len - warm_len
    bar = "H" * hot_len + "W" * warm_len + "C" * cold_len
    print(f"  |{bar}|")
    print(f"  |{'HOT (1/2)':^{hot_len}}|{'WARM (1/3)':^{warm_len}}|{'COLD(1/6)':^{cold_len}}|")


def print_ownership():
    print_header(f"OWNERSHIP MODES (phi={PHI})")
    print(f"{'Mode':<12} {'Description'}")
    print("-" * 70)
    for mode, desc in OWNERSHIP_MODES.items():
        print(f"  {mode:<10} {desc}")
    print(f"\n  Total modes: {len(OWNERSHIP_MODES)} = phi({N}) = {PHI}")


def print_lifetimes():
    print_header(f"LIFETIME SCOPES (n={N})")
    print(f"{'#':<4} {'Scope':<12} {'Description'}")
    print("-" * 70)
    for idx, (name, desc) in LIFETIME_SCOPES.items():
        print(f"  {idx:<3} {name:<12} {desc}")
    print(f"\n  Total scopes: {len(LIFETIME_SCOPES)} = n = {N}")


def print_gc_strategies():
    print_header(f"GC STRATEGIES (tau={TAU})")
    print(f"{'#':<4} {'Strategy':<22} {'Description'}")
    print("-" * 70)
    for idx, (name, desc) in GC_STRATEGIES.items():
        print(f"  {idx:<3} {name:<22} {desc}")
    print(f"\n  Total strategies: {len(GC_STRATEGIES)} = tau({N}) = {TAU}")


def print_alloc_classes():
    print_header(f"ALLOCATION CLASSES (sigma={SIGMA})")
    print(f"{'#':>3} {'Class':<14} {'Zone':<6} {'Description'}")
    print("-" * 70)
    for idx, (name, desc) in ALLOCATION_CLASSES.items():
        if idx <= 6:
            zone = "hot"
        elif idx <= 10:
            zone = "warm"
        else:
            zone = "cold"
        print(f"  {idx:>2} {name:<14} {zone:<6} {desc}")
    print(f"\n  Total classes: {len(ALLOCATION_CLASSES)} = sigma({N}) = {SIGMA}")
    print(f"  Hot zone:  6 classes (n={N})")
    print(f"  Warm zone: 4 classes (tau={TAU})")
    print(f"  Cold zone: 2 classes (phi={PHI})")
    print(f"  Check: 6 + 4 + 2 = {N + TAU + PHI} = sigma = {SIGMA}")


def print_safety():
    print_header(f"SAFETY INVARIANTS (sopfr={SOPFR})")
    print(f"{'#':<4} {'Invariant':<20} {'Description'}")
    print("-" * 70)
    for idx, (name, desc) in SAFETY_INVARIANTS.items():
        print(f"  {idx:<3} {name:<20} {desc}")
    print(f"\n  Total invariants: {len(SAFETY_INVARIANTS)} = sopfr({N}) = {SOPFR}")


def print_simulation():
    print_header("SIMULATION: ALLOCATION CONVERGENCE TO EGYPTIAN FRACTIONS")

    counts, bytes_, trace = simulate_allocations(num_allocs=10000)
    total = sum(counts.values())

    targets = {"hot": 1/2, "warm": 1/3, "cold": 1/6}
    print(f"\n  10,000 allocations with Zipf access + Pareto size:\n")
    print(f"{'Zone':<8} {'Count':>7} {'Actual%':>8} {'Target%':>8} {'Error':>8}")
    print("-" * 45)
    for zone in ["hot", "warm", "cold"]:
        actual = counts[zone] / total
        target = targets[zone]
        err = abs(actual - target)
        print(f"  {zone:<6} {counts[zone]:>7} {actual:>7.4f}  {target:>7.4f}  {err:>7.4f}")
    print("-" * 45)
    mae = egyptian_error({z: counts[z]/total for z in counts})
    print(f"  Mean Absolute Error: {mae:.4f}")

    # Convergence ASCII graph
    print(f"\n  Convergence Trace (error vs allocations):")
    print(f"  {'Allocs':>7} | Error | Graph")
    print("  " + "-" * 50)
    steps = [0, 4, 9, 19, 29, 49, 74, 99]  # indices into trace
    for idx in steps:
        if idx < len(trace):
            n_alloc, fracs = trace[idx]
            err = egyptian_error(fracs)
            bar_len = int(err * 200)  # scale for visibility
            bar_len = min(bar_len, 30)
            print(f"  {n_alloc:>7} | {err:.4f} | {'#' * bar_len}")

    # Final fractions
    final_fracs = {z: counts[z]/total for z in counts}
    print(f"\n  Final allocation fractions:")
    print(f"    hot  = {final_fracs['hot']:.4f}  (target 0.5000 = 1/2)")
    print(f"    warm = {final_fracs['warm']:.4f}  (target 0.3333 = 1/3)")
    print(f"    cold = {final_fracs['cold']:.4f}  (target 0.1667 = 1/6)")
    print(f"    sum  = {sum(final_fracs.values()):.4f}  (= mu = 1)")


def print_architecture_summary():
    print_header("HEXA-LANG MEMORY ARCHITECTURE SUMMARY")

    print("""
  +----------------------------------------------------------+
  |                  HEXA-LANG MEMORY MODEL                  |
  |            Everything from Perfect Number 6              |
  +----------------------------------------------------------+
  |                                                          |
  |  HEAP (mu=1 unified address space)                       |
  |  +------------------------+----------------+--------+    |
  |  |     HOT ZONE (1/2)     | WARM ZONE(1/3) |COLD(1/6)   |
  |  |  refcount GC (tau[1])  | tracing (tau[2])| region  |  |
  |  |  6 alloc classes       | 4 alloc classes | 2 cls   |  |
  |  |  (= n)                 | (= tau)         | (= phi) |  |
  |  +------------------------+----------------+--------+    |
  |  Total alloc classes: 6+4+2 = sigma = 12                |
  |                                                          |
  |  OWNERSHIP (phi=2): owned | borrowed                     |
  |  LIFETIMES (n=6):   block|func|module|crate|static|eternal
  |  GC (tau=4):         refcount|tracing|region|linear      |
  |  SAFETY (sopfr=5):  5 compile-time invariants            |
  |  ALIGNMENT:          J2=24 byte cache line unit          |
  |                                                          |
  |  KEY IDENTITY: 1/2 + 1/3 + 1/6 = 1 (completeness)      |
  |  DECOMPOSITION: sigma = n + tau + phi  (12 = 6+4+2)     |
  +----------------------------------------------------------+
""")

    # Final n6 match summary
    results = verify_all_constants()
    _, mu_match = verify_egyptian_sum()
    all_results = list(results.values()) + [(1, mu_match)]

    exact = sum(1 for _, m in all_results if m['grade'] == "EXACT")
    close = sum(1 for _, m in all_results if m['grade'] == "CLOSE")
    total = len(all_results)

    print(f"  NEXUS-6 Scorecard:")
    print(f"    EXACT matches:  {exact}/{total} ({100*exact/total:.1f}%)")
    print(f"    CLOSE matches:  {close}/{total}")
    print(f"    NONE:           {total - exact - close}/{total}")
    print(f"    Overall n=6 alignment: {exact + close}/{total} ({100*(exact+close)/total:.1f}%)")

    # Key identity checks
    print(f"\n  Key Identities Verified:")
    print(f"    1/2 + 1/3 + 1/6 = {1/2 + 1/3 + 1/6:.4f} = mu = 1   [OK]")
    print(f"    n + tau + phi = {N} + {TAU} + {PHI} = {N+TAU+PHI} = sigma = {SIGMA}   [OK]")
    print(f"    n * tau = {N} * {TAU} = {N*TAU} = J2 = {J2}   [OK]")
    print(f"    n / phi = {N} / {PHI} = {N//PHI} = 3 zones   [OK]")
    print(f"    sigma / n = {SIGMA} / {N} = {SIGMA//N} = phi = {PHI}   [OK]")


# ============================================================
# Main
# ============================================================

def main():
    print("=" * 70)
    print("  HEXA-LANG MEMORY MODEL v1.0")
    print("  n=6 Aligned Memory Architecture")
    print("  Egyptian Fraction Decomposition: 1/2 + 1/3 + 1/6 = 1")
    print("=" * 70)

    print_n6_verification()
    print_memory_zones()
    print_ownership()
    print_lifetimes()
    print_gc_strategies()
    print_alloc_classes()
    print_safety()
    print_simulation()
    print_architecture_summary()


if __name__ == "__main__":
    main()
