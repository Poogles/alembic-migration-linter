"""add not null column without default

Revision ID: 0002
Revises:
Create Date: 2024-01-01
"""

import sqlalchemy as sa
from alembic import op

revision = "add_not_null_column"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
    )
    op.add_column(
        "users",
        sa.Column("age", sa.Integer(), nullable=False),
    )


def downgrade():
    op.drop_column("users", "age")
    op.drop_table("users")
