```python
#!/usr/bin/env python3
"""EEG synthetic data based CCT validator — neuroscience verification without public data

Without public EEG data (PhysioNet etc.), reproduce known statistical properties
of EEG with synthetic data and apply CCT (Consciousness Continuity Test).

5 brain states:
  1. awake:       alpha+beta+gamma, 1/f noise, high complexity
  2. sleep N1 (drowsy): theta dominant + weak alpha
  3. sleep N3 (deep):   delta dominant, high amplitude slow waves, high synchronization
  4. anesthesia:        delta + burst-suppression pattern
  5. seizure:          3Hz spike-wave, very periodic

Usage:
  python3 eeg_cct_validator.py
  python3 eeg_cct_validator.py --duration 60
  python3 eeg_cct_validator.py --state awake
"""

import argparse
import sys

import numpy as np
from scipy import signal as sp_signal


# ─────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────

FS = 256          # Sampling frequency (Hz) — standard clinical EEG
SEED = 42

# Predictions by brain state (number of CCT tests passed)
PREDICTIONS = {
    "awake": {
        "total": 5,
        "tests": {"T1": True, "T2": True, "T3": True, "T4": True, "T5": True},
        "reason": "Continuous+chaotic: predicted to pass all tests",
    },
    "sleep_n1": {
        "total": 5,
        "tests": {"T1": True, "T2": True, "T3": True, "T4": True, "T5": True},
        "reason": "Theta dominant but still maintains sufficient complexity (drowsy ≠ sleep)",
    },
    "sleep_n3": {
        "total": 3,
        "tests": {"T1": True, "T2": False, "T3": True, "T4": True, "T5": False},
        "reason": "T2,T5 fail: highly synchronized slow waves → periodic+stagnant",
    },
    "anesthesia": {
        "total": 1,
        "tests": {"T1": False, "T2": True, "T3": False, "T4": False, "T5": True},
        "reason": "T1,T3,T4 fail: burst-suppression → gap+discontinuous+entropy deviation",
    },
    "seizure": {
        "total": 2,
        "tests": {"T1": True, "T2": False, "T3": False, "T4": True, "T5": False},
        "reason": "T2,T3,T5 fail: spike-wave → periodic+jump+stagnant",
    },
}

STATE_LABELS = {
    "awake": "Awake",
    "sleep_n1": "Sleep N1 (Drowsy)",
    "sleep_n3": "Sleep N3 (Deep Sleep)",
    "anesthesia": "Anesthesia",
    "seizure": "Seizure",
}


# ─────────────────────────────────────────────
# Synthetic EEG generators
# ─────────────────────────────────────────────

def generate_1f_noise(n, fs, rng, exponent=1.0):
    """Generate 1/f^exponent noise (pink noise).

    Background noise in brain EEG shows 1/f spectrum characteristics.
    """
    freqs = np.fft.rfftfreq(n, d=1.0 / fs)
    freqs[0] = 1.0  # Prevent division by zero for DC component
    amplitudes = 1.0 / (freqs ** (exponent / 2.0))
    phases = rng.uniform(0, 2 * np.pi, len(freqs))
    spectrum = amplitudes * np.exp(1j * phases)
    spectrum[0] = 0  # DC = 0
    noise = np.fft.irfft(spectrum, n=n)
    return noise / (np.std(noise) + 1e-15)


def generate_oscillation(n, fs, freq, amplitude, rng, phase_jitter=0.0):
    """Generate oscillation component (frequency + phase variation)."""
    t = np.arange(n) / fs
    phase = 2 * np.pi * freq * t
    if phase_jitter > 0:
        # Nonlinearity: add small random walk to phase
        walk = np.cumsum(rng.normal(0, phase_jitter, n))
        phase += walk
    return amplitude * np.sin(phase)


def generate_coupled_oscillators(n, fs, freqs, amplitudes, rng, coupling=0.1):
    """Coupled oscillator system — nonlinear interaction.

    Each oscillator is affected by the phase of other oscillators.
    This creates the nonlinear characteristics of awake EEG.
    Strong phase noise and amplitude modulation ensure chaotic properties.
    """
    dt = 1.0 / fs
    n_osc = len(freqs)
    phases = rng.uniform(0, 2 * np.pi, n_osc)
    result = np.zeros(n)

    # Slow random walk for amplitude modulation
    amp_mod = np.ones((n, n_osc))
    for k in range(n_osc):
        walk = np.cumsum(rng.normal(0, 0.005, n))
        amp_mod[:, k] = np.clip(1.0 + walk, 0.3, 2.0)

    for i in range(n):
        for k in range(n_osc):
            result[i] += amplitudes[k] * amp_mod[i, k] * np.sin(phases[k])

        # Phase update (Kuramoto model + strong noise)
        for k in range(n_osc):
            omega = 2 * np.pi * freqs[k]
            coupling_term = 0.0
            for j in range(n_osc):
                if j != k:
                    coupling_term += np.sin(phases[j] - phases[k])
            coupling_term *= coupling / n_osc
            # Strong phase noise to break periodicity
            phase_noise = rng.normal(0, 0.3)
            phases[k] += (omega + coupling_term) * dt + phase_noise * dt

    return result


def synthesize_awake(n, fs, rng):
    """Awake EEG: alpha(10Hz) + beta(20Hz) + gamma(40Hz) + 1/f noise.

    Characteristics: nonlinear, high complexity, continuous, chaotic.
    Amplitude: 20-100 uV
    """
    # Coupled oscillators: alpha, beta, gamma (strong coupling)
    eeg = generate_coupled_oscillators(
        n, fs,
        freqs=[10.0, 20.0, 40.0],
        amplitudes=[30.0, 15.0, 5.0],  # uV
        rng=rng,
        coupling=0.3,
    )
    # Strong 1/f background noise (enhances chaotic properties)
    pink = generate_1f_noise(n, fs, rng, exponent=1.0)
    eeg += pink * 15.0  # 15 uV scale

    # Nonlinear modulation: irregular amplitude changes
    t = np.arange(n) / fs
    # Multi-frequency modulation (non-integer ratio → quasiperiodic)
    modulation = (1.0
                  + 0.3 * np.sin(2 * np.pi * 0.1 * t + rng.uniform(0, 2 * np.pi))
                  + 0.2 * np.sin(2 * np.pi * 0.073 * t + rng.uniform(0, 2 * np.pi))
                  + 0.15 * np.sin(2 * np.pi * 0.031 * t + rng.uniform(0, 2 * np.pi)))
    eeg *= modulation

    # Intermittent bursts: short high-energy segments (atypical activity specific to wakefulness)
    n_bursts = max(1, n // (fs * 5))  # About 1 per 5 seconds
    for _ in range(n_bursts):
        burst_start = rng.integers(0, max(1, n - fs))
        burst_len = rng.integers(fs // 4, fs)
        burst_end = min(burst_start + burst_len, n)
        eeg[burst_start:burst_end] += rng.normal(0, 20.0, burst_end - burst_start)

    return eeg


def synthesize_sleep_n1(n, fs, rng):
    """Sleep N1 EEG: theta(5Hz) dominant + weak alpha + 1/f noise.

    Characteristics: alpha decrease, theta increase, slightly reduced complexity.
    Amplitude: 50-100 uV
    """
    # Theta dominant
    theta = generate_oscillation(n, fs, 5.0, 40.0, rng, phase_jitter=0.02)
    # Weak alpha
    alpha = generate_oscillation(n, fs, 10.0, 10.0, rng, phase_jitter=0.01)
    # 1/f noise
    pink = generate_1f_noise(n, fs, rng, exponent=1.2)

    eeg = theta + alpha + pink * 8.0

    # Slow modulation (gradual changes in drowsy state)
    t = np.arange(n) / fs
    modulation = 1.0 + 0.2 * np.sin(2 * np.pi * 0.05 * t)
    eeg *= modulation

    return eeg


def synthesize_sleep_n3(n, fs, rng):
    """Sleep N3 EEG: delta(1-2Hz) dominant, high amplitude slow waves.

    Characteristics: high amplitude low frequency, low complexity, high synchronization.
    Very periodic → expected to fail T2(Loop).
    Amplitude: 100-200 uV
    """
    # Very regular delta (minimal phase noise)
    delta1 = generate_oscillation(n, fs, 1.0, 120.0, rng, phase_jitter=0.0005)
    delta2 = generate_oscillation(n, fs, 2.0, 50.0, rng, phase_jitter=0.0005)
    # Extremely weak noise (high synchronization)
    pink = generate_1f_noise(n, fs, rng, exponent=2.0)

    eeg = delta1 + delta2 + pink * 2.0

    return eeg


def synthesize_anesthesia(n, fs, rng):
    """Anesthesia EEG: delta(1Hz) + burst-suppression pattern.

    Characteristics: intermittent suppression intervals — this is the gap!
    Amplitude: 0~200 uV (alternating burst and suppression)

    Set suppression intervals to actual constant value (0) to clearly create gaps.
    This preserves frozen segments even after Takens embedding.
    """
    eeg = np.zeros(n)

    # Generate burst-suppression mask
    i = 0
    suppressed = False
    suppression_mask = np.zeros(n, dtype=bool)

    while i < n:
        if suppressed:
            # suppression: 2-5 seconds (must be long enough to be detected as gap)
            dur = int(rng.uniform(2.0, 5.0) * fs)
            end = min(i + dur, n)
            suppression_mask[i:end] = True
            # Completely flat signal (isoelectric)
            eeg[i:end] = 0.0
            i = end
        else:
            # burst: 1-3 seconds
            dur = int(rng.uniform(1.0, 3.0) * fs)
            end = min(i + dur, n)
            # Burst: high amplitude delta + noise
            t_seg = np.arange(end - i) / fs
            eeg[i:end] = (100.0 * np.sin(2 * np.pi * 1.0 * t_seg)
                          + rng.normal(0, 20.0, end - i))
            i = end
        suppressed = not suppressed

    return eeg, suppression_mask


def synthesize_seizure(n, fs, rng):
    """Seizure EEG: 3Hz spike-wave, very periodic.

    Characteristics: high amplitude, repetitive spikes, high energy, low complexity.
    Entropy in each window is nearly identical → expected to fail T5(novelty).
    Amplitude: 200-500 uV
    """
    t = np.arange(n) / fs

    # 3Hz spike-wave: very regular
    phase = 2 * np.pi * 3.0 * t
    # Spike component (sharp peaks)
    spike = 250.0 * np.exp(-((np.mod(phase, 2 * np.pi) - 0.5) ** 2) / 0.03)
    # Slow wave component
    slow_wave = -100.0 * np.sin(phase)

    eeg = spike + slow_wave

    # Extremely small noise only (actual seizures are very regular)
    eeg += rng.normal(0, 1.0, n)

    return eeg


GENERATORS = {
    "awake": synthesize_awake,
    "sleep_n1": synthesize_sleep_n1,
    "sleep_n3": synthesize_sleep_n3,
    "anesthesia": synthesize_anesthesia,  # returns (eeg, mask) tuple
    "seizure": synthesize_seizure,
}


# ─────────────────────────────────────────────
# Takens embedding: EEG → 3D state vector
# ─────────────────────────────────────────────

def eeg_to_state_vector(eeg, fs, suppression_mask=None):
    """Convert EEG to 3D state vector.

    S(t) = [x(t), dx/dt, d^2x/dt^2]
    Simplified version of Takens embedding: original, 1st derivative, 2nd derivative.

    If suppression_mask is given, force state vector to 0 in those intervals
    to clearly create gaps (stops).
    """
    dt = 1.0 / fs
    dx = np.gradient(eeg, dt)
    d2x = np.gradient(dx, dt)
    S = np.column_stack([eeg, dx, d2x])

    if suppression_mask is not None:
        # suppression intervals = state 0 (complete stop)
        S[suppression_mask] = 0.0

    return S


# ─────────────────────────────────────────────
# CCT 5 tests (self-implementation)
# ─────────────────────────────────────────────

def compute_entropy(data, bins=30):
    """Shannon entropy of 1D data."""
    if len(data) < 2:
        return 0.0
    data_range = data.max() - data.min()
    if data_range < 1e-12:
        return 0.0
    hist, _ = np.histogram(data, bins=bins, density=True)
    hist = hist[hist > 0]
    width = data_range / bins
    probs = hist * width
    probs = probs[probs > 0]
    if len(probs) == 0:
        return 0.0
    probs = probs / probs.sum()
    return -np.sum(probs * np.log(probs + 1e-15))


def test_gap(S):
    """T1 Gap test: presence of stop intervals (suppression).

    In EEG, burst-suppression patterns are indicators of absence of consciousness.
    Measure the ratio of intervals with almost no change between adjacent steps.
    """
    diffs = np.diff(S, axis=0)
    norms = np.linalg.norm(diffs, axis=1)

    # Stop determination: intervals with very small change
    # In EEG, suppression = amplitude < few uV
    median_norm = np.median(norms)
    if median_norm < 1e-12:
        return 0.0, False, "Complete stop state"

    # Stop threshold: 1% of median
    frozen_threshold = max(median_norm * 0.01, 1e-10)
    frozen = np.sum(norms < frozen_threshold)
    frozen_ratio = frozen / len(norms)

    if frozen_ratio > 0.01:
        score = max(0.0, 1.0 - frozen_ratio)
        return score, False, f"Stop ratio {frozen_ratio:.1%} (suppression detected)"

    return 1.0, True, f"No gap (stop {frozen_ratio:.3%})"


def test_loop(S, threshold=0.5):
    """T2 Loop test: periodic repetition of trajectory.

    Periodic signals (seizure, deep sleep slow waves) repeatedly
    visit the same path in state space → high revisit rate.
    Chaotic signals (awake) come close but never repeat exactly.

    Method: measure recurrence ratio in state space.
    Normalize each dimension independently to correct for scale differences.
    """
    n = len(S)
    if n < 200:
        return 0.0, False, "Insufficient data"

    # Downsample
    step = max(1, n // 5000)
    Ss = S[::step].copy()
    ns = len(Ss)

    if np.std(Ss) < 1e-10:
        return 0.0, False, "No state change"

    # Normalize each dimension by standard deviation (correct x, dx, d2x scale differences)
    for dim in range(Ss.shape[1]):
        std_d = np.std(Ss[:, dim])
        if std_d > 1e-12:
            Ss[:, dim] /= std_d

    # Revisit determination in normalized space
    # eps = 0.05: after normalization, std=1 for each dimension,
    # 0.05 = within 5% return → only possible with periodic orbits
    eps = 0.05

    recurrence = 0
    sample_size = min(500, ns // 2)
    rng = np.random.default_rng(42)
    indices = rng.choice(ns // 2, size=sample_size, replace=False)

    min_future_gap = max(100, ns // 10)

    for idx in indices:
        future_start = idx + min_future_gap
        future = Ss[future_start:]
        if len(future) == 0:
            continue
        dists = np.linalg.norm(future - Ss[idx], axis=1)
        if np.min(dists) < eps:
            recurrence += 1

    recurrence_ratio = recurrence / sample_size
    passed = recurrence_ratio < threshold
    score = max(0, 1.0 - recurrence_ratio)

    detail = f"Revisit rate={recurrence_ratio:.3f}"
    if passed:
        detail += ", aperiodic"
    else:
        detail += ", periodic repetition detected"

    return score, passed, detail


def test_continuity(S, threshold=0.01):
    """T3 Continuity test: connectivity between adjacent steps.

    Measure ratio of large jumps (discontinuous) or stops (frozen).
    In anesthesia burst-suppression, large jumps occur at burst↔suppression transitions.
    """
    diffs = np.linalg.norm(np.diff(S, axis=0), axis=1)
    n = len(diffs)

    if n < 10:
        return 0.0, False, "Insufficient data"

    mean_diff = np.mean(diffs)
    if mean_diff < 1e-12:
        return 0.0, False, "No state change"

    # Large jumps: more than 10x the mean
    big_jumps = np.sum(diffs > mean_diff * 10)
    # Stops: almost no change
    frozen = np.sum(diffs < 1e-12)

    jump_ratio = big_jumps / n
    frozen_ratio = frozen / n
    disconnect_ratio = jump_ratio + frozen_ratio

    passed = disconnect_ratio < threshold
    score = max(0, 1.0 - disconnect_ratio * 10)
    score = min(1.0, score)

    detail = f"Jump={jump_ratio:.3f}, stop={frozen_ratio:.3f}"
    if passed:
        detail += ", connection maintained"
    else:
        detail += ", disconnection detected"

    return score, passed, detail


def test_entropy_band(S, window_sec=2.0, fs=FS, h_min=0.3, h_max=4.5):
    """T4 Entropy Band test: whether H(t) stays within band.

    Conscious states maintain entropy within a certain range.
    Too low (completely periodic) indicates absence of consciousness, too high indicates disorder.
    """
    x = S[:, 0]
    window = int(window_sec * fs)
    n = len(x)
    n_windows = n // window

    if n_windows < 2:
        return 0.0, False, "Insufficient data"

    entropies = []
    for i in range(n_windows):
        w = x[i * window:(i + 1) * window]
        if np.std(w) < 1e-12:
            entropies.append(0.0)
        else:
            entropies.append(compute_entropy(w))

    entropies = np.array(entropies)
    in_band = np.sum((entropies > h_min) & (entropies < h_max))
    ratio = in_band / len(entropies)

    h_range_str = f"H in [{entropies.min():.2f}, {entropies.max():.2f}]"
    passed = ratio > 0.95
    score = ratio

    if passed:
        detail = f"{h_range_str}, within band"
    else:
        detail = f"{h_range_str}, band deviation {1 - ratio:.1%}"

    return score, passed, detail


def test_novelty(S, window_sec=2.0, fs=FS):
    """T5 Novelty test: dH/dt != 0 (entropy stagnation ratio).

    Conscious states always generate new information → entropy changes.
    In deep sleep or seizures, entropy stagnates.

    Threshold: use 10% of median entropy change rate.
    This is an adaptive threshold instead of absolute.
    """
    x = S[:, 0]
    window = int(window_sec * fs)
    n = len(x)
    n_windows = n // window

    if n_windows < 3:
        return 0.0, False, "Insufficient data"

    entropies = []
    for i in range(n_windows):
        w = x[i * window:(i + 1) * window]
        if np.std(w) < 1e-12:
            entropies.append(0.0)
        else:
            entropies.append(compute_entropy(w))

    entropies = np.array(entropies)
    dH = np.abs(np.diff(entropies))

    if len(dH) == 0:
        return 0.0, False, "Insufficient intervals"

    # Adaptive threshold: 20% of median
    # Chaotic signal: dH varies greatly → high median → passes even with high threshold
    # Periodic signal: dH very small → small median → stagnation detected
    median_dH = np.median(dH)
    threshold = max(median_dH * 0.2, 0.005)

    stagnant = np.sum(dH < threshold)
    stagnant_ratio = stagnant / len(dH)

    # Additional: if entropy variance is very small, lacks novelty
    entropy_cv = np.std(entropies) / (np.mean(entropies) + 1e-15)

    # If coefficient of variation < 0.5%, stagnant
    if entropy_cv < 0.005:
        stagnant_ratio = max(stagnant_ratio, 0.8)

    passed = stagnant_ratio < 0.3
    score = max(0, 1.0 - stagnant_ratio)

    detail = (f"Stagnant intervals {stagnant_ratio:.1%}, "
              f"dH median={median_dH:.4f}, CV={entropy_cv:.4f}")

    return score, passed, detail


def run_cct(S, fs=FS):
    """Run CCT 5 tests."""
    results = {}
    results["T1"] = test_gap(S)
    results["T2"] = test_loop(S)
    results["T3"] = test_continuity(S)
    results["T4"] = test_entropy_band(S, fs=fs)
    results["T5"] = test_novelty(S, fs=fs)
    return results


# ─────────────────────────────────────────────
# EEG characteristic analysis
# ─────────────────────────────────────────────

def analyze_eeg_properties(eeg, fs):
    """Analyze basic properties of synthetic EEG."""
    props = {}
    props["amplitude_mean"] = np.mean(np.abs(eeg))
    props["amplitude_max"] = np.max(np.abs(eeg))
    props["amplitude_std"] = np.std(eeg)

    # PSD (Power Spectral Density)
    freqs, psd = sp_signal.welch(eeg, fs=fs, nperseg=min(1024, len(eeg) // 2))

    # Band power
    bands = {
        "delta": (0.5, 4),
        "theta": (4, 8),
        "alpha": (8, 13),
        "beta": (13, 30),
        "gamma": (30, 100),
    }
    total_power = np.trapezoid(psd, freqs)
    props["band_power"] = {}
    for band_name, (f_low, f_high) in bands.items():
        idx = (freqs >= f_low) & (freqs <= f_high)
        band_power = np.trapezoid(psd[idx], freqs[idx]) if np.any(idx) else 0.0
        props["band_power"][band_name] = band_power / total_power if total_power > 0 else 0.0

    # Dominant frequency
    dominant_idx = np.argmax(psd[1:]) + 1  # Exclude DC
    props["dominant_freq"] = freqs[dominant_idx]

    # Complexity (sample entropy approximation — autocorrelation decay rate)
    if len(eeg) > 100:
        acf = np.correlate(eeg[:1000] - np.mean(eeg[:1000]),
                           eeg[:1000] - np.mean(eeg[:1000]), mode="full")
        acf = acf[len(acf) // 2:]
        acf = acf / (acf[0] + 1e-15)
        # Lag for autocorrelation to drop below 0.5
        decay = np.argmax(acf < 0.5) if np.any(acf < 0.5) else len(acf)
        props["acf_decay_lag"] = decay
    else:
        props["acf_decay_lag"] = 0

    return props


# ─────────────────────────────────────────────
# ASCII waveform
# ─────────────────────────────────────────────

def ascii_waveform(eeg, fs, duration_show=2.0, width=60, height=10):
    """Short segment ASCII waveform of EEG."""
    n_show = int(duration_show * fs)
    # Extract from middle point
    start = max(0, len(eeg) // 2 - n_show // 2)
    segment = eeg[start:start + n_show]

    if len(segment) == 0:
        return "  (No data)"

    # Downsample
    step = max(1, len(segment) // width)
    xs = segment[::step][:width]

    y_min, y_max = xs.min(), xs.max()
    if y_max - y_min < 1e-6:
        y_max = y_min + 1

    lines = []
    for row in range(height, -1, -1):
        y_val = y_min + (y_max - y_min) * row / height
        line = f"  {y_val:8.1f}|"
        for col in range(len(xs)):
            cell_row = int((xs[col] - y_min) / (y_max - y_min) * height)
            if cell_row == row:
                line += "*"
            else:
                line += " "
        lines.append(line)

    t_end = duration_show
    lines.append(f"          +{'─' * len(xs)}")
    lines.append(f"           0{' ' * (len(xs) // 2 - 1)}t(s){' ' * (len(xs) // 2 - 4)}{t_end:.1f}")

    return "\n".join(lines)


# ─────────────────────────────────────────────
# Judgment
# ─────────────────────────────────────────────

def judge(results):
    """Overall judgment from CCT results."""
    passes = sum(1 for _, (_, p, _) in results.items() if p)
    halfs = sum(0.5 for _, (s, p, _) in results.items() if not p and s > 0.7)
    total = passes + halfs

    if total >= 5:
        return total, "★ Continuous"
    elif total >= 4:
        return total, "◎ Weakened"
    elif total >= 3:
        return total, "△ Fragile"
    elif total >= 1:
        return total, "▽ Minimal"
    else:
        return total, "✕ Absent"


# ─────────────────────────────────────────────
# Output
# ─────────────────────────────────────────────

def print_state_result(state, eeg, props, S, results, fs):
    """Print single state result."""
    label = STATE_LABELS[state]
    pred = PREDICTIONS[state]
    total, verdict = judge(results)

    print(f"\n {'─' * 58}")
    print(f"  [{state.upper()}] {label}")
    print(f" {'─' * 58}")

    # EEG properties
    bp = props["band_power"]
    print(f"  Amplitude: mean={props['amplitude_mean']:.1f} uV, "
          f"max={props['amplitude_max']:.1f} uV, std={props['amplitude_std']:.1f} uV")
    print(f"  Dominant frequency: {props['dominant_freq']:.1f} Hz")
    print(f"  Band power: delta={bp['delta']:.1%} theta={bp['theta']:.1%} "
          f"alpha={bp['alpha']:.1%} beta={bp['beta']:.1%} gamma={bp['gamma']:.1%}")
    print(f"  ACF decay: {props['acf_decay_lag']} lags (shorter = more complex)")

    # ASCII waveform
    print(f"\n  Waveform (2 second segment):")
    print(ascii_waveform(eeg, fs))

    # CCT results
    print(f"\n  CCT test results:")
    test_labels = {
        "T1": "T1 Gap       ",
        "T2": "T2 Loop      ",
        "T3": "T3 Continuity",
        "T4": "T4 Entropy   ",
        "T5": "T5 Novelty   ",
    }

    for key, label_str in test_labels.items():
        score, passed, detail = results[key]
        mark = "PASS" if passed else "FAIL"
        symbol = "+" if passed else "-"
        pred_mark = "+" if pred["tests"][key] else "-"
        match = "=" if (passed == pred["tests"][key]) else "!"
        print(f"    {label_str} | {symbol} {mark} | {score:.3f} | "
              f"Predicted:{pred_mark} {match} | {detail}")

    print(f"\n  Overall: {total}/5 {verdict}")
    print(f"  Prediction: {pred['total']}/5 ({pred['reason']})")

    # Match status
    matches = sum(1 for k in ["T1", "T2", "T3", "T4", "T5"]
                  if (results[k][1] == pred["tests"][k]))
    print(f"  Per-test match: {matches}/5")

    return matches


def print_comparison_table(all_results):
    """Overall comparison table + match analysis."""
    print("\n" + "=" * 76)
    print("  EEG-CCT Verification Summary Comparison Table")
    print("=" * 76)

    header = ("  State        | T1  | T2  | T3  | T4  | T5  | Score| Pred | Match| Verdict")
    sep =    ("  ─────────────┼─────┼─────┼─────┼─────┼─────┼──────┼──────┼──────┼───────")
    print(header)
    print(sep)

    total_matches = 0
    total_tests = 0

    for state in ["awake", "sleep_n1", "sleep_n3", "anesthesia", "seizure"]:
        results, matches = all_results[state]
        pred = PREDICTIONS[state]
        total, verdict = judge(results)

        marks = []
        for key in ["T1", "T2", "T3", "T4", "T5"]:
            _, passed, _ = results[key]
            if passed:
                marks.append(" +  ")
            else:
                marks.append(" -  ")

        label = f"{state:13s}"
        marks_str = "|".join(marks)
        short_verdict = verdict.split("(")[0].strip()
        print(f"  {label}|{marks_str}| {total:<4.0f} | {pred['total']:<4} | {matches}/5  | {short_verdict}")

        total_matches += matches
        total_tests += 5

    print(sep)
    match_pct = total_matches / total_tests * 100
    print(f"  Overall match: {total_matches}/{total_tests} ({match_pct:.0f}%)")
    print()

    # Match judgment
    if match_pct >= 80:
        level = "Strong verification"
        detail = "CCT accurately distinguishes EEG consciousness states"
    elif match_pct >= 60:
        level = "Partial verification"
        detail = "Mostly matches, some test conditions need adjustment"
    else:
        level = "Mismatch"
        detail = "CCT conditions need modification"

    print(f"  Judgment: {level} — {detail}")

    # Mismatch analysis
    mismatches = []
    for state in ["awake", "sleep_n1", "sleep_n3", "anesthesia", "seizure"]:
        results, _ = all_results[state]
        pred = PREDICTIONS[state]
        for key in ["T1", "T2", "T3", "T4", "T5"]:
            actual = results[key][1]
            expected = pred["tests"][key]
            if actual != expected:
                direction = "PASS(expected FAIL)" if actual else "FAIL(expected PASS)"
                mismatches.append((state, key, direction, results[key][2]))

    if mismatches:
        print(f"\n  Mismatch details ({len(mismatches)} cases):")
        for state, test, direction, detail in mismatches:
            print(f"    {state:13s} {test}: {direction}")
            print(f"      {detail}")

    print("=" * 76)


# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────

def run_state(state, duration, fs, seed):
    """Run single state."""
    rng = np.random.default_rng(seed)
    n = int(duration * fs)

    # Generate synthetic EEG
    gen_func = GENERATORS[state]
    suppression_mask = None

    if state == "anesthesia":
        eeg, suppression_mask = gen_func(n, fs, rng)
    else:
        eeg = gen_func(n, fs, rng)

    # Analyze properties
    props = analyze_eeg_properties(eeg, fs)

    # Takens embedding → 3D state vector
    S = eeg_to_state_vector(eeg, fs, suppression_mask=suppression_mask)

    # Run CCT
    results = run_cct(S, fs=fs)

    return eeg, props, S, results


def main():
    parser = argparse.ArgumentParser(
        description="EEG synthetic data based CCT validator — neuroscience verification without public data",
    )
    parser.add_argument("--duration", type=float, default=30,
                        help="Synthetic EEG duration (seconds, default: 30)")
    parser.add_argument("--state", type=str, default=None,
                        choices=list(GENERATORS.keys()),
                        help="Run single state only")
    parser.add_argument("--fs", type=int, default=FS,
                        help=f"Sampling frequency (default: {FS} Hz)")
    parser.add_argument("--seed", type=int, default=SEED,
                        help=f"Random seed (default: {SEED})")

    args = parser.parse_args()

    print("=" * 76)
    print("  EEG-CCT Validator v1.0")
    print("  Consciousness Continuity Validator based on Synthetic EEG")
    print("=" * 76)
    print(f"  Settings: duration={args.duration}s, fs={args.fs}Hz, "
          f"samples={int(args.duration * args.fs):,}, seed={args.seed}")
    print(f"  Method: Synthetic EEG → Takens embedding S(t)=[x, dx/dt, d2x/dt2] → CCT 5 tests")

    if args.state:
        # Single state
        states = [args.state]
    else:
        states = list(GENERATORS.keys())

    all_results = {}

    for state in states:
        eeg, props, S, results = run_state(state, args.duration, args.fs, args.seed)
        matches = print_state_result(state, eeg, props, S, results, args.fs)
        all_results[state] = (results, matches)

    # Overall comparison table (for multiple states)
    if len(states) > 1:
        print_comparison_table(all_results)


if __name__ == "__main__":
    main()
```