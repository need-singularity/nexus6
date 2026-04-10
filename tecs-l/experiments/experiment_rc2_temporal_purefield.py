#!/usr/bin/env python3
"""RC-2: Temporal Continuity for PureField Engine

PureField produces tension from engine_A vs engine_G repulsion.
This experiment adds temporal memory (GRU-style hidden state)
so tension fingerprints persist across time steps.

Task: MNIST digit sequence prediction (predict next digit).
Key question: does tension track "surprise" (unexpected digits)?

Architecture:
  PureField (baseline):  no memory, each input independent
  PureField+Memory:      state = GRU(prev_state, tension_fingerprint)
                          PureField uses state as additional context

Metrics:
  1. Next-digit prediction accuracy
  2. Tension vs surprise correlation (surprise = -log P(digit))
  3. Temporal coherence (does state carry useful info?)
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader
from torchvision import datasets, transforms
import numpy as np
import time
import math


# ─────────────────────────────────────────
# PureField base (from model_pure_field.py)
# ─────────────────────────────────────────
class PureFieldCore(nn.Module):
    """Core PureField: returns output logits + tension fingerprint."""

    def __init__(self, input_dim, hidden_dim, output_dim):
        super().__init__()
        self.engine_a = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(hidden_dim, output_dim),
        )
        self.engine_g = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(hidden_dim, output_dim),
        )
        self.tension_scale = nn.Parameter(torch.tensor(1.0))

    def forward(self, x):
        out_a = self.engine_a(x)
        out_g = self.engine_g(x)

        repulsion = out_a - out_g
        tension = (repulsion ** 2).mean(dim=-1, keepdim=True)
        direction = F.normalize(repulsion, dim=-1)

        output = self.tension_scale * torch.sqrt(tension + 1e-8) * direction
        # tension_fingerprint = full repulsion vector (richer than scalar)
        return output, repulsion, tension.squeeze(-1)


# ─────────────────────────────────────────
# Model 1: PureField (no memory) for sequences
# ─────────────────────────────────────────
class PureFieldSeq(nn.Module):
    """PureField without memory. Processes each step independently."""

    def __init__(self, input_dim=784, hidden_dim=128, output_dim=10):
        super().__init__()
        self.core = PureFieldCore(input_dim, hidden_dim, output_dim)
        # Predict next digit from current PureField output
        self.predictor = nn.Linear(output_dim, output_dim)

    def forward(self, x_seq):
        """x_seq: (batch, seq_len, input_dim)"""
        batch, seq_len, inp_dim = x_seq.shape
        all_preds = []
        all_tensions = []

        for t in range(seq_len):
            output, repulsion, tension = self.core(x_seq[:, t])
            pred = self.predictor(output)
            all_preds.append(pred)
            all_tensions.append(tension)

        preds = torch.stack(all_preds, dim=1)       # (batch, seq_len, 10)
        tensions = torch.stack(all_tensions, dim=1)  # (batch, seq_len)
        return preds, tensions


# ─────────────────────────────────────────
# Model 2: PureField + Memory (GRU-style)
# ─────────────────────────────────────────
class PureFieldMemory(nn.Module):
    """PureField with GRU-style temporal memory.

    state = GRU(prev_state, tension_fingerprint)
    PureField uses state as additional input context.
    """

    def __init__(self, input_dim=784, hidden_dim=128, output_dim=10, state_dim=64):
        super().__init__()
        self.state_dim = state_dim
        self.output_dim = output_dim

        # Core PureField takes input + state context
        self.core = PureFieldCore(input_dim + state_dim, hidden_dim, output_dim)

        # GRU cell: updates state from tension fingerprint (repulsion vector)
        self.gru = nn.GRUCell(input_size=output_dim, hidden_size=state_dim)

        # Predict next digit from PureField output + state
        self.predictor = nn.Linear(output_dim + state_dim, output_dim)

    def forward(self, x_seq, initial_state=None):
        """x_seq: (batch, seq_len, input_dim)"""
        batch, seq_len, inp_dim = x_seq.shape

        # Initialize hidden state
        if initial_state is None:
            state = torch.zeros(batch, self.state_dim, device=x_seq.device)
        else:
            state = initial_state

        all_preds = []
        all_tensions = []
        all_states = []

        for t in range(seq_len):
            # Concatenate input with temporal state
            x_with_state = torch.cat([x_seq[:, t], state], dim=-1)

            # PureField forward
            output, repulsion, tension = self.core(x_with_state)

            # Update state via GRU using tension fingerprint (repulsion)
            state = self.gru(repulsion, state)

            # Predict next digit using output + updated state
            pred = self.predictor(torch.cat([output, state], dim=-1))
            all_preds.append(pred)
            all_tensions.append(tension)
            all_states.append(state)

        preds = torch.stack(all_preds, dim=1)       # (batch, seq_len, 10)
        tensions = torch.stack(all_tensions, dim=1)  # (batch, seq_len)
        states = torch.stack(all_states, dim=1)      # (batch, seq_len, state_dim)
        return preds, tensions, states


# ─────────────────────────────────────────
# Model 3: GRU baseline (no PureField)
# ─────────────────────────────────────────
class GRUBaseline(nn.Module):
    """Plain GRU baseline for comparison."""

    def __init__(self, input_dim=784, hidden_dim=128, output_dim=10):
        super().__init__()
        self.encoder = nn.Linear(input_dim, hidden_dim)
        self.gru = nn.GRUCell(hidden_dim, hidden_dim)
        self.predictor = nn.Linear(hidden_dim, output_dim)

    def forward(self, x_seq):
        batch, seq_len, inp_dim = x_seq.shape
        state = torch.zeros(batch, self.gru.hidden_size, device=x_seq.device)
        all_preds = []

        for t in range(seq_len):
            enc = F.relu(self.encoder(x_seq[:, t]))
            state = self.gru(enc, state)
            pred = self.predictor(state)
            all_preds.append(pred)

        preds = torch.stack(all_preds, dim=1)
        return preds


# ─────────────────────────────────────────
# Dataset: MNIST digit sequences
# ─────────────────────────────────────────
class MNISTSequenceDataset(Dataset):
    """Random digit sequences from MNIST.

    Each sample: sequence of seq_len random MNIST images.
    Target: next digit in the sequence (shifted by 1).
    Some sequences have "pattern" (e.g., ascending) to test surprise.
    """

    def __init__(self, mnist_dataset, seq_len=8, num_sequences=5000,
                 pattern_ratio=0.3, seed=42):
        self.mnist = mnist_dataset
        self.seq_len = seq_len
        self.num_sequences = num_sequences
        self.rng = np.random.RandomState(seed)

        # Index MNIST by digit
        self.digit_indices = {d: [] for d in range(10)}
        for i, (_, label) in enumerate(mnist_dataset):
            self.digit_indices[label].append(i)
        for d in range(10):
            self.digit_indices[d] = np.array(self.digit_indices[d])

        # Pre-generate sequences
        self.sequences = []
        self.labels = []
        self.is_pattern = []  # whether this sequence follows a pattern
        self.surprise_flags = []  # per-step: is this digit "surprising"?

        for i in range(num_sequences):
            if self.rng.random() < pattern_ratio:
                # Pattern sequence: repeat or ascending
                seq_digits, surprises = self._make_pattern_sequence()
                self.is_pattern.append(True)
            else:
                # Random sequence
                seq_digits = self.rng.randint(0, 10, size=seq_len + 1)
                surprises = [False] * (seq_len + 1)
                self.is_pattern.append(False)

            # Get MNIST images for these digits
            images = []
            for d in seq_digits:
                idx = self.rng.choice(self.digit_indices[d])
                img, _ = self.mnist[idx]
                images.append(img.view(-1))  # flatten to 784

            self.sequences.append(torch.stack(images))
            self.labels.append(torch.tensor(seq_digits, dtype=torch.long))
            self.surprise_flags.append(surprises)

    def _make_pattern_sequence(self):
        """Generate a patterned sequence with occasional surprise breaks."""
        seq_len = self.seq_len + 1  # +1 for target
        pattern_type = self.rng.choice(['repeat', 'ascending', 'cycle3'])
        surprises = [False] * seq_len

        if pattern_type == 'repeat':
            base = self.rng.randint(0, 10)
            digits = [base] * seq_len
        elif pattern_type == 'ascending':
            start = self.rng.randint(0, 5)
            digits = [(start + i) % 10 for i in range(seq_len)]
        else:  # cycle3
            base = self.rng.randint(0, 8)
            cycle = [base, base + 1, base + 2]
            digits = [cycle[i % 3] for i in range(seq_len)]

        # Insert 1-2 surprise breaks
        n_breaks = self.rng.randint(1, 3)
        break_positions = self.rng.choice(
            range(2, seq_len), size=min(n_breaks, seq_len - 2), replace=False
        )
        for pos in break_positions:
            old = digits[pos]
            new = (old + self.rng.randint(3, 8)) % 10  # different digit
            digits[pos] = new
            surprises[pos] = True

        return np.array(digits), surprises

    def __len__(self):
        return self.num_sequences

    def __getitem__(self, idx):
        # Input: first seq_len images, Target: digits[1:seq_len+1]
        images = self.sequences[idx]  # (seq_len+1, 784)
        labels = self.labels[idx]     # (seq_len+1,)
        surprises = self.surprise_flags[idx]

        x = images[:self.seq_len]           # (seq_len, 784)
        y = labels[1:self.seq_len + 1]      # (seq_len,) next digit targets
        surprise_mask = torch.tensor(
            surprises[1:self.seq_len + 1], dtype=torch.bool
        )
        return x, y, surprise_mask


# ─────────────────────────────────────────
# Training
# ─────────────────────────────────────────
def train_model(model, train_loader, test_loader, epochs=15, lr=1e-3,
                model_type='memory', verbose=True):
    """Train a sequence prediction model."""
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    criterion = nn.CrossEntropyLoss()

    history = {'train_loss': [], 'test_acc': [], 'test_loss': []}

    for epoch in range(epochs):
        model.train()
        total_loss = 0
        n_batches = 0

        for x, y, _ in train_loader:
            optimizer.zero_grad()

            if model_type == 'memory':
                preds, tensions, states = model(x)
            elif model_type == 'no_memory':
                preds, tensions = model(x)
            else:  # gru baseline
                preds = model(x)

            # preds: (batch, seq_len, 10), y: (batch, seq_len)
            loss = criterion(preds.reshape(-1, 10), y.reshape(-1))
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
            n_batches += 1

        avg_loss = total_loss / n_batches
        history['train_loss'].append(avg_loss)

        # Evaluate
        model.eval()
        correct = total = 0
        test_loss = 0
        n_test = 0
        with torch.no_grad():
            for x, y, _ in test_loader:
                if model_type == 'memory':
                    preds, _, _ = model(x)
                elif model_type == 'no_memory':
                    preds, _ = model(x)
                else:
                    preds = model(x)

                loss = criterion(preds.reshape(-1, 10), y.reshape(-1))
                test_loss += loss.item()
                n_test += 1
                correct += (preds.reshape(-1, 10).argmax(1) == y.reshape(-1)).sum().item()
                total += y.numel()

        acc = correct / total
        history['test_acc'].append(acc)
        history['test_loss'].append(test_loss / n_test)

        if verbose and ((epoch + 1) % 3 == 0 or epoch == 0):
            print(f"    Epoch {epoch+1:>2}/{epochs}: "
                  f"Loss={avg_loss:.4f}, Acc={acc*100:.1f}%")

    return history


# ─────────────────────────────────────────
# Surprise-Tension Analysis
# ─────────────────────────────────────────
def analyze_tension_surprise(model, test_loader, model_type='memory'):
    """Analyze correlation between tension and surprise."""
    model.eval()
    all_tensions_surprise = []
    all_tensions_normal = []
    all_tensions_by_position = {t: [] for t in range(8)}

    # Track tension delta at surprise points
    tension_deltas_surprise = []
    tension_deltas_normal = []

    with torch.no_grad():
        for x, y, surprise_mask in test_loader:
            if model_type == 'memory':
                preds, tensions, states = model(x)
            elif model_type == 'no_memory':
                preds, tensions = model(x)
            else:
                continue  # GRU baseline has no tension

            # tensions: (batch, seq_len)
            for b in range(tensions.size(0)):
                for t in range(tensions.size(1)):
                    val = tensions[b, t].item()
                    all_tensions_by_position[t].append(val)

                    if t > 0:
                        delta = val - tensions[b, t-1].item()
                        if surprise_mask[b, t]:
                            tension_deltas_surprise.append(delta)
                            all_tensions_surprise.append(val)
                        else:
                            tension_deltas_normal.append(delta)
                            all_tensions_normal.append(val)

    results = {}
    if all_tensions_surprise and all_tensions_normal:
        mean_s = np.mean(all_tensions_surprise)
        mean_n = np.mean(all_tensions_normal)
        std_s = np.std(all_tensions_surprise)
        std_n = np.std(all_tensions_normal)
        results['tension_surprise_mean'] = mean_s
        results['tension_normal_mean'] = mean_n
        results['tension_ratio'] = mean_s / (mean_n + 1e-8)
        results['tension_surprise_std'] = std_s
        results['tension_normal_std'] = std_n

        # Cohen's d effect size
        pooled_std = np.sqrt((std_s**2 + std_n**2) / 2)
        results['cohens_d'] = (mean_s - mean_n) / (pooled_std + 1e-8)

        # Tension delta analysis
        if tension_deltas_surprise and tension_deltas_normal:
            results['delta_surprise_mean'] = np.mean(tension_deltas_surprise)
            results['delta_normal_mean'] = np.mean(tension_deltas_normal)
            results['delta_ratio'] = (
                np.mean(tension_deltas_surprise) /
                (abs(np.mean(tension_deltas_normal)) + 1e-8)
            )

    # Temporal evolution
    results['tension_by_position'] = {
        t: np.mean(vals) for t, vals in all_tensions_by_position.items() if vals
    }

    return results


# ─────────────────────────────────────────
# State continuity analysis
# ─────────────────────────────────────────
def analyze_state_continuity(model, test_loader):
    """Check if hidden states carry meaningful temporal info."""
    model.eval()
    state_norms = []
    state_diffs = []

    with torch.no_grad():
        for x, y, _ in test_loader:
            _, _, states = model(x)  # (batch, seq_len, state_dim)
            # State norms over time
            norms = states.norm(dim=-1)  # (batch, seq_len)
            state_norms.append(norms.mean(dim=0).cpu().numpy())

            # State change between steps
            if states.size(1) > 1:
                diffs = (states[:, 1:] - states[:, :-1]).norm(dim=-1)
                state_diffs.append(diffs.mean(dim=0).cpu().numpy())

    avg_norms = np.mean(state_norms, axis=0)
    avg_diffs = np.mean(state_diffs, axis=0) if state_diffs else np.array([0])

    return {
        'state_norms': avg_norms,
        'state_diffs': avg_diffs,
        'norm_growth': avg_norms[-1] / (avg_norms[0] + 1e-8),
        'avg_state_change': avg_diffs.mean(),
    }


# ─────────────────────────────────────────
# Visualization (ASCII)
# ─────────────────────────────────────────
def ascii_bar(label, value, max_val, width=40):
    bar_len = int(value / (max_val + 1e-8) * width)
    bar = '#' * bar_len + '.' * (width - bar_len)
    return f"  {label:>12s} |{bar}| {value:.4f}"


def ascii_line_graph(values, title, width=60, height=12):
    """Simple ASCII line graph."""
    if not values:
        return ""
    min_v = min(values)
    max_v = max(values)
    rng = max_v - min_v if max_v > min_v else 1

    lines = [f"  {title}"]
    lines.append(f"  {max_v:.4f} |")

    grid = [[' '] * width for _ in range(height)]
    for i, v in enumerate(values):
        x = int(i / (len(values) - 1 + 1e-8) * (width - 1))
        y = int((v - min_v) / rng * (height - 1))
        y = height - 1 - y  # invert
        if 0 <= x < width and 0 <= y < height:
            grid[y][x] = '*'

    for row in grid:
        lines.append(f"          |{''.join(row)}|")
    lines.append(f"  {min_v:.4f} |{'_' * width}|")
    lines.append(f"          {'step 0':<{width//2}}{'step ' + str(len(values)-1):>{width//2}}")

    return '\n'.join(lines)


# ─────────────────────────────────────────
# Main experiment
# ─────────────────────────────────────────
def main():
    print("=" * 70)
    print("  RC-2: Temporal Continuity for PureField Engine")
    print("  PureField + GRU-style state memory")
    print("  Task: MNIST sequence -> predict next digit")
    print("=" * 70)

    torch.manual_seed(42)
    np.random.seed(42)

    # Load MNIST
    print("\n[1] Loading MNIST...")
    transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize((0.1307,), (0.3081,))
    ])
    mnist_train = datasets.MNIST('data', train=True, download=True, transform=transform)
    mnist_test = datasets.MNIST('data', train=False, transform=transform)

    SEQ_LEN = 8
    N_TRAIN = 8000
    N_TEST = 2000
    BATCH = 64
    EPOCHS = 20

    print(f"  Sequence length: {SEQ_LEN}")
    print(f"  Train sequences: {N_TRAIN}, Test: {N_TEST}")
    print(f"  Pattern ratio: 30% (with surprise breaks)")
    print(f"  Epochs: {EPOCHS}")

    train_ds = MNISTSequenceDataset(mnist_train, seq_len=SEQ_LEN,
                                     num_sequences=N_TRAIN, seed=42)
    test_ds = MNISTSequenceDataset(mnist_test, seq_len=SEQ_LEN,
                                    num_sequences=N_TEST, seed=123)

    train_loader = DataLoader(train_ds, batch_size=BATCH, shuffle=True)
    test_loader = DataLoader(test_ds, batch_size=BATCH, shuffle=False)

    results = {}

    # ── Model 1: PureField (no memory) ──
    print("\n" + "-" * 70)
    print("  [2] PureField (no memory)")
    print("-" * 70)
    model_no_mem = PureFieldSeq(784, 128, 10)
    n_params = sum(p.numel() for p in model_no_mem.parameters())
    print(f"  Parameters: {n_params:,}")

    t0 = time.time()
    hist_no_mem = train_model(model_no_mem, train_loader, test_loader,
                               epochs=EPOCHS, model_type='no_memory')
    t_no_mem = time.time() - t0
    print(f"  Time: {t_no_mem:.1f}s")

    results['PureField (no mem)'] = {
        'acc': hist_no_mem['test_acc'][-1],
        'loss': hist_no_mem['test_loss'][-1],
        'params': n_params,
        'history': hist_no_mem,
    }

    # ── Model 2: PureField + Memory ──
    print("\n" + "-" * 70)
    print("  [3] PureField + Memory (GRU-style)")
    print("-" * 70)
    model_mem = PureFieldMemory(784, 128, 10, state_dim=64)
    n_params_mem = sum(p.numel() for p in model_mem.parameters())
    print(f"  Parameters: {n_params_mem:,}")

    t0 = time.time()
    hist_mem = train_model(model_mem, train_loader, test_loader,
                            epochs=EPOCHS, model_type='memory')
    t_mem = time.time() - t0
    print(f"  Time: {t_mem:.1f}s")

    results['PureField+Memory'] = {
        'acc': hist_mem['test_acc'][-1],
        'loss': hist_mem['test_loss'][-1],
        'params': n_params_mem,
        'history': hist_mem,
    }

    # ── Model 3: GRU Baseline ──
    print("\n" + "-" * 70)
    print("  [4] GRU Baseline (no PureField)")
    print("-" * 70)
    model_gru = GRUBaseline(784, 128, 10)
    n_params_gru = sum(p.numel() for p in model_gru.parameters())
    print(f"  Parameters: {n_params_gru:,}")

    t0 = time.time()
    hist_gru = train_model(model_gru, train_loader, test_loader,
                            epochs=EPOCHS, model_type='gru')
    t_gru = time.time() - t0
    print(f"  Time: {t_gru:.1f}s")

    results['GRU Baseline'] = {
        'acc': hist_gru['test_acc'][-1],
        'loss': hist_gru['test_loss'][-1],
        'params': n_params_gru,
        'history': hist_gru,
    }

    # ── Comparison ──
    print("\n" + "=" * 70)
    print("  RESULTS: Next-Digit Prediction Accuracy")
    print("=" * 70)
    print(f"  {'Model':<25} {'Acc':>8} {'Loss':>8} {'Params':>10}")
    print("-" * 70)
    best_acc = max(r['acc'] for r in results.values())
    for name, r in sorted(results.items(), key=lambda x: -x[1]['acc']):
        marker = ' <-- best' if r['acc'] == best_acc else ''
        print(f"  {name:<25} {r['acc']*100:>7.2f}% {r['loss']:>8.4f} "
              f"{r['params']:>10,}{marker}")
    print("=" * 70)

    # Memory advantage
    mem_acc = results['PureField+Memory']['acc']
    no_mem_acc = results['PureField (no mem)']['acc']
    gru_acc = results['GRU Baseline']['acc']
    print(f"\n  Memory advantage:  +{(mem_acc - no_mem_acc)*100:.2f}% "
          f"(PureField+Memory vs PureField)")
    print(f"  vs GRU baseline:   {(mem_acc - gru_acc)*100:+.2f}% "
          f"(PureField+Memory vs GRU)")

    # ── Learning curves ──
    print("\n" + "-" * 70)
    print("  Learning Curves (test accuracy %)")
    print("-" * 70)
    print(f"  {'Epoch':>5}", end='')
    for name in ['PureField (no mem)', 'PureField+Memory', 'GRU Baseline']:
        print(f"  {name:>22}", end='')
    print()
    for e in range(EPOCHS):
        print(f"  {e+1:>5}", end='')
        for name in ['PureField (no mem)', 'PureField+Memory', 'GRU Baseline']:
            acc = results[name]['history']['test_acc'][e]
            print(f"  {acc*100:>21.2f}%", end='')
        print()

    # ── Tension-Surprise Analysis ──
    print("\n" + "=" * 70)
    print("  TENSION-SURPRISE ANALYSIS")
    print("=" * 70)

    for name, model, mtype in [
        ('PureField (no mem)', model_no_mem, 'no_memory'),
        ('PureField+Memory', model_mem, 'memory'),
    ]:
        print(f"\n  --- {name} ---")
        ts = analyze_tension_surprise(model, test_loader, model_type=mtype)

        if 'tension_surprise_mean' in ts:
            print(f"  Tension at SURPRISE steps:  {ts['tension_surprise_mean']:.6f} "
                  f"(std={ts['tension_surprise_std']:.6f})")
            print(f"  Tension at NORMAL steps:    {ts['tension_normal_mean']:.6f} "
                  f"(std={ts['tension_normal_std']:.6f})")
            print(f"  Ratio (surprise/normal):    {ts['tension_ratio']:.4f}")
            print(f"  Cohen's d effect size:      {ts['cohens_d']:.4f}")

            if 'delta_surprise_mean' in ts:
                print(f"  Tension DELTA at surprise:  {ts['delta_surprise_mean']:.6f}")
                print(f"  Tension DELTA at normal:    {ts['delta_normal_mean']:.6f}")
                print(f"  Delta ratio:                {ts['delta_ratio']:.4f}")

            # ASCII bar chart
            max_t = max(ts['tension_surprise_mean'], ts['tension_normal_mean'])
            print()
            print(ascii_bar("surprise", ts['tension_surprise_mean'], max_t))
            print(ascii_bar("normal", ts['tension_normal_mean'], max_t))

        # Tension by position
        if ts.get('tension_by_position'):
            print(f"\n  Tension by sequence position:")
            pos_vals = ts['tension_by_position']
            max_t = max(pos_vals.values())
            for t in sorted(pos_vals.keys()):
                print(ascii_bar(f"t={t}", pos_vals[t], max_t))

    # ── State Continuity Analysis (Memory model only) ──
    print("\n" + "=" * 70)
    print("  STATE CONTINUITY ANALYSIS (PureField+Memory)")
    print("=" * 70)

    sc = analyze_state_continuity(model_mem, test_loader)
    print(f"  State norm growth (t=0 -> t={SEQ_LEN-1}): {sc['norm_growth']:.4f}x")
    print(f"  Average state change per step:              {sc['avg_state_change']:.6f}")

    print(f"\n  State norms by position:")
    max_norm = max(sc['state_norms'])
    for t, val in enumerate(sc['state_norms']):
        print(ascii_bar(f"t={t}", val, max_norm))

    print(f"\n  State change (delta) by position:")
    max_diff = max(sc['state_diffs']) if len(sc['state_diffs']) > 0 else 1
    for t, val in enumerate(sc['state_diffs']):
        print(ascii_bar(f"t={t}->{t+1}", val, max_diff))

    # ── Summary ──
    print("\n" + "=" * 70)
    print("  RC-2 SUMMARY")
    print("=" * 70)
    print(f"""
  1. Memory helps:     {'YES' if mem_acc > no_mem_acc else 'NO'}
     ({(mem_acc - no_mem_acc)*100:+.2f}% accuracy gain)

  2. Tension tracks surprise: """, end='')

    ts_mem = analyze_tension_surprise(model_mem, test_loader, model_type='memory')
    if 'cohens_d' in ts_mem:
        d = ts_mem['cohens_d']
        if abs(d) > 0.5:
            print(f"STRONG (Cohen's d = {d:.3f})")
        elif abs(d) > 0.2:
            print(f"MODERATE (Cohen's d = {d:.3f})")
        else:
            print(f"WEAK (Cohen's d = {d:.3f})")
    else:
        print("N/A")

    print(f"""
  3. State continuity: norm grows {sc['norm_growth']:.2f}x over {SEQ_LEN} steps
     (>1 = state accumulates info, ~1 = stationary)

  4. Architecture:
     PureField+Memory = PureField(input||state) + GRU(tension_fingerprint)
     Tension fingerprint = repulsion vector (engine_A - engine_G)
     State captures temporal context through tension dynamics
""")
    print("=" * 70)


if __name__ == '__main__':
    main()
