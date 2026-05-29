#!/usr/bin/env python3
"""
Benchmark harness for MURMUR LLM runtimes.

Simplified benchmarker that measures LLM inference latency directly
via the runtime adapters. Supports concurrency sweep and JSON output.
"""

import asyncio
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any
import argparse
from collections import defaultdict
import statistics
import sys

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from runtimes.registry import get_runtime

# Configuration
RESULTS_DIR = Path(__file__).parent / "results"
WARMUP_REQUESTS = 3
CONCURRENCY_LEVELS = [1, 4, 8, 16, 32]

class BenchmarkRunner:
    def __init__(self, runtime_name: str, dataset: str):
        self.runtime_name = runtime_name
        self.dataset = dataset
        self.runtime = None
        
    async def load_dataset(self) -> List[Dict[str, Any]]:
        """Load prompts from dataset file."""
        dataset_path = Path(__file__).parent / "datasets" / f"{self.dataset}.jsonl"
        prompts = []
        
        with open(dataset_path, 'r') as f:
            for line in f:
                data = json.loads(line)
                if 'prompt' in data:
                    # voice_turns.jsonl format
                    prompts.append({
                        'prompt': data['prompt'],
                        'category': data.get('category', 'general')
                    })
                elif 'conversations' in data:
                    # sharegpt_sample.jsonl format
                    conv = data['conversations']
                    if conv and conv[0].get('from') == 'human':
                        prompts.append({
                            'prompt': conv[0]['value'],
                            'category': 'conversation'
                        })
        
        return prompts
    
    async def single_request(self, prompt: str) -> Dict[str, Any]:
        """Execute single LLM request and measure latency."""
        
        start_time = time.perf_counter()
        ttft = None
        tokens = []
        
        try:
            async for chunk in self.runtime.stream(prompt):
                if ttft is None:
                    ttft = (time.perf_counter() - start_time) * 1000
                tokens.append(chunk)
        
        except Exception as e:
            return {"error": str(e)}
        
        e2e = (time.perf_counter() - start_time) * 1000
        token_count = len(tokens)
        
        if token_count > 1 and ttft:
            tpot = (e2e - ttft) / (token_count - 1) if token_count > 1 else 0
            throughput = token_count / (e2e / 1000) if e2e > 0 else 0
        else:
            tpot = 0
            throughput = 0
        
        return {
            "ttft_ms": ttft or 0,
            "e2e_ms": e2e,
            "tpot_ms": tpot,
            "tokens": token_count,
            "throughput_tps": throughput,
            "prompt_length": len(prompt),
        }
    
    async def run_concurrency_level(self, concurrency: int, prompts: List[Dict]) -> Dict[str, Any]:
        """Run benchmark at specific concurrency level."""
        print(f"  Running concurrency={concurrency}...")
        
        # Distribute prompts across concurrent requests
        tasks = []
        for i in range(concurrency):
            prompt_data = prompts[i % len(prompts)]
            tasks.append(self.single_request(prompt_data['prompt']))
        
        results = await asyncio.gather(*tasks)
        
        # Filter out errors
        valid_results = [r for r in results if 'error' not in r and r['ttft_ms']]
        
        if not valid_results:
            return {
                "concurrency": concurrency,
                "error": "All requests failed",
                "successful_requests": 0
            }
        
        # Aggregate metrics
        return {
            "concurrency": concurrency,
            "successful_requests": len(valid_results),
            "failed_requests": len(results) - len(valid_results),
            "ttft_ms": {
                "mean": statistics.mean(r['ttft_ms'] for r in valid_results),
                "median": statistics.median(r['ttft_ms'] for r in valid_results),
                "p95": statistics.quantiles(sorted(r['ttft_ms'] for r in valid_results), n=20)[18] if len(valid_results) > 1 else valid_results[0]['ttft_ms'],
                "min": min(r['ttft_ms'] for r in valid_results),
                "max": max(r['ttft_ms'] for r in valid_results),
            },
            "e2e_ms": {
                "mean": statistics.mean(r['e2e_ms'] for r in valid_results),
                "median": statistics.median(r['e2e_ms'] for r in valid_results),
                "p95": statistics.quantiles(sorted(r['e2e_ms'] for r in valid_results), n=20)[18] if len(valid_results) > 1 else valid_results[0]['e2e_ms'],
            },
            "tpot_ms": {
                "mean": statistics.mean(r['tpot_ms'] for r in valid_results if r['tpot_ms'] > 0),
                "median": statistics.median(r['tpot_ms'] for r in valid_results if r['tpot_ms'] > 0),
            } if any(r['tpot_ms'] > 0 for r in valid_results) else {"mean": 0, "median": 0},
            "throughput_tps": {
                "mean": statistics.mean(r['throughput_tps'] for r in valid_results),
                "total": sum(r['tokens'] for r in valid_results) / (max(r['e2e_ms'] for r in valid_results) / 1000),
            },
            "tokens": {
                "total": sum(r['tokens'] for r in valid_results),
                "mean_per_request": statistics.mean(r['tokens'] for r in valid_results),
            }
        }
    
    async def warmup(self, prompts: List[Dict]):
        """Run warmup requests to stabilize performance."""
        print(f"Running {WARMUP_REQUESTS} warmup requests...")
        for i in range(WARMUP_REQUESTS):
            prompt = prompts[i % len(prompts)]['prompt']
            await self.single_request(prompt)
        print("Warmup complete.")
    
    async def run(self):
        """Execute full benchmark suite."""
        print(f"\n{'='*60}")
        print(f"MURMUR Benchmark: {self.runtime_name} runtime")
        print(f"Dataset: {self.dataset}")
        print(f"{'='*60}\n")
        
        # Initialize runtime
        print("Initializing runtime...")
        self.runtime = get_runtime(self.runtime_name)
        
        # Load dataset
        prompts = await self.load_dataset()
        print(f"Loaded {len(prompts)} prompts from {self.dataset}")
        
        # Warmup
        await self.warmup(prompts)
        
        # Run concurrency sweep
        results = {
            "metadata": {
                "runtime": self.runtime_name,
                "dataset": self.dataset,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "concurrency_levels": CONCURRENCY_LEVELS,
            },
            "results": []
        }
        
        for concurrency in CONCURRENCY_LEVELS:
            result = await self.run_concurrency_level(concurrency, prompts)
            results["results"].append(result)
            
            # Print summary
            if 'error' not in result:
                print(f"    TTFT: {result['ttft_ms']['mean']:.1f}ms (p95: {result['ttft_ms']['p95']:.1f}ms)")
                print(f"    E2E:  {result['e2e_ms']['mean']:.1f}ms")
                print(f"    TPOT: {result['tpot_ms']['mean']:.2f}ms")
                print(f"    Throughput: {result['throughput_tps']['mean']:.1f} tok/s")
            else:
                print(f"    ERROR: {result['error']}")
            print()
        
        # Save results
        RESULTS_DIR.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = RESULTS_DIR / f"{self.runtime_name}_{self.dataset}_{timestamp}.json"
        
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n✓ Results saved to: {output_file}")
        return results


async def main():
    parser = argparse.ArgumentParser(description="MURMUR Benchmark Harness")
    parser.add_argument(
        "--runtime",
        choices=["vllm", "sglang", "ollama", "mock"],
        default="mock",
        help="LLM runtime to benchmark"
    )
    parser.add_argument(
        "--dataset",
        choices=["voice_turns", "sharegpt_sample"],
        default="voice_turns",
        help="Dataset to use for benchmarking"
    )
    
    args = parser.parse_args()
    
    runner = BenchmarkRunner(args.runtime, args.dataset)
    await runner.run()


if __name__ == "__main__":
    asyncio.run(main())
