.PHONY: help up down build logs api web airflow db-migrate db-upgrade db-downgrade diagrams backfill test lint

help:
	@echo "NMDPRA Data Platform - Common commands"
	@echo "  make up          - Start all services (postgres, airflow, api, web)"
	@echo "  make down        - Stop all services"
	@echo "  make build       - Build Docker images"
	@echo "  make logs        - Tail docker-compose logs"
	@echo "  make api         - Run API locally (uvicorn)"
	@echo "  make web         - Run Next.js locally"
	@echo "  make airflow     - Start only Airflow (postgres + webserver + scheduler)"
	@echo "  make db-migrate  - Create new Alembic migration"
	@echo "  make db-upgrade  - Apply migrations"
	@echo "  make db-downgrade - Rollback one migration"
	@echo "  make diagrams    - Generate Mermaid diagrams (requires DB)"
	@echo "  make backfill    - Run backfill (e.g. make backfill SOURCE=oilgasdata FROM=2023-01 TO=2026-12)"
	@echo "  make test        - Run pytest"
	@echo "  make lint        - Run ruff + mypy"

up:
	docker compose up -d

down:
	docker compose down

build:
	docker compose build

logs:
	docker compose logs -f

api:
	cd apps/api && pip install -e ".[dev]" && uvicorn main:app --reload --port 8000

web:
	cd apps/web && npm install && npm run dev

airflow:
	docker compose up -d postgres airflow-webserver airflow-scheduler

db-migrate:
	cd apps/api && alembic revision --autogenerate -m "$(msg)"

db-upgrade:
	cd apps/api && alembic upgrade head

db-downgrade:
	cd apps/api && alembic downgrade -1

diagrams:
	python scripts/generate_diagrams.py

backfill:
	python scripts/backfill.py --source $(SOURCE) --from $(FROM) --to $(TO)

test:
	pytest tests/ -v

lint:
	ruff check . && mypy apps/api
