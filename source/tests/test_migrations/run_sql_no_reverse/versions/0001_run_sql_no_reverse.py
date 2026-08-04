"""run sql no reverse

Revision ID: 0017
Revises:
Create Date: 2024-01-01
"""

import sqlalchemy as sa
from alembic import op

revision = "run_sql_no_reverse"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "products",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("active", sa.Boolean()),
    )
    op.execute("UPDATE products SET active = true WHERE active IS NULL")


def downgrade():
    op.drop_table("products")
