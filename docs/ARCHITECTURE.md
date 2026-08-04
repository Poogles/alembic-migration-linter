# Architecture

## Overview

`alembic-migration-linter` detects backward-incompatible database migrations in Alembic projects. It works by rendering migration operations into raw SQL, then analysing that SQL with regex-based rules to flag operations that would break zero-downtime deployments.

The tool is composed of two layers:

1. **SQL Generation** (this project) — renders Alembic migration scripts into dialect-specific SQL
2. **SQL Analysis** ([django-migration-linter](https://github.com/3YOURMIND/django-migration-linter)) — inspects SQL statements for backward-incompatible patterns

The SQL analysis layer is imported as a dependency, not copied. This project only provides the Alembic-specific SQL generation and CLI.

## Data Flow

```
alembic-lint --dialect postgresql
        │
        ▼
┌──────────────────────────────────────────────────────────────┐
│                        CLI (cli.py)                          │
│                                                              │
│  • Parse CLI flags and alembic.ini [linters] section         │
│  • Construct AlembicMigrationLinter with merged config       │
│  • Invoke lint_all() or lint_migration()                     │
│  • Format and print results, exit with code 0 or 1           │
└────────────────────────────┬─────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────────┐
│              AlembicMigrationLinter (linter.py)              │
│                                                              │
│  • Orchestrates loader → generator → analyser pipeline       │
│  • Manages skip rules (ignore_revisions, ignore_revision_contains)    │
│  • Manages MD5-based file cache (cache.py)                   │
│  • Filters excluded test codes from results                  │
└────┬───────────────────────────┬─────────────────────────────┘
     │                           │
     ▼                           ▼
┌──────────────────┐  ┌────────────────────────────────────────┐
│ AlembicMigration │  │       AlembicSqlGenerator              │
│ Loader           │  │                                        │
│ (loader.py)      │  │  • EnvironmentContext(as_sql=True)     │
│                  │  │  • MigrationContext + Operations       │
│ • ScriptDirectory│  │  • Dialect-specific URL construction   │
│   .walk_revisions│  │  • Splits output on ";" into statements│
│ • Imports .py    │  │                                        │
│   modules        │  │  Output: list[str] of SQL statements   │
│ • Extracts       │  └────────────────┬───────────────────────┘
│   revision,      │                   │
│   down_revision, │                   │
│   depends_on     │                   │
│                  │                   │
│ Output:          │                   │
│ list[Alembic     │                   │
│  Migration]      │                   │
└──────────────────┘                   │
                                       ▼
┌──────────────────────────────────────────────────────────────┐
│           SQL Analyser (django-migration-linter)             │
│                                                              │
│  Imported from django_migration_linter.sql_analyser:         │
│  • analyse_sql_statements() — two-pass analysis              │
│  • get_sql_analyser_class() — dialect-specific analyser      │
│                                                              │
│  Pass 1: Per-statement checks (ONE_LINER mode)               │
│    DROP_TABLE, DROP_COLUMN, RENAME_TABLE, RENAME_COLUMN,     │
│    ALTER_COLUMN, DROP_INDEX, REINDEX                         │
│                                                              │
│  Pass 2: Cross-statement checks (TRANSACTION mode)           │
│    NOT_NULL, ADD_UNIQUE, CREATE_INDEX,                       │
│    CREATE_INDEX_EXCLUSIVE                                    │
│                                                              │
│  Output: (errors, ignored, warnings) — list[Issue] each      │
└──────────────────────────────────────────────────────────────┘
```

## Module Reference

### `cli.py` — Command-Line Interface

Built with Click. Accepts flags for dialect, revision filtering, test exclusion, and output control. Merges CLI options with `[linters]` section from `alembic.ini` — CLI flags take precedence.

Key behaviour:
- `--revision` lints a single migration; `--since-revision` lints all migrations after a given revision
- `--warnings-as-errors` promotes warnings to errors (affects exit code)
- `--quiet` suppresses "OK" lines for cleaner CI output
- Exit code 0 = no errors, 1 = errors found or revision not found

### `linter.py` — Orchestration

`AlembicMigrationLinter` is the central class. It:

1. Creates an `AlembicMigrationLoader` and `AlembicSqlGenerator` for the given config and dialect
2. Resolves the appropriate analyser class from `django-migration-linter` via `get_sql_analyser_class(dialect)`
3. For each migration: checks skip rules, checks cache, generates SQL, runs analysis, caches result
4. Returns `LintResult` objects containing errors, warnings, and ignored issues per migration

### `loader.py` — Migration Discovery

`AlembicMigrationLoader` uses Alembic's `ScriptDirectory.from_config()` to discover migration scripts. It walks the revision graph via `walk_revisions(base="base", head="heads")`, which handles branching and multi-head scenarios.

Each script module is imported and its `upgrade`/`downgrade` functions are extracted. The `AlembicMigration` dataclass holds the revision metadata and callable functions.

### `generator.py` — SQL Rendering

`AlembicSqlGenerator` renders migration operations into raw SQL using Alembic's offline mode:

1. Constructs a fake connection URL with the target dialect (e.g., `postgresql://user:pass@localhost/db`)
2. Creates an `EnvironmentContext` with `as_sql=True` — this captures SQL instead of executing it
3. Calls the migration's `upgrade()` function within an `Operations.context(mc)` — the `op` object writes to the output buffer
4. Splits the output on `;` to produce individual SQL statements

No live database connection is required.

### `cache.py` — File Cache

Pickle-based cache stored in `~/.cache/alembic-migration-linter/`. Cache key is the MD5 hash of the migration file contents concatenated with the dialect name, so each dialect gets its own cache entry. Bypassed with `--no-cache` flag.

### `config.py` — alembic.ini Parsing

Reads the `[linters]` section from `alembic.ini`. Supported keys:

| Key                  | Type            | Description                                     |
|:---------------------|:----------------|:------------------------------------------------|
| `dialect`            | string          | Target database dialect (default: `postgresql`) |
| `exclude_tests`      | comma-separated | Test codes to exclude                           |
| `warnings_as_errors` | `true`/`false`  | Promote warnings to errors                      |

## Relationship with django-migration-linter

django-migration-linter was built for Django migrations. Its architecture has two layers:

1. **SQL Generation** — Django's `sqlmigrate` command renders migrations to SQL
2. **SQL Analysis** — Regex-based rules inspect SQL for backward-incompatible patterns

The SQL analysis layer is database-aware but framework-agnostic — it operates on SQL syntax, not Python code. This project reuses that layer by importing it directly:

```python
from django_migration_linter.sql_analyser import (
    analyse_sql_statements,
    get_sql_analyser_class,
)
```

The only component this project replaces is the SQL generation layer: Django's `sqlmigrate` becomes Alembic's offline `EnvironmentContext`. The analyser receives the same `list[str]` of SQL statements regardless of source.

This means:
- All incompatibility rules (11 codes: 7 base rules shared by every dialect, plus 4 PostgreSQL-specific rules; MySQL and SQLite refine existing codes rather than adding new ones) are inherited from django-migration-linter
- Rule updates in django-migration-linter are automatically available via dependency updates
- No rule duplication or maintenance burden

## Licensing

This project uses a dual-license model:

| Component | License | Location |
|-----------|---------|----------|
| Original code (CLI, loader, generator, linter, cache, config) | MIT | `source/LICENSE` |
| SQL analyser rules (imported at runtime) | Apache 2.0 | `django-migration-linter` package |

### Why Import Rather Copy?

The SQL analyser from django-migration-linter is imported as a runtime dependency, never vendored or copied. This was a deliberate choice for three reasons:

**1. Licensing compliance.** django-migration-linter is licensed under Apache 2.0. Apache 2.0 requires that modified code be clearly attributed and that the license text be included with any distribution. By importing the library as a dependency rather than copying its source, we avoid the obligation to carry the Apache 2.0 license text in our own repository while remaining fully compliant — the dependency's own LICENSE file is included in the installed package metadata. Our own code remains under MIT.

**2. Zero rule maintenance.** The analyser contains 11 incompatibility rules across four dialects, each with carefully tuned regex patterns. Copying these rules would mean maintaining them independently — tracking bug fixes, new rules, and dialect-specific edge cases upstream. Importing the library means every improvement in django-migration-linter is available to us via a version bump.

**3. Framework-agnostic boundary.** The analyser operates on SQL strings, not framework-specific objects. This clean separation — SQL generation is framework-specific, SQL analysis is framework-agnostic — is what makes the port possible. If the analyser had been tightly coupled to Django's migration objects, this architecture would not work.

## Architectural Decisions

### Why Offline SQL Rendering?

Alembic supports two modes for running migrations: online (against a live database) and offline (rendering SQL to stdout). We use offline mode exclusively:

- **No database required.** The linter runs without a live PostgreSQL, MySQL, or SQLite instance. This is essential for CI environments where provisioning databases adds complexity and cost.
- **Deterministic output.** The same migration script always produces the same SQL for a given dialect. Online execution can produce different results depending on the current database state.
- **Safety.** The linter never executes migration code against a real database. A buggy migration that drops a production table won't cause damage during linting.
- **Speed.** Rendering SQL is orders of magnitude faster than running migrations against a real database.

The trade-off is that some Alembic constructs (e.g., `op.execute()` with server-side SQL that depends on runtime state, custom `env.py` hooks) may not render cleanly in offline mode. These are edge cases that can be handled with skip rules.

### Why a Two-Layer Architecture?

The separation between SQL generation and SQL analysis is not incidental, it's the core insight that makes this project viable:

- **SQL Generation** is the hard part that's framework-specific. Alembic's `EnvironmentContext` API, migration module loading, and revision graph traversal are all unique to Alembic.
- **SQL Analysis** is the hard part that's framework-agnostic. The regex patterns for detecting `DROP TABLE`, `NOT NULL` without defaults, and so on are the same regardless of whether the SQL came from Django, Alembic, or a raw SQL file.

By keeping these layers separate, we only need to write and maintain the Alembic-specific layer. The analysis layer is battle-tested by django-migration-linter's user base.

### Why Click for the CLI?

Click was chosen over argparse for three reasons:

1. **Composable commands.** Click's decorator-based API makes it straightforward to add subcommands in the future (e.g., `alembic-lint check`, `alembic-lint diff`).
2. **Type coercion.** Click handles type conversion (strings to booleans, paths to `Path` objects) automatically, reducing boilerplate.
3. **Convention.** Click is the de facto standard for Python CLI tools in the data and DevOps space, making the interface familiar to users of tools like `pip`, `poetry`, and `alembic` itself.

### Why MD5-Based File Caching?

The cache uses MD5 hashes of migration file contents rather than file modification times:

- **Content-addressed.** If a migration file is edited, the hash changes and the cache is invalidated automatically. With mtime-based caching, clock skew or filesystem quirks can cause stale results.
- **Portable.** The cache works across environments — a developer's machine and a CI runner will produce the same hash for the same file content and dialect.
- **Simple.** No database, no lock files, no cache warming logic. Each cache entry is a standalone pickle file keyed by hash.

The trade-off is that the cache doesn't account for changes in the analyser rules or the Alembic version. This is acceptable because rule changes are rare and the `--no-cache` flag is available for CI environments where determinism matters more than speed.

## Dialect Support

The linter renders and analyses SQL per-dialect. The same migration script may produce different SQL for different databases, triggering different rules:

| Dialect    | Flag                   | Extra Rules                                                                                             |
|:-----------|:-----------------------|:--------------------------------------------------------------------------------------------------------|
| PostgreSQL | `--dialect postgresql` | `CREATE_INDEX`, `CREATE_INDEX_EXCLUSIVE`, `DROP_INDEX`, `REINDEX`                                       |
| MySQL      | `--dialect mysql`      | `ALTER_COLUMN` also matches `MODIFY` (refinement, not new code)                                         |
| SQLite     | `--dialect sqlite`     | `RENAME_TABLE` (excludes internal renames), `DROP_TABLE` (transaction-aware), `NOT_NULL` (rename-aware) |

Base rules (`DROP_TABLE`, `DROP_COLUMN`, `RENAME_TABLE`, `RENAME_COLUMN`, `ALTER_COLUMN`, `ADD_UNIQUE`, `NOT_NULL`) apply to all dialects.
