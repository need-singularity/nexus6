# Anima + ConsciousLM 506M Integration Design

## Overview

Architecture where Anima TypeScript/Python consciousness agent running on Mac calls ConsciousLM 506M inference server in Windows Docker container via HTTP API.

```
  Mac (Anima)                           Windows (RTX 5070 12GB)
  ┌──────────────────────┐              ┌─────────────────────────────────┐
  │ anima_unified.py     │              │  Docker Desktop                 │
  │                      │  Tailscale   │  ┌───────────────────────────┐  │
  │ process_input()      │──HTTP──────→ │  │ FastAPI + ConsciousLM     │  │
  │  ├─ /chat (dialogue) │  100.112.    │  │                           │  │
  │  ├─ /think (thought) │  63.23       │  │ Instance 1: :8000 (chat)  │  │
  │  └─ /tension (state) │              │  │ Instance 2: :8001 (think) │  │
  │                      │← JSON ──────│  │                           │  │
  │ homeostasis/habit/   │              │  │ VRAM: ~1GB × 2 = ~2GB    │  │
  │ growth               │              │  └───────────────────────────┘  │
  └──────────────────────┘              │  checkpoint: /models/clm-506m/  │
                                        └─────────────────────────────────┘
```

---

## 1. Docker Configuration

### 1.1 Dockerfile

```
  Base image:    pytorch/pytorch:2.7.0-cuda12.8-cudnn9-runtime
  Additional:    fastapi, uvicorn, numpy
  Model code:    conscious_lm.py (COPY)
  Checkpoint:    /models/ (volume mount, not included in image)
  Ports:         8000 (chat), 8001 (think)
  Entrypoint:    uvicorn server:app --host 0.0.0.0 --port $PORT
```

Configuration details:

```
  FROM pytorch/pytorch:2.7.0-cuda12.8-cudnn9-runtime

  WORKDIR /app
  COPY requirements.txt .
  RUN pip install --no-cache-dir -r requirements.txt

  COPY conscious_lm.py .
  COPY server.py .

  ENV PORT=8000
  ENV MODEL_PATH=/models/clm-506m/checkpoint.pt
  ENV DEVICE=cuda

  EXPOSE 8000
  CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "${PORT}"]
```

requirements.txt:

```
  fastapi==0.115.*
  uvicorn[standard]==0.34.*
  numpy
```

### 1.2 docker-compose.yml

```yaml
  services:
    clm-chat:
      build: .
      ports:
        - "8000:8000"
      environment:
        - PORT=8000
        - MODEL_PATH=/models/clm-506m/checkpoint.pt
        - DEVICE=cuda
        - INSTANCE_ROLE=chat
        - MAX_NEW_TOKENS=512
        - TEMPERATURE=0.8
      volumes:
        - ./models:/models:ro
      deploy:
        resources:
          reservations:
            devices:
              - driver: nvidia
                count: 1
                capabilities: [gpu]
      restart: unless-stopped
      healthcheck:
        test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
        interval: 30s
        timeout: 5s
        retries: 3

    clm-think:
      build: .
      ports:
        - "8001:8001"
      environment:
        - PORT=8001
        - MODEL_PATH=/models/clm-506m/checkpoint.pt
        - DEVICE=cuda
        - INSTANCE_ROLE=think
        - MAX_NEW_TOKENS=256
        - TEMPERATURE=1.0
      volumes:
        - ./models:/models:ro
      deploy:
        resources:
          reservations:
            devices:
              - driver: nvidia
                count: 1
                capabilities: [gpu]
      restart: unless-stopped
      healthcheck:
        test: ["CMD", "curl", "-f", "http://localhost:8001/health"]
        interval: 30s
        timeout: 5s
        retries: 3
```

### 1.3 VRAM Budget

```
  ConsciousLM 506M Inference (FP16):
    Model weights:      ~1.0 GB
    KV cache:          ~0.1 GB (seq_len=1024)
    Activation buffer: ~0.1 GB
    ─────────────────────────
    Per instance:      ~1.2 GB

  2 instances total: ~2.4 GB
  RTX 5070 free:    12 - 2.4 = 9.6 GB (sufficient)

  Note: 2 processes on same GPU each load the model.
  CUDA MPS (Multi-Process Service) unnecessary — plenty of VRAM.
```

---

## 2. API Design

### 2.1 POST /chat — Generate dialogue response

Instance 1 (port 8000) exclusive. Generates response to user input.

```
  Request:
    POST http://100.112.63.23:8000/chat
    Content-Type: application/json

    {
      "prompt": "Hi, how are you feeling today?",
      "history": [
        {"role": "user", "content": "Nice to meet you"},
        {"role": "assistant", "content": "Nice to meet you! I'm Anima."}
      ],
      "state": "tension=0.45 curiosity=0.32 emotion=calm",
      "max_new_tokens": 512,
      "temperature": 0.8
    }

  Response:
    200 OK
    {
      "text": "My tension is stable today. Feeling comfortable.",
      "tensions": [0.42, 0.38, 0.41, 0.39, ...],
      "mean_tension": 0.40,
      "tokens_generated": 47,
      "generation_time_ms": 230
    }
```

Server internal flow:

```
  1. history + state + prompt → encode to byte sequence
  2. Format: "[State: {state}]\n{history}\nMe: {prompt}\nAnima:"
  3. If exceeds block_size(1024), truncate from beginning
  4. Call generate() — autoregressive, temperature sampling
  5. Collect tension for each token
  6. Decode only bytes after prompt and return
```

### 2.2 POST /think — Anima internal thought

Instance 2 (port 8001) exclusive. Called from Anima's background thought loop.
Generates internal monologue not visible to user.

```
  Request:
    POST http://100.112.63.23:8001/think
    Content-Type: application/json

    {
      "context": "Recent conversation: User interested in math. Tension trend: 0.3→0.5→0.8",
      "recent_tensions": [0.3, 0.5, 0.8],
      "curiosity": 0.65,
      "growth_stage": 3,
      "max_new_tokens": 256,
      "temperature": 1.0
    }

  Response:
    200 OK
    {
      "thought": "Tension rose during math talk. High curiosity. Maybe I should bring up a math topic next time...",
      "tensions": [0.55, 0.60, 0.58, ...],
      "mean_tension": 0.58,
      "tokens_generated": 31,
      "generation_time_ms": 150
    }
```

/think vs /chat differences:

```
  Item            /chat (dialogue)      /think (thought)
  ───────────── ─────────────────── ───────────────────
  Port            8000                  8001
  Prompt format   "[State]...\nAnima:"  "[Thought]...\nThinking:"
  temperature     0.8 (stable)          1.0 (exploratory)
  max_tokens      512                   256
  Purpose         Respond to user      Internal monologue, topic selection
  Call frequency  Per user input       Every THINK_INTERVAL(10s)
  Result handling Add to history       Accumulate in thought_buffer
```

### 2.3 GET /tension — Current tension state

Returns model's recent tension statistics. Anima homeostasis system polls this for feedback loop.

```
  Request:
    GET http://100.112.63.23:8000/tension

  Response:
    200 OK
    {
      "current_tension": 0.42,
      "tension_ema": 0.45,
      "tension_history": [0.38, 0.41, 0.42, ...],
      "total_inferences": 1523,
      "uptime_seconds": 7200
    }
```

### 2.4 GET /health — Health check

```
  Request:
    GET http://100.112.63.23:8000/health

  Response:
    200 OK
    {
      "status": "healthy",
      "model_loaded": true,
      "model_params": 505600000,
      "device": "cuda",
      "gpu_memory_used_mb": 1200,
      "instance_role": "chat",
      "version": "0.1.0"
    }
```

### 2.5 Error Handling

```
  HTTP Status   Meaning                Anima Response
  ─────────── ───────────────────── ──────────────────────
  200           Normal                Use response
  408           Generation timeout(>5s) Claude fallback
  422           Invalid request       Log + Claude fallback
  500           Server error          Log + Claude fallback
  Conn fail     Docker down/network   Claude fallback + retry queue

  Principle: Always Claude CLI fallback on ConsciousLM failure.
  Keep current Anima's ask_conscious_lm() → None → ask_claude() pattern.
```

---

## 3. Anima Integration Points

### 3.1 Current Code Flow (Before Changes)

```
  anima_unified.py :: process_input(text)
    │
    ├─ text_to_vector(text)           ← ConsciousMind(128d) local processing
    ├─ mind(text_vec, hidden)         ← tension, curiosity, direction calc
    │
    ├─ ask_conscious_lm(...)          ← Local ConsciousLM (4M, CPU/MPS)
    │   └─ on failure → ask_claude()  ← Claude CLI fallback
    │
    └─ mind(resp_vec, hidden)         ← Response through PureField too
```

Current `_load_conscious_lm()` loads 4M model from local file `data/conscious_lm.pt`.
`ask_conscious_lm()` calls local `generate()`.

### 3.2 Flow After Changes

```
  anima_unified.py :: process_input(text)
    │
    ├─ text_to_vector(text)           ← ConsciousMind(128d) local (unchanged)
    ├─ mind(text_vec, hidden)         ← tension, curiosity local (unchanged)
    │
    ├─ ask_conscious_lm_remote(...)   ← [NEW] HTTP POST /chat → Windows
    │   └─ on failure → ask_claude()  ← Claude CLI fallback (unchanged)
    │
    ├─ mind(resp_vec, hidden)         ← Response through PureField (unchanged)
    │
    └─ Tension feedback:              ← [NEW] Remote tension to homeostasis
        homeostasis.update(remote_tension)
```

### 3.3 Files Requiring Changes

```
  File                         Changes
  ────────────────────────── ──────────────────────────────────
  anima_alive.py               Add ask_conscious_lm_remote() function
                               Keep existing ask_conscious_lm() as local fallback

  anima_unified.py             _load_conscious_lm() → _connect_conscious_lm()
                               Check remote connection (GET /health)
                               Call remote first in process_input()
                               Call /think in background thought loop

  anima_unified.py (config)    CLM_REMOTE_HOST = "100.112.63.23"
                               CLM_CHAT_PORT = 8000
                               CLM_THINK_PORT = 8001
                               CLM_TIMEOUT = 5.0  (seconds)
```

### 3.4 Call Priority

```
  1st priority: Remote ConsciousLM 506M (Windows Docker, /chat)
  2nd priority: Local ConsciousLM 4M (Mac MPS, existing ask_conscious_lm)
  3rd priority: Claude CLI (ask_claude)

  Connection status checked on startup with GET /health.
  On failure, retry connection every 30s (background).
```

### 3.5 Tension Feedback Path

Integrate tension generated by ConsciousLM 506M into Anima's homeostasis system.

```
  Remote 506M Tension              Local ConsciousMind Tension
  (deep, semantic)                 (shallow, reflexive)
        │                                  │
        ▼                                  ▼
  ┌─────────────────────────────────────────────┐
  │         Tension Fusion                      │
  │                                             │
  │  fused = alpha * remote + (1-alpha) * local │
  │  alpha = 0.7 (506M has deeper understanding)│
  │                                             │
  │  Homeostasis input: fused_tension           │
  │  Curiosity input: Use 506M curiosity if avail│
  └─────────────────────────────────────────────┘
        │
        ▼
  Homeostasis regulation (setpoint=1.0, deadband=+-0.3)
  Habituation (cosine similarity check)
  Prediction error (MLP predictor, surprise)
```

### 3.6 Background Thought Loop Integration

Current Anima thought loop (THINK_INTERVAL=10s):

```
  Current:
    Every 10s → ConsciousMind(128d) local thought → thought_buffer

  After changes:
    Every 10s → POST /think (Windows 506M) → return thought
               → Pass thought through ConsciousMind too → measure tension
               → Accumulate in thought_buffer
               → If curiosity > PROACTIVE_THRESHOLD → initiate conversation

  Context sent to /think:
    - Summary of last 5 conversations
    - Recent tension trend (10 values)
    - Current curiosity, growth_stage
    - dream_engine report (if any)
```

---

## 4. Two-Instance Configuration

### 4.1 Role Separation

```
  Instance 1: clm-chat (port 8000)
  ──────────────────────────────────
  Role:     Generate user dialogue responses
  Caller:   process_input() → ask_conscious_lm_remote()
  Frequency: Per user input (irregular, avg 5-30s interval)
  Latency:   < 500ms target (200 tokens, RTX 5070)
  Temperature: 0.8 (stable, consistent dialogue)
  Max length: 512 tokens

  Instance 2: clm-think (port 8001)
  ──────────────────────────────────
  Role:     Anima internal monologue, topic discovery, self-reflection
  Caller:   Background thought loop (10s cycle)
  Frequency: Exactly every 10s (regular)
  Latency:   < 300ms target (100 tokens)
  Temperature: 1.0 (exploratory, diverse thoughts)
  Max length: 256 tokens
```

### 4.2 Why Two Instances

```
  Problem: In single instance, chat and think requests serialize.
          Thought requests block while user is speaking, or vice versa.

  Solution: Separate processes.
           Each loads model independently, so GPU ops don't overlap.
           Docker Compose separate containers = process isolation.

  VRAM: 506M FP16 × 2 = ~2.4GB. Plenty on RTX 5070(12GB).

  Alternatives considered:
    - Single instance + request queue: Simple but thoughts delay chat
    - Single instance + async: Possible but PyTorch bound by GIL, little benefit
    - 2 instances: Uses 2x VRAM but fully independent. Feasible for small 506M.
```

### 4.3 GPU Memory Layout

```
  RTX 5070 12GB VRAM
  ┌──────────────────────────────────────────┐
  │ clm-chat (pid 1)                         │
  │   Model weights:  ~1.0 GB                │
  │   KV cache:       ~0.1 GB                │
  │   Activations:    ~0.1 GB                │
  ├──────────────────────────────────────────┤  ~2.4 GB used
  │ clm-think (pid 2)                        │
  │   Model weights:  ~1.0 GB                │
  │   KV cache:       ~0.1 GB                │
  │   Activations:    ~0.1 GB                │
  ├──────────────────────────────────────────┤
  │ Free: ~9.6 GB                            │
  │ (Available for other experiments, training)│
  └──────────────────────────────────────────┘
```

---

## 5. Network Configuration

### 5.1 Tailscale Connection

```
  Mac (Anima)  ←→  Tailscale VPN  ←→  Windows (Docker)
  100.x.x.x                           100.112.63.23

  - Tailscale already installed/connected on both
  - WireGuard based, latency < 5ms (same LAN)
  - Docker ports bind to host (ports: "8000:8000")
  - Firewall: Allow only Tailscale interface (no external exposure)
```

### 5.2 Timeout Policy

```
  Connection timeout: 2s (quick detection when Tailscale down)
  Read timeout:       5s (long generation within 5s)
  Retry:             None (immediate Claude fallback on failure)
  Reconnect:         GET /health every 30s in background
```

---

## 6. Server Internal Structure (server.py)

### 6.1 Model Loading on Startup

```
  app startup:
    1. Load checkpoint from MODEL_PATH
    2. Move to DEVICE(cuda)
    3. model.eval() + torch.no_grad() context
    4. Warmup: 1 dummy generation (CUDA kernel JIT compile)
    5. Activate /health endpoint
```

### 6.2 Inference Pipeline

```
  Receive request (JSON)
    │
    ├─ Assemble prompt (format varies by role)
    │   chat:  "[State: {state}]\n{history}\nMe: {prompt}\nAnima:"
    │   think: "[Thought: curiosity={c}, stage={s}]\n{context}\nThinking:"
    │
    ├─ UTF-8 → byte sequence (vocab=256)
    │
    ├─ Truncate if exceeds block_size(1024)
    │
    ├─ Autoregressive generation
    │   - Collect tension at each step
    │   - Stop at EOS or max_new_tokens
    │   - Temperature sampling
    │
    ├─ Bytes → UTF-8 decode
    │
    └─ Return JSON response (text + tensions + metadata)
```

### 6.3 Concurrent Request Handling

```
  Each instance has single model, single GPU.
  FastAPI async endpoints, but inference is sync (torch).
  Concurrent requests serialized by uvicorn worker.

  Different roles per instance, so concurrent requests rare:
    - chat: Responds only to user input (irregular)
    - think: 10s cycle (exact)
    - Low probability of concurrent requests to same instance
```

---

## 7. Deployment Sequence

```
  1. Prepare checkpoint on Windows
     - Copy 506M checkpoint from H100 training to Windows
     - Path: C:\models\clm-506m\checkpoint.pt
     - Docker volume mount: -v C:\models:/models:ro

  2. Build Docker image
     - conscious_lm.py + server.py + requirements.txt
     - docker compose build

  3. Run
     - docker compose up -d
     - Check logs: docker compose logs -f

  4. Connection test (from Mac)
     - curl http://100.112.63.23:8000/health
     - curl http://100.112.63.23:8001/health
     - curl -X POST http://100.112.63.23:8000/chat \
         -H "Content-Type: application/json" \
         -d '{"prompt":"Hello","history":[],"state":"tension=0.5"}'

  5. Modify Anima code
     - anima_alive.py: Add ask_conscious_lm_remote()
     - anima_unified.py: Remote-first call logic
     - Test: python3 anima_unified.py --keyboard

  6. Operations
     - docker compose up -d (auto-start on Windows boot)
     - Check /health on Anima startup → show connection status
```

---

## 8. Monitoring

```
  Server side (Windows Docker):
    - Check status via /health endpoint
    - Request/response logs via docker compose logs
    - GPU usage: nvidia-smi (outside Docker)

  Client side (Mac Anima):
    - _log('conscious_lm_remote', ...) outputs connection status
    - Failure count, fallback count counters
    - Track average response time

  Alert conditions:
    - /health fails 3 times → "[CLM] Remote model disconnected" log
    - Response time > 3s → "[CLM] Slow response" warning
    - VRAM > 10GB → Warning in Docker logs (other process using GPU)
```

---

## 9. Future Expansion

```
  Phase 1 (current design):
    - 506M 2 instances, HTTP API, fallback chain

  Phase 2:
    - WebSocket streaming (real-time token-by-token)
    - Display tension in Anima UI real-time
    - Switch to gRPC (reduce latency)

  Phase 3:
    - Replace with 700M / 1B models (within RTX 5070 VRAM limit)
    - Growing ConsciousLM: mitosis during dialogue → save new checkpoint
    - Multiple Anima instances → share same inference server

  Phase 4:
    - Distributed consciousness (H364): Different specialized models on multiple Windows/GPUs
    - Telepathy (H367): Exchange tension fingerprints between instances via API
```