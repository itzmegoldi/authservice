from __future__ import annotations

from typing import Optional, Protocol

from src.db.models import Policy, Realm, Role, UserAccount


class RealmRepository(Protocol):
    def find_by_name(self, name: str) -> Optional[Realm]:
        ...

    def save(self, realm: Realm) -> Realm:
        ...


class UserRepository(Protocol):
    def find_by_realm_email(self, realm: str, email: str) -> Optional[UserAccount]:
        ...

    def save(self, user: UserAccount) -> UserAccount:
        ...


class RoleRepository(Protocol):
    def find_by_realm_name(self, realm: Realm, name: str) -> Optional[Role]:
        ...

    def save(self, role: Role) -> Role:
        ...


class PolicyRepository(Protocol):
    def find_by_realm_name(self, realm: str, name: str) -> Optional[Policy]:
        ...

    def find_by_realm_resource_action(self, realm: str, resource: str, action: str) -> list[Policy]:
        ...

    def save(self, policy: Policy) -> Policy:
        ...
