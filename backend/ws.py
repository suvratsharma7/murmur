"""WebSocket handler for push-to-talk voice sessions.

Protocol (documented in docs/08-api.md):
    Client → server:
        JSON: {"type": "audio_start", "sample_rate": 16000, "encoding": "pcm16"}
        Binary: raw PCM16 mono audio frames
        JSON: {"type": "audio_end"}

    Server → client:
        JSON text frames: status, transcript, token, metrics events
        Binary frames: [0x01 type byte][PCM16 mono 24kHz audio data]

Runtime selection is driven exclusively by the `?runtime=<name>` query
parameter. There is no fallback to mock unless `?runtime=mock` is explicitly
requested. If the param is missing, the orchestrator falls back to the
`MURMUR_RUNTIME` env value (default: sglang).
"""
import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import structlog

from chunker import SentenceBoundaryChunker
from config import settings
from db import turns_collection
from pipeline import run_voice_turn
from runtimes.mock_client import MockSTTClient, MockTTSClient
from runtimes.registry import RUNTIMES, get_runtime
from stt_client import STTClient
from tts_client import TTSClient

logger = structlog.get_logger()

ws_router = APIRouter()


def _build_stt(runtime_name: str):
    """Return mock STT only when runtime is explicitly 'mock'. Otherwise real Whisper."""
    if runtime_name == "mock":
        return MockSTTClient(), "mock"
    return STTClient(base_url=settings.whisper_url), settings.whisper_url


def _build_tts(runtime_name: str):
    """Return mock TTS only when runtime is explicitly 'mock'. Otherwise real Kokoro."""
    if runtime_name == "mock":
        return MockTTSClient(), "mock"
    return TTSClient(base_url=settings.kokoro_url), settings.kokoro_url


@ws_router.websocket("/ws")
async def websocket_handler(websocket: WebSocket):
    """Handle a push-to-talk voice session over WebSocket.

    Runtime is determined by the `runtime` query parameter:
        ws://host/api/ws?runtime=sglang   → SGLang adapter + real Whisper + real Kokoro
        ws://host/api/ws?runtime=vllm     → vLLM adapter + real Whisper + real Kokoro
        ws://host/api/ws?runtime=ollama   → Ollama adapter + real Whisper + real Kokoro
        ws://host/api/ws?runtime=mock     → Mock adapters end-to-end
        ws://host/api/ws                   → Falls back to settings.runtime (MURMUR_RUNTIME)
    """
    await websocket.accept()

    # ── Resolve runtime from query param, falling back to env default ────
    requested = websocket.query_params.get("runtime")
    runtime_name = requested if requested else settings.runtime

    # ── Validate runtime BEFORE instantiating adapters ───────────────────
    if runtime_name not in RUNTIMES:
        logger.warning(
            "ws_rejected_unknown_runtime",
            requested=requested,
            resolved=runtime_name,
            available=list(RUNTIMES),
        )
        await websocket.send_json(
            {
                "type": "status",
                "phase": "error",
                "detail": f"Unknown runtime '{runtime_name}'. Available: {list(RUNTIMES)}",
            }
        )
        await websocket.close()
        return

    # ── Instantiate the three adapters (LLM/STT/TTS) by runtime name ─────
    llm = get_runtime(runtime_name)
    stt, stt_target = _build_stt(runtime_name)
    tts, tts_target = _build_tts(runtime_name)
    chunker = SentenceBoundaryChunker()

    logger.info(
        "ws_connected",
        runtime=runtime_name,
        llm_class=type(llm).__name__,
        llm_url=llm.base_url,
        stt_class=type(stt).__name__,
        stt_target=stt_target,
        tts_class=type(tts).__name__,
        tts_target=tts_target,
        query_runtime=requested,
    )

    audio_buffer = bytearray()
    recording = False

    try:
        await websocket.send_json(
            {"type": "status", "phase": "idle", "detail": None, "runtime": runtime_name}
        )

        while True:
            message = await websocket.receive()

            if "text" in message:
                try:
                    data = json.loads(message["text"])
                except json.JSONDecodeError:
                    continue

                msg_type = data.get("type")

                if msg_type == "audio_start":
                    recording = True
                    audio_buffer = bytearray()
                    await websocket.send_json(
                        {"type": "status", "phase": "listening", "detail": None}
                    )

                elif msg_type == "audio_end":
                    recording = False

                    # Enforce utterance length ceiling
                    max_bytes = settings.max_utterance_seconds * 16000 * 2
                    if len(audio_buffer) > max_bytes:
                        await websocket.send_json(
                            {
                                "type": "status",
                                "phase": "error",
                                "detail": f"Utterance exceeded {settings.max_utterance_seconds}s limit",
                            }
                        )
                        await websocket.send_json(
                            {"type": "status", "phase": "idle", "detail": None}
                        )
                        continue

                    if len(audio_buffer) == 0:
                        await websocket.send_json(
                            {
                                "type": "status",
                                "phase": "error",
                                "detail": "No audio data received",
                            }
                        )
                        await websocket.send_json(
                            {"type": "status", "phase": "idle", "detail": None}
                        )
                        continue

                    # Run the full voice pipeline
                    async def emit(event: dict) -> None:
                        """Forward pipeline events to the WebSocket client."""
                        if event["type"] == "audio":
                            # Binary frame: [0x01 type byte][PCM16 audio data]
                            await websocket.send_bytes(b"\x01" + event["pcm"])
                        else:
                            await websocket.send_json(event)

                    await run_voice_turn(
                        utterance_pcm=bytes(audio_buffer),
                        llm=llm,
                        stt=stt,
                        tts=tts,
                        chunker=chunker,
                        emit=emit,
                        db_collection=turns_collection,
                    )

            elif "bytes" in message:
                if recording:
                    audio_buffer.extend(message["bytes"])

    except WebSocketDisconnect:
        logger.info("ws_disconnected", runtime=runtime_name)
    except Exception as exc:
        logger.error("ws_error", error=str(exc), runtime=runtime_name)
        try:
            await websocket.send_json(
                {"type": "status", "phase": "error", "detail": str(exc)}
            )
        except Exception:
            pass
