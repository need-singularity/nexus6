"""
H-CX-63: R(n)-based gradient clipping
H-CX-64: heads=sopfr(6)=5 configuration

H-CX-63 Hypothesis: For an n-block transformer, using R(n)=sigma(n)*phi(n)/(n*tau(n))
as gradient clip value is optimal vs standard clip=1.0.

H-CX-64 Hypothesis: For a 6-block model, heads count derived from divisor functions
may be optimal (specifically sopfr(6)=5).
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import math
import random
import numpy as np
from dataclasses import dataclass
from typing import Optional

# --- R(n) values ---
# R(n) = sigma(n) * phi(n) / (n * tau(n))
# sigma(n) = sum of divisors, phi(n) = Euler totient, tau(n) = number of divisors
def compute_R(n):
    # sigma
    sigma = sum(d for d in range(1, n+1) if n % d == 0)
    # phi
    phi = sum(1 for k in range(1, n+1) if math.gcd(k, n) == 1)
    # tau
    tau = sum(1 for d in range(1, n+1) if n % d == 0)
    return sigma * phi / (n * tau)

# Pre-verify R values match hypothesis
R_values = {n: compute_R(n) for n in range(3, 9)}
print("=== R(n) values ===")
for n, r in R_values.items():
    print(f"  R({n}) = {r:.6f}")

# Expected from hypothesis doc (some may have typos):
# R(3)=4/3, R(4)=7/6, R(5)=4/5, R(6)=1.0, R(7)=48/7, R(8)=3/8
# NOTE: The formula sigma(n)*phi(n)/(n*tau(n)) gives different values for n=5,7,8.
# The computed values from the formula are used as ground truth.
# Hypothesis doc values for R(5), R(7), R(8) appear to be incorrect.
doc_expected = {3: 4/3, 4: 7/6, 5: 4/5, 6: 1.0, 7: 48/7, 8: 3/8}
from fractions import Fraction
print("\n=== Formula R(n) = sigma(n)*phi(n)/(n*tau(n)) exact fractions ===")
for n, r in R_values.items():
    import math as _math
    sigma_n = sum(d for d in range(1, n+1) if n % d == 0)
    phi_n   = sum(1 for k in range(1, n+1) if _math.gcd(k, n) == 1)
    tau_n   = sum(1 for d in range(1, n+1) if n % d == 0)
    frac    = Fraction(sigma_n * phi_n, n * tau_n)
    doc_v   = doc_expected[n]
    match   = abs(float(frac) - doc_v) < 1e-9
    flag    = "" if match else "  <-- DISCREPANCY with hypothesis doc"
    print(f"  R({n}) = {frac} = {float(frac):.6f}  (doc says {Fraction(doc_v).limit_denominator(100)}){flag}")

# --- Device ---
if torch.backends.mps.is_available():
    device = torch.device("mps")
    print(f"\nUsing MPS device")
elif torch.cuda.is_available():
    device = torch.device("cuda")
    print(f"\nUsing CUDA device")
else:
    device = torch.device("cpu")
    print(f"\nUsing CPU device")


# --- Minimal Transformer ---
class TransformerBlock(nn.Module):
    def __init__(self, d_model, n_heads):
        super().__init__()
        assert d_model % n_heads == 0, f"d_model={d_model} must be divisible by n_heads={n_heads}"
        self.attn = nn.MultiheadAttention(d_model, n_heads, batch_first=True)
        self.ff = nn.Sequential(
            nn.Linear(d_model, d_model * 2),
            nn.GELU(),
            nn.Linear(d_model * 2, d_model),
        )
        self.ln1 = nn.LayerNorm(d_model)
        self.ln2 = nn.LayerNorm(d_model)

    def forward(self, x):
        attn_out, _ = self.attn(x, x, x)
        x = self.ln1(x + attn_out)
        x = self.ln2(x + self.ff(x))
        return x


class MiniTransformer(nn.Module):
    def __init__(self, vocab_size, d_model, n_blocks, n_heads):
        super().__init__()
        self.embed = nn.Embedding(vocab_size, d_model)
        self.pos_embed = nn.Embedding(128, d_model)
        self.blocks = nn.ModuleList([
            TransformerBlock(d_model, n_heads) for _ in range(n_blocks)
        ])
        self.ln_f = nn.LayerNorm(d_model)
        self.head = nn.Linear(d_model, vocab_size, bias=False)

    def forward(self, idx):
        B, T = idx.shape
        tok = self.embed(idx)
        pos = self.pos_embed(torch.arange(T, device=idx.device).unsqueeze(0))
        x = tok + pos
        for block in self.blocks:
            x = block(x)
        x = self.ln_f(x)
        return self.head(x)


def make_batch(vocab_size, seq_len, batch_size, device):
    """Random token sequences as language modelling data."""
    x = torch.randint(0, vocab_size, (batch_size, seq_len), device=device)
    return x[:, :-1], x[:, 1:]


def train_model(model, n_steps, grad_clip, seed, device, vocab_size=256,
                seq_len=32, batch_size=16, lr=1e-3):
    """Train model and return final loss (average of last 50 steps)."""
    torch.manual_seed(seed)
    random.seed(seed)
    np.random.seed(seed)

    model = model.to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)

    losses = []
    for step in range(n_steps):
        xb, yb = make_batch(vocab_size, seq_len, batch_size, device)
        logits = model(xb)
        loss = F.cross_entropy(logits.reshape(-1, vocab_size), yb.reshape(-1))

        optimizer.zero_grad()
        loss.backward()
        nn.utils.clip_grad_norm_(model.parameters(), grad_clip)
        optimizer.step()

        losses.append(loss.item())

    final_loss = np.mean(losses[-50:])
    return final_loss


# ============================================================
# EXPERIMENT 1: H-CX-63 — R(n)-based gradient clipping
# ============================================================
print("\n" + "="*60)
print("EXPERIMENT 1: H-CX-63 — R(n)-based gradient clipping")
print("="*60)
print("Config: d_model=128, vocab=256, n_heads=2, 300 steps, 2 seeds")
print()

VOCAB = 256
D_MODEL = 128
N_HEADS = 2
N_STEPS = 300
SEEDS = [42, 123]

results_63 = []

for n_blocks in [3, 4, 5, 6, 7, 8]:
    r_clip = R_values[n_blocks]
    std_clip = 1.0

    r_losses = []
    std_losses = []

    for seed in SEEDS:
        # R(n) clip
        torch.manual_seed(seed)
        model_r = MiniTransformer(VOCAB, D_MODEL, n_blocks, N_HEADS)
        loss_r = train_model(model_r, N_STEPS, r_clip, seed, device, VOCAB)
        r_losses.append(loss_r)
        del model_r

        # Standard clip=1.0
        torch.manual_seed(seed)
        model_std = MiniTransformer(VOCAB, D_MODEL, n_blocks, N_HEADS)
        loss_std = train_model(model_std, N_STEPS, std_clip, seed, device, VOCAB)
        std_losses.append(loss_std)
        del model_std

    mean_r = np.mean(r_losses)
    mean_std = np.mean(std_losses)
    delta = mean_r - mean_std
    winner = "R(n)" if delta < 0 else "std"

    results_63.append({
        "n_blocks": n_blocks,
        "R_n": r_clip,
        "loss_R": mean_r,
        "loss_std": mean_std,
        "delta": delta,
        "winner": winner,
        "seed_losses_R": r_losses,
        "seed_losses_std": std_losses,
    })

    print(f"n={n_blocks}: R({n_blocks})={r_clip:.4f} | loss_R={mean_r:.4f} | loss_std={mean_std:.4f} | delta={delta:+.4f} | winner={winner}")

# Summary table
print("\n--- H-CX-63 Results Table ---")
print(f"| n_blocks | R(n)    | loss_R(n) | loss_std | delta    | winner |")
print(f"|----------|---------|-----------|----------|----------|--------|")
for r in results_63:
    print(f"| {r['n_blocks']:8d} | {r['R_n']:7.4f} | {r['loss_R']:9.4f} | {r['loss_std']:8.4f} | {r['delta']:+8.4f} | {r['winner']:6s} |")

r_wins = sum(1 for r in results_63 if r['winner'] == 'R(n)')
std_wins = sum(1 for r in results_63 if r['winner'] == 'std')
print(f"\nR(n) wins: {r_wins}/6, std wins: {std_wins}/6")

# Per-seed detail
print("\n--- Per-seed detail ---")
print(f"| n_blocks | R(n) | seed | loss_R  | loss_std | delta   |")
print(f"|----------|------|------|---------|----------|---------|")
for r in results_63:
    for i, seed in enumerate(SEEDS):
        lr_ = r['seed_losses_R'][i]
        ls_ = r['seed_losses_std'][i]
        d_ = lr_ - ls_
        print(f"| {r['n_blocks']:8d} | {r['R_n']:4.3f} | {seed:4d} | {lr_:7.4f} | {ls_:8.4f} | {d_:+7.4f} |")


# ============================================================
# EXPERIMENT 2: H-CX-64 — heads configuration for 6-block model
# ============================================================
print("\n" + "="*60)
print("EXPERIMENT 2: H-CX-64 — heads=sopfr(6)=5 configuration")
print("="*60)
print("Config: n_blocks=6, vocab=256, d_model=120, 300 steps, 2 seeds")
print("sopfr(6) = sum of prime factors with repetition = 2+3 = 5")
print("d_model=120 = lcm(1,2,3,4,5,6)*2, divisible by all heads 1..6")
print()

# sopfr(6) = 2 + 3 = 5 (sum of prime factors with repetition)
# d_model = lcm(1,2,3,4,5,6)*2 = 60*2 = 120

D_MODEL_64 = 120  # lcm(1,2,3,4,5,6) = 60, *2 = 120
N_BLOCKS_64 = 6
N_STEPS_64 = 300

# Verify d_model divisible by all heads 1..6
print(f"d_model=120 divisibility check:")
for h in range(1, 7):
    ok = 120 % h == 0
    print(f"  120 / {h} = {120//h if ok else 'NOT DIVISIBLE'} {'OK' if ok else 'FAIL'}")

results_64 = []

for n_heads in [1, 2, 3, 4, 5, 6]:
    head_losses = []

    for seed in SEEDS:
        torch.manual_seed(seed)
        model = MiniTransformer(VOCAB, D_MODEL_64, N_BLOCKS_64, n_heads)
        loss = train_model(model, N_STEPS_64, 1.0, seed, device, VOCAB)
        head_losses.append(loss)
        del model

    mean_loss = np.mean(head_losses)
    results_64.append({
        "n_heads": n_heads,
        "mean_loss": mean_loss,
        "seed_losses": head_losses,
    })
    print(f"heads={n_heads}: mean_loss={mean_loss:.4f} (seeds: {[f'{l:.4f}' for l in head_losses]})")

# Sort by loss to find winner
results_64_sorted = sorted(results_64, key=lambda x: x['mean_loss'])
best = results_64_sorted[0]

print("\n--- H-CX-64 Results Table ---")
print(f"| n_heads | mean_loss | seed={SEEDS[0]}  | seed={SEEDS[1]}  | rank |")
print(f"|---------|-----------|---------|---------|------|")
for rank, r in enumerate(results_64_sorted, 1):
    marker = " <-- BEST" if rank == 1 else (" <-- sopfr(6)" if r['n_heads'] == 5 else "")
    print(f"| {r['n_heads']:7d} | {r['mean_loss']:9.4f} | {r['seed_losses'][0]:7.4f} | {r['seed_losses'][1]:7.4f} | {rank:4d} |{marker}")

print(f"\nBest heads: {best['n_heads']} (loss={best['mean_loss']:.4f})")

# Check sopfr(6) = 5 specifically
sopfr6_result = next(r for r in results_64 if r['n_heads'] == 5)
print(f"sopfr(6)=5 rank: {results_64_sorted.index(sopfr6_result)+1}/6 (loss={sopfr6_result['mean_loss']:.4f})")

# ASCII bar chart of losses
print("\n--- Loss by heads (ASCII bar chart, lower=better) ---")
min_loss = min(r['mean_loss'] for r in results_64)
max_loss = max(r['mean_loss'] for r in results_64)
bar_width = 40
for r in results_64:
    frac = (r['mean_loss'] - min_loss) / (max_loss - min_loss + 1e-9)
    bar_len = int(frac * bar_width)
    bar = "#" * bar_len
    marker = " <-- sopfr(6)" if r['n_heads'] == 5 else ""
    print(f"  heads={r['n_heads']}: [{bar:<{bar_width}}] {r['mean_loss']:.4f}{marker}")

print("\n=== EXPERIMENT COMPLETE ===")

# Summary verdict
print("\n--- VERDICT ---")
print(f"H-CX-63: R(n) clip beats standard in {r_wins}/6 block counts")
if r_wins > 3:
    print("  -> SUPPORTS H-CX-63 (R(n) clip is mostly better)")
elif r_wins == 3:
    print("  -> NEUTRAL (tie)")
else:
    print("  -> REFUTES H-CX-63 (standard clip is mostly better)")

sopfr_rank = results_64_sorted.index(sopfr6_result) + 1
print(f"H-CX-64: sopfr(6)=5 heads ranks {sopfr_rank}/6")
if sopfr_rank == 1:
    print("  -> SUPPORTS H-CX-64 (heads=5 is optimal for 6-block)")
elif sopfr_rank <= 2:
    print("  -> WEAK SUPPORT for H-CX-64 (heads=5 near top)")
else:
    print("  -> REFUTES H-CX-64 (heads=5 not optimal)")
