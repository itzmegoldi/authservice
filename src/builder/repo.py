from src.pkg.db import IHandler
from src.repositories.user import IUserRepository, UserRepository


class Repos:
    def with_user_repository(self, db_handler: IHandler):
        # pylint: disable=attribute-defined-outside-init
        self.user_repository: IUserRepository = UserRepository(db_handler=db_handler)
        return self
