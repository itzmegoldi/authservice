from sqlalchemy import Boolean, Column, ForeignKey, Integer, JSON, String, UniqueConstraint
from sqlalchemy.orm import relationship
from src.pkg.db import BaseModel
from src.pkg.security import hash_password, verify_password


class RealmModel(BaseModel):
    __tablename__ = "realms"
    name = Column(String, nullable=False, unique=True, default="master")

    users = relationship("UserModel", back_populates="realm")
    clients = relationship("ClientModel", back_populates="realm")


class UserModel(BaseModel):
    __tablename__ = "users"
    email = Column(String, nullable=False, unique=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    password = Column(String, nullable=True)
    attributes = Column(JSON, default=dict)
    realm_id = Column(ForeignKey("realms.id"), nullable=False)
    is_admin = Column(Boolean, nullable=False, default=False)
    is_active = Column(Boolean, nullable=False, default=True)
    refresh_token_jti = Column(String, nullable=True)
    google_subject = Column(String, nullable=True, unique=True)

    realm = relationship(RealmModel, back_populates="users")

    roles = relationship("RoleModel", secondary="user_roles", back_populates="users")
    groups = relationship("GroupModel", secondary="user_groups", back_populates="users")
    client_roles = relationship(
        "ClientRoleModel", secondary="user_client_roles", back_populates="users"
    )

    def set_password(self, password):
        self.password = hash_password(password)

    def check_password(self, password):
        return verify_password(password, self.password)


class RoleModel(BaseModel):
    __tablename__ = "roles"
    name = Column(String, nullable=False, unique=True)

    users = relationship("UserModel", secondary="user_roles", back_populates="roles")
    groups = relationship("GroupModel", secondary="group_roles", back_populates="roles")


class GroupModel(BaseModel):
    __tablename__ = "groups"
    name = Column(String, nullable=False, unique=True)

    roles = relationship("RoleModel", secondary="group_roles", back_populates="groups")
    users = relationship("UserModel", secondary="user_groups", back_populates="groups")


class UserRoleModel(BaseModel):
    __tablename__ = "user_roles"
    user_id = Column(ForeignKey("users.id"), nullable=False)
    role_id = Column(ForeignKey("roles.id"), nullable=False)


class UserGroupModel(BaseModel):
    __tablename__ = "user_groups"
    user_id = Column(ForeignKey("users.id"), nullable=False)
    group_id = Column(ForeignKey("groups.id"), nullable=False)


class GroupRoleModel(BaseModel):
    __tablename__ = "group_roles"
    group_id = Column(ForeignKey("groups.id"), nullable=False)
    role_id = Column(ForeignKey("roles.id"), nullable=False)


class ClientModel(BaseModel):
    __tablename__ = "clients"

    client_id = Column(String, nullable=False, unique=True)
    client_secret_hash = Column(String, nullable=False)
    name = Column(String, nullable=False)
    realm_id = Column(ForeignKey("realms.id"), nullable=False)
    attributes = Column(JSON, default=dict)
    allowed_grant_types = Column(
        JSON, nullable=False, default=lambda: ["password", "refresh_token"]
    )
    is_active = Column(Boolean, nullable=False, default=True)

    roles = relationship(
        "ClientRoleModel", back_populates="client", cascade="all, delete-orphan"
    )
    realm = relationship("RealmModel", back_populates="clients")

    def set_secret(self, secret: str):
        self.client_secret_hash = hash_password(secret)

    def check_secret(self, secret: str) -> bool:
        return verify_password(secret, self.client_secret_hash)


class ClientRoleModel(BaseModel):
    __tablename__ = "client_roles"
    __table_args__ = (
        UniqueConstraint("client_id", "name", name="uq_client_roles_client_id_name"),
    )

    client_id = Column(ForeignKey("clients.id"), nullable=False)
    name = Column(String, nullable=False)
    attributes = Column(JSON, default=dict)

    client = relationship("ClientModel", back_populates="roles")
    users = relationship(
        "UserModel", secondary="user_client_roles", back_populates="client_roles"
    )


class UserClientRoleModel(BaseModel):
    __tablename__ = "user_client_roles"
    __table_args__ = (
        UniqueConstraint(
            "user_id", "client_role_id", name="uq_user_client_roles_user_role"
        ),
    )

    user_id = Column(ForeignKey("users.id"), nullable=False)
    client_role_id = Column(ForeignKey("client_roles.id"), nullable=False)
