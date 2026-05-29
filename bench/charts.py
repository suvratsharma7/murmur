#!/usr/bin/env python3
"""
Generate PNG charts from benchmark JSON results.

Creates comparison charts for TTFT, throughput, and E2E latency
across runtimes and concurrency levels.
"""

import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import numpy as np

RESULTS_DIR = Path(__file__).parent / "results"
OUTPUT_DIR = Path(__file__).parent.parent / "docs" / "img"

# Style configuration
plt.style.use('seaborn-v0_8-darkgrid')
COLORS = {'vllm': '#4A90E2', 'sglang': '#50C878', 'ollama': '#F5A623', 'mock': '#9B59B6'}

def load_results():
    """Load all JSON result files."""
    results = []
    for json_file in RESULTS_DIR.glob("*.json"):
        with open(json_file, 'r') as f:
            data = json.load(f)
            results.append(data)
    return results

def extract_metrics(results):
    """Extract metrics organized by runtime and concurrency."""
    data = {}
    
    for result in results:
        runtime = result['metadata']['runtime']
        if runtime not in data:
            data[runtime] = {
                'concurrency': [],
                'ttft_mean': [],
                'ttft_p95': [],
                'e2e_mean': [],
                'throughput_mean': [],
                'tpot_mean': []
            }
        
        for cr in result['results']:
            if 'error' not in cr:
                data[runtime]['concurrency'].append(cr['concurrency'])
                data[runtime]['ttft_mean'].append(cr['ttft_ms']['mean'])
                data[runtime]['ttft_p95'].append(cr['ttft_ms']['p95'])
                data[runtime]['e2e_mean'].append(cr['e2e_ms']['mean'])
                data[runtime]['throughput_mean'].append(cr['throughput_tps']['mean'])
                data[runtime]['tpot_mean'].append(cr['tpot_ms']['mean'])
    
    return data

def create_ttft_chart(data, output_path):
    """Create TTFT comparison chart."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    
    # Mean TTFT
    for runtime, metrics in sorted(data.items()):
        ax1.plot(
            metrics['concurrency'],
            metrics['ttft_mean'],
            marker='o',
            label=runtime,
            color=COLORS.get(runtime, '#333333'),
            linewidth=2
        )
    
    ax1.set_xlabel('Concurrency', fontsize=12)
    ax1.set_ylabel('Mean TTFT (ms)', fontsize=12)
    ax1.set_title('Time to First Token - Mean', fontsize=14, fontweight='bold')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # P95 TTFT
    for runtime, metrics in sorted(data.items()):
        ax2.plot(
            metrics['concurrency'],
            metrics['ttft_p95'],
            marker='s',
            label=runtime,
            color=COLORS.get(runtime, '#333333'),
            linewidth=2
        )
    
    ax2.set_xlabel('Concurrency', fontsize=12)
    ax2.set_ylabel('P95 TTFT (ms)', fontsize=12)
    ax2.set_title('Time to First Token - P95', fontsize=14, fontweight='bold')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()

def create_throughput_chart(data, output_path):
    """Create throughput comparison chart."""
    fig, ax = plt.subplots(figsize=(10, 6))
    
    for runtime, metrics in sorted(data.items()):
        ax.plot(
            metrics['concurrency'],
            metrics['throughput_mean'],
            marker='o',
            label=runtime,
            color=COLORS.get(runtime, '#333333'),
            linewidth=2,
            markersize=8
        )
    
    ax.set_xlabel('Concurrency', fontsize=12)
    ax.set_ylabel('Throughput (tokens/sec)', fontsize=12)
    ax.set_title('Throughput Comparison', fontsize=14, fontweight='bold')
    ax.legend(fontsize=11)
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()

def create_e2e_chart(data, output_path):
    """Create E2E latency comparison chart."""
    fig, ax = plt.subplots(figsize=(10, 6))
    
    for runtime, metrics in sorted(data.items()):
        ax.plot(
            metrics['concurrency'],
            metrics['e2e_mean'],
            marker='D',
            label=runtime,
            color=COLORS.get(runtime, '#333333'),
            linewidth=2,
            markersize=7
        )
    
    ax.set_xlabel('Concurrency', fontsize=12)
    ax.set_ylabel('Mean E2E Latency (ms)', fontsize=12)
    ax.set_title('End-to-End Latency Comparison', fontsize=14, fontweight='bold')
    ax.legend(fontsize=11)
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()

def create_tpot_chart(data, output_path):
    """Create TPOT comparison chart."""
    fig, ax = plt.subplots(figsize=(10, 6))
    
    for runtime, metrics in sorted(data.items()):
        ax.plot(
            metrics['concurrency'],
            metrics['tpot_mean'],
            marker='^',
            label=runtime,
            color=COLORS.get(runtime, '#333333'),
            linewidth=2,
            markersize=8
        )
    
    ax.set_xlabel('Concurrency', fontsize=12)
    ax.set_ylabel('Mean TPOT (ms)', fontsize=12)
    ax.set_title('Time Per Output Token Comparison', fontsize=14, fontweight='bold')
    ax.legend(fontsize=11)
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()

def main():
    print("Loading benchmark results...")
    results = load_results()
    
    if not results:
        print("⚠ No results found in bench/results/")
        print("Run benchmarks first with: python bench/run.py --runtime <runtime>")
        return
    
    print(f"Found {len(results)} result file(s)")
    
    print("Extracting metrics...")
    data = extract_metrics(results)
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    print("Generating charts...")
    create_ttft_chart(data, OUTPUT_DIR / "ttft_comparison.png")
    print("  ✓ ttft_comparison.png")
    
    create_throughput_chart(data, OUTPUT_DIR / "throughput_comparison.png")
    print("  ✓ throughput_comparison.png")
    
    create_e2e_chart(data, OUTPUT_DIR / "e2e_comparison.png")
    print("  ✓ e2e_comparison.png")
    
    create_tpot_chart(data, OUTPUT_DIR / "tpot_comparison.png")
    print("  ✓ tpot_comparison.png")
    
    print(f"\n✓ All charts saved to: {OUTPUT_DIR}")

if __name__ == "__main__":
    main()
