"""scope OAuth clients to realms

Revision ID: 2d6e4f98a1c3
Revises: 8a4c0d17b5e3
Create Date: 2026-09-08
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op


revision: str = "2d6e4f98a1c3"
down_revision: Union[str, Sequence[str], None] = "8a4c0d17b5e3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("clients", sa.Column("realm_id", sa.BigInteger(), nullable=True))
    op.execute(
        "UPDATE clients SET realm_id = "
        "(SELECT id FROM realms WHERE name = 'master') "
        "WHERE realm_id IS NULL"
    )
    op.create_foreign_key(
        "fk_clients_realm_id_realms", "clients", "realms", ["realm_id"], ["id"]
    )
    op.alter_column("clients", "realm_id", nullable=False)


def downgrade() -> None:
    op.drop_constraint("fk_clients_realm_id_realms", "clients", type_="foreignkey")
    op.drop_column("clients", "realm_id")
