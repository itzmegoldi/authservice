from typing import Protocol

from sqlalchemy.orm import joinedload

from src.dto.user import BootstrapUser, UserCreateRequestDto

from src.models.user import RealmModel, UserModel
from src.pkg.db import IHandler


class IUserRepository(Protocol):

    def bootstrap(self, request: BootstrapUser): ...
    def create_user(self, request: UserCreateRequestDto): ...
    def get_user(self, email: str): ...
    def get_user_by_id(self, user_id: int): ...
    def set_refresh_token_jti(self, user_id: int, token_id: str): ...
    def rotate_refresh_token_jti(
        self, user_id: int, old_token_id: str, new_token_id: str
    ) -> bool: ...


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

    def get_user(self, email, is_admin=False):
        try:
            params = {"email": email}

            if is_admin:
                params["is_admin"] = True

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

    def get_user_by_id(self, user_id: int):
        with self.db_handler.get_session() as session:
            return (
                session.query(UserModel)
                .options(
                    joinedload(UserModel.roles),
                    joinedload(UserModel.groups),
                    joinedload(UserModel.realm),
                )
                .filter(UserModel.id == user_id)
                .first()
            )

    def set_refresh_token_jti(self, user_id: int, token_id: str):
        with self.db_handler.get_session() as session:
            session.query(UserModel).filter(UserModel.id == user_id).update(
                {UserModel.refresh_token_jti: token_id}
            )
            session.commit()

    def rotate_refresh_token_jti(
        self, user_id: int, old_token_id: str, new_token_id: str
    ) -> bool:
        with self.db_handler.get_session() as session:
            updated_count = (
                session.query(UserModel)
                .filter(
                    UserModel.id == user_id,
                    UserModel.refresh_token_jti == old_token_id,
                )
                .update({UserModel.refresh_token_jti: new_token_id})
            )
            session.commit()
            return updated_count == 1
