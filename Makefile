.PHONY: install lint format typecheck test audit ci db-up db-down migrate seed

install:
	pip install -e ".[dev]"

lint:
	ruff check .
	ruff format --check .

format:
	ruff format .
	ruff check --fix .

typecheck:
	mypy

test:
	pytest

audit:
	pip-audit

ci: lint typecheck test

db-up:
	docker compose -f infra/docker-compose.yml up -d

db-down:
	docker compose -f infra/docker-compose.yml down

migrate:
	python scripts/migrate.py

seed:
	python scripts/seed_reference_data.py
