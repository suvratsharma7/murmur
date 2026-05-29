"""Streaming voice pipeline — the heart of the Murmur orchestrator.

Orchestrates one voice turn: buffered utterance → STT → LLM (streamed) →
sentence chunker → TTS (streamed per chunk) → audio frames back to client.

The streaming invariant: TTS synthesis begins on the first complete sentence
boundary (or first 20 tokens), NOT after the LLM finishes generating.
This is what keeps TTFB-audio low.
"""
from typing import Awaitable, Callable

import structlog

from chunker import SentenceBoundaryChunker
from metrics import StageTimer, TurnMetrics, persist_metrics
from runtimes.base import LLMClient

logger = structlog.get_logger()


async def run_voice_turn(
    utterance_pcm: bytes,
    llm: LLMClient,
    stt,  # STTClient or MockSTTClient
    tts,  # TTSClient or MockTTSClient
    chunker: SentenceBoundaryChunker,
    emit: Callable[[dict], Awaitable[None]],
    db_collection,
) -> TurnMetrics:
    """Execute one complete voice turn through the full pipeline.

    The pipeline satisfies the streaming invariant: TTS synthesis begins
    on the first complete sentence (or 20-token fallback), not after the
    LLM finishes generating. This is what makes TTFB-audio low.

    Args:
        utterance_pcm: Raw PCM16 mono 16kHz audio bytes from push-to-talk.
        llm: The LLM runtime client (vLLM, SGLang, Ollama, or mock).
        stt: The STT client (Whisper HTTP or mock).
        tts: The TTS client (Kokoro HTTP streaming or mock).
        chunker: Sentence boundary chunker instance.
        emit: Callback to send events to the client via WebSocket.
        db_collection: MongoDB collection for persisting turn metrics.

    Returns:
        TurnMetrics for this voice turn.
    """
    timer = StageTimer()
    timer.mark("turn_start")

    await emit({"type": "status", "phase": "thinking", "detail": None})

    # ── Stage 1: Speech-to-Text ───────────────────────────────────────────
    timer.mark("stt_start")
    try:
        transcript = await stt.transcribe(utterance_pcm)
    except Exception as exc:
        logger.error("stt_failed", error=str(exc))
        await emit({"type": "status", "phase": "error", "detail": f"STT failed: {exc}"})
        timer.mark("turn_end")
        return timer.to_metrics(llm.name, llm.params.model, "", 0)
    timer.mark("stt_end")

    await emit({"type": "transcript", "text": transcript, "is_final": True})

    if not transcript.strip():
        await emit({"type": "status", "phase": "done", "detail": "Empty transcript"})
        timer.mark("turn_end")
        return timer.to_metrics(llm.name, llm.params.model, "", 0)

    # ── Stage 2: LLM streaming + chunked TTS ──────────────────────────────
    timer.mark("llm_first_call")

    token_count = 0
    first_chunk_tokens = 0

    async def on_token(token: str) -> None:
        """Callback for each LLM token: emit to client and update timing."""
        nonlocal token_count
        token_count += 1
        if token_count == 1:
            timer.mark("llm_first_token")
        timer.mark("llm_last_token")
        await emit({"type": "token", "text": token})

    try:
        token_stream = llm.stream(transcript)

        async for chunk in chunker.feed(token_stream, on_token=on_token):
            if chunk.idx == 0:
                first_chunk_tokens = token_count
                await emit({"type": "status", "phase": "speaking", "detail": None})

            # Stream TTS audio for this sentence chunk
            timer.mark(f"tts_start_chunk_{chunk.idx}")
            try:
                async for pcm_frame in tts.synthesize_stream(chunk.text):
                    if chunk.idx == 0 and not timer.has("first_audio_emit"):
                        timer.mark("first_audio_emit")
                    await emit({"type": "audio", "pcm": pcm_frame})
            except Exception as exc:
                logger.error(
                    "tts_chunk_failed", chunk_idx=chunk.idx, error=str(exc)
                )
                await emit(
                    {
                        "type": "status",
                        "phase": "error",
                        "detail": f"TTS failed on chunk {chunk.idx}: {exc}",
                    }
                )
                break
            timer.mark(f"tts_end_chunk_{chunk.idx}")

    except Exception as exc:
        logger.error("llm_stream_failed", error=str(exc))
        await emit(
            {"type": "status", "phase": "error", "detail": f"LLM stream failed: {exc}"}
        )

    # ── Stage 3: Finalize ──────────────────────────────────────────────
    timer.mark("turn_end")

    metrics = timer.to_metrics(
        runtime=llm.name,
        model=llm.params.model,
        transcript=transcript,
        token_count=token_count,
        first_chunk_tokens=first_chunk_tokens,
    )

    # Persist to MongoDB + ndjson
    try:
        await persist_metrics(metrics, db_collection)
    except Exception as exc:
        logger.error("metrics_persist_failed", error=str(exc))

    # Emit final metrics to client
    await emit(
        {
            "type": "metrics",
            "stt_latency_ms": metrics.stt_latency_ms,
            "ttft_ms": metrics.ttft_ms,
            "ttfb_audio_ms": metrics.ttfb_audio_ms,
            "e2e_ms": metrics.e2e_ms,
            "tokens_emitted": metrics.response_tokens,
            "output_tokens_per_second": metrics.output_tokens_per_second,
        }
    )

    await emit({"type": "status", "phase": "done", "detail": None})

    logger.info(
        "voice_turn_complete",
        turn_id=metrics.turn_id,
        runtime=metrics.runtime,
        transcript_len=len(transcript),
        tokens=token_count,
        ttfb_audio_ms=metrics.ttfb_audio_ms,
        e2e_ms=metrics.e2e_ms,
    )

    return metrics
