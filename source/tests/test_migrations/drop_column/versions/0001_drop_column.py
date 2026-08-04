"""drop column

Revision ID: 0003
Revises:
Create Date: 2024-01-01
"""

import sqlalchemy as sa
from alembic import op

revision = "drop_column"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(255)),
    )
    op.drop_column("users", "email")


def downgrade():
    op.drop_table("users")
