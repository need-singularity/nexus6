#!/usr/bin/env python3
"""
Explore connections between n=6 (the first perfect number) and sporadic groups / moonshine.
"""

from math import gcd, log2, log
from sympy import factorint, isprime, divisors, divisor_sigma, totient
from functools import reduce

print("=" * 80)
print("  n=6 AND SPORADIC GROUPS / MOONSHINE CONNECTIONS")
print("=" * 80)

# === Arithmetic functions of 6 ===
n = 6
sigma_6 = int(divisor_sigma(n, 1))  # 12
tau_6 = len(divisors(n))            # 4
phi_6 = int(totient(n))             # 2
sigma_star_phi = sigma_6 * phi_6    # 24

print(f"\n--- Arithmetic functions of 6 ---")
print(f"  sigma(6) = {sigma_6}")
print(f"  tau(6)   = {tau_6}")
print(f"  phi(6)   = {phi_6}")
print(f"  sigma(6)*phi(6) = {sigma_star_phi}")
print(f"  sigma(6) - tau(6) = {sigma_6 - tau_6}")
print(f"  6 itself (P_1, first perfect number)")

# =========================================================================
# 1. MATHIEU GROUPS
# =========================================================================
print("\n" + "=" * 80)
print("  1. MATHIEU GROUPS")
print("=" * 80)

mathieu_groups = {
    'M_11': {'order': 7920,    'acts_on': 11, 'mult_trans': 4},
    'M_12': {'order': 95040,   'acts_on': 12, 'mult_trans': 5},
    'M_22': {'order': 443520,  'acts_on': 22, 'mult_trans': 3},
    'M_23': {'order': 10200960,'acts_on': 23, 'mult_trans': 4},
    'M_24': {'order': 244823040,'acts_on': 24, 'mult_trans': 5},
}

print(f"\n{'Group':<8} {'|G|':>15} {'Acts on':>8} {'Factorization':<35} {'v_2(|G|)':>8}")
print("-" * 80)
for name, info in mathieu_groups.items():
    order = info['order']
    acts = info['acts_on']
    factors = factorint(order)
    fstr = " * ".join(f"{p}^{e}" if e > 1 else str(p) for p, e in sorted(factors.items()))
    v2 = factors.get(2, 0)
    print(f"{name:<8} {order:>15,} {acts:>8} {fstr:<35} {v2:>8}")

print(f"\n  KEY OBSERVATIONS:")
print(f"  * M_12 acts on {mathieu_groups['M_12']['acts_on']} = sigma(6) points")
print(f"  * M_24 acts on {mathieu_groups['M_24']['acts_on']} = sigma(6)*phi(6) points")
print(f"  * v_2(|M_12|) = {factorint(mathieu_groups['M_12']['order']).get(2,0)} = 6 = P_1 (first perfect number!)")
print(f"  * M_12 and M_24 are the ONLY 5-transitive Mathieu groups")
print(f"  * M_12 transitivity = 5, M_24 transitivity = 5")

# =========================================================================
# 2. STEINER SYSTEMS
# =========================================================================
print("\n" + "=" * 80)
print("  2. STEINER SYSTEMS")
print("=" * 80)

print(f"""
  S(5, 6, 12): The small Witt design
    - Block size    = 6  = P_1 (first perfect number)
    - Point set     = 12 = sigma(6)
    - t-design      = 5  (5-transitive)
    - # of blocks   = C(12,5)/C(6,5) = {792//6}
    - Automorphism group = M_12

  S(5, 8, 24): The large Witt design
    - Block size    = 8  = sigma(6) - tau(6)
    - Point set     = 24 = sigma(6) * phi(6)
    - t-design      = 5  (5-transitive)
    - # of blocks   = C(24,5)/C(8,5) = {42504//56}
    - Automorphism group = M_24

  CONNECTION TABLE:
  +------------------+----------------+-------------------+
  | Parameter        | S(5,6,12)      | S(5,8,24)         |
  +------------------+----------------+-------------------+
  | block size       | 6 = P_1        | 8 = sigma-tau     |
  | points           | 12 = sigma(6)  | 24 = sigma*phi(6) |
  | aut group        | M_12           | M_24              |
  | v_2(|Aut|)       | 6 = P_1        | 10                |
  +------------------+----------------+-------------------+
""")

# Verify block counts
from math import comb
blocks_512 = comb(12, 5) // comb(6, 5)
blocks_524 = comb(24, 5) // comb(8, 5)
print(f"  S(5,6,12) blocks: C(12,5)/C(6,5) = {comb(12,5)}/{comb(6,5)} = {blocks_512}")
print(f"  S(5,8,24) blocks: C(24,5)/C(8,5) = {comb(24,5)}/{comb(8,5)} = {blocks_524}")
print(f"  Ratio: {blocks_524}/{blocks_512} = {blocks_524/blocks_512:.4f}")

# =========================================================================
# 3. GOLAY CODE
# =========================================================================
print("\n" + "=" * 80)
print("  3. GOLAY CODE — [24, 12, 8]")
print("=" * 80)

golay_n = 24
golay_k = 12
golay_d = 8

print(f"""
  Binary Golay code parameters: [{golay_n}, {golay_k}, {golay_d}]

  Parameter mapping to n=6:
  +------------------+-------+----------------------------+
  | Code parameter   | Value | Function of 6              |
  +------------------+-------+----------------------------+
  | Length n          |  {golay_n:>3}  | sigma(6)*phi(6) = 12*2     |
  | Dimension k      |  {golay_k:>3}  | sigma(6)                   |
  | Min distance d   |   {golay_d:>3}  | sigma(6) - tau(6) = 12-4   |
  +------------------+-------+----------------------------+

  Verification:
    sigma(6) = {sigma_6}  --> dimension = {golay_k} CHECK: {sigma_6 == golay_k}
    sigma(6)*phi(6) = {sigma_star_phi} --> length = {golay_n} CHECK: {sigma_star_phi == golay_n}
    sigma(6)-tau(6) = {sigma_6 - tau_6}  --> min dist = {golay_d} CHECK: {sigma_6 - tau_6 == golay_d}

  The extended Golay code:
    - 2^12 = {2**12} codewords
    - Weight enumerator: A_0=1, A_8=759, A_12=2576, A_16=759, A_24=1
    - 759 = blocks of S(5,8,24) = min-weight codewords
    - 2576 = weight-12 codewords (dimension = sigma(6))
""")

# Ternary Golay code
print(f"  Ternary Golay code: [{golay_k}, 6, {golay_d-2}]")
print(f"    Length = {golay_k} = sigma(6)")
print(f"    Dimension = 6 = P_1")
print(f"    Min distance = 6 = P_1")
print(f"    --> The ternary Golay code has BOTH dimension and min distance = 6!")

# =========================================================================
# 4. LEECH LATTICE
# =========================================================================
print("\n" + "=" * 80)
print("  4. LEECH LATTICE")
print("=" * 80)

leech_dim = 24
leech_kissing = 196560
leech_min_norm_sq = 4

print(f"""
  Leech lattice Lambda_24:
    Dimension        = {leech_dim} = sigma(6)*phi(6)
    Kissing number   = {leech_kissing:,}
    Min norm squared = {leech_min_norm_sq} = tau(6)

  Constructed from Golay code [{golay_n},{golay_k},{golay_d}]:
    All three Golay parameters are functions of 6.
    --> Leech lattice is "built from n=6 arithmetic"
""")

# Factor the kissing number
k_factors = factorint(leech_kissing)
k_fstr = " * ".join(f"{p}^{e}" if e > 1 else str(p) for p, e in sorted(k_factors.items()))
print(f"  Kissing number factorization: {leech_kissing:,} = {k_fstr}")
print(f"  196560 / 6  = {leech_kissing // 6:,}  (divisible by 6: {leech_kissing % 6 == 0})")
print(f"  196560 / 12 = {leech_kissing // 12:,}  (divisible by sigma(6): {leech_kissing % 12 == 0})")
print(f"  196560 / 24 = {leech_kissing // 24:,}  (divisible by sigma*phi: {leech_kissing % 24 == 0})")

# Conway groups from Leech lattice
print(f"\n  Conway groups (automorphisms of Leech lattice):")
conway = {
    'Co_0': {'order': 8315553613086720000, 'note': 'full aut group (incl. -1)'},
    'Co_1': {'order': 4157776806543360000, 'note': 'Co_0 / {+/-1}'},
    'Co_2': {'order': 42305421312000, 'note': 'stabilizer of type-2 vector'},
    'Co_3': {'order': 495766656000, 'note': 'stabilizer of type-3 vector'},
}
print(f"  {'Group':<8} {'|G|':>25} {'Note':<40}")
print(f"  {'-'*75}")
for name, info in conway.items():
    print(f"  {name:<8} {info['order']:>25,} {info['note']:<40}")

co1_factors = factorint(conway['Co_1']['order'])
co1_fstr = " * ".join(f"{p}^{e}" if e > 1 else str(p) for p, e in sorted(co1_factors.items()))
print(f"\n  |Co_1| = {co1_fstr}")
v2_co1 = co1_factors.get(2, 0)
v3_co1 = co1_factors.get(3, 0)
print(f"  v_2(|Co_1|) = {v2_co1}")
print(f"  v_3(|Co_1|) = {v3_co1}")

# =========================================================================
# 5. MONSTER GROUP AND MOONSHINE
# =========================================================================
print("\n" + "=" * 80)
print("  5. MONSTER GROUP AND MONSTROUS MOONSHINE")
print("=" * 80)

# Monster order
monster_order = (2**46) * (3**20) * (5**9) * (7**6) * (11**2) * (13**3) * 17 * 19 * 23 * 29 * 31 * 41 * 47 * 59 * 71
monster_factors = factorint(monster_order)

print(f"\n  |Monster| = 2^46 * 3^20 * 5^9 * 7^6 * 11^2 * 13^3 * 17 * 19 * 23 * 29 * 31 * 41 * 47 * 59 * 71")
print(f"  |Monster| = {monster_order:,}")
print(f"  |Monster| has {len(str(monster_order))} digits")

print(f"\n  Exponents in |Monster| related to n=6:")
print(f"  +----------+----------+----------------------------+")
print(f"  | Prime p  | v_p(|M|) | Relation to 6              |")
print(f"  +----------+----------+----------------------------+")
relations = {
    2: "46 (no simple relation)",
    3: "20 (no simple relation)",
    5: "9 = sigma(6) - tau(6) + 1?",
    7: "6 = P_1 !!!",
    11: "2 = phi(6)",
    13: "3 (= # prime factors of 6)",
    17: "1",
    19: "1",
    23: "1",
    29: "1",
    31: "1",
    41: "1",
    47: "1",
    59: "1",
    71: "1",
}
for p in sorted(monster_factors.keys()):
    e = monster_factors[p]
    rel = relations.get(p, "")
    marker = " <-- v_7 = 6!" if p == 7 else ""
    print(f"  | {p:>6}   | {e:>8} | {rel:<26} |{marker}")
print(f"  +----------+----------+----------------------------+")
print(f"\n  KEY: v_7(|Monster|) = 6 = P_1 (first perfect number)")
print(f"       v_11(|Monster|) = 2 = phi(6)")

# =========================================================================
# 6. j-FUNCTION AND 196884
# =========================================================================
print("\n" + "=" * 80)
print("  6. j-FUNCTION, 196884, AND MCKAY'S OBSERVATION")
print("=" * 80)

j1 = 196884  # coefficient of q in j(q)
monster_rep = 196883  # smallest faithful rep

print(f"\n  j(tau) = q^(-1) + 744 + 196884*q + 21493760*q^2 + ...")
print(f"  Smallest faithful Monster rep: {monster_rep}")
print(f"  McKay: {j1} = 1 + {monster_rep}")
print(f"  Thompson: {j1} = {monster_rep} + 1 (trivial + faithful)")

# Divisibility by functions of 6
print(f"\n  Divisibility of {j1} by functions of 6:")
for val, name in [(6, 'P_1'), (12, 'sigma(6)'), (24, 'sigma*phi'), (4, 'tau(6)'), (2, 'phi(6)'), (8, 'sigma-tau')]:
    q, r = divmod(j1, val)
    div = "YES" if r == 0 else "no"
    print(f"    {j1} / {val:>2} ({name:>12}) = {q:>8}.{'0' if r==0 else str(r/val)[:4]} [{div}]")

j1_factors = factorint(j1)
j1_fstr = " * ".join(f"{p}^{e}" if e > 1 else str(p) for p, e in sorted(j1_factors.items()))
print(f"\n  {j1} = {j1_fstr}")

rep_factors = factorint(monster_rep)
rep_fstr = " * ".join(f"{p}^{e}" if e > 1 else str(p) for p, e in sorted(rep_factors.items()))
print(f"  {monster_rep} = {rep_fstr}")

print(f"\n  196884 = 4 * 49221 = tau(6) * 49221")
print(f"  196884 / 6 = {j1 // 6} = 2 * 3 * {j1 // 6 // 6}")
print(f"  196884 / 12 = {j1 // 12} = {j1 // 12}")
f49221 = factorint(49221)
print(f"  49221 = {' * '.join(f'{p}^{e}' if e>1 else str(p) for p,e in sorted(f49221.items()))}")

# 744 (constant term of j)
print(f"\n  Constant term: 744")
f744 = factorint(744)
f744_str = " * ".join(f"{p}^{e}" if e > 1 else str(p) for p, e in sorted(f744.items()))
print(f"  744 = {f744_str}")
print(f"  744 / 6  = {744 // 6} = {744//6}")
print(f"  744 / 12 = {744 // 12}")
print(f"  744 / 24 = {744 // 24} = 31")
print(f"  744 = 24 * 31 = sigma(6)*phi(6) * 31")

# More j-function coefficients
j_coeffs = [1, 744, 196884, 21493760, 864299970, 20245856256]
print(f"\n  j-function coefficients mod 6 and mod 12:")
print(f"  {'n':>4} {'c_n':>15} {'c_n mod 6':>10} {'c_n mod 12':>11} {'c_n / 6':>15} {'c_n / 12':>15}")
print(f"  {'-'*72}")
for i, c in enumerate(j_coeffs):
    m6 = c % 6
    m12 = c % 12
    d6 = f"{c // 6}" if m6 == 0 else "---"
    d12 = f"{c // 12}" if m12 == 0 else "---"
    print(f"  {i-1:>4} {c:>15,} {m6:>10} {m12:>11} {d6:>15} {d12:>15}")

# =========================================================================
# 7. ALL 26 SPORADIC GROUPS - R(n) analysis
# =========================================================================
print("\n" + "=" * 80)
print("  7. ALL 26 SPORADIC GROUPS — v_2, v_3, mod 6 ANALYSIS")
print("=" * 80)

sporadic_groups = {
    'M_11':      7920,
    'M_12':      95040,
    'M_22':      443520,
    'M_23':      10200960,
    'M_24':      244823040,
    'J_1':       175560,
    'J_2':       604800,
    'J_3':       50232960,
    'J_4':       86775571046077562880,
    'HS':        44352000,
    'McL':       898128000,
    'Co_3':      495766656000,
    'Co_2':      42305421312000,
    'Co_1':      4157776806543360000,
    'He':        4030387200,
    'Fi_22':     64561751654400,
    'Fi_23':     4089470473293004800,
    'Fi_24p':    1255205709190661721292800,
    'Suz':       448345497600,
    'Ru':        145926144000,
    'ON':        460815505920,
    'HN':        273030912000000,
    'Ly':        51765179004000000,
    'Th':        90745943887872000,
    'B':         4154781481226426191177580544000000,
    'M':         monster_order,
}

print(f"\n  {'Group':<10} {'|G| digits':>10} {'v_2':>5} {'v_3':>5} {'v_7':>5} {'|G| mod 6':>10} {'div by 6':>8}")
print(f"  {'-'*60}")

v2_is_6 = []
v7_is_6 = []
div_by_6_count = 0

for name, order in sporadic_groups.items():
    factors = factorint(order)
    v2 = factors.get(2, 0)
    v3 = factors.get(3, 0)
    v7 = factors.get(7, 0)
    mod6 = order % 6
    divby6 = "YES" if mod6 == 0 else "no"
    if mod6 == 0:
        div_by_6_count += 1
    ndigits = len(str(order))

    marker = ""
    if v2 == 6:
        v2_is_6.append(name)
        marker += " <-- v_2=6"
    if v7 == 6:
        v7_is_6.append(name)
        marker += " <-- v_7=6"

    print(f"  {name:<10} {ndigits:>10} {v2:>5} {v3:>5} {v7:>5} {mod6:>10} {divby6:>8}{marker}")

print(f"\n  Groups with v_2(|G|) = 6 (= P_1): {v2_is_6 if v2_is_6 else 'none'}")
print(f"  Groups with v_7(|G|) = 6 (= P_1): {v7_is_6 if v7_is_6 else 'none'}")
print(f"  Groups divisible by 6: {div_by_6_count} / {len(sporadic_groups)} = ALL" if div_by_6_count == len(sporadic_groups) else f"  Groups divisible by 6: {div_by_6_count} / {len(sporadic_groups)}")

# =========================================================================
# 8. DEEPER: sigma-phi CHAIN
# =========================================================================
print("\n" + "=" * 80)
print("  8. THE sigma-phi CHAIN: 6 -> 12 -> 24 -> SPORADIC")
print("=" * 80)

print(f"""
  Start:  6 (first perfect number)

  sigma(6) = 12   --> M_12 acts on 12 points
                   --> S(5,6,12) on 12 points with blocks of 6
                   --> Golay code dimension = 12
                   --> Ternary Golay code length = 12

  sigma(6)*phi(6) = 12*2 = 24
                   --> M_24 acts on 24 points
                   --> S(5,8,24) on 24 points
                   --> Binary Golay code length = 24
                   --> Leech lattice dimension = 24

  Leech lattice   --> Co_0 (Conway group)
                   --> Monster (via FLM vertex algebra on Leech)

  tau(6) = 4      --> Leech lattice min norm^2 = 4
                   --> 196884 = 4 * 49221

  sigma(6)-tau(6) = 8
                   --> Golay code min distance = 8
                   --> S(5,8,24) block size = 8
                   --> E_8 lattice dimension = 8
""")

# =========================================================================
# 9. E_8 CONNECTION
# =========================================================================
print("=" * 80)
print("  9. E_8 LATTICE AND 6")
print("=" * 80)

e8_dim = 8
e8_kissing = 240
e8_det = 1

print(f"\n  E_8 lattice:")
print(f"    Dimension = {e8_dim} = sigma(6) - tau(6)")
print(f"    Kissing number = {e8_kissing}")
e8k_factors = factorint(e8_kissing)
e8k_fstr = " * ".join(f"{p}^{e}" if e > 1 else str(p) for p, e in sorted(e8k_factors.items()))
print(f"    240 = {e8k_fstr}")
print(f"    240 / 6  = {240 // 6} (divisible by P_1)")
print(f"    240 / 12 = {240 // 12} (divisible by sigma(6))")
print(f"    240 / 24 = {240 // 24} (divisible by sigma*phi)")
print(f"    240 = sigma(6) * phi(6) * 10 = 24 * 10")
print(f"    240 = 2 * sigma_1(6)^2 - sigma_1(6) * tau(6) ??? let's check: {2*12**2 - 12*4} = {2*144-48}")
print(f"    Actually: 240 = 2 * 120 = 2 * 5! and also 240 = Product(d|6, d+1) - 1 ??? = {(1+1)*(2+1)*(3+1)*(6+1)-1}")

# Check: product of (d+1) for d|6
divs6 = divisors(6)
prod_d_plus_1 = 1
for d in divs6:
    prod_d_plus_1 *= (d + 1)
print(f"    Product of (d+1) for d|6: {' * '.join(str(d+1) for d in divs6)} = {prod_d_plus_1}")
print(f"    Product - 1 = {prod_d_plus_1 - 1}")

# sum of (d^3) for d|6
sum_d3 = sum(d**3 for d in divs6)
print(f"    Sum of d^3 for d|6: {' + '.join(str(d**3) for d in divs6)} = {sum_d3}")
print(f"    sigma_3(6) = {sum_d3}")
print(f"    {sum_d3} vs 240: ratio = {240/sum_d3:.4f}")
print(f"    240 = sigma_3(6) + {240 - sum_d3}")

# 240 = sum of Euler phi over d|24?
sum_phi_24 = sum(int(totient(d)) for d in divisors(24))
print(f"    Sum of phi(d) for d|24 = {sum_phi_24}  (should be 24)")
# Actually 240 is the kissing number. Let's note:
# 240 = |W(E_8)| / |W(D_8)| * something? No, |W(E_8)| = 696729600
we8 = 696729600
print(f"    |W(E_8)| = {we8:,}")
print(f"    |W(E_8)| / 240 = {we8 // 240:,}")
print(f"    |W(E_8)| / 6 = {we8 // 6:,}")

# =========================================================================
# 10. SUMMARY TABLE
# =========================================================================
print("\n" + "=" * 80)
print("  10. GRAND SUMMARY: n=6 ARITHMETIC --> SPORADIC LANDSCAPE")
print("=" * 80)

summary = [
    ("6 = P_1",            "S(5,6,12) block size",    "Ternary Golay dim & dist", "v_2(|M_12|), v_7(|M|)"),
    ("12 = sigma(6)",      "M_12 acts on 12 pts",     "Golay [24,12,8] dim",      "S(5,6,12) point set"),
    ("24 = sigma*phi",     "M_24 acts on 24 pts",     "Golay [24,12,8] length",   "Leech lattice dim"),
    ("4 = tau(6)",         "Leech min norm^2",        "196884 = 4 * 49221",       "S(5,6,12) t-val - 1"),
    ("2 = phi(6)",         "sigma/phi = 6 chain",     "v_11(|M|) = 2",            "24/12 ratio"),
    ("8 = sigma-tau",      "Golay min distance",      "S(5,8,24) block size",     "E_8 dimension"),
]

print(f"\n  {'Value':<20} {'Connection 1':<25} {'Connection 2':<28} {'Connection 3':<25}")
print(f"  {'-'*98}")
for row in summary:
    print(f"  {row[0]:<20} {row[1]:<25} {row[2]:<28} {row[3]:<25}")

# =========================================================================
# 11. TEXAS SHARPSHOOTER CHECK
# =========================================================================
print("\n" + "=" * 80)
print("  11. TEXAS SHARPSHOOTER ASSESSMENT")
print("=" * 80)

print(f"""
  How many of these connections are STRUCTURAL (not cherry-picked)?

  STRUCTURAL (well-known mathematical facts):
    [S] M_12 acts on 12 = sigma(6) points           -- by construction
    [S] M_24 acts on 24 = sigma(6)*phi(6) points     -- by construction
    [S] S(5,6,12) has block size 6                    -- by definition
    [S] Golay [24,12,8] parameters                    -- proved
    [S] Leech lattice dim 24 from Golay               -- construction
    [S] E_8 dim 8                                     -- standard

  The key question: Is it a COINCIDENCE that sigma(6)=12 and phi(6)=2
  happen to be the parameters that generate the sporadic groups?

  Or does the "perfection" of 6 (sigma(6)=2*6=12, unique divisor structure)
  create the arithmetic conditions needed for these exceptional objects?

  OBSERVATION: The chain 6 -> 12 -> 24 is:
    6 -> sigma(6) -> sigma(6)*phi(6)
    This is equivalent to: 6 -> 2*6 -> 4*6
    Which is just: 6, 12, 24 = 6*2^k for k=0,1,2

  But sigma(6)=12 is NOT arbitrary -- it follows from 6 being perfect:
    sigma(6) = 2*6 BECAUSE 6 is perfect.

  So the chain is: P_1 -> 2*P_1 -> 4*P_1
  And the sporadic groups live at 2*P_1 and 4*P_1.

  VERDICT: The 6->12->24 chain is STRUCTURALLY significant because
  6 being perfect forces sigma(6)=12, and the Mathieu/Golay/Leech
  objects genuinely require exactly these parameters.
  The v_2(|M_12|)=6 and v_7(|M|)=6 coincidences are less clear.
""")

# =========================================================================
# 12. NUMERICAL MOONSHINE: j-coefficients and 6
# =========================================================================
print("=" * 80)
print("  12. j-FUNCTION COEFFICIENTS DEEPER ANALYSIS")
print("=" * 80)

# First several j-function coefficients (of j(tau) - 744)
# j(tau) = q^{-1} + 744 + sum c_n q^n
j_minus_744 = [196884, 21493760, 864299970, 20245856256, 333202640600,
               4252023300096, 44656994071935, 401490886656000,
               3176440229784420, 22567393309593600]

print(f"\n  First 10 coefficients of j(tau) - 744:")
print(f"  {'n':>4} {'c_n':>20} {'c_n mod 6':>10} {'c_n mod 12':>11} {'c_n mod 24':>11} {'c_n / 12':>18}")
print(f"  {'-'*78}")
all_div_6 = True
all_div_12 = True
for i, c in enumerate(j_minus_744, 1):
    m6 = c % 6
    m12 = c % 12
    m24 = c % 24
    if m6 != 0: all_div_6 = False
    if m12 != 0: all_div_12 = False
    d12 = str(c // 12) if m12 == 0 else "---"
    print(f"  {i:>4} {c:>20,} {m6:>10} {m12:>11} {m24:>11} {d12:>18}")

print(f"\n  All c_n divisible by 6?  {all_div_6}")
print(f"  All c_n divisible by 12? {all_div_12}")

# Check: are all j-coefficients divisible by 12?
# This is actually known: c_n ≡ 0 (mod 12) for all n >= 1? Let's verify.
# Actually c_1 = 196884 = 12 * 16407. Yes.
print(f"\n  196884 / 12 = {196884 // 12}")
print(f"  21493760 / 12 = {21493760 // 12}")
print(f"  If true for all n: j(tau) - 744 ≡ 0 (mod 12 = sigma(6)) for Im(tau) > 0")
print(f"  This would mean: the moonshine module decomposes into sigma(6)-sized blocks!")

print("\n" + "=" * 80)
print("  COMPUTATION COMPLETE")
print("=" * 80)
