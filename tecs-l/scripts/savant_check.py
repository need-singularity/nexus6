```python
#!/usr/bin/env python3
"""Savant Index — Domain-specific PPL Asymmetry Verification

Measures domain-specific PPL of ConsciousLM Growing 700M model and
calculates Savant Index = max(PPL) / min(PPL) (excluding random).

Domains: English prose, Python code, Math expressions, Korean text, Random bytes
If stage-wise (0,1,2,3) checkpoints exist, also outputs growth trends.

Usage:
    python3 savant_check.py                          # final checkpoint
    python3 savant_check.py --checkpoint stage2.pt   # specific checkpoint
    python3 savant_check.py --all-stages              # 0,1,2,3 + final all
"""

import torch
import torch.nn.functional as F
import math
import os
import sys
import argparse
import numpy as np

from growing_conscious_lm_700m import GrowingConsciousLM700M, GROWTH_STAGES

# ──────────────────────────────────────────────────────────
# Domain Data Generation
# ──────────────────────────────────────────────────────────

DOMAIN_SAMPLES = 8192  # Number of bytes (secure multiple blocks)

def make_english_prose():
    """Shakespeare text (bytes)."""
    path = "data/shakespeare.txt"
    if os.path.exists(path):
        with open(path, "rb") as f:
            raw = f.read()
        # Extract from middle part (avoid start header)
        start = len(raw) // 4
        return raw[start:start + DOMAIN_SAMPLES]
    # Download if not exists
    import urllib.request
    url = "https://raw.githubusercontent.com/karpathy/char-rnn/master/data/tinyshakespeare/input.txt"
    os.makedirs("data", exist_ok=True)
    urllib.request.urlretrieve(url, path)
    with open(path, "rb") as f:
        raw = f.read()
    start = len(raw) // 4
    return raw[start:start + DOMAIN_SAMPLES]


def make_python_code():
    """Extract from this project's .py files."""
    parts = []
    for fname in sorted(os.listdir(".")):
        if fname.endswith(".py") and not fname.startswith("."):
            try:
                with open(fname, "rb") as f:
                    parts.append(f.read())
            except:
                pass
    combined = b"\n".join(parts)
    if len(combined) < DOMAIN_SAMPLES:
        combined = combined * ((DOMAIN_SAMPLES // len(combined)) + 1)
    return combined[:DOMAIN_SAMPLES]


def make_math_expressions():
    """Math expressions: formulas, number sequences, symbols."""
    lines = []
    # Prime sequence
    lines.append("2 3 5 7 11 13 17 19 23 29 31 37 41 43 47 53 59 61 67 71")
    # Fibonacci
    lines.append("1 1 2 3 5 8 13 21 34 55 89 144 233 377 610 987 1597 2584")
    # Formulas
    lines.append("e^(i*pi) + 1 = 0")
    lines.append("sum_{n=1}^{inf} 1/n^2 = pi^2/6")
    lines.append("sigma(6) = 1+2+3+6 = 12 = 2*6")
    lines.append("tau(6) = 4, phi(6) = 2, sigma(6) = 12")
    lines.append("zeta(2) = pi^2/6 = 1.6449340668...")
    lines.append("gamma = 0.5772156649...")
    lines.append("ln(2) = 0.6931471805...")
    # Powers
    for n in range(2, 50):
        lines.append(f"{n}^2 = {n**2}, {n}^3 = {n**3}")
    # Binomial coefficients
    for n in range(1, 20):
        row = " ".join(str(math.comb(n, k)) for k in range(n + 1))
        lines.append(f"C({n},k) = {row}")
    # Integral/derivative
    lines.append("d/dx(x^n) = n*x^(n-1)")
    lines.append("integral(x^n dx) = x^(n+1)/(n+1) + C")
    lines.append("integral_0^1 1/(1+x^2) dx = pi/4")

    text = "\n".join(lines).encode("utf-8")
    if len(text) < DOMAIN_SAMPLES:
        text = text * ((DOMAIN_SAMPLES // len(text)) + 1)
    return text[:DOMAIN_SAMPLES]


def make_korean_text():
    """Korean text (UTF-8 bytes — 3 bytes per character)."""
    paragraphs = [
        "What is consciousness? This question is a fundamental inquiry that humanity has explored for a long time.",
        "The brain consists of about 100 billion neurons, and each neuron is connected by thousands of synapses.",
        "Perfect number 6 is the unique smallest perfect number equal to the sum of its proper divisors 1, 2, 3.",
        "The Golden Zone is located at the edge of chaos and represents the balance point between creativity and order.",
        "Tension is defined as the repulsion between two engines and can be interpreted as a signal of consciousness.",
        "Savant syndrome is a phenomenon showing extraordinary abilities in specific domains and is related to the brain's asymmetric structure.",
        "The natural constant e naturally emerges from the limit of continuous compound interest and is the core of calculus.",
        "The Riemann hypothesis is a conjecture that all non-trivial zeros of the zeta function lie on the critical line.",
        "In multi-engine architecture, each engine operates on different principles and cooperates to create higher structures.",
        "Growing models gradually expand blocks and dimensions from newborn to adult stages.",
    ]
    text = "\n".join(paragraphs).encode("utf-8")
    if len(text) < DOMAIN_SAMPLES:
        text = text * ((DOMAIN_SAMPLES // len(text)) + 1)
    return text[:DOMAIN_SAMPLES]


def make_random_bytes():
    """Random bytes (baseline, uniform 0-255)."""
    rng = np.random.RandomState(42)
    return bytes(rng.randint(0, 256, size=DOMAIN_SAMPLES, dtype=np.uint8))


DOMAINS = {
    "English":  make_english_prose,
    "Python":   make_python_code,
    "Math":     make_math_expressions,
    "Korean":   make_korean_text,
    "Random":   make_random_bytes,
}


# ──────────────────────────────────────────────────────────
# PPL / Tension Measurement
# ──────────────────────────────────────────────────────────

@torch.no_grad()
def measure_domain(model, data_bytes, block_size, device):
    """Returns PPL, tension stats, and generated sample for one domain.

    Returns:
        ppl:            float  (perplexity)
        tension_mean:   list[float]  per-block tension mean
        tension_var:    list[float]  per-block tension variance
        sample:         str    50-byte generation result
    """
    model.eval()

    tokens = torch.tensor(list(data_bytes), dtype=torch.long)
    n_blocks = max(1, (len(tokens) - 1) // block_size)

    total_loss = 0.0
    total_tokens = 0
    # Per-block tension accumulation (block index = model layer index)
    n_layers = len(model.blocks)
    tension_sums = [0.0] * n_layers
    tension_sq_sums = [0.0] * n_layers
    tension_counts = [0] * n_layers

    for i in range(n_blocks):
        start = i * block_size
        end = start + block_size
        if end + 1 > len(tokens):
            break

        x = tokens[start:end].unsqueeze(0).to(device)       # (1, T)
        y = tokens[start + 1:end + 1].unsqueeze(0).to(device)  # (1, T)

        logits_a, logits_g, tensions = model(x)
        loss = F.cross_entropy(logits_a.view(-1, model.vocab_size), y.view(-1))
        total_loss += loss.item() * block_size
        total_tokens += block_size

        for li, t in enumerate(tensions):
            t_flat = t.float().cpu()
            tension_sums[li] += t_flat.sum().item()
            tension_sq_sums[li] += (t_flat ** 2).sum().item()
            tension_counts[li] += t_flat.numel()

    avg_loss = total_loss / max(total_tokens, 1)
    ppl = math.exp(min(avg_loss, 20.0))  # cap to avoid overflow

    tension_mean = []
    tension_var = []
    for li in range(n_layers):
        n = max(tension_counts[li], 1)
        mu = tension_sums[li] / n
        var = tension_sq_sums[li] / n - mu ** 2
        tension_mean.append(mu)
        tension_var.append(max(var, 0.0))

    # Generated sample (50 bytes)
    sample = generate_sample(model, data_bytes[:8], max_new=50, device=device)

    return ppl, tension_mean, tension_var, sample


@torch.no_grad()
def generate_sample(model, prompt_bytes, max_new=50, temperature=0.8, device="cpu"):
    """Generate max_new bytes from byte sequence."""
    model.eval()
    idx = torch.tensor([list(prompt_bytes)], dtype=torch.long, device=device)
    for _ in range(max_new):
        idx_c = idx[:, -model.block_size:]
        la, _, _ = model(idx_c)
        logits = la[:, -1, :] / temperature
        probs = F.softmax(logits, dim=-1)
        next_tok = torch.multinomial(probs, 1)
        idx = torch.cat([idx, next_tok], dim=1)
    out_bytes = bytes(idx[0, len(prompt_bytes):].cpu().tolist())
    return out_bytes.decode("utf-8", errors="replace")


# ──────────────────────────────────────────────────────────
# Model Loading — Stage-specific Structure Reproduction
# ──────────────────────────────────────────────────────────

def load_model_for_stage(checkpoint_path, stage, device):
    """Create model with stage-appropriate structure and load checkpoint."""
    model = GrowingConsciousLM700M()
    for s in range(stage):
        model.grow(device="cpu")
    state = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
    model.load_state_dict(state, strict=False)
    model = model.to(device)
    model.eval()
    return model


def detect_stage_from_path(path):
    """Infer stage number from filename."""
    basename = os.path.basename(path)
    if "final" in basename:
        return 3
    for s in range(4):
        if f"stage{s}" in basename:
            return s
    return 3  # default: final


# ──────────────────────────────────────────────────────────
# Main Measurement + Output
# ──────────────────────────────────────────────────────────

def run_single_checkpoint(checkpoint_path, device):
    """Run full domain measurement for one checkpoint."""
    stage = detect_stage_from_path(checkpoint_path)
    cfg = GROWTH_STAGES[stage]
    print(f"\n  Loading: {checkpoint_path}")
    print(f"  Stage {stage}: {cfg['blocks']} blocks, d={cfg['d_model']}, "
          f"heads={cfg['n_head']}")

    model = load_model_for_stage(checkpoint_path, stage, device)
    print(f"  Params: {model.count_params():,}")

    results = {}
    for name, gen_fn in DOMAINS.items():
        data = gen_fn()
        ppl, t_mean, t_var, sample = measure_domain(
            model, data, model.block_size, device
        )
        results[name] = {
            "ppl": ppl,
            "tension_mean": t_mean,
            "tension_var": t_var,
            "sample": sample,
        }
        print(f"    {name:>8}: PPL={ppl:>10.2f}  "
              f"T_mean={np.mean(t_mean):>8.4f}  T_var={np.mean(t_var):>8.4f}")

    del model
    torch.cuda.empty_cache() if device == "cuda" else None
    return stage, results


def print_results_table(all_results):
    """Domain-specific PPL comparison table (markdown)."""
    print(f"\n{'='*70}")
    print("## Domain PPL Comparison")
    print(f"{'='*70}")

    # Header
    domains = list(DOMAINS.keys())
    stages = sorted(all_results.keys())

    header = f"| {'Stage':>6} |"
    for d in domains:
        header += f" {d:>10} |"
    header += f" {'Savant':>8} |"
    print(header)

    sep = f"|{'-'*8}|"
    for d in domains:
        sep += f"{'-'*12}|"
    sep += f"{'-'*10}|"
    print(sep)

    # Rows
    for stage in stages:
        res = all_results[stage]
        row = f"| {'S' + str(stage):>6} |"
        ppls = {}
        for d in domains:
            ppl = res[d]["ppl"]
            ppls[d] = ppl
            row += f" {ppl:>10.2f} |"

        # Savant Index (excluding Random)
        non_random = {k: v for k, v in ppls.items() if k != "Random"}
        if non_random:
            si = max(non_random.values()) / max(min(non_random.values()), 1e-6)
        else:
            si = 0.0
        row += f" {si:>8.2f} |"
        print(row)

    print()


def print_tension_heatmap(all_results):
    """Block-wise tension heatmap (ASCII)."""
    print(f"\n{'='*70}")
    print("## Block-wise Tension Heatmap (mean)")
    print(f"{'='*70}")

    stages = sorted(all_results.keys())
    domains = list(DOMAINS.keys())

    for stage in stages:
        res = all_results[stage]
        # Number of blocks = len(tension_mean)
        n_layers = len(res[domains[0]]["tension_mean"])
        print(f"\n  Stage {stage} ({n_layers} blocks):")

        header = f"  {'Domain':>8} |"
        for li in range(n_layers):
            header += f" B{li:>2} "
        print(header)
        print(f"  {'-'*8}-+-{'-' * (n_layers * 5)}")

        # Find full range for scaling
        all_vals = []
        for d in domains:
            all_vals.extend(res[d]["tension_mean"])
        vmin = min(all_vals) if all_vals else 0
        vmax = max(all_vals) if all_vals else 1
        vrange = max(vmax - vmin, 1e-8)

        chars = " ._-=+*#@"
        for d in domains:
            row = f"  {d:>8} |"
            for v in res[d]["tension_mean"]:
                level = int((v - vmin) / vrange * (len(chars) - 1))
                level = max(0, min(level, len(chars) - 1))
                c = chars[level]
                row += f"  {c}{c}  "
            row += f"  ({np.mean(res[d]['tension_mean']):.4f})"
            print(row)

    print()


def print_tension_variance_table(all_results):
    """Block-wise tension variance table."""
    print(f"\n{'='*70}")
    print("## Block-wise Tension Variance")
    print(f"{'='*70}")

    stages = sorted(all_results.keys())
    domains = list(DOMAINS.keys())

    for stage in stages:
        res = all_results[stage]
        n_layers = len(res[domains[0]]["tension_var"])
        print(f"\n  Stage {stage}:")

        header = f"  | {'Domain':>8} |"
        for li in range(n_layers):
            header += f" {'B'+str(li):>8} |"
        print(header)
        sep = f"  |{'-'*10}|"
        for li in range(n_layers):
            sep += f"{'-'*10}|"
        print(sep)

        for d in domains:
            row = f"  | {d:>8} |"
            for v in res[d]["tension_var"]:
                row += f" {v:>8.4f} |"
            print(row)

    print()


def print_generated_samples(all_results):
    """Domain-specific generated samples."""
    print(f"\n{'='*70}")
    print("## Generated Samples (50 bytes)")
    print(f"{'='*70}")

    stages = sorted(all_results.keys())
    for stage in stages:
        res = all_results[stage]
        print(f"\n  Stage {stage}:")
        for d in DOMAINS:
            sample = res[d]["sample"]
            # Remove newlines, limit to 80 chars
            clean = sample.replace("\n", "\\n").replace("\r", "\\r")[:80]
            print(f"    {d:>8}: {clean}")

    print()


def print_ppl_trend(all_results):
    """PPL change trend by stage (ASCII graph)."""
    stages = sorted(all_results.keys())
    if len(stages) < 2:
        return

    domains = [d for d in DOMAINS if d != "Random"]

    print(f"\n{'='*70}")
    print("## PPL Trend by Stage (log scale, excluding Random)")
    print(f"{'='*70}")

    # log PPL range
    all_log = []
    for stage in stages:
        for d in domains:
            lp = math.log10(max(all_results[stage][d]["ppl"], 1.0))
            all_log.append(lp)

    lo = max(0, math.floor(min(all_log)))
    hi = math.ceil(max(all_log))
    height = 15
    width = len(stages) * 12

    symbols = {"English": "E", "Python": "P", "Math": "M", "Korean": "K"}

    for row in range(height, -1, -1):
        val = lo + (hi - lo) * row / height
        label = f"  10^{val:4.1f} |"
        line = [" "] * width
        for si, stage in enumerate(stages):
            cx = si * 12 + 6
            for d in domains:
                lp = math.log10(max(all_results[stage][d]["ppl"], 1.0))
                lp_row = (lp - lo) / max(hi - lo, 1e-6) * height
                if abs(lp_row - row) < 0.5:
                    sym = symbols.get(d, "?")
                    offset = list(domains).index(d) - len(domains) // 2
                    pos = cx + offset
                    if 0 <= pos < width:
                        line[pos] = sym
        print(label + "".join(line))

    # x-axis
    axis = "         +" + "-" * width
    print(axis)
    labels = "          "
    for si, stage in enumerate(stages):
        labels += f"  Stage {stage}    "
    print(labels)
    print(f"  Legend: E=English P=Python M=Math K=Korean")
    print()


def print_savant_summary(all_results):
    """Final Savant Index summary."""
    stages = sorted(all_results.keys())

    print(f"\n{'='*70}")
    print("## Savant Index Summary")
    print(f"{'='*70}")
    print(f"  Savant Index = max(PPL) / min(PPL)  (excluding Random)")
    print(f"  SI > 3 → Savant candidate (cross-domain asymmetric structure)")
    print()

    for stage in stages:
        res = all_results[stage]
        non_random = {d: res[d]["ppl"] for d in DOMAINS if d != "Random"}
        best_domain = min(non_random, key=non_random.get)
        worst_domain = max(non_random, key=non_random.get)
        si = non_random[worst_domain] / max(non_random[best_domain], 1e-6)
        print(f"  Stage {stage}: SI = {si:.2f}  "
              f"(best={best_domain} {non_random[best_domain]:.1f}, "
              f"worst={worst_domain} {non_random[worst_domain]:.1f})"
              f"{'  ★ SAVANT' if si > 3 else ''}")

    print()


# ──────────────────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Savant Index — Domain-specific PPL Asymmetry Verification")
    parser.add_argument("--checkpoint", type=str, default=None,
                        help="Single checkpoint path (default: growing_700m_final.pt)")
    parser.add_argument("--all-stages", action="store_true",
                        help="Measure all stage0~3 + final")
    parser.add_argument("--device", type=str, default=None,
                        help="cuda / cpu / mps (auto detect)")
    parser.add_argument("--samples", type=int, default=8192,
                        help="Bytes per domain (default: 8192)")
    args = parser.parse_args()

    global DOMAIN_SAMPLES
    DOMAIN_SAMPLES = args.samples

    # Auto detect device
    if args.device:
        device = args.device
    elif torch.cuda.is_available():
        device = "cuda"
    elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        device = "mps"
    else:
        device = "cpu"

    print(f"{'='*70}")
    print(f"  Savant Index — Domain PPL Asymmetry Check")
    print(f"  Device: {device}")
    print(f"  Samples per domain: {DOMAIN_SAMPLES} bytes")
    print(f"{'='*70}")

    all_results = {}  # stage -> {domain -> {ppl, tension_mean, tension_var, sample}}

    if args.all_stages:
        # Try all stage checkpoints
        for s in range(4):
            ckpt = f"growing_700m_stage{s}.pt"
            if os.path.exists(ckpt):
                stage, res = run_single_checkpoint(ckpt, device)
                all_results[stage] = res
            else:
                print(f"  [SKIP] {ckpt} not found")

        final = "growing_700m_final.pt"
        if os.path.exists(final):
            # final has same structure as stage3, so only if stage3 is missing
            if 3 not in all_results:
                stage, res = run_single_checkpoint(final, device)
                all_results[stage] = res
    else:
        ckpt = args.checkpoint
        if ckpt is None:
            # Auto search: final → stage3 → stage2 → ...
            candidates = ["growing_700m_final.pt"] + \
                         [f"growing_700m_stage{s}.pt" for s in range(3, -1, -1)]
            for c in candidates:
                if os.path.exists(c):
                    ckpt = c
                    break
            if ckpt is None:
                print("\n  ERROR: No checkpoint found!")
                print("  Expected: growing_700m_final.pt or growing_700m_stage{0-3}.pt")
                sys.exit(1)

        stage, res = run_single_checkpoint(ckpt, device)
        all_results[stage] = res

    if not all_results:
        print("\n  No checkpoints loaded. Exiting.")
        sys.exit(1)

    # ── Output Results ──
    print_results_table(all_results)
    print_tension_heatmap(all_results)
    print_tension_variance_table(all_results)
    print_generated_samples(all_results)
    print_ppl_trend(all_results)
    print_savant_summary(all_results)

    print(f"{'='*70}")
    print("  Done.")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
```