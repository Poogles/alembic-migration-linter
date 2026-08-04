"""add engine_versions table — uses sa.inspect(conn)

Revision ID: 044f1bdcbf1c
Revises:
Create Date: 2025-08-13 17:26:39.971205
"""

import sqlalchemy as sa
from alembic import op

revision = "044f1bdcbf1c"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "engine_versions",
        sa.Column("id", sa.String(length=255), nullable=False),
        sa.Column("engine_version", sa.String(length=255), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    conn = op.get_bind()
    inspector = sa.inspect(conn)
    constraints = [fk["name"] for fk in inspector.get_foreign_keys("engine_versions")]
    if "fk_old" in constraints:
        op.drop_constraint("fk_old", "engine_versions", type_="foreignkey")


def downgrade() -> None:
    op.drop_table("engine_versions")
