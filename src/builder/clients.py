from src.clients.jwt_client import JwtClient
from src.clients.google_client import GoogleClient
from src.config.config import Config
from src.pkg.db import IHandler, PostgresDbHandler
from typing_extensions import Self


class Clients:

    def with_db_handler(self, config: Config) -> Self:
        # pylint: disable=attribute-defined-outside-init
        self.db_handler: IHandler = PostgresDbHandler(config=config.database)
        return self

    def with_token_client(self, config: Config) -> Self:
        # pylint: disable=attribute-defined-outside-init
        self.token_client = JwtClient(config=config)
        return self

    def with_google_client(self) -> Self:
        # pylint: disable=attribute-defined-outside-init
        self.google_client = GoogleClient()
        return self
