"""safe add unique on new table — safe pattern for ADD_UNIQUE error

Adding a unique constraint when creating a new table is safe because
there are no existing rows to violate the constraint.

Revision ID: safe_add_unique_on_new_table
Revises:
Create Date: 2024-01-01
"""

import sqlalchemy as sa
from alembic import op

revision = "safe_add_unique_on_new_table"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False),
    )
    op.create_unique_constraint("uq_users_email", "users", ["email"])


def downgrade():
    op.drop_table("users")
