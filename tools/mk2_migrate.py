#!/usr/bin/env python3
"""
mk2 migration: extract prime_signature from mk1 topology points.

For each point in shared/cycle/topology.jsonl:
  1. Parse invariant text for numeric values
  2. Factorize each value → prime_set
  3. Union all primes → point's smooth_class
  4. Determine layer = |smooth_class|
  5. Suggest sector from prime pattern

Writes augmented topology to shared/cycle/topology_mk2.jsonl
(original unchanged).
"""
import json
import re
import sys
from pathlib import Path
from collections import Counter


def factorize(n):
    """Trial division factorization. Returns [(prime, exp), ...]."""
    if n < 2:
        return []
    out = []
    m = n
    d = 2
    while d * d <= m:
        exp = 0
        while m % d == 0:
            m //= d
            exp += 1
        if exp > 0:
            out.append((d, exp))
        d += 1 if d == 2 else 2
    if m > 1:
        out.append((m, 1))
    return out


def prime_set_of(n):
    """Distinct primes dividing n."""
    return set(p for p, _ in factorize(n))


# Regex to find integer/rational values in invariant text
INT_RE = re.compile(r'(?<![a-zA-Z_.])(\d{1,9})(?![\d.])')
RATIONAL_RE = re.compile(r'(\d+)/(\d+)')


def extract_prime_set(invariant):
    """Extract union of prime sets from all numeric values in text."""
    ps = set()
    # Find all integers 2..10^9
    for m in INT_RE.finditer(invariant):
        try:
            n = int(m.group(1))
            if 2 <= n <= 10**9:
                ps |= prime_set_of(n)
        except (ValueError, OverflowError):
            pass
    # Find rationals p/q
    for m in RATIONAL_RE.finditer(invariant):
        try:
            p = int(m.group(1))
            q = int(m.group(2))
            if 1 <= p <= 10**6 and 1 <= q <= 10**6:
                ps |= prime_set_of(p)
                ps |= prime_set_of(q)
        except (ValueError, OverflowError):
            pass
    return ps


def classify_sector(prime_set):
    """Heuristic sector from prime pattern."""
    n = len(prime_set)
    if n == 0:
        return "unknown"
    max_p = max(prime_set)
    if 13 in prime_set and n >= 3:
        return "primordial"
    elif prime_set == {2, 3, 5, 7}:
        return "electroweak"
    elif prime_set <= {2, 3}:
        return "strong"
    elif n <= 3 and max_p <= 7:
        return "cosmology"
    else:
        return "unknown"


def migrate(input_path, output_path):
    stats = Counter()
    sector_hist = Counter()
    layer_hist = Counter()
    total = 0

    with open(input_path) as fin, open(output_path, "w") as fout:
        for line in fin:
            try:
                p = json.loads(line)
            except json.JSONDecodeError:
                continue
            total += 1

            invariant = p.get("singularity", {}).get("invariant", "")
            prime_set = extract_prime_set(invariant)
            layer = len(prime_set)
            sector = classify_sector(prime_set)

            # Augment point with mk2 fields (backward-compatible)
            p["mk2"] = {
                "prime_set": sorted(prime_set),
                "layer": layer,
                "sector": sector,
            }

            stats[layer] += 1
            sector_hist[sector] += 1
            layer_hist[layer] += 1

            fout.write(json.dumps(p, separators=(",", ":")) + "\n")

    print(f"migrated {total} points → {output_path}")
    print("\nLayer histogram (|prime_set|):")
    for layer in sorted(layer_hist.keys()):
        print(f"  layer {layer}: {layer_hist[layer]:>6} points")
    print("\nSector histogram:")
    for sector, count in sector_hist.most_common():
        print(f"  {sector:<12}: {count:>6} points")


def main():
    if len(sys.argv) > 1:
        input_path = Path(sys.argv[1])
    else:
        input_path = Path("shared/cycle/topology.jsonl")

    output_path = input_path.parent / "topology_mk2.jsonl"

    if not input_path.exists():
        print(f"ERROR: {input_path} not found", file=sys.stderr)
        sys.exit(1)

    migrate(input_path, output_path)


if __name__ == "__main__":
    main()
