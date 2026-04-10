"""
H-EN-2: R=1 as Minimum Energy MoE Operating Point
===================================================
Tests whether k/n = 1/3 (the R=1 ratio tau/sigma) is the most energy-efficient
MoE configuration, where efficiency = (baseline_loss - loss) / active_FLOP.

R = tau / sigma = (1/3) / (1/3) = 1  ← prediction: optimal operating point
"""

import math
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.optim import Adam
import time

# ─── Config ──────────────────────────────────────────────────────────────────
VOCAB      = 128
SEQ_LEN    = 32
D_MODEL    = 64
D_FF       = 256          # expert hidden dim (4x d_model)
BATCH      = 16
STEPS      = 200
LR         = 3e-4
SEED       = 42
DEVICE     = "cpu"        # MPS or CUDA if available

if torch.cuda.is_available():
    DEVICE = "cuda"
elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
    DEVICE = "mps"

torch.manual_seed(SEED)

# Configurations: (n_experts, k_active, label)
CONFIGS = [
    (6,  2, "n=6  k=2  k/n=1/3 [R=1]"),
    (8,  2, "n=8  k=2  k/n=1/4"),
    (8,  4, "n=8  k=4  k/n=1/2"),
    (12, 4, "n=12 k=4  k/n=1/3 [R=1]"),
    (12, 6, "n=12 k=6  k/n=1/2"),
    (16, 4, "n=16 k=4  k/n=1/4"),
    (4,  2, "n=4  k=2  k/n=1/2"),
]

# ─── Model Components ─────────────────────────────────────────────────────────

class Expert(nn.Module):
    """Simple 2-layer MLP expert."""
    def __init__(self, d_model: int, d_ff: int):
        super().__init__()
        self.fc1 = nn.Linear(d_model, d_ff)
        self.fc2 = nn.Linear(d_ff, d_model)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.fc2(F.gelu(self.fc1(x)))


class TopKMoE(nn.Module):
    """Top-K Mixture of Experts layer with noisy gating."""
    def __init__(self, n_experts: int, k: int, d_model: int, d_ff: int):
        super().__init__()
        self.n_experts = n_experts
        self.k = k
        self.gate = nn.Linear(d_model, n_experts, bias=False)
        self.experts = nn.ModuleList([Expert(d_model, d_ff) for _ in range(n_experts)])

    def forward(self, x: torch.Tensor):
        # x: [B, T, D]
        B, T, D = x.shape
        x_flat = x.view(-1, D)  # [B*T, D]
        N = x_flat.shape[0]

        logits = self.gate(x_flat)                     # [N, E]
        topk_val, topk_idx = torch.topk(logits, self.k, dim=-1)  # [N, k]
        gates = F.softmax(topk_val, dim=-1)             # [N, k]

        out = torch.zeros_like(x_flat)
        for i in range(self.k):
            expert_ids = topk_idx[:, i]   # [N]
            g          = gates[:, i]      # [N]
            for e in range(self.n_experts):
                mask = (expert_ids == e)
                if mask.any():
                    expert_out = self.experts[e](x_flat[mask])  # [m, D]
                    out[mask] += g[mask].unsqueeze(-1) * expert_out

        return out.view(B, T, D)


class SimpleMoELM(nn.Module):
    """Minimal language model with one MoE layer."""
    def __init__(self, vocab: int, seq_len: int, d_model: int,
                 n_experts: int, k: int, d_ff: int):
        super().__init__()
        self.embed  = nn.Embedding(vocab, d_model)
        self.pos    = nn.Embedding(seq_len, d_model)
        self.moe    = TopKMoE(n_experts, k, d_model, d_ff)
        self.norm   = nn.LayerNorm(d_model)
        self.head   = nn.Linear(d_model, vocab, bias=False)

    def forward(self, idx: torch.Tensor):
        B, T = idx.shape
        positions = torch.arange(T, device=idx.device).unsqueeze(0)
        x = self.embed(idx) + self.pos(positions)
        x = self.norm(x + self.moe(x))
        return self.head(x)   # [B, T, V]


# ─── Active FLOP Estimate ─────────────────────────────────────────────────────

def active_flop_per_token(k: int, d_model: int, d_ff: int) -> int:
    """
    FLOPs for k active experts processing one token.
    Each expert: fc1  = 2 * d_model * d_ff
                 fc2  = 2 * d_ff * d_model
    Total per token = k * 2 * 2 * d_model * d_ff
    (factor 2 for multiply-add in matmul)
    """
    flop_per_expert = 2 * (2 * d_model * d_ff)
    return k * flop_per_expert


# ─── Training ─────────────────────────────────────────────────────────────────

def generate_batch(vocab: int, seq_len: int, batch: int, device: str):
    """Random token sequences; target = next-token prediction."""
    x = torch.randint(0, vocab, (batch, seq_len), device=device)
    return x[:, :-1], x[:, 1:]          # input, target


def train_config(n_experts: int, k: int, label: str, baseline_loss: float):
    torch.manual_seed(SEED)
    model = SimpleMoELM(VOCAB, SEQ_LEN, D_MODEL, n_experts, k, D_FF).to(DEVICE)
    opt   = Adam(model.parameters(), lr=LR)

    losses = []
    t0 = time.time()
    for step in range(STEPS):
        x, y = generate_batch(VOCAB, SEQ_LEN, BATCH, DEVICE)
        logits = model(x)                               # [B, T-1, V]
        loss = F.cross_entropy(logits.reshape(-1, VOCAB), y.reshape(-1))
        opt.zero_grad()
        loss.backward()
        nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        opt.step()
        losses.append(loss.item())

    final_loss = sum(losses[-20:]) / 20          # average last 20 steps
    elapsed    = time.time() - t0
    flop       = active_flop_per_token(k, D_MODEL, D_FF)
    ratio      = k / n_experts
    improvement = baseline_loss - final_loss
    efficiency  = improvement / flop if flop > 0 else 0.0

    return {
        "label":       label,
        "n":           n_experts,
        "k":           k,
        "ratio":       ratio,
        "final_loss":  final_loss,
        "flop":        flop,
        "improvement": improvement,
        "efficiency":  efficiency,
        "time_s":      elapsed,
    }


# ─── Baseline (dense, no MoE) ─────────────────────────────────────────────────

def get_baseline_loss() -> float:
    """Train a dense 2-layer MLP LM and return its average final loss."""
    torch.manual_seed(SEED)

    class DenseLM(nn.Module):
        def __init__(self):
            super().__init__()
            self.embed = nn.Embedding(VOCAB, D_MODEL)
            self.pos   = nn.Embedding(SEQ_LEN, D_MODEL)
            self.ff1   = nn.Linear(D_MODEL, D_FF)
            self.ff2   = nn.Linear(D_FF, D_MODEL)
            self.norm  = nn.LayerNorm(D_MODEL)
            self.head  = nn.Linear(D_MODEL, VOCAB, bias=False)

        def forward(self, idx):
            B, T = idx.shape
            pos  = torch.arange(T, device=idx.device).unsqueeze(0)
            x    = self.embed(idx) + self.pos(pos)
            x    = self.norm(x + self.ff2(F.gelu(self.ff1(x))))
            return self.head(x)

    model = DenseLM().to(DEVICE)
    opt   = Adam(model.parameters(), lr=LR)
    losses = []
    for _ in range(STEPS):
        x, y = generate_batch(VOCAB, SEQ_LEN, BATCH, DEVICE)
        logits = model(x)
        loss = F.cross_entropy(logits.reshape(-1, VOCAB), y.reshape(-1))
        opt.zero_grad()
        loss.backward()
        nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        opt.step()
        losses.append(loss.item())
    return sum(losses[-20:]) / 20


# ─── Main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print(f"Device: {DEVICE}")
    print(f"Vocab={VOCAB}, SeqLen={SEQ_LEN}, d_model={D_MODEL}, d_ff={D_FF}")
    print(f"Batch={BATCH}, Steps={STEPS}, LR={LR}")
    print()

    print("Training baseline (dense LM)...")
    baseline_loss = get_baseline_loss()
    print(f"Baseline final loss: {baseline_loss:.4f}")
    print()

    results = []
    for n_exp, k_act, lbl in CONFIGS:
        print(f"Training {lbl} ...")
        r = train_config(n_exp, k_act, lbl, baseline_loss)
        results.append(r)
        print(f"  loss={r['final_loss']:.4f}  flop={r['flop']}  "
              f"eff={r['efficiency']:.6e}  ({r['time_s']:.1f}s)")

    # ─── Sort by efficiency for display ───────────────────────────────────────
    results_sorted = sorted(results, key=lambda x: x["efficiency"], reverse=True)

    # ─── Print markdown table ─────────────────────────────────────────────────
    print()
    print("## H-EN-2: MoE Energy Efficiency Results")
    print()
    print(f"Baseline loss (dense): {baseline_loss:.4f}")
    print()
    print("| Config | n | k | k/n | Final Loss | Active FLOP | Improvement | Efficiency (Δloss/FLOP) | Rank |")
    print("|--------|---|---|-----|-----------|-------------|-------------|------------------------|------|")
    for rank, r in enumerate(results_sorted, 1):
        star = " **[R=1]**" if abs(r["ratio"] - 1/3) < 0.01 else ""
        print(f"| {r['label']}{star} | {r['n']} | {r['k']} | {r['ratio']:.4f} | "
              f"{r['final_loss']:.4f} | {r['flop']} | {r['improvement']:+.4f} | "
              f"{r['efficiency']:.4e} | #{rank} |")

    print()

    # ─── Rank analysis ────────────────────────────────────────────────────────
    r1_results = [r for r in results if abs(r["ratio"] - 1/3) < 0.01]
    other_results = [r for r in results if abs(r["ratio"] - 1/3) >= 0.01]

    r1_eff_avg  = sum(r["efficiency"] for r in r1_results) / len(r1_results) if r1_results else 0
    oth_eff_avg = sum(r["efficiency"] for r in other_results) / len(other_results) if other_results else 0

    print("## Summary")
    print()
    print(f"R=1 configurations (k/n=1/3):  avg efficiency = {r1_eff_avg:.4e}")
    print(f"Other configurations:          avg efficiency = {oth_eff_avg:.4e}")
    ratio_str = f"{r1_eff_avg / oth_eff_avg:.3f}x" if oth_eff_avg != 0 else "N/A"
    print(f"R=1 / Other efficiency ratio:  {ratio_str}")
    print()

    # Rank of R=1 configs
    ranks_r1 = [i+1 for i, r in enumerate(results_sorted) if abs(r["ratio"] - 1/3) < 0.01]
    print(f"Ranks of R=1 configs in efficiency table: {ranks_r1}")
    print()

    # ─── ASCII efficiency bar chart ───────────────────────────────────────────
    print("## Efficiency Bar Chart (higher = better)")
    print()
    max_eff = max(r["efficiency"] for r in results) if results else 1
    bar_width = 40
    for r in results:
        bar_len = int((r["efficiency"] / max_eff) * bar_width) if max_eff > 0 else 0
        bar = "#" * bar_len
        marker = " <-- R=1" if abs(r["ratio"] - 1/3) < 0.01 else ""
        short_label = f"n={r['n']:2d} k={r['k']} ({r['ratio']:.2f})"
        print(f"  {short_label} | {bar:<{bar_width}} | {r['efficiency']:.3e}{marker}")

    print()

    # ─── Loss bar chart ───────────────────────────────────────────────────────
    print("## Final Loss Bar Chart (lower = better)")
    print()
    min_loss = min(r["final_loss"] for r in results)
    max_loss = max(r["final_loss"] for r in results)
    loss_range = max_loss - min_loss if max_loss != min_loss else 1
    for r in results:
        bar_len = int(((r["final_loss"] - min_loss) / loss_range) * bar_width)
        bar = "#" * bar_len
        marker = " <-- R=1" if abs(r["ratio"] - 1/3) < 0.01 else ""
        short_label = f"n={r['n']:2d} k={r['k']} ({r['ratio']:.2f})"
        print(f"  {short_label} | {bar:<{bar_width}} | {r['final_loss']:.4f}{marker}")

    print()

    # ─── Prediction verdict ───────────────────────────────────────────────────
    print("## H-EN-2 Prediction Verdict")
    print()
    print("Prediction: k/n = 1/3 (R=1) should be MOST energy-efficient.")
    print()
    top_rank = results_sorted[0]
    if abs(top_rank["ratio"] - 1/3) < 0.01:
        print("RESULT: CONFIRMED - R=1 configuration ranks #1 in efficiency.")
    else:
        best_r1_rank = min(ranks_r1) if ranks_r1 else None
        print(f"RESULT: NOT CONFIRMED - Top config is {top_rank['label']} (k/n={top_rank['ratio']:.4f}).")
        if best_r1_rank:
            print(f"        Best R=1 config ranks #{best_r1_rank} out of {len(results)}.")

    print()
    print(f"R=1 configs tested: {[r['label'] for r in r1_results]}")
    print(f"R=1 avg efficiency vs others: {ratio_str}")
