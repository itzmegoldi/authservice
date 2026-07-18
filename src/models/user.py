from sqlalchemy import Boolean, Column, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import relationship
from src.pkg.db import BaseModel
from src.pkg.security import hash_password, verify_password


class RealmModel(BaseModel):
    __tablename__ = "realms"
    name = Column(String, nullable=False, unique=True, default="master")

    users = relationship("UserModel", back_populates="realm")


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

    realm = relationship(RealmModel, back_populates="users")

    roles = relationship("RoleModel", secondary="user_roles", back_populates="users")
    groups = relationship("GroupModel", secondary="user_groups", back_populates="users")

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
