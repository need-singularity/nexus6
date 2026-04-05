#!/usr/bin/env python3
"""
mk2 classifier v2: keyword + value_range + prime_set scoring.

Solves Phase 4 finding: electroweak 100% false positive when using
prime_set alone. Here we combine 3 signals with weighted scoring.

Usage:
  python3 tools/mk2_classify_v2.py [topology_mk2.jsonl]
"""
import json
import re
import sys
from pathlib import Path
from collections import Counter


def factorize(n):
    if n < 2: return []
    out, m, d = [], n, 2
    while d * d <= m:
        e = 0
        while m % d == 0:
            m //= d; e += 1
        if e: out.append((d, e))
        d += 1 if d == 2 else 2
    if m > 1: out.append((m, 1))
    return out


def prime_set_of(n):
    return frozenset(p for p, _ in factorize(n))


# Sector dictionary (inline; can load from sectors.yaml)
SECTORS = {
    "strong": {
        "keywords": ["quark", "color", "gluon", "QCD", "confinement", "baryon"],
        "value_ranges": [(0.33, 0.34), (0.66, 0.67)],
        "prime_set_preferred": [frozenset({2}), frozenset({3}), frozenset({2, 3})],
    },
    "electroweak": {
        "keywords": ["Weinberg", "theta_W", "θ_W", "Cabibbo", "θ_C",
                     "W boson", "Z boson", "electroweak", "CKM", "Jarlskog"],
        "value_ranges": [(0.20, 0.25)],
        "prime_set_required": frozenset({2, 3, 5, 7}),
    },
    "cosmology": {
        "keywords": ["Omega_m", "Omega_Lambda", "Omega_b", "Omega_DM",
                     "dark energy", "dark matter", "Hubble", "H0",
                     "flatness", "Planck 2018", "Ω_m", "Ω_Λ", "Ω_b", "Ω_DM"],
        "value_ranges": [(0.0, 1.0)],
        "prime_set_preferred": [frozenset({5, 7}), frozenset({2, 3, 5}),
                                frozenset({2, 3})],
    },
    "primordial": {
        "keywords": ["BBN", "nucleosynthesis", "helium", "deuterium",
                     "Y_p", "eta_baryon", "baryogenesis", "CMB", "inflation"],
        "value_ranges": [(0.24, 0.26)],
        "prime_set_preferred": [frozenset({2, 3, 5, 13})],
    },
}


def keyword_score(text, sector_kws):
    text_low = text.lower()
    matches = sum(1 for k in sector_kws if k.lower() in text_low)
    return min(1.0, matches / 2.0)  # cap at 1.0


def value_range_score(value, ranges):
    if value is None or not ranges:
        return 0.0
    for lo, hi in ranges:
        if lo <= value <= hi:
            return 1.0
    return 0.0


def prime_set_score(ps, sector_def):
    if "prime_set_required" in sector_def:
        req = sector_def["prime_set_required"]
        return 1.0 if ps == req else (0.5 if req.issubset(ps) else 0.0)
    if "prime_set_preferred" in sector_def:
        for preferred in sector_def["prime_set_preferred"]:
            if ps == preferred:
                return 1.0
            if ps.issuperset(preferred):
                return 0.5
    return 0.0


def extract_all_floats(text):
    """Find all floats in text (0.0 < x < 1000)."""
    out = []
    for m in re.finditer(r'[0-9]+(?:\.[0-9]+)?', text):
        try:
            v = float(m.group())
            if 0.001 < v < 10000:
                out.append(v)
        except ValueError:
            pass
    return out


def classify_v2(invariant_text, prime_set):
    """Score each sector with weighted signals."""
    values = extract_all_floats(invariant_text)
    best_sector = "unknown"
    best_score = 0.0

    for sector_name, sector_def in SECTORS.items():
        kw_s = keyword_score(invariant_text, sector_def["keywords"])
        # Value range: test all extracted values, take max
        val_s = 0.0
        if values and "value_ranges" in sector_def:
            val_s = max(
                (value_range_score(v, sector_def["value_ranges"]) for v in values),
                default=0.0,
            )
        ps_s = prime_set_score(prime_set, sector_def)

        # Weighted sum
        score = 0.5 * kw_s + 0.3 * val_s + 0.2 * ps_s
        if score > best_score:
            best_score = score
            best_sector = sector_name

    # Confidence threshold
    if best_score < 0.3:
        return "unknown", best_score
    return best_sector, best_score


def main():
    input_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(
        "shared/cycle/topology_mk2.jsonl"
    )
    if not input_path.exists():
        print(f"ERROR: {input_path} not found", file=sys.stderr)
        sys.exit(1)

    sector_hist = Counter()
    conf_bucket = Counter()
    confident_samples = {s: [] for s in SECTORS}
    total = 0

    with open(input_path) as f:
        for line in f:
            p = json.loads(line)
            inv = p.get("singularity", {}).get("invariant", "")
            ps = frozenset(p.get("mk2", {}).get("prime_set", []))
            sector, conf = classify_v2(inv, ps)
            sector_hist[sector] += 1
            conf_bucket[round(conf, 1)] += 1
            total += 1
            if sector != "unknown" and conf >= 0.5 and len(confident_samples.get(sector, [])) < 3:
                confident_samples.setdefault(sector, []).append(
                    (p["id"], inv[:80])
                )

    print(f"=== classify_v2 on {total} points ===")
    print("Sector distribution:")
    for s, c in sector_hist.most_common():
        print(f"  {s:<18} {c:>6}  ({100*c/total:.1f}%)")
    print()
    print("Confidence histogram:")
    for conf in sorted(conf_bucket.keys()):
        print(f"  conf≥{conf:.1f}: {conf_bucket[conf]:>6}")
    print()
    print("High-confidence samples (conf≥0.5):")
    for sector, samples in confident_samples.items():
        if not samples:
            continue
        print(f"\n[{sector}]")
        for pid, text in samples:
            print(f"  {pid}: {text}")


if __name__ == "__main__":
    main()
