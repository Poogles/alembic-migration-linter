"""alter column type

Revision ID: 0007
Revises:
Create Date: 2024-01-01
"""

import sqlalchemy as sa
from alembic import op

revision = "alter_column"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "products",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(255)),
    )
    op.execute("ALTER TABLE products ALTER COLUMN name TYPE TEXT")


def downgrade():
    op.drop_table("products")
