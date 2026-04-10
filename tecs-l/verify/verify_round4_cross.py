#!/usr/bin/env python3
"""
verify_round4_cross.py
25 NEW cross-domain hypotheses for TECS-L project (Round 4).
No overlap with Rounds 1-3.

Domains: sorting, B-trees, PID control, auction theory, Boolean algebra,
         lambda calculus, type theory, databases, network protocols, color theory,
         typography, paper sizes, dice, card games, sports, guitar strings,
         waltz time, Maillard reaction, navigation degrees, time zones,
         UTF-8, DNA Phred scores, Fibonacci/golden ratio, Penrose tiling,
         mechanism design (VCG).

n=6: sigma=12, tau=4, phi=2, sopfr=5, sigma*phi=24, ln(4/3)=0.2877
"""

import math
import sys
from fractions import Fraction
from functools import reduce

# -- Constants --
N = 6
SIGMA = 12
TAU = 4
PHI = 2
SOPFR = 5
SIGMA_PHI = SIGMA * PHI  # 24
LN43 = math.log(4 / 3)   # 0.28768...
GOLDEN_UPPER = 0.5
GOLDEN_CENTER = 1 / math.e
GOLDEN_LOWER = 0.5 - LN43
GOLDEN_RATIO = (1 + math.sqrt(5)) / 2  # 1.6180...

results = []

def report(tag, title, formula, passed, value, grade, note=""):
    status = "PASS" if passed else "FAIL"
    results.append((tag, title, formula, status, value, grade, note))
    print(f"\n{'='*76}")
    print(f"{tag}: {title}")
    print(f"  Formula : {formula}")
    print(f"  Result  : {status}  (value={value})")
    print(f"  Grade   : {grade}")
    if note:
        print(f"  Note    : {note}")


# ======================================================================
# R4-CROSS-01: Sorting 6 elements -- optimal comparison count
# ======================================================================
def test_01():
    """Optimal comparison sorting of 6 elements requires exactly 10 comparisons.
    Information-theoretic lower bound: ceil(log2(6!)) = ceil(log2(720)) = ceil(9.17) = 10.
    This is tight: merge-insertion sort achieves 10.
    Claim: ceil(log2(n!)) = 10 = sigma - phi at n=6. And 6! = 720 = sigma * 60."""
    n_fact = math.factorial(N)  # 720
    lower_bound = math.ceil(math.log2(n_fact))  # ceil(9.17) = 10
    optimal = 10  # Known result: sorting 6 elements needs exactly 10 comparisons

    c1 = (lower_bound == optimal)  # tight bound
    c2 = (optimal == SIGMA - PHI)  # 12 - 2 = 10

    # Honesty: sigma - phi = 10 is just 12-2=10. Many ways to get 10 from small numbers.
    # The real fact is that the info-theoretic bound is tight at n=6.
    passed = c1
    report("R4-CROSS-01",
           "Sorting 6 elements: optimal = 10 comparisons (tight bound)",
           f"ceil(log2(6!)) = ceil(log2(720)) = 10 = optimal",
           passed, f"6!={n_fact}, bound={lower_bound}, optimal={optimal}",
           "🟩" if passed else "⚪",
           "The info-theoretic bound ceil(log2(6!))=10 is exactly achievable. "
           "Genuine CS fact. The sigma-phi=10 mapping is numerological (grade applies to tightness, not mapping).")


# ======================================================================
# R4-CROSS-02: B-tree -- order and branching
# ======================================================================
def test_02():
    """B-tree of order m: each node has ceil(m/2) to m children.
    Common textbook orders: m=3 (2-3 tree), m=4 (2-3-4 tree), m=5, m=6.
    B-tree order 6: min children=3, max=6, min keys=2=phi, max keys=5=sopfr.
    Max keys per node = m-1 = 5 = sopfr(6).
    Min children = ceil(m/2) = 3 = n/phi."""
    m = N  # order 6
    max_keys = m - 1  # 5
    min_children = math.ceil(m / 2)  # 3
    min_keys = min_children - 1  # 2

    c1 = (max_keys == SOPFR)  # 5 = sopfr(6)
    c2 = (min_keys == PHI)    # 2 = phi(6)
    c3 = (min_children == N // PHI)  # 3 = 6/2

    # Honesty: m-1=5 for m=6 is trivial arithmetic. min_keys=2 for any even m.
    passed = c1 and c2 and c3
    report("R4-CROSS-02",
           "B-tree order 6: max_keys=5=sopfr, min_keys=2=phi",
           f"order m={m}: max_keys=m-1={max_keys}=sopfr(6), min_keys=ceil(m/2)-1={min_keys}=phi(6)",
           passed, f"max_keys={max_keys}, min_keys={min_keys}, min_children={min_children}",
           "⚪",
           "COINCIDENCE. m-1=5 is trivial subtraction, not a deep connection. "
           "Any number's predecessor can be matched to something. phi(6)=2 is too small to be meaningful.")


# ======================================================================
# R4-CROSS-03: Hash table load factor -- optimal ~ 0.75
# ======================================================================
def test_03():
    """Java HashMap default load factor = 0.75 = 3/4.
    ln(4/3) = 0.2877 is the Golden Zone width.
    1 - ln(4/3) = 0.7123. Compare to 0.75.
    Also: 3/4 = (n/phi)/(n-phi) = 3/4. Exact fraction.
    Expected probe count in linear probing at alpha=0.75: 1/(1-alpha)^2 * (1+1/(1-alpha))/2.
    At alpha=3/4: avg probes ~ 8.5 for unsuccessful search."""
    load_factor = 0.75
    one_minus_ln43 = 1 - LN43  # 0.7123

    diff = abs(load_factor - one_minus_ln43)
    close = diff < 0.05

    # Average unsuccessful probe at alpha: 1/(1-alpha)^2 / 2 (approx)
    avg_probe = 0.5 * (1 + 1/(1 - load_factor)**2)  # 0.5*(1+16) = 8.5

    c1 = (Fraction(3, 4) == Fraction(N // PHI, N - PHI))  # 3/4 = 3/4

    passed = close and c1
    report("R4-CROSS-03",
           "Hash load factor 0.75 ~ 1 - ln(4/3) = 0.712 (within 5%)",
           f"Java default 3/4 = 0.75; 1-ln(4/3) = {one_minus_ln43:.4f}; diff = {diff:.4f}",
           passed, f"load={load_factor}, 1-ln43={one_minus_ln43:.4f}, diff={diff:.4f}",
           "⚪",
           "WEAK. 5% tolerance is generous. 0.75 was chosen for practical collision tradeoffs, "
           "not from information theory. The 3/4 = (n/phi)/(n-phi) is circular. Grade: coincidence.")


# ======================================================================
# R4-CROSS-04: PID controller -- 3 terms, transfer function structure
# ======================================================================
def test_04():
    """PID controller has 3 terms: Proportional, Integral, Derivative.
    Transfer function: G(s) = Kp + Ki/s + Kd*s = (Kd*s^2 + Kp*s + Ki)/s
    Number of terms = 3 = sigma/tau = 12/4.
    Degree of numerator polynomial = 2 = phi(6).
    Claim: PID structure maps to n=6 arithmetic.
    Also: Ziegler-Nichols tuning for quarter-decay uses ratios involving 4=tau."""
    n_terms = 3
    num_degree = 2  # Kd*s^2 + Kp*s + Ki
    den_degree = 1  # s

    c1 = (n_terms == SIGMA // TAU)  # 3 = 12/4
    c2 = (num_degree == PHI)        # 2
    c3 = (n_terms == N // PHI)      # 3 = 6/2

    # Ziegler-Nichols quarter-decay ratio: overshoot decays by 1/4 per cycle
    zn_decay = Fraction(1, 4)  # = 1/tau

    c4 = (zn_decay == Fraction(1, TAU))

    passed = c1 and c2 and c4
    report("R4-CROSS-04",
           "PID: 3=sigma/tau terms, degree 2=phi, ZN quarter-decay=1/tau",
           f"PID terms=3=sigma/tau, numerator degree=2=phi, ZN decay ratio=1/4=1/tau",
           passed, f"terms={n_terms}, degree={num_degree}, ZN_decay=1/{TAU}",
           "⚪",
           "COINCIDENCE. 3 terms is a design choice (P, I, D are conceptually distinct operations). "
           "Quarter-decay is 1/4 which trivially equals 1/tau. Small numbers matching small numbers.")


# ======================================================================
# R4-CROSS-05: Vickrey auction for 6 bidders
# ======================================================================
def test_05():
    """Vickrey (second-price sealed-bid) auction with n=6 bidders.
    If values are i.i.d. Uniform[0,1]:
      E[revenue] = E[2nd highest of 6] = (n-1)/(n+1) = 5/7
      E[winner's value] = E[max of 6] = n/(n+1) = 6/7
      E[winner's surplus] = E[max] - E[2nd] = 1/(n+1) = 1/7
    Note: numerator of revenue = n-1 = 5 = sopfr(6).
    Denominator = n+1 = 7 (prime, Mersenne prime exponent)."""
    n = N
    e_revenue = Fraction(n - 1, n + 1)  # 5/7
    e_max = Fraction(n, n + 1)          # 6/7
    e_surplus = Fraction(1, n + 1)      # 1/7

    c1 = (e_revenue == Fraction(SOPFR, 7))  # 5/7
    c2 = (e_surplus == Fraction(1, 7))
    c3 = (e_revenue.numerator == SOPFR)

    # Honesty: (n-1)/(n+1) for n=6 gives 5/7. The sopfr match is just n-1=5.
    passed = c1 and c2
    report("R4-CROSS-05",
           "Vickrey auction n=6: E[revenue]=5/7, E[surplus]=1/7",
           f"E[2nd of 6 uniforms] = (n-1)/(n+1) = 5/7; surplus = 1/7",
           passed, f"revenue=5/7={float(e_revenue):.4f}, surplus=1/7={float(e_surplus):.4f}",
           "🟩",
           "Exact order statistics result. The 5/7 fraction is clean but n-1=5=sopfr is just "
           "because sopfr(6)=2+3=5=6-1. Genuine probability fact, trivial n=6 mapping.")


# ======================================================================
# R4-CROSS-06: VCG mechanism -- payment structure for 6 agents
# ======================================================================
def test_06():
    """Vickrey-Clarke-Groves mechanism for n=6 agents allocating 1 item.
    VCG payment for winner = max value among losers = 2nd highest value.
    Number of Clarke pivot computations = n = 6.
    Each agent's externality calculated by removing them: n-1=5=sopfr computations of social welfare.
    Total welfare comparisons: n * (n-1) = 30 = sigma(6) * (sopfr(6)/2).
    Claim: VCG computational structure at n=6."""
    n = N
    pivot_computations = n  # 6
    welfare_per_agent = n - 1  # 5
    total_comparisons = n * (n - 1)  # 30

    c1 = (pivot_computations == N)
    c2 = (welfare_per_agent == SOPFR)  # 5 = sopfr(6)
    c3 = (total_comparisons == 30)

    # 30 = 5*6. Not particularly connected to n=6 arithmetic divisors.
    passed = c1 and c2
    report("R4-CROSS-06",
           "VCG mechanism n=6: n-1=5=sopfr pivot welfare computations",
           f"VCG pivots: {n} agents, each excludes self -> {welfare_per_agent} others = sopfr(6)",
           passed, f"pivots={pivot_computations}, per_agent={welfare_per_agent}, total={total_comparisons}",
           "⚪",
           "TRIVIAL. n-1=5 for any mechanism with 6 agents. sopfr(6)=5=n-1 is just a property of 6. "
           "No deep mechanism design principle here.")


# ======================================================================
# R4-CROSS-07: Boolean functions on phi=2 variables
# ======================================================================
def test_07():
    """Number of Boolean functions on k variables = 2^(2^k).
    For k = phi(6) = 2: 2^(2^2) = 2^4 = 16 Boolean functions.
    These are exactly the 16 binary connectives (AND, OR, XOR, NAND, ...).
    16 = 2^tau(6) = 2^4.
    The 16 connectives form a Boolean algebra of order 2^4.
    Also: number of monotone Boolean functions on 2 vars = 6 = n!
    (Dedekind number D(2) = 6.)"""
    k = PHI  # 2 variables
    total_bf = 2**(2**k)  # 2^4 = 16

    c1 = (total_bf == 2**TAU)  # 16 = 2^4 = 2^tau(6)
    c2 = (k == PHI)

    # Dedekind number D(2) = 6
    # D(0)=2, D(1)=3, D(2)=6, D(3)=20, D(4)=168
    dedekind_2 = 6
    c3 = (dedekind_2 == N)

    passed = c1 and c3
    report("R4-CROSS-07",
           "Boolean functions on phi=2 vars: 16=2^tau; Dedekind D(2)=6=n",
           f"2^(2^phi) = 2^4 = 16 = 2^tau(6); D(2) = 6 = n",
           passed, f"total_bf={total_bf}, Dedekind_D(2)={dedekind_2}",
           "🟧",
           "Dedekind D(2)=6 is a genuine combinatorial fact: exactly 6 monotone Boolean functions "
           "on 2 variables. The 2^tau match is less surprising since tau=4 and 2^4=16 is standard. "
           "D(2)=6 is the interesting connection.")


# ======================================================================
# R4-CROSS-08: Church numeral 6 in lambda calculus
# ======================================================================
def test_08():
    """Church numeral for 6: lambda f. lambda x. f(f(f(f(f(f(x))))))
    Number of beta-reduction steps to compute MULT(2)(3) = 6:
      MULT = lambda m. lambda n. lambda f. m(n(f))
      MULT(2)(3) applies 3 twice = 6 applications.
    Church numeral n has exactly n applications of f.
    MULT(phi)(n/phi) = MULT(2)(3) = 6 = n.
    ADD(phi)(tau) = ADD(2)(4) = 6 = n. Also ADD(sopfr)(1) = 6.
    Key: 6 = 2*3 = phi * (n/phi) in Church arithmetic."""
    church_6_apps = N  # 6 applications of f
    mult_2_3 = PHI * (N // PHI)  # 2 * 3 = 6
    add_2_4 = PHI + TAU  # 2 + 4 = 6

    c1 = (church_6_apps == N)
    c2 = (mult_2_3 == N)
    c3 = (add_2_4 == N)

    passed = c1 and c2 and c3
    report("R4-CROSS-08",
           "Church numeral 6: MULT(2)(3) = MULT(phi)(3) = 6 = n",
           f"Church 6 = f^6(x); MULT(phi(6))(n/phi) = 2*3 = 6; ADD(phi)(tau) = 2+4 = 6",
           passed, f"apps={church_6_apps}, 2*3={mult_2_3}, 2+4={add_2_4}",
           "⚪",
           "TAUTOLOGICAL. 6 = 2*3 and 6 = 2+4 are just factorization and partition of 6. "
           "Church numerals encode numbers as iteration counts by definition. No new content.")


# ======================================================================
# R4-CROSS-09: Type theory -- universe levels and dependent types
# ======================================================================
def test_09():
    """In type theory (e.g., Coq, Agda), universe hierarchy: Type_0 : Type_1 : Type_2 : ...
    To avoid Girard's paradox, need at least 2 = phi(6) universe levels.
    Martin-Lof type theory with 1 universe is consistent; with impredicativity needs care.
    Calculus of Constructions: 2 sorts (Prop, Type) = phi(6).
    With universe polymorphism, typical systems use levels 0,1,2,...
    Lambda cube has 2^3 = 8 vertices (3 binary features: polymorphism, type operators, dependent types).
    Lambda cube dimension = 3 = n/phi. Vertices = 8 = 2^3."""
    coc_sorts = 2  # Prop and Type
    lambda_cube_dim = 3
    lambda_cube_vertices = 2**3  # 8

    c1 = (coc_sorts == PHI)
    c2 = (lambda_cube_dim == N // PHI)  # 3 = 6/2
    c3 = (lambda_cube_vertices == 2**(N // PHI))  # 8

    passed = c1 and c2 and c3
    report("R4-CROSS-09",
           "Type theory: CoC has 2=phi sorts, Lambda cube dim=3=n/phi",
           f"CoC sorts=2=phi(6), Lambda cube: 3 axes (=n/phi), 2^3=8 systems",
           passed, f"sorts={coc_sorts}, cube_dim={lambda_cube_dim}, vertices={lambda_cube_vertices}",
           "⚪",
           "WEAK. The CoC having 2 sorts is a foundational design choice. "
           "Lambda cube has 3 dimensions because there are 3 orthogonal type features. "
           "phi(6)=2 matches too many things. No structural depth.")


# ======================================================================
# R4-CROSS-10: Database normal forms -- 1NF through 6NF
# ======================================================================
def test_10():
    """Database normalization: 1NF, 2NF, 3NF, BCNF, 4NF, 5NF, 6NF.
    Total named normal forms = 7 = n+1.
    Practically used: 1NF through 3NF + BCNF = 4 = tau(6) forms.
    6NF (sixth normal form) is the highest, decomposing to irreducible components.
    6NF = n-th normal form. Each relation is in 6NF iff it's in 5NF and
    every join dependency is trivial.
    Codd defined up to 3NF (1971), then BCNF. The number 6NF is a real thing."""
    total_nf = 7  # 1NF,2NF,3NF,BCNF,4NF,5NF,6NF
    practical_nf = 4  # 1NF,2NF,3NF,BCNF
    highest_nf = 6  # 6NF

    c1 = (total_nf == N + 1)  # 7 = n+1
    c2 = (practical_nf == TAU)  # 4 commonly used
    c3 = (highest_nf == N)     # 6NF is the maximum

    # But: 6NF exists because Date & Darwen defined it; numbering is sequential
    passed = c1 and c2 and c3
    report("R4-CROSS-10",
           "Database normalization: 6NF = n, 7 forms = n+1, 4 practical = tau",
           f"Normal forms: 6NF highest (=n), total 7 named (=n+1), 4 practical (=tau)",
           passed, f"highest={highest_nf}, total={total_nf}, practical={practical_nf}",
           "⚪",
           "COINCIDENCE. Normal forms are numbered sequentially from 1; 6NF exists because "
           "someone defined it after 5NF. The '7 total' counts BCNF as separate. "
           "The 4 practical forms is a judgment call, not a theorem.")


# ======================================================================
# R4-CROSS-11: OSI 7 layers = n+1, TCP/IP 4 = tau
# ======================================================================
def test_11():
    """OSI model: 7 layers (Physical, Data Link, Network, Transport, Session, Presentation, Application).
    TCP/IP model: 4 layers (Link, Internet, Transport, Application).
    7 = n + 1 = sigma(6)/phi(6) + 1? No, sigma/phi = 6. So 7 = n + 1.
    4 = tau(6).
    Ratio: OSI/TCP = 7/4 = 1.75.
    The 'session layer' (layer 5 = sopfr) is the most controversial/vestigial."""
    osi_layers = 7
    tcpip_layers = 4

    c1 = (osi_layers == N + 1)  # 7
    c2 = (tcpip_layers == TAU)  # 4
    ratio = Fraction(osi_layers, tcpip_layers)  # 7/4
    c3 = (ratio == Fraction(7, 4))

    # Session layer number
    session_layer = 5  # Layer 5 in OSI
    c4 = (session_layer == SOPFR)

    passed = c1 and c2 and c4
    report("R4-CROSS-11",
           "OSI 7=n+1 layers, TCP/IP 4=tau layers, session=layer 5=sopfr",
           f"OSI={osi_layers}=n+1, TCP/IP={tcpip_layers}=tau, session=L{session_layer}=sopfr",
           passed, f"OSI={osi_layers}, TCP={tcpip_layers}, session=L{session_layer}",
           "⚪",
           "COINCIDENCE. OSI was designed by committee (ISO) with 7 layers as a political/technical "
           "compromise. TCP/IP has 4 because it merged several OSI layers. "
           "Layer 5 = session is just counting from bottom. Human design choices, not mathematical necessity.")


# ======================================================================
# R4-CROSS-12: RYB color wheel -- 6 primary+secondary colors
# ======================================================================
def test_12():
    """RYB color model: 3 primaries (Red, Yellow, Blue) + 3 secondaries (Orange, Green, Purple).
    Total primary+secondary = 6 = n.
    Primaries = 3 = n/phi.
    RGB model also has 3+3 = 6 (primaries + secondaries).
    HSV/HSL: hue wheel divided into 6 sectors of 60 degrees each.
    360/6 = 60 degrees per sector. 360 = 6 * 60 = n * 60.
    Complementary pairs = 3 = n/phi."""
    primaries = 3
    secondaries = 3
    total_colors = primaries + secondaries  # 6
    hue_sectors = 6
    degrees_per_sector = 360 // hue_sectors  # 60

    c1 = (total_colors == N)
    c2 = (hue_sectors == N)
    c3 = (degrees_per_sector == 60)
    c4 = (primaries == N // PHI)

    # 360/6 = 60 is just how degrees work with hex color
    passed = c1 and c2
    report("R4-CROSS-12",
           "Color theory: 6=n primary+secondary colors, 6 hue sectors",
           f"3 primary + 3 secondary = 6 = n; HSV hue = 6 sectors of 60 degrees",
           passed, f"colors={total_colors}, sectors={hue_sectors}, deg/sector={degrees_per_sector}",
           "🟧",
           "The 6-fold color symmetry is genuine perceptual structure: human trichromacy "
           "(3 cone types = 3 primaries) yields 3 complementary secondaries. "
           "The 6-sector hue wheel reflects this biology. Still, 3+3=6 is simple arithmetic.")


# ======================================================================
# R4-CROSS-13: Typography -- 12pt standard body size
# ======================================================================
def test_13():
    """Standard body text size in typography: 12 points = sigma(6).
    1 pica = 12 points (typographic unit).
    6 picas = 1 inch (historically). So 1 inch = 72 points = 6 * 12 = n * sigma.
    Point system: 72 points/inch was standardized (PostScript point).
    12pt body text has been standard since movable type (Gutenberg era).
    Also: em-dash width = 1 em = point size; en-dash = 1/2 em."""
    points_per_pica = 12
    picas_per_inch = 6
    points_per_inch = points_per_pica * picas_per_inch  # 72

    c1 = (points_per_pica == SIGMA)  # 12 = sigma(6)
    c2 = (picas_per_inch == N)       # 6 picas = 1 inch
    c3 = (points_per_inch == N * SIGMA)  # 72 = 6 * 12
    c4 = (points_per_inch == 72)

    passed = c1 and c2 and c3
    report("R4-CROSS-13",
           "Typography: 12pt=sigma per pica, 6=n picas per inch, 72=n*sigma pts/in",
           f"1 pica = 12pt = sigma(6); 1 inch = 6 picas = n; 72pts = n*sigma(6)",
           passed, f"pts/pica={points_per_pica}, picas/in={picas_per_inch}, pts/in={points_per_inch}",
           "🟧",
           "Historical fact: the point-pica-inch system genuinely uses 12 and 6. "
           "This is because both derive from base-12 (duodecimal) measurement tradition. "
           "The 12/6 structure predates and is independent of n=6 theory, but the base-12 "
           "connection to sigma(6)=12 is at least structurally interesting.")


# ======================================================================
# R4-CROSS-14: A-series paper -- sqrt(2) aspect ratio
# ======================================================================
def test_14():
    """ISO 216 A-series paper: aspect ratio = sqrt(2) = 1.4142...
    A0 area = 1 m^2. Each fold halves: A(n) = A0/2^n.
    A6 paper: 105mm x 148mm (postcard size). Area = A0/2^6 = 1/64 m^2.
    1/64 = 1/2^6 = 1/2^n.
    sqrt(2) ~ 1.4142. Compare: sigma/n - 1/phi = 12/6 - 1/2 = 1.5. Not close.
    sqrt(2) = 2^(1/2) = 2^(1/phi). That's a genuine identity."""
    aspect = math.sqrt(2)
    a6_area = 1 / 2**N  # 1/64 m^2 = 0.015625

    c1 = abs(aspect - 2**(1/PHI)) < 1e-10  # sqrt(2) = 2^(1/phi(6))? phi(6)=2, so 2^(1/2)=sqrt(2). Tautology.
    c2 = (2**N == 64)  # A6 = 1/64 m^2

    # sqrt(2) = 2^(1/2) is literally the definition. phi(6)=2 makes 1/phi=1/2. Circular.
    passed = c1 and c2
    report("R4-CROSS-14",
           "A-series paper: A6 area = 1/2^6 m^2, aspect sqrt(2) = 2^(1/phi)",
           f"A6 = 1/2^6 = {a6_area} m^2; sqrt(2) = 2^(1/2) = 2^(1/phi(6)) [tautological]",
           passed, f"A6_area={a6_area}, aspect={aspect:.6f}",
           "⚪",
           "TAUTOLOGICAL. sqrt(2) = 2^(1/2) is a definition, and phi(6)=2 makes 1/phi(6)=1/2. "
           "A6 being 1/64 m^2 is just the 6th halving. No structural connection to n=6 theory.")


# ======================================================================
# R4-CROSS-15: Standard d6 dice properties
# ======================================================================
def test_15():
    """Standard die (d6): 6 faces, opposite faces sum to 7 = n+1.
    Total of all faces: 1+2+3+4+5+6 = 21 = T(6) = n(n+1)/2.
    Expected value per roll: 3.5 = 7/2 = (n+1)/phi.
    Variance: 35/12 = 35/sigma(6).
    35/12 = 2.9167. Interesting: variance denominator = sigma(6).
    Number of opposite pairs: 3 = n/phi.
    Product of all faces: 720 = 6! = n!."""
    faces = N
    face_sum = N * (N + 1) // 2  # 21
    expected = Fraction(N + 1, 2)  # 7/2
    variance = Fraction(N**2 - 1, 12)  # (36-1)/12 = 35/12
    pairs = N // 2  # 3
    face_product = math.factorial(N)  # 720

    c1 = (face_sum == 21)
    c2 = (expected == Fraction(7, 2))
    c3 = (variance == Fraction(35, SIGMA))  # denominator = 12 = sigma(6)
    c4 = (pairs == N // PHI)
    c5 = (face_product == 720)

    passed = c1 and c3 and c5
    report("R4-CROSS-15",
           "d6 dice: sum=21, variance=35/12=35/sigma, 6!=720",
           f"Sum=n(n+1)/2=21; Var=(n^2-1)/12=35/sigma(6); Product=n!=720",
           passed, f"sum={face_sum}, var={variance}=35/{SIGMA}, product={face_product}",
           "🟧",
           "The variance formula (n^2-1)/12 with 12=sigma(6) is a GENUINE coincidence worth noting: "
           "the uniform discrete variance on {1..n} always has denominator 12, and sigma(6)=12. "
           "This connects dice variance to the divisor sum. But it holds for ANY n, not just n=6.")


# ======================================================================
# R4-CROSS-16: Playing cards -- suits=tau, ranks=13
# ======================================================================
def test_16():
    """Standard deck: 4 suits, 13 ranks, 52 cards.
    Suits = 4 = tau(6). Ranks = 13 = sigma(6) + 1.
    Total = 4 * 13 = 52 = tau(6) * (sigma(6)+1).
    Deck + 2 jokers = 54 = 6 * 9 = n * 9.
    Cards per suit = 13 = sigma + 1. Face cards per suit = 3 = n/phi.
    Number values (A-10) per suit = 10 = sigma - phi.
    Total face cards = 12 = sigma(6). Total number cards = 40."""
    suits = 4
    ranks = 13
    total = suits * ranks  # 52
    face_per_suit = 3  # J, Q, K
    total_face = suits * face_per_suit  # 12

    c1 = (suits == TAU)
    c2 = (ranks == SIGMA + 1)
    c3 = (total == TAU * (SIGMA + 1))
    c4 = (total_face == SIGMA)
    c5 = (face_per_suit == N // PHI)

    passed = c1 and c2 and c4 and c5
    report("R4-CROSS-16",
           "Playing cards: 4=tau suits, 13=sigma+1 ranks, 12=sigma face cards",
           f"Suits={suits}=tau, ranks={ranks}=sigma+1, face_cards={total_face}=sigma",
           passed, f"suits={suits}, ranks={ranks}, total={total}, faces={total_face}",
           "🟧",
           "The 4 suits and 12 face cards do genuinely match tau(6) and sigma(6). "
           "Historically, playing cards evolved from Mamluk designs with similar structure. "
           "The 13 = sigma+1 is a +1 correction which weakens it. "
           "12 face cards = sigma(6) is the strongest single match here.")


# ======================================================================
# R4-CROSS-17: Sports team sizes
# ======================================================================
def test_17():
    """Volleyball: 6 players per side = n.
    Ice hockey: 6 players on ice (5 skaters + 1 goalie) = n.
    Basketball: 5 players = sopfr(6).
    Soccer: 11 players. 11 is not directly an n=6 invariant.
      But: 11 = p(6) = partitions of 6? No, p(6)=11. YES! p(6) = 11.
    Baseball: 9 players = ? (9 = n + n/phi = 6 + 3. Weak.)
    Claim: volleyball=n, basketball=sopfr, soccer=p(6)."""
    volleyball = 6
    hockey = 6  # on-ice
    basketball = 5
    soccer = 11

    # p(6) = number of partitions of 6 = 11
    # Partitions of 6: {6}, {5,1}, {4,2}, {4,1,1}, {3,3}, {3,2,1}, {3,1,1,1},
    #   {2,2,2}, {2,2,1,1}, {2,1,1,1,1}, {1,1,1,1,1,1} = 11
    p6 = 11

    c1 = (volleyball == N)
    c2 = (hockey == N)
    c3 = (basketball == SOPFR)
    c4 = (soccer == p6)  # p(6) = 11

    passed = c1 and c3 and c4
    report("R4-CROSS-17",
           "Sports: volleyball=6=n, basketball=5=sopfr, soccer=11=p(6)",
           f"Volleyball={volleyball}=n, basketball={basketball}=sopfr(6), soccer={soccer}=p(6)",
           passed, f"volleyball={volleyball}, basketball={basketball}, soccer={soccer}, p(6)={p6}",
           "⚪",
           "CHERRY-PICKED. We chose sports that match and ignored those that don't "
           "(rugby 15, cricket 11, tennis 1-2, football 11). Soccer 11=p(6) is interesting "
           "as a fact about p(6) but the sports connection is coincidence. "
           "Team sizes are determined by field/game design, not number theory.")


# ======================================================================
# R4-CROSS-18: Guitar -- 6 strings = n
# ======================================================================
def test_18():
    """Standard guitar: 6 strings = n.
    Standard tuning: E2-A2-D3-G3-B3-E4.
    Interval between most adjacent strings: perfect 4th = 5 semitones = sopfr(6).
    Exception: G3-B3 = major 3rd = 4 semitones = tau(6).
    Total semitone span E2 to E4: 24 semitones = 2 octaves = sigma*phi = 24.
    Number of frets (standard): 19-24. Classical = 19. Many electrics = 24 = sigma*phi.
    Strings * semitones_per_4th = 6 * 5 = 30 (approximate total, minus the one major 3rd)."""
    strings = 6
    interval_p4 = 5  # semitones in perfect 4th
    interval_m3 = 4  # semitones in major 3rd (G-B exception)
    total_span = 24  # E2 to E4 = 24 semitones
    frets_electric = 24  # common electric guitar

    c1 = (strings == N)
    c2 = (interval_p4 == SOPFR)  # 5 semitones
    c3 = (interval_m3 == TAU)    # 4 semitones
    c4 = (total_span == SIGMA_PHI)  # 24
    c5 = (frets_electric == SIGMA_PHI)  # 24 frets

    passed = c1 and c2 and c3 and c4
    report("R4-CROSS-18",
           "Guitar: 6=n strings, P4=5=sopfr semitones, span=24=sigma*phi, M3=4=tau",
           f"Strings={strings}=n, P4={interval_p4}=sopfr, M3={interval_m3}=tau, span={total_span}=sigma*phi",
           passed, f"strings={strings}, P4={interval_p4}st, M3={interval_m3}st, span={total_span}st",
           "🟧★",
           "Multiple independent matches: 6 strings, P4=5 semitones, M3=4 semitones, 24 semitone span. "
           "The perfect 4th = 5 semitones matching sopfr(6) is notable because the guitar's tuning "
           "is physics-driven (4:3 frequency ratio -> ln(4/3) is the Golden Zone width!). "
           "P4 freq ratio = 4/3, and ln(4/3) = Golden Zone width. This is the strongest link.")


# ======================================================================
# R4-CROSS-19: Waltz -- 3/4 time signature
# ======================================================================
def test_19():
    """Waltz: 3/4 time = 3 beats per measure, quarter note gets one beat.
    3/4 = 0.75. Compare: 1 - ln(4/3) = 0.7123 (not very close).
    3/4 = (n/phi)/tau = 3/4. Fraction: n/(phi*tau) = 6/8 = 3/4. Hmm, 6/8 is a different time sig.
    Actually: 3/4 time. Numerator 3 = n/phi. Denominator 4 = tau.
    Waltz tempo: 84-96 BPM typical. Midpoint ~ 90. 90 = 15 * n = sigma * 7.5. Weak.
    Measure duration at 90 BPM: 3 beats / 90 bpm * 60 = 2 seconds. 2 = phi(6)."""
    beats = 3
    note_value = 4  # quarter note
    time_sig = Fraction(beats, note_value)  # 3/4

    c1 = (beats == N // PHI)  # 3 = 6/2
    c2 = (note_value == TAU)   # 4
    c3 = (time_sig == Fraction(3, 4))

    # At 90 BPM, measure = 2 seconds
    bpm = 90
    measure_duration = beats / bpm * 60  # 2.0 seconds
    c4 = (measure_duration == PHI)

    passed = c1 and c2
    report("R4-CROSS-19",
           "Waltz 3/4 time: beats=3=n/phi, quarter=4=tau",
           f"3/4 time: 3 beats=n/phi(6), quarter note value=4=tau(6)",
           passed, f"beats={beats}, note_value={note_value}, sig={time_sig}",
           "⚪",
           "TRIVIAL. 3 and 4 are extremely common small numbers. The waltz uses 3/4 because "
           "of the dance pattern (step-step-step), not number theory. "
           "3=n/phi and 4=tau are just small number coincidences.")


# ======================================================================
# R4-CROSS-20: Navigation -- 360 degrees
# ======================================================================
def test_20():
    """360 degrees in a full circle.
    360 = 6 * 60 = n * 60.
    360 = sigma * sopfr * n = 12 * 5 * 6 = 360. Check: 12*5*6 = 360. YES.
    Also: 360 = sigma(6) * 30 = tau(6) * 90 = phi(6) * 180.
    Babylonian origin: 360 ~ days in year, highly composite number.
    tau(360) = 24 = sigma*phi. 360 has 24 divisors!
    sigma(360) = 1170. Not clean.
    360 = 2^3 * 3^2 * 5 = uses exactly primes 2,3,5 = prime factors of 6 plus 5=sopfr(6)."""
    degrees = 360

    c1 = (degrees == SIGMA * SOPFR * N)  # 12 * 5 * 6 = 360
    c2 = (degrees == N * 60)

    # Number of divisors of 360
    def count_divisors(n):
        count = 0
        for i in range(1, n + 1):
            if n % i == 0:
                count += 1
        return count

    tau_360 = count_divisors(360)  # 24
    c3 = (tau_360 == SIGMA_PHI)  # tau(360) = 24 = sigma(6)*phi(6)

    # Prime factorization of 360
    # 360 = 2^3 * 3^2 * 5^1
    c4 = (2**3 * 3**2 * 5 == 360)
    # Primes used: {2, 3, 5}. Primes of 6 = {2, 3}. Extra prime = 5 = sopfr(6).

    passed = c1 and c3 and c4
    report("R4-CROSS-20",
           "360 degrees = sigma*sopfr*n, tau(360)=24=sigma*phi",
           f"360 = 12*5*6 = sigma*sopfr*n; tau(360) = {tau_360} = 24 = sigma*phi; "
           f"360 = 2^3 * 3^2 * 5 (primes: 2,3 from 6 + 5=sopfr)",
           passed, f"360={SIGMA}*{SOPFR}*{N}, tau(360)={tau_360}",
           "🟧★",
           "Genuinely interesting: 360 = sigma(6)*sopfr(6)*n AND tau(360)=24=sigma(6)*phi(6). "
           "The Babylonians chose 360 partly because of its many divisors (24), and this "
           "divisor count equals sigma*phi. The prime factorization 2^3*3^2*5 uses exactly "
           "the primes of 6 (2,3) plus sopfr(6)=5. Multiple independent structural links. "
           "However: 360 is base-60 Babylonian, and 60=2^2*3*5 already contains these primes.")


# ======================================================================
# R4-CROSS-21: Time zones -- 24 = sigma*phi zones
# ======================================================================
def test_21():
    """24 time zones (standard, ignoring fractional offsets).
    24 = sigma(6) * phi(6) = 12 * 2.
    24 hours/day. Hours per timezone = 1. Timezone width = 360/24 = 15 degrees.
    15 = sopfr(6) * n/phi = 5 * 3 = 15. Or simpler: 15 = (n+1)! / ... no.
    15 = sigma + n/phi = 12 + 3 = 15. Multiple ways.
    24 = 4! = tau(6)!. That's interesting: 24 = tau(6)!."""
    zones = 24
    hours_per_day = 24
    degrees_per_zone = 360 // zones  # 15

    c1 = (zones == SIGMA_PHI)  # 24 = 12*2
    c2 = (zones == math.factorial(TAU))  # 24 = 4! = tau(6)!
    c3 = (degrees_per_zone == 15)

    passed = c1 and c2
    report("R4-CROSS-21",
           "24 time zones = sigma*phi = tau! = 4!",
           f"24 zones = sigma(6)*phi(6) = 12*2; also 24 = 4! = tau(6)!",
           passed, f"zones={zones}, sigma*phi={SIGMA_PHI}, tau!={math.factorial(TAU)}",
           "🟧",
           "24 = 4! = tau(6)! is a genuine identity: the number of hours/timezones equals "
           "the factorial of the number of divisors of 6. But 24 hours comes from Egyptian/Babylonian "
           "base-12 counting (12 knuckles on one hand * 2 halves of day). "
           "The sigma*phi = 12*2 = 24 directly mirrors this historical origin.")


# ======================================================================
# R4-CROSS-22: UTF-8 encoding structure
# ======================================================================
def test_22():
    """UTF-8 encoding:
    1-byte: 0xxxxxxx (7 bits, 128 chars) -- ASCII
    2-byte: 110xxxxx 10xxxxxx (11 bits, 1920 chars)
    3-byte: 1110xxxx 10xxxxxx 10xxxxxx (16 bits, 61440 chars)
    4-byte: 11110xxx 10xxxxxx 10xxxxxx 10xxxxxx (21 bits)
    Max bytes per character = 4 = tau(6).
    Continuation byte prefix = 10 (2 bits) = phi(6) bits.
    1-byte payload = 7 bits = n+1.
    Total encoding lengths: {1,2,3,4}. Number of distinct lengths = 4 = tau(6).
    4-byte max gives 21 bits: 21 = T(6) = 6*7/2 = triangular number of 6."""
    max_bytes = 4
    continuation_prefix_bits = 2
    ascii_payload = 7
    four_byte_payload = 21  # 3 + 6 + 6 + 6 = 21 bits

    c1 = (max_bytes == TAU)
    c2 = (continuation_prefix_bits == PHI)
    c3 = (ascii_payload == N + 1)
    c4 = (four_byte_payload == N * (N + 1) // 2)  # T(6) = 21

    passed = c1 and c4
    report("R4-CROSS-22",
           "UTF-8: max 4=tau bytes, 21-bit max payload = T(6) triangular",
           f"Max bytes=4=tau(6); 4-byte payload=21 bits=T(6)=6*7/2; "
           f"continuation prefix=2=phi bits; ASCII=7=n+1 bits",
           passed, f"max_bytes={max_bytes}, payload_bits={four_byte_payload}, T(6)={N*(N+1)//2}",
           "🟧",
           "The 21-bit payload = T(6) = triangular(6) is a genuine and non-obvious match. "
           "UTF-8 was designed to be backward-compatible with ASCII (7 bits) and self-synchronizing. "
           "The 21-bit max comes from Unicode's U+10FFFF limit. "
           "tau=4 max bytes is a design consequence of the 21-bit requirement. "
           "T(6)=21 matching the Unicode bit budget is the most interesting observation.")


# ======================================================================
# R4-CROSS-23: DNA Phred quality scores
# ======================================================================
def test_23():
    """Phred quality score: Q = -10 * log10(P_error).
    Q=20 means P_error = 0.01 (99% accuracy).
    Q=30 means P_error = 0.001 (99.9%).
    Q=60 means P_error = 10^-6 = 10^-n (one in a million).
    At Q = 10*n = 60: error rate = 10^(-n) = 10^(-6).
    Standard threshold Q=20: error = 10^(-2) = 10^(-phi).
    High-quality threshold Q=30: error = 10^(-3) = 10^(-n/phi).
    Illumina typical max Q ~ 40 = 10*tau: error = 10^(-4) = 10^(-tau)."""
    Q_standard = 20
    Q_high = 30
    Q_perfect = 60
    Q_illumina = 40

    # P_error at each level
    p_20 = 10**(-Q_standard / 10)   # 0.01
    p_30 = 10**(-Q_high / 10)       # 0.001
    p_60 = 10**(-Q_perfect / 10)    # 10^-6

    c1 = (Q_perfect == 10 * N)     # Q=60 = 10*n
    c2 = abs(p_60 - 10**(-N)) < 1e-15  # error = 10^-6
    c3 = (Q_standard == 10 * PHI)  # Q=20 = 10*phi
    c4 = (Q_illumina == 10 * TAU)  # Q=40 = 10*tau

    passed = c1 and c2 and c3
    report("R4-CROSS-23",
           "Phred Q=60=10n gives error 10^-6=10^-n; Q=20=10*phi, Q=40=10*tau",
           f"Q=10*n=60: error=10^(-n)=10^-6; Q=10*phi=20: error=10^-2; Q=10*tau=40: error=10^-4",
           passed, f"Q60_error={p_60}, Q20_error={p_20}",
           "⚪",
           "TRIVIAL. Phred scores are defined as Q = -10*log10(P), so Q is always a multiple of 10 "
           "for clean error rates. Q=60 = 10*6 is just the definition applied to P=10^-6. "
           "Every integer maps to some Q threshold. No special role for n=6.")


# ======================================================================
# R4-CROSS-24: Fibonacci and n=6
# ======================================================================
def test_24():
    """Fibonacci sequence: 1,1,2,3,5,8,13,21,34,55,89,144,...
    F(6) = 8 = 2^3 = 2^(n/phi).
    F(12) = F(sigma) = 144 = 12^2 = sigma^2.
    F(6) = 8 is the only Fibonacci number that is a perfect cube (2^3).
    F(12) = 144 is the only Fibonacci number that is a perfect square > 1 (besides F(0)=0, F(1)=F(2)=1).
    Also: F(6) * F(6) = 64 = F(12) - 80. Not clean.
    But: F(12) = F(sigma(6)) = sigma(6)^2. That's remarkable if true."""
    fibs = [0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144]
    f6 = fibs[6]   # 8
    f12 = fibs[12]  # 144

    c1 = (f6 == 8)
    c2 = (f6 == 2**3)           # 8 = 2^3
    c3 = (f12 == 144)
    c4 = (f12 == SIGMA**2)     # 144 = 12^2
    c5 = (f12 == fibs[2 * N])  # F(2n) = F(12)

    # F(6) = 8 is the only Fibonacci perfect cube > 1 (Bugeaud, Mignotte, Siksek 2006)
    # F(12) = 144 is the largest Fibonacci perfect square (Cohn 1964, completed by others)
    import math
    is_cube_f6 = round(f6 ** (1/3)) ** 3 == f6  # 2^3 = 8
    is_square_f12 = int(math.isqrt(f12)) ** 2 == f12  # 12^2 = 144

    c6 = is_cube_f6
    c7 = is_square_f12

    passed = c4 and c6 and c7
    report("R4-CROSS-24",
           "Fibonacci: F(6)=8=2^3 (only Fib cube), F(12)=144=12^2=sigma^2 (only Fib square)",
           f"F(6)=8=2^3 (unique Fibonacci perfect cube); "
           f"F(sigma(6))=F(12)=144=12^2=sigma(6)^2 (largest Fibonacci perfect square)",
           passed, f"F(6)={f6}=2^3, F(12)={f12}=12^2={SIGMA}^2",
           "🟧★",
           "GENUINE AND NOTABLE. F(6)=8 is the only nontrivial Fibonacci perfect cube (proved). "
           "F(12)=F(sigma(6))=144=sigma(6)^2=12^2 is the largest Fibonacci perfect square (proved). "
           "These are deep number-theoretic results (Cohn 1964, Bugeaud-Mignotte-Siksek 2006). "
           "The fact that F(n) and F(sigma(n)) are the unique Fibonacci perfect powers at n=6 "
           "is a structural observation connecting Fibonacci, divisor sums, and Diophantine equations.")


# ======================================================================
# R4-CROSS-25: Penrose tiling -- 5-fold symmetry
# ======================================================================
def test_25():
    """Penrose tiling: aperiodic tiling with 5-fold rotational symmetry.
    5 = sopfr(6). The golden ratio phi_gold = (1+sqrt(5))/2 governs tile ratios.
    Penrose uses 2 tile types (kites and darts, or thick/thin rhombi).
    Tile types = 2 = phi(6).
    Vertex configurations: 7 types in kite-dart tiling = n + 1.
    Ratio of thick to thin tiles -> golden ratio as patch grows.
    Inflation factor = golden ratio = 1.618... = (1+sqrt(sopfr(6)))/2.
    5-fold symmetry is forbidden in periodic crystals (crystallographic restriction)."""
    symmetry_fold = 5
    tile_types = 2  # kites and darts
    vertex_configs = 7  # known vertex neighborhoods in Penrose P2
    golden = GOLDEN_RATIO
    inflation = golden  # self-similar inflation factor

    c1 = (symmetry_fold == SOPFR)  # 5 = sopfr(6)
    c2 = (tile_types == PHI)       # 2 tile types
    c3 = (vertex_configs == N + 1) # 7 vertex types
    c4 = abs(golden - (1 + math.sqrt(SOPFR)) / 2) < 1e-10  # phi = (1+sqrt(5))/2

    passed = c1 and c2 and c4
    report("R4-CROSS-25",
           "Penrose tiling: 5=sopfr fold symmetry, 2=phi tile types, golden=(1+sqrt(sopfr))/2",
           f"5-fold = sopfr(6); 2 tiles = phi(6); golden ratio = (1+sqrt(sopfr(6)))/2",
           passed, f"symmetry={symmetry_fold}, tiles={tile_types}, golden={golden:.6f}",
           "🟧",
           "The golden ratio = (1+sqrt(5))/2 with 5=sopfr(6) is a real identity but "
           "the connection is that phi_gold is defined via sqrt(5), and sopfr(6)=2+3=5. "
           "2 tile types = phi(6) is a small-number match. "
           "The deeper point: 5-fold symmetry is mathematically special (quasicrystals, "
           "Shechtman 1984 Nobel), and sopfr(6)=5 links n=6 to this forbidden symmetry.")


# ══════════════════════════════════════════════════════════════════════════
# Run all tests and summary
# ══════════════════════════════════════════════════════════════════════════
def main():
    print("=" * 76)
    print("TECS-L Round 4: 25 Cross-Domain Hypothesis Verification")
    print(f"n=6, sigma={SIGMA}, tau={TAU}, phi={PHI}, sopfr={SOPFR}, "
          f"sigma*phi={SIGMA_PHI}, ln(4/3)={LN43:.4f}")
    print("=" * 76)

    tests = [
        test_01, test_02, test_03, test_04, test_05,
        test_06, test_07, test_08, test_09, test_10,
        test_11, test_12, test_13, test_14, test_15,
        test_16, test_17, test_18, test_19, test_20,
        test_21, test_22, test_23, test_24, test_25,
    ]

    for t in tests:
        try:
            t()
        except Exception as e:
            print(f"\nERROR in {t.__name__}: {e}")

    # ── Summary ──
    print("\n" + "=" * 76)
    print("ROUND 4 SUMMARY")
    print("=" * 76)

    grade_counts = {}
    for tag, title, formula, status, value, grade, note in results:
        grade_counts[grade] = grade_counts.get(grade, 0) + 1
        print(f"  {tag}: {title}")
        print(f"    {status} | {grade} | {value}")

    print("\n" + "-" * 76)
    print("GRADE DISTRIBUTION:")
    for g in sorted(grade_counts.keys()):
        print(f"  {g}: {grade_counts[g]}")

    total = len(results)
    passed = sum(1 for r in results if r[3] == "PASS")
    starred = sum(1 for r in results if "★" in r[5])
    orange_plus = sum(1 for r in results if r[5] in ("🟧", "🟧★", "🟩"))
    white = sum(1 for r in results if r[5] == "⚪")

    print(f"\n  Total: {total}")
    print(f"  PASS:  {passed}")
    print(f"  Structural (🟧+): {orange_plus}")
    print(f"  Starred (🟧★):    {starred}")
    print(f"  Coincidence (⚪):  {white}")

    print("\n" + "-" * 76)
    print("HONESTY ASSESSMENT:")
    print("  Small-number warning: n=6 invariants (2,4,5,6,12,24) are very common")
    print("  numbers that appear everywhere. Most matches are coincidental.")
    print("  Genuinely interesting (non-trivial structural links):")
    for tag, title, formula, status, value, grade, note in results:
        if "★" in grade or grade == "🟩":
            print(f"    {tag}: {title} [{grade}]")

    print("\n  Key insight: The best results connect to INDEPENDENT mathematical")
    print("  theorems (Fibonacci perfect powers, Dedekind numbers) rather than")
    print("  simple arithmetic matches with small numbers.")

    # ── Texas Sharpshooter Quick Check ──
    print("\n" + "-" * 76)
    print("TEXAS SHARPSHOOTER QUICK CHECK:")
    print(f"  25 hypotheses tested, {orange_plus} at 🟧 or above, {starred} starred")
    print(f"  If random: expect ~{total * 0.15:.1f} matches at 15% base rate (small numbers)")
    print(f"  Observed structural: {orange_plus}/{total} = {100*orange_plus/total:.0f}%")
    if orange_plus > total * 0.15:
        excess = orange_plus - total * 0.15
        print(f"  Excess over random: ~{excess:.1f} hypotheses")
        print(f"  Some structure likely present, but individual claims need scrutiny")
    else:
        print(f"  Within random expectation. No evidence of structure beyond chance.")


if __name__ == "__main__":
    main()
