"""add not null then default

Revision ID: 0013
Revises:
Create Date: 2024-01-01
"""

import sqlalchemy as sa
from alembic import op

revision = "add_not_null_then_default"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "products",
        sa.Column("id", sa.Integer(), primary_key=True),
    )
    op.add_column(
        "products",
        sa.Column("description", sa.Text(), nullable=True),
    )
    op.execute("ALTER TABLE products ALTER COLUMN description SET NOT NULL")
    op.execute("ALTER TABLE products ALTER COLUMN description SET DEFAULT ''")


def downgrade():
    op.drop_column("products", "description")
    op.drop_table("products")
