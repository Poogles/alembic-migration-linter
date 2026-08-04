"""skip this migration

Revision ID: 0023
Revises:
Create Date: 2024-01-01
"""

import sqlalchemy as sa
from alembic import op

revision = "skip_this_migration"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "products",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("category", sa.String(100)),
    )
    op.drop_column("products", "category")


def downgrade():
    op.drop_table("products")
