"""
H-CX-69: Cyclotomic Activation Re-run (300 steps)
Compares GELU vs Phi6_norm vs Phi6_clip on a small transformer
"""
import torch
import torch.nn as nn
import torch.nn.functional as F
import math
import time

torch.manual_seed(42)

VOCAB = 64
SEQ_LEN = 32
BATCH = 16
D_MODEL = 64
N_HEADS = 4
N_LAYERS = 4
STEPS = 300
LR = 1e-3

# --- Activation functions ---

def phi6_norm(x):
    """Normalized 6th cyclotomic: (x^2 - x + 1) / (1 + x^2)"""
    return (x**2 - x + 1) / (1 + x**2)

def phi6_clip(x):
    """Clipped cyclotomic: clip to [-3,3] then apply x^2 - x + 1"""
    x_c = torch.clamp(x, -3.0, 3.0)
    return x_c**2 - x_c + 1

# --- Transformer components ---

class MultiHeadSelfAttention(nn.Module):
    def __init__(self, d_model, n_heads):
        super().__init__()
        assert d_model % n_heads == 0
        self.n_heads = n_heads
        self.d_head = d_model // n_heads
        self.qkv = nn.Linear(d_model, 3 * d_model)
        self.proj = nn.Linear(d_model, d_model)

    def forward(self, x):
        B, T, C = x.shape
        qkv = self.qkv(x).reshape(B, T, 3, self.n_heads, self.d_head)
        qkv = qkv.permute(2, 0, 3, 1, 4)
        q, k, v = qkv[0], qkv[1], qkv[2]
        scale = math.sqrt(self.d_head)
        attn = (q @ k.transpose(-2, -1)) / scale
        mask = torch.tril(torch.ones(T, T, device=x.device)).bool()
        attn = attn.masked_fill(~mask, float('-inf'))
        attn = F.softmax(attn, dim=-1)
        out = (attn @ v).transpose(1, 2).reshape(B, T, C)
        return self.proj(out)

class TransformerBlock(nn.Module):
    def __init__(self, d_model, n_heads, act_fn):
        super().__init__()
        self.attn = MultiHeadSelfAttention(d_model, n_heads)
        self.ln1 = nn.LayerNorm(d_model)
        self.ln2 = nn.LayerNorm(d_model)
        self.fc1 = nn.Linear(d_model, 4 * d_model)
        self.fc2 = nn.Linear(4 * d_model, d_model)
        self.act_fn = act_fn

    def forward(self, x):
        x = x + self.attn(self.ln1(x))
        h = self.fc1(self.ln2(x))
        h = self.act_fn(h)
        x = x + self.fc2(h)
        return x

class SmallTransformer(nn.Module):
    def __init__(self, vocab, d_model, n_heads, n_layers, act_fn):
        super().__init__()
        self.embed = nn.Embedding(vocab, d_model)
        self.pos_embed = nn.Embedding(SEQ_LEN, d_model)
        self.blocks = nn.ModuleList([
            TransformerBlock(d_model, n_heads, act_fn) for _ in range(n_layers)
        ])
        self.ln_f = nn.LayerNorm(d_model)
        self.head = nn.Linear(d_model, vocab, bias=False)

    def forward(self, idx):
        B, T = idx.shape
        pos = torch.arange(T, device=idx.device).unsqueeze(0)
        x = self.embed(idx) + self.pos_embed(pos)
        for block in self.blocks:
            x = block(x)
        x = self.ln_f(x)
        return self.head(x)

def count_params(model):
    return sum(p.numel() for p in model.parameters())

def generate_batch():
    data = torch.randint(0, VOCAB, (BATCH, SEQ_LEN + 1))
    x = data[:, :-1]
    y = data[:, 1:]
    return x, y

def train(act_name, act_fn):
    torch.manual_seed(42)
    model = SmallTransformer(VOCAB, D_MODEL, N_HEADS, N_LAYERS, act_fn)
    optimizer = torch.optim.AdamW(model.parameters(), lr=LR)
    n_params = count_params(model)

    losses = []
    step_losses = {}
    t0 = time.time()

    for step in range(1, STEPS + 1):
        x, y = generate_batch()
        logits = model(x)
        loss = F.cross_entropy(logits.reshape(-1, VOCAB), y.reshape(-1))
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        losses.append(loss.item())
        if step in (1, 10, 50, 100, 150, 200, 250, 300):
            step_losses[step] = loss.item()

    elapsed = time.time() - t0
    final_loss = losses[-1]
    # Convergence speed: steps to reach within 10% of final loss
    target = final_loss * 1.1
    conv_step = next((i+1 for i, l in enumerate(losses) if l <= target), STEPS)

    return {
        'act': act_name,
        'n_params': n_params,
        'final_loss': final_loss,
        'conv_step': conv_step,
        'elapsed': elapsed,
        'step_losses': step_losses,
        'losses': losses,
    }

# --- Run experiments ---
print("# H-CX-69: Cyclotomic Activation Comparison (300 steps)")
print()

configs = [
    ('GELU',       F.gelu),
    ('Phi6_norm',  phi6_norm),
    ('Phi6_clip',  phi6_clip),
]

results = []
for name, fn in configs:
    print(f"Training {name}...", flush=True)
    r = train(name, fn)
    results.append(r)
    print(f"  Done: final_loss={r['final_loss']:.4f}, conv_step={r['conv_step']}, time={r['elapsed']:.1f}s", flush=True)

print()
print("## Summary Table")
print()
print("| Activation | Params | Final Loss | Conv Step | Time (s) |")
print("|---|---|---|---|---|")
for r in results:
    print(f"| {r['act']} | {r['n_params']:,} | {r['final_loss']:.4f} | {r['conv_step']} | {r['elapsed']:.1f} |")

print()
print("## Loss at Key Steps")
print()
steps_header = [1, 10, 50, 100, 150, 200, 250, 300]
print("| Activation | " + " | ".join(f"Step {s}" for s in steps_header) + " |")
print("|---|" + "|".join(["---"] * len(steps_header)) + "|")
for r in results:
    row = " | ".join(f"{r['step_losses'].get(s, 'N/A'):.4f}" for s in steps_header)
    print(f"| {r['act']} | {row} |")

print()
print("## Relative Performance vs GELU (Final Loss)")
baseline = results[0]['final_loss']
print()
print("| Activation | Final Loss | Delta vs GELU | % Better |")
print("|---|---|---|---|")
for r in results:
    delta = r['final_loss'] - baseline
    pct = -delta / baseline * 100
    sign = "+" if delta >= 0 else ""
    print(f"| {r['act']} | {r['final_loss']:.4f} | {sign}{delta:.4f} | {pct:+.2f}% |")

print()
print("## ASCII Loss Curves (Final 50 steps)")
print()
print("```")
all_losses = {r['act']: r['losses'] for r in results}
final_50 = {k: v[-50:] for k, v in all_losses.items()}
colors = list(final_50.keys())
HEIGHT = 10
all_vals = [v for vals in final_50.values() for v in vals]
lo, hi = min(all_vals), max(all_vals)
span = hi - lo if hi != lo else 1

for row_i in range(HEIGHT, -1, -1):
    threshold = lo + span * row_i / HEIGHT
    line = f"{threshold:6.3f} |"
    for step_i in range(50):
        chars = []
        for ci, (act, vals) in enumerate(final_50.items()):
            v = vals[step_i]
            if abs(v - threshold) < span / (2 * HEIGHT):
                chars.append(act[0])
        if chars:
            line += chars[0]
        else:
            line += " "
    print(line)
print("       " + "-" * 50)
print("       Step 251" + " " * 38 + "300")
print()
for act in colors:
    print(f"  {act[0]} = {act}")
print("```")

print()
print("## Interpretation")
print()
print("- Phi6_norm: (x^2-x+1)/(1+x^2) — smooth bounded activation, always > 0")
print("- Phi6_clip: clamp then polynomial — harder non-linearity, larger magnitude")
print("- GELU: standard baseline")
print()
print("Done.")
