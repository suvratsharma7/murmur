"""vLLM runtime adapter — BF16 serving via vLLM's OpenAI-compatible API.

vLLM uses PagedAttention for efficient KV cache management and
continuous batching for high-throughput concurrent serving.
Model name matches HuggingFace format directly.
"""
from runtimes.base import OpenAICompatibleClient


class VLLMClient(OpenAICompatibleClient):
    """vLLM adapter for Qwen2.5-7B-Instruct."""

    @property
    def name(self) -> str:
        return "vllm"
