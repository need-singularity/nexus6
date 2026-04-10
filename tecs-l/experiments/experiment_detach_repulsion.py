#!/usr/bin/env python3
"""Experiment: Detach Observer on Repulsion Field

Hypothesis 272: detach improves observation by +7.4%.
Test: Add a detach() observer to the standard repulsion field.

Three models compared:
  1. RepulsionFieldEngine (baseline, no observer)
  2. RepulsionFieldWithObserver (observer reads DETACHED pole outputs)
  3. RepulsionFieldWithObserverNoDetach (observer reads raw pole outputs)

The detach observer reads both poles' outputs without interfering with
their gradient flow, then produces an error-correction signal.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import time
import sys

sys.path.insert(0, '/Users/ghost/Dev/logout')

from model_utils import load_mnist, train_and_evaluate, count_params
from model_meta_engine import RepulsionFieldEngine, EngineA, EngineG


class RepulsionFieldWithObserver(nn.Module):
    """Standard repulsion field + detach observer for error correction."""
    def __init__(self, input_dim=784, hidden_dim=48, output_dim=10):
        super().__init__()
        # Same as RepulsionFieldEngine
        self.pole_plus = EngineA(input_dim, hidden_dim, output_dim)
        self.pole_minus = EngineG(input_dim, hidden_dim, output_dim)
        self.field_transform = nn.Sequential(
            nn.Linear(output_dim, output_dim),
            nn.Tanh(),
        )
        self.tension_scale = nn.Parameter(torch.tensor(1/3))

        # NEW: detach observer
        # Observes the repulsion (detached!) and produces a correction
        self.observer = nn.Sequential(
            nn.Linear(output_dim * 2, hidden_dim),  # reads both poles' outputs (detached)
            nn.Tanh(),
            nn.Linear(hidden_dim, output_dim),
        )
        self.observer_scale = nn.Parameter(torch.tensor(0.1))

        self.aux_loss = torch.tensor(0.0)
        self.tension_magnitude = 0.0

    def forward(self, x):
        out_plus = self.pole_plus(x)
        out_minus = self.pole_minus(x)

        # Standard repulsion field output
        repulsion = out_plus - out_minus
        tension = (repulsion ** 2).sum(dim=-1, keepdim=True)
        equilibrium = (out_plus + out_minus) / 2
        field_direction = self.field_transform(repulsion)
        field_output = equilibrium + self.tension_scale * torch.sqrt(tension + 1e-8) * field_direction

        # Observer: reads DETACHED outputs (can't interfere with poles)
        observed = torch.cat([out_plus.detach(), out_minus.detach()], dim=-1)
        correction = self.observer(observed)

        # Final output = field + observer correction
        output = field_output + self.observer_scale * correction

        # Aux loss from G engine
        self.aux_loss = getattr(self.pole_minus, 'entropy_loss', torch.tensor(0.0))

        with torch.no_grad():
            self.tension_magnitude = tension.mean().item()

        return (output, self.aux_loss)


class RepulsionFieldWithObserverNoDetach(nn.Module):
    """Repulsion field + observer WITHOUT detach (for comparison)."""
    def __init__(self, input_dim=784, hidden_dim=48, output_dim=10):
        super().__init__()
        self.pole_plus = EngineA(input_dim, hidden_dim, output_dim)
        self.pole_minus = EngineG(input_dim, hidden_dim, output_dim)
        self.field_transform = nn.Sequential(
            nn.Linear(output_dim, output_dim),
            nn.Tanh(),
        )
        self.tension_scale = nn.Parameter(torch.tensor(1/3))

        # Observer WITHOUT detach
        self.observer = nn.Sequential(
            nn.Linear(output_dim * 2, hidden_dim),
            nn.Tanh(),
            nn.Linear(hidden_dim, output_dim),
        )
        self.observer_scale = nn.Parameter(torch.tensor(0.1))

        self.aux_loss = torch.tensor(0.0)
        self.tension_magnitude = 0.0

    def forward(self, x):
        out_plus = self.pole_plus(x)
        out_minus = self.pole_minus(x)

        repulsion = out_plus - out_minus
        tension = (repulsion ** 2).sum(dim=-1, keepdim=True)
        equilibrium = (out_plus + out_minus) / 2
        field_direction = self.field_transform(repulsion)
        field_output = equilibrium + self.tension_scale * torch.sqrt(tension + 1e-8) * field_direction

        # Observer: reads RAW outputs (gradients flow back to poles)
        observed = torch.cat([out_plus, out_minus], dim=-1)  # NO detach
        correction = self.observer(observed)

        output = field_output + self.observer_scale * correction

        self.aux_loss = getattr(self.pole_minus, 'entropy_loss', torch.tensor(0.0))

        with torch.no_grad():
            self.tension_magnitude = tension.mean().item()

        return (output, self.aux_loss)


def per_digit_accuracy(model, test_loader, flatten=True):
    """Compute per-digit accuracy."""
    correct = [0] * 10
    total = [0] * 10
    model.eval()
    with torch.no_grad():
        for X, y in test_loader:
            if flatten:
                X = X.view(X.size(0), -1)
            out = model(X)
            if isinstance(out, tuple):
                out = out[0]
            preds = out.argmax(1)
            for digit in range(10):
                mask = (y == digit)
                total[digit] += mask.sum().item()
                correct[digit] += ((preds == digit) & mask).sum().item()
    return {d: correct[d] / max(total[d], 1) for d in range(10)}


def run_trial(model_cls, name, train_loader, test_loader, input_dim, hidden_dim, output_dim, epochs):
    """Run a single trial and return results."""
    model = model_cls(input_dim, hidden_dim, output_dim)
    params = count_params(model)
    print(f"\n{'='*60}")
    print(f"  {name}")
    print(f"  Parameters: {params:,}")
    print(f"{'='*60}")

    t0 = time.time()
    losses, accs = train_and_evaluate(model, train_loader, test_loader, epochs, aux_lambda=0.01)
    elapsed = time.time() - t0

    # Per-digit accuracy
    digit_acc = per_digit_accuracy(model, test_loader)

    # Observer scale (if applicable)
    obs_scale = None
    if hasattr(model, 'observer_scale'):
        obs_scale = model.observer_scale.item()

    tension = getattr(model, 'tension_magnitude', None)

    return {
        'name': name,
        'acc': accs[-1],
        'loss': losses[-1],
        'params': params,
        'time': elapsed,
        'accs': accs,
        'losses': losses,
        'digit_acc': digit_acc,
        'observer_scale': obs_scale,
        'tension': tension,
        'tension_scale': model.tension_scale.item(),
    }


def main():
    print()
    print("=" * 65)
    print("   Experiment: Detach Observer on Repulsion Field")
    print("   Hypothesis 272: detach improves observation by +7.4%")
    print("=" * 65)

    train_loader, test_loader = load_mnist()
    input_dim, hidden_dim, output_dim = 784, 48, 10
    epochs = 10
    n_trials = 3

    all_results = {
        'baseline': [],
        'detach': [],
        'no_detach': [],
    }

    models = [
        (RepulsionFieldEngine, 'Baseline (RepulsionField)', 'baseline'),
        (RepulsionFieldWithObserver, 'Detach Observer', 'detach'),
        (RepulsionFieldWithObserverNoDetach, 'No-Detach Observer', 'no_detach'),
    ]

    for trial in range(n_trials):
        print(f"\n{'#'*65}")
        print(f"  TRIAL {trial+1}/{n_trials}")
        print(f"{'#'*65}")

        # Set seed for reproducibility within trial, but different across trials
        torch.manual_seed(42 + trial * 100)
        np.random.seed(42 + trial * 100)

        for model_cls, name, key in models:
            torch.manual_seed(42 + trial * 100)
            np.random.seed(42 + trial * 100)
            result = run_trial(model_cls, f"{name} (trial {trial+1})",
                             train_loader, test_loader,
                             input_dim, hidden_dim, output_dim, epochs)
            all_results[key].append(result)

    # ─── Summary ───
    print("\n")
    print("=" * 75)
    print("   RESULTS SUMMARY (averaged over 3 trials)")
    print("=" * 75)

    summary = {}
    for key, label in [('baseline', 'Baseline (no observer)'),
                        ('detach', 'Detach Observer'),
                        ('no_detach', 'No-Detach Observer')]:
        accs = [r['acc'] for r in all_results[key]]
        losses = [r['loss'] for r in all_results[key]]
        params = all_results[key][0]['params']
        times = [r['time'] for r in all_results[key]]

        summary[key] = {
            'label': label,
            'acc_mean': np.mean(accs),
            'acc_std': np.std(accs),
            'loss_mean': np.mean(losses),
            'params': params,
            'time_mean': np.mean(times),
        }

    print(f"\n  {'Model':<30} {'Acc (mean +/- std)':>22} {'Loss':>10} {'Params':>10} {'Time':>8}")
    print("  " + "-" * 82)
    best_acc = max(s['acc_mean'] for s in summary.values())
    for key in ['baseline', 'detach', 'no_detach']:
        s = summary[key]
        marker = ' <-- best' if s['acc_mean'] == best_acc else ''
        print(f"  {s['label']:<30} {s['acc_mean']*100:>7.2f}% +/- {s['acc_std']*100:.2f}% "
              f"{s['loss_mean']:>8.4f} {s['params']:>10,} {s['time_mean']:>6.1f}s{marker}")

    # ─── Improvement ───
    baseline_mean = summary['baseline']['acc_mean']
    detach_mean = summary['detach']['acc_mean']
    no_detach_mean = summary['no_detach']['acc_mean']
    detach_delta = (detach_mean - baseline_mean) * 100
    no_detach_delta = (no_detach_mean - baseline_mean) * 100

    print(f"\n  Detach vs Baseline:    {'+' if detach_delta >= 0 else ''}{detach_delta:.2f}%")
    print(f"  No-Detach vs Baseline: {'+' if no_detach_delta >= 0 else ''}{no_detach_delta:.2f}%")
    print(f"  Detach vs No-Detach:   {'+' if detach_delta - no_detach_delta >= 0 else ''}{detach_delta - no_detach_delta:.2f}%")

    # ─── Observer Scale Analysis ───
    print(f"\n  Observer Scale (learned values):")
    print(f"  {'Model':<30} {'Trial 1':>10} {'Trial 2':>10} {'Trial 3':>10} {'Mean':>10}")
    print("  " + "-" * 62)
    for key, label in [('detach', 'Detach Observer'), ('no_detach', 'No-Detach Observer')]:
        scales = [r['observer_scale'] for r in all_results[key]]
        print(f"  {label:<30} {scales[0]:>10.4f} {scales[1]:>10.4f} {scales[2]:>10.4f} {np.mean(scales):>10.4f}")

    # ─── Tension Scale Analysis ───
    print(f"\n  Tension Scale (learned values):")
    print(f"  {'Model':<30} {'Trial 1':>10} {'Trial 2':>10} {'Trial 3':>10} {'Mean':>10}")
    print("  " + "-" * 62)
    for key, label in [('baseline', 'Baseline'),
                        ('detach', 'Detach Observer'),
                        ('no_detach', 'No-Detach Observer')]:
        scales = [r['tension_scale'] for r in all_results[key]]
        print(f"  {label:<30} {scales[0]:>10.4f} {scales[1]:>10.4f} {scales[2]:>10.4f} {np.mean(scales):>10.4f}")

    # ─── Per-Digit Comparison ───
    print(f"\n  Per-Digit Accuracy (last trial):")
    print(f"  {'Digit':<8}", end="")
    for key, label in [('baseline', 'Baseline'), ('detach', 'Detach'), ('no_detach', 'NoDetach')]:
        print(f" {label:>10}", end="")
    print(f" {'Det-Base':>10} {'NoDet-Base':>10}")
    print("  " + "-" * 62)

    baseline_digits = all_results['baseline'][-1]['digit_acc']
    detach_digits = all_results['detach'][-1]['digit_acc']
    nodetach_digits = all_results['no_detach'][-1]['digit_acc']

    digit_improvements = []
    for d in range(10):
        b = baseline_digits[d]
        dt = detach_digits[d]
        nd = nodetach_digits[d]
        diff_dt = (dt - b) * 100
        diff_nd = (nd - b) * 100
        digit_improvements.append(diff_dt)
        print(f"  {d:<8} {b*100:>9.1f}% {dt*100:>9.1f}% {nd*100:>9.1f}% "
              f"{'+' if diff_dt >= 0 else ''}{diff_dt:>8.1f}% "
              f"{'+' if diff_nd >= 0 else ''}{diff_nd:>8.1f}%")

    # ─── Does the Observer Learn Useful Corrections? ───
    print(f"\n  Observer Correction Analysis:")
    obs_scales_detach = [r['observer_scale'] for r in all_results['detach']]
    obs_scales_nodetach = [r['observer_scale'] for r in all_results['no_detach']]

    detach_scale_grew = np.mean(obs_scales_detach) > 0.1  # grew from init
    nodetach_scale_grew = np.mean(obs_scales_nodetach) > 0.1

    print(f"  Detach observer scale grew from 0.1:    {'YES' if detach_scale_grew else 'NO'} (mean={np.mean(obs_scales_detach):.4f})")
    print(f"  No-detach observer scale grew from 0.1: {'YES' if nodetach_scale_grew else 'NO'} (mean={np.mean(obs_scales_nodetach):.4f})")

    digits_improved = sum(1 for d in digit_improvements if d > 0)
    print(f"  Digits improved by detach observer: {digits_improved}/10")

    # ─── Epoch-by-Epoch Learning Curves (last trial) ───
    print(f"\n  Learning Curves (last trial, accuracy %):")
    print(f"  {'Epoch':<8}", end="")
    for label in ['Baseline', 'Detach', 'NoDetach']:
        print(f" {label:>10}", end="")
    print()
    print("  " + "-" * 40)
    for ep in range(epochs):
        b = all_results['baseline'][-1]['accs'][ep]
        dt = all_results['detach'][-1]['accs'][ep]
        nd = all_results['no_detach'][-1]['accs'][ep]
        print(f"  {ep+1:<8} {b*100:>9.2f}% {dt*100:>9.2f}% {nd*100:>9.2f}%")

    # ─── Verdict ───
    print(f"\n{'='*65}")
    print("  VERDICT")
    print(f"{'='*65}")

    if detach_delta > 0.1:
        print(f"  Detach observer IMPROVES accuracy by +{detach_delta:.2f}%")
        if detach_delta > no_detach_delta:
            print(f"  Detach is BETTER than no-detach by +{detach_delta - no_detach_delta:.2f}%")
            print(f"  -> Hypothesis 272 SUPPORTED: detach observation helps")
        else:
            print(f"  But no-detach is better: observer helps, detach not critical")
    elif detach_delta > -0.1:
        print(f"  Detach observer has NEUTRAL effect ({detach_delta:+.2f}%)")
        print(f"  -> Hypothesis 272 NOT SUPPORTED at this scale")
    else:
        print(f"  Detach observer HURTS accuracy by {detach_delta:.2f}%")
        print(f"  -> Hypothesis 272 CONTRADICTED")

    param_overhead = summary['detach']['params'] - summary['baseline']['params']
    print(f"\n  Parameter overhead: +{param_overhead:,} ({param_overhead/summary['baseline']['params']*100:.1f}%)")
    print()


if __name__ == '__main__':
    main()
