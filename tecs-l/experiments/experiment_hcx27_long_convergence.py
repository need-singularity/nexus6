#!/usr/bin/env python3
"""H-CX-27 Verification: tension_scale Long-term Convergence — Do all inits converge to ln(4)?

In the existing 15ep, only init=0.3 converged to ln(4). Check if all inits converge at 100ep.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import torch
import torch.nn as nn
import numpy as np
from model_pure_field import PureFieldEngine
from model_utils import load_mnist
import math

LN4 = math.log(4)  # 1.38629...

def train_track_ts(model, train_loader, epochs=100, lr=0.001):
    """Train and track tension_scale every epoch."""
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    criterion = nn.CrossEntropyLoss()

    ts_history = [model.tension_scale.item()]
    acc_history = []

    for epoch in range(epochs):
        model.train()
        for X, y in train_loader:
            X = X.view(X.size(0), -1)
            optimizer.zero_grad()
            logits, tension = model(X)
            loss = criterion(logits, y)
            loss.backward()
            optimizer.step()

        ts_history.append(model.tension_scale.item())

        # Quick eval every 10 epochs
        if (epoch + 1) % 10 == 0:
            model.eval()
            correct = total = 0
            with torch.no_grad():
                for X, y in train_loader:
                    X = X.view(X.size(0), -1)
                    out, _ = model(X)
                    correct += (out.argmax(1) == y).sum().item()
                    total += y.size(0)
                    if total > 5000:
                        break
            acc = correct / total
            acc_history.append((epoch + 1, acc))

    return ts_history, acc_history

def ascii_convergence_plot(all_ts, inits, epochs):
    """ASCII plot of tension_scale trajectories."""
    print(f"\n  tension_scale convergence over {epochs} epochs")
    print(f"  (target: ln(4) = {LN4:.4f})")

    # Find range
    all_vals = [v for ts in all_ts for v in ts]
    ymin, ymax = min(all_vals), max(all_vals)
    ymin = min(ymin, LN4 - 0.5)
    ymax = max(ymax, LN4 + 0.5)

    rows = 20
    cols = 50
    grid = [[' ' for _ in range(cols)] for _ in range(rows)]

    # ln(4) line
    ln4_row = rows - 1 - int((LN4 - ymin) / (ymax - ymin) * (rows - 1))
    if 0 <= ln4_row < rows:
        for c in range(cols):
            grid[ln4_row][c] = '─'

    # Plot each trajectory
    symbols = '●◆■▲○◇□△'
    for idx, (ts, init_val) in enumerate(zip(all_ts, inits)):
        sym = symbols[idx % len(symbols)]
        for ep_idx in range(0, len(ts), max(1, len(ts)//cols)):
            c = min(int(ep_idx / len(ts) * cols), cols - 1)
            r = rows - 1 - int((ts[ep_idx] - ymin) / (ymax - ymin) * (rows - 1))
            r = max(0, min(rows - 1, r))
            grid[r][c] = sym

    for r in range(rows):
        val = ymax - r * (ymax - ymin) / (rows - 1)
        marker = ' ←ln(4)' if r == ln4_row else ''
        line = ''.join(grid[r])
        print(f"  {val:>5.2f} |{line}|{marker}")
    print(f"  {'':>5} +{'─' * cols}+")
    print(f"  {'':>5}  0{' ' * (cols - 5)}{epochs}")
    print(f"  {'':>5}           epoch")

    # Legend
    print(f"\n  Legend:")
    for idx, init_val in enumerate(inits):
        sym = symbols[idx % len(symbols)]
        print(f"    {sym} init={init_val}")

if __name__ == '__main__':
    print("=" * 60)
    print(f"  H-CX-27: tension_scale long convergence test")
    print(f"  target: ln(4) = {LN4:.6f}")
    print(f"  epochs: 100, inits: [0.01, 0.1, 0.3, 0.5, 1.0, 2.0]")
    print("=" * 60)

    train_loader, test_loader = load_mnist(batch_size=128)

    inits = [0.01, 0.1, 0.3, 0.5, 1.0, 2.0]
    all_ts = []
    epochs = 100

    for init_val in inits:
        print(f"\n  --- init = {init_val} ---")
        model = PureFieldEngine(784, 128, 10)
        with torch.no_grad():
            model.tension_scale.fill_(init_val)

        ts_history, acc_history = train_track_ts(model, train_loader, epochs=epochs)
        all_ts.append(ts_history)

        final_ts = ts_history[-1]
        err = abs(final_ts - LN4) / LN4 * 100
        print(f"    final ts = {final_ts:.4f}, ln(4) error = {err:.1f}%")
        for ep, acc in acc_history:
            print(f"    epoch {ep:>3}: acc={acc*100:.1f}%, ts={ts_history[ep]:.4f}")

    # Summary table
    print(f"\n{'='*60}")
    print(f"  === CONVERGENCE SUMMARY ===")
    print(f"{'='*60}")
    print(f"  {'init':>6} {'final_ts':>10} {'ln4_err%':>10} {'converged?':>12}")
    print(f"  {'─'*6} {'─'*10} {'─'*10} {'─'*12}")

    converged_count = 0
    for init_val, ts in zip(inits, all_ts):
        final = ts[-1]
        err = abs(final - LN4) / LN4 * 100
        conv = 'YES' if err < 5 else 'no'
        if conv == 'YES':
            converged_count += 1
        print(f"  {init_val:>6.2f} {final:>10.4f} {err:>9.1f}% {conv:>12}")

    print(f"\n  Converged to ln(4)±5%: {converged_count}/{len(inits)}")
    print(f"  ln(4) = {LN4:.6f}")

    if converged_count >= len(inits) - 1:
        print(f"\n  Conclusion: Most converged to ln(4) in long-term learning → H-CX-27 restored!")
    elif converged_count >= len(inits) // 2:
        print(f"\n  Conclusion: Majority converged → H-CX-27 partially confirmed")
    else:
        print(f"\n  Conclusion: Convergence failed → H-CX-27 refutation strengthened (init dependency confirmed)")

    # Plot
    ascii_convergence_plot(all_ts, inits, epochs)