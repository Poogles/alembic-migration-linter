"""add server default

Revision ID: 0014
Revises:
Create Date: 2024-01-01
"""

import sqlalchemy as sa
from alembic import op

revision = "add_server_default"
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
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.func.now(),
        ),
    )


def downgrade():
    op.drop_column("products", "created_at")
    op.drop_table("products")
