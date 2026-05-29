#!/usr/bin/env bash
# serve_whisper.sh — Start faster-whisper STT server on L4 GPU
# Murmur project · https://github.com/YOUR_USERNAME/murmur
#
# Runs a minimal FastAPI wrapper around faster-whisper large-v3-turbo.
# Reserves ~3 GB VRAM. Stays up across LLM runtime swaps.
#
# Usage:
#   ./serve_whisper.sh              # Start Whisper in a detached tmux session
#   ./serve_whisper.sh --health-check  # Curl the /health endpoint and exit

set -euo pipefail

# ─── Configuration ─────────────────────────────────────────────────────────
MODEL="large-v3-turbo"
PORT=9000
HOST="0.0.0.0"
COMPUTE_TYPE="float16"
SESSION="murmur_whisper"
SERVER_SCRIPT="/tmp/murmur_whisper_server.py"

# ─── Health check mode ─────────────────────────────────────────────────────
if [[ "${1:-}" == "--health-check" ]]; then
    response=$(curl -sf "http://localhost:${PORT}/health" 2>/dev/null) || {
        echo "FAIL: Whisper not responding on port ${PORT}"
        exit 1
    }
    echo "OK: Whisper healthy on port ${PORT}"
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

# ─── Ensure dependencies are installed ────────────────────────────────────
pip install faster-whisper "fastapi[standard]" python-multipart --quiet 2>/dev/null

# ─── Write the embedded server ────────────────────────────────────────────
cat > "${SERVER_SCRIPT}" << 'PYEOF'
"""Murmur Whisper STT Server — thin FastAPI wrapper around faster-whisper.

Exposes POST /transcribe accepting raw PCM16 mono 16kHz audio.
Returns {"text": "...", "duration_s": N, "latency_ms": M}.
"""
import io
import time
import struct
import logging

import numpy as np
import uvicorn
from fastapi import FastAPI, File, UploadFile, HTTPException
from faster_whisper import WhisperModel

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)
logger = logging.getLogger("murmur.whisper")

MODEL_SIZE = "large-v3-turbo"
COMPUTE_TYPE = "float16"
SAMPLE_RATE = 16_000

app = FastAPI(title="Murmur Whisper STT")
model: WhisperModel | None = None


@app.on_event("startup")
def load_model():
    global model
    logger.info("Loading faster-whisper model: %s (compute=%s)", MODEL_SIZE, COMPUTE_TYPE)
    model = WhisperModel(MODEL_SIZE, device="cuda", compute_type=COMPUTE_TYPE)
    logger.info("Model loaded successfully.")


@app.get("/health")
def health():
    if model is None:
        raise HTTPException(503, detail="Model not loaded")
    return {"status": "ok", "model": MODEL_SIZE, "compute_type": COMPUTE_TYPE}


@app.post("/transcribe")
async def transcribe(file: UploadFile = File(...)):
    """Accept raw PCM16 mono 16kHz audio and return transcript with timing."""
    if model is None:
        raise HTTPException(503, detail="Model not loaded")

    start = time.perf_counter()
    raw_bytes = await file.read()

    # Convert PCM16 bytes → float32 numpy array normalised to [-1, 1]
    sample_count = len(raw_bytes) // 2
    samples = np.frombuffer(raw_bytes, dtype=np.int16).astype(np.float32) / 32768.0
    duration_s = sample_count / SAMPLE_RATE

    segments, info = model.transcribe(samples, beam_size=1, language="en")
    text = " ".join(seg.text.strip() for seg in segments)

    latency_ms = (time.perf_counter() - start) * 1000
    logger.info(
        "Transcribed %.1fs audio in %.0fms: '%s'",
        duration_s, latency_ms, text[:80],
    )
    return {"text": text, "duration_s": round(duration_s, 3), "latency_ms": round(latency_ms, 1)}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=9000)
PYEOF

# ─── Launch in tmux ───────────────────────────────────────────────────────
echo "Starting Whisper STT server..."
echo "  Model:          ${MODEL}"
echo "  Port:           ${PORT}"
echo "  Compute type:   ${COMPUTE_TYPE}"
echo "  VRAM:           ~3 GB"

tmux new-session -d -s "${SESSION}" \
    "python3 ${SERVER_SCRIPT}; \
     echo 'Whisper process exited. Press enter to close.'; read"

echo ""
echo "Waiting for Whisper to load model..."
for i in $(seq 1 90); do
    if curl -sf "http://localhost:${PORT}/health" &>/dev/null; then
        echo ""
        echo "READY: Whisper on http://${HOST}:${PORT}"
        echo "  Logs:      tmux attach -t ${SESSION}"
        echo "  Stop:      tmux kill-session -t ${SESSION}"
        echo "  Endpoints: POST /transcribe, GET /health"
        exit 0
    fi
    printf "."
    sleep 2
done

echo ""
echo "WARN: Whisper did not become healthy within 3 minutes."
echo "  Check logs: tmux attach -t ${SESSION}"
exit 1
