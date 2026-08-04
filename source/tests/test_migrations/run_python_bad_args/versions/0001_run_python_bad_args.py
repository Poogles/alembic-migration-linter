"""function args not op

Revision ID: 0016
Revises:
Create Date: 2024-01-01
"""

import sqlalchemy as sa

revision = "run_python_bad_args"
down_revision = None
branch_labels = None
depends_on = None


def upgrade(alembic_op):
    alembic_op.create_table(
        "products",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("active", sa.Boolean()),
    )
    conn = alembic_op.get_bind()
    conn.execute(sa.text("UPDATE products SET active = true WHERE active IS NULL"))


def downgrade(alembic_op):
    alembic_op.drop_table("products")
