#!/usr/bin/env python3
"""Monte Carlo v6.0 engine."""
import json, os, sys, random, math, time
from collections import Counter, defaultdict

MAP_PATH    = sys.argv[1]
OUT_PATH    = sys.argv[2]
REPORT_PATH = sys.argv[3]
N_TRIALS    = int(sys.argv[4])
DIAGNOSE    = sys.argv[5] == '1' if len(sys.argv) > 5 else False
SEED        = 20260409

def n_constants(n):
    """n의 7대 산술함수: [n, sigma, tau, phi, sopfr, J2, mu=1]."""
    divs = [d for d in range(1, n+1) if n % d == 0]
    sigma = sum(divs)
    tau = len(divs)
    phi = sum(1 for k in range(1, n+1) if math.gcd(k, n) == 1)
    sopfr = 0
    tmp = n
    for p in range(2, n+1):
        while tmp % p == 0:
            sopfr += p
            tmp //= p
    j2 = n * n
    tmp2 = n
    for p in range(2, n+1):
        if tmp2 % p == 0:
            j2 = j2 * (1 - 1/(p*p))
            while tmp2 % p == 0:
                tmp2 //= p
    j2 = int(round(j2))
    return sorted(set([n, sigma, tau, phi, sopfr, j2, 1]))

def reachable(constants, max_r=10000, max_exp=10):
    reach = set()
    for a in constants:
        if 0 < a <= max_r: reach.add(a)
    for a in constants:
        for b in constants:
            for v in (a+b, a-b, a*b):
                if 0 < v <= max_r: reach.add(v)
            if b != 0 and a % b == 0:
                v = a // b
                if 0 < v <= max_r: reach.add(v)
            if 0 < b <= max_exp and a > 0:
                try:
                    v = a ** b
                    if 0 < v <= max_r: reach.add(v)
                except (OverflowError, MemoryError): pass
            if 0 <= b <= a:
                try:
                    c = math.comb(a, b)
                    if 0 < c <= max_r: reach.add(c)
                except Exception: pass
    return reach

def load_targets(path):
    with open(path, encoding='utf-8') as f: data = json.load(f)
    nodes = data.get('nodes', [])
    natural_int, all_int = [], []
    origin_counts = Counter()
    origin_hits = defaultdict(list)
    for nd in nodes:
        origin = nd.get('origin', 'unknown')
        origin_counts[origin] += 1
        m = nd.get('measured')
        v = None
        if isinstance(m, int) and m > 0: v = m
        elif isinstance(m, float) and m == int(m) and m > 0 and math.isfinite(m): v = int(m)
        if v is not None and v <= 10000:
            all_int.append(v)
            origin_hits[origin].append(v)
            if origin == 'natural': natural_int.append(v)
    return natural_int, all_int, origin_counts, origin_hits, data.get('_meta', {})

def stats(xs):
    n = len(xs)
    if n == 0: return 0.0, 0.0
    m = sum(xs) / n
    v = sum((x - m)**2 for x in xs) / n
    return m, v**0.5

def z_and_p(obs, dist):
    m, s = stats(dist)
    z = (obs - m) / s if s > 0 else (float('inf') if obs > m else 0.0)
    cnt = sum(1 for v in dist if v >= obs)
    p = cnt / len(dist) if dist else 1.0
    return z, p, m, s

def bootstrap_ci(hits, reach_size, trial_effs, n_boot=5000):
    eff = hits / reach_size if reach_size > 0 else 0.0
    rng = random.Random(42)
    boot_zs = []
    for _ in range(n_boot):
        sample = [rng.choice(trial_effs) for _ in range(len(trial_effs))]
        m, s = stats(sample)
        if s > 0: boot_zs.append((eff - m) / s)
    if not boot_zs: return {'eff': eff, 'z_lo': 0, 'z_hi': 0, 'p_boot': 1.0}
    boot_zs.sort()
    lo = boot_zs[int(0.005 * len(boot_zs))]
    hi = boot_zs[int(0.995 * len(boot_zs))]
    p_boot = sum(1 for z in boot_zs if z <= 0) / len(boot_zs)
    return {'eff': eff, 'z_lo': lo, 'z_hi': hi, 'p_boot': p_boot}

def run_mc(label, constants, targets, n_trials):
    reach = reachable(constants)
    reach_size = len(reach)
    hits = sum(1 for t in targets if t in reach)
    eff = hits / reach_size if reach_size > 0 else 0.0
    rng = random.Random(SEED)
    trial_hits, trial_effs, trial_sizes = [], [], []
    for _ in range(n_trials):
        rc = [rng.randint(1, 30) for _ in range(7)]
        rr = reachable(rc)
        sz = len(rr)
        h = sum(1 for t in targets if t in rr)
        trial_hits.append(h)
        trial_sizes.append(sz)
        trial_effs.append(h / sz if sz > 0 else 0.0)
    z_hit, p_hit, mu_h, sig_h = z_and_p(float(hits), [float(x) for x in trial_hits])
    z_eff, p_eff, mu_e, sig_e = z_and_p(eff, trial_effs)
    tol_sz = max(5, int(reach_size * 0.10))
    matched = [trial_hits[i] for i in range(n_trials) if abs(trial_sizes[i] - reach_size) <= tol_sz]
    z_sm, p_sm = 0.0, 1.0
    if len(matched) >= 30:
        z_sm, p_sm, _, _ = z_and_p(float(hits), [float(x) for x in matched])
    boot = bootstrap_ci(hits, reach_size, trial_effs)
    return {'label': label, 'constants': constants, 'reach_size': reach_size,
            'hits': hits, 'hit_rate': hits/len(targets) if targets else 0,
            'eff': eff, 'z_hit': z_hit, 'p_hit': p_hit,
            'z_eff': z_eff, 'p_eff': p_eff,
            'z_sm': z_sm, 'p_sm': p_sm, 'n_matched': len(matched),
            'bootstrap': boot, 'mu_h': mu_h, 'sig_h': sig_h,
            'mu_e': mu_e, 'sig_e': sig_e, 'trial_effs': trial_effs}

def diagnose(targets, all_int):
    n6r = reachable([6,12,4,2,5,24,1])
    small = sum(1 for t in targets if t <= 24)
    lines = ['## z>3 gap analysis', '',
        f'n=6 reach={len(n6r)}, natural targets={len(targets)}, all={len(all_int)}', '',
        '### Cause 1: reach size bias',
        'n=6 constants max=24, random 1-30 similar range -> high overlap.', '',
        '### Cause 2: target distribution',
        f'targets<=24: {small}/{len(targets)} ({small/len(targets)*100:.1f}%)',
        'Small integers dominate -> all small-number sets perform well.', '',
        '### Cause 3: 2-op limit',
        '6 ops x 49 pairs -> ~51 unique reach. Limited discrimination.', '',
        '### Cause 4: multiple comparisons',
        'n=2..12 (11 candidates) -> Bonferroni: p_adj = p*11',
        'z=2.03->p=0.021->p_adj=0.23 (not significant after correction).', '',
        '### Solutions',
        '1. 3-op extension: (a op b) op c',
        '2. Match random range to max(constants)',
        '3. Use unique targets only (deduplicated)',
        '4. Filter STRUCTURAL/CAUSAL only (exclude CONVENTION)',
        '5. Combined z_eff + z_size_matched metric']
    return '\n'.join(lines)

def main():
    t0 = time.time()
    nat_int, all_int, org_cnt, org_hits, meta = load_targets(MAP_PATH)
    ver = meta.get('version', '?')
    tot = meta.get('node_count', 0)
    print(f'reality_map {ver}, {tot} nodes')
    print(f'origin: {dict(org_cnt)}')
    print(f'natural int targets: {len(nat_int)} (unique {len(set(nat_int))})')
    print()
    n6r = reachable([6,12,4,2,5,24,1])
    org_st = {}
    for org, vals in sorted(org_hits.items()):
        h = sum(1 for v in vals if v in n6r)
        org_st[org] = {'count':len(vals),'unique':len(set(vals)),'n6_hits':h,'rate':h/len(vals) if vals else 0}
        print(f'  {org:15s}: {len(vals):5d} tgt, {len(set(vals)):4d} uniq, n6={h} ({h/len(vals)*100:.1f}%)')
    print()
    if DIAGNOSE:
        d = diagnose(nat_int, all_int)
        print(d)
        with open(REPORT_PATH,'w') as f: f.write(d)
        return
    tgt_u = sorted(set(nat_int))
    tgt_a = nat_int
    print(f'-- n=2..12 comparison (N={N_TRIALS}) --')
    res_u, res_a = {}, {}
    for n in range(2, 13):
        c = n_constants(n)
        print(f'  n={n:2d} c={c}')
        ru = run_mc(f'n={n}(u)', c, tgt_u, N_TRIALS)
        ra = run_mc(f'n={n}(a)', c, tgt_a, N_TRIALS)
        for r in (ru, ra): del r['trial_effs']
        res_u[n], res_a[n] = ru, ra
        print(f'    unique: hit={ru["hits"]}/{len(tgt_u)} z_h={ru["z_hit"]:+.2f} z_e={ru["z_eff"]:+.2f} z_sm={ru["z_sm"]:+.2f}')
        print(f'    all:    hit={ra["hits"]}/{len(tgt_a)} z_h={ra["z_hit"]:+.2f} z_e={ra["z_eff"]:+.2f} z_sm={ra["z_sm"]:+.2f}')
    nc = 11
    for n in range(2, 13):
        res_u[n]['p_bonf'] = min(1.0, res_u[n]['p_eff'] * nc)
        res_a[n]['p_bonf'] = min(1.0, res_a[n]['p_eff'] * nc)
    sp = {'primes':[2,3,5,7,11,13,17], 'fib':[1,1,2,3,5,8,13], 'pow2':[1,2,4,8,16,32,64]}
    sp_res = {}
    for nm, cs in sp.items():
        r = run_mc(nm, cs, tgt_u, N_TRIALS)
        del r['trial_effs']
        sp_res[nm] = r
        print(f'  {nm:12s}: hit={r["hits"]} z_eff={r["z_eff"]:+.2f}')
    n6u = res_u[6]
    bz = max(n6u['z_eff'], n6u['z_sm'], n6u['z_hit'])
    rk = sorted(res_u.items(), key=lambda x: x[1]['z_eff'], reverse=True)
    r6 = next(i for i,(n,_) in enumerate(rk) if n==6) + 1
    el = time.time() - t0
    print()
    print('=' * 60)
    print(f'  n=6 (unique tgt={len(tgt_u)}):')
    print(f'    z_hit={n6u["z_hit"]:+.3f} z_eff={n6u["z_eff"]:+.3f} z_sm={n6u["z_sm"]:+.3f}')
    print(f'    best_z={bz:+.3f} rank={r6}/11 z>3={bz>3}')
    print(f'    p_bonf={n6u["p_bonf"]:.4f}')
    print(f'  elapsed: {el:.1f}s')
    print('=' * 60)
    # report
    rpt = ['# Monte Carlo v6.0 Rerun', '',
        f'- date: {time.strftime("%Y-%m-%d %H:%M")}',
        f'- data: reality_map_live.json ({ver}, {tot} nodes)',
        f'- natural int targets: {len(nat_int)} (unique {len(tgt_u)})',
        f'- N={N_TRIALS}', '',
        '## n=2..12 (unique targets)', '',
        '| n | constants | reach | hits | hit% | eff | z_hit | z_eff | z_sm | p_bonf |',
        '|---|-----------|-------|------|------|-----|-------|-------|------|--------|']
    for n in range(2, 13):
        r = res_u[n]
        rpt.append(f'| {n} | {r["constants"]} | {r["reach_size"]} | {r["hits"]} | {r["hit_rate"]*100:.1f}% | {r["eff"]:.3f} | {r["z_hit"]:+.2f} | {r["z_eff"]:+.2f} | {r["z_sm"]:+.2f} | {r["p_bonf"]:.4f} |')
    rpt += ['', '## Special sets', '',
        '| set | reach | hits | z_eff |', '|-----|-------|------|-------|']
    for nm, r in sp_res.items():
        rpt.append(f'| {nm} | {r["reach_size"]} | {r["hits"]} | {r["z_eff"]:+.2f} |')
    rpt += ['', '## Origin stats', '',
        '| origin | targets | unique | n6_hits | rate |',
        '|--------|---------|--------|---------|------|']
    for org, st in sorted(org_st.items()):
        rpt.append(f'| {org} | {st["count"]} | {st["unique"]} | {st["n6_hits"]} | {st["rate"]*100:.1f}% |')
    rpt += ['', '## Verdict', '',
        f'- **best z = {bz:+.3f}**',
        f'- **z>3: {"YES" if bz>3 else "NO"}**',
        f'- n=6 eff rank: {r6}/11',
        f'- p_bonf: {n6u["p_bonf"]:.4f}',
        f'- prev best z_eff=2.03 vs current {n6u["z_eff"]:+.3f}', '']
    rpt.append(diagnose(nat_int, all_int))
    with open(REPORT_PATH, 'w') as f: f.write('\n'.join(rpt))
    out = {'meta':{'script':'monte_carlo_v6.hexa','generated':time.strftime('%Y-%m-%dT%H:%M:%S'),
        'version':ver,'total_nodes':tot,'natural_targets':len(nat_int),
        'unique_targets':len(tgt_u),'n_trials':N_TRIALS,'seed':SEED,'elapsed':el},
        'origin_stats':org_st,
        'n_comparison':{str(n):r for n,r in res_u.items()},
        'n_comparison_all':{str(n):r for n,r in res_a.items()},
        'special':sp_res,
        'verdict':{'best_z':bz,'z_gt_3':bz>3,'rank':r6,
            'z_eff':n6u['z_eff'],'z_hit':n6u['z_hit'],'z_sm':n6u['z_sm'],
            'prev':2.03,'gap':'small-number-bias+2op-overlap+target-dist'}}
    with open(OUT_PATH, 'w') as f: json.dump(out, f, indent=2, ensure_ascii=False)
    print(f'saved: {OUT_PATH}')
    print(f'report: {REPORT_PATH}')

if __name__ == '__main__': main()
