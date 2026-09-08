"""OAuth 2.0 token endpoint for first-party clients."""

import base64
import binascii
from urllib.parse import parse_qs

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel

from src.api.v1.user import UserServiceDep
from src.services.user import IUserService


router = APIRouter(prefix="/oauth", tags=["oauth"])


class OAuthTokenResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    expires_in: int
    refresh_token: str


async def _form_values(request: Request) -> dict[str, str]:
    content_type = request.headers.get("content-type", "")
    if not content_type.startswith("application/x-www-form-urlencoded"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OAuth token requests must use application/x-www-form-urlencoded",
        )
    form = parse_qs((await request.body()).decode(), keep_blank_values=True)
    return {key: values[-1] for key, values in form.items()}


def _client_credentials(request: Request, form: dict[str, str]) -> tuple[str, str]:
    authorization = request.headers.get("authorization", "")
    if authorization:
        scheme, _, encoded_value = authorization.partition(" ")
        if scheme.lower() != "basic" or not encoded_value:
            raise _invalid_client()
        try:
            client_id, client_secret = base64.b64decode(
                encoded_value, validate=True
            ).decode().split(":", 1)
        except (UnicodeDecodeError, ValueError, binascii.Error):
            raise _invalid_client() from None
        return client_id, client_secret

    client_id = form.get("client_id")
    client_secret = form.get("client_secret")
    if not client_id or not client_secret:
        raise _invalid_client()
    return client_id, client_secret


def _invalid_client() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid OAuth client credentials",
        headers={"WWW-Authenticate": "Basic realm=oauth"},
    )


@router.post("/token", response_model=OAuthTokenResponse)
async def oauth_token(request: Request, service: UserServiceDep) -> OAuthTokenResponse:
    form = await _form_values(request)
    client_id, client_secret = _client_credentials(request, form)
    grant_type = form.get("grant_type")
    realm = form.get("realm")
    if not realm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="realm is required",
        )

    try:
        if grant_type == "password":
            username = form.get("username")
            password = form.get("password")
            if not username or not password:
                raise ValueError("username and password are required")
            tokens = service.oauth_password_grant(
                client_id, client_secret, realm, username, password
            )
        elif grant_type == "refresh_token":
            refresh_token = form.get("refresh_token")
            if not refresh_token:
                raise ValueError("refresh_token is required")
            tokens = service.oauth_refresh_grant(
                client_id, client_secret, realm, refresh_token
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported grant_type",
            )
    except PermissionError as error:
        raise _invalid_client() from error
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    return OAuthTokenResponse(
        access_token=tokens["access"],
        refresh_token=tokens["refresh"],
        expires_in=service.access_token_ttl_seconds(),
    )
