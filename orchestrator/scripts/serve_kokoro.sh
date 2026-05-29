#!/usr/bin/env bash
# serve_kokoro.sh — Start Kokoro TTS server on L4 GPU
# Murmur project · https://github.com/YOUR_USERNAME/murmur
#
# Runs a minimal FastAPI wrapper around Kokoro-82M TTS.
# Streams PCM16 frames at 24 kHz back to the client. TTFB-audio depends
# on this NOT buffering the entire utterance before responding.
# Reserves ~0.5 GB VRAM. Stays up across LLM runtime swaps.
#
# Usage:
#   ./serve_kokoro.sh              # Start Kokoro in a detached tmux session
#   ./serve_kokoro.sh --health-check  # Curl the /health endpoint and exit

set -euo pipefail

# ─── Configuration ─────────────────────────────────────────────────────────
MODEL="hexgrad/Kokoro-82M"
PORT=9001
HOST="0.0.0.0"
OUTPUT_SAMPLE_RATE=24000
DEFAULT_VOICE="af_heart"
SESSION="murmur_kokoro"
SERVER_SCRIPT="/tmp/murmur_kokoro_server.py"

# ─── Health check mode ─────────────────────────────────────────────────────
if [[ "${1:-}" == "--health-check" ]]; then
    response=$(curl -sf "http://localhost:${PORT}/health" 2>/dev/null) || {
        echo "FAIL: Kokoro not responding on port ${PORT}"
        exit 1
    }
    echo "OK: Kokoro healthy on port ${PORT}"
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
pip install kokoro "fastapi[standard]" soundfile --quiet 2>/dev/null

# ─── Write the embedded server ────────────────────────────────────────────
cat > "${SERVER_SCRIPT}" << 'PYEOF'
"""Murmur Kokoro TTS Server — thin FastAPI wrapper around Kokoro-82M.

Exposes POST /tts accepting {"text": "...", "voice": "af_heart"}.
Streams PCM16 mono 24kHz frames via StreamingResponse so the orchestrator
can forward first audio bytes before full synthesis completes.
"""
import io
import time
import logging
import struct

import numpy as np
import torch
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)
logger = logging.getLogger("murmur.kokoro")

OUTPUT_SAMPLE_RATE = 24_000
DEFAULT_VOICE = "af_heart"

app = FastAPI(title="Murmur Kokoro TTS")
pipeline = None


@app.on_event("startup")
def load_model():
    global pipeline
    logger.info("Loading Kokoro TTS pipeline...")
    try:
        from kokoro import KPipeline
        pipeline = KPipeline(lang_code="a")
        logger.info("Kokoro pipeline loaded successfully.")
    except Exception as exc:
        logger.error("Failed to load Kokoro pipeline: %s", exc)
        raise


class TTSRequest(BaseModel):
    text: str
    voice: str | None = None


@app.get("/health")
def health():
    if pipeline is None:
        raise HTTPException(503, detail="Pipeline not loaded")
    return {
        "status": "ok",
        "model": "hexgrad/Kokoro-82M",
        "output_sample_rate": OUTPUT_SAMPLE_RATE,
    }


@app.post("/tts")
async def synthesize(request: TTSRequest):
    """Synthesize speech and stream PCM16 frames at 24 kHz.

    The streaming response starts yielding audio chunks as soon as the first
    segment is ready, keeping TTFB-audio low for downstream consumers.
    """
    if pipeline is None:
        raise HTTPException(503, detail="Pipeline not loaded")
    if not request.text.strip():
        raise HTTPException(400, detail="Text cannot be empty")

    voice = request.voice or DEFAULT_VOICE
    start = time.perf_counter()
    logger.info("TTS request: voice=%s text='%s'", voice, request.text[:60])

    def generate_pcm_chunks():
        """Yield PCM16 byte chunks as kokoro produces audio segments."""
        chunk_idx = 0
        for _gs, _ps, audio_segment in pipeline(request.text, voice=voice):
            # audio_segment is a numpy float32 array; convert to PCM16 bytes
            audio_int16 = (audio_segment * 32767).astype(np.int16)
            yield audio_int16.tobytes()
            chunk_idx += 1

        elapsed = (time.perf_counter() - start) * 1000
        logger.info("TTS complete: %d chunks in %.0fms", chunk_idx, elapsed)

    return StreamingResponse(
        generate_pcm_chunks(),
        media_type="audio/x-raw",
        headers={
            "X-Sample-Rate": str(OUTPUT_SAMPLE_RATE),
            "X-Encoding": "pcm16",
            "X-Channels": "1",
        },
    )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=9001)
PYEOF

# ─── Launch in tmux ───────────────────────────────────────────────────────
echo "Starting Kokoro TTS server..."
echo "  Model:          ${MODEL}"
echo "  Port:           ${PORT}"
echo "  Sample rate:    ${OUTPUT_SAMPLE_RATE} Hz"
echo "  Default voice:  ${DEFAULT_VOICE}"
echo "  VRAM:           ~0.5 GB"

tmux new-session -d -s "${SESSION}" \
    "python3 ${SERVER_SCRIPT}; \
     echo 'Kokoro process exited. Press enter to close.'; read"

echo ""
echo "Waiting for Kokoro to load model..."
for i in $(seq 1 90); do
    if curl -sf "http://localhost:${PORT}/health" &>/dev/null; then
        echo ""
        echo "READY: Kokoro TTS on http://${HOST}:${PORT}"
        echo "  Logs:      tmux attach -t ${SESSION}"
        echo "  Stop:      tmux kill-session -t ${SESSION}"
        echo "  Endpoints: POST /tts, GET /health"
        exit 0
    fi
    printf "."
    sleep 2
done

echo ""
echo "WARN: Kokoro did not become healthy within 3 minutes."
echo "  Check logs: tmux attach -t ${SESSION}"
exit 1
