"""add unique constraint

Revision ID: 0008
Revises:
Create Date: 2024-01-01
"""

from alembic import op

revision = "add_unique_constraint"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_unique_constraint("uq_products_sku", "products", ["sku"])


def downgrade():
    op.drop_constraint("uq_products_sku", "products", type_="unique")
