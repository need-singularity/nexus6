#!/usr/bin/env python3
"""
HEN-5: HCN vs Power-of-2 Dimensions on Real Language Data
==========================================================
Tests whether Highly Composite Number (HCN) dimensions outperform
standard power-of-2 dimensions in small GPT-like transformers.

Task: Character-level next-token prediction on a structured English corpus.
Metric: Final loss, convergence speed, and parameter efficiency.

Results formatted for AI practitioners.
"""

import math
import time
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.optim import Adam

# ─── Dataset ───────────────────────────────────────────────────────────────────

CORPUS_TEXT = (
    "The quick brown fox jumps over the lazy dog. "
    "A perfect number is a positive integer that is equal to the sum of its proper divisors. "
    "The smallest perfect number is six because one plus two plus three equals six."
)

TRAINING_TEXT = CORPUS_TEXT * 100  # repeat 100x

# Build vocab from unique characters
CHARS = sorted(set(TRAINING_TEXT))
VOCAB_SIZE = len(CHARS)
CHAR2IDX = {c: i for i, c in enumerate(CHARS)}
IDX2CHAR = {i: c for c, i in CHAR2IDX.items()}

TOKENS = torch.tensor([CHAR2IDX[c] for c in TRAINING_TEXT], dtype=torch.long)

SEQ_LEN = 64        # context window
BATCH_SIZE = 32
TRAIN_STEPS = 500
LR = 3e-4
DEVICE = "cpu"      # keep deterministic; MPS optional

torch.manual_seed(42)

# ─── Number-theoretic helpers ──────────────────────────────────────────────────

def num_divisors(n: int) -> int:
    count = 0
    for i in range(1, int(n**0.5) + 1):
        if n % i == 0:
            count += 2 if i != n // i else 1
    return count

def tau(n: int) -> int:
    return num_divisors(n)

# ─── Model ────────────────────────────────────────────────────────────────────

class CausalSelfAttention(nn.Module):
    def __init__(self, d_model: int, num_heads: int):
        super().__init__()
        assert d_model % num_heads == 0, f"d_model={d_model} not divisible by num_heads={num_heads}"
        self.num_heads = num_heads
        self.head_dim = d_model // num_heads
        self.qkv = nn.Linear(d_model, 3 * d_model, bias=False)
        self.proj = nn.Linear(d_model, d_model, bias=False)

    def forward(self, x):
        B, T, C = x.shape
        q, k, v = self.qkv(x).split(C, dim=2)
        q = q.view(B, T, self.num_heads, self.head_dim).transpose(1, 2)
        k = k.view(B, T, self.num_heads, self.head_dim).transpose(1, 2)
        v = v.view(B, T, self.num_heads, self.head_dim).transpose(1, 2)
        scale = self.head_dim ** -0.5
        att = (q @ k.transpose(-2, -1)) * scale
        mask = torch.tril(torch.ones(T, T, device=x.device)).bool()
        att = att.masked_fill(~mask, float('-inf'))
        att = F.softmax(att, dim=-1)
        y = (att @ v).transpose(1, 2).contiguous().view(B, T, C)
        return self.proj(y)


class MLP(nn.Module):
    def __init__(self, d_model: int):
        super().__init__()
        self.fc1 = nn.Linear(d_model, 4 * d_model)
        self.fc2 = nn.Linear(4 * d_model, d_model)

    def forward(self, x):
        return self.fc2(F.gelu(self.fc1(x)))


class TransformerBlock(nn.Module):
    def __init__(self, d_model: int, num_heads: int):
        super().__init__()
        self.ln1 = nn.LayerNorm(d_model)
        self.attn = CausalSelfAttention(d_model, num_heads)
        self.ln2 = nn.LayerNorm(d_model)
        self.mlp = MLP(d_model)

    def forward(self, x):
        x = x + self.attn(self.ln1(x))
        x = x + self.mlp(self.ln2(x))
        return x


class MiniGPT(nn.Module):
    def __init__(self, vocab_size: int, d_model: int, num_heads: int,
                 num_layers: int = 2, seq_len: int = 64):
        super().__init__()
        self.tok_emb = nn.Embedding(vocab_size, d_model)
        self.pos_emb = nn.Embedding(seq_len, d_model)
        self.blocks = nn.Sequential(*[
            TransformerBlock(d_model, num_heads) for _ in range(num_layers)
        ])
        self.ln_f = nn.LayerNorm(d_model)
        self.head = nn.Linear(d_model, vocab_size, bias=False)

    def forward(self, idx):
        B, T = idx.shape
        pos = torch.arange(T, device=idx.device)
        x = self.tok_emb(idx) + self.pos_emb(pos)
        x = self.blocks(x)
        x = self.ln_f(x)
        return self.head(x)

    def count_parameters(self) -> int:
        return sum(p.numel() for p in self.parameters())


# ─── Training ─────────────────────────────────────────────────────────────────

def get_batch(tokens, seq_len, batch_size):
    ix = torch.randint(0, len(tokens) - seq_len - 1, (batch_size,))
    x = torch.stack([tokens[i:i+seq_len] for i in ix])
    y = torch.stack([tokens[i+1:i+seq_len+1] for i in ix])
    return x.to(DEVICE), y.to(DEVICE)


def train_model(d_model: int, num_heads: int, label: str):
    torch.manual_seed(42)
    model = MiniGPT(
        vocab_size=VOCAB_SIZE,
        d_model=d_model,
        num_heads=num_heads,
        num_layers=2,
        seq_len=SEQ_LEN
    ).to(DEVICE)

    n_params = model.count_parameters()
    optimizer = Adam(model.parameters(), lr=LR)
    losses_at = {}
    checkpoints = {100, 200, 300, 400, 500}

    t0 = time.time()
    model.train()
    for step in range(1, TRAIN_STEPS + 1):
        x, y = get_batch(TOKENS, SEQ_LEN, BATCH_SIZE)
        logits = model(x)
        loss = F.cross_entropy(logits.view(-1, VOCAB_SIZE), y.view(-1))
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        if step in checkpoints:
            losses_at[step] = loss.item()

    wall_time = time.time() - t0
    final_loss = losses_at[500]
    loss_per_1m = final_loss / (n_params / 1_000_000)

    return {
        "label": label,
        "d_model": d_model,
        "num_heads": num_heads,
        "tau": tau(d_model),
        "n_params": n_params,
        "wall_time": wall_time,
        "losses": losses_at,
        "final_loss": final_loss,
        "loss_per_1m": loss_per_1m,
    }


# ─── Experiment 1: HCN vs Power-of-2 ──────────────────────────────────────────

PAIRS = [
    # (d_model, num_heads, label)
    (60,  4,  "HCN-60  (τ=12)"),
    (64,  4,  "POW2-64 (τ=7) "),
    (120, 8,  "HCN-120 (τ=16)"),
    (128, 8,  "POW2-128(τ=8) "),
    (240, 8,  "HCN-240 (τ=20)"),
    (256, 8,  "POW2-256(τ=9) "),
]

print("=" * 70)
print("HEN-5: HCN vs Power-of-2 Dimensions — Real Language Data")
print("=" * 70)
print(f"Vocab size  : {VOCAB_SIZE} unique characters")
print(f"Corpus len  : {len(TRAINING_TEXT):,} characters ({len(TOKENS):,} tokens)")
print(f"Seq len     : {SEQ_LEN}  |  Batch size: {BATCH_SIZE}  |  Steps: {TRAIN_STEPS}")
print(f"Task        : Character-level next-token prediction")
print(f"Model       : 2-layer causal transformer (GPT-style)")
print()

results_main = []
for d_model, num_heads, label in PAIRS:
    print(f"  Training {label} ...", flush=True)
    r = train_model(d_model, num_heads, label)
    results_main.append(r)
    print(f"    loss={r['final_loss']:.4f}  params={r['n_params']:,}  time={r['wall_time']:.1f}s")

# ─── Experiment 2: Head-count sweep on d=120 and d=128 ────────────────────────

HEAD_SWEEP_CONFIGS = [
    # (d_model, num_heads, label)
    (120, 4,  "d=120 heads=4 "),
    (120, 6,  "d=120 heads=6 "),
    (120, 8,  "d=120 heads=8 "),
    (120, 10, "d=120 heads=10"),
    (120, 12, "d=120 heads=12"),
    (128, 4,  "d=128 heads=4 "),
    (128, 8,  "d=128 heads=8 "),
    (128, 16, "d=128 heads=16"),
]

print()
print("  Head-count sweep on d=120 (HCN) and d=128 (POW2) ...")
results_heads = []
for d_model, num_heads, label in HEAD_SWEEP_CONFIGS:
    r = train_model(d_model, num_heads, label)
    results_heads.append(r)
    print(f"    {label}  loss={r['final_loss']:.4f}  time={r['wall_time']:.1f}s")

# ─── Output: Main comparison table ────────────────────────────────────────────

print()
print("=" * 70)
print("RESULTS — Main Comparison Table")
print("=" * 70)
print()

hdr = f"| {'Model':<22} | {'d':>4} | {'τ(d)':>5} | {'Params':>8} | {'Loss@500':>8} | {'Loss/1Mpar':>10} | {'Time(s)':>7} |"
sep = "|" + "-"*24 + "|" + "-"*6 + "|" + "-"*7 + "|" + "-"*10 + "|" + "-"*10 + "|" + "-"*12 + "|" + "-"*9 + "|"
print(hdr)
print(sep)
for r in results_main:
    print(f"| {r['label']:<22} | {r['d_model']:>4} | {r['tau']:>5} | {r['n_params']:>8,} | {r['final_loss']:>8.4f} | {r['loss_per_1m']:>10.4f} | {r['wall_time']:>7.1f} |")

# ─── Convergence curves ────────────────────────────────────────────────────────

print()
print("=" * 70)
print("RESULTS — Convergence Curves (cross-entropy loss)")
print("=" * 70)
print()

steps_header = "| {:<22} |".format("Model")
for s in [100, 200, 300, 400, 500]:
    steps_header += f" {'step'+str(s):>8} |"
print(steps_header)

steps_sep = "|" + "-"*24 + "|" + ("-"*10 + "|") * 5
print(steps_sep)

for r in results_main:
    row = f"| {r['label']:<22} |"
    for s in [100, 200, 300, 400, 500]:
        row += f" {r['losses'][s]:>8.4f} |"
    print(row)

# ─── Pair-by-pair deltas ───────────────────────────────────────────────────────

print()
print("=" * 70)
print("RESULTS — HCN vs POW2 Head-to-Head Delta")
print("=" * 70)
print()

pairs_eval = [
    (results_main[0], results_main[1]),   # 60 vs 64
    (results_main[2], results_main[3]),   # 120 vs 128
    (results_main[4], results_main[5]),   # 240 vs 256
]

print(f"| {'Pair':<28} | {'HCN loss':>9} | {'POW2 loss':>9} | {'Delta':>8} | {'Winner':>10} |")
print("|" + "-"*30 + "|" + "-"*11 + "|" + "-"*11 + "|" + "-"*10 + "|" + "-"*12 + "|")
for hcn, pow2 in pairs_eval:
    delta = hcn['final_loss'] - pow2['final_loss']
    winner = "HCN" if delta < 0 else "POW2"
    pct = abs(delta) / pow2['final_loss'] * 100
    label = f"d={hcn['d_model']} vs d={pow2['d_model']}"
    print(f"| {label:<28} | {hcn['final_loss']:>9.4f} | {pow2['final_loss']:>9.4f} | {delta:>+8.4f} | {winner}({pct:.1f}%) |")

# ─── Head sweep results ────────────────────────────────────────────────────────

print()
print("=" * 70)
print("RESULTS — Attention Head Sweep (d=120 HCN vs d=128 POW2)")
print("=" * 70)
print()

print(f"| {'Config':<18} | {'d':>4} | {'Heads':>5} | {'head_dim':>8} | {'Loss@500':>8} | {'Loss/1Mpar':>10} | {'Time(s)':>7} |")
print("|" + "-"*20 + "|" + "-"*6 + "|" + "-"*7 + "|" + "-"*10 + "|" + "-"*10 + "|" + "-"*12 + "|" + "-"*9 + "|")
for r in results_heads:
    head_dim = r['d_model'] // r['num_heads']
    print(f"| {r['label']:<18} | {r['d_model']:>4} | {r['num_heads']:>5} | {head_dim:>8} | {r['final_loss']:>8.4f} | {r['loss_per_1m']:>10.4f} | {r['wall_time']:.1f}s |")

# Best head config for each d
best_120 = min((r for r in results_heads if r['d_model'] == 120), key=lambda r: r['final_loss'])
best_128 = min((r for r in results_heads if r['d_model'] == 128), key=lambda r: r['final_loss'])
print()
print(f"  Best for d=120 (HCN): heads={best_120['num_heads']}  loss={best_120['final_loss']:.4f}")
print(f"  Best for d=128 (POW2): heads={best_128['num_heads']}  loss={best_128['final_loss']:.4f}")
delta_best = best_120['final_loss'] - best_128['final_loss']
print(f"  Best-config delta (HCN - POW2): {delta_best:+.4f}  ({'HCN wins' if delta_best < 0 else 'POW2 wins'})")

# ─── ASCII convergence graph ───────────────────────────────────────────────────

print()
print("=" * 70)
print("ASCII GRAPH — Loss Convergence (d=120 HCN vs d=128 POW2, heads=8)")
print("=" * 70)
print()

r_hcn = results_main[2]   # d=120
r_pow = results_main[3]   # d=128

steps = [100, 200, 300, 400, 500]
all_losses = [r_hcn['losses'][s] for s in steps] + [r_pow['losses'][s] for s in steps]
y_max = max(all_losses) + 0.05
y_min = min(all_losses) - 0.05
height = 12
width = 5  # columns = steps

def scale_y(val):
    return int((y_max - val) / (y_max - y_min) * (height - 1))

grid = [[' '] * (width * 4 + 4) for _ in range(height)]

for col, s in enumerate(steps):
    y_h = scale_y(r_hcn['losses'][s])
    y_p = scale_y(r_pow['losses'][s])
    x = col * 4 + 4
    if 0 <= y_h < height:
        grid[y_h][x] = 'H'
    if 0 <= y_p < height:
        grid[y_p][x] = 'P'

# y-axis labels
for row in range(height):
    val = y_max - row * (y_max - y_min) / (height - 1)
    label = f"{val:5.3f} |"
    line = label + ''.join(grid[row])
    print(line)

print("       " + "".join(f"  {s:<3}" for s in steps))
print("       " + "         (step)")
print()
print("  H = HCN d=120   P = POW2 d=128")

# ─── Divisor count summary ─────────────────────────────────────────────────────

print()
print("=" * 70)
print("MATHEMATICAL CONTEXT — Divisor Counts τ(d)")
print("=" * 70)
print()
print(f"| {'d':>5} | {'τ(d)':>5} | {'Type':<10} | {'Divisors':<40} |")
print("|" + "-"*7 + "|" + "-"*7 + "|" + "-"*12 + "|" + "-"*42 + "|")
for d in [60, 64, 120, 128, 240, 256]:
    divs = [i for i in range(1, d+1) if d % i == 0]
    t = tau(d)
    kind = "HCN" if d in {60, 120, 240} else "2^k"
    print(f"| {d:>5} | {t:>5} | {kind:<10} | {str(divs)[:38]:<40} |")
print()
print("  τ(d) = number of divisors. HCN dimensions have the MOST divisors for their size.")
print("  Divisibility → more valid (num_heads, head_dim) pairings → more architectural choices.")

# ─── Summary statistics ────────────────────────────────────────────────────────

hcn_losses = [results_main[0]['final_loss'], results_main[2]['final_loss'], results_main[4]['final_loss']]
pow_losses  = [results_main[1]['final_loss'], results_main[3]['final_loss'], results_main[5]['final_loss']]
avg_hcn = sum(hcn_losses) / len(hcn_losses)
avg_pow = sum(pow_losses) / len(pow_losses)
wins_hcn = sum(1 for h, p in zip(hcn_losses, pow_losses) if h < p)

print()
print("=" * 70)
print("SUMMARY STATISTICS")
print("=" * 70)
print()
print(f"  Average final loss — HCN: {avg_hcn:.4f}   POW2: {avg_pow:.4f}")
print(f"  HCN wins (lower loss):    {wins_hcn}/3 pairs")
print(f"  Average delta (HCN-POW2): {avg_hcn - avg_pow:+.4f}  ({'HCN better' if avg_hcn < avg_pow else 'POW2 better'})")

hcn_eff  = [results_main[0]['loss_per_1m'], results_main[2]['loss_per_1m'], results_main[4]['loss_per_1m']]
pow_eff  = [results_main[1]['loss_per_1m'], results_main[3]['loss_per_1m'], results_main[5]['loss_per_1m']]
avg_hcn_eff = sum(hcn_eff) / len(hcn_eff)
avg_pow_eff = sum(pow_eff) / len(pow_eff)
print()
print(f"  Average loss/1M params — HCN: {avg_hcn_eff:.4f}   POW2: {avg_pow_eff:.4f}")
print(f"  Parameter efficiency:         {'HCN more efficient' if avg_hcn_eff < avg_pow_eff else 'POW2 more efficient'}")

# ─── Recommendation ───────────────────────────────────────────────────────────

print()
print("=" * 70)
print("RECOMMENDATION FOR AI PRACTITIONERS")
print("=" * 70)
print()

winner_count = wins_hcn
delta_avg = avg_hcn - avg_pow

if winner_count >= 2 and delta_avg < -0.005:
    verdict = "POSITIVE — HCN dimensions show consistent advantage"
    action = "Consider using HCN dimensions (60, 120, 240, 360, 480, 720) as drop-in replacements for 2^k dimensions."
elif winner_count >= 2 and abs(delta_avg) < 0.005:
    verdict = "MIXED — HCN wins by count but margins are small"
    action = "HCN dimensions are at least as good as 2^k. Use them for architectural flexibility (more valid head configs)."
elif winner_count == 1:
    verdict = "WEAK — Neither architecture dominates consistently"
    action = "Default to 2^k for hardware efficiency. HCN has no clear loss advantage at this scale."
else:
    verdict = "NEGATIVE — POW2 outperforms HCN in this experiment"
    action = "Stick with power-of-2 dimensions for this task type."

print(f"  Verdict: {verdict}")
print()
print(f"  Action: {action}")
print()
print("  Key findings:")
print(f"    1. HCN dims won {wins_hcn}/3 size pairs on raw loss.")
print(f"    2. Average loss delta: {delta_avg:+.4f} (HCN vs POW2).")
print(f"    3. HCN d=120 (τ=16 divisors) has {len([i for i in range(1,121) if 120%i==0])} valid head counts,")
print(f"       vs d=128 (τ=8) with only {len([i for i in range(1,129) if 128%i==0])} valid head counts.")
print(f"       → HCN offers 2x more architectural search space with near-identical param count.")
print()
print("  Practical guidance (ordered by confidence):")
print("    [HIGH]   HCN dims give more head-count flexibility — useful for NAS/HPO search spaces.")
print("    [MEDIUM] If loss difference > 2%: prefer HCN for new model families (GPT-size < 1B).")
print("    [MEDIUM] d=120 with heads=12 (d/heads=10) is the richest option by divisor theory.")
print("    [LOW]    Hardware tensor-core alignment favors 2^k. Benchmark on target hardware.")
print("    [LOW]    At scale (>1B params), hardware efficiency likely dominates mathematical advantage.")
print()
print("  HCN dimension reference table for practitioners:")
print(f"    | {'HCN d':>6} | {'τ(d)':>5} | {'Valid head counts':<40} |")
print(f"    |" + "-"*8 + "|" + "-"*7 + "|" + "-"*42 + "|")
for d in [60, 120, 240, 360, 480, 720]:
    heads = [h for h in range(1, d+1) if d % h == 0 and h <= 32]
    print(f"    | {d:>6} | {tau(d):>5} | {str(heads):<40} |")

print()
print("=" * 70)
print("END OF HEN-5 EXPERIMENT")
print("=" * 70)
