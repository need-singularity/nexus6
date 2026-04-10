#!/usr/bin/env python3
"""H-CX-474: The TRUE Convergence Map at Depth 1 Only

Since H-CX-467 proved depth-3 saturation is trivial (random constants also
reach 100%), ONLY depth-1 reachability is meaningful.

For each domain independently:
  - All unary ops on each constant: identity, ln, sqrt, 1/x, exp
  - All binary ops on pairs within that domain: +, -, *, /, ^, log_a(b)
Then check which of 24 non-trivial targets each domain can reach (0.1% tolerance).

Finally: Texas Sharpshooter comparison vs random baseline.
"""

import warnings
import sys
import os
import numpy as np
from collections import defaultdict
from itertools import combinations

warnings.filterwarnings("ignore", category=RuntimeWarning)

# Import DOMAINS from convergence_engine
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from convergence_engine import DOMAINS

# ═══════════════════════════════════════════════════════════
# TARGET CONSTANTS (24 non-trivial mathematical constants)
# ═══════════════════════════════════════════════════════════

TARGETS = {
    "e":              np.e,
    "pi":             np.pi,
    "sqrt(2)":        np.sqrt(2),
    "sqrt(3)":        np.sqrt(3),
    "sqrt(5)":        np.sqrt(5),
    "phi":            (1 + np.sqrt(5)) / 2,
    "gamma_EM":       0.5772156649,
    "zeta(3)":        1.2020569031,
    "ln(2)":          np.log(2),
    "ln(3)":          np.log(3),
    "ln(4/3)":        np.log(4/3),
    "1/e":            1 / np.e,
    "GZ_width":       np.log(4/3),         # same as ln(4/3)
    "GZ_center":      1 / np.e,            # same as 1/e
    "GZ_lower":       0.5 - np.log(4/3),
    "pi/2":           np.pi / 2,
    "pi/3":           np.pi / 3,
    "pi/4":           np.pi / 4,
    "pi/6":           np.pi / 6,
    "pi^2/6":         np.pi**2 / 6,
    "e^2":            np.e**2,
    "Catalan":        0.9159655941,
    "Khinchin":       2.6854520010,
    "Feigenbaum_d":   4.66920160910299,
}

# Deduplicate targets with same value
unique_targets = {}
alias_map = defaultdict(list)
for name, val in TARGETS.items():
    found = False
    for uname, uval in unique_targets.items():
        if abs(val - uval) < 1e-12:
            alias_map[uname].append(name)
            found = True
            break
    if not found:
        unique_targets[name] = val
        alias_map[name].append(name)

THRESHOLD = 0.001  # 0.1%


def safe_op(func, *args):
    """Execute operation safely, return None on error."""
    try:
        with np.errstate(all='ignore'):
            result = func(*args)
            if result is None or not np.isfinite(result):
                return None
            if abs(result) > 1e15 or abs(result) < 1e-15:
                return None
            return float(result)
    except:
        return None


def compute_depth1_values(constants):
    """Compute all depth-1 reachable values from a set of constants."""
    values = set()
    vals = list(constants.values())

    # Unary operations on each constant
    for v in vals:
        # identity
        values.add(v)
        # ln
        r = safe_op(np.log, v)
        if r is not None:
            values.add(r)
        # sqrt
        r = safe_op(np.sqrt, v)
        if r is not None:
            values.add(r)
        # 1/x
        if v != 0:
            r = safe_op(lambda x: 1.0 / x, v)
            if r is not None:
                values.add(r)
        # exp
        r = safe_op(np.exp, v)
        if r is not None:
            values.add(r)

    # Binary operations on all pairs (including same constant with itself)
    for i, a in enumerate(vals):
        for j, b in enumerate(vals):
            # +
            r = safe_op(lambda x, y: x + y, a, b)
            if r is not None:
                values.add(r)
            # -
            r = safe_op(lambda x, y: x - y, a, b)
            if r is not None:
                values.add(r)
            # *
            r = safe_op(lambda x, y: x * y, a, b)
            if r is not None:
                values.add(r)
            # /
            if b != 0:
                r = safe_op(lambda x, y: x / y, a, b)
                if r is not None:
                    values.add(r)
            # ^
            r = safe_op(lambda x, y: x ** y, a, b)
            if r is not None:
                values.add(r)
            # log_a(b)
            if a > 0 and a != 1 and b > 0:
                r = safe_op(lambda x, y: np.log(y) / np.log(x), a, b)
                if r is not None:
                    values.add(r)

    return values


def check_targets(values, targets, threshold=THRESHOLD):
    """Check which targets are reachable within threshold."""
    reached = {}
    for tname, tval in targets.items():
        for v in values:
            if tval != 0:
                rel_err = abs(v - tval) / abs(tval)
            else:
                rel_err = abs(v - tval)
            if rel_err <= threshold:
                if tname not in reached or rel_err < reached[tname]:
                    reached[tname] = rel_err
                break
        # If not found yet, check more carefully (set iteration is random)
        if tname not in reached:
            best_err = float('inf')
            for v in values:
                if tval != 0:
                    rel_err = abs(v - tval) / abs(tval)
                else:
                    rel_err = abs(v - tval)
                if rel_err < best_err:
                    best_err = rel_err
            if best_err <= threshold:
                reached[tname] = best_err
    return reached


def generate_random_domain(n_constants, rng):
    """Generate a random domain with n_constants values."""
    consts = {}
    for i in range(n_constants):
        # Mix of small and large random constants
        if rng.random() < 0.5:
            consts[f"r{i}"] = rng.uniform(0.1, 10.0)
        else:
            consts[f"r{i}"] = rng.uniform(1.0, 500.0)
    return consts


# ═══════════════════════════════════════════════════════════
# MAIN COMPUTATION
# ═══════════════════════════════════════════════════════════

print("=" * 72)
print("H-CX-474: TRUE Convergence Map — Depth 1 Only")
print("=" * 72)
print()
print(f"Threshold: {THRESHOLD*100:.1f}%")
print(f"Unique targets: {len(unique_targets)}")
print(f"Domains: {len(DOMAINS)}")
print()

# Step 1: Compute depth-1 reachable values per domain
domain_values = {}
domain_reached = {}
domain_sizes = {}

for dkey, dinfo in DOMAINS.items():
    cname = dinfo["name"]
    consts = dinfo["constants"]
    n_consts = len(consts)

    print(f"  [{dkey}] {cname}: {n_consts} constants ... ", end="", flush=True)

    values = compute_depth1_values(consts)
    domain_values[dkey] = values
    domain_sizes[dkey] = n_consts

    reached = check_targets(values, unique_targets)
    domain_reached[dkey] = reached

    print(f"{len(values)} depth-1 values, {len(reached)}/{len(unique_targets)} targets reached")

print()

# Step 2: Build convergence ranking table
print("=" * 72)
print("DEPTH-1 CONVERGENCE RANKING TABLE")
print("=" * 72)
print()

# For each target, which domains reach it?
target_domains = defaultdict(list)
for tname in unique_targets:
    for dkey in DOMAINS:
        if tname in domain_reached[dkey]:
            target_domains[tname].append(dkey)

# Sort by number of domains (descending), then by name
ranking = sorted(unique_targets.keys(), key=lambda t: (-len(target_domains[t]), t))

# Print header
print(f"{'Target':<18} {'Value':>10} {'#Dom':>5}  {'Domains':<35} {'Aliases'}")
print("-" * 100)

for tname in ranking:
    tval = unique_targets[tname]
    doms = target_domains[tname]
    n_doms = len(doms)
    dom_str = ",".join(sorted(doms)) if doms else "(none)"
    aliases = alias_map[tname]
    alias_str = ", ".join(a for a in aliases if a != tname)
    if alias_str:
        alias_str = f"= {alias_str}"
    print(f"  {tname:<16} {tval:>10.6f} {n_doms:>5}  {dom_str:<35} {alias_str}")

print()

# Summary statistics
n_reached_by = defaultdict(int)
for tname in unique_targets:
    n_doms = len(target_domains[tname])
    n_reached_by[n_doms] += 1

print("Distribution of target reachability:")
for k in sorted(n_reached_by.keys()):
    bar = "#" * n_reached_by[k]
    print(f"  {k} domains: {n_reached_by[k]:>3} targets  {bar}")

total_reached = sum(1 for t in unique_targets if len(target_domains[t]) > 0)
print(f"\n  Total reachable: {total_reached}/{len(unique_targets)}")
print(f"  Unreachable:     {len(unique_targets) - total_reached}/{len(unique_targets)}")

# Step 3: Domain-specific constants (only 1 domain reaches them)
print()
print("=" * 72)
print("DOMAIN-SPECIFIC CONSTANTS (reachable from exactly 1 domain)")
print("=" * 72)
print()

domain_specific = {t: target_domains[t] for t in unique_targets if len(target_domains[t]) == 1}
if domain_specific:
    for tname in sorted(domain_specific.keys()):
        dkey = domain_specific[tname][0]
        dname = DOMAINS[dkey]["name"]
        print(f"  {tname:<16} -> [{dkey}] {dname}")
else:
    print("  (none)")

# Step 4: High-convergence targets (3+ domains)
print()
print("=" * 72)
print("HIGH-CONVERGENCE TARGETS (3+ domains)")
print("=" * 72)
print()

high_conv = {t: target_domains[t] for t in unique_targets if len(target_domains[t]) >= 3}
if high_conv:
    for tname in sorted(high_conv.keys(), key=lambda t: -len(target_domains[t])):
        doms = target_domains[tname]
        print(f"  {tname:<16} ({len(doms)} domains): {', '.join(sorted(doms))}")
else:
    print("  (none)")

# Step 5: Domain-wise ASCII heatmap
print()
print("=" * 72)
print("DOMAIN x TARGET HEATMAP (X = reached at depth 1)")
print("=" * 72)
print()

# Short target names for display
short_targets = [t[:12] for t in ranking]
domain_keys = sorted(DOMAINS.keys())

# Print header
print(f"{'Target':<18}", end="")
for dk in domain_keys:
    print(f" {dk}", end="")
print(f"  #")
print("-" * (18 + 3 * len(domain_keys) + 4))

for tname in ranking:
    print(f"  {tname:<16}", end="")
    count = 0
    for dk in domain_keys:
        if tname in domain_reached[dk]:
            print(f" X", end="")
            count += 1
        else:
            print(f" .", end="")
    print(f"  {count}")

print()

# Step 6: Per-domain summary
print("=" * 72)
print("PER-DOMAIN SUMMARY")
print("=" * 72)
print()

print(f"{'Domain':<6} {'Name':<25} {'#Const':>6} {'#D1vals':>8} {'#Targets':>8} {'Rate':>8}")
print("-" * 65)
for dk in sorted(DOMAINS.keys()):
    dname = DOMAINS[dk]["name"]
    nc = domain_sizes[dk]
    nv = len(domain_values[dk])
    nr = len(domain_reached[dk])
    rate = nr / len(unique_targets) * 100
    bar = "#" * nr
    print(f"  {dk:<4} {dname:<25} {nc:>6} {nv:>8} {nr:>8} {rate:>7.1f}%  {bar}")

print()

# ═══════════════════════════════════════════════════════════
# TEXAS SHARPSHOOTER: Random baseline comparison
# ═══════════════════════════════════════════════════════════

print("=" * 72)
print("TEXAS SHARPSHOOTER: Random Baseline Comparison")
print("=" * 72)
print()

N_RANDOM_TRIALS = 1000
rng = np.random.RandomState(42)

# For each domain size, run random trials
# Use median domain size for baseline
domain_size_list = [domain_sizes[dk] for dk in DOMAINS]
median_size = int(np.median(domain_size_list))

print(f"Random baseline: {N_RANDOM_TRIALS} trials, each with {median_size} random constants")
print(f"Same unary/binary operations, same 0.1% threshold")
print()

random_hit_counts = []
for trial in range(N_RANDOM_TRIALS):
    rand_consts = generate_random_domain(median_size, rng)
    rand_values = compute_depth1_values(rand_consts)
    rand_reached = check_targets(rand_values, unique_targets)
    random_hit_counts.append(len(rand_reached))

random_mean = np.mean(random_hit_counts)
random_std = np.std(random_hit_counts)
random_median = np.median(random_hit_counts)
random_max = np.max(random_hit_counts)

print(f"Random baseline results:")
print(f"  Mean:   {random_mean:.2f} +/- {random_std:.2f}")
print(f"  Median: {random_median:.1f}")
print(f"  Max:    {random_max}")
print()

# Distribution of random hits
print("Random hit distribution:")
max_hits = int(random_max) + 1
hist = np.zeros(max_hits + 1, dtype=int)
for h in random_hit_counts:
    hist[int(h)] += 1

for i in range(max_hits + 1):
    if hist[i] > 0:
        bar = "#" * (hist[i] * 50 // N_RANDOM_TRIALS)
        print(f"  {i:>3} targets: {hist[i]:>4} trials ({hist[i]/N_RANDOM_TRIALS*100:>5.1f}%)  {bar}")

print()

# Compare actual domains vs random
print("Actual domains vs random baseline:")
print(f"{'Domain':<6} {'Actual':>7} {'Z-score':>8} {'p-value':>10} {'Sig':>5}")
print("-" * 45)

for dk in sorted(DOMAINS.keys()):
    actual = len(domain_reached[dk])
    if random_std > 0:
        z = (actual - random_mean) / random_std
    else:
        z = 0
    # One-tailed p-value
    p_value = sum(1 for h in random_hit_counts if h >= actual) / N_RANDOM_TRIALS
    sig = ""
    if p_value < 0.001:
        sig = "***"
    elif p_value < 0.01:
        sig = "**"
    elif p_value < 0.05:
        sig = "*"
    print(f"  {dk:<4} {actual:>7} {z:>8.2f} {p_value:>10.4f} {sig:>5}")

print()

# Overall: for the HIGH-CONVERGENCE targets (3+ domains),
# how often does a random set of 8 domains produce similar convergence?
print("=" * 72)
print("CONVERGENCE ANALYSIS: How many targets have 3+ domain overlap?")
print("=" * 72)
print()

actual_3plus = sum(1 for t in unique_targets if len(target_domains[t]) >= 3)
print(f"Actual: {actual_3plus} targets reachable from 3+ domains")
print()

# Simulate: 8 random domains, check 3+ overlap
N_SIM = 200
random_3plus_counts = []
for sim in range(N_SIM):
    sim_domain_reached_sets = []
    for d in range(8):
        n_c = domain_size_list[d % len(domain_size_list)]
        rand_consts = generate_random_domain(n_c, rng)
        rand_values = compute_depth1_values(rand_consts)
        rand_reached = check_targets(rand_values, unique_targets)
        sim_domain_reached_sets.append(set(rand_reached.keys()))

    # Count targets with 3+ domain overlap
    count_3plus = 0
    for tname in unique_targets:
        n_hit = sum(1 for s in sim_domain_reached_sets if tname in s)
        if n_hit >= 3:
            count_3plus += 1
    random_3plus_counts.append(count_3plus)

r3_mean = np.mean(random_3plus_counts)
r3_std = np.std(random_3plus_counts)
r3_max = np.max(random_3plus_counts)

print(f"Random 8-domain simulation ({N_SIM} trials):")
print(f"  Mean 3+ overlap: {r3_mean:.2f} +/- {r3_std:.2f}")
print(f"  Max 3+ overlap:  {r3_max}")
if r3_std > 0:
    z_overall = (actual_3plus - r3_mean) / r3_std
else:
    z_overall = float('inf') if actual_3plus > r3_mean else 0
p_overall = sum(1 for c in random_3plus_counts if c >= actual_3plus) / N_SIM

print(f"\n  Actual vs Random:")
print(f"    Actual 3+ overlap:  {actual_3plus}")
print(f"    Random mean:        {r3_mean:.2f}")
print(f"    Z-score:            {z_overall:.2f}")
print(f"    p-value:            {p_overall:.4f}")

if p_overall < 0.01:
    verdict = "SIGNIFICANT (p < 0.01) — convergence is NOT random"
elif p_overall < 0.05:
    verdict = "WEAKLY SIGNIFICANT (p < 0.05)"
else:
    verdict = "NOT SIGNIFICANT — convergence could be random at depth 1"

print(f"    Verdict:            {verdict}")

print()
print("=" * 72)
print("H-CX-474 VERIFICATION COMPLETE")
print("=" * 72)
