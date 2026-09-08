from __future__ import annotations

import json
from uuid import uuid4

from datetime import datetime, timedelta, timezone
from typing import Any

import jwt

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from src.config.config import Config
from src.models.user import UserModel


class JwtClient:
    def __init__(self, config: Config) -> None:
        self.config = config
        private_pem = config.auth.keys.rsa_private_pem
        public_pem = config.auth.keys.rsa_public_pem
        if private_pem:
            self.private_key = serialization.load_pem_private_key(
                private_pem.encode(), password=None
            )
            self.public_key = (
                serialization.load_pem_public_key(public_pem.encode())
                if public_pem
                else self.private_key.public_key()
            )
        else:
            self.private_key = rsa.generate_private_key(
                public_exponent=65537, key_size=2048
            )
            self.public_key = self.private_key.public_key()
        self.kid = f"auth-service-{int(datetime.now(timezone.utc).timestamp())}"

    def _create_token(
        self,
        claims: dict[str, Any],
        expires_at: datetime,
    ) -> str:
        claims["iat"] = int(datetime.now(timezone.utc).timestamp())
        claims["exp"] = int(expires_at.timestamp())

        return jwt.encode(
            claims,
            self._private_pem(),
            algorithm="RS256",
            headers={"kid": self.kid},
        )

    def create_access_token(
        self, user: UserModel, client_id: str | None = None
    ) -> tuple[str, datetime]:
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(minutes=self.config.auth.token_ttl_minutes)
        roles = sorted(role.name for role in user.roles)
        client_roles = [
            role for role in user.client_roles if role.client.client_id == client_id
        ]
        claims = {
            "iss": self.config.auth.issuer,
            "iat": int(now.timestamp()),
            "exp": int(expires_at.timestamp()),
            "sub": str(user.id),
            "typ": "user",
            "realm": user.realm.name,
            "email": user.email,
            "roles": roles,
            "attributes": user.attributes,
            "is_admin": user.is_admin,
        }
        if client_id:
            claims["client_id"] = client_id
            claims["resource_access"] = {
                client_id: {"roles": sorted(role.name for role in client_roles)}
            }
            claims["client_role_attributes"] = {
                role.name: role.attributes for role in client_roles
            }
        token = self._create_token(
            claims,
            expires_at,
        )
        return token, expires_at

    def create_refresh_token(
        self,
        user: UserModel,
        client_id: str | None = None,
    ) -> tuple[str, datetime, str]:

        expires_at = datetime.now(timezone.utc) + timedelta(
            days=self.config.auth.refresh_token_ttl_days
        )

        token_id = uuid4().hex
        claims = {
            "iss": self.config.auth.issuer,
            "sub": str(user.id),
            "typ": "refresh",
            "jti": token_id,
            "iat": int(datetime.now(timezone.utc).timestamp()),
            "exp": int(expires_at.timestamp()),
        }
        if client_id:
            claims["client_id"] = client_id

        token = self._create_token(
            claims,
            expires_at,
        )

        return token, expires_at, token_id

    def decode_access_token(self, token: str) -> dict[str, Any]:
        return self._decode_token(token)

    def decode_refresh_token(self, token: str) -> dict[str, Any]:
        return self._decode_token(token)

    def _decode_token(self, token: str) -> dict[str, Any]:
        return jwt.decode(
            token,
            self._public_pem(),
            algorithms=["RS256"],
            issuer=self.config.auth.issuer,
        )

    def jwks(self) -> dict[str, Any]:
        jwk = json.loads(jwt.algorithms.RSAAlgorithm.to_jwk(self.public_key))
        jwk["kid"] = self.kid
        jwk["use"] = "sig"
        jwk["alg"] = "RS256"
        return {"keys": [jwk]}

    def _private_pem(self) -> bytes:
        return self.private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )

    def _public_pem(self) -> bytes:
        return self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
