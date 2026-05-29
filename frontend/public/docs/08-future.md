# Future Work & Roadmap

This document outlines potential enhancements, research directions, and known limitations of MURMUR.

## Phase 1: Core Improvements

### 1.1 Voice Pipeline Benchmark Mode

**Status:** Planned

**Description:** Extend benchmark harness to measure full pipeline (STT → LLM → TTS) using pre-recorded audio fixtures.

**Implementation:**
```python
# bench/voice_pipeline_bench.py
class VoicePipelineBenchmark:
    async def run_turn(self, audio_fixture_path):
        # 1. Load PCM16 audio file
        # 2. Stream to /ws/stream endpoint
        # 3. Measure full E2E latency
        # 4. Collect metrics: STT + LLM + TTS combined
```

**Benefits:**
- Real-world user experience metrics
- Identify pipeline bottlenecks beyond LLM
- Test networking and WebSocket overhead

**Challenges:**
- Requires high-quality test audio recordings
- More complex timing measurement
- Hardware-dependent (microphone simulation)

---

### 1.2 Advanced Metrics

**Status:** Planned

**Additional metrics to track:**

1. **Inter-Token Variance**
   - Measure consistency of TPOT across response
   - Identify "hitches" or stalls in streaming

2. **Memory Usage**
   - Track VRAM consumption per runtime
   - Measure KV cache efficiency

3. **Batch Efficiency**
   - Compare single vs. batched request performance
   - Optimal batch size recommendations

4. **Queue Depth**
   - Monitor request queue length
   - Identify contention under load

**Implementation:**
```python
class AdvancedMetrics:
    inter_token_variance: float
    memory_peak_mb: int
    memory_mean_mb: int
    queue_depth_p95: int
    batch_utilization: float
```

---

### 1.3 Streaming Strategy Comparison

**Status:** Research

**Question:** How do different chunking strategies affect user experience?

**Strategies to Compare:**
1. **Sentence Boundary** (current) - Wait for `.` / `!` / `?`
2. **Fixed Token Count** - Chunk every N tokens
3. **Semantic Boundaries** - Pause at phrase breaks
4. **Hybrid** - Min tokens + semantic hints

**Metrics:**
- TTFB-audio variance
- Speech naturalness (human evaluation)
- Perceived latency (user study)

---

## Phase 2: Infrastructure & Scaling

### 2.1 Multi-Region Deployment

**Status:** Design

**Goal:** Deploy orchestrator + GPU services across multiple regions for latency optimization.

**Architecture:**
```
User (SF) → Orchestrator (SF) → GPU (us-west-1)
User (NYC) → Orchestrator (NYC) → GPU (us-east-1)
User (LON) → Orchestrator (LON) → GPU (eu-west-1)
```

**Challenges:**
- Orchestrator state synchronization
- Metrics aggregation across regions
- Cost optimization (GPU placement)

---

### 2.2 Kubernetes Deployment

**Status:** Draft

**Helm Chart Structure:**
```yaml
murmur/
  charts/
    - backend/        # FastAPI orchestrator
    - frontend/       # Next.js app
    - mongodb/        # Metrics storage
  values.yaml         # Configuration
```

**Features:**
- Horizontal pod autoscaling (HPA) for orchestrator
- GPU node affinity for inference services
- Persistent volume claims for MongoDB
- Ingress with TLS termination

---

### 2.3 Observability Stack

**Status:** Planned

**Components:**
- **Prometheus** - Metrics collection
- **Grafana** - Dashboards
- **Jaeger** - Distributed tracing
- **ELK Stack** - Log aggregation

**Custom Metrics:**
```
murmur_turns_total{runtime,status}
murmur_stt_latency_seconds_bucket
murmur_ttft_latency_seconds_bucket
murmur_websocket_connections_active
```

**Dashboards:**
1. Real-time voice pipeline overview
2. Per-runtime performance comparison
3. Error rate and SLO tracking
4. Cost per turn estimation

---

## Phase 3: Features & Usability

### 3.1 Multi-Turn Conversations

**Status:** Design

**Goal:** Support conversation context across multiple voice turns.

**Implementation:**
```python
class ConversationManager:
    def __init__(self, session_id: str):
        self.history = []
    
    async def add_turn(self, user_input: str, ai_response: str):
        self.history.append({
            "role": "user",
            "content": user_input
        })
        self.history.append({
            "role": "assistant",
            "content": ai_response
        })
    
    def get_context(self) -> List[Dict]:
        return self.history[-10:]  # Last 5 turns
```

**UI Changes:**
- Conversation history panel
- Clear context button
- Turn-by-turn metrics view

---

### 3.2 Model Selection

**Status:** Planned

**Goal:** Support multiple models per runtime.

**Configuration:**
```yaml
runtimes:
  vllm:
    models:
      - name: "llama-3-8b"
        vllm_url: "http://gpu:8001"
      - name: "llama-3-70b"
        vllm_url: "http://gpu:8002"
  sglang:
    models:
      - name: "qwen-2.5-7b"
        sglang_url: "http://gpu:8003"
```

**UI:**
- Dropdown for model selection
- Per-model benchmark results
- Model card information display

---

### 3.3 Batch Benchmarking

**Status:** Planned

**Goal:** Run benchmarks across all runtimes + datasets automatically.

**CLI:**
```bash
make bench-all
# Runs:
# - mock × voice_turns
# - mock × sharegpt_sample
# - vllm × voice_turns
# - vllm × sharegpt_sample
# - sglang × voice_turns
# - sglang × sharegpt_sample
# - ollama × voice_turns
# - ollama × sharegpt_sample
```

**Output:**
```
BENCHMARK_REPORT_FULL.md
charts/
  - runtime_comparison_voice_turns.png
  - runtime_comparison_sharegpt.png
  - dataset_comparison_vllm.png
  - concurrency_heatmap.png
```

---

### 3.4 Real-Time Collaboration

**Status:** Concept

**Goal:** Multiple users can join the same demo session and see/hear each other's interactions.

**Use Case:**
- Live demonstrations
- Collaborative testing
- A/B comparison sessions

**Architecture:**
- Room-based WebSocket broadcast
- Shared metrics dashboard
- Permission system (viewer vs. speaker)

---

## Phase 4: Research & Experimentation

### 4.1 Interruption Handling

**Status:** Research

**Challenge:** User interrupts AI mid-response (e.g., push-to-talk while speaking).

**Strategies:**
1. **Immediate Cancel** - Kill LLM/TTS, restart pipeline
2. **Graceful Pause** - Buffer partial response, resume if user stops
3. **Barge-In Detection** - Use VAD to detect overlapping speech

**Metrics:**
- Interruption latency (time to silence AI)
- Context preservation accuracy
- User satisfaction (subjective)

---

### 4.2 Adaptive Chunking

**Status:** Research

**Idea:** Dynamically adjust chunk size based on LLM generation speed.

**Algorithm:**
```python
if tokens_per_second > 50:
    chunk_size = 30  # More aggressive (lower latency)
elif tokens_per_second > 30:
    chunk_size = 20  # Balanced
else:
    chunk_size = 10  # Conservative (avoid gaps)
```

**Expected Benefit:**
- Optimize TTFB-audio vs. speech naturalness trade-off
- Adapt to varying LLM performance under load

---

### 4.3 Speculative TTS

**Status:** Concept

**Idea:** Start TTS synthesis before full sentence is complete.

**Approach:**
1. Predict sentence ending using language model
2. Start TTS speculatively
3. Validate prediction; if wrong, restart TTS

**Risk:**
- Increased compute (may waste TTS cycles)
- Complexity (requires rollback mechanism)

**Potential Gain:**
- 20-50ms TTFB-audio reduction
- More natural interruption handling

---

### 4.4 Edge Deployment

**Status:** Exploration

**Goal:** Run LLM inference on-device (laptop, mobile) for privacy and latency.

**Candidates:**
- **Ollama** - Already supports local deployment
- **MLX** - Apple Silicon optimized (M1/M2/M3)
- **llama.cpp** - CPU-optimized inference

**Challenges:**
- Model size constraints (7B models max)
- Battery/thermal management on mobile
- Quantization quality (4-bit vs. 8-bit)

---

## Known Limitations

### Current Constraints

1. **No Authentication**
   - Open WebSocket endpoint
   - Production requires external auth layer

2. **No Rate Limiting**
   - Vulnerable to DoS
   - Need per-IP or per-user quotas

3. **Single Language (English)**
   - Whisper supports multilingual, but pipeline hardcoded for English
   - TTS (Kokoro) is English-only

4. **No Streaming STT**
   - Whisper processes full audio clip
   - Faster-Whisper or streaming alternatives needed for sub-50ms STT

5. **Fixed Audio Format**
   - Hardcoded to 16kHz PCM16 input, 24kHz PCM16 output
   - No codec support (Opus, MP3, etc.)

6. **MongoDB Only**
   - No PostgreSQL or TimescaleDB support
   - Limited time-series query optimization

---

## Community Contributions Welcome

### Good First Issues

- **Add new runtime adapter** (e.g., TGI, llama.cpp, Petals)
- **Implement Prometheus metrics exporter**
- **Add more benchmark datasets** (multilingual, domain-specific)
- **Create Docker Compose production config**
- **Write integration tests** for WebSocket edge cases

### Research Collaboration

- **Interruption handling studies**
- **Adaptive chunking experiments**
- **Edge deployment benchmarks**
- **Multi-turn conversation datasets**

---

## Long-Term Vision

MURMUR aims to become the **de facto benchmarking standard** for voice AI pipelines, similar to how:

- **MLPerf** standardizes ML training/inference benchmarks
- **Speedtest** standardizes internet speed measurement
- **Lighthouse** standardizes web performance auditing

**Target Users:**
1. **LLM Serving Runtime Authors** - Optimize for voice workloads
2. **Voice AI Engineers** - Choose optimal infrastructure
3. **Researchers** - Study latency/quality trade-offs
4. **Cloud Providers** - Offer voice-optimized instance types

**Success Metrics:**
- Adopted by 3+ major LLM serving projects
- Cited in 10+ research papers
- Used in production by 50+ organizations

---

## Contributing

See `CONTRIBUTING.md` for development setup and guidelines.

**Contact:**
- GitHub Issues: Bug reports and feature requests
- Discussions: Architecture and research questions
- Email: maintainers@murmur.dev (not active yet)

---

**Previous:** [← Benchmarks](07-benchmarks.md) | **Back to:** [Introduction →](01-intro.md)
