import unittest
from types import SimpleNamespace

import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from src.clients.jwt_client import JwtClient
from src.config.config import KeyConfig


def _config(private_key: str, public_key: str):
    return SimpleNamespace(
        auth=SimpleNamespace(
            issuer="https://auth.example.test",
            token_ttl_minutes=5,
            refresh_token_ttl_days=1,
            keys=SimpleNamespace(
                rsa_private_pem=private_key, rsa_public_pem=public_key
            ),
        )
    )


class JwtClientTests(unittest.TestCase):
    def setUp(self):
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        private_pem = private_key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        ).decode()
        public_pem = private_key.public_key().public_bytes(
            serialization.Encoding.PEM,
            serialization.PublicFormat.SubjectPublicKeyInfo,
        ).decode()
        self.client = JwtClient(_config(private_pem, public_pem))

    def test_accepts_deployment_key_aliases(self):
        keys = KeyConfig.model_validate({"secret": "private", "public": "public"})
        self.assertEqual(keys.rsa_private_pem, "private")
        self.assertEqual(keys.rsa_public_pem, "public")

    def test_client_token_has_audience_and_is_verifiable(self):
        token, _ = self.client.create_client_access_token(
            "orders-api", "master", ["orders.read"]
        )
        claims = jwt.decode(
            token,
            self.client._public_pem(),
            algorithms=["RS256"],
            issuer="https://auth.example.test",
            audience="orders-api",
        )
        self.assertEqual(claims["typ"], "client")
        self.assertEqual(claims["scope"], "orders.read")

    def test_missing_signing_key_is_rejected(self):
        config = _config("", "")
        with self.assertRaises(ValueError):
            JwtClient(config)
