"""
H-CX-62~71 All-in-one experiment script
Tests 10 cross-domain hypotheses connecting math constants to consciousness engine
"""
import torch
import torch.nn as nn
import torch.nn.functional as F
import math
import time
import numpy as np
from collections import defaultdict

device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
print(f"Device: {device}")

# === Shared tiny transformer ===
class TinyBlock(nn.Module):
    def __init__(self, d_model, n_heads, dropout=0.0):
        super().__init__()
        self.attn = nn.MultiheadAttention(d_model, n_heads, dropout=dropout, batch_first=True)
        self.ff = nn.Sequential(
            nn.Linear(d_model, 4*d_model), nn.GELU(), nn.Linear(4*d_model, d_model)
        )
        self.ln1 = nn.LayerNorm(d_model)
        self.ln2 = nn.LayerNorm(d_model)

    def forward(self, x, mask=None):
        h = self.ln1(x)
        h2, _ = self.attn(h, h, h, attn_mask=mask)
        x = x + h2
        x = x + self.ff(self.ln2(x))
        return x

class TinyLM(nn.Module):
    def __init__(self, vocab, d_model, n_heads, n_layers, seq_len=32):
        super().__init__()
        self.tok_emb = nn.Embedding(vocab, d_model)
        self.pos_emb = nn.Embedding(seq_len, d_model)
        self.blocks = nn.ModuleList([TinyBlock(d_model, n_heads) for _ in range(n_layers)])
        self.ln_f = nn.LayerNorm(d_model)
        self.head = nn.Linear(d_model, vocab, bias=False)
        self.seq_len = seq_len

    def forward(self, x):
        B, T = x.shape
        mask = torch.triu(torch.ones(T, T, device=x.device), diagonal=1).bool()
        h = self.tok_emb(x) + self.pos_emb(torch.arange(T, device=x.device))
        for block in self.blocks:
            h = block(h, mask)
        return self.head(self.ln_f(h))

    def get_tensions(self, x):
        B, T = x.shape
        mask = torch.triu(torch.ones(T, T, device=x.device), diagonal=1).bool()
        h = self.tok_emb(x) + self.pos_emb(torch.arange(T, device=x.device))
        tensions = []
        prev = h
        for block in self.blocks:
            h = block(h, mask)
            t = (h - prev).pow(2).mean().item()
            tensions.append(t)
            prev = h
        return tensions

def train_model(vocab, d_model, n_heads, n_layers, steps, seed, grad_clip=1.0, lr=1e-3):
    torch.manual_seed(seed)
    model = TinyLM(vocab, d_model, n_heads, n_layers).to(device)
    opt = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=0.01)
    losses = []
    for step in range(steps):
        x = torch.randint(0, vocab, (8, 32), device=device)
        logits = model(x)
        loss = F.cross_entropy(logits[:, :-1].reshape(-1, vocab), x[:, 1:].reshape(-1))
        opt.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), grad_clip)
        opt.step()
        if step % 50 == 0 or step == steps-1:
            losses.append((step, loss.item()))
    return model, losses

STEPS = 200
SEEDS = [42, 137]

# ============================================================
# H-CX-62: vocab=252 vs 256
# ============================================================
print("\n" + "="*60)
print("H-CX-62: vocab sweep (sigma_3(6)=252 vs 256)")
print("="*60)
vocab_results = {}
for vocab in [248, 250, 252, 254, 256, 258, 260]:
    seed_losses = []
    for seed in SEEDS:
        _, losses = train_model(vocab, 128, 2, 6, STEPS, seed)
        seed_losses.append(losses[-1][1])
    avg = sum(seed_losses)/len(seed_losses)
    vocab_results[vocab] = (avg, seed_losses)
    print(f"  vocab={vocab}: loss={avg:.4f} ({seed_losses})")

best_v = min(vocab_results, key=lambda v: vocab_results[v][0])
print(f"  BEST: vocab={best_v} (loss={vocab_results[best_v][0]:.4f})")
print(f"  252 vs 256: {vocab_results.get(252,(0,))[0]:.4f} vs {vocab_results.get(256,(0,))[0]:.4f}")

# ============================================================
# H-CX-63: R(n)-based gradient clipping
# ============================================================
print("\n" + "="*60)
print("H-CX-63: R(n) gradient clipping")
print("="*60)

def R(n):
    """Compute R(n) = sigma*phi/(n*tau)"""
    from sympy import divisor_sigma, totient, divisor_count
    s = int(divisor_sigma(n))
    p = int(totient(n))
    t = int(divisor_count(n))
    return s*p/(n*t)

r_values = {3: 4/3, 4: 7/6, 5: 24/10, 6: 1.0, 8: 15/8}  # pre-computed

clip_results = {}
for n_blocks in [3, 4, 6, 8]:
    r_clip = r_values[n_blocks]
    for clip_val, label in [(1.0, "std"), (r_clip, f"R({n_blocks})")]:
        seed_losses = []
        for seed in SEEDS:
            _, losses = train_model(256, 128, 2, n_blocks, STEPS, seed, grad_clip=clip_val)
            seed_losses.append(losses[-1][1])
        avg = sum(seed_losses)/len(seed_losses)
        clip_results[(n_blocks, label)] = avg
        print(f"  blocks={n_blocks}, clip={label}={clip_val:.3f}: loss={avg:.4f}")

print("\n  Summary: R(n)-clip vs standard")
for n in [3,4,6,8]:
    std = clip_results.get((n, "std"), 0)
    rn = clip_results.get((n, f"R({n})"), 0)
    diff = rn - std
    print(f"  n={n}: std={std:.4f}, R(n)={rn:.4f}, diff={diff:+.4f} {'BETTER' if diff < 0 else 'WORSE'}")

# ============================================================
# H-CX-64: heads sweep for 6-block
# ============================================================
print("\n" + "="*60)
print("H-CX-64: heads sweep (phi=2, sigma/tau=3, tau=4, sopfr=5, P1=6)")
print("="*60)

d_model = 120  # divisible by 1,2,3,4,5,6
heads_results = {}
for n_heads in [1, 2, 3, 4, 5, 6]:
    seed_losses = []
    for seed in SEEDS:
        _, losses = train_model(256, d_model, n_heads, 6, STEPS, seed)
        seed_losses.append(losses[-1][1])
    avg = sum(seed_losses)/len(seed_losses)
    heads_results[n_heads] = avg
    labels = {1:"1", 2:"phi(6)", 3:"sigma/tau", 4:"tau(6)", 5:"sopfr(6)", 6:"P1"}
    print(f"  heads={n_heads} ({labels[n_heads]}): loss={avg:.4f}")

best_h = min(heads_results, key=lambda h: heads_results[h])
print(f"  BEST: heads={best_h}")

# ============================================================
# H-CX-66: d_model=252 sweep
# ============================================================
print("\n" + "="*60)
print("H-CX-66: d_model sweep (sigma_3=252)")
print("="*60)

dmodel_results = {}
for dm in [240, 248, 252, 256, 264]:
    n_heads = 4 if dm % 4 == 0 else (3 if dm % 3 == 0 else 2)
    seed_losses = []
    for seed in SEEDS:
        _, losses = train_model(256, dm, n_heads, 6, STEPS, seed)
        seed_losses.append(losses[-1][1])
    avg = sum(seed_losses)/len(seed_losses)
    dmodel_results[dm] = avg
    print(f"  d_model={dm} (heads={n_heads}): loss={avg:.4f}")

# ============================================================
# H-CX-67: Tension ratio tracking
# ============================================================
print("\n" + "="*60)
print("H-CX-67: Tension ratio convergence")
print("="*60)

torch.manual_seed(42)
models = {}
opts = {}
for nb in [3, 4, 6, 8]:
    m = TinyLM(256, 128, 2, nb).to(device)
    models[nb] = m
    opts[nb] = torch.optim.AdamW(m.parameters(), lr=1e-3)

tension_history = {nb: [] for nb in [3,4,6,8]}
for step in range(300):
    x = torch.randint(0, 256, (8, 32), device=device)
    for nb in [3,4,6,8]:
        m = models[nb]
        logits = m(x)
        loss = F.cross_entropy(logits[:, :-1].reshape(-1, 256), x[:, 1:].reshape(-1))
        opts[nb].zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(m.parameters(), 1.0)
        opts[nb].step()
        if step % 30 == 0:
            with torch.no_grad():
                t = m.get_tensions(x)
                tension_history[nb].append((step, sum(t)/len(t)))

print("  Step | T(3)     | T(6)     | T(6)/T(3) | T(8)/T(6)")
print("  -----|----------|----------|-----------|----------")
for i in range(len(tension_history[3])):
    s = tension_history[3][i][0]
    t3 = tension_history[3][i][1]
    t6 = tension_history[6][i][1]
    t8 = tension_history[8][i][1]
    r63 = t6/t3 if t3 > 0 else 0
    r86 = t8/t6 if t6 > 0 else 0
    print(f"  {s:4d} | {t3:.6f} | {t6:.6f} | {r63:.4f}    | {r86:.4f}")

# Known divisor ratios for comparison
print("\n  Reference divisor ratios:")
print("  sigma(6)/sigma(3)=3, tau(6)/tau(3)=2, R(6)/R(3)=0.75, phi(6)/phi(3)=1")

# ============================================================
# H-CX-69: Cyclotomic activation
# ============================================================
print("\n" + "="*60)
print("H-CX-69: Cyclotomic activation functions")
print("="*60)

class Phi6Act(nn.Module):
    def forward(self, x):
        return x*x - x + 1

class Phi6Norm(nn.Module):
    def forward(self, x):
        return (x*x - x + 1) / (1 + x*x + 1e-8)

class TinyBlockAct(nn.Module):
    def __init__(self, d_model, n_heads, act_fn):
        super().__init__()
        self.attn = nn.MultiheadAttention(d_model, n_heads, batch_first=True)
        self.ff = nn.Sequential(
            nn.Linear(d_model, 4*d_model), act_fn, nn.Linear(4*d_model, d_model)
        )
        self.ln1 = nn.LayerNorm(d_model)
        self.ln2 = nn.LayerNorm(d_model)

    def forward(self, x, mask=None):
        h = self.ln1(x)
        h2, _ = self.attn(h, h, h, attn_mask=mask)
        x = x + h2
        x = x + self.ff(self.ln2(x))
        return x

class TinyLMAct(nn.Module):
    def __init__(self, vocab, d_model, n_heads, n_layers, act_fn):
        super().__init__()
        self.tok_emb = nn.Embedding(vocab, d_model)
        self.pos_emb = nn.Embedding(32, d_model)
        self.blocks = nn.ModuleList([TinyBlockAct(d_model, n_heads, act_fn) for _ in range(n_layers)])
        self.ln_f = nn.LayerNorm(d_model)
        self.head = nn.Linear(d_model, vocab, bias=False)

    def forward(self, x):
        B, T = x.shape
        mask = torch.triu(torch.ones(T, T, device=x.device), diagonal=1).bool()
        h = self.tok_emb(x) + self.pos_emb(torch.arange(T, device=x.device))
        for block in self.blocks:
            h = block(h, mask)
        return self.head(self.ln_f(h))

act_results = {}
for name, act_fn in [("GELU", nn.GELU()), ("SiLU", nn.SiLU()), ("ReLU", nn.ReLU()),
                       ("Phi6", Phi6Act()), ("Phi6Norm", Phi6Norm())]:
    seed_losses = []
    for seed in SEEDS:
        torch.manual_seed(seed)
        model = TinyLMAct(256, 128, 2, 6, act_fn).to(device)
        opt = torch.optim.AdamW(model.parameters(), lr=1e-3)
        for step in range(STEPS):
            xb = torch.randint(0, 256, (8, 32), device=device)
            logits = model(xb)
            loss = F.cross_entropy(logits[:, :-1].reshape(-1, 256), xb[:, 1:].reshape(-1))
            opt.zero_grad()
            loss.backward()
            gn = torch.nn.utils.clip_grad_norm_(model.parameters(), 5.0)
            opt.step()
        seed_losses.append(loss.item())
    avg = sum(seed_losses)/len(seed_losses)
    act_results[name] = (avg, seed_losses)
    print(f"  {name:10s}: loss={avg:.4f} {seed_losses}")

# ============================================================
# H-CX-68: Expert activation rate (simplified MoE)
# ============================================================
print("\n" + "="*60)
print("H-CX-68: Expert activation rate (top-k MoE)")
print("="*60)

class SimpleMoE(nn.Module):
    def __init__(self, d_model, n_experts=8, top_k=2):
        super().__init__()
        self.experts = nn.ModuleList([
            nn.Sequential(nn.Linear(d_model, 4*d_model), nn.GELU(), nn.Linear(4*d_model, d_model))
            for _ in range(n_experts)
        ])
        self.gate = nn.Linear(d_model, n_experts)
        self.top_k = top_k
        self.n_experts = n_experts

    def forward(self, x):
        B, T, D = x.shape
        gate_logits = self.gate(x)
        topk_vals, topk_idx = torch.topk(gate_logits, self.top_k, dim=-1)
        topk_weights = F.softmax(topk_vals, dim=-1)
        out = torch.zeros_like(x)
        for k in range(self.top_k):
            idx = topk_idx[:, :, k]
            w = topk_weights[:, :, k:k+1]
            for e in range(self.n_experts):
                mask = (idx == e)
                if mask.any():
                    inp = x[mask]
                    out[mask] += (w[mask] * self.experts[e](inp))
        return out

moe_results = {}
for top_k, label in [(1, "1/8=0.125"), (2, "2/8=0.250"), (3, "3/8=0.375~1/e"),
                       (4, "4/8=0.500"), (5, "5/8=0.625"), (6, "6/8=0.750")]:
    seed_losses = []
    for seed in SEEDS:
        torch.manual_seed(seed)
        # 6-block with MoE FFN
        tok_emb = nn.Embedding(256, 128).to(device)
        pos_emb = nn.Embedding(32, 128).to(device)
        blocks = nn.ModuleList()
        for _ in range(6):
            blocks.append(nn.ModuleDict({
                'attn': nn.MultiheadAttention(128, 2, batch_first=True),
                'moe': SimpleMoE(128, 8, top_k),
                'ln1': nn.LayerNorm(128),
                'ln2': nn.LayerNorm(128),
            }))
        blocks = blocks.to(device)
        ln_f = nn.LayerNorm(128).to(device)
        head = nn.Linear(128, 256, bias=False).to(device)

        all_params = list(tok_emb.parameters()) + list(pos_emb.parameters())
        for b in blocks:
            all_params += list(b.parameters())
        all_params += list(ln_f.parameters()) + list(head.parameters())
        opt = torch.optim.AdamW(all_params, lr=1e-3)

        for step in range(STEPS):
            xb = torch.randint(0, 256, (8, 32), device=device)
            mask = torch.triu(torch.ones(32, 32, device=device), diagonal=1).bool()
            h = tok_emb(xb) + pos_emb(torch.arange(32, device=device))
            for b in blocks:
                h2 = b['ln1'](h)
                h2, _ = b['attn'](h2, h2, h2, attn_mask=mask)
                h = h + h2
                h = h + b['moe'](b['ln2'](h))
            logits = head(ln_f(h))
            loss = F.cross_entropy(logits[:, :-1].reshape(-1, 256), xb[:, 1:].reshape(-1))
            opt.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(all_params, 1.0)
            opt.step()
        seed_losses.append(loss.item())
    avg = sum(seed_losses)/len(seed_losses)
    moe_results[top_k] = (avg, label)
    print(f"  top_k={top_k} ({label}): loss={avg:.4f}")

print("\n  1/e = 0.3679 -> closest is top_k=3 (3/8=0.375)")

# ============================================================
# H-CX-70: phi-bottleneck
# ============================================================
print("\n" + "="*60)
print("H-CX-70: phi(n)-bottleneck FFN")
print("="*60)

class PhiBottleneckBlock(nn.Module):
    def __init__(self, d_model, n_heads, bottleneck_ratio):
        super().__init__()
        self.attn = nn.MultiheadAttention(d_model, n_heads, batch_first=True)
        bottleneck = max(1, int(d_model * bottleneck_ratio))
        self.ff = nn.Sequential(
            nn.Linear(d_model, bottleneck),
            nn.GELU(),
            nn.Linear(bottleneck, 4*d_model),
            nn.GELU(),
            nn.Linear(4*d_model, d_model)
        )
        self.ln1 = nn.LayerNorm(d_model)
        self.ln2 = nn.LayerNorm(d_model)

    def forward(self, x, mask=None):
        h = self.ln1(x)
        h2, _ = self.attn(h, h, h, attn_mask=mask)
        x = x + h2
        x = x + self.ff(self.ln2(x))
        return x

bneck_results = {}
# phi(n)/n ratios: 3->2/3, 4->1/2, 6->1/3, 8->1/2
for n_blocks, phi_ratio, label in [(3, 2/3, "phi(3)/3=2/3"),
                                     (4, 1/2, "phi(4)/4=1/2"),
                                     (6, 1/3, "phi(6)/6=1/3"),
                                     (8, 1/2, "phi(8)/8=1/2")]:
    for use_bneck in [False, True]:
        seed_losses = []
        for seed in SEEDS:
            torch.manual_seed(seed)
            if use_bneck:
                tok = nn.Embedding(256, 120).to(device)
                pos = nn.Embedding(32, 120).to(device)
                blks = nn.ModuleList([PhiBottleneckBlock(120, 2, phi_ratio) for _ in range(n_blocks)]).to(device)
            else:
                tok = nn.Embedding(256, 120).to(device)
                pos = nn.Embedding(32, 120).to(device)
                blks = nn.ModuleList([TinyBlock(120, 2) for _ in range(n_blocks)]).to(device)
            lnf = nn.LayerNorm(120).to(device)
            hd = nn.Linear(120, 256, bias=False).to(device)
            ps = list(tok.parameters())+list(pos.parameters())+list(blks.parameters())+list(lnf.parameters())+list(hd.parameters())
            opt = torch.optim.AdamW(ps, lr=1e-3)
            for step in range(STEPS):
                xb = torch.randint(0, 256, (8, 32), device=device)
                msk = torch.triu(torch.ones(32, 32, device=device), diagonal=1).bool()
                h = tok(xb) + pos(torch.arange(32, device=device))
                for b in blks:
                    h = b(h, msk)
                logits = hd(lnf(h))
                loss = F.cross_entropy(logits[:, :-1].reshape(-1, 256), xb[:, 1:].reshape(-1))
                opt.zero_grad(); loss.backward()
                torch.nn.utils.clip_grad_norm_(ps, 1.0); opt.step()
            seed_losses.append(loss.item())
        avg = sum(seed_losses)/len(seed_losses)
        tag = f"phi-bneck" if use_bneck else "standard"
        bneck_results[(n_blocks, tag)] = avg
        print(f"  n={n_blocks}, {tag:12s} ({label if use_bneck else '4x expand'}): loss={avg:.4f}")

print("\n  Comparison: phi-bottleneck advantage?")
for n in [3,4,6,8]:
    std = bneck_results.get((n, "standard"), 0)
    phi = bneck_results.get((n, "phi-bneck"), 0)
    print(f"  n={n}: std={std:.4f}, phi-bneck={phi:.4f}, diff={phi-std:+.4f}")

# ============================================================
# FINAL SUMMARY
# ============================================================
print("\n" + "="*60)
print("FINAL SUMMARY — ALL HYPOTHESES")
print("="*60)

print(f"\nH-CX-62 vocab=252: loss={vocab_results.get(252,(0,))[0]:.4f} vs 256={vocab_results.get(256,(0,))[0]:.4f}")
print(f"  -> {'SUPPORTED' if vocab_results.get(252,(999,))[0] < vocab_results.get(256,(0,))[0] else 'REFUTED'}")

print(f"\nH-CX-63 R(n)-clip:")
for n in [3,4,6,8]:
    std = clip_results.get((n, "std"), 0)
    rn = clip_results.get((n, f"R({n})"), 0)
    print(f"  n={n}: {'SUPPORTED' if rn < std else 'REFUTED'} (diff={rn-std:+.4f})")

print(f"\nH-CX-64 heads: best={best_h} (expected: varies)")

print(f"\nH-CX-66 d_model=252: loss={dmodel_results.get(252,0):.4f}")
best_dm = min(dmodel_results, key=lambda d: dmodel_results[d])
print(f"  best d_model={best_dm}")

print(f"\nH-CX-69 cyclotomic activation:")
for name in ["GELU", "SiLU", "ReLU", "Phi6", "Phi6Norm"]:
    r = act_results.get(name, (0,[]))
    print(f"  {name}: {r[0]:.4f}")

print(f"\nH-CX-68 MoE top-k:")
for k in sorted(moe_results):
    avg, label = moe_results[k]
    marker = " <-- 1/e zone" if k == 3 else ""
    print(f"  top_k={k} ({label}): {avg:.4f}{marker}")

print(f"\nH-CX-70 phi-bottleneck:")
for n in [3,4,6,8]:
    std = bneck_results.get((n, "standard"), 0)
    phi = bneck_results.get((n, "phi-bneck"), 0)
    tag = "SUPPORTED" if phi < std else "REFUTED"
    print(f"  n={n}: {tag}")

print("\nDone!")
