.PHONY: help build up down restart logs clean test

help:
	@echo "Rhetoric Analyzer - Available commands:"
	@echo "  make build    - Build all Docker images"
	@echo "  make up       - Start all services"
	@echo "  make down     - Stop all services"
	@echo "  make restart  - Restart all services"
	@echo "  make logs     - Show logs from all services"
	@echo "  make clean    - Remove all containers, volumes, and images"
	@echo "  make test     - Run tests"
	@echo "  make health   - Check health of all services"

build:
	docker-compose build

up:
	docker-compose up -d
	@echo "✅ All services started!"
	@echo "📊 Dashboard: http://localhost:8501"
	@echo "🔧 Ingest API: http://localhost:8001/docs"
	@echo "🎤 Transcribe API: http://localhost:8002/docs"
	@echo "🔍 Analyze API: http://localhost:8003/docs"
	@echo "💾 MinIO Console: http://localhost:9001"

down:
	docker-compose down

restart:
	docker-compose restart

logs:
	docker-compose logs -f

clean:
	docker-compose down -v --rmi all
	@echo "✅ Cleaned up all containers, volumes, and images"

test:
	@echo "Running tests..."
	# TODO: Add pytest commands

health:
	@echo "Checking service health..."
	@curl -s http://localhost:8001/health | python -m json.tool || echo "❌ Ingest service down"
	@curl -s http://localhost:8002/health | python -m json.tool || echo "❌ Transcribe service down"
	@curl -s http://localhost:8003/health | python -m json.tool || echo "❌ Analyze service down"

