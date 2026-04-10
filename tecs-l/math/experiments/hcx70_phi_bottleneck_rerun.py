"""
H-CX-70: Phi-Bottleneck Re-run (300 steps)
Compares Standard d_model=64 vs Phi-bottleneck (64 -> 21 -> 64)
phi(6) = 2, so bottleneck = 64 * phi(6)/6 = 64 * 2/6 = 64/3 ≈ 21
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

# phi(6) = 2 (Euler's totient of 6)
PHI_6 = 2
BOTTLENECK_DIM = int(D_MODEL * PHI_6 / 6)  # = 64 * 2/6 = 21

print(f"# H-CX-70: Phi-Bottleneck Experiment (300 steps)")
print(f"")
print(f"## Configuration")
print(f"")
print(f"| Parameter | Value |")
print(f"|---|---|")
print(f"| d_model | {D_MODEL} |")
print(f"| phi(6) | {PHI_6} |")
print(f"| Bottleneck dim | {D_MODEL} * {PHI_6} / 6 = {BOTTLENECK_DIM} |")
print(f"| Vocab | {VOCAB} |")
print(f"| Seq len | {SEQ_LEN} |")
print(f"| Batch | {BATCH} |")
print(f"| Layers | {N_LAYERS} |")
print(f"| Heads | {N_HEADS} |")
print(f"| Steps | {STEPS} |")
print(f"| LR | {LR} |")
print()

# --- Attention ---
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

# --- Standard FFN block ---
class StandardFFN(nn.Module):
    def __init__(self, d_model):
        super().__init__()
        self.fc1 = nn.Linear(d_model, 4 * d_model)
        self.fc2 = nn.Linear(4 * d_model, d_model)

    def forward(self, x):
        return self.fc2(F.gelu(self.fc1(x)))

    def param_count(self):
        return sum(p.numel() for p in self.parameters())

# --- Phi-Bottleneck FFN block ---
class PhiBottleneckFFN(nn.Module):
    """d_model -> bottleneck -> 4*d_model -> bottleneck -> d_model"""
    def __init__(self, d_model, bottleneck_dim):
        super().__init__()
        # Compress to bottleneck, expand to 4x, then back through bottleneck to d_model
        self.fc_in   = nn.Linear(d_model, bottleneck_dim)      # 64 -> 21
        self.fc_mid1 = nn.Linear(bottleneck_dim, 4 * d_model)  # 21 -> 256
        self.fc_mid2 = nn.Linear(4 * d_model, bottleneck_dim)  # 256 -> 21
        self.fc_out  = nn.Linear(bottleneck_dim, d_model)       # 21 -> 64

    def forward(self, x):
        x = F.gelu(self.fc_in(x))
        x = F.gelu(self.fc_mid1(x))
        x = F.gelu(self.fc_mid2(x))
        x = self.fc_out(x)
        return x

    def param_count(self):
        return sum(p.numel() for p in self.parameters())

# --- Transformer Block (generic) ---
class TransformerBlock(nn.Module):
    def __init__(self, d_model, n_heads, ffn):
        super().__init__()
        self.attn = MultiHeadSelfAttention(d_model, n_heads)
        self.ln1 = nn.LayerNorm(d_model)
        self.ln2 = nn.LayerNorm(d_model)
        self.ffn = ffn

    def forward(self, x):
        x = x + self.attn(self.ln1(x))
        x = x + self.ffn(self.ln2(x))
        return x

# --- Full Transformer ---
class SmallTransformer(nn.Module):
    def __init__(self, vocab, d_model, n_heads, n_layers, ffn_builder):
        super().__init__()
        self.embed = nn.Embedding(vocab, d_model)
        self.pos_embed = nn.Embedding(SEQ_LEN, d_model)
        self.blocks = nn.ModuleList([
            TransformerBlock(d_model, n_heads, ffn_builder(i)) for i in range(n_layers)
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

def train(name, ffn_builder):
    torch.manual_seed(42)
    model = SmallTransformer(VOCAB, D_MODEL, N_HEADS, N_LAYERS, ffn_builder)
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
    # Steps to converge to within 10% of final
    target = final_loss * 1.1
    conv_step = next((i+1 for i, l in enumerate(losses) if l <= target), STEPS)

    return {
        'name': name,
        'n_params': n_params,
        'final_loss': final_loss,
        'conv_step': conv_step,
        'elapsed': elapsed,
        'step_losses': step_losses,
        'losses': losses,
    }

# --- Builders ---
def standard_builder(i):
    return StandardFFN(D_MODEL)

def phi_bottleneck_builder(i):
    return PhiBottleneckFFN(D_MODEL, BOTTLENECK_DIM)

# --- Run ---
configs = [
    ('Standard (d=64)',           standard_builder),
    (f'Phi-Bottleneck (d={BOTTLENECK_DIM})', phi_bottleneck_builder),
]

results = []
for name, builder in configs:
    print(f"Training {name}...", flush=True)
    r = train(name, builder)
    results.append(r)
    print(f"  Done: final_loss={r['final_loss']:.4f}, params={r['n_params']:,}, time={r['elapsed']:.1f}s", flush=True)

print()
print("## Summary Table")
print()
print("| Model | Params | Final Loss | Conv Step | Time (s) | Loss/kParam |")
print("|---|---|---|---|---|---|")
for r in results:
    lpkp = r['final_loss'] / (r['n_params'] / 1000)
    print(f"| {r['name']} | {r['n_params']:,} | {r['final_loss']:.4f} | {r['conv_step']} | {r['elapsed']:.1f} | {lpkp:.5f} |")

print()
print("## Loss at Key Steps")
print()
steps_header = [1, 10, 50, 100, 150, 200, 250, 300]
print("| Model | " + " | ".join(f"Step {s}" for s in steps_header) + " |")
print("|---|" + "|".join(["---"] * len(steps_header)) + "|")
for r in results:
    row = " | ".join(f"{r['step_losses'].get(s, 'N/A'):.4f}" for s in steps_header)
    print(f"| {r['name']} | {row} |")

print()
print("## Efficiency Analysis")
print()
standard = results[0]
bottleneck = results[1]

param_ratio = bottleneck['n_params'] / standard['n_params']
loss_ratio = bottleneck['final_loss'] / standard['final_loss']
param_savings = (1 - param_ratio) * 100
loss_delta = bottleneck['final_loss'] - standard['final_loss']

print("| Metric | Standard | Phi-Bottleneck | Ratio |")
print("|---|---|---|---|")
print(f"| Parameters | {standard['n_params']:,} | {bottleneck['n_params']:,} | {param_ratio:.3f} |")
print(f"| Final Loss | {standard['final_loss']:.4f} | {bottleneck['final_loss']:.4f} | {loss_ratio:.3f} |")
print(f"| Param Savings | — | {param_savings:.1f}% fewer | — |")
print(f"| Loss Delta | — | {loss_delta:+.4f} | — |")
std_eff = standard['final_loss'] / (standard['n_params'] / 1000)
bn_eff = bottleneck['final_loss'] / (bottleneck['n_params'] / 1000)
print(f"| Loss/kParam | {std_eff:.5f} | {bn_eff:.5f} | {bn_eff/std_eff:.3f} |")

print()
print("## ASCII Loss Curves")
print()
print("```")
all_losses = {r['name'].split(' ')[0]: r['losses'] for r in results}
HEIGHT = 10
all_vals = [v for vals in all_losses.values() for v in vals]
lo, hi = min(all_vals), max(all_vals)
span = hi - lo if hi != lo else 1

keys = list(all_losses.keys())
symbols = ['S', 'P']

for row_i in range(HEIGHT, -1, -1):
    threshold = lo + span * row_i / HEIGHT
    line = f"{threshold:6.3f} |"
    for step_i in range(0, STEPS, STEPS // 50):
        chars = []
        for ci, (act, vals) in enumerate(all_losses.items()):
            if step_i < len(vals):
                v = vals[step_i]
                if abs(v - threshold) < span / (2 * HEIGHT):
                    chars.append(symbols[ci])
        if chars:
            line += chars[0]
        else:
            line += " "
    print(line)
print("       " + "-" * 50)
print("       Step 1" + " " * 40 + "300")
for i, k in enumerate(keys):
    print(f"  {symbols[i]} = {k}")
print("```")

print()
print("## Interpretation")
print()
print(f"- Bottleneck dim = {BOTTLENECK_DIM} = floor(64 * phi(6)/6) = floor(64 * 2/6)")
print(f"- phi(6) = Euler totient = #{'{'}k : gcd(k,6)=1, 1<=k<=6{'}'} = #{'{'}1,5{'}'} = 2")
print(f"- Bottleneck ratio = {PHI_6}/6 = {PHI_6/6:.4f} ≈ 1/3")
print(f"- If Phi-bottleneck achieves similar loss with fewer params -> efficiency gain confirmed")
print(f"- If loss degrades significantly -> bottleneck too narrow for this task")
print()
print("Done.")
