#!/usr/bin/env python3
"""
Korean conversation SFT data preparation script
For ConsciousLM 700M (byte-level, vocab=256)

Usage:
    pip install datasets
    python3 prepare_korean_sft.py

Output: data/korean_sft.bin (numpy uint8)
"""

import os
import sys
import json
import numpy as np
from collections import Counter

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
OUTPUT_DIR = "data"
OUTPUT_PATH = os.path.join(OUTPUT_DIR, "korean_sft.bin")
MIN_CONVERSATIONS = 100_000
TARGET_BYTES = 50 * 1024 * 1024  # 50MB

# Special tokens (encoded as UTF-8 bytes)
USER_TOKEN = "<|user|>"
ASSISTANT_TOKEN = "<|assistant|>"
EOS_TOKEN = "<|eos|>"

# ---------------------------------------------------------------------------
# Dataset source definitions
# ---------------------------------------------------------------------------
SOURCES = [
    {
        "name": "beomi/KoAlpaca-v1.1a",
        "split": "train",
        "format": "koalpaca",
    },
    {
        "name": "kyujinpy/KOR-OpenOrca-Platypus-v3",
        "split": "train",
        "format": "openorca",
    },
    {
        "name": "squarelike/OpenOrca-gugugo-ko",
        "split": "train",
        "format": "gugugo",
    },
    {
        "name": "nlpai-lab/kullm-v2",
        "split": "train",
        "format": "openorca",
    },
]


def format_ko_chatgpt(example):
    """heegyu/ko-chatgpt-data format -> conversation string."""
    # Fields: instruction, output (or input/output)
    user_msg = example.get("instruction", "") or example.get("input", "")
    if not user_msg:
        return None
    assistant_msg = example.get("output", "")
    if not assistant_msg:
        return None

    # If input field exists separately, append to instruction
    extra_input = example.get("input", "")
    if extra_input and extra_input != user_msg:
        user_msg = f"{user_msg}\n{extra_input}"

    return f"{USER_TOKEN} {user_msg.strip()} {ASSISTANT_TOKEN} {assistant_msg.strip()} {EOS_TOKEN}"


def format_openorca(example):
    """kyujinpy/KOR-OpenOrca-Platypus-v3 format."""
    # Fields: instruction, input, output
    user_msg = example.get("instruction", "")
    extra = example.get("input", "")
    if extra:
        user_msg = f"{user_msg}\n{extra}" if user_msg else extra
    if not user_msg:
        return None
    assistant_msg = example.get("output", "")
    if not assistant_msg:
        return None
    return f"{USER_TOKEN} {user_msg.strip()} {ASSISTANT_TOKEN} {assistant_msg.strip()} {EOS_TOKEN}"


def format_koalpaca(example):
    """beomi/KoAlpaca-v1.1a format."""
    # Fields: instruction, output
    user_msg = example.get("instruction", "")
    if not user_msg:
        return None
    assistant_msg = example.get("output", "")
    if not assistant_msg:
        return None
    return f"{USER_TOKEN} {user_msg.strip()} {ASSISTANT_TOKEN} {assistant_msg.strip()} {EOS_TOKEN}"


def format_gugugo(example):
    """squarelike/OpenOrca-gugugo-ko format."""
    # Fields: system_prompt, question, response
    user_msg = example.get("question", "")
    if not user_msg:
        return None
    assistant_msg = example.get("response", "")
    if not assistant_msg:
        return None
    return f"{USER_TOKEN} {user_msg.strip()} {ASSISTANT_TOKEN} {assistant_msg.strip()} {EOS_TOKEN}"


FORMATTERS = {
    "ko_chatgpt": format_ko_chatgpt,
    "openorca": format_openorca,
    "koalpaca": format_koalpaca,
    "gugugo": format_gugugo,
}


def load_and_format_source(source_info):
    """Load and format data from a single source."""
    from datasets import load_dataset

    name = source_info["name"]
    split = source_info["split"]
    fmt = source_info["format"]
    formatter = FORMATTERS[fmt]

    print(f"\n{'='*60}")
    print(f"  Loading: {name} (split={split})")
    print(f"{'='*60}")

    try:
        ds = load_dataset(name, split=split)
    except Exception as e:
        print(f"  [WARN] Failed to load {name}: {e}")
        print(f"  Skipping this source.")
        return []

    print(f"  Raw examples: {len(ds):,}")

    # Check available fields
    if len(ds) > 0:
        print(f"  Fields: {list(ds[0].keys())}")

    conversations = []
    skipped = 0
    for example in ds:
        text = formatter(example)
        if text is None:
            skipped += 1
            continue
        # Minimum length filter (remove conversations that are too short)
        if len(text.encode("utf-8")) < 20:
            skipped += 1
            continue
        conversations.append(text)

    print(f"  Formatted: {len(conversations):,} conversations")
    print(f"  Skipped: {skipped:,}")

    return conversations


def compute_stats(conversations, byte_data):
    """Calculate and output data statistics."""
    total_bytes = len(byte_data)
    total_convs = len(conversations)

    # Byte length distribution
    lengths = [len(c.encode("utf-8")) for c in conversations]
    lengths_arr = np.array(lengths)

    print(f"\n{'='*60}")
    print(f"  Data Statistics")
    print(f"{'='*60}")
    print(f"  Total conversations: {total_convs:>12,}")
    print(f"  Total bytes:         {total_bytes:>12,} ({total_bytes/1024/1024:.1f} MB)")
    print(f"  Average length:      {lengths_arr.mean():>12.0f} bytes/conv")
    print(f"  Median length:       {np.median(lengths_arr):>12.0f} bytes/conv")
    print(f"  Minimum length:      {lengths_arr.min():>12,} bytes")
    print(f"  Maximum length:      {lengths_arr.max():>12,} bytes")
    print(f"  Std deviation:       {lengths_arr.std():>12.0f} bytes")

    # Length distribution histogram (ASCII)
    print(f"\n  Length distribution (bytes):")
    bins = [0, 100, 200, 500, 1000, 2000, 5000, 10000, 50000, float("inf")]
    labels = ["<100", "100-200", "200-500", "500-1K", "1K-2K", "2K-5K", "5K-10K", "10K-50K", "50K+"]
    max_bar = 40
    counts = []
    for i in range(len(bins) - 1):
        c = int(np.sum((lengths_arr >= bins[i]) & (lengths_arr < bins[i+1])))
        counts.append(c)
    max_count = max(counts) if counts else 1
    for label, count in zip(labels, counts):
        bar_len = int(count / max_count * max_bar)
        bar = "#" * bar_len
        pct = count / total_convs * 100
        print(f"    {label:>8s} | {bar:<{max_bar}s} {count:>8,} ({pct:5.1f}%)")

    # Byte value distribution (Korean in 0xEA-0xED range)
    byte_counts = Counter(byte_data)
    korean_bytes = sum(byte_counts.get(b, 0) for b in range(0xEA, 0xEE))
    ascii_bytes = sum(byte_counts.get(b, 0) for b in range(0x20, 0x7F))
    print(f"\n  Byte distribution:")
    print(f"    Korean range (0xEA-0xED): {korean_bytes:>12,} ({korean_bytes/total_bytes*100:.1f}%)")
    print(f"    ASCII range (0x20-0x7E):  {ascii_bytes:>12,} ({ascii_bytes/total_bytes*100:.1f}%)")
    print(f"    Other:                    {total_bytes-korean_bytes-ascii_bytes:>12,}")

    # Target achievement
    print(f"\n  Target achievement:")
    conv_ok = total_convs >= MIN_CONVERSATIONS
    byte_ok = total_bytes >= TARGET_BYTES
    print(f"    Conversations >= {MIN_CONVERSATIONS:,}: {'OK' if conv_ok else 'FAIL'} ({total_convs:,})")
    print(f"    Bytes >= {TARGET_BYTES/1024/1024:.0f}MB: {'OK' if byte_ok else 'FAIL'} ({total_bytes/1024/1024:.1f}MB)")

    if not conv_ok:
        print(f"\n  [WARN] Insufficient conversations. Will augment with repetition.")
    if not byte_ok:
        print(f"\n  [WARN] Insufficient bytes. Will augment with repetition.")


def preview_samples(conversations, n=3):
    """Preview samples."""
    print(f"\n{'='*60}")
    print(f"  Sample Preview ({n} samples)")
    print(f"{'='*60}")
    import random
    random.seed(42)
    indices = random.sample(range(len(conversations)), min(n, len(conversations)))
    for i, idx in enumerate(indices):
        text = conversations[idx]
        # Truncate if too long
        display = text[:500] + "..." if len(text) > 500 else text
        byte_repr = text.encode("utf-8")[:80]
        print(f"\n  --- Sample {i+1} (idx={idx}, {len(text.encode('utf-8')):,} bytes) ---")
        print(f"  Text: {display}")
        print(f"  Bytes[:80]: {list(byte_repr)}")


def main():
    print("=" * 60)
    print("  Korean Conversation SFT Data Preparation")
    print(f"  ConsciousLM 700M (byte-level, vocab=256)")
    print(f"  Output: {OUTPUT_PATH}")
    print("=" * 60)

    # Check datasets library
    try:
        from datasets import load_dataset
    except ImportError:
        print("\n  [ERROR] 'datasets' package required.")
        print("  Install: pip install datasets")
        sys.exit(1)

    # Collect data from all sources
    all_conversations = []
    source_stats = []

    for source in SOURCES:
        convs = load_and_format_source(source)
        source_stats.append((source["name"], len(convs)))
        all_conversations.extend(convs)

    print(f"\n{'='*60}")
    print(f"  Collection Results by Source")
    print(f"{'='*60}")
    for name, count in source_stats:
        print(f"    {name:<45s} {count:>8,}")
    print(f"    {'─'*45} {'─'*8}")
    print(f"    {'TOTAL':<45s} {len(all_conversations):>8,}")

    if len(all_conversations) == 0:
        print("\n  [ERROR] No conversations collected. Check network connection.")
        sys.exit(1)

    # Shuffle
    import random
    random.seed(42)
    random.shuffle(all_conversations)

    # Augment with repetition if insufficient conversations
    if len(all_conversations) < MIN_CONVERSATIONS:
        print(f"\n  Augmenting conversations: {len(all_conversations):,} -> {MIN_CONVERSATIONS:,}")
        repeats = (MIN_CONVERSATIONS // len(all_conversations)) + 1
        all_conversations = (all_conversations * repeats)[:MIN_CONVERSATIONS]
        random.shuffle(all_conversations)

    # Convert to UTF-8 bytes
    print(f"\n  Converting to UTF-8 bytes...")
    # Separate conversations with double newlines (serves as separator at byte level)
    separator = b"\n\n"
    byte_parts = []
    for conv in all_conversations:
        byte_parts.append(conv.encode("utf-8"))
    combined = separator.join(byte_parts)

    # Augment with repetition if insufficient bytes
    if len(combined) < TARGET_BYTES:
        print(f"  Augmenting bytes: {len(combined):,} -> {TARGET_BYTES:,}")
        repeats = (TARGET_BYTES // len(combined)) + 1
        combined = (separator.join(byte_parts) + separator) * repeats
        combined = combined[:TARGET_BYTES]

    # Convert to numpy uint8 and save
    byte_data = np.frombuffer(combined, dtype=np.uint8).copy()

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    byte_data.tofile(OUTPUT_PATH)
    print(f"\n  Save complete: {OUTPUT_PATH}")
    print(f"  File size: {os.path.getsize(OUTPUT_PATH):,} bytes ({os.path.getsize(OUTPUT_PATH)/1024/1024:.1f} MB)")

    # Output statistics
    compute_stats(all_conversations, byte_data)

    # Preview samples
    preview_samples(all_conversations)

    # Validation: reload saved file to verify
    print(f"\n{'='*60}")
    print(f"  Validation: Saved File Load Test")
    print(f"{'='*60}")
    loaded = np.fromfile(OUTPUT_PATH, dtype=np.uint8)
    print(f"  Loaded shape: {loaded.shape}")
    print(f"  dtype: {loaded.dtype}")
    print(f"  Range: [{loaded.min()}, {loaded.max()}]")
    # Decode first 200 bytes to check
    sample_bytes = bytes(loaded[:200])
    try:
        decoded = sample_bytes.decode("utf-8", errors="replace")
        print(f"  First 200 bytes decoded: {decoded[:200]}")
    except Exception as e:
        print(f"  Decode error: {e}")

    print(f"\n  Complete!")
    print(f"  Usage: data = np.fromfile('{OUTPUT_PATH}', dtype=np.uint8)")
    print(f"         data = torch.tensor(data, dtype=torch.long)")


if __name__ == "__main__":
    main()