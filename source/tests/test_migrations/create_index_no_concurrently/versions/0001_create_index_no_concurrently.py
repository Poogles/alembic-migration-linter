"""create index no concurrently

Revision ID: 0019
Revises:
Create Date: 2024-01-01
"""

from alembic import op

revision = "create_index_no_concurrently"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_index("idx_products_sku", "products", ["sku"])


def downgrade():
    op.drop_index("idx_products_sku", table_name="products")
