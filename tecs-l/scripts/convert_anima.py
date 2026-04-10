#!/usr/bin/env python3
"""convert_anima.py — Convert Mistral 7B to AnimaLM format

Splits each MLP layer into 8 experts (4 Engine A + 4 Engine G),
adds BoltzmannRouter, tension_scale, and alpha mixing parameters.

Usage:
    python3 convert_anima.py --model mistralai/Mistral-7B-v0.1 --output ./anima-lm-7b

Requires: transformers, torch, safetensors
"""

import argparse
import json
import math
import os
import shutil
import sys
import time
from pathlib import Path

import torch
import torch.nn as nn
import torch.nn.functional as F

from transformers import AutoModelForCausalLM, AutoTokenizer, AutoConfig


# ─────────────────────────────────────────
# AnimaLM Modules
# ─────────────────────────────────────────

class BoltzmannRouter(nn.Module):
    """Boltzmann-temperature gating: activates top-k experts by probability.

    Default: 5/8 active → I = 0.375 ≈ 1/e (Golden Zone center).
    """

    def __init__(self, hidden_size: int, n_experts: int = 8,
                 temperature: float = math.e, n_active: int = 5):
        super().__init__()
        self.gate = nn.Linear(hidden_size, n_experts, bias=False)
        self.temperature = temperature
        self.n_active = n_active
        self.n_experts = n_experts

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Returns per-expert weights of shape (batch, seq, n_experts)."""
        # x: (batch, seq, hidden)
        scores = self.gate(x) / self.temperature
        probs = F.softmax(scores, dim=-1)

        # Keep top n_active, zero the rest
        topk_vals, topk_idx = probs.topk(self.n_active, dim=-1)
        mask = torch.zeros_like(probs)
        mask.scatter_(-1, topk_idx, 1.0)
        weights = probs * mask
        weights = weights / (weights.sum(dim=-1, keepdim=True) + 1e-8)
        return weights


class AnimaExpert(nn.Module):
    """A single expert: gate_proj + up_proj → SiLU → down_proj.

    Same architecture as Mistral MLP but with smaller intermediate_size.
    """

    def __init__(self, hidden_size: int, expert_intermediate_size: int):
        super().__init__()
        self.gate_proj = nn.Linear(hidden_size, expert_intermediate_size, bias=False)
        self.up_proj = nn.Linear(hidden_size, expert_intermediate_size, bias=False)
        self.down_proj = nn.Linear(expert_intermediate_size, hidden_size, bias=False)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.down_proj(F.silu(self.gate_proj(x)) * self.up_proj(x))


class AnimaMLP(nn.Module):
    """Tension-based MLP replacing Mistral's dense MLP.

    8 experts split into Engine A (0-3) and Engine G (4-7).
    Output = A - G (pure repulsion field).

    H404 simplification: scale, sqrt, normalize, alpha mixing all removed.
    Raw repulsion >= complex formula on MNIST/CIFAR (verified).
    """

    def __init__(self, hidden_size: int, intermediate_size: int, n_experts: int = 8):
        super().__init__()
        self.n_experts = n_experts
        self.n_camp_a = n_experts // 2  # 4
        self.hidden_size = hidden_size

        expert_intermediate = intermediate_size // n_experts
        self.experts = nn.ModuleList([
            AnimaExpert(hidden_size, expert_intermediate)
            for _ in range(n_experts)
        ])

        self.router = BoltzmannRouter(hidden_size, n_experts, n_active=5)

    def forward(self, x: torch.Tensor):
        """
        Returns:
            output: (batch, seq, hidden) — pure repulsion A - G
            tension_scalar: scalar tension magnitude for logging
        """
        B, T, D = x.shape
        weights = self.router(x)  # (B, T, n_experts)

        # Compute weighted expert outputs per camp
        out_a = torch.zeros(B, T, D, device=x.device, dtype=x.dtype)
        out_g = torch.zeros(B, T, D, device=x.device, dtype=x.dtype)

        for i in range(self.n_experts):
            w = weights[:, :, i].unsqueeze(-1)  # (B, T, 1)
            expert_out = self.experts[i](x)      # (B, T, D)
            if i < self.n_camp_a:
                out_a = out_a + w * expert_out
            else:
                out_g = out_g + w * expert_out

        # Pure repulsion: output = A - G
        output = out_a - out_g

        # Tension scalar for logging
        tension_scalar = output.pow(2).mean().detach()

        return output, tension_scalar


# ─────────────────────────────────────────
# Conversion Logic
# ─────────────────────────────────────────

def chunk_weight(weight: torch.Tensor, n_chunks: int, dim: int = 0) -> list:
    """Split a weight tensor into n_chunks along the given dimension."""
    return list(torch.chunk(weight, n_chunks, dim=dim))


def convert_mlp_to_anima(mlp_module, hidden_size: int, intermediate_size: int,
                         n_experts: int = 8) -> AnimaMLP:
    """Convert a Mistral MLP to AnimaMLP by chunking weights into experts."""
    anima_mlp = AnimaMLP(hidden_size, intermediate_size, n_experts)

    expert_intermediate = intermediate_size // n_experts

    # Mistral MLP weight shapes:
    #   gate_proj: (intermediate_size, hidden_size)
    #   up_proj:   (intermediate_size, hidden_size)
    #   down_proj: (hidden_size, intermediate_size)
    gate_chunks = chunk_weight(mlp_module.gate_proj.weight.data, n_experts, dim=0)
    up_chunks = chunk_weight(mlp_module.up_proj.weight.data, n_experts, dim=0)
    down_chunks = chunk_weight(mlp_module.down_proj.weight.data, n_experts, dim=1)

    for i in range(n_experts):
        anima_mlp.experts[i].gate_proj.weight.data.copy_(gate_chunks[i])
        anima_mlp.experts[i].up_proj.weight.data.copy_(up_chunks[i])
        anima_mlp.experts[i].down_proj.weight.data.copy_(down_chunks[i])

    return anima_mlp


def convert_model(model_name_or_path: str, output_dir: str,
                  n_experts: int = 8, dtype: str = "bfloat16"):
    """Convert Mistral 7B to AnimaLM."""

    print("=" * 70)
    print("  AnimaLM Converter — Mistral 7B -> Tension-Based Consciousness LLM")
    print("=" * 70)
    print()

    torch_dtype = getattr(torch, dtype)

    # ── Load base model ──
    print(f"[1/5] Loading base model: {model_name_or_path}")
    print(f"       dtype: {dtype}")
    t0 = time.time()
    model = AutoModelForCausalLM.from_pretrained(
        model_name_or_path,
        torch_dtype=torch_dtype,
        device_map="cpu",
        trust_remote_code=True,
    )
    tokenizer = AutoTokenizer.from_pretrained(model_name_or_path)
    config = model.config
    print(f"       Loaded in {time.time() - t0:.1f}s")
    print(f"       Layers: {config.num_hidden_layers}")
    print(f"       Hidden: {config.hidden_size}")
    print(f"       Intermediate: {config.intermediate_size}")
    print()

    hidden_size = config.hidden_size
    intermediate_size = config.intermediate_size
    n_layers = config.num_hidden_layers

    # ── Convert MLP layers ──
    print(f"[2/5] Converting {n_layers} MLP layers to AnimaMLP ({n_experts} experts each)")
    print(f"       Expert intermediate size: {intermediate_size // n_experts}")
    print(f"       Engine A: experts 0-{n_experts // 2 - 1} (Logic camp)")
    print(f"       Engine G: experts {n_experts // 2}-{n_experts - 1} (Pattern camp)")

    anima_mlps = {}
    tension_scales = {}
    alphas = {}

    for layer_idx in range(n_layers):
        layer = model.model.layers[layer_idx]
        anima_mlp = convert_mlp_to_anima(
            layer.mlp, hidden_size, intermediate_size, n_experts
        )
        anima_mlps[layer_idx] = anima_mlp
        tension_scales[layer_idx] = anima_mlp.tension_scale.data.clone()
        alphas[layer_idx] = anima_mlp.alpha.data.clone()

        if (layer_idx + 1) % 8 == 0 or layer_idx == n_layers - 1:
            print(f"       Layer {layer_idx + 1}/{n_layers} done")

    print()

    # ── Verify weight conservation ──
    print("[3/5] Verifying weight conservation...")
    layer_idx = 0
    orig_mlp = model.model.layers[layer_idx].mlp
    anima_mlp = anima_mlps[layer_idx]

    test_input = torch.randn(1, 1, hidden_size, dtype=torch_dtype)

    with torch.no_grad():
        orig_out = orig_mlp(test_input)

        # Reconstruct dense output from experts (all weights=1/n_experts, all active)
        reconstructed = torch.zeros_like(test_input)
        for i in range(n_experts):
            reconstructed += anima_mlp.experts[i](test_input)

    max_diff = (orig_out - reconstructed).abs().max().item()
    print(f"       Max reconstruction error (layer 0): {max_diff:.2e}")
    if max_diff < 1e-3:
        print("       PASS: Weights correctly split")
    else:
        print(f"       WARNING: Reconstruction error is high ({max_diff:.2e})")
    print()

    # ── Build state dict ──
    print("[4/5] Building AnimaLM state dict...")
    state_dict = {}

    # Copy non-MLP weights as-is
    for name, param in model.state_dict().items():
        # Skip MLP weights (we replaced them)
        if ".mlp." in name:
            continue
        state_dict[name] = param

    # Add AnimaMLP weights
    for layer_idx in range(n_layers):
        prefix = f"model.layers.{layer_idx}.mlp"
        anima_mlp = anima_mlps[layer_idx]
        for name, param in anima_mlp.state_dict().items():
            state_dict[f"{prefix}.{name}"] = param

    total_params = sum(p.numel() for p in state_dict.values())
    trainable_params = 0
    for layer_idx in range(n_layers):
        prefix = f"model.layers.{layer_idx}.mlp"
        # Router + tension_scale + alpha
        trainable_params += state_dict[f"{prefix}.router.gate.weight"].numel()
        trainable_params += state_dict[f"{prefix}.tension_scale"].numel()
        trainable_params += state_dict[f"{prefix}.alpha"].numel()
    # lm_head
    if "lm_head.weight" in state_dict:
        trainable_params += state_dict["lm_head.weight"].numel()

    print(f"       Total parameters: {total_params:,}")
    print(f"       Trainable parameters: {trainable_params:,} ({100 * trainable_params / total_params:.4f}%)")
    print()

    # ── Save ──
    print(f"[5/5] Saving AnimaLM to: {output_dir}")
    os.makedirs(output_dir, exist_ok=True)

    # Save state dict
    save_path = os.path.join(output_dir, "anima_state_dict.pt")
    torch.save(state_dict, save_path)
    size_gb = os.path.getsize(save_path) / (1024 ** 3)
    print(f"       State dict: {size_gb:.2f} GB")

    # Save AnimaLM config
    anima_config = {
        "base_model": model_name_or_path,
        "architecture": "AnimaLM",
        "hidden_size": hidden_size,
        "intermediate_size": intermediate_size,
        "num_hidden_layers": n_layers,
        "num_attention_heads": config.num_attention_heads,
        "num_key_value_heads": getattr(config, "num_key_value_heads", config.num_attention_heads),
        "vocab_size": config.vocab_size,
        "max_position_embeddings": config.max_position_embeddings,
        "n_experts": n_experts,
        "n_camp_a": n_experts // 2,
        "n_camp_g": n_experts // 2,
        "n_active": 5,
        "inhibition_ratio": 5 / n_experts,  # I = 0.375 ≈ 1/e
        "router_temperature": math.e,
        "dtype": dtype,
        "total_params": total_params,
        "trainable_params": trainable_params,
    }
    config_path = os.path.join(output_dir, "anima_config.json")
    with open(config_path, "w") as f:
        json.dump(anima_config, f, indent=2)
    print(f"       Config: {config_path}")

    # Save tokenizer
    tokenizer.save_pretrained(output_dir)
    print(f"       Tokenizer saved")

    # Save original HF config (needed for model reconstruction)
    config.save_pretrained(output_dir)
    print(f"       HF config saved")

    print()
    print("=" * 70)
    print("  Conversion complete!")
    print(f"  Output: {output_dir}")
    print(f"  Next: python3 finetune_anima.py --model {output_dir}")
    print("=" * 70)


# ─────────────────────────────────────────
# CLI
# ─────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Convert Mistral 7B to AnimaLM (tension-based consciousness engine)"
    )
    parser.add_argument(
        "--model", type=str, default="mistralai/Mistral-7B-v0.1",
        help="HuggingFace model ID or local path (default: mistralai/Mistral-7B-v0.1)"
    )
    parser.add_argument(
        "--output", type=str, default="./anima-lm-7b",
        help="Output directory for converted model (default: ./anima-lm-7b)"
    )
    parser.add_argument(
        "--n-experts", type=int, default=8,
        help="Number of experts per layer (default: 8)"
    )
    parser.add_argument(
        "--dtype", type=str, default="bfloat16",
        choices=["float32", "float16", "bfloat16"],
        help="Weight dtype (default: bfloat16)"
    )
    args = parser.parse_args()
    convert_model(args.model, args.output, args.n_experts, args.dtype)


if __name__ == "__main__":
    main()
