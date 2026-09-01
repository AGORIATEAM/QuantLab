.PHONY: install lint format typecheck test audit ci db-up db-down migrate seed backup restore-check

# Physical copy outside the Docker volume (the volume lives on the internal
# disk since the USB bind-mount incident). Override: make backup BACKUP_DIR=...
BACKUP_DIR ?= /Volumes/Stockage/QuantLab-backups
# A real data dump is hundreds of MB; anything under this is a failed dump
# (shell redirection creates the file even when pg_dump dies immediately).
MIN_BACKUP_BYTES ?= 1048576

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

# Write to .tmp, promote to .dump only after pg_dump exits 0 AND the file has
# a plausible size — never leave a silent 0-byte "backup" behind.
backup:
	@mkdir -p "$(BACKUP_DIR)"
	@f="$(BACKUP_DIR)/quantlab_dev_$$(date -u +%Y%m%dT%H%M%SZ).dump"; \
	if ! docker compose -f infra/docker-compose.yml exec -T postgres \
		pg_dump -U quantlab -d quantlab_dev --format=custom > "$$f.tmp"; then \
		rm -f "$$f.tmp"; \
		echo "backup FAILED: pg_dump exited non-zero, no file kept" >&2; exit 1; \
	fi; \
	size=$$(stat -f%z "$$f.tmp" 2>/dev/null || stat -c%s "$$f.tmp"); \
	if [ "$$size" -lt "$(MIN_BACKUP_BYTES)" ]; then \
		rm -f "$$f.tmp"; \
		echo "backup FAILED: dump is $$size bytes (< $(MIN_BACKUP_BYTES)), no file kept" >&2; exit 1; \
	fi; \
	mv "$$f.tmp" "$$f"; \
	echo "backup OK: $$f ($$size bytes)"

# Validate a dump with pg_restore --list. DUMP=... to pick one; defaults to
# the newest .dump in BACKUP_DIR.
restore-check:
	@dump="$(DUMP)"; \
	if [ -z "$$dump" ]; then dump=$$(ls -t "$(BACKUP_DIR)"/*.dump 2>/dev/null | head -1); fi; \
	if [ -z "$$dump" ]; then \
		echo "restore-check FAILED: no .dump in $(BACKUP_DIR) (or pass DUMP=/path/to/file.dump)" >&2; exit 1; \
	fi; \
	if docker compose -f infra/docker-compose.yml exec -T postgres \
		pg_restore --list < "$$dump" > /dev/null; then \
		echo "restore-check OK: $$dump is a readable pg_dump archive"; \
	else \
		echo "restore-check FAILED: $$dump is not a readable pg_dump archive" >&2; exit 1; \
	fi
