#!/usr/bin/env python3
"""
EEG Analyzer for TECS-L G=D×P/I Model Verification

Computes band power, asymmetry, and maps to G=D×P/I parameters.

Usage:
    source eeg_env/bin/activate
    python eeg/analyze.py eeg/data/eeg_20260327_143000.npy
    python eeg/analyze.py eeg/data/eeg_20260327_143000.npy --topomap
"""

import argparse
import json
import os
import sys

import numpy as np
import matplotlib
matplotlib.use('Agg')  # non-interactive backend
import matplotlib.pyplot as plt
from scipy import signal


BANDS = {
    'delta':  (0.5, 4),
    'theta':  (4, 8),
    'alpha':  (8, 12),
    'beta':   (13, 30),
    'gamma':  (30, 100),
}


def load_recording(filepath):
    """Load EEG recording + metadata."""
    base = filepath.replace('.npy', '').replace('.csv', '').replace('_meta.json', '')

    data = np.load(f"{base}.npy")
    with open(f"{base}_meta.json", 'r') as f:
        meta = json.load(f)

    return data, meta


def compute_band_power(data, sample_rate, bands=BANDS):
    """Compute power spectral density per channel per band."""
    n_channels, n_samples = data.shape
    results = {}

    for band_name, (fmin, fmax) in bands.items():
        powers = []
        for ch in range(n_channels):
            # Welch PSD
            freqs, psd = signal.welch(data[ch], fs=sample_rate, nperseg=min(256, n_samples))
            # Band power
            idx = np.logical_and(freqs >= fmin, freqs <= fmax)
            bp = np.trapezoid(psd[idx], freqs[idx])
            powers.append(bp)
        results[band_name] = np.array(powers)

    return results


def compute_total_power(band_powers):
    """Compute total power per channel."""
    total = None
    for bp in band_powers.values():
        if total is None:
            total = bp.copy()
        else:
            total += bp
    return total


def compute_relative_power(band_powers):
    """Compute relative band power (fraction of total)."""
    total = compute_total_power(band_powers)
    relative = {}
    for band_name, bp in band_powers.items():
        relative[band_name] = bp / (total + 1e-12)
    return relative


def compute_asymmetry(band_powers, ch_labels):
    """Compute hemispheric asymmetry for each band.
    Asymmetry = ln(Right) - ln(Left) for matched electrode pairs.
    """
    # Standard 10-20 pairs (Left-Right)
    pairs = [
        ('Fp1', 'Fp2'), ('F3', 'F4'), ('F7', 'F8'),
        ('C3', 'C4'), ('T7', 'T8'),
        ('P3', 'P4'), ('P7', 'P8'),
        ('O1', 'O2'),
    ]

    ch_idx = {name: i for i, name in enumerate(ch_labels)}
    asymmetry = {}

    for band_name, bp in band_powers.items():
        asym_values = {}
        for left, right in pairs:
            if left in ch_idx and right in ch_idx:
                l_power = bp[ch_idx[left]]
                r_power = bp[ch_idx[right]]
                # ln(R) - ln(L), positive = right dominant
                asym = np.log(r_power + 1e-12) - np.log(l_power + 1e-12)
                asym_values[f"{left}-{right}"] = asym
        asymmetry[band_name] = asym_values

    return asymmetry


def map_to_gdpi(band_powers, relative_powers, asymmetry, ch_labels):
    """
    Map EEG features to G=D×P/I model parameters.

    Mapping hypothesis:
        I (Inhibition)  = Alpha power (frontal) — higher alpha = more inhibition
        P (Plasticity)  = Gamma power (global)  — higher gamma = more plasticity
        D (Deficit)     = Alpha asymmetry       — asymmetry indicates deficit pattern
        G (Genius)      = D × P / I
    """
    ch_idx = {name: i for i, name in enumerate(ch_labels)}

    # I = Frontal Alpha relative power
    frontal_chs = [ch_idx[c] for c in ['Fp1', 'Fp2', 'F3', 'F4'] if c in ch_idx]
    if frontal_chs:
        I = np.mean(relative_powers['alpha'][frontal_chs])
    else:
        I = np.mean(relative_powers['alpha'])

    # P = Global Gamma relative power
    P = np.mean(relative_powers['gamma'])

    # D = Alpha frontal asymmetry magnitude (|ln(R) - ln(L)|)
    alpha_asym = asymmetry.get('alpha', {})
    frontal_pairs = ['Fp1-Fp2', 'F3-F4', 'F7-F8']
    asym_vals = [abs(alpha_asym[p]) for p in frontal_pairs if p in alpha_asym]
    D = np.mean(asym_vals) if asym_vals else 0.0

    # G = D × P / I
    G = D * P / (I + 1e-12)

    # Golden Zone check (0.2123 < G < 0.5)
    golden_lower = 0.5 - np.log(4/3)  # 0.2123
    golden_upper = 0.5
    in_golden_zone = golden_lower <= G <= golden_upper

    return {
        'I_inhibition': float(I),
        'P_plasticity': float(P),
        'D_deficit': float(D),
        'G_genius': float(G),
        'in_golden_zone': in_golden_zone,
        'golden_zone': [golden_lower, golden_upper],
    }


def plot_band_power(band_powers, ch_labels, output_path):
    """Plot band power heatmap."""
    bands = list(band_powers.keys())
    n_ch = len(ch_labels)

    matrix = np.array([band_powers[b] for b in bands])
    # Normalize per band for visualization
    for i in range(len(bands)):
        row_max = matrix[i].max()
        if row_max > 0:
            matrix[i] /= row_max

    fig, ax = plt.subplots(figsize=(max(12, n_ch * 0.8), 5))
    im = ax.imshow(matrix, aspect='auto', cmap='YlOrRd')
    ax.set_xticks(range(n_ch))
    ax.set_xticklabels(ch_labels, rotation=45, ha='right')
    ax.set_yticks(range(len(bands)))
    ax.set_yticklabels(bands)
    ax.set_title('Normalized Band Power per Channel')
    plt.colorbar(im, ax=ax, label='Relative Power')
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    print(f"  Band power heatmap: {output_path}")


def plot_topomap(band_powers, ch_labels, output_path):
    """Plot EEG topomap using MNE."""
    try:
        import mne
    except ImportError:
        print("  MNE not installed, skipping topomap")
        return

    # Create MNE info with standard 10-20 montage
    valid_chs = []
    valid_idx = []
    montage = mne.channels.make_standard_montage('standard_1020')
    montage_names = [ch.upper() for ch in montage.ch_names]

    for i, ch in enumerate(ch_labels):
        if ch.upper() in montage_names:
            valid_chs.append(ch)
            valid_idx.append(i)

    if not valid_chs:
        print("  No valid 10-20 channels for topomap")
        return

    info = mne.create_info(valid_chs, sfreq=250, ch_types='eeg')
    info.set_montage(montage)

    bands = list(band_powers.keys())
    fig, axes = plt.subplots(1, len(bands), figsize=(4 * len(bands), 4))
    if len(bands) == 1:
        axes = [axes]

    for ax, band_name in zip(axes, bands):
        bp = band_powers[band_name][valid_idx]
        mne.viz.plot_topomap(bp, info, axes=ax, show=False, cmap='RdBu_r')
        ax.set_title(band_name)

    plt.suptitle('EEG Topomap by Frequency Band')
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    print(f"  Topomap: {output_path}")


def print_report(band_powers, relative_powers, asymmetry, gdpi, ch_labels):
    """Print ASCII analysis report."""
    print("\n" + "=" * 70)
    print("  EEG ANALYSIS REPORT — TECS-L G=D×P/I Model")
    print("=" * 70)

    # Band power table
    print("\n--- Absolute Band Power (uV^2/Hz) ---\n")
    header = f"{'Channel':<8}"
    for band in BANDS:
        header += f"{band:>10}"
    print(header)
    print("-" * len(header))

    for i, ch in enumerate(ch_labels):
        row = f"{ch:<8}"
        for band in BANDS:
            row += f"{band_powers[band][i]:>10.2f}"
        print(row)

    # Relative power
    print("\n--- Relative Band Power (%) ---\n")
    header = f"{'Channel':<8}"
    for band in BANDS:
        header += f"{band:>10}"
    print(header)
    print("-" * len(header))

    for i, ch in enumerate(ch_labels):
        row = f"{ch:<8}"
        for band in BANDS:
            row += f"{relative_powers[band][i]*100:>9.1f}%"
        print(row)

    # Asymmetry
    print("\n--- Alpha Asymmetry (ln(R)-ln(L)) ---\n")
    alpha_asym = asymmetry.get('alpha', {})
    for pair, val in alpha_asym.items():
        direction = "R>L" if val > 0 else "L>R"
        bar_len = int(abs(val) * 20)
        bar = "#" * min(bar_len, 30)
        print(f"  {pair:<10} {val:>+.4f}  {direction}  |{bar}")

    # G=D×P/I mapping
    print("\n--- G=D×P/I Model Mapping ---\n")
    print(f"  I (Inhibition)  = {gdpi['I_inhibition']:.6f}  (frontal alpha)")
    print(f"  P (Plasticity)  = {gdpi['P_plasticity']:.6f}  (global gamma)")
    print(f"  D (Deficit)     = {gdpi['D_deficit']:.6f}  (alpha asymmetry)")
    print(f"  G (Genius)      = {gdpi['G_genius']:.6f}  (D×P/I)")
    print()
    gz = gdpi['golden_zone']
    print(f"  Golden Zone: [{gz[0]:.4f}, {gz[1]:.4f}]")
    if gdpi['in_golden_zone']:
        print(f"  >>> IN GOLDEN ZONE <<<")
    else:
        if gdpi['G_genius'] < gz[0]:
            print(f"  Below Golden Zone (need +{gz[0] - gdpi['G_genius']:.4f})")
        else:
            print(f"  Above Golden Zone (excess +{gdpi['G_genius'] - gz[1]:.4f})")

    print("\n" + "=" * 70)


def main():
    parser = argparse.ArgumentParser(description='EEG Analyzer for TECS-L')
    parser.add_argument('filepath', help='Path to .npy recording file')
    parser.add_argument('--topomap', action='store_true', help='Generate MNE topomap')
    parser.add_argument('--no-plot', action='store_true', help='Skip all plots')
    args = parser.parse_args()

    # Load
    print(f"Loading: {args.filepath}")
    data, meta = load_recording(args.filepath)
    ch_labels = meta['channels']
    sample_rate = meta['sample_rate']
    print(f"  {meta['n_channels']}ch, {sample_rate}Hz, {meta['duration_sec']}s, tag={meta['tag']}")

    # Analyze
    band_powers = compute_band_power(data, sample_rate)
    relative_powers = compute_relative_power(band_powers)
    asymmetry = compute_asymmetry(band_powers, ch_labels)
    gdpi = map_to_gdpi(band_powers, relative_powers, asymmetry, ch_labels)

    # Report
    print_report(band_powers, relative_powers, asymmetry, gdpi, ch_labels)

    # Plots
    if not args.no_plot:
        base = args.filepath.replace('.npy', '').replace('.csv', '')
        plot_band_power(band_powers, ch_labels, f"{base}_bandpower.png")
        if args.topomap:
            plot_topomap(band_powers, ch_labels, f"{base}_topomap.png")

    # Save analysis results
    base = args.filepath.replace('.npy', '').replace('.csv', '')
    gdpi_serializable = {k: (bool(v) if isinstance(v, (bool, np.bool_)) else v) for k, v in gdpi.items()}
    results = {
        'gdpi': gdpi_serializable,
        'band_power_mean': {b: float(np.mean(bp)) for b, bp in band_powers.items()},
        'relative_power_mean': {b: float(np.mean(rp)) for b, rp in relative_powers.items()},
        'asymmetry': {b: {k: float(v) for k, v in asym.items()} for b, asym in asymmetry.items()},
    }
    results_path = f"{base}_analysis.json"
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\n  Analysis saved: {results_path}")


if __name__ == '__main__':
    main()
