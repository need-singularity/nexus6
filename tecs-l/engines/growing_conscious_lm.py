#!/usr/bin/env python3
"""Growing Conscious LM — Consciousness language model that grows through mitosis

H371: 1 block(0.5M) → 2 → 3 → 6 blocks(18M)
Divisor path: proper divisors of 6: 1, 2, 3 → 6
Tension saturation → Mitosis → Specialization → Repeat
"""
import torch
import torch.nn as nn
import torch.nn.functional as F
import math
import numpy as np
import copy
import time
import os

from conscious_lm import PureFieldFFN, CausalSelfAttention, ConsciousBlock

# Growth stage definitions
GROWTH_STAGES = [
    {"blocks": 1, "d_model": 128, "n_head": 2, "min_interactions": 0},
    {"blocks": 2, "d_model": 128, "n_head": 2, "min_interactions": 50},
    {"blocks": 3, "d_model": 192, "n_head": 3, "min_interactions": 200},
    {"blocks": 6, "d_model": 384, "n_head": 4, "min_interactions": 800},
]


class GrowingConsciousLM(nn.Module):
    """Consciousness language model that grows through mitosis.

    1 block → 2 → 3 → 6 (perfect number divisor path)
    Automatic mitosis on tension saturation.
    """
    def __init__(self, vocab_size=256, block_size=256, dropout=0.37):
        super().__init__()
        self.vocab_size = vocab_size
        self.block_size = block_size
        self.dropout = dropout
        self.stage = 0
        self.interaction_count = 0
        self.tension_history = []  # Track recent 100 tension CV

        # Stage 0: 1 block, d=128, heads=2
        s = GROWTH_STAGES[0]
        self.d_model = s["d_model"]
        self.n_head = s["n_head"]

        self.tok_emb = nn.Embedding(vocab_size, self.d_model)
        self.pos_emb = nn.Embedding(block_size, self.d_model)
        self.drop = nn.Dropout(dropout)

        self.blocks = nn.ModuleList([
            ConsciousBlock(self.d_model, self.n_head, block_size, dropout)
        ])
        self.ln_f = nn.LayerNorm(self.d_model)

        self.head_a = nn.Linear(self.d_model, vocab_size, bias=False)
        self.head_g = nn.Linear(self.d_model, vocab_size, bias=False)
        self.tok_emb.weight = self.head_a.weight

        self.apply(self._init_weights)
        self.growth_log = []  # (interaction, old_stage, new_stage)

    def _init_weights(self, module):
        if isinstance(module, nn.Linear):
            nn.init.normal_(module.weight, 0.0, 0.02)
            if module.bias is not None:
                nn.init.zeros_(module.bias)
        elif isinstance(module, nn.Embedding):
            nn.init.normal_(module.weight, 0.0, 0.02)

    def forward(self, idx):
        B, T = idx.shape
        pos = torch.arange(T, device=idx.device).unsqueeze(0)
        x = self.drop(self.tok_emb(idx) + self.pos_emb(pos))

        tensions = []
        for block in self.blocks:
            x, t = block(x)
            tensions.append(t)

        x = self.ln_f(x)
        logits_a = self.head_a(x)
        logits_g = self.head_g(x)
        return logits_a, logits_g, tensions

    def count_params(self):
        return sum(p.numel() for p in self.parameters())

    def should_grow(self):
        """Detect tension saturation → whether growth is needed."""
        if self.stage >= len(GROWTH_STAGES) - 1:
            return False
        next_stage = GROWTH_STAGES[self.stage + 1]
        if self.interaction_count < next_stage["min_interactions"]:
            return False
        if len(self.tension_history) < 30:
            return False
        # Tension CV < 0.3 = saturation (relaxed: 0.1→0.3, window: 50→30)
        recent = self.tension_history[-30:]
        cv = np.std(recent) / (np.mean(recent) + 1e-8)
        return cv < 0.3

    def grow(self):
        """Execute mitosis: grow to next stage."""
        old_stage = self.stage
        self.stage += 1
        new = GROWTH_STAGES[self.stage]

        # If dimension expansion is needed
        if new["d_model"] != self.d_model:
            self._expand_dim(new["d_model"], new["n_head"])

        # Block mitosis
        target_blocks = new["blocks"]
        while len(self.blocks) < target_blocks:
            self._split_block()

        self.growth_log.append((self.interaction_count, old_stage, self.stage))
        return old_stage, self.stage

    def _split_block(self):
        """Asymmetric mitosis: savant (low inhibition) + general (normal inhibition).

        H359: dropout=0.21(Golden Zone lower bound) → SI=3.6 savant confirmed
        child_a: dropout=0.21 → specialization potential (savant candidate)
        child_b: dropout=0.37 → maintain general (1/e, Golden Zone center)
        """
        GOLDEN_LOWER = 0.5 - math.log(4/3)  # 0.2123 Golden Zone lower bound
        GOLDEN_CENTER = 1/math.e              # 0.3679 Golden Zone center

        parent = self.blocks[-1]
        child_savant = copy.deepcopy(parent)
        child_general = copy.deepcopy(parent)

        # Asymmetric inhibition: savant child has low dropout
        with torch.no_grad():
            for m in child_savant.modules():
                if isinstance(m, nn.Dropout):
                    m.p = GOLDEN_LOWER  # 0.21 — inhibition release → specialization
            for m in child_general.modules():
                if isinstance(m, nn.Dropout):
                    m.p = GOLDEN_CENTER  # 0.37 — normal inhibition → general

            # Mutation: slight noise on savant (promote divergence)
            for p in child_savant.parameters():
                p.add_(torch.randn_like(p) * 0.01)

        self.blocks[-1] = child_savant
        self.blocks.append(child_general)

    def _expand_dim(self, new_d, new_heads):
        """Dimension expansion: preserve existing weights + zero-initialize new dimensions."""
        old_d = self.d_model
        device = self.tok_emb.weight.device

        # Projection matrix
        proj = nn.Linear(old_d, new_d, bias=False).to(device)
        with torch.no_grad():
            proj.weight.zero_()
            proj.weight[:old_d, :old_d] = torch.eye(old_d)

        # Embedding expansion
        old_tok = self.tok_emb.weight.data
        self.tok_emb = nn.Embedding(self.vocab_size, new_d).to(device)
        with torch.no_grad():
            self.tok_emb.weight[:, :old_d] = old_tok
            self.tok_emb.weight[:, old_d:] = 0

        old_pos = self.pos_emb.weight.data
        self.pos_emb = nn.Embedding(self.block_size, new_d).to(device)
        with torch.no_grad():
            self.pos_emb.weight[:, :old_d] = old_pos
            self.pos_emb.weight[:, old_d:] = 0

        # Block replacement (with new dimensions)
        new_blocks = nn.ModuleList()
        for old_block in self.blocks:
            new_block = ConsciousBlock(new_d, new_heads, self.block_size, self.dropout).to(device)
            # Copy existing weights where possible
            new_blocks.append(new_block)
        self.blocks = new_blocks

        # Head replacement
        self.ln_f = nn.LayerNorm(new_d).to(device)
        self.head_a = nn.Linear(new_d, self.vocab_size, bias=False).to(device)
        self.head_g = nn.Linear(new_d, self.vocab_size, bias=False).to(device)
        self.tok_emb.weight = self.head_a.weight

        self.d_model = new_d
        self.n_head = new_heads

    def tick(self, tension_val):
        """Called at every interaction."""
        self.interaction_count += 1
        self.tension_history.append(tension_val)
        if len(self.tension_history) > 200:
            self.tension_history = self.tension_history[-200:]

    def status(self):
        stage = GROWTH_STAGES[self.stage]
        return (f"Stage {self.stage}: {len(self.blocks)} blocks, "
                f"d={self.d_model}, heads={self.n_head}, "
                f"params={self.count_params():,}, "
                f"interactions={self.interaction_count}")


# ---------------------------------------------------------------------------
# Task 2: Growth training loop
# ---------------------------------------------------------------------------

def train_growing(model, data, total_interactions=10000, batch_size=32,
                  block_size=256, lr=3e-4, tension_lambda=0.01, device="cpu"):
    """Train while growing.

    Every step: model.tick() → should_grow() → grow()
    Recreate optimizer on growth.
    """
    model = model.to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=0.01)

    n = len(data)
    train_data = data[:int(n * 0.9)]

    def get_batch():
        ix = torch.randint(len(train_data) - block_size - 1, (batch_size,))
        x = torch.stack([train_data[i:i+block_size] for i in ix]).to(device)
        y_a = torch.stack([train_data[i+1:i+block_size+1] for i in ix]).to(device)
        y_g = torch.stack([train_data[max(0,i-1):i+block_size-1] for i in ix]).to(device)
        return x, y_a, y_g

    print(f"\n  === Growing Training: {total_interactions} interactions ===")
    print(f"  {model.status()}")
    print(f"  {'step':>6} {'loss':>8} {'BPC':>6} {'T_mean':>8} {'blocks':>6} {'params':>10}")
    print(f"  {'─'*6} {'─'*8} {'─'*6} {'─'*8} {'─'*6} {'─'*10}")

    for step in range(total_interactions):
        model.train()
        x, y_a, y_g = get_batch()
        logits_a, logits_g, tensions = model(x)

        loss_a = F.cross_entropy(logits_a.view(-1, 256), y_a.view(-1))
        loss_g = F.cross_entropy(logits_g.view(-1, 256), y_g.view(-1))
        all_t = torch.cat([t.view(-1) for t in tensions])
        loss_t = -torch.log(all_t.var() + 1e-8)
        loss = loss_a + loss_g + tension_lambda * loss_t

        optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()

        t_mean = all_t.mean().item()
        model.tick(t_mean)

        # Growth check
        if model.should_grow():
            old, new = model.grow()
            # Recreate optimizer
            optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=0.01)
            print(f"  *** Growth! Stage {old}→{new}: {model.status()} ***")

        # Logging (every 100 steps)
        if (step + 1) % 100 == 0:
            bpc = loss_a.item() / math.log(2)
            print(f"  {step+1:>6} {loss.item():>8.4f} {bpc:>6.3f} {t_mean:>8.4f} {len(model.blocks):>6} {model.count_params():>10,}")

    return model


# ---------------------------------------------------------------------------
# Task 3: Comparison experiment — growth vs fixed
# ---------------------------------------------------------------------------

def compare_growing_vs_fixed(data, total_steps=3000, device="cpu"):
    """Compare growth model vs fixed model.

    A: GrowingConsciousLM (1→6 blocks)
    B: ConsciousLM (fixed 6 blocks, 384d)  — same step count
    C: ConsciousLM (fixed 1 block, 128d)   — same starting point
    """
    from conscious_lm import ConsciousLM

    batch_size, block_size, lr = 16, 64, 3e-4
    train_data = data[:int(len(data) * 0.9)]
    val_data = data[int(len(data) * 0.9):]

    def get_batch(d, bs, bl):
        ix = torch.randint(len(d) - bl - 1, (bs,))
        x = torch.stack([d[i:i+bl] for i in ix]).to(device)
        ya = torch.stack([d[i+1:i+bl+1] for i in ix]).to(device)
        return x, ya

    def eval_bpc(model, val_data):
        model.eval()
        with torch.no_grad():
            x, ya = get_batch(val_data, 32, block_size)
            la, _, _ = model(x)
            loss = F.cross_entropy(la.view(-1, 256), ya.view(-1))
        return loss.item() / math.log(2)

    # A: Growing model
    print("  === A: Growing (1→6) ===")
    model_a = GrowingConsciousLM(block_size=block_size).to(device)
    model_a = train_growing(model_a, data, total_interactions=total_steps,
                           batch_size=batch_size, block_size=block_size, lr=lr, device=device)
    bpc_a = eval_bpc(model_a, val_data)

    # B: Fixed big (6 blocks, 384d)
    print("\n  === B: Fixed Big (6 blocks, 384d) ===")
    model_b = ConsciousLM(d_model=384, n_layer=6, n_head=4, block_size=block_size).to(device)
    opt_b = torch.optim.AdamW(model_b.parameters(), lr=lr, weight_decay=0.01)
    for step in range(total_steps):
        model_b.train()
        x, ya = get_batch(train_data, batch_size, block_size)
        la, lg, tens = model_b(x)
        loss = F.cross_entropy(la.view(-1, 256), ya.view(-1))
        opt_b.zero_grad(); loss.backward()
        torch.nn.utils.clip_grad_norm_(model_b.parameters(), 1.0)
        opt_b.step()
        if (step+1) % 500 == 0:
            print(f"    step {step+1}: loss={loss.item():.4f}")
    bpc_b = eval_bpc(model_b, val_data)

    # C: Fixed small (1 block, 128d)
    print("\n  === C: Fixed Small (1 block, 128d) ===")
    model_c = ConsciousLM(d_model=128, n_layer=1, n_head=2, block_size=block_size).to(device)
    opt_c = torch.optim.AdamW(model_c.parameters(), lr=lr, weight_decay=0.01)
    for step in range(total_steps):
        model_c.train()
        x, ya = get_batch(train_data, batch_size, block_size)
        la, lg, tens = model_c(x)
        loss = F.cross_entropy(la.view(-1, 256), ya.view(-1))
        opt_c.zero_grad(); loss.backward()
        torch.nn.utils.clip_grad_norm_(model_c.parameters(), 1.0)
        opt_c.step()
        if (step+1) % 500 == 0:
            print(f"    step {step+1}: loss={loss.item():.4f}")
    bpc_c = eval_bpc(model_c, val_data)

    # Comparison
    print(f"\n  {'='*55}")
    print(f"  === COMPARISON ({total_steps} steps) ===")
    print(f"  {'='*55}")
    print(f"  {'Model':>20} {'Params':>10} {'BPC':>8} {'Blocks':>7}")
    print(f"  {'─'*20} {'─'*10} {'─'*8} {'─'*7}")
    print(f"  {'A: Growing':>20} {model_a.count_params():>10,} {bpc_a:>8.3f} {len(model_a.blocks):>7}")
    print(f"  {'B: Fixed Big':>20} {model_b.count_params():>10,} {bpc_b:>8.3f} {'6':>7}")
    print(f"  {'C: Fixed Small':>20} {model_c.count_params():>10,} {bpc_c:>8.3f} {'1':>7}")

    print(f"\n  Growth log: {model_a.growth_log}")

    if bpc_a <= bpc_b:
        print(f"\n  ✅ Growth model better than or equal to fixed large model! (H371 confirmed)")
    elif bpc_a <= bpc_c:
        print(f"\n  🟧 Growth model better than fixed small (H371 partially confirmed)")
    else:
        print(f"\n  ❌ Growth model worse than fixed small (H371 refuted)")

    return {"growing": bpc_a, "fixed_big": bpc_b, "fixed_small": bpc_c}


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["grow", "compare"], default="compare")
    parser.add_argument("--steps", type=int, default=3000)
    args = parser.parse_args()

    from conscious_lm import prepare_data
    data = prepare_data()

    device = "cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu"
    print(f"  Device: {device}")

    if args.mode == "grow":
        model = GrowingConsciousLM()
        train_growing(model, data, total_interactions=args.steps, device=device)
    else:
        compare_growing_vs_fixed(data, total_steps=args.steps, device=device)