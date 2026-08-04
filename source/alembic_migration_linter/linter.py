from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from alembic.config import Config
from django_migration_linter.sql_analyser import (  # type: ignore[attr-defined]
    analyse_sql_statements,
    get_sql_analyser_class,
)
from django_migration_linter.sql_analyser.base import Issue

from .cache import get_cache_key, get_cached_result, set_cached_result
from .generator import AlembicSqlGenerator
from .loader import AlembicMigration, AlembicMigrationLoader

if TYPE_CHECKING:
    pass


@dataclass
class LintResult:
    migration_revision: str
    filepath: Path
    errors: list[Issue]
    warnings: list[Issue]
    ignored: list[Issue]
    skipped: bool = False


class AlembicMigrationLinter:
    """Lints Alembic migrations for backward incompatibilities."""

    def __init__(
        self,
        config_path: str | Path,
        dialect: str = "postgresql",
        exclude_tests: list[str] | None = None,
        ignore_revision_contains: str | None = None,
        ignore_revisions: list[str] | None = None,
        no_cache: bool = False,
    ) -> None:
        self.config_path = Path(config_path)
        self.loader = AlembicMigrationLoader(self.config_path)
        self.dialect = dialect
        self.exclude_tests = exclude_tests or []
        self.analyser_class = get_sql_analyser_class(dialect)
        self.generator = AlembicSqlGenerator(Config(str(self.config_path)), dialect)
        self.ignore_revision_contains = ignore_revision_contains
        self.ignore_revisions = ignore_revisions or []
        self.no_cache = no_cache

    def lint_all(self, since_revision: str | None = None) -> list[LintResult]:
        """Lint all migrations, optionally filtering since a revision."""
        if since_revision is not None:
            migrations = self.loader.get_revisions_since(since_revision)
        else:
            migrations = self.loader.load()

        return [self.lint_migration(m) for m in migrations]

    def lint_migration(self, migration: AlembicMigration) -> LintResult:
        """Lint a single migration."""
        if self._should_skip(migration):
            return LintResult(
                migration_revision=migration.revision,
                filepath=migration.filepath,
                errors=[],
                warnings=[],
                ignored=[],
                skipped=True,
            )

        if not self.no_cache:
            cache_key = get_cache_key(migration.filepath, self.dialect)
            cached = get_cached_result(cache_key)
            if cached is not None:
                return cached  # type: ignore[return-value]

        sql_statements = self.generator.generate_sql(migration)
        errors, ignored, warnings = analyse_sql_statements(
            self.analyser_class,
            sql_statements,
            self.exclude_tests,
        )

        result = LintResult(
            migration_revision=migration.revision,
            filepath=migration.filepath,
            errors=errors,
            warnings=warnings,
            ignored=ignored,
        )

        if not self.no_cache:
            set_cached_result(cache_key, result)

        return result

    def _should_skip(self, migration: AlembicMigration) -> bool:
        """Check if a migration should be skipped."""
        if migration.revision in self.ignore_revisions:
            return True

        if self.ignore_revision_contains is not None:
            if self.ignore_revision_contains in migration.revision:
                return True
            if self.ignore_revision_contains in migration.filepath.name:
                return True

        return False
