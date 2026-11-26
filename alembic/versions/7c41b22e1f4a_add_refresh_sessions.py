"""add rotating refresh-token session families

Revision ID: 7c41b22e1f4a
Revises: 59f1a6b72e04
Create Date: 2026-11-26
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "7c41b22e1f4a"
down_revision: Union[str, Sequence[str], None] = "59f1a6b72e04"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "refresh_sessions",
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("realm_id", sa.BigInteger(), nullable=False),
        sa.Column("client_id", sa.String(), nullable=True),
        sa.Column("family_id", sa.String(), nullable=False),
        sa.Column("token_id_hash", sa.String(), nullable=False),
        sa.Column("expires_at", sa.BigInteger(), nullable=False),
        sa.Column("rotated_at", sa.BigInteger(), nullable=True),
        sa.Column("revoked_at", sa.BigInteger(), nullable=True),
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column(
            "created_at", sa.BigInteger(),
            server_default=sa.text("EXTRACT(epoch FROM now())"), nullable=False,
        ),
        sa.Column(
            "updated_at", sa.BigInteger(),
            server_default=sa.text("EXTRACT(epoch FROM now())"), nullable=False,
        ),
        sa.ForeignKeyConstraint(["realm_id"], ["realms.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_id_hash"),
    )
    op.create_index("ix_refresh_sessions_id", "refresh_sessions", ["id"])
    op.create_index("ix_refresh_sessions_family_id", "refresh_sessions", ["family_id"])


def downgrade() -> None:
    op.drop_index("ix_refresh_sessions_family_id", table_name="refresh_sessions")
    op.drop_index("ix_refresh_sessions_id", table_name="refresh_sessions")
    op.drop_table("refresh_sessions")
