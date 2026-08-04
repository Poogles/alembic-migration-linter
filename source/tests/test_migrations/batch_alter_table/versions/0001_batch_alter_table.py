"""batch alter table with not null

Revision ID: batch_alter_table
Revises:
Create Date: 2024-01-01
"""

import sqlalchemy as sa
from alembic import op

revision = "batch_alter_table"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(100)),
    )
    with op.batch_alter_table("items") as batch_op:
        batch_op.alter_column("name", nullable=False)


def downgrade():
    op.drop_table("items")
