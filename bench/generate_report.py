#!/usr/bin/env python3
"""
Generate markdown benchmark report from JSON results.

Reads all JSON files in bench/results/ and produces BENCHMARK_REPORT.md
with tables, comparisons, and key findings.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

RESULTS_DIR = Path(__file__).parent / "results"
OUTPUT_FILE = Path(__file__).parent.parent / "BENCHMARK_REPORT.md"

def load_results() -> List[Dict[str, Any]]:
    """Load all JSON result files."""
    results = []
    for json_file in RESULTS_DIR.glob("*.json"):
        with open(json_file, 'r') as f:
            data = json.load(f)
            results.append(data)
    return results

def generate_report(results: List[Dict[str, Any]]):
    """Generate comprehensive markdown report."""
    
    report = []
    report.append("# MURMUR Benchmark Report\n")
    report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n")
    
    report.append("## Executive Summary\n\n")
    report.append("This report presents latency and throughput benchmarks for the MURMUR voice pipeline ")
    report.append("across multiple LLM serving runtimes (vLLM, SGLang, Ollama) at varying concurrency levels.\n\n")
    
    # Group results by runtime
    by_runtime = {}
    for result in results:
        runtime = result['metadata']['runtime']
        if runtime not in by_runtime:
            by_runtime[runtime] = []
        by_runtime[runtime].append(result)
    
    report.append(f"**Runtimes Benchmarked:** {', '.join(sorted(by_runtime.keys()))}\n\n")
    report.append(f"**Total Benchmark Runs:** {len(results)}\n\n")
    
    # Summary table
    report.append("## Performance Summary\n\n")
    report.append("### Time to First Token (TTFT)\n\n")
    report.append("| Runtime | Concurrency | Mean (ms) | Median (ms) | P95 (ms) | Min (ms) | Max (ms) |\n")
    report.append("|---------|------------|-----------|-------------|----------|----------|----------|\n")
    
    for runtime, runtime_results in sorted(by_runtime.items()):
        for result in runtime_results:
            for concurrency_result in result['results']:
                if 'error' not in concurrency_result:
                    ttft = concurrency_result['ttft_ms']
                    conc = concurrency_result['concurrency']
                    report.append(
                        f"| {runtime} | {conc} | {ttft['mean']:.1f} | {ttft['median']:.1f} | "
                        f"{ttft['p95']:.1f} | {ttft['min']:.1f} | {ttft['max']:.1f} |\n"
                    )
    
    report.append("\n### End-to-End Latency (E2E)\n\n")
    report.append("| Runtime | Concurrency | Mean (ms) | Median (ms) | P95 (ms) |\n")
    report.append("|---------|------------|-----------|-------------|----------|\n")
    
    for runtime, runtime_results in sorted(by_runtime.items()):
        for result in runtime_results:
            for concurrency_result in result['results']:
                if 'error' not in concurrency_result:
                    e2e = concurrency_result['e2e_ms']
                    conc = concurrency_result['concurrency']
                    report.append(
                        f"| {runtime} | {conc} | {e2e['mean']:.1f} | {e2e['median']:.1f} | {e2e['p95']:.1f} |\n"
                    )
    
    report.append("\n### Throughput\n\n")
    report.append("| Runtime | Concurrency | Mean (tok/s) | Total Tokens | Requests |\n")
    report.append("|---------|------------|--------------|--------------|----------|\n")
    
    for runtime, runtime_results in sorted(by_runtime.items()):
        for result in runtime_results:
            for concurrency_result in result['results']:
                if 'error' not in concurrency_result:
                    tput = concurrency_result['throughput_tps']
                    tokens = concurrency_result['tokens']
                    conc = concurrency_result['concurrency']
                    reqs = concurrency_result['successful_requests']
                    report.append(
                        f"| {runtime} | {conc} | {tput['mean']:.1f} | {tokens['total']} | {reqs} |\n"
                    )
    
    # Key findings
    report.append("\n## Key Findings\n\n")
    report.append("### Latency\n\n")
    
    # Find best TTFT at each concurrency level
    for conc in [1, 4, 8, 16, 32]:
        best_ttft = None
        best_runtime = None
        
        for runtime, runtime_results in by_runtime.items():
            for result in runtime_results:
                for cr in result['results']:
                    if cr['concurrency'] == conc and 'error' not in cr:
                        ttft = cr['ttft_ms']['mean']
                        if best_ttft is None or ttft < best_ttft:
                            best_ttft = ttft
                            best_runtime = runtime
        
        if best_runtime:
            report.append(f"- **Concurrency {conc}:** {best_runtime} achieved lowest mean TTFT ({best_ttft:.1f}ms)\n")
    
    report.append("\n### Throughput\n\n")
    
    # Find best throughput
    for conc in [1, 4, 8, 16, 32]:
        best_tput = None
        best_runtime = None
        
        for runtime, runtime_results in by_runtime.items():
            for result in runtime_results:
                for cr in result['results']:
                    if cr['concurrency'] == conc and 'error' not in cr:
                        tput = cr['throughput_tps']['mean']
                        if best_tput is None or tput > best_tput:
                            best_tput = tput
                            best_runtime = runtime
        
        if best_runtime:
            report.append(f"- **Concurrency {conc}:** {best_runtime} achieved highest throughput ({best_tput:.1f} tok/s)\n")
    
    # Methodology
    report.append("\n## Methodology\n\n")
    report.append("### Test Configuration\n\n")
    report.append("- **Warmup:** 3 requests per runtime before measurement\n")
    report.append("- **Concurrency Levels:** 1, 4, 8, 16, 32 concurrent requests\n")
    report.append("- **Dataset:** Voice turns (factual, creative, instructional prompts)\n")
    report.append("- **Model Parameters:** temperature=0.7, max_tokens=200\n")
    report.append("- **Metrics Collected:**\n")
    report.append("  - TTFT (Time to First Token): Latency until first token arrives\n")
    report.append("  - TPOT (Time Per Output Token): Average time per token after first\n")
    report.append("  - E2E (End-to-End): Total request completion time\n")
    report.append("  - Throughput: Tokens generated per second\n\n")
    
    report.append("### Environment\n\n")
    if results:
        sample = results[0]['metadata']
        if 'backend_url' in sample:
            report.append(f"- **Backend URL:** {sample['backend_url']}\n")
        report.append(f"- **Timestamp:** {sample['timestamp']}\n")
    
    report.append("\n## Charts\n\n")
    report.append("Visual comparisons of runtime performance are available in `docs/img/`:\n\n")
    report.append("- `ttft_comparison.png` - TTFT across concurrency levels\n")
    report.append("- `throughput_comparison.png` - Throughput across concurrency levels\n")
    report.append("- `e2e_comparison.png` - End-to-end latency comparison\n\n")
    
    report.append("## Conclusion\n\n")
    report.append("This benchmark provides reproducible, measurement-first data for comparing ")
    report.append("LLM serving runtimes in a real-time voice pipeline context. Results are ")
    report.append("deterministically generated from JSON outputs in `bench/results/`.\n\n")
    report.append("For detailed per-request data, refer to individual JSON files in the results directory.\n")
    
    return ''.join(report)

def main():
    print("Loading benchmark results...")
    results = load_results()
    
    if not results:
        print("⚠ No results found in bench/results/")
        print("Run benchmarks first with: python bench/run.py --runtime <runtime>")
        return
    
    print(f"Found {len(results)} result file(s)")
    
    print("Generating report...")
    report_content = generate_report(results)
    
    with open(OUTPUT_FILE, 'w') as f:
        f.write(report_content)
    
    print(f"✓ Report generated: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
