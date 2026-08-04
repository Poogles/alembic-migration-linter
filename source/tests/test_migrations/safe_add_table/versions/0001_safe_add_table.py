"""safe add table — expand phase of DROP_TABLE / RENAME_TABLE safe pattern

Instead of dropping or renaming a table directly, create the new
table alongside it. After deploying code that uses the new table,
drop the old table in a separate migration.

Revision ID: safe_add_table
Revises:
Create Date: 2024-01-01
"""

import sqlalchemy as sa
from alembic import op

revision = "safe_add_table"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Old table still exists — create new table alongside it
    op.create_table(
        "users_v2",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
    )


def downgrade():
    op.drop_table("users_v2")
