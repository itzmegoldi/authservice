from __future__ import annotations

from typing import Any

from src.clients.interfaces import MessageClient


class IntegrationService:
    def __init__(self, message_client: MessageClient) -> None:
        self.message_client = message_client

    def enqueue_verification(self, payload: dict[str, Any]) -> dict[str, str]:
        self.message_client.publish_integration_verification(payload)
        return {"status": "queued"}
