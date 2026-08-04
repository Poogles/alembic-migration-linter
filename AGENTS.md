# AGENTS.md

## Quick Start

All development commands must run from the `source/` directory.

```bash
cd source
make install      # poetry install --with=dev
make check        # lint + format check + typecheck (must pass before merging)
make format       # auto-fix lint and formatting
make test         # run all tests
make test-cov     # tests with coverage report
```

## Project Structure

- `source/alembic_migration_linter/` — the package (8 modules: cli, linter, loader, generator, cache, config)
- `source/tests/` — unit tests + functional tests with scenario directories under `test_migrations/`
- `source/README.md` — user-facing docs (installation, configuration, CI, safe migration patterns)
- `docs/` — ARCHITECTURE.md (data flow, module reference)

## Toolchain

| Tool | Purpose | Scope |
|------|---------|-------|
| ruff | lint + format | `alembic_migration_linter/`, `tests/` |
| mypy | type checking (strict) | `alembic_migration_linter/` only — tests are excluded |
| pyupgrade | syntax upgrades | py311+ |

Python >= 3.11. Ruff targets `py311`.

## CI vs Local

CI installs via `pip install -e ".[test]"` (not poetry). Locally, use `make install` (poetry). Both work; the Makefile targets are the source of truth for local development.

## Testing

Tests are scenario-driven: each directory under `source/tests/test_migrations/` is a self-contained migration scenario with its own `alembic.ini`. Fixtures in `conftest.py` copy scenarios to temp dirs and build linters against them.

- `tests/unit/` — module-level tests for loader, generator, linter
- `tests/functional/` — integration tests against real migration scenarios
- Parametrized fixtures (`error_scenario_name`, `safe_scenario_name`, `warning_scenario_name`) iterate over scenario dictionaries in `conftest.py`

To add a new test scenario: create a directory under `test_migrations/` with an `alembic.ini` and migration files, then register it in the appropriate dictionary in `conftest.py`.

## Nix Environment

A `shell.nix` at the repo root provides a Nix development environment (python314, poetry, postgresql, pre-commit). Activated via direnv (`.envrc` present). Not required — poetry alone suffices.

## Licensing

Original code is MIT (`source/LICENSE`). The SQL analyser rules come from `django-migration-linter` (Apache 2.0) imported as a dependency — never copied or vendored.
