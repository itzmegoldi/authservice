from typing import Optional

from pydantic import BaseModel
from src.pkg.config import ConfigMixIn


class ServerConfig(BaseModel):
    host: str
    port: int


class DbSslConfig(BaseModel):
    sslmode: str = "verify-full"
    cert_path: str


class DatabaseConfig(BaseModel):
    username: str
    password: str
    url: str
    port: int
    database: str
    ssl: Optional[DbSslConfig]


class RedisConfig(BaseModel):
    host: str
    port: int


class BootstrapConfig(BaseModel):
    admin_email: str
    admin_password: str


class KeyConfig(BaseModel):
    rsa_private_pem: str = ""
    rsa_public_pem: str = ""


class AuthConfig(BaseModel):
    issuer: str
    token_ttl_minutes: int
    bootstrap: BootstrapConfig
    keys: KeyConfig


class Config(BaseModel, ConfigMixIn):
    server: ServerConfig
    database: DatabaseConfig
    redis: RedisConfig
    auth: AuthConfig
