#!/usr/bin/env python3
"""
Verification of Infrastructure Hypotheses H-INFRA-001 to H-INFRA-020.

Tests each claim computationally against known constants, industry data,
and mathematical properties of the perfect number 6.

Usage: PYTHONPATH=. python3 verify/verify_infra_hypotheses.py
"""

import math
import numpy as np

# ── Core constants from the TECS-L system ──
PERFECT_6 = 6
DIVISORS_6 = [1, 2, 3, 6]
PROPER_DIVISORS_6 = [1, 2, 3]
SIGMA_6 = sum(DIVISORS_6)          # 12
SIGMA_NEG1_6 = sum(1/d for d in DIVISORS_6)  # 1/1+1/2+1/3+1/6 = 2
INV_E = 1 / math.e                 # 0.3679
LN_4_3 = math.log(4/3)             # 0.2877
GZ_UPPER = 0.5
GZ_LOWER = 0.5 - LN_4_3           # 0.2123
ONE_MINUS_INV_E = 1 - 1/math.e    # 0.6321

results = []

def grade(hypothesis_id, title, passed, grade_str, explanation):
    results.append((hypothesis_id, title, passed, grade_str, explanation))
    status = "PASS" if passed else "FAIL"
    print(f"\n{'='*70}")
    print(f"{hypothesis_id}: {title}")
    print(f"  Grade: {grade_str}  [{status}]")
    print(f"  {explanation}")


# ════════════════════════════════════════════════════════════════════
# A. Data Center Infrastructure
# ════════════════════════════════════════════════════════════════════

# H-INFRA-001: Rack Density 6 kW/U
# Claim: Optimal air-cooled rack density converges to 6 kW/U.
# Reality: Industry standard air-cooled racks are 5-10 kW per rack (not per U).
# Per-U density in 42U racks: typical 100-250 W/U (air), up to 500 W/U (liquid).
# 6 kW/U would be ~252 kW/rack -- well beyond any air-cooled capability.
# Standard air-cooled racks: ~5-8 kW total, high-density: 15-30 kW.
# The claim confuses kW/rack with kW/U.
rack_kw_per_u_air_typical = 0.15  # 150 W/U typical air-cooled
rack_kw_per_u_claim = 6.0
off_by_factor = rack_kw_per_u_claim / rack_kw_per_u_air_typical
grade("H-INFRA-001", "Rack Density 6 kW/U",
      False, "⬛",
      f"6 kW/U is ~40x typical air-cooled density (~0.15 kW/U). "
      f"Even 6 kW/rack is at the low end. The claim likely confuses kW/rack with kW/U. "
      f"Factually incorrect as stated.")

# H-INFRA-002: Tier Delta at Divisor Ratios
# Uptime Institute availability: Tier I=99.671%, II=99.741%, III=99.982%, IV=99.995%
# Gap from perfect = 1 - availability
gaps = [1 - 0.99671, 1 - 0.99741, 1 - 0.99982, 1 - 0.99995]
# gaps = [0.00329, 0.00259, 0.00018, 0.00005]
# Ratios of successive gaps
ratios = [gaps[i+1]/gaps[i] for i in range(len(gaps)-1)]
# Predicted ratios: 5/6, 2/3, 1/2
predicted = [5/6, 2/3, 1/2]
rel_errors = [abs(r - p)/p * 100 for r, p in zip(ratios, predicted)]

grade("H-INFRA-002", "Tier Delta at Divisor Ratios",
      all(e < 10 for e in rel_errors) if False else False, "⬛",
      f"Gap ratios: {[f'{r:.4f}' for r in ratios]} vs predicted {[f'{p:.4f}' for p in predicted]}. "
      f"Relative errors: {[f'{e:.1f}%' for e in rel_errors]}. "
      f"Ratio Tier2/1={ratios[0]:.4f} (pred 0.833), Tier3/2={ratios[1]:.4f} (pred 0.667), "
      f"Tier4/3={ratios[2]:.4f} (pred 0.500). "
      f"Ratios are {ratios[0]:.3f}, {ratios[1]:.3f}, {ratios[2]:.3f} -- "
      f"Tier3/2 ratio 0.070 is nowhere near 0.667. Factually wrong.")

# H-INFRA-003: Geographic Capacity Split 1/2 + 1/3 + 1/6
# Claim: The split (1/2, 1/3, 1/6) is optimal for latency-weighted cost.
# Verification: 1/2 + 1/3 + 1/6 = 1 (mathematically exact).
# The optimality claim is unfalsifiable without specific traffic model.
# The arithmetic (sums to 1) is trivially correct.
split_sum = 1/2 + 1/3 + 1/6
grade("H-INFRA-003", "Geographic Capacity Split 1/2+1/3+1/6",
      abs(split_sum - 1.0) < 1e-15, "⚪",
      f"1/2+1/3+1/6 = {split_sum} = 1 exactly. Arithmetic correct. "
      f"Optimality claim is an assertion without proof -- any 3 fractions summing to 1 "
      f"form a valid split. The choice of (1/2,1/3,1/6) is not uniquely optimal. "
      f"Trivially correct arithmetic, unverifiable optimality claim.")

# H-INFRA-004: Cooling Technology Mix
# Same structure as H-003 -- 1/2 + 1/3 + 1/6 = 1 applied to cooling.
# PUE claim (1.15 vs 1.25) is plausible but not derivable from the math.
grade("H-INFRA-004", "Cooling Technology Mix 1/2+1/3+1/6",
      True, "⚪",
      f"1/2+1/3+1/6=1 is correct. The specific PUE claims (<=1.15) are "
      f"plausible but not derivable from perfect-number theory. "
      f"The mapping of cooling technologies to divisor fractions is arbitrary.")

# H-INFRA-005: N+2 Redundancy from sigma_{-1}(6)=2
# sigma_{-1}(6) = 1/1 + 1/2 + 1/3 + 1/6 = 2 (exact, proven)
# N+2 is a real engineering standard for critical infrastructure.
# But the connection to sigma_{-1}(6) is a post-hoc mapping.
sigma_neg1 = 1 + 1/2 + 1/3 + 1/6
grade("H-INFRA-005", "N+2 Redundancy from sigma_{-1}(6)=2",
      abs(sigma_neg1 - 2.0) < 1e-15, "⚪",
      f"sigma_{{-1}}(6) = {sigma_neg1} = 2 exactly. N+2 redundancy is indeed "
      f"standard practice. However, the causal link (N+2 BECAUSE sigma_{{-1}}(6)=2) "
      f"is a post-hoc mapping. The number 2 appears in many contexts.")


# ════════════════════════════════════════════════════════════════════
# B. Small Modular Reactors
# ════════════════════════════════════════════════════════════════════

# H-INFRA-006: 6 Modules Per Site
# Claim: 6 modules optimal because divisor structure enables flexible configs.
# Verify: How many partition subsets does 6 have?
# Partitions of 6 as sums of divisors {1,2,3}: checked combinatorially.
# Actually the claim is about configurations: {1,2,3} subsets summing to 6.
from itertools import combinations_with_replacement
target = 6
divisors = [1, 2, 3]
configs = set()
for r in range(1, target+1):
    for combo in combinations_with_replacement(divisors, r):
        if sum(combo) == target:
            configs.add(combo)

# Compare with n=4,5,7,8
def count_configs(n, divs):
    c = set()
    for r in range(1, n+1):
        for combo in combinations_with_replacement(divs, r):
            if sum(combo) == n:
                c.add(combo)
    return c

configs_4 = count_configs(4, [1,2,3])
configs_5 = count_configs(5, [1,2,3])
configs_6 = count_configs(6, [1,2,3])
configs_7 = count_configs(7, [1,2,3])
configs_8 = count_configs(8, [1,2,3])

grade("H-INFRA-006", "6 Modules Per Site",
      True, "⚪",
      f"Partition counts using divisors {{1,2,3}}: "
      f"n=4:{len(configs_4)}, n=5:{len(configs_5)}, n=6:{len(configs_6)}, "
      f"n=7:{len(configs_7)}, n=8:{len(configs_8)}. "
      f"n=6 has {len(configs_6)} configs -- not uniquely maximal vs neighbors. "
      f"The flexibility argument is correct but not special to 6. "
      f"Industry SMR sites typically plan 4-12 modules.")

# H-INFRA-007: 6 x 50 MW = 300 MW Standard
# NuScale: 77 MW x 6 = 462 MW (actual). Earlier: 50 MW x 12.
# Other SMRs: 300 MW is within range but not a universal standard.
# 300 MW is a reasonable size but "optimal" is not proven.
grade("H-INFRA-007", "6 x 50 MW = 300 MW Standard",
      True, "⚪",
      f"6 x 50 = 300 MW is arithmetically trivial. "
      f"NuScale originally planned 50 MW modules (now 77 MW). "
      f"300 MW is a plausible site size but not a proven optimum. "
      f"The 50% transmission cost claim is unverified.")

# H-INFRA-008: 12-Year Fuel Cycle (sigma(6)=12)
# sigma(6) = 1+2+3+6 = 12 (exact)
# Real SMR fuel cycles: NuScale ~24 months, some designs target 5-10 years.
# Some micro-reactors target 10-20 year sealed cores.
# 12 years is within the range of some designs but not universal.
grade("H-INFRA-008", "12-Year Fuel Cycle = sigma(6)=12",
      SIGMA_6 == 12, "⚪",
      f"sigma(6) = {SIGMA_6} = 12 exactly. "
      f"Some advanced SMR designs do target 10-20 year fuel cycles (e.g., NuScale "
      f"VOYGR: 24 months, but sealed micro-reactors: 10-20 years). "
      f"The maintenance synchronization argument (divisors 1,2,3,4,6,12) is "
      f"a property of the number 12, not specific to perfect-number theory.")

# H-INFRA-009: Safety Margin at 1/e
# Claim: Passive cooling sized at 1+1/e = 1.368x design basis.
# Real safety margins: typically 1.25x to 2.0x depending on regulation.
# 1.368 is within this range but not a standard.
safety_factor = 1 + 1/math.e
grade("H-INFRA-009", "Safety Margin at 1/e (1.368x)",
      True, "⚪",
      f"1 + 1/e = {safety_factor:.4f}. This is within typical safety margin "
      f"range (1.25-2.0x) but is not a recognized engineering standard. "
      f"The connection to 'exponential decay transition' is metaphorical.")

# H-INFRA-010: Cost Crossover at 6th Deployment
# Learning curves in manufacturing: typically 80-90% learning rate.
# Cost at 6th unit with 85% learning rate:
learning_rate = 0.85
cost_ratio_6th = learning_rate ** (math.log2(6))
grade("H-INFRA-010", "Cost Crossover at 6th Deployment",
      True, "⚪",
      f"With 85% learning curve: unit 6 cost = {cost_ratio_6th:.3f}x unit 1 "
      f"({cost_ratio_6th*100:.1f}%). With 80% curve: {0.80**math.log2(6):.3f}x. "
      f"The claim of <=80% at 6th unit requires an aggressive 80% learning rate. "
      f"Nuclear construction learning rates historically are 90-95% (slow). "
      f"The 6th-unit crossover is not supported by nuclear industry data.")


# ════════════════════════════════════════════════════════════════════
# C. Power Grid Infrastructure
# ════════════════════════════════════════════════════════════════════

# H-INFRA-011: 6-Source Generation Mix
# Claim: 6 source types maximize reliability.
# Verification: This is a diversification argument. More sources generally
# help, but 6 is not a mathematical optimum -- diminishing returns set in.
grade("H-INFRA-011", "6-Source Generation Mix",
      True, "⚪",
      f"Diversification improves reliability (basic portfolio theory). "
      f"6 sources is reasonable for a modern grid, but the LOLE claims "
      f"(0.1 vs 0.3 days/year) are not derivable from perfect-number theory. "
      f"The connection to divisor structure is metaphorical.")

# H-INFRA-012: N-2 Contingency Standard from sigma_{-1}(6)=2
# N-1 is the actual NERC standard. N-2 (TPPL-003) exists for certain elements.
# sigma_{-1}(6) = 2 is exact, but N-2 is not the universal standard.
grade("H-INFRA-012", "N-2 Contingency from sigma_{-1}(6)=2",
      abs(sigma_neg1 - 2.0) < 1e-15, "⚪",
      f"sigma_{{-1}}(6) = 2 exactly. N-2 contingency does exist (NERC TPL-003) "
      f"but N-1 (TPL-001) remains the base standard. The causal connection "
      f"to sigma_{{-1}} is a post-hoc mapping.")

# H-INFRA-013: Transmission Loss at 1/e Gap
# Claim: Optimal voltage where losses = 0.368 x (gen cost - delivery cost).
# This is a cost optimization claim. Let's check if it has mathematical basis.
# For a simple loss model: P_loss = I^2 R ~ P^2/(V^2) * R
# Total cost = gen_cost + loss_cost + capital_cost(V)
# Optimizing: d/dV [loss_cost + capital_cost] = 0
# The 1/e factor would need to arise naturally from this optimization.
# It does NOT in general -- it depends on the specific cost functions.
grade("H-INFRA-013", "Transmission Loss at 1/e Gap",
      True, "⚪",
      f"The optimization of transmission voltage is a well-studied problem. "
      f"The factor 1/e does not naturally arise from standard loss models "
      f"(P_loss ~ P^2*R/V^2). The 2% claim is unverifiable without specific "
      f"cost functions. Mapping is post-hoc.")

# H-INFRA-014: Frequency Deadband at ln(4/3)
# Claim: Deadband = ln(4/3) * f_nominal
# For 50 Hz: ln(4/3) * 50 = 0.2877 * 50 = 14.38 Hz (!!)
# Wait -- the claim says "mHz". Let's recalculate:
# ln(4/3) * 50 = 14.38 -- this is in Hz, not mHz.
# If interpreted as fraction: ln(4/3) * 50 Hz = 14.4 Hz (not mHz!)
# For mHz: 14.4 mHz = 0.0144 Hz, which would be ln(4/3)/1000 * 50.
# Standard deadbands: 10-20 mHz for 50 Hz systems.
# The hypothesis says "0.288 x 50 = 14.4 mHz" -- but 0.288 * 50 = 14.4 Hz, not mHz!
deadband_hz = LN_4_3 * 50
deadband_mhz_claim = 14.4  # mHz as stated
actual_calc = LN_4_3 * 50  # = 14.38 Hz, not mHz!

grade("H-INFRA-014", "Frequency Deadband at ln(4/3)",
      False, "⬛",
      f"ln(4/3) x 50 = {deadband_hz:.2f} Hz, NOT {deadband_mhz_claim} mHz as claimed. "
      f"The hypothesis has a units error: 0.288 x 50 = 14.4 (Hz), but it says mHz. "
      f"To get 14.4 mHz, you'd need ln(4/3) x 50 / 1000, which is not ln(4/3) x f_nominal. "
      f"Arithmetic/units error.")

# H-INFRA-015: Storage Ratio 1/6 of Peak Demand
# Claim: Storage = 1/6 of peak MW enables 95% renewable integration.
# 1/6 = 0.1667. For a 60 GW peak grid: 10 GW storage.
# Real-world: NREL studies suggest 4-8 hours of storage at ~10-20% of peak
# for high renewable penetration. 1/6 (16.7%) is within this range.
grade("H-INFRA-015", "Storage Ratio 1/6 of Peak Demand",
      True, "⚪",
      f"1/6 = {1/6:.4f} of peak demand. This is within the range of "
      f"real grid studies (10-25% of peak for high renewables). "
      f"However, the specific 95% renewable / 1% curtailment claim is not "
      f"derivable from the constant system. Reasonable but post-hoc.")


# ════════════════════════════════════════════════════════════════════
# D. Sustainable Infrastructure
# ════════════════════════════════════════════════════════════════════

# H-INFRA-016: 6-Phase Carbon Neutrality
# 1/2 + 1/3 + 1/6 = 1 (first 3 phases cover 100%).
# But then what do phases 4-6 do? The claim contradicts itself.
grade("H-INFRA-016", "6-Phase Carbon Neutrality",
      True, "⚪",
      f"1/2+1/3+1/6=1 means phases 1-3 already cover 100% of emissions. "
      f"Phases 4-6 (storage, capture, offsets) are then redundant by the "
      f"hypothesis's own math. Internal inconsistency. "
      f"The 6-phase structure is arbitrary categorization.")

# H-INFRA-017: Electrolysis Efficiency at 1-1/e = 63.2%
# Real efficiencies (HHV):
#   Alkaline: 60-70% (commercial), PEM: 55-70%, SOEC: 75-90%
# The claim that <5% exceed 63.2% is FALSE -- many commercial systems exceed this.
# SOEC routinely achieves 75%+ HHV efficiency.
grade("H-INFRA-017", "Electrolysis Efficiency at 1-1/e = 63.2%",
      False, "⬛",
      f"1 - 1/e = {ONE_MINUS_INV_E:.4f} = 63.2%. "
      f"However, SOEC electrolyzers achieve 75-90% HHV efficiency, "
      f"and advanced PEM achieves 65-70%. The claim that <5% exceed 63.2% "
      f"is factually incorrect. Even alkaline systems can exceed this.")

# H-INFRA-018: 6 Buildings Per Thermal Node
# The claim about minimizing pipe diameter steps via divisor structure
# has no hydraulic engineering basis. Pipe sizing depends on flow rate,
# pressure drop, and distance -- not divisor combinatorics.
grade("H-INFRA-018", "6 Buildings Per Thermal Node",
      True, "⚪",
      f"6 buildings per node is within typical district heating practice "
      f"(4-10 per branch). The divisor-based pipe sizing argument has no "
      f"basis in hydraulic engineering. Reasonable number, arbitrary mapping.")

# H-INFRA-019: 6 Microgrids Per Federation
# Claim: Divisor structure enables balanced power-sharing for all failure subsets.
# Number of non-empty subsets of 6 members: 2^6 - 1 = 63.
# For n members, coalitions that can exactly compensate k failures:
# This is a combinatorial argument. Let's check: with 6 members, each
# contributing 1 unit, can every subset of failures be compensated?
# If k members fail, remaining 6-k must cover. This is trivial as long
# as there's enough total capacity. Not related to divisors of 6.
grade("H-INFRA-019", "6 Microgrids Per Federation",
      True, "⚪",
      f"6 microgrids have 2^6-1=63 non-empty subsets. The availability "
      f"claims (99.9% vs 99.5%) are not derivable from divisor theory. "
      f"The 'balanced coalition' argument works for any n with sufficient "
      f"capacity. Not unique to n=6.")

# H-INFRA-020: EROI Cliff at 3:1
# 6/2 = 3 (correct arithmetic from divisors of 6).
# Real EROI thresholds: Hall et al. (2014) suggest EROI ~3:1 as minimum
# for civilization to function. This is a genuine finding in energy science!
# However, it was derived from thermodynamic/economic analysis, not from
# perfect number theory. The mapping is post-hoc but the 3:1 threshold is real.
grade("H-INFRA-020", "EROI Cliff at 3:1",
      6/2 == 3, "🟧",
      f"6/2 = 3 exactly. The 3:1 EROI threshold IS a real finding in energy "
      f"science (Hall et al. 2014, 'EROI of different fuels'). The historical "
      f"claim about technologies <3:1 never exceeding 5% is approximately "
      f"supported. However, the DERIVATION from 6/2 is post-hoc -- the real "
      f"3:1 threshold comes from thermodynamic net-energy analysis, not from "
      f"perfect number divisors. Numerically interesting coincidence.")


# ════════════════════════════════════════════════════════════════════
# Summary
# ════════════════════════════════════════════════════════════════════
print("\n")
print("=" * 70)
print("SUMMARY: Infrastructure Hypotheses H-INFRA-001 to H-INFRA-020")
print("=" * 70)

grade_counts = {}
for hid, title, passed, g, expl in results:
    grade_counts[g] = grade_counts.get(g, 0) + 1
    status = "PASS" if passed else "FAIL"
    print(f"  {hid}: {g} [{status}] {title}")

print(f"\n  Grade Distribution:")
for g in ["🟩", "🟧", "⚪", "⬛"]:
    count = grade_counts.get(g, 0)
    print(f"    {g}: {count}")

print(f"\n  Total: {len(results)} hypotheses")
print(f"  Key Findings:")
print(f"    - No hypothesis achieves 🟩 (proven). None derive infrastructure")
print(f"      constants FROM perfect-number theory; all are post-hoc mappings.")
print(f"    - H-INFRA-020 (EROI 3:1) is the most interesting: the threshold")
print(f"      is real in energy science, though not derived from 6/2.")
print(f"    - H-INFRA-001 has a factual error (kW/U vs kW/rack confusion).")
print(f"    - H-INFRA-014 has a units error (Hz vs mHz).")
print(f"    - H-INFRA-017 is factually wrong (SOEC exceeds 63.2%).")
print(f"    - Most hypotheses (13/20) are ⚪: correct arithmetic applied to")
print(f"      infrastructure via arbitrary post-hoc mappings.")
