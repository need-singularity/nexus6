#!/usr/bin/env python3
"""NEXUS-6 Real Data Validation — test against known n=6 constants.

Loads actual n=6 constants, creates structured test data, runs full scan,
and checks how many constants are rediscovered by the lens engine.

Grading: EXACT (<0.1%), CLOSE (<1%), MISS (>1%)

Usage:
  python3 validate_real_data.py           # Run full validation
  python3 validate_real_data.py --verbose  # Show all matches
"""
import sys, os, time
import numpy as np

try:
    import nexus6
except ImportError:
    print("nexus6 not installed"); sys.exit(1)

# n=6 fundamental constants (from TECS-L model_utils.py)
N6_CONSTANTS = {
    "n": 6, "sigma": 12, "tau": 4, "phi": 2, "mu": 1, "sopfr": 5, "J2": 24,
    "sigma-tau": 8, "sigma-phi": 10, "sigma+tau": 16, "sigma*tau": 48,
    "sigma_sq": 144, "sigma*J2": 288, "2^sigma": 4096, "2^tau": 16,
    "2^sopfr": 32, "2^n": 64, "2^(sigma-tau)": 256, "2^(sigma-sopfr)": 128,
    "tau_sq_over_sigma": 4.0 / 3.0, "ln_4_3": np.log(4.0 / 3.0),
    "inv_e": 1.0 / np.e, "R6": 1.0, "pi_sq_over_6": np.pi**2 / 6.0,
}

VERBOSE = "--verbose" in sys.argv


def build_test_data():
    """Create test matrix embedding n=6 constants."""
    np.random.seed(6)
    n_rows = 100
    d = 6
    data = np.random.randn(n_rows, d) * 0.1

    # Embed constants into feature means
    targets = [12.0, 4.0, 6.0, 24.0, 2.0, 8.0]
    for col, t in enumerate(targets):
        data[:, col] += t

    # Embed ratios between rows
    for i in range(0, min(20, n_rows), 2):
        data[i, 0] = 12.0 + np.random.randn() * 0.01
        data[i, 1] = 4.0 + np.random.randn() * 0.01
        data[i + 1, 0] = 6.0 + np.random.randn() * 0.01
        data[i + 1, 1] = 24.0 + np.random.randn() * 0.01

    return data


def scan_and_collect(data):
    """Run full scan and collect all metric values."""
    n, d = data.shape
    flat = data.flatten().tolist()
    t0 = time.time()
    result = nexus6.scan(flat, n, d)
    elapsed = time.time() - t0

    all_values = []
    lens_count = 0
    for nm in result.lens_names:
        m = result.get_lens(nm)
        if m:
            lens_count += 1
            for key, vals in m.items():
                for v in vals:
                    if np.isfinite(v):
                        all_values.append((nm, key, v))
    return all_values, lens_count, elapsed


def grade_match(value, target):
    """Grade how close a value matches a target constant."""
    if target == 0:
        return ("EXACT", 0.0) if abs(value) < 0.001 else ("MISS", abs(value))
    rel_err = abs(value - target) / abs(target)
    if rel_err < 0.001:
        return ("EXACT", rel_err)
    elif rel_err < 0.01:
        return ("CLOSE", rel_err)
    return ("MISS", rel_err)


def validate():
    print("=== NEXUS-6 Real Data Validation ===\n")

    data = build_test_data()
    print(f"Test data: {data.shape[0]}x{data.shape[1]}, embedded constants: {len(N6_CONSTANTS)}")

    all_values, lens_count, elapsed = scan_and_collect(data)
    print(f"Scan: {elapsed:.2f}s, {lens_count} active lenses, {len(all_values)} metric values\n")

    # Check each constant against all metric values
    results = {"EXACT": [], "CLOSE": [], "MISS": []}

    for const_name, const_val in N6_CONSTANTS.items():
        best_grade, best_err, best_source = "MISS", 1.0, ""
        for lens_name, metric_key, val in all_values:
            grade, err = grade_match(val, const_val)
            if grade != "MISS" and err < best_err:
                best_grade, best_err, best_source = grade, err, f"{lens_name}.{metric_key}"
        results[best_grade].append((const_name, const_val, best_err, best_source))

    # Report
    print(f"{'Constant':<25} {'Value':>10} {'Grade':>7} {'Error':>8} {'Source'}")
    print("-" * 85)

    for grade in ["EXACT", "CLOSE", "MISS"]:
        for name, val, err, source in sorted(results[grade], key=lambda x: x[2]):
            marker = {"EXACT": "+", "CLOSE": "~", "MISS": "-"}[grade]
            err_str = f"{err:.4f}" if grade != "MISS" else "---"
            src_str = source[:40] if source else "not found"
            if VERBOSE or grade != "MISS":
                print(f"  [{marker}] {name:<22} {val:>10.4f} {grade:>7} {err_str:>8}  {src_str}")

    # Summary
    total = len(N6_CONSTANTS)
    exact = len(results["EXACT"])
    close = len(results["CLOSE"])
    miss = len(results["MISS"])
    score = (exact * 1.0 + close * 0.5) / total * 100

    print(f"\n{'='*50}")
    print(f"EXACT: {exact}/{total}  CLOSE: {close}/{total}  MISS: {miss}/{total}")
    print(f"Rediscovery score: {score:.1f}%")
    print(f"Grade: {'A' if score > 60 else 'B' if score > 40 else 'C' if score > 20 else 'D'}")


if __name__ == "__main__":
    validate()
