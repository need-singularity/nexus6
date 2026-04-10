#!/usr/bin/env python3
"""H-406: Native PureField vs Converted MoE — Tension Dynamics Comparison

Two models with ~equal parameters on MNIST + CIFAR-10:
1. MoE-PureField (AnimaLM-style): 8 experts, 4A+4G, BoltzmannRouter, output=A-G
2. Native-PureField (ConsciousLM-style): 2 engines, no router, output=A-G
3. Standard MLP (control): single FFN, no tension

Measures: accuracy, tension magnitude, tension-accuracy correlation, PH divergence
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


def barcode_distance(a, g, n=64):
    a_np = a.detach().cpu().numpy()
    g_np = g.detach().cpu().numpy()
    if a_np.shape[0] > n: a_np = a_np[np.random.choice(a_np.shape[0], n, replace=False)]
    if g_np.shape[0] > n: g_np = g_np[np.random.choice(g_np.shape[0], n, replace=False)]
    if not HAS_RIPSER or a_np.shape[0] < 3: return 0.0
    try:
        ra = ripser(a_np, maxdim=0)['dgms'][0]
        rg = ripser(g_np, maxdim=0)['dgms'][0]
        ra = ra[np.isfinite(ra[:,1])]; rg = rg[np.isfinite(rg[:,1])]
        pa = (ra[:,1]-ra[:,0]).sum() if len(ra)>0 else 0
        pg = (rg[:,1]-rg[:,0]).sum() if len(rg)>0 else 0
        return abs(pa-pg)/(pa+pg+1e-8)
    except: return 0.0


# ─── Expert (shared) ───
class Expert(nn.Module):
    def __init__(self, d_in, d_hid, d_out, dropout=0.5):
        super().__init__()
        self.net = nn.Sequential(nn.Linear(d_in, d_hid), nn.ReLU(), nn.Dropout(dropout), nn.Linear(d_hid, d_out))
    def forward(self, x): return self.net(x)

class Expert3L(nn.Module):
    def __init__(self, d_in, d_hid, d_out, dropout=0.5):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(d_in, d_hid), nn.ReLU(), nn.Dropout(dropout),
            nn.Linear(d_hid, d_hid), nn.ReLU(), nn.Dropout(dropout),
            nn.Linear(d_hid, d_out))
    def forward(self, x): return self.net(x)


# ─── 1. MoE-PureField (AnimaLM-style) ───
class MoEPureField(nn.Module):
    def __init__(self, d_in, d_hid, d_out, n_experts=8, ExpertCls=Expert):
        super().__init__()
        self.n_camp_a = n_experts // 2
        self.experts = nn.ModuleList([ExpertCls(d_in, d_hid, d_out) for _ in range(n_experts)])
        self.gate = nn.Linear(d_in, n_experts)
        self.temperature = np.e
        self.n_active = max(1, int(n_experts * 0.625))
        self.last_a = self.last_g = self.last_tension = None

    def forward(self, x):
        scores = self.gate(x) / self.temperature
        probs = F.softmax(scores, dim=-1)
        topk_vals, topk_idx = probs.topk(self.n_active, dim=-1)
        mask = torch.zeros_like(probs)
        mask.scatter_(-1, topk_idx, 1.0)
        weights = probs * mask
        weights = weights / (weights.sum(dim=-1, keepdim=True) + 1e-8)

        out_a = torch.zeros(x.size(0), self.experts[0].net[-1].out_features, device=x.device)
        out_g = torch.zeros_like(out_a)
        for i, expert in enumerate(self.experts):
            w = weights[:, i].unsqueeze(-1)
            e_out = expert(x)
            if i < self.n_camp_a:
                out_a = out_a + w * e_out
            else:
                out_g = out_g + w * e_out

        output = out_a - out_g
        self.last_a, self.last_g = out_a, out_g
        self.last_tension = (output ** 2).mean(dim=-1)
        return output


# ─── 2. Native-PureField (ConsciousLM-style) ───
class NativePureField(nn.Module):
    def __init__(self, d_in, d_hid, d_out, ExpertCls=Expert):
        super().__init__()
        # Two independent engines, ~same total params as 8-expert MoE
        # Each engine gets 4x the hidden dim of a single MoE expert
        big_hid = d_hid * 2  # compensate for only 2 engines vs 8
        self.engine_a = nn.Sequential(
            nn.Linear(d_in, big_hid), nn.GELU(), nn.Dropout(0.37),
            nn.Linear(big_hid, d_out))
        self.engine_g = nn.Sequential(
            nn.Linear(d_in, big_hid), nn.GELU(), nn.Dropout(0.37),
            nn.Linear(big_hid, d_out))
        self.last_a = self.last_g = self.last_tension = None

    def forward(self, x):
        a = self.engine_a(x)
        g = self.engine_g(x)
        output = a - g
        self.last_a, self.last_g = a, g
        self.last_tension = (output ** 2).mean(dim=-1)
        return output


# ─── 3. Standard MLP (control) ───
class StandardMLP(nn.Module):
    def __init__(self, d_in, d_hid, d_out, ExpertCls=Expert):
        super().__init__()
        big_hid = d_hid * 4
        self.net = nn.Sequential(
            nn.Linear(d_in, big_hid), nn.GELU(), nn.Dropout(0.37),
            nn.Linear(big_hid, d_out))
        self.last_a = self.last_g = self.last_tension = None

    def forward(self, x):
        out = self.net(x)
        self.last_a = out
        self.last_g = torch.zeros_like(out)
        self.last_tension = torch.zeros(x.size(0), device=x.device)
        return out


def train_eval_tracked(model, train_loader, test_loader, epochs, device, track_every=1):
    model = model.to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
    criterion = nn.CrossEntropyLoss()
    epoch_data = []

    for epoch in range(epochs):
        model.train()
        epoch_tensions = []
        for X, y in train_loader:
            X = X.view(X.size(0), -1).to(device)
            y = y.to(device)
            optimizer.zero_grad()
            out = model(X)
            loss = criterion(out, y)
            loss.backward()
            optimizer.step()
            if model.last_tension is not None:
                epoch_tensions.append(model.last_tension.detach().mean().item())

        model.eval()
        correct = total = 0
        all_a, all_g = [], []
        per_class_tension = {}

        with torch.no_grad():
            for X, y in test_loader:
                X = X.view(X.size(0), -1).to(device)
                y = y.to(device)
                out = model(X)
                correct += (out.argmax(1) == y).sum().item()
                total += y.size(0)
                if model.last_a is not None:
                    all_a.append(model.last_a.cpu())
                    all_g.append(model.last_g.cpu())
                if model.last_tension is not None:
                    for cls in range(10):
                        mask = (y == cls)
                        if mask.any():
                            t = model.last_tension[mask].mean().item()
                            per_class_tension.setdefault(cls, []).append(t)

        acc = correct / total
        mean_tension = np.mean(epoch_tensions) if epoch_tensions else 0
        std_tension = np.std(epoch_tensions) if epoch_tensions else 0

        # PH measurement
        bd = 0.0
        if all_a and (epoch + 1) % track_every == 0:
            cat_a = torch.cat(all_a)
            cat_g = torch.cat(all_g)
            bd = barcode_distance(cat_a, cat_g)

        # Per-class tension mean
        cls_tensions = [np.mean(v) for v in per_class_tension.values()] if per_class_tension else []
        cls_accs = []  # would need per-class accuracy tracking

        epoch_data.append({
            'epoch': epoch+1, 'acc': acc,
            'tension_mean': mean_tension, 'tension_std': std_tension,
            'bd': bd, 'cls_tensions': cls_tensions,
        })

        if (epoch+1) % 5 == 0 or epoch == 0:
            print(f"    Ep {epoch+1:>2}: acc={acc*100:.2f}% T_mean={mean_tension:.4f} T_std={std_tension:.4f} BD={bd:.4f}")

    return epoch_data


def run_comparison(dataset_name, d_in, d_hid, epochs, ExpertCls, device):
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
        'MoE-PureField':    lambda: MoEPureField(d_in, d_hid, 10, ExpertCls=ExpertCls),
        'Native-PureField': lambda: NativePureField(d_in, d_hid, 10, ExpertCls=ExpertCls),
        'Standard MLP':     lambda: StandardMLP(d_in, d_hid, 10, ExpertCls=ExpertCls),
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
            data = train_eval_tracked(model, train_loader, test_loader, epochs, device)
            elapsed = time.time() - start

            results[name].append({
                'best': max(d['acc'] for d in data),
                'final': data[-1]['acc'],
                'params': params, 'time': elapsed,
                'epochs': data,
            })
            print(f"  -> best={max(d['acc'] for d in data)*100:.2f}% time={elapsed:.0f}s")

    return results


def print_comparison(dataset_name, results):
    print(f"\n{'=' * 70}")
    print(f"  H-406: {dataset_name} — Native vs Converted")
    print(f"{'=' * 70}")

    # Accuracy table
    print(f"\n  {'Model':20s} | {'Best':>8s} | {'Final':>8s} | {'Params':>8s}")
    print(f"  {'─'*20}-+-{'─'*8}-+-{'─'*8}-+-{'─'*8}")
    for name, runs in results.items():
        mb = np.mean([r['best'] for r in runs]) * 100
        mf = np.mean([r['final'] for r in runs]) * 100
        p = runs[0]['params']
        print(f"  {name:20s} | {mb:5.2f}%   | {mf:5.2f}%   | {p:>8,}")

    # Tension comparison
    print(f"\n  Tension Dynamics (final epoch, mean of seeds):")
    print(f"  {'Model':20s} | {'T_mean':>10s} | {'T_std':>10s} | {'BD':>8s}")
    print(f"  {'─'*20}-+-{'─'*10}-+-{'─'*10}-+-{'─'*8}")
    for name, runs in results.items():
        t_means = [r['epochs'][-1]['tension_mean'] for r in runs]
        t_stds = [r['epochs'][-1]['tension_std'] for r in runs]
        bds = [r['epochs'][-1]['bd'] for r in runs]
        print(f"  {name:20s} | {np.mean(t_means):10.4f} | {np.mean(t_stds):10.4f} | {np.mean(bds):8.4f}")

    # Tension ratio
    moe_t = np.mean([r['epochs'][-1]['tension_mean'] for r in results['MoE-PureField']])
    native_t = np.mean([r['epochs'][-1]['tension_mean'] for r in results['Native-PureField']])
    if moe_t > 0:
        print(f"\n  Tension ratio (Native/MoE): {native_t/moe_t:.2f}x")

    # Tension evolution ASCII
    print(f"\n  Tension Evolution (seed 42):")
    for name in ['MoE-PureField', 'Native-PureField']:
        data = results[name][0]['epochs']
        max_t = max(d['tension_mean'] for d in data) if data else 1
        print(f"    {name}:")
        for d in data:
            if (d['epoch']) % 3 == 1 or d['epoch'] == len(data):
                bar = int(d['tension_mean'] / (max_t + 1e-8) * 30)
                print(f"      Ep{d['epoch']:>2}: {'█' * bar:30s} {d['tension_mean']:.4f}")

    # Delta
    moe_best = np.mean([r['best'] for r in results['MoE-PureField']])
    native_best = np.mean([r['best'] for r in results['Native-PureField']])
    mlp_best = np.mean([r['best'] for r in results['Standard MLP']])

    print(f"\n  Deltas:")
    print(f"    Native vs MoE:     {(native_best-moe_best)*100:+.2f}%")
    print(f"    Native vs MLP:     {(native_best-mlp_best)*100:+.2f}%")
    print(f"    MoE vs MLP:        {(moe_best-mlp_best)*100:+.2f}%")

    # Verdict
    print(f"\n  VERDICT for {dataset_name}:")
    if native_best > moe_best + 0.003:
        print(f"    -> SUPPORTED: Native PureField > MoE-PureField")
    elif native_best < moe_best - 0.003:
        print(f"    -> REFUTED: MoE-PureField > Native PureField")
    else:
        print(f"    -> NEUTRAL: difference < 0.3%")

    if native_t > moe_t * 1.5:
        print(f"    -> TENSION SUPPORTED: Native tension {native_t/moe_t:.1f}x higher")
    else:
        print(f"    -> TENSION NEUTRAL: ratio {native_t/moe_t:.2f}x (< 1.5x threshold)")


def main():
    print("=" * 70)
    print("  H-406: Native PureField vs Converted MoE")
    print("  Does training from scratch produce better tension dynamics?")
    print("=" * 70)

    device = 'mps' if torch.backends.mps.is_available() else 'cpu'
    print(f"  Device: {device}")

    # MNIST
    print(f"\n{'─' * 70}")
    print(f"  MNIST (10 epochs)")
    print(f"{'─' * 70}")
    mnist = run_comparison('MNIST', 784, 64, 10, Expert, device)
    print_comparison('MNIST', mnist)

    # CIFAR-10
    print(f"\n{'─' * 70}")
    print(f"  CIFAR-10 (15 epochs)")
    print(f"{'─' * 70}")
    cifar = run_comparison('CIFAR', 3072, 128, 15, Expert3L, device)
    print_comparison('CIFAR-10', cifar)

    print(f"\n{'=' * 70}")


if __name__ == '__main__':
    main()
