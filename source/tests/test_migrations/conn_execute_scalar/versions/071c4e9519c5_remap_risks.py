"""remap risks to latest engine — uses conn.execute().scalar()

Revision ID: 071c4e9519c5
Revises:
Create Date: 2026-03-12 13:14:01.441981
"""

import sqlalchemy as sa
from alembic import op

revision = "071c4e9519c5"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    team = "COWW"

    latest_engine_id = conn.execute(
        sa.text(
            """
            SELECT id
            FROM engine_versions
            WHERE underwriting_team_business_code = :team
              AND is_active = true
              AND is_deployed = true
              AND is_primary = true
            ORDER BY effective_from DESC, id DESC
            LIMIT 1
            """
        ),
        {"team": team},
    ).scalar()

    if latest_engine_id is None:
        return

    conn.execute(
        sa.text(
            """
            UPDATE engine_versions
            SET is_active = true,
                is_deployed = true
            WHERE id = :target_engine_id
            """
        ),
        {"target_engine_id": latest_engine_id},
    )

    conn.execute(
        sa.text(
            """
            UPDATE risk
            SET engine_version_id = :target_engine_id
            WHERE engine_version_id <> :target_engine_id
            """
        ),
        {"target_engine_id": latest_engine_id},
    )


def downgrade() -> None:
    return None
