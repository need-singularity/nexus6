```python
#!/usr/bin/env python3
"""H-CX-94~97 Integration: meta-PH + generalization gap + weight transfer + cross dataset

Round 8: Utilization and mechanisms of confusion structures
"""
import sys, copy
sys.path.insert(0, '/Users/ghost/Dev/logout')

import torch, torch.nn as nn, torch.nn.functional as F, numpy as np
from sklearn.metrics import roc_auc_score
from scipy.stats import spearmanr, kendalltau
from ripser import ripser
from model_pure_field import PureFieldEngine
from calc.direction_analyzer import load_data


def get_ph_features(D, Y, n_cls=10):
    means = []
    for c in range(n_cls):
        mask = Y == c
        if mask.sum() > 0:
            m = D[mask].mean(0); n = np.linalg.norm(m)
            means.append(m / max(n, 1e-8))
        else:
            means.append(np.zeros(D.shape[1]))
    means = np.array(means)
    cos_dist = np.clip(1 - means @ means.T, 0, 2)
    np.fill_diagonal(cos_dist, 0)

    result = ripser(cos_dist, maxdim=0, distance_matrix=True)
    h0 = result['dgms'][0]
    h0_finite = h0[h0[:, 1] < np.inf]
    h0_total = np.sum(h0_finite[:, 1] - h0_finite[:, 0]) if len(h0_finite) > 0 else 0

    # Merge events
    sorted_edges = sorted([(cos_dist[i,j], min(i,j), max(i,j))
                           for i in range(n_cls) for j in range(i+1, n_cls)])
    parent = list(range(n_cls))
    def find(x):
        while parent[x] != x: parent[x] = parent[parent[x]]; x = parent[x]
        return x
    def union(a, b):
        a, b = find(a), find(b)
        if a != b: parent[a] = b; return True
        return False
    merges = []
    for dist, i, j in sorted_edges:
        if union(i, j): merges.append((dist, i, j))

    return h0_total, merges, cos_dist


def pair_conf(Y, P, n_cls):
    conf = np.zeros((n_cls, n_cls), dtype=int)
    for idx in np.where(P != Y)[0]:
        conf[Y[idx], P[idx]] += 1
    pairs = {}
    for i in range(n_cls):
        for j in range(i+1, n_cls):
            pairs[(i,j)] = conf[i,j] + conf[j,i]
    return pairs, conf


def eval_model(model, dim, loader):
    model.eval()
    dirs, ys, preds = [], [], []
    with torch.no_grad():
        for x, y in loader:
            x_flat = x.view(-1, dim)
            rep = model.engine_a(x_flat) - model.engine_g(x_flat)
            d = F.normalize(rep, dim=-1)
            out = model.tension_scale * torch.sqrt((rep**2).mean(-1, keepdim=True)+1e-8) * d
            dirs.append(d.numpy()); ys.extend(y.numpy().tolist())
            preds.extend(out.argmax(1).numpy().tolist())
    return np.concatenate(dirs), np.array(ys), np.array(preds)


def run_experiment(dataset_name='mnist', epochs=15):
    dim, tl, te, names = load_data(dataset_name)
    n_cls = len(names)

    print(f"\n{'='*70}")
    print(f"  H-CX-94~97: Round 8 — {dataset_name.upper()}")
    print(f"{'='*70}")

    torch.manual_seed(42)
    model = PureFieldEngine(dim, 128, 10)
    opt = torch.optim.Adam(model.parameters(), lr=1e-3)
    ce = nn.CrossEntropyLoss()

    # Save epoch 0 weights
    w0 = {k: v.clone() for k, v in model.state_dict().items()}

    # === H-CX-96: Weight delta tracking ===
    weight_deltas = []
    h0_deltas = []
    prev_h0 = None
    prev_w = w0

    epoch_train_acc = []
    epoch_test_acc = []
    epoch_h0_train = []
    epoch_h0_test = []

    for ep in range(epochs):
        model.train()
        train_correct = train_total = 0
        for x, y in tl:
            opt.zero_grad()
            out, t = model(x.view(-1, dim))
            loss = ce(out, y); loss.backward(); opt.step()
            train_correct += (out.argmax(1)==y).sum().item()
            train_total += y.size(0)
        train_acc = train_correct / train_total * 100

        # Weight delta
        curr_w = {k: v.clone() for k, v in model.state_dict().items()}
        delta_w = sum(((curr_w[k] - prev_w[k])**2).sum().item() for k in curr_w)
        delta_w = delta_w ** 0.5
        weight_deltas.append(delta_w)
        prev_w = curr_w

        # Test eval
        D_te, Y_te, P_te = eval_model(model, dim, te)
        test_acc = (P_te == Y_te).mean() * 100

        # Train eval (subsample)
        D_tr, Y_tr, P_tr = eval_model(model, dim, tl)
        tr_acc_eval = (P_tr == Y_tr).mean() * 100

        # PH on train and test
        h0_te, merges_te, _ = get_ph_features(D_te, Y_te, n_cls)
        h0_tr, merges_tr, _ = get_ph_features(D_tr, Y_tr, n_cls)

        if prev_h0 is not None:
            h0_deltas.append(abs(h0_te - prev_h0))
        prev_h0 = h0_te

        epoch_train_acc.append(tr_acc_eval)
        epoch_test_acc.append(test_acc)
        epoch_h0_train.append(h0_tr)
        epoch_h0_test.append(h0_te)

        if (ep+1) % 5 == 0 or ep == 0:
            gap = tr_acc_eval - test_acc
            print(f"  Ep {ep+1}: train={tr_acc_eval:.1f}% test={test_acc:.1f}% gap={gap:+.1f} "
                  f"H0_tr={h0_tr:.4f} H0_te={h0_te:.4f} dW={delta_w:.2f}")

    # Final confusion
    pairs_te, conf_te = pair_conf(Y_te, P_te, n_cls)

    # === H-CX-94: Meta-PH ===
    print(f"\n  === H-CX-94: Meta-PH (Confusion as Distance) ===")
    conf_sym = (conf_te + conf_te.T) / 2.0
    max_conf = conf_sym.max()
    conf_dist = max_conf - conf_sym  # high confusion = low distance
    np.fill_diagonal(conf_dist, 0)
    conf_dist = np.clip(conf_dist, 0, None)

    meta_result = ripser(conf_dist, maxdim=1, distance_matrix=True)
    meta_h0 = meta_result['dgms'][0]
    meta_h0_finite = meta_h0[meta_h0[:, 1] < np.inf]
    meta_h0_total = np.sum(meta_h0_finite[:, 1] - meta_h0_finite[:, 0]) if len(meta_h0_finite) > 0 else 0

    meta_h1 = meta_result['dgms'][1] if len(meta_result['dgms']) > 1 else np.array([]).reshape(0,2)

    print(f"  Meta-H0 features: {len(meta_h0_finite)}, total_persist: {meta_h0_total:.2f}")
    print(f"  Meta-H1 features: {len(meta_h1)}")

    # Meta merge events
    meta_merges = []
    sorted_meta = sorted([(conf_dist[i,j], min(i,j), max(i,j))
                          for i in range(n_cls) for j in range(i+1, n_cls)])
    parent = list(range(n_cls))
    def find(x):
        while parent[x] != x: parent[x] = parent[parent[x]]; x = parent[x]
        return x
    def union(a, b):
        a, b = find(a), find(b)
        if a != b: parent[a] = b; return True
        return False
    for dist, i, j in sorted_meta:
        if union(i, j): meta_merges.append((dist, i, j))

    # Compare meta-merge with PH merge
    _, ph_merges, _ = get_ph_features(D_te, Y_te, n_cls)
    ph_order = [(min(i,j),max(i,j)) for d,i,j in sorted(ph_merges, key=lambda x: x[0])]
    meta_order = [(min(i,j),max(i,j)) for d,i,j in sorted(meta_merges, key=lambda x: x[0])]
    ph_rank = {p: k for k, p in enumerate(ph_order)}
    meta_vals = [ph_rank.get(p, 99) for p in meta_order]
    tau_meta, _ = kendalltau(list(range(len(meta_order))), meta_vals)

    print(f"  Meta-merge vs PH-merge Kendall tau: {tau_meta:.4f}")
    print(f"  H-CX-94 (self-consistency tau > 0.5): {'SUPPORTED' if tau_meta > 0.5 else 'REJECTED'}")

    print(f"\n  Meta-merge order (confusion-based):")
    for dist, i, j in meta_merges[:5]:
        conf_val = conf_sym[i,j]
        print(f"    {names[i]:>6}-{names[j]:<6} conf_dist={dist:.1f}  confusion={conf_val:.0f}")

    # === H-CX-95: Generalization Gap ===
    print(f"\n  === H-CX-95: PH Generalization Gap ===")
    gaps = [epoch_train_acc[i] - epoch_test_acc[i] for i in range(epochs)]
    ph_gaps = [abs(epoch_h0_train[i] - epoch_h0_test[i]) for i in range(epochs)]

    r_gap, p_gap = spearmanr(ph_gaps, gaps)
    print(f"  Spearman(|H0_train-H0_test|, gen_gap): r={r_gap:.4f}, p={p_gap:.4f}")

    print(f"  {'Epoch':>5} {'Train%':>7} {'Test%':>7} {'Gap':>6} {'H0_gap':>7}")
    print(f"  {'-'*35}")
    for i in range(0, epochs, 3):
        print(f"  {i+1:>5} {epoch_train_acc[i]:>7.1f} {epoch_test_acc[i]:>7.1f} "
              f"{gaps[i]:>+6.1f} {ph_gaps[i]:>7.4f}")

    print(f"  H-CX-95 (r > 0.5): {'SUPPORTED' if r_gap > 0.5 else 'PARTIAL' if r_gap > 0.3 else 'REJECTED'}")

    # === H-CX-96: Weight Delta ===
    print(f"\n  === H-CX-96: Weight Delta Phase Transition ===")
    dw_01 = weight_deltas[0]
    dw_rest = np.mean(weight_deltas[1:])
    ratio_w = dw_01 / dw_rest if dw_rest > 0 else 999

    print(f"  ||dW|| ep0→1: {dw_01:.4f}  avg(ep1→...): {dw_rest:.4f}  ratio: {ratio_w:.2f}x")

    # Correlation between weight delta and H0 delta
    if len(h0_deltas) > 3:
        r_wh, p_wh = spearmanr(weight_deltas[1:len(h0_deltas)+1], h0_deltas)
        print(f"  Corr(||dW||, |dH0|): r={r_wh:.4f}")
    else:
        r_wh = 0

    print(f"  {'Epoch':>5} {'||dW||':>10} {'|dH0|':>10}")
    print(f"  {'-'*28}")
    for i in range(min(5, len(weight_deltas))):
        dh = h0_deltas[i] if i < len(h0_deltas) else 0
        print(f"  {i+1:>5} {weight_deltas[i]:>10.4f} {dh:>10.4f}")

    print(f"  H-CX-96 (dW ratio > 2): {'SUPPORTED' if ratio_w > 2 else 'REJECTED'}")

    # === H-CX-96b: Slow LR ===
    print(f"\n  --- H-CX-96b: Slow LR (1e-4) phase transition delay ---")
    torch.manual_seed(42)
    model_slow = PureFieldEngine(dim, 128, 10)
    opt_slow = torch.optim.Adam(model_slow.parameters(), lr=1e-4)

    slow_h0s = []
    model_slow.eval()
    D_s0, Y_s0, _ = eval_model(model_slow, dim, te)
    h0_s0, _, _ = get_ph_features(D_s0, Y_s0, n_cls)
    slow_h0s.append(h0_s0)

    for ep in range(10):
        model_slow.train()
        for x, y in tl:
            opt_slow.zero_grad()
            out, t = model_slow(x.view(-1, dim))
            loss = ce(out, y); loss.backward(); opt_slow.step()
        model_slow.eval()
        D_s, Y_s, P_s = eval_model(model_slow, dim, te)
        h0_s, _, _ = get_ph_features(D_s, Y_s, n_cls)
        slow_h0s.append(h0_s)
        acc_s = (P_s == Y_s).mean() * 100
        if (ep+1) % 2 == 0:
            print(f"  Slow ep{ep+1}: acc={acc_s:.1f}%  H0={h0_s:.4f}")

    # Find when big H0 change happens
    slow_changes = [abs(slow_h0s[i+1]-slow_h0s[i]) for i in range(len(slow_h0s)-1)]
    max_change_ep = np.argmax(slow_changes)
    print(f"  Max H0 change at slow ep{max_change_ep}: {slow_changes[max_change_ep]:.4f}")
    print(f"  Normal LR: phase transition at ep0→1")
    print(f"  Slow LR: phase transition at ep{max_change_ep}→{max_change_ep+1}")
    print(f"  Delayed? {'YES' if max_change_ep > 0 else 'NO (still ep0→1)'}")

    return {
        'meta_tau': tau_meta, 'meta_h0': meta_h0_total,
        'r_gap': r_gap, 'dw_ratio': ratio_w,
        'slow_delay': max_change_ep,
    }

if __name__ == '__main__':
    results = {}
    for ds in ['mnist', 'fashion', 'cifar']:
        try:
            results[ds] = run_experiment(ds)
        except Exception as e:
            print(f"  {ds} failed: {e}")
            import traceback; traceback.print_exc()

    print(f"\n{'='*70}")
    print(f"  Round 8 SUMMARY")
    print(f"{'='*70}")
    for ds, r in results.items():
        print(f"  {ds}: meta_tau={r['meta_tau']:.3f}, r_gap={r['r_gap']:.3f}, "
              f"dw_ratio={r['dw_ratio']:.1f}x, slow_delay=ep{r['slow_delay']}")
```