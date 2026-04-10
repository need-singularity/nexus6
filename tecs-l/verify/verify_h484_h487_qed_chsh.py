#!/usr/bin/env python3
"""Verify H-CX-484 and H-CX-487: QED pi-path and CHSH domain structure.

H-CX-484: Q->pi path = alpha/(g-2) - m_e/m_mu ~ pi (0.0024%?)
H-CX-487: CHSH Domain Structure — can Q reach 2 (Bell) and 2sqrt(2) (Tsirelson)?
"""

import numpy as np
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from convergence_engine import DOMAINS

THRESHOLD = 0.001  # 0.1%

# Q domain constants
Q_CONSTS = list(DOMAINS["Q"]["constants"].items())
Q_VALS = {name: val for name, val in Q_CONSTS}

# ═══════════════════════════════════════════════════════════════
# H-CX-484: Q -> pi path via QED constants
# ═══════════════════════════════════════════════════════════════
def verify_h484():
    print("=" * 72)
    print("  H-CX-484: Q -> pi path = alpha/(g-2) - m_e/m_mu ~ pi")
    print("=" * 72)

    alpha = 1 / 137.035999084
    g_minus_2 = 0.00231930436256
    m_e_over_m_mu = 1 / 206.7682830

    print(f"\n--- Precise constants ---")
    print(f"  alpha            = {alpha:.15e}")
    print(f"  g-2 (electron)   = {g_minus_2:.15e}")
    print(f"  m_e/m_mu         = {m_e_over_m_mu:.15e}")

    # Step 1: alpha / (g-2)
    ratio = alpha / g_minus_2
    print(f"\n--- Step 1: alpha / (g-2) ---")
    print(f"  alpha / (g-2)    = {ratio:.15f}")
    print(f"  2*pi             = {2*np.pi:.15f}")
    print(f"  pi               = {np.pi:.15f}")
    err_2pi = abs(ratio - 2*np.pi) / (2*np.pi) * 100
    err_pi = abs(ratio - np.pi) / np.pi * 100
    print(f"  Error vs 2*pi    = {err_2pi:.6f}%")
    print(f"  Error vs pi      = {err_pi:.6f}%")

    # Physical interpretation: g-2 = alpha/(2*pi) at leading order (Schwinger)
    # So alpha/(g-2) = alpha / (alpha/(2*pi) + ...) = 2*pi / (1 + higher_order_terms)
    schwinger = alpha / (2 * np.pi)
    print(f"\n--- Physical interpretation ---")
    print(f"  Schwinger term:  alpha/(2*pi) = {schwinger:.15e}")
    print(f"  Actual g-2:                     {g_minus_2:.15e}")
    print(f"  Ratio actual/Schwinger:         {g_minus_2/schwinger:.15f}")
    print(f"  Higher order correction:        {(g_minus_2 - schwinger)/schwinger*100:.6f}%")
    print(f"  -> alpha/(g-2) = 2*pi / (1 + corrections) ~ 2*pi * 0.998... ~ {ratio:.8f}")

    # Step 2: alpha/(g-2) - m_e/m_mu
    subtracted = ratio - m_e_over_m_mu
    print(f"\n--- Step 2: alpha/(g-2) - m_e/m_mu ---")
    print(f"  alpha/(g-2) - m_e/m_mu = {subtracted:.15f}")
    print(f"  pi                     = {np.pi:.15f}")
    print(f"  2*pi                   = {2*np.pi:.15f}")
    err_pi2 = abs(subtracted - np.pi) / np.pi * 100
    err_2pi2 = abs(subtracted - 2*np.pi) / (2*np.pi) * 100
    print(f"  Error vs pi            = {err_pi2:.6f}%")
    print(f"  Error vs 2*pi          = {err_2pi2:.6f}%")

    # Neither seems right. Let's check what the actual depth-2 expression was.
    # The claim was "0.0024% match to pi". Let's search ALL depth-2 Q expressions for pi.
    print(f"\n{'='*72}")
    print(f"  Exhaustive depth-2 Q search for pi matches (within 0.1%)")
    print(f"{'='*72}")

    # Build depth-1 results
    d1_results = []
    for i, (n1, v1) in enumerate(Q_CONSTS):
        # Unary
        d1_results.append((v1, n1))
        if v1 > 0:
            d1_results.append((np.sqrt(v1), f"sqrt({n1})"))
            d1_results.append((np.log(v1), f"ln({n1})"))
        if v1 != 0:
            d1_results.append((1/v1, f"1/{n1}"))
        d1_results.append((v1**2, f"({n1})^2"))
        if abs(v1) < 50:
            try:
                ev = np.exp(v1)
                if np.isfinite(ev):
                    d1_results.append((ev, f"exp({n1})"))
            except:
                pass

        # Binary with all others
        for j, (n2, v2) in enumerate(Q_CONSTS):
            d1_results.append((v1 + v2, f"{n1} + {n2}"))
            d1_results.append((v1 - v2, f"{n1} - {n2}"))
            d1_results.append((v1 * v2, f"{n1} * {n2}"))
            if v2 != 0:
                d1_results.append((v1 / v2, f"{n1} / {n2}"))
            if v1 > 0 and abs(v2) < 20:
                try:
                    v = v1 ** v2
                    if np.isfinite(v) and abs(v) < 1e12:
                        d1_results.append((v, f"{n1} ^ {n2}"))
                except:
                    pass

    # Filter finite
    d1_results = [(v, e) for v, e in d1_results if np.isfinite(v)]
    print(f"  Depth-1 expressions: {len(d1_results)}")

    # Build depth-2: d1_result op Q_constant
    pi_matches = []
    for v1, e1 in d1_results:
        for n2, v2 in Q_CONSTS:
            candidates = [
                (v1 + v2, f"({e1}) + {n2}"),
                (v1 - v2, f"({e1}) - {n2}"),
                (v2 - v1, f"{n2} - ({e1})"),
                (v1 * v2, f"({e1}) * {n2}"),
            ]
            if v2 != 0:
                candidates.append((v1 / v2, f"({e1}) / {n2}"))
            if v1 != 0:
                candidates.append((v2 / v1, f"{n2} / ({e1})"))

            for val, expr in candidates:
                if np.isfinite(val) and abs(val) > 0:
                    err = abs(val - np.pi) / np.pi * 100
                    if err < 0.1:
                        pi_matches.append((expr, val, err))

    # Also check d1 directly
    for val, expr in d1_results:
        if abs(val) > 0:
            err = abs(val - np.pi) / np.pi * 100
            if err < 0.1:
                pi_matches.append((expr, val, err))

    # Deduplicate and sort
    seen = set()
    unique_matches = []
    for expr, val, err in sorted(pi_matches, key=lambda x: x[2]):
        key = f"{val:.12f}"
        if key not in seen:
            seen.add(key)
            unique_matches.append((expr, val, err))

    print(f"  Pi matches found (within 0.1%): {len(unique_matches)}")
    print(f"\n  {'Rank':<6} {'Error%':<12} {'Value':<20} Expression")
    print(f"  {'-'*80}")
    for i, (expr, val, err) in enumerate(unique_matches[:20]):
        marker = " <-- BEST" if i == 0 else ""
        print(f"  {i+1:<6} {err:<12.6f} {val:<20.15f} {expr}{marker}")

    if unique_matches:
        best = unique_matches[0]
        print(f"\n  BEST Q->pi path:")
        print(f"    Expression: {best[0]}")
        print(f"    Value:      {best[1]:.15f}")
        print(f"    pi:         {np.pi:.15f}")
        print(f"    Error:      {best[2]:.6f}%")
        print(f"    Abs error:  {abs(best[1] - np.pi):.2e}")

        if best[2] < 0.01:
            print(f"    VERDICT: CONFIRMED (error < 0.01%)")
        elif best[2] < 0.1:
            print(f"    VERDICT: APPROXIMATE (error < 0.1%)")
        else:
            print(f"    VERDICT: WEAK (error > 0.1%)")
    else:
        print(f"\n  VERDICT: No Q->pi path found within 0.1% at depth 2")

    # Physical analysis of the claimed expression
    print(f"\n--- Physical analysis of alpha/(g-2) ---")
    print(f"  At tree level (Schwinger):  g-2 = alpha/(2*pi)")
    print(f"  Therefore alpha/(g-2) = 2*pi at tree level")
    print(f"  With higher-order QED corrections:")
    print(f"    g-2 = (alpha/2pi)(1 + C2*(alpha/pi) + C3*(alpha/pi)^2 + ...)")
    print(f"    where C2 ~ -0.328...")
    a_over_pi = alpha / np.pi
    print(f"    alpha/pi = {a_over_pi:.10f}")
    print(f"    1 + C2*(alpha/pi) ~ {1 - 0.328 * a_over_pi:.10f}")
    print(f"    So alpha/(g-2) ~ 2*pi / (1 + corrections) = {ratio:.10f}")
    print(f"    This is 2*pi * {np.pi*2/ratio:.10f}")
    print(f"    Deficit from 2*pi: {2*np.pi - ratio:.10e}")
    print(f"    m_e/m_mu:          {m_e_over_m_mu:.10e}")
    print(f"    After subtracting m_e/m_mu: {subtracted:.10f} (vs pi = {np.pi:.10f})")


# ═══════════════════════════════════════════════════════════════
# H-CX-487: CHSH Domain Structure
# ═══════════════════════════════════════════════════════════════
def verify_h487():
    print(f"\n\n{'='*72}")
    print(f"  H-CX-487: CHSH Domain Structure")
    print(f"  Can Q domain reach Bell bound (2) and Tsirelson bound (2*sqrt(2))?")
    print(f"{'='*72}")

    bell_bound = 2.0
    tsirelson = 2 * np.sqrt(2)
    sqrt2 = np.sqrt(2)

    print(f"\n  Key targets:")
    print(f"    Bell bound (classical):    {bell_bound}")
    print(f"    Tsirelson bound (quantum): {tsirelson:.10f}")
    print(f"    sqrt(2):                   {sqrt2:.10f}")

    # Build depth-1 Q results
    d1_results = []
    for i, (n1, v1) in enumerate(Q_CONSTS):
        # Unary
        d1_results.append((v1, n1))
        if v1 > 0:
            d1_results.append((np.sqrt(v1), f"sqrt({n1})"))
            d1_results.append((np.log(v1), f"ln({n1})"))
        if v1 != 0:
            d1_results.append((1/v1, f"1/{n1}"))
        d1_results.append((v1**2, f"({n1})^2"))

        # Binary with all others
        for j, (n2, v2) in enumerate(Q_CONSTS):
            d1_results.append((v1 + v2, f"{n1} + {n2}"))
            d1_results.append((v1 - v2, f"{n1} - {n2}"))
            d1_results.append((v1 * v2, f"{n1} * {n2}"))
            if v2 != 0:
                d1_results.append((v1 / v2, f"{n1} / {n2}"))
            if v1 > 0 and abs(v2) < 20:
                try:
                    v = v1 ** v2
                    if np.isfinite(v) and abs(v) < 1e12:
                        d1_results.append((v, f"{n1} ^ {n2}"))
                except:
                    pass

    d1_results = [(v, e) for v, e in d1_results if np.isfinite(v)]
    print(f"\n  Depth-1 Q expressions: {len(d1_results)}")

    # Check each target at depth 1
    targets = {
        "2 (Bell bound)":          bell_bound,
        "2*sqrt(2) (Tsirelson)":   tsirelson,
        "sqrt(2)":                 sqrt2,
    }

    d1_reach = {}
    print(f"\n  {'Target':<28} {'Depth-1?':<10} {'Best expr':<45} {'Value':<16} {'Error%'}")
    print(f"  {'-'*110}")

    for tname, tval in targets.items():
        matches = []
        for val, expr in d1_results:
            if abs(val) > 0:
                err = abs(val - tval) / abs(tval) * 100
                if err < THRESHOLD * 100:
                    matches.append((expr, val, err))
        matches.sort(key=lambda x: x[2])

        if matches:
            best = matches[0]
            d1_reach[tname] = True
            print(f"  {tname:<28} {'YES':<10} {best[0]:<45} {best[1]:<16.10f} {best[2]:.6f}%")
        else:
            d1_reach[tname] = False
            # Find closest
            closest = min(d1_results, key=lambda x: abs(x[0] - tval) if np.isfinite(x[0]) else 1e99)
            err = abs(closest[0] - tval) / abs(tval) * 100
            print(f"  {tname:<28} {'NO':<10} {'(closest: ' + closest[1] + ')':<45} {closest[0]:<16.10f} {err:.4f}%")

    # Depth 2 for unreachable targets
    print(f"\n--- Depth-2 search for unreachable targets ---")
    d2_results = []
    for v1, e1 in d1_results:
        for n2, v2 in Q_CONSTS:
            d2_results.append((v1 + v2, f"({e1}) + {n2}"))
            d2_results.append((v1 - v2, f"({e1}) - {n2}"))
            d2_results.append((v2 - v1, f"{n2} - ({e1})"))
            d2_results.append((v1 * v2, f"({e1}) * {n2}"))
            if v2 != 0:
                d2_results.append((v1 / v2, f"({e1}) / {n2}"))
            if v1 != 0:
                d2_results.append((v2 / v1, f"{n2} / ({e1})"))

    d2_results = [(v, e) for v, e in d2_results if np.isfinite(v)]
    print(f"  Depth-2 Q expressions: {len(d2_results)}")

    d2_reach = {}
    print(f"\n  {'Target':<28} {'D1?':<6} {'D2?':<6} {'D2 Best expr':<55} {'Value':<16} {'Error%'}")
    print(f"  {'-'*120}")

    for tname, tval in targets.items():
        d1_flag = "YES" if d1_reach[tname] else "NO"

        matches = []
        for val, expr in d2_results:
            if abs(val) > 0:
                err = abs(val - tval) / abs(tval) * 100
                if err < THRESHOLD * 100:
                    matches.append((expr, val, err))
        matches.sort(key=lambda x: x[2])

        if matches:
            best = matches[0]
            d2_reach[tname] = True
            print(f"  {tname:<28} {d1_flag:<6} {'YES':<6} {best[0][:53]:<55} {best[1]:<16.10f} {best[2]:.6f}%")
        else:
            d2_reach[tname] = False
            print(f"  {tname:<28} {d1_flag:<6} {'NO':<6}")

    # Show top matches for each target at depth 2
    for tname, tval in targets.items():
        matches = []
        for val, expr in d2_results:
            if abs(val) > 0:
                err = abs(val - tval) / abs(tval) * 100
                if err < 0.1:  # 0.1%
                    matches.append((expr, val, err))
        matches.sort(key=lambda x: x[2])

        if matches:
            print(f"\n  Top depth-2 matches for {tname}:")
            seen_vals = set()
            count = 0
            for expr, val, err in matches:
                vkey = f"{val:.10f}"
                if vkey not in seen_vals:
                    seen_vals.add(vkey)
                    print(f"    {err:.6f}%  {val:.12f}  {expr}")
                    count += 1
                    if count >= 5:
                        break

    # Verdict
    print(f"\n{'='*72}")
    print(f"  CHSH Domain Structure Verdict")
    print(f"{'='*72}")

    bell_d1 = d1_reach.get("2 (Bell bound)", False)
    tsirelson_d1 = d1_reach.get("2*sqrt(2) (Tsirelson)", False)
    sqrt2_d1 = d1_reach.get("sqrt(2)", False)
    tsirelson_d2 = d2_reach.get("2*sqrt(2) (Tsirelson)", False)
    sqrt2_d2 = d2_reach.get("sqrt(2)", False)

    print(f"\n  Bell bound (2):      D1={'YES' if bell_d1 else 'NO'}")
    print(f"  Tsirelson (2*sqrt2): D1={'YES' if tsirelson_d1 else 'NO'}, D2={'YES' if tsirelson_d2 else 'NO'}")
    print(f"  sqrt(2):             D1={'YES' if sqrt2_d1 else 'NO'}, D2={'YES' if sqrt2_d2 else 'NO'}")

    if bell_d1 and not tsirelson_d1:
        print(f"\n  CONFIRMED: Q reaches classical Bell bound (2) at depth 1")
        print(f"             but cannot reach quantum Tsirelson bound (2*sqrt(2)) at depth 1")
        print(f"  -> Q can express classical limit but not quantum limit")
        print(f"  -> Algebraic irrationals (sqrt(2)) form a barrier for Q domain")
    elif bell_d1 and tsirelson_d1:
        print(f"\n  REFUTED: Q reaches BOTH Bell and Tsirelson bounds at depth 1")
    elif not bell_d1:
        print(f"\n  UNEXPECTED: Q cannot reach even Bell bound (2) at depth 1")
        # Check why
        print(f"  Checking: is 2.000 achievable from Q constants?")
        for val, expr in d1_results:
            if abs(val - 2.0) < 0.01:
                print(f"    Near-2: {expr} = {val:.10f}")

    if not sqrt2_d1 and sqrt2_d2:
        print(f"\n  sqrt(2): Unreachable at D1, reached at D2")
        print(f"  -> Confirms algebraic irrationals require extra computation from Q")
    elif not sqrt2_d1 and not sqrt2_d2:
        print(f"\n  sqrt(2): Unreachable even at D2")
        print(f"  -> Strong Q-barrier against algebraic irrationals")


# ═══════════════════════════════════════════════════════════════
# Additional: Cross-domain analysis
# ═══════════════════════════════════════════════════════════════
def cross_domain_chsh():
    """Which domains CAN reach sqrt(2), 2, and 2*sqrt(2)?"""
    print(f"\n\n{'='*72}")
    print(f"  Cross-domain CHSH reachability")
    print(f"{'='*72}")

    targets = {
        "sqrt(2)":           np.sqrt(2),
        "2 (Bell)":          2.0,
        "2*sqrt(2) (Tsir.)": 2*np.sqrt(2),
    }

    domain_ids = list(DOMAINS.keys())

    print(f"\n  {'Domain':<6} {'Name':<25}", end="")
    for t in targets:
        print(f" {t:>20}", end="")
    print()
    print(f"  {'-'*90}")

    for did in domain_ids:
        consts = list(DOMAINS[did]["constants"].items())
        dname = DOMAINS[did]["name"]

        # Build depth-1
        results = []
        for n1, v1 in consts:
            results.append((v1, n1))
            if v1 > 0:
                results.append((np.sqrt(v1), f"sqrt({n1})"))
                results.append((np.log(v1), f"ln({n1})"))
            if v1 != 0:
                results.append((1/v1, f"1/{n1}"))
            results.append((v1**2, f"({n1})^2"))

            for n2, v2 in consts:
                results.append((v1 + v2, f"{n1}+{n2}"))
                results.append((v1 - v2, f"{n1}-{n2}"))
                results.append((v1 * v2, f"{n1}*{n2}"))
                if v2 != 0:
                    results.append((v1 / v2, f"{n1}/{n2}"))
                if v1 > 0 and abs(v2) < 20:
                    try:
                        v = v1 ** v2
                        if np.isfinite(v) and abs(v) < 1e12:
                            results.append((v, f"{n1}^{n2}"))
                    except:
                        pass

        results = [(v, e) for v, e in results if np.isfinite(v)]

        print(f"  {did:<6} {dname:<25}", end="")
        for tname, tval in targets.items():
            matches = [(e, v, abs(v-tval)/abs(tval)*100)
                       for v, e in results
                       if abs(v) > 0 and abs(v-tval)/abs(tval) < THRESHOLD]
            matches.sort(key=lambda x: x[2])
            if matches:
                print(f" {'YES ('+matches[0][0]+')':>20}", end="")
            else:
                print(f" {'--':>20}", end="")
        print()


# ═══════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("=" * 72)
    print("  VERIFICATION: H-CX-484 & H-CX-487")
    print("  QED Pi-Path & CHSH Domain Structure")
    print("=" * 72)

    print(f"\nQ domain constants:")
    for name, val in Q_CONSTS:
        print(f"  {name:>15} = {val:.15g}")

    verify_h484()
    verify_h487()
    cross_domain_chsh()

    print(f"\n{'='*72}")
    print(f"  ALL VERIFICATIONS COMPLETE")
    print(f"{'='*72}")
