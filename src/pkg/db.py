import os
import ssl
from pathlib import Path
from typing import Generator, Protocol

from sqlalchemy import BigInteger, Column, create_engine, JSON, MetaData, String, Table
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, DeclarativeMeta, Session, sessionmaker
from src.config.config import DatabaseConfig


class IHandler(Protocol):  # pragma: no cover
    def get_session(self) -> Session: ...

    async def get_async_session(self) -> AsyncSession: ...


class PostgresDbHandler(IHandler):
    config: DatabaseConfig

    def __init__(self, config: DatabaseConfig) -> None:
        self.config = config
        self.__db_url: str = (
            f"postgresql://{config.username}:{config.password}"
            f"@{config.url}:{config.port}/{config.database}"
        )
        self.__async_db_url: str = (
            f"postgresql+asyncpg://{config.username}:{config.password}"
            f"@{config.url}:{config.port}/{config.database}"
        )

        connect_args: dict[str, str] = {
            "sslmode": "disable",
        }
        if config.ssl is not None:
            connect_args = {
                "sslmode": config.ssl.sslmode,
                "sslrootcert": f"{os.getcwd()}/{config.ssl.cert_path}",
            }

        self.engine = create_engine(
            self.__db_url,
            connect_args=connect_args,
            pool_pre_ping=True,
            pool_recycle=3600,
        )
        async_connect_args = {}
        if config.ssl is not None:
            ssl_context = ssl.create_default_context(
                cafile=f"{os.getcwd()}/{config.ssl.cert_path}"
            )
            ssl_context.verify_mode = ssl.CERT_REQUIRED
            async_connect_args = {"ssl": ssl_context}
        self.async_engine = create_async_engine(
            self.__async_db_url,
            connect_args=async_connect_args,
            pool_pre_ping=True,
            pool_recycle=3600,
        )
        self.__session_local = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine
        )

    def get_session(self) -> Session:
        return self.__session_local()

    async def get_async_session(self) -> AsyncSession:
        """Returns an asynchronous session."""
        return async_sessionmaker(
            expire_on_commit=True, bind=self.async_engine, class_=AsyncSession
        )()

    async def load_table(self, table_name) -> Table:
        return Table(
            table_name,
            MetaData(),
            autoload_with=self.engine,
        )
