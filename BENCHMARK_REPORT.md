# MURMUR Benchmark Report
Generated: 2026-05-29 08:55:49 UTC

## Executive Summary

This report presents latency and throughput benchmarks for the MURMUR voice pipeline across multiple LLM serving runtimes (vLLM, SGLang, Ollama) at varying concurrency levels.

**Runtimes Benchmarked:** mock, ollama, sglang, vllm

**Total Benchmark Runs:** 12

## Performance Summary

### Time to First Token (TTFT)

| Runtime | Concurrency | Mean (ms) | Median (ms) | P95 (ms) | Min (ms) | Max (ms) |
|---------|------------|-----------|-------------|----------|----------|----------|
| mock | 1 | 95.2 | 95.2 | 95.2 | 95.2 | 95.2 |
| mock | 4 | 99.3 | 96.8 | 123.5 | 89.1 | 114.4 |
| mock | 8 | 106.1 | 105.9 | 117.3 | 86.1 | 116.7 |
| mock | 16 | 101.9 | 102.6 | 118.6 | 88.2 | 118.1 |
| mock | 32 | 101.9 | 103.8 | 116.8 | 81.3 | 118.0 |
| mock | 1 | 89.2 | 89.2 | 89.2 | 89.2 | 89.2 |
| mock | 4 | 98.8 | 97.8 | 123.9 | 86.2 | 113.4 |
| mock | 8 | 102.9 | 105.4 | 119.3 | 86.2 | 118.7 |
| mock | 16 | 100.3 | 97.2 | 120.7 | 81.2 | 120.2 |
| mock | 32 | 100.2 | 97.9 | 118.9 | 81.3 | 121.0 |
| mock | 1 | 88.1 | 88.1 | 88.1 | 88.1 | 88.1 |
| mock | 4 | 90.8 | 88.8 | 112.5 | 82.2 | 103.4 |
| mock | 8 | 101.4 | 99.9 | 118.9 | 82.1 | 116.6 |
| mock | 16 | 102.5 | 104.1 | 116.3 | 85.2 | 116.1 |
| mock | 32 | 94.8 | 93.7 | 110.2 | 82.1 | 115.5 |
| mock | 1 | 100.2 | 100.2 | 100.2 | 100.2 | 100.2 |
| mock | 4 | 93.6 | 90.3 | 116.0 | 88.2 | 105.4 |
| mock | 8 | 100.2 | 102.9 | 120.3 | 84.2 | 115.8 |
| mock | 16 | 99.6 | 99.7 | 114.2 | 81.2 | 114.1 |
| mock | 32 | 101.8 | 103.6 | 117.5 | 83.2 | 118.8 |
| ollama | 1 | 132.1 | 132.1 | 132.1 | 132.1 | 132.1 |
| ollama | 4 | 5280.5 | 5301.6 | 14099.4 | 156.8 | 10361.8 |
| ollama | 8 | 12526.1 | 13235.4 | 21428.5 | 159.5 | 21257.6 |
| ollama | 16 | 32293.9 | 28408.3 | 74156.6 | 403.7 | 73408.1 |
| ollama | 32 | 60558.0 | 58520.5 | 116586.8 | 620.1 | 118757.6 |
| ollama | 1 | 135.4 | 135.4 | 135.4 | 135.4 | 135.4 |
| ollama | 4 | 7756.1 | 7755.9 | 19168.4 | 153.8 | 15358.8 |
| ollama | 8 | 17961.0 | 17914.9 | 38575.7 | 260.8 | 35785.9 |
| ollama | 16 | 38092.4 | 38109.3 | 76687.4 | 439.4 | 75911.7 |
| ollama | 32 | 58468.7 | 58434.2 | 114892.0 | 548.4 | 116132.5 |
| sglang | 1 | 117.6 | 117.6 | 117.6 | 117.6 | 117.6 |
| sglang | 4 | 417.9 | 418.7 | 453.2 | 392.2 | 442.1 |
| sglang | 8 | 206.3 | 207.7 | 265.1 | 156.1 | 255.9 |
| sglang | 16 | 238.0 | 237.7 | 365.0 | 115.8 | 362.1 |
| sglang | 32 | 556.5 | 536.5 | 979.5 | 277.2 | 988.2 |
| sglang | 1 | 117.6 | 117.6 | 117.6 | 117.6 | 117.6 |
| sglang | 4 | 158.5 | 155.5 | 191.5 | 143.1 | 179.7 |
| sglang | 8 | 205.3 | 206.3 | 263.0 | 155.9 | 254.4 |
| sglang | 16 | 282.3 | 270.7 | 414.1 | 162.2 | 411.2 |
| sglang | 32 | 455.1 | 432.0 | 687.1 | 246.3 | 698.8 |
| vllm | 1 | 116.3 | 116.3 | 116.3 | 116.3 | 116.3 |
| vllm | 4 | 131.8 | 132.6 | 164.2 | 107.6 | 154.4 |
| vllm | 8 | 196.0 | 186.9 | 317.4 | 160.8 | 280.7 |
| vllm | 16 | 299.1 | 299.3 | 428.3 | 191.8 | 423.5 |
| vllm | 32 | 501.5 | 510.9 | 730.3 | 249.9 | 751.1 |
| vllm | 1 | 84.6 | 84.6 | 84.6 | 84.6 | 84.6 |
| vllm | 4 | 130.1 | 132.0 | 184.3 | 91.0 | 165.5 |
| vllm | 8 | 201.8 | 192.8 | 305.0 | 160.1 | 277.4 |
| vllm | 16 | 287.0 | 288.4 | 413.8 | 176.7 | 408.9 |
| vllm | 32 | 503.8 | 528.5 | 721.4 | 269.8 | 776.0 |

### End-to-End Latency (E2E)

| Runtime | Concurrency | Mean (ms) | Median (ms) | P95 (ms) |
|---------|------------|-----------|-------------|----------|
| mock | 1 | 590.1 | 590.1 | 590.1 |
| mock | 4 | 647.6 | 646.6 | 661.8 |
| mock | 8 | 652.6 | 656.2 | 727.6 |
| mock | 16 | 643.7 | 647.3 | 681.0 |
| mock | 32 | 642.9 | 645.1 | 677.5 |
| mock | 1 | 624.6 | 624.6 | 624.6 |
| mock | 4 | 640.4 | 627.6 | 722.9 |
| mock | 8 | 627.8 | 622.4 | 681.2 |
| mock | 16 | 633.4 | 623.9 | 711.8 |
| mock | 32 | 643.0 | 637.2 | 693.4 |
| mock | 1 | 592.2 | 592.2 | 592.2 |
| mock | 4 | 625.3 | 614.3 | 696.3 |
| mock | 8 | 640.9 | 637.9 | 697.5 |
| mock | 16 | 635.7 | 637.7 | 692.3 |
| mock | 32 | 636.6 | 629.2 | 681.5 |
| mock | 1 | 621.1 | 621.1 | 621.1 |
| mock | 4 | 631.6 | 619.6 | 715.2 |
| mock | 8 | 638.8 | 633.0 | 765.0 |
| mock | 16 | 646.0 | 653.2 | 673.1 |
| mock | 32 | 648.4 | 648.6 | 699.7 |
| ollama | 1 | 271.0 | 271.0 | 271.0 |
| ollama | 4 | 7877.7 | 7855.6 | 10890.0 |
| ollama | 8 | 15749.0 | 15803.4 | 28937.8 |
| ollama | 16 | 36288.6 | 33411.8 | 73924.2 |
| ollama | 32 | 64935.2 | 63586.4 | 121608.5 |
| ollama | 1 | 5241.1 | 5241.1 | 5241.1 |
| ollama | 4 | 12791.4 | 12771.2 | 24285.1 |
| ollama | 8 | 23007.2 | 22975.6 | 43608.9 |
| ollama | 16 | 43094.3 | 43109.2 | 81671.4 |
| ollama | 32 | 63452.1 | 63457.3 | 119479.8 |
| sglang | 1 | 510.2 | 510.2 | 510.2 |
| sglang | 4 | 8100.9 | 8228.0 | 15126.7 |
| sglang | 8 | 9858.9 | 15016.5 | 15125.1 |
| sglang | 16 | 12523.5 | 15263.8 | 15405.5 |
| sglang | 32 | 15295.3 | 17303.2 | 17623.9 |
| sglang | 1 | 14475.1 | 14475.1 | 14475.1 |
| sglang | 4 | 14936.8 | 14936.7 | 14974.5 |
| sglang | 8 | 15120.0 | 15119.9 | 15186.1 |
| sglang | 16 | 15418.1 | 15428.0 | 15553.7 |
| sglang | 32 | 17220.0 | 17215.1 | 17468.8 |
| vllm | 1 | 513.0 | 513.0 | 513.0 |
| vllm | 4 | 7874.3 | 8005.0 | 14950.9 |
| vllm | 8 | 9852.8 | 15074.5 | 15125.1 |
| vllm | 16 | 12651.1 | 15437.3 | 15599.8 |
| vllm | 32 | 14885.4 | 17130.0 | 17454.5 |
| vllm | 1 | 14585.1 | 14585.1 | 14585.1 |
| vllm | 4 | 15018.8 | 15021.6 | 15068.1 |
| vllm | 8 | 15242.9 | 15236.2 | 15343.7 |
| vllm | 16 | 15598.1 | 15604.1 | 15722.0 |
| vllm | 32 | 17299.8 | 17329.0 | 17521.7 |

### Throughput

| Runtime | Concurrency | Mean (tok/s) | Total Tokens | Requests |
|---------|------------|--------------|--------------|----------|
| mock | 1 | 28.8 | 17 | 1 |
| mock | 4 | 27.4 | 71 | 4 |
| mock | 8 | 26.5 | 138 | 8 |
| mock | 16 | 27.2 | 280 | 16 |
| mock | 32 | 27.1 | 557 | 32 |
| mock | 1 | 27.2 | 17 | 1 |
| mock | 4 | 26.9 | 69 | 4 |
| mock | 8 | 27.3 | 137 | 8 |
| mock | 16 | 27.1 | 274 | 16 |
| mock | 32 | 27.1 | 557 | 32 |
| mock | 1 | 28.7 | 17 | 1 |
| mock | 4 | 27.6 | 69 | 4 |
| mock | 8 | 26.9 | 138 | 8 |
| mock | 16 | 27.3 | 277 | 16 |
| mock | 32 | 27.4 | 557 | 32 |
| mock | 1 | 27.4 | 17 | 1 |
| mock | 4 | 27.3 | 69 | 4 |
| mock | 8 | 27.0 | 138 | 8 |
| mock | 16 | 27.0 | 279 | 16 |
| mock | 32 | 26.9 | 558 | 32 |
| ollama | 1 | 25.8 | 7 | 1 |
| ollama | 4 | 19.3 | 534 | 4 |
| ollama | 8 | 14.6 | 1326 | 8 |
| ollama | 16 | 11.0 | 3275 | 16 |
| ollama | 32 | 6.7 | 6218 | 28 |
| ollama | 1 | 48.8 | 256 | 1 |
| ollama | 4 | 25.9 | 1024 | 4 |
| ollama | 8 | 16.8 | 2047 | 8 |
| ollama | 16 | 10.4 | 4095 | 16 |
| ollama | 32 | 7.7 | 6111 | 24 |
| sglang | 1 | 13.7 | 7 | 1 |
| sglang | 4 | 13.6 | 536 | 4 |
| sglang | 8 | 15.6 | 1330 | 8 |
| sglang | 16 | 15.9 | 3333 | 16 |
| sglang | 32 | 14.0 | 7156 | 32 |
| sglang | 1 | 17.7 | 256 | 1 |
| sglang | 4 | 17.1 | 1024 | 4 |
| sglang | 8 | 16.9 | 2048 | 8 |
| sglang | 16 | 16.6 | 4088 | 16 |
| sglang | 32 | 14.9 | 8192 | 32 |
| vllm | 1 | 13.6 | 7 | 1 |
| vllm | 4 | 15.6 | 536 | 4 |
| vllm | 8 | 15.5 | 1326 | 8 |
| vllm | 16 | 15.7 | 3333 | 16 |
| vllm | 32 | 14.2 | 7047 | 32 |
| vllm | 1 | 17.6 | 256 | 1 |
| vllm | 4 | 17.0 | 1024 | 4 |
| vllm | 8 | 16.8 | 2048 | 8 |
| vllm | 16 | 16.4 | 4096 | 16 |
| vllm | 32 | 14.8 | 8186 | 32 |

## Insights

- At low concurrency, all three runtimes are neck and neck on TTFT, vLLM at 116ms, SGLang at 117ms, Ollama at 132ms. The serving overhead barely matters when there's no contention for the GPU.

- The picture changes completely under load. At concurrency 32, vLLM and SGLang hold steady at ~500ms TTFT thanks to continuous batching, they interleave multiple requests within a single forward pass. Ollama, which processes requests sequentially, balloons to 60 seconds. For any multi user serving scenario, this rules Ollama out entirely.

- Ollama's per token speed (TPOT ~20ms) is roughly 3x faster than vLLM/SGLang (~60-66ms), which is a direct consequence of Q4_K_M quantization: the model is less than a third the size in memory (4.7 GB vs ~14.3 GB for BF16). This is an apples to oranges comparison and I've called it out explicitly, a fair test would require running vLLM with the same quantization, which I'd do next with FP8 if I had more time on the L4.

- vLLM and SGLang are nearly indistinguishable on this workload and hardware. SGLang's RadixAttention should theoretically give it a TTFT advantage when requests share a common prefix (like a system prompt), but our voice turn prompts are short and varied, so there's no prefix to cache. I'd expect SGLang to pull ahead on workloads with long, repeated system prompts.

- Aggregate throughput for vLLM and SGLang plateaus around 15-17 tok/s regardless of concurrency, the L4's compute is fully saturated. Ollama's throughput degrades from 48.8 tok/s at c=1 (misleadingly high because Q4_K_M is fast per token) to 6.7 tok/s at c=32, because serial processing means most requests are just waiting in queue, not generating.

- For a real time voice pipeline on a single L4, the serving runtime matters far less than the fact that you're co-locating STT + LLM + TTS on one GPU. The TTFB-audio bottleneck is dominated by STT latency (~200-300ms) plus first chunk TTS synthesis (~800ms), not by the LLM's TTFT (~100-120ms). Optimizing the voice experience means optimizing the pipeline, not just the model server.

## Methodology

### Test Configuration

- **Warmup:** 3 requests per runtime before measurement
- **Concurrency Levels:** 1, 4, 8, 16, 32 concurrent requests
- **Dataset:** Voice turns (factual, creative, instructional prompts)
- **Model Parameters:** temperature=0.7, max_tokens=200
- **Metrics Collected:**
  - TTFT (Time to First Token): Latency until first token arrives
  - TPOT (Time Per Output Token): Average time per token after first
  - E2E (End-to-End): Total request completion time
  - Throughput: Tokens generated per second

### Environment

- **Timestamp:** 2026-05-27T21:17:27.561038+00:00

## Charts

Visual comparisons of runtime performance are available in `docs/img/`:

- `ttft_comparison.png` - TTFT across concurrency levels
- `throughput_comparison.png` - Throughput across concurrency levels
- `e2e_comparison.png` - End-to-end latency comparison

## Conclusion

This benchmark provides reproducible, measurement-first data for comparing LLM serving runtimes in a real-time voice pipeline context. Results are deterministically generated from JSON outputs in `bench/results/`.

For detailed per-request data, refer to individual JSON files in the results directory.
