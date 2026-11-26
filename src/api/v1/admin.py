"""Administrative read/write API used by the first-party admin console.

The OAuth endpoints deliberately remain small.  This router is the explicit
management surface and every route requires an administrator access token.
"""

from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import joinedload

from src.api.v1.user import AdminClaimsDep
from src.builder import get_clients
from src.models.user import (
    ClientModel,
    ClientRoleModel,
    GroupModel,
    RealmModel,
    RoleModel,
    UserModel,
)

router = APIRouter(prefix="/admin", tags=["admin"])


class RealmInput(BaseModel):
    name: str


class UserInput(BaseModel):
    email: str
    password: str
    first_name: str | None = None
    last_name: str | None = None
    is_admin: bool = False
    is_active: bool = True
    attributes: dict[str, Any] = Field(default_factory=dict)


class UserUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    password: str | None = None
    is_admin: bool | None = None
    is_active: bool | None = None
    attributes: dict[str, Any] | None = None


class ClientInput(BaseModel):
    client_id: str
    client_secret: str
    name: str
    allowed_grant_types: list[str] = Field(
        default_factory=lambda: ["password", "refresh_token"]
    )
    attributes: dict[str, Any] = Field(default_factory=dict)


class ClientUpdate(BaseModel):
    name: str | None = None
    client_secret: str | None = None
    allowed_grant_types: list[str] | None = None
    attributes: dict[str, Any] | None = None
    is_active: bool | None = None


class NameInput(BaseModel):
    name: str


def _session():
    return get_clients().db_handler.get_session()


def _realm(session, realm_name: str) -> RealmModel:
    realm = session.query(RealmModel).filter(RealmModel.name == realm_name).first()
    if not realm:
        raise HTTPException(status_code=404, detail="Realm not found")
    return realm


def _user_view(user: UserModel) -> dict[str, Any]:
    return {
        "id": user.id,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "is_admin": user.is_admin,
        "is_active": user.is_active,
        "attributes": user.attributes or {},
        "groups": [group.name for group in user.groups],
        "roles": [role.name for role in user.roles],
        "client_roles": [
            {"client_id": role.client.client_id, "name": role.name}
            for role in user.client_roles
        ],
    }


def _client_view(client: ClientModel) -> dict[str, Any]:
    return {
        "id": client.id,
        "client_id": client.client_id,
        "name": client.name,
        "is_active": client.is_active,
        "attributes": client.attributes or {},
        "allowed_grant_types": client.allowed_grant_types,
        "roles": [
            {"id": role.id, "name": role.name, "attributes": role.attributes or {}}
            for role in client.roles
        ],
    }


@router.get("/overview")
def overview(_: AdminClaimsDep):
    with _session() as session:
        return {
            "realms": session.query(RealmModel).count(),
            "users": session.query(UserModel).count(),
            "clients": session.query(ClientModel).count(),
            "groups": session.query(GroupModel).count(),
            "roles": session.query(RoleModel).count(),
        }


@router.get("/realms")
def list_realms(_: AdminClaimsDep):
    with _session() as session:
        return [
            {"id": realm.id, "name": realm.name}
            for realm in session.query(RealmModel).order_by(RealmModel.name).all()
        ]


@router.post("/realms", status_code=status.HTTP_201_CREATED)
def create_realm(request: RealmInput, _: AdminClaimsDep):
    with _session() as session:
        if session.query(RealmModel).filter(RealmModel.name == request.name).first():
            raise HTTPException(status_code=409, detail="Realm already exists")
        realm = RealmModel(name=request.name)
        session.add(realm)
        session.commit()
        return {"id": realm.id, "name": realm.name}


@router.get("/realms/{realm_name}/users")
def list_users(realm_name: str, _: AdminClaimsDep):
    with _session() as session:
        realm = _realm(session, realm_name)
        users = (
            session.query(UserModel)
            .options(
                joinedload(UserModel.groups),
                joinedload(UserModel.roles),
                joinedload(UserModel.client_roles).joinedload(ClientRoleModel.client),
            )
            .filter(UserModel.realm_id == realm.id)
            .order_by(UserModel.email)
            .all()
        )
        return [_user_view(user) for user in users]


@router.post("/realms/{realm_name}/users", status_code=status.HTTP_201_CREATED)
def create_user(realm_name: str, request: UserInput, _: AdminClaimsDep):
    with _session() as session:
        realm = _realm(session, realm_name)
        if session.query(UserModel).filter(UserModel.email == request.email).first():
            raise HTTPException(status_code=409, detail="Email already exists")
        user = UserModel(
            email=request.email,
            first_name=request.first_name,
            last_name=request.last_name,
            realm_id=realm.id,
            is_admin=request.is_admin,
            is_active=request.is_active,
            attributes=request.attributes,
        )
        user.set_password(request.password)
        session.add(user)
        session.commit()
        session.refresh(user)
        return _user_view(user)


@router.patch("/realms/{realm_name}/users/{user_id}")
def update_user(realm_name: str, user_id: int, request: UserUpdate, _: AdminClaimsDep):
    with _session() as session:
        realm = _realm(session, realm_name)
        user = (
            session.query(UserModel)
            .options(joinedload(UserModel.groups), joinedload(UserModel.roles))
            .filter(UserModel.id == user_id, UserModel.realm_id == realm.id)
            .first()
        )
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        for field, value in request.model_dump(exclude_unset=True).items():
            if field == "password" and value:
                user.set_password(value)
            elif field != "password":
                setattr(user, field, value)
        session.commit()
        return _user_view(user)


@router.get("/realms/{realm_name}/clients")
def list_clients(realm_name: str, _: AdminClaimsDep):
    with _session() as session:
        realm = _realm(session, realm_name)
        clients = (
            session.query(ClientModel)
            .options(joinedload(ClientModel.roles))
            .filter(ClientModel.realm_id == realm.id)
            .order_by(ClientModel.client_id)
            .all()
        )
        return [_client_view(client) for client in clients]


@router.post("/realms/{realm_name}/clients", status_code=status.HTTP_201_CREATED)
def create_client(realm_name: str, request: ClientInput, _: AdminClaimsDep):
    with _session() as session:
        realm = _realm(session, realm_name)
        if session.query(ClientModel).filter(ClientModel.client_id == request.client_id).first():
            raise HTTPException(status_code=409, detail="Client ID already exists")
        client = ClientModel(
            client_id=request.client_id,
            name=request.name,
            realm_id=realm.id,
            attributes=request.attributes,
            allowed_grant_types=request.allowed_grant_types,
        )
        client.set_secret(request.client_secret)
        session.add(client)
        session.commit()
        return _client_view(client)


@router.patch("/realms/{realm_name}/clients/{client_id}")
def update_client(realm_name: str, client_id: str, request: ClientUpdate, _: AdminClaimsDep):
    with _session() as session:
        realm = _realm(session, realm_name)
        client = (
            session.query(ClientModel)
            .options(joinedload(ClientModel.roles))
            .filter(ClientModel.client_id == client_id, ClientModel.realm_id == realm.id)
            .first()
        )
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
        for field, value in request.model_dump(exclude_unset=True).items():
            if field == "client_secret" and value:
                client.set_secret(value)
            elif field != "client_secret":
                setattr(client, field, value)
        session.commit()
        return _client_view(client)


@router.get("/realms/{realm_name}/roles")
def list_roles(realm_name: str, _: AdminClaimsDep):
    with _session() as session:
        _realm(session, realm_name)
        return [{"id": role.id, "name": role.name} for role in session.query(RoleModel).order_by(RoleModel.name).all()]


@router.post("/realms/{realm_name}/roles", status_code=status.HTTP_201_CREATED)
def create_role(realm_name: str, request: NameInput, _: AdminClaimsDep):
    with _session() as session:
        _realm(session, realm_name)
        if session.query(RoleModel).filter(RoleModel.name == request.name).first():
            raise HTTPException(status_code=409, detail="Role already exists")
        role = RoleModel(name=request.name)
        session.add(role)
        session.commit()
        return {"id": role.id, "name": role.name}


@router.get("/realms/{realm_name}/groups")
def list_groups(realm_name: str, _: AdminClaimsDep):
    with _session() as session:
        _realm(session, realm_name)
        groups = session.query(GroupModel).options(joinedload(GroupModel.roles)).order_by(GroupModel.name).all()
        return [{"id": group.id, "name": group.name, "roles": [role.name for role in group.roles]} for group in groups]


@router.post("/realms/{realm_name}/groups", status_code=status.HTTP_201_CREATED)
def create_group(realm_name: str, request: NameInput, _: AdminClaimsDep):
    with _session() as session:
        _realm(session, realm_name)
        if session.query(GroupModel).filter(GroupModel.name == request.name).first():
            raise HTTPException(status_code=409, detail="Group already exists")
        group = GroupModel(name=request.name)
        session.add(group)
        session.commit()
        return {"id": group.id, "name": group.name, "roles": []}


@router.put("/realms/{realm_name}/users/{user_id}/groups/{group_name}", status_code=status.HTTP_204_NO_CONTENT)
def add_user_to_group(realm_name: str, user_id: int, group_name: str, _: AdminClaimsDep):
    with _session() as session:
        realm = _realm(session, realm_name)
        user = session.query(UserModel).filter(UserModel.id == user_id, UserModel.realm_id == realm.id).first()
        group = session.query(GroupModel).filter(GroupModel.name == group_name).first()
        if not user or not group:
            raise HTTPException(status_code=404, detail="User or group not found")
        if group not in user.groups:
            user.groups.append(group)
            session.commit()


@router.put("/realms/{realm_name}/users/{user_id}/roles/{role_name}", status_code=status.HTTP_204_NO_CONTENT)
def add_role_to_user(realm_name: str, user_id: int, role_name: str, _: AdminClaimsDep):
    with _session() as session:
        realm = _realm(session, realm_name)
        user = session.query(UserModel).filter(UserModel.id == user_id, UserModel.realm_id == realm.id).first()
        role = session.query(RoleModel).filter(RoleModel.name == role_name).first()
        if not user or not role:
            raise HTTPException(status_code=404, detail="User or role not found")
        if role not in user.roles:
            user.roles.append(role)
            session.commit()


@router.put("/realms/{realm_name}/groups/{group_name}/roles/{role_name}", status_code=status.HTTP_204_NO_CONTENT)
def add_role_to_group(realm_name: str, group_name: str, role_name: str, _: AdminClaimsDep):
    with _session() as session:
        _realm(session, realm_name)
        group = session.query(GroupModel).options(joinedload(GroupModel.roles)).filter(GroupModel.name == group_name).first()
        role = session.query(RoleModel).filter(RoleModel.name == role_name).first()
        if not group or not role:
            raise HTTPException(status_code=404, detail="Group or role not found")
        if role not in group.roles:
            group.roles.append(role)
            session.commit()


@router.post("/realms/{realm_name}/clients/{client_id}/roles", status_code=status.HTTP_201_CREATED)
def create_client_role(realm_name: str, client_id: str, request: NameInput, _: AdminClaimsDep):
    with _session() as session:
        realm = _realm(session, realm_name)
        client = session.query(ClientModel).filter(ClientModel.client_id == client_id, ClientModel.realm_id == realm.id).first()
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
        if session.query(ClientRoleModel).filter(ClientRoleModel.client_id == client.id, ClientRoleModel.name == request.name).first():
            raise HTTPException(status_code=409, detail="Client role already exists")
        role = ClientRoleModel(client_id=client.id, name=request.name)
        session.add(role)
        session.commit()
        return {"id": role.id, "name": role.name, "attributes": {}}
