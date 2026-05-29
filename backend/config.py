"""Murmur orchestrator configuration — environment-driven, no magic.

All values are drawn from environment variables with sensible defaults
for local development (mock mode, localhost endpoints).
"""
import os
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")


class Settings:
    """Central configuration for the Murmur orchestrator."""

    def __init__(self):
        self.mongo_url: str = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
        self.db_name: str = os.environ.get("DB_NAME", "murmur")

        # L4 service endpoints (remote GPU server)
        self.whisper_url: str = os.environ.get("WHISPER_URL", "http://localhost:9000")
        self.kokoro_url: str = os.environ.get("KOKORO_URL", "http://localhost:9001")
        self.vllm_url: str = os.environ.get("VLLM_URL", "http://localhost:8001")
        self.sglang_url: str = os.environ.get("SGLANG_URL", "http://localhost:8002")
        self.ollama_url: str = os.environ.get("OLLAMA_URL", "http://localhost:8003")

        # Runtime selection: mock | vllm | sglang | ollama
        self.runtime: str = os.environ.get("MURMUR_RUNTIME", "mock")

        # Pipeline tuning
        self.chunk_fallback_tokens: int = int(
            os.environ.get("MURMUR_CHUNK_FALLBACK_TOKENS", "20")
        )
        self.max_utterance_seconds: int = int(
            os.environ.get("MURMUR_MAX_UTTERANCE_SECONDS", "30")
        )

        # CORS
        self.cors_origins: str = os.environ.get("CORS_ORIGINS", "*")

        # Paths
        self.data_dir: Path = ROOT_DIR / "data"
        self.ndjson_path: Path = self.data_dir / "events.ndjson"


settings = Settings()
