"""Murmur orchestrator — FastAPI entry point.

This is the thin CPU-only orchestrator that speaks WebSocket to the browser
and HTTP to three remote services on the Jarvis Labs L4 GPU:
  - Whisper STT (port 9000)
  - Kokoro TTS (port 9001)
  - LLM server: vLLM (8001), SGLang (8002), or Ollama (8003)

All GPU inference is delegated to the L4. The orchestrator handles:
  - WebSocket push-to-talk sessions
  - Streaming pipeline orchestration (STT → LLM → chunker → TTS)
  - Per-turn metrics collection (MongoDB + ndjson)
  - REST API for runtime listing, health checks, and benchmark results
"""
import asyncio
from pathlib import Path

import structlog
from dotenv import load_dotenv
from fastapi import FastAPI, APIRouter
from starlette.middleware.cors import CORSMiddleware

# Load environment before importing modules that read it
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

from config import settings
from db import turns_collection, bench_runs_collection, client as mongo_client
from runtimes.registry import get_runtime, RUNTIMES, RUNTIME_URLS
from stt_client import STTClient
from tts_client import TTSClient
from ws import ws_router

# Configure structlog for JSON output
structlog.configure(
    processors=[
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer(),
    ],
)

logger = structlog.get_logger()

# ── App setup ───────────────────────────────────────────────────────────────
app = FastAPI(title="Murmur Orchestrator", version="1.0.0")
api_router = APIRouter(prefix="/api")


# ── Health ─────────────────────────────────────────────────────────────────
@api_router.get("/healthz")
async def healthz():
    """Per-upstream health for Whisper, Kokoro, and the active LLM runtime."""
    runtime_name = settings.runtime

    if runtime_name == "mock":
        return {
            "status": "ok",
            "runtime": {"name": "mock", "healthy": True, "url": "http://mock"},
            "whisper": {"healthy": True, "url": "mock"},
            "kokoro": {"healthy": True, "url": "mock"},
        }

    llm = get_runtime(runtime_name)
    stt = STTClient(base_url=settings.whisper_url)
    tts = TTSClient(base_url=settings.kokoro_url)

    llm_healthy, stt_healthy, tts_healthy = await asyncio.gather(
        llm.health(), stt.health(), tts.health()
    )

    all_ok = llm_healthy and stt_healthy and tts_healthy

    return {
        "status": "ok" if all_ok else "degraded",
        "runtime": {
            "name": runtime_name,
            "healthy": llm_healthy,
            "url": RUNTIME_URLS.get(runtime_name, ""),
        },
        "whisper": {"healthy": stt_healthy, "url": settings.whisper_url},
        "kokoro": {"healthy": tts_healthy, "url": settings.kokoro_url},
    }


# ── Runtimes ───────────────────────────────────────────────────────────────
@api_router.get("/runtimes")
async def list_runtimes():
    """List every configured LLM runtime with health, URL, and active flag.

    Health checks run concurrently to keep response time bounded by the slowest
    upstream (≈ 5s timeout) rather than the sum of all four. Whisper and Kokoro
    health are also surfaced under `services` so the demo UI can show one
    unified system-health panel.
    """

    async def _check(name: str):
        llm = get_runtime(name)
        healthy = await llm.health()
        return {
            "name": name,
            "healthy": healthy,
            "url": RUNTIME_URLS.get(name, ""),
            "active": name == settings.runtime,
        }

    runtime_results = await asyncio.gather(*(_check(n) for n in RUNTIMES))

    # Side-car services (STT/TTS) — only meaningful when not in mock mode
    if settings.runtime == "mock":
        services = {
            "whisper": {"healthy": True, "url": "mock"},
            "kokoro": {"healthy": True, "url": "mock"},
        }
    else:
        stt = STTClient(base_url=settings.whisper_url)
        tts = TTSClient(base_url=settings.kokoro_url)
        stt_h, tts_h = await asyncio.gather(stt.health(), tts.health())
        services = {
            "whisper": {"healthy": stt_h, "url": settings.whisper_url},
            "kokoro": {"healthy": tts_h, "url": settings.kokoro_url},
        }

    return {
        "runtimes": runtime_results,
        "active": settings.runtime,
        "services": services,
    }


# ── Benchmarks ─────────────────────────────────────────────────────────────
@api_router.get("/benchmarks")
async def list_benchmarks():
    """Return benchmark results from MongoDB. Returns empty list on DB failure."""
    try:
        results = await bench_runs_collection.find({}, {"_id": 0}).to_list(100)
        return {"benchmarks": results}
    except Exception as exc:
        logger.error("benchmarks_query_failed", error=str(exc))
        return {"benchmarks": [], "error": str(exc)}


# ── Turns history ──────────────────────────────────────────────────────────
@api_router.get("/turns")
async def list_turns(limit: int = 50):
    """Return recent voice turn metrics. Returns empty list on DB failure."""
    try:
        results = (
            await turns_collection.find({}, {"_id": 0}).sort("ts", -1).to_list(limit)
        )
        return {"turns": results}
    except Exception as exc:
        logger.error("turns_query_failed", error=str(exc))
        return {"turns": [], "error": str(exc)}


# ── Mount routers ──────────────────────────────────────────────────────────
app.include_router(api_router)
app.include_router(ws_router, prefix="/api")

# ── CORS ───────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=settings.cors_origins.split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Lifecycle ───────────────────────────────────────────────────────────────
@app.on_event("startup")
async def startup():
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    logger.info(
        "orchestrator_started",
        runtime=settings.runtime,
        whisper_url=settings.whisper_url,
        kokoro_url=settings.kokoro_url,
        sglang_url=settings.sglang_url,
        vllm_url=settings.vllm_url,
        ollama_url=settings.ollama_url,
    )


@app.on_event("shutdown")
async def shutdown():
    mongo_client.close()
    logger.info("orchestrator_shutdown")
