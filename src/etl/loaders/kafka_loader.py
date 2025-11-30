# src/etl/loaders/kafka_loader.py
from __future__ import annotations

import json
from typing import Any, Sequence

from confluent_kafka import Producer

from config.settings import settings
from config.logging_config import get_logger

logger = get_logger(__name__)

_producer: Producer | None = None


def _create_producer() -> Producer:
    """Crée un producer Kafka configuré à partir des settings."""
    conf = {
        "bootstrap.servers": settings.kafka_bootstrap_servers,
        "acks": settings.kafka_producer_acks,
        "retries": settings.kafka_producer_retries,
        "compression.type": settings.kafka_producer_compression_type,
    }
    logger.info("Creating Kafka producer with bootstrap.servers=%s", conf["bootstrap.servers"])
    return Producer(conf)


def get_producer() -> Producer:
    """Retourne un producer global (singleton simple)."""
    global _producer
    if _producer is None:
        _producer = _create_producer()
    return _producer


def publish_offers_batch_to_kafka(
    offers: Sequence[dict[str, Any]],
    topic: str,
    key_field: str | None = "id",
) -> int:
    """
    Publie une liste d'offres sur un topic Kafka.
    - offers : liste de dicts (format brut API ou nettoyé),
    - topic : nom du topic,
    - key_field : champ utilisé comme clé (pour la partition), ex: "id".
    Retourne le nombre de messages envoyés.
    """
    producer = get_producer()
    sent = 0

    def delivery_report(err, msg):
        if err is not None:
            logger.error(
                "Kafka delivery failed for %s [%d] at offset %s: %s",
                msg.topic(),
                msg.partition(),
                msg.offset(),
                err,
            )

    for offer in offers:
        try:
            key = None
            if key_field and key_field in offer:
                key = str(offer[key_field])

            producer.produce(
                topic=topic,
                key=key,
                value=json.dumps(offer).encode("utf-8"),
                callback=delivery_report,
            )
            sent += 1
        except BufferError:
            # Buffer plein : flush et réessaye une fois
            logger.warning("Kafka local queue full, flushing producer")
            producer.flush()
            try:
                producer.produce(
                    topic=topic,
                    key=key,
                    value=json.dumps(offer).encode("utf-8"),
                    callback=delivery_report,
                )
                sent += 1
            except Exception as e:
                logger.exception("Failed to publish offer to Kafka after flush (id=%s)", offer.get("id"))
        except Exception as e:
            logger.exception("Failed to publish offer to Kafka (id=%s)", offer.get("id"))

    producer.flush()
    logger.info("Published %d offers to Kafka topic '%s'", sent, topic)
    return sent
