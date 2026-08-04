from __future__ import annotations

import io
from collections.abc import Callable

from alembic.config import Config
from alembic.operations import Operations
from alembic.runtime.environment import EnvironmentContext
from alembic.script import ScriptDirectory

from .loader import AlembicMigration


class AlembicSqlGenerator:
    """Renders Alembic migration operations into raw SQL."""

    def __init__(self, alembic_config: Config, dialect_name: str) -> None:
        self.config = alembic_config
        self.dialect_name = dialect_name

    def generate_sql(self, migration: AlembicMigration) -> list[str]:
        """Render the upgrade() operations of a migration into SQL statements."""
        return self._render_sql(migration, migration.upgrade_fn)

    def generate_downgrade_sql(self, migration: AlembicMigration) -> list[str]:
        """Render the downgrade() operations into SQL statements."""
        if migration.downgrade_fn is None:
            return []
        return self._render_sql(migration, migration.downgrade_fn)

    def _render_sql(
        self,
        migration: AlembicMigration,
        fn: Callable[..., None],
    ) -> list[str]:
        """Render a migration function into SQL statements."""
        url = f"{self.dialect_name}://user:pass@localhost/db"

        output = io.StringIO()
        script_dir = ScriptDirectory.from_config(self.config)

        env_ctx = EnvironmentContext(self.config, script_dir, as_sql=True)
        env_ctx.configure(
            url=url,
            dialect_name=self.dialect_name,
            output_buffer=output,
            literal_binds=False,
        )

        mc = env_ctx.get_context()
        with mc.begin_transaction(), Operations.context(mc):
            fn()

        sql = output.getvalue().strip()
        if not sql:
            return []

        return [stmt.strip() for stmt in sql.split(";") if stmt.strip()]
