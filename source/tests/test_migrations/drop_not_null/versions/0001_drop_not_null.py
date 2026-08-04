"""drop not null

Revision ID: 0011
Revises:
Create Date: 2024-01-01
"""

import sqlalchemy as sa
from alembic import op

revision = "drop_not_null"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "products",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("sku", sa.String(50), nullable=False),
    )
    op.execute("ALTER TABLE products ALTER COLUMN sku DROP NOT NULL")


def downgrade():
    op.drop_table("products")
