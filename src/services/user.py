from typing import Protocol

from src.builder.clients import Clients
from src.config.config import Config
from src.dto.user import BootstrapUser, UserCreateRequestDto, UserLoginRequest
from src.pkg import logging
from src.repositories.user import IUserRepository
from src.repositories.client import IClientRepository

logger = logging.get_logger()


class IUserService(Protocol):
    def create_user(self, request: UserCreateRequestDto) -> dict: ...
    def bootstrap(self): ...
    def login(self, request: UserLoginRequest) -> dict: ...
    def refresh(
        self,
        refresh_token: str,
        client_id: str | None = None,
        realm: str | None = None,
    ) -> dict: ...
    def refresh_cookie_max_age(self) -> int: ...
    def access_token_ttl_seconds(self) -> int: ...
    def oauth_password_grant(
        self,
        client_id: str,
        client_secret: str,
        realm: str,
        username: str,
        password: str,
    ) -> dict: ...
    def oauth_refresh_grant(
        self, client_id: str, client_secret: str, realm: str, refresh_token: str
    ) -> dict: ...


class UserService(IUserService):
    def __init__(self, config: Config, clients: Clients, repo: IUserRepository):
        self.config = config
        self.clients = clients
        self.repo = repo
        self.token_client = self.clients.token_client
        self.client_repo: IClientRepository | None = None

    def with_client_repository(self, client_repo: IClientRepository):
        self.client_repo = client_repo
        return self

    def bootstrap(self):
        try:
            adminuser = BootstrapUser(
                email=self.config.auth.bootstrap.admin_email,
                password=self.config.auth.bootstrap.admin_password,
                is_admin=True,
                is_active=True,
            )
            self.repo.bootstrap(adminuser)
        except Exception as e:
            raise e

    def create_user(self, request: UserCreateRequestDto):
        return self.repo.create_user(request)

    def login(self, request: UserLoginRequest):
        try:
            user = self.repo.get_user(request.email, is_admin=True)
            if not user:
                raise Exception("User not found")
            if not user.check_password(request.password):
                raise Exception("Invalid password")
            if not user.is_active:
                raise ValueError("User is inactive")
            return self._issue_token_pair(user)
        except Exception as e:
            raise e

    def refresh(
        self,
        refresh_token: str,
        client_id: str | None = None,
        realm: str | None = None,
    ) -> dict:
        try:
            claims = self.token_client.decode_refresh_token(refresh_token)
            if claims.get("typ") != "refresh":
                raise ValueError("A refresh token is required")
            if claims.get("client_id") != client_id:
                raise ValueError("Refresh token was not issued to this client")
            if realm is not None and claims.get("realm") != realm:
                raise ValueError("Refresh token was not issued to this realm")

            user_id = int(claims["sub"])
            old_token_id = claims["jti"]
            user = self.repo.get_user_by_id(user_id)
            if not user or not user.is_active:
                raise ValueError("User is not available")
            if claims.get("realm") != user.realm.name:
                raise ValueError("Refresh token realm does not match the user")

            access_token, _ = self.token_client.create_access_token(user, client_id)
            new_refresh_token, _, new_token_id = self.token_client.create_refresh_token(
                user, client_id=client_id, realm=claims.get("realm")
            )
            if not self.repo.rotate_refresh_token_jti(
                user.id, old_token_id, new_token_id
            ):
                raise ValueError("Refresh token has already been used or revoked")

            return {"access": access_token, "refresh": new_refresh_token}
        except Exception as e:
            raise e

    def refresh_cookie_max_age(self) -> int:
        return self.config.auth.refresh_token_ttl_days * 24 * 60 * 60

    def access_token_ttl_seconds(self) -> int:
        return self.config.auth.token_ttl_minutes * 60

    def oauth_password_grant(
        self,
        client_id: str,
        client_secret: str,
        realm: str,
        username: str,
        password: str,
    ) -> dict:
        self._validate_oauth_client(client_id, client_secret, realm, "password")
        user = self.repo.get_user(username, realm_name=realm)
        if not user or not user.check_password(password) or not user.is_active:
            raise ValueError("Invalid resource owner credentials")
        return self._issue_token_pair(user, client_id=client_id, realm=realm)

    def oauth_refresh_grant(
        self, client_id: str, client_secret: str, realm: str, refresh_token: str
    ) -> dict:
        self._validate_oauth_client(client_id, client_secret, realm, "refresh_token")
        return self.refresh(refresh_token, client_id=client_id, realm=realm)

    def _validate_oauth_client(
        self, client_id: str, client_secret: str, realm: str, grant_type: str
    ) -> None:
        if not self.client_repo:
            raise RuntimeError("Client repository has not been configured")
        client = self.client_repo.get_client(client_id, realm)
        if (
            not client
            or not client.is_active
            or not client.check_secret(client_secret)
            or grant_type not in client.allowed_grant_types
        ):
            raise PermissionError("Invalid OAuth client credentials")

    def _issue_token_pair(
        self, user, client_id: str | None = None, realm: str | None = None
    ) -> dict:
        access_token, _ = self.token_client.create_access_token(user, client_id)
        refresh_token, _, token_id = self.token_client.create_refresh_token(
            user, client_id=client_id, realm=realm or user.realm.name
        )
        self.repo.set_refresh_token_jti(user.id, token_id)
        return {"access": access_token, "refresh": refresh_token}
