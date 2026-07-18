import os

from src.builder import Clients, set_clients, set_config, set_services
from src.builder.repo import Repos
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
    return Clients().with_db_handler(config=config).with_token_client(config=config)


def build_all_services(config: Config, clients: Clients) -> Services:
    repo = Repos().with_user_repository(db_handler=clients.db_handler)
    services = Services().with_user_service(
        config=config, clients=clients, repo=repo.user_repository
    )
    return services


def fetch_config_and_build_services():
    cfg = fetch_config()
    clients = build_all_clients(config=cfg)
    svc = build_all_services(cfg, clients)
    set_config(cfg)
    set_clients(clients)
    set_services(svc)
