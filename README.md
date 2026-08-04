# Alembic Migration Linter

Detect backward incompatible database migrations for Alembic projects.

Based on the SQL analysis layer from [django-migration-linter](https://github.com/3YOURMIND/django-migration-linter), adapted for Alembic's offline SQL rendering.

## Quick Start

```bash
# Install
pip install alembic-migration-linter

# Lint all migrations against PostgreSQL
alembic-lint --dialect postgresql

# Lint only changes since a revision (use a literal revision ID)
alembic-lint --since-revision abc1234567

# Exclude specific checks
alembic-lint --exclude-test ALTER_COLUMN

# Treat warnings as errors (CI-friendly)
alembic-lint --warnings-as-errors
```

## Development

All commands should be run from the `source/` directory. This project uses [Poetry](https://python-poetry.org/) for dependency management.

```bash
cd source

# Install with test dependencies
make install

# Run all checks (lint + format + typecheck)
make check

# Auto-format code
make format

# Run tests
make test

# Run tests with coverage
make test-cov

# Run pre-commit hooks on all files
make pre-commit
```

Alternatively, run Poetry commands directly:

```bash
poetry install --with dev
poetry run pytest
poetry run ruff check alembic_migration_linter/ tests/
poetry run mypy alembic_migration_linter/
```

## Linting

This project uses:
- **ruff** — linting and formatting
- **mypy** — type checking (strict mode)
- **pyupgrade** — automatic syntax upgrades (py311+)

Every phase of development must pass `make check` before merging.

## Documentation

- [Architecture](docs/ARCHITECTURE.md) — data flow, module reference, design decisions, licensing
- [User Guide](source/README.md) — installation, configuration, CI integration, safe migration patterns

## License

New code: **MIT** — see [LICENSE](source/LICENSE)

SQL analyser rules are from [django-migration-linter](https://github.com/3YOURMIND/django-migration-linter) (Apache-2.0), imported as a dependency — not copied. See [Architecture → Licensing](docs/ARCHITECTURE.md#licensing) for details.
