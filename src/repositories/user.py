from typing import Protocol

from sqlalchemy.orm import joinedload

from src.dto.user import BootstrapUser, UserCreateRequestDto

from src.models.user import RealmModel, UserModel
from src.pkg.db import IHandler


class IUserRepository(Protocol):

    def bootstrap(self, request: BootstrapUser): ...
    def create_user(self, request: UserCreateRequestDto): ...
    def get_user(self, email: str): ...


class UserRepository(IUserRepository):
    def __init__(self, db_handler: IHandler):
        self.db_handler = db_handler

    def bootstrap(self, request: BootstrapUser):
        try:
            realm = self.__ensure_master_realm()
            self.__ensure_admin_user(realm, request)
        except Exception as e:
            raise e

    def __ensure_master_realm(self):
        with self.db_handler.get_session() as session:
            realm = (
                session.query(RealmModel).filter(RealmModel.name == "master").first()
            )
            if not realm:
                realm = RealmModel(name="master")
                session.add(realm)
                session.commit()
            return realm

    def __ensure_admin_user(self, realm: RealmModel, request: BootstrapUser):
        with self.db_handler.get_session() as session:
            user = (
                session.query(UserModel)
                .filter(UserModel.email == request.email)
                .first()
            )
            if not user:
                user = UserModel(
                    email=request.email,
                    is_admin=request.is_admin,
                    is_active=request.is_active,
                    realm_id=realm.id,
                )
                user.set_password(request.password)
                session.add(user)
                session.commit()

    def create_user(self, request: UserCreateRequestDto):
        with self.db_handler.get_session() as session:
            user = UserModel(
                **request.model_dump(),
            )
            user.set_password(request.password)
            session.add(user)
            session.commit()
            return user

    def get_user(self, email):
        try:
            params = {"email": email}

            filter_params = []
            for key, value in params.items():
                filter_params.append(getattr(UserModel, key) == value)

            with self.db_handler.get_session() as session:
                return (
                    session.query(UserModel)
                    .options(
                        joinedload(UserModel.roles),
                        joinedload(UserModel.groups),
                        joinedload(UserModel.realm),
                    )
                    .filter(*filter_params)
                    .first()
                )
        except Exception as e:
            raise e
