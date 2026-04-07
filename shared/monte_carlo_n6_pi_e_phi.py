#!/usr/bin/env python3
"""n=6 vs π/e/φ/소수 기반 특수 수 집합 대조 — Monte Carlo N=10000."""
import json, os, random, math, time
from collections import Counter

SCRIPT_DIR = os.path.expanduser("~/Dev/nexus/shared")
REALITY_MAP = os.path.join(SCRIPT_DIR, "reality_map.json")
N_TRIALS = 10_000
RANDOM_RANGE = (1, 30)
RANDOM_SET_SIZE = 7
MAX_EXP = 10
MAX_RESULT = 10_000


NATURAL_ONLY = os.environ.get("NATURAL_ONLY", "1") == "1"


def load_targets(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    tg = []
    total = 0
    for node in data.get("nodes", []):
        total += 1
        if NATURAL_ONLY and node.get("origin") != "natural":
            continue
        m = node.get("measured")
        if isinstance(m, int):
            tg.append(m)
        elif isinstance(m, float) and m == int(m) and m > 0:
            tg.append(int(m))
    print(f"[filter] NATURAL_ONLY={NATURAL_ONLY} total_nodes={total} targets_after_filter={len(tg)}")
    return tg


def comb(a, b):
    if b < 0 or a < 0 or b > a:
        return None
    try:
        return math.comb(a, b)
    except Exception:
        return None


def generate_reachable(constants):
    r = set()
    for a in constants:
        if 0 < a <= MAX_RESULT:
            r.add(a)
    for a in constants:
        for b in constants:
            for v in (a+b, a-b, a*b):
                if 0 < v <= MAX_RESULT:
                    r.add(v)
            if b != 0 and a % b == 0:
                v = a // b
                if 0 < v <= MAX_RESULT:
                    r.add(v)
            if 0 < b <= MAX_EXP and a > 0:
                try:
                    v = a ** b
                    if 0 < v <= MAX_RESULT:
                        r.add(v)
                except Exception:
                    pass
            c = comb(a, b)
            if c is not None and 0 < c <= MAX_RESULT:
                r.add(c)
    return r


def count_hits(reach, targets):
    return sum(1 for t in targets if t in reach)


def stats(vals):
    n = len(vals)
    if n == 0:
        return 0.0, 0.0
    m = sum(vals) / n
    v = sum((x - m) ** 2 for x in vals) / n
    return m, v ** 0.5


def zp(obs, dist):
    m, s = stats(dist)
    z = (obs - m) / s if s > 0 else (float("inf") if obs > m else 0.0)
    cnt = sum(1 for v in dist if v >= obs)
    return z, cnt / len(dist), cnt


def dedupe7(seq):
    out = []
    for x in seq:
        if x > 0 and x not in out:
            out.append(x)
        if len(out) >= 7:
            break
    # pad if necessary
    i = 1
    while len(out) < 7:
        if i not in out:
            out.append(i)
        i += 1
    return out


def main():
    targets = load_targets(REALITY_MAP)
    uniq = sorted(set(targets))
    print(f"타겟: {len(targets)}개 (고유 {len(uniq)})")

    # n=6 상수
    n6 = [6, 12, 4, 2, 5, 24, 1]

    # π 기반: round(π·k) for k=1..7  → 3,6,9,13,16,19,22
    pi_set = dedupe7([round(math.pi * k) for k in range(1, 10)])
    # e 기반: round(e·k)  → 3,5,8,11,14,16,19
    e_set = dedupe7([round(math.e * k) for k in range(1, 10)])
    # φ 기반: round(φ·k)  → 2,3,5,6,8,10,11
    phi = (1 + 5 ** 0.5) / 2
    phi_set = dedupe7([round(phi * k) for k in range(1, 10)])
    # 소수: 2,3,5,7,11,13,17
    prime_set = [2, 3, 5, 7, 11, 13, 17]
    # 작은 수 (기존 대조)
    small_set = [1, 2, 3, 4, 5, 6, 3]

    sets = {
        "n=6":   n6,
        "π기반": pi_set,
        "e기반":  e_set,
        "φ기반": phi_set,
        "소수":   prime_set,
        "작은수": small_set,
    }

    print("\n[대조군 집합]")
    for name, s in sets.items():
        print(f"  {name:8s} = {s}")

    # 각 집합 평가
    results = {}
    for name, s in sets.items():
        reach = generate_reachable(s)
        h = count_hits(reach, targets)
        eff = h / len(reach) if reach else 0.0
        results[name] = {"set": s, "reach": len(reach), "hits": h, "eff": eff}

    # Monte Carlo
    print(f"\n[MC {N_TRIALS}회 랜덤 7개 1~30]")
    t0 = time.time()
    trial_hits, trial_eff, trial_sizes = [], [], []
    for i in range(N_TRIALS):
        rc = [random.randint(*RANDOM_RANGE) for _ in range(RANDOM_SET_SIZE)]
        rr = generate_reachable(rc)
        h = count_hits(rr, targets)
        sz = len(rr)
        trial_hits.append(h)
        trial_sizes.append(sz)
        trial_eff.append(h / sz if sz > 0 else 0.0)
        if (i + 1) % 2500 == 0:
            print(f"  {i+1}/{N_TRIALS} ({time.time()-t0:.1f}s)")
    print(f"  완료 {time.time()-t0:.1f}s")

    mean_h, std_h = stats([float(x) for x in trial_hits])
    mean_e, std_e = stats(trial_eff)
    mean_s, std_s = stats([float(x) for x in trial_sizes])
    print(f"\n랜덤 HIT: {mean_h:.2f}±{std_h:.2f}  eff: {mean_e:.4f}±{std_e:.4f}  size: {mean_s:.1f}±{std_s:.1f}")

    # z/p 계산
    print("\n" + "="*80)
    print(f"  {'집합':8s} {'reach':>6s} {'HIT':>5s} {'HIT%':>6s} {'eff':>8s} "
          f"{'z_HIT':>7s} {'p_HIT':>8s} {'z_eff':>7s} {'p_eff':>8s}")
    print("="*80)
    rows = []
    for name, r in results.items():
        zh, ph, _ = zp(float(r["hits"]), [float(x) for x in trial_hits])
        ze, pe, _ = zp(r["eff"], trial_eff)
        rows.append((name, r, zh, ph, ze, pe))
        print(f"  {name:8s} {r['reach']:>6d} {r['hits']:>5d} "
              f"{r['hits']/len(targets)*100:>5.1f}% {r['eff']:>8.4f} "
              f"{zh:>7.2f} {ph:>8.4f} {ze:>7.2f} {pe:>8.4f}")
    print("="*80)

    # JSON 저장 (리포트 작성용)
    out = {
        "n_trials": N_TRIALS,
        "targets_total": len(targets),
        "targets_unique": len(uniq),
        "random_mean_hit": mean_h, "random_std_hit": std_h,
        "random_mean_eff": mean_e, "random_std_eff": std_e,
        "random_mean_size": mean_s, "random_std_size": std_s,
        "rows": [
            {"name": n, "set": r["set"], "reach": r["reach"], "hits": r["hits"],
             "hit_pct": r["hits"]/len(targets),
             "eff": r["eff"], "z_hit": zh, "p_hit": ph, "z_eff": ze, "p_eff": pe}
            for (n, r, zh, ph, ze, pe) in rows
        ],
    }
    with open(os.path.join(SCRIPT_DIR, "n6_uniqueness_pi_e_phi.json"), "w") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    print("\n저장: shared/n6_uniqueness_pi_e_phi.json")


if __name__ == "__main__":
    main()
