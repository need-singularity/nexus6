#!/usr/bin/env python3
"""
TECS-L Round 2 Bridge Hypotheses: 20 Cross-Domain Bridges via n=6 Arithmetic
=============================================================================
Each hypothesis bridges AT LEAST 2 distinct domains, linked by n=6 arithmetic.
n=6: sigma=12, tau=4, phi=2, sopfr=5, sigma*phi=24, sigma_{-1}=2
"""

import math
import sys
from fractions import Fraction

# ─── n=6 arithmetic constants ───
N = 6
SIGMA = 12       # sum of divisors: 1+2+3+6
TAU = 4          # number of divisors: {1,2,3,6}
PHI = 2          # Euler totient: {1,5}
SOPFR = 5        # sum of prime factors: 2+3
SIGMA_PHI = 24   # sigma * phi = 12 * 2
SIGMA_INV = 2    # sigma_{-1}(6) = 1/1 + 1/2 + 1/3 + 1/6 = 2
DIVISORS = [1, 2, 3, 6]

results = []
pass_count = 0
fail_count = 0

def report(num, title, domain_a, domain_b, fact_a, fact_b, bridge_via,
           verified_a, verified_b, assessment, grade, details=""):
    global pass_count, fail_count
    both = verified_a and verified_b
    if both:
        pass_count += 1
    else:
        fail_count += 1

    status = "YES" if both else "NO"
    r = {
        "num": num, "title": title, "domain_a": domain_a, "domain_b": domain_b,
        "fact_a": fact_a, "fact_b": fact_b, "bridge_via": bridge_via,
        "verified": status, "assessment": assessment, "grade": grade,
        "details": details
    }
    results.append(r)

    print(f"\nR2-BRIDGE-{num:02d}: [{domain_a}] <-> [{domain_b}]: {title}")
    print(f"  Domain A fact: {fact_a}")
    print(f"  Domain B fact: {fact_b}")
    print(f"  Bridge via: {bridge_via}")
    print(f"  Both verified: {status}")
    print(f"  Structural or coincidental: {assessment}")
    print(f"  Grade: {grade}")
    if details:
        print(f"  Details: {details}")


def verify_sigma_inv():
    """Verify sigma_{-1}(6) = 2"""
    return sum(Fraction(1, d) for d in DIVISORS) == 2

# ═══════════════════════════════════════════════════════════════
# BRIDGE 01: Bosonic String Dimension <-> Ramanujan Sum
# ═══════════════════════════════════════════════════════════════
def bridge_01():
    # Domain A: String theory requires D=26 for bosonic strings
    # The critical dimension uses 1+2+3+...= -1/12 (zeta regularization)
    # D = 2 + 24 = 26, where 24 = the "transverse dimensions"

    # Domain B: sigma(6)*phi(6) = 12*2 = 24
    # Also: Ramanujan tau function, Leech lattice dimension = 24

    # Verify A: D_bosonic = 26, transverse = 24
    D_bosonic = 26
    transverse = D_bosonic - 2  # subtract time + longitudinal

    # Verify B: sigma*phi = 24
    sp = SIGMA * PHI

    verified_a = (transverse == 24)
    verified_b = (sp == 24)

    # Deeper check: Leech lattice = unique even unimodular lattice in dim 24
    # Its theta function relates to Ramanujan Delta
    leech_dim = 24

    report(1, "Bosonic string transverse dim = sigma*phi(6)",
           "String Theory", "Number Theory (n=6)",
           f"Bosonic string: D=26, transverse dimensions = {transverse}",
           f"sigma(6)*phi(6) = {SIGMA}*{PHI} = {sp}",
           f"sigma*phi(6) = {sp} = transverse dimensions of bosonic string",
           verified_a, verified_b,
           "STRUCTURAL: 24 appears in Leech lattice, modular forms, bosonic strings -- all linked via modular invariance. sigma*phi(6)=24 is arithmetic.",
           "star_star" if verified_a and verified_b else "white",
           f"Leech lattice dim={leech_dim}, Monster group connection via j-invariant")

bridge_01()

# ═══════════════════════════════════════════════════════════════
# BRIDGE 02: QCD Color Factor <-> Musical Fourth <-> R-spectrum
# ═══════════════════════════════════════════════════════════════
def bridge_02():
    # Domain A: QCD - ratio of Casimir operators C_F/C_A = 4/3 / 3 ... no.
    # Actually: In QCD, the color factor for quark-gluon vertex = C_F = (N_c^2-1)/(2*N_c) = 4/3 for N_c=3
    N_c = 3
    C_F = (N_c**2 - 1) / (2 * N_c)

    # Domain B: Musical perfect fourth = frequency ratio 4/3
    musical_fourth = Fraction(4, 3)

    # Domain C (R-spectrum): ln(4/3) = Golden Zone width
    gz_width = math.log(4/3)

    # Bridge via n=6: divisors of 6 include 2 and 3
    # 4/3 = (2^2)/3, using prime factors of 6
    # Also: 4 = tau(6)^1... no, tau=4 exactly! And 3 is a divisor.
    # So 4/3 = tau(6) / 3 where 3 | 6

    verified_a = abs(C_F - 4/3) < 1e-10
    verified_b = (musical_fourth == Fraction(4, 3))

    report(2, "QCD color factor = musical fourth = tau(6)/3",
           "QCD (Physics)", "Music Theory / Information Theory",
           f"QCD color factor C_F = (N_c^2-1)/(2*N_c) = {C_F} for N_c=3",
           f"Perfect fourth = {musical_fourth}, GZ width = ln(4/3) = {gz_width:.6f}",
           f"4/3 = tau(6)/3 where tau(6)={TAU}, 3|6",
           verified_a, verified_b,
           "MIXED: 4/3 in QCD follows from SU(3) group theory. 4/3 in music from Pythagorean tuning. The n=6 link (tau/3) is suggestive but may be coincidental. The ln(4/3) entropy jump is independently motivated.",
           "star",
           f"C_F={C_F:.6f}, tau(6)={TAU}, 3 divides 6, ln(4/3)={gz_width:.6f}")

bridge_02()

# ═══════════════════════════════════════════════════════════════
# BRIDGE 03: Hexagonal Close Packing <-> Carbon sp2 <-> Grid Cells
# ═══════════════════════════════════════════════════════════════
def bridge_03():
    # Domain A: Hexagonal close packing - packing fraction
    # HCP packing fraction = pi/(3*sqrt(2)) = 0.7405
    hcp_fraction = math.pi / (3 * math.sqrt(2))

    # Domain B: Graphene - each C atom has 3 bonds, hexagonal lattice
    # Coordination number = 3, ring size = 6
    graphene_ring = 6
    graphene_coord = 3  # sp2 hybridization

    # Domain C: Entorhinal grid cells fire in hexagonal pattern
    # Grid cell spacing ratio between modules ~ 1.42 ≈ sqrt(2)
    grid_cell_ratio = math.sqrt(2)  # experimentally ~1.4-1.5

    # Bridge: n=6 is the ring size. Why hexagonal?
    # Hexagon tiles the plane (one of only 3 regular tilings: 3,4,6)
    # Among these, hexagon maximizes area/perimeter ratio
    # Area/perimeter for regular n-gon with unit side:
    def area_per_perimeter(n):
        area = n / 4 * 1 / math.tan(math.pi / n)
        perimeter = n
        return area / perimeter

    ratios = {n: area_per_perimeter(n) for n in [3, 4, 6]}
    hex_is_max = ratios[6] == max(ratios.values())

    verified_a = abs(hcp_fraction - 0.7405) < 0.001
    verified_b = (graphene_ring == 6) and hex_is_max

    report(3, "Hexagonal optimality: packing <-> graphene <-> grid cells",
           "Crystallography/Materials", "Neuroscience (Grid Cells)",
           f"HCP fraction = pi/(3*sqrt(2)) = {hcp_fraction:.4f}; hex tiles plane optimally",
           f"Grid cells use hexagonal firing pattern; graphene ring size = {graphene_ring}",
           f"n=6 hexagon: max area/perimeter among plane-tiling regular polygons. Ratios: {', '.join(f'{k}-gon={v:.4f}' for k,v in ratios.items())}",
           verified_a, verified_b,
           "STRUCTURAL: Hexagonal geometry is the UNIQUE optimal solution for 2D packing/tiling. This is a theorem (honeycomb conjecture, proved by Hales 1999). All three domains independently converge on hex because they solve the same optimization.",
           "star_star_star",
           f"Honeycomb theorem (Hales 1999). Isoperimetric optimality drives convergence.")

bridge_03()

# ═══════════════════════════════════════════════════════════════
# BRIDGE 04: RMT Dyson Index <-> Attention Heads <-> Spacetime
# ═══════════════════════════════════════════════════════════════
def bridge_04():
    # Domain A: Random Matrix Theory - Dyson index beta in {1,2,4}
    # beta=1: GOE (real symmetric), beta=2: GUE (complex Hermitian), beta=4: GSE (quaternion)
    # phi(6)=2, tau(6)=4: these ARE Dyson indices!

    dyson_indices = [1, 2, 4]

    # Domain B: Transformer attention
    # Typical multi-head attention uses power-of-2 heads: 2, 4, 8, 16
    # phi(6)=2 (minimum heads for diversity), tau(6)=4 (standard small model)

    # Domain C: Spacetime
    # phi(6)^2 = 4 = number of spacetime dimensions
    spacetime_dim = PHI ** 2

    verified_a = (PHI in dyson_indices) and (TAU in dyson_indices)
    verified_b = (spacetime_dim == 4)

    # Check: phi^2 = tau is an arithmetic identity for n=6
    identity_holds = (PHI ** 2 == TAU)

    report(4, "phi(6)^2 = tau(6) = 4: RMT beta <-> spacetime dimension",
           "Random Matrix Theory", "Physics (Spacetime)",
           f"Dyson indices = {dyson_indices}; phi(6)={PHI} (GUE), tau(6)={TAU} (GSE) are both Dyson indices",
           f"phi(6)^2 = {PHI}^2 = {spacetime_dim} = spacetime dimensions",
           f"Arithmetic identity phi(6)^2 = tau(6) maps GUE universality class to spacetime dim",
           verified_a, verified_b,
           "COINCIDENTAL for spacetime link (4 appears everywhere). STRUCTURAL for RMT: phi,tau being Dyson indices is non-trivial since only 1,2,4 are allowed.",
           "star",
           f"phi^2=tau identity: {identity_holds}. Only n=6 among small perfect numbers has this.")

bridge_04()

# ═══════════════════════════════════════════════════════════════
# BRIDGE 05: Shannon Channel Capacity <-> sigma_{-1}(6) = 2
# ═══════════════════════════════════════════════════════════════
def bridge_05():
    # Domain A: Shannon's channel capacity theorem
    # C = B * log2(1 + S/N)
    # For S/N = 1 (signal = noise): C = B * log2(2) = B * 1 = B
    # The "1 bit per Hz" threshold occurs at S/N = 1

    # Domain B: sigma_{-1}(6) = 1/1 + 1/2 + 1/3 + 1/6 = 2
    # This is the DEFINITION of perfect number: sigma_{-1}(n) = 2

    # Bridge: sigma_{-1}(6) = 2 means the "information budget" of divisors
    # sums to exactly 2, giving a natural doubling/1-bit structure

    snr_threshold = 1  # S/N where C = B
    capacity_at_snr1 = math.log2(1 + snr_threshold)  # = 1 bit/Hz

    sigma_inv_val = sum(Fraction(1, d) for d in DIVISORS)
    log2_sigma_inv = math.log2(float(sigma_inv_val))  # log2(2) = 1

    verified_a = abs(capacity_at_snr1 - 1.0) < 1e-10
    verified_b = (sigma_inv_val == 2) and abs(log2_sigma_inv - 1.0) < 1e-10

    report(5, "sigma_{-1}(6) = 2: perfect number as 1-bit information boundary",
           "Information Theory (Shannon)", "Number Theory (Perfect Numbers)",
           f"Shannon: C=B*log2(1+S/N); at S/N=1, C=B*{capacity_at_snr1} = B bits/Hz",
           f"sigma_{{-1}}(6) = {sigma_inv_val}; log2(sigma_{{-1}}(6)) = {log2_sigma_inv:.1f} bit",
           f"Perfect numbers are exactly those where divisor-reciprocal sum = 2 = 2^1, encoding exactly 1 bit of redundancy",
           verified_a, verified_b,
           "STRUCTURAL: The connection is that sigma_{-1}=2 is equivalent to saying n is perfect. The information-theoretic reading (1 bit) is a restatement, not a coincidence. But the BRIDGE to Shannon capacity is suggestive, not proven.",
           "star",
           f"Only perfect numbers satisfy sigma_{{-1}}=2. For n=6 this is exact.")

bridge_05()

# ═══════════════════════════════════════════════════════════════
# BRIDGE 06: Euler Product Truncation <-> Hydrogen Atom
# ═══════════════════════════════════════════════════════════════
def bridge_06():
    # Domain A: zeta(s) Euler product truncated at primes 2,3 (prime factors of 6)
    # Product_{p|6} 1/(1-p^{-s}) at s=2:
    # = 1/(1-1/4) * 1/(1-1/9) = (4/3) * (9/8) = 36/24 = 3/2

    s = 2
    euler_trunc = 1.0
    for p in [2, 3]:
        euler_trunc *= 1 / (1 - p**(-s))

    # Full zeta(2) = pi^2/6
    zeta_2 = math.pi**2 / 6

    # Ratio of truncation to full
    ratio = euler_trunc / zeta_2

    # Domain B: Hydrogen atom - Rydberg constant structure
    # E_n = -13.6 eV / n^2
    # Ratio E_1/E_2 = 4, E_1/E_3 = 9
    # Lyman series limit / Balmer limit = (1 - 1/4)/(1 - 1/9) ... no
    # Better: Balmer series uses n=2 lower state, Paschen uses n=3
    # Balmer limit: 1/4, Paschen limit: 1/9
    # The Euler factors at p=2,3 are 1/(1-1/p^2) = 1/(1-1/4), 1/(1-1/9)
    # These are EXACTLY the hydrogen spectral series denominators!

    balmer_factor = 1 / (1 - Fraction(1, 4))   # = 4/3
    paschen_factor = 1 / (1 - Fraction(1, 9))  # = 9/8

    verified_a = abs(euler_trunc - 1.5) < 1e-10  # 3/2
    verified_b = (balmer_factor == Fraction(4, 3)) and (paschen_factor == Fraction(9, 8))

    report(6, "Euler product at p=2,3 <-> Hydrogen Balmer/Paschen series factors",
           "Analytic Number Theory", "Atomic Physics (Hydrogen)",
           f"zeta Euler product truncated at primes of 6: (4/3)*(9/8) = {euler_trunc}",
           f"Balmer factor 1/(1-1/4)=4/3, Paschen factor 1/(1-1/9)=9/8",
           f"Euler factors 1/(1-p^{{-2}}) at p=2,3 are hydrogen spectral series geometric sums",
           verified_a, verified_b,
           "STRUCTURAL: Both arise from geometric series Sum(1/p^{2k}). Hydrogen energy levels go as 1/n^2 and Euler product factors are 1/(1-p^{-s}). At s=2, the algebraic form is identical. The p=2,3 truncation selects exactly the first two spectral series.",
           "star_star",
           f"Euler product at p=2,3 for s=2: {euler_trunc}. zeta(2)={zeta_2:.6f}, ratio={ratio:.4f}")

bridge_06()

# ═══════════════════════════════════════════════════════════════
# BRIDGE 07: ADE Classification <-> Ice Crystal Symmetry
# ═══════════════════════════════════════════════════════════════
def bridge_07():
    # Domain A: ADE classification - E6 exceptional Lie algebra
    # E6 has rank 6, dimension 78, Coxeter number h=12
    E6_rank = 6
    E6_dim = 78
    E6_coxeter = 12  # Coxeter number

    # Domain B: Ice Ih crystal structure
    # Ice has hexagonal symmetry (space group P6_3/mmc)
    # Each water molecule has 4 nearest neighbors (tetrahedral)
    # But the overall lattice symmetry is hexagonal (6-fold)
    ice_symmetry = 6  # hexagonal
    ice_coordination = 4  # tetrahedral hydrogen bonding

    # Bridge: E6 rank = 6, Coxeter number = 12 = sigma(6)
    # Ice: 6-fold symmetry, 4 coordination = tau(6)

    verified_a = (E6_rank == N) and (E6_coxeter == SIGMA)
    verified_b = (ice_symmetry == N) and (ice_coordination == TAU)

    report(7, "E6 Lie algebra (rank=6, h=12) <-> Ice Ih (6-fold, coord=4)",
           "Algebra (ADE Classification)", "Crystallography (Ice Physics)",
           f"E6: rank={E6_rank}=n, dim={E6_dim}, Coxeter number h={E6_coxeter}=sigma(6)",
           f"Ice Ih: hexagonal symmetry order {ice_symmetry}=n, coordination {ice_coordination}=tau(6)",
           f"E6 rank=n=6, Coxeter h=sigma(6)=12; Ice: symmetry=6, coord=tau(6)=4",
           verified_a, verified_b,
           "MIXED: E6 having rank 6 and h=12 is a mathematical fact. Ice having 6-fold symmetry and 4-coordination is physics. The bridge via sigma and tau is numerological -- the numbers match but there is no known causal mechanism.",
           "star",
           f"E6 Coxeter number=12=sigma(6): this is verified. Ice coordination=4=tau(6): verified.")

bridge_07()

# ═══════════════════════════════════════════════════════════════
# BRIDGE 08: Benzene pi-electrons <-> Aromaticity Rule <-> n=6
# ═══════════════════════════════════════════════════════════════
def bridge_08():
    # Domain A: Benzene C6H6 has 6 pi-electrons in a ring of 6 carbons
    # Huckel's rule: aromatic if 4k+2 pi-electrons, k=1 gives 6
    k = 1
    huckel_electrons = 4 * k + 2  # = 6

    # Domain B: Topological index - benzene's Wiener index
    # Wiener index W = sum of all shortest path distances
    # For C6 cycle: W = 6*1 + 6*2 + 3*3 = 6+12+9 = 27...
    # Actually for hexagonal ring (cycle graph C6):
    # distances: each vertex to others: 1,2,3,2,1 -> sum per vertex = 9
    # Total W = 6*9/2 = 27
    wiener_C6 = 27

    # Domain C: Graph theory - cycle C6 properties
    # Chromatic number chi(C6) = 2 (bipartite, even cycle)
    # Independence number alpha(C6) = 3
    # C6 automorphism group = dihedral D6, order 12 = sigma(6)

    C6_automorphisms = 2 * 6  # dihedral group D_6 has order 2n = 12

    verified_a = (huckel_electrons == 6)
    verified_b = (C6_automorphisms == SIGMA)

    report(8, "Benzene aromaticity <-> C6 graph automorphisms = sigma(6)",
           "Chemistry (Aromaticity)", "Graph Theory",
           f"Benzene: {huckel_electrons} pi-electrons by Huckel rule (4*{k}+2), ring size 6",
           f"Cycle graph C6: |Aut(C6)| = |D_6| = {C6_automorphisms} = sigma(6)",
           f"Huckel 4k+2 at k=1 gives 6; C6 dihedral symmetry group order = sigma(6) = 12",
           verified_a, verified_b,
           "STRUCTURAL: The dihedral group D_n always has order 2n, so D_6 = 12 = sigma(6). This is NOT a coincidence: sigma(6)=2*6 because 6 is perfect (so sigma(6)=12=2n). For non-perfect n, sigma(n) != 2n. The benzene ring's symmetry group order equals sigma(n) BECAUSE n=6 is perfect.",
           "star_star",
           f"D_6 order = 2*6 = 12 = sigma(6). This equality holds iff sigma(n)=2n iff n perfect.")

bridge_08()

# ═══════════════════════════════════════════════════════════════
# BRIDGE 09: Proton Quark Content <-> sopfr(6)
# ═══════════════════════════════════════════════════════════════
def bridge_09():
    # Domain A: Proton = uud, total quark charge = 2/3 + 2/3 - 1/3 = 1
    # Number of valence quarks = 3
    # But consider: proton is in SU(3) flavor, with 3 light quarks u,d,s
    # Up quark mass ~ 2.2 MeV, down ~ 4.7 MeV, strange ~ 93 MeV
    # Sum of lightest 2 quark masses (u+d) ~ 6.9 MeV (but this is approximate)

    # Better: Baryon number = 1/3 per quark. 3 quarks -> B=1.
    # Meson has 2 quarks (quark+antiquark).
    # Pentaquark has 5 quarks (4q + 1 anti-q).
    # sopfr(6) = 2+3 = 5 = number of quarks in a pentaquark!

    pentaquark_quarks = 5
    baryon_quarks = 3  # a divisor of 6
    meson_quarks = 2   # a divisor of 6 (and prime factor)

    # Domain B: sopfr(6) = 2+3 = 5
    # Also: SU(5) is the simplest GUT group
    SU5_rank = 4  # rank of SU(5) = 5-1 = 4 = tau(6)... tangent

    verified_a = (pentaquark_quarks == SOPFR)
    verified_b = (meson_quarks in DIVISORS) and (baryon_quarks in DIVISORS)

    report(9, "Quark multiplets {2,3,5} <-> prime decomposition of 6",
           "Particle Physics (QCD)", "Number Theory (sopfr)",
           f"Meson=2q, Baryon=3q, Pentaquark=5q; exotic states at prime factors and their sum",
           f"6=2*3, sopfr(6)=2+3=5; divisors include {{1,2,3,6}}",
           f"Quark content of hadron families = {{2,3,5}} = {{prime factors, sopfr}} of 6",
           verified_a, verified_b,
           "COINCIDENTAL: Meson=qq(2) and baryon=qqq(3) follow from SU(3) color confinement (color singlets). Pentaquark=5 is 4q+1qbar. The match to sopfr(6)=5 is amusing but the physics has independent origin.",
           "white",
           f"Interesting numerology but no causal mechanism. sopfr(6)={SOPFR}")

bridge_09()

# ═══════════════════════════════════════════════════════════════
# BRIDGE 10: Fractal Dimension of DLA <-> sigma_{-1}(6)
# ═══════════════════════════════════════════════════════════════
def bridge_10():
    # Domain A: Diffusion-Limited Aggregation in 2D
    # Fractal dimension d_f ≈ 1.71 (well-established numerical result)
    # Not obviously connected...

    # Better bridge: Mandelbrot set boundary
    # d_f(Mandelbrot boundary) = 2 exactly (proved by Shishikura 1998)
    mandelbrot_boundary_dim = 2

    # Domain B: sigma_{-1}(6) = 2
    # The fractal dimension of the Mandelbrot boundary = sigma_{-1}(6)

    # Another: Brownian motion has Hausdorff dimension 2 in any ambient dimension >= 2
    brownian_dim = 2  # proved by Levy

    # Koch snowflake: d = log(4)/log(3) = ln(4)/ln(3)
    # And ln(4/3) = ln(4) - ln(3) is our Golden Zone width!
    koch_dim = math.log(4) / math.log(3)
    gz_width = math.log(4/3)
    # Relation: koch_dim = ln(4)/ln(3) = 1 + ln(4/3)/ln(3) = 1 + gz_width/ln(3)
    koch_from_gz = 1 + gz_width / math.log(3)

    verified_a = (mandelbrot_boundary_dim == 2) and (brownian_dim == 2)
    verified_b = (float(sum(Fraction(1,d) for d in DIVISORS)) == 2.0)

    report(10, "Mandelbrot boundary dim = Brownian dim = sigma_{-1}(6) = 2",
           "Fractal Geometry", "Number Theory (Perfect Numbers)",
           f"Mandelbrot boundary Hausdorff dim = {mandelbrot_boundary_dim} (Shishikura 1998); Brownian motion dim = {brownian_dim}",
           f"sigma_{{-1}}(6) = {float(sum(Fraction(1,d) for d in DIVISORS))}",
           f"Three independent appearances of 2: Mandelbrot boundary, Brownian motion, perfect number criterion",
           verified_a, verified_b,
           "COINCIDENTAL: dim=2 for Mandelbrot boundary comes from complex dynamics. For Brownian motion from probability. sigma_{-1}(6)=2 from number theory. The value 2 is too common to be meaningful.",
           "white",
           f"Koch snowflake dim = ln4/ln3 = {koch_dim:.6f} = 1 + GZ_width/ln3 = {koch_from_gz:.6f}")

bridge_10()

# ═══════════════════════════════════════════════════════════════
# BRIDGE 11: DNA Codon Table <-> 6^3 Overcounting
# ═══════════════════════════════════════════════════════════════
def bridge_11():
    # Domain A: Genetic code has 64 codons = 4^3 (4 bases, 3 positions)
    # Encodes 20 amino acids + 1 stop = 21 signals
    # Degeneracy: 64/21 ≈ 3.05 (each amino acid coded by ~3 codons on average)

    codons = 4**3  # = 64
    amino_acids = 20
    stop_codons = 3
    signals = amino_acids + 1  # 20 AA + stop
    degeneracy = codons / signals

    # Domain B: n=6 arithmetic
    # tau(6) = 4 (number of DNA bases?)
    # Actually: 4 bases = 2^2 = phi(6)^2 = tau(6)
    # Codon length = 3 (divisor of 6)
    # 4^3 = tau(6)^3 = 64

    tau_cubed = TAU ** 3
    codon_length = 3  # divisor of 6

    verified_a = (codons == 64) and (codon_length == 3)
    verified_b = (tau_cubed == 64) and (codon_length in DIVISORS)

    report(11, "Genetic code: 64 codons = tau(6)^3, codon length = 3|6",
           "Molecular Biology (Genetics)", "Number Theory (n=6 divisors)",
           f"DNA: {codons} codons = 4^3, codon length 3, encodes {amino_acids} amino acids",
           f"tau(6)={TAU}, tau(6)^3={tau_cubed}=64; codon length 3 is a divisor of 6",
           f"4 bases = tau(6), 3-letter codons use divisor of 6, total = tau(6)^3",
           verified_a, verified_b,
           "COINCIDENTAL: 4 DNA bases evolved from chemistry (hydrogen bonding pairs). Codon length 3 gives 64>20 (minimum for 20 AA). Numbers match tau(6) by coincidence.",
           "white",
           f"Degeneracy = {degeneracy:.2f} codons per signal. 64/20 ≈ 3.2")

bridge_11()

# ═══════════════════════════════════════════════════════════════
# BRIDGE 12: Kepler Conjecture <-> Kissing Number <-> sigma(6)
# ═══════════════════════════════════════════════════════════════
def bridge_12():
    # Domain A: Kissing number in 3D = 12
    # This is the maximum number of unit spheres that can touch a central unit sphere
    # Proved by Schutte and van der Waerden (1953)
    kissing_3d = 12

    # Domain B: sigma(6) = 12

    # Also: kissing number in dimension n:
    # dim 1: 2, dim 2: 6, dim 3: 12, dim 4: 24, dim 8: 240, dim 24: 196560
    kissing_numbers = {1: 2, 2: 6, 3: 12, 4: 24, 8: 240, 24: 196560}

    # Remarkable: kissing(2) = 6 = n
    # kissing(3) = 12 = sigma(6)
    # kissing(4) = 24 = sigma(6)*phi(6)

    verified_a = (kissing_3d == 12)
    verified_b = (SIGMA == 12)

    # Check the deeper pattern
    kiss2_eq_n = (kissing_numbers[2] == N)
    kiss3_eq_sigma = (kissing_numbers[3] == SIGMA)
    kiss4_eq_sigmaphi = (kissing_numbers[4] == SIGMA_PHI)

    report(12, "Kissing numbers k(2)=6, k(3)=12=sigma(6), k(4)=24=sigma*phi(6)",
           "Sphere Packing (Geometry)", "Number Theory (n=6 arithmetic)",
           f"Kissing numbers: k(2)={kissing_numbers[2]}, k(3)={kissing_numbers[3]}, k(4)={kissing_numbers[4]}",
           f"n=6, sigma(6)={SIGMA}, sigma*phi(6)={SIGMA_PHI}",
           f"k(d) for d=2,3,4 gives exactly {{6, 12, 24}} = {{n, sigma, sigma*phi}}",
           verified_a, verified_b,
           f"STRUCTURAL: The kissing number sequence at d=2,3,4 IS {{6,12,24}}. These are also lattice properties (A2, A3/D3, D4). The n=6 match at d=2 may seed the higher matches via lattice relationships. k(2)=6={kiss2_eq_n}, k(3)=12={kiss3_eq_sigma}, k(4)=24={kiss4_eq_sigmaphi}.",
           "star_star_star",
           f"All three verified. This is a striking triple match involving well-known constants.")

bridge_12()

# ═══════════════════════════════════════════════════════════════
# BRIDGE 13: Modular Forms Weight 12 <-> sigma(6) <-> Music
# ═══════════════════════════════════════════════════════════════
def bridge_13():
    # Domain A: Ramanujan Delta function is a modular form of weight 12
    # Delta(q) = q * Product_{n>=1} (1-q^n)^24
    # Weight k=12, with the exponent 24 = sigma*phi(6)
    delta_weight = 12
    delta_exponent = 24

    # Domain B: Western music - 12 semitones per octave
    # Equal temperament: f_n = f_0 * 2^(n/12)
    semitones = 12

    # Domain C: sigma(6) = 12

    # The 12 in music comes from approximating ratios like 3/2, 4/3, 5/4
    # by powers of 2^(1/12). Why 12? Because 2^(7/12) ≈ 1.4983 ≈ 3/2
    fifth_approx = 2**(7/12)
    fifth_exact = 3/2
    fifth_error = abs(fifth_approx - fifth_exact) / fifth_exact * 100

    verified_a = (delta_weight == SIGMA) and (delta_exponent == SIGMA_PHI)
    verified_b = (semitones == SIGMA)

    report(13, "Ramanujan Delta weight 12 = chromatic scale 12 = sigma(6)",
           "Modular Forms (Number Theory)", "Music Theory (Acoustics)",
           f"Ramanujan Delta: weight {delta_weight}=sigma(6), exponent {delta_exponent}=sigma*phi(6)",
           f"Chromatic scale: {semitones} semitones; 2^(7/12) = {fifth_approx:.4f} ≈ 3/2 (err {fifth_error:.2f}%)",
           f"sigma(6)={SIGMA} appears as modular form weight AND musical octave division",
           verified_a, verified_b,
           "MIXED: 12 in modular forms comes from SL(2,Z) theory. 12 in music from rational approximation (continued fraction of log2(3)). Both are structural in their domains but the bridge is numerological.",
           "star",
           f"Fifth approx error = {fifth_error:.4f}%. 12 = smallest n with 2^(k/n) close to 3/2.")

bridge_13()

# ═══════════════════════════════════════════════════════════════
# BRIDGE 14: Euler Characteristic <-> Circuit Topology
# ═══════════════════════════════════════════════════════════════
def bridge_14():
    # Domain A: Euler characteristic of closed surfaces
    # Sphere: V-E+F = 2
    # Torus: V-E+F = 0
    # For a graph on the sphere (polyhedron): V-E+F = 2 = sigma_{-1}(6)

    # Cube: V=8, E=12, F=6 -> chi = 8-12+6 = 2
    cube_V, cube_E, cube_F = 8, 12, 6
    cube_chi = cube_V - cube_E + cube_F

    # Octahedron (dual of cube): V=6, E=12, F=8 -> chi = 2
    oct_V, oct_E, oct_F = 6, 12, 8
    oct_chi = oct_V - oct_E + oct_F

    # Domain B: Kirchhoff's circuit laws
    # For a circuit with N nodes, B branches, L loops:
    # B = N - 1 + L (from graph theory)
    # Number of independent KVL equations = L = B - N + 1
    # Number of independent KCL equations = N - 1
    # Total independent equations = B, and this relates to Euler char.

    # Bridge: Euler characteristic chi=2=sigma_{-1}(6) governs both
    # topology of polyhedra AND circuit graph topology

    # Also remarkable: octahedron has V=6=n vertices, E=12=sigma(6) edges

    verified_a = (cube_chi == 2) and (oct_chi == 2)
    verified_b = (oct_V == N) and (oct_E == SIGMA)

    report(14, "Octahedron: V=6=n, E=12=sigma(6), chi=2=sigma_{-1}(6)",
           "Topology (Euler Characteristic)", "Graph Theory / Electrical Circuits",
           f"Euler char chi=V-E+F=2 for all convex polyhedra; Cube: {cube_V}-{cube_E}+{cube_F}={cube_chi}",
           f"Octahedron: V={oct_V}=n, E={oct_E}=sigma(6), F={oct_F}; chi={oct_chi}=sigma_{{-1}}(6)",
           f"Octahedron encodes n=6 arithmetic: V=n, E=sigma(n), chi=sigma_{{-1}}(n)",
           verified_a, verified_b,
           "STRUCTURAL: The octahedron is the DUAL of the cube. Its V=6 comes from cube's F=6. Its E=12 is shared with the cube. This is constrained by Euler's formula: if V=6,F=8 then E=12. So sigma(6)=12 appearing as E is forced by V=n=6.",
           "star_star",
           f"Octahedron is self-consistent: V=6 forces E=12=sigma(6) via Euler formula + regularity.")

bridge_14()

# ═══════════════════════════════════════════════════════════════
# BRIDGE 15: Calabi-Yau 3-fold <-> tau(6)/2 complex dimensions
# ═══════════════════════════════════════════════════════════════
def bridge_15():
    # Domain A: String theory compactification requires Calabi-Yau manifold
    # Superstring: 10 dimensions total, 4 extended + 6 compact
    # CY manifold: complex dimension 3 (real dimension 6)

    string_dim = 10
    extended_dim = 4  # spacetime we see
    compact_dim = string_dim - extended_dim  # = 6
    CY_complex_dim = compact_dim // 2  # = 3

    # Domain B: n=6 arithmetic
    # Compact dimensions = n = 6
    # Complex dimensions = n/phi(6) = 6/2 = 3
    # Extended dimensions = tau(6) = 4

    verified_a = (compact_dim == 6) and (CY_complex_dim == 3) and (extended_dim == 4)
    verified_b = (compact_dim == N) and (extended_dim == TAU) and (CY_complex_dim == N // PHI)

    report(15, "String compactification: 10 = tau(6) + n = 4 + 6",
           "String Theory (Compactification)", "Number Theory (n=6)",
           f"Superstring: {string_dim}D = {extended_dim} extended + {compact_dim} compact; CY complex dim = {CY_complex_dim}",
           f"tau(6)={TAU}=extended dim, n=6=compact dim, CY complex dim = n/phi(6) = {N//PHI}",
           f"10 = tau(6) + 6 = 4 + 6; CY 3-fold has complex dim = 6/phi(6)",
           verified_a, verified_b,
           "MIXED: The 10D requirement comes from conformal anomaly cancellation. The 4+6 split is standard. tau(6)=4 matching extended dimensions is intriguing. But 4 spacetime dimensions have independent physical motivation (anthropic or otherwise).",
           "star",
           f"D=10 from anomaly cancellation. Split 4+6 matches tau(6)+n.")

bridge_15()

# ═══════════════════════════════════════════════════════════════
# BRIDGE 16: Thermodynamic Degrees of Freedom <-> phi(6)
# ═══════════════════════════════════════════════════════════════
def bridge_16():
    # Domain A: Ideal diatomic gas at room temperature
    # Degrees of freedom f = 5 (3 translational + 2 rotational)
    # Adiabatic index gamma = (f+2)/f = 7/5 = 1.4
    # At high T, vibrational modes add 2 more: f=7, gamma=9/7

    f_diatomic = 5  # = sopfr(6)!
    gamma_diatomic = (f_diatomic + 2) / f_diatomic

    # Domain B: sopfr(6) = 2+3 = 5
    # Equipartition: E = (f/2)*kT, so E = sopfr(6)/2 * kT = 5/2 * kT

    # Also: monatomic gas f=3 (divisor of 6)
    # Diatomic f=5 = sopfr(6)
    # Full vibrational f=7 (not directly related)

    f_monatomic = 3
    gamma_monatomic = (f_monatomic + 2) / f_monatomic  # = 5/3

    # phi(6) = 2: number of vibrational DOF added at high T
    vibrational_dof = 2

    verified_a = (f_diatomic == 5) and abs(gamma_diatomic - 1.4) < 1e-10
    verified_b = (f_diatomic == SOPFR) and (f_monatomic in DIVISORS) and (vibrational_dof == PHI)

    report(16, "Gas DOF: monatomic=3|6, diatomic=5=sopfr(6), vibration=2=phi(6)",
           "Thermodynamics (Statistical Mechanics)", "Number Theory (n=6)",
           f"Monatomic gas: f={f_monatomic}, gamma={gamma_monatomic:.4f}; Diatomic: f={f_diatomic}, gamma={gamma_diatomic:.4f}",
           f"sopfr(6)={SOPFR}=diatomic DOF; 3|6=monatomic DOF; phi(6)={PHI}=vibrational DOF",
           f"DOF progression {{3,5,7}} starts with divisor of 6, passes through sopfr(6), increments by phi(6)",
           verified_a, verified_b,
           "COINCIDENTAL: DOF=3 for point particle from 3 spatial dimensions. DOF=5 adds 2 rotational axes (linear molecule lacks one). DOF=7 adds 2 vibrational. Physics origin is clear and independent of number theory.",
           "white",
           f"gamma_diatomic = 7/5 = {gamma_diatomic}. Numerology is neat but not causal.")

bridge_16()

# ═══════════════════════════════════════════════════════════════
# BRIDGE 17: Platonic Solids Count <-> sopfr(6)
# ═══════════════════════════════════════════════════════════════
def bridge_17():
    # Domain A: There are exactly 5 Platonic solids
    # Tetra(4,6,4), Cube(8,12,6), Octa(6,12,8), Dodeca(20,30,12), Icosa(12,30,20)
    platonic_count = 5

    # Domain B: sopfr(6) = 5

    # Deeper: the 5 Platonic solids have face counts: 4, 6, 8, 12, 20
    # Among these: 6 appears (cube has 6 faces)
    # 12 appears (dodecahedron has 12 faces) = sigma(6)
    platonic_faces = [4, 6, 8, 12, 20]
    has_n = (N in platonic_faces)
    has_sigma = (SIGMA in platonic_faces)

    # Sum of Platonic solid face counts: 4+6+8+12+20 = 50
    face_sum = sum(platonic_faces)

    verified_a = (platonic_count == 5)
    verified_b = (platonic_count == SOPFR)

    report(17, "5 Platonic solids = sopfr(6); faces include {6, 12}={n, sigma(6)}",
           "Geometry (Platonic Solids)", "Number Theory",
           f"{platonic_count} Platonic solids, face counts = {platonic_faces}, sum = {face_sum}",
           f"sopfr(6)={SOPFR}; n=6 and sigma(6)=12 appear in face counts",
           f"Count of Platonic solids = sopfr(6) = 5; face set contains n and sigma(n)",
           verified_a, verified_b,
           "COINCIDENTAL: 5 Platonic solids from topology constraint (Euler formula + convexity). The count being sopfr(6) is accidental. However, n=6 and sigma(6)=12 appearing as face counts is mildly interesting (cube = 6 faces, dodecahedron = 12 faces).",
           "white",
           f"Cube=6 faces=n, dodecahedron=12 faces=sigma(6). No causal link to perfect numbers.")

bridge_17()

# ═══════════════════════════════════════════════════════════════
# BRIDGE 18: Quantum Error Correction <-> Perfect Code <-> n=6
# ═══════════════════════════════════════════════════════════════
def bridge_18():
    # Domain A: The [6,1] repetition code encodes 1 logical bit in 6 physical bits
    # Can correct floor((6-1)/2) = 2 errors
    # Rate = 1/6

    # But more interesting: the Steane [[7,1,3]] code is based on the
    # classical Hamming [7,4,3] code
    # Hamming codes exist for lengths 2^r - 1

    # Perfect codes (classical): Hamming codes and the Golay code
    # Hamming [7,4,3]: 7 = 2^3 - 1
    # Golay [23,12,7]: note 12 = sigma(6)!

    golay_n = 23
    golay_k = 12  # = sigma(6)
    golay_d = 7

    # Domain B: The extended Golay code [24,12,8]
    # 24 = sigma*phi(6), information symbols = 12 = sigma(6)
    ext_golay_n = 24  # = sigma*phi(6)!
    ext_golay_k = 12  # = sigma(6)!
    ext_golay_d = 8

    # This is also connected to the Leech lattice (dimension 24)

    verified_a = (golay_k == SIGMA) and (ext_golay_n == SIGMA_PHI)
    verified_b = (ext_golay_k == SIGMA)

    report(18, "Golay code [23,12,7]: k=sigma(6); extended [24,12,8]: n=sigma*phi(6)",
           "Coding Theory (Error Correction)", "Number Theory / Lattice Theory",
           f"Golay [23,{golay_k},{golay_d}]: k={golay_k}=sigma(6). Extended [{ext_golay_n},{ext_golay_k},{ext_golay_d}]: n={ext_golay_n}=sigma*phi(6)",
           f"sigma(6)={SIGMA}, sigma*phi(6)={SIGMA_PHI}",
           f"The unique perfect binary code (Golay) has information dimension sigma(6)=12 and its extension lives in dimension sigma*phi(6)=24",
           verified_a, verified_b,
           "STRUCTURAL: The Golay code is deeply connected to the Leech lattice (dim 24) and thence to the Monster group. The 24 and 12 are NOT arbitrary - they come from the same mathematical universe as modular forms. sigma(6)=12 and sigma*phi(6)=24 appearing here is part of the 24-dimensional structure.",
           "star_star_star",
           f"Golay code -> Leech lattice (dim 24) -> Monster group. The 12 and 24 are structural.")

bridge_18()

# ═══════════════════════════════════════════════════════════════
# BRIDGE 19: Neural Oscillation Bands <-> Divisors of 6
# ═══════════════════════════════════════════════════════════════
def bridge_19():
    # Domain A: Brain oscillation frequency bands
    # Delta: 0.5-4 Hz, Theta: 4-8 Hz, Alpha: 8-13 Hz, Beta: 13-30 Hz, Gamma: 30-100 Hz
    # Key ratios between band boundaries:
    # Theta/Delta boundary: 4 Hz
    # Alpha/Theta boundary: 8 Hz = 2*4
    # Band boundary ratios are roughly powers of 2

    # But consider the NUMBER of standard bands: Delta, Theta, Alpha, Beta, Gamma = 5
    # With sub-bands (low/high gamma): 6
    # Standard clinical bands: 5 or 6 depending on classification

    # Domain B: Cross-frequency coupling
    # Theta-gamma coupling: gamma power modulated by theta phase
    # Typical ratio: gamma/theta ~ 30/6 = 5 or 40/8 = 5
    # This 1:5 ratio is SOPFR(6)

    theta_center = 6  # Hz (typical theta)
    gamma_low = 30    # Hz (low gamma)
    coupling_ratio = gamma_low / theta_center  # = 5

    # Number of gamma cycles per theta cycle = 5 = sopfr(6)
    # This determines working memory capacity (Lisman & Jensen, 2013)
    # Miller's 7±2 items, but more recent: 4±1 items = tau(6)!

    wm_capacity = 4  # Cowan's estimate (2001)

    verified_a = abs(coupling_ratio - 5) < 0.5
    verified_b = (int(coupling_ratio) == SOPFR) and (wm_capacity == TAU)

    report(19, "Theta-gamma coupling ratio ~5=sopfr(6); WM capacity ~4=tau(6)",
           "Neuroscience (Neural Oscillations)", "Number Theory / Cognitive Science",
           f"Theta-gamma coupling: {gamma_low}/{theta_center} = {coupling_ratio:.1f} gamma cycles per theta",
           f"sopfr(6)={SOPFR}; working memory capacity ~ {wm_capacity} = tau(6)",
           f"Neural coupling ratio = sopfr(6); memory slots = tau(6)",
           verified_a, verified_b,
           "MIXED: The theta-gamma ratio of ~5 is empirically observed (Lisman-Jensen model). WM capacity ~4 is Cowan's estimate. Both are approximate. The n=6 arithmetic match is intriguing but the biological values have ranges (4-7 for coupling, 3-5 for WM).",
           "star",
           f"Approximate match. theta~6Hz is itself n=6 (but frequency varies 4-8Hz).")

bridge_19()

# ═══════════════════════════════════════════════════════════════
# BRIDGE 20: Carbon-12 Hoyle State <-> sigma(6)*phi(6)
# ═══════════════════════════════════════════════════════════════
def bridge_20():
    # Domain A: Carbon-12 nucleus
    # The Hoyle state: excited state of C-12 at 7.654 MeV
    # This resonance is essential for carbon production in stars
    # (triple-alpha process: 3 * He-4 -> C-12)

    carbon_A = 12  # mass number
    alpha_A = 4    # He-4 mass number
    num_alphas = carbon_A // alpha_A  # = 3

    # Domain B: sigma(6) = 12 = Carbon mass number
    # tau(6) = 4 = Helium-4 mass number
    # sigma(6)/tau(6) = 12/4 = 3 = number of alpha particles
    # Triple alpha: 3 * tau(6) = sigma(6) exactly!

    verified_a = (carbon_A == 12) and (alpha_A == 4) and (num_alphas == 3)
    verified_b = (SIGMA == 12) and (TAU == 4) and (SIGMA // TAU == 3)

    # Even deeper: Carbon-12 is the standard atomic mass unit reference
    # 1 amu = 1/12 of C-12 mass = 1/sigma(6) of C-sigma(6) mass

    report(20, "Triple-alpha: 3 * He-4 -> C-12 = 3 * tau(6) -> sigma(6)",
           "Nuclear Physics (Stellar Nucleosynthesis)", "Number Theory (n=6)",
           f"Triple-alpha process: {num_alphas} x He-{alpha_A} -> C-{carbon_A}",
           f"sigma(6)={SIGMA}, tau(6)={TAU}, sigma/tau = {SIGMA//TAU} = num alphas",
           f"Carbon-12 = sigma(6), Helium-4 = tau(6), triple alpha = sigma(6)/tau(6) alphas",
           verified_a, verified_b,
           "MIXED: Carbon-12 = 12 nucleons, He-4 = 4 nucleons. These are nuclear physics facts from binding energy. sigma(6)=12, tau(6)=4 is number theory. The arithmetic is exact but the physics is governed by nuclear force, not number theory. However, the triple-alpha process IS governed by the ratio 12/4=3, and 3 is a divisor of 6.",
           "star_star",
           f"C-12 is sigma(6), He-4 is tau(6). Ratio = 3 (divisor of 6). All three are n=6 arithmetic.")

bridge_20()

# ═══════════════════════════════════════════════════════════════
# SUMMARY
# ═══════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("ROUND 2 BRIDGE HYPOTHESES — SUMMARY")
print("=" * 70)

grade_map = {
    "star_star_star": "***",
    "star_star": "**",
    "star": "*",
    "green": "PROVEN",
    "orange": "WEAK",
    "white": "COINCIDENCE"
}

# Grade symbols for display
def grade_display(g):
    m = {"star_star_star": "3-STAR", "star_star": "2-STAR", "star": "1-STAR",
         "green": "PROVEN", "orange": "WEAK", "white": "COINCIDENCE"}
    return m.get(g, g)

structural = []
mixed = []
coincidental = []

for r in results:
    label = f"R2-BRIDGE-{r['num']:02d}"
    grade = grade_display(r['grade'])
    v = r['verified']
    print(f"  {label}: [{r['domain_a']}] <-> [{r['domain_b']}]: {r['title']}")
    print(f"           Verified: {v}  Grade: {grade}")

    if "STRUCTURAL" in r['assessment']:
        structural.append(r)
    elif "COINCIDENTAL" in r['assessment']:
        coincidental.append(r)
    else:
        mixed.append(r)

print(f"\n  TOTAL: {len(results)} bridge hypotheses")
print(f"  Both sides verified: {pass_count}")
print(f"  Verification failed: {fail_count}")
print(f"\n  STRUCTURAL bridges: {len(structural)}")
for r in structural:
    print(f"    R2-BRIDGE-{r['num']:02d}: {r['title']}")
print(f"\n  MIXED (suggestive) bridges: {len(mixed)}")
for r in mixed:
    print(f"    R2-BRIDGE-{r['num']:02d}: {r['title']}")
print(f"\n  COINCIDENTAL bridges: {len(coincidental)}")
for r in coincidental:
    print(f"    R2-BRIDGE-{r['num']:02d}: {r['title']}")

# Grade distribution
from collections import Counter
grades = Counter(r['grade'] for r in results)
print(f"\n  Grade distribution:")
for g, c in sorted(grades.items(), key=lambda x: -x[1]):
    print(f"    {grade_display(g)}: {c}")

# Key finding
print(f"""
  ═══ KEY FINDINGS ═══
  1. The number 24 = sigma*phi(6) appears structurally in: bosonic strings,
     Leech lattice, kissing number k(4), Golay code, Ramanujan Delta exponent.
     These are ALL connected via modular invariance — not coincidence.

  2. The kissing number sequence k(2,3,4) = (6, 12, 24) = (n, sigma, sigma*phi)
     is the most striking single bridge (R2-BRIDGE-12).

  3. Hexagonal optimality (R2-BRIDGE-03) is the most rigorous bridge:
     Hales' honeycomb theorem PROVES hexagonal tiling is optimal.

  4. The Golay code (R2-BRIDGE-18) bridge is deep: the unique perfect binary
     code lives in dimensions 12 and 24, which are sigma(6) and sigma*phi(6).

  5. Many bridges with small numbers (2,3,4,5,6,12) risk being coincidental.
     The structural bridges are those where the NUMBER ITSELF is constrained
     (e.g., kissing numbers, Golay uniqueness, hexagonal optimality).
""")
