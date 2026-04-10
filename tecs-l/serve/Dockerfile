FROM pytorch/pytorch:2.4.0-cuda12.4-cudnn9-runtime

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY serve/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Model source files (from repo root)
COPY conscious_lm.py .
COPY growing_conscious_lm_700m.py .
COPY serve/server.py .

# Default checkpoint path (override via env or volume mount)
ENV CHECKPOINT_PATH=/models/growing_700m_korean_sft.pt
ENV PORT=8000

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

CMD ["python", "server.py"]
