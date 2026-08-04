# Alembic Migration Linter

Detect backward incompatible database migrations for Alembic projects.

Based on the SQL analysis layer from [django-migration-linter](https://github.com/3YOURMIND/django-migration-linter), adapted for Alembic's offline SQL rendering.

## Installation

```bash
pip install alembic-migration-linter
```

Requires Python 3.11+ and an existing Alembic project with `alembic.ini`.

## Quick Start

```bash
# Lint all migrations against PostgreSQL
alembic-lint --dialect postgresql

# Lint only changes since a revision (use a literal revision ID)
alembic-lint --since-revision abc1234567

# Exclude specific checks
alembic-lint --exclude-test ALTER_COLUMN

# Treat warnings as errors (CI-friendly)
alembic-lint --warnings-as-errors
```

## Basic Usage

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

### Expand/Contract (DROP_TABLE, DROP_COLUMN, RENAME_TABLE, RENAME_COLUMN, ALTER_COLUMN)

The pattern is expand/contract: first expand the schema without breaking old code, deploy, then contract in a follow-up migration. The expand migration passes the linter; the contract migration will still be flagged because the linter cannot know whether old code has been retired. Use `--ignore-revision` or `--since-revision` to scope linting to the expand phase.

#### DROP_TABLE

Create the replacement table alongside the old one. After deploying code that uses the new table, drop the old table in a separate migration:

```python
# Migration 1: create replacement table
def upgrade():
    op.create_table(
        "users_v2",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
    )

# Migration 2 (after code deploy): drop old table — still flagged by linter
def upgrade():
    op.drop_table("users")
```

#### DROP_COLUMN

Stop writing to the column in code first. In a later migration, drop it after old code is fully retired:

```python
# Migration 1: add replacement column, backfill data
def upgrade():
    op.add_column("users", sa.Column("full_name", sa.String(255)))
    op.execute("UPDATE users SET full_name = name")

# Migration 2 (after code deploy): drop old column — still flagged by linter
def upgrade():
    op.drop_column("users", "name")
```

#### RENAME_TABLE

Create the new table, copy data, switch code, then drop the old table:

```python
# Migration 1: create new table alongside old
def upgrade():
    op.create_table(
        "products",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("sku", sa.String(50), nullable=False),
    )
    op.execute("INSERT INTO products (id, sku) SELECT id, sku FROM items")

# Migration 2 (after code deploy): drop old table — still flagged by linter
def upgrade():
    op.drop_table("items")
```

#### RENAME_COLUMN

Add a new column with the desired name, backfill, switch code, then drop the old column:

```python
# Migration 1: add new column and backfill
def upgrade():
    op.add_column("users", sa.Column("name", sa.String(255)))
    op.execute("UPDATE users SET name = title")

# Migration 2 (after code deploy): drop old column — still flagged by linter
def upgrade():
    op.drop_column("users", "title")
```

#### ALTER_COLUMN

Add a new column with the desired type, backfill, switch code, then drop the old column:

```python
# Migration 1: add new column with target type
def upgrade():
    op.add_column("products", sa.Column("description_long", sa.Text()))
    op.execute("UPDATE products SET description_long = description")

# Migration 2 (after code deploy): drop old column — still flagged by linter
def upgrade():
    op.drop_column("products", "description")
```

### NOT_NULL

Two-step approach — add nullable first, then backfill and add NOT NULL with a default:

```python
# Migration 1: add nullable column
def upgrade():
    op.add_column("users", sa.Column("status", sa.String(50), nullable=True))

# Migration 2: backfill and constrain
def upgrade():
    op.execute("UPDATE users SET status = 'active' WHERE status IS NULL")
    op.alter_column("users", "status", nullable=False, server_default="active")
```

### ADD_UNIQUE

Adding a unique constraint to an existing table is always flagged because the linter cannot verify that duplicates have been eliminated. The only safe alternative is to add the constraint when creating a new table (no existing rows to violate it):

```python
def upgrade():
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False),
    )
    op.create_unique_constraint("uq_users_email", "users", ["email"])
```

### CREATE_INDEX (PostgreSQL)

Use `CONCURRENTLY` to avoid locking the table during creation. `CONCURRENTLY` cannot run inside a transaction, so wrap it in an autocommit block:

```python
def upgrade():
    with op.get_context().autocommit_block():
        op.execute("CREATE INDEX CONCURRENTLY idx_users_email ON users (email)")
```

### CREATE_INDEX_EXCLUSIVE (PostgreSQL)

Don't combine `ALTER TABLE` and `CREATE INDEX` in the same migration. Split into separate migrations:

```python
# Migration 1: alter table
def upgrade():
    op.add_column("products", sa.Column("category", sa.String(100)))

# Migration 2: create index
def upgrade():
    with op.get_context().autocommit_block():
        op.execute("CREATE INDEX CONCURRENTLY idx_products_category ON products (category)")
```

### DROP_INDEX (PostgreSQL)

Use `CONCURRENTLY` to avoid locking the table during drop:

```python
def upgrade():
    with op.get_context().autocommit_block():
        op.execute("DROP INDEX CONCURRENTLY idx_users_email")
```

### REINDEX (PostgreSQL)

There is no safe alternative — any `REINDEX` statement triggers a warning because the linter cannot distinguish `REINDEX TABLE` from `REINDEX INDEX CONCURRENTLY`. Use `--exclude-test REINDEX` if you use concurrent reindex.

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

## License

New code: **MIT**

SQL analyser rules are from [django-migration-linter](https://github.com/3YOURMIND/django-migration-linter) (Apache-2.0), imported as a dependency — not copied.
