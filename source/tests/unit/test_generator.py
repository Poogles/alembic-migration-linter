from __future__ import annotations

from pathlib import Path

import pytest
from alembic.config import Config

from alembic_migration_linter.generator import AlembicSqlGenerator
from alembic_migration_linter.loader import AlembicMigration, AlembicMigrationLoader
from tests.conftest import _create_migration_with_content, _get_versions_dir

DROP_COLUMN_MIGRATION = """
from alembic import op

def upgrade():
    op.drop_column("users", "email")

def downgrade():
    pass
"""

ADD_COLUMN_MIGRATION = """
from alembic import op
import sqlalchemy as sa

def upgrade():
    op.add_column("users", sa.Column("age", sa.Integer()))

def downgrade():
    pass
"""

DROP_TABLE_MIGRATION = """
from alembic import op

def upgrade():
    op.drop_table("users")

def downgrade():
    pass
"""

EMPTY_MIGRATION = """
def upgrade():
    pass

def downgrade():
    pass
"""

DOWNGRADE_DROP_COLUMN = """
from alembic import op

def upgrade():
    pass

def downgrade():
    op.drop_column("users", "email")
"""

NO_DOWNGRADE_MIGRATION = """
from alembic import op

def upgrade():
    pass
"""

TYPEERROR_MIGRATION = """
from alembic import op

def upgrade():
    raise TypeError("something went wrong in migration")

def downgrade():
    pass
"""


def test_drop_column(alembic_config: Path) -> None:
    versions_dir = _get_versions_dir(alembic_config)
    _create_migration_with_content(versions_dir, "0001", DROP_COLUMN_MIGRATION)

    migration = _load_migration(alembic_config)
    sql = _generate_sql(alembic_config, migration)

    assert len(sql) == 3
    assert sql[0].upper() == "BEGIN"
    assert "DROP COLUMN" in sql[1].upper()
    assert sql[2].upper() == "COMMIT"


def test_add_column(alembic_config: Path) -> None:
    versions_dir = _get_versions_dir(alembic_config)
    _create_migration_with_content(versions_dir, "0001", ADD_COLUMN_MIGRATION)

    migration = _load_migration(alembic_config)
    sql = _generate_sql(alembic_config, migration)

    assert len(sql) >= 1
    assert any("ADD COLUMN" in stmt.upper() for stmt in sql)


def test_drop_table(alembic_config: Path) -> None:
    versions_dir = _get_versions_dir(alembic_config)
    _create_migration_with_content(versions_dir, "0001", DROP_TABLE_MIGRATION)

    migration = _load_migration(alembic_config)
    sql = _generate_sql(alembic_config, migration)

    assert len(sql) >= 1
    assert any("DROP TABLE" in stmt.upper() for stmt in sql)


def test_empty_migration(alembic_config: Path) -> None:
    versions_dir = _get_versions_dir(alembic_config)
    _create_migration_with_content(versions_dir, "0001", EMPTY_MIGRATION)

    migration = _load_migration(alembic_config)
    sql = _generate_sql(alembic_config, migration)

    assert sql == ["BEGIN", "COMMIT"]


def test_generate_downgrade_sql(alembic_config: Path) -> None:
    versions_dir = _get_versions_dir(alembic_config)
    _create_migration_with_content(versions_dir, "0001", DOWNGRADE_DROP_COLUMN)

    migration = _load_migration(alembic_config)
    generator = AlembicSqlGenerator(Config(str(alembic_config)), "postgresql")
    sql = generator.generate_downgrade_sql(migration)

    assert len(sql) >= 1
    assert any("DROP COLUMN" in stmt.upper() for stmt in sql)


def test_no_downgrade_function(alembic_config: Path) -> None:
    versions_dir = _get_versions_dir(alembic_config)
    _create_migration_with_content(versions_dir, "0001", NO_DOWNGRADE_MIGRATION)

    migration = _load_migration(alembic_config)
    assert migration.downgrade_fn is None

    generator = AlembicSqlGenerator(Config(str(alembic_config)), "postgresql")
    sql = generator.generate_downgrade_sql(migration)

    assert sql == []


def test_typeerror_in_migration_raises(alembic_config: Path) -> None:
    """TypeError raised inside upgrade() should propagate, not be swallowed."""
    versions_dir = _get_versions_dir(alembic_config)
    _create_migration_with_content(versions_dir, "0001", TYPEERROR_MIGRATION)

    migration = _load_migration(alembic_config)
    generator = AlembicSqlGenerator(Config(str(alembic_config)), "postgresql")

    with pytest.raises(TypeError, match="something went wrong in migration"):
        generator.generate_sql(migration)


def _load_migration(alembic_config: Path) -> AlembicMigration:
    loader = AlembicMigrationLoader(alembic_config)
    return loader.load()[0]


def _generate_sql(alembic_config: Path, migration: AlembicMigration) -> list[str]:
    generator = AlembicSqlGenerator(Config(str(alembic_config)), "postgresql")
    return generator.generate_sql(migration)
