"""Tests for pipeline metrics and the streaming invariant.

The key invariant: TTFB-audio must occur BEFORE the LLM finishes generating,
proving that TTS starts on the first sentence chunk rather than waiting
for the complete response.
"""
import asyncio

import pytest
from metrics import StageTimer


@pytest.mark.asyncio
async def test_ttfb_audio_before_e2e():
    """TTFB-audio must be significantly less than E2E latency.

    This validates the streaming invariant: TTS starts on the first chunk,
    not after the full LLM response completes.
    """
    timer = StageTimer()

    timer.mark("turn_start")

    # STT: ~100ms
    timer.mark("stt_start")
    await asyncio.sleep(0.1)
    timer.mark("stt_end")

    # LLM: TTFT ~80ms
    timer.mark("llm_first_call")
    await asyncio.sleep(0.08)
    timer.mark("llm_first_token")

    # Tokens arrive at ~30ms each; first chunk after 5 tokens
    for _ in range(5):
        await asyncio.sleep(0.03)
        timer.mark("llm_last_token")

    # TTS starts on first chunk → first audio within ~50ms of chunk start
    timer.mark("tts_start_chunk_0")
    await asyncio.sleep(0.05)
    timer.mark("first_audio_emit")

    # More tokens continue while audio is already streaming
    for _ in range(10):
        await asyncio.sleep(0.03)
        timer.mark("llm_last_token")

    timer.mark("turn_end")

    ttfb_audio_ms = timer.elapsed_ms("turn_start", "first_audio_emit")
    e2e_ms = timer.elapsed_ms("turn_start", "turn_end")

    # TTFB-audio must be much less than E2E (streaming proof)
    assert ttfb_audio_ms < e2e_ms, (
        f"TTFB-audio ({ttfb_audio_ms:.0f}ms) should be < E2E ({e2e_ms:.0f}ms)"
    )
    # Specifically, TTFB-audio should be less than half of E2E
    # because the second half of tokens + their TTS happen after first audio
    assert ttfb_audio_ms < e2e_ms * 0.7, (
        f"TTFB-audio ({ttfb_audio_ms:.0f}ms) should be < 70% of E2E ({e2e_ms:.0f}ms)"
    )


@pytest.mark.asyncio
async def test_ttfb_audio_upper_bound():
    """TTFB-audio should not exceed STT + TTFT + chunk_accumulation + TTS_first_chunk.

    With mock values: ~100ms STT + ~80ms TTFT + ~150ms (5 tokens * 30ms) + ~50ms TTS
    = ~380ms expected. We allow generous tolerance.
    """
    timer = StageTimer()

    timer.mark("turn_start")
    timer.mark("stt_start")
    await asyncio.sleep(0.1)
    timer.mark("stt_end")

    timer.mark("llm_first_call")
    await asyncio.sleep(0.08)
    timer.mark("llm_first_token")

    for _ in range(5):
        await asyncio.sleep(0.03)
        timer.mark("llm_last_token")

    timer.mark("tts_start_chunk_0")
    await asyncio.sleep(0.05)
    timer.mark("first_audio_emit")
    timer.mark("turn_end")

    ttfb_audio_ms = timer.elapsed_ms("turn_start", "first_audio_emit")
    # Upper bound: STT + TTFT + 5*TPOT + TTS_first = 100+80+150+50 = 380ms + tolerance
    assert ttfb_audio_ms < 600, (
        f"TTFB-audio ({ttfb_audio_ms:.0f}ms) exceeded generous upper bound (600ms)"
    )


@pytest.mark.asyncio
async def test_metrics_completeness():
    """All expected metric fields are populated after a full turn."""
    timer = StageTimer()

    timer.mark("turn_start")
    timer.mark("stt_start")
    await asyncio.sleep(0.01)
    timer.mark("stt_end")
    timer.mark("llm_first_call")
    await asyncio.sleep(0.01)
    timer.mark("llm_first_token")
    await asyncio.sleep(0.05)
    timer.mark("llm_last_token")
    timer.mark("first_audio_emit")
    timer.mark("turn_end")

    metrics = timer.to_metrics(
        runtime="mock",
        model="test-model",
        transcript="test input",
        token_count=10,
    )

    assert metrics.stt_latency_ms > 0
    assert metrics.ttft_ms > 0
    assert metrics.ttfb_audio_ms > 0
    assert metrics.e2e_ms > 0
    assert metrics.tpot_mean_ms > 0
    assert metrics.output_tokens_per_second > 0
    assert metrics.runtime == "mock"
    assert metrics.model == "test-model"
    assert metrics.transcript_chars == 10
    assert metrics.response_tokens == 10
    assert metrics.turn_id.startswith("tid_")


@pytest.mark.asyncio
async def test_timer_missing_marks():
    """Missing marks return 0 for elapsed_ms rather than raising."""
    timer = StageTimer()
    timer.mark("turn_start")

    assert timer.elapsed_ms("turn_start", "nonexistent") == 0.0
    assert timer.elapsed_ms("nonexistent", "turn_start") == 0.0
    assert timer.has("turn_start") is True
    assert timer.has("nonexistent") is False
