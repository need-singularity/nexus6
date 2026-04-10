#!/usr/bin/env python3
"""Golden Inhibition GPU Experiments — Windows PC (RTX 5070)

1. Expert activation heatmap
2. Savant Index
3. I sweep (U-curve)
4. Noise analysis (Dense vs MoE)
5. Step 15000 PPL check

Requires: torch, transformers (Golden MoE checkpoint)
Run: python golden_inhibition_gpu.py --checkpoint /path/to/golden_moe
"""

import argparse
import json
import sys

def experiment_1_activation_heatmap(model, tokenizer):
    """Visualize expert activation patterns"""
    print("\n=== Experiment 1: Expert Activation Heatmap ===")

    test_prompts = {
        "factual": "The capital of France is",
        "code": "def fibonacci(n):",
        "emotion": "I feel very sad because",
        "math": "The integral of x squared is",
        "creative": "Once upon a time in a dark forest",
    }

    results = {}
    for category, prompt in test_prompts.items():
        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
        with torch.no_grad():
            outputs = model(**inputs, output_router_logits=True)

        # Get router decisions
        router_logits = outputs.router_logits  # list of (batch, seq, n_experts)
        # Average over layers and tokens
        avg_activation = torch.stack([r.softmax(-1).mean(dim=(0,1)) for r in router_logits]).mean(0)
        results[category] = avg_activation.cpu().tolist()

        top_experts = avg_activation.topk(3).indices.tolist()
        print(f"  {category:10s}: top experts = {top_experts}")

    return results

def experiment_2_savant_index(model, tokenizer, datasets):
    """Savant Index: max(domainPPL)/min(domainPPL)"""
    print("\n=== Experiment 2: Savant Index ===")

    ppls = {}
    for domain, texts in datasets.items():
        total_loss = 0
        total_tokens = 0
        for text in texts[:100]:
            inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512).to(model.device)
            with torch.no_grad():
                outputs = model(**inputs, labels=inputs["input_ids"])
            total_loss += outputs.loss.item() * inputs["input_ids"].shape[1]
            total_tokens += inputs["input_ids"].shape[1]
        ppl = math.exp(total_loss / total_tokens)
        ppls[domain] = ppl
        print(f"  {domain:10s}: PPL = {ppl:.2f}")

    si = max(ppls.values()) / min(ppls.values())
    print(f"  Savant Index = {si:.2f} (>3 = savant candidate)")
    return {"ppls": ppls, "savant_index": si}

def experiment_3_i_sweep():
    """I sweep: inhibition rate vs PPL (requires retraining)"""
    print("\n=== Experiment 3: I Sweep ===")
    print("  NOTE: This requires training multiple models.")
    print("  Recommended: train with I=0.1,0.2,0.3,1/e,0.4,0.5,0.7")
    print("  Expected: U-curve with minimum at I≈1/e≈0.368")
    # This is a meta-experiment - needs to be run separately
    return {"status": "needs_separate_training"}

def experiment_4_noise_analysis(model, tokenizer):
    """Dense vs MoE output variance"""
    print("\n=== Experiment 4: Noise Analysis ===")

    prompt = "The meaning of life is"
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

    # Run multiple forward passes (MoE has stochastic routing)
    outputs_list = []
    for _ in range(10):
        with torch.no_grad():
            out = model(**inputs)
        outputs_list.append(out.logits[:, -1, :].cpu())

    stacked = torch.stack(outputs_list)
    variance = stacked.var(dim=0).mean().item()
    mean_logit = stacked.mean(dim=0).abs().mean().item()

    print(f"  Output variance across runs: {variance:.6f}")
    print(f"  Mean |logit|: {mean_logit:.4f}")
    print(f"  SNR estimate: {mean_logit/max(variance**0.5, 1e-10):.2f}")

    return {"variance": variance, "mean_logit": mean_logit}

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", type=str, help="Golden MoE checkpoint path")
    parser.add_argument("--cpu-only", action="store_true", help="Run CPU-only experiments")
    args = parser.parse_args()

    if args.cpu_only:
        print("CPU-only mode: running mathematical analysis only")
        import subprocess
        subprocess.run([sys.executable, "golden_inhibition_analysis.py"])
        sys.exit(0)

    try:
        import torch
        import math
        print(f"PyTorch {torch.__version__}, CUDA: {torch.cuda.is_available()}")
        if torch.cuda.is_available():
            print(f"GPU: {torch.cuda.get_device_name(0)}")
    except ImportError:
        print("PyTorch not found. Run with --cpu-only for mathematical analysis.")
        sys.exit(1)

    if not args.checkpoint:
        print("No checkpoint specified. Run mathematical analysis only.")
        print("Usage: python golden_inhibition_gpu.py --checkpoint /path/to/model")
        sys.exit(0)

    # Load model
    from transformers import AutoModelForCausalLM, AutoTokenizer
    print(f"Loading model from {args.checkpoint}...")
    tokenizer = AutoTokenizer.from_pretrained(args.checkpoint)
    model = AutoModelForCausalLM.from_pretrained(args.checkpoint, torch_dtype=torch.float16)
    if torch.cuda.is_available():
        model = model.cuda()

    r1 = experiment_1_activation_heatmap(model, tokenizer)
    # r2 = experiment_2_savant_index(model, tokenizer, datasets)  # needs datasets
    experiment_3_i_sweep()
    r4 = experiment_4_noise_analysis(model, tokenizer)

    results = {"exp1_heatmap": r1, "exp4_noise": r4}
    with open("golden_inhibition_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print("\nResults saved to golden_inhibition_results.json")