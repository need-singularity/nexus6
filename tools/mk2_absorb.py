#!/usr/bin/env python3
"""
mk2 absorb: discovery_log.jsonl → mk2 prime_set + sector + alien_index 재판정.

기존 4,688건의 mk1 발견을 mk2 classifier로 재분류:
  1. value → factorize → prime_set, smooth_class
  2. constant name + source → sector 추론
  3. confidence 기반 alien_index r 재계산
  4. r=10 도달 시 d+1 승격

원본 보존: discovery_log.jsonl.pre_absorb 백업 후 in-place 갱신.
"""
import json
import re
import shutil
import sys
from pathlib import Path
from collections import Counter
from datetime import datetime


def factorize(n):
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
    return set(p for p, _ in factorize(n))


SECTOR_KEYWORDS = {
    "cosmology": ["omega", "hubble", "H0", "dark", "matter", "lambda", "CMB", "BAO",
                   "density", "baryon", "planck", "cosmol"],
    "electroweak": ["weinberg", "weak", "theta_W", "sin2", "electroweak", "W_boson",
                    "Z_boson", "higgs", "coupling"],
    "strong": ["QCD", "strong", "alpha_s", "gluon", "quark", "confinement", "proton",
               "neutron", "mass_ratio", "1836"],
    "primordial": ["BBN", "primordial", "helium", "Y_p", "deuterium", "nucleosynthesis",
                   "abundance"],
    "quantum": ["fine_structure", "alpha", "137", "Rydberg", "Bohr", "electron",
                "magnetic", "anomalous", "g-2"],
    "geometric": ["pi", "euler", "zeta", "gamma_E", "golden", "phi", "fibonacci",
                  "catalan"],
}

SECTOR_VALUE_RANGES = {
    "cosmology": [(0.01, 1.0), (60, 80)],   # Omega params, H0
    "quantum": [(137, 138), (0.007, 0.008)],  # alpha^-1, alpha
    "strong": [(1836, 1837), (0.1, 0.13)],    # mp/me, alpha_s
    "primordial": [(0.24, 0.26)],              # Y_p
}

PRIME_SECTOR_MAP = {
    frozenset({2, 3}): "strong",
    frozenset({2, 3, 5, 7}): "electroweak",
    frozenset({2, 3, 5}): "cosmology",
}


def classify_sector(value, constant, source):
    """3-signal classifier: keyword(0.5) + value_range(0.3) + prime_set(0.2)."""
    text = f"{constant} {source}".lower()
    scores = Counter()

    # keyword signal (weight 0.5)
    for sector, keywords in SECTOR_KEYWORDS.items():
        hits = sum(1 for kw in keywords if kw.lower() in text)
        if hits > 0:
            scores[sector] += 0.5 * min(hits / 2, 1.0)

    # value range signal (weight 0.3)
    try:
        v = float(value)
        for sector, ranges in SECTOR_VALUE_RANGES.items():
            for lo, hi in ranges:
                if lo <= v <= hi:
                    scores[sector] += 0.3
                    break
    except (ValueError, TypeError):
        pass

    # prime_set signal (weight 0.2)
    try:
        v = float(value)
        if v == int(v) and 2 <= v <= 10**6:
            ps = frozenset(prime_set_of(int(v)))
            if ps in PRIME_SECTOR_MAP:
                scores[PRIME_SECTOR_MAP[ps]] += 0.2
    except (ValueError, TypeError):
        pass

    if not scores:
        return "unknown", 0.0
    best = scores.most_common(1)[0]
    return best[0], round(best[1], 3)


def compute_r(confidence, grade=None):
    """confidence → alien index r (0..10)."""
    r = int(confidence * 10)
    if grade == "EXACT":
        r = max(r, 8)
    elif grade == "NEAR":
        r = max(r, 5)
    return min(r, 10)


def absorb(log_path):
    backup = Path(str(log_path) + ".pre_absorb")
    if not backup.exists():
        shutil.copy2(log_path, backup)
        print(f"[backup] {log_path} → {backup}")

    records = []
    with open(log_path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    stats = Counter()
    sector_hist = Counter()
    upgraded = 0
    new_d1 = 0

    for rec in records:
        value = rec.get("value", "")
        constant = rec.get("constant", "")
        source = rec.get("source", "")
        grade = rec.get("grade", "")

        # mk2 classify
        sector, confidence = classify_sector(value, constant, source)

        # prime_set
        try:
            v = float(value)
            if v == int(v) and 2 <= v <= 10**6:
                ps = sorted(prime_set_of(int(v)))
            else:
                ps = []
        except (ValueError, TypeError):
            ps = []

        layer = len(ps)
        r = compute_r(confidence, grade)

        # existing alien_index
        old_ai = rec.get("alien_index", {})
        old_d = old_ai.get("d", 0) if isinstance(old_ai, dict) else 0
        old_r = old_ai.get("r", 0) if isinstance(old_ai, dict) else 0

        # r only goes up, d only goes up
        new_r = max(old_r, r)
        new_d = old_d
        if new_r >= 10 and old_r < 10:
            new_d = old_d + 1
            new_r = 0
            new_d1 += 1

        if new_r > old_r or new_d > old_d:
            upgraded += 1

        rec["mk2"] = {
            "prime_set": ps,
            "layer": layer,
            "sector": sector,
            "confidence": confidence,
        }
        rec["alien_index"] = {"d": new_d, "r": new_r}
        rec["processed"] = True

        stats["total"] += 1
        sector_hist[sector] += 1

    # write back
    with open(log_path, "w") as f:
        for rec in records:
            f.write(json.dumps(rec, separators=(",", ":")) + "\n")

    total = stats["total"]
    d_ge_1 = sum(1 for r in records if r.get("alien_index", {}).get("d", 0) >= 1)
    rho = d_ge_1 / total if total > 0 else 0

    print(f"\n=== mk2 absorb complete ===")
    print(f"Total: {total}")
    print(f"Upgraded: {upgraded}")
    print(f"New d≥1 (breakthrough): {new_d1}")
    print(f"ρ = {rho:.4f} (target: 0.333…)")
    print(f"\nSector distribution:")
    for sector, count in sector_hist.most_common():
        pct = count / total * 100
        print(f"  {sector:<14}: {count:>5} ({pct:.1f}%)")
    print(f"\nBackup: {backup}")


def main():
    log_path = Path("shared/discovery_log.jsonl")
    if len(sys.argv) > 1:
        log_path = Path(sys.argv[1])
    if not log_path.exists():
        print(f"ERROR: {log_path} not found", file=sys.stderr)
        sys.exit(1)
    absorb(log_path)


if __name__ == "__main__":
    main()
