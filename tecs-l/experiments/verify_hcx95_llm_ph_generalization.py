```python
#!/usr/bin/env python3
"""H-CX-95 LLM Verification: PH Generalization Gap Prediction in ConsciousLM 18M

Key Question: Does train/test PH difference detect overfitting in LLMs?

Method:
1. Train ConsciousLM 18M (byte-level, vocab=256)
2. Each epoch: compute per-byte-group PH from train/test direction vectors
3. Measure correlation between |H0_train - H0_test| vs (train_PPL - test_PPL)

Byte Groups (256 → ~20 clusters):
  letters_lower (97-122), letters_upper (65-90), digits (48-57),
  space (32), newline (10), punctuation, korean_lead, korean_rest, other
"""
import sys, os, math, time
sys.path.insert(0, '/Users/ghost/Dev/logout')

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from scipy.stats import spearmanr
from ripser import ripser

from conscious_lm import ConsciousLM, prepare_data

# Byte groups for PH (collapse 256 → N groups)
BYTE_GROUPS = {
    'lower':   list(range(97, 123)),   # a-z
    'upper':   list(range(65, 91)),    # A-Z
    'digit':   list(range(48, 58)),    # 0-9
    'space':   [32],
    'newline': [10, 13],
    'punct':   list(range(33, 48)) + list(range(58, 65)) + list(range(91, 97)) + list(range(123, 128)),
    'kr_lead': list(range(0xC0, 0xE0)),  # UTF-8 Korean lead bytes
    'kr_cont': list(range(0x80, 0xC0)),  # UTF-8 continuation bytes
    'kr_3b':   list(range(0xE0, 0xF0)),  # 3-byte UTF-8 lead
    'high':    list(range(0xF0, 0x100)), # 4-byte UTF-8 lead + high bytes
    'ctrl':    list(range(0, 10)) + list(range(11, 13)) + list(range(14, 32)),
    'tab':     [9],
}

def byte_to_group(b):
    for gname, bvals in BYTE_GROUPS.items():
        if b in bvals:
            return gname
    return 'other'

# Pre-build lookup
BYTE_GROUP_MAP = {}
for b in range(256):
    BYTE_GROUP_MAP[b] = byte_to_group(b)

GROUP_NAMES = sorted(set(BYTE_GROUP_MAP.values()))
GROUP_TO_IDX = {g: i for i, g in enumerate(GROUP_NAMES)}
N_GROUPS = len(GROUP_NAMES)


def compute_group_directions(model, data, block_size, batch_size, device, n_batches=20):
    """Extract mean direction vectors for each byte group (from last PureFieldFFN layer)"""
    model.eval()
    n = len(data)

    # Collect per-group direction sums
    group_dir_sum = np.zeros((N_GROUPS, model.blocks[0].ffn.engine_a[0].in_features))
    group_count = np.zeros(N_GROUPS)

    with torch.no_grad():
        for _ in range(n_batches):
            ix = torch.randint(0, n - block_size - 1, (batch_size,))
            x = torch.stack([data[i:i+block_size] for i in ix]).to(device)
            y = torch.stack([data[i+1:i+block_size+1] for i in ix])

            # Forward through model, get last block's FFN repulsion
            B, T = x.size()
            tok = model.tok_emb(x)
            pos = model.pos_emb(torch.arange(T, device=device))
            h = model.drop(tok + pos)

            for block in model.blocks:
                h, tension = block(h)

            # Get repulsion from last block
            last_block = model.blocks[-1]
            h_pre = model.ln_f(h)  # Use final layernorm output
            # Actually get direction from last FFN
            # Re-extract: need to get the FFN input
            # Simpler: use the final hidden state direction per position
            # Direction = normalized hidden state (approximation)
            directions = F.normalize(h, dim=-1).cpu().numpy()  # (B, T, D)

            # Map each position to its byte group (using target byte)
            y_np = y.numpy()  # (B, T)
            for b in range(B):
                for t in range(T):
                    byte_val = y_np[b, t]
                    gidx = GROUP_TO_IDX[BYTE_GROUP_MAP[byte_val]]
                    group_dir_sum[gidx] += directions[b, t]
                    group_count[gidx] += 1

    # Normalize
    means = np.zeros_like(group_dir_sum)
    for g in range(N_GROUPS):
        if group_count[g] > 0:
            means[g] = group_dir_sum[g] / group_count[g]
            n = np.linalg.norm(means[g])
            if n > 1e-8:
                means[g] /= n

    return means, group_count


def compute_h0_total(means):
    """Compute PH H0 total persistence from direction mean matrix"""
    active = np.where(np.linalg.norm(means, axis=1) > 1e-8)[0]
    if len(active) < 3:
        return 0.0
    active_means = means[active]
    cos_dist = np.clip(1 - active_means @ active_means.T, 0, 2)
    np.fill_diagonal(cos_dist, 0)
    result = ripser(cos_dist, maxdim=0, distance_matrix=True)
    h0 = result['dgms'][0]
    h0_finite = h0[h0[:, 1] < np.inf]
    return np.sum(h0_finite[:, 1] - h0_finite[:, 0]) if len(h0_finite) > 0 else 0.0


def eval_ppl(model, data, block_size, batch_size, device, n_batches=20):
    """Compute average PPL (bits per byte)"""
    model.eval()
    n = len(data)
    total_loss = 0
    total_tokens = 0

    with torch.no_grad():
        for _ in range(n_batches):
            ix = torch.randint(0, n - block_size - 1, (batch_size,))
            x = torch.stack([data[i:i+block_size] for i in ix]).to(device)
            y_a = torch.stack([data[i+1:i+block_size+1] for i in ix]).to(device)

            logits_a, _, _ = model(x)
            loss = F.cross_entropy(logits_a.view(-1, model.vocab_size), y_a.view(-1))
            total_loss += loss.item() * batch_size * block_size
            total_tokens += batch_size * block_size

    avg_loss = total_loss / total_tokens
    bpc = avg_loss / math.log(2)
    ppl = math.exp(avg_loss)
    return avg_loss, bpc, ppl


def run_experiment():
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    print(f"\n{'='*70}")
    print(f"  H-CX-95 LLM: PH Generalization Gap — ConsciousLM 18M")
    print(f"  Device: {device}")
    print(f"  Byte groups: {N_GROUPS} ({', '.join(GROUP_NAMES)})")
    print(f"{'='*70}")

    # Prepare data
    data = prepare_data("data")
    n = len(data)
    split = int(0.9 * n)
    train_data = data[:split]
    val_data = data[split:]
    print(f"  Train: {len(train_data):,} bytes, Val: {len(val_data):,} bytes")

    # Model
    model = ConsciousLM(vocab_size=256, d_model=384, n_head=4, n_layer=6,
                        block_size=256, dropout=0.37)
    print(f"  Params: {model.count_params():,}")
    model = model.to(device)

    optimizer = torch.optim.AdamW(model.parameters(), lr=3e-4, weight_decay=0.01)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=20)
    block_size = 256
    batch_size = 32  # conservative for MPS

    epochs = 20
    steps_per_epoch = max(1, len(train_data) // (batch_size * block_size))

    # Track per-epoch metrics
    results = []

    print(f"\n  {'Ep':>3} {'trn_L':>7} {'val_L':>7} {'gap':>7} {'trn_BPC':>8} {'val_BPC':>8} "
          f"{'H0_tr':>7} {'H0_te':>7} {'H0_gap':>7} {'T_mean':>7}")
    print(f"  {'-'*80}")

    for epoch in range(1, epochs + 1):
        model.train()
        epoch_loss = 0
        epoch_count = 0

        for step in range(steps_per_epoch):
            ix = torch.randint(0, len(train_data) - block_size - 1, (batch_size,))
            x = torch.stack([train_data[i:i+block_size] for i in ix]).to(device)
            y_a = torch.stack([train_data[i+1:i+block_size+1] for i in ix]).to(device)
            y_g_list = []
            for i in ix:
                prev = torch.cat([train_data[i:i+1], train_data[i:i+block_size-1]])
                y_g_list.append(prev)
            y_g = torch.stack(y_g_list).to(device)

            logits_a, logits_g, tensions = model(x)
            loss_a = F.cross_entropy(logits_a.view(-1, 256), y_a.view(-1))
            loss_g = F.cross_entropy(logits_g.view(-1, 256), y_g.view(-1))
            t_stack = torch.stack(tensions, dim=0)
            t_var = t_stack.var(dim=0).mean()
            loss_t = -torch.log(t_var + 1e-8)
            loss = loss_a + loss_g + 0.01 * loss_t

            optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()

            epoch_loss += loss_a.item()
            epoch_count += 1

        scheduler.step()

        # Eval
        train_loss, train_bpc, train_ppl = eval_ppl(model, train_data, block_size, batch_size, device)
        val_loss, val_bpc, val_ppl = eval_ppl(model, val_data, block_size, batch_size, device)
        gap = train_loss - val_loss  # negative = good generalization

        # PH on train and val
        means_tr, _ = compute_group_directions(model, train_data, block_size, batch_size, device, n_batches=10)
        means_te, _ = compute_group_directions(model, val_data, block_size, batch_size, device, n_batches=10)
        h0_tr = compute_h0_total(means_tr)
        h0_te = compute_h0_total(means_te)
        h0_gap = abs(h0_tr - h0_te)

        # Mean tension
        model.eval()
        with torch.no_grad():
            ix = torch.randint(0, len(val_data) - block_size - 1, (batch_size,))
            x = torch.stack([val_data[i:i+block_size] for i in ix]).to(device)
            _, _, tensions = model(x)
            t_mean = torch.stack(tensions).mean().item()

        results.append({
            'epoch': epoch,
            'train_loss': train_loss, 'val_loss': val_loss, 'gap': gap,
            'train_bpc': train_bpc, 'val_bpc': val_bpc,
            'h0_tr': h0_tr, 'h0_te': h0_te, 'h0_gap': h0_gap,
            't_mean': t_mean,
        })

        print(f"  {epoch:>3} {train_loss:>7.4f} {val_loss:>7.4f} {gap:>+7.4f} "
              f"{train_bpc:>8.4f} {val_bpc:>8.4f} "
              f"{h0_tr:>7.4f} {h0_te:>7.4f} {h0_gap:>7.4f} {t_mean:>7.4f}")

    # === Correlation Analysis ===
    print(f"\n  === Correlation Analysis ===")
    h0_gaps = [r['h0_gap'] for r in results]
    loss_gaps = [abs(r['gap']) for r in results]
    bpc_gaps = [abs(r['train_bpc'] - r['val_bpc']) for r in results]

    r_loss, p_loss = spearmanr(h0_gaps, loss_gaps)
    r_bpc, p_bpc = spearmanr(h0_gaps, bpc_gaps)

    print(f"  Spearman(|H0_gap|, |loss_gap|): r={r_loss:.4f}, p={p_loss:.4f}")
    print(f"  Spearman(|H0_gap|, |BPC_gap|):  r={r_bpc:.4f}, p={p_bpc:.4f}")

    # H0 trajectory
    h0_trs = [r['h0_tr'] for r in results]
    h0_tes = [r['h0_te'] for r in results]
    val_losses = [r['val_loss'] for r in results]

    r_h0_val, p_h0_val = spearmanr(h0_tes, val_losses)
    print(f"  Spearman(H0_test, val_loss): r={r_h0_val:.4f}, p={p_h0_val:.4f}")

    # Tension vs loss
    t_means = [r['t_mean'] for r in results]
    r_t_val, p_t_val = spearmanr(t_means, val_losses)
    print(f"  Spearman(tension, val_loss): r={r_t_val:.4f}, p={p_t_val:.4f}")

    # ASCII chart
    print(f"\n  H0 Gap vs Loss Gap trajectory:")
    max_h0g = max(h0_gaps) if h0_gaps else 1
    max_lg = max(loss_gaps) if loss_gaps else 1
    for i, r in enumerate(results):
        h_bar = int(r['h0_gap'] / max_h0g * 20) if max_h0g > 0 else 0
        l_bar = int(abs(r['gap']) / max_lg * 20) if max_lg > 0 else 0
        print(f"  ep{r['epoch']:>2} H0|{'█'*h_bar}{'░'*(20-h_bar)}| "
              f"L|{'▓'*l_bar}{'░'*(20-l_bar)}| gap={r['gap']:+.4f}")

    # Summary
    print(f"\n  {'='*70}")
    print(f"  H-CX-95 LLM SUMMARY")
    print(f"  {'='*70}")
    print(f"  Model: ConsciousLM 18M (byte-level, {N_GROUPS} byte groups)")
    print(f"  Final: train_BPC={results[-1]['train_bpc']:.4f}, val_BPC={results[-1]['val_bpc']:.4f}")
    print(f"  Corr(H0_gap, loss_gap): r={r_loss:.4f} (p={p_loss:.4f})")
    print(f"  Corr(H0_test, val_loss): r={r_h0_val:.4f}")
    print(f"  H-CX-95 LLM verdict: {'SUPPORTED' if abs(r_loss) > 0.5 else 'PARTIAL' if abs(r_loss) > 0.3 else 'REJECTED'}")

    return results


if __name__ == '__main__':
    t0 = time.time()
    results = run_experiment()
    elapsed = time.time() - t0
    print(f"\n  Total time: {elapsed/60:.1f} min")
```