#!/usr/bin/env python3
"""H-401 Verification: PH-Corrected Repulsion Field

Tests whether PH correction (barcode distance between Engine A and G representations)
improves AnimaLM output quality by distinguishing content vs structural tension.

Models compared:
1. Raw Repulsion: output = A - G  (baseline, H-404 winner)
2. PH-Corrected: output = (A - G) * PH_correction(repr_A, repr_G)
3. Oracle PH: output = (A - G) * confidence_based_correction (upper bound)

Uses Ripser for persistent homology on intermediate representations.
MNIST + CIFAR-10, 2 seeds each.
"""
import sys
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader
from torchvision import datasets, transforms
import numpy as np
import time

print = lambda *a, **k: (sys.stdout.write(' '.join(map(str, a)) + k.get('end', '\n')), sys.stdout.flush())

try:
    from ripser import ripser
    HAS_RIPSER = True
except ImportError:
    HAS_RIPSER = False
    print("WARNING: ripser not available, using distance-matrix proxy for PH")


# ─── PH Utilities ───

def compute_barcode_distance(repr_a, repr_g, max_dim=0, n_subsample=32):
    """Compute approximate topological distance between two representation sets.

    Uses Ripser H0 persistence diagrams + Wasserstein-like distance.
    For speed, subsamples to n_subsample points.
    """
    a = repr_a.detach().cpu().numpy()
    g = repr_g.detach().cpu().numpy()

    # Subsample for speed
    if a.shape[0] > n_subsample:
        idx = np.random.choice(a.shape[0], n_subsample, replace=False)
        a = a[idx]
    if g.shape[0] > n_subsample:
        idx = np.random.choice(g.shape[0], n_subsample, replace=False)
        g = g[idx]

    if HAS_RIPSER:
        try:
            dgm_a = ripser(a, maxdim=max_dim)['dgms'][0]
            dgm_g = ripser(g, maxdim=max_dim)['dgms'][0]

            # Remove infinite death points
            dgm_a = dgm_a[np.isfinite(dgm_a[:, 1])]
            dgm_g = dgm_g[np.isfinite(dgm_g[:, 1])]

            # Persistence: death - birth
            pers_a = dgm_a[:, 1] - dgm_a[:, 0] if len(dgm_a) > 0 else np.array([0.0])
            pers_g = dgm_g[:, 1] - dgm_g[:, 0] if len(dgm_g) > 0 else np.array([0.0])

            # Simple barcode distance: difference in total persistence
            bd = abs(pers_a.sum() - pers_g.sum()) / (pers_a.sum() + pers_g.sum() + 1e-8)
            return float(bd)
        except Exception:
            pass

    # Fallback: use distribution difference as proxy
    mean_diff = np.linalg.norm(a.mean(0) - g.mean(0))
    std_diff = abs(a.std() - g.std())
    return float(mean_diff / (mean_diff + 1.0)) + float(std_diff / (std_diff + 1.0)) * 0.3


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


# ─── 1. Raw Repulsion Baseline ───
class AnimaRaw(nn.Module):
    def __init__(self, input_dim, hidden_dim, output_dim, n_experts=8, ExpertCls=Expert):
        super().__init__()
        self.n_camp_a = n_experts // 2
        self.experts = nn.ModuleList([ExpertCls(input_dim, hidden_dim, output_dim) for _ in range(n_experts)])
        self.gate = BoltzmannGate(input_dim, n_experts)
        self.repr_a_cache = None
        self.repr_g_cache = None

    def forward(self, x):
        weights = self.gate(x)
        out_a = torch.zeros(x.size(0), self.experts[0].net[-1].out_features, device=x.device)
        out_g = torch.zeros_like(out_a)
        for i, expert in enumerate(self.experts):
            w = weights[:, i].unsqueeze(-1)
            e_out = expert(x)
            if i < self.n_camp_a:
                out_a = out_a + w * e_out
            else:
                out_g = out_g + w * e_out
        self.repr_a_cache = out_a
        self.repr_g_cache = out_g
        return out_a - out_g


# ─── 2. PH-Corrected Repulsion ───
class AnimaPHCorrected(nn.Module):
    """output = (A - G) * sigmoid(alpha * barcode_distance + beta) * 2"""
    def __init__(self, input_dim, hidden_dim, output_dim, n_experts=8, ExpertCls=Expert):
        super().__init__()
        self.n_camp_a = n_experts // 2
        self.experts = nn.ModuleList([ExpertCls(input_dim, hidden_dim, output_dim) for _ in range(n_experts)])
        self.gate = BoltzmannGate(input_dim, n_experts)
        # Learnable PH correction parameters
        self.ph_alpha = nn.Parameter(torch.tensor(1.0))
        self.ph_beta = nn.Parameter(torch.tensor(0.0))
        self.ph_correction_history = []

    def forward(self, x):
        weights = self.gate(x)
        out_a = torch.zeros(x.size(0), self.experts[0].net[-1].out_features, device=x.device)
        out_g = torch.zeros_like(out_a)
        for i, expert in enumerate(self.experts):
            w = weights[:, i].unsqueeze(-1)
            e_out = expert(x)
            if i < self.n_camp_a:
                out_a = out_a + w * e_out
            else:
                out_g = out_g + w * e_out

        repulsion = out_a - out_g

        # PH correction: compute barcode distance
        if self.training and np.random.random() < 0.05:
            # Sample 5% of batches for PH (expensive)
            bd = compute_barcode_distance(out_a, out_g)
            self.ph_correction_history.append(bd)
            bd_tensor = torch.tensor(bd, device=x.device, dtype=x.dtype)
        else:
            # Use running average
            if self.ph_correction_history:
                bd = np.mean(self.ph_correction_history[-20:])
            else:
                bd = 0.5
            bd_tensor = torch.tensor(bd, device=x.device, dtype=x.dtype)

        # Correction factor: sigmoid(alpha * bd + beta) * 2 -> (0, 2)
        correction = torch.sigmoid(self.ph_alpha * bd_tensor + self.ph_beta) * 2.0
        return repulsion * correction


# ─── 3. Confidence-Gated PH (advanced) ───
class AnimaPHConfidence(nn.Module):
    """PH correction + confidence gating:
    High PH distance + high confidence -> amplify (creative)
    High PH distance + low confidence -> dampen (hallucination)
    """
    def __init__(self, input_dim, hidden_dim, output_dim, n_experts=8, ExpertCls=Expert):
        super().__init__()
        self.n_camp_a = n_experts // 2
        self.experts = nn.ModuleList([ExpertCls(input_dim, hidden_dim, output_dim) for _ in range(n_experts)])
        self.gate = BoltzmannGate(input_dim, n_experts)
        # Confidence estimator from repulsion magnitude
        self.confidence_proj = nn.Sequential(
            nn.Linear(output_dim, 16), nn.ReLU(), nn.Linear(16, 1), nn.Sigmoid()
        )
        self.ph_alpha = nn.Parameter(torch.tensor(1.0))
        self.ph_beta = nn.Parameter(torch.tensor(0.0))
        self.ph_history = []

    def forward(self, x):
        weights = self.gate(x)
        out_a = torch.zeros(x.size(0), self.experts[0].net[-1].out_features, device=x.device)
        out_g = torch.zeros_like(out_a)
        for i, expert in enumerate(self.experts):
            w = weights[:, i].unsqueeze(-1)
            e_out = expert(x)
            if i < self.n_camp_a:
                out_a = out_a + w * e_out
            else:
                out_g = out_g + w * e_out

        repulsion = out_a - out_g
        confidence = self.confidence_proj(repulsion.detach())  # (batch, 1)

        # Batch-level PH distance
        if self.training and np.random.random() < 0.05:
            bd = compute_barcode_distance(out_a, out_g)
            self.ph_history.append(bd)
        bd = np.mean(self.ph_history[-20:]) if self.ph_history else 0.5
        bd_tensor = torch.tensor(bd, device=x.device, dtype=x.dtype)

        # Correction: high PH dist + high confidence -> amplify
        # high PH dist + low confidence -> dampen
        base_correction = torch.sigmoid(self.ph_alpha * bd_tensor + self.ph_beta) * 2.0
        # Modulate by confidence: confident = correction stays, not confident = pulls to 1.0
        final_correction = confidence * base_correction + (1.0 - confidence) * 1.0

        return repulsion * final_correction


def train_eval(model, train_loader, test_loader, epochs, lr=0.001, device='cpu'):
    model = model.to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    criterion = nn.CrossEntropyLoss()
    accs = []
    losses = []

    for epoch in range(epochs):
        model.train()
        epoch_loss = 0.0
        n_batches = 0
        for X, y in train_loader:
            X = X.view(X.size(0), -1).to(device)
            y = y.to(device)
            optimizer.zero_grad()
            out = model(X)
            loss = criterion(out, y)
            loss.backward()
            optimizer.step()
            epoch_loss += loss.item()
            n_batches += 1

        model.eval()
        correct = total = 0
        with torch.no_grad():
            for X, y in test_loader:
                X = X.view(X.size(0), -1).to(device)
                y = y.to(device)
                correct += (model(X).argmax(1) == y).sum().item()
                total += y.size(0)
        acc = correct / total
        accs.append(acc)
        losses.append(epoch_loss / n_batches)

        if (epoch + 1) % 5 == 0 or epoch == 0:
            print(f"    Epoch {epoch+1:>2}: acc={acc*100:.2f}% loss={epoch_loss/n_batches:.4f}")

    return accs, losses


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

    models = {
        'Raw (A-G)':         lambda: AnimaRaw(input_dim, hidden_dim, 10, ExpertCls=ExpertCls),
        'PH-Corrected':      lambda: AnimaPHCorrected(input_dim, hidden_dim, 10, ExpertCls=ExpertCls),
        'PH+Confidence':     lambda: AnimaPHConfidence(input_dim, hidden_dim, 10, ExpertCls=ExpertCls),
    }

    seeds = [42, 123]
    results = {name: [] for name in models}

    for seed in seeds:
        print(f"\n  --- Seed {seed} ---")
        for name, model_fn in models.items():
            torch.manual_seed(seed)
            np.random.seed(seed)
            model = model_fn()
            params = sum(p.numel() for p in model.parameters())

            print(f"\n  [{name}] params={params:,}")
            start = time.time()
            accs, losses = train_eval(model, train_loader, test_loader, epochs, device=device)
            elapsed = time.time() - start

            # Collect PH stats
            ph_stats = {}
            if hasattr(model, 'ph_correction_history') and model.ph_correction_history:
                ph_stats['ph_bd_mean'] = np.mean(model.ph_correction_history)
                ph_stats['ph_bd_std'] = np.std(model.ph_correction_history)
                ph_stats['ph_bd_n'] = len(model.ph_correction_history)
            if hasattr(model, 'ph_history') and model.ph_history:
                ph_stats['ph_bd_mean'] = np.mean(model.ph_history)
                ph_stats['ph_bd_std'] = np.std(model.ph_history)
            if hasattr(model, 'ph_alpha'):
                ph_stats['alpha'] = model.ph_alpha.item()
                ph_stats['beta'] = model.ph_beta.item()

            results[name].append({
                'best': max(accs), 'final': accs[-1],
                'time': elapsed, 'params': params,
                'accs': accs, 'losses': losses,
                'ph_stats': ph_stats,
            })
            print(f"  -> best={max(accs)*100:.2f}% final={accs[-1]*100:.2f}% time={elapsed:.0f}s")
            if ph_stats:
                print(f"     PH: bd_mean={ph_stats.get('ph_bd_mean', 'N/A'):.4f} "
                      f"alpha={ph_stats.get('alpha', 'N/A'):.3f} "
                      f"beta={ph_stats.get('beta', 'N/A'):.3f}")

    return results


def print_results(dataset_name, results):
    print(f"\n{'=' * 70}")
    print(f"  H-401 PH Correction: {dataset_name} Results")
    print(f"{'=' * 70}")

    print(f"\n  {'Model':20s} | {'Best':>8s} | {'Final':>8s} | {'Params':>8s} | {'PH bd':>8s}")
    print(f"  {'─'*20}-+-{'─'*8}-+-{'─'*8}-+-{'─'*8}-+-{'─'*8}")

    for name, runs in results.items():
        mb = np.mean([r['best'] for r in runs]) * 100
        sb = np.std([r['best'] for r in runs]) * 100
        mf = np.mean([r['final'] for r in runs]) * 100
        p = runs[0]['params']
        ph = np.mean([r['ph_stats'].get('ph_bd_mean', 0) for r in runs])
        print(f"  {name:20s} | {mb:5.2f}%   | {mf:5.2f}%   | {p:>8,} | {ph:.4f}")

    # Delta analysis
    raw_best = np.mean([r['best'] for r in results['Raw (A-G)']])
    print(f"\n  Delta vs Raw (A-G):")
    for name, runs in results.items():
        mb = np.mean([r['best'] for r in runs])
        print(f"    {name:20s}: {(mb-raw_best)*100:+.3f}%")

    # PH parameter evolution
    print(f"\n  Learned PH parameters (last seed):")
    for name, runs in results.items():
        ph = runs[-1].get('ph_stats', {})
        if ph.get('alpha') is not None:
            print(f"    {name:20s}: alpha={ph['alpha']:.3f} beta={ph['beta']:.3f} "
                  f"bd_mean={ph.get('ph_bd_mean', 0):.4f}")


def main():
    print("=" * 70)
    print("  H-401: PH-Corrected Repulsion Field Verification")
    print("  Q: Does PH correction improve AnimaLM output?")
    print("  Q: Can PH distinguish content vs structural tension?")
    print("=" * 70)

    device = 'mps' if torch.backends.mps.is_available() else 'cpu'
    print(f"  Device: {device}")
    print(f"  Ripser: {'available' if HAS_RIPSER else 'proxy mode'}")

    # MNIST
    print(f"\n{'─' * 70}")
    print(f"  MNIST (10 epochs)")
    print(f"{'─' * 70}")
    mnist_results = run_experiment('MNIST', 784, 64, 10, Expert, device)
    print_results('MNIST', mnist_results)

    # CIFAR-10
    print(f"\n{'─' * 70}")
    print(f"  CIFAR-10 (15 epochs)")
    print(f"{'─' * 70}")
    cifar_results = run_experiment('CIFAR', 3072, 128, 15, Expert3L, device)
    print_results('CIFAR-10', cifar_results)

    # Final verdict
    print(f"\n{'=' * 70}")
    print(f"  H-401 VERDICT")
    print(f"{'=' * 70}")

    for ds, res in [('MNIST', mnist_results), ('CIFAR-10', cifar_results)]:
        bests = {n: np.mean([r['best'] for r in runs]) for n, runs in res.items()}
        winner = max(bests, key=bests.get)
        raw = bests['Raw (A-G)']
        ph = bests['PH-Corrected']
        phc = bests['PH+Confidence']

        print(f"\n  {ds}:")
        print(f"    Winner: {winner} ({bests[winner]*100:.2f}%)")
        print(f"    PH-Corrected vs Raw: {(ph-raw)*100:+.3f}%")
        print(f"    PH+Confidence vs Raw: {(phc-raw)*100:+.3f}%")

        if ph > raw + 0.002:
            print(f"    --> PH correction HELPS (+{(ph-raw)*100:.2f}%) -> H-401 SUPPORTED")
        elif ph < raw - 0.002:
            print(f"    --> PH correction HURTS ({(ph-raw)*100:.2f}%) -> H-401 WEAKENED")
        else:
            print(f"    --> PH correction negligible on {ds} (ceiling/scale effect)")

    print(f"\n{'=' * 70}")


if __name__ == '__main__':
    main()
