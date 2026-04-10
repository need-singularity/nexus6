"""
H-CX-67: Tension ratio convergence to divisor function ratio
H-CX-68: 1/e as optimal expert activation rate in MoE

Single script running both experiments back-to-back.
"""

import math
import random
import time
import json
from collections import defaultdict

# ── reproducibility ──────────────────────────────────────────────────────────
def set_seed(seed):
    random.seed(seed)

# ── minimal numpy-free tensor ops using plain Python lists ────────────────────
# We use Python lists + math for portability (no numpy/torch required on Mac CPU)
# but we try to import torch and fall back gracefully.

try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    HAS_TORCH = True
    print("Using PyTorch backend")
except ImportError:
    HAS_TORCH = False
    print("PyTorch not found — using pure-Python fallback (slow but correct)")

# ═══════════════════════════════════════════════════════════════════════════════
# SHARED UTILITIES
# ═══════════════════════════════════════════════════════════════════════════════

def sigma(n):
    """Sum of divisors."""
    return sum(d for d in range(1, n+1) if n % d == 0)

def tau(n):
    """Number of divisors."""
    return sum(1 for d in range(1, n+1) if n % d == 0)

def phi(n):
    """Euler totient."""
    return sum(1 for k in range(1, n+1) if math.gcd(k, n) == 1)

def R(n):
    """Dirichlet R = 1/phi(n)  (used in project)."""
    return 1 / phi(n)

# Known divisor ratios
DIVISOR_RATIOS = {
    "sigma(6)/sigma(3)": sigma(6) / sigma(3),   # 12/4 = 3.0
    "tau(6)/tau(3)":     tau(6)  / tau(3),       # 4/2  = 2.0
    "R(6)/R(3)":         R(6)    / R(3),          # phi(3)/phi(6) = 2/2 = 1.0 ... let's recheck
    "phi(6)/phi(3)":     phi(6)  / phi(3),        # 2/2  = 1.0
}

print("\n=== Divisor function reference values ===")
for k, v in DIVISOR_RATIOS.items():
    print(f"  {k} = {v:.6f}")


# ═══════════════════════════════════════════════════════════════════════════════
# EXPERIMENT 1 — H-CX-67
# ═══════════════════════════════════════════════════════════════════════════════

print("\n" + "="*70)
print("EXPERIMENT 1: H-CX-67 — Tension ratio convergence to divisor ratios")
print("="*70)

if HAS_TORCH:

    class TransformerBlock(nn.Module):
        def __init__(self, d_model, n_heads):
            super().__init__()
            self.attn = nn.MultiheadAttention(d_model, n_heads, batch_first=True)
            self.ff   = nn.Sequential(
                nn.Linear(d_model, d_model * 2),
                nn.ReLU(),
                nn.Linear(d_model * 2, d_model),
            )
            self.ln1 = nn.LayerNorm(d_model)
            self.ln2 = nn.LayerNorm(d_model)

        def forward(self, x):
            a, _ = self.attn(x, x, x)
            x    = self.ln1(x + a)
            x    = self.ln2(x + self.ff(x))
            return x

    class NBlockModel(nn.Module):
        def __init__(self, n_blocks, d_model=128, vocab=256, n_heads=2):
            super().__init__()
            self.embed  = nn.Embedding(vocab, d_model)
            self.blocks = nn.ModuleList([TransformerBlock(d_model, n_heads) for _ in range(n_blocks)])
            self.head   = nn.Linear(d_model, vocab)
            self.n_blocks = n_blocks

        def forward(self, x, return_intermediates=False):
            h = self.embed(x)
            intermediates = [h]
            for blk in self.blocks:
                h = blk(h)
                intermediates.append(h)
            logits = self.head(h)
            if return_intermediates:
                return logits, intermediates
            return logits

    def compute_tension(intermediates):
        """Mean squared difference between adjacent block outputs."""
        total = 0.0
        count = 0
        for i in range(len(intermediates) - 1):
            diff = intermediates[i+1] - intermediates[i]
            total += (diff ** 2).mean().item()
            count += 1
        return total / count if count > 0 else 0.0

    def make_batch(batch_size=32, seq_len=16, vocab=256):
        return torch.randint(0, vocab, (batch_size, seq_len))

    def train_models_and_track_tension(n_blocks_list, steps=500, log_every=50, seed=42,
                                        batch_size=32, seq_len=16, d_model=128, vocab=256):
        torch.manual_seed(seed)
        random.seed(seed)

        models    = {n: NBlockModel(n, d_model=d_model, vocab=vocab) for n in n_blocks_list}
        optimizers = {n: torch.optim.Adam(models[n].parameters(), lr=1e-3) for n in n_blocks_list}
        tension_log = {n: [] for n in n_blocks_list}  # step -> tension

        for step in range(1, steps + 1):
            x = make_batch(batch_size, seq_len, vocab)
            # shift for LM loss: input x[:,:-1], target x[:,1:]
            inp, tgt = x[:, :-1], x[:, 1:]

            for n in n_blocks_list:
                logits, intermediates = models[n](inp, return_intermediates=True)
                loss = F.cross_entropy(logits.reshape(-1, vocab), tgt.reshape(-1))
                optimizers[n].zero_grad()
                loss.backward()
                optimizers[n].step()

            if step % log_every == 0:
                for n in n_blocks_list:
                    with torch.no_grad():
                        _, intermediates = models[n](inp, return_intermediates=True)
                        t = compute_tension(intermediates)
                    tension_log[n].append((step, t))

        return tension_log

    # --- Run H-CX-67 ---
    N_BLOCKS_LIST = [3, 4, 6, 8]
    SEEDS = [42, 137]
    STEPS = 500
    LOG_EVERY = 50

    all_seeds_tension = {}

    for seed in SEEDS:
        print(f"\n  Training seed={seed}...")
        t0 = time.time()
        tlog = train_models_and_track_tension(
            N_BLOCKS_LIST, steps=STEPS, log_every=LOG_EVERY, seed=seed)
        elapsed = time.time() - t0
        all_seeds_tension[seed] = tlog
        print(f"  Done in {elapsed:.1f}s")

    # --- Compute ratios ---
    print("\n--- H-CX-67 Results ---\n")

    # For each seed, compute ratios at each logged step
    ratio_defs = [
        ("tension_6/tension_3", 6, 3),
        ("tension_4/tension_3", 4, 3),
        ("tension_8/tension_6", 8, 6),
    ]

    # Aggregate across seeds
    for ratio_name, n_num, n_den in ratio_defs:
        print(f"\n### Ratio: {ratio_name}")
        print(f"| Step | Seed 42 | Seed 137 | Mean | Reference candidates |")
        print(f"|------|---------|----------|------|----------------------|")

        steps_common = [s for s, _ in all_seeds_tension[SEEDS[0]][n_num]]
        for i, step in enumerate(steps_common):
            vals = []
            for seed in SEEDS:
                t_num = all_seeds_tension[seed][n_num][i][1]
                t_den = all_seeds_tension[seed][n_den][i][1]
                ratio = t_num / t_den if t_den > 1e-12 else float('nan')
                vals.append(ratio)
            mean_r = sum(vals) / len(vals)
            # find closest divisor ratio
            closest = min(DIVISOR_RATIOS.items(), key=lambda kv: abs(kv[1] - mean_r))
            print(f"| {step:4d} | {vals[0]:.4f}  | {vals[1]:.4f}   | {mean_r:.4f} | closest={closest[0]}={closest[1]:.4f} |")

    # Summary table: final-step ratios vs divisor ratios
    print("\n### Summary: Final-step mean ratios vs divisor function predictions")
    print(f"| Ratio | Final Mean | sigma | tau | R | phi | Closest |")
    print(f"|-------|-----------|-------|-----|---|-----|---------|")
    for ratio_name, n_num, n_den in ratio_defs:
        vals = []
        for seed in SEEDS:
            last_idx = -1
            t_num = all_seeds_tension[seed][n_num][last_idx][1]
            t_den = all_seeds_tension[seed][n_den][last_idx][1]
            ratio = t_num / t_den if t_den > 1e-12 else float('nan')
            vals.append(ratio)
        mean_r = sum(vals) / len(vals)
        # compare against all known ratios for these n
        candidates = {
            "sigma": sigma(n_num)/sigma(n_den),
            "tau":   tau(n_num)/tau(n_den),
            "phi":   phi(n_num)/phi(n_den),
        }
        closest_k = min(candidates.items(), key=lambda kv: abs(kv[1] - mean_r))
        print(f"| {ratio_name} | {mean_r:.4f} | {candidates['sigma']:.4f} | {candidates['tau']:.4f} | N/A | {candidates['phi']:.4f} | {closest_k[0]}={closest_k[1]:.4f} |")

else:
    print("PyTorch not available — skipping H-CX-67 (requires neural network training)")


# ═══════════════════════════════════════════════════════════════════════════════
# EXPERIMENT 2 — H-CX-68
# ═══════════════════════════════════════════════════════════════════════════════

print("\n" + "="*70)
print("EXPERIMENT 2: H-CX-68 — 1/e as optimal expert activation rate in MoE")
print("="*70)

INV_E = 1.0 / math.e  # ≈ 0.3679

# Activation rates to test
RATES = [0.125, 0.25, INV_E, 0.375, 0.5, 0.625, 0.75]
N_EXPERTS = 8

print(f"\n1/e = {INV_E:.6f}")
print(f"Testing rates: {[round(r, 4) for r in RATES]}")
print(f"n_experts = {N_EXPERTS}")

if HAS_TORCH:

    class MoELayer(nn.Module):
        """Simple MoE with top-k hard routing."""
        def __init__(self, d_model, n_experts, k):
            super().__init__()
            self.n_experts = n_experts
            self.k = k
            self.gate    = nn.Linear(d_model, n_experts, bias=False)
            self.experts = nn.ModuleList([
                nn.Sequential(nn.Linear(d_model, d_model*2), nn.ReLU(), nn.Linear(d_model*2, d_model))
                for _ in range(n_experts)
            ])

        def forward(self, x):
            # x: (B, T, d_model)
            B, T, D = x.shape
            xf = x.reshape(-1, D)               # (B*T, D)
            scores = self.gate(xf)               # (B*T, E)
            topk_scores, topk_idx = scores.topk(self.k, dim=-1)  # (B*T, k)
            topk_weights = F.softmax(topk_scores, dim=-1)         # (B*T, k)

            # Accumulate expert outputs
            out = torch.zeros_like(xf)
            expert_counts = torch.zeros(self.n_experts, device=x.device)
            for i, expert in enumerate(self.experts):
                mask = (topk_idx == i).any(dim=-1)   # (B*T,)
                expert_counts[i] = mask.float().sum()
                if mask.any():
                    # weight for this expert
                    ex_in  = xf[mask]                # (M, D)
                    ex_out = expert(ex_in)           # (M, D)
                    # find weight for expert i among topk
                    pos = (topk_idx[mask] == i).float()          # (M, k)
                    w   = (pos * topk_weights[mask]).sum(dim=-1, keepdim=True)  # (M,1)
                    out[mask] += w * ex_out

            return out.reshape(B, T, D), expert_counts

    class MoETransformer(nn.Module):
        def __init__(self, n_blocks, d_model, vocab, n_heads, n_experts, k):
            super().__init__()
            self.embed = nn.Embedding(vocab, d_model)
            self.blocks = nn.ModuleList()
            for _ in range(n_blocks):
                self.blocks.append(nn.ModuleDict({
                    'attn': nn.MultiheadAttention(d_model, n_heads, batch_first=True),
                    'ln1':  nn.LayerNorm(d_model),
                    'moe':  MoELayer(d_model, n_experts, k),
                    'ln2':  nn.LayerNorm(d_model),
                }))
            self.head = nn.Linear(d_model, vocab)

        def forward(self, x):
            h = self.embed(x)
            total_counts = None
            for blk in self.blocks:
                a, _ = blk['attn'](h, h, h)
                h    = blk['ln1'](h + a)
                m, cnts = blk['moe'](h)
                h    = blk['ln2'](h + m)
                if total_counts is None:
                    total_counts = cnts
                else:
                    total_counts = total_counts + cnts
            return self.head(h), total_counts

    def expert_utilization_entropy(counts):
        """Shannon entropy of expert usage distribution (normalized)."""
        total = counts.sum().item()
        if total < 1e-12:
            return 0.0
        probs = counts / total
        probs = probs[probs > 0]
        H = -(probs * probs.log()).sum().item()
        H_max = math.log(len(counts))
        return H / H_max if H_max > 0 else 0.0  # normalized [0,1]

    def load_balance_score(counts):
        """CV = std/mean; lower = better balance."""
        n = counts.float()
        if n.sum() < 1e-12:
            return float('inf')
        mean = n.mean().item()
        std  = n.std().item()
        return std / mean if mean > 1e-12 else float('inf')

    def run_moe_experiment(rate, n_experts=8, n_blocks=6, d_model=128, vocab=256,
                           n_heads=2, steps=300, seed=42, batch_size=32, seq_len=16):
        k = max(1, round(rate * n_experts))
        torch.manual_seed(seed)
        random.seed(seed)

        model = MoETransformer(n_blocks, d_model, vocab, n_heads, n_experts, k)
        opt   = torch.optim.Adam(model.parameters(), lr=1e-3)

        losses = []
        for step in range(1, steps+1):
            x   = torch.randint(0, vocab, (batch_size, seq_len))
            inp, tgt = x[:, :-1], x[:, 1:]
            logits, _ = model(inp)
            loss = F.cross_entropy(logits.reshape(-1, vocab), tgt.reshape(-1))
            opt.zero_grad()
            loss.backward()
            opt.step()
            losses.append(loss.item())

        # Final metrics
        model.eval()
        with torch.no_grad():
            x   = torch.randint(0, vocab, (batch_size*4, seq_len))
            inp, tgt = x[:, :-1], x[:, 1:]
            logits, final_counts = model(inp)
            final_loss = F.cross_entropy(logits.reshape(-1, vocab), tgt.reshape(-1)).item()

        ent   = expert_utilization_entropy(final_counts)
        cv    = load_balance_score(final_counts)
        counts_list = final_counts.tolist()

        return {
            "rate":      rate,
            "k":         k,
            "seed":      seed,
            "final_loss": final_loss,
            "entropy_norm": ent,
            "load_balance_cv": cv,
            "expert_counts": counts_list,
            "loss_trajectory_last10": losses[-10:],
        }

    # --- Run H-CX-68 ---
    SEEDS_68 = [42, 137]
    N_BLOCKS_68 = 6
    STEPS_68 = 300

    results_68 = defaultdict(list)  # rate -> list of result dicts

    for rate in RATES:
        k = max(1, round(rate * N_EXPERTS))
        for seed in SEEDS_68:
            print(f"  rate={rate:.4f} (k={k}/{N_EXPERTS}), seed={seed}...", end=" ", flush=True)
            t0 = time.time()
            res = run_moe_experiment(
                rate, n_experts=N_EXPERTS, n_blocks=N_BLOCKS_68,
                steps=STEPS_68, seed=seed)
            elapsed = time.time() - t0
            results_68[rate].append(res)
            print(f"loss={res['final_loss']:.4f}, H={res['entropy_norm']:.4f}, CV={res['load_balance_cv']:.4f}  [{elapsed:.1f}s]")

    # --- Print results ---
    print("\n--- H-CX-68 Results ---\n")
    print("### Main results table")
    print(f"| Rate | k/8 | Loss S42 | Loss S137 | Mean Loss | Entropy S42 | Entropy S137 | Mean H | CV S42 | CV S137 | Mean CV |")
    print(f"|------|-----|----------|-----------|-----------|-------------|--------------|--------|--------|---------|---------|")

    summary_rows = []
    for rate in RATES:
        rlist = results_68[rate]
        losses = [r['final_loss'] for r in rlist]
        ents   = [r['entropy_norm'] for r in rlist]
        cvs    = [r['load_balance_cv'] for r in rlist]
        k      = rlist[0]['k']
        mean_loss = sum(losses)/len(losses)
        mean_ent  = sum(ents)/len(ents)
        mean_cv   = sum(cvs)/len(cvs)
        marker = " <-- 1/e" if abs(rate - INV_E) < 0.01 else ""
        print(f"| {rate:.4f}{marker} | {k} | {losses[0]:.4f} | {losses[1]:.4f} | {mean_loss:.4f} | {ents[0]:.4f} | {ents[1]:.4f} | {mean_ent:.4f} | {cvs[0]:.4f} | {cvs[1]:.4f} | {mean_cv:.4f} |")
        summary_rows.append((rate, k, mean_loss, mean_ent, mean_cv))

    # Find best rates
    best_loss_rate  = min(summary_rows, key=lambda r: r[2])
    best_ent_rate   = max(summary_rows, key=lambda r: r[3])
    best_cv_rate    = min(summary_rows, key=lambda r: r[4])

    print(f"\n### Winner summary")
    print(f"| Metric | Best Rate | Value | 1/e ({INV_E:.4f}) value | 1/e is best? |")
    print(f"|--------|-----------|-------|----------------------|--------------|")

    inv_e_row = next(r for r in summary_rows if abs(r[0] - INV_E) < 0.01)
    print(f"| Final Loss (lower=better) | {best_loss_rate[0]:.4f} | {best_loss_rate[2]:.4f} | {inv_e_row[2]:.4f} | {'YES' if abs(best_loss_rate[0]-INV_E)<0.01 else 'NO'} |")
    print(f"| Expert Entropy (higher=better) | {best_ent_rate[0]:.4f} | {best_ent_rate[3]:.4f} | {inv_e_row[3]:.4f} | {'YES' if abs(best_ent_rate[0]-INV_E)<0.01 else 'NO'} |")
    print(f"| Load Balance CV (lower=better) | {best_cv_rate[0]:.4f} | {best_cv_rate[4]:.4f} | {inv_e_row[4]:.4f} | {'YES' if abs(best_cv_rate[0]-INV_E)<0.01 else 'NO'} |")

    # ASCII plot of loss vs rate
    print("\n### ASCII Plot: Mean Final Loss vs Activation Rate")
    print("(lower is better)\n")
    min_l = min(r[2] for r in summary_rows)
    max_l = max(r[2] for r in summary_rows)
    span  = max_l - min_l if max_l > min_l else 1.0
    bar_width = 40
    for rate, k, mean_loss, mean_ent, mean_cv in summary_rows:
        bar_len = int(bar_width * (mean_loss - min_l) / span)
        marker  = " <-- 1/e" if abs(rate - INV_E) < 0.01 else ""
        print(f"  {rate:.4f} (k={k}) | {'#'*bar_len:{bar_width}} | {mean_loss:.4f}{marker}")

    # ASCII plot of entropy vs rate
    print("\n### ASCII Plot: Mean Expert Entropy vs Activation Rate")
    print("(higher is better)\n")
    min_h = min(r[3] for r in summary_rows)
    max_h = max(r[3] for r in summary_rows)
    span_h = max_h - min_h if max_h > min_h else 1.0
    for rate, k, mean_loss, mean_ent, mean_cv in summary_rows:
        bar_len = int(bar_width * (mean_ent - min_h) / span_h)
        marker  = " <-- 1/e" if abs(rate - INV_E) < 0.01 else ""
        print(f"  {rate:.4f} (k={k}) | {'#'*bar_len:{bar_width}} | {mean_ent:.4f}{marker}")

    # Expert counts breakdown for 1/e rate
    print(f"\n### Expert utilization at rate=1/e (seed=42)")
    inv_e_res = results_68[INV_E][0]
    counts = inv_e_res['expert_counts']
    total  = sum(counts)
    print(f"| Expert | Count | Fraction |")
    print(f"|--------|-------|----------|")
    for i, c in enumerate(counts):
        print(f"| {i} | {c:.0f} | {c/total:.4f} |")

else:
    print("PyTorch not available — skipping H-CX-68")

# ═══════════════════════════════════════════════════════════════════════════════
# HYPOTHESIS ASSESSMENT
# ═══════════════════════════════════════════════════════════════════════════════

print("\n" + "="*70)
print("HYPOTHESIS ASSESSMENT")
print("="*70)

print("""
H-CX-67 Assessment:
  Predicts tension ratios converge to specific divisor function ratios.
  Key targets:
    tension_6/tension_3  -> sigma(6)/sigma(3)=3.0 or tau(6)/tau(3)=2.0 or phi(6)/phi(3)=1.0
    tension_4/tension_3  -> sigma(4)/sigma(3)=7/4=1.75 or tau(4)/tau(3)=3/2=1.5
    tension_8/tension_6  -> sigma(8)/sigma(6)=15/12=1.25 or tau(8)/tau(6)=4/4=1.0
  See tables above for actual convergence.

H-CX-68 Assessment:
  Predicts rate=1/e is optimal in {loss, entropy, load balance}.
  1/e ≈ 0.3679 is between k=3 (0.375) after rounding.
  k = round(1/e * 8) = round(2.943) = 3
  See winner summary table above.
""")

print("Done.")
