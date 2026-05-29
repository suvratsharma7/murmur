#!/usr/bin/env bash
# serve_vllm.sh — Start vLLM inference server for Qwen2.5-7B-Instruct on L4 GPU
# Murmur project · https://github.com/YOUR_USERNAME/murmur
#
# Usage:
#   ./serve_vllm.sh              # Start vLLM in a detached tmux session
#   ./serve_vllm.sh --health-check  # Curl the /v1/models endpoint and exit

set -euo pipefail

# ─── Configuration ─────────────────────────────────────────────────────────
MODEL="Qwen/Qwen2.5-7B-Instruct"
PORT=8001
HOST="0.0.0.0"
GPU_MEM_UTIL="0.65"       # Leave headroom for colocated Whisper (~3 GB) + Kokoro (~0.5 GB)
DTYPE="bfloat16"
MAX_MODEL_LEN=8192
SESSION="murmur_vllm"

# ─── Health check mode ─────────────────────────────────────────────────────
if [[ "${1:-}" == "--health-check" ]]; then
    response=$(curl -sf "http://localhost:${PORT}/v1/models" 2>/dev/null) || {
        echo "FAIL: vLLM not responding on port ${PORT}"
        exit 1
    }
    echo "OK: vLLM healthy on port ${PORT}"
    echo "$response" | python3 -m json.tool 2>/dev/null || echo "$response"
    exit 0
fi

# ─── Pre-flight checks ────────────────────────────────────────────────────
if lsof -i :"${PORT}" &>/dev/null; then
    echo "ABORT: Port ${PORT} is already in use."
    echo "  Run: lsof -i :${PORT}   to identify the process."
    echo "  Run: tmux kill-session -t ${SESSION}   if it's a stale Murmur session."
    exit 1
fi

if tmux has-session -t "${SESSION}" 2>/dev/null; then
    echo "ABORT: tmux session '${SESSION}' already exists."
    echo "  Run: tmux kill-session -t ${SESSION}   to remove it."
    exit 1
fi

# ─── Ensure vLLM is installed ─────────────────────────────────────────────
if ! python3 -c "import vllm" &>/dev/null; then
    echo "Installing vLLM..."
    pip install vllm --quiet
fi

# ─── Launch in tmux ───────────────────────────────────────────────────────
echo "Starting vLLM server..."
echo "  Model:            ${MODEL}"
echo "  Port:             ${PORT}"
echo "  GPU mem util:     ${GPU_MEM_UTIL}"
echo "  DType:            ${DTYPE}"
echo "  Max model len:    ${MAX_MODEL_LEN}"

tmux new-session -d -s "${SESSION}" \
    "python3 -m vllm.entrypoints.openai.api_server \
        --model ${MODEL} \
        --host ${HOST} \
        --port ${PORT} \
        --gpu-memory-utilization ${GPU_MEM_UTIL} \
        --dtype ${DTYPE} \
        --max-model-len ${MAX_MODEL_LEN} \
        --served-model-name ${MODEL}; \
     echo 'vLLM process exited. Press enter to close.'; read"

echo ""
echo "Waiting for vLLM to load model (this may take 2-5 minutes)..."
for i in $(seq 1 120); do
    if curl -sf "http://localhost:${PORT}/v1/models" &>/dev/null; then
        echo ""
        echo "READY: vLLM on http://${HOST}:${PORT}"
        echo "  Logs:  tmux attach -t ${SESSION}"
        echo "  Stop:  tmux kill-session -t ${SESSION}"
        exit 0
    fi
    printf "."
    sleep 3
done

echo ""
echo "WARN: vLLM did not become healthy within 6 minutes."
echo "  Check logs: tmux attach -t ${SESSION}"
echo "  The server may still be loading the model."
exit 1
