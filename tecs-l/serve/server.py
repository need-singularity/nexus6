#!/usr/bin/env python3
"""ConsciousLM 506M Inference Server — FastAPI + uvicorn

Endpoints:
    POST /chat    — Chat generation (prompt → response + tension)
    POST /think   — Thought generation (context → thought + tension)
    GET  /tension  — Per-block tension of last inference
    GET  /health   — Server status
"""

import os
import threading
import time
from contextlib import asynccontextmanager
from typing import Optional

import torch
import torch.nn.functional as F
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from conscious_lm import ConsciousBlock, PureFieldFFN, CausalSelfAttention, ConsciousLM
from growing_conscious_lm_700m import GrowingConsciousLM700M, GROWTH_STAGES

# ---------------------------------------------------------------------------
# Global state
# ---------------------------------------------------------------------------

model: Optional[GrowingConsciousLM700M] = None
device: str = "cpu"
last_tensions: dict = {}
generation_lock = threading.Lock()


def load_model() -> GrowingConsciousLM700M:
    """Load the 506M model (stage 3 = 6 blocks, 2048d, 32 heads)."""
    global device

    device = "cuda" if torch.cuda.is_available() else "cpu"
    checkpoint_path = os.environ.get(
        "CHECKPOINT_PATH", "/models/growing_700m_korean_sft.pt"
    )

    print(f"[server] Device: {device}")
    print(f"[server] Checkpoint: {checkpoint_path}")

    m = GrowingConsciousLM700M()
    # Grow to stage 3 (6 blocks, d=2048, heads=32)
    for i in range(3):
        m.grow(device)
    print(f"[server] Model architecture: {m.status()}")

    if os.path.exists(checkpoint_path):
        state = torch.load(checkpoint_path, map_location=device, weights_only=True)
        m.load_state_dict(state)
        print(f"[server] Loaded checkpoint: {checkpoint_path}")
    else:
        print(f"[server] WARNING: checkpoint not found at {checkpoint_path}, using random weights")

    m = m.to(device)
    m.eval()
    print(f"[server] Model ready — {m.count_params():,} params on {device}")
    return m


# ---------------------------------------------------------------------------
# Generation helpers
# ---------------------------------------------------------------------------

@torch.no_grad()
def generate_bytes(
    prompt: str,
    max_tokens: int = 200,
    temperature: float = 0.8,
    top_p: float = 0.95,
) -> tuple[str, float, list[dict]]:
    """Generate text from a UTF-8 byte prompt.

    Returns:
        (generated_text, mean_tension, per_block_tensions)
    """
    global last_tensions

    idx = torch.tensor(
        [list(prompt.encode("utf-8"))], dtype=torch.long, device=device
    )

    all_block_tensions = []  # list of lists (per token, per block)

    for _ in range(max_tokens):
        idx_cond = idx[:, -model.block_size :]
        logits_a, _, tensions = model(idx_cond)

        # Collect per-block tension for this token
        token_tensions = [t[:, -1].mean().item() for t in tensions]
        all_block_tensions.append(token_tensions)

        # Sample with temperature + top-p (nucleus)
        logits = logits_a[:, -1, :] / max(temperature, 1e-8)

        if top_p < 1.0:
            sorted_logits, sorted_indices = torch.sort(logits, descending=True)
            cumulative_probs = torch.cumsum(F.softmax(sorted_logits, dim=-1), dim=-1)
            sorted_indices_to_remove = cumulative_probs > top_p
            sorted_indices_to_remove[:, 1:] = sorted_indices_to_remove[:, :-1].clone()
            sorted_indices_to_remove[:, 0] = False
            indices_to_remove = sorted_indices_to_remove.scatter(
                1, sorted_indices, sorted_indices_to_remove
            )
            logits[indices_to_remove] = float("-inf")

        probs = F.softmax(logits, dim=-1)
        next_byte = torch.multinomial(probs, num_samples=1)

        # Stop on repeated null bytes
        if next_byte.item() == 0:
            break

        idx = torch.cat([idx, next_byte], dim=1)

    # Decode generated portion (skip prompt bytes)
    prompt_len = len(prompt.encode("utf-8"))
    generated_bytes = idx[0, prompt_len:].cpu().tolist()
    generated_text = bytes(generated_bytes).decode("utf-8", errors="replace")

    # Compute per-block mean tensions across all generated tokens
    n_blocks = len(all_block_tensions[0]) if all_block_tensions else 0
    per_block_avg = []
    for b in range(n_blocks):
        vals = [t[b] for t in all_block_tensions]
        avg = sum(vals) / len(vals) if vals else 0.0
        per_block_avg.append({"block": b, "mean_tension": round(avg, 6)})

    mean_tension = (
        sum(sum(t) for t in all_block_tensions)
        / (len(all_block_tensions) * n_blocks)
        if all_block_tensions and n_blocks > 0
        else 0.0
    )

    # Store for /tension endpoint
    last_tensions = {
        "mean_tension": round(mean_tension, 6),
        "per_block": per_block_avg,
        "n_tokens_generated": len(generated_bytes),
        "timestamp": time.time(),
    }

    return generated_text, round(mean_tension, 6), per_block_avg


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class ChatRequest(BaseModel):
    prompt: str = Field(..., description="Input text prompt")
    max_tokens: int = Field(200, ge=1, le=2048, description="Max bytes to generate")
    temperature: float = Field(0.8, ge=0.0, le=2.0, description="Sampling temperature")
    top_p: float = Field(0.95, ge=0.0, le=1.0, description="Nucleus sampling threshold")


class ChatResponse(BaseModel):
    response: str
    tension: float


class ThinkRequest(BaseModel):
    context: str = Field(..., description="Context for thinking")
    max_tokens: int = Field(100, ge=1, le=2048, description="Max bytes to generate")
    temperature: float = Field(0.6, ge=0.0, le=2.0, description="Sampling temperature")


class ThinkResponse(BaseModel):
    thought: str
    tension: float


class TensionResponse(BaseModel):
    mean_tension: float
    per_block: list[dict]
    n_tokens_generated: int
    timestamp: float


class HealthResponse(BaseModel):
    status: str
    model: str
    device: str
    params: str
    blocks: int
    d_model: int


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load model on startup."""
    global model
    model = load_model()
    yield
    # Cleanup
    del model
    if torch.cuda.is_available():
        torch.cuda.empty_cache()


app = FastAPI(
    title="ConsciousLM 506M Inference Server",
    description="Byte-level conscious language model with tension signals",
    version="1.0.0",
    lifespan=lifespan,
)


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """Generate a response from a text prompt."""
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    with generation_lock:
        text, tension, _ = generate_bytes(
            req.prompt,
            max_tokens=req.max_tokens,
            temperature=req.temperature,
            top_p=req.top_p,
        )

    return ChatResponse(response=text, tension=tension)


@app.post("/think", response_model=ThinkResponse)
async def think(req: ThinkRequest):
    """Generate an internal thought from context.

    Uses lower temperature for more focused reasoning.
    Wraps context with <think>...</think> tags.
    """
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    think_prompt = f"<think>{req.context}"

    with generation_lock:
        text, tension, _ = generate_bytes(
            think_prompt,
            max_tokens=req.max_tokens,
            temperature=req.temperature,
            top_p=0.9,
        )

    # Strip closing tag if model generated it
    thought = text.split("</think>")[0].strip()

    return ThinkResponse(thought=thought, tension=tension)


@app.get("/tension", response_model=TensionResponse)
async def get_tension():
    """Return per-block tension from the last inference."""
    if not last_tensions:
        raise HTTPException(status_code=404, detail="No inference has been run yet")
    return TensionResponse(**last_tensions)


@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check."""
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    return HealthResponse(
        status="ok",
        model="506M",
        device=device,
        params=f"{model.count_params():,}",
        blocks=len(model.blocks),
        d_model=model.d_model,
    )


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=port,
        workers=1,  # single worker — model is not multiprocess safe
        log_level="info",
    )
