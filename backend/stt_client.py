"""HTTP client for the Whisper STT server running on the L4 GPU.

Sends raw PCM16 mono 16kHz audio via multipart upload to POST /transcribe.
The Whisper server returns JSON with text, duration, and latency.
"""
import httpx
import structlog

logger = structlog.get_logger()


class STTClient:
    """Async client for the faster-whisper STT server on the L4."""

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")

    async def transcribe(self, pcm_audio: bytes) -> str:
        """Send PCM16 audio to Whisper and return transcript text."""
        async with httpx.AsyncClient() as http:
            files = {"file": ("utterance.pcm", pcm_audio, "audio/x-raw")}
            response = await http.post(
                f"{self.base_url}/transcribe",
                files=files,
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()
            logger.info(
                "stt_transcribed",
                text=data["text"][:80],
                latency_ms=data.get("latency_ms"),
            )
            return data["text"]

    async def health(self) -> bool:
        """Check if the Whisper server is healthy."""
        try:
            async with httpx.AsyncClient() as http:
                resp = await http.get(f"{self.base_url}/health", timeout=5.0)
                return resp.status_code == 200
        except (httpx.ConnectError, httpx.TimeoutException):
            return False
