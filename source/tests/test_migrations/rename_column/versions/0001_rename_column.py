"""rename column

Revision ID: 0005
Revises:
Create Date: 2024-01-01
"""

import sqlalchemy as sa
from alembic import op

revision = "rename_column"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(255)),
    )
    op.execute("ALTER TABLE items RENAME COLUMN title TO name")


def downgrade():
    op.drop_table("items")
