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
            user = self.repo.get_user(request.email)
            if not user.check_password(request.password):
                raise Exception("Invalid password")
            access_token, _ = self.token_client.create_access_token(user)
            refresh_token, _ = self.token_client.create_refresh_token(user)
            return {"access": access_token, "refresh": refresh_token}
        except Exception as e:
            raise e
