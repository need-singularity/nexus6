#!/usr/bin/env python3
"""Experiment: Repulsion Field on AUDIO Classification

Apply the repulsion field architecture to synthetic audio classification.
No downloads needed — all audio is generated synthetically.

5 classes of synthetic sounds:
  Class 0: Low frequency sine (200Hz)
  Class 1: Mid frequency sine (500Hz)
  Class 2: High frequency sine (1000Hz)
  Class 3: Chord (200+500Hz combined)
  Class 4: Noise (random)

Feature extraction: FFT magnitudes (first 100 bins)

Models compared:
  1. Dense baseline (100 -> hidden -> 5)
  2. RepulsionField 2-pole (A vs G)
  3. RepulsionQuad 4-pole (A|G x E|F)
  4. MetaFixed {1/2, 1/3, 1/6}

Music theory connection:
  ln(4/3) = 0.2877 appears in music (perfect 4th interval ratio)
  Does tension between engines relate to musical intervals?

Cross-domain check:
  Is MI efficiency ~ ln(2) for audio too?
  Does tension separate frequency classes?
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import math
import time

# ─────────────────────────────────────────
# Constants
# ─────────────────────────────────────────
SAMPLE_RATE = 8000
DURATION = 1.0
N_SAMPLES = int(SAMPLE_RATE * DURATION)  # 8000 points
# FFT bin resolution = SAMPLE_RATE / N_SAMPLES = 1 Hz/bin
# We need bins up to at least 1000Hz, so use first 1500 bins then downsample
N_FFT_BINS = 100  # final feature dimension (downsampled from full spectrum)
N_PER_CLASS = 100
N_CLASSES = 5

DIVISOR_RECIPROCALS = [1/2, 1/3, 1/6]  # perfect number 6

# Musical frequency pairs and their ratios
FREQ_PAIRS = {
    'unison':     (200, 200),    # 1:1
    'octave':     (200, 400),    # 2:1
    'fifth':      (200, 300),    # 3:2
    'fourth':     (200, 267),    # ~4:3
    'major_3rd':  (200, 250),    # 5:4
    'minor_3rd':  (200, 240),    # 6:5
    'tritone':    (200, 283),    # ~sqrt(2):1
}


# ─────────────────────────────────────────
# Synthetic Audio Generation
# ─────────────────────────────────────────

def generate_sine(freq, noise_level=0.1):
    """Generate a sine wave with noise."""
    t = np.linspace(0, DURATION, N_SAMPLES, endpoint=False)
    signal = np.sin(2 * np.pi * freq * t)
    signal += noise_level * np.random.randn(N_SAMPLES)
    return signal


def generate_chord(freqs, noise_level=0.1):
    """Generate a chord (sum of sines) with noise."""
    t = np.linspace(0, DURATION, N_SAMPLES, endpoint=False)
    signal = sum(np.sin(2 * np.pi * f * t) for f in freqs)
    signal /= len(freqs)  # normalize
    signal += noise_level * np.random.randn(N_SAMPLES)
    return signal


def generate_noise():
    """Generate random noise."""
    return np.random.randn(N_SAMPLES)


def extract_fft_features(signal):
    """Extract FFT magnitude features.

    FFT bin resolution = SAMPLE_RATE / N_SAMPLES = 1 Hz/bin for 8kHz/8000pts.
    Our signals are at 200, 500, 1000 Hz, so we need bins 0..~1500.
    We take the full spectrum up to Nyquist (4000 Hz), then downsample
    to N_FFT_BINS by averaging adjacent bins.
    """
    fft = np.fft.rfft(signal)
    magnitudes = np.abs(fft)  # 4001 bins (0 to 4000 Hz)

    # Log scale for better dynamic range
    magnitudes = np.log1p(magnitudes)

    # Downsample to N_FFT_BINS by averaging blocks
    n_total = len(magnitudes)
    block_size = n_total // N_FFT_BINS
    features = np.array([
        magnitudes[i * block_size:(i + 1) * block_size].mean()
        for i in range(N_FFT_BINS)
    ], dtype=np.float32)

    return features


def generate_dataset(n_per_class=N_PER_CLASS, noise_level=0.1):
    """Generate synthetic audio dataset.

    Classes:
      0: Low sine (200Hz)
      1: Mid sine (500Hz)
      2: High sine (1000Hz)
      3: Chord (200+500Hz)
      4: Noise
    """
    X, y = [], []

    for _ in range(n_per_class):
        # Class 0: Low frequency sine (200Hz)
        sig = generate_sine(200, noise_level)
        X.append(extract_fft_features(sig))
        y.append(0)

        # Class 1: Mid frequency sine (500Hz)
        sig = generate_sine(500, noise_level)
        X.append(extract_fft_features(sig))
        y.append(1)

        # Class 2: High frequency sine (1000Hz)
        sig = generate_sine(1000, noise_level)
        X.append(extract_fft_features(sig))
        y.append(2)

        # Class 3: Chord (200+500Hz)
        sig = generate_chord([200, 500], noise_level)
        X.append(extract_fft_features(sig))
        y.append(3)

        # Class 4: Noise
        sig = generate_noise()
        X.append(extract_fft_features(sig))
        y.append(4)

    X = np.array(X, dtype=np.float32)
    y = np.array(y, dtype=np.int64)

    # Normalize features
    mean = X.mean(axis=0)
    std = X.std(axis=0) + 1e-8
    X = (X - mean) / std

    return X, y, mean, std


def make_dataloaders(batch_size=32):
    """Create train/test dataloaders with consistent normalization."""
    # Generate training data
    np.random.seed(42)
    X_train, y_train, train_mean, train_std = generate_dataset(n_per_class=200, noise_level=0.05)

    # Generate test data (raw, unnormalized)
    np.random.seed(123)
    X_test_raw, y_test, _, _ = generate_dataset(n_per_class=50, noise_level=0.05)

    # Normalize test with TRAIN stats (undo test normalization, apply train)
    # generate_dataset already normalized X_test_raw with its own stats,
    # so we need raw features. Re-generate without normalization.
    np.random.seed(123)
    X_test_unnorm, y_test, test_mean, test_std = generate_dataset(n_per_class=50, noise_level=0.05)
    # Undo test normalization
    X_test_raw = X_test_unnorm * test_std + test_mean  # back to raw
    # Apply train normalization
    X_test = (X_test_raw - train_mean) / train_std

    train_ds = torch.utils.data.TensorDataset(
        torch.tensor(X_train), torch.tensor(y_train)
    )
    test_ds = torch.utils.data.TensorDataset(
        torch.tensor(X_test.astype(np.float32)), torch.tensor(y_test)
    )

    train_loader = torch.utils.data.DataLoader(train_ds, batch_size=batch_size, shuffle=True)
    test_loader = torch.utils.data.DataLoader(test_ds, batch_size=batch_size, shuffle=False)

    return train_loader, test_loader


# ─────────────────────────────────────────
# Models
# ─────────────────────────────────────────

class AudioDense(nn.Module):
    """Simple dense baseline for audio classification."""
    def __init__(self, input_dim=N_FFT_BINS, hidden_dim=64, output_dim=N_CLASSES):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(hidden_dim, output_dim),
        )

    def forward(self, x):
        return self.net(x)


class AudioRepulsionField(nn.Module):
    """Repulsion field (2-pole) for audio classification.

    Engine+ (pole_plus): excitatory — generates broad predictions
    Engine- (pole_minus): inhibitory — corrects and sharpens

    Output = equilibrium + tension_scale * sqrt(tension) * field_direction

    Tension measures disagreement between poles.
    """
    def __init__(self, input_dim=N_FFT_BINS, hidden_dim=64, output_dim=N_CLASSES):
        super().__init__()
        self.pole_plus = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(hidden_dim, output_dim),
        )
        self.pole_minus = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(hidden_dim, output_dim),
        )
        self.field_transform = nn.Sequential(
            nn.Linear(output_dim, output_dim),
            nn.Tanh(),
        )
        # Initial tension scale = 1/3 (meta fixed point)
        self.tension_scale = nn.Parameter(torch.tensor(1/3))
        self.tension_magnitude = 0.0

    def forward(self, x):
        out_plus = self.pole_plus(x)
        out_minus = self.pole_minus(x)

        repulsion = out_plus - out_minus
        tension = (repulsion ** 2).sum(dim=-1, keepdim=True)

        equilibrium = (out_plus + out_minus) / 2
        field_direction = self.field_transform(repulsion)
        output = equilibrium + self.tension_scale * torch.sqrt(tension + 1e-8) * field_direction

        with torch.no_grad():
            self.tension_magnitude = tension.mean().item()

        return output


class AudioRepulsionQuad(nn.Module):
    """4-pole repulsion field for audio.

    Axis 1: Content (A vs G) — generation vs correction
    Axis 2: Structure (E vs F) — exploration vs constraint
    """
    def __init__(self, input_dim=N_FFT_BINS, hidden_dim=64, output_dim=N_CLASSES):
        super().__init__()
        self.head_a = nn.Sequential(
            nn.Linear(input_dim, hidden_dim), nn.ReLU(), nn.Dropout(0.3),
            nn.Linear(hidden_dim, output_dim),
        )
        self.head_g = nn.Sequential(
            nn.Linear(input_dim, hidden_dim), nn.ReLU(), nn.Dropout(0.3),
            nn.Linear(hidden_dim, output_dim),
        )
        self.head_e = nn.Sequential(
            nn.Linear(input_dim, hidden_dim), nn.ReLU(), nn.Dropout(0.3),
            nn.Linear(hidden_dim, output_dim),
        )
        self.head_f = nn.Sequential(
            nn.Linear(input_dim, hidden_dim), nn.ReLU(), nn.Dropout(0.3),
            nn.Linear(hidden_dim, output_dim),
        )
        self.field_transform = nn.Sequential(
            nn.Linear(output_dim * 2, output_dim),
            nn.Tanh(),
        )
        self.tension_scale = nn.Parameter(torch.tensor(1/3))
        self.tension_content = 0.0
        self.tension_structure = 0.0

    def forward(self, x):
        out_a = self.head_a(x)
        out_g = self.head_g(x)
        out_e = self.head_e(x)
        out_f = self.head_f(x)

        repulsion_content = out_a - out_g
        repulsion_structure = out_e - out_f

        t_content = (repulsion_content ** 2).sum(dim=-1, keepdim=True)
        t_structure = (repulsion_structure ** 2).sum(dim=-1, keepdim=True)

        equilibrium = (out_a + out_g + out_e + out_f) / 4
        combined_repulsion = torch.cat([repulsion_content, repulsion_structure], dim=-1)
        field_direction = self.field_transform(combined_repulsion)

        total_tension = torch.sqrt((t_content * t_structure) + 1e-8)
        output = equilibrium + self.tension_scale * torch.sqrt(total_tension + 1e-8) * field_direction

        with torch.no_grad():
            self.tension_content = t_content.mean().item()
            self.tension_structure = t_structure.mean().item()

        return output


class AudioMetaFixed(nn.Module):
    """3-head model with {1/2, 1/3, 1/6} initial weights.

    Uses perfect number 6's divisor reciprocals as initial combination weights.
    Weights are learnable (softmax-normalized).
    """
    def __init__(self, input_dim=N_FFT_BINS, hidden_dim=64, output_dim=N_CLASSES):
        super().__init__()
        self.head_a = nn.Sequential(
            nn.Linear(input_dim, hidden_dim), nn.ReLU(), nn.Dropout(0.3),
            nn.Linear(hidden_dim, output_dim),
        )
        self.head_b = nn.Sequential(
            nn.Linear(input_dim, hidden_dim), nn.ReLU(), nn.Dropout(0.3),
            nn.Linear(hidden_dim, output_dim),
        )
        self.head_c = nn.Sequential(
            nn.Linear(input_dim, hidden_dim), nn.ReLU(), nn.Dropout(0.3),
            nn.Linear(hidden_dim, output_dim),
        )
        init_weights = torch.tensor(DIVISOR_RECIPROCALS, dtype=torch.float)
        self.weights = nn.Parameter(init_weights)

    def forward(self, x):
        out_a = self.head_a(x)
        out_b = self.head_b(x)
        out_c = self.head_c(x)
        w = F.softmax(self.weights, dim=0)
        return w[0] * out_a + w[1] * out_b + w[2] * out_c

    def get_weights(self):
        with torch.no_grad():
            return F.softmax(self.weights, dim=0).cpu().numpy()


# ─────────────────────────────────────────
# Training
# ─────────────────────────────────────────

def count_params(model):
    return sum(p.numel() for p in model.parameters())


def train_model(model, train_loader, test_loader, epochs=50, lr=0.001):
    """Train and evaluate a model. Returns losses, accs, per-epoch tension."""
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    criterion = nn.CrossEntropyLoss()

    train_losses = []
    test_accs = []
    tensions = []

    for epoch in range(epochs):
        model.train()
        total_loss = 0
        for X, y in train_loader:
            optimizer.zero_grad()
            out = model(X)
            loss = criterion(out, y)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()

        avg_loss = total_loss / len(train_loader)
        train_losses.append(avg_loss)

        model.eval()
        correct = total = 0
        with torch.no_grad():
            for X, y in test_loader:
                out = model(X)
                correct += (out.argmax(1) == y).sum().item()
                total += y.size(0)
        acc = correct / total
        test_accs.append(acc)

        # Record tension if available
        t = getattr(model, 'tension_magnitude', None)
        tensions.append(t)

        if (epoch + 1) % 10 == 0 or epoch == 0:
            t_str = f", T={t:.4f}" if t is not None else ""
            print(f"    Epoch {epoch+1:>2}/{epochs}: Loss={avg_loss:.4f}, Acc={acc*100:.1f}%{t_str}")

    return train_losses, test_accs, tensions


def per_class_accuracy(model, test_loader):
    """Compute per-class accuracy."""
    correct = [0] * N_CLASSES
    total = [0] * N_CLASSES
    model.eval()
    with torch.no_grad():
        for X, y in test_loader:
            out = model(X)
            preds = out.argmax(1)
            for c in range(N_CLASSES):
                mask = (y == c)
                total[c] += mask.sum().item()
                correct[c] += ((preds == c) & mask).sum().item()
    return {c: correct[c] / max(total[c], 1) for c in range(N_CLASSES)}


def per_class_tension(model, test_loader):
    """Measure tension per class (repulsion models only)."""
    if not hasattr(model, 'pole_plus'):
        return None

    tensions = {c: [] for c in range(N_CLASSES)}
    model.eval()
    with torch.no_grad():
        for X, y in test_loader:
            out_plus = model.pole_plus(X)
            out_minus = model.pole_minus(X)
            repulsion = out_plus - out_minus
            tension = (repulsion ** 2).sum(dim=-1)  # per-sample tension
            for i in range(len(y)):
                tensions[y[i].item()].append(tension[i].item())

    return {c: np.mean(tensions[c]) if tensions[c] else 0 for c in range(N_CLASSES)}


# ─────────────────────────────────────────
# Music Theory Analysis
# ─────────────────────────────────────────

def music_theory_analysis(model, noise_level=0.1):
    """Analyze tension for musical interval pairs.

    ln(4/3) = 0.2877 is the golden zone width AND the perfect 4th ratio log.
    Does tension correlate with musical consonance/dissonance?
    """
    print("\n  Musical Interval Tension Analysis:")
    print(f"  {'Interval':<14} {'Freq Pair':>14} {'Ratio':>8} {'ln(ratio)':>10} {'Tension':>10}")
    print("  " + "-" * 60)

    if not hasattr(model, 'pole_plus'):
        print("  (Model has no poles, skipping)")
        return {}

    results = {}
    np.random.seed(999)

    for name, (f1, f2) in FREQ_PAIRS.items():
        # Generate 50 samples of this interval
        tensions = []
        for _ in range(50):
            sig = generate_chord([f1, f2], noise_level)
            feat = extract_fft_features(sig)
            # Normalize (use rough normalization)
            feat = (feat - feat.mean()) / (feat.std() + 1e-8)
            x = torch.tensor(feat, dtype=torch.float32).unsqueeze(0)

            model.eval()
            with torch.no_grad():
                out_plus = model.pole_plus(x)
                out_minus = model.pole_minus(x)
                repulsion = out_plus - out_minus
                t = (repulsion ** 2).sum().item()
                tensions.append(t)

        mean_tension = np.mean(tensions)
        ratio = max(f1, f2) / min(f1, f2)
        log_ratio = math.log(ratio)
        results[name] = {
            'freqs': (f1, f2),
            'ratio': ratio,
            'log_ratio': log_ratio,
            'tension': mean_tension,
        }
        print(f"  {name:<14} {f1:>6}+{f2:<6} {ratio:>8.3f} {log_ratio:>10.4f} {mean_tension:>10.4f}")

    # Check if tension correlates with dissonance
    # Consonant intervals (unison, octave, fifth) should have LOWER tension
    # Dissonant intervals (tritone) should have HIGHER tension
    if results:
        consonant = ['unison', 'octave', 'fifth']
        dissonant = ['tritone', 'minor_3rd']
        cons_t = np.mean([results[n]['tension'] for n in consonant if n in results])
        diss_t = np.mean([results[n]['tension'] for n in dissonant if n in results])

        print(f"\n  Consonant mean tension:  {cons_t:.4f}")
        print(f"  Dissonant mean tension:  {diss_t:.4f}")
        print(f"  Ratio (diss/cons):       {diss_t/cons_t:.4f}" if cons_t > 0 else "")

        # ln(4/3) connection
        ln43 = math.log(4/3)
        print(f"\n  ln(4/3) = {ln43:.4f} (golden zone width = perfect 4th log-ratio)")
        fourth_t = results.get('fourth', {}).get('tension', 0)
        print(f"  Perfect 4th tension:     {fourth_t:.4f}")

    return results


# ─────────────────────────────────────────
# Cross-Domain Analysis
# ─────────────────────────────────────────

def cross_domain_analysis(results):
    """Check cross-domain constants.

    From MNIST/CIFAR experiments:
      - MI efficiency ~ ln(2) = 0.693
      - Tension scale converges to ~ 1/3

    Do the same constants appear in audio?
    """
    print("\n  Cross-Domain Constant Check:")
    print("  " + "-" * 50)

    ln2 = math.log(2)
    ln43 = math.log(4/3)
    one_third = 1/3
    one_e = 1/math.e

    for name, r in results.items():
        if 'tension_scale' in r:
            ts = r['tension_scale']
            print(f"\n  {name}:")
            print(f"    Tension scale:     {ts:.4f}")
            print(f"    vs 1/3:            {abs(ts - one_third):.4f} (delta)")
            print(f"    vs 1/e:            {abs(ts - one_e):.4f} (delta)")

        if 'final_tension' in r:
            ft = r['final_tension']
            print(f"    Final tension:     {ft:.4f}")
            print(f"    vs ln(2):          {abs(ft - ln2):.4f} (delta)")
            print(f"    vs ln(4/3):        {abs(ft - ln43):.4f} (delta)")

    # MI efficiency estimation (rough)
    # Use accuracy improvement per parameter as proxy
    if 'Dense' in results and 'Repulsion' in results:
        dense_acc = results['Dense']['acc']
        rep_acc = results['Repulsion']['acc']
        dense_p = results['Dense']['params']
        rep_p = results['Repulsion']['params']

        if rep_p > dense_p:
            efficiency = (rep_acc - dense_acc) / ((rep_p - dense_p) / dense_p)
            print(f"\n  MI efficiency proxy:")
            print(f"    (RepulsionAcc - DenseAcc) / (param overhead ratio)")
            print(f"    = ({rep_acc*100:.1f}% - {dense_acc*100:.1f}%) / ({(rep_p-dense_p)/dense_p:.3f})")
            print(f"    = {efficiency*100:.4f}")
            print(f"    ln(2) = {ln2:.4f}")


# ─────────────────────────────────────────
# Tension-Accuracy Correlation
# ─────────────────────────────────────────

def tension_accuracy_correlation(accs_over_time, tensions_over_time):
    """Compute correlation between tension and accuracy over training."""
    if tensions_over_time[0] is None:
        return None, None

    valid = [(a, t) for a, t in zip(accs_over_time, tensions_over_time) if t is not None]
    if len(valid) < 3:
        return None, None

    accs_arr = np.array([v[0] for v in valid])
    tens_arr = np.array([v[1] for v in valid])

    # Pearson correlation
    if tens_arr.std() < 1e-10 or accs_arr.std() < 1e-10:
        return 0.0, 1.0

    corr = np.corrcoef(accs_arr, tens_arr)[0, 1]

    # Simple p-value approximation (Fisher transform)
    n = len(valid)
    if abs(corr) > 0.999:
        p_val = 0.0
    else:
        z = 0.5 * math.log((1 + corr) / (1 - corr))
        se = 1 / math.sqrt(n - 3) if n > 3 else float('inf')
        p_val = 2 * (1 - 0.5 * (1 + math.erf(abs(z / se) / math.sqrt(2))))

    return corr, p_val


# ─────────────────────────────────────────
# Main
# ─────────────────────────────────────────

def main():
    print()
    print("=" * 70)
    print("   logout -- Audio Repulsion Field Experiment")
    print("   Synthetic audio classification (5 classes)")
    print("   Does the repulsion field generalize to audio domain?")
    print("=" * 70)

    # ── Generate Data ──
    print("\n[0] Generating synthetic audio dataset...")
    train_loader, test_loader = make_dataloaders()
    n_train = len(train_loader.dataset)
    n_test = len(test_loader.dataset)
    print(f"    Train: {n_train} samples, Test: {n_test} samples")
    print(f"    Features: {N_FFT_BINS} FFT magnitude bins")
    print(f"    Classes: 200Hz, 500Hz, 1000Hz, Chord(200+500), Noise")

    epochs = 50
    lr = 0.001
    n_trials = 3
    all_results = {}

    class_names = ['200Hz', '500Hz', '1000Hz', 'Chord', 'Noise']

    models_to_test = [
        ('Dense', AudioDense),
        ('Repulsion', AudioRepulsionField),
        ('RepulsionQuad', AudioRepulsionQuad),
        ('Meta{1/2,1/3,1/6}', AudioMetaFixed),
    ]

    # ── Train all models ──
    for model_name, model_cls in models_to_test:
        print(f"\n{'='*60}")
        print(f"  [{model_name}] Training ({n_trials} trials, {epochs} epochs each)")
        print(f"{'='*60}")

        trial_results = []
        for trial in range(n_trials):
            torch.manual_seed(42 + trial * 100)
            np.random.seed(42 + trial * 100)

            model = model_cls()
            params = count_params(model)

            if trial == 0:
                print(f"  Parameters: {params:,}")

            print(f"\n  --- Trial {trial+1}/{n_trials} ---")
            losses, accs, tensions = train_model(model, train_loader, test_loader, epochs, lr)

            # Per-class accuracy
            cls_acc = per_class_accuracy(model, test_loader)

            # Per-class tension (repulsion models only)
            cls_tension = per_class_tension(model, test_loader)

            # Tension-accuracy correlation
            corr, p_val = tension_accuracy_correlation(accs, tensions)

            trial_data = {
                'acc': accs[-1],
                'loss': losses[-1],
                'params': params,
                'accs': accs,
                'losses': losses,
                'tensions': tensions,
                'cls_acc': cls_acc,
                'cls_tension': cls_tension,
                'tension_acc_corr': corr,
                'tension_acc_pval': p_val,
            }

            # Model-specific data
            if hasattr(model, 'tension_magnitude'):
                trial_data['final_tension'] = model.tension_magnitude
            if hasattr(model, 'tension_scale'):
                trial_data['tension_scale'] = model.tension_scale.item()
            if hasattr(model, 'tension_content'):
                trial_data['tension_content'] = model.tension_content
                trial_data['tension_structure'] = model.tension_structure
            if hasattr(model, 'get_weights'):
                trial_data['learned_weights'] = model.get_weights()

            trial_results.append(trial_data)

            # Keep last model for music analysis
            if trial == n_trials - 1:
                trial_data['model'] = model

        all_results[model_name] = trial_results

    # ─────────────────────────────────────────
    # Results Summary
    # ─────────────────────────────────────────
    print("\n\n")
    print("=" * 75)
    print("   RESULTS SUMMARY (averaged over 3 trials)")
    print("=" * 75)

    summary = {}
    for name, trials in all_results.items():
        accs = [t['acc'] for t in trials]
        losses = [t['loss'] for t in trials]
        summary[name] = {
            'acc_mean': np.mean(accs),
            'acc_std': np.std(accs),
            'loss_mean': np.mean(losses),
            'params': trials[0]['params'],
        }

    print(f"\n  {'Model':<25} {'Accuracy':>20} {'Loss':>10} {'Params':>10}")
    print("  " + "-" * 68)
    best_acc = max(s['acc_mean'] for s in summary.values())
    for name in ['Dense', 'Repulsion', 'RepulsionQuad', 'Meta{1/2,1/3,1/6}']:
        s = summary[name]
        marker = ' <-- best' if s['acc_mean'] == best_acc else ''
        print(f"  {name:<25} {s['acc_mean']*100:>7.2f}% +/- {s['acc_std']*100:.2f}% "
              f"{s['loss_mean']:>8.4f} {s['params']:>10,}{marker}")

    # ─────────────────────────────────────────
    # Per-Class Accuracy
    # ─────────────────────────────────────────
    print(f"\n\n  Per-Class Accuracy (last trial):")
    print(f"  {'Class':<12}", end="")
    for name in ['Dense', 'Repulsion', 'RepulsionQuad', 'Meta{1/2,1/3,1/6}']:
        print(f" {name:>12}", end="")
    print()
    print("  " + "-" * 62)
    for c in range(N_CLASSES):
        print(f"  {class_names[c]:<12}", end="")
        for name in ['Dense', 'Repulsion', 'RepulsionQuad', 'Meta{1/2,1/3,1/6}']:
            acc = all_results[name][-1]['cls_acc'][c]
            print(f" {acc*100:>11.1f}%", end="")
        print()

    # ─────────────────────────────────────────
    # Tension Analysis
    # ─────────────────────────────────────────
    print(f"\n\n  Tension Analysis:")
    print("  " + "-" * 60)

    # Per-class tension for repulsion model
    rep_trials = all_results['Repulsion']
    cls_tension = rep_trials[-1]['cls_tension']
    if cls_tension:
        print(f"\n  Per-Class Tension (Repulsion 2-pole, last trial):")
        print(f"  {'Class':<12} {'Tension':>10}")
        print("  " + "-" * 24)
        for c in range(N_CLASSES):
            print(f"  {class_names[c]:<12} {cls_tension[c]:>10.4f}")

        # Which class has highest tension?
        max_t_class = max(cls_tension, key=cls_tension.get)
        min_t_class = min(cls_tension, key=cls_tension.get)
        print(f"\n  Highest tension: Class {max_t_class} ({class_names[max_t_class]}) = {cls_tension[max_t_class]:.4f}")
        print(f"  Lowest tension:  Class {min_t_class} ({class_names[min_t_class]}) = {cls_tension[min_t_class]:.4f}")
        print(f"  Ratio (max/min): {cls_tension[max_t_class]/max(cls_tension[min_t_class], 1e-8):.2f}x")

    # Tension scale convergence
    print(f"\n  Tension Scale Convergence:")
    for name in ['Repulsion', 'RepulsionQuad']:
        scales = [t.get('tension_scale', None) for t in all_results[name]]
        scales = [s for s in scales if s is not None]
        if scales:
            mean_s = np.mean(scales)
            print(f"  {name:<20} scale = {mean_s:.4f} (init=0.3333, delta={abs(mean_s - 1/3):.4f})")

    # Tension-Accuracy Correlation
    print(f"\n  Tension-Accuracy Correlation:")
    for name in ['Repulsion', 'RepulsionQuad']:
        corrs = [t['tension_acc_corr'] for t in all_results[name] if t['tension_acc_corr'] is not None]
        if corrs:
            mean_corr = np.mean(corrs)
            print(f"  {name:<20} r = {mean_corr:>+.4f} ({'positive' if mean_corr > 0 else 'negative'} correlation)")

    # Quad-specific: content vs structure tension
    quad_trials = all_results['RepulsionQuad']
    print(f"\n  RepulsionQuad Axis Tensions (last trial):")
    tc = quad_trials[-1].get('tension_content', 0)
    ts = quad_trials[-1].get('tension_structure', 0)
    print(f"    Content tension (A vs G):   {tc:.4f}")
    print(f"    Structure tension (E vs F): {ts:.4f}")
    if tc > 0 and ts > 0:
        print(f"    Ratio (content/structure):  {tc/ts:.4f}")

    # ─────────────────────────────────────────
    # Music Theory Connection
    # ─────────────────────────────────────────
    print("\n\n" + "=" * 70)
    print("   MUSIC THEORY CONNECTION")
    print("   ln(4/3) = 0.2877 = golden zone width = perfect 4th log-ratio")
    print("=" * 70)

    rep_model = all_results['Repulsion'][-1].get('model')
    if rep_model:
        interval_results = music_theory_analysis(rep_model)

    # ─────────────────────────────────────────
    # MetaFixed Weight Analysis
    # ─────────────────────────────────────────
    print(f"\n\n  MetaFixed {{1/2, 1/3, 1/6}} Weight Analysis:")
    print("  " + "-" * 50)
    print(f"  {'Trial':<10} {'w1':>8} {'w2':>8} {'w3':>8} {'L2 drift':>10}")
    print("  " + "-" * 50)
    meta_trials = all_results['Meta{1/2,1/3,1/6}']
    drifts = []
    for i, t in enumerate(meta_trials):
        w = t.get('learned_weights')
        if w is not None:
            drift = np.sqrt(sum((a - b) ** 2 for a, b in zip(w, [0.5, 1/3, 1/6])))
            drifts.append(drift)
            print(f"  Trial {i+1:<4} {w[0]:>8.4f} {w[1]:>8.4f} {w[2]:>8.4f} {drift:>10.4f}")
    print(f"  Init      {'0.5000':>8} {'0.3333':>8} {'0.1667':>8}")
    if drifts:
        print(f"  Mean drift: {np.mean(drifts):.4f}")
        print(f"  {'Stable (drift < 0.1)' if np.mean(drifts) < 0.1 else 'Significant drift'}")

    # ─────────────────────────────────────────
    # Cross-Domain Constants
    # ─────────────────────────────────────────
    print("\n\n" + "=" * 70)
    print("   CROSS-DOMAIN CONSTANT CHECK")
    print("   Same constants in audio as in MNIST/CIFAR?")
    print("=" * 70)

    cross_data = {}
    for name, trials in all_results.items():
        t = trials[-1]
        cross_data[name] = {
            'acc': t['acc'],
            'params': t['params'],
        }
        if 'tension_scale' in t:
            cross_data[name]['tension_scale'] = t['tension_scale']
        if 'final_tension' in t:
            cross_data[name]['final_tension'] = t['final_tension']

    cross_domain_analysis(cross_data)

    # ─────────────────────────────────────────
    # Training Curves
    # ─────────────────────────────────────────
    print(f"\n\n  Training Curves (last trial, accuracy at checkpoints):")
    checkpoints = [0, 9, 19, 29, 39, 49]
    print(f"  {'Model':<25}", end="")
    for cp in checkpoints:
        print(f" {'E'+str(cp+1):>6}", end="")
    print()
    print("  " + "-" * 65)
    for name in ['Dense', 'Repulsion', 'RepulsionQuad', 'Meta{1/2,1/3,1/6}']:
        accs = all_results[name][-1]['accs']
        print(f"  {name:<25}", end="")
        for cp in checkpoints:
            if cp < len(accs):
                print(f" {accs[cp]*100:>5.1f}%", end="")
            else:
                print(f"   N/A", end="")
        print()

    # ─────────────────────────────────────────
    # Tension Over Training (ASCII graph)
    # ─────────────────────────────────────────
    rep_tensions = all_results['Repulsion'][-1]['tensions']
    valid_tensions = [t for t in rep_tensions if t is not None]
    if valid_tensions:
        print(f"\n\n  Repulsion Tension Over Training (last trial):")
        t_min = min(valid_tensions)
        t_max = max(valid_tensions)
        width = 40
        for i, t in enumerate(valid_tensions):
            if (i % 5 == 0) or i == len(valid_tensions) - 1:
                bar_len = int((t - t_min) / max(t_max - t_min, 1e-8) * width)
                bar = '#' * max(bar_len, 1)
                print(f"    E{i+1:>2} |{bar:<{width}}| {t:.4f}")

    # ─────────────────────────────────────────
    # Frequency Pair Tension (which pairs cause most disagreement?)
    # ─────────────────────────────────────────
    print(f"\n\n  Which frequency PAIRS cause most pole disagreement?")
    print("  (Higher tension = poles disagree more = harder to classify)")
    if cls_tension:
        # Class 3 (chord) vs pure tones
        chord_t = cls_tension[3]
        pure_avg = np.mean([cls_tension[c] for c in [0, 1, 2]])
        noise_t = cls_tension[4]
        print(f"    Pure tones avg tension:   {pure_avg:.4f}")
        print(f"    Chord (200+500) tension:  {chord_t:.4f}")
        print(f"    Noise tension:            {noise_t:.4f}")
        print(f"    Chord/Pure ratio:         {chord_t/max(pure_avg, 1e-8):.2f}x")
        print(f"    Noise/Pure ratio:         {noise_t/max(pure_avg, 1e-8):.2f}x")

    # ─────────────────────────────────────────
    # Final Verdict
    # ─────────────────────────────────────────
    print("\n\n" + "=" * 70)
    print("   VERDICT: Audio Repulsion Field")
    print("=" * 70)

    dense_mean = summary['Dense']['acc_mean']
    rep_mean = summary['Repulsion']['acc_mean']
    quad_mean = summary['RepulsionQuad']['acc_mean']
    meta_mean = summary['Meta{1/2,1/3,1/6}']['acc_mean']

    print(f"\n  Dense baseline:    {dense_mean*100:.2f}%")
    print(f"  Repulsion 2-pole:  {rep_mean*100:.2f}% ({(rep_mean-dense_mean)*100:+.2f}%)")
    print(f"  Repulsion 4-pole:  {quad_mean*100:.2f}% ({(quad_mean-dense_mean)*100:+.2f}%)")
    print(f"  Meta {{1/2,1/3,1/6}}: {meta_mean*100:.2f}% ({(meta_mean-dense_mean)*100:+.2f}%)")

    best_name = max(summary.items(), key=lambda x: x[1]['acc_mean'])[0]
    print(f"\n  Best model: {best_name}")

    # Key questions
    print(f"\n  Q1: Does repulsion field generalize to audio?")
    best_rep = max(rep_mean, quad_mean)
    best_rep_name = "RepulsionQuad" if quad_mean > rep_mean else "Repulsion"
    if best_rep > dense_mean:
        print(f"      YES - {best_rep_name} beats Dense by {(best_rep-dense_mean)*100:+.2f}%")
    elif rep_mean > dense_mean:
        print(f"      YES - Repulsion beats Dense by {(rep_mean-dense_mean)*100:+.2f}%")
    else:
        print(f"      NO  - Dense wins by {(dense_mean-rep_mean)*100:+.2f}%")

    print(f"\n  Q2: Does tension separate frequency classes?")
    if cls_tension:
        t_values = list(cls_tension.values())
        t_range = max(t_values) - min(t_values)
        t_mean = np.mean(t_values)
        cv = t_range / max(t_mean, 1e-8)
        print(f"      Tension range: {t_range:.4f}, CV: {cv:.4f}")
        print(f"      {'YES - significant separation' if cv > 0.3 else 'WEAK - tension relatively uniform'}")

    print(f"\n  Q3: ln(4/3) connection to audio tension?")
    ln43 = math.log(4/3)
    print(f"      ln(4/3) = {ln43:.4f}")
    if 'tension_scale' in all_results['Repulsion'][-1]:
        ts = all_results['Repulsion'][-1]['tension_scale']
        print(f"      Tension scale = {ts:.4f}")
        print(f"      Delta from ln(4/3): {abs(ts - ln43):.4f}")
        print(f"      Delta from 1/3:     {abs(ts - 1/3):.4f}")

    print(f"\n  Q4: Does {{1/2, 1/3, 1/6}} maintain advantage?")
    if meta_mean >= max(rep_mean, quad_mean, dense_mean):
        print(f"      YES - Meta fixed is best or tied for best")
    else:
        print(f"      NO  - {best_name} wins")

    print()


if __name__ == '__main__':
    main()
