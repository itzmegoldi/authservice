from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from src.clients.interfaces import TokenClient
from src.pkg.security import hash_password, verify_password
from src.db.models import Role, UserAccount
from src.repositories.interfaces import RealmRepository, RoleRepository, UserRepository
from src.api.v1.schemas import RegisterRequest, TokenResponse


class AuthService:
    def __init__(
        self,
        db: Session,
        token_client: TokenClient,
        realms: RealmRepository,
        users: UserRepository,
        roles: RoleRepository,
    ) -> None:
        self.db = db
        self.token_client = token_client
        self.realms = realms
        self.users = users
        self.roles = roles

    def register(self, request: RegisterRequest) -> TokenResponse:
        realm = self.realms.find_by_name(request.realm)
        if realm is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown realm")
        if self.users.find_by_realm_email(request.realm, request.email):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already exists")

        user = UserAccount(
            realm=realm,
            email=request.email.lower(),
            password_hash=hash_password(request.password),
            attributes_json=request.attributes or {},
        )
        role = self.roles.find_by_realm_name(realm, "user")
        if role is None:
            role = self.roles.save(Role(realm=realm, name="user", description="Default application user"))
        user.roles.append(role)
        self.users.save(user)
        self.db.commit()
        self.db.refresh(user)
        return self._token_response(user)

    def login(self, realm: str, email: str, password: str) -> TokenResponse:
        user = self.users.find_by_realm_email(realm, email)
        if user is None or user.status != "ACTIVE" or not verify_password(password, user.password_hash):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        return self._token_response(user)

    def _token_response(self, user: UserAccount) -> TokenResponse:
        token, expires_at, roles = self.token_client.create_access_token(user)
        return TokenResponse(
            access_token=token,
            token_type="Bearer",
            expires_at=expires_at.isoformat(),
            roles=roles,
        )
