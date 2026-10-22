.PHONY: all setup test train benchmark simulate clean help

all: setup test

setup:
	@echo "Installing SlothMesh dependencies..."
	python3 -m pip install -r requirements.txt

test:
	@echo "Running SlothMesh test suite..."
	python3 -m pytest tests/ -v

train:
	@echo "Training and quantizing TinyML model to INT8..."
	python3 models/train_slothmesh_tinyml.py

benchmark:
	@echo "Running local benchmark harness (mock mode)..."
	python3 agent/sloth_benchmark_eval.py --mock

benchmark-live:
	@echo "Running live benchmark with local Ollama..."
	python3 agent/sloth_benchmark_eval.py --models baseline qwen3:0.6b

simulate:
	@echo "Starting SlothMesh agent in simulation mode..."
	python3 agent/sloth_agent.py --simulate

demo:
	@echo "Running live hardware/simulated demo..."
	python3 run_live_demo.py

lint:
	@echo "Checking Python syntax across project..."
	python3 -m py_compile agent/*.py models/*.py tests/*.py uno_q_core/*.py run_live_demo.py

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
	@echo "  make benchmark      - Run benchmark in mocked mode"
	@echo "  make benchmark-live - Run benchmark with local Ollama models"
	@echo "  make simulate       - Run physical agent in hardware-free simulation"
	@echo "  make demo           - Run interactive judge demo"
	@echo "  make lint           - Verify Python syntax"
