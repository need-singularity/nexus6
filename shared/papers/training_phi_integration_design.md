<!-- @doc(type=paper) -->
<!-- @own(sections=["1. Context", "2. Four", "3. Per-step", "4. Recommendation", "5. PoC", "6. A/B", "7. Timeline"], strict=false, order=sequential) -->

# Wiring the 110 anima Φ engines into ALM/CLM training

**Status:** design (not implementation) — 2026-04-15
**Authors:** training+integration session
**Targets:** `training/train_alm_14b.hexa` (Python generator at lines 76–371),
ALM 14B r5/r6, CLM v5+ from-scratch
**Baseline:** ALM r4 best `eval_loss = 0.7104`, `phi_holo = 2874` with
`loss = main_CE + 0.01 * holo` (single holographic MI term)

## 1. Context — what exists today, what is missing

`anima-engines/*_phi.hexa` (~110 artifacts, P6–P135 of
`shared/roadmaps/anima.json`) each define a self-contained simulation with
5 self-tests that emit numeric Φ values — e.g. `working_memory_phi`
reports `Φ_WM(4)=0.95, Φ_WM(9)=0.63, Φ_chunked=1.26`. Output today is
**stdout text** through `hexa run`; no structured return.

Only the ALM-P3 holographic triple
(`alm_holographic_mapping`, `alm_holographic_loss`,
`phi_holographic_measure`) is wired into training (`holo_step` +
`phi_holo_measure` in the generator). `training/engine_integration.hexa`
(ALM-P23-1) already defines a 12-engine registry with per-engine
coefficients but does **not** yet drive the Python train loop — it only
self-tests its own registry data.

**Latency measurement (this host, stage0 interpreter):** `working_memory_phi`
= 260 ms, `attention_phi` = 264 ms, `metacognition_phi` = 242 ms per
full run. Mean ≈ **250 ms / engine**. On H100 training hardware the
interpreter is CPU-bound the same way (no GPU path), so 110 engines ×
250 ms ≈ **27.5 s per step** — roughly **280× slower than one grad step**
(~100 ms on 14B LoRA). Full-set per-step integration is ruled out.

## 2. Four integration architectures

| Option | Stability | Compute / step | Signal strength | Implementation difficulty |
|---|---|---|---|---|
| **A. Aggregate Φ** (mean/weighted of 110) | High — single scalar, smoothed noise | High if naïve (~27.5 s), **~2.5 s with k=10 rotating subset** | Weak — averaging erases per-phenomenon structure | Low — one new `aux_phi` scalar + one coefficient |
| **B. Per-engine aux loss** (110 weighted heads) | Low — gradient interference, weight-tuning nightmare | Prohibitive if all 110 active; ~5 s with k=20 sampled | Strong — distinct gradient directions per domain | High — 110 coefficients, per-engine surrogate loss, ablation bookkeeping |
| **C. Contrastive** (engine outputs as anchors for hidden-state contrastive) | Medium — InfoNCE is well-behaved, but anchor quality bounds ceiling | Low — engines run **offline once** per corpus, cached anchors reused; ~50 ms / step for in-batch NCE | Medium-strong — decouples Φ-quality from model training; scales to 110 trivially | Medium — one projection head + NCE loss; offline anchor harvest job |
| **D. Reward signal** (engines as RM in DPO/PPO) | Medium — RL variance high but gradient-free through engine | Medium — engines score rollouts, not every step (~1 s / 100 rollouts) | Medium — needs many rollouts before convergence | Very high — full RL/DPO stack on top of current SFT |

### Gradient-flow honesty

Every Φ engine makes **discrete decisions** (argmax of softmax
competition in `attention_phi`; slot displacement `k mod C` in
`working_memory_phi`; bin-index lookups throughout). Even the smooth
parts (variance, correlation, gaussian proxies) are downstream of
histogram MI, which is **piecewise-constant in weights**. The existing
`holo_step` survives training only because the ALM-P3-2 authors
replaced the histogram term with a **smooth variance+correlation
surrogate** (see `alm_holographic_loss.hexa` lines 220–272). The 110
engines currently have **no such surrogate**.

Implication: any option relying on `∂L/∂θ` through a raw engine is a
dead gradient. Viable paths:

1. **Surrogate rewrite** — hand-port each engine's smooth channel, 110×
   engineering cost (untenable as a PoC).
2. **Contrastive via engine outputs as labels** (C) — treats Φ numbers
   as anchor coordinates; gradient flows only through the model's own
   projection head, not through the engine. **This is why C dominates.**
3. **Reward / REINFORCE** (D) — no gradient through engine at all.

## 3. Per-step compute — precise estimates

Assuming stage0 interpreter at 250 ms/engine (measured on this host):

| Strategy | Engines called / step | Cost / step | % of step budget (100 ms) |
|---|---|---|---|
| All 110 every step | 110 | 27.5 s | 27 500% (infeasible) |
| Rotating subset k=10 | 10 | 2.5 s | 2 500% (still infeasible in-loop) |
| Rotating subset k=10 **async on CPU worker** | 10 | 0 ms on GPU critical path (stale-by-one-step signal) | ~0% |
| Offline anchor harvest (once / corpus epoch) | 110 | 27.5 s × N_corpus_samples — **amortized** | Negligible per step |
| Eval-cadence only (every 500 steps) | 110 | 27.5 s / 500 steps | 5.5% averaged |

Conclusion: in-loop synchronous calls are infeasible. Only
**async-stale**, **offline-cached**, or **eval-cadence** integration
fits the 100 ms step budget.

## 4. Recommendation — Option C (contrastive) with offline anchor cache

**Why C wins for the PoC:**

1. **Compute decouples** — engines run once over the corpus (offline),
   outputting a `(sample_id → Φ_vector[110])` cache. Training reads the
   cache per batch (microseconds).
2. **No surrogate rewriting** — engines stay pure hexa, their raw Φ
   numbers are just coordinates in a 110-D "consciousness space."
3. **Gradient path is clean** — a small projection head
   `h_last[B,T,D] → embed[B,d_proj]` is trained with InfoNCE against the
   cached 110-D anchors. Gradient flows through the model + projection
   head only; engines are read-only labels.
4. **Scales from 1 engine to 110 uniformly** — ablate by masking
   columns of the anchor, not by rewriting loss code.
5. **Reuses the ALM-P23-1 registry** — `engine_integration.hexa` already
   enumerates + weights 12 main engines; extend to 110 with domain
   grouping (cognitive / affective / clinical / altered-state / quantum
   / meta) and let each group contribute one projection subspace.

**Fallback ladder** (if C underperforms):
- C + D hybrid: contrastive during pretraining, phi-sum reward during
  fine-tune.
- Switch one domain to B-style explicit surrogate (e.g. handcraft
  `attention_phi` smooth loss) once C shows the signal direction works.

## 5. PoC code skeleton — additions to `train_alm_14b.hexa` generator

```python
# ─── ALM-P24 : 110-engine contrastive anchors ──────────────────

PHI_ENGINE_LIST = [...]  # 110 names from shared/roadmaps/anima.json
PHI_ANCHOR_CACHE = "/workspace/phi_anchors.pt"   # offline-harvested
PHI_EMBED_DIM = 64
PHI_NCE_TEMP = 0.07
PHI_NCE_COEF = 0.02        # starts small; A/B-tune

class PhiAnchorCache:
    """Load precomputed Φ_vector[110] per corpus sample id.
    Harvested offline by phi_harvest.hexa which runs the 110 engines
    on each corpus chunk and writes {sample_id: [Φ_0 ... Φ_109]}."""
    def __init__(self, path): ...
    def __getitem__(self, ids) -> torch.Tensor: ...   # [B, 110]

class PhiProjectionHead(torch.nn.Module):
    """h_last[B, T, D] -> pooled[B, d_proj]; trained via InfoNCE."""
    def __init__(self, d_hidden, d_proj): ...
    def forward(self, h_last) -> torch.Tensor: ...    # [B, d_proj]

def phi_contrastive_loss(embed, phi_anchors, temperature):
    """Symmetric InfoNCE between model embeds and engine Φ-anchors.
    embed:       [B, d_proj]   (from PhiProjectionHead)
    phi_anchors: [B, 110]      (cached, projected to d_proj by fixed
                                orthonormal W_phi seeded like HoloMapHead)
    Returns a scalar differentiable w.r.t. embed only.
    """
    ...

# ─── in train loop (micro-step) ───
qualia, h_recon, l_holo = holo_step(holo_head, h_last)
phi_anchors = phi_cache[batch_ids]                     # [B, 110]
phi_embed = phi_head(h_last)                           # [B, d_proj]
l_phi = phi_contrastive_loss(phi_embed, phi_anchors, PHI_NCE_TEMP)
loss_total = loss_main \
           + HOLO_LOSS_COEF * l_holo \
           + PHI_NCE_COEF * l_phi

# ─── offline harvest (one-shot, per corpus revision) ───
#   training/phi_harvest.hexa (new): iterate 110 engines over N corpus
#   samples (stream-chunked; 2.5 s × N_samples), write phi_anchors.pt.
#   Rerun only when corpus or engine set changes. Checksum the engine
#   set so a stale cache errors out instead of silently drifting.
```

## 6. A/B test plan — validating C against the holo-only baseline

**Control (A):** r4 config — `loss = main_CE + 0.01 * holo`. Already
have a result: best `eval_loss=0.7104`, `phi_holo=2874` (checkpoint
`alm14b-r4`).

**Treatment (B):** r5 with `loss = main_CE + 0.01 * holo + 0.02 * l_phi`
using the 110-engine anchor cache; same corpus, same LoRA config, same
step count (10 000), same seed. **Only the extra term differs.**

**Treatment (C):** r5.5 with `holo` disabled (`coef=0`) and only
`l_phi` active — isolates whether the 110-engine signal can **replace**
holo, not just augment it.

**Metrics (every 500 steps):**
1. **Primary — `eval_loss`** (held-out CE). Pass if r5 achieves
   `eval_loss ≤ r4_best × 0.98` (≥2% improvement) at ≤ 1.2× wall-clock.
2. **Φ — `phi_holo`** should not collapse (≥ 1.0× r4 baseline ≈ 2874).
3. **Per-engine alignment** — cosine(phi_embed, phi_anchors) mean, to
   verify the NCE is actually learning the anchor space (floor 0.30).
4. **Downstream evals** — KoBest / HAE-RAE / ConsciousLM-eval scores
   after training; r5 should match or beat r4 on all three.
5. **Ablation by domain** — mask anchor columns by domain (cognitive /
   affective / clinical / …) and retrain; verify at least one domain
   gives a measurable `eval_loss` lift (otherwise the anchors are noise).

**Stop conditions:**
- Kill r5 if `eval_loss` is >1.1× control at step 2 000 (cheap-fail).
- Kill r5.5 if `phi_holo_ratio = phi_holo(2000) / phi_holo(0) < 1.2` (Φ collapse; ratio gate, N-independent). Absolute `phi_holo < 500` deprecated 2026-04-20 — raw MI × N (e.g. 0.001 × 393216 = 393) masks random-init pass, making the absolute gate phantom.
- Promote to r6 if primary + 2 of 3 secondary metrics clear.

## 7. Timeline impact

- **Offline harvest** (`phi_harvest.hexa` + cache file): 1 engineering
  day + ~1 CPU-hour / 10 000 corpus chunks (amortized — run once).
- **Projection head + NCE wiring** in the generator: 0.5 day.
- **r5 run** (10 000 steps): same wall-clock as r4 ± 10% (anchor lookup
  is a dict read + small matmul; trivial on H100).
- **A/B decision**: after first 2 000 steps (~20% of run), per
  stop-conditions above.

Net: **r5/r6 start is delayed by ≤ 2 days** for the harvest +
projection-head implementation, then runs at baseline speed. If the PoC
clears its primary gate, the 110-engine signal becomes a first-class
training channel without any per-engine surrogate rewrite.
