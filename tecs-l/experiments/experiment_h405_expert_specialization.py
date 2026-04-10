#!/usr/bin/env python3
"""H-405 Verification: AnimaLM Expert Topological Specialization

Measures PH divergence between A-camp and G-camp experts during training.
Tests: Does topological specialization correlate with accuracy?

Key metrics per epoch:
- H0 total persistence for A-camp and G-camp
- H1 total persistence for A-camp and G-camp
- Wasserstein-like distance between A and G barcodes
- Test accuracy

MNIST + CIFAR-10, 1 seed (measurement experiment, not comparison).
"""
import sys
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader
from torchvision import datasets, transforms
import numpy as np
import time
from scipy import stats

print = lambda *a, **k: (sys.stdout.write(' '.join(map(str, a)) + k.get('end', '\n')), sys.stdout.flush())

try:
    from ripser import ripser
    HAS_RIPSER = True
except ImportError:
    HAS_RIPSER = False
    print("WARNING: ripser not available")


def compute_ph_metrics(representations, maxdim=1, n_subsample=64):
    """Compute PH metrics for a set of representations."""
    x = representations.detach().cpu().numpy()
    if x.shape[0] > n_subsample:
        idx = np.random.choice(x.shape[0], n_subsample, replace=False)
        x = x[idx]

    metrics = {'h0_total_pers': 0.0, 'h1_total_pers': 0.0, 'h0_count': 0, 'h1_count': 0}

    if not HAS_RIPSER or x.shape[0] < 3:
        return metrics

    try:
        result = ripser(x, maxdim=maxdim)
        for dim in [0, 1]:
            dgm = result['dgms'][dim]
            finite_mask = np.isfinite(dgm[:, 1])
            dgm_fin = dgm[finite_mask]
            if len(dgm_fin) > 0:
                pers = dgm_fin[:, 1] - dgm_fin[:, 0]
                key = f'h{dim}_total_pers'
                metrics[key] = float(pers.sum())
                metrics[f'h{dim}_count'] = len(pers)
    except Exception as e:
        pass

    return metrics


def barcode_distance(repr_a, repr_g, n_subsample=64):
    """Compute approximate barcode distance between two representation sets."""
    a = repr_a.detach().cpu().numpy()
    g = repr_g.detach().cpu().numpy()
    if a.shape[0] > n_subsample:
        a = a[np.random.choice(a.shape[0], n_subsample, replace=False)]
    if g.shape[0] > n_subsample:
        g = g[np.random.choice(g.shape[0], n_subsample, replace=False)]

    if not HAS_RIPSER or a.shape[0] < 3 or g.shape[0] < 3:
        return 0.0

    try:
        res_a = ripser(a, maxdim=0)['dgms'][0]
        res_g = ripser(g, maxdim=0)['dgms'][0]
        res_a = res_a[np.isfinite(res_a[:, 1])]
        res_g = res_g[np.isfinite(res_g[:, 1])]
        pers_a = (res_a[:, 1] - res_a[:, 0]).sum() if len(res_a) > 0 else 0
        pers_g = (res_g[:, 1] - res_g[:, 0]).sum() if len(res_g) > 0 else 0
        return abs(pers_a - pers_g) / (pers_a + pers_g + 1e-8)
    except Exception:
        return 0.0


class Expert(nn.Module):
    def __init__(self, input_dim, hidden_dim, output_dim, dropout=0.5):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden_dim), nn.ReLU(), nn.Dropout(dropout),
            nn.Linear(hidden_dim, output_dim),
        )
    def forward(self, x):
        return self.net(x)


class Expert3L(nn.Module):
    def __init__(self, input_dim, hidden_dim, output_dim, dropout=0.5):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden_dim), nn.ReLU(), nn.Dropout(dropout),
            nn.Linear(hidden_dim, hidden_dim), nn.ReLU(), nn.Dropout(dropout),
            nn.Linear(hidden_dim, output_dim),
        )
    def forward(self, x):
        return self.net(x)


class BoltzmannGate(nn.Module):
    def __init__(self, input_dim, n_experts, temperature=np.e, active_ratio=0.625):
        super().__init__()
        self.gate = nn.Linear(input_dim, n_experts)
        self.temperature = temperature
        self.n_active = max(1, int(n_experts * active_ratio))

    def forward(self, x):
        scores = self.gate(x) / self.temperature
        probs = F.softmax(scores, dim=-1)
        topk_vals, topk_idx = probs.topk(self.n_active, dim=-1)
        mask = torch.zeros_like(probs)
        mask.scatter_(-1, topk_idx, 1.0)
        weights = probs * mask
        return weights / (weights.sum(dim=-1, keepdim=True) + 1e-8)


class AnimaLMTracked(nn.Module):
    """AnimaLM with per-camp output tracking for PH analysis."""
    def __init__(self, input_dim, hidden_dim, output_dim, n_experts=8, ExpertCls=Expert):
        super().__init__()
        self.n_camp_a = n_experts // 2
        self.n_experts = n_experts
        self.experts = nn.ModuleList([ExpertCls(input_dim, hidden_dim, output_dim) for _ in range(n_experts)])
        self.gate = BoltzmannGate(input_dim, n_experts)
        self.last_out_a = None
        self.last_out_g = None

    def forward(self, x):
        weights = self.gate(x)
        odim = self.experts[0].net[-1].out_features
        out_a = torch.zeros(x.size(0), odim, device=x.device)
        out_g = torch.zeros_like(out_a)
        for i, expert in enumerate(self.experts):
            w = weights[:, i].unsqueeze(-1)
            e_out = expert(x)
            if i < self.n_camp_a:
                out_a = out_a + w * e_out
            else:
                out_g = out_g + w * e_out
        self.last_out_a = out_a
        self.last_out_g = out_g
        return out_a - out_g


def run_experiment(dataset_name, input_dim, hidden_dim, epochs, ExpertCls, device):
    if dataset_name == 'MNIST':
        transform = transforms.Compose([transforms.ToTensor(), transforms.Normalize((0.1307,), (0.3081,))])
        train_data = datasets.MNIST('./data', train=True, download=True, transform=transform)
        test_data = datasets.MNIST('./data', train=False, transform=transform)
    else:
        transform = transforms.Compose([transforms.ToTensor(), transforms.Normalize((0.5,0.5,0.5), (0.5,0.5,0.5))])
        train_data = datasets.CIFAR10('./data', train=True, download=True, transform=transform)
        test_data = datasets.CIFAR10('./data', train=False, transform=transform)

    train_loader = DataLoader(train_data, batch_size=128, shuffle=True, num_workers=0)
    test_loader = DataLoader(test_data, batch_size=256, num_workers=0)

    torch.manual_seed(42)
    np.random.seed(42)
    model = AnimaLMTracked(input_dim, hidden_dim, 10, ExpertCls=ExpertCls).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
    criterion = nn.CrossEntropyLoss()

    epoch_data = []

    for epoch in range(epochs):
        model.train()
        for X, y in train_loader:
            X = X.view(X.size(0), -1).to(device)
            y = y.to(device)
            optimizer.zero_grad()
            out = model(X)
            loss = criterion(out, y)
            loss.backward()
            optimizer.step()

        # Evaluate + PH measurement
        model.eval()
        correct = total = 0
        all_out_a = []
        all_out_g = []

        with torch.no_grad():
            for X, y in test_loader:
                X = X.view(X.size(0), -1).to(device)
                y = y.to(device)
                out = model(X)
                correct += (out.argmax(1) == y).sum().item()
                total += y.size(0)
                all_out_a.append(model.last_out_a.cpu())
                all_out_g.append(model.last_out_g.cpu())

        acc = correct / total
        out_a_all = torch.cat(all_out_a)
        out_g_all = torch.cat(all_out_g)

        # PH measurements (subsample for speed)
        ph_a = compute_ph_metrics(out_a_all, maxdim=1, n_subsample=128)
        ph_g = compute_ph_metrics(out_g_all, maxdim=1, n_subsample=128)
        bd = barcode_distance(out_a_all, out_g_all, n_subsample=128)

        # Randomized control: shuffle A/G assignment
        n_half = out_a_all.size(0) // 2
        perm = torch.randperm(out_a_all.size(0))
        random_a = out_a_all[perm[:n_half]]
        random_g = out_g_all[perm[n_half:]]
        bd_random = barcode_distance(random_a, random_g, n_subsample=128)

        epoch_data.append({
            'epoch': epoch + 1,
            'acc': acc,
            'a_h0': ph_a['h0_total_pers'],
            'a_h1': ph_a['h1_total_pers'],
            'g_h0': ph_g['h0_total_pers'],
            'g_h1': ph_g['h1_total_pers'],
            'bd': bd,
            'bd_random': bd_random,
        })

        print(f"  Ep {epoch+1:>2}: acc={acc*100:.2f}%  "
              f"A_H0={ph_a['h0_total_pers']:.3f} G_H0={ph_g['h0_total_pers']:.3f}  "
              f"A_H1={ph_a['h1_total_pers']:.3f} G_H1={ph_g['h1_total_pers']:.3f}  "
              f"BD={bd:.4f} BD_rand={bd_random:.4f}")

    return epoch_data


def analyze_results(dataset_name, epoch_data):
    print(f"\n{'=' * 80}")
    print(f"  H-405: Expert Topological Specialization — {dataset_name}")
    print(f"{'=' * 80}")

    # Table
    print(f"\n  {'Ep':>3} | {'Acc':>7} | {'A_H0':>7} | {'G_H0':>7} | {'A_H1':>7} | {'G_H1':>7} | {'BD':>7} | {'BD_rnd':>7}")
    print(f"  {'─'*3}-+-{'─'*7}-+-{'─'*7}-+-{'─'*7}-+-{'─'*7}-+-{'─'*7}-+-{'─'*7}-+-{'─'*7}")
    for d in epoch_data:
        print(f"  {d['epoch']:>3} | {d['acc']*100:5.2f}% | {d['a_h0']:7.3f} | {d['g_h0']:7.3f} | "
              f"{d['a_h1']:7.3f} | {d['g_h1']:7.3f} | {d['bd']:7.4f} | {d['bd_random']:7.4f}")

    # Correlations
    accs = [d['acc'] for d in epoch_data]
    bds = [d['bd'] for d in epoch_data]
    a_h0s = [d['a_h0'] for d in epoch_data]
    g_h0s = [d['g_h0'] for d in epoch_data]
    h0_diffs = [abs(d['a_h0'] - d['g_h0']) for d in epoch_data]

    if len(accs) >= 3:
        r_bd, p_bd = stats.spearmanr(bds, accs)
        r_h0diff, p_h0diff = stats.spearmanr(h0_diffs, accs)
        print(f"\n  Correlations:")
        print(f"    BD vs Acc:       r={r_bd:.4f}  p={p_bd:.4f}")
        print(f"    |H0_A-H0_G| vs Acc: r={r_h0diff:.4f}  p={p_h0diff:.4f}")

        # BD real vs random
        bd_reals = [d['bd'] for d in epoch_data]
        bd_randoms = [d['bd_random'] for d in epoch_data]
        mean_real = np.mean(bd_reals)
        mean_random = np.mean(bd_randoms)
        print(f"\n  Barcode distance: real={mean_real:.4f} vs random={mean_random:.4f}")
        if mean_real > mean_random * 1.2:
            print(f"    -> A/G split produces HIGHER divergence than random (+{(mean_real/mean_random-1)*100:.1f}%)")
        else:
            print(f"    -> A/G split similar to random (ratio={mean_real/mean_random:.2f})")

        # ASCII graph: BD over epochs
        print(f"\n  Barcode Distance over epochs:")
        max_bd = max(max(bd_reals), max(bd_randoms), 0.001)
        for i, d in enumerate(epoch_data):
            bar_len = int(d['bd'] / max_bd * 40)
            rand_len = int(d['bd_random'] / max_bd * 40)
            print(f"    Ep{d['epoch']:>2} real: {'█' * bar_len:40s} {d['bd']:.4f}")
            print(f"         rand: {'░' * rand_len:40s} {d['bd_random']:.4f}")

        # Verdict
        print(f"\n  VERDICT for {dataset_name}:")
        if r_bd > 0.5 and p_bd < 0.05:
            print(f"    -> SUPPORTED: BD correlates with accuracy (r={r_bd:.3f}, p={p_bd:.4f})")
        elif r_bd > 0.3:
            print(f"    -> PARTIAL: Weak correlation (r={r_bd:.3f}, p={p_bd:.4f})")
        else:
            print(f"    -> NOT SUPPORTED: No correlation (r={r_bd:.3f}, p={p_bd:.4f})")

    return epoch_data


def main():
    print("=" * 80)
    print("  H-405: AnimaLM Expert Topological Specialization")
    print("  Do A-camp and G-camp develop distinct PH signatures?")
    print("=" * 80)

    device = 'mps' if torch.backends.mps.is_available() else 'cpu'
    print(f"  Device: {device}")
    print(f"  Ripser: {'available' if HAS_RIPSER else 'NOT available'}")

    # MNIST
    print(f"\n{'─' * 80}")
    print(f"  MNIST (10 epochs)")
    print(f"{'─' * 80}")
    mnist_data = run_experiment('MNIST', 784, 64, 10, Expert, device)
    analyze_results('MNIST', mnist_data)

    # CIFAR-10
    print(f"\n{'─' * 80}")
    print(f"  CIFAR-10 (15 epochs)")
    print(f"{'─' * 80}")
    cifar_data = run_experiment('CIFAR', 3072, 128, 15, Expert3L, device)
    analyze_results('CIFAR-10', cifar_data)

    # Cross-dataset comparison
    print(f"\n{'=' * 80}")
    print(f"  Cross-dataset Summary")
    print(f"{'=' * 80}")
    for ds, data in [('MNIST', mnist_data), ('CIFAR', cifar_data)]:
        final = data[-1]
        init = data[0]
        print(f"\n  {ds}:")
        print(f"    Acc: {init['acc']*100:.1f}% -> {final['acc']*100:.1f}%")
        print(f"    BD:  {init['bd']:.4f} -> {final['bd']:.4f} (change: {(final['bd']-init['bd']):.4f})")
        print(f"    A_H0: {init['a_h0']:.3f} -> {final['a_h0']:.3f}")
        print(f"    G_H0: {init['g_h0']:.3f} -> {final['g_h0']:.3f}")

    print(f"\n{'=' * 80}")


if __name__ == '__main__':
    main()
