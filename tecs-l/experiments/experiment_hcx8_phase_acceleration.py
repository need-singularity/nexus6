```python
#!/usr/bin/env python3
"""H-CX-8: Phase Acceleration x3 = sigma/tau Experiment

Hypothesis: sigma/tau ratio determines convergence speed (phase acceleration).
  - sigma/tau = 3 (mean divisor of perfect number 6) setting should converge fastest.
  - Verify if this corresponds to Jamba x3 acceleration.

Experiment Design:
  6 EngineA settings (n_experts, k):
    (6,2) → sigma/tau=3    (6,3) → sigma/tau=2
    (8,2) → sigma/tau=4    (12,4) → sigma/tau=3 [original]
    (12,6) → sigma/tau=2   (12,3) → sigma/tau=4

  Create RepulsionFieldEngine variants with each setting for MNIST training.
  Measure: final accuracy, epochs to 95%, tension.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import time

from model_utils import (
    Expert, TopKGate, load_mnist, train_and_evaluate, count_params, H_TARGET
)


# ─────────────────────────────────────────
# Configurable EngineA
# ─────────────────────────────────────────

class ConfigurableEngineA(nn.Module):
    """EngineA with configurable n_experts and k."""
    def __init__(self, input_dim, hidden_dim, output_dim, n_experts=12, k=4):
        super().__init__()
        self.n_experts = n_experts
        self.k = k
        self.experts = nn.ModuleList([
            Expert(input_dim, hidden_dim, output_dim) for _ in range(n_experts)
        ])
        self.gate = TopKGate(input_dim, n_experts, k)

    def forward(self, x):
        weights = self.gate(x)
        outputs = torch.stack([e(x) for e in self.experts], dim=1)
        return (weights.unsqueeze(-1) * outputs).sum(dim=1)


class ConfigurableEngineG(nn.Module):
    """EngineG (Shannon entropy MoE) — kept at 6 experts for fair comparison."""
    def __init__(self, input_dim, hidden_dim, output_dim):
        super().__init__()
        self.experts = nn.ModuleList([
            Expert(input_dim, hidden_dim, output_dim) for _ in range(6)
        ])
        self.gate = nn.Linear(input_dim, 6)
        self.h_target = H_TARGET

    def forward(self, x):
        weights = F.softmax(self.gate(x), dim=-1)
        outputs = torch.stack([e(x) for e in self.experts], dim=1)
        result = (weights.unsqueeze(-1) * outputs).sum(dim=1)
        h = -(weights * (weights + 1e-8).log()).sum(dim=-1).mean()
        self.entropy_loss = (h - self.h_target) ** 2
        return result


class ConfigurableRepulsionField(nn.Module):
    """RepulsionFieldEngine with configurable EngineA (pole_plus)."""
    def __init__(self, input_dim=784, hidden_dim=48, output_dim=10,
                 n_experts=12, k=4):
        super().__init__()
        self.n_experts = n_experts
        self.k = k
        self.sigma_tau = n_experts / k

        self.pole_plus = ConfigurableEngineA(input_dim, hidden_dim, output_dim,
                                              n_experts=n_experts, k=k)
        self.pole_minus = ConfigurableEngineG(input_dim, hidden_dim, output_dim)

        self.field_transform = nn.Sequential(
            nn.Linear(output_dim, output_dim),
            nn.Tanh(),
        )
        self.tension_scale = nn.Parameter(torch.tensor(1/3))
        self.aux_loss = torch.tensor(0.0)
        self.tension_magnitude = 0.0

    def forward(self, x):
        out_plus = self.pole_plus(x)
        out_minus = self.pole_minus(x)

        repulsion = out_plus - out_minus
        tension = (repulsion ** 2).sum(dim=-1, keepdim=True)
        equilibrium = (out_plus + out_minus) / 2
        field_direction = self.field_transform(repulsion)
        output = equilibrium + self.tension_scale * torch.sqrt(tension + 1e-8) * field_direction

        self.aux_loss = getattr(self.pole_minus, 'entropy_loss', torch.tensor(0.0))

        with torch.no_grad():
            self.tension_magnitude = tension.mean().item()

        return (output, self.aux_loss)


# ─────────────────────────────────────────
# Experiment runner
# ─────────────────────────────────────────

def train_with_epoch_tracking(model, train_loader, test_loader, epochs=15,
                               lr=0.001, target_acc=0.95):
    """Train and track per-epoch accuracy, return epochs_to_target."""
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    criterion = nn.CrossEntropyLoss()

    epoch_accs = []
    epoch_losses = []
    epoch_tensions = []
    epochs_to_target = None

    for epoch in range(epochs):
        model.train()
        total_loss = 0
        for X, y in train_loader:
            X = X.view(X.size(0), -1)
            optimizer.zero_grad()
            out = model(X)
            if isinstance(out, tuple):
                logits, aux = out
                loss = criterion(logits, y) + 0.01 * aux
            else:
                logits = out
                loss = criterion(logits, y)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()

        avg_loss = total_loss / len(train_loader)
        epoch_losses.append(avg_loss)

        model.eval()
        correct = total = 0
        with torch.no_grad():
            for X, y in test_loader:
                X = X.view(X.size(0), -1)
                out = model(X)
                if isinstance(out, tuple):
                    out = out[0]
                correct += (out.argmax(1) == y).sum().item()
                total += y.size(0)
        acc = correct / total
        epoch_accs.append(acc)

        tension = getattr(model, 'tension_magnitude', 0.0)
        epoch_tensions.append(tension)

        if acc >= target_acc and epochs_to_target is None:
            epochs_to_target = epoch + 1

        if (epoch + 1) % 3 == 0 or epoch == 0:
            print(f"      Epoch {epoch+1:>2}/{epochs}: Loss={avg_loss:.4f}, "
                  f"Acc={acc*100:.1f}%, Tension={tension:.2f}")

    return {
        'accs': epoch_accs,
        'losses': epoch_losses,
        'tensions': epoch_tensions,
        'final_acc': epoch_accs[-1],
        'epochs_to_95': epochs_to_target,
        'final_tension': epoch_tensions[-1],
        'params': count_params(model),
    }


def main():
    print()
    print("=" * 70)
    print("  H-CX-8: Phase Acceleration x3 = sigma/tau Experiment")
    print("  Does sigma/tau ratio predict convergence speed?")
    print("=" * 70)

    # Configurations: (n_experts, k, label)
    configs = [
        (6,  2, "6e/k2"),    # sigma/tau = 3.0
        (6,  3, "6e/k3"),    # sigma/tau = 2.0
        (8,  2, "8e/k2"),    # sigma/tau = 4.0
        (12, 4, "12e/k4"),   # sigma/tau = 3.0 [original]
        (12, 6, "12e/k6"),   # sigma/tau = 2.0
        (12, 3, "12e/k3"),   # sigma/tau = 4.0
    ]

    train_loader, test_loader = load_mnist()
    input_dim, hidden_dim, output_dim = 784, 48, 10
    epochs = 15
    n_runs = 3  # multiple runs for stability

    all_results = {}

    for n_exp, k, label in configs:
        ratio = n_exp / k
        print(f"\n{'─'*70}")
        print(f"  Config: {label}  (n_experts={n_exp}, k={k}, sigma/tau={ratio:.1f})")
        print(f"{'─'*70}")

        run_results = []
        for run in range(n_runs):
            print(f"    Run {run+1}/{n_runs}:")
            torch.manual_seed(42 + run)
            np.random.seed(42 + run)

            model = ConfigurableRepulsionField(
                input_dim, hidden_dim, output_dim,
                n_experts=n_exp, k=k
            )
            result = train_with_epoch_tracking(
                model, train_loader, test_loader,
                epochs=epochs, target_acc=0.95
            )
            run_results.append(result)

        # Average across runs
        avg_acc = np.mean([r['final_acc'] for r in run_results])
        avg_tension = np.mean([r['final_tension'] for r in run_results])

        epochs_list = [r['epochs_to_95'] for r in run_results]
        valid_epochs = [e for e in epochs_list if e is not None]
        avg_epochs_to_95 = np.mean(valid_epochs) if valid_epochs else None
        reached_95_count = len(valid_epochs)

        # Per-epoch accuracy averaged across runs
        avg_epoch_accs = np.mean(
            [r['accs'] for r in run_results], axis=0
        )

        all_results[label] = {
            'n_experts': n_exp,
            'k': k,
            'sigma_tau': ratio,
            'avg_acc': avg_acc,
            'avg_epochs_to_95': avg_epochs_to_95,
            'reached_95_count': reached_95_count,
            'avg_tension': avg_tension,
            'params': run_results[0]['params'],
            'avg_epoch_accs': avg_epoch_accs,
            'individual_epochs': epochs_list,
        }

    # ─────────────────────────────────────────
    # Results table
    # ─────────────────────────────────────────
    print("\n")
    print("=" * 80)
    print("  RESULTS: sigma/tau vs Convergence Speed")
    print("=" * 80)
    print(f"  {'Config':<10} {'sigma/tau':>9} {'Final Acc':>10} {'Ep->95%':>8} "
          f"{'Reached':>8} {'Tension':>9} {'Params':>8}")
    print("-" * 80)

    # Sort by sigma/tau then by n_experts
    sorted_results = sorted(all_results.items(),
                            key=lambda x: (x[1]['sigma_tau'], x[1]['n_experts']))

    for label, r in sorted_results:
        ep_str = f"{r['avg_epochs_to_95']:.1f}" if r['avg_epochs_to_95'] is not None else "N/A"
        print(f"  {label:<10} {r['sigma_tau']:>9.1f} {r['avg_acc']*100:>9.2f}% "
              f"{ep_str:>8} {r['reached_95_count']}/{n_runs}    "
              f"{r['avg_tension']:>8.2f} {r['params']:>8,}")

    # ─────────────────────────────────────────
    # Group by sigma/tau ratio
    # ─────────────────────────────────────────
    print("\n")
    print("=" * 80)
    print("  GROUPED BY sigma/tau RATIO")
    print("=" * 80)

    ratio_groups = {}
    for label, r in all_results.items():
        ratio = r['sigma_tau']
        if ratio not in ratio_groups:
            ratio_groups[ratio] = []
        ratio_groups[ratio].append(r)

    for ratio in sorted(ratio_groups.keys()):
        group = ratio_groups[ratio]
        avg_acc = np.mean([r['avg_acc'] for r in group])
        valid_ep = [r['avg_epochs_to_95'] for r in group if r['avg_epochs_to_95'] is not None]
        avg_ep = np.mean(valid_ep) if valid_ep else None
        avg_tension = np.mean([r['avg_tension'] for r in group])

        ep_str = f"{avg_ep:.1f}" if avg_ep is not None else "N/A"
        configs_str = ", ".join(
            f"{r['n_experts']}e/k{r['k']}" for r in group
        )
        print(f"  sigma/tau = {ratio:.1f}:  Acc={avg_acc*100:.2f}%  "
              f"Ep->95%={ep_str}  Tension={avg_tension:.2f}  [{configs_str}]")

    # ─────────────────────────────────────────
    # ASCII Graph: sigma/tau vs epochs_to_95%
    # ─────────────────────────────────────────
    print("\n")
    print("=" * 80)
    print("  ASCII GRAPH: sigma/tau ratio (X) vs Epochs to 95% (Y)")
    print("  (Lower Y = faster convergence = stronger phase acceleration)")
    print("=" * 80)

    # Collect data points
    plot_data = []
    for label, r in sorted_results:
        if r['avg_epochs_to_95'] is not None:
            plot_data.append((r['sigma_tau'], r['avg_epochs_to_95'], label))

    if plot_data:
        max_ep = max(d[1] for d in plot_data)
        min_ep = min(d[1] for d in plot_data)
        graph_height = 20
        graph_width = 50

        # Y axis: epochs (inverted: top = fewer epochs = faster)
        # X axis: sigma/tau ratio
        x_vals = sorted(set(d[0] for d in plot_data))
        x_min, x_max = min(x_vals) - 0.5, max(x_vals) + 0.5

        # Create grid
        grid = [[' ' for _ in range(graph_width)] for _ in range(graph_height)]

        for ratio, ep, label in plot_data:
            x_pos = int((ratio - x_min) / (x_max - x_min) * (graph_width - 1))
            x_pos = max(0, min(graph_width - 1, x_pos))

            if max_ep > min_ep:
                y_pos = int((ep - min_ep) / (max_ep - min_ep) * (graph_height - 1))
            else:
                y_pos = graph_height // 2
            y_pos = max(0, min(graph_height - 1, y_pos))
            # Invert: top = more epochs (slower), bottom = fewer (faster)
            row = y_pos

            char = '*'
            if ratio == 3.0:
                char = '#'  # highlight sigma/tau=3
            grid[row][x_pos] = char

        # Print
        for i in range(graph_height - 1, -1, -1):
            if max_ep > min_ep:
                ep_val = min_ep + (i / (graph_height - 1)) * (max_ep - min_ep)
            else:
                ep_val = min_ep
            line = ''.join(grid[i])
            print(f"  {ep_val:>5.1f} |{line}|")

        # X axis
        print(f"        +{'─' * graph_width}+")
        x_labels = "        "
        for r in x_vals:
            pos = int((r - x_min) / (x_max - x_min) * (graph_width - 1))
            x_labels_list = list(x_labels.ljust(pos + 9))
            lbl = f"{r:.0f}"
            for ci, c in enumerate(lbl):
                if pos + 9 + ci < len(x_labels_list):
                    x_labels_list[pos + 9 + ci] = c
            x_labels = ''.join(x_labels_list)
        print(x_labels)
        print(f"        {'':>20}sigma/tau ratio")
        print()
        print("  Legend: # = sigma/tau=3 (predicted optimal), * = other ratios")
    else:
        print("  No configs reached 95% accuracy. Showing raw convergence curves.")

    # ─────────────────────────────────────────
    # Convergence curves (per-epoch accuracy)
    # ─────────────────────────────────────────
    print("\n")
    print("=" * 80)
    print("  CONVERGENCE CURVES: Accuracy per Epoch")
    print("=" * 80)
    print(f"  {'Epoch':<7}", end="")
    for label, _ in sorted_results:
        print(f" {label:>10}", end="")
    print()
    print("-" * (7 + 11 * len(sorted_results)))

    for ep in range(epochs):
        print(f"  {ep+1:<7}", end="")
        for label, r in sorted_results:
            acc = r['avg_epoch_accs'][ep]
            print(f" {acc*100:>9.2f}%", end="")
        print()

    # ─────────────────────────────────────────
    # Statistical test: correlation between sigma/tau and convergence
    # ─────────────────────────────────────────
    print("\n")
    print("=" * 80)
    print("  CORRELATION ANALYSIS")
    print("=" * 80)

    ratios = np.array([r['sigma_tau'] for r in all_results.values()])
    accs = np.array([r['avg_acc'] for r in all_results.values()])

    # Epochs to 95% (use max epochs for those that didn't reach)
    ep_to_95 = np.array([
        r['avg_epochs_to_95'] if r['avg_epochs_to_95'] is not None else epochs + 1
        for r in all_results.values()
    ])

    tensions = np.array([r['avg_tension'] for r in all_results.values()])

    # Pearson correlation
    if len(ratios) > 2:
        corr_acc = np.corrcoef(ratios, accs)[0, 1]
        corr_ep = np.corrcoef(ratios, ep_to_95)[0, 1]
        corr_tension = np.corrcoef(ratios, tensions)[0, 1]

        print(f"  Pearson r(sigma/tau, accuracy):      {corr_acc:>+.4f}")
        print(f"  Pearson r(sigma/tau, epochs_to_95):   {corr_ep:>+.4f}")
        print(f"  Pearson r(sigma/tau, tension):        {corr_tension:>+.4f}")

    # Check if sigma/tau=3 is special
    print("\n  Is sigma/tau=3 special?")
    ratio3_accs = [r['avg_acc'] for r in all_results.values() if r['sigma_tau'] == 3.0]
    other_accs = [r['avg_acc'] for r in all_results.values() if r['sigma_tau'] != 3.0]

    if ratio3_accs and other_accs:
        avg_3 = np.mean(ratio3_accs)
        avg_other = np.mean(other_accs)
        print(f"    sigma/tau=3 avg accuracy:  {avg_3*100:.2f}%")
        print(f"    Other ratios avg accuracy: {avg_other*100:.2f}%")
        print(f"    Difference:                {(avg_3 - avg_other)*100:+.2f}%")

    ratio3_eps = [r['avg_epochs_to_95'] for r in all_results.values()
                  if r['sigma_tau'] == 3.0 and r['avg_epochs_to_95'] is not None]
    other_eps = [r['avg_epochs_to_95'] for r in all_results.values()
                 if r['sigma_tau'] != 3.0 and r['avg_epochs_to_95'] is not None]

    if ratio3_eps and other_eps:
        avg_ep3 = np.mean(ratio3_eps)
        avg_ep_other = np.mean(other_eps)
        print(f"    sigma/tau=3 avg ep->95%:   {avg_ep3:.1f}")
        print(f"    Other ratios avg ep->95%:  {avg_ep_other:.1f}")
        print(f"    Speed advantage:           {(avg_ep_other - avg_ep3):+.1f} epochs faster")

    # ─────────────────────────────────────────
    # Conclusion
    # ─────────────────────────────────────────
    print("\n")
    print("=" * 80)
    print("  CONCLUSION")
    print("=" * 80)

    if ratio3_eps and other_eps:
        if avg_ep3 < avg_ep_other:
            print("  SUPPORTED: sigma/tau=3 converges faster than other ratios.")
            print(f"  Phase acceleration factor: {avg_ep_other/avg_ep3:.2f}x")
        elif avg_ep3 > avg_ep_other:
            print("  CONTRADICTED: sigma/tau=3 converges SLOWER than other ratios.")
            print(f"  Speed ratio: {avg_ep_other/avg_ep3:.2f}x (inverted)")
        else:
            print("  INCONCLUSIVE: No significant difference between ratios.")
    else:
        # Fall back to accuracy comparison
        if ratio3_accs and other_accs:
            if avg_3 > avg_other:
                print("  PARTIAL SUPPORT: sigma/tau=3 achieves higher accuracy.")
            else:
                print("  NOT SUPPORTED by accuracy data alone.")

    print()
    print("  H-CX-8 prediction: sigma/tau=3 (= mean divisor of 6) should give x3 acceleration")
    print("  Connected to: H124 (phase acceleration = step x3, Jamba)")
    print("  Connected to: sigma(6)/tau(6) = 12/4 = 3 = mean divisor")
    print()


if __name__ == '__main__':
    main()
```