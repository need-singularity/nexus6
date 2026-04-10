"""CLI entry point."""

import argparse
from .trainer import PHTrainer


def main():
    parser = argparse.ArgumentParser(
        description='ph-train: Automatic model training with Persistent Homology',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  ph-train --dataset mnist
  ph-train --dataset fashion --epochs 30
  ph-train --dataset cifar --lr 0.001
        """,
    )
    parser.add_argument('--dataset', default='mnist',
                        choices=['mnist', 'fashion', 'cifar'],
                        help='Training dataset (default: mnist)')
    parser.add_argument('--epochs', type=int, default=20,
                        help='Maximum epochs (default: 20)')
    parser.add_argument('--lr', default='auto',
                        help='Learning rate, auto=H0 CV search (default: auto)')
    parser.add_argument('--hidden', type=int, default=128,
                        help='Hidden layer dimension (default: 128)')
    parser.add_argument('--batch-size', type=int, default=256,
                        help='Batch size (default: 256)')
    parser.add_argument('--gap-threshold', type=float, default=0.08,
                        help='H0 gap alert threshold (default: 0.08)')
    parser.add_argument('--seed', type=int, default=42,
                        help='Random seed (default: 42)')
    parser.add_argument('--quiet', action='store_true',
                        help='Minimal output')

    args = parser.parse_args()

    trainer = PHTrainer(
        dataset=args.dataset,
        epochs=args.epochs,
        hidden_dim=args.hidden,
        lr=args.lr,
        batch_size=args.batch_size,
        gap_threshold=args.gap_threshold,
        seed=args.seed,
        verbose=not args.quiet,
    )

    result = trainer.run()

    if args.quiet:
        print(f"{result.dataset}: {result.best_acc:.1f}% "
              f"(LR={result.best_lr:.0e}, {result.difficulty})")


if __name__ == '__main__':
    main()
