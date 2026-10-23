.PHONY: all setup test train bench benchmark benchmark-live power capture simulate demo lint clean help

all: setup test

setup:
	@echo "Installing SlothMesh dependencies..."
	python3 -m pip install -r requirements.txt

test:
	@echo "Running SlothMesh test suite..."
	python3 -m pytest tests/ -v

train:
	@echo "Training TinyML model with session-based split & baselines..."
	python3 models/train_slothmesh_tinyml.py

bench: benchmark

benchmark:
	@echo "Running 52-scenario ablation benchmark (5 runs per scenario)..."
	python3 agent/sloth_benchmark_eval.py --mock --runs 5

benchmark-live:
	@echo "Running live benchmark with local Ollama models..."
	python3 agent/sloth_benchmark_eval.py --models rules_only tinyml_only cascaded_slothmesh qwen3:0.6b --runs 5

power:
	@echo "Computing two-domain power model & generating profile..."
	python3 power/measure_power.py

capture:
	@echo "Capturing real-time physical Wi-Fi telemetry..."
	python3 data/capture_real_rf.py --simulate --samples 20

simulate:
	@echo "Starting SlothMesh agent in simulation mode..."
	python3 agent/sloth_agent.py --simulate

demo:
	@echo "Running interactive cognitive demo (simulation mode)..."
	python3 run_live_demo.py --simulate

demo-hardware:
	@echo "Running interactive cognitive demo (physical hardware)..."
	python3 run_live_demo.py --hardware

lint:
	@echo "Checking Python syntax across project..."
	python3 -m py_compile agent/*.py models/*.py tests/*.py uno_q_core/*.py power/*.py data/*.py run_live_demo.py

clean:
	@echo "Cleaning cache files..."
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	rm -f agent/decisions_audit.jsonl

help:
	@echo "SlothMesh Development Commands:"
	@echo "  make setup          - Install dependencies from requirements.txt"
	@echo "  make test           - Run all 15 unit and integration tests"
	@echo "  make train          - Train INT8 TinyML model and export metrics.json"
	@echo "  make bench          - Run 52-scenario benchmark (5 runs/scenario)"
	@echo "  make benchmark-live - Run live benchmark with local Ollama models"
	@echo "  make power          - Execute two-domain derived energy profiler"
	@echo "  make capture        - Capture physical/simulated Wi-Fi telemetry"
	@echo "  make demo           - Run interactive cognitive demo (--simulate)"
	@echo "  make demo-hardware  - Run interactive demo on physical Arduino UNO Q"
	@echo "  make lint           - Verify Python syntax"
