"""Ollama runtime adapter — Q4_K_M quantized serving via Ollama's OpenAI-compatible API.

Ollama defaults to Q4_K_M quantization (~5 GB VRAM), while vLLM and
SGLang serve in BF16 (~15 GB). This is not an apples-to-apples comparison
and is documented in docs/06-decisions.md.

Model name uses Ollama's colon-separated format rather than HuggingFace slashes.
"""
from runtimes.base import GenerationParams, OpenAICompatibleClient


class OllamaClient(OpenAICompatibleClient):
    """Ollama adapter for qwen2.5:7b-instruct (Q4_K_M quantized)."""

    OLLAMA_MODEL_NAME = "qwen2.5:7b-instruct"

    def __init__(self, base_url: str, params: GenerationParams | None = None):
        adjusted = params or GenerationParams()
        adjusted = adjusted.model_copy(update={"model": self.OLLAMA_MODEL_NAME})
        super().__init__(base_url, adjusted)

    @property
    def name(self) -> str:
        return "ollama"
