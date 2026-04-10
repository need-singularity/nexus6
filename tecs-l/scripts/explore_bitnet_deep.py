#!/usr/bin/env python3
"""Deep exploration: BitNet x Golden MoE — hunting for major discoveries.

Explores dimensions not yet tested:
1. Per-class synergy (which classes benefit most?)
2. Expert specialization under dual constraint
3. Convergence dynamics (epoch-level synergy evolution)
4. Ternary weight evolution over training
5. Expert correlation matrix (do ternary experts decorrelate?)
6. Temperature sweep (is T=e optimal for BitNet?)
7. The 0.63 cluster: mathematical deep dive
8. Loss ratio analysis (BitNet+Golden loss structure)
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader
from torchvision import datasets, transforms
import numpy as np
import math
import time

# ── Core components (compact) ──
def tq(w):
    a = w.abs().mean()
    return torch.sign(w) * (w.abs() > a * 0.5).float()

class TW(torch.autograd.Function):
    @staticmethod
    def forward(ctx, w): return tq(w)
    @staticmethod
    def backward(ctx, g): return g

class TL(nn.Module):
    def __init__(self, i, o):
        super().__init__()
        self.linear = nn.Linear(i, o)
        self.dist = None
    def forward(self, x):
        wt = TW.apply(self.linear.weight)
        with torch.no_grad():
            self.dist = ((wt==-1).float().mean().item(),
                         (wt==0).float().mean().item(),
                         (wt==1).float().mean().item())
        return F.linear(x, wt, self.linear.bias)

class TopKGate(nn.Module):
    def __init__(self, d, n, k=2):
        super().__init__()
        self.g = nn.Linear(d, n); self.k = k
    def forward(self, x):
        s = self.g(x); _, idx = s.topk(self.k, -1)
        m = torch.zeros_like(s).scatter_(-1, idx, 1.0)
        w = F.softmax(s,-1)*m; return w/(w.sum(-1,keepdim=True)+1e-8)

class BoltzmannGate(nn.Module):
    def __init__(self, d, n, T=np.e, ar=0.7):
        super().__init__()
        self.g = nn.Linear(d, n); self.T = T
        self.na = max(1, int(n*ar))
    def forward(self, x):
        p = F.softmax(self.g(x)/self.T, -1)
        _, idx = p.topk(self.na, -1)
        m = torch.zeros_like(p).scatter_(-1, idx, 1.0)
        w = p*m; return w/(w.sum(-1,keepdim=True)+1e-8)

class Expert(nn.Module):
    def __init__(self, d, h, o):
        super().__init__()
        self.net = nn.Sequential(nn.Linear(d,h), nn.ReLU(), nn.Dropout(0.5), nn.Linear(h,o))
    def forward(self, x): return self.net(x)

class TernaryExpert(nn.Module):
    def __init__(self, d, h, o):
        super().__init__()
        self.fc1 = TL(d,h); self.fc2 = TL(h,o); self.dr = nn.Dropout(0.5)
    def forward(self, x): return self.fc2(self.dr(F.relu(self.fc1(x))))

class MoE(nn.Module):
    def __init__(self, d, h, o, n=8, gt='boltzmann', ternary=False, T=np.e, ar=0.7, k=2):
        super().__init__()
        EC = TernaryExpert if ternary else Expert
        self.experts = nn.ModuleList([EC(d,h,o) for _ in range(n)])
        self.n = n; self.ternary = ternary
        if gt == 'topk': self.gate = TopKGate(d, n, k)
        elif gt == 'boltzmann': self.gate = BoltzmannGate(d, n, T, ar)
        else: self.gate = None
        self.expert_usage = torch.zeros(n)

    def forward(self, x):
        eo = torch.stack([e(x) for e in self.experts], 1)
        if self.gate is None:
            return eo.mean(1), None
        w = self.gate(x)
        with torch.no_grad():
            self.expert_usage += (w > 0).float().sum(0).mean(0).cpu()
        return (w.unsqueeze(-1)*eo).sum(1), w

    def get_expert_outputs(self, x):
        return [e(x) for e in self.experts]


def load_data(name='mnist'):
    tf = transforms.Compose([transforms.ToTensor(), transforms.Normalize((0.5,),(0.5,))])
    if name == 'mnist':
        tr = datasets.MNIST('./data', train=True, download=True, transform=tf)
        te = datasets.MNIST('./data', train=False, transform=tf)
        return DataLoader(tr,128,True), DataLoader(te,256), 784, 10
    else:
        tr = datasets.FashionMNIST('./data', train=True, download=True, transform=tf)
        te = datasets.FashionMNIST('./data', train=False, transform=tf)
        return DataLoader(tr,128,True), DataLoader(te,256), 784, 10


# ═══════════════════════════════════════
# EXPLORATION 1: Per-Class Synergy
# ═══════════════════════════════════════
def explore_per_class_synergy():
    print(f"\n{'='*70}")
    print(f"  EXPLORATION 1: Per-Class Synergy Analysis")
    print(f"{'='*70}")

    configs = [
        ('Dense',    'dense',     False, {}),
        ('Golden',   'boltzmann', False, {'T': np.e, 'ar': 0.7}),
        ('BitNet-D', 'dense',     False, {}),  # will set ternary=True below
        ('BitNet+G', 'boltzmann', True,  {'T': np.e, 'ar': 0.7}),
    ]
    # Fix: BitNet-D should be ternary
    configs[2] = ('BitNet-D', 'dense', True, {})

    for ds_name in ['mnist', 'fashion']:
        trl, tel, dim, nc = load_data(ds_name)
        label = 'MNIST' if ds_name == 'mnist' else 'FashionMNIST'
        print(f"\n  [{label}]")

        class_results = {}  # {config: {class: (correct, total)}}
        class_names_mnist = [str(i) for i in range(10)]
        class_names_fashion = ['T-shirt', 'Trouser', 'Pullover', 'Dress', 'Coat',
                               'Sandal', 'Shirt', 'Sneaker', 'Bag', 'Boot']
        cnames = class_names_mnist if ds_name == 'mnist' else class_names_fashion

        for cname, gt, tern, kw in configs:
            torch.manual_seed(42); np.random.seed(42)
            T = kw.get('T', np.e); ar = kw.get('ar', 0.7)
            model = MoE(dim, 64, nc, 8, gt, tern, T, ar)
            opt = torch.optim.Adam(model.parameters(), 0.001)
            crit = nn.CrossEntropyLoss()

            for ep in range(10):
                model.train()
                for X, y in trl:
                    opt.zero_grad()
                    out, _ = model(X.view(X.size(0),-1))
                    crit(out, y).backward(); opt.step()

            model.eval()
            per_class = {i: [0, 0] for i in range(nc)}
            with torch.no_grad():
                for X, y in tel:
                    out, _ = model(X.view(X.size(0),-1))
                    pred = out.argmax(1)
                    for i in range(nc):
                        mask = (y == i)
                        per_class[i][1] += mask.sum().item()
                        per_class[i][0] += ((pred == y) & mask).sum().item()

            class_results[cname] = {i: per_class[i][0]/max(per_class[i][1],1) for i in range(nc)}

        # Per-class synergy
        print(f"\n  {'Class':>10} | {'Dense':>7} | {'Golden':>7} | {'BitN-D':>7} | {'BitN+G':>7} | {'Synergy':>8} | {'Recovery':>9}")
        print(f"  {'─'*10}─+{'─'*9}+{'─'*9}+{'─'*9}+{'─'*9}+{'─'*10}+{'─'*11}")

        synergies_per_class = []
        for i in range(nc):
            d = class_results['Dense'][i]
            g = class_results['Golden'][i]
            bd = class_results['BitNet-D'][i]
            bg = class_results['BitNet+G'][i]
            g_gain = g - d
            b_gain = bd - d
            dual_gain = bg - d
            syn = dual_gain - (g_gain + b_gain)
            b_loss = d - bd
            d_loss = d - bg
            rec = (b_loss - d_loss) / b_loss if b_loss > 0.01 else 0
            synergies_per_class.append((cnames[i], syn, rec, d, g, bd, bg))
            print(f"  {cnames[i]:>10} | {d*100:>6.1f}% | {g*100:>6.1f}% | {bd*100:>6.1f}% | {bg*100:>6.1f}% | {syn*100:>+7.2f}% | {rec*100:>8.1f}%")

        # Sort by synergy
        synergies_per_class.sort(key=lambda x: x[1], reverse=True)
        print(f"\n  Top synergy classes:")
        for name, syn, rec, d, g, bd, bg in synergies_per_class[:3]:
            print(f"    {name}: synergy={syn*100:+.2f}%, recovery={rec*100:.1f}%")
        print(f"  Bottom synergy classes:")
        for name, syn, rec, d, g, bd, bg in synergies_per_class[-3:]:
            print(f"    {name}: synergy={syn*100:+.2f}%, recovery={rec*100:.1f}%")

        # Correlation: Does synergy correlate with task difficulty?
        diffs = [(s[3], s[1]) for s in synergies_per_class]  # (dense_acc, synergy)
        if len(diffs) > 2:
            dense_accs = [x[0] for x in diffs]
            syns = [x[1] for x in diffs]
            corr = np.corrcoef(dense_accs, syns)[0,1]
            print(f"\n  Correlation(class_difficulty, synergy) = {corr:.4f}")
            if corr < -0.3:
                print(f"  --> HARDER CLASSES GET MORE SYNERGY (negative correlation)")
            elif corr > 0.3:
                print(f"  --> EASIER CLASSES GET MORE SYNERGY (positive correlation)")


# ═══════════════════════════════════════
# EXPLORATION 2: Expert Specialization
# ═══════════════════════════════════════
def explore_expert_specialization():
    print(f"\n{'='*70}")
    print(f"  EXPLORATION 2: Expert Specialization Under Dual Constraint")
    print(f"{'='*70}")

    trl, tel, dim, nc = load_data('mnist')

    for label, tern, gt in [('Golden(FP32)', False, 'boltzmann'),
                             ('BitNet+Golden', True, 'boltzmann')]:
        torch.manual_seed(42); np.random.seed(42)
        model = MoE(dim, 64, nc, 8, gt, tern, np.e, 0.7)
        opt = torch.optim.Adam(model.parameters(), 0.001)
        crit = nn.CrossEntropyLoss()

        for ep in range(10):
            model.train()
            for X, y in trl:
                opt.zero_grad()
                out, _ = model(X.view(X.size(0),-1))
                crit(out, y).backward(); opt.step()

        # Measure per-expert per-class activation
        model.eval()
        expert_class_weights = torch.zeros(8, 10)  # expert x class
        with torch.no_grad():
            for X, y in tel:
                out, w = model(X.view(X.size(0),-1))
                if w is not None:
                    for c in range(10):
                        mask = (y == c)
                        if mask.sum() > 0:
                            expert_class_weights[:, c] += w[mask].mean(0).cpu()

        # Normalize
        ecw = expert_class_weights / expert_class_weights.sum(0, keepdim=True).clamp(min=1e-8)

        print(f"\n  [{label}] Expert-Class Activation Heatmap:")
        print(f"  {'Expert':>8} |", end="")
        for c in range(10):
            print(f" {c:>5} |", end="")
        print(f" {'Entropy':>8}")
        print(f"  {'─'*8}─+" + ("─"*7+"+")*10 + "─"*10)

        expert_entropies = []
        for e in range(8):
            row = ecw[e].numpy()
            ent = -sum(p * math.log2(p) for p in row if p > 0.001)
            expert_entropies.append(ent)
            print(f"  {'E'+str(e):>8} |", end="")
            for c in range(10):
                val = row[c]
                if val > 0.15:
                    print(f" {'##':>5} |", end="")
                elif val > 0.10:
                    print(f" {'# ':>5} |", end="")
                else:
                    print(f" {val:>5.3f} |", end="")
            print(f" {ent:>8.3f}")

        mean_ent = np.mean(expert_entropies)
        print(f"\n  Mean expert entropy: {mean_ent:.4f} (max={math.log2(10):.4f})")
        print(f"  Specialization index: {1 - mean_ent/math.log2(10):.4f} (1=fully specialized)")


# ═══════════════════════════════════════
# EXPLORATION 3: Epoch-Level Synergy Evolution
# ═══════════════════════════════════════
def explore_synergy_evolution():
    print(f"\n{'='*70}")
    print(f"  EXPLORATION 3: Synergy Evolution Over Training")
    print(f"{'='*70}")

    for ds_name in ['mnist', 'fashion']:
        trl, tel, dim, nc = load_data(ds_name)
        label = 'MNIST' if ds_name == 'mnist' else 'FashionMNIST'

        configs = [
            ('Dense',    'dense',     False),
            ('Golden',   'boltzmann', False),
            ('BitNet-D', 'dense',     True),
            ('BitNet+G', 'boltzmann', True),
        ]

        epoch_accs = {}
        for cname, gt, tern in configs:
            torch.manual_seed(42); np.random.seed(42)
            model = MoE(dim, 64, nc, 8, gt, tern, np.e, 0.7)
            opt = torch.optim.Adam(model.parameters(), 0.001)
            crit = nn.CrossEntropyLoss()
            accs = []

            for ep in range(10):
                model.train()
                for X, y in trl:
                    opt.zero_grad()
                    out, _ = model(X.view(X.size(0),-1))
                    crit(out, y).backward(); opt.step()
                model.eval()
                c = t = 0
                with torch.no_grad():
                    for X, y in tel:
                        out, _ = model(X.view(X.size(0),-1))
                        c += (out.argmax(1)==y).sum().item(); t += y.size(0)
                accs.append(c/t)
            epoch_accs[cname] = accs

        # Compute per-epoch synergy
        print(f"\n  [{label}] Epoch-by-Epoch Synergy:")
        print(f"  {'Epoch':>5} | {'Dense':>7} | {'Golden':>7} | {'BitN-D':>7} | {'BitN+G':>7} | {'Synergy':>8} | {'Recovery':>9}")
        print(f"  {'─'*5}─+{'─'*9}+{'─'*9}+{'─'*9}+{'─'*9}+{'─'*10}+{'─'*11}")

        synergies = []
        for ep in range(10):
            d = epoch_accs['Dense'][ep]
            g = epoch_accs['Golden'][ep]
            bd = epoch_accs['BitNet-D'][ep]
            bg = epoch_accs['BitNet+G'][ep]
            syn = (bg - d) - ((g - d) + (bd - d))
            b_loss = d - bd
            d_loss = d - bg
            rec = (b_loss - d_loss) / b_loss if b_loss > 0.01 else 0
            synergies.append(syn)
            print(f"  {ep+1:>5} | {d*100:>6.2f}% | {g*100:>6.2f}% | {bd*100:>6.2f}% | {bg*100:>6.2f}% | {syn*100:>+7.3f}% | {rec*100:>8.1f}%")

        # Trend analysis
        x = np.arange(10)
        slope = np.polyfit(x, synergies, 1)[0]
        print(f"\n  Synergy trend: slope = {slope*100:+.4f}%/epoch")
        if slope > 0.001:
            print(f"  --> SYNERGY INCREASES with training (compounds over time)")
        elif slope < -0.001:
            print(f"  --> SYNERGY DECREASES with training (early benefit)")
        else:
            print(f"  --> SYNERGY STABLE over training")

        # Phase transition detection
        max_syn_ep = np.argmax(synergies)
        print(f"  Peak synergy at epoch {max_syn_ep+1}: {synergies[max_syn_ep]*100:+.3f}%")


# ═══════════════════════════════════════
# EXPLORATION 4: Temperature Sweep for BitNet
# ═══════════════════════════════════════
def explore_temperature_sweep():
    print(f"\n{'='*70}")
    print(f"  EXPLORATION 4: Is T=e Optimal for BitNet+Golden?")
    print(f"{'='*70}")

    trl, tel, dim, nc = load_data('mnist')

    temperatures = [0.5, 1.0, 1.5, np.e/2, 2.0, np.e, 3.0, np.e*1.5, 5.0, 10.0]
    temp_labels = ['0.5', '1.0', '1.5', 'e/2', '2.0', 'e', '3.0', '1.5e', '5.0', '10.0']

    print(f"\n  {'Temp':>6} | {'Value':>6} | {'Accuracy':>9} | {'1/T':>6} | {'in GZ?':>7}")
    print(f"  {'─'*6}─+{'─'*8}+{'─'*11}+{'─'*8}+{'─'*9}")

    results = []
    for T, tlabel in zip(temperatures, temp_labels):
        torch.manual_seed(42); np.random.seed(42)
        model = MoE(dim, 64, nc, 8, 'boltzmann', True, T, 0.7)
        opt = torch.optim.Adam(model.parameters(), 0.001)
        crit = nn.CrossEntropyLoss()

        best = 0
        for ep in range(10):
            model.train()
            for X, y in trl:
                opt.zero_grad()
                out, _ = model(X.view(X.size(0),-1))
                crit(out, y).backward(); opt.step()
            model.eval()
            c = t = 0
            with torch.no_grad():
                for X, y in tel:
                    out, _ = model(X.view(X.size(0),-1))
                    c += (out.argmax(1)==y).sum().item(); t += y.size(0)
            best = max(best, c/t)

        inv_T = 1/T
        in_gz = "YES" if 0.213 <= inv_T <= 0.500 else "no"
        results.append((T, tlabel, best, inv_T, in_gz))
        marker = " <<<" if tlabel == 'e' else ""
        print(f"  {tlabel:>6} | {T:>6.3f} | {best*100:>8.2f}% | {inv_T:>6.4f} | {in_gz:>7}{marker}")

    peak = max(results, key=lambda x: x[2])
    print(f"\n  Peak: T={peak[1]} ({peak[0]:.3f}), Acc={peak[2]*100:.2f}%")
    print(f"  T=e rank: {sorted([r[2] for r in results], reverse=True).index(results[5][2])+1}/{len(results)}")

    e_acc = results[5][2]
    if peak[2] - e_acc < 0.005:
        print(f"  --> T=e is NEAR-OPTIMAL for BitNet+Golden")
    else:
        print(f"  --> T={peak[1]} outperforms T=e by {(peak[2]-e_acc)*100:+.2f}%")


# ═══════════════════════════════════════
# EXPLORATION 5: Weight Dynamics Over Training
# ═══════════════════════════════════════
def explore_weight_dynamics():
    print(f"\n{'='*70}")
    print(f"  EXPLORATION 5: Ternary Weight Evolution During Training")
    print(f"{'='*70}")

    trl, tel, dim, nc = load_data('mnist')

    for label, gt in [('BitNet-Dense', 'dense'), ('BitNet+Golden', 'boltzmann')]:
        torch.manual_seed(42); np.random.seed(42)
        model = MoE(dim, 64, nc, 8, gt, True, np.e, 0.7)
        opt = torch.optim.Adam(model.parameters(), 0.001)
        crit = nn.CrossEntropyLoss()

        print(f"\n  [{label}] Weight distribution per epoch:")
        print(f"  {'Epoch':>5} | {'(-1)':>6} | {'(0)':>6} | {'(+1)':>6} | {'Symm':>6} | {'ZeroDrift':>10}")

        prev_zero = None
        for ep in range(10):
            model.train()
            for X, y in trl:
                opt.zero_grad()
                out, _ = model(X.view(X.size(0),-1))
                crit(out, y).backward(); opt.step()

            # Collect ternary stats
            all_dists = []
            for expert in model.experts:
                if hasattr(expert, 'fc1'):
                    # Force a forward pass to update stats
                    model.eval()
                    with torch.no_grad():
                        dummy = torch.randn(1, dim)
                        model(dummy)
                    for layer in [expert.fc1, expert.fc2]:
                        if layer.dist:
                            all_dists.append(layer.dist)

            if all_dists:
                avg = tuple(np.mean([d[i] for d in all_dists]) for i in range(3))
                sym = 1 - abs(avg[0] - avg[2]) / max(avg[0] + avg[2], 0.001)
                zero_drift = avg[1] - prev_zero if prev_zero is not None else 0
                prev_zero = avg[1]
                print(f"  {ep+1:>5} | {avg[0]:>6.4f} | {avg[1]:>6.4f} | {avg[2]:>6.4f} | {sym:>6.4f} | {zero_drift:>+10.4f}")


# ═══════════════════════════════════════
# EXPLORATION 6: The 0.63 Cluster
# ═══════════════════════════════════════
def explore_063_cluster():
    print(f"\n{'='*70}")
    print(f"  EXPLORATION 6: The 0.63 Cluster — Deep Mathematical Dive")
    print(f"{'='*70}")

    log3_2 = math.log(2)/math.log(3)       # 0.63093
    one_minus_inv_e = 1 - 1/math.e          # 0.63212
    two_over_pi = 2/math.pi                 # 0.63662

    print(f"\n  The 0.63 Cluster:")
    print(f"    log_3(2)  = {log3_2:.10f}")
    print(f"    1 - 1/e   = {one_minus_inv_e:.10f}")
    print(f"    2/pi      = {two_over_pi:.10f}")
    center = np.mean([log3_2, one_minus_inv_e, two_over_pi])
    spread = np.std([log3_2, one_minus_inv_e, two_over_pi])
    print(f"    Center:     {center:.10f}")
    print(f"    Spread:     {spread:.10f} ({spread/center*100:.3f}%)")

    # Each pair
    pairs = [
        ('log_3(2)', ' 1-1/e', log3_2, one_minus_inv_e),
        ('log_3(2)', '  2/pi', log3_2, two_over_pi),
        (' 1-1/e',   '  2/pi', one_minus_inv_e, two_over_pi),
    ]
    print(f"\n  Pairwise distances:")
    for a, b, va, vb in pairs:
        d = abs(va - vb)
        print(f"    {a} vs {b}: diff = {d:.10f} ({d/max(va,vb)*100:.4f}%)")

    # Functional relationships
    print(f"\n  Algebraic identities to test:")

    # Test: log_3(2) = 1 - 1/e - epsilon
    eps1 = one_minus_inv_e - log3_2
    print(f"    1-1/e - log_3(2) = {eps1:.10f}")
    print(f"      vs 1/(6*e*pi)  = {1/(6*math.e*math.pi):.10f} (diff: {abs(eps1 - 1/(6*math.e*math.pi)):.10f})")
    print(f"      vs 1/840       = {1/840:.10f} (diff: {abs(eps1 - 1/840):.10f})")
    print(f"      vs 1/(e^6)     = {1/math.e**6:.10f} (diff: {abs(eps1 - 1/math.e**6):.10f})")

    # Test: 2/pi - log_3(2)
    eps2 = two_over_pi - log3_2
    print(f"\n    2/pi - log_3(2) = {eps2:.10f}")
    print(f"      vs 1/(6*pi)    = {1/(6*math.pi):.10f} (diff: {abs(eps2 - 1/(6*math.pi)):.10f})")

    # Test: Are they related via n=6?
    print(f"\n  n=6 connections:")
    print(f"    sigma(6) = 12, tau(6) = 4, phi(6) = 2")
    print(f"    log_3(2) * 6 = {log3_2 * 6:.6f}")
    print(f"    (1-1/e) * 6  = {one_minus_inv_e * 6:.6f}")
    print(f"    (2/pi) * 6   = {two_over_pi * 6:.6f}")
    print(f"    All ~ 3.8 (close to sigma(6)/pi = {12/math.pi:.6f})")

    diff_6_pi = abs(log3_2 * 6 - 12/math.pi)
    print(f"    log_3(2)*6 vs sigma(6)/pi: diff = {diff_6_pi:.6f} ({diff_6_pi/(12/math.pi)*100:.3f}%)")

    # Continued fraction analysis
    print(f"\n  Continued fraction representations:")
    for name, val in [('log_3(2)', log3_2), ('1-1/e', one_minus_inv_e), ('2/pi', two_over_pi)]:
        cf = []
        x = val
        for _ in range(8):
            a = int(x)
            cf.append(a)
            frac = x - a
            if frac < 1e-10: break
            x = 1 / frac
        print(f"    {name:>10} = [{cf[0]}; {', '.join(str(c) for c in cf[1:])}]")

    # Golden ratio connection
    phi = (1 + math.sqrt(5)) / 2
    print(f"\n  Golden ratio connections:")
    print(f"    log_3(2) * phi   = {log3_2 * phi:.6f} (vs 1? diff={abs(log3_2*phi - 1):.6f})")
    print(f"    (1-1/e) * phi    = {one_minus_inv_e * phi:.6f}")
    print(f"    (2/pi) * phi     = {two_over_pi * phi:.6f} (vs 1? diff={abs(two_over_pi*phi - 1):.6f})")

    # TECS-L master formula connection
    print(f"\n  Master formula 1/2+1/3+1/6=1 connection:")
    print(f"    log_3(2) = 1 - log_3(3/2) = 1 - log_3(1+1/2)")
    print(f"    1-1/e is the complement of 1/e in [0,1]")
    print(f"    2/pi = probability of Buffon's needle crossing a line")
    print(f"    All three: 'cost of a fundamental transition'")
    print(f"      log_3(2): cost of base change (binary->ternary)")
    print(f"      1-1/e:    cost of thermal transition")
    print(f"      2/pi:     probability of geometric intersection")


# ═══════════════════════════════════════
# EXPLORATION 7: Expert Count Scaling
# ═══════════════════════════════════════
def explore_expert_scaling():
    print(f"\n{'='*70}")
    print(f"  EXPLORATION 7: Expert Count Scaling (4, 8, 16 experts)")
    print(f"{'='*70}")

    trl, tel, dim, nc = load_data('mnist')

    expert_counts = [4, 8, 16]

    print(f"\n  {'Experts':>8} | {'Dense':>7} | {'Golden':>7} | {'BitN-D':>7} | {'BitN+G':>7} | {'Synergy':>8} | {'Recovery':>9}")
    print(f"  {'─'*8}─+{'─'*9}+{'─'*9}+{'─'*9}+{'─'*9}+{'─'*10}+{'─'*11}")

    for ne in expert_counts:
        accs = {}
        for cname, gt, tern in [('Dense','dense',False), ('Golden','boltzmann',False),
                                  ('BitNet-D','dense',True), ('BitNet+G','boltzmann',True)]:
            torch.manual_seed(42); np.random.seed(42)
            model = MoE(dim, 64, nc, ne, gt, tern, np.e, 0.7)
            opt = torch.optim.Adam(model.parameters(), 0.001)
            crit = nn.CrossEntropyLoss()
            best = 0
            for ep in range(10):
                model.train()
                for X, y in trl:
                    opt.zero_grad()
                    out, _ = model(X.view(X.size(0),-1))
                    crit(out, y).backward(); opt.step()
                model.eval()
                c = t = 0
                with torch.no_grad():
                    for X, y in tel:
                        out, _ = model(X.view(X.size(0),-1))
                        c += (out.argmax(1)==y).sum().item(); t += y.size(0)
                best = max(best, c/t)
            accs[cname] = best

        d = accs['Dense']; g = accs['Golden']; bd = accs['BitNet-D']; bg = accs['BitNet+G']
        syn = (bg-d) - ((g-d)+(bd-d))
        bl = d-bd; dl = d-bg
        rec = (bl-dl)/bl if bl > 0.01 else 0
        print(f"  {ne:>8} | {d*100:>6.2f}% | {g*100:>6.2f}% | {bd*100:>6.2f}% | {bg*100:>6.2f}% | {syn*100:>+7.3f}% | {rec*100:>8.1f}%")


def main():
    print("=" * 70)
    print("  DEEP EXPLORATION: BitNet x Golden MoE")
    print("  Hunting for Major Discoveries")
    print("=" * 70)

    t0 = time.time()

    explore_per_class_synergy()
    explore_expert_specialization()
    explore_synergy_evolution()
    explore_temperature_sweep()
    explore_weight_dynamics()
    explore_063_cluster()
    explore_expert_scaling()

    print(f"\n{'='*70}")
    print(f"  Total time: {time.time()-t0:.1f}s")
    print(f"{'='*70}")

if __name__ == '__main__':
    main()
