from pathlib import Path
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.config.config import DatabaseConfig


class SqliteDbHandler:
    config: DatabaseConfig

    def __init__(self, config: DatabaseConfig) -> None:
        self.config = config
        self._ensure_sqlite_parent(config.url)
        self.engine = create_engine(
            config.url,
            connect_args=self._sqlite_connect_args(config.url),
            future=True,
        )
        self.__session_local = sessionmaker(
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,
            bind=self.engine,
            future=True,
        )

    def get_session(self) -> Session:
        return self.__session_local()

    def db_session(self) -> Generator[Session, None, None]:
        db = self.get_session()
        try:
            yield db
        finally:
            db.close()

    def _sqlite_connect_args(self, url: str) -> dict[str, bool]:
        if url.startswith("sqlite"):
            return {"check_same_thread": False}
        return {}

    def _ensure_sqlite_parent(self, url: str) -> None:
        if not url.startswith("sqlite:///"):
            return
        path = url.removeprefix("sqlite:///")
        if path != ":memory:":
            Path(path).parent.mkdir(parents=True, exist_ok=True)

