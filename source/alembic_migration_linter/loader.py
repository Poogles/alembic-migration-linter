from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from alembic.config import Config
from alembic.script import Script, ScriptDirectory


@dataclass
class AlembicMigration:
    """Represents a single Alembic migration script."""

    revision: str
    down_revision: str | None
    depends_on: tuple[str, ...] | None
    filepath: Path
    upgrade_fn: Callable[..., None]
    downgrade_fn: Callable[..., None] | None


class AlembicMigrationLoader:
    """Discovers and orders Alembic migration scripts."""

    def __init__(self, config_path: str | Path) -> None:
        self.config_path = Path(config_path)
        self._migrations: dict[str, AlembicMigration] = {}

    def load(self) -> list[AlembicMigration]:
        """Load all migration scripts and return them in dependency order."""
        config = Config(str(self.config_path))
        script_dir = ScriptDirectory.from_config(config)

        for script in script_dir.walk_revisions(base="base", head="heads"):
            revision_id = script.revision
            if revision_id in self._migrations:
                continue

            migration = self._load_migration(script)
            if migration is not None:
                self._migrations[revision_id] = migration

        return list(self._migrations.values())

    def _load_migration(self, script: Script) -> AlembicMigration | None:
        """Load a single migration script."""
        filepath = Path(script.path)

        module = script.module
        upgrade_fn = getattr(module, "upgrade", None)
        downgrade_fn = getattr(module, "downgrade", None)

        if upgrade_fn is None:
            return None

        down_revision = script.down_revision
        if isinstance(down_revision, tuple):
            down_revision = down_revision[0] if down_revision else None
        elif down_revision is not None:
            down_revision = str(down_revision)

        depends_on = script.dependencies
        if isinstance(depends_on, tuple):
            pass
        elif isinstance(depends_on, str):
            depends_on = (depends_on,)
        else:
            depends_on = None

        return AlembicMigration(
            revision=script.revision,
            down_revision=down_revision,
            depends_on=depends_on,
            filepath=filepath,
            upgrade_fn=upgrade_fn,
            downgrade_fn=downgrade_fn,
        )

    def get_migration(self, revision: str) -> AlembicMigration | None:
        """Get a migration by its revision ID."""
        if not self._migrations:
            self.load()
        return self._migrations.get(revision)

    def get_head_revisions(self) -> list[str]:
        """Return revision IDs that have no dependents."""
        if not self._migrations:
            self.load()

        has_dependents: set[str] = set()
        for migration in self._migrations.values():
            if migration.down_revision:
                has_dependents.add(migration.down_revision)
            if migration.depends_on:
                has_dependents.update(migration.depends_on)

        return [
            rev
            for rev, migration in self._migrations.items()
            if rev not in has_dependents
        ]

    def get_revisions_since(self, base_revision: str) -> list[AlembicMigration]:
        """Return all migrations reachable from base_revision to heads."""
        if not self._migrations:
            self.load()

        result: list[AlembicMigration] = []
        visited: set[str] = set()
        self._walk_from(base_revision, result, visited)
        return result

    def _walk_from(
        self,
        revision: str,
        result: list[AlembicMigration],
        visited: set[str],
    ) -> None:
        """Recursively walk from a revision to all dependent revisions."""
        if revision in visited:
            return
        visited.add(revision)

        for migration in self._migrations.values():
            if migration.down_revision == revision or (
                migration.depends_on and revision in migration.depends_on
            ):
                result.append(migration)
                self._walk_from(migration.revision, result, visited)
