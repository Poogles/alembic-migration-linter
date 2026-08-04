from __future__ import annotations

from pathlib import Path

import pytest

from alembic_migration_linter.linter import LintResult
from tests.conftest import ERROR_SCENARIOS, SAFE_SCENARIOS, _lint_scenario


@pytest.mark.parametrize("scenario_name", list(ERROR_SCENARIOS.keys()))
def test_error_scenarios(
    scenario_name: str,
    tmp_path: Path,
) -> None:
    expected_errors, expected_warnings = ERROR_SCENARIOS[scenario_name]

    linter = _lint_scenario(scenario_name, tmp_path)
    results = linter.lint_all()

    assert len(results) == 1, (
        f"Scenario {scenario_name}: expected 1 result, got {len(results)}"
    )

    result: LintResult = results[0]
    error_codes = [e.code for e in result.errors]
    warning_codes = [w.code for w in result.warnings]

    for code in expected_errors:
        assert code in error_codes, (
            f"Scenario {scenario_name}: expected error {code}, "
            f"got errors={error_codes}, warnings={warning_codes}"
        )

    assert warning_codes == expected_warnings, (
        f"Scenario {scenario_name}: expected warnings "
        f"{expected_warnings}, got {warning_codes}"
    )


@pytest.mark.parametrize("scenario_name", list(SAFE_SCENARIOS.keys()))
def test_safe_scenarios(
    scenario_name: str,
    tmp_path: Path,
) -> None:
    linter = _lint_scenario(scenario_name, tmp_path)
    results = linter.lint_all()

    assert len(results) == 1

    result: LintResult = results[0]
    assert result.errors == [], (
        f"Scenario {scenario_name}: expected no errors, "
        f"got {[e.code for e in result.errors]}"
    )
    assert result.warnings == [], (
        f"Scenario {scenario_name}: expected no warnings, "
        f"got {[w.code for w in result.warnings]}"
    )
