#!/usr/bin/env python3
"""H311: Mitosis = Local Minimum Escape Mechanism

Tests whether mitosis (splitting a model into two noisy children) helps escape
local minima compared to:
  A) No mitosis: just continue training the parent
  B) Noise restart: add noise to parent (same scale) but don't split
  C) Mitosis: split into 2 children, train both, pick best

Setup:
  - 2-engine autoencoder on MNIST (all digits)
  - Phase 1: Train parent 15 epochs -> plateau
  - Phase 2: 3 strategies for 10 more epochs
  - 5 trials, loss comparison table
  - PCA distance between parent, child_a, child_b final positions
"""

import sys
import os
os.environ['PYTHONUNBUFFERED'] = '1'
sys.stdout.reconfigure(line_buffering=True)
sys.path.insert(0, '/Users/ghost/Dev/logout')

import torch
import torch.nn as nn
import numpy as np
import copy
from torchvision import datasets, transforms
from sklearn.decomposition import PCA

torch.manual_seed(42)
np.random.seed(42)

DEVICE = 'cpu'
PHASE1_EPOCHS = 15
PHASE2_EPOCHS = 10
MITOSIS_SCALE = 0.01
NUM_TRIALS = 5
BATCH_SIZE = 256
LR = 1e-3


# ---------------------------------------------------------------------------
# Model: 2-engine autoencoder
# ---------------------------------------------------------------------------
class DualEngineAutoencoder(nn.Module):
    def __init__(self, input_dim=784, hidden_dim=128, bottleneck=32):
        super().__init__()
        self.engine_a = nn.Sequential(
            nn.Linear(input_dim, hidden_dim), nn.ReLU(),
            nn.Linear(hidden_dim, bottleneck), nn.ReLU(),
            nn.Linear(bottleneck, hidden_dim), nn.ReLU(),
            nn.Linear(hidden_dim, input_dim), nn.Sigmoid(),
        )
        self.engine_g = nn.Sequential(
            nn.Linear(input_dim, hidden_dim), nn.ReLU(),
            nn.Linear(hidden_dim, bottleneck), nn.ReLU(),
            nn.Linear(bottleneck, hidden_dim), nn.ReLU(),
            nn.Linear(hidden_dim, input_dim), nn.Sigmoid(),
        )

    def forward(self, x):
        a = self.engine_a(x)
        g = self.engine_g(x)
        out = (a + g) / 2
        return out

    def param_vector(self):
        """Flatten all parameters into a single vector."""
        return torch.cat([p.detach().flatten() for p in self.parameters()])


def mitosis(parent, scale=0.01):
    """Split parent into two children with small random perturbation."""
    c_a = copy.deepcopy(parent)
    c_b = copy.deepcopy(parent)
    with torch.no_grad():
        for p in c_a.parameters():
            p.add_(torch.randn_like(p) * scale)
        for p in c_b.parameters():
            p.add_(torch.randn_like(p) * scale)
    return c_a, c_b


def add_noise(model, scale=0.01):
    """Add noise to model parameters (no split)."""
    noised = copy.deepcopy(model)
    with torch.no_grad():
        for p in noised.parameters():
            p.add_(torch.randn_like(p) * scale)
    return noised


# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------
def get_mnist_loaders():
    transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Lambda(lambda x: x.view(-1)),
    ])
    train_ds = datasets.MNIST('/tmp/mnist', train=True, download=True, transform=transform)
    test_ds = datasets.MNIST('/tmp/mnist', train=False, download=True, transform=transform)
    train_loader = torch.utils.data.DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True)
    test_loader = torch.utils.data.DataLoader(test_ds, batch_size=BATCH_SIZE, shuffle=False)
    return train_loader, test_loader


def eval_loss(model, loader):
    """Compute average MSE loss on a data loader."""
    model.eval()
    total_loss = 0.0
    count = 0
    with torch.no_grad():
        for x, _ in loader:
            x = x.to(DEVICE)
            out = model(x)
            total_loss += nn.functional.mse_loss(out, x, reduction='sum').item()
            count += x.size(0)
    return total_loss / count


def train_epoch(model, loader, optimizer):
    """Train one epoch, return average loss."""
    model.train()
    total_loss = 0.0
    count = 0
    for x, _ in loader:
        x = x.to(DEVICE)
        out = model(x)
        loss = nn.functional.mse_loss(out, x)
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        total_loss += loss.item() * x.size(0)
        count += x.size(0)
    return total_loss / count


def train_model(model, loader, epochs, lr=LR):
    """Train model for N epochs, return per-epoch losses."""
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    losses = []
    for ep in range(epochs):
        l = train_epoch(model, loader, optimizer)
        losses.append(l)
    return losses


# ---------------------------------------------------------------------------
# Main experiment
# ---------------------------------------------------------------------------
def run_trial(trial_idx, train_loader, test_loader):
    """Run one trial: parent training + 3 strategies."""
    torch.manual_seed(42 + trial_idx * 1000)

    # Phase 1: Train parent
    parent = DualEngineAutoencoder().to(DEVICE)
    phase1_losses = train_model(parent, train_loader, PHASE1_EPOCHS)
    parent_plateau_loss = eval_loss(parent, test_loader)
    parent_snapshot = copy.deepcopy(parent)
    parent_params = parent.param_vector().numpy()

    print(f"  Trial {trial_idx+1}: Phase 1 done. Plateau test loss = {parent_plateau_loss:.6f}")
    print(f"    Phase 1 train losses: {' -> '.join(f'{l:.5f}' for l in phase1_losses[::3])}")

    # Strategy A: Continue training parent (no mitosis)
    model_a = copy.deepcopy(parent_snapshot)
    a_losses = train_model(model_a, train_loader, PHASE2_EPOCHS)
    a_final_loss = eval_loss(model_a, test_loader)
    a_params = model_a.param_vector().numpy()

    # Strategy B: Noise restart (add noise, no split)
    model_b = add_noise(parent_snapshot, scale=MITOSIS_SCALE)
    b_losses = train_model(model_b, train_loader, PHASE2_EPOCHS)
    b_final_loss = eval_loss(model_b, test_loader)
    b_params = model_b.param_vector().numpy()

    # Strategy C: Mitosis (split into 2 children)
    child_a, child_b = mitosis(parent_snapshot, scale=MITOSIS_SCALE)
    ca_losses = train_model(child_a, train_loader, PHASE2_EPOCHS)
    cb_losses = train_model(child_b, train_loader, PHASE2_EPOCHS)
    ca_final_loss = eval_loss(child_a, test_loader)
    cb_final_loss = eval_loss(child_b, test_loader)
    c_best_loss = min(ca_final_loss, cb_final_loss)
    ca_params = child_a.param_vector().numpy()
    cb_params = child_b.param_vector().numpy()

    # Ensemble: average outputs of both children
    ensemble_loss = eval_ensemble(child_a, child_b, test_loader)

    # PCA distance analysis
    all_params = np.stack([parent_params, a_params, b_params, ca_params, cb_params])
    pca = PCA(n_components=2)
    coords = pca.fit_transform(all_params)

    # Euclidean distances in full param space
    dist_ca_parent = np.linalg.norm(ca_params - parent_params)
    dist_cb_parent = np.linalg.norm(cb_params - parent_params)
    dist_ca_cb = np.linalg.norm(ca_params - cb_params)
    dist_a_parent = np.linalg.norm(a_params - parent_params)
    dist_b_parent = np.linalg.norm(b_params - parent_params)

    return {
        'parent_plateau': parent_plateau_loss,
        'a_continue': a_final_loss,
        'b_noise': b_final_loss,
        'c_best_child': c_best_loss,
        'c_child_a': ca_final_loss,
        'c_child_b': cb_final_loss,
        'c_ensemble': ensemble_loss,
        'phase1_losses': phase1_losses,
        'a_losses': a_losses,
        'b_losses': b_losses,
        'ca_losses': ca_losses,
        'cb_losses': cb_losses,
        'pca_coords': coords,
        'dist_ca_parent': dist_ca_parent,
        'dist_cb_parent': dist_cb_parent,
        'dist_ca_cb': dist_ca_cb,
        'dist_a_parent': dist_a_parent,
        'dist_b_parent': dist_b_parent,
    }


def eval_ensemble(model_a, model_b, loader):
    """Average outputs of two models, compute MSE."""
    model_a.eval()
    model_b.eval()
    total_loss = 0.0
    count = 0
    with torch.no_grad():
        for x, _ in loader:
            x = x.to(DEVICE)
            out_a = model_a(x)
            out_b = model_b(x)
            out = (out_a + out_b) / 2
            total_loss += nn.functional.mse_loss(out, x, reduction='sum').item()
            count += x.size(0)
    return total_loss / count


def ascii_loss_curve(losses_dict, width=60, height=15):
    """Draw ASCII loss curves for multiple strategies."""
    all_vals = []
    for v in losses_dict.values():
        all_vals.extend(v)
    lo, hi = min(all_vals), max(all_vals)
    if hi - lo < 1e-8:
        hi = lo + 1e-8

    max_len = max(len(v) for v in losses_dict.values())
    symbols = {'Phase1': '.', 'A:Continue': 'A', 'B:Noise': 'B', 'C:Child_a': 'a', 'C:Child_b': 'b'}

    print(f"\n  Loss curve (y: {lo:.5f} to {hi:.5f})")
    print(f"  {'':>10} {'|'}", end='')
    for i in range(max_len):
        if i % 5 == 0:
            print(f"{i:>2}", end='')
        else:
            print(' ', end='')
    print()

    # Build grid
    grid = [[' ' for _ in range(max_len)] for _ in range(height)]
    for name, vals in losses_dict.items():
        sym = symbols.get(name, '?')
        for i, v in enumerate(vals):
            row = int((1 - (v - lo) / (hi - lo)) * (height - 1))
            row = max(0, min(height - 1, row))
            if i < max_len:
                grid[row][i] = sym

    for r in range(height):
        y_val = hi - r * (hi - lo) / (height - 1)
        print(f"  {y_val:.5f} |{''.join(grid[r])}")
    print(f"  {'':>10} +{''.join(['-'] * max_len)}")
    print(f"  {'':>10}  {'epoch':^{max_len}}")
    print(f"  Legend: .=Phase1  A=Continue  B=Noise  a=Child_a  b=Child_b")


def ascii_pca_plot(coords, labels, width=50, height=20):
    """Plot PCA coordinates as ASCII."""
    xs = coords[:, 0]
    ys = coords[:, 1]
    x_lo, x_hi = xs.min(), xs.max()
    y_lo, y_hi = ys.min(), ys.max()
    # Add margin
    x_range = max(x_hi - x_lo, 1e-6) * 1.1
    y_range = max(y_hi - y_lo, 1e-6) * 1.1
    x_mid = (x_lo + x_hi) / 2
    y_mid = (y_lo + y_hi) / 2

    grid = [[' ' for _ in range(width)] for _ in range(height)]
    for i, (x, y) in enumerate(zip(xs, ys)):
        col = int(((x - x_mid) / x_range + 0.5) * (width - 1))
        row = int((0.5 - (y - y_mid) / y_range) * (height - 1))
        col = max(0, min(width - 1, col))
        row = max(0, min(height - 1, row))
        sym = labels[i][0]  # first char
        grid[row][col] = sym

    print("\n  PCA of parameter space (P=Parent, A=Continue, B=Noise, a=Child_a, b=Child_b)")
    for r in range(height):
        print(f"  |{''.join(grid[r])}|")
    print(f"  +{'-' * width}+")


def main():
    print("=" * 70)
    print("H311: Mitosis = Local Minimum Escape Mechanism")
    print("=" * 70)
    print(f"  Phase 1: {PHASE1_EPOCHS} epochs (plateau)")
    print(f"  Phase 2: {PHASE2_EPOCHS} epochs (escape attempt)")
    print(f"  Mitosis scale: {MITOSIS_SCALE}")
    print(f"  Trials: {NUM_TRIALS}")
    print(f"  Device: {DEVICE}")
    print()

    train_loader, test_loader = get_mnist_loaders()

    results = []
    for t in range(NUM_TRIALS):
        print(f"\n--- Trial {t+1}/{NUM_TRIALS} ---")
        r = run_trial(t, train_loader, test_loader)
        results.append(r)

        # Print per-trial quick summary
        print(f"    Parent plateau:  {r['parent_plateau']:.6f}")
        print(f"    A) Continue:     {r['a_continue']:.6f}  (delta={r['a_continue'] - r['parent_plateau']:.6f})")
        print(f"    B) Noise:        {r['b_noise']:.6f}  (delta={r['b_noise'] - r['parent_plateau']:.6f})")
        print(f"    C) Best child:   {r['c_best_child']:.6f}  (delta={r['c_best_child'] - r['parent_plateau']:.6f})")
        print(f"    C) Ensemble:     {r['c_ensemble']:.6f}  (delta={r['c_ensemble'] - r['parent_plateau']:.6f})")

    # -----------------------------------------------------------------------
    # Summary table
    # -----------------------------------------------------------------------
    print("\n" + "=" * 70)
    print("LOSS COMPARISON TABLE (test MSE)")
    print("=" * 70)

    header = f"{'Trial':>6} | {'Parent':>10} | {'A:Continue':>10} | {'B:Noise':>10} | {'C:Best':>10} | {'C:Ensemble':>10} | {'Winner':>10}"
    print(header)
    print("-" * len(header))

    winners = {'A': 0, 'B': 0, 'C_best': 0, 'C_ens': 0}
    for i, r in enumerate(results):
        strats = {
            'A': r['a_continue'],
            'B': r['b_noise'],
            'C_best': r['c_best_child'],
            'C_ens': r['c_ensemble'],
        }
        winner = min(strats, key=strats.get)
        winners[winner] += 1
        print(f"  {i+1:>4} | {r['parent_plateau']:>10.6f} | {r['a_continue']:>10.6f} | {r['b_noise']:>10.6f} | {r['c_best_child']:>10.6f} | {r['c_ensemble']:>10.6f} | {winner:>10}")

    print("-" * len(header))

    # Averages
    avg = lambda key: np.mean([r[key] for r in results])
    std = lambda key: np.std([r[key] for r in results])
    print(f"  {'Mean':>4} | {avg('parent_plateau'):>10.6f} | {avg('a_continue'):>10.6f} | {avg('b_noise'):>10.6f} | {avg('c_best_child'):>10.6f} | {avg('c_ensemble'):>10.6f} |")
    print(f"  {'Std':>4} | {std('parent_plateau'):>10.6f} | {std('a_continue'):>10.6f} | {std('b_noise'):>10.6f} | {std('c_best_child'):>10.6f} | {std('c_ensemble'):>10.6f} |")

    print(f"\n  Winner counts: A={winners['A']} B={winners['B']} C_best={winners['C_best']} C_ensemble={winners['C_ens']}")

    # Improvement over parent
    print(f"\n  Average improvement over parent plateau (negative = better):")
    print(f"    A) Continue:   {avg('a_continue') - avg('parent_plateau'):>+.6f}")
    print(f"    B) Noise:      {avg('b_noise') - avg('parent_plateau'):>+.6f}")
    print(f"    C) Best child: {avg('c_best_child') - avg('parent_plateau'):>+.6f}")
    print(f"    C) Ensemble:   {avg('c_ensemble') - avg('parent_plateau'):>+.6f}")

    # -----------------------------------------------------------------------
    # PCA distance table
    # -----------------------------------------------------------------------
    print("\n" + "=" * 70)
    print("PCA DISTANCE TABLE (L2 in full parameter space)")
    print("=" * 70)
    dist_header = f"{'Trial':>6} | {'A-Parent':>10} | {'B-Parent':>10} | {'Ca-Parent':>10} | {'Cb-Parent':>10} | {'Ca-Cb':>10}"
    print(dist_header)
    print("-" * len(dist_header))
    for i, r in enumerate(results):
        print(f"  {i+1:>4} | {r['dist_a_parent']:>10.2f} | {r['dist_b_parent']:>10.2f} | {r['dist_ca_parent']:>10.2f} | {r['dist_cb_parent']:>10.2f} | {r['dist_ca_cb']:>10.2f}")
    print("-" * len(dist_header))
    print(f"  {'Mean':>4} | {avg('dist_a_parent'):>10.2f} | {avg('dist_b_parent'):>10.2f} | {avg('dist_ca_parent'):>10.2f} | {avg('dist_cb_parent'):>10.2f} | {avg('dist_ca_cb'):>10.2f}")

    # -----------------------------------------------------------------------
    # Loss curves (last trial)
    # -----------------------------------------------------------------------
    r = results[-1]
    full_phase1 = r['phase1_losses']
    full_a = full_phase1 + r['a_losses']
    full_b = full_phase1 + r['b_losses']
    full_ca = full_phase1 + r['ca_losses']
    full_cb = full_phase1 + r['cb_losses']

    ascii_loss_curve({
        'Phase1': full_phase1,
        'A:Continue': full_a,
        'B:Noise': full_b,
        'C:Child_a': full_ca,
        'C:Child_b': full_cb,
    })

    # PCA plot (last trial)
    labels = ['Parent', 'A:Continue', 'B:Noise', 'Child_a', 'Child_b']
    ascii_pca_plot(r['pca_coords'], labels)

    # -----------------------------------------------------------------------
    # Escape analysis
    # -----------------------------------------------------------------------
    print("\n" + "=" * 70)
    print("ESCAPE ANALYSIS")
    print("=" * 70)

    escape_a = sum(1 for r in results if r['a_continue'] < r['parent_plateau'])
    escape_b = sum(1 for r in results if r['b_noise'] < r['parent_plateau'])
    escape_c = sum(1 for r in results if r['c_best_child'] < r['parent_plateau'])
    escape_e = sum(1 for r in results if r['c_ensemble'] < r['parent_plateau'])

    print(f"  Escaped plateau (lower loss than parent):")
    print(f"    A) Continue:   {escape_a}/{NUM_TRIALS}")
    print(f"    B) Noise:      {escape_b}/{NUM_TRIALS}")
    print(f"    C) Best child: {escape_c}/{NUM_TRIALS}")
    print(f"    C) Ensemble:   {escape_e}/{NUM_TRIALS}")

    # Did children diverge?
    avg_ca_cb_dist = np.mean([r['dist_ca_cb'] for r in results])
    avg_a_parent_dist = np.mean([r['dist_a_parent'] for r in results])
    print(f"\n  Average child-child distance: {avg_ca_cb_dist:.2f}")
    print(f"  Average continue-parent distance: {avg_a_parent_dist:.2f}")
    print(f"  Divergence ratio (children / continue): {avg_ca_cb_dist / max(avg_a_parent_dist, 1e-8):.2f}x")

    # Verdict
    print("\n" + "=" * 70)
    print("VERDICT")
    print("=" * 70)
    best_strategy = min(
        [('A:Continue', avg('a_continue')),
         ('B:Noise', avg('b_noise')),
         ('C:Best_child', avg('c_best_child')),
         ('C:Ensemble', avg('c_ensemble'))],
        key=lambda x: x[1]
    )
    print(f"  Best strategy: {best_strategy[0]} (avg loss = {best_strategy[1]:.6f})")
    print(f"  Parent plateau avg: {avg('parent_plateau'):.6f}")
    improvement = avg('parent_plateau') - best_strategy[1]
    pct = improvement / avg('parent_plateau') * 100
    print(f"  Improvement: {improvement:.6f} ({pct:.2f}%)")

    if best_strategy[0].startswith('C'):
        print(f"\n  >>> MITOSIS WINS: Splitting helps escape local minima! <<<")
        print(f"  H311 SUPPORTED")
    elif best_strategy[0] == 'B:Noise':
        print(f"\n  >>> NOISE WINS: Perturbation helps, but splitting not necessary <<<")
        print(f"  H311 PARTIALLY SUPPORTED (noise is the key, not splitting)")
    else:
        print(f"\n  >>> CONTINUE WINS: No escape mechanism needed <<<")
        print(f"  H311 NOT SUPPORTED (model was not truly stuck)")

    print("\nDone.")


if __name__ == '__main__':
    main()
