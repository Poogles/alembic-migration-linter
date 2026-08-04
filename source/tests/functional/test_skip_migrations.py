from __future__ import annotations

from pathlib import Path

from alembic_migration_linter.linter import AlembicMigrationLinter, LintResult
from tests.conftest import _copy_scenario, _lint_scenario


def test_skip_by_revision_contains(tmp_path: Path) -> None:
    """Migration with matching revision ID is skipped."""
    config_path = _copy_scenario("skip_this_migration", tmp_path)

    linter = AlembicMigrationLinter(
        config_path=config_path,
        dialect="postgresql",
        no_cache=True,
        ignore_revision_contains="skip",
    )
    results = linter.lint_all()

    assert len(results) == 1
    result: LintResult = results[0]
    assert result.skipped is True


def test_skip_by_ignore_revisions(tmp_path: Path) -> None:
    """Migration explicitly listed in ignore_revisions is skipped."""
    config_path = _copy_scenario("skip_this_migration", tmp_path)

    linter = AlembicMigrationLinter(
        config_path=config_path,
        dialect="postgresql",
        no_cache=True,
        ignore_revisions=["skip_this_migration"],
    )
    results = linter.lint_all()

    assert len(results) == 1
    result: LintResult = results[0]
    assert result.skipped is True


def test_skip_by_filename_contains(tmp_path: Path) -> None:
    """Migration with matching filename is skipped."""
    config_path = _copy_scenario("skip_this_migration", tmp_path)

    linter = AlembicMigrationLinter(
        config_path=config_path,
        dialect="postgresql",
        no_cache=True,
        ignore_revision_contains="skip_this",
    )
    results = linter.lint_all()

    assert len(results) == 1
    result: LintResult = results[0]
    assert result.skipped is True


def test_no_skip_without_marker(tmp_path: Path) -> None:
    """Migration is not skipped when no ignore criteria match."""
    linter = _lint_scenario("skip_this_migration", tmp_path)
    results = linter.lint_all()

    assert len(results) == 1
    result: LintResult = results[0]
    assert result.skipped is False
