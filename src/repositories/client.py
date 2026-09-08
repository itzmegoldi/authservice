from typing import Protocol

from sqlalchemy.orm import joinedload

from src.models.user import ClientModel, ClientRoleModel, UserModel
from src.pkg.db import IHandler


class IClientRepository(Protocol):
    def get_client(self, client_id: str): ...
    def create_client(
        self,
        client_id: str,
        client_secret: str,
        name: str,
        attributes: dict,
        allowed_grant_types: list[str],
    ): ...
    def create_role(self, client_id: str, name: str, attributes: dict): ...
    def assign_role(self, client_id: str, user_id: int, role_name: str): ...


class ClientRepository(IClientRepository):
    def __init__(self, db_handler: IHandler):
        self.db_handler = db_handler

    def get_client(self, client_id: str):
        with self.db_handler.get_session() as session:
            return (
                session.query(ClientModel)
                .filter(ClientModel.client_id == client_id)
                .first()
            )

    def create_client(
        self,
        client_id: str,
        client_secret: str,
        name: str,
        attributes: dict,
        allowed_grant_types: list[str],
    ):
        with self.db_handler.get_session() as session:
            if session.query(ClientModel).filter(ClientModel.client_id == client_id).first():
                raise ValueError("Client ID already exists")
            client = ClientModel(
                client_id=client_id,
                name=name,
                attributes=attributes,
                allowed_grant_types=allowed_grant_types,
            )
            client.set_secret(client_secret)
            session.add(client)
            session.commit()
            return client

    def create_role(self, client_id: str, name: str, attributes: dict):
        with self.db_handler.get_session() as session:
            client = (
                session.query(ClientModel)
                .filter(ClientModel.client_id == client_id)
                .first()
            )
            if not client:
                raise ValueError("Client not found")
            if (
                session.query(ClientRoleModel)
                .filter(
                    ClientRoleModel.client_id == client.id,
                    ClientRoleModel.name == name,
                )
                .first()
            ):
                raise ValueError("Client role already exists")
            role = ClientRoleModel(client_id=client.id, name=name, attributes=attributes)
            session.add(role)
            session.commit()
            return role

    def assign_role(self, client_id: str, user_id: int, role_name: str):
        with self.db_handler.get_session() as session:
            client = (
                session.query(ClientModel)
                .filter(ClientModel.client_id == client_id)
                .first()
            )
            if not client:
                raise ValueError("Client not found")
            user = session.query(UserModel).filter(UserModel.id == user_id).first()
            if not user:
                raise ValueError("User not found")
            role = (
                session.query(ClientRoleModel)
                .filter(
                    ClientRoleModel.client_id == client.id,
                    ClientRoleModel.name == role_name,
                )
                .first()
            )
            if not role:
                raise ValueError("Client role not found")
            if role not in user.client_roles:
                user.client_roles.append(role)
                session.commit()
            return role
