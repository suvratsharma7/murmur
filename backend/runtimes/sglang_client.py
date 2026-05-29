"""SGLang runtime adapter — BF16 serving via SGLang's OpenAI-compatible API.

SGLang uses RadixAttention for automatic KV cache reuse across
requests sharing common prefixes. For short voice prompts, prefix
caching yields minimal benefit unless a long system prompt is used.
Documented in docs/03-runtime-abstraction.md.
"""
from runtimes.base import OpenAICompatibleClient


class SGLangClient(OpenAICompatibleClient):
    """SGLang adapter for Qwen2.5-7B-Instruct."""

    @property
    def name(self) -> str:
        return "sglang"
