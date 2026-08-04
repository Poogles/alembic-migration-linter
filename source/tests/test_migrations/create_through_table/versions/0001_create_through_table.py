"""create through table

Revision ID: 0012
Revises:
Create Date: 2024-01-01
"""

import sqlalchemy as sa
from alembic import op

revision = "create_through_table"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "products",
        sa.Column("id", sa.Integer(), primary_key=True),
    )
    op.create_table(
        "tags",
        sa.Column("id", sa.Integer(), primary_key=True),
    )
    op.create_table(
        "product_tags",
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("tag_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
        sa.ForeignKeyConstraint(["tag_id"], ["tags.id"]),
    )


def downgrade():
    op.drop_table("product_tags")
    op.drop_table("tags")
    op.drop_table("products")
