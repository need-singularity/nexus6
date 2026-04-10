#!/usr/bin/env python3
"""H-CX-98~101: Round 9 — PH Practical Tool Verification

H-CX-98: PH early stopping vs val_loss early stopping
H-CX-99: H0_gap minimum epoch = optimal checkpoint?
H-CX-100: H0 stability in LR sweep → optimal LR
H-CX-101: Epoch 1 H0_total = dataset difficulty score
"""
import sys
sys.path.insert(0, '/Users/ghost/Dev/logout')

import torch, torch.nn as nn, torch.nn.functional as F, numpy as np
from scipy.stats import spearmanr
from ripser import ripser
from model_pure_field import PureFieldEngine
from calc.direction_analyzer import load_data


def compute_h0(D, Y, n_cls=10):
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
    return np.sum(h0_finite[:, 1] - h0_finite[:, 0]) if len(h0_finite) > 0 else 0


def extract_dirs(model, dim, loader):
    model.eval()
    dirs, ys, preds = [], [], []
    with torch.no_grad():
        for x, y in loader:
            x_flat = x.view(-1, dim)
            rep = model.engine_a(x_flat) - model.engine_g(x_flat)
            d = F.normalize(rep, dim=-1)
            out = model.tension_scale * torch.sqrt((rep**2).mean(-1, keepdim=True)+1e-8) * d
            dirs.append(d.numpy()); ys.extend(y.numpy()); preds.extend(out.argmax(1).numpy())
    return np.concatenate(dirs), np.array(ys), np.array(preds)


def train_with_tracking(dataset_name, epochs=20, lr=1e-3):
    dim, tl, te, names = load_data(dataset_name)
    n_cls = len(names)
    torch.manual_seed(42)
    model = PureFieldEngine(dim, 128, 10)
    opt = torch.optim.Adam(model.parameters(), lr=lr)
    ce = nn.CrossEntropyLoss()

    history = []
    for ep in range(epochs):
        model.train()
        train_loss_sum = 0; train_n = 0
        for x, y in tl:
            opt.zero_grad()
            out, t = model(x.view(-1, dim))
            loss = ce(out, y); loss.backward(); opt.step()
            train_loss_sum += loss.item() * y.size(0); train_n += y.size(0)

        # Eval
        D_tr, Y_tr, P_tr = extract_dirs(model, dim, tl)
        D_te, Y_te, P_te = extract_dirs(model, dim, te)
        train_acc = (P_tr == Y_tr).mean() * 100
        test_acc = (P_te == Y_te).mean() * 100

        # Val loss
        model.eval()
        val_loss_sum = 0; val_n = 0
        with torch.no_grad():
            for x, y in te:
                out, _ = model(x.view(-1, dim))
                loss = ce(out, y)
                val_loss_sum += loss.item() * y.size(0); val_n += y.size(0)
        val_loss = val_loss_sum / val_n
        train_loss = train_loss_sum / train_n

        h0_tr = compute_h0(D_tr, Y_tr, n_cls)
        h0_te = compute_h0(D_te, Y_te, n_cls)
        h0_gap = abs(h0_tr - h0_te)

        history.append({
            'ep': ep+1, 'train_acc': train_acc, 'test_acc': test_acc,
            'train_loss': train_loss, 'val_loss': val_loss,
            'h0_tr': h0_tr, 'h0_te': h0_te, 'h0_gap': h0_gap,
        })

    return history


def run_experiment(dataset_name='cifar', epochs=20):
    print(f"\n{'='*70}")
    print(f"  H-CX-98~101: Round 9 — {dataset_name.upper()}")
    print(f"{'='*70}")

    history = train_with_tracking(dataset_name, epochs)

    # Print tracking table
    print(f"\n  {'Ep':>3} {'trn%':>6} {'tst%':>6} {'gap':>6} {'vLoss':>7} {'H0gap':>7}")
    print(f"  {'-'*40}")
    for h in history:
        print(f"  {h['ep']:>3} {h['train_acc']:>6.1f} {h['test_acc']:>6.1f} "
              f"{h['train_acc']-h['test_acc']:>+6.1f} {h['val_loss']:>7.4f} {h['h0_gap']:>7.4f}")

    # === H-CX-98: Early stopping comparison ===
    print(f"\n  === H-CX-98: PH vs Val_Loss Early Stopping ===")

    # Val_loss early stop: first epoch where val_loss increases 3 times in a row
    val_losses = [h['val_loss'] for h in history]
    val_stop_ep = epochs
    for i in range(2, len(val_losses)):
        if val_losses[i] > val_losses[i-1] > val_losses[i-2]:
            val_stop_ep = i - 1  # stop at the minimum before increases
            break

    # Best val_loss epoch
    best_val_ep = np.argmin(val_losses) + 1

    # H0_gap early stop: first epoch where H0_gap > threshold
    h0_gaps = [h['h0_gap'] for h in history]
    # Adaptive threshold: 2x the minimum H0_gap
    min_h0_gap = min(h0_gaps)
    h0_threshold = max(min_h0_gap * 3, 0.03)
    h0_stop_ep = epochs
    for i, g in enumerate(h0_gaps):
        if g > h0_threshold:
            h0_stop_ep = i + 1
            break

    test_accs = [h['test_acc'] for h in history]
    best_test_ep = np.argmax(test_accs) + 1

    print(f"  Val_loss early stop:  ep{val_stop_ep} (test_acc={test_accs[min(val_stop_ep-1, len(test_accs)-1)]:.1f}%)")
    print(f"  Best val_loss epoch:  ep{best_val_ep} (test_acc={test_accs[best_val_ep-1]:.1f}%)")
    print(f"  H0_gap early stop:   ep{h0_stop_ep} (threshold={h0_threshold:.4f}, test_acc={test_accs[min(h0_stop_ep-1, len(test_accs)-1)]:.1f}%)")
    print(f"  Best test_acc epoch:  ep{best_test_ep} (test_acc={test_accs[best_test_ep-1]:.1f}%)")
    print(f"  H-CX-98 (H0 stop earlier): {'SUPPORTED' if h0_stop_ep < val_stop_ep else 'REJECTED'}")

    # === H-CX-99: Optimal checkpoint ===
    print(f"\n  === H-CX-99: H0_gap Minimum = Optimal Checkpoint? ===")
    min_h0_ep = np.argmin(h0_gaps) + 1
    print(f"  Min H0_gap at ep{min_h0_ep} (H0_gap={min(h0_gaps):.4f}, test_acc={test_accs[min_h0_ep-1]:.1f}%)")
    print(f"  Best test_acc at ep{best_test_ep} (test_acc={max(test_accs):.1f}%)")
    delta = abs(min_h0_ep - best_test_ep)
    print(f"  Delta: {delta} epochs")
    print(f"  H-CX-99 (delta <= 3): {'SUPPORTED' if delta <= 3 else 'REJECTED'}")

    # === H-CX-101: Dataset difficulty score ===
    print(f"\n  === H-CX-101: Epoch 1 H0 = Difficulty Score ===")
    h0_ep1 = history[0]['h0_te']
    final_acc = history[-1]['test_acc']
    print(f"  Epoch 1 H0_test: {h0_ep1:.4f}")
    print(f"  Final test_acc:  {final_acc:.1f}%")

    return {
        'h0_ep1': h0_ep1, 'final_acc': final_acc,
        'h0_stop_ep': h0_stop_ep, 'val_stop_ep': val_stop_ep,
        'best_test_ep': best_test_ep, 'min_h0_ep': min_h0_ep,
        'h0_gaps': h0_gaps, 'test_accs': test_accs,
    }


def run_lr_sweep(dataset_name='cifar'):
    """H-CX-100: LR sweep with H0 stability"""
    print(f"\n  === H-CX-100: LR Sweep — {dataset_name.upper()} ===")
    lrs = [3e-4, 1e-3, 3e-3, 1e-2]
    lr_results = []

    for lr in lrs:
        history = train_with_tracking(dataset_name, epochs=10, lr=lr)
        h0s = [h['h0_te'] for h in history]
        h0_cv = np.std(h0s) / np.mean(h0s) if np.mean(h0s) > 0 else 999
        final_acc = history[-1]['test_acc']
        lr_results.append({'lr': lr, 'h0_cv': h0_cv, 'acc': final_acc})
        print(f"  LR={lr:.0e}: H0_CV={h0_cv:.4f}, acc={final_acc:.1f}%")

    # Best by H0 stability
    best_h0 = min(lr_results, key=lambda x: x['h0_cv'])
    best_acc = max(lr_results, key=lambda x: x['acc'])
    print(f"\n  Best by H0 stability: LR={best_h0['lr']:.0e} (CV={best_h0['h0_cv']:.4f}, acc={best_h0['acc']:.1f}%)")
    print(f"  Best by accuracy:     LR={best_acc['lr']:.0e} (acc={best_acc['acc']:.1f}%)")
    print(f"  H-CX-100 (same LR): {'SUPPORTED' if best_h0['lr'] == best_acc['lr'] else 'PARTIAL'}")

    return lr_results


if __name__ == '__main__':
    # Main experiments on 3 datasets
    all_results = {}
    for ds in ['mnist', 'fashion', 'cifar']:
        all_results[ds] = run_experiment(ds, epochs=20)

    # H-CX-101: Cross-dataset difficulty
    print(f"\n  === H-CX-101: Cross-Dataset Difficulty Score ===")
    h0s = [all_results[ds]['h0_ep1'] for ds in ['mnist', 'fashion', 'cifar']]
    accs = [all_results[ds]['final_acc'] for ds in ['mnist', 'fashion', 'cifar']]
    r101, p101 = spearmanr(h0s, accs)
    print(f"  {'Dataset':>10} {'H0_ep1':>8} {'Final_acc':>10}")
    print(f"  {'-'*30}")
    for ds in ['mnist', 'fashion', 'cifar']:
        print(f"  {ds:>10} {all_results[ds]['h0_ep1']:>8.4f} {all_results[ds]['final_acc']:>10.1f}")
    print(f"  Spearman(H0_ep1, acc): r={r101:.4f}")
    print(f"  H-CX-101 (r > 0.9): {'SUPPORTED' if r101 > 0.9 else 'PARTIAL'}")

    # H-CX-100: LR sweep on CIFAR
    lr_results = run_lr_sweep('cifar')

    print(f"\n{'='*70}")
    print(f"  Round 9 FINAL SUMMARY")
    print(f"{'='*70}")
    for ds in ['mnist', 'fashion', 'cifar']:
        r = all_results[ds]
        print(f"  {ds}: H0_stop=ep{r['h0_stop_ep']}, val_stop=ep{r['val_stop_ep']}, "
              f"best_test=ep{r['best_test_ep']}, min_H0=ep{r['min_h0_ep']}")