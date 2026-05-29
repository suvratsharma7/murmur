#!/usr/bin/env bash
# serve_ollama.sh — Start Ollama inference server for qwen2.5:7b-instruct on L4 GPU
# Murmur project · https://github.com/YOUR_USERNAME/murmur
#
# NOTE: Ollama uses Q4_K_M quantization by default. This is an apples-to-oranges
# comparison against vLLM/SGLang running BF16. Documented in docs/06-decisions.md.
#
# Usage:
#   ./serve_ollama.sh              # Start Ollama in a detached tmux session
#   ./serve_ollama.sh --health-check  # Curl the /v1/models endpoint and exit

set -euo pipefail

# ─── Configuration ─────────────────────────────────────────────────────────
MODEL="qwen2.5:7b-instruct"
PORT=8003
HOST="0.0.0.0"
SESSION="murmur_ollama"

# ─── Health check mode ─────────────────────────────────────────────────────
if [[ "${1:-}" == "--health-check" ]]; then
    response=$(curl -sf "http://localhost:${PORT}/v1/models" 2>/dev/null) || {
        echo "FAIL: Ollama not responding on port ${PORT}"
        exit 1
    }
    echo "OK: Ollama healthy on port ${PORT}"
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

# ─── Ensure Ollama is installed ───────────────────────────────────────────
if ! command -v ollama &>/dev/null; then
    echo "Installing Ollama..."
    curl -fsSL https://ollama.com/install.sh | sh
fi

# ─── Pull model (idempotent — skips if already present) ──────────────────
echo "Ensuring model '${MODEL}' is available..."
ollama pull "${MODEL}"

# ─── Launch in tmux ───────────────────────────────────────────────────────
echo "Starting Ollama server..."
echo "  Model:   ${MODEL}"
echo "  Port:    ${PORT}"
echo "  Quant:   Q4_K_M (Ollama default — see docs/06-decisions.md)"

tmux new-session -d -s "${SESSION}" \
    "OLLAMA_HOST=${HOST}:${PORT} ollama serve; \
     echo 'Ollama process exited. Press enter to close.'; read"

echo ""
echo "Waiting for Ollama to start..."
for i in $(seq 1 60); do
    if curl -sf "http://localhost:${PORT}/v1/models" &>/dev/null; then
        echo ""
        echo "READY: Ollama on http://${HOST}:${PORT}"
        echo "  Logs:  tmux attach -t ${SESSION}"
        echo "  Stop:  tmux kill-session -t ${SESSION}"
        exit 0
    fi
    printf "."
    sleep 2
done

echo ""
echo "WARN: Ollama did not become healthy within 2 minutes."
echo "  Check logs: tmux attach -t ${SESSION}"
exit 1
