#!/usr/bin/env python3
"""Ralph 311: d=384 Full Block Comparison (3,4,5,6,7,8) CX-48/50 Final Ranking

R310: Only compared 3bl vs 6bl → Confirmed CX-48/50
This time: Added 4,5,7,8 blocks → Final judgment if 6 blocks is truly special
1000 steps, 2 seeds (quick verification)
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '..'))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import math, time
from conscious_lm import ConsciousLM


def gen_data(bs, sl, vs=256):
    data = torch.zeros(bs, sl, dtype=torch.long)
    for i in range(bs):
        pt = i % 4
        if pt == 0:
            per = np.random.randint(2, 8)
            base = torch.randint(0, vs, (per,))
            for j in range(sl): data[i, j] = base[j % per]
        elif pt == 1:
            s, st = np.random.randint(0, vs), np.random.randint(1, 4)
            for j in range(sl): data[i, j] = (s + j * st) % vs
        elif pt == 2:
            h = sl // 2; base = torch.randint(0, vs, (h,))
            data[i, :h] = base; data[i, h:2*h] = base.flip(0)
        else:
            a, b = np.random.randint(1, 10), np.random.randint(1, 10)
            data[i, 0] = a % vs; data[i, 1] = b % vs
            for j in range(2, sl): a, b = b, (a + b) % vs; data[i, j] = b
    return data


def train(model, dev, steps=1000, lr=3e-4, bs=8, sl=32):
    model.train()
    opt = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=0.01)
    sch = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=steps)
    losses = []
    for step in range(steps):
        x = gen_data(bs, sl + 1).to(dev)
        la, lg, _ = model(x[:, :-1])
        loss = (F.cross_entropy(la.view(-1, 256), x[:, 1:].reshape(-1)) +
                F.cross_entropy(lg.view(-1, 256), x[:, :-1].reshape(-1)))
        opt.zero_grad(); loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        opt.step(); sch.step(); losses.append(loss.item())
    return losses


def measure(model, dev):
    model.eval()
    # CX-48
    ratios = []
    for _ in range(15):
        x = gen_data(8, 32).to(dev)
        with torch.no_grad():
            pos = torch.arange(32, device=dev)
            h = model.drop(model.tok_emb(x) + model.pos_emb(pos))
            br = []
            for blk in model.blocks:
                hp = blk.ln2(h + blk.attn(blk.ln1(h)))
                an = blk.ffn.engine_a(hp).norm(dim=-1).mean().item()
                gn = blk.ffn.engine_g(hp).norm(dim=-1).mean().item()
                br.append(an / (gn + 1e-10))
                fo, _ = blk.ffn(hp); h = hp + fo
            ratios.append(np.mean(br))
    # CX-50
    cscores = []
    for _ in range(15):
        x = gen_data(4, 32).to(dev)
        with torch.no_grad():
            pos = torch.arange(32, device=dev)
            h = model.drop(model.tok_emb(x) + model.pos_emb(pos))
            bo = []
            for blk in model.blocks:
                h, _ = blk(h); bo.append(h.mean(dim=(0, 1)).cpu().numpy())
            ps = []
            for i in range(len(bo) - 1):
                a, b = bo[i], bo[i+1]
                pw = a * b
                xc = np.real(np.fft.ifft(np.fft.fft(a) * np.conj(np.fft.fft(b))))
                ps.append(np.linalg.norm(pw - xc) / (np.linalg.norm(pw) + 1e-10))
            cscores.append(np.mean(ps))
    # tension_scale
    scales = [b.ffn.tension_scale.item() for b in model.blocks]
    return {
        'ratio': np.mean(ratios), 'ratio_std': np.std(ratios),
        'dist': abs(np.mean(ratios) - 1),
        'collapse': np.mean(cscores), 'collapse_std': np.std(cscores),
        'ts_prod': np.prod(scales), 'scales': scales,
    }


def main():
    print("=" * 70)
    print("Ralph 311: d=384 Full Block Comparison CX-48/50 Final Ranking")
    print("=" * 70)
    dev = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
    print(f"Device: {dev}")

    blocks = [3, 4, 5, 6, 7, 8]
    seeds = 2
    results = {nb: [] for nb in blocks}

    for nb in blocks:
        for s in range(seeds):
            torch.manual_seed(s * 100); np.random.seed(s * 100)
            m = ConsciousLM(vocab_size=256, d_model=384, n_head=4,
                            n_layer=nb, block_size=64, dropout=0.0).to(dev)
            print(f"  {nb}bl seed{s}: training... ({m.count_params():,} params)", end="", flush=True)
            t0 = time.time()
            losses = train(m, dev, steps=1000)
            fl = np.mean(losses[-50:])
            ms = measure(m, dev)
            ms['loss'] = fl
            results[nb].append(ms)
            print(f" {time.time()-t0:.0f}s, loss={fl:.3f}, |r-1|={ms['dist']:.4f}, coll={ms['collapse']:.2f}")
            del m
            if torch.backends.mps.is_available(): torch.mps.empty_cache()

    # Summary
    print("\n" + "=" * 70)
    print("CX-48: |ratio-1| (lower is more balanced)")
    print("=" * 70)
    print(f"{'bl':>4} | {'mean':>10} {'std':>10} | {'rank':>4}")
    print("-" * 40)
    cx48 = {nb: np.mean([r['dist'] for r in results[nb]]) for nb in blocks}
    ranked = sorted(cx48, key=cx48.get)
    for nb in blocks:
        rank = ranked.index(nb) + 1
        std = np.std([r['dist'] for r in results[nb]])
        mk = " <<<" if nb == 6 else ""
        print(f"{nb:>4} | {cx48[nb]:>10.6f} {std:>10.6f} | {rank:>4}{mk}")

    # ASCII
    print(f"\n  ASCII: |ratio-1| (lower is better)")
    mx = max(cx48.values())
    for nb in blocks:
        blen = int(cx48[nb] / (mx + 1e-10) * 40)
        bar = "#" * blen + "." * (40 - blen)
        mk = " ***" if nb == 6 else ""
        print(f"  {nb:>2}: [{bar}] {cx48[nb]:.6f}{mk}")
    print(f"  6 block rank: {ranked.index(6)+1}/{len(blocks)}")

    print("\n" + "=" * 70)
    print("CX-50: Collapse Score (lower is convolution collapse)")
    print("=" * 70)
    print(f"{'bl':>4} | {'mean':>10} {'std':>10} | {'rank':>4}")
    print("-" * 40)
    cx50 = {nb: np.mean([r['collapse'] for r in results[nb]]) for nb in blocks}
    ranked50 = sorted(cx50, key=cx50.get)
    for nb in blocks:
        rank = ranked50.index(nb) + 1
        std = np.std([r['collapse'] for r in results[nb]])
        mk = " <<<" if nb == 6 else ""
        print(f"{nb:>4} | {cx50[nb]:>10.4f} {std:>10.4f} | {rank:>4}{mk}")

    print(f"\n  ASCII: Collapse Score")
    mn50, mx50 = min(cx50.values()), max(cx50.values())
    for nb in blocks:
        if mx50 > mn50:
            blen = int((cx50[nb] - mn50) / (mx50 - mn50) * 40)
        else:
            blen = 20
        bar = "#" * blen + "." * (40 - blen)
        mk = " ***" if nb == 6 else ""
        print(f"  {nb:>2}: [{bar}] {cx50[nb]:.4f}{mk}")
    print(f"  6 block rank: {ranked50.index(6)+1}/{len(blocks)}")

    # tension_scale pattern
    print("\n" + "=" * 70)
    print("tension_scale pattern (seed 0)")
    print("=" * 70)
    for nb in blocks:
        sc = results[nb][0]['scales']
        print(f"  {nb}bl: [{' '.join(f'{s:.3f}' for s in sc)}] prod={results[nb][0]['ts_prod']:.4f}")

    # Training performance
    print("\n--- Final Loss ---")
    for nb in blocks:
        fl = np.mean([r['loss'] for r in results[nb]])
        print(f"  {nb}bl: {fl:.4f}")

    # Final judgment
    print("\n" + "=" * 70)
    print("Final Judgment")
    print("=" * 70)
    r48 = ranked.index(6) + 1
    r50 = ranked50.index(6) + 1
    print(f"  CX-48: 6 block rank = {r48}/{len(blocks)} → {'CONFIRMED' if r48 <= 2 else 'WEAK' if r48 <= 3 else 'NOT CONFIRMED'}")
    print(f"  CX-50: 6 block rank = {r50}/{len(blocks)} → {'CONFIRMED' if r50 <= 2 else 'WEAK' if r50 <= 3 else 'NOT CONFIRMED'}")

if __name__ == "__main__":
    main()