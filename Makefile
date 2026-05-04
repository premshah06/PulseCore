.PHONY: up down logs test lint build shell-api shell-consumer init-db

ENV_FILE ?= .env

# ── Stack ──────────────────────────────────────────────────────────────────────
up: ## Start the full stack (builds images if needed)
	@[ -f $(ENV_FILE) ] || (cp .env.example $(ENV_FILE) && echo "Created $(ENV_FILE) from .env.example")
	docker compose --env-file $(ENV_FILE) up --build -d
	@echo ""
	@echo "Services starting. Check health with:  make status"
	@echo "Tail logs with:                        make logs"
	@echo "Dashboard:                             http://localhost:3000"
	@echo "API:                                   http://localhost:8000/docs"

down: ## Stop and remove containers (preserves volumes)
	docker compose down

down-v: ## Stop containers AND delete all volumes (wipes data)
	docker compose down -v

logs: ## Tail logs from all services
	docker compose logs -f

status: ## Show health status of all containers
	docker compose ps

build: ## Build all Docker images without starting
	docker compose build --parallel

# ── Database ───────────────────────────────────────────────────────────────────
init-db: ## Create MongoDB collections + indexes (run once after `make up`)
	python schema/init_mongo.py

# ── Tests ──────────────────────────────────────────────────────────────────────
test: test-backend test-frontend ## Run all tests

test-backend: ## Run Python tests with coverage
	pytest tests/ --cov=. --cov-report=term-missing --cov-fail-under=85 -q

test-frontend: ## Run Jest tests
	cd frontend && npm test -- --watchAll=false

# ── Lint ───────────────────────────────────────────────────────────────────────
lint: ## Run ruff + mypy
	ruff check .
	mypy api/ consumer/ inference/ producer/ --ignore-missing-imports

lint-fix: ## Auto-fix ruff violations
	ruff check . --fix

# ── Shells ─────────────────────────────────────────────────────────────────────
shell-api: ## Open a shell in the api container
	docker compose exec api bash

shell-consumer: ## Open a shell in the consumer container
	docker compose exec consumer bash

# ── Help ───────────────────────────────────────────────────────────────────────
help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

.DEFAULT_GOAL := help
