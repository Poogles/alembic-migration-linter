"""reindex

Revision ID: 0022
Revises:
Create Date: 2024-01-01
"""

from alembic import op

revision = "reindex"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.execute("REINDEX TABLE products")


def downgrade():
    pass
