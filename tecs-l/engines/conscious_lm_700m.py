#!/usr/bin/env python3
"""Conscious LM 700M — RTX 5070 Safe Limit Model

Perfect number 6 extension: 24 layers, 1024d, 16 heads, vocab=256 bytes
RTX 5070 (12GB): inference ✅ (2.8GB), training ⚠️ (9GB)
A100 (80GB): training ✅ comfortable

Training: A100 ~2-3 hours
Inference: RTX 5070 or Mac MPS
"""
import torch
import torch.nn as nn
import torch.nn.functional as F
import math
import numpy as np
import os
import time

from conscious_lm import PureFieldFFN, CausalSelfAttention, ConsciousBlock, ConsciousLM
from conscious_lm_100m import prepare_large_data, train_100m, generate


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Conscious LM 700M")
    parser.add_argument("--epochs", type=int, default=2)
    parser.add_argument("--batch_size", type=int, default=32)
    parser.add_argument("--block_size", type=int, default=512)
    parser.add_argument("--lr", type=float, default=2e-4)
    parser.add_argument("--prompt", type=str, default="hello")
    parser.add_argument("--checkpoint", type=str, default="conscious_lm_700m.pt")
    parser.add_argument("--generate_only", action="store_true")
    args = parser.parse_args()

    device = "cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu"
    print(f"Device: {device}")

    # 700M: 24 layers, 1024d, 16 heads
    model = ConsciousLM(
        vocab_size=256,
        d_model=1024,
        n_head=16,
        n_layer=24,
        block_size=args.block_size,
        dropout=0.1,
    )
    print(f"Parameters: {model.count_params():,}")

    if args.generate_only:
        model.load_state_dict(torch.load(args.checkpoint, weights_only=True, map_location=device))
        text, tensions = generate(model, args.prompt.encode("utf-8"), device=device)
        print(f"\n{text}")
    else:
        data = prepare_large_data()
        model = train_100m(model, data, epochs=args.epochs,
                          batch_size=args.batch_size, block_size=args.block_size,
                          lr=args.lr, device=device)
        torch.save(model.state_dict(), args.checkpoint)
        print(f"Saved to {args.checkpoint}")

        for prompt in ["hello ", "consciousness is ", "def forward("]:
            text, tensions = generate(model, prompt.encode("utf-8"), max_new=200, device=device)
            print(f"\n  Prompt: {prompt}")
            print(f"  Output: {text[:200]}")
            print(f"  Tension: mean={np.mean(tensions):.2f}, std={np.std(tensions):.2f}")