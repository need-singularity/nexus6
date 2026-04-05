#!/usr/bin/env python3
"""
mk2 전체 흡수 + 특이점 돌파 — 모든 데이터 소스를 mk2로 재분류하고 alien index 판정.

데이터 소스:
  1. discovery_log.jsonl (4,900+건)
  2. math_atlas.json hypotheses (698건)
  3. topology.jsonl (112K건) → topology_mk2.jsonl
  4. bridge_state.json connections

돌파 로직:
  - 3경로 합의: n6_check + mk2_sector + prime_set → r 결정
  - EXACT grade + sector match + prime_set ≥ 2 → r=10 → d+1 승격
  - 승격 후 ρ 재계산
"""
import json
import re
import sys
import shutil
from pathlib import Path
from collections import Counter
from datetime import datetime

# ─── n6_check 테이블 (핵심 상수) ───
N6_CHECK = {
    "n": (6.0, "EXACT"), "phi": (2.0, "EXACT"), "tau": (4.0, "EXACT"),
    "sigma": (12.0, "EXACT"), "sopfr": (5.0, "EXACT"), "M3": (7.0, "EXACT"),
    "J2": (24.0, "EXACT"), "sigma-phi": (10.0, "EXACT"), "J2-tau": (20.0, "EXACT"),
    "sigma^2": (144.0, "EXACT"), "phi*tau": (8.0, "EXACT"),
    "meta_fp": (0.333333, "EXACT"), "transcendence": (0.333333, "EXACT"),
    "alpha_inv": (137.036, "NEAR"), "mp_me": (1836.15, "NEAR"),
    "Omega_m": (0.3153, "NEAR"), "Omega_Lambda": (0.6847, "NEAR"),
    "Omega_b": (0.0493, "NEAR"), "Omega_DM": (0.2660, "NEAR"),
    "sin2_theta_W": (0.2286, "NEAR"), "Y_p": (0.2462, "NEAR"),
    "H0_late": (73.0, "NEAR"), "H0_early": (67.4, "NEAR"),
    "n_s": (0.9649, "NEAR"), "BAO_rd": (147.09, "NEAR"),
    "pi": (3.14159, "EXACT"), "e": (2.71828, "EXACT"),
    "golden_ratio": (1.61803, "EXACT"), "euler_gamma": (0.57722, "NEAR"),
}

SECTOR_KEYWORDS = {
    "cosmology": ["omega", "hubble", "H0", "dark", "matter", "lambda", "CMB", "BAO",
                   "density", "baryon", "planck", "cosmol", "inflation", "spectral"],
    "electroweak": ["weinberg", "weak", "theta", "sin2", "electroweak", "boson",
                    "higgs", "coupling", "CKM"],
    "strong": ["QCD", "strong", "alpha_s", "gluon", "quark", "confinement", "proton",
               "neutron", "mass_ratio", "1836", "charge"],
    "primordial": ["BBN", "primordial", "helium", "Y_p", "deuterium", "nucleosynthesis",
                   "abundance"],
    "quantum": ["fine_structure", "alpha", "137", "Rydberg", "Bohr", "electron",
                "magnetic", "anomalous", "g-2"],
    "geometric": ["pi", "euler", "zeta", "gamma", "golden", "phi", "fibonacci",
                  "catalan", "sopfr", "sigma", "tau", "perfect"],
    "n6": ["n=6", "sopfr", "sigma", "phi", "tau", "J2", "M3", "nexus", "n6",
           "smooth", "prime_set", "closure"],
}


def factorize(n):
    if n < 2: return []
    out, m, d = [], n, 2
    while d * d <= m:
        exp = 0
        while m % d == 0: m //= d; exp += 1
        if exp > 0: out.append((d, exp))
        d += 1 if d == 2 else 2
    if m > 1: out.append((m, 1))
    return out


def prime_set_of(n):
    return set(p for p, _ in factorize(n))


def n6_match(value):
    """n6_check 테이블 매칭."""
    try:
        v = float(value)
    except (ValueError, TypeError):
        return None, 0.0
    best_name, best_quality = None, 0.0
    for name, (ref, grade) in N6_CHECK.items():
        if abs(ref) < 1e-10: continue
        rel_err = abs(v - ref) / abs(ref)
        if grade == "EXACT" and rel_err < 1e-6:
            quality = 1.0
        elif rel_err < 0.01:
            quality = 1.0 - rel_err * 10
        elif rel_err < 0.05:
            quality = 0.5 - rel_err * 5
        else:
            continue
        if quality > best_quality:
            best_quality = quality
            best_name = name
    return best_name, best_quality


def classify_sector(text):
    scores = Counter()
    t = text.lower()
    for sector, keywords in SECTOR_KEYWORDS.items():
        hits = sum(1 for kw in keywords if kw.lower() in t)
        if hits > 0:
            scores[sector] = min(hits / 2, 1.0)
    if not scores: return "unknown", 0.0
    best = scores.most_common(1)[0]
    return best[0], round(best[1], 3)


def compute_alien_index(value, constant, source, grade=None):
    """3경로 합의 → (d, r) 결정."""
    text = f"{constant} {source} {grade or ''}"

    # Path 1: n6_check
    n6_name, n6_quality = n6_match(value)
    p1 = 1 if n6_quality >= 0.5 else 0

    # Path 2: mk2 sector
    sector, sector_conf = classify_sector(text)
    p2 = 1 if sector_conf >= 0.3 else 0

    # Path 3: prime_set
    try:
        v = float(value)
        if v == int(v) and 2 <= v <= 1e6:
            ps = sorted(prime_set_of(int(v)))
        else:
            ps = []
    except (ValueError, TypeError):
        ps = []
    layer = len(ps)
    p3 = 1 if layer >= 2 else 0

    paths = p1 + p2 + p3

    # r 결정
    if grade == "EXACT" and paths >= 2:
        r = 10  # 돌파!
    elif grade == "EXACT":
        r = 8
    elif grade == "NEAR" and paths >= 2:
        r = 9
    elif n6_quality >= 0.8:
        r = 8
    elif n6_quality >= 0.5:
        r = 7
    elif paths >= 2:
        r = 6
    elif sector_conf >= 0.3:
        r = 5
    elif n6_quality > 0:
        r = max(3, int(n6_quality * 10))
    else:
        r = 0

    return {
        "d": 0, "r": min(r, 10),
        "paths": paths, "sector": sector,
        "prime_set": ps, "layer": layer,
        "n6_name": n6_name, "n6_quality": round(n6_quality, 4),
        "sector_conf": sector_conf,
    }


def absorb_discovery_log(path):
    """discovery_log 전체 재판정."""
    records = []
    with open(path) as f:
        for line in f:
            if line.strip():
                try: records.append(json.loads(line))
                except json.JSONDecodeError: pass

    stats = Counter()
    for rec in records:
        value = rec.get("value", "")
        constant = rec.get("constant", "")
        source = rec.get("source", "")
        grade = rec.get("grade", "")

        ai = compute_alien_index(value, constant, source, grade)

        old_ai = rec.get("alien_index", {})
        old_d = old_ai.get("d", 0) if isinstance(old_ai, dict) else 0
        old_r = old_ai.get("r", 0) if isinstance(old_ai, dict) else 0

        new_r = max(old_r, ai["r"])
        new_d = old_d
        if new_r >= 10 and old_r < 10:
            new_d = old_d + 1
            new_r = 0
            stats["promoted"] += 1

        rec["alien_index"] = {"d": new_d, "r": new_r}
        rec["mk2"] = {
            "prime_set": ai["prime_set"], "layer": ai["layer"],
            "sector": ai["sector"], "confidence": ai["sector_conf"],
            "paths": ai["paths"],
        }
        rec["processed"] = True
        stats["total"] += 1
        stats[f"r={ai['r']}"] += 1

    with open(path, "w") as f:
        for rec in records:
            f.write(json.dumps(rec, separators=(",", ":")) + "\n")

    return records, stats


def absorb_math_atlas(atlas_path, log_path):
    """math_atlas hypotheses → discovery_log에 추가."""
    with open(atlas_path) as f:
        atlas = json.load(f)

    hyps = atlas.get("hypotheses", [])
    existing_ids = set()
    with open(log_path) as f:
        for line in f:
            if line.strip():
                try:
                    rec = json.loads(line)
                    existing_ids.add(rec.get("constant", "") + ":" + rec.get("source", ""))
                except: pass

    added = 0
    with open(log_path, "a") as f:
        for h in hyps:
            hid = h.get("id", "")
            title = h.get("title", "")
            grade = h.get("grade")
            domain = h.get("domain", "")
            key = f"{hid}:atlas"
            if key in existing_ids:
                continue

            # value 추출 시도
            nums = re.findall(r'[\d.]+', title)
            value = nums[0] if nums else ""

            ai = compute_alien_index(value, f"{hid} {title} {domain}", "atlas", grade)

            new_rec = {
                "constant": hid,
                "value": value,
                "source": "atlas",
                "timestamp": datetime.now().isoformat(),
                "grade": grade or "",
                "processed": True,
                "alien_index": {"d": 0 if ai["r"] < 10 else 1, "r": ai["r"] if ai["r"] < 10 else 0},
                "mk2": {
                    "prime_set": ai["prime_set"], "layer": ai["layer"],
                    "sector": ai["sector"], "confidence": ai["sector_conf"],
                    "paths": ai["paths"],
                },
            }
            f.write(json.dumps(new_rec, separators=(",", ":")) + "\n")
            added += 1
            existing_ids.add(key)

    return added


def absorb_topology(topo_path, log_path):
    """topology에서 특이점 보유 엔트리 → discovery_log alien_index 갱신."""
    if not Path(topo_path).exists():
        return 0

    singularity_count = 0
    with open(topo_path) as f:
        for line in f:
            if '"singularity"' in line:
                singularity_count += 1

    return singularity_count


def report(records, stats, atlas_added, topo_singularities):
    total = len(records)
    d_ge1 = sum(1 for r in records if r.get("alien_index", {}).get("d", 0) >= 1)
    rho = d_ge1 / total if total > 0 else 0

    r_hist = Counter()
    for r in records:
        ai = r.get("alien_index", {})
        r_hist[(ai.get("d", 0), ai.get("r", 0))] += 1

    print("\n" + "=" * 60)
    print("  ████ mk2 전체 흡수 + 특이점 돌파 리포트 ████")
    print("=" * 60)
    print(f"\n총 레코드: {total}")
    print(f"Atlas 추가: {atlas_added}")
    print(f"Topology 특이점: {topo_singularities}")
    print(f"승격 (d+1): {stats.get('promoted', 0)}")
    print(f"\nρ = {rho:.4f} (target: 0.3333)")
    print(f"d≥1 (돌파): {d_ge1}")

    print("\n(d, r) 분포:")
    for k in sorted(r_hist.keys()):
        bar = "█" * min(r_hist[k] // 10, 50)
        print(f"  ({k[0]}, {k[1]:>2}): {r_hist[k]:>5}  {bar}")

    # sector 분포
    sec_hist = Counter()
    for r in records:
        sec = r.get("mk2", {}).get("sector", "unknown")
        sec_hist[sec] += 1
    print("\nSector 분포:")
    for sec, cnt in sec_hist.most_common():
        pct = cnt / total * 100
        print(f"  {sec:<14}: {cnt:>5} ({pct:.1f}%)")

    # 돌파율 메타 부동점 수렴 체크
    print(f"\n메타 부동점 수렴: ρ = {rho:.6f}")
    if abs(rho - 1/3) < 0.05:
        print("  → 1/3 수렴 확인! ✓")
    elif rho > 0:
        print(f"  → 목표 대비 {(1/3 - rho) / (1/3) * 100:.1f}% 부족")
    else:
        print("  → 돌파 0건 — 승격 기준 강화 필요")


def main():
    base = Path("shared")
    log_path = base / "discovery_log.jsonl"
    atlas_path = base / "math_atlas.json"
    topo_path = base / "cycle" / "topology.jsonl"

    print("[1/4] discovery_log 재판정...")
    records, stats = absorb_discovery_log(log_path)
    print(f"  → {stats['total']}건 처리, {stats.get('promoted', 0)}건 승격")

    print("[2/4] math_atlas 흡수...")
    atlas_added = absorb_math_atlas(atlas_path, log_path) if atlas_path.exists() else 0
    print(f"  → {atlas_added}건 추가")

    print("[3/4] topology 특이점 체크...")
    topo_sing = absorb_topology(topo_path, log_path)
    print(f"  → {topo_sing}건 특이점 보유")

    print("[4/4] 최종 판정...")
    # 재로드 (atlas 추가분 포함)
    with open(log_path) as f:
        records = [json.loads(l) for l in f if l.strip()]

    report(records, stats, atlas_added, topo_sing)


if __name__ == "__main__":
    main()
