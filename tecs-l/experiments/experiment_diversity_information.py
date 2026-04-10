I'll translate all Korean text to English while maintaining the exact structure and formatting of the Python file:

```python
#!/usr/bin/env python3
"""Hypothesis 270: Diversity IS Information

Experimental verification of the hypothesis that diversity IS information.

Key idea:
  In a RepulsionField, if we gradually increase the diversity between two poles,
  do tension and accuracy increase together?

Diversity spectrum:
  Level 0: Identical EngineA copy (same seed) → diversity = 0
  Level 1: Two EngineA with different seeds → diversity = initialization difference
  Level 2: EngineA + weight noise added → diversity = perturbation
  Level 3: EngineA + EngineE (different architecture, similar principle) → diversity = structural
  Level 4: EngineA + EngineG (different architecture, different principle) → diversity = maximum

Additional experiments:
  - Weight interpolation: Continuous change from G to A
  - Mutual Information (MI) estimation: How much information does diversity add
"""

import sys
import os
import copy
import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import math
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from model_utils import (
    Expert, TopKGate, load_mnist, train_and_evaluate, count_params
)
from model_meta_engine import EngineA, EngineE, EngineG


# ─────────────────────────────────────────
# DiversityRepulsionField
# ─────────────────────────────────────────

class DiversityRepulsionField(nn.Module):
    """Repulsion field using two arbitrary engines as poles.

    Same structure as RepulsionFieldEngine but accepts any engine pair.
    """
    def __init__(self, pole_plus, pole_minus, output_dim=10):
        super().__init__()
        self.pole_plus = pole_plus
        self.pole_minus = pole_minus
        self.field_transform = nn.Sequential(
            nn.Linear(output_dim, output_dim),
            nn.Tanh(),
        )
        self.tension_scale = nn.Parameter(torch.tensor(1/3))
        self.aux_loss = torch.tensor(0.0)
        self.tension_magnitude = 0.0
        self._per_sample_tensions = []

    def forward(self, x):
        out_plus = self.pole_plus(x)
        out_minus = self.pole_minus(x)

        repulsion = out_plus - out_minus
        tension = (repulsion ** 2).sum(dim=-1, keepdim=True)

        equilibrium = (out_plus + out_minus) / 2
        field_direction = self.field_transform(repulsion)

        output = equilibrium + self.tension_scale * torch.sqrt(tension + 1e-8) * field_direction

        # Collect entropy loss from EngineG if present
        entropy_loss = torch.tensor(0.0, device=x.device)
        for pole in [self.pole_plus, self.pole_minus]:
            if hasattr(pole, 'entropy_loss'):
                entropy_loss = entropy_loss + pole.entropy_loss
        self.aux_loss = entropy_loss

        with torch.no_grad():
            self.tension_magnitude = tension.mean().item()
            self._per_sample_tensions = tension.squeeze(-1).cpu().numpy()

        return (output, self.aux_loss)


# ─────────────────────────────────────────
# Helper: weight-interpolated engine
# ─────────────────────────────────────────

def interpolate_state_dicts(sd_a, sd_b, alpha):
    """sd_result = alpha * sd_a + (1-alpha) * sd_b.

    Only interpolates parameters with matching shapes; skips mismatches.
    """
    result = {}
    for key in sd_a:
        if key in sd_b and sd_a[key].shape == sd_b[key].shape:
            result[key] = alpha * sd_a[key] + (1 - alpha) * sd_b[key]
        else:
            result[key] = sd_a[key].clone()
    return result


def make_interpolated_engine(engine_a_sd, engine_g_sd, alpha, input_dim, hidden_dim, output_dim):
    """Create an EngineA-shaped model with weights = alpha*A + (1-alpha)*G.

    Since EngineA and EngineG have different architectures, we create a fresh
    EngineA and interpolate only the overlapping expert weights.
    For a fair test, we use a simple dense model as the interpolation vessel.
    """
    # Both EngineA and EngineG have expert sub-networks of the same shape
    # but different gating. We use a DenseInterpolated vessel.
    model = InterpolatedDense(input_dim, hidden_dim, output_dim)
    return model


class InterpolatedDense(nn.Module):
    """Simple 2-layer network used as interpolation vessel between engines."""
    def __init__(self, input_dim, hidden_dim, output_dim):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, output_dim),
        )

    def forward(self, x):
        return self.net(x)


# ─────────────────────────────────────────
# Mutual information estimation (binned)
# ─────────────────────────────────────────

def estimate_mi_binned(logits, labels, n_bins=20):
    """Estimate MI(logits; labels) using binned histogram method.

    Uses the argmax prediction as a discrete variable.
    MI(pred; label) = H(label) - H(label | pred)
    """
    preds = logits.argmax(dim=1).numpy()
    labels = labels.numpy()
    n_classes = max(labels.max(), preds.max()) + 1

    # Joint distribution
    joint = np.zeros((n_classes, n_classes))
    for p, l in zip(preds, labels):
        joint[p, l] += 1
    joint = joint / joint.sum()

    # Marginals
    p_pred = joint.sum(axis=1)
    p_label = joint.sum(axis=0)

    # MI = sum p(x,y) log(p(x,y) / (p(x)p(y)))
    mi = 0.0
    for i in range(n_classes):
        for j in range(n_classes):
            if joint[i, j] > 0 and p_pred[i] > 0 and p_label[j] > 0:
                mi += joint[i, j] * np.log(joint[i, j] / (p_pred[i] * p_label[j]))
    return mi


def collect_predictions(model, test_loader, flatten=True):
    """Collect all model predictions and labels from test set."""
    model.eval()
    all_logits = []
    all_labels = []
    with torch.no_grad():
        for X, y in test_loader:
            if flatten:
                X = X.view(X.size(0), -1)
            out = model(X)
            if isinstance(out, tuple):
                out = out[0]
            all_logits.append(out.cpu())
            all_labels.append(y.cpu())
    return torch.cat(all_logits), torch.cat(all_labels)


def collect_pole_predictions(field_model, test_loader, flatten=True):
    """Collect predictions from both poles and the field output."""
    field_model.eval()
    plus_logits, minus_logits, field_logits, labels = [], [], [], []
    with torch.no_grad():
        for X, y in test_loader:
            if flatten:
                X = X.view(X.size(0), -1)
            out_p = field_model.pole_plus(X)
            out_m = field_model.pole_minus(X)
            out_f = field_model(X)
            if isinstance(out_f, tuple):
                out_f = out_f[0]
            plus_logits.append(out_p.cpu())
            minus_logits.append(out_m.cpu())
            field_logits.append(out_f.cpu())
            labels.append(y.cpu())
    return (torch.cat(plus_logits), torch.cat(minus_logits),
            torch.cat(field_logits), torch.cat(labels))


# ─────────────────────────────────────────
# ASCII graph helpers
# ─────────────────────────────────────────

def ascii_bar_chart(labels, values, title, width=40, fmt=".2f"):
    """Draw a horizontal ASCII bar chart."""
    print(f"\n  {title}")
    print(f"  {'─' * (width + 25)}")
    max_val = max(abs(v) for v in values) if values else 1
    for label, val in zip(labels, values):
        bar_len = int(abs(val) / max_val * width) if max_val > 0 else 0
        bar = "█" * bar_len
        print(f"  {label:>20} │{bar} {val:{fmt}}")
    print()


def ascii_xy_plot(xs, ys_dict, title, width=60, height=15):
    """Draw an ASCII scatter/line plot with multiple series."""
    print(f"\n  {title}")
    print(f"  {'─' * (width + 10)}")

    all_ys = [y for ys in ys_dict.values() for y in ys]
    if not all_ys:
        print("  (no data)")
        return
    y_min = min(all_ys)
    y_max = max(all_ys)
    if y_max == y_min:
        y_max = y_min + 1

    x_min = min(xs)
    x_max = max(xs)
    if x_max == x_min:
        x_max = x_min + 1

    # Build canvas
    canvas = [[' ' for _ in range(width)] for _ in range(height)]

    markers = list("*o+x#@&%")
    legend = []
    for idx, (name, ys) in enumerate(ys_dict.items()):
        marker = markers[idx % len(markers)]
        legend.append(f"{marker}={name}")
        for x, y in zip(xs, ys):
            col = int((x - x_min) / (x_max - x_min) * (width - 1))
            row = height - 1 - int((y - y_min) / (y_max - y_min) * (height - 1))
            col = max(0, min(width - 1, col))
            row = max(0, min(height - 1, row))
            canvas[row][col] = marker

    # Print
    for r in range(height):
        y_val = y_max - r * (y_max - y_min) / (height - 1)
        line = ''.join(canvas[r])
        print(f"  {y_val:>8.3f} │{line}")
    print(f"  {'':>8} └{'─' * width}")
    x_labels = f"  {'':>8}  {x_min:<10.2f}{' ' * (width - 20)}{x_max:>10.2f}"
    print(x_labels)
    print(f"  Legend: {', '.join(legend)}")
    print()


# ─────────────────────────────────────────
# Main experiment
# ─────────────────────────────────────────

def run_diversity_gradient(train_loader, test_loader, input_dim, hidden_dim, output_dim, epochs):
    """Experiment 1: Diversity gradient from identical to maximally different."""
    print("\n" + "=" * 70)
    print("  EXPERIMENT 1: Diversity Gradient")
    print("  Level 0: Identical (A clone)  →  Level 4: Maximum (A vs G)")
    print("=" * 70)

    results = {}

    # ── Level 0: Identical (same seed, deep copy) ──
    print("\n  [Level 0] Two identical EngineA copies (same seed)")
    torch.manual_seed(42)
    engine_a_base = EngineA(input_dim, hidden_dim, output_dim)
    engine_a_clone = copy.deepcopy(engine_a_base)
    model = DiversityRepulsionField(engine_a_base, engine_a_clone, output_dim)
    losses, accs = train_and_evaluate(model, train_loader, test_loader, epochs,
                                       aux_lambda=0.01, verbose=True)
    results['L0_identical'] = {
        'acc': accs[-1], 'loss': losses[-1], 'tension': model.tension_magnitude,
        'tension_scale': model.tension_scale.item(), 'params': count_params(model),
        'label': 'L0: Identical', 'diversity': 0,
    }

    # ── Level 1: Different seeds ──
    print("\n  [Level 1] Two EngineA with different seeds")
    torch.manual_seed(42)
    engine_a1 = EngineA(input_dim, hidden_dim, output_dim)
    torch.manual_seed(999)
    engine_a2 = EngineA(input_dim, hidden_dim, output_dim)
    model = DiversityRepulsionField(engine_a1, engine_a2, output_dim)
    losses, accs = train_and_evaluate(model, train_loader, test_loader, epochs,
                                       aux_lambda=0.01, verbose=True)
    results['L1_diff_seed'] = {
        'acc': accs[-1], 'loss': losses[-1], 'tension': model.tension_magnitude,
        'tension_scale': model.tension_scale.item(), 'params': count_params(model),
        'label': 'L1: Diff seed', 'diversity': 1,
    }

    # ── Level 2: EngineA + noised weights ──
    print("\n  [Level 2] EngineA + weight-noised EngineA (sigma=0.5)")
    torch.manual_seed(42)
    engine_a_clean = EngineA(input_dim, hidden_dim, output_dim)
    engine_a_noisy = copy.deepcopy(engine_a_clean)
    with torch.no_grad():
        for p in engine_a_noisy.parameters():
            p.add_(torch.randn_like(p) * 0.5)
    model = DiversityRepulsionField(engine_a_clean, engine_a_noisy, output_dim)
    losses, accs = train_and_evaluate(model, train_loader, test_loader, epochs,
                                       aux_lambda=0.01, verbose=True)
    results['L2_noise'] = {
        'acc': accs[-1], 'loss': losses[-1], 'tension': model.tension_magnitude,
        'tension_scale': model.tension_scale.item(), 'params': count_params(model),
        'label': 'L2: +Noise', 'diversity': 2,
    }

    # ── Level 3: EngineA + EngineE (different arch, similar principle) ──
    print("\n  [Level 3] EngineA + EngineE (different architecture, similar MoE principle)")
    torch.manual_seed(42)
    engine_a3 = EngineA(input_dim, hidden_dim, output_dim)
    engine_e = EngineE(input_dim, hidden_dim, output_dim)
    model = DiversityRepulsionField(engine_a3, engine_e, output_dim)
    losses, accs = train_and_evaluate(model, train_loader, test_loader, epochs,
                                       aux_lambda=0.01, verbose=True)
    results['L3_diff_arch'] = {
        'acc': accs[-1], 'loss': losses[-1], 'tension': model.tension_magnitude,
        'tension_scale': model.tension_scale.item(), 'params': count_params(model),
        'label': 'L3: A+E', 'diversity': 3,
    }

    # ── Level 4: EngineA + EngineG (different arch, different principle) ──
    print("\n  [Level 4] EngineA + EngineG (maximum diversity — different principle)")
    torch.manual_seed(42)
    engine_a4 = EngineA(input_dim, hidden_dim, output_dim)
    engine_g = EngineG(input_dim, hidden_dim, output_dim)
    model_l4 = DiversityRepulsionField(engine_a4, engine_g, output_dim)
    losses, accs = train_and_evaluate(model_l4, train_loader, test_loader, epochs,
                                       aux_lambda=0.01, verbose=True)
    results['L4_max_div'] = {
        'acc': accs[-1], 'loss': losses[-1], 'tension': model_l4.tension_magnitude,
        'tension_scale': model_l4.tension_scale.item(), 'params': count_params(model_l4),
        'label': 'L4: A+G', 'diversity': 4,
    }

    return results, model_l4


def run_interpolation_experiment(train_loader, test_loader, input_dim, hidden_dim, output_dim, epochs):
    """Experiment 2: Weight interpolation between trained engines.

    Train EngineA and EngineG separately, then create interpolated dense models.
    Use G as pole_plus, E(alpha) as pole_minus. alpha=0 → G vs G, alpha=1 → G vs A.
    """
    print("\n" + "=" * 70)
    print("  EXPERIMENT 2: Weight Interpolation")
    print("  alpha=0: G vs G (no diversity) → alpha=1: G vs A (max diversity)")
    print("=" * 70)

    # Train standalone EngineA
    print("\n  Training standalone EngineA...")
    torch.manual_seed(42)
    engine_a = EngineA(input_dim, hidden_dim, output_dim)
    train_and_evaluate(engine_a, train_loader, test_loader, epochs, verbose=False)
    sd_a = {k: v.cpu().clone() for k, v in engine_a.state_dict().items()}

    # Train standalone EngineG
    print("  Training standalone EngineG...")
    torch.manual_seed(42)
    engine_g = EngineG(input_dim, hidden_dim, output_dim)
    train_and_evaluate(engine_g, train_loader, test_loader, epochs,
                       aux_lambda=0.01, verbose=False)
    sd_g = {k: v.cpu().clone() for k, v in engine_g.state_dict().items()}

    # Since A and G have different architectures, we train two InterpolatedDense
    # networks that distill A and G, then interpolate those.
    print("  Training dense distillation of EngineA...")
    torch.manual_seed(42)
    dense_a = InterpolatedDense(input_dim, hidden_dim * 2, output_dim)
    train_and_evaluate(dense_a, train_loader, test_loader, epochs, verbose=False)
    sd_dense_a = {k: v.cpu().clone() for k, v in dense_a.state_dict().items()}

    print("  Training dense distillation of EngineG (different seed)...")
    torch.manual_seed(777)
    dense_g = InterpolatedDense(input_dim, hidden_dim * 2, output_dim)
    train_and_evaluate(dense_g, train_loader, test_loader, epochs, verbose=False)
    sd_dense_g = {k: v.cpu().clone() for k, v in dense_g.state_dict().items()}

    # Interpolation experiment
    alphas = [0.0, 0.1, 0.25, 0.5, 0.75, 0.9, 1.0]
    interp_results = {}

    for alpha in alphas:
        label = f"alpha={alpha:.2f}"
        print(f"\n  [Interpolation] {label}: pole_minus = {alpha:.0%}A + {1-alpha:.0%}G")

        # Fixed pole_plus = G
        torch.manual_seed(42)
        pole_plus = InterpolatedDense(input_dim, hidden_dim * 2, output_dim)
        pole_plus.load_state_dict(sd_dense_g)

        # Interpolated pole_minus
        torch.manual_seed(42)
        pole_minus = InterpolatedDense(input_dim, hidden_dim * 2, output_dim)
        interp_sd = interpolate_state_dicts(sd_dense_a, sd_dense_g, alpha)
        pole_minus.load_state_dict(interp_sd)

        model = DiversityRepulsionField(pole_plus, pole_minus, output_dim)
        losses, accs = train_and_evaluate(model, train_loader, test_loader, epochs,
                                           aux_lambda=0.0, verbose=False)
        interp_results[label] = {
            'alpha': alpha,
            'acc': accs[-1], 'loss': losses[-1],
            'tension': model.tension_magnitude,
            'tension_scale': model.tension_scale.item(),
        }
        print(f"    Acc={accs[-1]*100:.1f}%, Tension={model.tension_magnitude:.4f}, "
              f"Scale={model.tension_scale.item():.4f}")

    return interp_results


def run_mi_analysis(model_l4, train_loader, test_loader):
    """Experiment 3: Mutual information analysis on the best model (Level 4)."""
    print("\n" + "=" * 70)
    print("  EXPERIMENT 3: Mutual Information Analysis")
    print("  How much information does the repulsion field add?")
    print("=" * 70)

    plus_logits, minus_logits, field_logits, labels = collect_pole_predictions(
        model_l4, test_loader, flatten=True)

    mi_plus = estimate_mi_binned(plus_logits, labels)
    mi_minus = estimate_mi_binned(minus_logits, labels)
    mi_field = estimate_mi_binned(field_logits, labels)

    # Accuracy of each
    acc_plus = (plus_logits.argmax(1) == labels).float().mean().item()
    acc_minus = (minus_logits.argmax(1) == labels).float().mean().item()
    acc_field = (field_logits.argmax(1) == labels).float().mean().item()

    mi_results = {
        'pole_plus': {'mi': mi_plus, 'acc': acc_plus},
        'pole_minus': {'mi': mi_minus, 'acc': acc_minus},
        'field': {'mi': mi_field, 'acc': acc_field},
    }

    print(f"\n  MI(pole+; label)  = {mi_plus:.4f}  (Acc={acc_plus*100:.1f}%)")
    print(f"  MI(pole-; label)  = {mi_minus:.4f}  (Acc={acc_minus*100:.1f}%)")
    print(f"  MI(field; label)  = {mi_field:.4f}  (Acc={acc_field*100:.1f}%)")
    print(f"\n  MI added by field = {mi_field - max(mi_plus, mi_minus):.4f}")
    print(f"  MI ratio (field / max_pole) = {mi_field / max(mi_plus, mi_minus, 1e-8):.3f}")

    return mi_results


# ─────────────────────────────────────────
# Summary and visualization
# ─────────────────────────────────────────

def print_summary(div_results, interp_results, mi_results):
    """Print comprehensive summary with tables and ASCII graphs."""
    print("\n")
    print("=" * 70)
    print("  HYPOTHESIS 270: Diversity IS Information — RESULTS")
    print("=" * 70)

    # ── Table 1: Diversity Gradient ──
    print("\n  Table 1: Diversity Gradient")
    print(f"  {'─' * 66}")
    print(f"  {'Level':<20} {'Acc%':>7} {'Tension':>10} {'T.Scale':>9} {'Params':>10}")
    print(f"  {'─' * 66}")
    for key in ['L0_identical', 'L1_diff_seed', 'L2_noise', 'L3_diff_arch', 'L4_max_div']:
        r = div_results[key]
        print(f"  {r['label']:<20} {r['acc']*100:>7.2f} {r['tension']:>10.4f} "
              f"{r['tension_scale']:>9.4f} {r['params']:>10,}")
    print(f"  {'─' * 66}")

    # Diversity vs Accuracy
    labels = [div_results[k]['label'] for k in ['L0_identical', 'L1_diff_seed', 'L2_noise', 'L3_diff_arch', 'L4_max_div']]
    accs = [div_results[k]['acc'] * 100 for k in ['L0_identical', 'L1_diff_seed', 'L2_noise', 'L3_diff_arch', 'L4_max_div']]
    tensions = [div_results[k]['tension'] for k in ['L0_identical', 'L1_diff_seed', 'L2_noise', 'L3_diff_arch', 'L4_max_div']]

    ascii_bar_chart(labels, accs, "Accuracy (%) by Diversity Level", fmt=".1f")
    ascii_bar_chart(labels, tensions, "Mean Tension by Diversity Level", fmt=".4f")

    # XY plot: diversity level vs acc and tension
    xs = list(range(5))
    ascii_xy_plot(
        xs,
        {'Accuracy': accs, 'Tension(x10)': [t * 10 for t in tensions]},
        "Diversity Level vs Accuracy & Tension",
    )

    # ── Table 2: Interpolation ──
    print("\n  Table 2: Weight Interpolation (alpha=0: G vs G, alpha=1: G vs A)")
    print(f"  {'─' * 55}")
    print(f"  {'Alpha':>8} {'Acc%':>8} {'Tension':>10} {'T.Scale':>10}")
    print(f"  {'─' * 55}")
    for key in sorted(interp_results.keys(), key=lambda k: interp_results[k]['alpha']):
        r = interp_results[key]
        print(f"  {r['alpha']:>8.2f} {r['acc']*100:>8.2f} {r['tension']:>10.4f} "
              f"{r['tension_scale']:>10.4f}")
    print(f"  {'─' * 55}")

    alphas = [interp_results[k]['alpha'] for k in sorted(interp_results.keys(),
              key=lambda k: interp_results[k]['alpha'])]
    i_accs = [interp_results[k]['acc'] * 100 for k in sorted(interp_results.keys(),
              key=lambda k: interp_results[k]['alpha'])]
    i_tensions = [interp_results[k]['tension'] for k in sorted(interp_results.keys(),
                  key=lambda k: interp_results[k]['alpha'])]

    ascii_xy_plot(
        alphas,
        {'Accuracy': i_accs, 'Tension(x10)': [t * 10 for t in i_tensions]},
        "Interpolation: Alpha vs Accuracy & Tension",
    )

    # ── Table 3: Mutual Information ──
    print("\n  Table 3: Mutual Information (Level 4: A vs G)")
    print(f"  {'─' * 45}")
    print(f"  {'Source':<15} {'MI(;label)':>12} {'Acc%':>8}")
    print(f"  {'─' * 45}")
    for name, r in mi_results.items():
        print(f"  {name:<15} {r['mi']:>12.4f} {r['acc']*100:>8.1f}")
    print(f"  {'─' * 45}")

    mi_pole_max = max(mi_results['pole_plus']['mi'], mi_results['pole_minus']['mi'])
    mi_field = mi_results['field']['mi']
    mi_added = mi_field - mi_pole_max

    print(f"\n  MI added by repulsion field: {mi_added:+.4f}")
    if mi_added > 0:
        print(f"  → Field CREATES information beyond individual poles")
    else:
        print(f"  → Field does NOT add information (hypothesis challenged)")

    # ── Correlation analysis ──
    print("\n" + "─" * 70)
    print("  CORRELATION: Diversity vs Tension vs Accuracy")
    print("─" * 70)

    divs = [0, 1, 2, 3, 4]
    accs_arr = np.array(accs)
    tens_arr = np.array(tensions)

    # Pearson correlations
    if np.std(accs_arr) > 0 and np.std(tens_arr) > 0:
        corr_div_acc = np.corrcoef(divs, accs_arr)[0, 1]
        corr_div_ten = np.corrcoef(divs, tens_arr)[0, 1]
        corr_ten_acc = np.corrcoef(tens_arr, accs_arr)[0, 1]
    else:
        corr_div_acc = corr_div_ten = corr_ten_acc = 0.0

    print(f"  r(diversity, accuracy) = {corr_div_acc:+.4f}")
    print(f"  r(diversity, tension)  = {corr_div_ten:+.4f}")
    print(f"  r(tension, accuracy)   = {corr_ten_acc:+.4f}")

    # ── Verdict ──
    print("\n" + "=" * 70)
    print("  VERDICT")
    print("=" * 70)

    l0_acc = div_results['L0_identical']['acc'] * 100
    l4_acc = div_results['L4_max_div']['acc'] * 100
    improvement = l4_acc - l0_acc

    print(f"\n  Identical poles (L0): {l0_acc:.2f}%")
    print(f"  Maximum diversity (L4): {l4_acc:.2f}%")
    print(f"  Improvement: {improvement:+.2f}%")

    if improvement > 0 and corr_div_acc > 0.5:
        print(f"\n  SUPPORTED: Diversity IS Information")
        print(f"  More diverse poles → more tension → more accuracy")
        print(f"  The repulsion field converts architectural diversity into task information.")
    elif improvement > 0:
        print(f"\n  PARTIALLY SUPPORTED: Diversity helps, but correlation is weak")
        print(f"  r(diversity, accuracy) = {corr_div_acc:.4f} (expected > 0.5)")
    else:
        print(f"\n  NOT SUPPORTED: Diversity does not improve accuracy in this setting")

    if mi_added > 0:
        print(f"\n  MI EVIDENCE: The field creates {mi_added:.4f} nats of additional information")
        print(f"  beyond what either pole provides alone.")
    print()


# ─────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────

def main():
    print()
    print("=" * 70)
    print("  Hypothesis 270: Diversity IS Information")
    print("  Does architectural diversity between poles create information?")
    print("=" * 70)
    print()

    t0 = time.time()

    train_loader, test_loader = load_mnist(batch_size=128)
    input_dim, hidden_dim, output_dim = 784, 48, 10
    epochs = 8

    # Experiment 1: Diversity gradient
    div_results, model_l4 = run_diversity_gradient(
        train_loader, test_loader, input_dim, hidden_dim, output_dim, epochs)

    # Experiment 2: Weight interpolation
    interp_results = run_interpolation_experiment(
        train_loader, test_loader, input_dim, hidden_dim, output_dim, epochs)

    # Experiment 3: Mutual information
    mi_results = run_mi_analysis(model_l4, train_loader, test_loader)

    # Summary
    print_summary(div_results, interp_results, mi_results)

    elapsed = time.time() - t0
    print(f"  Total time: {elapsed:.1f}s")
    print()


if __name__ == '__main__':
    main()
```