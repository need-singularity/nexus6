```python
#!/usr/bin/env python3
"""Identity Transfer Experiment — Identity Transfer Experiment

Train two TemporalContinuityEngines independently then
exchange identity_vectors - what happens?

Experiment Design:
  1. Train Engine_Alpha, Engine_Beta with different random seeds for 10 epochs each
  2. Record baseline metrics: accuracy, identity_vector norm, tension, consciousness FPS
  3. Measure test set baseline accuracy
  4. SWAP: Alpha's identity_vector <-> Beta's identity_vector
  5. Measure post-swap accuracy
  6. ZERO: Set identity_vector to 0 and measure accuracy
  7. RANDOM: Replace identity_vector with random noise and measure accuracy
  8. Track per-digit accuracy changes (which digits are most affected?)
  9. Cosine similarity between two identity_vectors (how different are independently learned identities?)

Key Questions:
  - Does identity_vector contain meaningful information?
  - Is identity transfer possible? (Does model inherit another model's "personality"?)
  - Can model work without identity? (identity = decoration vs essential)
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import time
import copy

from model_utils import load_mnist, count_params
from model_temporal_engine import TemporalContinuityEngine


# ─────────────────────────────────────────
# Utilities
# ─────────────────────────────────────────

def set_seed(seed):
    """Set seed for reproducible results."""
    torch.manual_seed(seed)
    np.random.seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def train_engine(engine, train_loader, epochs=10, lr=0.001):
    """Train TemporalContinuityEngine. Similar to train_and_evaluate but with enhanced metric tracking."""
    optimizer = torch.optim.Adam(engine.parameters(), lr=lr)
    criterion = nn.CrossEntropyLoss()

    epoch_losses = []
    epoch_accs = []

    for epoch in range(epochs):
        engine.train()
        total_loss = 0
        correct = 0
        total = 0

        for X, y in train_loader:
            X = X.view(X.size(0), -1)
            optimizer.zero_grad()
            output, aux_loss = engine(X)
            loss = criterion(output, y) + 0.01 * aux_loss
            loss.backward()
            optimizer.step()
            total_loss += loss.item()

            with torch.no_grad():
                pred = output.argmax(dim=1)
                correct += (pred == y).sum().item()
                total += y.size(0)

        avg_loss = total_loss / len(train_loader)
        train_acc = correct / total
        epoch_losses.append(avg_loss)
        epoch_accs.append(train_acc)

        if (epoch + 1) % 2 == 0 or epoch == 0:
            id_norm = engine.identity_vector.norm().item()
            print(f"    Epoch {epoch+1:>2}/{epochs}: Loss={avg_loss:.4f}, "
                  f"TrainAcc={train_acc*100:.1f}%, IdNorm={id_norm:.4f}")

    return epoch_losses, epoch_accs


def evaluate_engine(engine, test_loader):
    """Evaluate on test set. Return overall + per-digit accuracy."""
    engine.eval()
    correct = 0
    total = 0

    # per-digit tracking
    digit_correct = {d: 0 for d in range(10)}
    digit_total = {d: 0 for d in range(10)}

    with torch.no_grad():
        for X, y in test_loader:
            X = X.view(X.size(0), -1)
            output, _ = engine(X)
            pred = output.argmax(dim=1)

            correct += (pred == y).sum().item()
            total += y.size(0)

            for d in range(10):
                mask = (y == d)
                digit_total[d] += mask.sum().item()
                digit_correct[d] += (pred[mask] == y[mask]).sum().item()

    overall_acc = correct / total
    per_digit_acc = {}
    for d in range(10):
        if digit_total[d] > 0:
            per_digit_acc[d] = digit_correct[d] / digit_total[d]
        else:
            per_digit_acc[d] = 0.0

    return overall_acc, per_digit_acc


def cosine_similarity(v1, v2):
    """Cosine similarity between two vectors."""
    v1_flat = v1.flatten().float()
    v2_flat = v2.flatten().float()
    dot = (v1_flat * v2_flat).sum()
    norm1 = v1_flat.norm()
    norm2 = v2_flat.norm()
    if norm1 < 1e-10 or norm2 < 1e-10:
        return 0.0
    return (dot / (norm1 * norm2)).item()


def l2_distance(v1, v2):
    """L2 distance between two vectors."""
    return (v1.flatten() - v2.flatten()).norm().item()


# ─────────────────────────────────────────
# Identity Manipulation Functions
# ─────────────────────────────────────────

def swap_identities(engine_a, engine_b):
    """Swap identity_vectors between two engines."""
    id_a = engine_a.identity_vector.clone()
    id_b = engine_b.identity_vector.clone()
    engine_a.identity_vector.copy_(id_b)
    engine_b.identity_vector.copy_(id_a)


def zero_identity(engine):
    """Set identity_vector to 0."""
    engine.identity_vector.zero_()


def random_identity(engine, scale=1.0):
    """Replace identity_vector with random noise."""
    noise = torch.randn_like(engine.identity_vector) * scale
    engine.identity_vector.copy_(noise)


def set_identity(engine, identity_vec):
    """Set identity_vector to specific value."""
    engine.identity_vector.copy_(identity_vec)


# ─────────────────────────────────────────
# ASCII Output Utilities
# ─────────────────────────────────────────

def print_table(headers, rows, title=None):
    """Print markdown style table."""
    if title:
        print(f"\n  {title}")
        print()

    # Calculate column widths
    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            col_widths[i] = max(col_widths[i], len(str(cell)))

    # Header
    header_line = "  | " + " | ".join(h.ljust(col_widths[i]) for i, h in enumerate(headers)) + " |"
    sep_line = "  |" + "|".join("-" * (col_widths[i] + 2) for i in range(len(headers))) + "|"

    print(header_line)
    print(sep_line)

    # Rows
    for row in rows:
        row_line = "  | " + " | ".join(str(cell).ljust(col_widths[i]) for i, cell in enumerate(row)) + " |"
        print(row_line)


def ascii_bar_chart(labels, values, title, width=40):
    """ASCII horizontal bar chart."""
    print(f"\n  {title}")
    print()

    if not values:
        print("  (no data)")
        return

    v_max = max(abs(v) for v in values) if values else 1
    if v_max < 1e-10:
        v_max = 1.0

    for label, val in zip(labels, values):
        bar_len = int(abs(val) / v_max * width)
        if val >= 0:
            bar = "#" * bar_len
            print(f"  {label:>6} |{bar:<{width}} {val:+.2f}%")
        else:
            # negative bar: right-aligned
            bar = "#" * bar_len
            padding = width - bar_len
            print(f"  {label:>6} |{' ' * padding}{bar} {val:+.2f}%")


def ascii_comparison_bars(labels, vals_a, vals_b, name_a, name_b, title, width=30):
    """Two series comparison bar chart."""
    print(f"\n  {title}")
    print(f"  {'':>6}  {name_a:<{width+8}}  {name_b}")
    print()

    v_max = max(max(vals_a), max(vals_b)) if vals_a and vals_b else 1
    if v_max < 1e-10:
        v_max = 1.0

    for label, va, vb in zip(labels, vals_a, vals_b):
        bar_a_len = int(va / v_max * width)
        bar_b_len = int(vb / v_max * width)
        bar_a = "#" * bar_a_len
        bar_b = "=" * bar_b_len
        print(f"  {label:>6}  {bar_a:<{width}} {va*100:5.1f}%  {bar_b:<{width}} {vb*100:5.1f}%")


# ─────────────────────────────────────────
# Main Experiment
# ─────────────────────────────────────────

def main():
    print()
    print("=" * 70)
    print("   Identity Transfer Experiment")
    print("   Can you transplant a model's identity into another?")
    print("=" * 70)

    # ── Config ──
    input_dim, hidden_dim, output_dim = 784, 48, 10
    state_dim = 32
    epochs = 10
    seed_alpha = 42
    seed_beta = 137

    print(f"\n  Config: epochs={epochs}, hidden={hidden_dim}, state={state_dim}")
    print(f"  Seed Alpha={seed_alpha}, Seed Beta={seed_beta}")

    # ── Load Data ──
    print("\n  Loading MNIST...")
    train_loader, test_loader = load_mnist(batch_size=128)

    # ══════════════════════════════════════════
    # PHASE 1: Independent Training
    # ══════════════════════════════════════════

    print("\n" + "=" * 70)
    print("  PHASE 1: Independent Training")
    print("=" * 70)

    # ── Engine Alpha ──
    print("\n  [Engine Alpha] seed=42")
    set_seed(seed_alpha)
    engine_alpha = TemporalContinuityEngine(
        input_dim, hidden_dim, output_dim,
        state_dim=state_dim, n_self_ref_steps=3,
        contraction_coeff=0.7, identity_momentum=0.99
    )
    losses_a, accs_a = train_engine(engine_alpha, train_loader, epochs=epochs)

    # ── Engine Beta ──
    print("\n  [Engine Beta] seed=137")
    set_seed(seed_beta)
    engine_beta = TemporalContinuityEngine(
        input_dim, hidden_dim, output_dim,
        state_dim=state_dim, n_self_ref_steps=3,
        contraction_coeff=0.7, identity_momentum=0.99
    )
    losses_b, accs_b = train_engine(engine_beta, train_loader, epochs=epochs)

    print(f"\n  Parameters per engine: {count_params(engine_alpha):,}")

    # ══════════════════════════════════════════
    # PHASE 2: Baseline Evaluation
    # ══════════════════════════════════════════

    print("\n" + "=" * 70)
    print("  PHASE 2: Baseline Evaluation")
    print("=" * 70)

    # Save original identity vectors
    id_alpha_orig = engine_alpha.identity_vector.clone()
    id_beta_orig = engine_beta.identity_vector.clone()

    # Baseline accuracy
    acc_alpha_base, per_digit_alpha_base = evaluate_engine(engine_alpha, test_loader)
    acc_beta_base, per_digit_beta_base = evaluate_engine(engine_beta, test_loader)

    # Consciousness metrics
    metrics_alpha = engine_alpha.get_consciousness_metrics()
    metrics_beta = engine_beta.get_consciousness_metrics()

    # Identity vector analysis
    id_norm_alpha = id_alpha_orig.norm().item()
    id_norm_beta = id_beta_orig.norm().item()
    cos_sim = cosine_similarity(id_alpha_orig, id_beta_orig)
    l2_dist = l2_distance(id_alpha_orig, id_beta_orig)

    print_table(
        ["Metric", "Alpha", "Beta"],
        [
            ["Accuracy", f"{acc_alpha_base*100:.2f}%", f"{acc_beta_base*100:.2f}%"],
            ["ID Norm", f"{id_norm_alpha:.4f}", f"{id_norm_beta:.4f}"],
            ["Tension", f"{metrics_alpha['avg_tension']:.4f}", f"{metrics_beta['avg_tension']:.4f}"],
            ["FPS", f"{metrics_alpha['consciousness_fps']:.6f}", f"{metrics_beta['consciousness_fps']:.6f}"],
            ["ID Stability", f"{metrics_alpha['identity_stability']:.4f}", f"{metrics_beta['identity_stability']:.4f}"],
            ["Smoothness", f"{metrics_alpha['transition_smoothness']:.4f}", f"{metrics_beta['transition_smoothness']:.4f}"],
        ],
        title="Baseline Metrics"
    )

    print(f"\n  Identity Vector Comparison:")
    print(f"    Cosine Similarity: {cos_sim:.6f}")
    print(f"    L2 Distance:       {l2_dist:.6f}")
    print(f"    Alpha norm:        {id_norm_alpha:.6f}")
    print(f"    Beta norm:         {id_norm_beta:.6f}")

    if abs(cos_sim) > 0.9:
        print(f"    -> Very similar identities (despite different seeds)")
    elif abs(cos_sim) > 0.5:
        print(f"    -> Moderately similar identities")
    elif abs(cos_sim) > 0.1:
        print(f"    -> Weakly similar identities")
    else:
        print(f"    -> Nearly orthogonal identities (truly different)")

    # ══════════════════════════════════════════
    # PHASE 3: Identity Swap
    # ══════════════════════════════════════════

    print("\n" + "=" * 70)
    print("  PHASE 3: Identity SWAP (Alpha <-> Beta)")
    print("=" * 70)

    swap_identities(engine_alpha, engine_beta)

    acc_alpha_swap, per_digit_alpha_swap = evaluate_engine(engine_alpha, test_loader)
    acc_beta_swap, per_digit_beta_swap = evaluate_engine(engine_beta, test_loader)

    delta_alpha_swap = (acc_alpha_swap - acc_alpha_base) * 100
    delta_beta_swap = (acc_beta_swap - acc_beta_base) * 100

    print_table(
        ["Engine", "Baseline", "Post-Swap", "Delta"],
        [
            ["Alpha", f"{acc_alpha_base*100:.2f}%", f"{acc_alpha_swap*100:.2f}%",
             f"{delta_alpha_swap:+.2f}%"],
            ["Beta", f"{acc_beta_base*100:.2f}%", f"{acc_beta_swap*100:.2f}%",
             f"{delta_beta_swap:+.2f}%"],
        ],
        title="Accuracy After Identity Swap"
    )

    # Restore originals for next tests
    set_identity(engine_alpha, id_alpha_orig)
    set_identity(engine_beta, id_beta_orig)

    # ══════════════════════════════════════════
    # PHASE 4: Identity Ablation (Zero)
    # ══════════════════════════════════════════

    print("\n" + "=" * 70)
    print("  PHASE 4: Identity ZERO (remove identity entirely)")
    print("=" * 70)

    zero_identity(engine_alpha)
    zero_identity(engine_beta)

    acc_alpha_zero, per_digit_alpha_zero = evaluate_engine(engine_alpha, test_loader)
    acc_beta_zero, per_digit_beta_zero = evaluate_engine(engine_beta, test_loader)

    delta_alpha_zero = (acc_alpha_zero - acc_alpha_base) * 100
    delta_beta_zero = (acc_beta_zero - acc_beta_base) * 100

    print_table(
        ["Engine", "Baseline", "Zero-ID", "Delta"],
        [
            ["Alpha", f"{acc_alpha_base*100:.2f}%", f"{acc_alpha_zero*100:.2f}%",
             f"{delta_alpha_zero:+.2f}%"],
            ["Beta", f"{acc_beta_base*100:.2f}%", f"{acc_beta_zero*100:.2f}%",
             f"{delta_beta_zero:+.2f}%"],
        ],
        title="Accuracy With Zeroed Identity"
    )

    # Restore originals
    set_identity(engine_alpha, id_alpha_orig)
    set_identity(engine_beta, id_beta_orig)

    # ══════════════════════════════════════════
    # PHASE 5: Random Identity
    # ══════════════════════════════════════════

    print("\n" + "=" * 70)
    print("  PHASE 5: Identity RANDOM (replace with noise)")
    print("=" * 70)

    # Use same scale as original norms
    set_seed(999)
    random_identity(engine_alpha, scale=id_norm_alpha)
    random_identity(engine_beta, scale=id_norm_beta)

    acc_alpha_rand, per_digit_alpha_rand = evaluate_engine(engine_alpha, test_loader)
    acc_beta_rand, per_digit_beta_rand = evaluate_engine(engine_beta, test_loader)

    delta_alpha_rand = (acc_alpha_rand - acc_alpha_base) * 100
    delta_beta_rand = (acc_beta_rand - acc_beta_base) * 100

    print_table(
        ["Engine", "Baseline", "Random-ID", "Delta"],
        [
            ["Alpha", f"{acc_alpha_base*100:.2f}%", f"{acc_alpha_rand*100:.2f}%",
             f"{delta_alpha_rand:+.2f}%"],
            ["Beta", f"{acc_beta_base*100:.2f}%", f"{acc_beta_rand*100:.2f}%",
             f"{delta_beta_rand:+.2f}%"],
        ],
        title="Accuracy With Random Identity"
    )

    # Restore originals
    set_identity(engine_alpha, id_alpha_orig)
    set_identity(engine_beta, id_beta_orig)

    # ══════════════════════════════════════════
    # PHASE 6: Per-Digit Analysis
    # ══════════════════════════════════════════

    print("\n" + "=" * 70)
    print("  PHASE 6: Per-Digit Accuracy Analysis (Alpha)")
    print("=" * 70)

    digit_labels = [str(d) for d in range(10)]

    # Per-digit deltas for Alpha across all conditions
    rows_digit = []
    swap_deltas = []
    zero_deltas = []
    rand_deltas = []

    for d in range(10):
        base = per_digit_alpha_base[d] * 100
        swap = per_digit_alpha_swap[d] * 100
        zero = per_digit_alpha_zero[d] * 100
        rand = per_digit_alpha_rand[d] * 100
        sd = swap - base
        zd = zero - base
        rd = rand - base
        swap_deltas.append(sd)
        zero_deltas.append(zd)
        rand_deltas.append(rd)
        rows_digit.append([
            str(d),
            f"{base:.1f}%",
            f"{swap:.1f}% ({sd:+.1f})",
            f"{zero:.1f}% ({zd:+.1f})",
            f"{rand:.1f}% ({rd:+.1f})",
        ])

    print_table(
        ["Digit", "Baseline", "Swapped", "Zeroed", "Random"],
        rows_digit,
        title="Alpha: Per-Digit Accuracy Under Identity Manipulation"
    )

    # Most affected digits
    print("\n  Most affected digits (by swap):")
    swap_impact = sorted(range(10), key=lambda d: abs(swap_deltas[d]), reverse=True)
    for rank, d in enumerate(swap_impact[:3]):
        print(f"    #{rank+1}: digit {d} -> {swap_deltas[d]:+.2f}%")

    # ASCII bar chart: swap deltas
    ascii_bar_chart(
        digit_labels, swap_deltas,
        "Per-Digit Accuracy Change After SWAP (Alpha)",
        width=40
    )

    # ASCII bar chart: zero deltas
    ascii_bar_chart(
        digit_labels, zero_deltas,
        "Per-Digit Accuracy Change After ZERO (Alpha)",
        width=40
    )

    # ══════════════════════════════════════════
    # PHASE 7: Per-Digit Analysis (Beta)
    # ══════════════════════════════════════════

    print("\n" + "=" * 70)
    print("  PHASE 7: Per-Digit Accuracy Analysis (Beta)")
    print("=" * 70)

    rows_digit_b = []
    swap_deltas_b = []
    zero_deltas_b = []
    rand_deltas_b = []

    for d in range(10):
        base = per_digit_beta_base[d] * 100
        swap = per_digit_beta_swap[d] * 100
        zero = per_digit_beta_zero[d] * 100
        rand = per_digit_beta_rand[d] * 100
        sd = swap - base
        zd = zero - base
        rd = rand - base
        swap_deltas_b.append(sd)
        zero_deltas_b.append(zd)
        rand_deltas_b.append(rd)
        rows_digit_b.append([
            str(d),
            f"{base:.1f}%",
            f"{swap:.1f}% ({sd:+.1f})",
            f"{zero:.1f}% ({zd:+.1f})",
            f"{rand:.1f}% ({rd:+.1f})",
        ])

    print_table(
        ["Digit", "Baseline", "Swapped", "Zeroed", "Random"],
        rows_digit_b,
        title="Beta: Per-Digit Accuracy Under Identity Manipulation"
    )

    # ══════════════════════════════════════════
    # PHASE 8: Summary & Conclusions
    # ══════════════════════════════════════════

    print("\n" + "=" * 70)
    print("  SUMMARY: Identity Transfer Experiment Results")
    print("=" * 70)

    print_table(
        ["Condition", "Alpha Acc", "Beta Acc", "Alpha Delta", "Beta Delta"],
        [
            ["Baseline (original)", f"{acc_alpha_base*100:.2f}%", f"{acc_beta_base*100:.2f}%",
             "---", "---"],
            ["Swapped identity", f"{acc_alpha_swap*100:.2f}%", f"{acc_beta_swap*100:.2f}%",
             f"{delta_alpha_swap:+.2f}%", f"{delta_beta_swap:+.2f}%"],
            ["Zeroed identity", f"{acc_alpha_zero*100:.2f}%", f"{acc_beta_zero*100:.2f}%",
             f"{delta_alpha_zero:+.2f}%", f"{delta_beta_zero:+.2f}%"],
            ["Random identity", f"{acc_alpha_rand*100:.2f}%", f"{acc_beta_rand*100:.2f}%",
             f"{delta_alpha_rand:+.2f}%", f"{delta_beta_rand:+.2f}%"],
        ],
        title="All Conditions Comparison"
    )

    print(f"\n  Identity Vector Properties:")
    print(f"    Cosine Similarity (Alpha vs Beta): {cos_sim:.6f}")
    print(f"    L2 Distance:                       {l2_dist:.6f}")
    print(f"    Alpha norm:                        {id_norm_alpha:.6f}")
    print(f"    Beta norm:                         {id_norm_beta:.6f}")

    # ── Interpretation ──
    print("\n" + "-" * 70)
    print("  INTERPRETATION")
    print("-" * 70)

    avg_swap_delta = (abs(delta_alpha_swap) + abs(delta_beta_swap)) / 2
    avg_zero_delta = (abs(delta_alpha_zero) + abs(delta_beta_zero)) / 2
    avg_rand_delta = (abs(delta_alpha_rand) + abs(delta_beta_rand)) / 2

    print(f"\n  Average absolute accuracy change:")
    print(f"    Swap:   {avg_swap_delta:.2f}%")
    print(f"    Zero:   {avg_zero_delta:.2f}%")
    print(f"    Random: {avg_rand_delta:.2f}%")

    # Identity importance assessment
    print(f"\n  Q: Does identity carry meaningful information?")
    if avg_zero_delta > 1.0:
        print(f"    A: YES. Removing identity degrades accuracy by {avg_zero_delta:.2f}%.")
        print(f"       Identity is functionally important.")
    elif avg_zero_delta > 0.2:
        print(f"    A: MARGINALLY. Removing identity degrades accuracy by only {avg_zero_delta:.2f}%.")
        print(f"       Identity carries some information but model is robust without it.")
    else:
        print(f"    A: MINIMAL EFFECT. Removing identity changes accuracy by only {avg_zero_delta:.2f}%.")
        print(f"       Identity may be decorative at this scale / training duration.")

    print(f"\n  Q: Is identity transfer possible?")
    if avg_swap_delta < 0.5:
        print(f"    A: YES (trivially). Swapping causes only {avg_swap_delta:.2f}% change.")
        print(f"       Either identities are interchangeable or carry little weight.")
    elif avg_swap_delta < 2.0:
        print(f"    A: PARTIALLY. Swapping causes {avg_swap_delta:.2f}% degradation.")
        print(f"       Identity is somewhat personalized but transfer is survivable.")
    else:
        print(f"    A: DIFFICULT. Swapping causes {avg_swap_delta:.2f}% degradation.")
        print(f"       Identity is deeply personalized. Transfer disrupts the model.")

    print(f"\n  Q: Random vs Zero vs Swap - which is worst?")
    conditions = [
        ("Swap", avg_swap_delta),
        ("Zero", avg_zero_delta),
        ("Random", avg_rand_delta),
    ]
    conditions.sort(key=lambda x: x[1], reverse=True)
    for rank, (name, delta) in enumerate(conditions):
        print(f"    #{rank+1}: {name:<7} -> {delta:.2f}% avg change")
    worst = conditions[0][0]
    if worst == "Random":
        print(f"    -> Random noise is most disruptive: identity space is structured.")
    elif worst == "Zero":
        print(f"    -> Absence is worse than wrong: identity provides useful bias.")
    else:
        print(f"    -> Wrong identity is worst: model co-adapts with its specific identity.")

    # Per-digit correlation between Alpha and Beta swap effects
    if swap_deltas and swap_deltas_b:
        alpha_arr = np.array(swap_deltas)
        beta_arr = np.array(swap_deltas_b)
        if alpha_arr.std() > 1e-10 and beta_arr.std() > 1e-10:
            corr = np.corrcoef(alpha_arr, beta_arr)[0, 1]
            print(f"\n  Per-digit swap effect correlation (Alpha vs Beta): {corr:.4f}")
            if corr > 0.5:
                print(f"    -> Same digits affected in both: identity encodes digit-general features.")
            elif corr < -0.5:
                print(f"    -> Opposite effects: identities are complementary.")
            else:
                print(f"    -> Uncorrelated: each identity encodes different digit-specific features.")

    print("\n" + "=" * 70)
    print("  Experiment complete.")
    print("=" * 70)
    print()


if __name__ == '__main__':
    main()
```