from typing import Protocol

from src.dto.client import ClientCreateRequest, ClientRoleCreateRequest
from src.repositories.client import IClientRepository


class IClientService(Protocol):
    def create_client(self, request: ClientCreateRequest): ...
    def create_role(self, client_id: str, request: ClientRoleCreateRequest): ...
    def assign_role(self, client_id: str, user_id: int, role_name: str): ...


class ClientService(IClientService):
    def __init__(self, repo: IClientRepository):
        self.repo = repo

    def create_client(self, request: ClientCreateRequest):
        return self.repo.create_client(
            client_id=request.client_id,
            client_secret=request.client_secret,
            name=request.name,
            attributes=request.attributes,
            allowed_grant_types=request.allowed_grant_types,
        )

    def create_role(self, client_id: str, request: ClientRoleCreateRequest):
        return self.repo.create_role(client_id, request.name, request.attributes)

    def assign_role(self, client_id: str, user_id: int, role_name: str):
        return self.repo.assign_role(client_id, user_id, role_name)
