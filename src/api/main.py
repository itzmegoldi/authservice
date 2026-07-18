from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.api.v1 import router as v1_router
from src.builder import get_services
from src.builder.helper import fetch_config, fetch_config_and_build_services
from src.pkg import logging
from src.pkg.middlewares import ErrorHandlingMiddleware, LoggerInitMiddleware

logging.configure_logger(
    default_logger_names=[
        "root",
        "fastapi",
        "sqlalchemy.engine.warnings",
        "alembic.runtime.migration",
        "uvicorn.access",
        "uvicorn.error",
        "uvicorn",
    ],
)
logger = logging.get_logger()


def get_user_service():
    return get_services().user_service


@asynccontextmanager
async def lifespan(_: FastAPI):
    fetch_config_and_build_services()

    try:
        get_user_service().bootstrap()
    except Exception as e:
        logger.exception(f"Failed to bootstrap application {str(e)}")

    yield


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

app.include_router(v1_router)


class HealthCheckModel(BaseModel):
    status: str


@app.get("/health", response_model=HealthCheckModel)
def health_check():
    return {"status": "ok"}


if __name__ == "__main__":
    cfg = fetch_config()
    uvicorn.run(app, host=cfg.server.host, port=cfg.server.port, log_config=None)
