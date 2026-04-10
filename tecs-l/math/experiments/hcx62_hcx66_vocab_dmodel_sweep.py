"""
H-CX-62: vocab=sigma_3(6)=252 vs vocab=256 sweep
H-CX-66: d_model=252 modular form symmetry sweep

Both experiments in one script.
sigma_3(6) = 1^3 + 2^3 + 3^3 + 6^3 = 1 + 8 + 27 + 216 = 252
C(10,5) = 252 (confirmed)
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import math
import time
from collections import defaultdict

# ── Device ──────────────────────────────────────────────────────────────────
if torch.backends.mps.is_available():
    device = torch.device("mps")
    print("Device: MPS (Apple Silicon)")
elif torch.cuda.is_available():
    device = torch.device("cuda")
    print("Device: CUDA")
else:
    device = torch.device("cpu")
    print("Device: CPU")

# ── Verify sigma_3(6) ────────────────────────────────────────────────────────
sigma_3_6 = 1**3 + 2**3 + 3**3 + 6**3
c_10_5 = math.comb(10, 5)
print(f"\nsigma_3(6) = 1^3+2^3+3^3+6^3 = {sigma_3_6}")
print(f"C(10,5) = {c_10_5}")
assert sigma_3_6 == 252 and c_10_5 == 252, "sanity check failed"
print("Both equal 252. Confirmed.\n")

# ── Tiny GPT-style transformer ───────────────────────────────────────────────
class TinyTransformer(nn.Module):
    def __init__(self, vocab_size, d_model, n_heads, n_layers=6, seq_len=64, dropout=0.1):
        super().__init__()
        assert d_model % n_heads == 0, f"d_model={d_model} not divisible by n_heads={n_heads}"
        self.embed = nn.Embedding(vocab_size, d_model)
        self.pos   = nn.Embedding(seq_len, d_model)
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model, nhead=n_heads, dim_feedforward=d_model*4,
            dropout=dropout, batch_first=True, norm_first=True
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=n_layers)
        self.head = nn.Linear(d_model, vocab_size, bias=False)
        self.seq_len = seq_len
        self.d_model = d_model
        self._init_weights()

    def _init_weights(self):
        for p in self.parameters():
            if p.dim() > 1:
                nn.init.xavier_uniform_(p)

    def forward(self, x):
        B, T = x.shape
        pos = torch.arange(T, device=x.device).unsqueeze(0)
        h = self.embed(x) + self.pos(pos)
        # causal mask
        mask = nn.Transformer.generate_square_subsequent_mask(T, device=x.device)
        h = self.transformer(h, mask=mask, is_causal=True)
        return self.head(h)


def make_batch(vocab_size, batch_size=32, seq_len=64, device=device):
    """Random token batch for speed."""
    return torch.randint(0, vocab_size, (batch_size, seq_len + 1), device=device)


def train_model(vocab_size, d_model, n_heads, n_steps=300, seed=42, batch_size=32, seq_len=64):
    torch.manual_seed(seed)
    model = TinyTransformer(vocab_size, d_model, n_heads, seq_len=seq_len).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=3e-4, weight_decay=0.01)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=n_steps)

    model.train()
    losses = []
    for step in range(n_steps):
        tokens = make_batch(vocab_size, batch_size, seq_len, device)
        x, y = tokens[:, :-1], tokens[:, 1:]
        logits = model(x)
        loss = F.cross_entropy(logits.reshape(-1, vocab_size), y.reshape(-1))
        optimizer.zero_grad()
        loss.backward()
        nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()
        scheduler.step()
        losses.append(loss.item())

    final_loss = np.mean(losses[-20:])  # avg last 20 steps
    return final_loss, model, losses


def get_spectral_stats(model):
    """Compute singular value stats across all weight matrices."""
    all_sv = []
    for name, p in model.named_parameters():
        if p.dim() == 2 and p.shape[0] >= 4 and p.shape[1] >= 4:
            with torch.no_grad():
                sv = torch.linalg.svdvals(p.float().cpu()).numpy()
            all_sv.append(sv)

    if not all_sv:
        return {}

    # Spectral gap = ratio of largest to second-largest SV (per layer avg)
    gaps = []
    for sv in all_sv:
        if len(sv) >= 2:
            gaps.append(sv[0] / sv[1] if sv[1] > 1e-8 else float('inf'))

    all_sv_flat = np.concatenate(all_sv)
    return {
        "sv_mean": float(np.mean(all_sv_flat)),
        "sv_std":  float(np.std(all_sv_flat)),
        "sv_max":  float(np.max(all_sv_flat)),
        "sv_min":  float(np.min(all_sv_flat[all_sv_flat > 1e-8])),
        "spectral_gap_mean": float(np.mean(gaps)),
        "spectral_gap_std":  float(np.std(gaps)),
        "n_matrices": len(all_sv),
    }


# ════════════════════════════════════════════════════════════════════════════
# EXPERIMENT 1: H-CX-62 — vocab sweep around 252 and 256
# ════════════════════════════════════════════════════════════════════════════
print("=" * 70)
print("EXPERIMENT 1: H-CX-62 — vocab_size sweep")
print("Hypothesis: vocab=252=sigma_3(6) outperforms vocab=256")
print("=" * 70)
print()

VOCAB_SWEEP    = [248, 250, 252, 254, 256, 258, 260]
D_MODEL_EXP1   = 128
N_HEADS_EXP1   = 2
N_STEPS        = 300
SEEDS          = [42, 137]

exp1_results = defaultdict(list)

for vocab in VOCAB_SWEEP:
    for seed in SEEDS:
        t0 = time.time()
        loss, _, _ = train_model(
            vocab_size=vocab, d_model=D_MODEL_EXP1,
            n_heads=N_HEADS_EXP1, n_steps=N_STEPS, seed=seed
        )
        elapsed = time.time() - t0
        exp1_results[vocab].append(loss)
        print(f"  vocab={vocab:3d} seed={seed} → loss={loss:.4f}  ({elapsed:.1f}s)")

print()
print("## Experiment 1 Results: vocab sweep (mean over 2 seeds)")
print()
print(f"| vocab | loss_seed42 | loss_seed137 | mean_loss | delta_vs_256 |")
print(f"|-------|------------|--------------|-----------|--------------|")

mean_256 = np.mean(exp1_results[256])
for vocab in VOCAB_SWEEP:
    losses = exp1_results[vocab]
    mean_l = np.mean(losses)
    delta  = mean_l - mean_256
    marker = " <-- 252=sigma_3(6)" if vocab == 252 else (" <-- 256=2^8" if vocab == 256 else "")
    print(f"| {vocab:5d} | {losses[0]:.4f}      | {losses[1]:.4f}       | {mean_l:.4f}    | {delta:+.4f}      |{marker}")

# Rank
ranked = sorted(VOCAB_SWEEP, key=lambda v: np.mean(exp1_results[v]))
print()
print(f"Ranking (best to worst loss): {ranked}")
rank_252 = ranked.index(252) + 1
rank_256 = ranked.index(256) + 1
print(f"  vocab=252 rank: {rank_252}/7")
print(f"  vocab=256 rank: {rank_256}/7")
print()
diff_252_vs_256 = np.mean(exp1_results[252]) - np.mean(exp1_results[256])
print(f"252 - 256 loss difference: {diff_252_vs_256:+.4f}")
if diff_252_vs_256 < -0.001:
    print("RESULT: vocab=252 LOWER loss (better) than vocab=256 → supports H-CX-62")
elif diff_252_vs_256 > 0.001:
    print("RESULT: vocab=252 HIGHER loss (worse) than vocab=256 → contradicts H-CX-62")
else:
    print("RESULT: No meaningful difference between vocab=252 and vocab=256")


# ════════════════════════════════════════════════════════════════════════════
# EXPERIMENT 2: H-CX-66 — d_model sweep around 252
# ════════════════════════════════════════════════════════════════════════════
print()
print("=" * 70)
print("EXPERIMENT 2: H-CX-66 — d_model sweep")
print("Hypothesis: d_model=252=sigma_3(6) has special weight structure")
print("=" * 70)
print()

# d_model must be divisible by n_heads.
# 240: divisible by 2,4,6,8 — use 4 heads
# 248: divisible by 2,4,8    — use 4 heads
# 252: divisible by 2,4,6    — use 4 heads (252/4=63)
# 256: divisible by 2,4,8    — use 4 heads
# 264: divisible by 2,4,8    — use 4 heads
DMODEL_SWEEP = [240, 248, 252, 256, 264]
N_HEADS_MAP  = {240: 4, 248: 4, 252: 4, 256: 4, 264: 4}
VOCAB_EXP2   = 256

# Verify divisibility
for dm in DMODEL_SWEEP:
    nh = N_HEADS_MAP[dm]
    assert dm % nh == 0, f"d_model={dm} not divisible by n_heads={nh}"
    print(f"  d_model={dm}, n_heads={nh}, head_dim={dm//nh}")

print()

exp2_results = {}  # d_model -> {seed: {loss, spectral_stats}}

for dm in DMODEL_SWEEP:
    nh = N_HEADS_MAP[dm]
    exp2_results[dm] = {}
    for seed in SEEDS:
        t0 = time.time()
        loss, model, _ = train_model(
            vocab_size=VOCAB_EXP2, d_model=dm,
            n_heads=nh, n_steps=N_STEPS, seed=seed
        )
        sv_stats = get_spectral_stats(model)
        elapsed = time.time() - t0
        exp2_results[dm][seed] = {"loss": loss, "sv": sv_stats}
        print(f"  d_model={dm:3d} seed={seed} → loss={loss:.4f}  "
              f"sv_mean={sv_stats.get('sv_mean',float('nan')):.4f}  "
              f"spec_gap={sv_stats.get('spectral_gap_mean',float('nan')):.4f}  "
              f"({elapsed:.1f}s)")

print()
print("## Experiment 2 Results: d_model sweep (mean over 2 seeds)")
print()
print(f"| d_model | loss_s42 | loss_s137 | mean_loss | sv_mean | sv_std | spec_gap | delta_loss_vs256 |")
print(f"|---------|---------|----------|-----------|---------|--------|----------|-----------------|")

mean_loss_256 = np.mean([exp2_results[256][s]["loss"] for s in SEEDS])
for dm in DMODEL_SWEEP:
    losses  = [exp2_results[dm][s]["loss"] for s in SEEDS]
    sv_vals = [exp2_results[dm][s]["sv"]   for s in SEEDS]
    mean_l  = np.mean(losses)
    delta   = mean_l - mean_loss_256
    mean_sv  = np.mean([v.get("sv_mean", float("nan")) for v in sv_vals])
    mean_svs = np.mean([v.get("sv_std",  float("nan")) for v in sv_vals])
    mean_gap = np.mean([v.get("spectral_gap_mean", float("nan")) for v in sv_vals])
    marker = " <-- 252=sigma_3(6)" if dm == 252 else (" <-- 256=2^8" if dm == 256 else "")
    print(f"| {dm:7d} | {losses[0]:.4f}   | {losses[1]:.4f}    | {mean_l:.4f}    | {mean_sv:.4f}  | {mean_svs:.4f} | {mean_gap:.4f}   | {delta:+.6f}       |{marker}")

print()
# Spectral gap comparison 252 vs 256
gap_252 = np.mean([exp2_results[252][s]["sv"]["spectral_gap_mean"] for s in SEEDS])
gap_256 = np.mean([exp2_results[256][s]["sv"]["spectral_gap_mean"] for s in SEEDS])
loss_252_e2 = np.mean([exp2_results[252][s]["loss"] for s in SEEDS])
loss_256_e2 = mean_loss_256

print(f"Spectral gap 252: {gap_252:.4f}")
print(f"Spectral gap 256: {gap_256:.4f}")
print(f"Spectral gap 252 - 256: {gap_252 - gap_256:+.4f}")
print()
print(f"Loss 252: {loss_252_e2:.4f}")
print(f"Loss 256: {loss_256_e2:.4f}")
print(f"Loss 252 - 256: {loss_252_e2 - loss_256_e2:+.4f}")
print()

# Rank by loss
ranked_dm = sorted(DMODEL_SWEEP, key=lambda d: np.mean([exp2_results[d][s]["loss"] for s in SEEDS]))
print(f"d_model ranking by loss (best first): {ranked_dm}")
r252 = ranked_dm.index(252) + 1
r256 = ranked_dm.index(256) + 1
print(f"  d_model=252 loss rank: {r252}/5")
print(f"  d_model=256 loss rank: {r256}/5")

# Rank by spectral gap
ranked_dm_gap = sorted(DMODEL_SWEEP, key=lambda d: -np.mean([exp2_results[d][s]["sv"]["spectral_gap_mean"] for s in SEEDS]))
print(f"d_model ranking by spectral gap (largest first): {ranked_dm_gap}")
r252g = ranked_dm_gap.index(252) + 1
r256g = ranked_dm_gap.index(256) + 1
print(f"  d_model=252 spectral gap rank: {r252g}/5")
print(f"  d_model=256 spectral gap rank: {r256g}/5")

print()
print("=" * 70)
print("SUMMARY")
print("=" * 70)
print()
print("H-CX-62 (vocab sweep):")
print(f"  252 vs 256 mean loss: {diff_252_vs_256:+.4f}")
if diff_252_vs_256 < -0.005:
    verdict62 = "SUPPORTED (meaningful improvement)"
elif diff_252_vs_256 > 0.005:
    verdict62 = "REFUTED (meaningful degradation)"
else:
    verdict62 = "INCONCLUSIVE (difference < 0.005)"
print(f"  Verdict: {verdict62}")
print()
print("H-CX-66 (d_model sweep):")
diff_loss_66 = loss_252_e2 - loss_256_e2
diff_gap_66  = gap_252 - gap_256
print(f"  252 vs 256 mean loss: {diff_loss_66:+.4f}")
print(f"  252 vs 256 spectral gap: {diff_gap_66:+.4f}")
if diff_gap_66 > 0.01:
    verdict66_gap = "SUPPORTED — larger spectral gap in d_model=252"
elif diff_gap_66 < -0.01:
    verdict66_gap = "REFUTED — smaller spectral gap in d_model=252"
else:
    verdict66_gap = "INCONCLUSIVE — spectral gap difference < 0.01"
print(f"  Verdict: {verdict66_gap}")

print()
print("Done.")
