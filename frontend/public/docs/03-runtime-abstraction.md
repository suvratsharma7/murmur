# Murmur — Runtime Abstraction Layer

This document describes the design of the runtime abstraction layer that lets
the Murmur orchestrator swap LLM inference servers without changing any pipeline
code.

---

## 1. Architecture

The orchestrator talks to exactly one LLM server at a time. All three supported
servers (vLLM, SGLang, Ollama) expose the **OpenAI Chat Completions API**:

```
POST /v1/chat/completions  (streaming SSE)
GET  /v1/models             (health check)
```

The abstraction exploits this: a shared `OpenAICompatibleClient` base class
implements SSE parsing and health checks once. Per-runtime adapters override
only configuration (model name, port).

## 2. Class Hierarchy

```
LLMClient (ABC)
│
├── OpenAICompatibleClient       # SSE parsing, health(), stream()
│   ├── VLLMClient              # name="vllm", default model
│   ├── SGLangClient            # name="sglang", default model
│   └── OllamaClient            # name="ollama", model="qwen2.5:7b-instruct"
│
└── MockLLMClient                # Canned responses, no HTTP
```

## 3. Adding a New Runtime

To add a 4th runtime (e.g., TensorRT-LLM):

1. **Create one file** in `backend/runtimes/trtllm_client.py`:
   ```python
   from runtimes.base import OpenAICompatibleClient
   class TRTLLMClient(OpenAICompatibleClient):
       @property
       def name(self) -> str:
           return "trtllm"
   ```

2. **Register it** in `backend/runtimes/registry.py`:
   ```python
   from runtimes.trtllm_client import TRTLLMClient
   RUNTIMES["trtllm"] = TRTLLMClient
   RUNTIME_URLS["trtllm"] = settings.trtllm_url
   ```

3. **Add the env var** in `.env`:
   ```
   TRTLLM_URL=http://<l4-host>:8004
   ```

Nothing else changes. The WebSocket handler, pipeline, chunker, metrics,
frontend RuntimeSelector, and benchmarks harness all discover the new
runtime automatically via the registry.

## 4. Why Manual SSE Parsing

We parse SSE manually with `httpx` streaming rather than using the OpenAI
Python SDK because:

- **Verified per-token yielding**: The SDK may buffer tokens internally.
  Our manual parser yields each `data:` line individually, which is critical
  for accurate TTFT and TPOT measurement.
- **No SDK dependency**: Keeps the orchestrator's dependency list slim.
- **Uniform behavior**: All three runtimes use the same parser, eliminating
  SDK version mismatch risk.

## 5. Health Check Contract

Each runtime must implement `async health() -> bool`:
- Returns `True` if `GET /v1/models` returns HTTP 200 within 5 seconds.
- Returns `False` on connection error, timeout, or non-200 status.
- Never raises an exception.

The mock runtime always returns `True`.

## 6. Error Semantics

- If a runtime is unreachable, the orchestrator returns a typed error event
  to the WebSocket client: `{"type": "status", "phase": "error", "detail": "..."}`.
- No silent fallbacks. If vLLM is selected but down, the user sees the error.
- The frontend can then suggest switching to mock or another runtime.

## 7. Ollama Model Name Mapping

Ollama uses colon-separated model names (`qwen2.5:7b-instruct`) instead of
HuggingFace slash format (`Qwen/Qwen2.5-7B-Instruct`). The `OllamaClient`
handles this by overriding the `model` field in `GenerationParams` at
construction time. This is the only per-runtime configuration difference.

---
