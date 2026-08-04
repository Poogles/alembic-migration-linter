"""drop index no concurrently

Revision ID: 0021
Revises:
Create Date: 2024-01-01
"""

from alembic import op

revision = "drop_index_no_concurrently"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.drop_index("idx_products_sku", table_name="products")


def downgrade():
    op.create_index("idx_products_sku", "products", ["sku"])
