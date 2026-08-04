.PHONY: install lint format typecheck check test test-cov clean pre-commit

install:
	poetry install --with=dev

lint:
	poetry run ruff check alembic_migration_linter/ tests/
	poetry run ruff format --check alembic_migration_linter/ tests/

format:
	poetry run ruff check --fix alembic_migration_linter/ tests/
	poetry run ruff format alembic_migration_linter/ tests/

typecheck:
	poetry run mypy alembic_migration_linter/

check: lint typecheck

test:
	poetry run pytest tests/

test-cov:
	poetry run pytest tests/ --cov=alembic_migration_linter --cov-report=term-missing --cov-fail-under=90

pre-commit:
	poetry run pre-commit run --all-files
