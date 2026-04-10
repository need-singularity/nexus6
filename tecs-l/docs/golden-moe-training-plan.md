# Golden MoE Training Plan

## 1. Current Status

### Model Configuration
- **Base Model**: TinyLlama/TinyLlama-1.1B-Chat-v1.0 (1.1B parameters)
- **Number of Experts**: 8, active ratio 62.5% (5/8 Experts active)
- **Inhibition Rate I**: 0.375 (within Golden Zone range [0.213, 0.500])
- **Temperature**: T = e ≈ 2.718 (Boltzmann router)
- **Layers**: All 22 layers MoE conversion complete
- **Intermediate per Expert**: 704 (5632 / 8)

### Training Results (500 steps)
- **PPL**: ~4634 (based on 500 steps)
- **Training Method**: Router-only fine-tuning (Experts frozen)
- **Dataset**: wikitext-2-raw-v1 (train split, partial ~23K samples)
- **Batch Size**: 8, Learning Rate: 1e-4, max_length: 256
- **Results**: Saved to golden-test-finetuned/

### Problem Diagnosis
- PPL 4634 is essentially random output level (cannot generate coherent text)
- Cause 1: 500 steps insufficient for router to learn Expert combinations
- Cause 2: Must learn 22 layers x 8 Experts = 176 router gates simultaneously
- Cause 3: After splitting Dense FFN into 8 parts, direct combination without router breaks output

## 2. Goals

| Phase | PPL Target | Meaning |
|-------|------------|---------|
| Phase 1 | < 1000 | Router begins selecting correct Experts |
| Phase 2 | < 100 | Minimum coherence — maintains sentence structure |
| Phase 3 | < 30 | Approaches original TinyLlama level |
| Phase 4 | < 20 | Practical MoE — speed advantage verifiable |

**Primary Goal**: PPL < 100 (achieve minimum coherence)

## 3. Training Strategy

### 3.1 Increase Steps: 2000 → 5000

Current `finetune_router.py` default `--max-steps` is 500. Increase incrementally:

```bash
# Phase 1: 2000 steps (Estimated time: CPU ~4 hours, GPU ~30 minutes)
python3 finetune_router.py --model golden-test --epochs 3 --max-steps 2000 --lr 3e-4

# Phase 2: 5000 steps (Estimated time: CPU ~10 hours, GPU ~1.5 hours)
python3 finetune_router.py --model golden-test --epochs 5 --max-steps 5000 --lr 1e-4
```

### 3.2 Utilize Full Dataset (23K samples)

Currently using full train split of wikitext-2-raw-v1, filtered to ~23K samples:
- Current: `len(text.strip()) > 10` filter → ~23K valid samples
- 500 steps x batch 8 = 4000 samples used (only ~17% of total)
- 5000 steps x batch 8 = 40000 → 1.7 epochs through full dataset

### 3.3 Learning Rate Scheduling (Code Modification Needed)

```python
# Add scheduler to finetune_router.py
from torch.optim.lr_scheduler import CosineAnnealingLR

scheduler = CosineAnnealingLR(optimizer, T_max=max_steps, eta_min=1e-6)
# Every step: scheduler.step()
```

Expect 2-3x convergence speed improvement with warmup + cosine decay.

### 3.4 Gradient Accumulation (For Memory Constraints)

```python
# Effective batch = batch_size * accumulation_steps = 8 * 4 = 32
accumulation_steps = 4
loss = loss / accumulation_steps
loss.backward()
if steps % accumulation_steps == 0:
    optimizer.step()
    optimizer.zero_grad()
```

## 4. Domain-Specific PPL Measurement — Savant Detection

### 4.1 Purpose

According to Hypothesis 178 (Sylvian fissure deficiency), Expert cross-activation patterns in specific domains correspond to savant abilities. Quantify Expert specialization by measuring domain-separated PPL.

### 4.2 Measurement Domains

| Domain | Data Source | Savant Correspondence |
|--------|-------------|----------------------|
| Math | GSM8K, MATH | Mathematical calculation ability |
| Music | MusicNet descriptions | Absolute pitch, music memory |
| Visual-Spatial | ARC-AGI patterns | Visual pattern recognition |
| Language | WikiText (current) | Basic language ability |
| Calendar | Date-day QA | Calendar calculation ability |

### 4.3 Implementation (`benchmark.py` extension)

```python
def measure_domain_ppl(model, tokenizer, domain="math"):
    """Domain-specific Perplexity — savant specialization measurement"""
    domain_datasets = {
        "math": ("gsm8k", "main", "question"),
        "language": ("wikitext", "wikitext-2-raw-v1", "text"),
        "code": ("codeparrot/github-code", "default", "code"),
    }
    dataset_name, subset, field = domain_datasets[domain]
    dataset = load_dataset(dataset_name, subset, split="test")
    texts = [t[field] for t in dataset if len(str(t[field])) > 50][:100]
    return measure_perplexity(model, tokenizer, texts)

def savant_profile(model, tokenizer):
    """Domain PPL profile → more uneven means more savant-like"""
    ppls = {}
    for domain in ["math", "language", "code"]:
        ppls[domain] = measure_domain_ppl(model, tokenizer, domain)

    # Savant Index = max(PPL) / min(PPL)
    # Higher means domain specialization (savant-like)
    values = list(ppls.values())
    savant_index = max(values) / min(values) if min(values) > 0 else float('inf')
    ppls['savant_index'] = savant_index
    return ppls
```

**Savant Index Interpretation**:
- SI ≈ 1.0: Equal across all domains → Similar to Dense model
- SI > 3.0: Strong specialization in certain domains → MoE Expert differentiation begins
- SI > 10.0: Extreme specialization → savant pattern (can be intentionally induced)

## 5. Expert Cross-Activation Implementation — Hypothesis 241

### 5.1 Hypothesis 241: Expert Cross-Activation

> "When specific inputs in MoE models abnormally activate many Experts simultaneously,
> this corresponds to hyperconnectivity due to Sylvian fissure deficiency in the brain."

### 5.2 Mathematical Definition

Normal mode: 5/8 Experts active (active_ratio = 0.625)
Cross-activation mode: 7/8 or 8/8 Experts active (for specific inputs)

```
CrossActivation(x) = |{e : w_e(x) > threshold}| / num_experts
```

Where `w_e(x)` is router weight of Expert e for input x.

### 5.3 Implementation Overview

```python
class AdaptiveGoldenMoELayer(GoldenMoELayer):
    """Hypothesis 241 — Adjust active Expert count based on input complexity"""

    def __init__(self, *args, cross_threshold=0.8, **kwargs):
        super().__init__(*args, **kwargs)
        self.cross_threshold = cross_threshold

    def forward(self, x):
        scores = self.router.gate(x) / self.router.temperature
        probs = F.softmax(scores, dim=-1)

        # Measure input complexity: entropy-based
        entropy = -(probs * (probs + 1e-8).log()).sum(dim=-1)  # (B, S)
        max_entropy = math.log(self.num_experts)
        complexity = entropy / max_entropy  # 0~1 normalized

        # Higher complexity → activate more Experts (cross-activation)
        adaptive_k = torch.where(
            complexity > self.cross_threshold,
            torch.tensor(self.num_experts),      # Full activation
            torch.tensor(self.router.num_active)  # Default 5/8
        )

        # Adaptive top-k selection
        # ... (implementation needed for per-token different k)

        return output

    def get_cross_activation_stats(self):
        """Cross-activation frequency statistics"""
        return {
            'cross_activation_rate': self._cross_count / max(self._total_count, 1),
            'avg_active_experts': self._active_sum / max(self._total_count, 1),
        }
```

### 5.4 Experiment Plan

1. **Complete basic router learning** (PPL < 100) → After Phase 2
2. **Replace with cross-activation router** → Apply `AdaptiveGoldenMoELayer`
3. **Measure cross-activation frequency** → Analyze which inputs trigger cross-activation by domain
4. **Recalculate G formula** → Generalize as G = D x P / I(x) since I changes dynamically during cross-activation

### 5.5 Expected Results

- Math problems → High cross-activation (multiple Experts needed simultaneously)
- General text → Low cross-activation (few Experts sufficient)
- Savant domains → Discoverable abnormal cross-activation patterns

## 6. Execution Roadmap

```
Current ─────────────────────────────────────── Target
PPL 4634                                    PPL < 20

Step 1: Train router for 2000 steps
  └─ Expected: PPL ~500
  └─ Check: Loss curve convergence

Step 2: Add learning rate scheduler + 5000 steps
  └─ Expected: PPL ~50-100
  └─ Check: Text generation coherence test

Step 3: Implement domain-specific PPL measurement tool
  └─ Add savant_profile() to benchmark.py
  └─ Calculate Savant Index

Step 4: Implement Expert cross-activation layer (Hypothesis 241)
  └─ Add AdaptiveGoldenMoELayer to convert.py
  └─ Collect cross-activation statistics

Step 5: Retrain cross-activation model
  └─ Adaptive router fine-tuning
  └─ Verify G = D × P / I(x) dynamic calculation
```

## 7. File References

| File | Location | Role |
|------|----------|------|
| convert.py | golden-llama/ | Dense → MoE conversion (BoltzmannRouter, GoldenMoELayer) |
| finetune_router.py | golden-llama/ | Router fine-tuning (Experts frozen) |
| benchmark.py | golden-llama/ | PPL/speed benchmarks |
| golden-test/ | golden-llama/ | Converted MoE model (4.1GB) |
| golden-test-finetuned/ | golden-llama/ | 500-step fine-tuned model |