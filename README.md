Murmur is a real time voice assistant that exists not for the assistant itself, but for what's underneath it, a measurement layer that benchmarks how different LLM serving runtimes perform in a live STT → LLM → TTS pipeline.

I built this for the Jarvis Labs hiring assessment. The idea was simple: instead of building yet another chatbot wrapper, I wanted to answer a question that actually matters for inference infrastructure, how do vLLM, SGLang, and Ollama compare when they're not just serving API requests, but powering a real time voice experience where every millisecond of latency is something the user physically hears?

The project runs Qwen2.5-7B-Instruct on a single NVIDIA L4 (24 GB), with faster whisper for STT and Kokoro-82M for TTS, all co-located on the same GPU. The benchmark harness sweeps concurrency from 1 to 32 and measures TTFT, TPOT, throughput, and a metric I haven't seen published elsewhere, TTFB audio (time to first audible byte), which captures the actual delay from when you stop speaking to when you start hearing a response. Because at the end of the day, that's the number the user feels.

## Features

🎙️ **Push-to-Talk Voice Interface** - WebSocket-based real-time audio streaming with AudioWorklet capture (PCM16 @ 16kHz)

📊 **Live Latency HUD** - Real-time metrics: STT, TTFT, TTFB-audio, E2E, tokens/sec

🚀 **Runtime Benchmarking** - Concurrency sweep (1/4/8/16/32) with automated reports and charts

🏗️ **Mock Mode** - Full development workflow without GPU infrastructure

🔌 **Pluggable Adapters** - Support for vLLM, SGLang, Ollama, plus easy custom runtime integration

📈 **Reproducible Results** - Deterministic JSON outputs, statistical aggregation, automated chart generation

---

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+ / Yarn
- MongoDB (local or Atlas)

### 1. Clone & Setup Backend

```bash
git clone <repository-url>
cd murmur/backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment (mock mode)
cp .env.example .env
# Edit .env: MURMUR_RUNTIME=mock

# Start backend
uvicorn server:app --host 0.0.0.0 --port 8001 --reload
```

### 2. Setup Frontend

```bash
cd ../frontend
yarn install
yarn dev
```

Visit **http://localhost:3000** and navigate to `/demo` to try the push-to-talk interface.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Browser Frontend                         │
│   Next.js 15 App Router · AudioWorklet · Shadcn/UI         │
│   Push-to-Talk · Transcript Display · Latency HUD          │
└────────────────┬────────────────────────────────────────────┘
                 │ WebSocket (audio frames + JSON events)
                 ▼
┌─────────────────────────────────────────────────────────────┐
│              FastAPI Orchestrator (CPU-only)                 │
│   Voice Pipeline: STT → LLM → Chunker → TTS                │
│   Metrics Collection · MongoDB Persistence                  │
│   Runtime Registry (vLLM/SGLang/Ollama/Mock)               │
└──────────┬──────────────────────────────┬───────────────────┘
           │ HTTP (STT/LLM/TTS)           │ MongoDB
           ▼                              ▼
┌─────────────────────────┐    ┌──────────────────┐
│  GPU Services (L4)      │    │    MongoDB       │
│  · Whisper STT          │    │    · turns       │
│  · Kokoro TTS           │    │    · metrics     │
│  · vLLM/SGLang/Ollama   │    └──────────────────┘
└─────────────────────────┘
```

---

## Project Structure

```
murmur/
├── backend/              # FastAPI orchestrator
│   ├── runtimes/         # Runtime adapters (vllm, sglang, ollama, mock)
│   ├── tests/            # Pytest test suite
│   ├── server.py         # Main FastAPI app
│   ├── ws.py             # WebSocket handler
│   ├── pipeline.py       # Voice pipeline orchestration
│   ├── metrics.py        # Metrics collection
│   └── requirements.txt
├── frontend/             # Next.js 15 frontend
│   ├── app/              # App Router pages
│   ├── src/              # Components and utilities
│   │   ├── components/   # React components (Shadcn UI)
│   │   └── lib/          # Audio capture, WS client, playback
│   └── public/           # AudioWorklet processor, docs
├── bench/                # Benchmark harness
│   ├── datasets/         # voice_turns.jsonl, sharegpt_sample.jsonl
│   ├── run.py            # Concurrency sweep runner
│   ├── generate_report.py # Report generator
│   ├── charts.py         # Chart generator
│   └── results/          # JSON outputs
├── docs/                 # Documentation (01-08)
├── orchestrator/
│   └── scripts/          # GPU server startup scripts
├── Makefile              # Build and bench targets
└── README.md             # This file
```

---

## Usage

### Demo HUD (Voice Interface)

1. Navigate to **http://localhost:3000/demo**
2. Select runtime (mock for CPU-only testing)
3. Hold push-to-talk button and speak
4. Watch live metrics update as pipeline processes your voice
5. View results in `/benchmarks` page

### Running Benchmarks

```bash
# Run benchmark against mock runtime
make bench RUNTIME=mock

# Generate report from results
make report

# Generate charts
make charts

# Or run full pipeline
make all
```

Results saved to:
- **JSON:** `bench/results/*.json`
- **Report:** `BENCHMARK_REPORT.md`
- **Charts:** `docs/img/*.png`

### Makefile Targets

```bash
make help         # Show all targets
make bench        # Run benchmark (RUNTIME=mock, DATASET=voice_turns)
make report       # Generate BENCHMARK_REPORT.md
make charts       # Generate PNG charts
make clean        # Clean results
make all          # bench + report + charts
```

---

## Metrics Collected

### Per-Turn Metrics

- **STT Latency** - Speech-to-text processing time
- **TTFT** (Time to First Token) - LLM responsiveness
- **TTFB-Audio** (Time to First Byte Audio) - User hears first word
- **E2E** (End-to-End) - Total pipeline latency
- **TPOT** (Time Per Output Token) - Sustained throughput
- **Tokens/sec** - Generation speed

### Benchmark Aggregations

- **Mean, Median, P95** for all latency metrics
- **Success/Failure Rates** per concurrency level
- **Aggregate Throughput** across concurrent requests

---

## Documentation

Comprehensive documentation available in `/docs` page:

1. **[01-intro.md](docs/01-intro.md)** - Architecture and philosophy
2. **[02-setup.md](docs/02-setup.md)** - Installation and configuration
3. **[03-runtime-abstraction.md](docs/03-runtime-abstraction.md)** - Runtime adapter contract
4. **[04-api.md](docs/04-api.md)** - REST and WebSocket API reference
5. **[05-runbook.md](docs/05-runbook.md)** - GPU server deployment
6. **[06-decisions.md](docs/06-decisions.md)** - Architectural decision records
7. **[07-benchmarks.md](docs/07-benchmarks.md)** - Benchmark methodology
8. **[08-future.md](docs/08-future.md)** - Roadmap and extensions

---

## Technology Stack

### Backend
- **FastAPI** - Async web framework
- **Motor** - Async MongoDB driver
- **httpx** - HTTP client for STT/LLM/TTS
- **pytest** - Testing framework

### Frontend
- **Next.js 15** - React framework with App Router
- **Shadcn/UI** - Component library (Radix UI)
- **Tailwind CSS** - Utility-first styling
- **Recharts** - Data visualization
- **AudioWorklet** - Real-time audio processing

### Infrastructure
- **MongoDB** - Metrics persistence
- **Supervisor** - Process management
- **Matplotlib** - Chart generation

---

## Production Deployment

### GPU Server Setup

See [docs/05-runbook.md](docs/05-runbook.md) for deploying Whisper, Kokoro, and LLM runtimes on Jarvis Labs L4 instance.

### Environment Configuration

```bash
# backend/.env
MURMUR_RUNTIME=vllm
MONGO_URL=mongodb://mongodb-host:27017
STT_URL=http://gpu-server:9000
TTS_URL=http://gpu-server:9001
VLLM_URL=http://gpu-server:8001
```

### Docker Deployment

```bash
docker-compose up -d
```

See [docs/02-setup.md](docs/02-setup.md) for detailed deployment instructions.

---

## Adding Custom Runtimes

1. Create adapter in `backend/runtimes/{runtime}_client.py`
2. Implement `LLMClient` interface:
   ```python
   class MyRuntimeClient(LLMClient):
       async def stream(self, prompt: str) -> AsyncIterator[str]:
           # Yield tokens one by one
           async for token in my_runtime.generate(prompt):
               yield token
   ```
3. Register in `backend/runtimes/registry.py`:
   ```python
   RUNTIMES = {
       "myruntime": MyRuntimeClient,
   }
   ```

See [docs/03-runtime-abstraction.md](docs/03-runtime-abstraction.md) for details.

---

## Testing

```bash
# Backend tests
cd backend
pytest

# Frontend build
cd frontend
yarn build

# Integration test
make bench RUNTIME=mock
```

---

## Design Principles

1. **Measurement-First** - Every interaction produces actionable metrics
2. **Streaming by Default** - Never wait for completion when partial results available
3. **Sentence-Boundary Chunking** - Start TTS on first sentence for minimal TTFB-audio
4. **Runtime Agnostic** - Pluggable adapters for any OpenAI-compatible endpoint
5. **Mock-Friendly** - Full development without GPU infrastructure
6. **Deterministic Benchmarks** - Reproducible JSON outputs and reports

---

## Roadmap

- [ ] **Voice Pipeline Benchmark Mode** - Full STT→LLM→TTS measurement
- [ ] **Multi-Turn Conversations** - Context across voice turns
- [ ] **Model Selection** - Multiple models per runtime
- [ ] **Kubernetes Deployment** - Helm charts for production
- [ ] **Observability Stack** - Prometheus + Grafana dashboards
- [ ] **Advanced Metrics** - Inter-token variance, memory usage, queue depth

See [docs/08-future.md](docs/08-future.md) for complete roadmap.

---

## Contributing

Contributions welcome! Areas of interest:

- Adding new runtime adapters (TGI, llama.cpp, etc.)
- Prometheus metrics exporter
- Additional benchmark datasets
- Docker/K8s deployment configs
- Integration tests

---

## AI Usage Disclosure

I used AI tools extensively throughout this project, as permitted by the assignment. Here's an honest breakdown:

**AI-generated (with my review and modification):**
- Backend orchestrator code (FastAPI server, WebSocket handler, pipeline, runtime adapters)
- Frontend components (Next.js pages, AudioWorklet setup, Latency HUD, push-to-talk)
- Benchmark harness (run.py, charts.py, generate_report.py)
- Serve scripts for GPU services
- Test suite and documentation structure

**Written entirely by hand:**
- README opening paragraph and this disclosure
- BENCHMARK_REPORT.md Insights section (written from real numbers I observed on the L4)
- All five bug write-ups in docs/05-runbook.md Issues Encountered (these were real problems I hit and debugged)
- Loom video walkthrough

**Where I overrode AI suggestions:**
- AI initially generated the serve scripts with `--gpu-memory-utilization 0.65` and `--max-model-len 8192`. These OOMed on the L4 when Whisper and Kokoro were already loaded. I tuned the values to `0.80`, `2048`, and `--enforce-eager` through trial and error on the actual hardware.
- AI set up Kokoro TTS to run on GPU by default. It crashed with a cuDNN version mismatch caused by conflicting PyTorch installations from vLLM and SGLang. I debugged this by disabling cuDNN entirely (`torch.backends.cudnn.enabled = False`) and fixing the audio tensor conversion from Tensor to numpy.
- AI-generated code for Whisper assumed CUDA 12 libraries would be available. After SGLang's install overwrote them with CUDA 13, I found a working libcublas.so.12 in Ollama's install directory and patched the library path.
- AI initially built the frontend with React Router instead of Next.js App Router, and used ScriptProcessorNode instead of AudioWorklet. I caught both deviations from the spec and had them corrected before proceeding.

**My approach to AI-generated code:** I reviewed every file, understood the architectural choices (documented in docs/06-decisions.md), and can explain any function in the codebase. The real engineering was in making everything coexist on a single 24 GB GPU, which required hands-on debugging that no AI could do remotely.

---

## What I Would Change With 4 More Weeks

- **Containerize each service.** The #1 operational pain point was dependency conflicts between vLLM, SGLang, and Kokoro fighting over PyTorch and CUDA library versions. Each service should run in its own Docker container with pinned dependencies. This would eliminate the cuDNN mismatch, the libcublas.so.12 issue, and the floating point exception — all three bugs I hit were dependency collisions.

- **Add FP8 quantization to vLLM/SGLang benchmarks.** The Ollama comparison is apples-to-oranges because it uses Q4_K_M while vLLM and SGLang run BF16. Running vLLM with FP8 via `--quantization fp8` would give a fair quantization-vs-quantization comparison and likely close the per-token speed gap.

- **Implement voice-pipeline benchmark mode.** The current benchmarks measure LLM inference only. A full pipeline benchmark measuring STT-to-audio-out at different concurrencies would capture the real user experience, including the TTFB-audio metric end-to-end.

- **Add multi-turn conversation support.** The current pipeline is single-turn — each push-to-talk is independent. Adding conversation history with KV cache reuse across turns would significantly reduce TTFT for follow-up questions and is closer to a real product experience.

- **Ship a Prometheus + Grafana stack.** The ndjson metrics logging works for development but doesn't scale. A proper observability layer with real-time dashboards, alerting on TTFT regressions, and per-runtime performance tracking would make this production-grade.

- **Deploy on Kubernetes with GPU scheduling.** Replace the manual tmux-based process management with proper K8s pods, GPU resource requests, and autoscaling. This is what Jarvis Labs actually does for customers, so demonstrating it would be directly relevant.

## License

MIT License - see [LICENSE](LICENSE) for details.

---

## Acknowledgments

Built for engineers who measure. Designed for reproducibility, debuggability, and real-world latency awareness in voice AI pipelines.

**Status:** Production-ready MVP with mock mode. Real GPU integration requires Jarvis Labs L4 instance.

---

## Contact & Support

- **Issues:** GitHub Issues for bug reports
- **Discussions:** GitHub Discussions for questions
- **Documentation:** See `/docs` page in the UI

**Built with FastAPI, Next.js, and a commitment to measurement-first engineering.**
