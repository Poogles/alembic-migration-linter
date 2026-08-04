from __future__ import annotations

from pathlib import Path

from alembic_migration_linter.loader import AlembicMigration, AlembicMigrationLoader
from tests.conftest import _create_migration, _get_versions_dir


def test_load_empty(alembic_config: Path) -> None:
    loader = AlembicMigrationLoader(alembic_config)
    migrations = loader.load()
    assert migrations == []


def test_load_single_migration(alembic_config: Path) -> None:
    versions_dir = _get_versions_dir(alembic_config)
    _create_migration(versions_dir, "0001", None)

    loader = AlembicMigrationLoader(alembic_config)
    migrations = loader.load()

    assert len(migrations) == 1
    assert migrations[0].revision == "0001"
    assert migrations[0].down_revision is None
    assert migrations[0].depends_on is None


def test_load_ordered_migrations(alembic_config: Path) -> None:
    versions_dir = _get_versions_dir(alembic_config)
    _create_migration(versions_dir, "0001", None)
    _create_migration(versions_dir, "0002", "0001")
    _create_migration(versions_dir, "0003", "0002")

    loader = AlembicMigrationLoader(alembic_config)
    migrations = loader.load()

    assert len(migrations) == 3
    revisions = [m.revision for m in migrations]
    assert revisions == ["0003", "0002", "0001"]


def test_get_migration(alembic_config: Path) -> None:
    versions_dir = _get_versions_dir(alembic_config)
    _create_migration(versions_dir, "0001", None)
    _create_migration(versions_dir, "0002", "0001")

    loader = AlembicMigrationLoader(alembic_config)
    loader.load()

    assert loader.get_migration("0001") is not None
    assert loader.get_migration("0002") is not None
    assert loader.get_migration("9999") is None


def test_get_head_revisions(alembic_config: Path) -> None:
    versions_dir = _get_versions_dir(alembic_config)
    _create_migration(versions_dir, "0001", None)
    _create_migration(versions_dir, "0002", "0001")
    _create_migration(versions_dir, "0003", "0002")

    loader = AlembicMigrationLoader(alembic_config)
    loader.load()

    heads = loader.get_head_revisions()
    assert heads == ["0003"]


def test_get_head_revisions_multiple_heads(alembic_config: Path) -> None:
    versions_dir = _get_versions_dir(alembic_config)
    _create_migration(versions_dir, "0001", None)
    _create_migration(versions_dir, "0002a", "0001")
    _create_migration(versions_dir, "0002b", "0001")

    loader = AlembicMigrationLoader(alembic_config)
    loader.load()

    heads = loader.get_head_revisions()
    assert set(heads) == {"0002a", "0002b"}


def test_get_revisions_since(alembic_config: Path) -> None:
    versions_dir = _get_versions_dir(alembic_config)
    _create_migration(versions_dir, "0001", None)
    _create_migration(versions_dir, "0002", "0001")
    _create_migration(versions_dir, "0003", "0002")

    loader = AlembicMigrationLoader(alembic_config)
    loader.load()

    since = loader.get_revisions_since("0001")
    revisions = [m.revision for m in since]
    assert revisions == ["0002", "0003"]


def test_get_revisions_since_no_matching(alembic_config: Path) -> None:
    versions_dir = _get_versions_dir(alembic_config)
    _create_migration(versions_dir, "0001", None)

    loader = AlembicMigrationLoader(alembic_config)
    loader.load()

    since = loader.get_revisions_since("9999")
    assert since == []


def test_skip_migration_without_upgrade(alembic_config: Path) -> None:
    versions_dir = _get_versions_dir(alembic_config)
    _create_migration(versions_dir, "0001", None, has_upgrade=False)

    loader = AlembicMigrationLoader(alembic_config)
    migrations = loader.load()
    assert migrations == []


def test_migration_filepath(alembic_config: Path) -> None:
    versions_dir = _get_versions_dir(alembic_config)
    _create_migration(versions_dir, "0001", None)

    loader = AlembicMigrationLoader(alembic_config)
    migrations = loader.load()

    assert migrations[0].filepath.name == "0001.py"
    assert migrations[0].filepath.is_file()


def test_migration_has_upgrade_fn(alembic_config: Path) -> None:
    versions_dir = _get_versions_dir(alembic_config)
    _create_migration(versions_dir, "0001", None)

    loader = AlembicMigrationLoader(alembic_config)
    migrations = loader.load()

    migration: AlembicMigration = migrations[0]
    assert callable(migration.upgrade_fn)


def test_migration_has_downgrade_fn(alembic_config: Path) -> None:
    versions_dir = _get_versions_dir(alembic_config)
    _create_migration(versions_dir, "0001", None, has_downgrade=True)

    loader = AlembicMigrationLoader(alembic_config)
    migrations = loader.load()

    migration: AlembicMigration = migrations[0]
    assert callable(migration.downgrade_fn)


def test_migration_no_downgrade_fn(alembic_config: Path) -> None:
    versions_dir = _get_versions_dir(alembic_config)
    _create_migration(versions_dir, "0001", None, has_downgrade=False)

    loader = AlembicMigrationLoader(alembic_config)
    migrations = loader.load()

    migration: AlembicMigration = migrations[0]
    assert migration.downgrade_fn is None


def test_depends_on_extracted(alembic_config: Path) -> None:
    """depends_on is correctly extracted from migration metadata."""
    versions_dir = _get_versions_dir(alembic_config)
    _create_migration(versions_dir, "0000", None)
    _create_migration(versions_dir, "0001", None, depends_on="0000")

    loader = AlembicMigrationLoader(alembic_config)
    migrations = loader.load()

    migration = next(m for m in migrations if m.revision == "0001")
    assert migration.depends_on == ("0000",)


def test_get_revisions_since_follows_chain(alembic_config: Path) -> None:
    """get_revisions_since follows the revision chain correctly."""
    versions_dir = _get_versions_dir(alembic_config)
    _create_migration(versions_dir, "0000", None)
    _create_migration(versions_dir, "0001", "0000")
    _create_migration(versions_dir, "0002", "0001")

    loader = AlembicMigrationLoader(alembic_config)
    loader.load()

    since = loader.get_revisions_since("0000")
    revisions = {m.revision for m in since}
    assert "0001" in revisions
    assert "0002" in revisions
    assert "0000" not in revisions


def test_heads_exclude_non_heads(alembic_config: Path) -> None:
    """Revisions that have dependents are not considered heads."""
    versions_dir = _get_versions_dir(alembic_config)
    _create_migration(versions_dir, "0000", None)
    _create_migration(versions_dir, "0001", "0000")

    loader = AlembicMigrationLoader(alembic_config)
    loader.load()

    heads = loader.get_head_revisions()
    assert "0000" not in heads
    assert "0001" in heads


def test_get_migration_lazy_loads(alembic_config: Path) -> None:
    """get_migration should lazy-load migrations without explicit load() call."""
    versions_dir = _get_versions_dir(alembic_config)
    _create_migration(versions_dir, "0001", None)
    _create_migration(versions_dir, "0002", "0001")

    loader = AlembicMigrationLoader(alembic_config)
    # Do NOT call loader.load() — get_migration should lazy-load
    migration = loader.get_migration("0001")

    assert migration is not None
    assert migration.revision == "0001"
