from __future__ import annotations

import json

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

    def create_access_token(self, user: UserModel) -> tuple[str, datetime, list[str]]:
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(minutes=self.config.auth.token_ttl_minutes)
        roles = sorted(role.name for role in user.roles)
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
        }
        token = self._create_token(
            claims,
            expires_at,
        )
        return token, expires_at

    def create_refresh_token(
        self,
        user: UserModel,
    ) -> tuple[str, datetime]:

        expires_at = datetime.now(timezone.utc) + timedelta(
            days=self.config.auth.refresh_token_ttl_days
        )

        claims = {
            "iss": self.config.auth.issuer,
            "sub": str(user.id),
            "typ": "refresh",
            "iat": int(datetime.now(timezone.utc).timestamp()),
            "exp": int(expires_at.timestamp()),
        }

        token = self._create_token(
            claims,
            expires_at,
        )

        return token, expires_at

    def decode_access_token(self, token: str) -> dict[str, Any]:
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
