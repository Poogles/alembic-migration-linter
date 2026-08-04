"""safe add column rename — expand phase of RENAME_COLUMN safe pattern

Instead of renaming a column directly, add a new column with the
desired name, backfill data, switch code to use the new column,
then drop the old column in a separate migration.

Revision ID: safe_add_column_rename
Revises:
Create Date: 2024-01-01
"""

import sqlalchemy as sa
from alembic import op

revision = "safe_add_column_rename"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(255)),
    )
    # Add new column with desired name instead of renaming
    op.add_column(
        "users",
        sa.Column("name", sa.String(255)),
    )
    # Backfill data from old column to new column
    op.execute("UPDATE users SET name = title")


def downgrade():
    op.drop_column("users", "name")
    op.drop_table("users")
