"""
HEN-1: phi-bottleneck (1/3 compression) Pareto efficiency test
==============================================================
Claim: Reducing FFN hidden dim by phi(6)/6 = 1/3 saves ~67% FFN params
       with minimal quality loss — placing it on the Pareto frontier.

Configs tested:
  a. Standard:        d_ff = 4 * d_model = 512
  b. Phi-bottleneck:  d_ff = 4 * d_model * phi(6)/6 = 512/3 ~ 171
  c. Half:            d_ff = 2 * d_model = 256
  d. Quarter:         d_ff = 1 * d_model = 128

Task: Character-level language model, 2-layer transformer, d_model=128, 4 heads
"""

import math
import time
import random
import torch
import torch.nn as nn
import torch.nn.functional as F

# ── Reproducibility ──────────────────────────────────────────────────────────
SEED = 42
random.seed(SEED)
torch.manual_seed(SEED)

# ── Training text ─────────────────────────────────────────────────────────────
BASE_TEXT = (
    "Mathematics reveals deep structure. "
    "The number six is perfect because its divisors one two and three sum to itself. "
    "Neural networks learn patterns through gradient descent optimization. "
    "Transformers use attention mechanisms to process sequences efficiently."
)
TEXT = (BASE_TEXT + " ") * 200

# ── Vocabulary ────────────────────────────────────────────────────────────────
chars = sorted(set(TEXT))
vocab_size = len(chars)
c2i = {c: i for i, c in enumerate(chars)}
i2c = {i: c for c, i in c2i.items()}
data = torch.tensor([c2i[c] for c in TEXT], dtype=torch.long)

# ── Hyper-parameters ──────────────────────────────────────────────────────────
D_MODEL  = 128
N_HEADS  = 4
N_LAYERS = 2
SEQ_LEN  = 64
BATCH    = 16
STEPS    = 500
LR       = 3e-3

# phi(6) = |{1,2,3,4,5,6}: gcd(k,6)=1| = |{1,5}| = 2
PHI6 = 2   # Euler totient of 6

# FFN configurations  ─ (label, d_ff)
CONFIGS = [
    ("standard",       4 * D_MODEL),                    # 512
    ("phi-bottleneck", round(4 * D_MODEL * PHI6 / 6)),  # 171
    ("half",           2 * D_MODEL),                    # 256
    ("quarter",        1 * D_MODEL),                    # 128
]

# ── Model ─────────────────────────────────────────────────────────────────────
class FFN(nn.Module):
    def __init__(self, d_model, d_ff):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(d_model, d_ff),
            nn.GELU(),
            nn.Linear(d_ff, d_model),
        )
    def forward(self, x):
        return self.net(x)

class TransformerBlock(nn.Module):
    def __init__(self, d_model, n_heads, d_ff):
        super().__init__()
        self.attn = nn.MultiheadAttention(d_model, n_heads, batch_first=True)
        self.ffn  = FFN(d_model, d_ff)
        self.ln1  = nn.LayerNorm(d_model)
        self.ln2  = nn.LayerNorm(d_model)

    def forward(self, x):
        L = x.size(1)
        mask = torch.triu(torch.ones(L, L, device=x.device), diagonal=1).bool()
        a, _ = self.attn(x, x, x, attn_mask=mask)
        x = self.ln1(x + a)
        x = self.ln2(x + self.ffn(x))
        return x

class CharLM(nn.Module):
    def __init__(self, vocab_size, d_model, n_heads, n_layers, d_ff, seq_len):
        super().__init__()
        self.emb = nn.Embedding(vocab_size, d_model)
        self.pos = nn.Embedding(seq_len, d_model)
        self.blocks = nn.ModuleList(
            [TransformerBlock(d_model, n_heads, d_ff) for _ in range(n_layers)]
        )
        self.head = nn.Linear(d_model, vocab_size)

    def forward(self, idx):
        B, T = idx.shape
        x = self.emb(idx) + self.pos(torch.arange(T, device=idx.device))
        for blk in self.blocks:
            x = blk(x)
        return self.head(x)

# ── Parameter counting ────────────────────────────────────────────────────────
def count_params(model):
    total = sum(p.numel() for p in model.parameters())
    ffn   = sum(p.numel() for blk in model.blocks for p in blk.ffn.parameters())
    return total, ffn

# ── Batch sampler ─────────────────────────────────────────────────────────────
def get_batch():
    ix = torch.randint(len(data) - SEQ_LEN - 1, (BATCH,))
    x = torch.stack([data[i:i+SEQ_LEN]   for i in ix])
    y = torch.stack([data[i+1:i+SEQ_LEN+1] for i in ix])
    return x, y

# ── Train one config ──────────────────────────────────────────────────────────
def train_config(label, d_ff):
    torch.manual_seed(SEED)
    model = CharLM(vocab_size, D_MODEL, N_HEADS, N_LAYERS, d_ff, SEQ_LEN)
    opt   = torch.optim.Adam(model.parameters(), lr=LR)

    total_params, ffn_params = count_params(model)
    loss_history = []

    t0 = time.time()
    for step in range(STEPS):
        x, y = get_batch()
        logits = model(x)
        loss = F.cross_entropy(logits.reshape(-1, vocab_size), y.reshape(-1))
        opt.zero_grad()
        loss.backward()
        nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        opt.step()
        loss_history.append(loss.item())

    elapsed = time.time() - t0
    final_loss = sum(loss_history[-50:]) / 50   # avg last 50 steps
    perplexity = math.exp(final_loss)

    return {
        "label":       label,
        "d_ff":        d_ff,
        "total_params": total_params,
        "ffn_params":  ffn_params,
        "final_loss":  final_loss,
        "perplexity":  perplexity,
        "train_time":  elapsed,
        "loss_history": loss_history,
    }

# ── Main ──────────────────────────────────────────────────────────────────────
print("=" * 70)
print("HEN-1: phi-bottleneck Pareto efficiency test")
print(f"  vocab={vocab_size}  d_model={D_MODEL}  heads={N_HEADS}  layers={N_LAYERS}")
print(f"  seq_len={SEQ_LEN}  batch={BATCH}  steps={STEPS}  lr={LR}")
print(f"  phi(6)={PHI6}  compression_ratio=phi(6)/6={PHI6/6:.4f}")
print("=" * 70)
print()

results = []
for label, d_ff in CONFIGS:
    print(f"Training [{label}]  d_ff={d_ff} ...", flush=True)
    r = train_config(label, d_ff)
    results.append(r)
    print(f"  loss={r['final_loss']:.4f}  ppl={r['perplexity']:.2f}  "
          f"total={r['total_params']:,}  ffn={r['ffn_params']:,}  "
          f"time={r['train_time']:.1f}s")
    print()

# ── Analysis ──────────────────────────────────────────────────────────────────
baseline = next(r for r in results if r["label"] == "standard")

print("=" * 70)
print("RESULTS TABLE")
print("=" * 70)
header = f"{'Config':<18} {'d_ff':>5} {'Total P':>10} {'FFN P':>8} {'Loss':>7} {'PPL':>7} {'Loss/MFFNP':>12} {'Time':>7}"
print(header)
print("-" * len(header))

for r in results:
    loss_per_m = r["final_loss"] / (r["ffn_params"] / 1e6)
    print(f"{r['label']:<18} {r['d_ff']:>5} {r['total_params']:>10,} "
          f"{r['ffn_params']:>8,} {r['final_loss']:>7.4f} {r['perplexity']:>7.2f} "
          f"{loss_per_m:>12.2f} {r['train_time']:>6.1f}s")

print()
print("=" * 70)
print("COMPARISON vs STANDARD BASELINE")
print("=" * 70)
print(f"{'Config':<18} {'FFN save%':>10} {'Loss delta':>12} {'PPL delta':>10} {'Pareto?':>8}")
print("-" * 62)

baseline_ffn = baseline["ffn_params"]
baseline_loss = baseline["final_loss"]
baseline_ppl = baseline["perplexity"]

pareto_front = []   # (ffn_params, loss)
for r in results:
    pareto_front.append((r["ffn_params"], r["final_loss"]))

def is_pareto(r_ffn, r_loss, all_points):
    """True if no other point is strictly better on both axes."""
    for (p, l) in all_points:
        if p <= r_ffn and l <= r_loss and (p < r_ffn or l < r_loss):
            return False
    return True

for r in results:
    ffn_save_pct = 100 * (1 - r["ffn_params"] / baseline_ffn)
    loss_delta   = r["final_loss"] - baseline_loss
    ppl_delta    = r["perplexity"] - baseline_ppl
    pareto       = is_pareto(r["ffn_params"], r["final_loss"], pareto_front)
    flag         = "YES *" if pareto else "no"
    print(f"{r['label']:<18} {ffn_save_pct:>9.1f}% {loss_delta:>+12.4f} "
          f"{ppl_delta:>+10.2f} {flag:>8}")

# ── Quality-efficiency ratio ──────────────────────────────────────────────────
print()
print("=" * 70)
print("QUALITY-EFFICIENCY RATIO  (lower = more efficient)")
print("  Formula: loss_delta / ffn_param_savings  (loss increase per saved param)")
print("=" * 70)
print(f"{'Config':<18} {'FFN saved':>10} {'Loss +delta':>12} {'Ratio':>14}")
print("-" * 58)

for r in results:
    if r["label"] == "standard":
        print(f"{r['label']:<18} {'---':>10} {'---':>12} {'--- (baseline)':>14}")
        continue
    ffn_saved  = baseline_ffn - r["ffn_params"]
    loss_delta = r["final_loss"] - baseline_loss
    ratio      = loss_delta / ffn_saved if ffn_saved > 0 else float("inf")
    print(f"{r['label']:<18} {ffn_saved:>10,} {loss_delta:>+12.4f} {ratio:>14.6f}")

# ── Loss per million FFN parameters ──────────────────────────────────────────
print()
print("=" * 70)
print("LOSS PER MILLION FFN PARAMETERS  (lower = more efficient use of params)")
print("=" * 70)
for r in results:
    lpm = r["final_loss"] / (r["ffn_params"] / 1e6)
    print(f"  {r['label']:<18}  {lpm:.3f}")

# ── ASCII Pareto plot ─────────────────────────────────────────────────────────
print()
print("=" * 70)
print("PARETO PLOT  (x=FFN params, y=loss)  * = Pareto optimal")
print("  Lower-left corner = better (fewer params AND lower loss)")
print("=" * 70)

# Normalize to grid
max_ffn  = max(r["ffn_params"]  for r in results)
min_ffn  = min(r["ffn_params"]  for r in results)
max_loss = max(r["final_loss"]  for r in results)
min_loss = min(r["final_loss"]  for r in results)

W, H = 50, 20
grid = [[" "] * W for _ in range(H)]

SYMBOLS = {
    "standard":       "S",
    "phi-bottleneck": "P",
    "half":           "H",
    "quarter":        "Q",
}

for r in results:
    fx = (r["ffn_params"] - min_ffn) / max(max_ffn - min_ffn, 1)
    fy = (r["final_loss"] - min_loss) / max(max_loss - min_loss, 1)
    col = int(fx * (W - 1))
    row = int((1 - fy) * (H - 1))   # flip y (low loss = top)
    sym = SYMBOLS[r["label"]]
    pareto = is_pareto(r["ffn_params"], r["final_loss"], pareto_front)
    grid[row][col] = f"[{sym}]"[1] if not pareto else f"*{sym}"[1]
    # simpler: just use sym, mark pareto with asterisk prefix in legend
    grid[row][col] = sym

# Draw frame
print("  loss")
print("  ^")
for row_i, row in enumerate(grid):
    bar = "high|" if row_i == 0 else " low|" if row_i == H - 1 else "    |"
    print(bar + "".join(row) + "|")
print("    +" + "-" * W + "+")
print("         low" + " " * (W - 18) + "high  --> FFN params")
print()
print("  Legend:")
for r in results:
    pareto = is_pareto(r["ffn_params"], r["final_loss"], pareto_front)
    sym    = SYMBOLS[r["label"]]
    pflag  = " [PARETO OPTIMAL]" if pareto else ""
    print(f"    {sym} = {r['label']:<18}  ffn={r['ffn_params']:,}  loss={r['final_loss']:.4f}{pflag}")

# ── Loss curve ASCII ──────────────────────────────────────────────────────────
print()
print("=" * 70)
print("LOSS CURVES  (every 50 steps, averaged)")
print("=" * 70)

CURVE_W = 50
CURVE_H = 12

# Sample every 50 steps
samples = list(range(0, STEPS, 50)) + [STEPS - 1]
curves = {}
for r in results:
    hist = r["loss_history"]
    curves[r["label"]] = [
        sum(hist[max(0, i-5):i+5]) / len(hist[max(0, i-5):i+5])
        for i in samples
    ]

all_vals = [v for c in curves.values() for v in c]
lo, hi = min(all_vals), max(all_vals)

syms_order = ["standard", "phi-bottleneck", "half", "quarter"]
sym_chars  = {"standard": "S", "phi-bottleneck": "P", "half": "H", "quarter": "Q"}

# Print curve grid
curve_grid = [[" "] * CURVE_W for _ in range(CURVE_H)]
col_step = max(1, CURVE_W // len(samples))
for ci, step_i in enumerate(samples):
    col = min(ci * col_step, CURVE_W - 1)
    for label in syms_order:
        val = curves[label][ci]
        fy  = (val - lo) / max(hi - lo, 1e-9)
        row = int((1 - fy) * (CURVE_H - 1))
        row = max(0, min(CURVE_H - 1, row))
        if curve_grid[row][col] == " ":
            curve_grid[row][col] = sym_chars[label]
        # collision: place below
        elif row + 1 < CURVE_H and curve_grid[row + 1][col] == " ":
            curve_grid[row + 1][col] = sym_chars[label].lower()

print(f"  loss {hi:.3f}")
for row in curve_grid:
    print("  |" + "".join(row) + "|")
print(f"  loss {lo:.3f}")
print(f"  step 0" + " " * (CURVE_W - 12) + f"step {STEPS}")
print()
print("  S=standard  P=phi-bottleneck  H=half  Q=quarter")

# ── Scale analysis ────────────────────────────────────────────────────────────
print()
print("=" * 70)
print("PRACTICAL SCALE ANALYSIS")
print("=" * 70)

phi_r = next(r for r in results if r["label"] == "phi-bottleneck")
half_r = next(r for r in results if r["label"] == "half")

phi_loss_delta = phi_r["final_loss"] - baseline["final_loss"]
phi_ffn_save   = 100 * (1 - phi_r["ffn_params"] / baseline["ffn_params"])
phi_total_save = 100 * (1 - phi_r["total_params"] / baseline["total_params"])

print(f"""
phi-bottleneck (d_ff = 4*d_model/3) statistics:
  FFN parameter saving : {phi_ffn_save:.1f}%
  Total parameter saving: {phi_total_save:.1f}%
  Loss increase        : {phi_loss_delta:+.4f} nats  ({100*phi_loss_delta/baseline['final_loss']:+.1f}%)
  PPL increase         : {phi_r['perplexity'] - baseline['perplexity']:+.2f}

FLOP estimate (FFN dominates at scale):
  Standard FFN FLOPs   ~ 2 * seq * (2 * d_ff * d_model)
  phi-bottleneck FLOPs ~ {PHI6/6:.3f}x standard
  FLOP savings         ~ {100*(1-PHI6/6):.1f}% per forward pass
  Energy savings (proportional to FLOPs): ~{100*(1-PHI6/6):.1f}%

Scale at which phi-bottleneck matters most:
  - At small scale (d_model=128): loss delta is {phi_loss_delta:+.4f}
  - FFN params grow as O(d_model * d_ff); saving 67% FFN = large absolute saving at scale
  - For GPT-2 (d_model=768, d_ff=3072, 12 layers):
      Standard FFN params  ~ {12 * 2 * 3072 * 768:,}
      phi-bottleneck FFN   ~ {int(12 * 2 * (3072//3) * 768):,}  (d_ff=1024)
      Saving              ~ {12 * 2 * (3072 - 3072//3) * 768:,} params
  - For GPT-3 175B (d_ff ~ 4*d_model, 96 layers, d_model=12288):
      FFN saving          ~ 67% of ~117B FFN params = ~78B params
""")

print("HuggingFace config change (GPT-2 example):")
print("""
  # Standard
  config = GPT2Config(n_embd=768, n_inner=3072)  # or n_inner=None (auto 4x)

  # phi-bottleneck (d_ff = d_model * 4/3)
  config = GPT2Config(n_embd=768, n_inner=1024)  # 768 * 4/3 = 1024

  # For LlamaConfig:
  config = LlamaConfig(hidden_size=4096, intermediate_size=round(4096*4/3))
  # Default intermediate_size=11008; phi-bottleneck = 5461
""")

# ── Summary verdict ───────────────────────────────────────────────────────────
print("=" * 70)
print("VERDICT")
print("=" * 70)

phi_pareto = is_pareto(phi_r["ffn_params"], phi_r["final_loss"], pareto_front)
half_pareto = is_pareto(half_r["ffn_params"], half_r["final_loss"], pareto_front)

print(f"  phi-bottleneck Pareto optimal: {'YES' if phi_pareto else 'NO'}")
print(f"  half (2x) Pareto optimal     : {'YES' if half_pareto else 'NO'}")
print()

if phi_pareto:
    print("  CONCLUSION: phi-bottleneck IS on the Pareto frontier.")
    print("  It achieves fewer FFN params without being dominated by any other config.")
else:
    # Find who dominates phi
    dominators = [
        r["label"] for r in results
        if r["ffn_params"] <= phi_r["ffn_params"]
        and r["final_loss"] <= phi_r["final_loss"]
        and (r["ffn_params"] < phi_r["ffn_params"] or r["final_loss"] < phi_r["final_loss"])
    ]
    print(f"  CONCLUSION: phi-bottleneck is NOT on the Pareto frontier.")
    print(f"  Dominated by: {dominators}")
    print(f"  However, loss increase is only {phi_loss_delta:+.4f} nats "
          f"({100*phi_loss_delta/baseline['final_loss']:+.1f}%) with {phi_ffn_save:.0f}% FFN saving.")

print()
print("=" * 70)
print("HEN-1 COMPLETE")
print("=" * 70)
