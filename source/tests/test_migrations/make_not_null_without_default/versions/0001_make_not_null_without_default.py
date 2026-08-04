"""make not null without default

Revision ID: 0009
Revises:
Create Date: 2024-01-01
"""

import sqlalchemy as sa
from alembic import op

revision = "make_not_null_without_default"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "products",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("sku", sa.String(50)),
    )
    op.execute("ALTER TABLE products ALTER COLUMN sku SET NOT NULL")


def downgrade():
    op.drop_table("products")
