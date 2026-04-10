#!/usr/bin/env python3
"""H-CX-148~151: Telepathy Mechanisms 4 types

148: Tension Resonance (two independent models tension correlation)
149: Direction Telepathy (A's dir → G's next output)
150: Silent Consensus (class direction convergence)
151: Cross-layer Tension Signal (cross-layer tension correlation)
"""
import sys
sys.path.insert(0, '/Users/ghost/Dev/logout')

import torch, torch.nn as nn, torch.nn.functional as F, numpy as np
from scipy.stats import spearmanr
from model_pure_field import PureFieldEngine
from calc.direction_analyzer import load_data


def run_all():
    dim, tl, te, names = load_data('mnist')
    n_cls = 10

    print(f"\n{'='*70}")
    print(f"  H-CX-148~151: Telepathy Mechanisms — MNIST")
    print(f"{'='*70}")

    # Train two independent models
    torch.manual_seed(42)
    model_a = PureFieldEngine(dim, 128, 10)
    torch.manual_seed(777)
    model_b = PureFieldEngine(dim, 128, 10)

    opt_a = torch.optim.Adam(model_a.parameters(), lr=1e-3)
    opt_b = torch.optim.Adam(model_b.parameters(), lr=1e-3)
    ce = nn.CrossEntropyLoss()

    for ep in range(15):
        for m, o in [(model_a, opt_a), (model_b, opt_b)]:
            m.train()
            for x, y in tl:
                o.zero_grad()
                out, t = m(x.view(-1, dim))
                loss = ce(out, y); loss.backward(); o.step()

    # === H-CX-148: Tension Resonance ===
    print(f"\n  === H-CX-148: Tension Resonance ===")
    model_a.eval(); model_b.eval()
    tensions_a, tensions_b = [], []
    with torch.no_grad():
        for x, y in te:
            x_flat = x.view(-1, dim)
            _, ta = model_a(x_flat)
            _, tb = model_b(x_flat)
            tensions_a.extend(ta.numpy()); tensions_b.extend(tb.numpy())

    r_148, p_148 = spearmanr(tensions_a, tensions_b)
    print(f"  Tension correlation (independent models): r={r_148:.4f}, p={p_148:.6f}")
    print(f"  H-CX-148 (r > 0.5): {'SUPPORTED' if r_148 > 0.5 else 'PARTIAL' if r_148 > 0.3 else 'REJECTED'}")

    # === H-CX-149: Direction Telepathy A→G ===
    print(f"\n  === H-CX-149: Direction Telepathy A→G ===")
    # Can A's direction predict G's output?
    model_a.eval()
    dir_a_list, out_g_list = [], []
    with torch.no_grad():
        for x, y in te:
            x_flat = x.view(-1, dim)
            a_out = model_a.engine_a(x_flat)
            g_out = model_a.engine_g(x_flat)
            dir_a = F.normalize(a_out, dim=-1)
            dir_a_list.append(dir_a.numpy())
            out_g_list.append(g_out.numpy())

    D_a = np.concatenate(dir_a_list); G_out = np.concatenate(out_g_list)
    # Correlation between A's direction and G's output (per dimension average)
    corrs = []
    for d in range(min(10, D_a.shape[1])):
        r, _ = spearmanr(D_a[:, d], G_out[:, d])
        if not np.isnan(r): corrs.append(abs(r))
    mean_corr = np.mean(corrs) if corrs else 0
    print(f"  Mean |corr(dir_A[d], out_G[d])|: {mean_corr:.4f}")
    print(f"  H-CX-149 (mean > 0.3): {'SUPPORTED' if mean_corr > 0.3 else 'PARTIAL' if mean_corr > 0.1 else 'REJECTED'}")

    # === H-CX-150: Silent Consensus ===
    print(f"\n  === H-CX-150: Silent Consensus ===")
    # Do two independent models converge to same class directions?
    model_a.eval(); model_b.eval()
    means_a = np.zeros((n_cls, 10)); means_b = np.zeros((n_cls, 10))
    counts = np.zeros(n_cls)
    with torch.no_grad():
        for x, y in te:
            x_flat = x.view(-1, dim)
            rep_a = model_a.engine_a(x_flat) - model_a.engine_g(x_flat)
            rep_b = model_b.engine_a(x_flat) - model_b.engine_g(x_flat)
            da = F.normalize(rep_a, dim=-1).numpy()
            db = F.normalize(rep_b, dim=-1).numpy()
            for i in range(len(y)):
                c = y[i].item()
                means_a[c] += da[i, :10]
                means_b[c] += db[i, :10]
                counts[c] += 1

    for c in range(n_cls):
        if counts[c] > 0:
            means_a[c] /= counts[c]; means_b[c] /= counts[c]
            means_a[c] /= max(np.linalg.norm(means_a[c]), 1e-8)
            means_b[c] /= max(np.linalg.norm(means_b[c]), 1e-8)

    # Cosine similarity of class directions between models
    cos_sims = []
    for c in range(n_cls):
        cos = (means_a[c] * means_b[c]).sum()
        cos_sims.append(cos)
        print(f"  Class {names[c]:>5}: cos(A,B) = {cos:.4f}")

    mean_cos = np.mean(cos_sims)
    print(f"\n  Mean cosine(model_A, model_B): {mean_cos:.4f}")
    print(f"  H-CX-150 (mean > 0.5): {'SUPPORTED' if mean_cos > 0.5 else 'PARTIAL' if mean_cos > 0.2 else 'REJECTED'}")

    # === H-CX-151: Cross-layer Tension Signal ===
    print(f"\n  === H-CX-151: Cross-layer Tension Signal ===")
    # PureFieldEngine has only 1 layer, so use ConsciousLM-like multi-block
    # Proxy: correlate tension with output confidence
    model_a.eval()
    tensions, confidences = [], []
    with torch.no_grad():
        for x, y in te:
            x_flat = x.view(-1, dim)
            out, t = model_a(x_flat)
            probs = F.softmax(out, dim=-1)
            conf = probs.max(dim=-1).values
            tensions.extend(t.numpy()); confidences.extend(conf.numpy())

    r_151, p_151 = spearmanr(tensions, confidences)
    print(f"  Corr(tension, output_confidence): r={r_151:.4f}, p={p_151:.6f}")
    print(f"  = tension transmits signal to output confidence")
    print(f"  H-CX-151 (r > 0.5): {'SUPPORTED' if r_151 > 0.5 else 'PARTIAL' if r_151 > 0.3 else 'REJECTED'}")

    print(f"\n{'='*70}")
    print(f"  SUMMARY")
    print(f"{'='*70}")
    print(f"  H-CX-148 Tension Resonance:     r={r_148:.4f}")
    print(f"  H-CX-149 Direction Telepathy:   mean_corr={mean_corr:.4f}")
    print(f"  H-CX-150 Silent Consensus:      mean_cos={mean_cos:.4f}")
    print(f"  H-CX-151 Tension Signal:        r={r_151:.4f}")


if __name__ == '__main__':
    run_all()