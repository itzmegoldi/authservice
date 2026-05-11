from pydantic import BaseModel

from src.config.server import ServerConfig
from src.pkg.config import ConfigMixIn


class DatabaseConfig(BaseModel):
    url: str


class KafkaConfig(BaseModel):
    bootstrap_servers: str
    integration_topic: str
    worker_group: str


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
    kafka: KafkaConfig
    redis: RedisConfig
    auth: AuthConfig

