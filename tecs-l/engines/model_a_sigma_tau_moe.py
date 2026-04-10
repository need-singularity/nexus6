#!/usr/bin/env python3
"""Model A: σ(6)-τ(6) MoE — MoE structure determined by divisor functions of perfect number 6

Mathematical basis:
  Divisor functions of perfect number 6:
    σ(6) = 1+2+3+6 = 12  (sum of divisors → Number of Experts)
    τ(6) = |{1,2,3,6}| = 4  (number of divisors → Number of active Experts)

  Conventional MoE (Shazeer 2017): 8 Experts, k=2 (ad hoc choice)
  σ-τ MoE: 12 Experts, k=4 (derived from perfect number 6)

  Active ratio = τ(6)/σ(6) = 4/12 = 1/3 — Matches meta fixed point!
  Fixed point of f(I) = 0.7I + 0.1 is I = 1/3.
  This model tests the natural ratio of "4 active out of 12".

Benchmark:
  σ-τ MoE (12 experts, k=4) vs Top-K (8 experts, k=2) vs Dense
  To match parameter counts, hidden_dim of 12-expert model is reduced.
"""

import torch
from model_utils import (
    Expert, TopKGate, BaseMoE, DenseModel,
    load_mnist, train_and_evaluate, compare_results, count_params,
    SIGMA, TAU,
)

INPUT_DIM = 784
OUTPUT_DIM = 10
EPOCHS = 10


def build_sigma_tau_moe(hidden_dim=48):
    """σ(6)=12 experts, τ(6)=4 active."""
    gate = TopKGate(INPUT_DIM, n_experts=SIGMA, k=TAU)
    model = BaseMoE(INPUT_DIM, hidden_dim, OUTPUT_DIM, n_experts=SIGMA, gate=gate)
    return model


def build_topk_baseline(hidden_dim=64):
    """Standard Top-K MoE: 8 experts, k=2."""
    gate = TopKGate(INPUT_DIM, n_experts=8, k=2)
    model = BaseMoE(INPUT_DIM, hidden_dim, OUTPUT_DIM, n_experts=8, gate=gate)
    return model


def build_dense(hidden_dim=256):
    """Dense baseline."""
    return DenseModel(INPUT_DIM, hidden_dim, OUTPUT_DIM)


def main():
    print("=" * 70)
    print("  Model A: σ(6)-τ(6) MoE  —  Expert=σ(6)=12, Active=τ(6)=4")
    print("  Active ratio = τ/σ = 4/12 = 1/3 (meta fixed point)")
    print("=" * 70)

    train_loader, test_loader = load_mnist()

    # ── Parameter count adjustment ──
    # Dense(256) ≈ 203K params
    # TopK(8, hidden=64) ≈ 8*(784*64+64*10) + 784*8 ≈ 412K
    # σ-τ(12, hidden=48) ≈ 12*(784*48+48*10) + 784*12 ≈ 467K
    # Adjust hidden_dim to match approximately

    models = {
        'σ-τ MoE (12e, k=4)': build_sigma_tau_moe(hidden_dim=48),
        'Top-K MoE (8e, k=2)': build_topk_baseline(hidden_dim=64),
        'Dense baseline': build_dense(hidden_dim=256),
    }

    results = {}
    for name, model in models.items():
        params = count_params(model)
        print(f"\n── {name} (params={params:,}) ──")
        losses, accs = train_and_evaluate(model, train_loader, test_loader, epochs=EPOCHS)

        result = {
            'acc': accs[-1],
            'loss': losses[-1],
            'params': params,
        }

        # Add metrics if MoE model
        if isinstance(model, BaseMoE):
            metrics = model.get_metrics()
            result.update(metrics)
            print(f"    Active ratio: {metrics['active_ratio']:.3f}")
            print(f"    I_effective:  {metrics['I_effective']:.3f}")
            active_ratio = metrics['active_ratio']
            target = TAU / SIGMA  # 1/3
            print(f"    Target ratio: {target:.3f} (τ/σ = {TAU}/{SIGMA})")
            print(f"    Deviation:    {abs(active_ratio - target):.4f}")

        results[name] = result

    compare_results(results)

    # ── σ-τ specific analysis ──
    print("\n── σ-τ Structure Analysis ──")
    print(f"  σ(6) = {SIGMA} experts (sum of divisors)")
    print(f"  τ(6) = {TAU} active  (number of divisors)")
    print(f"  Active ratio = {TAU}/{SIGMA} = {TAU/SIGMA:.4f} ≈ 1/3")
    print(f"  Meta fixed point f(I)=0.7I+0.1 → I*=1/3 = {1/3:.4f}")

    st_acc = results['σ-τ MoE (12e, k=4)']['acc']
    tk_acc = results['Top-K MoE (8e, k=2)']['acc']
    diff = st_acc - tk_acc
    print(f"\n  σ-τ vs Top-K: {diff*100:+.2f}%")
    if diff > 0:
        print("  → σ-τ structure is superior ✓")
    else:
        print("  → Top-K is superior (consider hidden_dim difference)")


if __name__ == '__main__':
    main()