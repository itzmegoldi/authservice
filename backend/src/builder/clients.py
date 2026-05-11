from typing_extensions import Self

from src.clients.jwt_client import JwtClient
from src.clients.kafka_client import KafkaMessageClient
from src.config.config import Config
from src.pkg.db import SqliteDbHandler


class Clients:

    def with_db_handler(self, config: Config) -> Self:
        # pylint: disable=attribute-defined-outside-init
        self.db_handler = SqliteDbHandler(config=config.database)
        return self

    def with_token_client(self, config: Config) -> Self:
        # pylint: disable=attribute-defined-outside-init
        self.token_client = JwtClient(config=config)
        return self

    def with_message_client(self, config: Config) -> Self:
        # pylint: disable=attribute-defined-outside-init
        self.message_client = KafkaMessageClient(config=config)
        return self

    def close(self):
        self.message_client.close()

