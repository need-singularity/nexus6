#!/opt/homebrew/bin/python3
"""H368: Tension Natural Frequency — Measuring PureFieldEngine's Natural Frequency

Experiment:
  1. Constant input 500 steps → tension time series → FFT for natural frequency measurement
  2. Sinusoidal modulated input → frequency response (resonance search)
  3. Before/after training comparison
  4. tension_scale comparison → omega_0 proportional to sqrt(tension_scale)?
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import torch
import numpy as np
from model_pure_field import PureFieldEngine

torch.manual_seed(42)
np.random.seed(42)

STEPS = 500
INPUT_DIM = 784
HIDDEN_DIM = 128
OUTPUT_DIM = 10
FREQS = [0.01, 0.05, 0.1, 0.2, 0.5]  # driving frequencies (cycles/step)


def ascii_plot(data, title, width=70, height=20, xlabel="step", ylabel="value"):
    """Minimal ASCII plot."""
    arr = np.array(data, dtype=float)
    mn, mx = arr.min(), arr.max()
    if mx - mn < 1e-12:
        mx = mn + 1e-6
    print(f"\n{'=' * width}")
    print(f"  {title}")
    print(f"  {ylabel} range: [{mn:.6f}, {mx:.6f}]")
    print(f"{'=' * width}")
    for row in range(height - 1, -1, -1):
        threshold = mn + (mx - mn) * row / (height - 1)
        label = f"{threshold:10.5f} |"
        line = []
        bucket_size = max(1, len(arr) // width)
        for b in range(min(width, len(arr))):
            idx_start = b * bucket_size
            idx_end = min(idx_start + bucket_size, len(arr))
            val = arr[idx_start:idx_end].mean()
            line.append("#" if val >= threshold else " ")
        print(label + "".join(line))
    print(" " * 11 + "+" + "-" * width)
    print(f"  {xlabel}: 0 .. {len(arr)-1}")


def ascii_bar(labels, values, title, width=50):
    """Horizontal ASCII bar chart."""
    mx = max(abs(v) for v in values) if values else 1
    if mx < 1e-12:
        mx = 1e-6
    print(f"\n{'=' * (width + 25)}")
    print(f"  {title}")
    print(f"{'=' * (width + 25)}")
    for lab, val in zip(labels, values):
        bar_len = int(abs(val) / mx * width)
        print(f"  {lab:>12s} | {'#' * bar_len} {val:.6f}")
    print()


def collect_tension(model, x_base, steps, modulation_freq=None, modulation_amp=0.5,
                    stochastic=True):
    """Run model on (optionally modulated) input for N steps, return tension series.

    stochastic=True uses train() mode so dropout fires each step,
    creating genuine tension fluctuations even with constant input.
    This models the realistic regime where internal noise exists.
    """
    if stochastic:
        model.train()   # dropout active → stochastic tension
    else:
        model.eval()
    tensions = []
    with torch.no_grad():  # no grad even in train mode (we just want forward noise)
        for t in range(steps):
            if modulation_freq is not None:
                scale = 1.0 + modulation_amp * np.sin(2 * np.pi * modulation_freq * t)
                x = x_base * scale
            else:
                x = x_base
            _, tension = model(x)
            tensions.append(tension.mean().item())
    model.eval()
    return np.array(tensions)


def compute_fft(tension_series):
    """Return frequencies and power spectrum (one-sided)."""
    n = len(tension_series)
    detrended = tension_series - tension_series.mean()
    fft_vals = np.fft.rfft(detrended)
    power = np.abs(fft_vals) ** 2
    freqs = np.fft.rfftfreq(n, d=1.0)  # d=1 step
    return freqs[1:], power[1:]  # skip DC


def find_peaks(freqs, power, top_k=5):
    """Find top-k frequency peaks."""
    indices = np.argsort(power)[::-1][:top_k]
    return [(freqs[i], power[i]) for i in sorted(indices)]


def frequency_response(model, x_base, steps, freqs, amp=0.5):
    """Measure tension amplitude at each driving frequency."""
    amplitudes = []
    for f in freqs:
        ts = collect_tension(model, x_base, steps, modulation_freq=f, modulation_amp=amp)
        # Amplitude = std of tension (RMS of oscillation)
        amplitudes.append(ts.std())
    return np.array(amplitudes)


def train_simple(model, steps=200):
    """Minimal training on random data to change weights."""
    model.train()
    opt = torch.optim.Adam(model.parameters(), lr=1e-3)
    x_train = torch.randn(64, INPUT_DIM)
    y_train = torch.randint(0, OUTPUT_DIM, (64,))
    for _ in range(steps):
        out, tension = model(x_train)
        loss = torch.nn.functional.cross_entropy(out, y_train) + 0.01 * tension.mean()
        opt.zero_grad()
        loss.backward()
        opt.step()
    model.eval()


# ─── EXPERIMENT 1: Constant input → natural frequency ───
print("=" * 75)
print("  H368: Tension Natural Frequency Experiment")
print("=" * 75)

x_base = torch.randn(1, INPUT_DIM)  # single constant input

print("\n--- Phase 1: Constant input, untrained model ---")
model_untrained = PureFieldEngine(INPUT_DIM, HIDDEN_DIM, OUTPUT_DIM)
ts_const = collect_tension(model_untrained, x_base, STEPS)

print(f"  Tension stats: mean={ts_const.mean():.6f}  std={ts_const.std():.6f}"
      f"  min={ts_const.min():.6f}  max={ts_const.max():.6f}")

ascii_plot(ts_const, "Tension time series (constant input, untrained)", ylabel="tension")

freqs_const, power_const = compute_fft(ts_const)
peaks_const = find_peaks(freqs_const, power_const)

print("\n  Top-5 FFT peaks (constant input, untrained):")
print(f"  {'Freq (cyc/step)':>18s}  {'Power':>12s}  {'Period (steps)':>15s}")
for f, p in peaks_const:
    period = 1.0 / f if f > 0 else float('inf')
    print(f"  {f:18.6f}  {p:12.4f}  {period:15.1f}")

ascii_plot(np.log10(power_const + 1e-30), "FFT Power Spectrum (log10, constant input)",
           xlabel="freq bin", ylabel="log10(power)")

# ─── EXPERIMENT 2: Sinusoidal driving → frequency response ───
print("\n--- Phase 2: Frequency response (untrained) ---")
resp_untrained = frequency_response(model_untrained, x_base, STEPS, FREQS)

labels = [f"f={f:.2f}" for f in FREQS]
ascii_bar(labels, resp_untrained.tolist(),
          "Frequency Response: tension std vs driving freq (untrained)")

print("  Frequency response table (untrained):")
print(f"  {'Drive freq':>12s}  {'Tension std':>12s}  {'Tension std/mean':>16s}")
for f, a in zip(FREQS, resp_untrained):
    print(f"  {f:12.3f}  {a:12.6f}  {a/max(ts_const.mean(),1e-8):16.6f}")

# ─── EXPERIMENT 3: Trained model comparison ───
print("\n--- Phase 3: Trained model comparison ---")
model_trained = PureFieldEngine(INPUT_DIM, HIDDEN_DIM, OUTPUT_DIM)
model_trained.load_state_dict(model_untrained.state_dict())  # same init
train_simple(model_trained, steps=200)

ts_trained = collect_tension(model_trained, x_base, STEPS)
print(f"  Trained tension: mean={ts_trained.mean():.6f}  std={ts_trained.std():.6f}")

freqs_tr, power_tr = compute_fft(ts_trained)
peaks_tr = find_peaks(freqs_tr, power_tr)

ascii_plot(ts_trained, "Tension time series (constant input, trained)")

print("\n  Top-5 FFT peaks (trained):")
print(f"  {'Freq (cyc/step)':>18s}  {'Power':>12s}  {'Period (steps)':>15s}")
for f, p in peaks_tr:
    period = 1.0 / f if f > 0 else float('inf')
    print(f"  {f:18.6f}  {p:12.4f}  {period:15.1f}")

resp_trained = frequency_response(model_trained, x_base, STEPS, FREQS)

ascii_bar(labels, resp_trained.tolist(),
          "Frequency Response: tension std vs driving freq (trained)")

# ─── EXPERIMENT 4: tension_scale sweep ───
print("\n--- Phase 4: tension_scale sweep ---")
scales = [1.0, 5.0, 10.0]
omega_0s = []

print(f"\n  {'scale':>8s}  {'mean_T':>10s}  {'std_T':>10s}  {'peak_freq':>12s}"
      f"  {'peak_power':>12s}  {'sqrt(scale)':>12s}")

for sc in scales:
    m = PureFieldEngine(INPUT_DIM, HIDDEN_DIM, OUTPUT_DIM)
    m.load_state_dict(model_untrained.state_dict())
    with torch.no_grad():
        m.tension_scale.fill_(sc)

    ts_sc = collect_tension(m, x_base, STEPS)
    fr, pw = compute_fft(ts_sc)
    pk = find_peaks(fr, pw, top_k=1)[0]
    omega_0s.append(pk[0])

    print(f"  {sc:8.1f}  {ts_sc.mean():10.6f}  {ts_sc.std():10.6f}"
          f"  {pk[0]:12.6f}  {pk[1]:12.4f}  {np.sqrt(sc):12.4f}")

# Check proportionality: omega_0 ~ sqrt(tension_scale)?
print("\n  Proportionality check: omega_0 / sqrt(tension_scale)")
for sc, om in zip(scales, omega_0s):
    ratio = om / np.sqrt(sc) if sc > 0 else 0
    print(f"    scale={sc:.1f}  omega_0={om:.6f}  ratio={ratio:.6f}")

ratios = [om / np.sqrt(sc) for sc, om in zip(scales, omega_0s)]
ratio_std = np.std(ratios)
ratio_mean = np.mean(ratios)
print(f"  Ratio mean={ratio_mean:.6f}  std={ratio_std:.6f}  CV={ratio_std/max(ratio_mean,1e-8):.4f}")
if ratio_std / max(ratio_mean, 1e-8) < 0.1:
    print("  >>> omega_0 IS proportional to sqrt(tension_scale) (CV < 10%)")
else:
    print("  >>> omega_0 is NOT clearly proportional to sqrt(tension_scale)")

# ─── EXPERIMENT 5: Resonance detection ───
print("\n--- Phase 5: Resonance detection ---")
fine_freqs = np.linspace(0.005, 0.5, 50)
resp_fine = []
for f in fine_freqs:
    ts_f = collect_tension(model_untrained, x_base, STEPS, modulation_freq=f, modulation_amp=0.5)
    resp_fine.append(ts_f.std())
resp_fine = np.array(resp_fine)

ascii_plot(resp_fine, "Bode-like: tension std vs driving frequency (50 points)",
           xlabel="freq index (0.005..0.5)", ylabel="tension std")

peak_idx = np.argmax(resp_fine)
print(f"\n  Resonance peak: f={fine_freqs[peak_idx]:.4f} cyc/step  "
      f"amplitude={resp_fine[peak_idx]:.6f}")
print(f"  DC response:    amplitude={resp_fine[0]:.6f}")
print(f"  HF response:    amplitude={resp_fine[-1]:.6f}")
Q = resp_fine[peak_idx] / resp_fine.mean() if resp_fine.mean() > 0 else 0
print(f"  Q factor (peak/mean): {Q:.4f}")

# ─── Summary ───
print("\n" + "=" * 75)
print("  SUMMARY")
print("=" * 75)
print(f"  Untrained natural freq (top peak):  {peaks_const[0][0]:.6f} cyc/step")
print(f"  Trained natural freq (top peak):    {peaks_tr[0][0]:.6f} cyc/step")
print(f"  Resonance frequency (fine scan):    {fine_freqs[peak_idx]:.6f} cyc/step")
print(f"  omega_0 ~ sqrt(tension_scale):      CV={ratio_std/max(ratio_mean,1e-8):.4f}"
      f"  ({'YES' if ratio_std/max(ratio_mean,1e-8) < 0.1 else 'NO'})")
print(f"  Q factor:                           {Q:.4f}")
print(f"  Training shifts tension mean:       "
      f"{ts_const.mean():.4f} -> {ts_trained.mean():.4f}")
print(f"  Training shifts tension std:        "
      f"{ts_const.std():.6f} -> {ts_trained.std():.6f}")
print("=" * 75)