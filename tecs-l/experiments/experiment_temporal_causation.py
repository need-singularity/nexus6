#!/usr/bin/env python3
"""Hypothesis 281: Tension Temporal Causation — Tension as Leading Indicator of Learning?"""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import torch, numpy as np
from model_utils import load_mnist, count_params
from model_meta_engine import RepulsionFieldQuad

def main():
    print("="*55)
    print("  Hypothesis 281: Tension as Leading Indicator")
    print("="*55)
    t0 = time.time()
    train_loader, test_loader = load_mnist()
    model = RepulsionFieldQuad(784, 48, 10)
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
    criterion = torch.nn.CrossEntropyLoss()

    epoch_data = []
    for ep in range(15):
        model.train()
        for X, y in train_loader:
            X = X.view(X.size(0), -1)
            optimizer.zero_grad()
            out, aux = model(X)
            loss = criterion(out, y) + 0.01 * aux
            loss.backward()
            optimizer.step()

        # Per-digit tension + accuracy
        model.eval()
        digit_tension = {d: [] for d in range(10)}
        digit_correct = {d: 0 for d in range(10)}
        digit_total = {d: 0 for d in range(10)}
        with torch.no_grad():
            for X, y in test_loader:
                X_flat = X.view(X.size(0), -1)
                out_a = model.engine_a(X_flat)
                out_g = model.engine_g(X_flat)
                out_e = model.engine_e(X_flat)
                out_f = model.engine_f(X_flat)
                t_c = (out_a - out_g).pow(2).sum(-1)
                t_s = (out_e - out_f).pow(2).sum(-1)
                tension = torch.sqrt(t_c * t_s + 1e-8)
                logits, _ = model(X_flat)
                preds = logits.argmax(1)
                for i in range(len(y)):
                    d = y[i].item()
                    digit_tension[d].append(tension[i].item())
                    digit_total[d] += 1
                    if preds[i] == y[i]:
                        digit_correct[d] += 1

        row = {}
        for d in range(10):
            row[f't{d}'] = np.mean(digit_tension[d])
            row[f'a{d}'] = digit_correct[d] / digit_total[d] * 100
        epoch_data.append(row)
        print(f"  Epoch {ep+1:>2}: overall {sum(digit_correct.values())/sum(digit_total.values())*100:.1f}%")

    # Lagged correlation: tension(t) vs accuracy(t+1)
    print(f"\n{'='*55}")
    print(f"  Lagged Correlation: tension(t) -> accuracy(t+1)")
    print(f"{'='*55}")
    print(f"  {'Digit':>5} | {'r(t,a_t)':>8} | {'r(t,a_t+1)':>10} | {'Lead?':>5}")
    print(f"  {'-'*5}-+-{'-'*8}-+-{'-'*10}-+-{'-'*5}")

    for d in range(10):
        tensions = [epoch_data[i][f't{d}'] for i in range(15)]
        accs = [epoch_data[i][f'a{d}'] for i in range(15)]
        # Contemporaneous correlation
        r_same = np.corrcoef(tensions, accs)[0, 1]
        # Lagged correlation: tension(0..13) vs acc(1..14)
        r_lead = np.corrcoef(tensions[:-1], accs[1:])[0, 1]
        lead = "YES" if r_lead > r_same + 0.05 else "no"
        print(f"  {d:>5} | {r_same:>+8.4f} | {r_lead:>+10.4f} | {lead:>5}")

    # ASCII: Digit 9 tension+accuracy trajectory
    print(f"\n  Digit 9 trajectory:")
    t9 = [epoch_data[i]['t9'] for i in range(15)]
    a9 = [epoch_data[i]['a9'] for i in range(15)]
    print(f"  Epoch | {'Tension':>8} | {'Acc%':>6} | Tension bar")
    for i in range(15):
        bar = '#' * int(t9[i] / max(t9) * 30)
        print(f"  {i+1:>5} | {t9[i]:>8.1f} | {a9[i]:>5.1f}% | {bar}")

    print(f"\n  Elapsed: {time.time()-t0:.1f}s")
    print("="*55)

if __name__ == '__main__':
    main()