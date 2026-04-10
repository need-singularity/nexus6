#!/bin/bash
# RC-1: PureField LLM — RunPod launch script
# Usage: bash experiments/rc1_runpod_launch.sh
#
# Prerequisites:
#   - RunPod pod running with SSH access
#   - RUNPOD_SSH set (e.g., "ssh root@<pod-ip> -p <port> -i ~/.ssh/id_ed25519")
#   - Or: use existing golden-moe-train pod
#
# Alternatively, run locally on Windows PC (RTX 5070):
#   scp experiments/experiment_rc1_purefield_llm.py aiden@100.112.63.23:~/
#   ssh aiden@100.112.63.23 "cd ~ && wsl -e /usr/bin/python3 experiment_rc1_purefield_llm.py"

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
EXPERIMENT="experiment_rc1_purefield_llm.py"
EXPERIMENT_PATH="${SCRIPT_DIR}/${EXPERIMENT}"

# ─── Configuration ───
# Set RUNPOD_SSH to your pod's SSH command, e.g.:
#   export RUNPOD_SSH="ssh root@205.196.17.2 -p 22118 -i ~/.ssh/id_ed25519"
# Or set POD_ID for RunPod CLI usage
RUNPOD_SSH="${RUNPOD_SSH:-}"
POD_ID="${POD_ID:-}"
REMOTE_DIR="/workspace"

echo "=============================================="
echo "  RC-1: PureField LLM — RunPod Launch"
echo "=============================================="

# ─── Check experiment file exists ───
if [ ! -f "$EXPERIMENT_PATH" ]; then
    echo "ERROR: ${EXPERIMENT_PATH} not found"
    exit 1
fi

# ─── Option 1: Direct SSH ───
if [ -n "$RUNPOD_SSH" ]; then
    echo "  Using SSH: ${RUNPOD_SSH}"
    echo ""

    # Upload experiment
    echo "[1/4] Uploading experiment..."
    SCP_CMD=$(echo "$RUNPOD_SSH" | sed 's/^ssh /scp /' | sed "s/root@/${EXPERIMENT_PATH} root@/" | sed 's/$/:\/workspace\//')
    # Parse SSH into SCP (handle port)
    SSH_HOST=$(echo "$RUNPOD_SSH" | grep -oP 'root@[\d.]+')
    SSH_PORT=$(echo "$RUNPOD_SSH" | grep -oP '(?<=-p )\d+')
    SSH_KEY=$(echo "$RUNPOD_SSH" | grep -oP '(?<=-i )\S+')

    KEY_FLAG=""
    [ -n "$SSH_KEY" ] && KEY_FLAG="-i $SSH_KEY"
    PORT_FLAG=""
    [ -n "$SSH_PORT" ] && PORT_FLAG="-P $SSH_PORT"

    scp $PORT_FLAG $KEY_FLAG "$EXPERIMENT_PATH" "${SSH_HOST}:${REMOTE_DIR}/"
    echo "  Uploaded to ${REMOTE_DIR}/${EXPERIMENT}"

    # Install dependencies
    echo "[2/4] Installing dependencies..."
    $RUNPOD_SSH "pip install torch numpy scipy 2>/dev/null || true"

    # Run experiment
    echo "[3/4] Running experiment (GPU)..."
    echo "  This should take ~5-10 minutes on A100/3090..."
    echo ""
    $RUNPOD_SSH "cd ${REMOTE_DIR} && /usr/bin/python3 ${EXPERIMENT} 2>&1" | tee "${SCRIPT_DIR}/rc1_output.log"

    # Download results
    echo "[4/4] Downloading results..."
    scp $PORT_FLAG $KEY_FLAG "${SSH_HOST}:${REMOTE_DIR}/rc1_results.json" "${SCRIPT_DIR}/" 2>/dev/null || echo "  (results JSON not found on remote)"

    echo ""
    echo "=============================================="
    echo "  DONE. Output saved to: ${SCRIPT_DIR}/rc1_output.log"
    echo "=============================================="

# ─── Option 2: RunPod CLI (pod ID) ───
elif [ -n "$POD_ID" ]; then
    echo "  Using RunPod CLI with pod: ${POD_ID}"
    echo "  (Requires 'runpodctl' installed)"
    echo ""

    # Upload
    echo "[1/3] Uploading..."
    runpodctl send "$EXPERIMENT_PATH" --podId "$POD_ID"

    # Run
    echo "[2/3] Running..."
    runpodctl exec --podId "$POD_ID" -- /usr/bin/python3 "/workspace/${EXPERIMENT}" 2>&1 | tee "${SCRIPT_DIR}/rc1_output.log"

    # Download
    echo "[3/3] Downloading results..."
    runpodctl receive --podId "$POD_ID" "/workspace/rc1_results.json" "${SCRIPT_DIR}/" 2>/dev/null || true

    echo "  DONE."

# ─── Option 3: Local GPU ───
else
    echo "  No RUNPOD_SSH or POD_ID set."
    echo "  Running locally (requires CUDA GPU)..."
    echo ""
    echo "  To use RunPod instead:"
    echo "    export RUNPOD_SSH='ssh root@<ip> -p <port> -i ~/.ssh/key'"
    echo "    bash $0"
    echo ""

    if /usr/bin/python3 -c "import torch; assert torch.cuda.is_available()" 2>/dev/null; then
        echo "  CUDA available. Running..."
        /usr/bin/python3 "$EXPERIMENT_PATH" 2>&1 | tee "${SCRIPT_DIR}/rc1_output.log"
    else
        echo "  WARNING: No CUDA detected. Running on CPU (will be slow)."
        echo "  Press Ctrl+C to cancel, or wait 3 seconds..."
        sleep 3
        /usr/bin/python3 "$EXPERIMENT_PATH" 2>&1 | tee "${SCRIPT_DIR}/rc1_output.log"
    fi
fi
