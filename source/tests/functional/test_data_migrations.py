from __future__ import annotations

from pathlib import Path

import pytest

from alembic_migration_linter.linter import LintResult
from tests.conftest import _lint_scenario


@pytest.mark.parametrize(
    "scenario_name,expected_error_codes",
    [
        ("run_sql_with_drop", ["DROP_COLUMN"]),
    ],
)
def test_data_migration_errors(
    scenario_name: str,
    expected_error_codes: list[str],
    tmp_path: Path,
) -> None:
    """Raw SQL operations are detected by the SQL analyser."""
    linter = _lint_scenario(scenario_name, tmp_path)
    results = linter.lint_all()

    assert len(results) == 1

    result: LintResult = results[0]
    error_codes = [e.code for e in result.errors]

    for code in expected_error_codes:
        assert code in error_codes


@pytest.mark.parametrize(
    "scenario_name",
    [
        "run_python_no_reverse",
        "run_sql_no_reverse",
    ],
)
def test_data_migration_safe_sql(
    scenario_name: str,
    tmp_path: Path,
) -> None:
    """Data migrations with UPDATE only produce no SQL-level issues."""
    linter = _lint_scenario(scenario_name, tmp_path)
    results = linter.lint_all()

    assert len(results) == 1

    result: LintResult = results[0]
    assert result.errors == []


def test_conn_execute_scalar_does_not_crash(tmp_path: Path) -> None:
    """Migrations that call conn.execute(...).scalar() should not crash the linter.

    In offline rendering mode, conn.execute() returns None, so .scalar() would
    raise AttributeError. The linter should gracefully handle this and still
    capture any SQL that was rendered before the failure.
    """
    linter = _lint_scenario("conn_execute_scalar", tmp_path)
    results = linter.lint_all()

    assert len(results) == 1
    result: LintResult = results[0]
    assert result.skipped is False
    # The SELECT and UPDATE statements should have been captured and analyzed
    assert result.errors == []
