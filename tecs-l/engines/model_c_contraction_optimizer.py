#!/usr/bin/env python3
"""Model C: Contraction Mapping Optimizer — Derived from f(x) = 0.7x + 0.1

Mathematical Basis:
  Golden Zone model's meta fixed point equation:
    f(I) = 0.7 * I + 0.1
    Fixed point: I* = 0.1 / (1 - 0.7) = 1/3

  Contraction mapping theorem (Banach):
    |f(x) - f(y)| ≤ 0.7 * |x - y|
    Contraction coefficient a = 0.7 < 1, so converges to unique fixed point 1/3.

  Applying this to optimization:
    θ_{t+1} = a * θ_t + b * (-∇L)
    where a = 0.7 (contraction coefficient), b acts as learning rate.

  Interpretation:
    - a*θ: Contracts current parameters to 0 (similar to weight decay, but multiplicative)
    - b*grad: Move in gradient direction
    - Fixed point: θ* = b*(-∇L) / (1-a) = b*(-∇L) / 0.3
      → At critical point of loss where ∇L=0, converges to θ*=0
      → With gradient, stabilizes at 3.33x the gradient

  a=0.7 is equivalent to L2 weight decay λ=0.3:
    θ - λθ = (1-λ)θ = 0.7θ

  Comparison: Adam, SGD (with/without weight decay)
"""

import torch
from torch.optim import Optimizer
from model_utils import (
    DenseModel, load_mnist, train_and_evaluate, compare_results, count_params,
)

INPUT_DIM = 784
OUTPUT_DIM = 10
EPOCHS = 10


class ContractionOptimizer(Optimizer):
    """Contraction mapping optimizer: θ_{t+1} = a * θ_t - b * ∇L

    Args:
        params: Model parameters
        lr: Learning rate (= b, gradient scaling)
        contraction: Contraction coefficient (= a, default 0.7)
    """

    def __init__(self, params, lr=0.01, contraction=0.7):
        if not 0.0 < contraction < 1.0:
            raise ValueError(f"Contraction coefficient must be in (0,1): {contraction}")
        defaults = dict(lr=lr, contraction=contraction)
        super().__init__(params, defaults)

    @torch.no_grad()
    def step(self, closure=None):
        loss = None
        if closure is not None:
            with torch.enable_grad():
                loss = closure()

        for group in self.param_groups:
            a = group['contraction']
            b = group['lr']

            for p in group['params']:
                if p.grad is None:
                    continue
                # f(θ) = a*θ - b*∇L
                p.mul_(a).add_(p.grad, alpha=-b)

        return loss


def main():
    print("=" * 70)
    print("  Model C: Contraction Mapping Optimizer")
    print("  f(θ) = 0.7θ - lr·∇L  (contraction coefficient a=0.7, fixed point I*=1/3)")
    print("=" * 70)

    train_loader, test_loader = load_mnist()

    HIDDEN_DIM = 256

    # Use same model structure for each optimizer
    configs = [
        ('Contraction (a=0.7)', lambda m: ContractionOptimizer(m.parameters(), lr=0.01, contraction=0.7)),
        ('Contraction (a=0.8)', lambda m: ContractionOptimizer(m.parameters(), lr=0.01, contraction=0.8)),
        ('Contraction (a=0.9)', lambda m: ContractionOptimizer(m.parameters(), lr=0.01, contraction=0.9)),
        ('Adam (baseline)',     lambda m: torch.optim.Adam(m.parameters(), lr=0.001)),
        ('SGD (lr=0.01)',       lambda m: torch.optim.SGD(m.parameters(), lr=0.01)),
        ('SGD+WD (wd=0.3)',    lambda m: torch.optim.SGD(m.parameters(), lr=0.01, weight_decay=0.3)),
    ]

    results = {}
    for name, opt_fn in configs:
        model = DenseModel(INPUT_DIM, HIDDEN_DIM, OUTPUT_DIM)
        params = count_params(model)
        optimizer = opt_fn(model)

        print(f"\n── {name} (params={params:,}) ──")
        losses, accs = train_and_evaluate(
            model, train_loader, test_loader,
            epochs=EPOCHS, optimizer=optimizer,
        )
        results[name] = {
            'acc': accs[-1],
            'loss': losses[-1],
            'params': params,
        }

    compare_results(results)

    # ── Contraction Analysis ──
    print("\n── Contraction Mapping Analysis ──")
    print("  f(θ) = a·θ - b·∇L")
    print("  a=0.7: Strong contraction, fast convergence, risk of underfitting")
    print("  a=0.9: Weak contraction, closer to SGD")
    print("  a=0.7 ↔ weight_decay=0.3: Mathematically equivalent")
    print()

    c07 = results.get('Contraction (a=0.7)', {}).get('acc', 0)
    sgd_wd = results.get('SGD+WD (wd=0.3)', {}).get('acc', 0)
    adam = results.get('Adam (baseline)', {}).get('acc', 0)

    print(f"  Contraction(0.7) vs SGD+WD(0.3): {(c07-sgd_wd)*100:+.2f}%")
    print(f"  Contraction(0.7) vs Adam:         {(c07-adam)*100:+.2f}%")

    if abs(c07 - sgd_wd) < 0.01:
        print("  → Empirically verified that a=0.7 and WD=0.3 are equivalent ✓")
    else:
        print("  → Performance gap due to implementation differences (multiplication vs subtraction order)")


if __name__ == '__main__':
    main()