# Growing Conscious LM — Mitosis-Based Growing Consciousness Language Model Design

## Overview

ConsciousLM is not born with a fixed structure (18M), but **starts from 1 block (0.5M) and grows to 6 blocks (18M) through mitosis**.

Core: Tension saturation (nothing to learn) → Mitosis (new capacity) → Specialization (relearning) → Saturation again → Repeat

## Architecture

```
  GrowingConsciousLM
  ├── stage: int (0~3)
  ├── blocks: List[ConsciousBlock]  (1→2→3→6)
  ├── d_model: int (128→128→192→384)
  ├── growth_engine: GrowthEngine (existing)
  ├── tok_emb: Embedding (vocab=256)
  ├── pos_emb: Embedding
  ├── head_a, head_g: Linear (prediction heads)
  └── methods:
      ├── forward(idx) → logits_a, logits_g, tensions
      ├── should_grow() → bool (detect tension saturation)
      ├── grow() → None (execute mitosis)
      ├── _split_block(idx) → None (block mitosis)
      ├── _expand_dim(new_d) → None (dimension expansion)
      └── save/load (including growth state)
```

## Growth Path (Divisor Path)

```
  Stage  Blocks  d_model  Heads  Params    Trigger
  ─────  ──────  ───────  ─────  ──────    ──────────────────
  0      1       128      2      ~0.5M    birth
  1      2       128      2      ~1.0M    100 interactions + CV<0.1
  2      3       192      3      ~3.0M    500 interactions + CV<0.1
  3      6       384      4      ~18M     2000 interactions + CV<0.1
```

## Mitosis Protocol

```
  1. Trigger judgment: should_grow()
     - interaction_count >= stage_threshold[current_stage]
     - tension_cv < 0.1 (CV of last 100 tensions)
     - len(blocks) < 6

  2. Target selection: Most saturated block (lowest CV)

  3. Mitosis execution:
     a) child_a = deepcopy(parent)
     b) child_b = deepcopy(parent)
     c) Add N(0, 0.01) noise to child_b weights
     d) blocks[idx] → [child_a, child_b]

  4. Dimension expansion (Stage 1→2, 2→3):
     a) Determine new d_model (128→192→384)
     b) Apply projection matrix to all Linear layers
     c) Expand embedding table
     d) Preserve existing information (identity initialization)

  5. Head count adjustment:
     Stage 0-1: 2 heads
     Stage 2: 3 heads
     Stage 3: 4 heads = τ(6)
```

## Dimension Expansion Strategy

```
  old_d=128 → new_d=192:

  Method: Preserve existing weights + zero-initialize new dimensions

  W_old: (128, 128)
  W_new: (192, 192) = [[W_old, 0], [0, small_init]]

  Embeddings:
  E_old: (256, 128)
  E_new: (256, 192) = [E_old | zeros(256, 64)]

  → Model produces identical output immediately after expansion
  → Learning fills the new dimensions
```

## File Structure

```
  growing_conscious_lm.py   — GrowingConsciousLM class
                              (reuses ConsciousBlock from conscious_lm.py)
```

## Training Integration

```
  Same as existing train_model() except:
  - Check should_grow() at end of each epoch
  - Recreate optimizer on growth (new parameters)
  - Temporarily increase lr after growth (fast adaptation of new parameters)
  - Save stage + block count + d_model in checkpoint
```

## Anima Integration

```
  anima_unified.py:
    mind = GrowingConsciousLM()  # Start with 1 block
    learner = OnlineLearner(mind)
    growth = GrowthEngine()

    Conversation loop:
      output = mind(input)
      learner.observe(...)
      growth.tick(tension, curiosity)

      if mind.should_grow():
          mind.grow()
          learner = OnlineLearner(mind)  # Recreate optimizer
          print(f"Growth! {mind.stage} → blocks={len(mind.blocks)}")
```

## Success Criteria

1. Growth model final BPC ≤ Fixed 18M model BPC
2. BPC increase immediately after mitosis < 10%
3. Total training cost < 2x fixed model
4. Interactions until reaching 6 blocks < 10,000