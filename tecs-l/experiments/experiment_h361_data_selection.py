#!/usr/bin/env python3
"""H361 Data Selection Simulation — Byte Entropy vs Tension Dynamics

Feed various data as bytes to PureFieldEngine without learning
to measure which data creates the richest tension dynamics.

Golden Zone hypothesis: A golden zone of data entropy exists,
within which tension variation is maximized.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import torch
import torch.nn.functional as F
import numpy as np
import math
from model_pure_field import PureFieldEngine

def bytes_to_tensor(data_bytes, dim=128):
    """Convert byte sequence to (N, dim) tensor."""
    arr = np.frombuffer(data_bytes, dtype=np.uint8).astype(np.float32) / 255.0
    # Padding or trimming
    n_samples = max(1, len(arr) // dim)
    arr = arr[:n_samples * dim]
    return torch.tensor(arr.reshape(n_samples, dim))

def byte_entropy(data_bytes):
    """Byte level Shannon entropy (nats)."""
    counts = np.zeros(256)
    for b in data_bytes:
        counts[b] += 1
    probs = counts / counts.sum()
    probs = probs[probs > 0]
    return -np.sum(probs * np.log(probs))

def byte_ngram_diversity(data_bytes, n=2):
    """n-gram diversity (unique n-gram ratio)."""
    if len(data_bytes) < n:
        return 0
    ngrams = set()
    for i in range(len(data_bytes) - n + 1):
        ngrams.add(tuple(data_bytes[i:i+n]))
    return len(ngrams) / (len(data_bytes) - n + 1)

def measure_tension_dynamics(model, data_tensor, max_samples=200):
    """Measure tension statistics for data."""
    model.eval()
    tensions = []
    directions = []

    with torch.no_grad():
        for i in range(min(len(data_tensor), max_samples)):
            x = data_tensor[i:i+1]
            if x.shape[1] < 784:
                x = F.pad(x, (0, 784 - x.shape[1]))
            elif x.shape[1] > 784:
                x = x[:, :784]

            logits, tension = model(x)
            tensions.append(tension.mean().item())

            # direction diversity
            repulsion = model.engine_a(x) - model.engine_g(x)
            direction = F.normalize(repulsion, dim=-1)
            directions.append(direction.squeeze().numpy())

    tensions = np.array(tensions)
    directions = np.array(directions)

    # direction diversity: avg pairwise cosine distance
    if len(directions) > 1:
        n = min(50, len(directions))
        cos_sims = []
        for i in range(n):
            for j in range(i+1, n):
                cos_sims.append(np.dot(directions[i], directions[j]))
        dir_diversity = 1 - np.mean(cos_sims)  # 0=identical, 1=orthogonal
    else:
        dir_diversity = 0

    return {
        'mean': tensions.mean(),
        'std': tensions.std(),
        'cv': tensions.std() / (tensions.mean() + 1e-8),  # coefficient of variation
        'range': tensions.max() - tensions.min(),
        'iqr': np.percentile(tensions, 75) - np.percentile(tensions, 25),
        'dir_diversity': dir_diversity,
        'richness': tensions.std() * dir_diversity,  # composite metric
        'n': len(tensions),
    }

def generate_synthetic(entropy_target, n_bytes=10000):
    """Generate synthetic data with specific entropy."""
    if entropy_target < 0.5:
        # Very low entropy: almost single byte
        return bytes([42] * n_bytes)
    elif entropy_target < 2.0:
        # Low entropy: use only a few bytes
        k = max(2, int(math.exp(entropy_target)))
        return bytes([i % k for i in range(n_bytes)])
    elif entropy_target < 4.0:
        # Medium entropy: zipf-like distribution
        k = max(4, int(math.exp(entropy_target)))
        weights = [1.0 / (i + 1) for i in range(min(k, 256))]
        total = sum(weights)
        weights = [w / total for w in weights]
        vals = np.random.choice(min(k, 256), size=n_bytes, p=weights)
        return bytes(vals.tolist())
    else:
        # High entropy: almost uniform
        k = min(256, int(math.exp(entropy_target)))
        return bytes(np.random.randint(0, k, size=n_bytes).tolist())

if __name__ == '__main__':
    print("=" * 70)
    print("  H361 Data Selection: Byte Entropy vs Tension Dynamics")
    print("  Golden Zone Hypothesis: Optimal range of data entropy exists")
    print("=" * 70)

    model = PureFieldEngine(784, 128, 10)

    # ═══ 1. Real data comparison ═══
    print("\n  [1/3] Measuring tension by real data types")

    datasets = {}

    # English text
    shakespeare = b"To be, or not to be, that is the question: Whether 'tis nobler in the mind to suffer The slings and arrows of outrageous fortune, Or to take arms against a sea of troubles, And by opposing end them. To die: to sleep; No more; and by a sleep to say we end The heart-ache and the thousand natural shocks That flesh is heir to, 'tis a consummation Devoutly to be wish'd. " * 20
    datasets['English'] = shakespeare

    # Korean text
    korean = "Consciousness is not fixed to a single hardware. Forces exist between consciousnesses. Control rights are transferable. Observation is possible even when pushed out. Consciousness does not disappear. The experience comes first. Math and code are languages created to explain that feeling. ".encode('utf-8') * 20
    datasets['Korean'] = korean

    # Python code
    code = b"""def forward(self, x):
    out_a = self.engine_a(x)
    out_g = self.engine_g(x)
    repulsion = out_a - out_g
    tension = (repulsion ** 2).mean(dim=-1, keepdim=True)
    direction = F.normalize(repulsion, dim=-1)
    output = self.tension_scale * torch.sqrt(tension + 1e-8) * direction
    return output, tension.squeeze()
""" * 30
    datasets['Code'] = code

    # Mixed (all three)
    mixed = shakespeare[:2000] + korean[:2000] + code[:2000]
    datasets['Mixed'] = mixed

    # Math formulas
    math_text = b"sigma(6)=12, tau(6)=4, phi(6)=2, sigma_inv(6)=2. 1/2+1/3+1/6=1. G=D*P/I. golden_zone=[0.2123, 0.5]. ln(4/3)=0.2877. 1/e=0.3679. " * 30
    datasets['Math'] = math_text

    # Random bytes
    random_data = bytes(np.random.randint(0, 256, size=8000).tolist())
    datasets['Random'] = random_data

    # Repetitive
    repetitive = b"aaaaaaa" * 1000
    datasets['Repetitive'] = repetitive

    print(f"\n  {'Data':>12} {'H(bytes)':>9} {'2gram%':>7} | {'T_mean':>8} {'T_std':>8} {'T_cv':>6} {'DirDiv':>7} {'Rich':>7}")
    print(f"  {'─'*12} {'─'*9} {'─'*7} | {'─'*8} {'─'*8} {'─'*6} {'─'*7} {'─'*7}")

    results = {}
    for name, data in datasets.items():
        H = byte_entropy(data)
        ngram = byte_ngram_diversity(data)
        tensor = bytes_to_tensor(data, dim=128)
        stats = measure_tension_dynamics(model, tensor)
        results[name] = {**stats, 'entropy': H, 'ngram': ngram}

        print(f"  {name:>12} {H:>9.4f} {ngram:>6.1%} | {stats['mean']:>8.1f} {stats['std']:>8.1f} {stats['cv']:>6.3f} {stats['dir_diversity']:>7.3f} {stats['richness']:>7.2f}")

    # ═══ 2. Entropy sweep (synthetic data) ═══
    print(f"\n  [2/3] Entropy sweep (synthetic data)")

    sweep_H = [0.1, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 5.5]
    sweep_results = []

    print(f"\n  {'H_target':>9} {'H_actual':>9} | {'T_std':>8} {'DirDiv':>7} {'Rich':>7} {'Plot'}")
    print(f"  {'─'*9} {'─'*9} | {'─'*8} {'─'*7} {'─'*7} {'─'*30}")

    max_rich = 0
    for h_target in sweep_H:
        data = generate_synthetic(h_target)
        H = byte_entropy(data)
        tensor = bytes_to_tensor(data, dim=128)
        stats = measure_tension_dynamics(model, tensor)
        sweep_results.append((h_target, H, stats))
        max_rich = max(max_rich, stats['richness'])

    for h_target, H, stats in sweep_results:
        bar_len = int(stats['richness'] / (max_rich + 1e-8) * 30)
        bar = '█' * bar_len
        print(f"  {h_target:>9.1f} {H:>9.4f} | {stats['std']:>8.1f} {stats['dir_diversity']:>7.3f} {stats['richness']:>7.2f} {bar}")

    # ═══ 3. Golden zone determination ═══
    print(f"\n  [3/3] Data entropy golden zone")

    # Find richest data type
    best_name = max(results, key=lambda k: results[k]['richness'])
    best = results[best_name]

    # Find richest synthetic entropy
    best_synth = max(sweep_results, key=lambda x: x[2]['richness'])

    print(f"\n  Best real data: {best_name} (H={best['entropy']:.4f}, richness={best['richness']:.2f})")
    print(f"  Best synthetic data: H≈{best_synth[1]:.4f} (richness={best_synth[2]['richness']:.2f})")

    # Theoretical golden zone
    gz_lower = 0.5 - math.log(4/3)  # 0.2123 (normalized)
    gz_upper = 0.5
    H_max = math.log(256)  # 5.545 (max byte entropy)

    # Map golden zone to entropy scale
    gz_H_lower = gz_lower * H_max  # ~1.18
    gz_H_upper = gz_upper * H_max  # ~2.77

    print(f"\n  Theoretical golden zone (I scale → H scale):")
    print(f"    I golden zone: [{gz_lower:.4f}, {gz_upper:.4f}]")
    print(f"    H golden zone: [{gz_H_lower:.4f}, {gz_H_upper:.4f}] nats")
    print(f"    H_max = ln(256) = {H_max:.4f}")

    # Check which data types fall in golden zone
    print(f"\n  Golden zone position by data:")
    for name, r in sorted(results.items(), key=lambda x: x[1]['richness'], reverse=True):
        in_gz = gz_H_lower <= r['entropy'] <= gz_H_upper
        marker = " ★ Golden zone!" if in_gz else ""
        bar = '█' * int(r['richness'] / (max_rich + 1e-8) * 20)
        print(f"    {name:>12}: H={r['entropy']:.3f} rich={r['richness']:.2f} {bar}{marker}")

    print(f"\n  === Recommendations ===")
    print(f"  1st: {best_name} (richness={best['richness']:.2f})")
    rank = sorted(results.items(), key=lambda x: x[1]['richness'], reverse=True)
    for i, (name, r) in enumerate(rank[1:], 2):
        print(f"  {i}{'st' if i==2 else 'nd' if i==3 else 'th'}: {name} (richness={r['richness']:.2f})")