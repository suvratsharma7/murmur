.PHONY: help bench report charts clean test lint format

# Default target
help:
	@echo "MURMUR Makefile Targets:"
	@echo ""
	@echo "  make bench RUNTIME=<runtime>  - Run benchmark suite (vllm|sglang|ollama|mock)"
	@echo "  make report                    - Generate BENCHMARK_REPORT.md from results"
	@echo "  make charts                    - Generate PNG charts from results"
	@echo "  make test                      - Run backend tests"
	@echo "  make lint                      - Run linters (Python + TypeScript)"
	@echo "  make format                    - Format code (black + prettier)"
	@echo "  make clean                     - Clean benchmark results"
	@echo ""
	@echo "Examples:"
	@echo "  make bench RUNTIME=mock"
	@echo "  make bench RUNTIME=vllm DATASET=sharegpt_sample"
	@echo "  make report"
	@echo "  make charts"
	@echo "  make test"

# Run benchmark
RUNTIME ?= mock
DATASET ?= voice_turns

bench:
	@echo "Running benchmark: runtime=$(RUNTIME), dataset=$(DATASET)"
	cd bench && python3 run.py --runtime $(RUNTIME) --dataset $(DATASET)

# Generate report
report:
	@echo "Generating benchmark report..."
	cd bench && python3 generate_report.py

# Generate charts
charts:
	@echo "Generating benchmark charts..."
	cd bench && python3 charts.py

# Clean results
clean:
	@echo "Cleaning benchmark results..."
	rm -rf bench/results/*.json
	rm -f BENCHMARK_REPORT.md
	rm -f docs/img/ttft_comparison.png
	rm -f docs/img/throughput_comparison.png
	rm -f docs/img/e2e_comparison.png
	rm -f docs/img/tpot_comparison.png
	@echo "✓ Cleaned"

# Run full benchmark pipeline
all: bench report charts
	@echo "✓ Full benchmark pipeline complete"

# Run backend tests
test:
	@echo "Running backend tests..."
	cd backend && pytest -v

# Run linters
lint:
	@echo "Linting Python code..."
	cd backend && ruff check .
	@echo "Linting TypeScript code..."
	cd frontend && yarn build --dry-run 2>&1 | head -20

# Format code
format:
	@echo "Formatting Python code..."
	cd backend && ruff format .
	@echo "Formatting TypeScript code..."
	cd frontend && yarn prettier --write "app/**/*.{ts,tsx}" "src/**/*.{ts,tsx,js,jsx}"
