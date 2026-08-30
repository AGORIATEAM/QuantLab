.PHONY: install lint format typecheck test audit ci db-up db-down migrate seed backup

# Physical copy outside the Docker volume (the volume lives on the internal
# disk since the USB bind-mount incident). Override: make backup BACKUP_DIR=...
BACKUP_DIR ?= /Volumes/Stockage/QuantLab-backups

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

backup:
	mkdir -p "$(BACKUP_DIR)"
	docker compose -f infra/docker-compose.yml exec -T postgres \
		pg_dump -U quantlab -d quantlab_dev --format=custom \
		> "$(BACKUP_DIR)/quantlab_dev_$$(date -u +%Y%m%dT%H%M%SZ).dump"
	@ls -lh "$(BACKUP_DIR)" | tail -3
