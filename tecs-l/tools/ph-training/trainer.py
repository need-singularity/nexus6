"""PHTrainer — Automatic training pipeline with PH monitoring.

Phase 1: Difficulty prediction (1-epoch H0)
Phase 2: Automatic LR search (H0 CV minimum)
Phase 3: Training with real-time overfitting detection (H0 gap)
Phase 4: Result analysis (dendrogram, confusion, vulnerability)
"""

import os, time
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from dataclasses import dataclass, field

from .engine import PureFieldEngine
from .ph import compute_h0, get_merges, compute_class_distances, PHMonitor
from .data import load_data

os.environ.setdefault('KMP_DUPLICATE_LIB_OK', 'TRUE')


@dataclass
class TrainingResult:
    """Training result container."""
    dataset: str
    difficulty: str
    h0_ep1: float
    best_lr: float
    best_acc: float
    best_epoch: int
    early_stopped: bool
    tension_scale: float
    confusion_pairs: list = field(default_factory=list)
    dendrogram: list = field(default_factory=list)
    epoch_log: list = field(default_factory=list)
    elapsed_minutes: float = 0.0


def _extract_dirs(model, dim, loader):
    """Extract direction vectors, labels, predictions, and tensions from a model."""
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
    return np.concatenate(dirs), np.array(ys), np.array(preds), np.array(tensions)


class PHTrainer:
    """Automatic training pipeline with PH-based monitoring.

    Runs a 4-phase pipeline:
    1. Difficulty prediction from 1-epoch H0
    2. Optimal LR search via H0 CV minimization
    3. Training with real-time overfitting detection
    4. Post-training analysis (dendrogram, confusion, FGSM vulnerability)

    Args:
        dataset: One of 'mnist', 'fashion', 'cifar'
        epochs: Maximum number of training epochs
        hidden_dim: Hidden layer dimension
        lr: Learning rate ('auto' for H0 CV search)
        batch_size: Training batch size
        gap_threshold: H0 gap threshold for overfitting alerts
        seed: Random seed
        verbose: Whether to print progress
    """

    def __init__(self, dataset='mnist', epochs=20, hidden_dim=128,
                 lr='auto', batch_size=256, gap_threshold=0.08,
                 seed=42, verbose=True):
        self.dataset = dataset
        self.epochs = epochs
        self.hidden_dim = hidden_dim
        self.lr = lr
        self.batch_size = batch_size
        self.gap_threshold = gap_threshold
        self.seed = seed
        self.verbose = verbose

    def _log(self, msg):
        if self.verbose:
            print(msg)

    def run(self) -> TrainingResult:
        """Run the full training pipeline.

        Returns:
            TrainingResult with all metrics, confusion pairs, and dendrogram.
        """
        t0 = time.time()
        torch.manual_seed(self.seed)

        dim, tl, te, names = load_data(self.dataset, self.batch_size)
        n_cls = len(names)
        ce = nn.CrossEntropyLoss()

        self._log(f"\n{'=' * 70}")
        self._log(f"  PH Auto-Training — {self.dataset.upper()}")
        self._log(f"  epochs={self.epochs}, hidden={self.hidden_dim}, seed={self.seed}")
        self._log(f"{'=' * 70}")

        # == Phase 1: Difficulty prediction ==
        self._log(f"\n  Phase 1: Difficulty prediction (1-epoch H0)")
        torch.manual_seed(self.seed)
        probe = PureFieldEngine(dim, self.hidden_dim, n_cls)
        opt = torch.optim.Adam(probe.parameters(), lr=1e-3)

        probe.train()
        for x, y in tl:
            opt.zero_grad()
            out, t = probe(x.view(-1, dim))
            ce(out, y).backward()
            opt.step()

        D_p, Y_p, P_p, _ = _extract_dirs(probe, dim, te)
        h0_ep1 = compute_h0(D_p, Y_p, n_cls)
        acc_ep1 = (P_p == Y_p).mean() * 100

        if h0_ep1 > 3.5:
            difficulty = "easy"
        elif h0_ep1 > 2.0:
            difficulty = "medium"
        else:
            difficulty = "hard"

        self._log(f"    H0_ep1 = {h0_ep1:.4f}, acc_ep1 = {acc_ep1:.1f}%")
        self._log(f"    Difficulty: {difficulty}")

        # Confusion pairs (confirmed at epoch 1)
        cos_dist_p, _ = compute_class_distances(D_p, Y_p, n_cls)
        merges_ep1 = get_merges(cos_dist_p, n_cls)

        self._log(f"\n    Confusion pairs (confirmed at epoch 1):")
        for dist, i, j in sorted(merges_ep1)[:5]:
            self._log(f"      {names[i]:>7} <-> {names[j]:<7}  dist={dist:.4f}")

        del probe, opt

        # == Phase 2: LR search ==
        if self.lr == 'auto':
            self._log(f"\n  Phase 2: LR auto-search (H0 CV minimum)")
            lr_candidates = [3e-4, 1e-3, 3e-3]
            best_lr, best_cv = None, 999

            for lr_c in lr_candidates:
                torch.manual_seed(self.seed)
                m = PureFieldEngine(dim, self.hidden_dim, n_cls)
                o = torch.optim.Adam(m.parameters(), lr=lr_c)
                h0s = []

                for ep in range(5):
                    m.train()
                    for x, y in tl:
                        o.zero_grad()
                        out, t = m(x.view(-1, dim))
                        ce(out, y).backward()
                        o.step()
                    D_lr, Y_lr, _, _ = _extract_dirs(m, dim, te)
                    h0s.append(compute_h0(D_lr, Y_lr, n_cls))

                cv = np.std(h0s) / (np.mean(h0s) + 1e-8)
                self._log(f"    LR={lr_c:.0e}: H0 CV={cv:.4f}")

                if cv < best_cv:
                    best_cv = cv
                    best_lr = lr_c
                del m, o

            self._log(f"    -> Best LR: {best_lr:.0e} (CV={best_cv:.4f})")
            lr = best_lr
        else:
            lr = float(self.lr)
            self._log(f"\n  Phase 2: LR = {lr} (manual)")

        # == Phase 3: Training ==
        self._log(f"\n  Phase 3: Training (LR={lr:.0e}, overfitting detection ON)")
        torch.manual_seed(self.seed)
        model = PureFieldEngine(dim, self.hidden_dim, n_cls)
        optimizer = torch.optim.Adam(model.parameters(), lr=lr)
        scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=self.epochs)
        monitor = PHMonitor(n_cls, self.gap_threshold)

        best_acc = 0
        best_epoch = 0
        early_stopped = False
        epoch_log = []
        save_path = f'/tmp/ph_best_{self.dataset}.pt'

        self._log(f"\n  {'Ep':>3} {'trn%':>6} {'tst%':>6} {'gap':>6} "
                  f"{'H0_tr':>7} {'H0_te':>7} {'H0gap':>7} {'ts':>6} {'status':>8}")
        self._log(f"  {'-' * 65}")

        for epoch in range(1, self.epochs + 1):
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

            D_tr, Y_tr, _, _ = _extract_dirs(model, dim, tl)
            D_te, Y_te, P_te, T_te = _extract_dirs(model, dim, te)
            test_acc = (P_te == Y_te).mean() * 100
            acc_gap = train_acc - test_acc

            ph_status = monitor.check(D_tr, Y_tr, D_te, Y_te)
            ts = model.tension_scale.item()

            if test_acc > best_acc:
                best_acc = test_acc
                best_epoch = epoch
                torch.save(model.state_dict(), save_path)

            log_entry = {
                'epoch': epoch,
                'train_acc': train_acc,
                'test_acc': test_acc,
                'acc_gap': acc_gap,
                'h0_train': ph_status.h0_train,
                'h0_test': ph_status.h0_test,
                'h0_gap': ph_status.h0_gap,
                'tension_scale': ts,
                'status': ph_status.status,
            }
            epoch_log.append(log_entry)

            self._log(f"  {epoch:>3} {train_acc:>6.1f} {test_acc:>6.1f} {acc_gap:>+6.1f} "
                      f"{ph_status.h0_train:>7.4f} {ph_status.h0_test:>7.4f} "
                      f"{ph_status.h0_gap:>7.4f} {ts:>6.3f} {ph_status.status:>8}")

            if monitor.should_stop and epoch > 5:
                self._log(f"\n  Early stop (3 consecutive ALERTs, epoch {epoch})")
                early_stopped = True
                break

        # == Phase 4: Analysis ==
        self._log(f"\n  Phase 4: Analysis")

        model.load_state_dict(torch.load(save_path, weights_only=True))
        D_f, Y_f, P_f, T_f = _extract_dirs(model, dim, te)
        final_acc = (P_f == Y_f).mean() * 100

        cos_dist_f, _ = compute_class_distances(D_f, Y_f, n_cls)
        merges_f = get_merges(cos_dist_f, n_cls)

        # Dendrogram
        self._log(f"\n    Dendrogram (semantic hierarchy):")
        dend_parent = list(range(n_cls))
        dend_clusters = {i: {i} for i in range(n_cls)}

        def find(x):
            while dend_parent[x] != x:
                dend_parent[x] = dend_parent[dend_parent[x]]
                x = dend_parent[x]
            return x

        all_edges = sorted([
            (cos_dist_f[i, j], min(i, j), max(i, j))
            for i in range(n_cls) for j in range(i + 1, n_cls)
        ])
        dendrogram = []
        for dist, i, j in all_edges:
            ri, rj = find(i), find(j)
            if ri != rj:
                merged = dend_clusters[ri] | dend_clusters[rj]
                dend_parent[ri] = rj
                dend_clusters[rj] = merged
                if ri in dend_clusters and ri != rj:
                    del dend_clusters[ri]
                dendrogram.append({
                    'distance': dist,
                    'classes': sorted([names[c] for c in merged]),
                })
                if 2 <= len(merged) <= 6:
                    cnames = sorted([names[c] for c in merged])
                    self._log(f"      d={dist:.4f} -> [{', '.join(cnames)}]")

        # FGSM vulnerable pairs
        self._log(f"\n    FGSM vulnerable pairs (shortest merge distance):")
        for dist, i, j in sorted(merges_f)[:3]:
            self._log(f"      {names[i]:>7} <-> {names[j]:<7}  vulnerability={1 / (dist + 0.01):.1f}")

        # Summary
        elapsed = (time.time() - t0) / 60
        self._log(f"\n{'=' * 70}")
        self._log(f"  SUMMARY — {self.dataset.upper()}")
        self._log(f"{'=' * 70}")
        self._log(f"  Difficulty:     {difficulty} (H0_ep1={h0_ep1:.4f})")
        self._log(f"  Best LR:        {lr:.0e}")
        self._log(f"  Best accuracy:  {final_acc:.1f}% (epoch {best_epoch})")
        self._log(f"  Early stop:     {'yes' if early_stopped else 'no'}")
        self._log(f"  Tension scale:  {model.tension_scale.item():.4f}")
        self._log(f"  Top confusion:  {names[merges_f[0][1]]}-{names[merges_f[0][2]]}")
        self._log(f"  Elapsed:        {elapsed:.1f} min")
        self._log(f"{'=' * 70}")

        return TrainingResult(
            dataset=self.dataset,
            difficulty=difficulty,
            h0_ep1=h0_ep1,
            best_lr=lr,
            best_acc=final_acc,
            best_epoch=best_epoch,
            early_stopped=early_stopped,
            tension_scale=model.tension_scale.item(),
            confusion_pairs=[(dist, names[i], names[j]) for dist, i, j in sorted(merges_f)[:5]],
            dendrogram=dendrogram,
            epoch_log=epoch_log,
            elapsed_minutes=elapsed,
        )
