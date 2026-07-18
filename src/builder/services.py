from src.builder.clients import Clients
from src.config.config import Config
from src.repositories.user import IUserRepository
from src.services.user import IUserService, UserService


class Services:
    def with_user_service(
        self, config: Config, clients: Clients, repo: IUserRepository
    ):
        # pylint: disable=attribute-defined-outside-init
        self.user_service: IUserService = UserService(
            config=config, clients=clients, repo=repo
        )
        return self
