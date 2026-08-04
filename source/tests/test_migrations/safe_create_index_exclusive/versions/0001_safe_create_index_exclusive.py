"""safe create index exclusive — safe pattern for CREATE_INDEX_EXCLUSIVE warning

Split ALTER TABLE and CREATE INDEX into separate migrations to avoid
prolonging the exclusive lock.

Revision ID: safe_create_index_exclusive
Revises:
Create Date: 2024-01-01
"""

from alembic import op

revision = "safe_create_index_exclusive"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.execute("CREATE INDEX CONCURRENTLY idx_products_category ON products (category)")


def downgrade():
    op.execute("DROP INDEX CONCURRENTLY idx_products_category")
