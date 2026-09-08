"""add refresh token rotation state

Revision ID: 19d08c61a2ef
Revises: 0e9d754423c6
Create Date: 2026-09-08
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "19d08c61a2ef"
down_revision: Union[str, Sequence[str], None] = "0e9d754423c6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("refresh_token_jti", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "refresh_token_jti")
