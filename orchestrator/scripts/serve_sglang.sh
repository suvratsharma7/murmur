#!/usr/bin/env bash
# serve_sglang.sh — Start SGLang inference server for Qwen2.5-7B-Instruct on L4 GPU
# Murmur project · https://github.com/YOUR_USERNAME/murmur
#
# Usage:
#   ./serve_sglang.sh              # Start SGLang in a detached tmux session
#   ./serve_sglang.sh --health-check  # Curl the /v1/models endpoint and exit

set -euo pipefail

# ─── Configuration ─────────────────────────────────────────────────────────
MODEL="Qwen/Qwen2.5-7B-Instruct"
PORT=8002
HOST="0.0.0.0"
MEM_FRACTION="0.65"       # Leave headroom for colocated Whisper (~3 GB) + Kokoro (~0.5 GB)
DTYPE="bfloat16"
SESSION="murmur_sglang"

# ─── Health check mode ─────────────────────────────────────────────────────
if [[ "${1:-}" == "--health-check" ]]; then
    response=$(curl -sf "http://localhost:${PORT}/v1/models" 2>/dev/null) || {
        echo "FAIL: SGLang not responding on port ${PORT}"
        exit 1
    }
    echo "OK: SGLang healthy on port ${PORT}"
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

# ─── Ensure SGLang is installed ───────────────────────────────────────────
if ! python3 -c "import sglang" &>/dev/null; then
    echo "Installing SGLang..."
    pip install "sglang[all]" --quiet
fi

# ─── Launch in tmux ───────────────────────────────────────────────────────
echo "Starting SGLang server..."
echo "  Model:              ${MODEL}"
echo "  Port:               ${PORT}"
echo "  Mem fraction:       ${MEM_FRACTION}"
echo "  DType:              ${DTYPE}"

tmux new-session -d -s "${SESSION}" \
    "python3 -m sglang.launch_server \
        --model-path ${MODEL} \
        --host ${HOST} \
        --port ${PORT} \
        --dtype ${DTYPE} \
        --mem-fraction-static ${MEM_FRACTION}; \
     echo 'SGLang process exited. Press enter to close.'; read"

echo ""
echo "Waiting for SGLang to load model (this may take 2-5 minutes)..."
for i in $(seq 1 120); do
    if curl -sf "http://localhost:${PORT}/v1/models" &>/dev/null; then
        echo ""
        echo "READY: SGLang on http://${HOST}:${PORT}"
        echo "  Logs:  tmux attach -t ${SESSION}"
        echo "  Stop:  tmux kill-session -t ${SESSION}"
        exit 0
    fi
    printf "."
    sleep 3
done

echo ""
echo "WARN: SGLang did not become healthy within 6 minutes."
echo "  Check logs: tmux attach -t ${SESSION}"
echo "  The server may still be loading the model."
exit 1
