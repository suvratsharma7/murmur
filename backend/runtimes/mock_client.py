"""Mock runtime adapters for development and testing without a live L4 instance.

When MURMUR_RUNTIME=mock, the orchestrator uses these clients instead of
making HTTP calls to remote GPU servers. Useful for frontend development,
pipeline testing, and CI.

The mock LLM yields tokens from canned responses at a realistic cadence.
The mock STT returns canned transcripts after simulated latency.
The mock TTS generates synthetic PCM16 sine wave audio.
"""
import asyncio
import math
import random
import struct
from typing import AsyncIterator

from runtimes.base import GenerationParams, LLMClient

MOCK_RESPONSES = [
    "The capital of France is Paris. It has been the country's capital since the late 10th century.",
    "Python was created by Guido van Rossum. It was first released in 1991 and emphasizes code readability.",
    "The speed of light is approximately 299,792 kilometers per second. Einstein showed this is a universal speed limit.",
    "Water boils at 100 degrees Celsius at standard atmospheric pressure. This temperature is lower at higher altitudes.",
    "The Great Wall of China stretches over 13,000 miles. It was built across several dynasties over many centuries.",
]


class MockLLMClient(LLMClient):
    """Yields tokens from canned responses at a realistic cadence (~30ms per token).

    Simulates the streaming behavior of a real LLM server without needing a GPU.
    Token cadence is randomized slightly to mimic real-world jitter.
    """

    def __init__(
        self, base_url: str = "http://mock", params: GenerationParams | None = None
    ):
        super().__init__(base_url, params)

    @property
    def name(self) -> str:
        return "mock"

    async def health(self) -> bool:
        return True

    async def stream(self, prompt: str) -> AsyncIterator[str]:
        """Yield space-separated words as individual tokens."""
        response = random.choice(MOCK_RESPONSES)
        words = response.split(" ")

        for i, word in enumerate(words):
            if i == 0:
                # Simulate TTFT for the first token
                await asyncio.sleep(0.08 + random.uniform(0, 0.04))
            else:
                await asyncio.sleep(0.025 + random.uniform(0, 0.015))

            suffix = " " if i < len(words) - 1 else ""
            yield word + suffix


class MockSTTClient:
    """Returns a canned transcript after simulating transcription latency."""

    TRANSCRIPTS = [
        "What is the capital of France?",
        "Tell me about Python programming.",
        "How fast does light travel?",
        "At what temperature does water boil?",
        "Tell me about the Great Wall of China.",
    ]

    async def transcribe(self, pcm_audio: bytes) -> str:
        """Simulate Whisper transcription with realistic latency (~150ms)."""
        await asyncio.sleep(0.15 + random.uniform(0, 0.1))
        return random.choice(self.TRANSCRIPTS)

    async def health(self) -> bool:
        return True


class MockTTSClient:
    """Generates synthetic PCM16 sine wave audio to simulate Kokoro TTS streaming.

    Produces a 440Hz tone at 24kHz sample rate, chunked to simulate
    the streaming behavior of the real TTS server.
    """

    SAMPLE_RATE = 24_000
    FREQUENCY = 440
    AMPLITUDE = 0.3

    async def synthesize_stream(
        self, text: str, voice: str = "af_heart"
    ) -> AsyncIterator[bytes]:
        """Yield PCM16 byte chunks approximating the duration of the input text."""
        word_count = len(text.split())
        duration_s = max(0.3, word_count * 0.08)
        total_samples = int(self.SAMPLE_RATE * duration_s)
        chunk_samples = 2400  # 100ms of audio per chunk

        for offset in range(0, total_samples, chunk_samples):
            count = min(chunk_samples, total_samples - offset)
            chunk = bytearray(count * 2)
            for j in range(count):
                t = (offset + j) / self.SAMPLE_RATE
                sample = int(
                    32767 * self.AMPLITUDE * math.sin(2 * math.pi * self.FREQUENCY * t)
                )
                struct.pack_into("<h", chunk, j * 2, sample)
            yield bytes(chunk)
            await asyncio.sleep(0.01)

    async def health(self) -> bool:
        return True
