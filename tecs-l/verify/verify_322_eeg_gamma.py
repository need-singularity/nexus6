#!/usr/bin/env python3
"""Hypothesis 322 Verification: EEG Gamma Oscillations = Repulsion Field Tension (Synthetic EEG Experiment)

Phase 1: Generate synthetic EEG for 5 brain states → Extract bandpower → Train repulsion field
→ Measure correlation between tension and gamma power
→ Compare tension distribution across consciousness levels
"""

import numpy as np
from scipy import signal as sp_signal
from scipy import stats

print("=" * 70)
print("Hypothesis 322 Verification: EEG Gamma Oscillations = Repulsion Field Tension")
print("Phase 1: Synthetic EEG + Repulsion Field Experiment")
print("=" * 70)

# ─────────────────────────────────────────────
# 1. Synthetic EEG Generation (based on eeg_cct_validator.py)
# ─────────────────────────────────────────────

FS = 256
SEED = 42
EPOCH_SEC = 2.0
EPOCH_SAMPLES = int(FS * EPOCH_SEC)
N_EPOCHS = 200  # 200 epochs per state

rng = np.random.default_rng(SEED)


def generate_1f_noise(n, fs, rng, exponent=1.0):
    freqs = np.fft.rfftfreq(n, d=1.0 / fs)
    freqs[0] = 1.0
    amplitudes = 1.0 / (freqs ** (exponent / 2.0))
    phases = rng.uniform(0, 2 * np.pi, len(freqs))
    spectrum = amplitudes * np.exp(1j * phases)
    spectrum[0] = 0
    noise = np.fft.irfft(spectrum, n=n)
    return noise / (np.std(noise) + 1e-15)


def generate_oscillation(n, fs, freq, amplitude, rng, phase_jitter=0.0):
    t = np.arange(n) / fs
    phase = 2 * np.pi * freq * t
    if phase_jitter > 0:
        walk = np.cumsum(rng.normal(0, phase_jitter, n))
        phase += walk
    return amplitude * np.sin(phase)


def synthesize_state(state, n, fs, rng):
    """Generate synthetic EEG for each brain state."""
    if state == "awake":
        theta = generate_oscillation(n, fs, 6.0, 10.0, rng, 0.02)
        alpha = generate_oscillation(n, fs, 10.0, 25.0, rng, 0.03)
        beta = generate_oscillation(n, fs, 22.0, 15.0, rng, 0.02)
        gamma = generate_oscillation(n, fs, 42.0, 8.0, rng, 0.01)
        pink = generate_1f_noise(n, fs, rng, 1.0) * 12.0
        return theta + alpha + beta + gamma + pink

    elif state == "sleep_n1":
        theta = generate_oscillation(n, fs, 5.0, 35.0, rng, 0.02)
        alpha = generate_oscillation(n, fs, 10.0, 10.0, rng, 0.01)
        gamma = generate_oscillation(n, fs, 40.0, 1.5, rng, 0.005)
        pink = generate_1f_noise(n, fs, rng, 1.2) * 8.0
        return theta + alpha + gamma + pink

    elif state == "sleep_n3":
        delta1 = generate_oscillation(n, fs, 1.0, 100.0, rng, 0.001)
        delta2 = generate_oscillation(n, fs, 2.0, 50.0, rng, 0.001)
        gamma = generate_oscillation(n, fs, 40.0, 0.3, rng, 0.001)
        pink = generate_1f_noise(n, fs, rng, 2.0) * 2.0
        return delta1 + delta2 + gamma + pink

    elif state == "anesthesia":
        delta = generate_oscillation(n, fs, 1.0, 80.0, rng, 0.001)
        # burst-suppression mask
        mask = np.ones(n)
        i = 0
        suppressed = False
        while i < n:
            if suppressed:
                dur = int(rng.uniform(1.5, 3.0) * fs)
                end = min(i + dur, n)
                mask[i:end] = 0.0
                i = end
            else:
                dur = int(rng.uniform(0.5, 1.5) * fs)
                i = min(i + dur, n)
            suppressed = not suppressed
        return delta * mask + rng.normal(0, 0.5, n)

    elif state == "rem":
        theta = generate_oscillation(n, fs, 5.5, 30.0, rng, 0.03)
        beta = generate_oscillation(n, fs, 20.0, 8.0, rng, 0.02)
        gamma = generate_oscillation(n, fs, 40.0, 4.0, rng, 0.01)
        pink = generate_1f_noise(n, fs, rng, 1.1) * 10.0
        return theta + beta + gamma + pink


STATES = ["awake", "rem", "sleep_n1", "sleep_n3", "anesthesia"]
STATE_NAMES = {
    "awake": "Awake (conscious)",
    "rem": "REM (dream)",
    "sleep_n1": "N1 (drowsy)",
    "sleep_n3": "N3 (deep sleep)",
    "anesthesia": "Anesthesia",
}
# Consciousness level order (high→low)
CONSCIOUSNESS_ORDER = {"awake": 5, "rem": 4, "sleep_n1": 3, "sleep_n3": 2, "anesthesia": 1}

print("\nGenerating synthetic EEG for each state...")
all_features = []
all_labels = []
all_gamma_power = []
all_consciousness = []

for state in STATES:
    for ep in range(N_EPOCHS):
        eeg = synthesize_state(state, EPOCH_SAMPLES, FS, rng)

        # ─────────────────────────────────────────────
        # 2. Extract bandpower (FFT)
        # ─────────────────────────────────────────────
        freqs_fft = np.fft.rfftfreq(EPOCH_SAMPLES, d=1.0/FS)
        fft_vals = np.abs(np.fft.rfft(eeg)) ** 2 / EPOCH_SAMPLES

        # Calculate bandpower
        def band_power(f_low, f_high):
            mask = (freqs_fft >= f_low) & (freqs_fft < f_high)
            return np.mean(fft_vals[mask]) if np.any(mask) else 0.0

        delta_p = band_power(0.5, 4.0)
        theta_p = band_power(4.0, 8.0)
        alpha_p = band_power(8.0, 13.0)
        beta_p = band_power(13.0, 30.0)
        gamma_p = band_power(30.0, 100.0)
        total_p = delta_p + theta_p + alpha_p + beta_p + gamma_p + 1e-15

        # Feature vector: relative bandpower + ratios
        gamma_ratio = gamma_p / total_p
        theta_beta = theta_p / (beta_p + 1e-15)

        # Spectral entropy
        psd_norm = fft_vals / (np.sum(fft_vals) + 1e-15)
        psd_norm = psd_norm[psd_norm > 0]
        spectral_entropy = -np.sum(psd_norm * np.log2(psd_norm + 1e-15))

        features = np.array([
            delta_p, theta_p, alpha_p, beta_p, gamma_p,
            spectral_entropy, gamma_ratio, theta_beta
        ])
        features_log = np.log1p(features)  # log scale for better separation

        all_features.append(features_log)
        all_labels.append(state)
        all_gamma_power.append(gamma_p)
        all_consciousness.append(CONSCIOUSNESS_ORDER[state])

X = np.array(all_features)
y_labels = np.array(all_labels)
y_gamma = np.array(all_gamma_power)
y_consciousness = np.array(all_consciousness)

print(f"  Total epochs: {len(X)} ({N_EPOCHS} x {len(STATES)} states)")
print(f"  Feature dimensions: {X.shape[1]}")

# ─────────────────────────────────────────────
# 3. Train Repulsive Field Engine
# ─────────────────────────────────────────────

print("\n" + "─" * 70)
print("3. Training Repulsive Field Engine")
print("─" * 70)


class SimpleEngine:
    """Simple linear engine (W*x + b → softmax)."""
    def __init__(self, n_features, n_classes, rng, lr=0.01):
        self.W = rng.normal(0, 0.1, (n_features, n_classes))
        self.b = np.zeros(n_classes)
        self.lr = lr

    def forward(self, X):
        logits = X @ self.W + self.b
        # softmax
        exp_logits = np.exp(logits - np.max(logits, axis=-1, keepdims=True))
        return exp_logits / (np.sum(exp_logits, axis=-1, keepdims=True) + 1e-15)

    def train_step(self, X, y_onehot):
        probs = self.forward(X)
        # gradient (cross-entropy)
        grad = probs - y_onehot
        self.W -= self.lr * (X.T @ grad) / len(X)
        self.b -= self.lr * np.mean(grad, axis=0)
        loss = -np.mean(np.sum(y_onehot * np.log(probs + 1e-15), axis=-1))
        return loss


# One-hot encoding
classes = sorted(set(y_labels))
class_to_idx = {c: i for i, c in enumerate(classes)}
n_classes = len(classes)
y_idx = np.array([class_to_idx[l] for l in y_labels])
y_onehot = np.zeros((len(y_idx), n_classes))
y_onehot[np.arange(len(y_idx)), y_idx] = 1.0

# Normalization
X_mean = X.mean(axis=0)
X_std = X.std(axis=0) + 1e-15
X_norm = (X - X_mean) / X_std

# Two engines: A (arithmetic), G (geometric)
# A: uses half features (bandpower)
# G: uses other half + all (ratios/entropy)
n_feat = X_norm.shape[1]
engine_A = SimpleEngine(n_feat, n_classes, np.random.default_rng(1), lr=0.05)
engine_G = SimpleEngine(n_feat, n_classes, np.random.default_rng(2), lr=0.05)

# Different initialization + different feature weights for diversity
# A emphasizes even features, G emphasizes odd features
X_A = X_norm.copy()
X_G = X_norm.copy()
X_A[:, 1::2] *= 0.3   # A: weaken odd features
X_G[:, 0::2] *= 0.3   # G: weaken even features

print("Starting training...")
n_epochs_train = 200
for epoch in range(n_epochs_train):
    # Shuffle
    perm = rng.permutation(len(X_norm))
    loss_A = engine_A.train_step(X_A[perm], y_onehot[perm])
    loss_G = engine_G.train_step(X_G[perm], y_onehot[perm])
    if (epoch + 1) % 50 == 0:
        print(f"  Epoch {epoch+1}/{n_epochs_train}: Loss_A={loss_A:.4f}, Loss_G={loss_G:.4f}")

# ─────────────────────────────────────────────
# 4. Calculate Tension
# ─────────────────────────────────────────────

print("\n" + "─" * 70)
print("4. Tension = |Engine_A(x) - Engine_G(x)|^2")
print("─" * 70)

probs_A = engine_A.forward(X_A)
probs_G = engine_G.forward(X_G)

# Tension = squared distance between engine outputs
tension = np.sum((probs_A - probs_G) ** 2, axis=1)

# Calculate accuracy
preds_A = np.argmax(probs_A, axis=1)
preds_G = np.argmax(probs_G, axis=1)
# Ensemble: average probabilities
probs_ensemble = (probs_A + probs_G) / 2.0
preds_ensemble = np.argmax(probs_ensemble, axis=1)

acc_A = np.mean(preds_A == y_idx)
acc_G = np.mean(preds_G == y_idx)
acc_E = np.mean(preds_ensemble == y_idx)

print(f"  Engine A accuracy: {acc_A:.4f}")
print(f"  Engine G accuracy: {acc_G:.4f}")
print(f"  Ensemble accuracy: {acc_E:.4f}")

# ─────────────────────────────────────────────
# 5. Prediction P1: tension(awake) > tension(sleep)
# ─────────────────────────────────────────────

print("\n" + "─" * 70)
print("5. Prediction Verification")
print("─" * 70)

print("\n--- P1: tension(awake) > tension(sleep) ---")
state_tensions = {}
for state in STATES:
    mask = y_labels == state
    t = tension[mask]
    state_tensions[state] = t
    print(f"  {STATE_NAMES[state]:<25} tension: mean={np.mean(t):.6f}, "
          f"std={np.std(t):.6f}, median={np.median(t):.6f}")

t_awake = state_tensions["awake"]
t_sleep = np.concatenate([state_tensions["sleep_n3"], state_tensions["anesthesia"]])

t_stat, p_val = stats.mannwhitneyu(t_awake, t_sleep, alternative="greater")
d_val = (np.mean(t_awake) - np.mean(t_sleep)) / np.sqrt(
    (np.std(t_awake)**2 + np.std(t_sleep)**2) / 2 + 1e-15
)
print(f"\n  Mann-Whitney U: stat={t_stat:.2f}, p={p_val:.2e}")
print(f"  Cohen's d: {d_val:.4f}")
p1_pass = p_val < 0.05 and d_val > 0.5
print(f"  P1 Result: {'PASS' if p1_pass else 'FAIL'} (d > 0.5 and p < 0.05)")

# ─────────────────────────────────────────────
# 6. Prediction P2: r(gamma_power, tension) > 0.5
# ─────────────────────────────────────────────

print("\n--- P2: r(gamma_power, tension) > 0.5 ---")
r_gamma, p_gamma = stats.pearsonr(y_gamma, tension)
r_spearman, p_spearman = stats.spearmanr(y_gamma, tension)
print(f"  Pearson r(gamma, tension) = {r_gamma:.4f}, p = {p_gamma:.2e}")
print(f"  Spearman rho(gamma, tension) = {r_spearman:.4f}, p = {p_spearman:.2e}")
p2_pass = r_gamma > 0.5 or r_spearman > 0.5
print(f"  P2 Result: {'PASS' if p2_pass else 'FAIL'}")

# ─────────────────────────────────────────────
# 7. Prediction P3: Consciousness classification with tension alone
# ─────────────────────────────────────────────

print("\n--- P3: Awake vs Sleep classification with single tension feature ---")

# Binary classification: awake vs non-awake
y_binary = (y_labels == "awake").astype(int)
# Find optimal threshold
thresholds = np.linspace(np.min(tension), np.max(tension), 100)
best_acc = 0
best_thr = 0
for thr in thresholds:
    pred = (tension >= thr).astype(int)
    acc = np.mean(pred == y_binary)
    if acc > best_acc:
        best_acc = acc
        best_thr = thr

print(f"  Optimal threshold: {best_thr:.6f}")
print(f"  Classification accuracy: {best_acc:.4f}")
p3_pass = best_acc > 0.80
print(f"  P3 Result: {'PASS' if p3_pass else 'FAIL'} (accuracy > 80%)")

# Also try 5-class classification
# Tension vs consciousness level correlation
r_consc, p_consc = stats.spearmanr(tension, y_consciousness)
print(f"\n  Tension vs consciousness level Spearman rho = {r_consc:.4f}, p = {p_consc:.2e}")

# ─────────────────────────────────────────────
# 8. Prediction P4: Tension order = Consciousness order
# ─────────────────────────────────────────────

print("\n--- P4: tension order = consciousness level order ---")
mean_tensions = {s: np.mean(state_tensions[s]) for s in STATES}
sorted_by_tension = sorted(mean_tensions.items(), key=lambda x: x[1], reverse=True)

print("  Expected order: awake > rem > N1 > N3 > anesthesia")
print("  Actual order (tension high → low):")
order_match = True
for i, (state, t_mean) in enumerate(sorted_by_tension):
    expected_order = STATES  # awake, rem, sleep_n1, sleep_n3, anesthesia
    marker = "✓" if sorted_by_tension[i][0] == STATES[i] else "✗"
    if sorted_by_tension[i][0] != STATES[i]:
        order_match = False
    print(f"    {i+1}. {STATE_NAMES[state]:<25} tension={t_mean:.6f} {marker}")

# Kendall's tau (order concordance)
predicted_rank = [CONSCIOUSNESS_ORDER[s] for s in STATES]
actual_rank_by_tension = []
for state in STATES:
    actual_rank_by_tension.append(mean_tensions[state])
tau, p_tau = stats.kendalltau(predicted_rank, actual_rank_by_tension)
print(f"\n  Kendall's tau = {tau:.4f}, p = {p_tau:.4f}")
p4_pass = tau > 0.6
print(f"  P4 Result: {'PASS' if p4_pass else 'FAIL'} (tau > 0.6)")

# ─────────────────────────────────────────────
# 9. Circular reasoning check: Re-analyze excluding gamma
# ─────────────────────────────────────────────

print("\n" + "─" * 70)
print("9. Circular Reasoning Check: Excluding Gamma Features")
print("─" * 70)

# Re-train excluding gamma power (feat[4]) and gamma ratio (feat[6])
exclude_idx = [4, 6]  # gamma_power, gamma_ratio
keep_idx = [i for i in range(n_feat) if i not in exclude_idx]

X_no_gamma = X_norm[:, keep_idx]
X_A_ng = X_no_gamma.copy()
X_G_ng = X_no_gamma.copy()
n_feat_ng = len(keep_idx)
X_A_ng[:, 1::2] *= 0.3
X_G_ng[:, ::2] *= 0.3

engine_A_ng = SimpleEngine(n_feat_ng, n_classes, np.random.default_rng(10), lr=0.05)
engine_G_ng = SimpleEngine(n_feat_ng, n_classes, np.random.default_rng(20), lr=0.05)

for epoch in range(n_epochs_train):
    perm = rng.permutation(len(X_no_gamma))
    engine_A_ng.train_step(X_A_ng[perm], y_onehot[perm])
    engine_G_ng.train_step(X_G_ng[perm], y_onehot[perm])

probs_A_ng = engine_A_ng.forward(X_A_ng)
probs_G_ng = engine_G_ng.forward(X_G_ng)
tension_no_gamma = np.sum((probs_A_ng - probs_G_ng) ** 2, axis=1)

r_ng, p_ng = stats.pearsonr(y_gamma, tension_no_gamma)
print(f"  After excluding gamma: r(gamma, tension) = {r_ng:.4f}, p = {p_ng:.2e}")

# Does it still correlate with consciousness level after excluding gamma?
r_consc_ng, p_consc_ng = stats.spearmanr(tension_no_gamma, y_consciousness)
print(f"  After excluding gamma: rho(tension, consciousness) = {r_consc_ng:.4f}, p = {p_consc_ng:.2e}")

for state in STATES:
    mask = y_labels == state
    t = tension_no_gamma[mask]
    print(f"    {STATE_NAMES[state]:<25} tension_no_gamma: mean={np.mean(t):.6f}")

# ─────────────────────────────────────────────
# 10. ASCII Visualization
# ─────────────────────────────────────────────

print("\n" + "─" * 70)
print("10. Results Visualization")
print("─" * 70)

# State-wise tension distribution histogram
print("\nTension distribution (by state):")
max_tension = np.max(tension)
bin_edges = np.linspace(0, max_tension * 1.1, 30)

for state in STATES:
    mask = y_labels == state
    t = tension[mask]
    hist, _ = np.histogram(t, bins=bin_edges)
    max_h = max(hist) if max(hist) > 0 else 1
    bar = ""
    for h in hist:
        n_chars = int(h / max_h * 20)
        bar += "█" * n_chars if n_chars > 0 else ""
    print(f"  {STATE_NAMES[state]:<25} |{bar}| mean={np.mean(t):.5f}")

# Gamma vs tension scatter plot (ASCII)
print("\nGamma power vs Tension (ASCII scatter plot):")
width, height = 60, 20
canvas = [[' ' for _ in range(width)] for _ in range(height)]

x_min, x_max = np.min(tension), np.max(tension)
y_min, y_max = np.min(y_gamma), np.max(y_gamma)

state_chars = {"awake": "A", "rem": "R", "sleep_n1": "1", "sleep_n3": "3", "anesthesia": "X"}

for i in range(0, len(tension), 5):  # subsample for readability
    x = int((tension[i] - x_min) / (x_max - x_min + 1e-15) * (width - 1))
    y = int((y_gamma[i] - y_min) / (y_max - y_min + 1e-15) * (height - 1))
    y = height - 1 - y
    x = max(0, min(x, width - 1))
    y = max(0, min(y, height - 1))
    canvas[y][x] = state_chars[y_labels[i]]

print(f"  Gamma {'':>{width-6}}")
print(f"  power")
for i, row in enumerate(canvas):
    if i == 0:
        print(f"  {y_max:>8.1f} |{''.join(row)}|")
    elif i == height - 1:
        print(f"  {y_min:>8.1f} |{''.join(row)}|")
    else:
        print(f"  {'':>8} |{''.join(row)}|")
print(f"  {'':>8}  {'─' * width}")
print(f"  {'':>8}  {x_min:.4f}{' ' * (width - 16)}{x_max:.4f}")
print(f"  {'':>8}  {'Tension (|A-G|^2)':^{width}}")
print(f"  Legend: A=Awake, R=REM, 1=N1, 3=N3, X=Anesthesia")

# ─────────────────────────────────────────────
# 11. Summary Results
# ─────────────────────────────────────────────

print("\n" + "=" * 70)
print("11. Summary Results")
print("=" * 70)

results = {
    "P1 tension(awake) > tension(sleep)": (p1_pass, f"d={d_val:.3f}, p={p_val:.2e}"),
    "P2 r(gamma, tension) > 0.5": (p2_pass, f"r={r_gamma:.3f}, rho={r_spearman:.3f}"),
    "P3 Single feature classification > 80%": (p3_pass, f"acc={best_acc:.3f}"),
    "P4 Tension order = consciousness order": (p4_pass, f"tau={tau:.3f}"),
}

print(f"\n{'Prediction':<40} {'Result':>8} {'Detail':<30}")
print("─" * 80)
pass_count = 0
for pred, (passed, detail) in results.items():
    result_str = "PASS" if passed else "FAIL"
    print(f"  {pred:<40} {result_str:>6}   {detail}")
    if passed:
        pass_count += 1

print(f"\nPassed: {pass_count}/{len(results)}")

# Circular reasoning check results
print(f"\nCircular reasoning check:")
print(f"  With gamma: r(gamma, tension) = {r_gamma:.4f}")
print(f"  Without gamma: r(gamma, tension) = {r_ng:.4f}")
if abs(r_ng) > 0.3:
    print(f"  → Correlation maintained after excluding gamma → Tension captures more than just gamma")
else:
    print(f"  → Correlation lost when gamma excluded → High gamma dependence of tension (beware circularity)")

print(f"""
  ┌─────────────────────────────────────────────────────────────────┐
  │ Hypothesis 322 Phase 1 Verification Results (Synthetic EEG)     │
  ├─────────────────────────────────────────────────────────────────┤
  │                                                                 │
  │ P1 (consciousness→tension): {'PASS' if p1_pass else 'FAIL':>4}  d={d_val:.3f}                     │
  │ P2 (gamma-tension): {'PASS' if p2_pass else 'FAIL':>4}  r={r_gamma:.3f}, rho={r_spearman:.3f}              │
  │ P3 (single classification):  {'PASS' if p3_pass else 'FAIL':>4}  acc={best_acc:.3f}                     │
  │ P4 (order match):  {'PASS' if p4_pass else 'FAIL':>4}  tau={tau:.3f}                           │
  │                                                                 │
  │ Circular check:                                                 │
  │   With gamma r={r_gamma:.3f} → Without gamma r={r_ng:.3f}                  │
  │   Consciousness corr rho={r_consc:.3f} → Without gamma rho={r_consc_ng:.3f}        │
  │                                                                 │
  │ Limitations: Synthetic data → Need re-verification with real EEG│
  │              (PhysioNet)                                        │
  │                                                                 │
  │ Status: {'🟧 Partially Verified' if pass_count >= 2 else '⚪ Not Verified'} (Phase 1 synthetic data)           │
  └─────────────────────────────────────────────────────────────────┘
""")

print("Verification complete.")