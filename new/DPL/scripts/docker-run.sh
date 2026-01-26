#!/bin/bash
# ============================================
# DPL Docker Run Script (Linux/Mac)
# ============================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== DPL: Political Rhetoric Analyzer ===${NC}"

# Проверяем наличие .env
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}Creating .env from env.example...${NC}"
    cp env.example .env
fi

# Проверяем наличие модели Whisper
if [ ! -f "models/whisper/config.json" ]; then
    echo -e "${RED}Warning: Whisper model not found in models/whisper/${NC}"
    echo -e "${YELLOW}Please clone the model first:${NC}"
    echo "  cd models/whisper"
    echo "  git lfs install"
    echo "  git clone https://huggingface.co/openai/whisper-large-v3 ."
    echo ""
fi

# Проверяем аргументы
if [ $# -eq 0 ]; then
    echo "Usage: $0 <command> [args]"
    echo ""
    echo "Commands:"
    echo "  analyze -p <politician>   Full pipeline: search → download → transcribe → analyze"
    echo "  legacy -t <transcript>    Analyze existing transcript"
    echo "  visualize -r <results>    Visualize existing results"
    echo "  shell                     Open shell in container"
    echo "  build                     Build Docker image"
    echo "  build-gpu                 Build GPU Docker image"
    echo ""
    echo "Examples:"
    echo "  $0 analyze -p 'Donald Trump'"
    echo "  $0 legacy -t data/transcripts/speech.txt"
    echo "  $0 shell"
    exit 0
fi

COMMAND=$1
shift

case $COMMAND in
    build)
        echo -e "${GREEN}Building Docker image (CPU)...${NC}"
        docker-compose build dpl
        ;;
    build-gpu)
        echo -e "${GREEN}Building Docker image (GPU)...${NC}"
        docker-compose --profile gpu build dpl-gpu
        ;;
    shell)
        echo -e "${GREEN}Opening shell in container...${NC}"
        docker-compose run --rm dpl /bin/bash
        ;;
    analyze|legacy|visualize)
        echo -e "${GREEN}Running: $COMMAND $@${NC}"
        docker-compose run --rm dpl $COMMAND "$@"
        ;;
    *)
        echo -e "${GREEN}Running custom command: $COMMAND $@${NC}"
        docker-compose run --rm dpl $COMMAND "$@"
        ;;
esac
