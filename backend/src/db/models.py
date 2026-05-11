from __future__ import annotations

from datetime import datetime, timezone
import json
from typing import Any, Optional

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.types import TypeDecorator


class Base(DeclarativeBase):
    pass


class JsonText(TypeDecorator):
    impl = Text
    cache_ok = True

    def process_bind_param(self, value: Any, dialect: Any) -> str:
        return json.dumps(value or {})

    def process_result_value(self, value: Optional[str], dialect: Any) -> Any:
        if not value:
            return {}
        return json.loads(value)


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


class Realm(Base):
    __tablename__ = "realms"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, nullable=False)

    users: Mapped[list["UserAccount"]] = relationship(back_populates="realm")
    roles: Mapped[list["Role"]] = relationship(back_populates="realm")
    policies: Mapped[list["Policy"]] = relationship(back_populates="realm")


class UserRole(Base):
    __tablename__ = "user_roles"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"), primary_key=True)


class UserAccount(Base):
    __tablename__ = "users"
    __table_args__ = (UniqueConstraint("realm_id", "email"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    realm_id: Mapped[int] = mapped_column(ForeignKey("realms.id"), nullable=False)
    email: Mapped[str] = mapped_column(String, nullable=False)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, default="ACTIVE", nullable=False)
    attributes_json: Mapped[dict[str, Any]] = mapped_column(JsonText, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, nullable=False)

    realm: Mapped[Realm] = relationship(back_populates="users")
    roles: Mapped[list["Role"]] = relationship(secondary="user_roles", back_populates="users", lazy="selectin")


class Role(Base):
    __tablename__ = "roles"
    __table_args__ = (UniqueConstraint("realm_id", "name"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    realm_id: Mapped[int] = mapped_column(ForeignKey("realms.id"), nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String)

    realm: Mapped[Realm] = relationship(back_populates="roles")
    users: Mapped[list[UserAccount]] = relationship(secondary="user_roles", back_populates="roles")


class Policy(Base):
    __tablename__ = "policies"
    __table_args__ = (UniqueConstraint("realm_id", "name"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    realm_id: Mapped[int] = mapped_column(ForeignKey("realms.id"), nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    resource: Mapped[str] = mapped_column(String, nullable=False)
    action: Mapped[str] = mapped_column(String, nullable=False)
    effect: Mapped[str] = mapped_column(String, nullable=False)
    condition_json: Mapped[dict[str, Any]] = mapped_column(JsonText, default=dict, nullable=False)

    realm: Mapped[Realm] = relationship(back_populates="policies")


class Client(Base):
    __tablename__ = "clients"
    __table_args__ = (UniqueConstraint("realm_id", "client_id"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    realm_id: Mapped[int] = mapped_column(ForeignKey("realms.id"), nullable=False)
    client_id: Mapped[str] = mapped_column(String, nullable=False)
    client_secret_hash: Mapped[str] = mapped_column(String, nullable=False)
    service_account_user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, nullable=False)


class ApiKey(Base):
    __tablename__ = "api_keys"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    realm_id: Mapped[int] = mapped_column(ForeignKey("realms.id"), nullable=False)
    owner_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    key_hash: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, nullable=False)
