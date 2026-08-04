"""raw sql with drop column via execute

Revision ID: raw_sql
Revises:
Create Date: 2024-01-01
"""

import sqlalchemy as sa
from alembic import op

revision = "raw_sql"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "products",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("description", sa.Text()),
    )
    op.execute("ALTER TABLE products DROP COLUMN description")


def downgrade():
    op.drop_table("products")
