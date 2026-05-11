from __future__ import annotations

from src.config.config import Config
from src.db.models import Policy, Realm, Role, UserAccount
from src.pkg.security import hash_password
from src.repositories.interfaces import PolicyRepository, RealmRepository, RoleRepository, UserRepository


class BootstrapService:
    def __init__(
        self,
        config: Config,
        realms: RealmRepository,
        roles: RoleRepository,
        users: UserRepository,
        policies: PolicyRepository,
    ) -> None:
        self.config = config
        self.realms = realms
        self.roles = roles
        self.users = users
        self.policies = policies

    def ensure_default_realm(self) -> None:
        realm = self.realms.find_by_name("master")
        if realm is None:
            realm = self.realms.save(Realm(name="master", display_name="Master Realm"))

        admin_role = self.roles.find_by_realm_name(realm, "admin")
        if admin_role is None:
            admin_role = self.roles.save(Role(realm=realm, name="admin", description="Realm administrator"))

        user_role = self.roles.find_by_realm_name(realm, "user")
        if user_role is None:
            self.roles.save(Role(realm=realm, name="user", description="Default application user"))

        admin_email = self.config.auth.bootstrap.admin_email.lower()
        admin = self.users.find_by_realm_email("master", admin_email)
        if admin is None:
            admin = UserAccount(
                realm=realm,
                email=admin_email,
                password_hash=hash_password(self.config.auth.bootstrap.admin_password),
                attributes_json={"department": "platform", "clearance": "high"},
            )
            admin.roles.append(admin_role)
            self.users.save(admin)

        policy = self.policies.find_by_realm_name("master", "admins-manage-integrations")
        if policy is None:
            self.policies.save(
                Policy(
                    realm=realm,
                    name="admins-manage-integrations",
                    resource="integration",
                    action="verify",
                    effect="ALLOW",
                    condition_json={"role": "admin"},
                )
            )
