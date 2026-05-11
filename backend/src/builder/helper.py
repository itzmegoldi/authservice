import os

from src.builder import Clients, set_clients, set_config, set_services
from src.builder.services import Services
from src.config.config import Config


def fetch_config() -> Config:
    config_path = os.path.join(os.getcwd(), "config/")
    app_env = os.environ.get("APP_ENV", "local")
    return Config.from_yaml(
        config_path,
        app_env,
    )


def build_all_clients(config: Config) -> Clients:
    return (
        Clients()
        .with_db_handler(config=config)
        .with_token_client(config=config)
        .with_message_client(config=config)
    )


def build_all_services(clients: Clients) -> Services:
    services = Services()
    return services


def fetch_config_and_build_services():
    cfg = fetch_config()
    clients = build_all_clients(config=cfg)
    svc = build_all_services(clients)
    set_config(cfg)
    set_clients(clients)
    set_services(svc)

