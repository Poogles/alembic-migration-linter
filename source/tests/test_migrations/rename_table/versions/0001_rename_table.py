"""rename table

Revision ID: 0006
Revises:
Create Date: 2024-01-01
"""

import sqlalchemy as sa
from alembic import op

revision = "rename_table"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "items",
        sa.Column("id", sa.Integer(), primary_key=True),
    )
    op.rename_table("items", "products")


def downgrade():
    op.rename_table("products", "items")
