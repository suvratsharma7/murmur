# Murmur — Architectural Decisions

A numbered record of every non-obvious decision, with reasoning. Updated continuously as the project evolves.

---

### 1. Why L4, not H100

The assessment budget provides ~₹1600 in Jarvis Labs credits. An L4 at ₹42.5/hr gives ~37 hours of runway — enough for development, debugging, and a full benchmark sweep. An H100 would burn through credits in under 10 hours. The assignment tests judgment and methodology, not raw FLOPs. An L4 is the right tool for a reproducible, honest benchmark within this budget.

### 2. Why Qwen2.5-7B-Instruct

Jarvis Labs' published blog ("vLLM vs SGLang vs TRT-LLM Comparison") benchmarks this exact model. Using the same model enables direct comparability with their methodology and results. A 7B parameter model also fits comfortably on an L4 with room for colocated STT and TTS services.

### 3. Why STT and TTS run on the L4, not in the Emergent orchestrator

Emergent deploys CPU-only containers. `faster-whisper large-v3-turbo` on CPU runs at roughly 1-2x realtime — a 5-second utterance would take 3-5 seconds to transcribe, destroying the latency story. On the L4 GPU it runs at ~30x realtime (~150ms for a 5-second clip). Kokoro TTS has a similar GPU advantage. The localhost-to-localhost network hop between services on the same L4 is sub-1ms — negligible compared to the compute savings.

### 4. Why Kokoro-82M for TTS

Kokoro-82M is fast (~0.5 GB VRAM), GPU-friendly, sounds natural for English, and exposes a generation pipeline that can be chunked into streaming segments. It ships via pip (`kokoro`) without complex engine builds. Alternatives like Bark (too slow), XTTS (too large), or Piper (CPU-only, less natural) were ruled out.

### 5. Why no TensorRT-LLM

TensorRT-LLM requires building an engine file for each model, which involves a multi-step compilation process that can take 30-60 minutes and is sensitive to GPU architecture, driver version, and model configuration. Within a 5-day assessment timebox, the risk of engine build failures consuming debugging hours outweighed the potential performance gains. Documented as the top item in `docs/07-future-work.md`.

### 6. Why Ollama is included despite Q4_K_M quantization unfairness

Ollama defaults to Q4_K_M quantization (~5 GB), while vLLM and SGLang run the model in BF16 (~15 GB). This is not an apples-to-apples comparison and is called out explicitly in the benchmark report methodology. Ollama is included because: (a) it is the most common "just works" LLM runtime and reviewers expect to see it, (b) the quantization tradeoff (lower quality, lower memory, different throughput characteristics) is itself an interesting result, (c) documenting the unfairness demonstrates benchmarking integrity.

### 7. Why sentence-boundary chunking, not fixed-token chunking

TTS prosody (how natural the speech sounds) depends heavily on receiving complete syntactic units. Cutting mid-sentence produces awkward pauses and unnatural intonation. Sentence boundaries (`.`, `!`, `?`, `\n`, `;`, `:`) produce the most natural-sounding speech. The 20-token fallback prevents indefinite stalls on long preambles without sentence-ending punctuation — a common LLM behavior pattern.

### 8. Why no auth, no multi-user, no persistent sessions

This is a single-user demo for a hiring assessment. Auth adds complexity without adding signal. The reviewer clicks a link, tries the demo, reads the report. Scope discipline: build fewer things well rather than more things poorly.

### 9. Why FastAPI + React (Emergent default stack)

FastAPI provides native async support for WebSockets and streaming HTTP, which are both critical for the pipeline. React is the Emergent default frontend. We use what the platform provides rather than fighting it. Both have strong type-safety stories (Pydantic for Python, TypeScript-like patterns for JS).

### 10. Why push-to-talk, not VAD (Voice Activity Detection)

Push-to-talk removes an entire dependency (silero-vad) and failure mode (false positive/negative speech boundaries). The demo audience is a recruiter clicking a button — not a hands-free use case. Deterministic "user holds button → audio streams → user releases → pipeline runs" is easier to demo, easier to debug, and produces more reproducible benchmark measurements.

### 11. Why WebSocket for audio, REST for everything else

Audio streaming requires low-latency bidirectional communication — WebSocket is the right tool. Runtime listing, benchmark results, and health checks are standard request-response patterns — REST is simpler and easier to test with curl. Mixing protocols where appropriate is better than forcing everything through one.

### 12. Why MongoDB for runtime metrics AND JSON files on disk for benchmark results

MongoDB is Emergent's default and works well for operational metrics (per-turn latencies). Benchmark results must also be committed to `bench/results/` as JSON so the GitHub repo is self-contained and reproducible without a live database. Both stores should agree; on a fresh benchmark run, write to both.
