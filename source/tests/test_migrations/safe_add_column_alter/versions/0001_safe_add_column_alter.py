"""safe add column alter — expand phase of ALTER_COLUMN safe pattern

Instead of altering a column's type directly, add a new column
with the desired type, backfill data, switch code, then drop the
old column in a separate migration.

Revision ID: safe_add_column_alter
Revises:
Create Date: 2024-01-01
"""

import sqlalchemy as sa
from alembic import op

revision = "safe_add_column_alter"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "products",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(255)),
    )
    # Add new column with desired type instead of altering
    op.add_column(
        "products",
        sa.Column("name_long", sa.Text()),
    )
    # Backfill data from old column to new column
    op.execute("UPDATE products SET name_long = name")


def downgrade():
    op.drop_column("products", "name_long")
    op.drop_table("products")
