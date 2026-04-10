```python
#!/usr/bin/env python3
"""TEXT domain RepulsionField experiment — 20 Newsgroups (4 categories)

Verify if RepulsionField structure works on text, not just images (MNIST/CIFAR).

Architecture:
  1. sklearn TF-IDF → 1000-dim fixed vector
  2. RepulsionField: EngineA-like MLP vs EngineG-like MLP
  3. Compare with Dense baseline
  4. Measure tension, accuracy, tension-accuracy correlation
  5. Verify MI efficiency ≈ ln(2) (H-CX-2)

Data: sklearn 20newsgroups (4 categories: sci.space, rec.sport.baseball,
      comp.graphics, talk.politics.guns)
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader, TensorDataset
import numpy as np
import math
import time

from sklearn.datasets import fetch_20newsgroups
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import mutual_info_score
from scipy.stats import pearsonr

# ─────────────────────────────────────────
# Constants
# ─────────────────────────────────────────
SIGMA = 12
TAU = 4
LN2 = math.log(2)  # 0.6931

CATEGORIES = [
    'sci.space',
    'rec.sport.baseball',
    'comp.graphics',
    'talk.politics.guns',
]
N_CLASSES = len(CATEGORIES)
INPUT_DIM = 1000
HIDDEN_DIM = 128
EPOCHS = 10
BATCH_SIZE = 64
LR = 0.001


# ─────────────────────────────────────────
# Data loading
# ─────────────────────────────────────────
def load_text_data():
    """20 Newsgroups 4-class → TF-IDF → PyTorch tensors."""
    print("  Loading 20 Newsgroups (4 categories)...")
    train_data = fetch_20newsgroups(subset='train', categories=CATEGORIES,
                                    remove=('headers', 'footers', 'quotes'))
    test_data = fetch_20newsgroups(subset='test', categories=CATEGORIES,
                                   remove=('headers', 'footers', 'quotes'))

    print(f"  Train: {len(train_data.data)} docs, Test: {len(test_data.data)} docs")

    tfidf = TfidfVectorizer(max_features=INPUT_DIM, stop_words='english')
    X_train = tfidf.fit_transform(train_data.data).toarray()
    X_test = tfidf.transform(test_data.data).toarray()
    y_train = train_data.target
    y_test = test_data.target

    X_train_t = torch.tensor(X_train, dtype=torch.float32)
    y_train_t = torch.tensor(y_train, dtype=torch.long)
    X_test_t = torch.tensor(X_test, dtype=torch.float32)
    y_test_t = torch.tensor(y_test, dtype=torch.long)

    train_loader = DataLoader(TensorDataset(X_train_t, y_train_t),
                              batch_size=BATCH_SIZE, shuffle=True)
    test_loader = DataLoader(TensorDataset(X_test_t, y_test_t),
                             batch_size=BATCH_SIZE, shuffle=False)

    print(f"  TF-IDF dim: {INPUT_DIM}, Classes: {N_CLASSES}")
    for i, cat in enumerate(CATEGORIES):
        n_train = (y_train == i).sum()
        n_test = (y_test == i).sum()
        print(f"    [{i}] {cat}: train={n_train}, test={n_test}")

    return train_loader, test_loader, X_test_t, y_test_t


# ─────────────────────────────────────────
# Expert (Basic MoE block)
# ─────────────────────────────────────────
class Expert(nn.Module):
    def __init__(self, input_dim, hidden_dim, output_dim, dropout=0.3):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, output_dim),
        )

    def forward(self, x):
        return self.net(x)


# ─────────────────────────────────────────
# TopK Gate
# ─────────────────────────────────────────
class TopKGate(nn.Module):
    def __init__(self, input_dim, n_experts, k=2):
        super().__init__()
        self.gate = nn.Linear(input_dim, n_experts)
        self.k = k

    def forward(self, x):
        scores = self.gate(x)
        topk_vals, topk_idx = scores.topk(self.k, dim=-1)
        mask = torch.zeros_like(scores)
        mask.scatter_(-1, topk_idx, 1.0)
        weights = F.softmax(scores, dim=-1) * mask
        return weights / (weights.sum(dim=-1, keepdim=True) + 1e-8)


# ─────────────────────────────────────────
# Text EngineA (sigma-tau MoE: 12 experts, top-4)
# ─────────────────────────────────────────
class TextEngineA(nn.Module):
    """EngineA-like: sigma(6)=12 experts, tau(6)=4 active."""
    def __init__(self, input_dim, hidden_dim, output_dim):
        super().__init__()
        n_experts = SIGMA  # 12
        k = TAU  # 4
        self.experts = nn.ModuleList([
            Expert(input_dim, hidden_dim, output_dim) for _ in range(n_experts)
        ])
        self.gate = TopKGate(input_dim, n_experts, k)

    def forward(self, x):
        weights = self.gate(x)
        outputs = torch.stack([e(x) for e in self.experts], dim=1)
        return (weights.unsqueeze(-1) * outputs).sum(dim=1)


# ─────────────────────────────────────────
# Text EngineG (Shannon entropy MoE)
# ─────────────────────────────────────────
DIVISOR_RECIPROCALS = [1/2, 1/3, 1/6]
H_TARGET = sum(-p * math.log(p) for p in DIVISOR_RECIPROCALS)

class TextEngineG(nn.Module):
    """EngineG-like: Shannon entropy regularized MoE."""
    def __init__(self, input_dim, hidden_dim, output_dim):
        super().__init__()
        self.experts = nn.ModuleList([
            Expert(input_dim, hidden_dim, output_dim) for _ in range(6)
        ])
        self.gate = nn.Linear(input_dim, 6)
        self.h_target = H_TARGET
        self.entropy_loss = torch.tensor(0.0)

    def forward(self, x):
        weights = F.softmax(self.gate(x), dim=-1)
        outputs = torch.stack([e(x) for e in self.experts], dim=1)
        result = (weights.unsqueeze(-1) * outputs).sum(dim=1)
        h = -(weights * (weights + 1e-8).log()).sum(dim=-1).mean()
        self.entropy_loss = (h - self.h_target) ** 2
        return result


# ─────────────────────────────────────────
# Dense Baseline
# ─────────────────────────────────────────
class DenseBaseline(nn.Module):
    def __init__(self, input_dim, hidden_dim, output_dim, dropout=0.3):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, output_dim),
        )

    def forward(self, x):
        return self.net(x)


# ─────────────────────────────────────────
# Text RepulsionField (A vs G)
# ─────────────────────────────────────────
class TextRepulsionField(nn.Module):
    """Repulsion Field: EngineA(generative) vs EngineG(calibration) on TF-IDF text.

    Structure is identical to RepulsionFieldEngine in model_meta_engine.py.
    """
    def __init__(self, input_dim=INPUT_DIM, hidden_dim=HIDDEN_DIM, output_dim=N_CLASSES):
        super().__init__()
        self.pole_plus = TextEngineA(input_dim, hidden_dim, output_dim)
        self.pole_minus = TextEngineG(input_dim, hidden_dim, output_dim)

        self.field_transform = nn.Sequential(
            nn.Linear(output_dim, output_dim),
            nn.Tanh(),
        )

        self.tension_scale = nn.Parameter(torch.tensor(1/3))  # Meta fixed point
        self.aux_loss = torch.tensor(0.0)
        self.tension_magnitude = 0.0

    def forward(self, x):
        out_plus = self.pole_plus(x)
        out_minus = self.pole_minus(x)

        repulsion = out_plus - out_minus
        tension = (repulsion ** 2).sum(dim=-1, keepdim=True)

        equilibrium = (out_plus + out_minus) / 2
        field_direction = self.field_transform(repulsion)

        output = equilibrium + self.tension_scale * torch.sqrt(tension + 1e-8) * field_direction

        self.aux_loss = getattr(self.pole_minus, 'entropy_loss', torch.tensor(0.0))

        with torch.no_grad():
            self.tension_magnitude = tension.mean().item()

        return (output, self.aux_loss)


# ─────────────────────────────────────────
# Training loop
# ─────────────────────────────────────────
def train_model(model, train_loader, test_loader, epochs=EPOCHS, lr=LR,
                is_repulsion=False, aux_lambda=0.1):
    """Train and return per-epoch metrics."""
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    criterion = nn.CrossEntropyLoss()

    history = {
        'train_loss': [],
        'test_acc': [],
        'tension': [],  # repulsion only
        'tension_scale': [],  # repulsion only
    }

    for epoch in range(epochs):
        model.train()
        total_loss = 0
        n_batches = 0
        epoch_tension = []

        for X, y in train_loader:
            optimizer.zero_grad()
            out = model(X)

            if is_repulsion:
                logits, aux = out
                loss = criterion(logits, y) + aux_lambda * aux
                with torch.no_grad():
                    epoch_tension.append(model.tension_magnitude)
            else:
                logits = out
                loss = criterion(logits, y)

            loss.backward()
            optimizer.step()
            total_loss += loss.item()
            n_batches += 1

        avg_loss = total_loss / n_batches

        # Test accuracy
        model.eval()
        correct = total = 0
        with torch.no_grad():
            for X, y in test_loader:
                out = model(X)
                if is_repulsion:
                    out = out[0]
                preds = out.argmax(dim=1)
                correct += (preds == y).sum().item()
                total += y.size(0)
        acc = correct / total

        history['train_loss'].append(avg_loss)
        history['test_acc'].append(acc)
        if is_repulsion:
            history['tension'].append(np.mean(epoch_tension))
            history['tension_scale'].append(model.tension_scale.item())

        if (epoch + 1) % 2 == 0 or epoch == 0:
            extra = ""
            if is_repulsion:
                extra = f"  T={np.mean(epoch_tension):.4f}  ts={model.tension_scale.item():.4f}"
            print(f"    Epoch {epoch+1:>2}/{epochs}: Loss={avg_loss:.4f}, Acc={acc*100:.1f}%{extra}")

    return history


# ─────────────────────────────────────────
# MI efficiency measurement
# ─────────────────────────────────────────
def compute_mi_efficiency(model, X_test, y_test):
    """MI efficiency = (MI_field - MI_best_pole) / (MI_max - MI_best_pole).

    MI = mutual_info_score(true_labels, predicted_labels).
    """
    model.eval()
    with torch.no_grad():
        # Full model predictions
        out = model(X_test)
        if isinstance(out, tuple):
            out = out[0]
        pred_field = out.argmax(dim=1).numpy()

        # Pole+ predictions
        out_plus = model.pole_plus(X_test)
        pred_plus = out_plus.argmax(dim=1).numpy()

        # Pole- predictions
        out_minus = model.pole_minus(X_test)
        pred_minus = out_minus.argmax(dim=1).numpy()

    y_np = y_test.numpy()

    mi_field = mutual_info_score(y_np, pred_field)
    mi_plus = mutual_info_score(y_np, pred_plus)
    mi_minus = mutual_info_score(y_np, pred_minus)
    mi_best_pole = max(mi_plus, mi_minus)

    # MI_max = H(Y) (entropy of true labels)
    from collections import Counter
    counts = Counter(y_np)
    total = len(y_np)
    mi_max = -sum((c / total) * math.log(c / total) for c in counts.values())

    if mi_max - mi_best_pole < 1e-8:
        efficiency = 0.0
    else:
        efficiency = (mi_field - mi_best_pole) / (mi_max - mi_best_pole)

    return {
        'mi_field': mi_field,
        'mi_plus': mi_plus,
        'mi_minus': mi_minus,
        'mi_best_pole': mi_best_pole,
        'mi_max': mi_max,
        'efficiency': efficiency,
    }


# ─────────────────────────────────────────
# Per-sample tension vs correctness
# ─────────────────────────────────────────
def tension_accuracy_correlation(model, X_test, y_test):
    """Measure correlation between per-sample tension and correctness."""
    model.eval()
    with torch.no_grad():
        out_plus = model.pole_plus(X_test)
        out_minus = model.pole_minus(X_test)
        repulsion = out_plus - out_minus
        tension = (repulsion ** 2).sum(dim=-1)  # (N,)

        out = model(X_test)
        if isinstance(out, tuple):
            out = out[0]
        preds = out.argmax(dim=1)
        correct = (preds == y_test).float()

    tension_np = tension.numpy()
    correct_np = correct.numpy()

    # Bin tension into quartiles
    quartiles = np.percentile(tension_np, [25, 50, 75])
    bins = np.digitize(tension_np, quartiles)

    acc_by_quartile = []
    for q in range(4):
        mask = bins == q
        if mask.sum() > 0:
            acc_by_quartile.append(correct_np[mask].mean())
        else:
            acc_by_quartile.append(0.0)

    # Pearson correlation
    if tension_np.std() > 1e-8 and correct_np.std() > 1e-8:
        r, p = pearsonr(tension_np, correct_np)
    else:
        r, p = 0.0, 1.0

    return {
        'pearson_r': r,
        'pearson_p': p,
        'acc_by_quartile': acc_by_quartile,
        'mean_tension_correct': tension_np[correct_np == 1].mean() if correct_np.sum() > 0 else 0,
        'mean_tension_wrong': tension_np[correct_np == 0].mean() if (1 - correct_np).sum() > 0 else 0,
    }


# ─────────────────────────────────────────
# ASCII visualization
# ─────────────────────────────────────────
def ascii_bar(label, value, max_val, width=40):
    filled = int(value / max_val * width) if max_val > 0 else 0
    bar = '#' * filled + '.' * (width - filled)
    return f"  {label:<20} |{bar}| {value:.4f}"


def ascii_plot(title, values, labels, width=50):
    """Simple ASCII line plot."""
    print(f"\n  {title}")
    print(f"  {'─' * (width + 20)}")
    if not values:
        print("  (no data)")
        return
    vmin = min(min(v) for v in values if v)
    vmax = max(max(v) for v in values if v)
    if vmax - vmin < 1e-8:
        vmax = vmin + 1
    for vals, label in zip(values, labels):
        line = ""
        for v in vals:
            pos = int((v - vmin) / (vmax - vmin) * (width - 1))
            line += " " * max(0, pos - len(line)) + "*"
        print(f"  {label:<12} {line}")
    print(f"  {'':>12} {'|' + '─' * (width - 2) + '|'}")
    print(f"  {'':>12} {vmin:.3f}{' ' * (width - 12)}{vmax:.3f}")


# ─────────────────────────────────────────
# Parameter count
# ─────────────────────────────────────────
def count_params(model):
    return sum(p.numel() for p in model.parameters())


# ═════════════════════════════════════════
# MAIN
# ═════════════════════════════════════════
def main():
    print("=" * 70)
    print("  TEXT REPULSION FIELD EXPERIMENT")
    print("  20 Newsgroups (4-class) + TF-IDF + RepulsionField")
    print("=" * 70)

    t0 = time.time()

    # ── 1. Load Data ──
    print("\n[1/4] Loading data...")
    train_loader, test_loader, X_test, y_test = load_text_data()

    # ── 2. Dense Baseline ──
    print("\n[2/4] Training Dense Baseline (2-layer MLP)...")
    dense = DenseBaseline(INPUT_DIM, HIDDEN_DIM, N_CLASSES)
    n_dense = count_params(dense)
    print(f"  Parameters: {n_dense:,}")
    hist_dense = train_model(dense, train_loader, test_loader, is_repulsion=False)

    # ── 3. RepulsionField ──
    print("\n[3/4] Training TextRepulsionField (EngineA vs EngineG)...")
    repulsion = TextRepulsionField(INPUT_DIM, HIDDEN_DIM, N_CLASSES)
    n_repulsion = count_params(repulsion)
    print(f"  Parameters: {n_repulsion:,}")
    hist_repulsion = train_model(repulsion, train_loader, test_loader,
                                  is_repulsion=True, aux_lambda=0.1)

    # ── 4. Analysis ──
    print("\n[4/4] Analysis...")

    acc_dense = hist_dense['test_acc'][-1]
    acc_repulsion = hist_repulsion['test_acc'][-1]
    best_dense = max(hist_dense['test_acc'])
    best_repulsion = max(hist_repulsion['test_acc'])

    print("\n" + "=" * 70)
    print("  RESULTS SUMMARY")
    print("=" * 70)
    print(f"\n  {'Model':<30} {'Best Acc':>10} {'Final Acc':>10} {'Params':>10}")
    print(f"  {'-'*60}")
    print(f"  {'Dense Baseline':<30} {best_dense*100:>9.2f}% {acc_dense*100:>9.2f}% {n_dense:>10,}")
    print(f"  {'TextRepulsionField':<30} {best_repulsion*100:>9.2f}% {acc_repulsion*100:>9.2f}% {n_repulsion:>10,}")
    diff = best_repulsion - best_dense
    winner = "RepulsionField" if diff > 0 else "Dense"
    print(f"\n  Delta: {diff*100:+.2f}% ({winner} wins)")

    # ── Tension dynamics ──
    print("\n  TENSION DYNAMICS")
    print(f"  {'-'*50}")
    for i, (t, ts) in enumerate(zip(hist_repulsion['tension'],
                                     hist_repulsion['tension_scale'])):
        if i == 0 or (i + 1) % 2 == 0:
            print(f"    Epoch {i+1:>2}: tension={t:.4f}, tension_scale={ts:.6f}")

    final_ts = hist_repulsion['tension_scale'][-1]
    print(f"\n  Final tension_scale: {final_ts:.6f}")
    print(f"  Target (1/3):        {1/3:.6f}")
    print(f"  Diff from 1/3:       {final_ts - 1/3:+.6f}")

    # ── Tension-accuracy correlation ──
    print("\n  TENSION-ACCURACY CORRELATION")
    print(f"  {'-'*50}")
    corr = tension_accuracy_correlation(repulsion, X_test, y_test)
    print(f"  Pearson r:           {corr['pearson_r']:.4f}")
    print(f"  Pearson p-value:     {corr['pearson_p']:.6f}")
    print(f"  Mean tension (correct):  {corr['mean_tension_correct']:.4f}")
    print(f"  Mean tension (wrong):    {corr['mean_tension_wrong']:.4f}")
    print(f"\n  Accuracy by tension quartile:")
    for i, acc_q in enumerate(corr['acc_by_quartile']):
        q_label = ['Q1 (low)', 'Q2', 'Q3', 'Q4 (high)'][i]
        print(ascii_bar(q_label, acc_q, 1.0))

    # ── MI efficiency (H-CX-2) ──
    print("\n  MI EFFICIENCY (H-CX-2 TEST)")
    print(f"  {'-'*50}")
    mi = compute_mi_efficiency(repulsion, X_test, y_test)
    print(f"  MI(field, labels):      {mi['mi_field']:.4f}")
    print(f"  MI(pole+, labels):      {mi['mi_plus']:.4f}")
    print(f"  MI(pole-, labels):      {mi['mi_minus']:.4f}")
    print(f"  MI(best_pole, labels):  {mi['mi_best_pole']:.4f}")
    print(f"  MI(max) = H(Y):        {mi['mi_max']:.4f}")
    print(f"  MI efficiency:          {mi['efficiency']:.4f}")
    print(f"  ln(2):                  {LN2:.4f}")
    mi_diff_pct = abs(mi['efficiency'] - LN2) / LN2 * 100
    print(f"  |efficiency - ln(2)|:   {abs(mi['efficiency'] - LN2):.4f} ({mi_diff_pct:.1f}%)")
    if mi_diff_pct < 10:
        print(f"  --> MI efficiency ~ ln(2) HOLDS for text! (within 10%)")
    elif mi_diff_pct < 20:
        print(f"  --> MI efficiency ~ ln(2) WEAK support (within 20%)")
    else:
        print(f"  --> MI efficiency ~ ln(2) does NOT hold for text ({mi_diff_pct:.1f}% off)")

    # ── ASCII accuracy plot ──
    ascii_plot("Accuracy over epochs",
               [hist_dense['test_acc'], hist_repulsion['test_acc']],
               ["Dense", "Repulsion"])

    # ── ASCII tension plot ──
    if hist_repulsion['tension']:
        print(f"\n  Tension over epochs:")
        t_max = max(hist_repulsion['tension']) if hist_repulsion['tension'] else 1
        for i, t in enumerate(hist_repulsion['tension']):
            bar_len = int(t / t_max * 40) if t_max > 0 else 0
            print(f"    E{i+1:>2} |{'#' * bar_len}{'.' * (40 - bar_len)}| {t:.4f}")

    # ── Final verdict ──
    elapsed = time.time() - t0
    print("\n" + "=" * 70)
    print("  VERDICT")
    print("=" * 70)
    print(f"  Domain:       TEXT (20 Newsgroups, TF-IDF)")
    print(f"  Architecture: RepulsionField (EngineA vs EngineG)")
    print(f"  Dense acc:    {best_dense*100:.2f}%")
    print(f"  Repulsion acc:{best_repulsion*100:.2f}%")
    print(f"  Delta:        {diff*100:+.2f}%")
    print(f"  Tension-Acc r:{corr['pearson_r']:.4f} (p={corr['pearson_p']:.4f})")
    print(f"  MI efficiency:{mi['efficiency']:.4f} (ln(2)={LN2:.4f}, diff={mi_diff_pct:.1f}%)")
    print(f"  tension_scale:{final_ts:.6f} (1/3={1/3:.6f})")
    print(f"  Time:         {elapsed:.1f}s")

    # Cross-domain comparison
    print(f"\n  CROSS-DOMAIN COMPARISON (TEXT vs IMAGE)")
    print(f"  {'-'*50}")
    print(f"  {'Metric':<25} {'TEXT':>10} {'IMAGE*':>10}")
    print(f"  {'-'*50}")
    print(f"  {'MI efficiency':<25} {mi['efficiency']:>10.4f} {'0.705':>10}")
    print(f"  {'tension_scale final':<25} {final_ts:>10.4f} {'~0.34':>10}")
    print(f"  {'Repulsion > Dense?':<25} {'YES' if diff > 0 else 'NO':>10} {'YES':>10}")
    print(f"  {'-'*50}")
    print(f"  * IMAGE = MNIST RepulsionFieldEngine from prior experiments")

    print("\n" + "=" * 70)
    print("  experiment_text_repulsion.py complete")
    print("=" * 70)


if __name__ == '__main__':
    main()
```