# User Guide

## Installation

```bash
pip install alembic-migration-linter
```

Requires Python 3.11+ and an existing Alembic project with `alembic.ini`.

## Basic Usage

Lint all migrations against PostgreSQL:

```bash
alembic-lint --dialect postgresql
```

Lint only migrations since a specific revision (the base revision itself is not re-linted):

```bash
alembic-lint --since-revision abc123
```

Lint a single revision:

```bash
alembic-lint --revision abc123
```

Use a non-default config file:

```bash
alembic-lint --config path/to/alembic.ini
```

Exclude noisy checks:

```bash
alembic-lint --exclude-test ALTER_COLUMN --exclude-test ADD_UNIQUE
```

Treat warnings as errors (recommended for CI):

```bash
alembic-lint --warnings-as-errors
```

**Note:** `--revision` and `--since-revision` require a literal revision ID (the value of the `revision` variable in the migration file). Symbolic references like `head` or `head~5` are not supported.

## Configuration

### alembic.ini

Add a `[linters]` section to your `alembic.ini` to set defaults:

```ini
[alembic]
script_location = migrations

[linters]
dialect = postgresql
exclude_tests = ALTER_COLUMN
warnings_as_errors = true
```

CLI flags override config file values. For example, `--dialect mysql` on the command line will override `dialect = postgresql` in the config file.

### Supported Config Keys

| Key                  | Type                 | Default      | Description                |
|:---------------------|:---------------------|:-------------|:---------------------------|
| `dialect`            | string               | `postgresql` | Target database dialect    |
| `exclude_tests`      | comma-separated list | *(none)*     | Test codes to skip         |
| `warnings_as_errors` | `true` / `false`     | `false`      | Promote warnings to errors |

## Output Format

Each migration produces one line:

```
(0001_create_users)... OK
(0002_add_not_null)... ERR
    NOT_NULL
(0003_create_index)... WARNING
    CREATE_INDEX
(0004_data_fix)... IGNORE
```

A summary follows:

```
*** Summary ***
Valid migrations: 1/4
Erroneous migrations: 1/4
Migrations with warnings: 1/4
Ignored migrations: 1/4
```

Exit code is `0` when no errors are found, `1` when errors exist.

## Incompatibility Rules

### Errors (all dialects)

| Code            | Trigger                                   | Why It Breaks Zero-Downtime        |
|:----------------|:------------------------------------------|:-----------------------------------|
| `DROP_TABLE`    | `DROP TABLE`                              | Old app code references the table  |
| `DROP_COLUMN`   | `DROP COLUMN`                             | Old app code reads the column      |
| `RENAME_TABLE`  | `ALTER TABLE ... RENAME TO`               | Old app code references old name   |
| `RENAME_COLUMN` | `ALTER TABLE ... RENAME COLUMN`           | Old app code references old name   |
| `ALTER_COLUMN`  | `ALTER COLUMN ... TYPE`                   | Type change may break old queries  |
| `NOT_NULL`      | `ADD COLUMN ... NOT NULL` without default | Old app inserts without the column |
| `ADD_UNIQUE`    | `ADD CONSTRAINT ... UNIQUE`               | Old app may have duplicate data    |

### Warnings (PostgreSQL)

| Code                     | Trigger                                            | Impact                      |
|:-------------------------|:---------------------------------------------------|:----------------------------|
| `CREATE_INDEX`           | `CREATE INDEX` without `CONCURRENTLY`              | Locks table during creation |
| `CREATE_INDEX_EXCLUSIVE` | `ALTER TABLE` + `CREATE INDEX` in same transaction | Prolongs exclusive lock     |
| `DROP_INDEX`             | `DROP INDEX` without `CONCURRENTLY`                | Locks table during drop     |
| `REINDEX`                | `REINDEX`                                          | Locks table during reindex  |

### MySQL Notes

MySQL adds no warning-level rules. It refines the base `ALTER_COLUMN` **error** to also catch MySQL's `ALTER TABLE ... MODIFY` syntax, which rebuilds the table and blocks writes.

### SQLite Notes

SQLite has limited `ALTER TABLE` support, so Alembic uses `batch_alter_table` which recreates tables. This triggers additional checks:

| Code           | Behaviour                                                        |
|:---------------|:-----------------------------------------------------------------|
| `RENAME_TABLE` | Internal renames from `batch_alter_table` are excluded           |
| `DROP_TABLE`   | Transaction-aware — detects drop + recreate patterns             |
| `NOT_NULL`     | Rename-aware — accounts for table recreation during batch alter  |

These are modifications to the base rules, not separate codes. If `batch_alter_table` produces false positives, use `--exclude-test` to suppress them.

## Safe Migration Patterns

### Adding a NOT NULL Column

Two-step approach — add nullable first, then add default and set NOT NULL:

```python
# Migration 1: add nullable column
def upgrade():
    op.add_column("users", sa.Column("status", sa.String(50), nullable=True))

# Migration 2: backfill and constrain
def upgrade():
    op.execute("UPDATE users SET status = 'active' WHERE status IS NULL")
    op.alter_column("users", "status", nullable=False, server_default="active")
```

### Adding a Unique Constraint

Ensure no duplicates exist before adding the constraint:

```python
# Migration 1: add index (non-unique) and backfill
def upgrade():
    op.create_index("idx_users_email", "users", ["email"])
    # Run a data migration to deduplicate

# Migration 2: add unique constraint
def upgrade():
    op.create_unique_constraint("uq_users_email", "users", ["email"])
```

### Creating an Index (PostgreSQL)

Use raw SQL with `CONCURRENTLY`:

```python
def upgrade():
    op.execute("CREATE INDEX CONCURRENTLY idx_users_email ON users (email)")
```

## CI Integration

### GitHub Actions

```yaml
name: Migration Lint

on:
  pull_request:
    branches: [main]

jobs:
  lint-migrations:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install linter
        run: pip install alembic-migration-linter

      - name: Lint migrations
        run: alembic-lint --dialect postgresql --warnings-as-errors --no-cache
```

### GitLab CI

```yaml
lint-migrations:
  stage: test
  image: python:3.11-slim
  script:
    - pip install alembic-migration-linter
    - alembic-lint --dialect postgresql --warnings-as-errors --no-cache
```

### CI Recommendations

1. **Use `--no-cache`** — CI environments are ephemeral; caching adds no value and can mask issues
2. **Use `--warnings-as-errors`** — catch locking issues before they reach production
3. **Use `--quiet`** — suppress OK lines for cleaner logs when you only care about failures
4. **Lint against all target dialects** — if you support PostgreSQL and MySQL, run the linter against both

Multi-dialect example:

```yaml
strategy:
  matrix:
    dialect: [postgresql, mysql]

- name: Lint migrations
  run: alembic-lint --dialect ${{ matrix.dialect }} --warnings-as-errors --no-cache
```

## Skipping Migrations

Some migrations are intentionally incompatible (e.g., initial schema setup, one-time data fixes). Skip them by matching the revision ID or filename.

### CLI

```bash
# Skip specific revisions by ID
alembic-lint --ignore-revision initial_schema --ignore-revision data_fix_001

# Skip any migration whose revision ID or filename contains a substring
alembic-lint --ignore-revision-contains data_fix
```

### Programmatic

```python
from alembic_migration_linter import AlembicMigrationLinter

linter = AlembicMigrationLinter(
    config_path="alembic.ini",
    ignore_revisions=["initial_schema"],
    ignore_revision_contains="data_fix",
)
```

Both `--ignore-revision` and `--ignore-revision-contains` can be specified multiple times. The `--ignore-revision-contains` flag matches against both the revision ID and the filename. A migration file named `0001_skip_this_migration.py` with revision `"skip_this_migration"` will be skipped by either `--ignore-revision-contains skip` or `--ignore-revision-contains skip_this`.

## Local Development Setup

### Prerequisites

- Python 3.11+
- A virtual environment

### Install from Source

This project uses [Poetry](https://python-poetry.org/) for dependency management.

```bash
cd source
poetry install --with dev
```

### Run Checks

```bash
# All checks: lint, format, typecheck
make check

# Run tests
make test

# Run tests with coverage report
make test-cov

# Auto-format code
make format
```

### Pre-commit Hooks

```bash
# Install hooks
pre-commit install

# Run against all files
make pre-commit
```

The pre-commit config runs `pyupgrade`, `ruff`, `ruff-format`, and `mypy` on every commit.

## Troubleshooting

### "Revision not found"

The revision ID must match the `revision` variable in the migration file exactly. Check with:

```bash
grep "^revision" migrations/versions/*.py
```

### False positives on batch_alter_table

SQLite uses `batch_alter_table` which generates temporary table SQL. The analyser may flag internal operations. Exclude with `--exclude-test` if needed.

### Raw SQL not detected

`op.execute()` produces SQL that is captured and analysed. If a raw SQL statement isn't being flagged, verify the SQL matches the analyser's regex patterns (check the [incompatibility rules](#incompatibility-rules) table).

### Cache causing stale results

Use `--no-cache` to bypass the file cache, or clear it manually:

```bash
rm -rf ~/.cache/alembic-migration-linter/
```
