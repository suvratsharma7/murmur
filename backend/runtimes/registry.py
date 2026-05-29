"""Runtime registry — maps runtime names to client classes.

Adding a 4th runtime (e.g., TensorRT-LLM) requires:
1. Creating one file in runtimes/ that subclasses LLMClient
2. Registering it here
Nothing else changes. Documented in docs/03-runtime-abstraction.md.
"""
from runtimes.base import LLMClient
from runtimes.mock_client import MockLLMClient
from runtimes.ollama_client import OllamaClient
from runtimes.sglang_client import SGLangClient
from runtimes.vllm_client import VLLMClient

from config import settings

RUNTIMES: dict[str, type[LLMClient]] = {
    "vllm": VLLMClient,
    "sglang": SGLangClient,
    "ollama": OllamaClient,
    "mock": MockLLMClient,
}

RUNTIME_URLS: dict[str, str] = {
    "vllm": settings.vllm_url,
    "sglang": settings.sglang_url,
    "ollama": settings.ollama_url,
    "mock": "http://mock",
}


def get_runtime(name: str) -> LLMClient:
    """Instantiate an LLM client by runtime name.

    Raises ValueError if the runtime name is not registered.
    """
    if name not in RUNTIMES:
        raise ValueError(f"Unknown runtime '{name}'. Available: {list(RUNTIMES)}")
    url = RUNTIME_URLS.get(name, "http://mock")
    return RUNTIMES[name](base_url=url)
