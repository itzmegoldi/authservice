from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.api.v1 import auth, authorization
from src.builder import get_clients, get_config
from src.builder.helper import fetch_config, fetch_config_and_build_services
from src.repositories.sqlalchemy import (
    SqlAlchemyPolicyRepository,
    SqlAlchemyRealmRepository,
    SqlAlchemyRoleRepository,
    SqlAlchemyUserRepository,
)
from src.services.bootstrap_service import BootstrapService
from src.pkg import logging
from src.pkg.middlewares import ErrorHandlingMiddleware, LoggerInitMiddleware

logging.configure_logger(
    default_logger_names=[
        "root",
        "fastapi",
        "sqlalchemy.engine",
        "alembic.runtime.migration",
        "uvicorn.access", 
        "uvicorn.error",
        "uvicorn"
        ],
)

logger = logging.get_logger()

@asynccontextmanager
async def lifespan(_: FastAPI):
    fetch_config_and_build_services()
    clients = get_clients()
    with clients.db_handler.get_session() as db:
        BootstrapService(
            config=get_config(),
            realms=SqlAlchemyRealmRepository(db),
            roles=SqlAlchemyRoleRepository(db),
            users=SqlAlchemyUserRepository(db),
            policies=SqlAlchemyPolicyRepository(db),
        ).ensure_default_realm()
        db.commit()
    try:
        yield
    finally:
        clients.close()


app = FastAPI(title="Auth Service", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(ErrorHandlingMiddleware)
app.add_middleware(LoggerInitMiddleware)

app.include_router(auth.router)
app.include_router(authorization.router)


class HealthCheckModel(BaseModel):
    status: str


@app.get("/actuator/health", response_model=HealthCheckModel)
def health_check():
    return {"status": "UP"}


if __name__ == "__main__":
    cfg = fetch_config()
    uvicorn.run(app, host=cfg.server.host, port=cfg.server.port, log_config=None)

