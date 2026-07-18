from __future__ import annotations

from datetime import datetime
from typing import Any, Protocol

# from src.models.models import UserAccount


class TokenClient(Protocol):
    def create_access_token(
        self, user: UserAccount
    ) -> tuple[str, datetime, list[str]]: ...

    def decode_access_token(self, token: str) -> dict[str, Any]: ...

    def jwks(self) -> dict[str, Any]: ...


class MessageClient(Protocol):
    def publish_integration_verification(self, payload: dict[str, Any]) -> None: ...

    def close(self) -> None: ...
