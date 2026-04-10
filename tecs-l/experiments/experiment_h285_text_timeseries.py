#!/usr/bin/env python3
"""H-285 Verification: RepulsionField beyond image classification

Part 1: Text Classification
  - 20 Newsgroups (4 classes)
  - TF-IDF (sparse, 1000-dim) vs Learned Embedding (dense, 64-dim)
  - RepulsionField vs Dense baseline for each

Part 2: Time Series Classification (expanded)
  - Synthetic: sine/square/sawtooth/triangle (4 classes)
  - Real-ish: varying frequency + amplitude + phase (harder)
  - RepulsionField vs Dense baseline

Part 3: Cross-domain summary table
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader, TensorDataset
import numpy as np
import math
import time

from sklearn.datasets import fetch_20newsgroups
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

# ═════════════════════════════════════════
# Common RepulsionField building block
# ═════════════════════════════════════════

class PoleNet(nn.Module):
    def __init__(self, input_dim, hidden_dim, output_dim, dropout=0.2):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, output_dim),
        )
    def forward(self, x):
        return self.net(x)


class RepulsionField(nn.Module):
    """Generic two-pole repulsion field."""
    def __init__(self, input_dim, hidden_dim, output_dim, dropout=0.2):
        super().__init__()
        self.pole_plus = PoleNet(input_dim, hidden_dim, output_dim, dropout)
        self.pole_minus = PoleNet(input_dim, hidden_dim, output_dim, dropout)
        self.field_transform = nn.Sequential(
            nn.Linear(output_dim, output_dim),
            nn.Tanh(),
        )
        self.tension_scale = nn.Parameter(torch.tensor(1/3))
        self.tension_magnitude = 0.0
        self.per_sample_tension = None

    def forward(self, x):
        a = self.pole_plus(x)
        b = self.pole_minus(x)
        repulsion = a - b
        tension = (repulsion ** 2).sum(dim=-1, keepdim=True)
        equilibrium = (a + b) / 2
        field_dir = self.field_transform(repulsion)
        output = equilibrium + self.tension_scale * torch.sqrt(tension + 1e-8) * field_dir
        with torch.no_grad():
            self.tension_magnitude = tension.mean().item()
            self.per_sample_tension = tension.squeeze(-1)
        return output


class DenseBaseline(nn.Module):
    def __init__(self, input_dim, hidden_dim, output_dim, dropout=0.2):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, output_dim),
        )
    def forward(self, x):
        return self.net(x)


class EmbeddingRepulsionField(nn.Module):
    """RepulsionField with learned embedding layer for text."""
    def __init__(self, vocab_size, embed_dim, hidden_dim, output_dim, max_len, dropout=0.2):
        super().__init__()
        self.embed = nn.Embedding(vocab_size, embed_dim, padding_idx=0)
        self.max_len = max_len
        self.repulsion = RepulsionField(embed_dim, hidden_dim, output_dim, dropout)
        self.tension_magnitude = 0.0
        self.tension_scale = self.repulsion.tension_scale

    def forward(self, x):
        e = self.embed(x.long())
        e = e.mean(dim=1)  # average pooling
        out = self.repulsion(e)
        self.tension_magnitude = self.repulsion.tension_magnitude
        return out


class EmbeddingDenseBaseline(nn.Module):
    """Dense baseline with learned embedding layer for text."""
    def __init__(self, vocab_size, embed_dim, hidden_dim, output_dim, max_len, dropout=0.2):
        super().__init__()
        self.embed = nn.Embedding(vocab_size, embed_dim, padding_idx=0)
        self.max_len = max_len
        self.dense = DenseBaseline(embed_dim, hidden_dim, output_dim, dropout)

    def forward(self, x):
        e = self.embed(x.long())
        e = e.mean(dim=1)
        return self.dense(e)


# ═════════════════════════════════════════
# Training utility
# ═════════════════════════════════════════

def train_eval(model, train_loader, test_loader, epochs=15, lr=0.001):
    """Train and return best accuracy, final accuracy, tensions."""
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    best_acc = 0.0
    tensions = []

    for epoch in range(epochs):
        model.train()
        for X, y in train_loader:
            optimizer.zero_grad()
            out = model(X)
            loss = F.cross_entropy(out, y)
            loss.backward()
            optimizer.step()

        model.eval()
        correct = total = 0
        with torch.no_grad():
            for X, y in test_loader:
                out = model(X)
                preds = out.argmax(1)
                correct += (preds == y).sum().item()
                total += y.size(0)
        acc = correct / total
        best_acc = max(best_acc, acc)
        t = getattr(model, 'tension_magnitude', 0.0)
        if hasattr(model, 'repulsion'):
            t = model.repulsion.tension_magnitude
        tensions.append(t)

    ts = None
    if hasattr(model, 'tension_scale'):
        ts = model.tension_scale.item()
    elif hasattr(model, 'repulsion'):
        ts = model.repulsion.tension_scale.item()

    return best_acc, acc, tensions, ts


def count_params(model):
    return sum(p.numel() for p in model.parameters())


# ═════════════════════════════════════════
# PART 1: TEXT CLASSIFICATION
# ═════════════════════════════════════════

def run_text_experiments():
    print("\n" + "=" * 70)
    print("  PART 1: TEXT CLASSIFICATION (20 Newsgroups, 4 classes)")
    print("=" * 70)

    cats = ['sci.space', 'rec.sport.baseball', 'comp.graphics', 'talk.politics.guns']
    N_CLASSES = len(cats)
    EPOCHS = 15
    N_SEEDS = 3

    print("  Loading 20 Newsgroups...")
    train_data = fetch_20newsgroups(subset='train', categories=cats,
                                     remove=('headers', 'footers', 'quotes'))
    test_data = fetch_20newsgroups(subset='test', categories=cats,
                                    remove=('headers', 'footers', 'quotes'))
    print(f"  Train: {len(train_data.data)}, Test: {len(test_data.data)}")

    # --- TF-IDF (sparse representation) ---
    print("\n  --- A. TF-IDF (Sparse, 1000-dim) ---")
    tfidf = TfidfVectorizer(max_features=1000, stop_words='english')
    X_train_tfidf = torch.tensor(tfidf.fit_transform(train_data.data).toarray(), dtype=torch.float32)
    X_test_tfidf = torch.tensor(tfidf.transform(test_data.data).toarray(), dtype=torch.float32)
    y_train = torch.tensor(train_data.target, dtype=torch.long)
    y_test = torch.tensor(test_data.target, dtype=torch.long)

    train_tfidf = DataLoader(TensorDataset(X_train_tfidf, y_train), batch_size=64, shuffle=True)
    test_tfidf = DataLoader(TensorDataset(X_test_tfidf, y_test), batch_size=64)

    tfidf_results = {'dense': [], 'repulsion': []}
    for seed in range(N_SEEDS):
        torch.manual_seed(42 + seed * 7)
        dense = DenseBaseline(1000, 128, N_CLASSES)
        best, final, _, _ = train_eval(dense, train_tfidf, test_tfidf, EPOCHS)
        tfidf_results['dense'].append(best)

        torch.manual_seed(42 + seed * 7)
        repul = RepulsionField(1000, 128, N_CLASSES)
        best, final, tensions, ts = train_eval(repul, train_tfidf, test_tfidf, EPOCHS)
        tfidf_results['repulsion'].append(best)
        print(f"    Seed {seed}: Dense={tfidf_results['dense'][-1]*100:.1f}%  "
              f"Repulsion={best*100:.1f}%  tension_scale={ts:.4f}")

    tfidf_dense_mean = np.mean(tfidf_results['dense']) * 100
    tfidf_repul_mean = np.mean(tfidf_results['repulsion']) * 100
    tfidf_delta = tfidf_repul_mean - tfidf_dense_mean

    # --- Dense Embedding ---
    print("\n  --- B. Learned Embedding (Dense, 64-dim) ---")
    VOCAB_SIZE = 2001  # +1 for padding
    EMBED_DIM = 64
    MAX_LEN = 100

    vec = CountVectorizer(max_features=VOCAB_SIZE - 1, binary=True)
    vec.fit(train_data.data)

    def texts_to_indices(texts, max_len=MAX_LEN):
        X = torch.zeros(len(texts), max_len, dtype=torch.long)
        for i, text in enumerate(texts):
            tokens = text.lower().split()
            for j, tok in enumerate(tokens[:max_len]):
                if tok in vec.vocabulary_:
                    X[i, j] = vec.vocabulary_[tok] + 1  # 0 = padding
        return X

    X_train_emb = texts_to_indices(train_data.data)
    X_test_emb = texts_to_indices(test_data.data)

    train_emb = DataLoader(TensorDataset(X_train_emb, y_train), batch_size=64, shuffle=True)
    test_emb = DataLoader(TensorDataset(X_test_emb, y_test), batch_size=64)

    emb_results = {'dense': [], 'repulsion': []}
    for seed in range(N_SEEDS):
        torch.manual_seed(42 + seed * 7)
        dense = EmbeddingDenseBaseline(VOCAB_SIZE, EMBED_DIM, 128, N_CLASSES, MAX_LEN)
        best, final, _, _ = train_eval(dense, train_emb, test_emb, EPOCHS)
        emb_results['dense'].append(best)

        torch.manual_seed(42 + seed * 7)
        repul = EmbeddingRepulsionField(VOCAB_SIZE, EMBED_DIM, 128, N_CLASSES, MAX_LEN)
        best, final, tensions, ts = train_eval(repul, train_emb, test_emb, EPOCHS)
        emb_results['repulsion'].append(best)
        print(f"    Seed {seed}: Dense={emb_results['dense'][-1]*100:.1f}%  "
              f"Repulsion={best*100:.1f}%  tension_scale={ts:.4f}")

    emb_dense_mean = np.mean(emb_results['dense']) * 100
    emb_repul_mean = np.mean(emb_results['repulsion']) * 100
    emb_delta = emb_repul_mean - emb_dense_mean

    # --- Text summary ---
    print(f"\n  {'='*60}")
    print(f"  TEXT CLASSIFICATION RESULTS")
    print(f"  {'='*60}")
    print(f"  {'Representation':<20} {'Dense':>10} {'Repulsion':>12} {'Delta':>8} {'Winner':>10}")
    print(f"  {'-'*60}")
    w1 = 'Repulsion' if tfidf_delta > 0 else 'Dense'
    w2 = 'Repulsion' if emb_delta > 0 else 'Dense'
    print(f"  {'TF-IDF (sparse)':<20} {tfidf_dense_mean:>8.2f}%  {tfidf_repul_mean:>9.2f}%  {tfidf_delta:>+6.2f}%  {w1:>9}")
    print(f"  {'Embedding (dense)':<20} {emb_dense_mean:>8.2f}%  {emb_repul_mean:>9.2f}%  {emb_delta:>+6.2f}%  {w2:>9}")
    print(f"\n  Key finding: Dense > Sparse? {emb_delta > tfidf_delta}")
    print(f"  Embedding advantage over TF-IDF delta: {emb_delta - tfidf_delta:+.2f}%")

    return {
        'tfidf_dense': tfidf_dense_mean,
        'tfidf_repul': tfidf_repul_mean,
        'tfidf_delta': tfidf_delta,
        'emb_dense': emb_dense_mean,
        'emb_repul': emb_repul_mean,
        'emb_delta': emb_delta,
    }


# ═════════════════════════════════════════
# PART 2: TIME SERIES CLASSIFICATION (expanded)
# ═════════════════════════════════════════

def generate_timeseries_4class(n_per_class=150, seq_len=64, noise_std=0.15, seed=42):
    """4 classes: sine, square, sawtooth, triangle."""
    rng = np.random.RandomState(seed)
    X_all, y_all = [], []
    t = np.linspace(0, 2 * np.pi, seq_len)

    for i in range(n_per_class):
        freq = rng.uniform(0.8, 1.5)
        phase = rng.uniform(0, 2 * np.pi)

        # Class 0: sine
        w = np.sin(freq * t + phase) + rng.randn(seq_len) * noise_std
        X_all.append(w); y_all.append(0)

        # Class 1: square
        w = np.sign(np.sin(freq * t + phase)) + rng.randn(seq_len) * noise_std
        X_all.append(w); y_all.append(1)

        # Class 2: sawtooth
        w = 2 * ((freq * t / (2 * np.pi) + phase / (2 * np.pi)) % 1) - 1 + rng.randn(seq_len) * noise_std
        X_all.append(w); y_all.append(2)

        # Class 3: triangle
        w = 2 * np.abs(2 * ((freq * t / (2 * np.pi) + phase / (2 * np.pi)) % 1) - 1) - 1 + rng.randn(seq_len) * noise_std
        X_all.append(w); y_all.append(3)

    X = np.array(X_all, dtype=np.float32)
    y = np.array(y_all, dtype=np.int64)
    idx = rng.permutation(len(y))
    X, y = X[idx], y[idx]

    split = int(0.8 * len(y))
    train_ds = TensorDataset(torch.from_numpy(X[:split]), torch.from_numpy(y[:split]))
    test_ds = TensorDataset(torch.from_numpy(X[split:]), torch.from_numpy(y[split:]))
    train_loader = DataLoader(train_ds, batch_size=32, shuffle=True)
    test_loader = DataLoader(test_ds, batch_size=64)

    return train_loader, test_loader


def generate_hard_timeseries(n_per_class=200, seq_len=64, seed=42):
    """Harder: same shapes but with varying amplitude and frequency overlap."""
    rng = np.random.RandomState(seed)
    X_all, y_all = [], []
    t = np.linspace(0, 4 * np.pi, seq_len)

    for i in range(n_per_class):
        freq = rng.uniform(0.5, 2.0)
        amp = rng.uniform(0.3, 1.5)
        phase = rng.uniform(0, 2 * np.pi)
        noise = rng.uniform(0.1, 0.3)

        # Class 0: damped sine
        decay = np.exp(-t / (4 * np.pi))
        w = amp * decay * np.sin(freq * t + phase) + rng.randn(seq_len) * noise
        X_all.append(w); y_all.append(0)

        # Class 1: chirp (increasing frequency)
        chirp_freq = freq * (1 + t / (4 * np.pi))
        w = amp * np.sin(chirp_freq * t + phase) + rng.randn(seq_len) * noise
        X_all.append(w); y_all.append(1)

        # Class 2: AM modulated
        w = amp * (1 + 0.5 * np.sin(0.3 * t)) * np.sin(freq * t + phase) + rng.randn(seq_len) * noise
        X_all.append(w); y_all.append(2)

    X = np.array(X_all, dtype=np.float32)
    y = np.array(y_all, dtype=np.int64)

    # Normalize per sample
    X = (X - X.mean(axis=1, keepdims=True)) / (X.std(axis=1, keepdims=True) + 1e-8)

    idx = rng.permutation(len(y))
    X, y = X[idx], y[idx]

    split = int(0.8 * len(y))
    train_ds = TensorDataset(torch.from_numpy(X[:split]), torch.from_numpy(y[:split]))
    test_ds = TensorDataset(torch.from_numpy(X[split:]), torch.from_numpy(y[split:]))
    train_loader = DataLoader(train_ds, batch_size=32, shuffle=True)
    test_loader = DataLoader(test_ds, batch_size=64)

    return train_loader, test_loader


def run_timeseries_experiments():
    print("\n" + "=" * 70)
    print("  PART 2: TIME SERIES CLASSIFICATION")
    print("=" * 70)

    SEQ_LEN = 64
    HIDDEN = 48
    EPOCHS = 30
    N_SEEDS = 5

    results = {}

    # --- Easy: 4-class waveforms ---
    print("\n  --- A. 4-class waveforms (sine/square/sawtooth/triangle) ---")
    easy_results = {'dense': [], 'repulsion': [], 'tensions': []}
    for seed in range(N_SEEDS):
        train_loader, test_loader = generate_timeseries_4class(
            n_per_class=150, seq_len=SEQ_LEN, noise_std=0.15, seed=42 + seed * 13)

        torch.manual_seed(42 + seed * 13)
        dense = DenseBaseline(SEQ_LEN, HIDDEN, 4)
        best_d, _, _, _ = train_eval(dense, train_loader, test_loader, EPOCHS, lr=0.003)
        easy_results['dense'].append(best_d)

        torch.manual_seed(42 + seed * 13)
        repul = RepulsionField(SEQ_LEN, HIDDEN, 4)
        best_r, _, tensions, ts = train_eval(repul, train_loader, test_loader, EPOCHS, lr=0.003)
        easy_results['repulsion'].append(best_r)
        easy_results['tensions'].append(tensions[-1])
        print(f"    Seed {seed}: Dense={best_d*100:.1f}%  Repulsion={best_r*100:.1f}%  "
              f"tension={tensions[-1]:.4f}  ts={ts:.4f}")

    easy_d = np.mean(easy_results['dense']) * 100
    easy_r = np.mean(easy_results['repulsion']) * 100
    easy_delta = easy_r - easy_d

    # --- Hard: signal processing classes ---
    print("\n  --- B. Hard: damped/chirp/AM (3 classes, overlapping) ---")
    hard_results = {'dense': [], 'repulsion': [], 'tensions': []}
    for seed in range(N_SEEDS):
        train_loader, test_loader = generate_hard_timeseries(
            n_per_class=200, seq_len=SEQ_LEN, seed=42 + seed * 17)

        torch.manual_seed(42 + seed * 17)
        dense = DenseBaseline(SEQ_LEN, HIDDEN, 3)
        best_d, _, _, _ = train_eval(dense, train_loader, test_loader, EPOCHS, lr=0.003)
        hard_results['dense'].append(best_d)

        torch.manual_seed(42 + seed * 17)
        repul = RepulsionField(SEQ_LEN, HIDDEN, 3)
        best_r, _, tensions, ts = train_eval(repul, train_loader, test_loader, EPOCHS, lr=0.003)
        hard_results['repulsion'].append(best_r)
        hard_results['tensions'].append(tensions[-1])
        print(f"    Seed {seed}: Dense={best_d*100:.1f}%  Repulsion={best_r*100:.1f}%  "
              f"tension={tensions[-1]:.4f}  ts={ts:.4f}")

    hard_d = np.mean(hard_results['dense']) * 100
    hard_r = np.mean(hard_results['repulsion']) * 100
    hard_delta = hard_r - hard_d

    # --- Time series summary ---
    print(f"\n  {'='*60}")
    print(f"  TIME SERIES RESULTS")
    print(f"  {'='*60}")
    print(f"  {'Dataset':<25} {'Dense':>10} {'Repulsion':>12} {'Delta':>8} {'Winner':>10}")
    print(f"  {'-'*65}")
    w1 = 'Repulsion' if easy_delta > 0 else 'Dense'
    w2 = 'Repulsion' if hard_delta > 0 else 'Dense'
    print(f"  {'Easy (4 waveforms)':<25} {easy_d:>8.2f}%  {easy_r:>9.2f}%  {easy_delta:>+6.2f}%  {w1:>9}")
    print(f"  {'Hard (signal proc.)':<25} {hard_d:>8.2f}%  {hard_r:>9.2f}%  {hard_delta:>+6.2f}%  {w2:>9}")

    return {
        'easy_dense': easy_d, 'easy_repul': easy_r, 'easy_delta': easy_delta,
        'hard_dense': hard_d, 'hard_repul': hard_r, 'hard_delta': hard_delta,
        'easy_tensions': easy_results['tensions'],
        'hard_tensions': hard_results['tensions'],
    }


# ═════════════════════════════════════════
# MAIN
# ═════════════════════════════════════════

def main():
    print("=" * 70)
    print("  H-285 VERIFICATION: RepulsionField Beyond Image Classification")
    print("  Part 1: Text (TF-IDF vs Embedding)")
    print("  Part 2: Time Series (Easy vs Hard)")
    print("=" * 70)
    t0 = time.time()

    text_res = run_text_experiments()
    ts_res = run_timeseries_experiments()

    # ═══ CROSS-DOMAIN SUMMARY ═══
    print(f"\n\n{'='*70}")
    print("  CROSS-DOMAIN SUMMARY TABLE")
    print(f"{'='*70}")
    print(f"\n  {'Domain':<25} {'Type':<10} {'Dense':>8} {'Repulsion':>10} {'Delta':>8}")
    print(f"  {'-'*65}")

    rows = [
        ('Text TF-IDF', 'Sparse', text_res['tfidf_dense'], text_res['tfidf_repul'], text_res['tfidf_delta']),
        ('Text Embedding', 'Dense', text_res['emb_dense'], text_res['emb_repul'], text_res['emb_delta']),
        ('TimeSeries Easy', 'Dense', ts_res['easy_dense'], ts_res['easy_repul'], ts_res['easy_delta']),
        ('TimeSeries Hard', 'Dense', ts_res['hard_dense'], ts_res['hard_repul'], ts_res['hard_delta']),
        ('MNIST (prior)', 'Dense', 97.1, 97.7, 0.6),
        ('CIFAR (prior)', 'Dense', 48.2, 53.0, 4.8),
    ]

    for name, dtype, d, r, delta in rows:
        marker = '*' if name.endswith('(prior)') else ' '
        print(f"  {name:<25} {dtype:<10} {d:>6.2f}%  {r:>8.2f}%  {delta:>+6.2f}%{marker}")

    print(f"\n  * = prior results (not from this experiment)")

    # ASCII comparison bar chart
    print(f"\n  --- Delta (Repulsion - Dense) ASCII Chart ---")
    for name, dtype, d, r, delta in rows:
        bar_width = int(abs(delta) * 5)
        if delta >= 0:
            bar = '+' * min(bar_width, 40)
            print(f"  {name:<25} |{'.' * 20}{bar:>20}| {delta:+.2f}%")
        else:
            bar = '-' * min(bar_width, 20)
            print(f"  {name:<25} |{bar:>20}{'.' * 20}| {delta:+.2f}%")

    # ═══ Key findings ═══
    print(f"\n{'='*70}")
    print("  KEY FINDINGS")
    print(f"{'='*70}")

    # Dense vs Sparse
    emb_better = text_res['emb_delta'] > text_res['tfidf_delta']
    print(f"\n  1. Dense > Sparse for RepulsionField? {'YES' if emb_better else 'NO'}")
    print(f"     TF-IDF delta:     {text_res['tfidf_delta']:+.2f}%")
    print(f"     Embedding delta:  {text_res['emb_delta']:+.2f}%")
    print(f"     Improvement:      {text_res['emb_delta'] - text_res['tfidf_delta']:+.2f}%")

    # Time series
    print(f"\n  2. Time series:")
    print(f"     Easy delta: {ts_res['easy_delta']:+.2f}%")
    print(f"     Hard delta: {ts_res['hard_delta']:+.2f}%")
    print(f"     Avg tension (easy): {np.mean(ts_res['easy_tensions']):.4f}")
    print(f"     Avg tension (hard): {np.mean(ts_res['hard_tensions']):.4f}")

    # Domain universality
    new_deltas = [text_res['tfidf_delta'], text_res['emb_delta'],
                  ts_res['easy_delta'], ts_res['hard_delta']]
    positive = sum(1 for d in new_deltas if d > 0)
    print(f"\n  3. Domains where RepulsionField > Dense: {positive}/{len(new_deltas)}")
    avg_delta = np.mean(new_deltas)
    print(f"     Average delta across new domains: {avg_delta:+.2f}%")

    elapsed = time.time() - t0
    print(f"\n  Total time: {elapsed:.1f}s")
    print("=" * 70)


if __name__ == '__main__':
    main()
