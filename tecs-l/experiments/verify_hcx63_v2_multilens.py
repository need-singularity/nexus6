```python
#!/usr/bin/env python3
"""H-CX-63 v2 verification: Multi-lens Precognition — Quad hidden_dim increase + learning rate adjustment

v1 failure cause: PureFieldQuad(hidden_dim=64) learning itself failed (acc~10%)
v2 fix: hidden_dim=128, lr=3e-4, epochs=20
"""
import sys
sys.path.insert(0, '/Users/ghost/Dev/logout')

import torch, torch.nn as nn, torch.nn.functional as F, numpy as np
from sklearn.metrics import roc_auc_score
from model_pure_field import PureFieldEngine
from calc.direction_analyzer import load_data


class PureFieldQuadV2(nn.Module):
    """4-pole pure consciousness engine v2 — larger hidden, pairwise repulsion."""

    def __init__(self, input_dim=784, hidden_dim=128, output_dim=10):
        super().__init__()
        self.engines = nn.ModuleList([
            nn.Sequential(nn.Linear(input_dim, hidden_dim), nn.ReLU(),
                          nn.Dropout(0.3), nn.Linear(hidden_dim, output_dim))
            for _ in range(4)
        ])
        self.tension_scale = nn.Parameter(torch.tensor(1.0))

    def forward(self, x):
        outs = [e(x) for e in self.engines]
        # Core change: use repulsion of main diagonal pairs (A-G, E-F) instead of average
        repulsion_ag = outs[0] - outs[2]  # A vs G
        repulsion_ef = outs[1] - outs[3]  # E vs F
        repulsion = (repulsion_ag + repulsion_ef) / 2
        tension = (repulsion ** 2).mean(dim=-1, keepdim=True)
        direction = F.normalize(repulsion, dim=-1)
        output = self.tension_scale * torch.sqrt(tension + 1e-8) * direction
        return output, tension.squeeze()

    def get_pair_tensions(self, x):
        """Return tensions for 6 engine pairs"""
        outs = [e(x) for e in self.engines]
        pairs = {}
        names = ['A', 'E', 'G', 'F']
        for i in range(4):
            for j in range(i+1, 4):
                rep = outs[i] - outs[j]
                t = (rep ** 2).mean(-1)
                pairs[f"{names[i]}-{names[j]}"] = t
        return pairs


def train_and_eval(model, dim, tl, te, epochs=20, lr=3e-4, name="model"):
    opt = torch.optim.Adam(model.parameters(), lr=lr)
    ce = nn.CrossEntropyLoss()

    for ep in range(epochs):
        model.train()
        for x, y in tl:
            opt.zero_grad()
            out, t = model(x.view(-1, dim))
            loss = ce(out, y); loss.backward(); opt.step()
        if (ep+1) % 5 == 0:
            model.eval(); correct = total = 0
            with torch.no_grad():
                for x, y in te:
                    o, _ = model(x.view(-1, dim))
                    correct += (o.argmax(1)==y).sum().item(); total += y.size(0)
            print(f"    {name} Epoch {ep+1}: acc={correct/total*100:.1f}%")

    model.eval()
    tensions, corrects = [], []
    with torch.no_grad():
        for x, y in te:
            out, t = model(x.view(-1, dim))
            pred = out.argmax(1)
            tensions.extend(t.numpy().tolist())
            corrects.extend((pred == y).numpy().tolist())

    T = np.array(tensions); C = np.array(corrects, dtype=float)
    acc = C.mean() * 100
    auc = roc_auc_score(C, T) if len(np.unique(C)) > 1 else 0.5
    ts = model.tension_scale.item()
    return T, C, acc, auc, ts


def run_experiment(dataset_name='mnist', epochs=20):
    dim, tl, te, names = load_data(dataset_name)

    print(f"\n{'='*70}")
    print(f"  H-CX-63 v2: Multi-Lens Precognition — {dataset_name.upper()}")
    print(f"{'='*70}")

    # Dual
    print(f"\n  --- Dual (PureFieldEngine, hidden=128) ---")
    dual = PureFieldEngine(dim, 128, 10)
    T2, C2, acc2, auc2, ts2 = train_and_eval(dual, dim, tl, te, epochs, lr=1e-3, name="Dual")
    print(f"    Params: {sum(p.numel() for p in dual.parameters()):,}  Acc: {acc2:.1f}%  AUC: {auc2:.4f}")

    # Quad v2 (larger hidden, paired repulsion)
    print(f"\n  --- Quad v2 (PureFieldQuadV2, hidden=128, paired repulsion) ---")
    quad = PureFieldQuadV2(dim, 128, 10)
    T4, C4, acc4, auc4, ts4 = train_and_eval(quad, dim, tl, te, epochs, lr=3e-4, name="QuadV2")
    print(f"    Params: {sum(p.numel() for p in quad.parameters()):,}  Acc: {acc4:.1f}%  AUC: {auc4:.4f}")

    # Comparison
    print(f"\n  {'='*55}")
    print(f"  {'':>15} {'Dual':>10} {'QuadV2':>10} {'Delta':>10}")
    print(f"  {'-'*45}")
    print(f"  {'Parameters':>15} {sum(p.numel() for p in dual.parameters()):>10,} {sum(p.numel() for p in quad.parameters()):>10,}")
    print(f"  {'Accuracy':>15} {acc2:>10.1f} {acc4:>10.1f} {acc4-acc2:>+10.1f}")
    print(f"  {'Precog AUC':>15} {auc2:>10.4f} {auc4:>10.4f} {auc4-auc2:>+10.4f}")
    print(f"  {'t_scale':>15} {ts2:>10.4f} {ts4:>10.4f} {ts4-ts2:>+10.4f}")

    amp = auc4 / auc2 if auc2 > 0 else 0
    print(f"\n  Amplification (Quad/Dual): {amp:.4f}")
    print(f"  Winner: {'QuadV2' if auc4 > auc2 else 'Dual'}")

    # Quad pair analysis
    if acc4 > 15:  # only if learning succeeded
        print(f"\n  --- Quad V2 Pair Tensions ---")
        quad.eval()
        pair_data = {k: [] for k in ['A-E', 'A-G', 'A-F', 'E-G', 'E-F', 'G-F']}
        all_correct = []
        with torch.no_grad():
            for x, y in te:
                x_flat = x.view(-1, dim)
                pairs = quad.get_pair_tensions(x_flat)
                out, _ = quad(x_flat)
                pred = out.argmax(1)
                all_correct.extend((pred == y).numpy().tolist())
                for k, v in pairs.items():
                    pair_data[k].extend(v.numpy().tolist())

        Cq = np.array(all_correct, dtype=float)
        direct = ['A-G', 'E-F']
        cross = ['A-E', 'A-F', 'E-G', 'G-F']

        print(f"  {'Pair':>7} {'Mean_T':>8} {'AUC':>7} {'Type':>8}")
        print(f"  {'-'*35}")
        direct_aucs, cross_aucs = [], []
        for k in pair_data:
            pt = np.array(pair_data[k])
            p_auc = roc_auc_score(Cq, pt) if len(np.unique(Cq)) > 1 else 0.5
            ptype = 'DIRECT' if k in direct else 'CROSS'
            if ptype == 'DIRECT': direct_aucs.append(p_auc)
            else: cross_aucs.append(p_auc)
            print(f"  {k:>7} {pt.mean():>8.3f} {p_auc:>7.4f} {ptype:>8}")

        print(f"\n  Mean direct AUC: {np.mean(direct_aucs):.4f}")
        print(f"  Mean cross AUC:  {np.mean(cross_aucs):.4f}")

    return acc2, auc2, acc4, auc4

if __name__ == '__main__':
    results = {}
    for ds in ['mnist', 'fashion', 'cifar']:
        try:
            a2, au2, a4, au4 = run_experiment(ds)
            results[ds] = (a2, au2, a4, au4)
        except Exception as e:
            print(f"  {ds} failed: {e}")
            import traceback; traceback.print_exc()

    print(f"\n{'='*70}")
    print(f"  H-CX-63 v2 FINAL SUMMARY")
    print(f"{'='*70}")
    print(f"  {'Dataset':>10} {'Dual_Acc':>9} {'Dual_AUC':>9} {'Quad_Acc':>9} {'Quad_AUC':>9} {'Winner':>7}")
    print(f"  {'-'*55}")
    for ds, (a2, au2, a4, au4) in results.items():
        w = 'QuadV2' if au4 > au2 else 'Dual'
        print(f"  {ds:>10} {a2:>9.1f} {au2:>9.4f} {a4:>9.1f} {au4:>9.4f} {w:>7}")
```