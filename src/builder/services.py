from src.builder.clients import Clients
from src.config.config import Config
from src.repositories.user import IUserRepository
from src.services.user import IUserService, UserService
from src.repositories.client import IClientRepository
from src.services.client import ClientService, IClientService


class Services:
    def with_user_service(
        self, config: Config, clients: Clients, repo: IUserRepository
    ):
        # pylint: disable=attribute-defined-outside-init
        self.user_service: IUserService = UserService(
            config=config, clients=clients, repo=repo
        )
        return self

    def with_client_service(self, repo: IClientRepository):
        # pylint: disable=attribute-defined-outside-init
        self.client_service: IClientService = ClientService(repo=repo)
        return self
