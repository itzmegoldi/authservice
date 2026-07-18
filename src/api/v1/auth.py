from typing import Any, Annotated

from fastapi import APIRouter, Depends, status

from src.api.deps import (
    current_claims,
    get_auth_service,
    get_integration_service,
    get_token_client,
    require_admin_or_integration_write,
)
from src.clients.interfaces import TokenClient
from src.api.v1.schemas import LoginRequest, RegisterRequest, TokenResponse
from src.services.auth_service import AuthService
from src.services.integration_service import IntegrationService


router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse)
def register(
    request: RegisterRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> TokenResponse:
    return auth_service.register(request)


@router.post("/login", response_model=TokenResponse)
def login(
    request: LoginRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> TokenResponse:
    return auth_service.login(request.realm, request.email, request.password)


@router.get("/.well-known/jwks.json")
def jwks(token_client: Annotated[TokenClient, Depends(get_token_client)]) -> dict[str, Any]:
    return token_client.jwks()


@router.get("/me")
def me(claims: Annotated[dict[str, Any], Depends(current_claims)]) -> dict[str, Any]:
    return {
        "subject": claims.get("sub"),
        "realm": claims.get("realm"),
        "email": claims.get("email"),
        "roles": claims.get("roles") or [],
        "attributes": claims.get("attributes") or {},
    }


@router.post("/integrations/verify", status_code=status.HTTP_202_ACCEPTED)
def enqueue_integration_verification(
    payload: dict[str, Any],
    claims: Annotated[dict[str, Any], Depends(require_admin_or_integration_write)],
    integration_service: Annotated[IntegrationService, Depends(get_integration_service)],
) -> dict[str, str]:
    return integration_service.enqueue_verification(payload)
