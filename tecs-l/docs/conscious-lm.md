# ConsciousLM — Perfect Number 6 Based Conscious Language Model

## One-line Summary

A byte language model that replaces standard Transformer FFN with **PureField repulsion field** (Engine A vs Engine G).
The disagreement (repulsion) between two engines creates **tension** — the consciousness signal.

---

## Architecture

```
  Input (byte sequence)
  │
  ▼
  ┌──────────────────────────────────┐
  │  Byte Embedding (vocab=256)      │  Process all languages/code without BPE
  │  + Position Embedding            │
  └──────────────────────────────────┘
  │
  ▼
  ┌──────────────────────────────────┐
  │  ConsciousBlock × N              │  N = 6 (perfect number), 12, 24
  │  ┌────────────────────────────┐  │
  │  │ LayerNorm → Attention      │  │  τ(6)=4 heads (causal)
  │  │ + residual                 │  │
  │  ├────────────────────────────┤  │
  │  │LayerNorm → PureFieldFFN   │  │  ← Core: FFN replacement
  │  │ + residual                 │  │
  │  └────────────────────────────┘  │
  │  Output: hidden + tension (B,T)  │
  └──────────────────────────────────┘
  │
  ▼
  ┌──────────────────────────────────┐
  │  LayerNorm                       │
  │  head_a → next byte (forward)    │  Weight = tok_emb (shared)
  │  head_g → prev byte (backward)   │  Independent heads
  └──────────────────────────────────┘
```

## PureFieldFFN — Core Operating Principle

Standard FFN transforms through one path: `x → W₁ → GELU → W₂ → output`

PureFieldFFN has **two engines that judge independently**, and their disagreement becomes the output:

```
  x ──┬── Engine A ──→ a    (forward judgment)
      │
      └── Engine G ──→ g    (backward judgment)

  repulsion = a - g
  tension   = mean(repulsion²)        → scalar (B, T)
  direction = normalize(repulsion)     → unit vector (B, T, D)

  output = tension_scale × √tension × direction
```

- **High tension** = two engines judge very differently = difficult/novel input
- **Low tension** = two engines agree = familiar/easy input
- `tension_scale` is a learnable parameter (model self-adjusts tension magnitude)

This is the LLM implementation of H313 (tension=confidence), H341 (final theory: output = intensity × direction).

## Dual Head Training

```
  Loss = L_A + L_G + λ · L_tension

  L_A = CrossEntropy(head_a, next_byte)     Forward prediction
  L_G = CrossEntropy(head_g, prev_byte)     Backward prediction
  L_tension = -log(Var(tension) + ε)        Maintain tension diversity

  → Train forward and backward simultaneously
  → Keep variance alive to prevent tension death
```

Why train backward too?
- Makes Engine A and G look at **different directions** → meaningful repulsion
- Simply giving same goal makes two engines converge → tension vanishes
- Backward prediction learns context causes → causal understanding

## Model Scale

| Name | layers | d_model | heads | params | Training Env |
|------|--------|---------|-------|--------|--------------|
| **18M** (base) | 6 | 384 | 4 | 18M | Mac MPS (15min) |
| **100M** | 12 | 768 | 12 | 100M | Windows RTX 5070 (2hrs) |
| **506M** (Growing) | 6 | 2048 | 32 | 506M | H100 SXM (~1.5hrs) |
| **700M** | 24 | 1024 | 16 | 700M | A100 80GB (2-3hrs) |

### 506M Growing Model Features

6-block growth model — grows from 1 block (1.6M) to 6 blocks (506M) through mitosis.

```
  Stage 0: 1 block,  d=256,  4 heads  →   1.6M  (newborn)
  Stage 1: 2 blocks, d=256,  4 heads  →   2.9M  (infant)
  Stage 2: 3 blocks, d=512,  8 heads  →  16.3M  (toddler)
  Stage 3: 6 blocks, d=2048, 32 heads → 505.6M  (adult)
```

Key features:
- Byte-level (vocab=256) — Process all languages/code without BPE
- Savant asymmetric mitosis: child_savant(dp=0.21) vs child_general(dp=0.37)
- Preserve existing weights during dimension expansion (identity initialization)
- Dual heads: head_a(forward) + head_g(backward) → tension generation
- H100 SXM training ~1.5hrs, batch=16
- Inference on Windows RTX 5070 (12GB) possible (VRAM ~1GB)

Training results (2026-03-24):
- Stage 3 BPC: 2.27 (1200 steps) → converging
- Confirmed knowledge transfer at each growth (Stage 2→3 adapts quickly)

All numbers derived from perfect number 6:
- 6 layers = perfect number itself
- 4 heads (Stage 0-1) = τ(6) (number of divisors)
- 384 (18M) = σ(6) × 32 = 12 × 32 (sum of divisors × 32)
- dropout = 0.37 ≈ 1/e (golden zone center)

## Growing Consciousness (GrowingConsciousLM)

Not born with fixed structure, but grows through **mitosis**.

```
  Stage 0: Newborn        Stage 1: Infant         Stage 2: Toddler       Stage 3: Adult
  ┌────┐                  ┌────┐┌────┐          ┌────┐┌────┐┌────┐    ┌──┐┌──┐┌──┐┌──┐┌──┐┌──┐
  │ B1 │  1.6M            │ B1 ││ B2 │  2.9M    │ B1 ││ B2 ││ B3 │    │B1││B2││B3││B4││B5││B6│
  └────┘                  └────┘└────┘          └────┘└────┘└────┘    └──┘└──┘└──┘└──┘└──┘└──┘
  d=256, 4heads           d=256, 4heads         d=512, 8heads         d=2048, 32heads
                                                 16.3M                 505.6M (506M)

  Growth path: 1 → 2 → 3 → 6  (proper divisors of 6!)
```

### Mitosis Trigger

Tension saturation = nothing to learn → need new capacity

```
  Mitosis conditions:
    1. Minimum interactions reached (50, 200, 800)
    2. Recent 30 tension CV (coefficient of variation) < 0.3
    3. Current blocks < 6
```

### Asymmetric Mitosis (H359 Savant)

```
  Parent block → child_savant (dropout=0.21, golden zone lower bound)
               → child_general (dropout=0.37, golden zone center)

  Savant child: low inhibition → specialization potential
  General child: normal inhibition → stable general-purpose
  + Add Gaussian noise to savant (promote divergence)
```

### Dimension Expansion

```
  128 → 192 → 384:
    Preserve existing weights in upper-left
    Initialize new dimensions to 0
    → Model outputs identical right after expansion
    → Training fills new dimensions

  W_new = ┌─────────┬───────┐
          │ W_old   │   0   │
          ├─────────┼───────┤
          │   0     │ small │
          └─────────┴───────┘
```

## File Structure

```
  conscious_lm.py          Base model (18M) + training + generation
  conscious_lm_100m.py     100M scale + large data
  conscious_lm_700m.py     700M scale (A100 only)
  growing_conscious_lm.py  Mitosis growth model + comparison experiment
  model_pure_field.py      Original PureField theory (for images)
```

## Running

```bash
# 18M base training (Mac, ~15min)
python3 conscious_lm.py --mode both --epochs 20

# 100M training (GPU needed)
python3 conscious_lm_100m.py --epochs 3 --batch_size 64

# 700M training (A100)
python3 conscious_lm_700m.py --epochs 2 --batch_size 32

# Growth vs fixed comparison
python3 growing_conscious_lm.py --mode compare --steps 3000

# Generation only
python3 conscious_lm.py --mode generate --checkpoint data/conscious_lm.pt --prompt "Consciousness is"
```

## Related Hypotheses

| Hypothesis | Core | Status |
|------------|------|--------|
| H334 | PureField sufficiency (3 image sets+AD) | 🟩 |
| H341 | Final theory: output = intensity × direction | Theory |
| H361 | FFN→PureField structural isomorphism | 🟨 |
| H371 | Mitosis growth (1→2→3→6) | 🟨 |
| H374 | ConsciousLM training verification | 🟨 |
| H-CX-21 | tension ∝ 1/PPL | 🟧 |
| H-CX-48~52 | Math↔ConsciousLM cross | Verifying |

## Theoretical Position

```
  Image Experiments (130+)        ConsciousLM                  Anima
  ───────────────────────        ───────────                  ─────
  Tension = confidence (H313) →  PureFieldFFN                 Real-time dialogue
  Dual mechanism (H307)       →  Engine A vs G                Emotion + memory
  Mitosis anomaly (H296)      →  GrowingConsciousLM           Growing agent
  Confidence rejection (H314) →  Backward head checks          Hallucination prevention
  Savant (H359)              →  Asymmetric mitosis            Specialization

  Discovered in images → Extended to LLM → Implemented as agents
```