from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

import pytest

from alembic_migration_linter.linter import AlembicMigrationLinter

TEST_MIGRATIONS_DIR = Path(__file__).parent / "test_migrations"


def _create_alembic_config(tmp_path: Path) -> Path:
    """Create a minimal Alembic config for unit testing."""
    migrations_dir = tmp_path / "migrations"
    versions_dir = migrations_dir / "versions"
    versions_dir.mkdir(parents=True)

    ini_path = tmp_path / "alembic.ini"
    ini_path.write_text(f"[alembic]\nscript_location = {migrations_dir}\n")

    (migrations_dir / "env.py").write_text("")
    (migrations_dir / "script.py.mako").write_text("")

    return ini_path


def _get_versions_dir(alembic_config: Path) -> Path:
    """Return the versions directory for a given alembic config."""
    return alembic_config.parent / "migrations" / "versions"


def _create_migration(
    versions_dir: Path,
    revision: str,
    down_revision: str | None,
    depends_on: str | None = None,
    has_upgrade: bool = True,
    has_downgrade: bool = True,
) -> None:
    """Create a migration file with metadata and optional upgrade/downgrade."""
    content = f'revision = "{revision}"\n'
    content += f"down_revision = {repr(down_revision)}\n"
    content += f"depends_on = {repr(depends_on)}\n\n"

    if has_upgrade:
        content += "from alembic import op\n\n"
        content += "def upgrade():\n    pass\n\n"

    if has_downgrade:
        content += "def downgrade():\n    pass\n"

    (versions_dir / f"{revision}.py").write_text(content)


def _create_migration_with_content(
    versions_dir: Path,
    revision: str,
    content: str,
) -> None:
    """Create a migration file with custom body content."""
    header = f'revision = "{revision}"\n'
    header += "down_revision = None\n"
    header += "depends_on = None\n\n"
    (versions_dir / f"{revision}.py").write_text(header + content)


@pytest.fixture
def alembic_config(tmp_path: Path) -> Path:
    """Create a minimal Alembic config for testing."""
    return _create_alembic_config(tmp_path)


def _copy_scenario(
    scenario_name: str,
    tmp_path: Path,
) -> Path:
    """Copy a single scenario directory to tmp_path and return alembic.ini path."""
    scenario_dir = TEST_MIGRATIONS_DIR / scenario_name
    dest = tmp_path / scenario_name
    shutil.copytree(scenario_dir, dest)
    return dest / "alembic.ini"


@pytest.fixture
def tmp_migrations(tmp_path: Path) -> Path:
    """Return a temp directory for copied migrations."""
    return tmp_path


# Scenario name → (expected_error_codes, expected_warning_codes)
ERROR_SCENARIOS: dict[str, tuple[list[str], list[str]]] = {
    "add_not_null_column": (["NOT_NULL"], []),
    "drop_column": (["DROP_COLUMN"], []),
    "drop_table": (["DROP_TABLE"], []),
    "rename_column": (["RENAME_COLUMN"], []),
    "rename_table": (["RENAME_TABLE"], []),
    "alter_column": (["ALTER_COLUMN"], []),
    "add_unique_constraint": (["ADD_UNIQUE"], []),
    "make_not_null_without_default": (["NOT_NULL"], []),
    "run_sql_with_drop": (["DROP_COLUMN"], []),
    "batch_alter_table": (["NOT_NULL"], []),
    "raw_sql": (["DROP_COLUMN"], []),
}

# Scenario name → (expected_error_codes, expected_warning_codes)
# New safe scenarios are annotated with the rule they guard against.
SAFE_SCENARIOS: dict[str, tuple[list[str], list[str]]] = {
    "create_table_with_not_null": ([], []),
    "add_column_with_default": ([], []),
    "drop_not_null": ([], []),
    "create_through_table": ([], []),
    "add_not_null_then_default": ([], []),  # NOT_NULL safe pattern
    "add_server_default": ([], []),
    "run_python_no_reverse": ([], []),
    "run_sql_no_reverse": ([], []),
    "safe_add_table": ([], []),  # DROP_TABLE / RENAME_TABLE safe pattern
    "safe_add_column": ([], []),  # DROP_COLUMN safe pattern
    "safe_add_column_rename": ([], []),  # RENAME_COLUMN safe pattern
    "safe_add_column_alter": ([], []),  # ALTER_COLUMN safe pattern
    "safe_create_index_concurrently": ([], []),  # CREATE_INDEX safe pattern
    "safe_drop_index_concurrently": ([], []),  # DROP_INDEX safe pattern
    "safe_create_index_exclusive": ([], []),  # CREATE_INDEX_EXCLUSIVE safe pattern
    "safe_add_unique_on_new_table": ([], []),  # ADD_UNIQUE safe pattern
}

WARNING_SCENARIOS: dict[str, tuple[list[str], list[str]]] = {
    "create_index_no_concurrently": ([], ["CREATE_INDEX"]),
    "create_index_exclusive_lock": ([], ["CREATE_INDEX_EXCLUSIVE"]),
    "drop_index_no_concurrently": ([], ["DROP_INDEX"]),
    "reindex": ([], ["REINDEX"]),
}


@pytest.fixture
def scenario_config_path(
    scenario_name: str,
    tmp_migrations: Path,
) -> Path:
    """Copy a single scenario to a temp dir and return alembic.ini path."""
    return _copy_scenario(scenario_name, tmp_migrations)


@pytest.fixture
def scenario_linter(
    scenario_config_path: Path,
    dialect: str,
) -> AlembicMigrationLinter:
    """Create a linter for a single scenario."""
    return AlembicMigrationLinter(
        config_path=scenario_config_path,
        dialect=dialect,
        no_cache=True,
    )


@pytest.fixture
def dialect() -> str:
    """Default dialect for tests."""
    return "postgresql"


@pytest.fixture(params=list(ERROR_SCENARIOS.keys()))
def error_scenario_name(request: pytest.FixtureRequest) -> str:
    """Parametrized fixture for error scenarios."""
    return request.param  # type: ignore[no-any-return]


@pytest.fixture(params=list(SAFE_SCENARIOS.keys()))
def safe_scenario_name(request: pytest.FixtureRequest) -> str:
    """Parametrized fixture for safe scenarios."""
    return request.param  # type: ignore[no-any-return]


@pytest.fixture(params=list(WARNING_SCENARIOS.keys()))
def warning_scenario_name(request: pytest.FixtureRequest) -> str:
    """Parametrized fixture for warning scenarios."""
    return request.param  # type: ignore[no-any-return]


@pytest.fixture
def all_scenario_names() -> list[str]:
    """All scenario directory names."""
    return sorted(d.name for d in TEST_MIGRATIONS_DIR.iterdir() if d.is_dir())


def _lint_scenario(
    scenario_name: str,
    tmp_path: Path,
    dialect: str = "postgresql",
    **linter_kwargs: Any,
) -> AlembicMigrationLinter:
    """Helper to create a linter for a scenario."""
    config_path = _copy_scenario(scenario_name, tmp_path)
    return AlembicMigrationLinter(
        config_path=config_path,
        dialect=dialect,
        no_cache=True,
        **linter_kwargs,
    )
