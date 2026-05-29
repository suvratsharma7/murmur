"""LLMClient abstract base + shared OpenAI-compatible streaming implementation.

All three production runtimes (vLLM, SGLang, Ollama) expose the OpenAI Chat
Completions API. This module provides the shared SSE parsing logic; per-runtime
adapters inherit from OpenAICompatibleClient and override only config.

We parse SSE manually with httpx streaming rather than using the OpenAI Python
SDK because we need verified per-token yielding without any internal buffering.
Documented in docs/03-runtime-abstraction.md.
"""
import json
from abc import ABC, abstractmethod
from typing import AsyncIterator

import httpx
import structlog
from pydantic import BaseModel

logger = structlog.get_logger()


class GenerationParams(BaseModel):
    """Parameters for LLM text generation."""

    model: str = "Qwen/Qwen2.5-7B-Instruct"
    max_tokens: int = 256
    temperature: float = 0.7
    top_p: float = 0.95
    stream: bool = True


class LLMClient(ABC):
    """Abstract interface for one OpenAI-compatible streaming LLM client.

    All three runtimes (vLLM, SGLang, Ollama) expose POST /v1/chat/completions.
    The differences are: model name format (Ollama uses colon-separated),
    quirks of streaming SSE parsing, and runtime-specific health endpoints.
    """

    def __init__(self, base_url: str, params: GenerationParams | None = None):
        self.base_url = base_url.rstrip("/")
        self.params = params or GenerationParams()

    @abstractmethod
    async def health(self) -> bool:
        ...

    @abstractmethod
    def stream(self, prompt: str) -> AsyncIterator[str]:
        """Yield token strings as they arrive. Must NOT buffer.

        On error mid-stream, raise an exception; do not silently terminate.
        """
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        ...


class OpenAICompatibleClient(LLMClient):
    """Shared implementation for servers exposing the OpenAI Chat Completions API.

    vLLM, SGLang, and Ollama all support this endpoint. The SSE stream format
    is identical: lines prefixed with 'data: ' containing JSON with
    choices[0].delta.content, terminated by 'data: [DONE]'.
    """

    async def health(self) -> bool:
        """Check if the server is reachable via GET /v1/models."""
        try:
            async with httpx.AsyncClient() as http:
                resp = await http.get(f"{self.base_url}/v1/models", timeout=5.0)
                return resp.status_code == 200
        except (httpx.ConnectError, httpx.TimeoutException, httpx.HTTPError):
            return False

    async def stream(self, prompt: str) -> AsyncIterator[str]:
        """Stream tokens from an OpenAI-compatible /v1/chat/completions endpoint."""
        payload = {
            "model": self.params.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": self.params.max_tokens,
            "temperature": self.params.temperature,
            "top_p": self.params.top_p,
            "stream": True,
        }
        timeout = httpx.Timeout(connect=10.0, read=120.0, write=10.0, pool=10.0)

        async with httpx.AsyncClient() as http:
            async with http.stream(
                "POST",
                f"{self.base_url}/v1/chat/completions",
                json=payload,
                timeout=timeout,
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    data_str = line[6:].strip()
                    if data_str == "[DONE]":
                        return
                    try:
                        data = json.loads(data_str)
                        delta = data["choices"][0].get("delta", {})
                        content = delta.get("content", "")
                        if content:
                            yield content
                    except (json.JSONDecodeError, KeyError, IndexError) as exc:
                        logger.warning(
                            "sse_parse_error", line=line[:100], error=str(exc)
                        )
                        continue
