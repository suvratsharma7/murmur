# Benchmark Methodology

This document describes MURMUR's benchmark harness design, methodology, and interpretation guidelines.

## Overview

MURMUR's benchmark harness measures **LLM runtime performance** in a voice pipeline context, focusing on:

- **TTFT** (Time to First Token) - Streaming responsiveness
- **TPOT** (Time Per Output Token) - Sustained throughput
- **E2E** (End-to-End) - Total completion time
- **Throughput** - Tokens generated per second

## Benchmark Architecture

```
┌──────────────────────────────────────────────────┐
│  bench/run.py (Orchestrator)                     │
│  ┌────────────────────────────────────────────┐  │
│  │  1. Load dataset (voice_turns.jsonl)      │  │
│  │  2. Initialize runtime adapter             │  │
│  │  3. Run warmup (3 requests)                │  │
│  │  4. For each concurrency level:            │  │
│  │     - Launch N concurrent requests         │  │
│  │     - Measure TTFT, E2E, TPOT             │  │
│  │     - Aggregate statistics                 │  │
│  │  5. Save JSON results                      │  │
│  └────────────────────────────────────────────┘  │
└──────────────┬────────────────────┬──────────────┘
               │                     │
               ▼                     ▼
        ┌─────────────┐      ┌──────────────┐
        │  LLM        │      │  JSON        │
        │  Runtime    │      │  Results     │
        │  Adapter    │      │  Storage     │
        └─────────────┘      └──────────────┘
                                     │
                                     ▼
                           ┌──────────────────┐
                           │ generate_report  │
                           │ + charts.py      │
                           └──────────────────┘
```

## Datasets

### voice_turns.jsonl

185 prompts designed for voice interaction:

- **Categories:** Factual, scientific, technical, creative, philosophical
- **Length:** Short (1-15 words) for natural voice queries
- **Format:** `{"prompt": "...", "category": "..."}`
- **Purpose:** Simulate real voice assistant usage

**Example:**
```json
{"prompt": "What is the capital of France?", "category": "factual"}
{"prompt": "Explain quantum computing in simple terms.", "category": "explanation"}
```

### sharegpt_sample.jsonl

161 conversation-style prompts:

- **Source:** ShareGPT conversation dataset patterns
- **Format:** `{"conversations": [{"from": "human", "value": "..."}]}`
- **Purpose:** Measure text-heavy interaction performance

**Example:**
```json
{
  "conversations": [
    {"from": "human", "value": "What is machine learning?"},
    {"from": "gpt", "value": "Machine learning is..."}
  ]
}
```

## Concurrency Levels

Benchmarks run at **five concurrency levels**: 1, 4, 8, 16, 32

### Why These Levels?

- **1** - Baseline single-user performance
- **4** - Typical small team / low concurrency
- **8** - Moderate load
- **16** - High load / production traffic
- **32** - Stress test / scaling limits

### Concurrency Behavior

- Requests are launched **simultaneously** (not sequentially)
- Prompts are **round-robin distributed** from dataset
- Each concurrency level is independent (no shared state)

## Metrics Collected

### Time to First Token (TTFT)

**Definition:** Latency from request start to first token arrival

**Measurement:**
```python
start = time.perf_counter()
async for token in runtime.stream(prompt):
    if ttft is None:
        ttft = (time.perf_counter() - start) * 1000
```

**Interpretation:**
- **<100ms** - Excellent (imperceptible delay)
- **100-300ms** - Good (acceptable for voice)
- **>300ms** - Poor (noticeable lag)

**Key Factor:** TTFT measures model warmth, queue depth, and inference startup overhead.

### Time Per Output Token (TPOT)

**Definition:** Average time between consecutive tokens

**Measurement:**
```python
tpot = (e2e_ms - ttft_ms) / (token_count - 1)
```

**Interpretation:**
- **<20ms** - Excellent (>50 tok/s)
- **20-40ms** - Good (25-50 tok/s)
- **>40ms** - Poor (<25 tok/s)

**Key Factor:** TPOT measures sustained decoding speed and memory bandwidth.

### End-to-End Latency (E2E)

**Definition:** Total time from request start to completion

**Measurement:**
```python
start = time.perf_counter()
# ... full request execution ...
e2e = (time.perf_counter() - start) * 1000
```

**Interpretation:**
- Context-dependent (varies with output length)
- Useful for comparing same-prompt-length scenarios
- Lower is better (faster total completion)

### Throughput

**Definition:** Tokens generated per second

**Measurement:**
```python
throughput = token_count / (e2e_ms / 1000)
```

**Interpretation:**
- **>30 tok/s** - Excellent
- **20-30 tok/s** - Good
- **<20 tok/s** - Poor for real-time voice

## Statistical Aggregation

For each concurrency level, we compute:

### Mean
```python
statistics.mean(values)
```
Average performance across all requests.

### Median
```python
statistics.median(values)
```
Middle value (50th percentile) - robust to outliers.

### P95 (95th Percentile)
```python
statistics.quantiles(sorted(values), n=20)[18]
```
95% of requests complete faster than this - tail latency indicator.

### Min / Max
```python
min(values), max(values)
```
Best and worst case performance.

## Warmup Strategy

**Purpose:** Eliminate cold-start effects and JIT compilation overhead

**Implementation:**
```python
async def warmup(self, prompts: List[Dict]):
    for i in range(3):  # 3 warmup requests
        prompt = prompts[i % len(prompts)]['prompt']
        await self.single_request(prompt)
```

**Why 3 requests?**
- First request: Initialize runtime, load model
- Second request: JIT compilation warmup
- Third request: Stabilize memory allocation

Warmup results are **discarded** and not included in benchmark metrics.

## Error Handling

### Failed Requests

Tracked separately:
```python
{
  "successful_requests": 14,
  "failed_requests": 2,
  "error": "Timeout after 60s"
}
```

### Error Categories

- **Timeout** - Request exceeded 60s
- **Connection** - Network failure
- **Runtime** - Model inference error
- **Invalid Response** - Malformed streaming output

Failed requests are **excluded** from metric calculations.

## JSON Output Format

```json
{
  "metadata": {
    "runtime": "mock",
    "dataset": "voice_turns",
    "timestamp": "2026-05-27T20:00:00Z",
    "concurrency_levels": [1, 4, 8, 16, 32]
  },
  "results": [
    {
      "concurrency": 1,
      "successful_requests": 1,
      "failed_requests": 0,
      "ttft_ms": {
        "mean": 100.2,
        "median": 100.2,
        "p95": 100.2,
        "min": 100.2,
        "max": 100.2
      },
      "e2e_ms": {
        "mean": 621.1,
        "median": 621.1,
        "p95": 621.1
      },
      "tpot_ms": {
        "mean": 32.5,
        "median": 32.5
      },
      "throughput_tps": {
        "mean": 27.4,
        "total": 27.4
      },
      "tokens": {
        "total": 17,
        "mean_per_request": 17.0
      }
    }
  ]
}
```

## Report Generation

### generate_report.py

Reads all JSON files from `bench/results/` and produces `BENCHMARK_REPORT.md`.

**Contents:**
1. Executive summary
2. Performance tables (TTFT, E2E, throughput)
3. Key findings (best performers per metric)
4. Methodology description
5. Environment details

**Determinism:** Running `generate_report.py` multiple times with same inputs produces **identical output**.

### charts.py

Generates 4 PNG charts using matplotlib:

1. **ttft_comparison.png** - Mean + P95 TTFT across concurrency
2. **throughput_comparison.png** - Tokens/sec comparison
3. **e2e_comparison.png** - End-to-end latency
4. **tpot_comparison.png** - Time per output token

Charts use **consistent colors** per runtime:
- vLLM: Blue (#4A90E2)
- SGLang: Green (#50C878)
- Ollama: Orange (#F5A623)
- Mock: Purple (#9B59B6)

## Running Benchmarks

### Single Runtime

```bash
make bench RUNTIME=mock
```

### Multiple Runtimes

```bash
make bench RUNTIME=vllm
make bench RUNTIME=sglang
make bench RUNTIME=ollama
make report
make charts
```

### Custom Dataset

```bash
make bench RUNTIME=mock DATASET=sharegpt_sample
```

### Viewing Results

1. **JSON:** `bench/results/*.json`
2. **Report:** `BENCHMARK_REPORT.md`
3. **Charts:** `docs/img/*.png`
4. **UI:** Navigate to `/benchmarks` page

## Interpretation Guidelines

### Comparing Runtimes

**Use Case:** Choosing between vLLM, SGLang, Ollama

**Metrics Priority:**
1. **TTFT** - Most critical for voice (user-facing latency)
2. **Throughput** - Sustained performance under load
3. **P95 TTFT** - Consistency (avoid outliers)

**Example Decision Matrix:**

| Metric | vLLM | SGLang | Ollama | Winner |
|--------|------|--------|--------|--------|
| TTFT (1x) | 85ms | 92ms | 120ms | vLLM |
| TTFT P95 (16x) | 110ms | 105ms | 180ms | SGLang |
| Throughput (16x) | 45 tok/s | 48 tok/s | 32 tok/s | SGLang |

**Recommendation:** SGLang for production (better P95 + throughput)

### Concurrency Scaling

**Good Scaling:**
- TTFT increases <30% from 1→32 concurrency
- Throughput remains stable or improves
- P95 stays within acceptable bounds

**Poor Scaling:**
- TTFT doubles or triples under load
- Throughput drops significantly
- High variance (large gap between mean and P95)

### Voice Pipeline Context

For real-time voice applications:

**Critical Path:** User speech → STT → **TTFT** → TTS → Audio playback

**Target:** E2E <2s for natural conversation

**Budget Breakdown:**
- STT: ~150ms (Whisper base)
- TTFT: <100ms (LLM)
- TTS: ~200ms (first sentence)
- Network: ~50ms (round-trip)
- **Total:** ~500ms to first audio

Remaining budget (~1.5s) for full response generation.

## Limitations

### Current Scope

Benchmarks measure **LLM runtime adapter streaming performance** only.

**Excluded from measurement:**
- Actual STT latency (Whisper processing time)
- Actual TTS latency (Kokoro synthesis time)
- WebSocket overhead
- Network latency
- Browser audio playback buffering

### Future Extension

**Voice Pipeline Benchmark Mode** (optional):

Use pre-recorded PCM16 audio fixtures to drive `/ws/stream` and measure:
- Full pipeline E2E (mic → speaker)
- STT + LLM + TTS combined latency
- Real-world user experience metrics

See [08-future.md](08-future.md) for details.

## Reproducibility

### Checklist

✅ **Deterministic datasets** - Committed JSONL files
✅ **Fixed concurrency levels** - 1/4/8/16/32
✅ **Warmup phase** - Eliminate cold starts
✅ **JSON outputs** - Machine-readable results
✅ **Statistical rigor** - Mean, median, P95
✅ **Error tracking** - Failed requests logged

### Best Practices

1. **Isolated environment** - No competing workloads
2. **Multiple runs** - Average across 3+ benchmark runs
3. **Version control** - Commit JSON results with git
4. **Documentation** - Note hardware specs, model versions
5. **Comparison baseline** - Always include mock results

---

**Previous:** [← Decisions](06-decisions.md) | **Next:** [Future Work →](08-future.md)
