#!/usr/bin/env python3
"""H-402 Verification: PH-Guided Expert Routing

Tests whether topology-aware routing (gate_score * PH_match) improves
Golden MoE by selecting experts based on input structure, not just activation.

Models compared:
1. Golden MoE (gate only) - baseline
2. PH-Weighted Routing: effective_score = gate * PH_match
3. Dynamic I: I(x) = I_base + gamma * PH_clarity(x)
4. Combined: PH-weighted + Dynamic I

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
    print("WARNING: ripser not available, using proxy")


def compute_ph_features(x_batch, n_subsample=32):
    """Compute PH-derived features for a batch of inputs.
    Returns: (total_persistence, n_components_at_threshold)
    """
    x = x_batch.detach().cpu().numpy()
    if x.shape[0] > n_subsample:
        idx = np.random.choice(x.shape[0], n_subsample, replace=False)
        x = x[idx]

    if HAS_RIPSER and x.shape[0] >= 3:
        try:
            result = ripser(x, maxdim=0)
            dgm = result['dgms'][0]
            dgm_finite = dgm[np.isfinite(dgm[:, 1])]
            if len(dgm_finite) > 0:
                persistence = dgm_finite[:, 1] - dgm_finite[:, 0]
                total_pers = persistence.sum()
                n_long = (persistence > np.median(persistence)).sum()
                clarity = 1.0 / (total_pers + 1e-8)
                return float(total_pers), int(n_long), float(clarity)
        except Exception:
            pass

    # Fallback proxy: variance as "topological complexity"
    var = x.var()
    return float(var), 3, float(1.0 / (var + 1e-8))


class Expert(nn.Module):
    def __init__(self, input_dim, hidden_dim, output_dim, dropout=0.5):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden_dim), nn.ReLU(), nn.Dropout(dropout),
            nn.Linear(hidden_dim, output_dim),
        )
        # Expert signature: learned embedding of what topology this expert handles
        self.signature = nn.Parameter(torch.randn(16) * 0.1)

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
        self.signature = nn.Parameter(torch.randn(16) * 0.1)

    def forward(self, x):
        return self.net(x)


# ─── 1. Golden MoE Baseline (gate only) ───
class GoldenMoEBaseline(nn.Module):
    def __init__(self, input_dim, hidden_dim, output_dim, n_experts=8, ExpertCls=Expert):
        super().__init__()
        self.experts = nn.ModuleList([ExpertCls(input_dim, hidden_dim, output_dim) for _ in range(n_experts)])
        self.gate_proj = nn.Linear(input_dim, n_experts)
        self.temperature = np.e
        self.n_active = max(1, int(n_experts * 0.7))

    def forward(self, x):
        scores = self.gate_proj(x) / self.temperature
        probs = F.softmax(scores, dim=-1)
        topk_vals, topk_idx = probs.topk(self.n_active, dim=-1)
        mask = torch.zeros_like(probs)
        mask.scatter_(-1, topk_idx, 1.0)
        weights = probs * mask
        weights = weights / (weights.sum(dim=-1, keepdim=True) + 1e-8)

        outputs = torch.stack([e(x) for e in self.experts], dim=1)
        return (weights.unsqueeze(-1) * outputs).sum(dim=1), {}


# ─── 2. PH-Weighted Routing ───
class GoldenMoEPHRouting(nn.Module):
    """effective_score_i = gate_i(x) * PH_match_i(x)"""
    def __init__(self, input_dim, hidden_dim, output_dim, n_experts=8, ExpertCls=Expert):
        super().__init__()
        self.n_experts = n_experts
        self.experts = nn.ModuleList([ExpertCls(input_dim, hidden_dim, output_dim) for _ in range(n_experts)])
        self.gate_proj = nn.Linear(input_dim, n_experts)
        self.temperature = np.e
        self.n_active = max(1, int(n_experts * 0.7))
        # PH feature projector: maps input to topology feature space
        self.ph_proj = nn.Sequential(
            nn.Linear(input_dim, 32), nn.ReLU(), nn.Linear(32, 16)
        )

    def forward(self, x):
        # Standard gate scores
        scores = self.gate_proj(x) / self.temperature
        probs = F.softmax(scores, dim=-1)

        # PH matching: compare input topology embedding with expert signatures
        ph_feat = self.ph_proj(x)  # (batch, 16)
        expert_sigs = torch.stack([e.signature for e in self.experts])  # (n_experts, 16)
        # Cosine similarity as PH_match proxy
        ph_feat_norm = F.normalize(ph_feat, dim=-1)  # (batch, 16)
        sig_norm = F.normalize(expert_sigs, dim=-1)   # (n_experts, 16)
        ph_match = torch.mm(ph_feat_norm, sig_norm.t())  # (batch, n_experts)
        ph_match = (ph_match + 1.0) / 2.0  # map [-1,1] to [0,1]

        # Effective scores = gate * PH_match
        effective = probs * ph_match

        # Top-k on effective scores
        topk_vals, topk_idx = effective.topk(self.n_active, dim=-1)
        mask = torch.zeros_like(effective)
        mask.scatter_(-1, topk_idx, 1.0)
        weights = effective * mask
        weights = weights / (weights.sum(dim=-1, keepdim=True) + 1e-8)

        outputs = torch.stack([e(x) for e in self.experts], dim=1)
        return (weights.unsqueeze(-1) * outputs).sum(dim=1), {}


# ─── 3. Dynamic I Threshold ───
class GoldenMoEDynamicI(nn.Module):
    """I(x) = I_base + gamma * PH_clarity(x)"""
    def __init__(self, input_dim, hidden_dim, output_dim, n_experts=8, ExpertCls=Expert):
        super().__init__()
        self.n_experts = n_experts
        self.experts = nn.ModuleList([ExpertCls(input_dim, hidden_dim, output_dim) for _ in range(n_experts)])
        self.gate_proj = nn.Linear(input_dim, n_experts)
        self.temperature = np.e
        self.base_active = int(n_experts * 0.7)
        # Clarity estimator: predicts how many experts to use
        self.clarity_proj = nn.Sequential(
            nn.Linear(input_dim, 16), nn.ReLU(), nn.Linear(16, 1), nn.Sigmoid()
        )
        self.routing_stats = {'n_active_mean': [], 'clarity_mean': []}

    def forward(self, x):
        scores = self.gate_proj(x) / self.temperature
        probs = F.softmax(scores, dim=-1)

        # Dynamic number of active experts based on clarity
        clarity = self.clarity_proj(x)  # (batch, 1), [0, 1]
        # More clarity -> fewer experts (more efficient)
        # Less clarity -> more experts (more thorough)
        # n_active per sample: between 2 and n_experts
        n_active_float = self.n_experts - clarity.squeeze(-1) * (self.n_experts - 2)
        # For tracking
        if self.training:
            self.routing_stats['clarity_mean'].append(clarity.mean().item())

        # Use batch-level average for top-k (can't vary per sample in simple impl)
        avg_n_active = max(2, min(self.n_experts, int(n_active_float.mean().item() + 0.5)))

        topk_vals, topk_idx = probs.topk(avg_n_active, dim=-1)
        mask = torch.zeros_like(probs)
        mask.scatter_(-1, topk_idx, 1.0)
        weights = probs * mask
        weights = weights / (weights.sum(dim=-1, keepdim=True) + 1e-8)

        if self.training:
            self.routing_stats['n_active_mean'].append(avg_n_active)

        outputs = torch.stack([e(x) for e in self.experts], dim=1)
        return (weights.unsqueeze(-1) * outputs).sum(dim=1), {}


# ─── 4. Combined: PH Routing + Dynamic I ───
class GoldenMoEPHFull(nn.Module):
    def __init__(self, input_dim, hidden_dim, output_dim, n_experts=8, ExpertCls=Expert):
        super().__init__()
        self.n_experts = n_experts
        self.experts = nn.ModuleList([ExpertCls(input_dim, hidden_dim, output_dim) for _ in range(n_experts)])
        self.gate_proj = nn.Linear(input_dim, n_experts)
        self.temperature = np.e
        self.ph_proj = nn.Sequential(nn.Linear(input_dim, 32), nn.ReLU(), nn.Linear(32, 16))
        self.clarity_proj = nn.Sequential(nn.Linear(input_dim, 16), nn.ReLU(), nn.Linear(16, 1), nn.Sigmoid())

    def forward(self, x):
        scores = self.gate_proj(x) / self.temperature
        probs = F.softmax(scores, dim=-1)

        # PH matching
        ph_feat = F.normalize(self.ph_proj(x), dim=-1)
        expert_sigs = F.normalize(torch.stack([e.signature for e in self.experts]), dim=-1)
        ph_match = (torch.mm(ph_feat, expert_sigs.t()) + 1.0) / 2.0
        effective = probs * ph_match

        # Dynamic n_active
        clarity = self.clarity_proj(x)
        n_active_float = self.n_experts - clarity.squeeze(-1) * (self.n_experts - 2)
        avg_n_active = max(2, min(self.n_experts, int(n_active_float.mean().item() + 0.5)))

        topk_vals, topk_idx = effective.topk(avg_n_active, dim=-1)
        mask = torch.zeros_like(effective)
        mask.scatter_(-1, topk_idx, 1.0)
        weights = effective * mask
        weights = weights / (weights.sum(dim=-1, keepdim=True) + 1e-8)

        # Load balance loss
        f = (weights > 0).float().mean(dim=0)
        P = probs.mean(dim=0)
        lb_loss = 0.01 * self.n_experts * (f * P).sum()

        outputs = torch.stack([e(x) for e in self.experts], dim=1)
        return (weights.unsqueeze(-1) * outputs).sum(dim=1), {'lb_loss': lb_loss}


def train_eval(model, train_loader, test_loader, epochs, lr=0.001, device='cpu'):
    model = model.to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    criterion = nn.CrossEntropyLoss()
    accs = []

    for epoch in range(epochs):
        model.train()
        for X, y in train_loader:
            X = X.view(X.size(0), -1).to(device)
            y = y.to(device)
            optimizer.zero_grad()
            out, extras = model(X)
            loss = criterion(out, y)
            if 'lb_loss' in extras:
                loss = loss + extras['lb_loss']
            loss.backward()
            optimizer.step()

        model.eval()
        correct = total = 0
        with torch.no_grad():
            for X, y in test_loader:
                X = X.view(X.size(0), -1).to(device)
                y = y.to(device)
                out, _ = model(X)
                correct += (out.argmax(1) == y).sum().item()
                total += y.size(0)
        acc = correct / total
        accs.append(acc)
        if (epoch + 1) % 5 == 0 or epoch == 0:
            print(f"    Epoch {epoch+1:>2}: {acc*100:.2f}%")

    return accs


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
        'Golden MoE (gate)':  lambda: GoldenMoEBaseline(input_dim, hidden_dim, 10, ExpertCls=ExpertCls),
        'PH-Weighted':        lambda: GoldenMoEPHRouting(input_dim, hidden_dim, 10, ExpertCls=ExpertCls),
        'Dynamic I':          lambda: GoldenMoEDynamicI(input_dim, hidden_dim, 10, ExpertCls=ExpertCls),
        'PH+DynI (full)':    lambda: GoldenMoEPHFull(input_dim, hidden_dim, 10, ExpertCls=ExpertCls),
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
            accs = train_eval(model, train_loader, test_loader, epochs, device=device)
            elapsed = time.time() - start

            # Expert signature analysis
            sig_stats = {}
            if hasattr(model, 'experts') and hasattr(model.experts[0], 'signature'):
                sigs = torch.stack([e.signature.detach().cpu() for e in model.experts])
                # Compute pairwise cosine similarity
                sigs_norm = F.normalize(sigs, dim=-1)
                sim_matrix = torch.mm(sigs_norm, sigs_norm.t())
                # Mean off-diagonal similarity
                mask = ~torch.eye(len(sigs), dtype=bool)
                sig_stats['mean_sim'] = sim_matrix[mask].mean().item()
                sig_stats['std_sim'] = sim_matrix[mask].std().item()

            # Dynamic I stats
            if hasattr(model, 'routing_stats') and model.routing_stats.get('n_active_mean'):
                sig_stats['avg_n_active'] = np.mean(model.routing_stats['n_active_mean'][-100:])
                sig_stats['avg_clarity'] = np.mean(model.routing_stats['clarity_mean'][-100:])

            results[name].append({
                'best': max(accs), 'final': accs[-1],
                'time': elapsed, 'params': params,
                'accs': accs, 'sig_stats': sig_stats,
            })
            print(f"  -> best={max(accs)*100:.2f}% final={accs[-1]*100:.2f}% time={elapsed:.0f}s")
            if sig_stats:
                for k, v in sig_stats.items():
                    print(f"     {k}: {v:.4f}")

    return results


def print_results(dataset_name, results):
    print(f"\n{'=' * 70}")
    print(f"  H-402 PH Routing: {dataset_name} Results")
    print(f"{'=' * 70}")

    print(f"\n  {'Model':22s} | {'Best':>8s} | {'Final':>8s} | {'Params':>8s}")
    print(f"  {'─'*22}-+-{'─'*8}-+-{'─'*8}-+-{'─'*8}")

    for name, runs in results.items():
        mb = np.mean([r['best'] for r in runs]) * 100
        mf = np.mean([r['final'] for r in runs]) * 100
        p = runs[0]['params']
        print(f"  {name:22s} | {mb:5.2f}%   | {mf:5.2f}%   | {p:>8,}")

    # Delta vs baseline
    base = np.mean([r['best'] for r in results['Golden MoE (gate)']])
    print(f"\n  Delta vs Golden MoE baseline:")
    for name, runs in results.items():
        mb = np.mean([r['best'] for r in runs])
        print(f"    {name:22s}: {(mb-base)*100:+.3f}%")

    # Expert signature diversity
    print(f"\n  Expert signature diversity (last seed):")
    for name, runs in results.items():
        ss = runs[-1].get('sig_stats', {})
        if 'mean_sim' in ss:
            print(f"    {name:22s}: mean_sim={ss['mean_sim']:.4f} std_sim={ss['std_sim']:.4f}")
        if 'avg_n_active' in ss:
            print(f"    {name:22s}: avg_experts={ss['avg_n_active']:.1f} clarity={ss['avg_clarity']:.3f}")


def main():
    print("=" * 70)
    print("  H-402: PH-Guided Expert Routing Verification")
    print("  Q: Does topology-aware routing improve Golden MoE?")
    print("  Q: Does dynamic I adapt expert count to input complexity?")
    print("=" * 70)

    device = 'mps' if torch.backends.mps.is_available() else 'cpu'
    print(f"  Device: {device}")

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
    print(f"  H-402 VERDICT")
    print(f"{'=' * 70}")

    for ds, res in [('MNIST', mnist_results), ('CIFAR-10', cifar_results)]:
        bests = {n: np.mean([r['best'] for r in runs]) for n, runs in res.items()}
        winner = max(bests, key=bests.get)
        base = bests['Golden MoE (gate)']

        print(f"\n  {ds}:")
        print(f"    Winner: {winner} ({bests[winner]*100:.2f}%)")
        for name, val in bests.items():
            tag = ""
            if val > base + 0.005:
                tag = " SUPPORTED"
            elif val < base - 0.005:
                tag = " WORSE"
            else:
                tag = " NEUTRAL"
            print(f"    {name:22s}: {val*100:.2f}% ({(val-base)*100:+.2f}%){tag}")

    print(f"\n{'=' * 70}")


if __name__ == '__main__':
    main()
