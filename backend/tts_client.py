"""HTTP streaming client for the Kokoro TTS server running on the L4 GPU.

Sends text to POST /tts and streams back PCM16 mono 24kHz audio frames.
The streaming response starts yielding chunks as soon as the first
TTS segment is synthesized, keeping TTFB-audio low.
"""
from typing import AsyncIterator

import httpx
import structlog

logger = structlog.get_logger()


class TTSClient:
    """Async streaming client for the Kokoro TTS server on the L4."""

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")

    async def synthesize_stream(
        self, text: str, voice: str = "af_heart"
    ) -> AsyncIterator[bytes]:
        """Stream PCM16 audio frames from Kokoro TTS."""
        timeout = httpx.Timeout(connect=10.0, read=60.0, write=10.0, pool=10.0)
        async with httpx.AsyncClient() as http:
            async with http.stream(
                "POST",
                f"{self.base_url}/tts",
                json={"text": text, "voice": voice},
                timeout=timeout,
            ) as response:
                response.raise_for_status()
                async for chunk in response.aiter_bytes(chunk_size=4096):
                    yield chunk

    async def health(self) -> bool:
        """Check if the Kokoro server is healthy."""
        try:
            async with httpx.AsyncClient() as http:
                resp = await http.get(f"{self.base_url}/health", timeout=5.0)
                return resp.status_code == 200
        except (httpx.ConnectError, httpx.TimeoutException):
            return False
