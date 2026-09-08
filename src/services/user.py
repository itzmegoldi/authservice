from typing import Protocol

from src.builder.clients import Clients
from src.config.config import Config
from src.dto.user import BootstrapUser, UserCreateRequestDto, UserLoginRequest
from src.pkg import logging
from src.repositories.user import IUserRepository

logger = logging.get_logger()


class IUserService(Protocol):
    def create_user(self, request: UserCreateRequestDto) -> dict: ...
    def bootstrap(self): ...
    def login(self, request: UserLoginRequest) -> dict: ...
    def refresh(self, refresh_token: str) -> dict: ...
    def refresh_cookie_max_age(self) -> int: ...


class UserService(IUserService):
    def __init__(self, config: Config, clients: Clients, repo: IUserRepository):
        self.config = config
        self.clients = clients
        self.repo = repo
        self.token_client = self.clients.token_client

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

    def refresh(self, refresh_token: str) -> dict:
        try:
            claims = self.token_client.decode_refresh_token(refresh_token)
            if claims.get("typ") != "refresh":
                raise ValueError("A refresh token is required")

            user_id = int(claims["sub"])
            old_token_id = claims["jti"]
            user = self.repo.get_user_by_id(user_id)
            if not user or not user.is_active:
                raise ValueError("User is not available")

            access_token, _ = self.token_client.create_access_token(user)
            new_refresh_token, _, new_token_id = self.token_client.create_refresh_token(user)
            if not self.repo.rotate_refresh_token_jti(
                user.id, old_token_id, new_token_id
            ):
                raise ValueError("Refresh token has already been used or revoked")

            return {"access": access_token, "refresh": new_refresh_token}
        except Exception as e:
            raise e

    def refresh_cookie_max_age(self) -> int:
        return self.config.auth.refresh_token_ttl_days * 24 * 60 * 60

    def _issue_token_pair(self, user) -> dict:
        access_token, _ = self.token_client.create_access_token(user)
        refresh_token, _, token_id = self.token_client.create_refresh_token(user)
        self.repo.set_refresh_token_jti(user.id, token_id)
        return {"access": access_token, "refresh": refresh_token}
