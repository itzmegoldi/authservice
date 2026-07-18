from __future__ import annotations

from typing import Any, Optional

from kafka import KafkaProducer

from src.config.config import Config


class KafkaMessageClient:
    def __init__(self, config: Config) -> None:
        self.config = config
        self._producer: Optional[KafkaProducer] = None

    @property
    def producer(self) -> KafkaProducer:
        if self._producer is None:
            self._producer = KafkaProducer(
                bootstrap_servers=self.config.kafka.bootstrap_servers,
                value_serializer=lambda value: str(value).encode("utf-8"),
            )
        return self._producer

    def publish_integration_verification(self, payload: dict[str, Any]) -> None:
        self.producer.send(self.config.kafka.integration_topic, payload)
        self.producer.flush(timeout=5)

    def close(self) -> None:
        if self._producer is not None:
            self._producer.close()
            self._producer = None
