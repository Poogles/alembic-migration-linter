from __future__ import annotations

from click.testing import CliRunner

from alembic_migration_linter.cli import main
from tests.conftest import (
    ERROR_SCENARIOS,
    SAFE_SCENARIOS,
    WARNING_SCENARIOS,
    _copy_scenario,
)


def test_cli_help() -> None:
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "Detect backward incompatible Alembic migrations" in result.output
    assert "--config" in result.output
    assert "--dialect" in result.output
    assert "--revision" in result.output
    assert "--since-revision" in result.output
    assert "--exclude-test" in result.output
    assert "--warnings-as-errors" in result.output
    assert "--no-cache" in result.output
    assert "--quiet" in result.output
    assert "--ignore-revision" in result.output
    assert "--ignore-revision-contains" in result.output


def test_cli_help_flag() -> None:
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "Detect backward incompatible Alembic migrations" in result.output


def test_cli_safe_migration(tmp_path) -> None:
    runner = CliRunner()
    config_path = _copy_scenario("add_column_with_default", tmp_path)
    result = runner.invoke(main, ["-c", str(config_path), "--no-cache"])
    assert result.exit_code == 0
    assert "OK" in result.output
    assert "Valid migrations: 1/1" in result.output
    assert "Erroneous migrations: 0/1" in result.output


def test_cli_error_migration(tmp_path) -> None:
    runner = CliRunner()
    config_path = _copy_scenario("drop_column", tmp_path)
    result = runner.invoke(main, ["-c", str(config_path), "--no-cache"])
    assert result.exit_code == 1
    assert "ERR" in result.output
    assert "DROP_COLUMN" in result.output
    assert "Erroneous migrations: 1/1" in result.output


def test_cli_warning_migration(tmp_path) -> None:
    runner = CliRunner()
    config_path = _copy_scenario("create_index_no_concurrently", tmp_path)
    result = runner.invoke(main, ["-c", str(config_path), "--no-cache"])
    assert result.exit_code == 0
    assert "WARNING" in result.output
    assert "CREATE_INDEX" in result.output
    assert "Migrations with warnings: 1/1" in result.output


def test_cli_warnings_as_errors(tmp_path) -> None:
    runner = CliRunner()
    config_path = _copy_scenario("create_index_no_concurrently", tmp_path)
    result = runner.invoke(
        main, ["-c", str(config_path), "--no-cache", "--warnings-as-errors"]
    )
    assert result.exit_code == 1
    assert "ERR" in result.output
    assert "CREATE_INDEX" in result.output
    assert "Erroneous migrations: 1/1" in result.output


def test_cli_quiet_flag(tmp_path) -> None:
    runner = CliRunner()
    config_path = _copy_scenario("add_column_with_default", tmp_path)
    result = runner.invoke(main, ["-c", str(config_path), "--no-cache", "--quiet"])
    assert result.exit_code == 0
    assert "OK" not in result.output
    assert "Valid migrations: 1/1" in result.output


def test_cli_quiet_still_shows_errors(tmp_path) -> None:
    runner = CliRunner()
    config_path = _copy_scenario("drop_column", tmp_path)
    result = runner.invoke(main, ["-c", str(config_path), "--no-cache", "--quiet"])
    assert result.exit_code == 1
    assert "ERR" in result.output
    assert "DROP_COLUMN" in result.output


def test_cli_revision_flag(tmp_path) -> None:
    runner = CliRunner()
    config_path = _copy_scenario("drop_column", tmp_path)
    result = runner.invoke(
        main, ["-c", str(config_path), "--no-cache", "--revision", "drop_column"]
    )
    assert result.exit_code == 1
    assert "ERR" in result.output
    assert "DROP_COLUMN" in result.output


def test_cli_revision_not_found(tmp_path) -> None:
    runner = CliRunner()
    config_path = _copy_scenario("drop_column", tmp_path)
    result = runner.invoke(
        main, ["-c", str(config_path), "--no-cache", "--revision", "nonexistent"]
    )
    assert result.exit_code == 1
    assert "not found" in result.output


def test_cli_short_revision_flag(tmp_path) -> None:
    runner = CliRunner()
    config_path = _copy_scenario("drop_column", tmp_path)
    result = runner.invoke(
        main, ["-c", str(config_path), "--no-cache", "-r", "drop_column"]
    )
    assert result.exit_code == 1
    assert "ERR" in result.output


def test_cli_exclude_test(tmp_path) -> None:
    runner = CliRunner()
    config_path = _copy_scenario("drop_column", tmp_path)
    result = runner.invoke(
        main, ["-c", str(config_path), "--no-cache", "--exclude-test", "DROP_COLUMN"]
    )
    assert result.exit_code == 0
    assert "OK" in result.output
    assert "Valid migrations: 1/1" in result.output


def test_cli_short_exclude_test(tmp_path) -> None:
    runner = CliRunner()
    config_path = _copy_scenario("drop_column", tmp_path)
    result = runner.invoke(
        main, ["-c", str(config_path), "--no-cache", "-e", "DROP_COLUMN"]
    )
    assert result.exit_code == 0
    assert "OK" in result.output


def test_cli_exclude_test_multiple(tmp_path) -> None:
    runner = CliRunner()
    config_path = _copy_scenario("drop_column", tmp_path)
    result = runner.invoke(
        main,
        [
            "-c",
            str(config_path),
            "--no-cache",
            "-e",
            "DROP_COLUMN",
            "-e",
            "DROP_TABLE",
        ],
    )
    assert result.exit_code == 0
    assert "OK" in result.output


def test_cli_ignore_revision(tmp_path) -> None:
    runner = CliRunner()
    config_path = _copy_scenario("drop_column", tmp_path)
    result = runner.invoke(
        main, ["-c", str(config_path), "--no-cache", "--ignore-revision", "drop_column"]
    )
    assert result.exit_code == 0
    assert "IGNORE" in result.output
    assert "Ignored migrations: 1/1" in result.output


def test_cli_ignore_revision_contains(tmp_path) -> None:
    runner = CliRunner()
    config_path = _copy_scenario("skip_this_migration", tmp_path)
    result = runner.invoke(
        main,
        [
            "-c",
            str(config_path),
            "--no-cache",
            "--ignore-revision-contains",
            "skip",
        ],
    )
    assert result.exit_code == 0
    assert "IGNORE" in result.output


def test_cli_dialect_flag(tmp_path) -> None:
    runner = CliRunner()
    config_path = _copy_scenario("drop_column", tmp_path)
    result = runner.invoke(
        main, ["-c", str(config_path), "--no-cache", "--dialect", "mysql"]
    )
    assert result.exit_code == 1
    assert "ERR" in result.output


def test_cli_short_dialect_flag(tmp_path) -> None:
    runner = CliRunner()
    config_path = _copy_scenario("drop_column", tmp_path)
    result = runner.invoke(main, ["-c", str(config_path), "--no-cache", "-d", "mysql"])
    assert result.exit_code == 1
    assert "ERR" in result.output


def test_cli_config_flag(tmp_path) -> None:
    runner = CliRunner()
    config_path = _copy_scenario("drop_column", tmp_path)
    result = runner.invoke(main, ["--config", str(config_path), "--no-cache"])
    assert result.exit_code == 1
    assert "ERR" in result.output


def test_cli_config_not_found() -> None:
    runner = CliRunner()
    result = runner.invoke(main, ["-c", "/nonexistent/alembic.ini"])
    assert result.exit_code != 0


def test_cli_linters_section_dialect(tmp_path) -> None:
    config_path = _copy_scenario("drop_column", tmp_path)
    config_path.write_text(
        "[alembic]\nscript_location = %(here)s\n\n[linters]\ndialect = mysql\n"
    )
    runner = CliRunner()
    result = runner.invoke(main, ["-c", str(config_path), "--no-cache"])
    assert result.exit_code == 1
    assert "ERR" in result.output


def test_cli_linters_section_exclude_tests(tmp_path) -> None:
    config_path = _copy_scenario("drop_column", tmp_path)
    config_path.write_text(
        "[alembic]\nscript_location = %(here)s\n\n"
        "[linters]\nexclude_tests = DROP_COLUMN\n"
    )
    runner = CliRunner()
    result = runner.invoke(main, ["-c", str(config_path), "--no-cache"])
    assert result.exit_code == 0
    assert "OK" in result.output


def test_cli_linters_section_warnings_as_errors(tmp_path) -> None:
    config_path = _copy_scenario("create_index_no_concurrently", tmp_path)
    config_path.write_text(
        "[alembic]\nscript_location = %(here)s\n\n"
        "[linters]\nwarnings_as_errors = true\n"
    )
    runner = CliRunner()
    result = runner.invoke(main, ["-c", str(config_path), "--no-cache"])
    assert result.exit_code == 1
    assert "ERR" in result.output


def test_cli_linters_section_exclude_tests_combined_with_cli(tmp_path) -> None:
    config_path = _copy_scenario("drop_column", tmp_path)
    config_path.write_text(
        "[alembic]\nscript_location = %(here)s\n\n"
        "[linters]\nexclude_tests = DROP_TABLE\n"
    )
    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "-c",
            str(config_path),
            "--no-cache",
            "-e",
            "DROP_COLUMN",
        ],
    )
    assert result.exit_code == 0
    assert "OK" in result.output


def test_cli_cli_dialect_overrides_config(tmp_path) -> None:
    config_path = _copy_scenario("drop_column", tmp_path)
    config_path.write_text(
        "[alembic]\nscript_location = %(here)s\n\n[linters]\ndialect = mysql\n"
    )
    runner = CliRunner()
    result = runner.invoke(
        main, ["-c", str(config_path), "--no-cache", "--dialect", "postgresql"]
    )
    assert result.exit_code == 1
    assert "ERR" in result.output


def test_cli_summary_output(tmp_path) -> None:
    runner = CliRunner()
    config_path = _copy_scenario("drop_column", tmp_path)
    result = runner.invoke(main, ["-c", str(config_path), "--no-cache"])
    assert "*** Summary ***" in result.output
    assert "Valid migrations:" in result.output
    assert "Erroneous migrations:" in result.output
    assert "Migrations with warnings:" in result.output
    assert "Ignored migrations:" in result.output


def test_cli_all_error_scenarios(tmp_path) -> None:
    runner = CliRunner()
    for scenario_name, (expected_errors, _) in ERROR_SCENARIOS.items():
        config_path = _copy_scenario(scenario_name, tmp_path)
        result = runner.invoke(main, ["-c", str(config_path), "--no-cache"])
        assert result.exit_code == 1, (
            f"Scenario {scenario_name}: expected exit code 1, got {result.exit_code}"
        )
        assert "ERR" in result.output, (
            f"Scenario {scenario_name}: expected ERR in output"
        )
        for code in expected_errors:
            assert code in result.output, (
                f"Scenario {scenario_name}: expected {code} in output"
            )


def test_cli_all_safe_scenarios(tmp_path) -> None:
    runner = CliRunner()
    for scenario_name, (_expected_errors, _expected_warnings) in SAFE_SCENARIOS.items():
        config_path = _copy_scenario(scenario_name, tmp_path)
        result = runner.invoke(main, ["-c", str(config_path), "--no-cache"])
        assert result.exit_code == 0, (
            f"Scenario {scenario_name}: expected exit code 0, got {result.exit_code}"
        )
        assert "Erroneous migrations: 0/1" in result.output, (
            f"Scenario {scenario_name}: expected no errors"
        )


def test_cli_all_warning_scenarios(tmp_path) -> None:
    runner = CliRunner()
    for scenario_name, (
        _expected_errors,
        expected_warnings,
    ) in WARNING_SCENARIOS.items():
        config_path = _copy_scenario(scenario_name, tmp_path)
        result = runner.invoke(main, ["-c", str(config_path), "--no-cache"])
        assert result.exit_code == 0, (
            f"Scenario {scenario_name}: expected exit code 0, got {result.exit_code}"
        )
        assert "WARNING" in result.output, (
            f"Scenario {scenario_name}: expected WARNING in output"
        )
        for code in expected_warnings:
            assert code in result.output, (
                f"Scenario {scenario_name}: expected {code} in output"
            )
