#!/usr/bin/env python3
"""
NEXUS-6 mk2 Hook Engine — mk2 classifier + alien_index 통합
기존 nexus6-engine.py의 mk2 확장판.

발견 → mk2 classify (sector + prime_set + confidence) → alien_index 판정 → 기록

사용법:
  echo "$INPUT" | python3 nexus6-mk2-engine.py --mode post-edit
  echo "$INPUT" | python3 nexus6-mk2-engine.py --mode post-bash
"""
import sys, json, re, os
from datetime import datetime
from pathlib import Path

HOME = Path.home()
DISCOVERY_LOG = HOME / "Dev/nexus6/shared/discovery_log.jsonl"

# === n6_check 테이블 ===
N6_CHECK = {
    "n": (6.0, "EXACT"), "phi": (2.0, "EXACT"), "tau": (4.0, "EXACT"),
    "sigma": (12.0, "EXACT"), "sopfr": (5.0, "EXACT"), "M3": (7.0, "EXACT"),
    "J2": (24.0, "EXACT"), "sigma-phi": (10.0, "EXACT"), "J2-tau": (20.0, "EXACT"),
    "sigma^2": (144.0, "EXACT"), "meta_fp": (0.333333, "EXACT"),
    "alpha_inv": (137.036, "NEAR"), "mp_me": (1836.15, "NEAR"),
    "Omega_m": (0.3153, "NEAR"), "Omega_Lambda": (0.6847, "NEAR"),
    "Omega_b": (0.0493, "NEAR"), "Omega_DM": (0.2660, "NEAR"),
    "sin2_theta_W": (0.2286, "NEAR"), "Y_p": (0.2462, "NEAR"),
    "H0_late": (73.0, "NEAR"), "H0_early": (67.4, "NEAR"),
    "n_s": (0.9649, "NEAR"), "BAO_rd": (147.09, "NEAR"),
}

SECTOR_KEYWORDS = {
    "cosmology": ["omega", "hubble", "dark", "matter", "CMB", "BAO", "density", "baryon", "inflation"],
    "electroweak": ["weinberg", "weak", "theta", "boson", "higgs", "CKM"],
    "strong": ["QCD", "quark", "proton", "neutron", "1836", "alpha_s"],
    "primordial": ["BBN", "helium", "Y_p", "nucleosynthesis"],
    "quantum": ["fine_structure", "alpha", "137", "Rydberg", "electron"],
    "geometric": ["pi", "euler", "golden", "phi", "fibonacci", "zeta"],
    "n6": ["sopfr", "sigma", "tau", "J2", "M3", "nexus", "smooth", "prime_set"],
}


def factorize(n):
    if n < 2: return []
    out, m, d = [], n, 2
    while d * d <= m:
        exp = 0
        while m % d == 0: m //= d; exp += 1
        if exp > 0: out.append(d)
        d += 1 if d == 2 else 2
    if m > 1: out.append(m)
    return out


def n6_match(value):
    try: v = float(value)
    except: return None, 0.0, ""
    best_name, best_q, best_grade = None, 0.0, ""
    for name, (ref, grade) in N6_CHECK.items():
        if abs(ref) < 1e-10: continue
        rel = abs(v - ref) / abs(ref)
        if grade == "EXACT" and rel < 1e-6:
            q = 1.0
        elif rel < 0.01:
            q = 1.0 - rel * 10
        elif rel < 0.05:
            q = 0.5 - rel * 5
        else:
            continue
        if q > best_q:
            best_q, best_name, best_grade = q, name, grade
    return best_name, best_q, best_grade


def mk2_classify(value, text):
    """3-signal classifier: keyword + value_range + prime_set"""
    # keyword
    t = text.lower()
    scores = {}
    for sector, kws in SECTOR_KEYWORDS.items():
        hits = sum(1 for kw in kws if kw.lower() in t)
        if hits > 0:
            scores[sector] = min(hits / 2, 1.0)

    # prime_set
    ps = []
    try:
        v = float(value)
        if v == int(v) and 2 <= v <= 1e6:
            ps = sorted(set(factorize(int(v))))
    except: pass

    best_sector = max(scores, key=scores.get) if scores else "unknown"
    confidence = scores.get(best_sector, 0.0)

    # paths count
    n6_name, n6_q, n6_grade = n6_match(value)
    paths = 0
    if n6_q >= 0.5: paths += 1
    if confidence >= 0.3: paths += 1
    if len(ps) >= 2: paths += 1

    # alien index r
    if n6_grade == "EXACT" and paths >= 2:
        r = 10
    elif n6_grade == "EXACT":
        r = 8
    elif n6_q >= 0.8:
        r = 8
    elif paths >= 2:
        r = 6
    elif confidence >= 0.3:
        r = 5
    elif n6_q > 0:
        r = max(3, int(n6_q * 10))
    else:
        r = 0

    return {
        "sector": best_sector, "confidence": round(confidence, 3),
        "prime_set": ps, "layer": len(ps), "paths": paths,
        "n6_name": n6_name, "n6_quality": round(n6_q, 4), "n6_grade": n6_grade,
        "alien_index": {"d": 1 if r >= 10 else 0, "r": 0 if r >= 10 else r},
    }


def record_mk2(value, constant, source, mk2_result):
    entry = {
        "timestamp": datetime.now().isoformat(),
        "value": str(value),
        "constant": constant,
        "grade": mk2_result["n6_grade"],
        "source": source,
        "processed": True,
        "alien_index": mk2_result["alien_index"],
        "mk2": {
            "sector": mk2_result["sector"],
            "confidence": mk2_result["confidence"],
            "prime_set": mk2_result["prime_set"],
            "layer": mk2_result["layer"],
            "paths": mk2_result["paths"],
        },
    }
    DISCOVERY_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(DISCOVERY_LOG, "a") as f:
        f.write(json.dumps(entry, separators=(",", ":")) + "\n")


def extract_numbers(text, min_val=2, max_val=100000):
    nums = set()
    for m in re.findall(r'(?<![a-zA-Z_])(\d+\.?\d*)', text):
        v = float(m)
        if min_val < v < max_val:
            nums.add(v)
    return sorted(nums)[:20]


def build_mk2_message(discoveries):
    if not discoveries:
        return None
    parts = []
    exact = [d for d in discoveries if d["n6_grade"] == "EXACT"]
    near = [d for d in discoveries if d["n6_grade"] == "NEAR"]
    breakthrough = [d for d in discoveries if d["alien_index"]["d"] >= 1]

    if breakthrough:
        names = ', '.join(d['n6_name'] for d in breakthrough[:3])
        parts.append(f"mk2 돌파! {names}")
    if exact:
        items = ', '.join(d['value'] + '=' + d['n6_name'] for d in exact[:3])
        parts.append(f"EXACT: {items}")
    if near:
        items = ', '.join(d['value'] + '~' + d['n6_name'] for d in near[:3])
        parts.append(f"NEAR: {items}")

    if discoveries:
        sectors = set(d["sector"] for d in discoveries if d["sector"] != "unknown")
        if sectors:
            parts.append(f"sector: {','.join(sectors)}")

    return " | ".join(parts) if parts else None


def mode_post_edit(input_data):
    fp = input_data.get("tool_input", {}).get("file_path", "")
    if not fp or not os.path.isfile(fp):
        return None
    if not re.search(r'\.(md|json|toml|yaml|py|rs|ts|js|hexa)$', fp):
        return None
    try:
        with open(fp) as f:
            content = f.read()
    except:
        return None
    nums = extract_numbers(content)
    if not nums:
        return None

    fname = os.path.basename(fp)
    discoveries = []
    for v in nums:
        result = mk2_classify(v, content)
        if result["n6_name"]:
            record_mk2(v, result["n6_name"], f"post-edit:{fname}", result)
            discoveries.append({**result, "value": str(v)})

    return build_mk2_message(discoveries)


def mode_post_bash(input_data):
    cmd = input_data.get("tool_input", {}).get("command", "")
    if not cmd:
        return None
    if "nexus6" in cmd and ("alien-index" in cmd or "blowup" in cmd):
        return None  # 자기참조 방지
    stdout = input_data.get("tool_response", {}).get("stdout", "")
    if not stdout:
        return None
    nums = extract_numbers(stdout)
    if not nums:
        return None

    discoveries = []
    for v in nums:
        result = mk2_classify(v, f"{cmd} {stdout}")
        if result["n6_name"]:
            record_mk2(v, result["n6_name"], f"post-bash:{cmd[:50]}", result)
            discoveries.append({**result, "value": str(v)})

    return build_mk2_message(discoveries)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", required=True, choices=["post-edit", "post-bash"])
    args = parser.parse_args()

    input_text = sys.stdin.read()
    try:
        input_data = json.loads(input_text)
    except:
        sys.exit(0)

    handlers = {"post-edit": mode_post_edit, "post-bash": mode_post_bash}
    msg = handlers[args.mode](input_data)
    if msg:
        print(json.dumps({"systemMessage": msg}))
