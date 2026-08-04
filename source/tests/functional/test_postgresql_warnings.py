from __future__ import annotations

from pathlib import Path

import pytest

from alembic_migration_linter.linter import LintResult
from tests.conftest import WARNING_SCENARIOS, _lint_scenario


@pytest.mark.parametrize("scenario_name", list(WARNING_SCENARIOS.keys()))
def test_postgresql_warnings(
    scenario_name: str,
    tmp_path: Path,
) -> None:
    expected_errors, expected_warnings = WARNING_SCENARIOS[scenario_name]

    linter = _lint_scenario(scenario_name, tmp_path)
    results = linter.lint_all()

    assert len(results) == 1

    result: LintResult = results[0]
    error_codes = [e.code for e in result.errors]
    warning_codes = [w.code for w in result.warnings]

    assert error_codes == expected_errors, (
        f"Scenario {scenario_name}: expected errors "
        f"{expected_errors}, got {error_codes}"
    )

    for code in expected_warnings:
        assert code in warning_codes, (
            f"Scenario {scenario_name}: expected warning "
            f"{code}, got warnings={warning_codes}"
        )


def test_warnings_present_by_default(tmp_path: Path) -> None:
    """Warnings appear as warnings, not errors, by default."""
    linter = _lint_scenario("create_index_no_concurrently", tmp_path)
    results = linter.lint_all()

    assert len(results) == 1

    result: LintResult = results[0]
    assert [w.code for w in result.warnings] == ["CREATE_INDEX"]
    assert result.errors == []
