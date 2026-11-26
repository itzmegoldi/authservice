import hashlib
import time
from typing import Protocol

from sqlalchemy.orm import joinedload

from src.dto.user import BootstrapUser, UserCreateRequestDto

from src.models.user import ClientRoleModel, RealmModel, RefreshSessionModel, UserModel
from src.pkg.db import IHandler


class IUserRepository(Protocol):

    def bootstrap(self, request: BootstrapUser): ...
    def create_user(self, request: UserCreateRequestDto): ...
    def get_user(
        self, email: str, is_admin: bool = False, realm_name: str | None = None
    ): ...
    def get_user_by_id(self, user_id: int): ...
    def get_user_by_google_subject(self, google_subject: str): ...
    def create_google_user(
        self, google_subject: str, email: str, realm_name: str
    ) -> int: ...
    def create_refresh_session(
        self, user_id: int, realm_id: int, client_id: str | None, family_id: str,
        token_id: str, expires_at: int,
    ) -> None: ...
    def rotate_refresh_session(
        self, user_id: int, realm_id: int, client_id: str | None, family_id: str,
        old_token_id: str, new_token_id: str, expires_at: int,
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

    def get_user(self, email, is_admin=False, realm_name: str | None = None):
        try:
            params = {"email": email}

            if is_admin:
                params["is_admin"] = True

            filter_params = []
            for key, value in params.items():
                filter_params.append(getattr(UserModel, key) == value)

            if realm_name:
                filter_params.append(RealmModel.name == realm_name)

            with self.db_handler.get_session() as session:
                return (
                    session.query(UserModel)
                    .options(
                        joinedload(UserModel.roles),
                        joinedload(UserModel.groups),
                        joinedload(UserModel.realm),
                        joinedload(UserModel.client_roles).joinedload(
                            ClientRoleModel.client
                        ),
                    )
                    .join(UserModel.realm)
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
                    joinedload(UserModel.client_roles).joinedload(ClientRoleModel.client),
                )
                .filter(UserModel.id == user_id)
                .first()
            )

    def get_user_by_google_subject(self, google_subject: str):
        with self.db_handler.get_session() as session:
            return (
                session.query(UserModel)
                .options(
                    joinedload(UserModel.roles),
                    joinedload(UserModel.groups),
                    joinedload(UserModel.realm),
                    joinedload(UserModel.client_roles).joinedload(ClientRoleModel.client),
                )
                .filter(UserModel.google_subject == google_subject)
                .first()
            )

    def create_google_user(self, google_subject: str, email: str, realm_name: str) -> int:
        with self.db_handler.get_session() as session:
            realm = session.query(RealmModel).filter(RealmModel.name == realm_name).first()
            if not realm:
                raise ValueError("Realm not found")
            if session.query(UserModel).filter(UserModel.email == email).first():
                raise ValueError("Email is already linked to another user")
            user = UserModel(
                email=email,
                realm_id=realm.id,
                google_subject=google_subject,
                is_active=True,
                is_admin=False,
            )
            session.add(user)
            session.flush()
            user_id = user.id
            session.commit()
            return user_id

    @staticmethod
    def _token_id_hash(token_id: str) -> str:
        return hashlib.sha256(token_id.encode()).hexdigest()

    def create_refresh_session(
        self, user_id: int, realm_id: int, client_id: str | None, family_id: str,
        token_id: str, expires_at: int,
    ) -> None:
        with self.db_handler.get_session() as session:
            session.add(RefreshSessionModel(
                user_id=user_id, realm_id=realm_id, client_id=client_id,
                family_id=family_id, token_id_hash=self._token_id_hash(token_id),
                expires_at=expires_at,
            ))
            session.commit()

    def rotate_refresh_session(
        self, user_id: int, realm_id: int, client_id: str | None, family_id: str,
        old_token_id: str, new_token_id: str, expires_at: int,
    ) -> bool:
        now = int(time.time())
        with self.db_handler.get_session() as session:
            updated_count = (
                session.query(RefreshSessionModel)
                .filter(
                    RefreshSessionModel.user_id == user_id,
                    RefreshSessionModel.realm_id == realm_id,
                    RefreshSessionModel.client_id == client_id,
                    RefreshSessionModel.family_id == family_id,
                    RefreshSessionModel.token_id_hash == self._token_id_hash(old_token_id),
                    RefreshSessionModel.rotated_at.is_(None),
                    RefreshSessionModel.revoked_at.is_(None),
                    RefreshSessionModel.expires_at > now,
                )
                .update({RefreshSessionModel.rotated_at: now})
            )
            if updated_count == 1:
                session.add(RefreshSessionModel(
                    user_id=user_id, realm_id=realm_id, client_id=client_id,
                    family_id=family_id, token_id_hash=self._token_id_hash(new_token_id),
                    expires_at=expires_at,
                ))
                session.commit()
                return True

            # A known, already-used token is a replay attempt. Revoke its whole
            # family so neither side can continue the session.
            known_token = session.query(RefreshSessionModel).filter(
                RefreshSessionModel.token_id_hash == self._token_id_hash(old_token_id)
            ).first()
            if known_token:
                session.query(RefreshSessionModel).filter(
                    RefreshSessionModel.family_id == known_token.family_id,
                    RefreshSessionModel.revoked_at.is_(None),
                ).update({RefreshSessionModel.revoked_at: now})
            session.commit()
            return False
