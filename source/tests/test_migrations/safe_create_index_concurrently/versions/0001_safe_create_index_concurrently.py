"""safe create index concurrently — safe pattern for CREATE_INDEX warning

Use CONCURRENTLY to avoid locking the table during index creation.
Must be run outside a transaction block.

Revision ID: safe_create_index_concurrently
Revises:
Create Date: 2024-01-01
"""

from alembic import op

revision = "safe_create_index_concurrently"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.execute("CREATE INDEX CONCURRENTLY idx_products_sku ON products (sku)")


def downgrade():
    op.execute("DROP INDEX CONCURRENTLY idx_products_sku")
