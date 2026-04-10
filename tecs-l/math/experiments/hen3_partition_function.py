"""
H-EN-3 + H-EN-14: Divisor Partition Function and Thermal Activation
====================================================================
Computes Z_n(beta) = sum_{d|n} exp(-beta*d) and derived thermodynamic quantities.

Golden Zone constants:
  W = ln(4/3)  (Golden Zone Width ~ 0.2877)
  1/e          (Golden Zone Center ~ 0.3679)
"""

import math
from fractions import Fraction


# ─── Utility Functions ──────────────────────────────────────────────────────

def get_divisors(n):
    """Return sorted list of divisors of n."""
    divs = []
    for i in range(1, int(n**0.5) + 1):
        if n % i == 0:
            divs.append(i)
            if i != n // i:
                divs.append(n // i)
    return sorted(divs)


def compute_partition(n, beta):
    """Z_n(beta) = sum_{d|n} exp(-beta*d)"""
    divs = get_divisors(n)
    return sum(math.exp(-beta * d) for d in divs)


def compute_free_energy(n, beta):
    """F = -ln(Z) / beta"""
    Z = compute_partition(n, beta)
    return -math.log(Z) / beta


def compute_internal_energy(n, beta):
    """U = <E> = sum_{d|n} d * exp(-beta*d) / Z"""
    divs = get_divisors(n)
    Z = compute_partition(n, beta)
    return sum(d * math.exp(-beta * d) for d in divs) / Z


def compute_entropy(n, beta):
    """S = beta * (U - F)"""
    U = compute_internal_energy(n, beta)
    F = compute_free_energy(n, beta)
    return beta * (U - F)


def compute_specific_heat(n, beta, dbeta=1e-6):
    """C = d<E>/d(beta) via finite difference (= -dU/d(1/beta) * (1/beta^2))"""
    U_plus  = compute_internal_energy(n, beta + dbeta)
    U_minus = compute_internal_energy(n, beta - dbeta)
    dU_dbeta = (U_plus - U_minus) / (2 * dbeta)
    # C = -beta^2 * dU/dbeta (heat capacity per kB)
    return -beta**2 * dU_dbeta


# ─── Part 1: Full table for all n and beta values ────────────────────────────

NS    = [1, 2, 3, 4, 5, 6, 7, 8, 10, 12, 28, 120]
BETAS = [0.01, 0.1, 0.2, 0.5, 1.0, 2.0, 5.0, 10.0]

W = math.log(4/3)         # Golden Zone Width
INV_E = 1 / math.e        # Golden Zone Center

print("=" * 80)
print("H-EN-3 + H-EN-14: DIVISOR PARTITION FUNCTION — THERMAL ANALYSIS")
print("=" * 80)
print(f"\nGolden Zone Width  W = ln(4/3) = {W:.6f}")
print(f"Golden Zone Center   = 1/e     = {INV_E:.6f}")
print()

# ── Table header ──
print("PART 1: Thermodynamic Quantities Z, F, U, S, C")
print("-" * 80)

for n in NS:
    divs = get_divisors(n)
    sigma = sum(divs)
    tau   = len(divs)
    avg_d = sigma / tau
    print(f"\n  n={n:3d}  divisors={divs}  sigma(n)={sigma}  tau(n)={tau}  <d>={avg_d:.4f}")
    print(f"  {'beta':>8}  {'Z':>12}  {'F':>10}  {'U':>10}  {'S':>10}  {'C':>10}")
    print(f"  {'-'*8}  {'-'*12}  {'-'*10}  {'-'*10}  {'-'*10}  {'-'*10}")
    for beta in BETAS:
        Z = compute_partition(n, beta)
        F = compute_free_energy(n, beta)
        U = compute_internal_energy(n, beta)
        S = compute_entropy(n, beta)
        C = compute_specific_heat(n, beta)
        print(f"  {beta:>8.3f}  {Z:>12.6f}  {F:>10.4f}  {U:>10.4f}  {S:>10.4f}  {C:>10.4f}")

# ─── Part 2: n=6 Special Analysis ────────────────────────────────────────────

print("\n" + "=" * 80)
print("PART 2: n=6 SPECIAL ANALYSIS")
print("=" * 80)

divs_6 = get_divisors(6)   # [1, 2, 3, 6]
sigma_6 = sum(divs_6)      # 12
tau_6   = len(divs_6)      # 4
avg_6   = sigma_6 / tau_6  # 3.0

print(f"\n  n=6: divisors={divs_6}  sigma(6)={sigma_6}  tau(6)={tau_6}  <d>={avg_6:.4f}")
print(f"  Note: 6 is perfect => sigma(6)=2*6=12, sigma_-1(6)=2")

# Fine beta scan
FINE_BETAS = [b / 100 for b in range(1, 1001)]   # 0.01 .. 10.0

Fs = [compute_free_energy(6, b) for b in FINE_BETAS]
Us = [compute_internal_energy(6, b) for b in FINE_BETAS]
Ss = [compute_entropy(6, b) for b in FINE_BETAS]
Cs = [compute_specific_heat(6, b) for b in FINE_BETAS]

# ── 2a: beta* that minimises F ──
beta_star_idx = Fs.index(min(Fs))
beta_star     = FINE_BETAS[beta_star_idx]
F_min         = Fs[beta_star_idx]
print(f"\n  2a. beta* minimising F_6(beta): beta*={beta_star:.4f}  F_min={F_min:.6f}")
print(f"      (Note: F(beta)->-inf as beta->0, so effective minimum is at beta->0+)")
# More informative: beta where dF/dbeta = 0 (if any local minimum)
dF = [Fs[i+1] - Fs[i] for i in range(len(Fs)-1)]
sign_changes = [(FINE_BETAS[i], FINE_BETAS[i+1]) for i in range(len(dF)-1) if dF[i]*dF[i+1] < 0]
if sign_changes:
    print(f"      Local extrema of F near: {sign_changes}")
else:
    print(f"      F is monotonically {'decreasing' if dF[0]<0 else 'increasing'} — no local min in [0.01,10]")
    # Report at what beta F is least negative (closest to 0)
    # F values at low and high beta
    print(f"      F(0.01)={compute_free_energy(6,0.01):.4f}  F(10)={compute_free_energy(6,10):.4f}")

# ── 2b: beta where S_6 = ln(4/3) ──
print(f"\n  2b. Find beta where S_6 = W = ln(4/3) = {W:.6f}")
target_S = W
beta_S_match = None
for i in range(len(FINE_BETAS)-1):
    if (Ss[i] - target_S) * (Ss[i+1] - target_S) < 0:
        # Linear interpolation
        frac = (target_S - Ss[i]) / (Ss[i+1] - Ss[i])
        beta_S_match = FINE_BETAS[i] + frac * (FINE_BETAS[i+1] - FINE_BETAS[i])
        break
if beta_S_match:
    T_S = 1 / beta_S_match
    print(f"      S_6 = ln(4/3) at beta = {beta_S_match:.4f}  (T = 1/beta = {T_S:.4f})")
    print(f"      Relation to W: beta_S / W = {beta_S_match / W:.4f}")
    print(f"      Relation to 1/e: beta_S / (1/e) = {beta_S_match * math.e:.4f}")
else:
    # Show S range
    print(f"      S_6 range: [{min(Ss):.4f}, {max(Ss):.4f}]")
    print(f"      Target {W:.4f} {'in range' if min(Ss) <= W <= max(Ss) else 'OUT OF RANGE'}")

# Also search for all crossings
crossings_S = []
for i in range(len(FINE_BETAS)-1):
    if (Ss[i] - target_S) * (Ss[i+1] - target_S) < 0:
        frac = (target_S - Ss[i]) / (Ss[i+1] - Ss[i])
        b_cross = FINE_BETAS[i] + frac * (FINE_BETAS[i+1] - FINE_BETAS[i])
        crossings_S.append(b_cross)
print(f"      All crossings of S_6 = W: {[f'{b:.4f}' for b in crossings_S]}")

# ── 2c: beta where U_6 = sigma/tau = 3 ──
print(f"\n  2c. Find beta where U_6 = sigma(6)/tau(6) = {sigma_6}/{tau_6} = {avg_6:.4f}")
target_U = avg_6
beta_U_match = None
for i in range(len(FINE_BETAS)-1):
    if (Us[i] - target_U) * (Us[i+1] - target_U) < 0:
        frac = (target_U - Us[i]) / (Us[i+1] - Us[i])
        beta_U_match = FINE_BETAS[i] + frac * (FINE_BETAS[i+1] - FINE_BETAS[i])
        break
if beta_U_match:
    T_U = 1 / beta_U_match
    print(f"      U_6 = 3 at beta = {beta_U_match:.4f}  (T = {T_U:.4f})")
    print(f"      Relation to 1/e: beta_U * e = {beta_U_match * math.e:.4f}")
    print(f"      Relation to W:   beta_U / W = {beta_U_match / W:.4f}")
    # Check specific values
    U_val = compute_internal_energy(6, beta_U_match)
    print(f"      Verification: U_6({beta_U_match:.4f}) = {U_val:.6f} (target 3.0)")
else:
    print(f"      U_6 range over beta in [0.01,10]: [{min(Us):.4f}, {max(Us):.4f}]")
    print(f"      Target 3.0 {'in range' if min(Us) <= 3.0 <= max(Us) else 'OUT OF RANGE'}")

# ── 2d: ASCII plots of F, U, S, C for n=6 ──
def ascii_plot(xs, ys, title, ylabel, width=70, height=20, highlight_x=None):
    """Simple ASCII line plot."""
    y_min, y_max = min(ys), max(ys)
    if abs(y_max - y_min) < 1e-12:
        y_max = y_min + 1
    x_min, x_max = xs[0], xs[-1]

    grid = [[' '] * width for _ in range(height)]

    # Plot points
    for xi, yi in zip(xs, ys):
        col = int((xi - x_min) / (x_max - x_min) * (width - 1))
        row = int((y_max - yi) / (y_max - y_min) * (height - 1))
        row = max(0, min(height - 1, row))
        col = max(0, min(width - 1, col))
        grid[row][col] = '*'

    # Highlight vertical line
    if highlight_x is not None:
        col_h = int((highlight_x - x_min) / (x_max - x_min) * (width - 1))
        col_h = max(0, min(width - 1, col_h))
        for row in range(height):
            if grid[row][col_h] == ' ':
                grid[row][col_h] = '|'

    # Y=0 line
    if y_min < 0 < y_max:
        row0 = int(y_max / (y_max - y_min) * (height - 1))
        row0 = max(0, min(height - 1, row0))
        for col in range(width):
            if grid[row0][col] == ' ':
                grid[row0][col] = '-'

    print(f"\n  [{title}] {ylabel}")
    print(f"  y_max={y_max:+.4f}  y_min={y_min:+.4f}")
    print("  +" + "-" * width + "+")
    for row in range(height):
        print("  |" + "".join(grid[row]) + "|")
    print("  +" + "-" * width + "+")
    print(f"  beta: {x_min:.2f}" + " " * (width - 12) + f"{x_max:.2f}")

# Use subset for clarity
plot_xs = FINE_BETAS[::5]   # every 5th point
plot_Fs = [compute_free_energy(6, b) for b in plot_xs]
plot_Us = [compute_internal_energy(6, b) for b in plot_xs]
plot_Ss = [compute_entropy(6, b) for b in plot_xs]
plot_Cs = [compute_specific_heat(6, b) for b in plot_xs]

print("\n  --- ASCII PLOTS: n=6 thermodynamic quantities vs beta ---")
ascii_plot(plot_xs, plot_Fs, "F_6(beta)", "Free Energy F = -ln(Z)/beta", highlight_x=beta_S_match)
ascii_plot(plot_xs, plot_Us, "U_6(beta)", "Internal Energy U = <d>", highlight_x=beta_U_match)
ascii_plot(plot_xs, plot_Ss, "S_6(beta)", "Entropy S = beta(U-F)",   highlight_x=beta_S_match)
ascii_plot(plot_xs, plot_Cs, "C_6(beta)", "Specific Heat C = -beta^2 dU/dbeta")

# ─── Part 3: Z_6 vs Z_28 comparison ─────────────────────────────────────────

print("\n" + "=" * 80)
print("PART 3: Z_6(beta) vs Z_28(beta) COMPARISON")
print("=" * 80)

divs_28 = get_divisors(28)
sigma_28 = sum(divs_28)
print(f"\n  n=28: divisors={divs_28}  sigma(28)={sigma_28}  tau(28)={len(divs_28)}")
print(f"  n=6:  divisors={divs_6}   sigma(6)={sigma_6}   tau(6)={tau_6}")
print(f"  Both are perfect numbers: sigma(n) = 2n")

print(f"\n  {'beta':>8}  {'Z_6':>14}  {'Z_28':>14}  {'F_6':>10}  {'F_28':>10}  {'Z_6>Z_28?':>10}")
print(f"  {'-'*8}  {'-'*14}  {'-'*14}  {'-'*10}  {'-'*10}  {'-'*10}")

crossing_betas_Z = []
prev_diff = None
for beta in BETAS:
    Z6  = compute_partition(6, beta)
    Z28 = compute_partition(28, beta)
    F6  = compute_free_energy(6, beta)
    F28 = compute_free_energy(28, beta)
    diff = Z6 - Z28
    if prev_diff is not None and prev_diff * diff < 0:
        crossing_betas_Z.append((beta_prev, beta))
    prev_diff = diff
    beta_prev = beta
    marker = "YES" if Z6 > Z28 else "NO "
    print(f"  {beta:>8.3f}  {Z6:>14.6f}  {Z28:>14.6f}  {F6:>10.4f}  {F28:>10.4f}  {marker:>10}")

# Fine-grain crossing search
print(f"\n  Fine-grain crossing search (beta in [0.01, 10]):")
fine_betas_cross = [b / 1000 for b in range(10, 10001)]
Z6s  = [compute_partition(6,  b) for b in fine_betas_cross]
Z28s = [compute_partition(28, b) for b in fine_betas_cross]
F6s  = [compute_free_energy(6,  b) for b in fine_betas_cross]
F28s = [compute_free_energy(28, b) for b in fine_betas_cross]

crossings_Z = []
for i in range(len(fine_betas_cross)-1):
    diff_i   = Z6s[i]   - Z28s[i]
    diff_ip1 = Z6s[i+1] - Z28s[i+1]
    if diff_i * diff_ip1 < 0:
        frac = -diff_i / (diff_ip1 - diff_i)
        b_cross = fine_betas_cross[i] + frac * (fine_betas_cross[i+1] - fine_betas_cross[i])
        crossings_Z.append(b_cross)

if crossings_Z:
    for bc in crossings_Z:
        Z6c  = compute_partition(6, bc)
        Z28c = compute_partition(28, bc)
        F6c  = compute_free_energy(6, bc)
        F28c = compute_free_energy(28, bc)
        print(f"    Z_6 = Z_28 crossing at beta = {bc:.4f}  (T = {1/bc:.4f})")
        print(f"    At crossing: Z_6={Z6c:.6f}  Z_28={Z28c:.6f}")
        print(f"    At crossing: F_6={F6c:.6f}  F_28={F28c:.6f}")
else:
    print(f"    No crossing found in beta=[0.01, 10]")
    print(f"    Z_6(0.01)={compute_partition(6,0.01):.4f}  Z_28(0.01)={compute_partition(28,0.01):.4f}")
    print(f"    Z_6(10.0)={compute_partition(6,10):.4f}  Z_28(10.0)={compute_partition(28,10):.6f}")

# F comparison at "room temperature" (beta=1 as reference)
beta_room = 1.0
F6_room  = compute_free_energy(6, beta_room)
F28_room = compute_free_energy(28, beta_room)
print(f"\n  At beta=1.0 (room temperature equivalent):")
print(f"    F_6(1)  = {F6_room:.6f}")
print(f"    F_28(1) = {F28_room:.6f}")
print(f"    {'n=6 has lower F (more stable)' if F6_room < F28_room else 'n=28 has lower F (more stable)'}")
print(f"    Delta F = F_6 - F_28 = {F6_room - F28_room:.6f}")

# ASCII comparison plot
plot_betas_cmp = fine_betas_cross[::50]
plot_F6s  = [compute_free_energy(6,  b) for b in plot_betas_cmp]
plot_F28s = [compute_free_energy(28, b) for b in plot_betas_cmp]

print(f"\n  ASCII comparison: F_6 (*) vs F_28 (o)  [beta in [0.01, 10]]")
width, height = 70, 20
all_Fs = plot_F6s + plot_F28s
y_min_c = min(all_Fs)
y_max_c = max(all_Fs)
x_min_c = plot_betas_cmp[0]
x_max_c = plot_betas_cmp[-1]
grid_c = [[' '] * width for _ in range(height)]
for xi, y6, y28 in zip(plot_betas_cmp, plot_F6s, plot_F28s):
    col = int((xi - x_min_c) / (x_max_c - x_min_c) * (width - 1))
    col = max(0, min(width - 1, col))
    r6  = int((y_max_c - y6)  / (y_max_c - y_min_c) * (height - 1))
    r28 = int((y_max_c - y28) / (y_max_c - y_min_c) * (height - 1))
    r6  = max(0, min(height - 1, r6))
    r28 = max(0, min(height - 1, r28))
    grid_c[r6][col]  = '*'
    grid_c[r28][col] = 'o'
print(f"  y_max={y_max_c:+.4f}  y_min={y_min_c:+.4f}   * = F_6   o = F_28")
print("  +" + "-" * width + "+")
for row in range(height):
    print("  |" + "".join(grid_c[row]) + "|")
print("  +" + "-" * width + "+")
print(f"  beta: {x_min_c:.2f}" + " " * (width - 12) + f"{x_max_c:.2f}")

# ─── Part 4: H-EN-14 Arrhenius Check ─────────────────────────────────────────

print("\n" + "=" * 80)
print("PART 4: H-EN-14 — ARRHENIUS CONNECTION")
print("=" * 80)

print(f"\n  Activation energy E_a = W = ln(4/3) = {W:.6f}")
print(f"  Arrhenius rate: k_rate ∝ exp(-E_a / kT) = exp(-W * beta)")
print(f"  With beta = 1/kT:")
print(f"    k_rate ∝ exp(-ln(4/3) * beta) = (3/4)^beta = (4/3)^(-beta)")
print()
print(f"  Trivial verification: exp(-W) = exp(-ln(4/3)) = 1/exp(ln(4/3)) = 3/4")
print(f"    exp(-W)        = {math.exp(-W):.8f}")
print(f"    3/4            = {3/4:.8f}")
print(f"    Match: {abs(math.exp(-W) - 3/4) < 1e-12}")
print()
print(f"  R(2) = sum of reciprocals of divisors of some n? Or R = 3/4 as ratio?")
print(f"  If R(2) = 3/4 = exp(-W), this is the exact Boltzmann factor at E_a=W, beta=1")
print()
print(f"  Arrhenius rate table k(beta) = (3/4)^beta:")
print(f"  {'beta':>8}  {'k_rate (3/4)^beta':>20}  {'exp(-W*beta)':>16}  {'Match':>8}")
print(f"  {'-'*8}  {'-'*20}  {'-'*16}  {'-'*8}")
for beta in BETAS:
    k_pow  = (3/4)**beta
    k_exp  = math.exp(-W * beta)
    match  = abs(k_pow - k_exp) < 1e-10
    print(f"  {beta:>8.3f}  {k_pow:>20.10f}  {k_exp:>16.10f}  {str(match):>8}")

print(f"\n  Note: (3/4)^beta = exp(-ln(4/3)*beta) is IDENTICALLY true by definition.")
print(f"  The physical claim is that W = ln(4/3) IS the natural activation energy")
print(f"  for the 3->4 state transition (3-divisor to 4-divisor), and the rate is")
print(f"  exactly 3/4 at beta=1 (unit temperature).")

# Golden Zone connection
print(f"\n  Golden Zone connection:")
print(f"    At beta = 1/e (Golden Zone center):")
beta_ge = 1/math.e
k_ge    = math.exp(-W * beta_ge)
print(f"      k_rate = exp(-W/e) = exp(-{W:.4f}/{math.e:.4f}) = {k_ge:.8f}")
print(f"      k_rate = (3/4)^(1/e) = {(3/4)**(1/math.e):.8f}")
print(f"    At beta = 1/2 (Riemann boundary):")
beta_rh = 0.5
k_rh    = math.exp(-W * beta_rh)
print(f"      k_rate = exp(-W/2) = exp(-{W/2:.4f}) = {k_rh:.8f}")
print(f"      k_rate = (3/4)^(1/2) = sqrt(3/4) = {math.sqrt(3/4):.8f}")
print(f"      sqrt(3/4) = sqrt(3)/2 = {math.sqrt(3)/2:.8f}")

# ─── Part 5: Arithmetic Heat Capacity C_n(beta) — Schottky Anomaly ───────────

print("\n" + "=" * 80)
print("PART 5: ARITHMETIC HEAT CAPACITY C_6(beta) — SCHOTTKY ANOMALY")
print("=" * 80)

# C = d<E>/d(1/beta) = d<E>/dT  (T = 1/beta)
# C_schottky = -beta^2 * dU/dbeta

fine_betas_sch = [b / 1000 for b in range(10, 5001)]   # 0.01 to 5.0
Cs_sch = [compute_specific_heat(6, b) for b in fine_betas_sch]

C_max     = max(Cs_sch)
C_max_idx = Cs_sch.index(C_max)
beta_peak = fine_betas_sch[C_max_idx]
T_peak    = 1 / beta_peak

print(f"\n  C_6(beta) = -beta^2 * dU/dbeta  (Schottky anomaly search)")
print(f"\n  Peak of C_6:")
print(f"    beta_peak = {beta_peak:.4f}  (T_peak = 1/beta = {T_peak:.4f})")
print(f"    C_max     = {C_max:.6f}")
print(f"\n  Comparison with key constants:")
print(f"    beta_peak / W         = {beta_peak / W:.6f}  (W = ln(4/3) = {W:.4f})")
print(f"    beta_peak * e         = {beta_peak * math.e:.6f}  (1/e = {1/math.e:.4f})")
print(f"    beta_peak / (1/2)     = {beta_peak / 0.5:.6f}")
print(f"    beta_peak / (1/3)     = {beta_peak / (1/3):.6f}")
print(f"    ln(beta_peak)         = {math.log(beta_peak):.6f}")
print(f"    T_peak (=1/beta_peak) = {T_peak:.6f}")
print(f"    ln(T_peak)            = {math.log(T_peak):.6f}")

# Check if beta_peak ≈ any simple expression
candidates = {
    "1/6":         1/6,
    "1/4":         1/4,
    "ln(2)":       math.log(2),
    "1/3":         1/3,
    "W=ln(4/3)":   W,
    "1/2-W":       0.5 - W,
    "1/sqrt(6)":   1/math.sqrt(6),
    "1/2":         0.5,
    "1/e":         1/math.e,
    "ln(6)/6":     math.log(6)/6,
    "ln(3)/3":     math.log(3)/3,
}
print(f"\n  Candidate matches for beta_peak = {beta_peak:.6f}:")
print(f"  {'Expression':>20}  {'Value':>12}  {'Rel. Error':>12}")
print(f"  {'-'*20}  {'-'*12}  {'-'*12}")
for name, val in sorted(candidates.items(), key=lambda x: abs(x[1] - beta_peak)):
    err = abs(val - beta_peak) / beta_peak
    flag = " <-- MATCH" if err < 0.01 else (" <-- CLOSE" if err < 0.05 else "")
    print(f"  {name:>20}  {val:>12.6f}  {err:>12.6f}{flag}")

# Also compute for n=28 Schottky peak
Cs_28_sch = [compute_specific_heat(28, b) for b in fine_betas_sch]
C28_max     = max(Cs_28_sch)
C28_max_idx = Cs_28_sch.index(C28_max)
beta28_peak = fine_betas_sch[C28_max_idx]
T28_peak    = 1 / beta28_peak
print(f"\n  n=28 Schottky peak for comparison:")
print(f"    beta_peak(28) = {beta28_peak:.4f}  (T_peak = {T28_peak:.4f})")
print(f"    C_max(28)     = {C28_max:.6f}")
print(f"    beta_peak(6) / beta_peak(28) = {beta_peak / beta28_peak:.6f}")
print(f"    T_peak(28) / T_peak(6)       = {T28_peak / T_peak:.6f}")

# ASCII plot of C_6 with peak marker
plot_betas_sch = fine_betas_sch[::10]
plot_Cs_sch    = Cs_sch[::10]
ascii_plot(plot_betas_sch, plot_Cs_sch,
           "C_6(beta)", "Specific Heat (Schottky anomaly)",
           highlight_x=beta_peak, height=18)

# ─── Summary Table ────────────────────────────────────────────────────────────

print("\n" + "=" * 80)
print("SUMMARY: KEY BETA VALUES FOR n=6")
print("=" * 80)
print()

rows = []
rows.append(("W = ln(4/3)",         W,          "Golden Zone Width"))
rows.append(("1/e",                  INV_E,      "Golden Zone Center"))
rows.append(("1/2 = Riemann",        0.5,        "Riemann critical line re(s)=1/2"))
rows.append(("beta where S=W",       beta_S_match if beta_S_match else float('nan'),
             f"S_6 = ln(4/3)"))
rows.append(("beta where U=3",       beta_U_match if beta_U_match else float('nan'),
             f"U_6 = sigma/tau = 3"))
rows.append(("beta_peak(C_6)",       beta_peak,  "Schottky anomaly peak of C_6"))
rows.append(("beta_peak(C_28)",      beta28_peak, "Schottky anomaly peak of C_28"))
if crossings_Z:
    rows.append(("Z_6=Z_28 crossing",  crossings_Z[0], "Z_6 crosses Z_28"))

print(f"  {'Key Beta':>25}  {'Value':>10}  {'T=1/beta':>10}  Description")
print(f"  {'-'*25}  {'-'*10}  {'-'*10}  {'-'*35}")
for name, val, desc in rows:
    T_val = 1/val if val and not math.isnan(val) and val != 0 else float('nan')
    print(f"  {name:>25}  {val:>10.6f}  {T_val:>10.6f}  {desc}")

print()
print("  Ratios between key betas:")
if beta_S_match and beta_U_match:
    print(f"    beta_S / beta_U = {beta_S_match/beta_U_match:.6f}")
    print(f"    beta_S / W      = {beta_S_match/W:.6f}")
    print(f"    beta_U / W      = {beta_U_match/W:.6f}")
print(f"    beta_peak / W   = {beta_peak/W:.6f}")
print(f"    beta_peak / (1/e) = {beta_peak*math.e:.6f}")

print()
print("=" * 80)
print("ANALYSIS COMPLETE")
print("=" * 80)
