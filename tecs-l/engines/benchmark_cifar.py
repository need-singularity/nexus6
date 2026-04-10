#!/usr/bin/env python3
"""CIFAR-10 Benchmark — Testing All Meta Engine Models

Compare meta engine architectures on CIFAR-10 (3072-dim, color),
which is harder than MNIST (784-dim, grayscale).

Input: 32x32x3 = 3072 (flatten)
hidden_dim: 64 (larger than MNIST's 48, for harder task)
epochs: 15 (longer than MNIST's 10)
"""

import torch
import time

from model_utils import (
    DenseModel, BaseMoE, TopKGate,
    load_cifar10, train_and_evaluate, compare_results, count_params,
)
from model_meta_engine import (
    EngineA, EngineE,
    DualBrainEngine, MetaEngine, HierarchicalMetaEngine,
    RepulsionFieldEngine, RepulsionFieldQuad, SelfReferentialField,
)


# ─────────────────────────────────────────
# MNIST Reference Results (model_meta_engine.py benchmark)
# ─────────────────────────────────────────
MNIST_RESULTS = {
    'Dense':             96.56,
    'Top-K MoE':         96.79,
    'Engine A':          97.17,
    'Engine E':          96.55,
    'DualBrain (A+G)':   97.27,
    'Meta (AEGF)':       97.63,
    'Meta fixed':        97.75,
    'Hierarchical':      97.49,
    'Repulsion (A|G)':   97.41,
    'Repulsion Quad':    97.19,
    'SelfRef Field':     97.52,
}


def main():
    print()
    print("=" * 65)
    print("   logout — CIFAR-10 Meta Engine Benchmark")
    print("   Engine + Engine = Higher Engine (harder task)")
    print("=" * 65)

    train_loader, test_loader = load_cifar10()
    input_dim, hidden_dim, output_dim = 3072, 64, 10
    epochs = 15
    results = {}

    start_time = time.time()

    # ── Baseline: Dense ──
    print("\n[Dense baseline]")
    model = DenseModel(input_dim, hidden_dim * 4, output_dim)
    losses, accs = train_and_evaluate(model, train_loader, test_loader, epochs)
    results['Dense'] = {'acc': accs[-1], 'loss': losses[-1], 'params': count_params(model)}

    # ── Baseline: Top-K MoE (8, k=2) ──
    print("\n[Top-K MoE (8 experts, k=2)]")
    model = BaseMoE(input_dim, hidden_dim, output_dim, 8,
                     TopKGate(input_dim, 8, 2))
    losses, accs = train_and_evaluate(model, train_loader, test_loader, epochs)
    results['Top-K MoE'] = {'acc': accs[-1], 'loss': losses[-1], 'params': count_params(model)}

    # ── Single Engine A ──
    print("\n[Engine A: sigma,tau-MoE (12e, k=4)]")
    model = EngineA(input_dim, hidden_dim, output_dim)
    losses, accs = train_and_evaluate(model, train_loader, test_loader, epochs)
    results['Engine A'] = {'acc': accs[-1], 'loss': losses[-1], 'params': count_params(model)}

    # ── Single Engine E ──
    print("\n[Engine E: Euler Product (2x3)]")
    model = EngineE(input_dim, hidden_dim, output_dim)
    losses, accs = train_and_evaluate(model, train_loader, test_loader, epochs)
    results['Engine E'] = {'acc': accs[-1], 'loss': losses[-1], 'params': count_params(model)}

    # ── DualBrain (A+G) ──
    print("\n[DualBrain: Left(A) + Right(G) + Corpus Callosum]")
    model = DualBrainEngine(input_dim, hidden_dim, output_dim)
    losses, accs = train_and_evaluate(model, train_loader, test_loader, epochs,
                                       aux_lambda=0.01)
    results['DualBrain (A+G)'] = {'acc': accs[-1], 'loss': losses[-1], 'params': count_params(model)}

    # ── MetaEngine (AEGF, contraction mapping routing) ──
    print("\n[MetaEngine: A+E+G+F (contraction routing)]")
    model = MetaEngine(input_dim, hidden_dim, output_dim,
                        engines='AEGF', routing='meta')
    losses, accs = train_and_evaluate(model, train_loader, test_loader, epochs,
                                       aux_lambda=0.01)
    results['Meta (AEGF)'] = {'acc': accs[-1], 'loss': losses[-1], 'params': count_params(model)}

    # ── MetaEngine (fixed weights) ──
    print("\n[MetaEngine: A+E+G+F (fixed {1/2,1/3,1/6} weights)]")
    model = MetaEngine(input_dim, hidden_dim, output_dim,
                        engines='AEGF', routing='fixed')
    losses, accs = train_and_evaluate(model, train_loader, test_loader, epochs,
                                       aux_lambda=0.01)
    results['Meta fixed'] = {'acc': accs[-1], 'loss': losses[-1], 'params': count_params(model)}

    # ── Hierarchical (meta of meta) ──
    print("\n[Hierarchical: (A+E) + (G+F) meta-combined]")
    model = HierarchicalMetaEngine(input_dim, hidden_dim, output_dim)
    losses, accs = train_and_evaluate(model, train_loader, test_loader, epochs,
                                       aux_lambda=0.01)
    results['Hierarchical'] = {'acc': accs[-1], 'loss': losses[-1], 'params': count_params(model)}

    # ── RepulsionField (2 poles: A vs G) ──
    print("\n[RepulsionField: Pole+(A) vs Pole-(G)]")
    model = RepulsionFieldEngine(input_dim, hidden_dim, output_dim)
    losses, accs = train_and_evaluate(model, train_loader, test_loader, epochs,
                                       aux_lambda=0.01)
    results['Repulsion (A|G)'] = {'acc': accs[-1], 'loss': losses[-1], 'params': count_params(model)}
    print(f"    Tension: {model.tension_magnitude:.4f}")

    # ── RepulsionFieldQuad (4 poles: A|G × E|F) ──
    print("\n[RepulsionFieldQuad: (A|G) x (E|F)]")
    model = RepulsionFieldQuad(input_dim, hidden_dim, output_dim)
    losses, accs = train_and_evaluate(model, train_loader, test_loader, epochs,
                                       aux_lambda=0.01)
    results['Repulsion Quad'] = {'acc': accs[-1], 'loss': losses[-1], 'params': count_params(model)}
    print(f"    Tension content: {model.tension_content:.4f}, structure: {model.tension_structure:.4f}")

    # ── SelfReferentialField (self-referential repulsion field) ──
    print("\n[SelfReferentialField: Engine observing tension (Phase 3)]")
    model = SelfReferentialField(input_dim, hidden_dim, output_dim, n_self_ref_steps=3)
    losses, accs = train_and_evaluate(model, train_loader, test_loader, epochs,
                                       aux_lambda=0.01)
    results['SelfRef Field'] = {'acc': accs[-1], 'loss': losses[-1], 'params': count_params(model)}
    print(f"    Tension history: {['%.1f' % t for t in model.tension_history]}")
    print(f"    Self-state norm: {model.self_state_norm:.4f}")
    converged = (len(model.tension_history) >= 2 and
                 abs(model.tension_history[-1] - model.tension_history[-2]) <
                 abs(model.tension_history[1] - model.tension_history[0]))
    print(f"    Tension converging: {'YES' if converged else 'NO'}")

    elapsed = time.time() - start_time

    # ── Compare Results ──
    compare_results(results)

    print(f"\n  Total time: {elapsed:.0f}s ({elapsed/60:.1f}min)")

    # ── Core Analysis ──
    print("\n" + "-" * 65)
    print("  Core Question: Is engine combination better than single engine? (CIFAR-10)")
    print("-" * 65)

    single_best = max(results['Engine A']['acc'], results['Engine E']['acc'])
    meta_acc = results['Meta (AEGF)']['acc']
    dual_acc = results['DualBrain (A+G)']['acc']

    print(f"  Single engine best:     {single_best*100:.2f}%")
    print(f"  DualBrain (A+G):    {dual_acc*100:.2f}%  ({'+' if dual_acc > single_best else ''}{(dual_acc-single_best)*100:.2f}%)")
    print(f"  Meta (AEGF):        {meta_acc*100:.2f}%  ({'+' if meta_acc > single_best else ''}{(meta_acc-single_best)*100:.2f}%)")

    # ── MNIST vs CIFAR-10 Comparison ──
    print("\n" + "=" * 70)
    print("   MNIST vs CIFAR-10 Comparison")
    print("=" * 70)
    print(f"  {'Model':<30} {'MNIST':>8} {'CIFAR':>8} {'Diff':>8}")
    print("-" * 70)

    for name in ['Dense', 'Top-K MoE', 'Engine A', 'Engine E',
                  'DualBrain (A+G)', 'Meta (AEGF)', 'Meta fixed',
                  'Hierarchical', 'Repulsion (A|G)', 'Repulsion Quad',
                  'SelfRef Field']:
        mnist = MNIST_RESULTS.get(name, 0)
        cifar = results.get(name, {}).get('acc', 0) * 100
        diff = cifar - mnist
        print(f"  {name:<30} {mnist:>7.2f}% {cifar:>7.2f}% {diff:>+7.2f}%")

    print("=" * 70)
    print("  CIFAR-10 is much harder than MNIST (color, real objects)")
    print("  Relative rankings between models more important than absolute accuracy drop")
    print()


if __name__ == '__main__':
    main()