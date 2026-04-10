#!/usr/bin/env python3
"""Mistral 7B → Golden MoA Converter

Splits Dense FFN into N Experts and equips with Boltzmann router (T=e).
Savant tuning: Domain specialization per Expert → Target Savant Index > 3.

Conversion strategy:
  1. Attention layers: Preserve as-is
  2. FFN (gate_proj + up_proj + down_proj): Split into N equal parts to create Experts
  3. Add Boltzmann router (T=e, 70% active)
  4. Weight copying: Split original FFN columns/rows by N
"""

import argparse
import json
import math
import os
import sys
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from safetensors.torch import load_file, save_file


# ─────────────────────────────────────────
# Golden MoA Constants (Golden Zone Theory)
# ─────────────────────────────────────────
GOLDEN_TEMPERATURE = math.e          # Boltzmann temperature T=e
GOLDEN_ACTIVE_RATIO = 0.7            # 70% Expert activation
GOLDEN_ZONE_LOWER = 0.5 - math.log(4/3)  # ≈ 0.2123
GOLDEN_ZONE_UPPER = 0.5                   # Riemann critical line
GOLDEN_ZONE_CENTER = 1 / math.e           # ≈ 0.3679


# ─────────────────────────────────────────
# Boltzmann Router
# ─────────────────────────────────────────
class BoltzmannRouter(nn.Module):
    """Golden Zone Boltzmann soft gating router"""

    def __init__(self, hidden_dim: int, n_experts: int,
                 temperature: float = GOLDEN_TEMPERATURE,
                 active_ratio: float = GOLDEN_ACTIVE_RATIO):
        super().__init__()
        self.gate = nn.Linear(hidden_dim, n_experts, bias=False)
        self.temperature = temperature
        self.n_active = max(1, int(n_experts * active_ratio))
        self.n_experts = n_experts

        # Xavier initialization — uniform routing initially
        nn.init.xavier_uniform_(self.gate.weight)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: (batch, seq_len, hidden_dim)
        Returns:
            weights: (batch, seq_len, n_experts) — weights only for active Experts
        """
        scores = self.gate(x) / self.temperature
        probs = F.softmax(scores, dim=-1)

        # Activate only top n_active
        topk_vals, topk_idx = probs.topk(self.n_active, dim=-1)
        mask = torch.zeros_like(probs)
        mask.scatter_(-1, topk_idx, 1.0)

        weights = probs * mask
        weights = weights / (weights.sum(dim=-1, keepdim=True) + 1e-8)
        return weights


# ─────────────────────────────────────────
# Expert (Partitioned FFN)
# ─────────────────────────────────────────
class MistralExpert(nn.Module):
    """Expert composed of a subset of Mistral FFN"""

    def __init__(self, hidden_dim: int, expert_intermediate_dim: int):
        super().__init__()
        self.gate_proj = nn.Linear(hidden_dim, expert_intermediate_dim, bias=False)
        self.up_proj = nn.Linear(hidden_dim, expert_intermediate_dim, bias=False)
        self.down_proj = nn.Linear(expert_intermediate_dim, hidden_dim, bias=False)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # SiLU gated FFN (same structure as original Mistral)
        return self.down_proj(F.silu(self.gate_proj(x)) * self.up_proj(x))


# ─────────────────────────────────────────
# Golden MoA Layer
# ─────────────────────────────────────────
class GoldenMoALayer(nn.Module):
    """Golden MoA layer replacing Dense FFN"""

    def __init__(self, hidden_dim: int, intermediate_dim: int, n_experts: int = 8):
        super().__init__()
        assert intermediate_dim % n_experts == 0, \
            f"intermediate_dim({intermediate_dim}) must be divisible by n_experts({n_experts})"

        self.n_experts = n_experts
        self.expert_dim = intermediate_dim // n_experts

        self.router = BoltzmannRouter(hidden_dim, n_experts)
        self.experts = nn.ModuleList([
            MistralExpert(hidden_dim, self.expert_dim)
            for _ in range(n_experts)
        ])

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: (batch, seq_len, hidden_dim)
        Returns:
            output: (batch, seq_len, hidden_dim)
        """
        batch, seq_len, hidden = x.shape
        weights = self.router(x)  # (batch, seq_len, n_experts)

        # Compute Expert outputs
        expert_outputs = torch.stack(
            [expert(x) for expert in self.experts], dim=-2
        )  # (batch, seq_len, n_experts, hidden)

        # Weighted sum
        output = (weights.unsqueeze(-1) * expert_outputs).sum(dim=-2)
        return output


# ─────────────────────────────────────────
# Conversion Functions
# ─────────────────────────────────────────
def split_ffn_weights(gate_proj_w, up_proj_w, down_proj_w, n_experts: int):
    """Split Dense FFN weights into N Experts

    gate_proj: (intermediate_dim, hidden_dim) → N × (expert_dim, hidden_dim)
    up_proj:   (intermediate_dim, hidden_dim) → N × (expert_dim, hidden_dim)
    down_proj: (hidden_dim, intermediate_dim) → N × (hidden_dim, expert_dim)
    """
    intermediate_dim = gate_proj_w.shape[0]
    expert_dim = intermediate_dim // n_experts

    expert_weights = []
    for i in range(n_experts):
        start = i * expert_dim
        end = start + expert_dim
        expert_weights.append({
            'gate_proj.weight': gate_proj_w[start:end, :].clone(),
            'up_proj.weight': up_proj_w[start:end, :].clone(),
            'down_proj.weight': down_proj_w[:, start:end].clone(),
        })

    return expert_weights


def convert_model(model_dir: str, output_dir: str, n_experts: int = 8):
    """Mistral 7B → Golden MoA conversion"""

    model_path = Path(model_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Read config
    config_file = model_path / "config.json"
    if not config_file.exists():
        print(f"ERROR: {config_file} not found")
        sys.exit(1)

    with open(config_file) as f:
        config = json.load(f)

    hidden_dim = config["hidden_size"]
    intermediate_dim = config["intermediate_size"]
    n_layers = config["num_hidden_layers"]

    print(f"═══════════════════════════════════════════════════")
    print(f"  Mistral 7B → Golden MoA Converter")
    print(f"═══════════════════════════════════════════════════")
    print(f"  Original:  hidden={hidden_dim}, intermediate={intermediate_dim}")
    print(f"  Layers:    {n_layers}")
    print(f"  Experts:   {n_experts}, each {intermediate_dim // n_experts}dim")
    print(f"  Router:    Boltzmann T=e, active ratio={GOLDEN_ACTIVE_RATIO:.0%}")
    print(f"  Golden Zone: I ∈ [{GOLDEN_ZONE_LOWER:.4f}, {GOLDEN_ZONE_UPPER:.4f}]")
    print(f"  I_target:  1 - {GOLDEN_ACTIVE_RATIO} = {1 - GOLDEN_ACTIVE_RATIO:.2f}")
    I_effective = 1 - GOLDEN_ACTIVE_RATIO
    zone_status = "IN" if GOLDEN_ZONE_LOWER <= I_effective <= GOLDEN_ZONE_UPPER else "OUT"
    print(f"  Golden Zone: {zone_status}")
    print(f"─────────────────────────────────────────────────")

    # Check Expert dimension compatibility
    if intermediate_dim % n_experts != 0:
        # Find nearest compatible Expert count
        for ne in [8, 4, 6, 2, 16]:
            if intermediate_dim % ne == 0:
                print(f"  ⚠ n_experts={n_experts} is incompatible with intermediate_dim={intermediate_dim}")
                print(f"    → Changing to n_experts={ne}")
                n_experts = ne
                break

    expert_dim = intermediate_dim // n_experts
    print(f"  Per-expert intermediate_dim: {expert_dim}")

    # Load safetensors files
    shard_files = sorted(model_path.glob("model*.safetensors"))
    if not shard_files:
        print("ERROR: No safetensors files found")
        sys.exit(1)

    print(f"\n  safetensors files: {len(shard_files)}")

    # Load all weights
    all_weights = {}
    for sf in shard_files:
        print(f"    Loading: {sf.name}...", end=" ", flush=True)
        weights = load_file(str(sf), device="cpu")
        all_weights.update(weights)
        print(f"({len(weights)} tensors)")

    print(f"  Total tensors: {len(all_weights)}")

    # Conversion
    new_weights = {}
    converted_layers = 0

    for layer_idx in range(n_layers):
        prefix = f"model.layers.{layer_idx}"

        # Attention weights — copy as-is
        for attn_key in ['self_attn.q_proj.weight', 'self_attn.k_proj.weight',
                         'self_attn.v_proj.weight', 'self_attn.o_proj.weight']:
            full_key = f"{prefix}.{attn_key}"
            if full_key in all_weights:
                new_weights[full_key] = all_weights[full_key]

        # LayerNorm — copy as-is
        for ln_key in ['input_layernorm.weight', 'post_attention_layernorm.weight']:
            full_key = f"{prefix}.{ln_key}"
            if full_key in all_weights:
                new_weights[full_key] = all_weights[full_key]

        # FFN → Expert split
        gate_key = f"{prefix}.mlp.gate_proj.weight"
        up_key = f"{prefix}.mlp.up_proj.weight"
        down_key = f"{prefix}.mlp.down_proj.weight"

        if gate_key in all_weights and up_key in all_weights and down_key in all_weights:
            expert_weights_list = split_ffn_weights(
                all_weights[gate_key],
                all_weights[up_key],
                all_weights[down_key],
                n_experts
            )

            # Save Expert weights
            moa_prefix = f"{prefix}.moa"
            for expert_idx, ew in enumerate(expert_weights_list):
                for key, tensor in ew.items():
                    new_key = f"{moa_prefix}.experts.{expert_idx}.{key}"
                    new_weights[new_key] = tensor

            # Router weights (Xavier initialization)
            router_weight = torch.empty(n_experts, hidden_dim)
            nn.init.xavier_uniform_(router_weight)
            new_weights[f"{moa_prefix}.router.gate.weight"] = router_weight

            converted_layers += 1

            if (layer_idx + 1) % 8 == 0 or layer_idx == 0:
                print(f"  Layer {layer_idx:>2}/{n_layers}: FFN → {n_experts} Experts ✓")

    # Embedding + LM head + final norm
    for key in ['model.embed_tokens.weight', 'model.norm.weight', 'lm_head.weight']:
        if key in all_weights:
            new_weights[key] = all_weights[key]

    print(f"\n  Conversion complete: {converted_layers}/{n_layers} layers")
    print(f"  Original tensors: {len(all_weights)}")
    print(f"  Converted tensors: {len(new_weights)}")

    # Calculate parameter counts
    orig_params = sum(t.numel() for t in all_weights.values())
    new_params = sum(t.numel() for t in new_weights.values())
    router_params = n_layers * n_experts * hidden_dim
    print(f"  Original parameters: {orig_params:,}")
    print(f"  Converted parameters: {new_params:,} (+{router_params:,} router)")

    # Save Golden MoA config
    moa_config = {
        **config,
        "model_type": "golden_moa_mistral",
        "architectures": ["GoldenMoAMistralForCausalLM"],
        "moa_config": {
            "n_experts": n_experts,
            "expert_intermediate_dim": expert_dim,
            "router_temperature": GOLDEN_TEMPERATURE,
            "active_ratio": GOLDEN_ACTIVE_RATIO,
            "golden_zone": {
                "lower": GOLDEN_ZONE_LOWER,
                "upper": GOLDEN_ZONE_UPPER,
                "center": GOLDEN_ZONE_CENTER,
            },
            "savant_config": {
                "target_savant_index": 3.0,
                "domain_experts": {
                    "math": list(range(0, n_experts // 4)),
                    "language": list(range(n_experts // 4, n_experts // 2)),
                    "code": list(range(n_experts // 2, 3 * n_experts // 4)),
                    "reasoning": list(range(3 * n_experts // 4, n_experts)),
                },
            },
        },
    }

    config_out = output_path / "config.json"
    with open(config_out, "w") as f:
        json.dump(moa_config, f, indent=2, ensure_ascii=False)
    print(f"\n  Config saved: {config_out}")

    # Save weights (safetensors)
    print(f"\n  Saving weights...", end=" ", flush=True)
    weights_out = output_path / "model.safetensors"

    # Large models save sharded
    total_bytes = sum(t.numel() * t.element_size() for t in new_weights.values())
    max_shard_bytes = 5 * 1024 ** 3  # 5GB per shard

    if total_bytes > max_shard_bytes:
        save_sharded(new_weights, output_path, max_shard_bytes)
    else:
        save_file(new_weights, str(weights_out))
        print(f"Done ({total_bytes / 1024**3:.1f}GB)")
        print(f"  Saved: {weights_out}")

    # Copy tokenizer
    for tok_file in ['tokenizer.json', 'tokenizer.model', 'tokenizer_config.json',
                     'special_tokens_map.json']:
        src = model_path / tok_file
        if src.exists():
            import shutil
            shutil.copy2(src, output_path / tok_file)
            print(f"  Tokenizer: {tok_file} ✓")

    print(f"\n═══════════════════════════════════════════════════")
    print(f"  Golden MoA conversion complete!")
    print(f"  Output: {output_path}")
    print(f"  Experts: {n_experts} × {expert_dim}dim / layer")
    print(f"  Router: Boltzmann T={GOLDEN_TEMPERATURE:.4f}")
    print(f"  Next step: Savant tuning (router learning)")
    print(f"═══════════════════════════════════════════════════")


def save_sharded(weights: dict, output_path: Path, max_shard_bytes: int):
    """Save weights split into multiple shards"""
    shard_idx = 0
    current_shard = {}
    current_bytes = 0
    index_map = {}  # key → shard filename

    sorted_keys = sorted(weights.keys())

    for key in sorted_keys:
        tensor = weights[key]
        tensor_bytes = tensor.numel() * tensor.element_size()

        if current_bytes + tensor_bytes > max_shard_bytes and current_shard:
            shard_name = f"model-{shard_idx:05d}-of-TOTAL.safetensors"
            save_file(current_shard, str(output_path / shard_name))
            print(f"\n    shard {shard_idx}: {current_bytes / 1024**3:.1f}GB ({len(current_shard)} tensors)")
            shard_idx += 1
            current_shard = {}
            current_bytes = 0

        current_shard[key] = tensor
        current_bytes += tensor_bytes
        index_map[key] = f"model-{shard_idx:05d}-of-TOTAL.safetensors"

    # Last shard
    if current_shard:
        shard_name = f"model-{shard_idx:05d}-of-TOTAL.safetensors"
        save_file(current_shard, str(output_path / shard_name))
        print(f"\n    shard {shard_idx}: {current_bytes / 1024**3:.1f}GB ({len(current_shard)} tensors)")
        shard_idx += 1

    total_shards = shard_idx

    # Update file names
    for i in range(total_shards):
        old_name = output_path / f"model-{i:05d}-of-TOTAL.safetensors"
        new_name = output_path / f"model-{i:05d}-of-{total_shards:05d}.safetensors"
        old_name.rename(new_name)

    # Update index map
    for key in index_map:
        old_shard = index_map[key]
        shard_num = old_shard.split("-")[1]
        index_map[key] = f"model-{shard_num}-of-{total_shards:05d}.safetensors"

    # Save index.json
    total_bytes = sum(t.numel() * t.element_size() for t in weights.values())
    index = {
        "metadata": {"total_size": total_bytes},
        "weight_map": index_map
    }
    with open(output_path / "model.safetensors.index.json", "w") as f:
        json.dump(index, f, indent=2)

    print(f"  Total {total_shards} shards, {total_bytes / 1024**3:.1f}GB")


# ─────────────────────────────────────────
# Golden MoA Inference Model (For loading after conversion)
# ─────────────────────────────────────────
class GoldenMoAMistralForCausalLM(nn.Module):
    """Converted Golden MoA Mistral model (for inference/training)"""

    @classmethod
    def from_pretrained(cls, model_dir: str, device: str = "cpu"):
        model_path = Path(model_dir)

        with open(model_path / "config.json") as f:
            config = json.load(f)

        moa_cfg = config["moa_config"]
        n_experts = moa_cfg["n_experts"]
        hidden_dim = config["hidden_size"]
        n_layers = config["num_hidden_layers"]

        print(f"  Loading Golden MoA: {n_layers}L × {n_experts}E, T={moa_cfg['router_temperature']:.4f}")

        # Load weights
        shard_files = sorted(model_path.glob("model*.safetensors"))
        weights = {}
        for sf in shard_files:
            if "index" not in sf.name:
                weights.update(load_file(str(sf), device=device))

        return weights, config


# ─────────────────────────────────────────
# Savant Tuning (Router Learning)
# ─────────────────────────────────────────
def savant_tune(model_dir: str, dataset: str = "wikitext",
                steps: int = 2000, lr: float = 1e-4,
                freeze_experts: bool = True):
    """Savant tuning: Freeze Experts and train only router

    Goals:
      - Induce domain specialization per Expert
      - Savant Index = max(domain_ppl) / min(domain_ppl) > 3
      - I_effective ∈ [0.2123, 0.5] (Golden Zone)
    """
    print(f"\n═══════════════════════════════════════════════════")
    print(f"  Golden MoA Savant Tuning")
    print(f"═══════════════════════════════════════════════════")
    print(f"  Model:      {model_dir}")
    print(f"  Dataset:    {dataset}")
    print(f"  Steps:      {steps}")
    print(f"  Learning rate: {lr}")
    print(f"  Freeze Experts: {freeze_experts}")
    print(f"  Goal: Savant Index > 3, I ∈ Golden Zone")
    print(f"─────────────────────────────────────────────────")
    print(f"\n  ⚠ Run Savant tuning in GPU environment")
    print(f"    Windows RTX 5070 or RunPod A100 recommended")
    print(f"    Mac MPS has insufficient memory for 7B models")


def main():
    parser = argparse.ArgumentParser(description="Mistral 7B → Golden MoA Converter")
    sub = parser.add_subparsers(dest="command")

    # convert command
    convert_cmd = sub.add_parser("convert", help="Dense → Golden MoA conversion")
    convert_cmd.add_argument("--model-dir", required=True, help="Mistral 7B path")
    convert_cmd.add_argument("--output-dir", required=True, help="Golden MoA output path")
    convert_cmd.add_argument("--n-experts", type=int, default=8, help="Number of Experts (default: 8)")

    # savant-tune command
    tune_cmd = sub.add_parser("savant-tune", help="Savant tuning (router learning)")
    tune_cmd.add_argument("--model-dir", required=True, help="Golden MoA path")
    tune_cmd.add_argument("--dataset", default="wikitext", help="Training dataset")
    tune_cmd.add_argument("--steps", type=int, default=2000, help="Training steps")
    tune_cmd.add_argument("--lr", type=float, default=1e-4, help="Learning rate")

    # info command
    info_cmd = sub.add_parser("info", help="Display Golden MoA model info")
    info_cmd.add_argument("--model-dir", required=True, help="Golden MoA path")

    args = parser.parse_args()

    if args.command == "convert":
        convert_model(args.model_dir, args.output_dir, args.n_experts)
    elif args.command == "savant_tune" or args.command == "savant-tune":
        savant_tune(args.model_dir, args.dataset, args.steps, args.lr)
    elif args.command == "info":
        weights, config = GoldenMoAMistralForCausalLM.from_pretrained(args.model_dir)
        moa = config["moa_config"]
        print(f"  Experts: {moa['n_experts']} × {moa['expert_intermediate_dim']}dim")
        print(f"  Router: T={moa['router_temperature']:.4f}, active={moa['active_ratio']:.0%}")
        print(f"  I_effective: {1 - moa['active_ratio']:.2f}")
        gz = moa['golden_zone']
        print(f"  Golden Zone: [{gz['lower']:.4f}, {gz['upper']:.4f}]")
        print(f"  Savant domains: {list(moa['savant_config']['domain_experts'].keys())}")
        print(f"  Number of tensors: {len(weights)}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()