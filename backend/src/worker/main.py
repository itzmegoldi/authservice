from kafka import KafkaConsumer

from src.builder.helper import fetch_config


def main() -> None:
    config = fetch_config()
    consumer = KafkaConsumer(
        config.kafka.integration_topic,
        bootstrap_servers=config.kafka.bootstrap_servers,
        group_id=config.kafka.worker_group,
        auto_offset_reset="earliest",
        enable_auto_commit=True,
        value_deserializer=lambda value: value.decode("utf-8"),
    )
    print(f"Listening on {config.kafka.integration_topic}", flush=True)
    for message in consumer:
        print(f"Verified integration payload: {message.value}", flush=True)


if __name__ == "__main__":
    main()
