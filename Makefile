# ── Utility Meter-to-Cash: Phase 1 Makefile ──────────────────────────────────
# Requires: Docker, Docker Compose, Python ≥ 3.11 + pip

.DEFAULT_GOAL := help
.PHONY: help up down clean seed seed-large cdc test psql logs check-env

# ── Colours ──────────────────────────────────────────────────────────────────
CYAN  := \033[0;36m
RESET := \033[0m

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN{FS=":.*?## "}; {printf "  $(CYAN)%-18s$(RESET) %s\n", $$1, $$2}'

# ── Infrastructure ────────────────────────────────────────────────────────────
up: ## Start PostgreSQL (runs migrations on first boot)
	docker compose up -d
	@echo "Waiting for PostgreSQL to become healthy..."
	@until docker compose exec postgres pg_isready -U meter_user -d meter_to_cash -q; do sleep 1; done
	@echo "PostgreSQL is ready."

up-admin: ## Start PostgreSQL + pgAdmin on http://localhost:8080
	docker compose --profile admin up -d

down: ## Stop containers (data preserved)
	docker compose down

clean: ## Stop containers AND wipe all data (irreversible!)
	docker compose down -v
	@echo "All data volumes deleted."

logs: ## Tail PostgreSQL logs
	docker compose logs -f postgres

psql: ## Open a psql shell inside the container
	docker compose exec postgres psql -U meter_user -d meter_to_cash

# ── Python environment ────────────────────────────────────────────────────────
install: ## Install Python dependencies into a venv
	python3 -m venv .venv
	.venv/bin/pip install -q --upgrade pip
	.venv/bin/pip install -q -r scripts/requirements.txt
	@echo "Dependencies installed. Activate with: source .venv/bin/activate"

# ── Seeding ───────────────────────────────────────────────────────────────────
check-env:
	@test -f .env || (echo "ERROR: .env not found. Copy .env.example first: cp .env.example .env" && exit 1)

seed: check-env up ## Seed with default scale (10k customers, 100k readings)
	@echo "Starting seed generation (default scale)..."
	python3 scripts/seed_generator.py

seed-large: check-env up ## Seed at full scale (100k customers, 1M readings) – takes ~10 min
	@NUM_CUSTOMERS=100000 NUM_METER_READINGS=1000000 python3 scripts/seed_generator.py

# ── CDC changes ───────────────────────────────────────────────────────────────
cdc: check-env ## Generate CDC test changes (INSERT/UPDATE/DELETE mix)
	@echo "Generating CDC changes..."
	python3 scripts/cdc_change_generator.py

# ── Tests ─────────────────────────────────────────────────────────────────────
test: check-env ## Run referential integrity + quality tests
	python3 -m pytest tests/ -v --tb=short

test-ci: check-env ## Run tests with JUnit XML output (for CI)
	python3 -m pytest tests/ -v --tb=short --junitxml=test-results.xml
