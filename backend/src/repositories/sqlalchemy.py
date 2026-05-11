from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from src.db.models import Policy, Realm, Role, UserAccount


class SqlAlchemyRealmRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def find_by_name(self, name: str) -> Optional[Realm]:
        return self.db.scalar(select(Realm).where(Realm.name == name))

    def save(self, realm: Realm) -> Realm:
        self.db.add(realm)
        self.db.flush()
        return realm


class SqlAlchemyUserRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def find_by_realm_email(self, realm: str, email: str) -> Optional[UserAccount]:
        stmt = (
            select(UserAccount)
            .join(UserAccount.realm)
            .where(Realm.name == realm, UserAccount.email == email.lower())
            .options(selectinload(UserAccount.roles), selectinload(UserAccount.realm))
        )
        return self.db.scalar(stmt)

    def save(self, user: UserAccount) -> UserAccount:
        self.db.add(user)
        self.db.flush()
        return user


class SqlAlchemyRoleRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def find_by_realm_name(self, realm: Realm, name: str) -> Optional[Role]:
        return self.db.scalar(select(Role).where(Role.realm == realm, Role.name == name))

    def save(self, role: Role) -> Role:
        self.db.add(role)
        self.db.flush()
        return role


class SqlAlchemyPolicyRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def find_by_realm_name(self, realm: str, name: str) -> Optional[Policy]:
        stmt = select(Policy).join(Policy.realm).where(Realm.name == realm, Policy.name == name)
        return self.db.scalar(stmt)

    def find_by_realm_resource_action(self, realm: str, resource: str, action: str) -> list[Policy]:
        stmt = (
            select(Policy)
            .join(Policy.realm)
            .where(Realm.name == realm, Policy.resource == resource, Policy.action == action)
        )
        return list(self.db.scalars(stmt).all())

    def save(self, policy: Policy) -> Policy:
        self.db.add(policy)
        self.db.flush()
        return policy
