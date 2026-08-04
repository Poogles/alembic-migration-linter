"""safe add column — expand phase of DROP_COLUMN safe pattern

Instead of dropping a column directly, stop writing to it in code.
In a later migration, drop the column after old code is fully retired.

This migration demonstrates the safe approach: just add the new
column without dropping the old one.

Revision ID: safe_add_column
Revises:
Create Date: 2024-01-01
"""

import sqlalchemy as sa
from alembic import op

revision = "safe_add_column"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(255)),
    )
    # Add new column instead of dropping old one
    op.add_column(
        "users",
        sa.Column("full_name", sa.String(255)),
    )


def downgrade():
    op.drop_column("users", "full_name")
    op.drop_table("users")
