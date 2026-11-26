"""Public OpenID Connect discovery and verification-key endpoints."""

from fastapi import APIRouter

from src.builder import get_clients, get_config


router = APIRouter(tags=["discovery"])


@router.get("/.well-known/openid-configuration")
def openid_configuration() -> dict[str, object]:
    issuer = get_config().auth.issuer.rstrip("/")
    api_base = f"{issuer}/v1/api"
    return {
        "issuer": issuer,
        "jwks_uri": f"{api_base}/oauth/jwks.json",
        "token_endpoint": f"{api_base}/oauth/token",
        "grant_types_supported": [
            "password", "refresh_token", "google", "client_credentials"
        ],
        "token_endpoint_auth_methods_supported": [
            "client_secret_basic", "client_secret_post"
        ],
        "id_token_signing_alg_values_supported": ["RS256"],
    }


@router.get("/oauth/jwks.json")
def jwks() -> dict[str, object]:
    return get_clients().token_client.jwks()
