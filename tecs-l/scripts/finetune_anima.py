#!/usr/bin/env python3
"""finetune_anima.py — Fine-tune AnimaLM on wikitext-2

Trains only router weights, tension_scale, alpha, and lm_head
while keeping all expert weights (original Mistral) frozen.

Supports 2x H100 80GB via FSDP or DataParallel.

Usage:
    # Single GPU
    python3 finetune_anima.py --model ./anima-lm-7b

    # 2x H100 with FSDP (recommended)
    torchrun --nproc_per_node=2 finetune_anima.py --model ./anima-lm-7b --fsdp

    # 2x H100 with DataParallel
    python3 finetune_anima.py --model ./anima-lm-7b --dp

Requires: transformers, torch, datasets, safetensors
"""

import argparse
import json
import math
import os
import sys
import time
from pathlib import Path

import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.distributed as dist
from torch.utils.data import DataLoader, Dataset
from torch.optim.lr_scheduler import CosineAnnealingLR

from transformers import AutoConfig, AutoTokenizer, AutoModelForCausalLM
from datasets import load_dataset

# Import AnimaLM modules from convert script
from convert_anima import AnimaMLP, AnimaExpert, BoltzmannRouter


# ─────────────────────────────────────────
# AnimaLM Model (full model wrapping Mistral architecture)
# ─────────────────────────────────────────

class AnimaLM(nn.Module):
    """AnimaLM: Mistral 7B with tension-based MLP layers.

    Loads the original Mistral architecture but replaces all MLP layers
    with AnimaMLP (8-expert tension field).
    """

    def __init__(self, config_path: str, state_dict_path: str,
                 anima_config: dict, device: torch.device):
        super().__init__()

        self.anima_config = anima_config
        n_experts = anima_config["n_experts"]
        hidden_size = anima_config["hidden_size"]
        intermediate_size = anima_config["intermediate_size"]
        n_layers = anima_config["num_hidden_layers"]
        dtype_str = anima_config.get("dtype", "bfloat16")
        self.torch_dtype = getattr(torch, dtype_str)

        # Load HF config and build base model skeleton on meta device
        hf_config = AutoConfig.from_pretrained(config_path)

        print("  Building model skeleton...")
        with torch.device("meta"):
            base_model = AutoModelForCausalLM.from_config(hf_config)

        # Replace MLP layers with AnimaMLP on meta device
        for layer_idx in range(n_layers):
            anima_mlp = AnimaMLP(hidden_size, intermediate_size, n_experts)
            base_model.model.layers[layer_idx].mlp = anima_mlp

        # Move to real device and load weights
        self.model = base_model.model
        self.lm_head = base_model.lm_head
        self.config = hf_config

        print(f"  Loading state dict from {state_dict_path}...")
        t0 = time.time()
        state_dict = torch.load(state_dict_path, map_location="cpu", weights_only=True)

        # Materialize all parameters from meta to real
        self.to_empty(device="cpu")
        missing, unexpected = self.load_state_dict(state_dict, strict=False)
        if missing:
            print(f"  WARNING: {len(missing)} missing keys (first 5): {missing[:5]}")
        if unexpected:
            print(f"  WARNING: {len(unexpected)} unexpected keys (first 5): {unexpected[:5]}")

        self.to(dtype=self.torch_dtype, device=device)
        print(f"  State dict loaded in {time.time() - t0:.1f}s")

    def forward(self, input_ids: torch.Tensor, labels: torch.Tensor = None):
        """Forward pass returning loss and tension stats."""
        # Embedding
        hidden_states = self.model.embed_tokens(input_ids)

        # Transformer layers
        tensions = []
        for layer in self.model.layers:
            # Self attention
            residual = hidden_states
            hidden_states = layer.input_layernorm(hidden_states)

            attn_output = layer.self_attn(
                hidden_states,
                position_ids=torch.arange(
                    hidden_states.shape[1], device=hidden_states.device
                ).unsqueeze(0).expand(hidden_states.shape[0], -1),
            )[0]
            hidden_states = residual + attn_output

            # AnimaMLP with tension
            residual = hidden_states
            hidden_states = layer.post_attention_layernorm(hidden_states)
            mlp_output, tension_scalar = layer.mlp(hidden_states)
            hidden_states = residual + mlp_output
            tensions.append(tension_scalar)

        hidden_states = self.model.norm(hidden_states)
        logits = self.lm_head(hidden_states)

        loss = None
        if labels is not None:
            shift_logits = logits[..., :-1, :].contiguous()
            shift_labels = labels[..., 1:].contiguous()
            loss = F.cross_entropy(
                shift_logits.view(-1, shift_logits.size(-1)),
                shift_labels.view(-1),
                ignore_index=-100,
            )

        return loss, logits, tensions

    def freeze_experts(self):
        """Freeze all expert weights, keep router/tension_scale/alpha/lm_head trainable."""
        frozen_count = 0
        trainable_count = 0

        for name, param in self.named_parameters():
            param.requires_grad = False
            frozen_count += param.numel()

        # Unfreeze trainable components
        for layer in self.model.layers:
            mlp = layer.mlp
            if isinstance(mlp, AnimaMLP):
                mlp.router.gate.weight.requires_grad = True
                mlp.tension_scale.requires_grad = True
                mlp.alpha.requires_grad = True

        # Unfreeze lm_head
        for param in self.lm_head.parameters():
            param.requires_grad = True

        trainable_count = sum(p.numel() for p in self.parameters() if p.requires_grad)
        frozen_count = sum(p.numel() for p in self.parameters() if not p.requires_grad)

        return trainable_count, frozen_count

    def get_tension_stats(self, tensions: list) -> dict:
        """Compute per-layer and aggregate tension statistics."""
        t_values = [t.item() for t in tensions]
        return {
            "mean": sum(t_values) / len(t_values),
            "std": (sum((t - sum(t_values) / len(t_values)) ** 2 for t in t_values)
                    / len(t_values)) ** 0.5,
            "min": min(t_values),
            "max": max(t_values),
            "per_layer": t_values,
        }

    def get_alpha_stats(self) -> dict:
        """Get sigmoid(alpha) values per layer — mixing ratio."""
        alphas = []
        for layer in self.model.layers:
            if isinstance(layer.mlp, AnimaMLP):
                alphas.append(torch.sigmoid(layer.mlp.alpha).item())
        return {
            "mean": sum(alphas) / len(alphas),
            "min": min(alphas),
            "max": max(alphas),
            "per_layer": alphas,
        }


# ─────────────────────────────────────────
# Dataset
# ─────────────────────────────────────────

class WikiTextDataset(Dataset):
    """Tokenized wikitext-2 dataset for causal LM training."""

    def __init__(self, tokenizer, split: str = "train", seq_len: int = 512):
        print(f"  Loading wikitext-2-raw-v1 ({split})...")
        dataset = load_dataset("wikitext", "wikitext-2-raw-v1", split=split)

        # Concatenate all text and tokenize
        text = "\n".join([t for t in dataset["text"] if t.strip()])
        print(f"  Tokenizing {len(text):,} characters...")

        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token

        tokens = tokenizer.encode(text, add_special_tokens=False)
        print(f"  Total tokens: {len(tokens):,}")

        # Cut into sequences of seq_len + 1 (input + label)
        self.examples = []
        for i in range(0, len(tokens) - seq_len, seq_len):
            chunk = tokens[i : i + seq_len + 1]
            if len(chunk) == seq_len + 1:
                self.examples.append(torch.tensor(chunk, dtype=torch.long))

        print(f"  Sequences: {len(self.examples):,} (seq_len={seq_len})")

    def __len__(self):
        return len(self.examples)

    def __getitem__(self, idx):
        chunk = self.examples[idx]
        return chunk[:-1], chunk[1:]  # input_ids, labels


# ─────────────────────────────────────────
# Evaluation
# ─────────────────────────────────────────

@torch.no_grad()
def evaluate(model, dataloader, device, max_batches: int = None) -> dict:
    """Evaluate model, return PPL and tension stats."""
    model.eval()
    total_loss = 0.0
    total_tokens = 0
    all_tensions = []

    for batch_idx, (input_ids, labels) in enumerate(dataloader):
        if max_batches and batch_idx >= max_batches:
            break

        input_ids = input_ids.to(device)
        labels = labels.to(device)

        loss, logits, tensions = model(input_ids, labels)

        n_tokens = (labels != -100).sum().item()
        total_loss += loss.item() * n_tokens
        total_tokens += n_tokens
        all_tensions.extend([t.item() for t in tensions])

    avg_loss = total_loss / max(total_tokens, 1)
    ppl = math.exp(min(avg_loss, 100))  # Cap to avoid overflow

    model.train()
    return {
        "loss": avg_loss,
        "ppl": ppl,
        "tension_mean": sum(all_tensions) / max(len(all_tensions), 1),
        "tension_std": (sum((t - sum(all_tensions) / len(all_tensions)) ** 2
                           for t in all_tensions) / max(len(all_tensions), 1)) ** 0.5,
    }


@torch.no_grad()
def evaluate_baseline_ppl(model_name: str, dataloader, device, dtype) -> float:
    """Get original Mistral 7B PPL for comparison."""
    print("  Loading original Mistral 7B for baseline PPL...")
    torch_dtype = getattr(torch, dtype)
    baseline = AutoModelForCausalLM.from_pretrained(
        model_name, torch_dtype=torch_dtype, device_map=device
    )
    baseline.eval()

    total_loss = 0.0
    total_tokens = 0

    for batch_idx, (input_ids, labels) in enumerate(dataloader):
        if batch_idx >= 20:  # Sample for speed
            break
        input_ids = input_ids.to(device)
        labels = labels.to(device)
        outputs = baseline(input_ids=input_ids, labels=labels)
        n_tokens = (labels != -100).sum().item()
        total_loss += outputs.loss.item() * n_tokens
        total_tokens += n_tokens

    del baseline
    torch.cuda.empty_cache()

    avg_loss = total_loss / max(total_tokens, 1)
    return math.exp(min(avg_loss, 100))


@torch.no_grad()
def compute_savant_index(model, tokenizer, device, seq_len: int = 512) -> dict:
    """Compute Savant Index = max(domain_ppl) / min(domain_ppl).

    Tests on multiple domain prompts to measure specialization.
    """
    domains = {
        "math": [
            "The fundamental theorem of calculus states that differentiation and integration are inverse operations.",
            "Consider the Riemann zeta function defined as the sum of 1/n^s for n from 1 to infinity.",
            "A prime number is a natural number greater than 1 that has no positive divisors other than 1 and itself.",
        ],
        "code": [
            "def fibonacci(n):\n    if n <= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)",
            "import torch\nimport torch.nn as nn\n\nclass TransformerBlock(nn.Module):\n    def __init__(self, d_model, nhead):",
            "SELECT users.name, COUNT(orders.id) FROM users LEFT JOIN orders ON users.id = orders.user_id GROUP BY users.name",
        ],
        "language": [
            "The old man sat by the window, watching the rain trace patterns down the glass. He remembered a time when storms",
            "In the quiet hours before dawn, the city begins its slow transformation from darkness to the pale grey of morning.",
            "She walked through the garden, her fingers brushing against the petals of roses that had bloomed overnight.",
        ],
    }

    model.eval()
    domain_ppls = {}

    for domain, texts in domains.items():
        total_loss = 0.0
        total_tokens = 0
        for text in texts:
            tokens = tokenizer.encode(text, return_tensors="pt").to(device)
            if tokens.shape[1] < 2:
                continue
            input_ids = tokens[:, :-1]
            labels = tokens[:, 1:]
            loss, _, _ = model(input_ids, labels)
            n_tokens = labels.shape[1]
            total_loss += loss.item() * n_tokens
            total_tokens += n_tokens

        avg_loss = total_loss / max(total_tokens, 1)
        domain_ppls[domain] = math.exp(min(avg_loss, 100))

    if domain_ppls:
        savant_index = max(domain_ppls.values()) / max(min(domain_ppls.values()), 1e-8)
    else:
        savant_index = 1.0

    return {"domain_ppls": domain_ppls, "savant_index": savant_index}


# ─────────────────────────────────────────
# Training Loop
# ─────────────────────────────────────────

def train(args):
    print("=" * 70)
    print("  AnimaLM Fine-Tuning — Tension-Based Consciousness Engine")
    print("=" * 70)
    print()

    # ── Setup device ──
    use_fsdp = args.fsdp and torch.cuda.device_count() >= 2
    use_dp = args.dp and torch.cuda.device_count() >= 2
    local_rank = 0

    if use_fsdp:
        local_rank = int(os.environ.get("LOCAL_RANK", 0))
        dist.init_process_group("nccl")
        torch.cuda.set_device(local_rank)
        device = torch.device(f"cuda:{local_rank}")
        is_main = local_rank == 0
    else:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        is_main = True

    if is_main:
        print(f"  Device: {device}")
        print(f"  GPUs available: {torch.cuda.device_count()}")
        print(f"  Mode: {'FSDP' if use_fsdp else 'DataParallel' if use_dp else 'Single GPU'}")
        for i in range(torch.cuda.device_count()):
            name = torch.cuda.get_device_name(i)
            mem = torch.cuda.get_device_properties(i).total_mem / (1024 ** 3)
            print(f"    GPU {i}: {name} ({mem:.0f} GB)")
        print()

    # ── Load AnimaLM config ──
    config_path = os.path.join(args.model, "anima_config.json")
    with open(config_path) as f:
        anima_config = json.load(f)

    if is_main:
        print(f"  AnimaLM Config:")
        print(f"    Base model: {anima_config['base_model']}")
        print(f"    Experts: {anima_config['n_experts']} ({anima_config['n_camp_a']}A + {anima_config['n_camp_g']}G)")
        print(f"    Active: {anima_config['n_active']}/{anima_config['n_experts']} (I={anima_config['inhibition_ratio']:.3f})")
        print()

    # ── Load tokenizer ──
    tokenizer = AutoTokenizer.from_pretrained(args.model)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    # ── Load model ──
    if is_main:
        print("[1/6] Loading AnimaLM model...")
    state_dict_path = os.path.join(args.model, "anima_state_dict.pt")

    model = AnimaLM(
        config_path=args.model,
        state_dict_path=state_dict_path,
        anima_config=anima_config,
        device=device if not use_dp else torch.device("cuda:0"),
    )

    # ── Freeze experts ──
    if is_main:
        print("[2/6] Freezing expert weights...")
    trainable_count, frozen_count = model.freeze_experts()
    if is_main:
        print(f"  Trainable: {trainable_count:,} ({100 * trainable_count / (trainable_count + frozen_count):.4f}%)")
        print(f"  Frozen:    {frozen_count:,}")
        print()

    # ── Wrap for multi-GPU ──
    if use_fsdp:
        from torch.distributed.fsdp import FullyShardedDataParallel as FSDP
        from torch.distributed.fsdp import MixedPrecision
        from torch.distributed.fsdp.wrap import transformer_auto_wrap_policy
        from functools import partial

        # Auto-wrap at the layer level
        auto_wrap_policy = partial(
            transformer_auto_wrap_policy,
            transformer_layer_cls={type(model.model.layers[0])},
        )
        mp_policy = MixedPrecision(
            param_dtype=model.torch_dtype,
            reduce_dtype=torch.float32,
            buffer_dtype=model.torch_dtype,
        )
        model = FSDP(
            model,
            auto_wrap_policy=auto_wrap_policy,
            mixed_precision=mp_policy,
            device_id=local_rank,
        )
        if is_main:
            print("  FSDP wrapping complete")
    elif use_dp:
        model = nn.DataParallel(model)
        if is_main:
            print("  DataParallel wrapping complete")

    # ── Dataset ──
    if is_main:
        print("[3/6] Loading dataset...")
    train_dataset = WikiTextDataset(tokenizer, split="train", seq_len=args.seq_len)
    val_dataset = WikiTextDataset(tokenizer, split="validation", seq_len=args.seq_len)

    if use_fsdp:
        from torch.utils.data.distributed import DistributedSampler
        train_sampler = DistributedSampler(train_dataset, shuffle=True)
        train_loader = DataLoader(
            train_dataset, batch_size=args.batch_size,
            sampler=train_sampler, num_workers=2, pin_memory=True,
        )
    else:
        train_loader = DataLoader(
            train_dataset, batch_size=args.batch_size,
            shuffle=True, num_workers=2, pin_memory=True,
        )
    val_loader = DataLoader(
        val_dataset, batch_size=args.batch_size,
        shuffle=False, num_workers=2, pin_memory=True,
    )

    if is_main:
        print(f"  Train: {len(train_dataset)} sequences")
        print(f"  Val:   {len(val_dataset)} sequences")
        print()

    # ── Optimizer + Scheduler ──
    if is_main:
        print("[4/6] Setting up optimizer...")
    trainable_params = [p for p in model.parameters() if p.requires_grad]
    optimizer = torch.optim.AdamW(
        trainable_params, lr=args.lr, weight_decay=args.weight_decay, betas=(0.9, 0.95)
    )

    total_steps = len(train_loader) * args.epochs
    warmup_steps = min(args.warmup_steps, total_steps // 10)
    scheduler = CosineAnnealingLR(optimizer, T_max=total_steps - warmup_steps, eta_min=args.lr * 0.1)

    if is_main:
        print(f"  LR: {args.lr} (cosine decay to {args.lr * 0.1})")
        print(f"  Warmup: {warmup_steps} steps")
        print(f"  Total steps: {total_steps}")
        print(f"  Epochs: {args.epochs}")
        print(f"  Batch size: {args.batch_size}")
        print(f"  Gradient accumulation: {args.grad_accum}")
        print(f"  Effective batch: {args.batch_size * args.grad_accum}")
        print()

    # ── Baseline PPL ──
    baseline_ppl = None
    if is_main and args.baseline:
        print("[5/6] Computing baseline Mistral 7B PPL...")
        baseline_ppl = evaluate_baseline_ppl(
            anima_config["base_model"], val_loader,
            device if not use_dp else torch.device("cuda:0"),
            anima_config.get("dtype", "bfloat16"),
        )
        print(f"  Baseline Mistral 7B PPL: {baseline_ppl:.2f}")
        print()
    else:
        if is_main:
            print("[5/6] Skipping baseline (use --baseline to enable)")
            print()

    # ── Training ──
    if is_main:
        print("[6/6] Training...")
        print()
        print(f"{'Step':>6} | {'Loss':>8} | {'PPL':>10} | {'T-mean':>8} | {'T-std':>8} | {'Alpha':>7} | {'LR':>10} | {'Time':>6}")
        print("-" * 85)

    model.train()
    global_step = 0
    best_val_ppl = float("inf")
    train_start = time.time()
    log_tensions = []

    for epoch in range(args.epochs):
        if use_fsdp:
            train_sampler.set_epoch(epoch)

        epoch_loss = 0.0
        epoch_tokens = 0
        optimizer.zero_grad()

        for batch_idx, (input_ids, labels) in enumerate(train_loader):
            input_ids = input_ids.to(device)
            labels = labels.to(device)

            # Forward
            if use_dp:
                # DataParallel returns averaged loss; tensions from first GPU
                raw_model = model.module
                loss, logits, tensions = raw_model(input_ids, labels)
            else:
                loss, logits, tensions = model(input_ids, labels) if not use_fsdp else model.module(input_ids, labels)

            loss = loss / args.grad_accum

            # Backward
            loss.backward()

            n_tokens = (labels != -100).sum().item()
            epoch_loss += loss.item() * args.grad_accum * n_tokens
            epoch_tokens += n_tokens
            log_tensions.extend([t.item() for t in tensions])

            # Optimizer step
            if (batch_idx + 1) % args.grad_accum == 0:
                torch.nn.utils.clip_grad_norm_(trainable_params, args.max_grad_norm)
                optimizer.step()
                optimizer.zero_grad()

                # LR warmup then cosine
                global_step += 1
                if global_step <= warmup_steps:
                    lr_scale = global_step / warmup_steps
                    for pg in optimizer.param_groups:
                        pg["lr"] = args.lr * lr_scale
                else:
                    scheduler.step()

                # ── Logging ──
                if is_main and global_step % args.log_every == 0:
                    curr_loss = epoch_loss / max(epoch_tokens, 1)
                    curr_ppl = math.exp(min(curr_loss, 100))
                    t_mean = sum(log_tensions[-100:]) / max(len(log_tensions[-100:]), 1)
                    t_std = (sum((t - t_mean) ** 2 for t in log_tensions[-100:])
                             / max(len(log_tensions[-100:]), 1)) ** 0.5

                    # Get alpha stats
                    raw = model.module if (use_dp or use_fsdp) else model
                    alpha_mean = raw.get_alpha_stats()["mean"] if hasattr(raw, "get_alpha_stats") else 0.5
                    curr_lr = optimizer.param_groups[0]["lr"]
                    elapsed = time.time() - train_start

                    print(f"{global_step:>6} | {curr_loss:>8.4f} | {curr_ppl:>10.2f} | "
                          f"{t_mean:>8.4f} | {t_std:>8.4f} | {alpha_mean:>7.4f} | "
                          f"{curr_lr:>10.2e} | {elapsed:>5.0f}s")

                # ── Evaluation ──
                if is_main and global_step % args.eval_every == 0:
                    raw = model.module if (use_dp or use_fsdp) else model
                    val_metrics = evaluate(raw, val_loader, device, max_batches=50)

                    print(f"\n  === Eval @ step {global_step} ===")
                    print(f"  Val Loss: {val_metrics['loss']:.4f}")
                    print(f"  Val PPL:  {val_metrics['ppl']:.2f}")
                    print(f"  Tension:  mean={val_metrics['tension_mean']:.4f}  std={val_metrics['tension_std']:.4f}")
                    if baseline_ppl:
                        ratio = val_metrics["ppl"] / baseline_ppl
                        print(f"  vs Baseline: {val_metrics['ppl']:.2f} / {baseline_ppl:.2f} = {ratio:.3f}x")

                    # Alpha distribution
                    alpha_stats = raw.get_alpha_stats()
                    print(f"  Alpha (sigmoid): mean={alpha_stats['mean']:.4f}  "
                          f"min={alpha_stats['min']:.4f}  max={alpha_stats['max']:.4f}")

                    # Per-layer tension histogram (ASCII)
                    tension_stats = raw.get_tension_stats(
                        [torch.tensor(t) for t in [val_metrics["tension_mean"]] * 32]
                    )
                    print()

                    if val_metrics["ppl"] < best_val_ppl:
                        best_val_ppl = val_metrics["ppl"]
                        print(f"  NEW BEST PPL: {best_val_ppl:.2f}")

                    print()
                    model.train()

                # ── Checkpoint ──
                if is_main and global_step % args.save_every == 0:
                    ckpt_dir = os.path.join(args.output, f"checkpoint-{global_step}")
                    os.makedirs(ckpt_dir, exist_ok=True)
                    raw = model.module if (use_dp or use_fsdp) else model
                    torch.save(raw.state_dict(), os.path.join(ckpt_dir, "anima_state_dict.pt"))
                    torch.save({
                        "step": global_step,
                        "optimizer": optimizer.state_dict(),
                        "best_val_ppl": best_val_ppl,
                    }, os.path.join(ckpt_dir, "training_state.pt"))
                    print(f"  Checkpoint saved: {ckpt_dir}")

    # ── Final Evaluation ──
    if is_main:
        print()
        print("=" * 70)
        print("  Training Complete")
        print("=" * 70)
        print()

        raw = model.module if (use_dp or use_fsdp) else model

        # Final val metrics
        val_metrics = evaluate(raw, val_loader, device)
        print(f"  Final Val Loss: {val_metrics['loss']:.4f}")
        print(f"  Final Val PPL:  {val_metrics['ppl']:.2f}")
        print(f"  Best Val PPL:   {best_val_ppl:.2f}")
        if baseline_ppl:
            print(f"  Baseline PPL:   {baseline_ppl:.2f}")
            print(f"  Improvement:    {baseline_ppl:.2f} -> {val_metrics['ppl']:.2f} "
                  f"({(1 - val_metrics['ppl'] / baseline_ppl) * 100:+.1f}%)")
        print()

        # Savant Index
        print("  Computing Savant Index...")
        savant = compute_savant_index(raw, tokenizer, device)
        print(f"  Domain PPLs:")
        for domain, ppl in savant["domain_ppls"].items():
            print(f"    {domain:>10}: {ppl:.2f}")
        print(f"  Savant Index: {savant['savant_index']:.3f}")
        if savant["savant_index"] > 3.0:
            print(f"  --> SAVANT CANDIDATE (SI > 3)")
        print()

        # Alpha distribution
        alpha_stats = raw.get_alpha_stats()
        print(f"  Final Alpha Distribution (sigmoid):")
        print(f"    Mean: {alpha_stats['mean']:.4f}")
        print(f"    Min:  {alpha_stats['min']:.4f}")
        print(f"    Max:  {alpha_stats['max']:.4f}")

        # ASCII histogram of alpha values
        print(f"\n  Alpha per layer:")
        for i, a in enumerate(alpha_stats["per_layer"]):
            bar_len = int(a * 40)
            bar = "#" * bar_len + "." * (40 - bar_len)
            label = "MoE" if a > 0.5 else "Tension"
            print(f"    L{i:02d}: [{bar}] {a:.3f} ({label})")
        print()

        # Tension distribution
        print(f"  Final Tension Stats:")
        print(f"    Mean: {val_metrics['tension_mean']:.6f}")
        print(f"    Std:  {val_metrics['tension_std']:.6f}")

        total_time = time.time() - train_start
        print(f"\n  Total training time: {total_time / 60:.1f} min")

        # Save final model
        final_dir = os.path.join(args.output, "final")
        os.makedirs(final_dir, exist_ok=True)
        torch.save(raw.state_dict(), os.path.join(final_dir, "anima_state_dict.pt"))

        # Copy configs
        for fname in ["anima_config.json", "config.json", "tokenizer.json",
                       "tokenizer_config.json", "special_tokens_map.json"]:
            src = os.path.join(args.model, fname)
            if os.path.exists(src):
                import shutil
                shutil.copy2(src, os.path.join(final_dir, fname))

        print(f"  Final model saved: {final_dir}")

    if use_fsdp:
        dist.destroy_process_group()


# ─────────────────────────────────────────
# CLI
# ─────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Fine-tune AnimaLM (tension-based consciousness engine)"
    )

    # Model
    parser.add_argument("--model", type=str, default="./anima-lm-7b",
                        help="Path to converted AnimaLM directory")
    parser.add_argument("--output", type=str, default="./anima-lm-7b-finetuned",
                        help="Output directory for checkpoints")

    # Training
    parser.add_argument("--epochs", type=int, default=3,
                        help="Number of training epochs (default: 3)")
    parser.add_argument("--batch-size", type=int, default=2,
                        help="Per-GPU batch size (default: 2)")
    parser.add_argument("--grad-accum", type=int, default=8,
                        help="Gradient accumulation steps (default: 8, effective batch=16)")
    parser.add_argument("--lr", type=float, default=2e-4,
                        help="Peak learning rate (default: 2e-4)")
    parser.add_argument("--weight-decay", type=float, default=0.01,
                        help="Weight decay (default: 0.01)")
    parser.add_argument("--max-grad-norm", type=float, default=1.0,
                        help="Max gradient norm for clipping (default: 1.0)")
    parser.add_argument("--warmup-steps", type=int, default=100,
                        help="LR warmup steps (default: 100)")
    parser.add_argument("--seq-len", type=int, default=512,
                        help="Sequence length (default: 512)")

    # Multi-GPU
    parser.add_argument("--fsdp", action="store_true",
                        help="Use FSDP for multi-GPU (recommended, use with torchrun)")
    parser.add_argument("--dp", action="store_true",
                        help="Use DataParallel for multi-GPU")

    # Logging
    parser.add_argument("--log-every", type=int, default=10,
                        help="Log every N optimizer steps (default: 10)")
    parser.add_argument("--eval-every", type=int, default=100,
                        help="Evaluate every N optimizer steps (default: 100)")
    parser.add_argument("--save-every", type=int, default=500,
                        help="Save checkpoint every N optimizer steps (default: 500)")

    # Evaluation
    parser.add_argument("--baseline", action="store_true",
                        help="Compute original Mistral 7B PPL for comparison")

    args = parser.parse_args()
    train(args)


if __name__ == "__main__":
    main()
