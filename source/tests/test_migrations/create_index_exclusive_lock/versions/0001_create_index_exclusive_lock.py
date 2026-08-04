"""create index exclusive lock

Revision ID: 0020
Revises:
Create Date: 2024-01-01
"""

import sqlalchemy as sa
from alembic import op

revision = "create_index_exclusive_lock"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "products",
        sa.Column("category", sa.String(100)),
    )
    op.create_index("idx_products_category", "products", ["category"])


def downgrade():
    op.drop_index("idx_products_category", table_name="products")
    op.drop_column("products", "category")
