from typing import Annotated, Any

from fastapi import APIRouter, Depends

from src.api.deps import current_claims, get_authorization_service
from src.api.v1.schemas import AuthorizationDecision, AuthorizeRequest
from src.services.authorization_service import AuthorizationService


router = APIRouter(prefix="/api/v1/authorize", tags=["authorization"])


@router.post("", response_model=AuthorizationDecision)
def authorize_request(
    request: AuthorizeRequest,
    claims: Annotated[dict[str, Any], Depends(current_claims)],
    authorization_service: Annotated[AuthorizationService, Depends(get_authorization_service)],
) -> AuthorizationDecision:
    return authorization_service.decide(claims, request.realm, request.resource, request.action, request.context or {})
