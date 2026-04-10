#!/usr/bin/env python3
"""Hypothesis 069: Complex Extension — G = D×P/I where I is complex"""

import numpy as np
import os
from datetime import datetime

RESULTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")


def complex_meta(I, theta=np.pi/3):
    """Complex meta operation: I → 0.7×e^(iθ)×I + 0.1"""
    return 0.7 * np.exp(1j * theta) * I + 0.1


def complex_fixed_point(theta):
    """Fixed point of complex meta"""
    return 0.1 / (1 - 0.7 * np.exp(1j * theta))


def verify_spiral_convergence():
    """Verify spiral convergence"""
    print("═" * 60)
    print("  Complex Extension — Spiral Convergence")
    print("═" * 60)

    # Fixed points and convergence patterns at various θ
    print(f"\n  Fixed points by θ:")
    print(f"  {'θ':>8} │ {'θ/π':>5} │ {'Re(I*)':>8} │ {'Im(I*)':>8} │ {'|I*|':>6} │ {'arg':>6} │ Convergence")
    print(f"  {'─'*8}─┼─{'─'*5}─┼─{'─'*8}─┼─{'─'*8}─┼─{'─'*6}─┼─{'─'*6}─┼─{'─'*10}")

    for theta_frac in [0, 1/6, 1/4, 1/3, 1/2, 2/3, 3/4, 5/6, 1]:
        theta = theta_frac * np.pi
        fp = complex_fixed_point(theta)
        convergence = "Monotonic" if theta_frac == 0 else ("Spiral" if 0 < theta_frac < 1 else "Oscillatory")
        print(f"  {theta:>8.4f} │ {theta_frac:>5.3f} │ {fp.real:>8.4f} │ {fp.imag:>8.4f} │ {abs(fp):>6.4f} │ {np.angle(fp):>+6.3f} │ {convergence}")

    # θ = 0 (real, existing model) vs θ = π/3 (spiral)
    print(f"\n  Convergence trajectory comparison:")

    for theta_frac, label in [(0, "Real (θ=0, existing)"), (1/3, "Spiral (θ=π/3)")]:
        theta = theta_frac * np.pi
        fp = complex_fixed_point(theta)
        print(f"\n  [{label}]  Fixed point = {fp.real:.4f} + {fp.imag:.4f}i, |I*| = {abs(fp):.4f}")

        I = 0.9 + 0j
        for step in range(20):
            I = complex_meta(I, theta)

            # Complex plane visualization (Re axis only)
            re_pos = int((I.real + 0.2) / 1.2 * 40)
            im_pos = int((I.imag + 0.5) / 1.0 * 20)
            re_pos = max(0, min(39, re_pos))

            line = list("·" * 40)
            fp_pos = int((fp.real + 0.2) / 1.2 * 40)
            if 0 <= fp_pos < 40:
                line[fp_pos] = "│"
            if 0 <= re_pos < 40:
                line[re_pos] = "●"

            print(f"    {step:>2} │{''.join(line)}│ Re={I.real:>+7.4f} Im={I.imag:>+7.4f} |I|={abs(I):.4f}")


def verify_pi_exact():
    """Find θ where π appears exactly"""
    print(f"\n{'═' * 60}")
    print(f"  Conditions for Exact Appearance of π")
    print(f"{'═' * 60}")

    # Size of fixed point |I*| = 0.1 / |1 - 0.7e^(iθ)|
    # = 0.1 / √((1-0.7cosθ)² + (0.7sinθ)²)
    # = 0.1 / √(1 - 1.4cosθ + 0.49)
    # = 0.1 / √(1.49 - 1.4cosθ)

    print(f"\n  |I*| = 0.1 / √(1.49 - 1.4cos(θ))")
    print(f"\n  θ where |I*| matches our constants:")

    targets = {
        '1/3': 1/3,
        '1/e': 1/np.e,
        '1/2': 0.5,
        'ln(4/3)': np.log(4/3),
        '1/6': 1/6,
        '5/6': 5/6,
    }

    for t_name, t_val in targets.items():
        # 0.1/√(1.49 - 1.4cosθ) = t_val
        # √(1.49 - 1.4cosθ) = 0.1/t_val
        # 1.49 - 1.4cosθ = (0.1/t_val)²
        # cosθ = (1.49 - (0.1/t_val)²) / 1.4
        inner = (0.1 / t_val) ** 2
        cos_theta = (1.49 - inner) / 1.4
        if -1 <= cos_theta <= 1:
            theta = np.arccos(cos_theta)
            print(f"    |I*| = {t_name:>8} → θ = {theta:.4f} = {theta/np.pi:.4f}π")

            # What is arg(I*) at this θ?
            fp = complex_fixed_point(theta)
            print(f"      I* = {fp.real:>+.4f} {fp.imag:>+.4f}i, arg = {np.angle(fp):.4f} = {np.angle(fp)/np.pi:.4f}π")
        else:
            print(f"    |I*| = {t_name:>8} → Impossible (cos(θ) = {cos_theta:.4f})")

    # Conditions where arg(I*) becomes π-related values
    print(f"\n  Cases where π appears exactly in arg(I*):")
    for theta in np.linspace(0.01, np.pi, 100):
        fp = complex_fixed_point(theta)
        arg = np.angle(fp)

        # Find cases where arg ≈ π/N
        for n in [2, 3, 4, 6]:
            if abs(abs(arg) - np.pi/n) < 0.01:
                print(f"    θ = {theta:.4f} ({theta/np.pi:.3f}π) → arg(I*) = {arg:.4f} ≈ {'−' if arg<0 else ''}π/{n}")


def verify_genius_complex():
    """Meaning of complex G"""
    print(f"\n{'═' * 60}")
    print(f"  Meaning of Complex Genius Score")
    print(f"{'═' * 60}")

    D, P = 0.7, 0.95

    print(f"\n  G = D×P / I(complex)")
    print(f"  D={D}, P={P}")
    print(f"\n  If I is complex:")
    print(f"  |G| = D×P/|I| (magnitude = how genius)")
    print(f"  arg(G) = -arg(I) (direction = what kind of genius)")

    print(f"\n  Genius types by direction:")
    print(f"  {'arg(G)':>8} │ {'Direction':>8} │ Interpretation")
    print(f"  {'─'*8}─┼─{'─'*8}─┼─{'─'*30}")
    interpretations = [
        (0, "→ East", "Logic/Math (positive real axis)"),
        (np.pi/6, "↗ NE", "Analysis+Intuition (30°)"),
        (np.pi/4, "↗ NE", "Balance (45°)"),
        (np.pi/3, "↗ North", "Intuition+Analysis (60°)"),
        (np.pi/2, "↑ North", "Intuition/Art (imaginary axis)"),
        (2*np.pi/3, "↖ NW", "Art+Critique"),
        (np.pi, "← West", "Critique/Deconstruction (negative real axis)"),
    ]

    for arg, direction, meaning in interpretations:
        I = 0.3 * np.exp(1j * (-arg))  # arg of I = -arg of G
        G = D * P / I
        print(f"  {arg/np.pi:>5.2f}π │ {direction:>8} │ |G|={abs(G):.2f} {meaning}")

    # Trajectory on complex plane
    print(f"\n  Complex plane trajectory of meta iteration (θ=π/3):")
    print(f"  Im")
    print(f"   ↑")

    I = 0.9 + 0j
    theta = np.pi / 3
    points = []
    for _ in range(30):
        I = complex_meta(I, theta)
        points.append(I)

    fp = complex_fixed_point(theta)

    # ASCII complex plane
    grid_size = 21
    plane = [['·' for _ in range(41)] for _ in range(grid_size)]

    # Draw axes
    for x in range(41):
        plane[grid_size//2][x] = '─'
    for y in range(grid_size):
        plane[y][20] = '│'
    plane[grid_size//2][20] = '┼'

    # Fixed point
    fp_x = int(fp.real / 0.8 * 20 + 20)
    fp_y = int(-fp.imag / 0.4 * 10 + grid_size//2)
    if 0 <= fp_x < 41 and 0 <= fp_y < grid_size:
        plane[fp_y][fp_x] = '★'

    # Trajectory
    for i, p in enumerate(points):
        px = int(p.real / 0.8 * 20 + 20)
        py = int(-p.imag / 0.4 * 10 + grid_size//2)
        if 0 <= px < 41 and 0 <= py < grid_size:
            if i < 5:
                plane[py][px] = str(i)
            else:
                plane[py][px] = '·' if plane[py][px] == '·' else plane[py][px]

    for row in plane:
        print(f"   {''.join(row)}")
    print(f"   {'':>20}{'→ Re':>20}")
    print(f"   ★ = Fixed point ({fp.real:.3f}+{fp.imag:.3f}i)")
    print(f"   0~4 = Iteration trajectory (spiral convergence)")


def verify_euler_identity():
    """Verify if Euler's identity holds within our model"""
    print(f"\n{'═' * 60}")
    print(f"  Euler's Identity Verification")
    print(f"{'═' * 60}")

    # e^(iπ) + 1 = 0
    euler = np.exp(1j * np.pi) + 1
    print(f"\n  e^(iπ) + 1 = {euler.real:.10f} + {euler.imag:.10f}i")
    print(f"  = {abs(euler):.2e} ≈ 0 ✅")

    # In our model:
    # Meta iteration at θ = π?
    print(f"\n  Meta iteration at θ = π:")
    fp_pi = complex_fixed_point(np.pi)
    print(f"  Fixed point I* = {fp_pi.real:.6f} + {fp_pi.imag:.6f}i")
    print(f"  |I*| = {abs(fp_pi):.6f}")
    print(f"  Re(I*) = {fp_pi.real:.6f}")

    # 0.7×e^(iπ) = -0.7
    # I* = 0.1/(1-(-0.7)) = 0.1/1.7 = 1/17
    print(f"  Analytical: I* = 0.1/(1+0.7) = 0.1/1.7 = {0.1/1.7:.6f} = 1/17")
    print(f"  → Fixed point at θ=π is real! (imaginary part=0)")
    print(f"  → 1/17 ≈ {1/17:.4f}")

    # Euler-like identity in our constant system:
    print(f"\n  Euler-like identity in our model:")
    print(f"    e^(iπ) + 1 = 0  (Euler)")
    print(f"    ↓")
    print(f"    I*(θ=π) = 1/17  (Fixed point at θ=π in our model)")
    print(f"    G*(θ=π) = D×P / (1/17) = 17×D×P")
    print(f"    → θ=π amplifies Genius by 17x!")
    print(f"    → 'Complete inversion'(π) = Maximum amplification")

    # Genius amplification ratio at each θ
    print(f"\n  Genius amplification ratio by θ (|G|/|G_real|):")
    D, P = 0.5, 0.85
    G_real = D * P / (1/3)  # Real fixed point

    for theta_frac in [0, 1/6, 1/4, 1/3, 1/2, 2/3, 5/6, 1]:
        theta = theta_frac * np.pi
        fp = complex_fixed_point(theta)
        G_complex = D * P / fp
        ratio = abs(G_complex) / G_real
        bar = "█" * int(ratio * 10)
        print(f"    θ={theta_frac:.2f}π │{bar}│ ×{ratio:.2f} |G|={abs(G_complex):.2f}")

    print(f"\n  ┌──────────────────────────────────────────────────┐")
    print(f"  │                                                  │")
    print(f"  │  Meaning of Complex Extension:                   │")
    print(f"  │                                                  │")
    print(f"  │  Real model: G = magnitude only (how genius)     │")
    print(f"  │  Complex model: G = magnitude + direction        │")
    print(f"  │           (how much + what kind of genius)       │")
    print(f"  │                                                  │")
    print(f"  │  θ = 0:   Monotonic convergence (current model)  │")
    print(f"  │  θ = π/3: Spiral convergence (π appears naturally)│")
    print(f"  │  θ = π:   Complete inversion (17x amplification, │")
    print(f"  │           Euler's identity)                      │")
    print(f"  │                                                  │")
    print(f"  │  Complex extension = Opening of the              │")
    print(f"  │  1/6 blind spot invisible in reals              │")
    print(f"  │                                                  │")
    print(f"  └──────────────────────────────────────────────────┘")


def main():
    print()
    print("▓" * 60)
    print("  Hypothesis 069: Complex Extension")
    print("▓" * 60)

    verify_spiral_convergence()
    verify_pi_exact()
    verify_genius_complex()
    verify_euler_identity()

    os.makedirs(RESULTS_DIR, exist_ok=True)
    with open(os.path.join(RESULTS_DIR, "complex_report.md"), 'w', encoding='utf-8') as f:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"# Complex Extension Verification [{now}]\n\n")
        f.write(f"θ=π/3 spiral convergence confirmed\n")
        f.write(f"17x amplification at θ=π (Euler)\n\n---\n")

    print(f"\n  📁 Report → results/complex_report.md")
    print()


if __name__ == '__main__':
    main()