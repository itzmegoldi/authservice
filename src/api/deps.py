from __future__ import annotations

from typing import Any, Annotated, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from src.builder import get_clients
from src.builder.clients import Clients
from src.clients.interfaces import MessageClient, TokenClient
from src.repositories.sqlalchemy import (
    SqlAlchemyPolicyRepository,
    SqlAlchemyRealmRepository,
    SqlAlchemyRoleRepository,
    SqlAlchemyUserRepository,
)
from src.services.auth_service import AuthService
from src.services.authorization_service import AuthorizationService
from src.services.integration_service import IntegrationService


bearer_scheme = HTTPBearer(auto_error=False)


def get_token_client(clients: Annotated[Clients, Depends(get_clients)]) -> TokenClient:
    return clients.token_client


def get_message_client(clients: Annotated[Clients, Depends(get_clients)]) -> MessageClient:
    return clients.message_client


def get_db(clients: Annotated[Clients, Depends(get_clients)]):
    yield from clients.db_handler.db_session()


def current_claims(
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(bearer_scheme)],
    token_client: Annotated[TokenClient, Depends(get_token_client)],
) -> dict[str, Any]:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    try:
        return token_client.decode_access_token(credentials.credentials)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid bearer token") from exc


def require_admin_or_integration_write(claims: Annotated[dict[str, Any], Depends(current_claims)]) -> dict[str, Any]:
    roles = claims.get("roles") or []
    scopes = str(claims.get("scope") or "").split()
    if "admin" in roles or "integrations:write" in scopes:
        return claims
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")


def get_auth_service(
    db: Annotated[Session, Depends(get_db)],
    token_client: Annotated[TokenClient, Depends(get_token_client)],
) -> AuthService:
    return AuthService(
        db=db,
        token_client=token_client,
        realms=SqlAlchemyRealmRepository(db),
        users=SqlAlchemyUserRepository(db),
        roles=SqlAlchemyRoleRepository(db),
    )


def get_authorization_service(db: Annotated[Session, Depends(get_db)]) -> AuthorizationService:
    return AuthorizationService(policies=SqlAlchemyPolicyRepository(db))


def get_integration_service(
    message_client: Annotated[MessageClient, Depends(get_message_client)],
) -> IntegrationService:
    return IntegrationService(message_client=message_client)
