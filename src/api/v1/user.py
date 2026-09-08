from typing import Annotated, Any

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel

from src.builder import get_services
from src.dto.user import UserLoginRequest
from src.services.user import IUserService

router = APIRouter(prefix="/user")


def get_user_service():
    return get_services().user_service


UserServiceDep = Annotated[IUserService, Depends(get_user_service)]


class AccessTokenValidationResponse(BaseModel):
    valid: bool
    subject: str
    email: str | None = None
    realm: str | None = None
    roles: list[str]
    issued_at: int
    expires_at: int


def get_access_token_claims(request: Request) -> dict[str, Any]:
    """Read claims placed on the request after middleware JWT verification."""
    claims = getattr(request.state, "token_claims", None)
    if not claims or claims.get("typ") != "user":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
        )
    return claims


AccessTokenClaimsDep = Annotated[dict[str, Any], Depends(get_access_token_claims)]


@router.post("/admin-login", status_code=status.HTTP_200_OK)
async def login(request: UserLoginRequest, service: UserServiceDep, response: Response):
    try:
        token = service.login(request)
        _set_refresh_cookie(
            response, token["refresh"], service.refresh_cookie_max_age()
        )
        return {"access_token": token["access"]}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.post("/refresh", status_code=status.HTTP_200_OK)
async def refresh(
    service: UserServiceDep,
    response: Response,
    refresh_token: str = Cookie(default=None),
):
    try:
        if refresh_token is None:
            raise ValueError("Refresh token not found")
        token = service.refresh(refresh_token)
        _set_refresh_cookie(
            response, token["refresh"], service.refresh_cookie_max_age()
        )
        return {"access_token": token["access"]}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e)
        ) from e


@router.get(
    "/validate-access-token",
    response_model=AccessTokenValidationResponse,
    status_code=status.HTTP_200_OK,
)
async def validate_access_token(
    claims: AccessTokenClaimsDep,
) -> AccessTokenValidationResponse:
    """Confirm the Bearer access token is valid and return its identity metadata."""
    return AccessTokenValidationResponse(
        valid=True,
        subject=claims["sub"],
        email=claims.get("email"),
        realm=claims.get("realm"),
        roles=claims.get("roles", []),
        issued_at=claims["iat"],
        expires_at=claims["exp"],
    )


def _set_refresh_cookie(response: Response, refresh_token: str, max_age: int):
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        samesite="lax",
        max_age=max_age,
        path="/v1/api/user/refresh",
    )
