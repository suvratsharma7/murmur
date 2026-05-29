"""Per-stage timestamping and metrics persistence for voice turns.

Every voice turn appends one line to events.ndjson (best-effort, never raises)
and one document to MongoDB's 'turns' collection. The ndjson file is for
grep-friendly debugging; MongoDB is the source of truth.

The ndjson write happens FIRST so that a transient MongoDB outage never costs
us the turn record.
"""
import json
import time
import uuid
from datetime import datetime, timezone

import structlog
from pydantic import BaseModel

from config import settings

logger = structlog.get_logger()


class TurnMetrics(BaseModel):
    """Complete metrics for one voice turn, matching the schema in docs/08-api.md."""

    ts: str
    turn_id: str
    runtime: str
    model: str
    transcript_chars: int = 0
    response_tokens: int = 0
    stt_latency_ms: float = 0.0
    ttft_ms: float = 0.0
    first_chunk_size_tokens: int = 0
    ttfb_audio_ms: float = 0.0
    tpot_mean_ms: float = 0.0
    e2e_ms: float = 0.0
    output_tokens_per_second: float = 0.0
    error: str | None = None


class StageTimer:
    """Records perf_counter timestamps at pipeline stage transitions.

    Every named mark() point becomes a metric. Derived metrics are computed
    in to_metrics() from pairs of marks.
    """

    def __init__(self):
        self._marks: dict[str, float] = {}

    def mark(self, name: str) -> None:
        """Record a timestamp for the named stage."""
        self._marks[name] = time.perf_counter()

    def has(self, name: str) -> bool:
        """Check whether a stage mark has been recorded."""
        return name in self._marks

    def elapsed_ms(self, start: str, end: str) -> float:
        """Compute wall-clock ms between two marks. Returns 0 if either missing."""
        if start not in self._marks or end not in self._marks:
            return 0.0
        return (self._marks[end] - self._marks[start]) * 1000

    def to_metrics(
        self,
        runtime: str,
        model: str,
        transcript: str,
        token_count: int,
        first_chunk_tokens: int = 0,
    ) -> TurnMetrics:
        """Compute derived metrics from recorded stage marks."""
        stt_latency = self.elapsed_ms("stt_start", "stt_end")
        ttft = self.elapsed_ms("llm_first_call", "llm_first_token")
        ttfb_audio = self.elapsed_ms("turn_start", "first_audio_emit")
        e2e = self.elapsed_ms("turn_start", "turn_end")

        # TPOT: mean inter-token interval (first-to-last / (count - 1))
        llm_span_ms = self.elapsed_ms("llm_first_token", "llm_last_token")
        tpot_mean = llm_span_ms / (token_count - 1) if token_count > 1 else 0.0

        # Output throughput: tokens / total LLM generation time
        llm_total_s = self.elapsed_ms("llm_first_call", "llm_last_token") / 1000
        tps = token_count / llm_total_s if llm_total_s > 0 else 0.0

        return TurnMetrics(
            ts=datetime.now(timezone.utc).isoformat(),
            turn_id=f"tid_{uuid.uuid4().hex[:12]}",
            runtime=runtime,
            model=model,
            transcript_chars=len(transcript),
            response_tokens=token_count,
            stt_latency_ms=round(stt_latency, 1),
            ttft_ms=round(ttft, 1),
            first_chunk_size_tokens=first_chunk_tokens,
            ttfb_audio_ms=round(ttfb_audio, 1),
            tpot_mean_ms=round(tpot_mean, 1),
            e2e_ms=round(e2e, 1),
            output_tokens_per_second=round(tps, 1),
        )


async def persist_metrics(metrics: TurnMetrics, db_collection) -> None:
    """Append to events.ndjson (always) and insert into MongoDB (best-effort).

    The ndjson write happens first so the turn record survives a MongoDB outage.
    MongoDB failure is logged but does NOT raise — voice turns must not break
    because the telemetry store is down.
    """
    doc = metrics.model_dump()

    # ndjson: always write, never raises beyond logging
    try:
        settings.data_dir.mkdir(parents=True, exist_ok=True)
        with open(settings.ndjson_path, "a") as f:
            f.write(json.dumps(doc, default=str) + "\n")
    except Exception as exc:
        logger.error("ndjson_write_failed", error=str(exc), turn_id=metrics.turn_id)

    # MongoDB: best-effort
    try:
        await db_collection.insert_one(doc)
        logger.info(
            "turn_metrics_persisted",
            turn_id=metrics.turn_id,
            runtime=metrics.runtime,
            e2e_ms=metrics.e2e_ms,
            ttfb_audio_ms=metrics.ttfb_audio_ms,
        )
    except Exception as exc:
        logger.warning(
            "mongo_insert_failed",
            error=str(exc),
            turn_id=metrics.turn_id,
            note="ndjson record was still written",
        )
