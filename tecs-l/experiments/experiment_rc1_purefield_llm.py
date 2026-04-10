I'll translate all Korean text to English in this Python file.

```python
#!/usr/bin/env python3
"""RC-1: PureField Language Model — Replace FFN with repulsion field

Hypothesis 335 verification: Replace Transformer FFN with PureField(engine_a, engine_g -> repulsion)
to achieve equal or better PPL, and tension correlates with per-token accuracy.

Architecture:
  Standard:  Attention -> LayerNorm -> FFN -> LayerNorm -> output
  PureField: Attention -> LayerNorm -> PureField -> LayerNorm -> output
  PureField: output = tension_scale * sqrt(|A-G|^2) * normalize(A-G)
             (no equilibrium, no residual FFN -- field only)

Data: Shakespeare (character-level, auto-download from TinyShakespeare)
Measurement: PPL, per-token tension, training loss curve, tension-correctness correlation

GPU required: single GPU ~10 min target
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader
import numpy as np
import math
import time
import os
import json
import urllib.request


# ═══════════════════════════════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════════════════════════════
CONFIG = {
    # Data
    "data_url": "https://raw.githubusercontent.com/karpathy/char-rnn/master/data/tinyshakespeare/input.txt",
    "data_path": "/tmp/tinyshakespeare.txt",
    "seq_len": 128,
    "train_ratio": 0.9,

    # Model
    "d_model": 128,
    "n_heads": 4,
    "n_layers": 2,
    "dropout": 0.1,
    "ffn_mult": 4,  # FFN hidden = d_model * ffn_mult (standard only)

    # Training
    "batch_size": 64,
    "lr": 3e-4,
    "epochs": 20,
    "warmup_steps": 200,
    "log_interval": 50,
    "eval_interval": 1,  # every N epochs
    "grad_clip": 1.0,

    # PureField specific
    "tension_init": 1.0,          # initial tension_scale
    "aux_entropy_lambda": 0.01,   # entropy regularization weight
}


# ═══════════════════════════════════════════════════════════════
# DATA: Character-level Shakespeare
# ═══════════════════════════════════════════════════════════════
class CharDataset(Dataset):
    """Character-level dataset from a text file."""

    def __init__(self, text, char2idx, seq_len):
        self.data = torch.tensor([char2idx[c] for c in text], dtype=torch.long)
        self.seq_len = seq_len

    def __len__(self):
        return max(0, len(self.data) - self.seq_len - 1)

    def __getitem__(self, idx):
        x = self.data[idx : idx + self.seq_len]
        y = self.data[idx + 1 : idx + self.seq_len + 1]
        return x, y


def load_shakespeare(cfg):
    """Download TinyShakespeare and return train/val dataloaders + vocab."""
    path = cfg["data_path"]
    if not os.path.exists(path):
        print(f"  Downloading TinyShakespeare to {path}...")
        urllib.request.urlretrieve(cfg["data_url"], path)

    with open(path, "r") as f:
        text = f.read()

    chars = sorted(set(text))
    vocab_size = len(chars)
    char2idx = {c: i for i, c in enumerate(chars)}
    idx2char = {i: c for c, i in char2idx.items()}

    split = int(len(text) * cfg["train_ratio"])
    train_text = text[:split]
    val_text = text[split:]

    train_ds = CharDataset(train_text, char2idx, cfg["seq_len"])
    val_ds = CharDataset(val_text, char2idx, cfg["seq_len"])

    train_loader = DataLoader(train_ds, batch_size=cfg["batch_size"],
                              shuffle=True, drop_last=True, num_workers=0)
    val_loader = DataLoader(val_ds, batch_size=cfg["batch_size"],
                            shuffle=False, drop_last=False, num_workers=0)

    print(f"  Text length: {len(text):,} chars")
    print(f"  Vocab size:  {vocab_size}")
    print(f"  Train seqs:  {len(train_ds):,}")
    print(f"  Val seqs:    {len(val_ds):,}")

    return train_loader, val_loader, vocab_size, char2idx, idx2char


# ═══════════════════════════════════════════════════════════════
# MODEL COMPONENTS
# ═══════════════════════════════════════════════════════════════

class MultiHeadAttention(nn.Module):
    """Standard multi-head self-attention with causal mask."""

    def __init__(self, d_model, n_heads, dropout=0.1, max_len=512):
        super().__init__()
        assert d_model % n_heads == 0
        self.d_model = d_model
        self.n_heads = n_heads
        self.d_k = d_model // n_heads

        self.qkv = nn.Linear(d_model, 3 * d_model)
        self.out_proj = nn.Linear(d_model, d_model)
        self.dropout = nn.Dropout(dropout)

        # Causal mask (upper triangular)
        mask = torch.triu(torch.ones(max_len, max_len), diagonal=1).bool()
        self.register_buffer("causal_mask", mask)

    def forward(self, x):
        B, T, C = x.shape
        qkv = self.qkv(x).reshape(B, T, 3, self.n_heads, self.d_k)
        qkv = qkv.permute(2, 0, 3, 1, 4)  # (3, B, H, T, D)
        q, k, v = qkv[0], qkv[1], qkv[2]

        attn = (q @ k.transpose(-2, -1)) / math.sqrt(self.d_k)
        attn = attn.masked_fill(self.causal_mask[:T, :T].unsqueeze(0).unsqueeze(0), float('-inf'))
        attn = F.softmax(attn, dim=-1)
        attn = self.dropout(attn)

        out = (attn @ v).transpose(1, 2).reshape(B, T, C)
        return self.out_proj(out)


class StandardFFN(nn.Module):
    """Standard Transformer FFN: Linear -> GELU -> Linear."""

    def __init__(self, d_model, ffn_mult=4, dropout=0.1):
        super().__init__()
        d_ff = d_model * ffn_mult
        self.net = nn.Sequential(
            nn.Linear(d_model, d_ff),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(d_ff, d_model),
            nn.Dropout(dropout),
        )

    def forward(self, x):
        return self.net(x), torch.tensor(0.0, device=x.device)  # no tension


# ═══════════════════════════════════════════════════════════════
# PUREFIELD: The core replacement for FFN
# ═══════════════════════════════════════════════════════════════

class PureFieldBlock(nn.Module):
    """PureField FFN replacement.

    Two engines (A and G) produce competing representations.
    Output = tension_scale * sqrt(tension) * normalize(A - G)

    No equilibrium term -- the output lives entirely in the
    repulsion field between the two engines.

    Key insight from H334: this is sufficient for classification.
    H335 tests whether it works for next-token prediction too.
    """

    def __init__(self, d_model, dropout=0.1):
        super().__init__()
        # Engine A: "analytical" pathway
        self.engine_a = nn.Sequential(
            nn.Linear(d_model, d_model * 2),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(d_model * 2, d_model),
        )
        # Engine G: "pattern" pathway
        self.engine_g = nn.Sequential(
            nn.Linear(d_model, d_model * 2),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(d_model * 2, d_model),
        )
        # Learnable tension scale (initialized to 1.0)
        self.tension_scale = nn.Parameter(torch.tensor(1.0))

        # Field transform: maps repulsion direction to output space
        self.field_transform = nn.Sequential(
            nn.Linear(d_model, d_model),
            nn.Tanh(),
        )

        # Per-forward storage for analysis
        self.last_tension = None

    def forward(self, x):
        """
        Args:
            x: (B, T, D)
        Returns:
            output: (B, T, D) -- the field output
            tension: (B, T) -- per-token tension magnitude
        """
        out_a = self.engine_a(x)  # (B, T, D)
        out_g = self.engine_g(x)  # (B, T, D)

        repulsion = out_a - out_g  # (B, T, D)
        tension = (repulsion ** 2).mean(dim=-1, keepdim=True)  # (B, T, 1)

        direction = self.field_transform(repulsion)  # (B, T, D)

        output = self.tension_scale * torch.sqrt(tension + 1e-8) * direction

        self.last_tension = tension.squeeze(-1).detach()  # (B, T)

        return output, tension.squeeze(-1)  # (B,T,D), (B,T)


# ═══════════════════════════════════════════════════════════════
# TRANSFORMER BLOCKS
# ═══════════════════════════════════════════════════════════════

class TransformerBlock(nn.Module):
    """Single transformer block: Attention + FFN (or PureField)."""

    def __init__(self, d_model, n_heads, ffn_module, dropout=0.1):
        super().__init__()
        self.attn = MultiHeadAttention(d_model, n_heads, dropout)
        self.ffn = ffn_module
        self.ln1 = nn.LayerNorm(d_model)
        self.ln2 = nn.LayerNorm(d_model)
        self.dropout = nn.Dropout(dropout)

    def forward(self, x):
        # Pre-norm architecture
        h = x + self.dropout(self.attn(self.ln1(x)))
        ffn_out, tension = self.ffn(self.ln2(h))
        h = h + self.dropout(ffn_out)
        return h, tension


# ═══════════════════════════════════════════════════════════════
# FULL LANGUAGE MODELS
# ═══════════════════════════════════════════════════════════════

class CharLM(nn.Module):
    """Character-level language model with configurable FFN type."""

    def __init__(self, vocab_size, d_model, n_heads, n_layers,
                 ffn_type="standard", dropout=0.1, ffn_mult=4,
                 max_len=512):
        super().__init__()
        self.d_model = d_model
        self.ffn_type = ffn_type

        self.tok_emb = nn.Embedding(vocab_size, d_model)
        self.pos_emb = nn.Embedding(max_len, d_model)
        self.drop = nn.Dropout(dropout)

        self.blocks = nn.ModuleList()
        for _ in range(n_layers):
            if ffn_type == "standard":
                ffn = StandardFFN(d_model, ffn_mult, dropout)
            elif ffn_type == "purefield":
                ffn = PureFieldBlock(d_model, dropout)
            else:
                raise ValueError(f"Unknown ffn_type: {ffn_type}")
            self.blocks.append(TransformerBlock(d_model, n_heads, ffn, dropout))

        self.ln_f = nn.LayerNorm(d_model)
        self.head = nn.Linear(d_model, vocab_size, bias=False)

        # Weight tying: tok_emb and head share weights
        self.head.weight = self.tok_emb.weight

        self._init_weights()

    def _init_weights(self):
        for p in self.parameters():
            if p.dim() > 1:
                nn.init.xavier_uniform_(p)

    def forward(self, x):
        """
        Args:
            x: (B, T) token indices
        Returns:
            logits: (B, T, V)
            tensions: list of (B, T) per layer, or empty for standard
        """
        B, T = x.shape
        positions = torch.arange(T, device=x.device).unsqueeze(0)

        h = self.drop(self.tok_emb(x) + self.pos_emb(positions))

        tensions = []
        for block in self.blocks:
            h, tension = block(h)
            tensions.append(tension)

        logits = self.head(self.ln_f(h))
        return logits, tensions

    def count_params(self):
        return sum(p.numel() for p in self.parameters())


# ═══════════════════════════════════════════════════════════════
# TRAINING
# ═══════════════════════════════════════════════════════════════

def get_lr(step, warmup, base_lr, total_steps):
    """Linear warmup + cosine decay."""
    if step < warmup:
        return base_lr * step / max(warmup, 1)
    progress = (step - warmup) / max(total_steps - warmup, 1)
    return base_lr * 0.5 * (1.0 + math.cos(math.pi * progress))


def train_epoch(model, loader, optimizer, cfg, device, epoch, global_step):
    """Train for one epoch. Returns metrics."""
    model.train()
    total_loss = 0.0
    total_tokens = 0
    all_tensions = []
    step_losses = []

    total_steps = cfg["epochs"] * len(loader)

    for batch_idx, (x, y) in enumerate(loader):
        x, y = x.to(device), y.to(device)

        # LR schedule
        lr = get_lr(global_step, cfg["warmup_steps"], cfg["lr"], total_steps)
        for pg in optimizer.param_groups:
            pg["lr"] = lr

        logits, tensions = model(x)
        loss = F.cross_entropy(logits.view(-1, logits.size(-1)), y.view(-1))

        # PureField entropy regularization: encourage diverse tension
        if model.ffn_type == "purefield" and cfg["aux_entropy_lambda"] > 0:
            for t in tensions:
                if t.requires_grad:
                    # Encourage tension variance (avoid collapse)
                    t_var = t.var()
                    loss = loss - cfg["aux_entropy_lambda"] * torch.log(t_var + 1e-8)

        optimizer.zero_grad()
        loss.backward()
        if cfg["grad_clip"] > 0:
            nn.utils.clip_grad_norm_(model.parameters(), cfg["grad_clip"])
        optimizer.step()

        n_tokens = y.numel()
        total_loss += loss.item() * n_tokens
        total_tokens += n_tokens
        step_losses.append(loss.item())

        # Collect tension stats
        if model.ffn_type == "purefield":
            with torch.no_grad():
                mean_t = torch.stack([t.mean() for t in tensions]).mean().item()
                all_tensions.append(mean_t)

        if (batch_idx + 1) % cfg["log_interval"] == 0:
            avg = total_loss / total_tokens
            ppl = math.exp(min(avg, 20))
            extra = ""
            if all_tensions:
                extra = f"  T={np.mean(all_tensions[-cfg['log_interval']:]):.4f}"
            print(f"    [E{epoch+1}] step {batch_idx+1}/{len(loader)}: "
                  f"loss={avg:.4f} ppl={ppl:.1f} lr={lr:.2e}{extra}")

        global_step += 1

    avg_loss = total_loss / total_tokens
    avg_ppl = math.exp(min(avg_loss, 20))

    return {
        "loss": avg_loss,
        "ppl": avg_ppl,
        "step_losses": step_losses,
        "tensions": all_tensions,
        "global_step": global_step,
    }


@torch.no_grad()
def evaluate(model, loader, device):
    """Evaluate on validation set. Returns per-token metrics."""
    model.eval()
    total_loss = 0.0
    total_tokens = 0

    # Per-token analysis
    all_token_ce = []       # cross-entropy per token position
    all_token_tension = []  # tension per token position (purefield only)
    all_token_correct = []  # top-1 correctness per token

    for x, y in loader:
        x, y = x.to(device), y.to(device)
        logits, tensions = model(x)

        # Per-token CE
        B, T, V = logits.shape
        ce = F.cross_entropy(logits.view(-1, V), y.view(-1), reduction='none')
        ce = ce.view(B, T)
        all_token_ce.append(ce.cpu())

        # Per-token correctness
        preds = logits.argmax(dim=-1)
        correct = (preds == y).float()
        all_token_correct.append(correct.cpu())

        # Per-token tension
        if model.ffn_type == "purefield":
            # Average tension across layers
            mean_tension = torch.stack(tensions).mean(dim=0)  # (B, T)
            all_token_tension.append(mean_tension.cpu())

        total_loss += ce.sum().item()
        total_tokens += y.numel()

    avg_loss = total_loss / total_tokens
    avg_ppl = math.exp(min(avg_loss, 20))

    token_ce = torch.cat(all_token_ce, dim=0)       # (N, T)
    token_correct = torch.cat(all_token_correct, dim=0)

    result = {
        "loss": avg_loss,
        "ppl": avg_ppl,
        "token_ce": token_ce,
        "token_correct": token_correct,
    }

    if all_token_tension:
        result["token_tension"] = torch.cat(all_token_tension, dim=0)

    return result


# ═══════════════════════════════════════════════════════════════
# ANALYSIS: Tension-Correctness Correlation
# ═══════════════════════════════════════════════════════════════

def analyze_tension_correctness(eval_result):
    """Analyze correlation between tension and per-token correctness/PPL."""
    if "token_tension" not in eval_result:
        return None

    tension = eval_result["token_tension"].numpy().flatten()
    correct = eval_result["token_correct"].numpy().flatten()
    ce = eval_result["token_ce"].numpy().flatten()
    ppl = np.exp(np.clip(ce, 0, 20))

    # Pearson correlations
    from scipy.stats import pearsonr, spearmanr

    r_correct, p_correct = pearsonr(tension, correct)
    r_ppl, p_ppl = pearsonr(tension, ppl)
    rho_correct, _ = spearmanr(tension, correct)
    rho_ppl, _ = spearmanr(tension, ppl)

    # Quartile analysis
    quartiles = np.percentile(tension, [25, 50, 75])
    bins = np.digitize(tension, quartiles)

    acc_by_q = []
    ppl_by_q = []
    tension_by_q = []
    for q in range(4):
        mask = bins == q
        if mask.sum() > 0:
            acc_by_q.append(correct[mask].mean())
            ppl_by_q.append(ppl[mask].mean())
            tension_by_q.append(tension[mask].mean())
        else:
            acc_by_q.append(0.0)
            ppl_by_q.append(0.0)
            tension_by_q.append(0.0)

    # Mean tension for correct vs wrong
    t_correct = tension[correct == 1].mean() if correct.sum() > 0 else 0.0
    t_wrong = tension[correct == 0].mean() if (1 - correct).sum() > 0 else 0.0

    return {
        "pearson_r_correct": r_correct,
        "pearson_p_correct": p_correct,
        "pearson_r_ppl": r_ppl,
        "pearson_p_ppl": p_ppl,
        "spearman_rho_correct": rho_correct,
        "spearman_rho_ppl": rho_ppl,
        "acc_by_quartile": acc_by_q,
        "ppl_by_quartile": ppl_by_q,
        "tension_by_quartile": tension_by_q,
        "mean_tension_correct": t_correct,
        "mean_tension_wrong": t_wrong,
        "tension_ratio": t_correct / (t_wrong + 1e-8),
    }


# ═══════════════════════════════════════════════════════════════
# ANALYSIS: PureField internals
# ═══════════════════════════════════════════════════════════════

def analyze_purefield_internals(model):
    """Extract learned parameters from PureField blocks."""
    info = []
    for i, block in enumerate(model.blocks):
        if hasattr(block.ffn, "tension_scale"):
            ts = block.ffn.tension_scale.item()
            info.append({"layer": i, "tension_scale": ts})
    return info


# ═══════════════════════════════════════════════════════════════
# ASCII VISUALIZATION
# ═══════════════════════════════════════════════════════════════

def ascii_loss_curve(losses_dict, width=60, height=15):
    """ASCII plot of training loss curves for multiple models."""
    print(f"\n  Training Loss Curve")
    print(f"  {'=' * (width + 15)}")

    all_vals = []
    for vals in losses_dict.values():
        all_vals.extend(vals)
    if not all_vals:
        print("  (no data)")
        return
    vmin = min(all_vals)
    vmax = max(all_vals)
    if vmax - vmin < 1e-8:
        vmax = vmin + 1

    symbols = {'Standard': '#', 'PureField': '*'}

    for name, vals in losses_dict.items():
        sym = symbols.get(name, '+')
        # Downsample to width
        if len(vals) > width:
            step = len(vals) / width
            sampled = [vals[int(i * step)] for i in range(width)]
        else:
            sampled = vals

        line = ""
        for v in sampled:
            pos = int((v - vmin) / (vmax - vmin) * (height - 1))
            pos = height - 1 - pos  # invert y
            line += sym if pos == height // 2 else " "  # simplified

        # Better: bar representation
        print(f"  {name:<12}", end="")
        for v in sampled[-min(width, len(sampled)):]:
            bar_pos = int((v - vmin) / (vmax - vmin) * 9)
            chars = " .:-=+*#%@"
            print(chars[bar_pos], end="")
        print()

    print(f"  {'':>12}{'|' + '-' * (min(width, len(sampled)) - 2) + '|'}")
    print(f"  {'':>12}{vmin:.3f}{' ' * (min(width, len(sampled)) - 12)}{vmax:.3f}")


def ascii_bar(label, value, max_val, width=40):
    filled = int(value / max_val * width) if max_val > 0 else 0
    bar = '#' * filled + '.' * (width - filled)
    return f"  {label:<20} |{bar}| {value:.4f}"


def ascii_quartile_table(analysis):
    """Print tension quartile analysis."""
    print(f"\n  Tension Quartile Analysis")
    print(f"  {'Quartile':<15} {'Tension':>10} {'Accuracy':>10} {'PPL':>10}")
    print(f"  {'-' * 47}")
    labels = ['Q1 (low)', 'Q2', 'Q3', 'Q4 (high)']
    for i in range(4):
        print(f"  {labels[i]:<15} {analysis['tension_by_quartile'][i]:>10.4f} "
              f"{analysis['acc_by_quartile'][i]:>10.4f} "
              f"{analysis['ppl_by_quartile'][i]:>10.2f}")


# ═══════════════════════════════════════════════════════════════
# MAIN EXPERIMENT
# ═══════════════════════════════════════════════════════════════

def run_experiment(cfg):
    """Run full A/B comparison: Standard FFN vs PureField."""

    # --- Device setup (GPU section) ---
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"  Device: {device}")
    if device.type == "cuda":
        print(f"  GPU: {torch.cuda.get_device_name(0)}")
        print(f"  Memory: {torch.cuda.get_device_properties(0).total_mem / 1e9:.1f} GB")

    # --- Data ---
    print("\n[1/5] Loading Shakespeare data...")
    train_loader, val_loader, vocab_size, char2idx, idx2char = load_shakespeare(cfg)

    results = {}

    # --- Model A: Standard FFN ---
    print("\n" + "=" * 70)
    print("[2/5] Training STANDARD Transformer (FFN baseline)")
    print("=" * 70)

    model_std = CharLM(
        vocab_size=vocab_size,
        d_model=cfg["d_model"],
        n_heads=cfg["n_heads"],
        n_layers=cfg["n_layers"],
        ffn_type="standard",
        dropout=cfg["dropout"],
        ffn_mult=cfg["ffn_mult"],
        max_len=cfg["seq_len"] + 16,
    ).to(device)

    n_params_std = model_std.count_params()
    print(f"  Parameters: {n_params_std:,}")

    optimizer_std = torch.optim.AdamW(model_std.parameters(), lr=cfg["lr"])
    std_train_losses = []
    std_val_metrics = []
    gs = 0

    for epoch in range(cfg["epochs"]):
        t0 = time.time()
        train_res = train_epoch(model_std, train_loader, optimizer_std,
                                cfg, device, epoch, gs)
        gs = train_res["global_step"]
        std_train_losses.extend(train_res["step_losses"])

        if (epoch + 1) % cfg["eval_interval"] == 0 or epoch == cfg["epochs"] - 1:
            val_res = evaluate(model_std, val_loader, device)
            std_val_metrics.append(val_res)
            dt = time.time() - t0
            print(f"  Epoch {epoch+1}/{cfg['epochs']}: "
                  f"train_loss={train_res['loss']:.4f} "
                  f"val_loss={val_res['loss']:.4f} "
                  f"val_ppl={val_res['ppl']:.2f} "
                  f"({dt:.1f}s)")

    results["standard"] = {
        "train_losses": std_train_losses,
        "val_metrics": std_val_metrics,
        "n_params": n_params_std,
        "final_ppl": std_val_metrics[-1]["ppl"],
        "final_loss": std_val_metrics[-1]["loss"],
    }

    # --- Model B: PureField ---
    print("\n" + "=" * 70)
    print("[3/5] Training PUREFIELD Transformer (field replaces FFN)")
    print("=" * 70)

    model_pf = CharLM(
        vocab_size=vocab_size,
        d_model=cfg["d_model"],
        n_heads=cfg["n_heads"],
        n_layers=cfg["n_layers"],
        ffn_type="purefield",
        dropout=cfg["dropout"],
        max_len=cfg["seq_len"] + 16,
    ).to(device)

    n_params_pf = model_pf.count_params()
    print(f"  Parameters: {n_params_pf:,}")
    print(f"  Param ratio vs Standard: {n_params_pf / n_params_std:.2f}x")

    optimizer_pf = torch.optim.AdamW(model_pf.parameters(), lr=cfg["lr"])
    pf_train_losses = []
    pf_val_metrics = []
    pf_tensions = []
    gs = 0

    for epoch in range(cfg["epochs"]):
        t0 = time.time()
        train_res = train_epoch(model_pf, train_loader, optimizer_pf,
                                cfg, device, epoch, gs)
        gs = train_res["global_step"]
        pf_train_losses.extend(train_res["step_losses"])
        if train_res["tensions"]:
            pf_tensions.append(np.mean(train_res["tensions"]))

        if (epoch + 1) % cfg["eval_interval"] == 0 or epoch == cfg["epochs"] - 1:
            val_res = evaluate(model_pf, val_loader, device)
            pf_val_metrics.append(val_res)
            dt = time.time() - t0
            t_str = f"  T={pf_tensions[-1]:.4f}" if pf_tensions else ""
            print(f"  Epoch {epoch+1}/{cfg['epochs']}: "
                  f"train_loss={train_res['loss']:.4f} "
                  f"val_loss={val_res['loss']:.4f} "
                  f"val_ppl={val_res['ppl']:.2f} "
                  f"({dt:.1f}s){t_str}")

    results["purefield"] = {
        "train_losses": pf_train_losses,
        "val_metrics": pf_val_metrics,
        "n_params": n_params_pf,
        "final_ppl": pf_val_metrics[-1]["ppl"],
        "final_loss": pf_val_metrics[-1]["loss"],
        "tensions": pf_tensions,
    }

    # --- Analysis ---
    print("\n" + "=" * 70)
    print("[4/5] Analysis")
    print("=" * 70)

    # Tension-correctness correlation (key test for H335)
    print("\n  --- Tension-Correctness Correlation (H335 Core Test) ---")
    pf_final_eval = pf_val_metrics[-1]
    tension_analysis = analyze_tension_correctness(pf_final_eval)

    if tension_analysis:
        print(f"  Pearson r(tension, correct):  {tension_analysis['pearson_r_correct']:+.4f} "
              f"(p={tension_analysis['pearson_p_correct']:.2e})")
        print(f"  Pearson r(tension, PPL):      {tension_analysis['pearson_r_ppl']:+.4f} "
              f"(p={tension_analysis['pearson_p_ppl']:.2e})")
        print(f"  Spearman rho(tension, correct): {tension_analysis['spearman_rho_correct']:+.4f}")
        print(f"  Spearman rho(tension, PPL):     {tension_analysis['spearman_rho_ppl']:+.4f}")
        print(f"  Mean tension (correct tokens): {tension_analysis['mean_tension_correct']:.4f}")
        print(f"  Mean tension (wrong tokens):   {tension_analysis['mean_tension_wrong']:.4f}")
        print(f"  Tension ratio (correct/wrong): {tension_analysis['tension_ratio']:.4f}")

        ascii_quartile_table(tension_analysis)

        # Interpret direction
        r = tension_analysis['pearson_r_correct']
        if r > 0.05:
            print(f"\n  --> High tension = MORE correct (confidence signal)")
        elif r < -0.05:
            print(f"\n  --> High tension = LESS correct (uncertainty signal)")
        else:
            print(f"\n  --> No clear correlation (|r| < 0.05)")

    # PureField internals
    print("\n  --- PureField Learned Parameters ---")
    internals = analyze_purefield_internals(model_pf)
    for info in internals:
        print(f"  Layer {info['layer']}: tension_scale = {info['tension_scale']:.6f}")
        print(f"    Distance from 1/3: {abs(info['tension_scale'] - 1/3):.6f}")
        print(f"    Distance from 1/e: {abs(info['tension_scale'] - 1/math.e):.6f}")

    # Tension dynamics over training
    if pf_tensions:
        print(f"\n  --- Tension Dynamics Over Training ---")
        for i, t in enumerate(pf_tensions):
            bar_len = min(50, int(t / (max(pf_tensions) + 1e-8) * 50))
            print(f"    Epoch {i+1:>2}: |{'#' * bar_len}{'.' * (50 - bar_len)}| {t:.6f}")

        # Check for ln(step) growth pattern (H320)
        if len(pf_tensions) > 3:
            epochs_arr = np.arange(1, len(pf_tensions) + 1)
            log_epochs = np.log(epochs_arr)
            r_log = np.corrcoef(log_epochs, pf_tensions)[0, 1]
            print(f"\n  r(ln(epoch), tension) = {r_log:.4f}")
            if r_log > 0.8:
                print(f"  --> Tension ~ ln(epoch) growth pattern CONFIRMED (H320)")
            elif r_log > 0.5:
                print(f"  --> Weak ln(epoch) pattern (r={r_log:.3f})")
            else:
                print(f"  --> No ln(epoch) pattern")

    # --- Summary ---
    print("\n" + "=" * 70)
    print("[5/5] RESULTS SUMMARY")
    print("=" * 70)

    ppl_std = results["standard"]["final_ppl"]
    ppl_pf = results["purefield"]["final_ppl"]
    ppl_diff = ppl_pf - ppl_std
    ppl_ratio = ppl_pf / ppl_std

    print(f"\n  {'Model':<20} {'Params':>10} {'Val Loss':>10} {'Val PPL':>10}")
    print(f"  {'-' * 52}")
    print(f"  {'Standard FFN':<20} {results['standard']['n_params']:>10,} "
          f"{results['standard']['final_loss']:>10.4f} {ppl_std:>10.2f}")
    print(f"  {'PureField':<20} {results['purefield']['n_params']:>10,} "
          f"{results['purefield']['final_loss']:>10.4f} {ppl_pf:>10.2f}")
    print(f"  {'-' * 52}")
    print(f"  PPL difference:  {ppl_diff:+.2f} ({'PureField worse' if ppl_diff > 0 else 'PureField better'})")
    print(f"  PPL ratio:       {ppl_ratio:.4f}x")
    print(f"  Param ratio:     {results['purefield']['n_params'] / results['standard']['n_params']:.4f}x")

    # Loss curve ASCII
    ascii_loss_curve({
        "Standard": [m["loss"] for m in std_val_metrics],
        "PureField": [m["loss"] for m in pf_val_metrics],
    })

    # Verdict
    print("\n  " + "=" * 50)
    print("  VERDICT (H335)")
    print("  " + "=" * 50)

    if ppl_ratio <= 1.0:
        print("  PureField PPL <= Standard FFN")
        print("  --> H335 SUPPORTED: Field-only FFN replacement viable")
    elif ppl_ratio <= 1.1:
        print("  PureField PPL within 10% of Standard FFN")
        print("  --> H335 PARTIALLY SUPPORTED: competitive with fewer assumptions")
    elif ppl_ratio <= 1.3:
        print("  PureField PPL within 30% of Standard FFN")
        print("  --> H335 WEAK: functional but not competitive yet")
    else:
        print(f"  PureField PPL {ppl_ratio:.2f}x worse than Standard")
        print("  --> H335 NOT SUPPORTED at this scale")

    if tension_analysis:
        r = tension_analysis['pearson_r_correct']
        p = tension_analysis['pearson_p_correct']
        if abs(r) > 0.05 and p < 0.01:
            direction = "confidence" if r > 0 else "uncertainty"
            print(f"  Tension-correctness: SIGNIFICANT ({direction} signal, r={r:+.3f}, p={p:.2e})")
        else:
            print(f"  Tension-correctness: NOT SIGNIFICANT (r={r:+.3f}, p={p:.2e})")

    # Save results to JSON
    save_path = os.path.join(os.path.dirname(__file__), "rc1_results.json")
    save_data = {
        "config": cfg,
        "standard": {
            "n_params": results["standard"]["n_params"],
            "final_ppl": float(ppl_std),
            "final_loss": float(results["standard"]["final_loss"]),
        },
        "purefield": {
            "n_params": results["purefield"]["n_params"],
            "final_ppl": float(ppl_pf),
            "final_loss": float(results["purefield"]["final_loss"]),
            "tensions": [float(t) for t in pf_tensions] if pf_tensions else [],
        },
        "tension_analysis": {
            k: float(v) if isinstance(v, (float, np.floating)) else v
            for k, v in (tension_analysis or {}).items()
            if not isinstance(v, np.ndarray)
        },
        "ppl_ratio": float(ppl_ratio),
    }
    with open(save_path, "w") as f:
        json.dump(save_data, f, indent=2, default=str)
    print(f"\n  Results saved to {save_path}")

    print("\n" + "=" * 70)
    print("  experiment_rc1_purefield_llm.py COMPLETE")
    print("=" * 70)

    return results


# ═══════════════════════════════════════════════════════════════
# ENTRY POINT
# ═══════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("=" * 70)
    print("  RC-1: PureField Language Model Experiment")
    print("  H335: FFN -> PureField replacement in Transformer LM")
    print("  Data: TinyShakespeare (character-level)")
    print("=" * 70)

    t_start = time.time()
    results = run_experiment(CONFIG)
    elapsed = time.time() - t_start
    print(f"\n  Total time: {elapsed:.1f}s ({elapsed/60:.1f}min)")
```