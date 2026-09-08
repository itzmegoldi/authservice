"""add OAuth clients and client roles

Revision ID: 8a4c0d17b5e3
Revises: 19d08c61a2ef
Create Date: 2026-09-08
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "8a4c0d17b5e3"
down_revision: Union[str, Sequence[str], None] = "19d08c61a2ef"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "clients",
        sa.Column("client_id", sa.String(), nullable=False),
        sa.Column("client_secret_hash", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("attributes", sa.JSON(), nullable=True),
        sa.Column("allowed_grant_types", sa.JSON(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column(
            "created_at",
            sa.BigInteger(),
            server_default=sa.text("EXTRACT(epoch FROM now())"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.BigInteger(),
            server_default=sa.text("EXTRACT(epoch FROM now())"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("client_id"),
    )
    op.create_index(op.f("ix_clients_id"), "clients", ["id"], unique=False)
    op.create_table(
        "client_roles",
        sa.Column("client_id", sa.BigInteger(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("attributes", sa.JSON(), nullable=True),
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column(
            "created_at",
            sa.BigInteger(),
            server_default=sa.text("EXTRACT(epoch FROM now())"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.BigInteger(),
            server_default=sa.text("EXTRACT(epoch FROM now())"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["client_id"], ["clients.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("client_id", "name", name="uq_client_roles_client_id_name"),
    )
    op.create_index(op.f("ix_client_roles_id"), "client_roles", ["id"], unique=False)
    op.create_table(
        "user_client_roles",
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("client_role_id", sa.BigInteger(), nullable=False),
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column(
            "created_at",
            sa.BigInteger(),
            server_default=sa.text("EXTRACT(epoch FROM now())"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.BigInteger(),
            server_default=sa.text("EXTRACT(epoch FROM now())"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["client_role_id"], ["client_roles.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "client_role_id", name="uq_user_client_roles_user_role"),
    )
    op.create_index(op.f("ix_user_client_roles_id"), "user_client_roles", ["id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_user_client_roles_id"), table_name="user_client_roles")
    op.drop_table("user_client_roles")
    op.drop_index(op.f("ix_client_roles_id"), table_name="client_roles")
    op.drop_table("client_roles")
    op.drop_index(op.f("ix_clients_id"), table_name="clients")
    op.drop_table("clients")
