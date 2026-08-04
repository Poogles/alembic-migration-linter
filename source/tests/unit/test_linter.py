from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from alembic_migration_linter.linter import AlembicMigrationLinter, LintResult
from tests.conftest import (
    _create_migration,
    _create_migration_with_content,
    _get_versions_dir,
)

DROP_COLUMN_MIGRATION = """
from alembic import op

def upgrade():
    op.drop_column("users", "email")

def downgrade():
    pass
"""

SAFE_ADD_COLUMN_MIGRATION = """
from alembic import op
import sqlalchemy as sa

def upgrade():
    op.add_column("users", sa.Column("age", sa.Integer()))

def downgrade():
    pass
"""


def test_lint_drop_column(alembic_config: Path) -> None:
    versions_dir = _get_versions_dir(alembic_config)
    _create_migration_with_content(versions_dir, "0001", DROP_COLUMN_MIGRATION)

    linter = AlembicMigrationLinter(
        alembic_config,
        dialect="postgresql",
        no_cache=True,
    )
    results = linter.lint_all()

    assert len(results) == 1
    result: LintResult = results[0]
    assert result.migration_revision == "0001"
    assert len(result.errors) >= 1
    assert any(e.code == "DROP_COLUMN" for e in result.errors)


def test_lint_safe_migration(alembic_config: Path) -> None:
    versions_dir = _get_versions_dir(alembic_config)
    _create_migration_with_content(versions_dir, "0001", SAFE_ADD_COLUMN_MIGRATION)

    linter = AlembicMigrationLinter(
        alembic_config,
        dialect="postgresql",
        no_cache=True,
    )
    results = linter.lint_all()

    assert len(results) == 1
    result: LintResult = results[0]
    assert result.errors == []


def test_lint_ignore_revision(alembic_config: Path) -> None:
    versions_dir = _get_versions_dir(alembic_config)
    _create_migration_with_content(versions_dir, "0001", DROP_COLUMN_MIGRATION)

    linter = AlembicMigrationLinter(
        alembic_config,
        dialect="postgresql",
        no_cache=True,
        ignore_revisions=["0001"],
    )
    results = linter.lint_all()

    assert len(results) == 1
    result: LintResult = results[0]
    assert result.skipped is True


def test_lint_ignore_revision_contains(alembic_config: Path) -> None:
    versions_dir = _get_versions_dir(alembic_config)
    _create_migration_with_content(versions_dir, "0001_skip_me", DROP_COLUMN_MIGRATION)

    linter = AlembicMigrationLinter(
        alembic_config,
        dialect="postgresql",
        no_cache=True,
        ignore_revision_contains="skip",
    )
    results = linter.lint_all()

    assert len(results) == 1
    result: LintResult = results[0]
    assert result.skipped is True


def test_lint_exclude_test(alembic_config: Path) -> None:
    versions_dir = _get_versions_dir(alembic_config)
    _create_migration_with_content(versions_dir, "0001", DROP_COLUMN_MIGRATION)

    linter = AlembicMigrationLinter(
        alembic_config,
        dialect="postgresql",
        no_cache=True,
        exclude_tests=["DROP_COLUMN"],
    )
    results = linter.lint_all()

    assert len(results) == 1
    result: LintResult = results[0]
    assert result.errors == []


def test_lint_empty(alembic_config: Path) -> None:
    linter = AlembicMigrationLinter(
        alembic_config,
        dialect="postgresql",
        no_cache=True,
    )
    results = linter.lint_all()
    assert results == []


def test_cache_key_includes_dialect(alembic_config: Path) -> None:
    """Cache key must include dialect so cross-dialect results aren't reused."""
    from alembic_migration_linter.cache import get_cache_key

    versions_dir = _get_versions_dir(alembic_config)
    _create_migration_with_content(versions_dir, "0001", SAFE_ADD_COLUMN_MIGRATION)

    migration_file = versions_dir / "0001.py"

    # The cache key should differ per dialect for the same file
    pg_key = get_cache_key(migration_file, "postgresql")
    mysql_key = get_cache_key(migration_file, "mysql")

    assert pg_key != mysql_key, "Cache key must differ per dialect"


def test_lint_single_revision_without_load(alembic_config: Path) -> None:
    """lint_migration via get_migration should work without prior load()."""
    versions_dir = _get_versions_dir(alembic_config)
    _create_migration_with_content(versions_dir, "0001", DROP_COLUMN_MIGRATION)

    linter = AlembicMigrationLinter(
        alembic_config,
        dialect="postgresql",
        no_cache=True,
    )
    # This mirrors the CLI --revision path: get_migration → lint_migration
    migration = linter.loader.get_migration("0001")
    assert migration is not None

    result = linter.lint_migration(migration)
    assert result.migration_revision == "0001"
    assert any(e.code == "DROP_COLUMN" for e in result.errors)


def test_cache_integration(alembic_config: Path, tmp_path: Path) -> None:
    """Cache miss on first run, cache hit on second run."""
    versions_dir = _get_versions_dir(alembic_config)
    _create_migration_with_content(versions_dir, "0001", SAFE_ADD_COLUMN_MIGRATION)

    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    with patch("alembic_migration_linter.cache._get_cache_dir", return_value=cache_dir):
        linter1 = AlembicMigrationLinter(
            alembic_config,
            dialect="postgresql",
            no_cache=False,
        )
        results1 = linter1.lint_all()
        assert len(results1) == 1

        linter2 = AlembicMigrationLinter(
            alembic_config,
            dialect="postgresql",
            no_cache=False,
        )
        results2 = linter2.lint_all()
        assert len(results2) == 1
        assert isinstance(results2[0], LintResult)
        assert results2[0].migration_revision == "0001"


def test_lint_all_since_revision(alembic_config: Path) -> None:
    """lint_all(since_revision) only returns migrations after the given revision."""
    versions_dir = _get_versions_dir(alembic_config)
    _create_migration_with_content(versions_dir, "0001", SAFE_ADD_COLUMN_MIGRATION)
    _create_migration(versions_dir, "0002", down_revision="0001")

    linter = AlembicMigrationLinter(
        alembic_config,
        dialect="postgresql",
        no_cache=True,
    )
    results = linter.lint_all(since_revision="0001")

    assert len(results) == 1
    assert results[0].migration_revision == "0002"


def test_lint_ignore_revision_contains_filename(alembic_config: Path) -> None:
    """Migration skipped when ignore_revision_contains matches filename but not rev."""
    versions_dir = _get_versions_dir(alembic_config)
    migration_file = versions_dir / "0001_skip_me.py"
    migration_file.write_text(
        'revision = "0001"\n'
        "down_revision = None\n"
        "depends_on = None\n\n"
        "from alembic import op\n\n"
        "def upgrade():\n"
        '    op.drop_column("users", "email")\n'
    )

    linter = AlembicMigrationLinter(
        alembic_config,
        dialect="postgresql",
        no_cache=True,
        ignore_revision_contains="skip_me",
    )
    results = linter.lint_all()

    assert len(results) == 1
    assert results[0].skipped is True
