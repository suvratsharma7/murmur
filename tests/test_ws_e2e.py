"""End-to-end test of the WebSocket voice pipeline with mock runtime.

Connects to the orchestrator, sends a fake audio utterance, and verifies
the full event sequence: status transitions, transcript, tokens, audio, metrics.
"""
import asyncio
import json
import struct

import httpx
import websockets


async def test_mock_voice_turn():
    """Run one full push-to-talk voice turn against the mock runtime."""
    uri = "ws://localhost:8001/api/ws?runtime=mock"

    events = []
    audio_frames = []

    async with websockets.connect(uri) as ws:
        # Wait for initial idle status
        raw = await asyncio.wait_for(ws.recv(), timeout=5)
        msg = json.loads(raw)
        events.append(msg)
        assert msg["type"] == "status" and msg["phase"] == "idle", f"Expected idle, got {msg}"
        print(f"  [1] Connected, status: {msg['phase']}")

        # Send audio_start
        await ws.send(json.dumps({
            "type": "audio_start",
            "sample_rate": 16000,
            "encoding": "pcm16",
        }))

        # Wait for listening status
        raw = await asyncio.wait_for(ws.recv(), timeout=5)
        msg = json.loads(raw)
        events.append(msg)
        assert msg["type"] == "status" and msg["phase"] == "listening", f"Expected listening, got {msg}"
        print(f"  [2] Status: listening")

        # Send 1 second of fake PCM16 audio (16000 samples * 2 bytes = 32000 bytes)
        fake_audio = struct.pack(f"<{16000}h", *([1000] * 16000))
        # Send in chunks to simulate real streaming
        chunk_size = 3200
        for i in range(0, len(fake_audio), chunk_size):
            await ws.send(fake_audio[i:i + chunk_size])
            await asyncio.sleep(0.01)

        # Send audio_end
        await ws.send(json.dumps({"type": "audio_end"}))

        # Collect all pipeline events until we see status=done
        done = False
        timeout_at = asyncio.get_event_loop().time() + 15  # 15s timeout

        while not done and asyncio.get_event_loop().time() < timeout_at:
            try:
                raw = await asyncio.wait_for(ws.recv(), timeout=5)
            except asyncio.TimeoutError:
                break

            if isinstance(raw, bytes):
                # Audio frame: [0x01][PCM16 data]
                assert raw[0] == 0x01, f"Audio frame should start with 0x01, got {raw[0]}"
                audio_frames.append(raw[1:])
            else:
                msg = json.loads(raw)
                events.append(msg)
                if msg["type"] == "status" and msg["phase"] == "done":
                    done = True

    # Validate event sequence
    event_types = [e["type"] for e in events]
    print(f"\n  Event types received: {event_types}")
    print(f"  Audio frames received: {len(audio_frames)}")

    # Must have these events in order
    assert "status" in event_types, "No status events"
    assert any(e["type"] == "transcript" for e in events), "No transcript event"
    assert any(e["type"] == "token" for e in events), "No token events"
    assert any(e["type"] == "metrics" for e in events), "No metrics event"
    assert len(audio_frames) > 0, "No audio frames received"

    # Check status transitions
    statuses = [e["phase"] for e in events if e["type"] == "status"]
    print(f"  Status transitions: {statuses}")
    assert "idle" in statuses, "Missing idle status"
    assert "listening" in statuses, "Missing listening status"
    assert "thinking" in statuses, "Missing thinking status"
    assert "speaking" in statuses, "Missing speaking status"
    assert "done" in statuses, "Missing done status"

    # Check metrics
    metrics_event = next(e for e in events if e["type"] == "metrics")
    print(f"  Metrics: ttfb_audio={metrics_event['ttfb_audio_ms']}ms, "
          f"e2e={metrics_event['e2e_ms']}ms, "
          f"tokens={metrics_event['tokens_emitted']}")
    assert metrics_event["ttfb_audio_ms"] > 0, "TTFB-audio should be > 0"
    assert metrics_event["e2e_ms"] > 0, "E2E should be > 0"
    assert metrics_event["ttfb_audio_ms"] < metrics_event["e2e_ms"], "TTFB-audio should be < E2E"

    # Check transcript
    transcript_event = next(e for e in events if e["type"] == "transcript")
    assert transcript_event["is_final"] is True
    assert len(transcript_event["text"]) > 0
    print(f"  Transcript: '{transcript_event['text']}'")

    print("\n  ALL CHECKS PASSED")
    return True


if __name__ == "__main__":
    print("Testing mock voice turn end-to-end...")
    result = asyncio.run(test_mock_voice_turn())
    print(f"\nResult: {'PASS' if result else 'FAIL'}")
