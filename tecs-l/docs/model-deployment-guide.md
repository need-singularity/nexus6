# 700M x 3 Model Internet Deployment Guide

## Overview

Infrastructure guide for serving three 700M parameter models on the internet.

## VRAM Requirements

| | FP16 | INT8 | INT4 |
|---|---|---|---|
| 1 model | ~1.4GB | ~0.7GB | ~0.35GB |
| **3 models total** | **~4.2GB** | **~2.1GB** | **~1.05GB** |
| + KV cache/overhead | ~6-8GB | ~4-5GB | ~3GB |

1 GPU (16GB+ VRAM) is sufficient.

## Serving Architecture

```
1 GPU Server
├── vLLM (3 models loaded simultaneously)
│   ├── model_A (port 8001)
│   ├── model_B (port 8002)
│   └── model_C (port 8003)
├── Nginx (reverse proxy + SSL + load balancing)
├── FastAPI gateway (routing + API key auth)
└── Cloudflare (domain + DDoS protection)
```

## Required Components

### Hardware
- 1 GPU server (16GB+ VRAM)

### Software
- Docker + NVIDIA Container Toolkit
- vLLM or TGI (serving framework)
- Nginx + Let's Encrypt (SSL)
- 1 domain (~$10/year)

### Network/Security
- Domain + SSL (Let's Encrypt free)
- Reverse proxy: Nginx / Caddy
- API key authentication + rate limiting
- Firewall (minimal port exposure)
- DDoS protection: Cloudflare

## Serving Framework Comparison

| Framework | Features |
|---|---|
| **vLLM** | LLM-specialized, PagedAttention, highest throughput |
| **TGI** (HuggingFace) | HF ecosystem integration, simple |
| **Triton** (NVIDIA) | General purpose, multi-model, batch optimization |
| **Ollama** | Local/small-scale, easy installation |
| **llama.cpp server** | CPU/lightweight GPU, GGUF format |

## Optimization

- **Quantization**: GPTQ, AWQ, GGUF (4bit/8bit) → VRAM reduction
- **KV cache optimization**: PagedAttention (vLLM automatic)
- **Batch processing**: continuous batching
- **Streaming**: SSE (Server-Sent Events)

## Platform Recommendations

### Cost-effectiveness Ranking

| Rank | Service | Monthly Cost | Features |
|---|---|---|---|
| 1 | **RunPod Serverless** | **$5-30** | Pay per call, $0 when no traffic |
| 2 | **Modal** | **$10-40** | Fast cold start, Python native |
| 3 | **Replicate** | **$20-50** | Easiest deployment, `cog push` one-liner |
| 4 | **RunPod Pod** | ~$160 | 24/7 always-on, high traffic |
| 5 | **AWS SageMaker** | ~$200+ | Enterprise |
| 6 | **GCP Vertex AI** | ~$200+ | Enterprise |

### Traffic-based Recommendations

| Traffic | Recommendation | Cost |
|---|---|---|
| Low (~1000/day or less) | RunPod Serverless / Modal | $5-30/month |
| Medium (~10k/day) | RunPod Pod (RTX 3090) | ~$160/month |
| High (~100k+/day) | Dedicated server (Hetzner, OVH) | $100-200/month |

### GPU Recommendations

| GPU | Monthly Cost | Notes |
|---|---|---|
| **RTX 3090 24GB** | ~$160/month (cloud) | 3 models comfortable, best value |
| **RTX 4090 24GB** | ~$300/month | 2x throughput |
| **T4 16GB** | ~$80/month (AWS/GCP) | FP16 3 models possible, slow |
| **A10G 24GB** | ~$120/month (AWS) | Stable |
| Your **RTX 5070** | $0 | Home serving possible |

### Cost Summary

| Item | Self-hosting (5070) | Cloud (RTX 3090) |
|---|---|---|
| Server | Electricity ~$30 | ~$160 |
| Domain | ~$1 | ~$1 |
| Cloudflare | Free | Free |
| **Total** | **~$31/month** | **~$161/month** |

## Quick Start

### Replicate (5-minute deployment)

```bash
cog push r8.im/username/model-a
cog push r8.im/username/model-b
cog push r8.im/username/model-c
```

### RunPod Serverless

```
Write handler.py → Docker build → Create endpoint → API call
```

### Self-hosting (RTX 5070)

```bash
# No fixed IP needed with Cloudflare Tunnel
cloudflared tunnel --url http://localhost:8000
```