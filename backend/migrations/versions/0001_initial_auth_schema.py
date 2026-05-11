from __future__ import annotations

"""initial auth schema

Revision ID: 0001
Revises:
Create Date: 2026-05-09 00:00:00.000000
"""

from collections.abc import Sequence
from typing import Optional, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0001"
down_revision: Optional[str] = None
branch_labels: Optional[Union[str, Sequence[str]]] = None
depends_on: Optional[Union[str, Sequence[str]]] = None


def upgrade() -> None:
    op.create_table(
        "realms",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(), nullable=False, unique=True),
        sa.Column("display_name", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("realm_id", sa.Integer(), sa.ForeignKey("realms.id"), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("password_hash", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("attributes_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("realm_id", "email"),
    )
    op.create_table(
        "roles",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("realm_id", sa.Integer(), sa.ForeignKey("realms.id"), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.String()),
        sa.UniqueConstraint("realm_id", "name"),
    )
    op.create_table(
        "user_roles",
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), primary_key=True),
        sa.Column("role_id", sa.Integer(), sa.ForeignKey("roles.id"), primary_key=True),
    )
    op.create_table(
        "policies",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("realm_id", sa.Integer(), sa.ForeignKey("realms.id"), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("resource", sa.String(), nullable=False),
        sa.Column("action", sa.String(), nullable=False),
        sa.Column("effect", sa.String(), nullable=False),
        sa.Column("condition_json", sa.Text(), nullable=False),
        sa.UniqueConstraint("realm_id", "name"),
    )
    op.create_table(
        "clients",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("realm_id", sa.Integer(), sa.ForeignKey("realms.id"), nullable=False),
        sa.Column("client_id", sa.String(), nullable=False),
        sa.Column("client_secret_hash", sa.String(), nullable=False),
        sa.Column("service_account_user_id", sa.Integer(), sa.ForeignKey("users.id")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("realm_id", "client_id"),
    )
    op.create_table(
        "api_keys",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("realm_id", sa.Integer(), sa.ForeignKey("realms.id"), nullable=False),
        sa.Column("owner_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("key_hash", sa.String(), nullable=False, unique=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("api_keys")
    op.drop_table("clients")
    op.drop_table("policies")
    op.drop_table("user_roles")
    op.drop_table("roles")
    op.drop_table("users")
    op.drop_table("realms")
