# Introduction to MURMUR

## What is MURMUR?

MURMUR is a **measurement-first voice pipeline and LLM serving benchmark** designed for engineers who need debuggable, reproducible latency metrics. It orchestrates real-time audio through **STT → LLM → TTS** and benchmarks serving runtimes (vLLM, SGLang, Ollama) at scale.

### Philosophy

MURMUR is built on three core principles:

1. **Measurement-First Design**
   - Every interaction produces actionable metrics
   - Live HUD shows STT, TTFT, TTFB-audio, E2E latency, and throughput
   - Metrics persisted to MongoDB + NDJSON for analysis

2. **Streaming by Default**
   - Never wait for full completion when partial results are available
   - Token-by-token LLM streaming
   - Sentence-boundary chunking for minimal TTFB-audio
   - Overlapped STT/LLM/TTS processing

3. **Debuggable Architecture**
   - Mock mode for CPU-only development
   - Runtime adapters for pluggable backends
   - Clear phase transitions (listening → thinking → speaking)
   - Comprehensive logging and error reporting

## Problem Statement

### The Challenge

Voice AI pipelines face a critical challenge: **latency kills user experience**. In real-time voice applications, users expect:

- **Sub-200ms TTFT** (Time to First Token) - When does the AI start responding?
- **Sub-500ms TTFB-audio** (Time to First Byte Audio) - When do I hear the first word?
- **<2s E2E** (End-to-End) - Total interaction time

Traditional benchmarking tools measure **text LLM performance** but ignore the voice-specific pipeline overhead:
- Audio capture and encoding
- STT (Speech-to-Text) latency
- Streaming orchestration
- TTS (Text-to-Speech) synthesis
- Audio playback buffering

### The Solution

MURMUR addresses this by:

1. **Full Pipeline Measurement**
   - Captures metrics from microphone input to speaker output
   - Measures real-world latency including network overhead
   - Tracks per-turn metrics for reproducibility

2. **Smart Chunking Strategy**
   - Starts TTS on first sentence boundary (or 20-token fallback)
   - Minimizes TTFB-audio without waiting for full LLM completion
   - Maintains natural speech rhythm

3. **Runtime Comparison**
   - Benchmarks vLLM, SGLang, and Ollama under identical conditions
   - Concurrency sweep (1/4/8/16/32) reveals scaling behavior
   - Deterministic JSON outputs enable apples-to-apples comparison

## Architecture Overview

### Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                        Browser / Frontend                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Push-to-Talk │  │ Transcript   │  │ Latency HUD  │     │
│  │   (16kHz     │  │   Display    │  │  (Live       │     │
│  │   PCM16)     │  │              │  │   Metrics)   │     │
│  └──────┬───────┘  └──────────────┘  └──────────────┘     │
│         │ AudioWorklet                                      │
└─────────┼───────────────────────────────────────────────────┘
          │ WebSocket (binary audio frames + JSON events)
          ▼
┌─────────────────────────────────────────────────────────────┐
│              FastAPI Orchestrator (CPU-only)                 │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  WebSocket Handler (ws.py)                           │   │
│  │    • Receives audio frames                           │   │
│  │    • Sends status events (phase transitions)         │   │
│  │    • Sends transcript, tokens, audio, metrics        │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Voice Pipeline (pipeline.py)                        │   │
│  │    1. STT: Audio → Text (Whisper)                    │   │
│  │    2. LLM: Text → Tokens (vLLM/SGLang/Ollama)        │   │
│  │    3. Chunker: Tokens → Sentences (chunker.py)       │   │
│  │    4. TTS: Sentences → Audio (Kokoro)                │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Metrics Collection (metrics.py)                     │   │
│  │    • StageTimer for latency tracking                 │   │
│  │    • TurnMetrics aggregation                         │   │
│  │    • MongoDB + NDJSON persistence                    │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────┬────────────────────────────────────┬───────────────┘
          │ HTTP (STT/TTS/LLM)                │ MongoDB
          ▼                                    ▼
┌─────────────────────────────────┐  ┌──────────────────┐
│  GPU Inference Services         │  │   MongoDB        │
│  (Jarvis Labs L4 instance)      │  │   • turns        │
│  ┌─────────────────────────┐    │  │   • bench_runs   │
│  │ Whisper STT  (port 9000)│    │  └──────────────────┘
│  │ Kokoro TTS   (port 9001)│    │
│  │ vLLM         (port 8001)│    │
│  │ SGLang       (port 8002)│    │
│  │ Ollama       (port 8003)│    │
│  └─────────────────────────┘    │
└─────────────────────────────────┘
```

### Key Design Decisions

1. **CPU-Only Orchestrator**
   - All GPU work happens on remote L4 instance
   - Orchestrator is stateless and horizontally scalable
   - Mock mode enables development without GPU

2. **Sentence-Boundary Chunking**
   - Starts TTS synthesis on first complete sentence
   - Falls back to 20-token chunks if no sentence boundary
   - Balances latency vs. natural speech rhythm

3. **Streaming Everything**
   - Audio streamed as captured (not batched)
   - LLM tokens streamed as generated
   - TTS audio streamed as synthesized
   - UI updates in real-time

4. **Mock Mode First**
   - All components have mock implementations
   - Frontend development possible without infrastructure
   - Realistic latency profiles for testing

## Use Cases

### 1. Voice Application Development

Build and test voice AI applications with real-time feedback:
- Push-to-talk interface for prototyping
- Live latency HUD shows bottlenecks immediately
- Iterative optimization based on measured metrics

### 2. Runtime Selection

Compare LLM serving runtimes for your workload:
- Run identical benchmarks on vLLM, SGLang, Ollama
- Measure TTFT, TPOT, throughput under load
- Make data-driven infrastructure decisions

### 3. Latency Optimization

Identify and fix pipeline bottlenecks:
- Per-stage latency breakdown (STT, LLM, TTS)
- Concurrency testing reveals scaling limits
- Historical metrics track optimization progress

### 4. Research and Education

Study voice pipeline behavior:
- Reproducible benchmark results
- Open-source architecture for experimentation
- Mock mode enables classroom use

## What MURMUR is NOT

- **Not a production voice assistant** - MURMUR is a development and benchmarking tool
- **Not an LLM serving framework** - It orchestrates existing serving runtimes
- **Not cloud-hosted** - Self-hosted architecture for full control
- **Not audio quality focused** - Optimizes for latency, not audio fidelity

## Getting Started

See [02-setup.md](02-setup.md) for installation and configuration instructions.

For runtime adapter details, see [03-runtime-abstraction.md](03-runtime-abstraction.md).

For API reference, see [04-api.md](04-api.md).

---

**Next:** [Setup Guide →](02-setup.md)
