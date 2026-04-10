"""
H-EN-5: HCN Dimension vs Power-of-2 Dimension comparison

Hypothesis: HCN (Highly Composite Number) dimensions achieve similar loss
with fewer parameters due to higher divisor density (eta = tau(d) / d).

Setup:
  - 2-layer transformer, 4 heads, vocab=256, seq_len=64
  - HCN d_model: 12, 24, 60, 120
  - Power-of-2 d_model: 16, 32, 64, 128
  - 200 training steps, batch=16, random next-token prediction
  - Metric: loss_improvement_per_MFLOP (efficiency)
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import time
import math

# --- Divisor count utility ---
def tau(n):
    """Number of divisors of n."""
    count = 0
    for i in range(1, int(n**0.5) + 1):
        if n % i == 0:
            count += 2 if i != n // i else 1
    return count

def divisor_density(d):
    return tau(d) / d

# --- Minimal Transformer ---
class TransformerBlock(nn.Module):
    def __init__(self, d_model, n_heads):
        super().__init__()
        # Ensure head_dim is integer; adjust n_heads if needed
        assert d_model % n_heads == 0, f"d_model={d_model} not divisible by n_heads={n_heads}"
        self.attn = nn.MultiheadAttention(d_model, n_heads, batch_first=True)
        self.ff1 = nn.Linear(d_model, 4 * d_model)
        self.ff2 = nn.Linear(4 * d_model, d_model)
        self.ln1 = nn.LayerNorm(d_model)
        self.ln2 = nn.LayerNorm(d_model)

    def forward(self, x):
        # Self-attention with residual
        attn_out, _ = self.attn(x, x, x)
        x = self.ln1(x + attn_out)
        # Feed-forward with residual
        ff_out = self.ff2(F.gelu(self.ff1(x)))
        x = self.ln2(x + ff_out)
        return x

class TinyTransformerLM(nn.Module):
    def __init__(self, d_model, n_heads, vocab_size, seq_len, n_layers=2):
        super().__init__()
        self.embed = nn.Embedding(vocab_size, d_model)
        self.pos_embed = nn.Embedding(seq_len, d_model)
        self.blocks = nn.ModuleList([
            TransformerBlock(d_model, n_heads) for _ in range(n_layers)
        ])
        self.head = nn.Linear(d_model, vocab_size, bias=False)

    def forward(self, x):
        B, T = x.shape
        pos = torch.arange(T, device=x.device).unsqueeze(0)
        h = self.embed(x) + self.pos_embed(pos)
        for block in self.blocks:
            h = block(h)
        return self.head(h)

def count_params(model):
    return sum(p.numel() for p in model.parameters())

def estimate_flops(n_params, batch_size, seq_len, n_steps):
    """Rough FLOP estimate: 6 * params * batch * seq_len * steps (standard LLM estimate)."""
    return 6 * n_params * batch_size * seq_len * n_steps

def run_experiment(d_model, n_heads, vocab_size, seq_len, n_steps, batch_size, device):
    """Train model and return (final_loss, initial_loss, n_params, elapsed_seconds)."""
    torch.manual_seed(42)

    # Adjust n_heads to be compatible with d_model
    adjusted_heads = n_heads
    while d_model % adjusted_heads != 0 and adjusted_heads > 1:
        adjusted_heads -= 1

    model = TinyTransformerLM(d_model, adjusted_heads, vocab_size, seq_len).to(device)
    n_params = count_params(model)

    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)

    # Generate fixed random dataset
    torch.manual_seed(0)
    data = torch.randint(0, vocab_size, (batch_size * n_steps, seq_len + 1), device=device)

    initial_loss = None
    start_time = time.time()

    for step in range(n_steps):
        batch = data[step * batch_size : (step + 1) * batch_size]
        x = batch[:, :-1]   # (B, T)
        y = batch[:, 1:]     # (B, T) next-token targets

        logits = model(x)    # (B, T, vocab)
        loss = F.cross_entropy(logits.reshape(-1, vocab_size), y.reshape(-1))

        if initial_loss is None:
            initial_loss = loss.item()

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

    elapsed = time.time() - start_time
    final_loss = loss.item()
    return final_loss, initial_loss, n_params, elapsed, adjusted_heads

def main():
    device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
    print(f"Device: {device}\n")

    VOCAB_SIZE = 256
    SEQ_LEN = 64
    N_STEPS = 200
    BATCH_SIZE = 16
    N_HEADS = 4

    # HCN dimensions (highly composite numbers)
    hcn_dims = [12, 24, 60, 120]
    # Power-of-2 dimensions
    pow2_dims = [16, 32, 64, 128]

    print("Running experiments...")
    print("=" * 80)

    results = []

    all_dims = [("HCN", d) for d in hcn_dims] + [("Pow2", d) for d in pow2_dims]

    for dim_type, d_model in all_dims:
        print(f"  Testing {dim_type} d_model={d_model} ...", end=" ", flush=True)
        final_loss, init_loss, n_params, elapsed, actual_heads = run_experiment(
            d_model, N_HEADS, VOCAB_SIZE, SEQ_LEN, N_STEPS, BATCH_SIZE, device
        )
        flops = estimate_flops(n_params, BATCH_SIZE, SEQ_LEN, N_STEPS)
        flops_M = flops / 1e6
        loss_improvement = init_loss - final_loss
        efficiency = loss_improvement / flops_M if flops_M > 0 else 0.0
        eta = divisor_density(d_model)
        results.append({
            "type": dim_type,
            "d_model": d_model,
            "tau": tau(d_model),
            "eta": eta,
            "heads": actual_heads,
            "params": n_params,
            "init_loss": init_loss,
            "final_loss": final_loss,
            "loss_improvement": loss_improvement,
            "flops_M": flops_M,
            "efficiency": efficiency,
            "time_s": elapsed,
        })
        print(f"loss={final_loss:.4f}, params={n_params:,}, time={elapsed:.1f}s")

    print()
    print("=" * 80)
    print("## H-EN-5 Results: HCN vs Power-of-2 Dimensions")
    print("=" * 80)
    print()

    # Main results table
    header = (
        "| Type | d_model | tau(d) | eta=tau/d | Heads | Params | "
        "Init Loss | Final Loss | Loss Imp | MFLOP | Eff (imp/MFLOP) | Time(s) |"
    )
    sep = "|------|---------|--------|-----------|-------|--------|----------|------------|----------|-------|-----------------|---------|"
    print(header)
    print(sep)
    for r in results:
        print(
            f"| {r['type']:4s} | {r['d_model']:7d} | {r['tau']:6d} | "
            f"{r['eta']:.4f}    | {r['heads']:5d} | {r['params']:6,} | "
            f"{r['init_loss']:.4f}   | {r['final_loss']:.4f}     | "
            f"{r['loss_improvement']:.4f}   | {r['flops_M']:5.1f} | "
            f"{r['efficiency']:.6f}      | {r['time_s']:.2f}   |"
        )

    print()

    # Summary: compare nearest-param pairs
    print("## Nearest-Param Pair Comparison")
    print()
    print("| HCN | Pow2 | HCN Params | Pow2 Params | HCN Eff | Pow2 Eff | HCN/Pow2 Eff Ratio |")
    print("|-----|------|------------|-------------|---------|----------|---------------------|")
    hcn_results = [r for r in results if r["type"] == "HCN"]
    pow2_results = [r for r in results if r["type"] == "Pow2"]

    # Pair by closest param count
    for hr in hcn_results:
        closest = min(pow2_results, key=lambda p: abs(p["params"] - hr["params"]))
        ratio = hr["efficiency"] / closest["efficiency"] if closest["efficiency"] > 0 else float("nan")
        print(
            f"| {hr['d_model']:3d} | {closest['d_model']:4d} | "
            f"{hr['params']:10,} | {closest['params']:11,} | "
            f"{hr['efficiency']:.6f} | {closest['efficiency']:.6f} | "
            f"{ratio:.4f}              |"
        )

    print()

    # Divisor density summary
    print("## Divisor Density (eta = tau(d)/d)")
    print()
    print("| Type | d_model | tau(d) | eta   | Relative to Pow2 pair |")
    print("|------|---------|--------|-------|----------------------|")
    for r in results:
        # find pow2 pair
        closest_pow2 = min(pow2_results, key=lambda p: abs(p["d_model"] - r["d_model"])) if r["type"] == "HCN" else None
        if r["type"] == "HCN" and closest_pow2:
            rel = r["eta"] / closest_pow2["eta"]
            print(f"| {r['type']:4s} | {r['d_model']:7d} | {r['tau']:6d} | {r['eta']:.4f} | {rel:.3f}x higher          |")
        else:
            print(f"| {r['type']:4s} | {r['d_model']:7d} | {r['tau']:6d} | {r['eta']:.4f} | —                    |")

    print()

    # Statistical summary
    hcn_eff = [r["efficiency"] for r in hcn_results]
    pow2_eff = [r["efficiency"] for r in pow2_results]
    hcn_mean_eff = sum(hcn_eff) / len(hcn_eff)
    pow2_mean_eff = sum(pow2_eff) / len(pow2_eff)
    overall_ratio = hcn_mean_eff / pow2_mean_eff if pow2_mean_eff > 0 else float("nan")

    hcn_losses = [r["final_loss"] for r in hcn_results]
    pow2_losses = [r["final_loss"] for r in pow2_results]

    print("## Summary Statistics")
    print()
    print(f"| Metric                   | HCN (mean)   | Pow2 (mean)  | Ratio |")
    print(f"|--------------------------|--------------|--------------|-------|")
    print(f"| Mean efficiency          | {hcn_mean_eff:.6f}  | {pow2_mean_eff:.6f}  | {overall_ratio:.4f} |")
    print(f"| Mean final loss          | {sum(hcn_losses)/len(hcn_losses):.4f}       | {sum(pow2_losses)/len(pow2_losses):.4f}       |       |")
    print(f"| Mean eta (tau/d)         | {sum(r['eta'] for r in hcn_results)/len(hcn_results):.4f}       | {sum(r['eta'] for r in pow2_results)/len(pow2_results):.4f}       |       |")

    print()
    print("## Hypothesis Verdict")
    print()
    if overall_ratio > 1.0:
        verdict = f"SUPPORTED — HCN dims are {overall_ratio:.3f}x more efficient than Pow2 dims"
    elif overall_ratio > 0.95:
        verdict = f"NEUTRAL — HCN dims show comparable efficiency (ratio={overall_ratio:.3f})"
    else:
        verdict = f"NOT SUPPORTED — Pow2 dims are {1/overall_ratio:.3f}x more efficient (ratio={overall_ratio:.3f})"
    print(f"  {verdict}")

    print()
    print("Notes:")
    print("  - Efficiency = (initial_loss - final_loss) / MFLOP")
    print("  - FLOP estimate: 6 * params * batch * seq_len * steps")
    print("  - Higher eta means more structural factors per dimension unit")
    print("  - Random data; measures optimizer convergence, not linguistic capability")

if __name__ == "__main__":
    main()
