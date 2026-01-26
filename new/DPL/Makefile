# ============================================
# DPL: Political Rhetoric Analyzer
# Makefile for Docker operations
# ============================================

.PHONY: help build build-gpu run analyze shell clean setup download-model

# Default target
help:
	@echo "DPL: Political Rhetoric Analyzer"
	@echo ""
	@echo "Usage: make <target>"
	@echo ""
	@echo "Setup:"
	@echo "  setup          - Initial setup (copy .env, create dirs)"
	@echo "  download-model - Download Whisper model"
	@echo ""
	@echo "Docker:"
	@echo "  build          - Build Docker image (CPU)"
	@echo "  build-gpu      - Build Docker image (GPU/CUDA)"
	@echo "  shell          - Open shell in container"
	@echo "  clean          - Remove containers and images"
	@echo ""
	@echo "Analysis:"
	@echo "  analyze p=NAME - Full pipeline for politician NAME"
	@echo "  legacy t=FILE  - Analyze transcript FILE"
	@echo "  visualize r=FILE - Visualize results FILE"
	@echo ""
	@echo "Examples:"
	@echo "  make setup"
	@echo "  make build"
	@echo "  make analyze p='Donald Trump'"
	@echo "  make legacy t=data/transcripts/speech.txt"

# === Setup ===

setup:
	@echo "Setting up project..."
	@if not exist .env copy env.example .env
	@if not exist data\videos mkdir data\videos
	@if not exist data\transcripts mkdir data\transcripts
	@if not exist data\results mkdir data\results
	@if not exist models\whisper mkdir models\whisper
	@echo "Setup complete!"
	@echo "Next: make download-model (or manually clone whisper model)"

download-model:
	@echo "Downloading Whisper model..."
	cd models\whisper && git lfs install && git clone https://huggingface.co/openai/whisper-large-v3 .
	@echo "Model downloaded!"

# === Docker Build ===

build:
	@echo "Building Docker image (CPU)..."
	docker-compose build dpl

build-gpu:
	@echo "Building Docker image (GPU)..."
	docker-compose --profile gpu build dpl-gpu

# === Docker Run ===

shell:
	docker-compose run --rm dpl /bin/bash

# Analysis with politician name
analyze:
ifndef p
	@echo "Error: politician name required"
	@echo "Usage: make analyze p='Donald Trump'"
else
	docker-compose run --rm dpl analyze -p "$(p)"
endif

# Analysis with extended catalog
analyze-extended:
ifndef p
	@echo "Error: politician name required"
	@echo "Usage: make analyze-extended p='Donald Trump'"
else
	docker-compose run --rm dpl analyze -p "$(p)" --extended
endif

# Legacy analysis (existing transcript)
legacy:
ifndef t
	@echo "Error: transcript path required"
	@echo "Usage: make legacy t=data/transcripts/speech.txt"
else
	docker-compose run --rm dpl legacy -t "$(t)"
endif

# Visualize results
visualize:
ifndef r
	@echo "Error: results file required"
	@echo "Usage: make visualize r=data/results/analysis-2024-01-01.json"
else
	docker-compose run --rm dpl visualize -r "$(r)"
endif

# === GPU versions ===

analyze-gpu:
ifndef p
	@echo "Error: politician name required"
else
	docker-compose --profile gpu run --rm dpl-gpu analyze -p "$(p)"
endif

shell-gpu:
	docker-compose --profile gpu run --rm dpl-gpu /bin/bash

# === Cleanup ===

clean:
	@echo "Cleaning up..."
	docker-compose down --rmi local --volumes --remove-orphans
	@echo "Cleanup complete!"

# Remove only containers
stop:
	docker-compose down

# View logs
logs:
	docker-compose logs -f
