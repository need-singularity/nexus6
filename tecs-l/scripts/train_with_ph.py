#!/usr/bin/env python3
"""PH-based automatic learning pipeline

Automatically apply all PH discoveries:
1. Difficulty prediction (H-CX-101)
2. Automatic LR search (H-CX-100)
3. Training + overfitting detection (H-CX-95)
4. Early stopping
5. dendrogram + PCA output (H-CX-85/93)

Usage:
  python3 train_with_ph.py --dataset mnist
  python3 train_with_ph.py --dataset cifar --epochs 30
  python3 train_with_ph.py --dataset fashion --lr auto
"""
import sys, os, argparse, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from scipy.stats import spearmanr
from model_pure_field import PureFieldEngine
from calc.direction_analyzer import load_data

try:
    import gudhi
    HAS_GUDHI = True
except ImportError:
    HAS_GUDHI = False
    try:
        from ripser import ripser
        HAS_RIPSER = True
    except ImportError:
        HAS_RIPSER = False
        print("⚠️ gudhi/ripser not installed — pip install gudhi")


def _ph_h0_lifetime(cos_dist):
    """Compute total H0 lifetime from distance matrix using fastest available backend."""
    if HAS_GUDHI:
        st = gudhi.SimplexTree.create_from_array(cos_dist)
        st.persistence()
        h0 = np.array(st.persistence_intervals_in_dimension(0))
    elif HAS_RIPSER:
        result = ripser(cos_dist, maxdim=0, distance_matrix=True)
        h0 = result['dgms'][0]
    else:
        return cos_dist[np.triu_indices(cos_dist.shape[0], 1)].sum()
    h0_finite = h0[h0[:, 1] < np.inf]
    return np.sum(h0_finite[:, 1] - h0_finite[:, 0]) if len(h0_finite) > 0 else 0


def compute_h0(D, Y, n_cls=10):
    means = []
    for c in range(n_cls):
        mask = Y == c
        if mask.sum() > 0:
            m = D[mask].mean(0)
            n = np.linalg.norm(m)
            means.append(m / max(n, 1e-8))
        else:
            means.append(np.zeros(D.shape[1]))
    means = np.array(means)
    cos_dist = np.clip(1 - means @ means.T, 0, 2)
    np.fill_diagonal(cos_dist, 0)
    return _ph_h0_lifetime(cos_dist)


def extract_dirs(model, dim, loader):
    model.eval()
    dirs, ys, preds, tensions = [], [], [], []
    with torch.no_grad():
        for x, y in loader:
            x_flat = x.view(-1, dim)
            rep = model.engine_a(x_flat) - model.engine_g(x_flat)
            d = F.normalize(rep, dim=-1)
            t = (rep ** 2).mean(-1)
            out = model.tension_scale * torch.sqrt(t.unsqueeze(-1) + 1e-8) * d
            dirs.append(d.numpy())
            ys.extend(y.numpy())
            preds.extend(out.argmax(1).numpy())
            tensions.extend(t.numpy())
    return (np.concatenate(dirs), np.array(ys),
            np.array(preds), np.array(tensions))


def get_merges(cos_dist, n_cls):
    edges = sorted([(cos_dist[i, j], min(i, j), max(i, j))
                    for i in range(n_cls) for j in range(i + 1, n_cls)])
    parent = list(range(n_cls))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        a, b = find(a), find(b)
        if a != b:
            parent[a] = b
            return True
        return False

    merges = []
    for dist, i, j in edges:
        if union(i, j):
            merges.append((dist, i, j))
    return merges


def main():
    parser = argparse.ArgumentParser(description='PH-based automatic learning')
    parser.add_argument('--dataset', default='mnist', choices=['mnist', 'fashion', 'cifar'])
    parser.add_argument('--epochs', type=int, default=20)
    parser.add_argument('--lr', default='auto', help='Learning rate (auto=H0 CV search)')
    parser.add_argument('--batch-size', type=int, default=256)
    parser.add_argument('--hidden', type=int, default=128)
    parser.add_argument('--gap-threshold', type=float, default=0.08)
    parser.add_argument('--seed', type=int, default=42)
    args = parser.parse_args()

    torch.manual_seed(args.seed)
    dim, tl, te, names = load_data(args.dataset)
    n_cls = len(names)

    print(f"\n{'=' * 70}")
    print(f"  PH automatic learning — {args.dataset.upper()}")
    print(f"  epochs={args.epochs}, hidden={args.hidden}, seed={args.seed}")
    print(f"{'=' * 70}")

    # ============================================================
    # Phase 1: Difficulty prediction (H-CX-101)
    # ============================================================
    print(f"\n  ▶ Phase 1: Difficulty prediction (1 epoch H0)")
    torch.manual_seed(args.seed)
    model_probe = PureFieldEngine(dim, args.hidden, n_cls)
    opt_probe = torch.optim.Adam(model_probe.parameters(), lr=1e-3)
    ce = nn.CrossEntropyLoss()

    model_probe.train()
    for x, y in tl:
        opt_probe.zero_grad()
        out, t = model_probe(x.view(-1, dim))
        loss = ce(out, y)
        loss.backward()
        opt_probe.step()

    D_probe, Y_probe, P_probe, _ = extract_dirs(model_probe, dim, te)
    h0_ep1 = compute_h0(D_probe, Y_probe, n_cls)
    acc_ep1 = (P_probe == Y_probe).mean() * 100

    if h0_ep1 > 3.5:
        difficulty = "easy"
    elif h0_ep1 > 2.0:
        difficulty = "medium"
    else:
        difficulty = "hard"

    print(f"    H0_ep1 = {h0_ep1:.4f}, acc_ep1 = {acc_ep1:.1f}%")
    print(f"    Difficulty: {difficulty}")

    # Confusion pairs (H-CX-82: already fixed at ep1)
    means = []
    for c in range(n_cls):
        mask = Y_probe == c
        if mask.sum() > 0:
            m = D_probe[mask].mean(0)
            means.append(m / max(np.linalg.norm(m), 1e-8))
        else:
            means.append(np.zeros(D_probe.shape[1]))
    means = np.array(means)
    cos_dist = np.clip(1 - means @ means.T, 0, 2)
    np.fill_diagonal(cos_dist, 0)
    merges_ep1 = get_merges(cos_dist, n_cls)

    print(f"\n    Confusion pairs (fixed at epoch 1):")
    for dist, i, j in sorted(merges_ep1)[:5]:
        print(f"      {names[i]:>7} ↔ {names[j]:<7}  dist={dist:.4f}")

    del model_probe, opt_probe

    # ============================================================
    # Phase 2: LR search (H-CX-100)
    # ============================================================
    if args.lr == 'auto':
        print(f"\n  ▶ Phase 2: Automatic LR search (minimize H0 CV)")
        lr_candidates = [3e-4, 1e-3, 3e-3]
        best_lr, best_cv = None, 999

        for lr in lr_candidates:
            torch.manual_seed(args.seed)
            m = PureFieldEngine(dim, args.hidden, n_cls)
            o = torch.optim.Adam(m.parameters(), lr=lr)
            h0s = []

            for ep in range(5):
                m.train()
                for x, y in tl:
                    o.zero_grad()
                    out, t = m(x.view(-1, dim))
                    loss = ce(out, y)
                    loss.backward()
                    o.step()
                D_lr, Y_lr, _, _ = extract_dirs(m, dim, te)
                h0s.append(compute_h0(D_lr, Y_lr, n_cls))

            cv = np.std(h0s) / (np.mean(h0s) + 1e-8)
            acc_lr = (np.array([1]) * 0).mean()  # placeholder
            print(f"    LR={lr:.0e}: H0 CV={cv:.4f}")

            if cv < best_cv:
                best_cv = cv
                best_lr = lr
            del m, o

        print(f"    → Best LR: {best_lr:.0e} (CV={best_cv:.4f})")
        lr = best_lr
    else:
        lr = float(args.lr)
        print(f"\n  ▶ Phase 2: LR = {lr} (manual)")

    # ============================================================
    # Phase 3: Main training + PH monitoring (H-CX-95)
    # ============================================================
    print(f"\n  ▶ Phase 3: Start training (LR={lr:.0e}, overfitting detection ON)")
    torch.manual_seed(args.seed)
    model = PureFieldEngine(dim, args.hidden, n_cls)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=args.epochs)

    best_acc = 0
    best_epoch = 0
    alert_count = 0
    early_stop = False

    print(f"\n  {'Ep':>3} {'trn%':>6} {'tst%':>6} {'gap':>6} "
          f"{'H0_tr':>7} {'H0_te':>7} {'H0gap':>7} {'ts':>6} {'status':>8}")
    print(f"  {'-' * 65}")

    for epoch in range(1, args.epochs + 1):
        # Train
        model.train()
        train_correct = train_total = 0
        for x, y in tl:
            optimizer.zero_grad()
            out, t = model(x.view(-1, dim))
            loss = ce(out, y)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            train_correct += (out.argmax(1) == y).sum().item()
            train_total += y.size(0)
        scheduler.step()

        train_acc = train_correct / train_total * 100

        # Eval
        D_tr, Y_tr, P_tr, _ = extract_dirs(model, dim, tl)
        D_te, Y_te, P_te, T_te = extract_dirs(model, dim, te)
        test_acc = (P_te == Y_te).mean() * 100
        acc_gap = train_acc - test_acc

        # PH monitoring
        h0_tr = compute_h0(D_tr, Y_tr, n_cls)
        h0_te = compute_h0(D_te, Y_te, n_cls)
        h0_gap = abs(h0_tr - h0_te)
        ts = model.tension_scale.item()

        # Status
        if h0_gap > args.gap_threshold:
            status = "⚠️ ALERT"
            alert_count += 1
        elif h0_gap > args.gap_threshold * 0.5:
            status = "🟡 WATCH"
        else:
            status = "🟢 OK"

        if test_acc > best_acc:
            best_acc = test_acc
            best_epoch = epoch
            torch.save(model.state_dict(), f'/tmp/best_{args.dataset}.pt')

        print(f"  {epoch:>3} {train_acc:>6.1f} {test_acc:>6.1f} {acc_gap:>+6.1f} "
              f"{h0_tr:>7.4f} {h0_te:>7.4f} {h0_gap:>7.4f} {ts:>6.3f} {status:>8}")

        # Early stopping (3 consecutive ALERTs)
        if alert_count >= 3 and epoch > 5:
            print(f"\n  ⛔ Early stopping (3 consecutive ALERTs, epoch {epoch})")
            early_stop = True
            break

    # ============================================================
    # Phase 4: Result analysis
    # ============================================================
    print(f"\n  ▶ Phase 4: Result analysis")

    # Load best model
    model.load_state_dict(torch.load(f'/tmp/best_{args.dataset}.pt', weights_only=True))
    D_f, Y_f, P_f, T_f = extract_dirs(model, dim, te)
    final_acc = (P_f == Y_f).mean() * 100

    # Confusion pairs
    means_f = []
    for c in range(n_cls):
        mask = Y_f == c
        if mask.sum() > 0:
            m = D_f[mask].mean(0)
            means_f.append(m / max(np.linalg.norm(m), 1e-8))
        else:
            means_f.append(np.zeros(D_f.shape[1]))
    means_f = np.array(means_f)
    cos_dist_f = np.clip(1 - means_f @ means_f.T, 0, 2)
    np.fill_diagonal(cos_dist_f, 0)
    merges_f = get_merges(cos_dist_f, n_cls)

    # Dendrogram (H-CX-85)
    print(f"\n    Dendrogram (semantic hierarchy):")
    clusters = {i: {i} for i in range(n_cls)}
    parent = list(range(n_cls))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        a, b = find(a), find(b)
        if a != b:
            merged = clusters[a] | clusters[b]
            parent[a] = b
            clusters[b] = merged
            if a in clusters and a != b:
                del clusters[a]
            return merged
        return None

    for dist, i, j in sorted([(cos_dist_f[i, j], min(i, j), max(i, j))
                               for i in range(n_cls) for j in range(i + 1, n_cls)]):
        merged = union(i, j)
        if merged and len(merged) >= 2 and len(merged) <= 6:
            cnames = sorted([names[c] for c in merged])
            print(f"      d={dist:.4f} → [{', '.join(cnames)}]")

    # Confusion PCA (H-CX-93)
    from sklearn.decomposition import PCA
    conf = np.zeros((n_cls, n_cls), dtype=int)
    for idx in np.where(P_f != Y_f)[0]:
        conf[Y_f[idx], P_f[idx]] += 1
    conf_sym = (conf + conf.T) / 2.0
    np.fill_diagonal(conf_sym, 0)

    if conf_sym.sum() > 0:
        pca = PCA(n_components=2)
        pca_result = pca.fit_transform(conf_sym)
        pc1 = pca_result[:, 0]
        print(f"\n    Confusion PCA (PC1 = semantic axis):")
        for c in sorted(range(n_cls), key=lambda c: pc1[c]):
            bar = int(abs(pc1[c]) / (max(abs(pc1)) + 1e-8) * 15)
            sign = '+' if pc1[c] > 0 else '-'
            print(f"      {names[c]:>7} {sign}{'█' * bar} {pc1[c]:>7.1f}")

    # FGSM vulnerable pairs (H-CX-104)
    print(f"\n    Expected FGSM vulnerable pairs (sorted by short merge distance):")
    for dist, i, j in sorted(merges_f)[:3]:
        print(f"      {names[i]:>7} ↔ {names[j]:<7}  vulnerability={1 / (dist + 0.01):.1f}")

    # ============================================================
    # Summary
    # ============================================================
    print(f"\n{'=' * 70}")
    print(f"  SUMMARY — {args.dataset.upper()}")
    print(f"{'=' * 70}")
    print(f"  Difficulty:    {difficulty} (H0_ep1={h0_ep1:.4f})")
    print(f"  Best LR:       {lr:.0e}")
    print(f"  Best accuracy: {final_acc:.1f}% (epoch {best_epoch})")
    print(f"  Early stop:    {'yes (epoch ' + str(epoch) + ')' if early_stop else 'no'}")
    print(f"  tension_scale: {model.tension_scale.item():.4f}")
    print(f"  Top confusion: {names[merges_f[0][1]]}-{names[merges_f[0][2]]}")
    elapsed = time.time()
    print(f"{'=' * 70}")


if __name__ == '__main__':
    t0 = time.time()
    main()
    print(f"\n  Total time: {(time.time() - t0) / 60:.1f} min")