#!/usr/bin/env python3
"""H-CX-18 Verification: Internal/Inter Tension Duality Quantification

Train 2 PureFieldEngines → on normal/anomaly data:
- Internal tension (engine_A vs engine_G within same model)
- Inter tension (model1 vs model2 output difference)
to verify duality.

Prediction: normal→internal↑,inter↓ / anomaly→internal↓,inter↑
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from model_pure_field import PureFieldEngine
from model_utils import load_mnist
from scipy import stats as sp_stats

def train_model(model, train_loader, epochs=15, lr=0.001):
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    criterion = nn.CrossEntropyLoss()
    for epoch in range(epochs):
        model.train()
        for X, y in train_loader:
            X = X.view(X.size(0), -1)
            optimizer.zero_grad()
            logits, tension = model(X)
            loss = criterion(logits, y)
            loss.backward()
            optimizer.step()
    return model

def collect_duality_data(model_1, model_2, test_loader, normal_classes, anomaly_classes):
    """Collect internal and inter-model tension for normal vs anomaly."""
    results = {'normal': {'internal_1': [], 'internal_2': [], 'inter': []},
               'anomaly': {'internal_1': [], 'internal_2': [], 'inter': []}}

    model_1.eval()
    model_2.eval()

    with torch.no_grad():
        for X, y in test_loader:
            X_flat = X.view(X.size(0), -1)

            # Model 1 internals
            out_a1 = model_1.engine_a(X_flat)
            out_g1 = model_1.engine_g(X_flat)
            internal_1 = ((out_a1 - out_g1) ** 2).mean(dim=-1)

            # Model 2 internals
            out_a2 = model_2.engine_a(X_flat)
            out_g2 = model_2.engine_g(X_flat)
            internal_2 = ((out_a2 - out_g2) ** 2).mean(dim=-1)

            # Inter-model tension (output difference)
            logits_1, _ = model_1(X_flat)
            logits_2, _ = model_2(X_flat)
            inter = ((logits_1 - logits_2) ** 2).mean(dim=-1)

            for i in range(len(y)):
                label = y[i].item()
                key = 'normal' if label in normal_classes else 'anomaly'
                results[key]['internal_1'].append(internal_1[i].item())
                results[key]['internal_2'].append(internal_2[i].item())
                results[key]['inter'].append(inter[i].item())

    for key in results:
        for sub in results[key]:
            results[key][sub] = np.array(results[key][sub])

    return results

def print_duality_table(results, title):
    """Print duality comparison table."""
    print(f"\n  === {title} ===")
    print(f"  {'Metric':>15} {'Normal':>12} {'Anomaly':>12} {'Ratio(N/A)':>12} {'Direction':>10}")
    print(f"  {'─'*15} {'─'*12} {'─'*12} {'─'*12} {'─'*10}")

    metrics = [
        ('internal_1', 'Internal T1'),
        ('internal_2', 'Internal T2'),
        ('inter', 'Inter-model'),
    ]

    for key, name in metrics:
        n_mean = results['normal'][key].mean()
        a_mean = results['anomaly'][key].mean()
        ratio = n_mean / (a_mean + 1e-10)
        direction = '↑' if n_mean > a_mean else '↓'
        print(f"  {name:>15} {n_mean:>12.4f} {a_mean:>12.4f} {ratio:>12.2f} {direction:>10}")

def ascii_duality_plot(results):
    """ASCII visualization of duality."""
    n_int = (results['normal']['internal_1'].mean() + results['normal']['internal_2'].mean()) / 2
    a_int = (results['anomaly']['internal_1'].mean() + results['anomaly']['internal_2'].mean()) / 2
    n_inter = results['normal']['inter'].mean()
    a_inter = results['anomaly']['inter'].mean()

    max_val = max(n_int, a_int, n_inter, a_inter)
    scale = 40 / (max_val + 1e-10)

    print(f"\n  === Duality Visualization ===")
    print(f"  (bar length = tension magnitude)")
    print()
    print(f"  Internal tension:")
    print(f"    Normal:  {'█' * int(n_int * scale)} {n_int:.4f}")
    print(f"    Anomaly: {'█' * int(a_int * scale)} {a_int:.4f}")
    print()
    print(f"  Inter-model tension:")
    print(f"    Normal:  {'░' * int(n_inter * scale)} {n_inter:.4f}")
    print(f"    Anomaly: {'░' * int(a_inter * scale)} {a_inter:.4f}")
    print()

    # Check duality
    internal_dir = 'Normal > Anomaly' if n_int > a_int else 'Anomaly > Normal'
    inter_dir = 'Normal > Anomaly' if n_inter > a_inter else 'Anomaly > Normal'

    duality = (n_int > a_int and a_inter > n_inter)
    print(f"  Internal: {internal_dir}")
    print(f"  Inter:    {inter_dir}")
    print(f"  Duality confirmed: {'YES! (internal↑inter↓ vs internal↓inter↑)' if duality else 'NO'}")

if __name__ == '__main__':
    print("=" * 60)
    print("  H-CX-18: Internal/Inter Tension Duality")
    print("  Prediction: normal→internal↑,inter↓ / anomaly→internal↓,inter↑")
    print("=" * 60)

    train_loader, test_loader = load_mnist(batch_size=128)

    # Experiment 1: digits 0-7 = normal, 8-9 = anomaly
    configs = [
        ('0-7 vs 8-9', set(range(8)), {8, 9}),
        ('0-4 vs 5-9', set(range(5)), set(range(5, 10))),
        ('even vs odd', {0, 2, 4, 6, 8}, {1, 3, 5, 7, 9}),
    ]

    all_results = []

    for trial in range(3):
        print(f"\n  ─── Trial {trial+1}/3 ───")

        # Train 2 independent models
        model_1 = PureFieldEngine(784, 128, 10)
        model_2 = PureFieldEngine(784, 128, 10)
        model_1 = train_model(model_1, train_loader, epochs=15)
        model_2 = train_model(model_2, train_loader, epochs=15)

        for config_name, normal_cls, anomaly_cls in configs:
            print(f"\n  Config: {config_name}")
            results = collect_duality_data(model_1, model_2, test_loader, normal_cls, anomaly_cls)
            print_duality_table(results, config_name)

            if trial == 2:  # Last trial
                ascii_duality_plot(results)

            # Statistical test
            for key_name in ['internal_1', 'inter']:
                t_stat, p_val = sp_stats.mannwhitneyu(
                    results['normal'][key_name], results['anomaly'][key_name],
                    alternative='two-sided'
                )
                print(f"    Mann-Whitney U ({key_name}): p={p_val:.2e}")

            all_results.append({
                'config': config_name,
                'trial': trial,
                'n_int': (results['normal']['internal_1'].mean() + results['normal']['internal_2'].mean()) / 2,
                'a_int': (results['anomaly']['internal_1'].mean() + results['anomaly']['internal_2'].mean()) / 2,
                'n_inter': results['normal']['inter'].mean(),
                'a_inter': results['anomaly']['inter'].mean(),
            })

    # Final summary
    print(f"\n{'='*60}")
    print(f"  === FINAL SUMMARY ===")
    print(f"{'='*60}")
    print(f"  {'Config':>12} {'T':>3} {'IntN':>8} {'IntA':>8} {'InterN':>8} {'InterA':>8} {'Dual?':>6}")
    print(f"  {'─'*12} {'─'*3} {'─'*8} {'─'*8} {'─'*8} {'─'*8} {'─'*6}")

    duality_count = 0
    total = 0
    for r in all_results:
        dual = r['n_int'] > r['a_int'] and r['a_inter'] > r['n_inter']
        if dual:
            duality_count += 1
        total += 1
        d = 'YES' if dual else 'no'
        print(f"  {r['config']:>12} {r['trial']+1:>3} {r['n_int']:>8.4f} {r['a_int']:>8.4f} {r['n_inter']:>8.4f} {r['a_inter']:>8.4f} {d:>6}")

    print(f"\n  Duality confirmed: {duality_count}/{total} ({duality_count/total*100:.0f}%)")

    if duality_count / total >= 0.7:
        print(f"  Conclusion: H-CX-18 confirmed! Internal/inter tension duality exists")
    elif duality_count / total >= 0.4:
        print(f"  Conclusion: H-CX-18 partially confirmed (conditional)")
    else:
        print(f"  Conclusion: H-CX-18 refuted")