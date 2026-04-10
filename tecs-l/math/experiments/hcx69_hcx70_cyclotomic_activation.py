"""
H-CX-69: Cyclotomic polynomial activation function
H-CX-70: phi(n)-bottleneck + Phi_n expansion self-organization

Uses numpy for speed. SPSA optimiser (2 forward passes per step).
"""

import math
import time
import sys
import numpy as np

RNG = np.random.default_rng(0)


# ── activations ───────────────────────────────────────────────────────────────

def relu(x):
    return np.maximum(0.0, x)

def gelu(x):
    return 0.5 * x * (1 + np.tanh(0.7978845 * (x + 0.044715 * x**3)))

def silu(x):
    return x / (1 + np.exp(-np.clip(x, -30, 30)))

def phi6(x):
    """Phi_6(x) = x^2 - x + 1  (6th cyclotomic polynomial, clipped for stability)"""
    xc = np.clip(x, -5.0, 5.0)
    return xc*xc - xc + 1.0

def phi6_norm(x):
    """(x^2 - x + 1) / (1 + x^2)  — bounded in (0, 1.25], always positive"""
    return (x*x - x + 1.0) / (1.0 + x*x)

def phi6_shifted(x):
    """x^2 - x = x(x-1)  — zero-centered, roots at 0 and 1, clipped"""
    xc = np.clip(x, -5.0, 5.0)
    return xc*xc - xc

ACTIVATIONS = {
    "relu":         relu,
    "gelu":         gelu,
    "silu":         silu,
    "phi6":         phi6,
    "phi6_norm":    phi6_norm,
    "phi6_shifted": phi6_shifted,
}


# ── cyclotomic polynomials for experiment 2 ───────────────────────────────────

def cyclotomic(n, x):
    """Phi_n(x) applied element-wise with input clipping for stability."""
    xc = np.clip(x, -3.0, 3.0)
    if   n == 1: return xc - 1
    elif n == 2: return xc + 1
    elif n == 3: return xc*xc + xc + 1
    elif n == 4: return xc*xc + 1
    elif n == 5: return xc**4 + xc**3 + xc**2 + xc + 1
    elif n == 6: return xc*xc - xc + 1
    elif n == 7: return xc**6 + xc**5 + xc**4 + xc**3 + xc**2 + xc + 1
    elif n == 8: return xc**4 + 1
    else:
        phi_n = euler_totient(n)
        return xc**phi_n


def euler_totient(n):
    result = n
    temp = n
    p = 2
    while p * p <= temp:
        if temp % p == 0:
            while temp % p == 0:
                temp //= p
            result -= result // p
        p += 1
    if temp > 1:
        result -= result // temp
    return result


# ── layer norm ────────────────────────────────────────────────────────────────

def layer_norm(x):
    mu  = x.mean()
    std = x.std() + 1e-5
    return (x - mu) / std


# ── flat-param model ──────────────────────────────────────────────────────────
# All weights stored in one numpy array self.p for easy SPSA gradient.

class TinyLM:
    """
    N-block residual MLP language model.
    Architecture: embed -> [LN->W1->act->W2->+residual] x n_blocks -> head
    """
    def __init__(self, n_blocks, d_model, d_hidden, vocab, act_fn, rng):
        self.n_blocks = n_blocks
        self.d_model  = d_model
        self.d_hidden = d_hidden
        self.vocab    = vocab
        self.act_fn   = act_fn

        # parameter sizes
        sizes = [vocab * d_model]                    # embed
        for _ in range(n_blocks):
            sizes += [d_hidden * d_model, d_hidden,  # W1, b1
                      d_model  * d_hidden, d_model]  # W2, b2
        sizes += [vocab * d_model, vocab]            # head, head_bias
        self.sizes = sizes
        self.off   = np.concatenate([[0], np.cumsum(sizes)]).tolist()
        self.total = self.off[-1]

        self.p = rng.normal(0, 0.02, self.total)

    def forward(self, tok):
        p  = self.p
        dm = self.d_model
        dh = self.d_hidden
        V  = self.vocab
        o  = self.off

        x = p[o[0] + tok*dm : o[0] + (tok+1)*dm].copy()

        for i in range(self.n_blocks):
            b   = 1 + i*4
            W1  = p[o[b]   : o[b]   + dh*dm].reshape(dh, dm)
            b1  = p[o[b+1] : o[b+1] + dh]
            W2  = p[o[b+2] : o[b+2] + dm*dh].reshape(dm, dh)
            b2  = p[o[b+3] : o[b+3] + dm]

            h = layer_norm(x)
            h = W1 @ h + b1
            h = self.act_fn(h)
            h = W2 @ h + b2
            x = x + h

        hi   = 1 + self.n_blocks*4
        head = p[o[hi]   : o[hi]   + V*dm].reshape(V, dm)
        hb   = p[o[hi+1] : o[hi+1] + V]
        return head @ x + hb

    def loss(self, tok, tgt):
        logits = self.forward(tok)
        m = logits.max()
        lse = m + np.log(np.exp(logits - m).sum())
        return -(logits[tgt] - lse)

    def param_count(self):
        return self.total


class PhiBLM:
    """
    N-block model with phi(n)-bottleneck FFN.
    Bottleneck dim = max(2, phi(n)*d_model//n).
    Activation in bottleneck: Phi_n(x).
    """
    def __init__(self, n, d_model, vocab, rng):
        self.n      = n
        self.d_model = d_model
        self.vocab   = vocab
        phi_n        = euler_totient(n)
        self.d_bk    = max(2, phi_n * d_model // n)
        dm = d_model
        db = self.d_bk
        V  = vocab

        sizes = [V * dm]
        for _ in range(n):
            sizes += [db * dm, db,
                      dm * db, dm]
        sizes += [V * dm, V]
        self.sizes = sizes
        self.off   = np.concatenate([[0], np.cumsum(sizes)]).tolist()
        self.total = self.off[-1]
        self.p     = rng.normal(0, 0.02, self.total)

    def forward(self, tok):
        p  = self.p
        dm = self.d_model
        db = self.d_bk
        V  = self.vocab
        n  = self.n
        o  = self.off

        x = p[o[0] + tok*dm : o[0] + (tok+1)*dm].copy()

        for i in range(n):
            b   = 1 + i*4
            Wd  = p[o[b]   : o[b]   + db*dm].reshape(db, dm)
            bd  = p[o[b+1] : o[b+1] + db]
            Wu  = p[o[b+2] : o[b+2] + dm*db].reshape(dm, db)
            bu  = p[o[b+3] : o[b+3] + dm]

            h = layer_norm(x)
            h = Wd @ h + bd
            h = cyclotomic(n, h)
            h = Wu @ h + bu
            x = x + h

        hi   = 1 + n*4
        head = p[o[hi]   : o[hi]   + V*dm].reshape(V, dm)
        hb   = p[o[hi+1] : o[hi+1] + V]
        return head @ x + hb

    def loss(self, tok, tgt):
        logits = self.forward(tok)
        m = logits.max()
        lse = m + np.log(np.exp(logits - m).sum())
        return -(logits[tgt] - lse)

    def param_count(self):
        return self.total


# ── SPSA optimiser ────────────────────────────────────────────────────────────

def spsa_step(model, tok, tgt, lr=0.01, c=0.001, rng=None, clip=1.0):
    """
    SPSA with gradient clipping.
    Uses decayed perturbation c and clipped update for stability.
    """
    p     = model.p
    delta = rng.choice([-1.0, 1.0], size=len(p))

    model.p = p + c * delta
    lp = float(model.loss(tok, tgt))
    model.p = p - c * delta
    lm = float(model.loss(tok, tgt))
    model.p = p.copy()

    # clip loss values to avoid inf propagation
    lp = min(lp, 1e6)
    lm = min(lm, 1e6)

    g = (lp - lm) / (2 * c)
    update = lr * g / (delta + 1e-12)
    # gradient clipping (per-param)
    update = np.clip(update, -clip, clip)
    model.p -= update

    return (lp + lm) / 2.0


def train(model, n_steps, seed, lr=0.01, c=0.001, vocab=64):
    rng = np.random.default_rng(seed + 777)
    losses = []
    for step in range(n_steps):
        tok = int(rng.integers(0, vocab))
        tgt = int(rng.integers(0, vocab))
        # cosine LR decay
        lr_t = lr * 0.5 * (1 + math.cos(math.pi * step / n_steps))
        losses.append(spsa_step(model, tok, tgt, lr=lr_t, c=c, rng=rng, clip=0.5))
    return np.array(losses)


# ── EXPERIMENT 1: H-CX-69 ────────────────────────────────────────────────────

def run_experiment1():
    print("=" * 72)
    print("EXPERIMENT 1: H-CX-69 — Cyclotomic Activation Function")
    print("=" * 72)
    print("Hypothesis: Phi_6(x)=x^2-x+1 as activation improves 6-block models")
    print()

    N_BLOCKS = 6
    D_MODEL  = 32
    D_HIDDEN = 64
    VOCAB    = 64
    N_STEPS  = 300
    SEEDS    = [42, 7]
    LR       = 0.01
    C        = 0.001

    random_baseline = math.log(VOCAB)
    print(f"Architecture: {N_BLOCKS} blocks, d_model={D_MODEL}, d_hidden={D_HIDDEN}, vocab={VOCAB}")
    print(f"Random baseline loss: {random_baseline:.4f}")
    print()

    results = {}

    for act_name, act_fn in ACTIVATIONS.items():
        seed_finals = []
        seed_conv   = []
        seed_gstd   = []
        all_losses  = []

        for seed in SEEDS:
            rng   = np.random.default_rng(seed)
            model = TinyLM(N_BLOCKS, D_MODEL, D_HIDDEN, VOCAB, act_fn, rng)
            losses = train(model, N_STEPS, seed, lr=LR, c=C, vocab=VOCAB)

            final20   = float(losses[-20:].mean())
            thresh    = random_baseline * 0.97
            conv_step = int(next((i for i, l in enumerate(losses) if l < thresh), N_STEPS))
            gstd      = float(losses[-50:].std())

            seed_finals.append(final20)
            seed_conv.append(conv_step)
            seed_gstd.append(gstd)
            all_losses.append(losses)

        avg_final = sum(seed_finals) / len(seed_finals)
        avg_conv  = sum(seed_conv)   / len(seed_conv)
        avg_gstd  = sum(seed_gstd)   / len(seed_gstd)

        results[act_name] = {
            "final_loss": avg_final,
            "conv_step":  avg_conv,
            "gnorm_std":  avg_gstd,
            "per_seed":   seed_finals,
            "all_losses": all_losses,
        }
        print(f"  [{act_name:14s}] final={avg_final:.4f}  conv={avg_conv:5.1f}  gstd={avg_gstd:.4f}  seeds={[round(v,4) for v in seed_finals]}")

    print()
    print("-- Summary Table (sorted by final loss, lower=better) --")
    print(f"{'Activation':<16} {'AvgLoss':>9} {'ConvStep':>10} {'GradStd':>9} {'Seed42':>8} {'Seed7':>8}")
    print("-" * 65)
    sorted_acts = sorted(results.items(), key=lambda kv: kv[1]["final_loss"])
    for act_name, r in sorted_acts:
        print(f"{act_name:<16} {r['final_loss']:>9.4f} {r['conv_step']:>10.1f} {r['gnorm_std']:>9.4f} {r['per_seed'][0]:>8.4f} {r['per_seed'][1]:>8.4f}")

    print()
    print("-- ASCII Loss Curves (avg seeds, sampled every 30 steps, step 0..300) --")
    WIDTH = 28
    for act_name, r in sorted_acts:
        arr   = np.stack(r["all_losses"]).mean(axis=0)
        samps = arr[::30]
        lo, hi = samps.min(), samps.max()
        def bar(v):
            if hi == lo: return "#" * WIDTH
            frac = (v - lo) / (hi - lo)
            return "#" * max(1, int((1 - frac) * WIDTH))
        row = "".join(f"|{bar(v)}" for v in samps) + "|"
        print(f"  {act_name:<14} {row}  final={arr[-1]:.4f}")

    print()
    best  = sorted_acts[0][0]
    worst = sorted_acts[-1][0]
    phi6_rank  = next(i for i,(k,_) in enumerate(sorted_acts) if k=="phi6") + 1
    phi6n_rank = next(i for i,(k,_) in enumerate(sorted_acts) if k=="phi6_norm") + 1
    phi6s_rank = next(i for i,(k,_) in enumerate(sorted_acts) if k=="phi6_shifted") + 1
    total = len(sorted_acts)

    best_base = min(results[k]["final_loss"] for k in ["relu","gelu","silu"])
    best_base_name = min(["relu","gelu","silu"], key=lambda k: results[k]["final_loss"])
    phi6_delta  = results["phi6"]["final_loss"]  - best_base
    phi6n_delta = results["phi6_norm"]["final_loss"] - best_base

    print(f"Best overall:         {best}  (loss={results[best]['final_loss']:.4f})")
    print(f"Worst overall:        {worst}  (loss={results[worst]['final_loss']:.4f})")
    print(f"Best baseline:        {best_base_name}  (loss={best_base:.4f})")
    print(f"phi6 rank:            {phi6_rank}/{total}  delta vs best_baseline={phi6_delta:+.4f}")
    print(f"phi6_norm rank:       {phi6n_rank}/{total}  delta vs best_baseline={phi6n_delta:+.4f}")
    print(f"phi6_shifted rank:    {phi6s_rank}/{total}")

    return results


# ── EXPERIMENT 2: H-CX-70 ────────────────────────────────────────────────────

def run_experiment2():
    print()
    print("=" * 72)
    print("EXPERIMENT 2: H-CX-70 — phi(n)-bottleneck Self-Organization")
    print("=" * 72)
    print("Hypothesis: bottleneck=phi(n)*d/n + Phi_n activation improves n-block models")
    print()

    D_MODEL  = 24
    VOCAB    = 64
    N_STEPS  = 300
    SEEDS    = [42, 7]
    N_VALUES = [3, 4, 5, 6, 7, 8]
    LR       = 0.01
    C        = 0.001

    print(f"Architecture: d_model={D_MODEL}, vocab={VOCAB}, {N_STEPS} steps, seeds={SEEDS}")
    print()
    print("-- Bottleneck configuration per n --")
    print(f"{'n':>3} {'phi(n)':>7} {'bk_dim':>7} {'std_4x':>8} {'bk/std':>8}")
    print("-" * 38)
    for n in N_VALUES:
        phi_n = euler_totient(n)
        bk    = max(2, phi_n * D_MODEL // n)
        std_h = 4 * D_MODEL
        print(f"{n:>3} {phi_n:>7} {bk:>7} {std_h:>8} {bk/std_h:>8.3f}")
    print()

    results = {}

    for n in N_VALUES:
        row = {}
        for variant in ["standard", "phi_bottleneck"]:
            seed_finals = []
            seed_params = []
            for seed in SEEDS:
                rng = np.random.default_rng(seed)
                if variant == "standard":
                    model  = TinyLM(n, D_MODEL, 4*D_MODEL, VOCAB, gelu, rng)
                    losses = train(model, N_STEPS, seed, lr=LR, c=C, vocab=VOCAB)
                else:
                    model  = PhiBLM(n, D_MODEL, VOCAB, rng)
                    losses = train(model, N_STEPS, seed, lr=LR, c=C, vocab=VOCAB)
                seed_finals.append(float(losses[-20:].mean()))
                seed_params.append(model.param_count())
            avg_f = sum(seed_finals) / len(seed_finals)
            avg_p = sum(seed_params) / len(seed_params)
            row[variant] = {"final_loss": avg_f, "param_count": int(avg_p), "per_seed": seed_finals}
            short = "std" if variant=="standard" else "phi"
            print(f"  n={n} [{short}] loss={avg_f:.4f}  params={int(avg_p)}  seeds={[round(v,4) for v in seed_finals]}")
        results[n] = row

    print()
    print("-- Standard vs Phi-Bottleneck (n, phi(n), bk_dim | losses | delta | params | param_ratio) --")
    print(f"{'n':>3} {'phi(n)':>7} {'bk':>5} | {'std_loss':>9} {'phi_loss':>9} {'delta':>8} | {'std_p':>7} {'phi_p':>7} {'ratio':>7}")
    print("-" * 72)
    for n in N_VALUES:
        phi_n = euler_totient(n)
        bk    = max(2, phi_n * D_MODEL // n)
        std   = results[n]["standard"]
        phi   = results[n]["phi_bottleneck"]
        delta = phi["final_loss"] - std["final_loss"]
        ratio = phi["param_count"] / std["param_count"]
        print(f"{n:>3} {phi_n:>7} {bk:>5} | {std['final_loss']:>9.4f} {phi['final_loss']:>9.4f} {delta:>+8.4f} | {std['param_count']:>7} {phi['param_count']:>7} {ratio:>7.3f}")

    print()
    print("-- Loss/Param efficiency (loss per param *1e4, lower=better) --")
    print(f"{'n':>3} | {'std_eff':>12} {'phi_eff':>12} {'phi_better?':>12}")
    print("-" * 44)
    phi_wins = 0
    for n in N_VALUES:
        std = results[n]["standard"]
        phi = results[n]["phi_bottleneck"]
        se  = std["final_loss"] / std["param_count"] * 1e4
        pe  = phi["final_loss"] / phi["param_count"] * 1e4
        win = "YES" if pe < se else "no"
        if pe < se: phi_wins += 1
        print(f"{n:>3} | {se:>12.5f} {pe:>12.5f} {win:>12}")

    # raw-loss wins
    phi_raw_wins = sum(
        1 for n in N_VALUES
        if results[n]["phi_bottleneck"]["final_loss"] < results[n]["standard"]["final_loss"]
    )

    print()
    print(f"Phi-bottleneck raw loss wins:        {phi_raw_wins}/{len(N_VALUES)}")
    print(f"Phi-bottleneck efficiency wins:      {phi_wins}/{len(N_VALUES)}")

    # n=6 spotlight
    n6s  = results[6]["standard"]
    n6p  = results[6]["phi_bottleneck"]
    d6   = n6p["final_loss"] - n6s["final_loss"]
    phi6_bk = max(2, euler_totient(6) * D_MODEL // 6)
    print()
    print(f"n=6 spotlight (H-CX-70 core target):")
    print(f"  phi(6)={euler_totient(6)}, bottleneck_dim={phi6_bk}  (= phi(6)*{D_MODEL}/6 = 2*{D_MODEL}/6)")
    print(f"  Standard   loss = {n6s['final_loss']:.4f}  params={n6s['param_count']}")
    print(f"  Phi-bk     loss = {n6p['final_loss']:.4f}  params={n6p['param_count']}")
    print(f"  Delta            = {d6:+.4f}  ({'phi-bk better' if d6<0 else 'standard better'})")
    print(f"  Param ratio      = {n6p['param_count']/n6s['param_count']:.3f}")

    return results


# ── MAIN ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    t0 = time.time()
    print(f"H-CX-69 / H-CX-70 Cyclotomic Activation Experiments")
    print(f"Started: {time.strftime('%Y-%m-%d %H:%M:%S')}  Python {sys.version.split()[0]}  numpy {np.__version__}")
    print()

    res1 = run_experiment1()
    res2 = run_experiment2()

    elapsed = time.time() - t0
    print()
    print("=" * 72)
    print(f"Both experiments complete. Total time: {elapsed:.1f}s")
    print("=" * 72)
