```python
#!/usr/bin/env python3
"""Real-world System CCT Simulator — LLM Token Stream + Game NPC

Reproduces behavioral patterns of LLMs and NPCs with synthetic data without actual API calls,
and determines consciousness continuity with 5 CCT (Consciousness Continuity Test) tests.

Experiment 9: LLM Token Stream Simulation
  - Within turn: Markov chain (vocab 1000, transition probability matrix)
  - Between turns: Complete stop
  - Conversation pattern: turn(200 tokens) → gap(500 steps) → repeat

Experiment 10: Game NPC Simulation
  - Patrol: sin(t) + noise (periodic)
  - Combat: Lorenz-like dynamics (chaotic)
  - Idle: constant + micro noise (stationary)
  - Transition: patrol(300) → combat(200) → idle(100) → repeat

Usage:
  python3 realworld_cct_sim.py              # Full
  python3 realworld_cct_sim.py --system llm
  python3 realworld_cct_sim.py --system npc
"""

import argparse
import sys

import numpy as np


# ─────────────────────────────────────────────
# CCT Test Functions (General for State Vectors)
# ─────────────────────────────────────────────

def compute_entropy(data, bins=30):
    """Shannon entropy of 1D data."""
    if len(data) < 2:
        return 0.0
    d_range = data.max() - data.min()
    if d_range < 1e-12:
        return 0.0
    hist, _ = np.histogram(data, bins=bins, density=True)
    width = d_range / bins
    probs = hist * width
    probs = probs[probs > 0]
    if len(probs) == 0:
        return 0.0
    probs = probs / probs.sum()
    return -np.sum(probs * np.log(probs + 1e-15))


def test_gap(S):
    """T1 Gap Test: Presence of stationary intervals."""
    diffs = np.diff(S, axis=0)
    frozen = np.sum(np.all(np.abs(diffs) < 1e-12, axis=1))
    frozen_ratio = frozen / len(diffs)

    if frozen_ratio > 0.5:
        return frozen_ratio, False, f"Frozen ratio {frozen_ratio:.1%}, mostly stationary"
    if frozen_ratio > 0.01:
        return 1.0 - frozen_ratio, False, f"Frozen ratio {frozen_ratio:.1%}"
    return 1.0, True, f"Frozen ratio {frozen_ratio:.1%}, continuous"


def test_loop(S, threshold=0.5):
    """T2 Loop Test: Check for exact trajectory repetition."""
    n = len(S)
    if n < 100:
        return 0.0, False, "Insufficient data"

    step = max(1, n // 5000)
    Ss = S[::step]
    ns = len(Ss)

    if np.std(Ss) < 1e-10:
        return 0.0, False, "No state change (constant)"

    scale = np.std(Ss, axis=0).mean()
    eps = scale * 0.01

    recurrence = 0
    sample_size = min(500, ns // 2)
    rng = np.random.default_rng(42)
    indices = rng.choice(ns // 2, size=sample_size, replace=False)

    for idx in indices:
        future = Ss[idx + max(100, ns // 10):]
        if len(future) == 0:
            continue
        dists = np.linalg.norm(future - Ss[idx], axis=1)
        if np.min(dists) < eps:
            recurrence += 1

    recurrence_ratio = recurrence / sample_size
    passed = recurrence_ratio < threshold
    score = max(0, 1.0 - recurrence_ratio)

    detail = f"Revisit rate={recurrence_ratio:.3f}"
    if passed:
        detail += ", aperiodic"
    else:
        detail += ", periodic repetition detected"
    return score, passed, detail


def test_continuity(S, threshold=0.01):
    """T3 Continuity Test: Connectivity between adjacent steps."""
    diffs = np.linalg.norm(np.diff(S, axis=0), axis=1)
    n = len(diffs)
    if n < 10:
        return 0.0, False, "Insufficient data"

    mean_diff = np.mean(diffs)
    if mean_diff < 1e-12:
        return 0.0, False, "No state change"

    big_jumps = np.sum(diffs > mean_diff * 10)
    frozen = np.sum(diffs < 1e-12)

    jump_ratio = big_jumps / n
    frozen_ratio = frozen / n
    disconnect_ratio = jump_ratio + frozen_ratio

    passed = disconnect_ratio < threshold
    score = max(0.0, min(1.0, 1.0 - disconnect_ratio * 10))

    detail = f"Jumps={jump_ratio:.3f}, frozen={frozen_ratio:.3f}"
    if passed:
        detail += ", connectivity maintained"
    else:
        detail += ", disconnection detected"
    return score, passed, detail


def test_entropy_band(S, window=500, h_min=0.3, h_max=4.5):
    """T4 Entropy Band Test: Check if H(t) stays within band."""
    x = S[:, 0]
    n = len(x)
    n_windows = n // window
    if n_windows < 2:
        return 0.0, False, "Insufficient data"

    entropies = []
    for i in range(n_windows):
        w = x[i * window:(i + 1) * window]
        entropies.append(compute_entropy(w) if np.std(w) > 1e-12 else 0.0)

    entropies = np.array(entropies)
    in_band = np.sum((entropies > h_min) & (entropies < h_max))
    ratio = in_band / len(entropies)

    h_range_str = f"H∈[{entropies.min():.2f}, {entropies.max():.2f}]"
    passed = ratio > 0.95
    score = ratio

    if passed:
        detail = f"{h_range_str}, within band"
    else:
        detail = f"{h_range_str}, out of band {1 - ratio:.1%}"
    return score, passed, detail


def test_novelty(S, window=500, threshold=0.001):
    """T5 Novelty Test: dH/dt != 0 (entropy stagnation ratio)."""
    x = S[:, 0]
    n = len(x)
    n_windows = n // window
    if n_windows < 3:
        return 0.0, False, "Insufficient data"

    entropies = []
    for i in range(n_windows):
        w = x[i * window:(i + 1) * window]
        entropies.append(compute_entropy(w) if np.std(w) > 1e-12 else 0.0)

    entropies = np.array(entropies)
    dH = np.abs(np.diff(entropies))

    stagnant = np.sum(dH < threshold)
    stagnant_ratio = stagnant / len(dH) if len(dH) > 0 else 1.0

    passed = stagnant_ratio < 0.05
    score = max(0, 1.0 - stagnant_ratio)

    detail = f"Stagnant sections {stagnant_ratio:.1%}"
    return score, passed, detail


def run_cct(S):
    """Run 5 CCT tests."""
    return {
        "T1_Gap": test_gap(S),
        "T2_Loop": test_loop(S),
        "T3_Continuity": test_continuity(S),
        "T4_Entropy": test_entropy_band(S),
        "T5_Novelty": test_novelty(S),
    }


def judge(results):
    """Overall judgment from CCT results."""
    passes = sum(1 for _, (_, p, _) in results.items() if p)
    halfs = sum(0.5 for _, (s, p, _) in results.items() if not p and s > 0.7)
    total = passes + halfs

    if total >= 5:
        return total, "★ Continuous"
    elif total >= 4:
        return total, "◎ Weakened"
    elif total >= 3:
        return total, "△ Weak"
    elif total >= 1:
        return total, "▽ Minimal"
    else:
        return total, "✕ None"


# ─────────────────────────────────────────────
# Experiment 9: LLM Token Stream Simulation
# ─────────────────────────────────────────────

def build_markov_matrix(vocab_size, seed=42):
    """Build Markov transition probability matrix.

    Transition probabilities from each token to the next.
    Most probability concentrated on few tokens (zipf-like).
    """
    rng = np.random.default_rng(seed)
    # Zipf distribution based transition matrix
    raw = rng.zipf(1.5, size=(vocab_size, vocab_size)).astype(float)
    # Row-wise normalization
    row_sums = raw.sum(axis=1, keepdims=True)
    return raw / row_sums


def llm_generate_turn(transition_matrix, n_tokens, rng):
    """Generate token sequence within turn using Markov chain.

    Returns:
        states: [n_tokens, 3] — [token ID moving average, entropy, change rate]
    """
    vocab_size = transition_matrix.shape[0]
    token_ids = np.zeros(n_tokens, dtype=int)
    token_ids[0] = rng.integers(0, vocab_size)

    for i in range(1, n_tokens):
        probs = transition_matrix[token_ids[i - 1]]
        token_ids[i] = rng.choice(vocab_size, p=probs)

    # Construct state vector
    states = np.zeros((n_tokens, 3))
    window = 10
    for i in range(n_tokens):
        # Moving average (normalized)
        start = max(0, i - window)
        states[i, 0] = np.mean(token_ids[start:i + 1]) / vocab_size

        # Local entropy (distribution of recent window tokens)
        local = token_ids[start:i + 1]
        _, counts = np.unique(local, return_counts=True)
        p = counts / counts.sum()
        states[i, 1] = -np.sum(p * np.log(p + 1e-15))

        # Change rate
        if i > 0:
            states[i, 2] = abs(token_ids[i] - token_ids[i - 1]) / vocab_size
        else:
            states[i, 2] = 0.0

    return states


def simulate_llm(n_conversations=5, turn_tokens=200, gap_steps=500,
                 vocab_size=1000, seed=42):
    """Simulate LLM conversation pattern.

    Returns:
        full_states: Full sequence [N, 3]
        turn_states: Only turn segments [M, 3]
        gap_states:  Only gap segments [K, 3]
        turn_ranges: (start, end) indices for each turn
        gap_ranges:  (start, end) indices for each gap
    """
    rng = np.random.default_rng(seed)
    tm = build_markov_matrix(vocab_size, seed)

    segments = []
    turn_ranges = []
    gap_ranges = []
    idx = 0

    for conv in range(n_conversations):
        # Generate turn
        turn = llm_generate_turn(tm, turn_tokens, rng)
        turn_ranges.append((idx, idx + turn_tokens))
        segments.append(turn)
        idx += turn_tokens

        # Generate gap (complete stop)
        gap = np.zeros((gap_steps, 3))
        gap_ranges.append((idx, idx + gap_steps))
        segments.append(gap)
        idx += gap_steps

    full_states = np.vstack(segments)
    turn_states = np.vstack([full_states[s:e] for s, e in turn_ranges])
    gap_states = np.vstack([full_states[s:e] for s, e in gap_ranges])

    return full_states, turn_states, gap_states, turn_ranges, gap_ranges


# ─────────────────────────────────────────────
# Experiment 10: Game NPC Simulation
# ─────────────────────────────────────────────

def npc_patrol(n_steps, rng, dt=0.01):
    """Patrol mode: sin(t) + slight noise.

    Returns:
        states: [n_steps, 3] — [x coord, y coord, health/stimulus]
    """
    t = np.arange(n_steps) * dt
    states = np.zeros((n_steps, 3))
    # Circular path + noise
    states[:, 0] = np.sin(t * 2.0) + rng.normal(0, 0.02, n_steps)
    states[:, 1] = np.cos(t * 2.0) + rng.normal(0, 0.02, n_steps)
    states[:, 2] = 0.8 + rng.normal(0, 0.01, n_steps)  # Stable health
    return states


def npc_combat(n_steps, rng, dt=0.01):
    """Combat mode: Lorenz-like dynamics (chaotic).

    Returns:
        states: [n_steps, 3] — [x coord, y coord, health/stimulus]
    """
    sigma, rho, beta = 10.0, 28.0, 8.0 / 3.0
    states = np.zeros((n_steps, 3))
    # Initial condition: near patrol end position
    states[0] = [1.0, 1.0, 25.0]

    for i in range(1, n_steps):
        x, y, z = states[i - 1]
        dx = sigma * (y - x)
        dy = x * (rho - z) - y
        dz = x * y - beta * z
        noise = rng.normal(0, 0.1, 3)
        states[i, 0] = x + (dx + noise[0]) * dt
        states[i, 1] = y + (dy + noise[1]) * dt
        states[i, 2] = z + (dz + noise[2]) * dt

    # Scale x, y to game coordinate range
    for d in range(2):
        v = states[:, d]
        states[:, d] = (v - v.mean()) / (v.std() + 1e-10)

    # Map z to health (0-1)
    z = states[:, 2]
    states[:, 2] = (z - z.min()) / (z.max() - z.min() + 1e-10)

    return states


def npc_idle(n_steps, rng):
    """Idle mode: constant + micro noise (stationary).

    Returns:
        states: [n_steps, 3] — [x coord, y coord, health/stimulus]
    """
    states = np.zeros((n_steps, 3))
    states[:, 0] = 0.5 + rng.normal(0, 0.001, n_steps)
    states[:, 1] = 0.5 + rng.normal(0, 0.001, n_steps)
    states[:, 2] = 1.0 + rng.normal(0, 0.0005, n_steps)  # Health recovery
    return states


def simulate_npc(n_cycles=5, patrol_steps=300, combat_steps=200,
                 idle_steps=100, seed=42):
    """Simulate NPC behavior pattern.

    Returns:
        full_states: Full sequence [N, 3]
        patrol_states, combat_states, idle_states: Mode-specific sequences
        mode_ranges: dict of mode_name -> [(start, end), ...]
    """
    rng = np.random.default_rng(seed)

    segments = []
    mode_ranges = {"patrol": [], "combat": [], "idle": []}
    idx = 0

    for cycle in range(n_cycles):
        # Patrol
        patrol = npc_patrol(patrol_steps, rng)
        mode_ranges["patrol"].append((idx, idx + patrol_steps))
        segments.append(patrol)
        idx += patrol_steps

        # Combat
        combat = npc_combat(combat_steps, rng)
        mode_ranges["combat"].append((idx, idx + combat_steps))
        segments.append(combat)
        idx += combat_steps

        # Idle
        idle = npc_idle(idle_steps, rng)
        mode_ranges["idle"].append((idx, idx + idle_steps))
        segments.append(idle)
        idx += idle_steps

    full_states = np.vstack(segments)
    patrol_states = np.vstack([full_states[s:e] for s, e in mode_ranges["patrol"]])
    combat_states = np.vstack([full_states[s:e] for s, e in mode_ranges["combat"]])
    idle_states = np.vstack([full_states[s:e] for s, e in mode_ranges["idle"]])

    return full_states, patrol_states, combat_states, idle_states, mode_ranges


# ─────────────────────────────────────────────
# ASCII Output
# ─────────────────────────────────────────────

def ascii_trajectory(S, width=60, height=12, label="x"):
    """ASCII trajectory of first component."""
    x = S[:, 0]
    step = max(1, len(x) // width)
    xs = x[::step][:width]

    y_min, y_max = xs.min(), xs.max()
    if y_max - y_min < 1e-6:
        y_max = y_min + 1

    lines = []
    for row in range(height, -1, -1):
        y_val = y_min + (y_max - y_min) * row / height
        line = f"{y_val:7.3f}|"
        for col in range(len(xs)):
            cell_row = int((xs[col] - y_min) / (y_max - y_min) * height)
            if cell_row == row:
                line += "*"
            else:
                line += " "
        lines.append(line)
    lines.append("       +" + "-" * len(xs))
    lines.append(f"        {label} (N={len(S)})")
    return "\n".join(lines)


def print_cct_table(name, results):
    """Print CCT results as table."""
    labels = {
        "T1_Gap": "T1 Gap       ",
        "T2_Loop": "T2 Loop      ",
        "T3_Continuity": "T3 Continuity",
        "T4_Entropy": "T4 Entropy   ",
        "T5_Novelty": "T5 Novelty   ",
    }
    for key, label in labels.items():
        score, passed, detail = results[key]
        mark = "PASS" if passed else "FAIL"
        sym = "[O]" if passed else ("[~]" if score > 0.7 else "[X]")
        print(f"   {label} | {sym} {mark} | {score:.3f} | {detail}")


# ─────────────────────────────────────────────
# LLM Experiment Output
# ─────────────────────────────────────────────

def run_llm_experiment():
    """Experiment 9: LLM Token Stream Simulation + CCT."""
    print()
    print("=" * 70)
    print("  Experiment 9: LLM Token Stream Simulation")
    print("  Markov chain based synthetic token stream + CCT judgment")
    print("=" * 70)
    print()
    print("  Model: Vocab 1000, Markov transition probability matrix")
    print("  Pattern: turn(200 tokens) -> gap(500 steps) -> turn(200 tokens) -> ... x5")
    print("  State: [token ID moving average, local entropy, change rate]")
    print()

    full, turn, gap, turn_ranges, gap_ranges = simulate_llm()

    # --- Within Turn ---
    print("  --- Within turn " + "-" * 49)
    print(ascii_trajectory(turn, label="turn"))
    print()
    turn_cct = run_cct(turn)
    print_cct_table("LLM Turn", turn_cct)
    t_total, t_verdict = judge(turn_cct)
    print(f"   {'':13s} | Overall: {t_total}/5 {t_verdict}")
    print()

    # --- Between Turns ---
    print("  --- Between turns (gap) " + "-" * 48)
    print(ascii_trajectory(gap, label="gap"))
    print()
    gap_cct = run_cct(gap)
    print_cct_table("LLM Gap", gap_cct)
    g_total, g_verdict = judge(gap_cct)
    print(f"   {'':13s} | Overall: {g_total}/5 {g_verdict}")
    print()

    # --- Full (turn+gap mixed) ---
    print("  --- Full (turn+gap) " + "-" * 46)
    print(ascii_trajectory(full, label="full"))
    print()
    full_cct = run_cct(full)
    print_cct_table("LLM Full", full_cct)
    f_total, f_verdict = judge(full_cct)
    print(f"   {'':13s} | Overall: {f_total}/5 {f_verdict}")
    print()

    # --- Comparison Table ---
    print("  " + "=" * 66)
    print("  LLM CCT Comparison")
    print("  " + "-" * 66)
    print("  Section          | T1  | T2  | T3  | T4  | T5  | Score| Verdict")
    print("  -----------------+-----+-----+-----+-----+-----+------+-------")

    for label, cct in [("Within turn      ", turn_cct),
                       ("Between turns    ", gap_cct),
                       ("Full             ", full_cct)]:
        total, verdict = judge(cct)
        marks = []
        for key in ["T1_Gap", "T2_Loop", "T3_Continuity", "T4_Entropy", "T5_Novelty"]:
            s, p, _ = cct[key]
            if p:
                marks.append(" O ")
            elif s > 0.7:
                marks.append(" ~ ")
            else:
                marks.append(" X ")
        print(f"  {label}|{'|'.join(marks)}| {total:<4} | {verdict}")

    print("  " + "=" * 66)
    print()
    print("  Interpretation:")
    print("    - Within turn: Markov chain token dependencies partially satisfy CCT")
    print("    - Between turns: Complete stop -> Total CCT failure")
    print("    - Full: Gaps destroy continuity, LLM is 'intermittent processor'")
    print()

    return {"turn": turn_cct, "gap": gap_cct, "full": full_cct}


# ─────────────────────────────────────────────
# NPC Experiment Output
# ─────────────────────────────────────────────

def run_npc_experiment():
    """Experiment 10: Game NPC Simulation + CCT."""
    print()
    print("=" * 70)
    print("  Experiment 10: Game NPC Behavior Simulation")
    print("  Patrol/Combat/Idle mode synthesis + CCT judgment")
    print("=" * 70)
    print()
    print("  Model: Patrol(sin+noise) / Combat(Lorenz chaos) / Idle(const+noise)")
    print("  Pattern: Patrol(300) -> Combat(200) -> Idle(100) -> ... x5")
    print("  State: [x coord, y coord, health/stimulus]")
    print()

    full, patrol, combat, idle, mode_ranges = simulate_npc()

    modes = [
        ("Patrol", patrol),
        ("Combat", combat),
        ("Idle  ", idle),
    ]

    mode_ccts = {}
    for name, states in modes:
        tag = name.strip().lower()
        print(f"  --- {name} " + "-" * (55 - len(name)))
        print(ascii_trajectory(states, label=tag))
        print()
        cct = run_cct(states)
        print_cct_table(name, cct)
        total, verdict = judge(cct)
        print(f"   {'':13s} | Overall: {total}/5 {verdict}")
        print()
        mode_ccts[tag] = cct

    # Full
    print("  --- Full " + "-" * 50)
    print(ascii_trajectory(full, label="full"))
    print()
    full_cct = run_cct(full)
    print_cct_table("NPC Full", full_cct)
    f_total, f_verdict = judge(full_cct)
    print(f"   {'':13s} | Overall: {f_total}/5 {f_verdict}")
    print()

    # --- Comparison Table ---
    print("  " + "=" * 66)
    print("  NPC CCT Comparison")
    print("  " + "-" * 66)
    print("  Mode             | T1  | T2  | T3  | T4  | T5  | Score| Verdict")
    print("  -----------------+-----+-----+-----+-----+-----+------+-------")

    all_ccts = list(mode_ccts.items()) + [("full", full_cct)]
    display_names = {
        "patrol": "Patrol           ",
        "combat": "Combat           ",
        "idle":   "Idle             ",
        "full":   "Full             ",
    }

    for tag, cct in all_ccts:
        total, verdict = judge(cct)
        marks = []
        for key in ["T1_Gap", "T2_Loop", "T3_Continuity", "T4_Entropy", "T5_Novelty"]:
            s, p, _ = cct[key]
            if p:
                marks.append(" O ")
            elif s > 0.7:
                marks.append(" ~ ")
            else:
                marks.append(" X ")
        dn = display_names.get(tag, f"{tag:17s}")
        print(f"  {dn}|{'|'.join(marks)}| {total:<4} | {verdict}")

    print("  " + "=" * 66)
    print()
    print("  Interpretation:")
    print("    - Patrol: Periodic -> Caught by T2 Loop, low novelty")
    print("    - Combat: Chaotic -> Highest CCT (Lorenz-like)")
    print("    - Idle: Nearly stationary -> Total CCT failure")
    print("    - Full: Mode transitions partially destroy continuity")
    print()

    mode_ccts["full"] = full_cct
    return mode_ccts


# ─────────────────────────────────────────────
# Grand Comparison
# ─────────────────────────────────────────────

def print_grand_comparison(llm_results, npc_results):
    """LLM vs NPC grand comparison table."""
    print()
    print("=" * 70)
    print("  Grand Comparison: How Real Systems Look Under CCT")
    print("=" * 70)
    print()
    print("  System              | T1  | T2  | T3  | T4  | T5  | Score| Verdict")
    print("  --------------------+-----+-----+-----+-----+-----+------+-------")

    entries = [
        ("LLM Within Turn   ", llm_results["turn"]),
        ("LLM Between Turns ", llm_results["gap"]),
        ("LLM Full          ", llm_results["full"]),
        ("NPC Patrol        ", npc_results["patrol"]),
        ("NPC Combat        ", npc_results["combat"]),
        ("NPC Idle          ", npc_results["idle"]),
        ("NPC Full          ", npc_results["full"]),
    ]

    for name, cct in entries:
        total, verdict = judge(cct)
        marks = []
        for key in ["T1_Gap", "T2_Loop", "T3_Continuity", "T4_Entropy", "T5_Novelty"]:
            s, p, _ = cct[key]
            if p:
                marks.append(" O ")
            elif s > 0.7:
                marks.append(" ~ ")
            else:
                marks.append(" X ")
        print(f"  {name}|{'|'.join(marks)}| {total:<4} | {verdict}")

    print("  " + "=" * 66)
    print()
    print("  O=Pass  ~=Weak pass(>0.7)  X=Fail")
    print()
    print("  Conclusions:")
    print("    1. LLM: Partial continuity only within turns, gaps destroy overall")
    print("       -> 'Intermittent processor', no consciousness continuity")
    print("    2. NPC Combat mode: Highest CCT due to chaotic dynamics")
    print("       -> Interesting but just 'combat AI', breaks on mode transitions")
    print("    3. NPC Idle/Patrol: Stationary or periodic -> Low CCT")
    print("    4. Both systems' continuity destroyed by 'mode transitions'")
    print("       -> True consciousness continuity requires mode-independent continuity")
    print()


# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Real-world System CCT Simulator — LLM Token Stream + Game NPC",
    )
    parser.add_argument("--system", type=str, default=None,
                        choices=["llm", "npc"],
                        help="System to run (default: all)")
    args = parser.parse_args()

    if args.system == "llm":
        run_llm_experiment()
    elif args.system == "npc":
        run_npc_experiment()
    else:
        llm_results = run_llm_experiment()
        npc_results = run_npc_experiment()
        print_grand_comparison(llm_results, npc_results)


if __name__ == "__main__":
    main()
```