#!/usr/bin/env python3
"""CIFAR-10 Tension Causal Experiment — Reproducing C48 on CIFAR"""

import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import torch
import torch.nn as nn
import numpy as np
from model_utils import load_cifar10, train_and_evaluate, count_params
from model_meta_engine import RepulsionFieldQuad

def main():
    print("="*60)
    print("  CIFAR-10 Tension Causal Experiment")
    print("  Does tension=0 crash accuracy on CIFAR too?")
    print("="*60)
    t0 = time.time()

    train_loader, test_loader = load_cifar10(batch_size=128)
    model = RepulsionFieldQuad(input_dim=3072, hidden_dim=96, output_dim=10)
    print(f"  Params: {count_params(model):,}")

    print("\n[1] Training (15 epochs)...")
    losses, accs = train_and_evaluate(model, train_loader, test_loader,
                                       epochs=15, aux_lambda=0.01)
    base_acc = accs[-1]
    print(f"  Baseline accuracy: {base_acc*100:.2f}%")
    print(f"  Tension content: {model.tension_content:.4f}")
    print(f"  Tension structure: {model.tension_structure:.4f}")
    original_scale = model.tension_scale.item()
    print(f"  Learned tension_scale: {original_scale:.4f}")

    print("\n[2] Causal test: varying tension_scale at inference...")
    scales = [0.0, 0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
    results = []

    for factor in scales:
        with torch.no_grad():
            model.tension_scale.fill_(original_scale * factor)
        model.eval()
        correct = total = 0
        with torch.no_grad():
            for X, y in test_loader:
                X = X.view(X.size(0), -1)
                out, _ = model(X)
                correct += (out.argmax(1) == y).sum().item()
                total += y.size(0)
        acc = correct / total
        delta = (acc - base_acc) * 100
        results.append((factor, acc, delta))
        print(f"    scale={factor:>4.1f}x: {acc*100:.2f}% ({delta:+.2f}pp)")

    # Restore
    with torch.no_grad():
        model.tension_scale.fill_(original_scale)

    print("\n[3] Results Table")
    print(f"  {'Scale':>6} | {'Accuracy':>8} | {'Delta':>8} | {'Bar':>20}")
    print(f"  {'-'*6}-+-{'-'*8}-+-{'-'*8}-+-{'-'*20}")
    for factor, acc, delta in results:
        bar = '#' * max(0, int((acc * 100 - 40) * 0.5))
        print(f"  {factor:>5.1f}x | {acc*100:>7.2f}% | {delta:>+7.2f}pp | {bar}")

    # Key metrics
    zero_acc = results[0][1]
    causal_effect = (base_acc - zero_acc) * 100
    error_ratio = (1 - zero_acc) / (1 - base_acc) if base_acc < 1 else float('inf')

    print(f"\n[4] Key Metrics")
    print(f"  Baseline (1.0x): {base_acc*100:.2f}%")
    print(f"  Zero tension:    {zero_acc*100:.2f}%")
    print(f"  Causal effect:   {causal_effect:.2f}pp")
    print(f"  Error ratio:     {error_ratio:.2f}x")
    print(f"  MNIST causal:    9.25pp (C48)")
    print(f"  CIFAR causal:    {causal_effect:.2f}pp")
    print(f"  Ratio:           {causal_effect/9.25:.2f}x MNIST")

    print(f"\n  Elapsed: {time.time()-t0:.1f}s")
    print("="*60)

if __name__ == '__main__':
    main()