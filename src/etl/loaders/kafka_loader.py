# src/etl/loaders/kafka_loader.py
from __future__ import annotations

import json
import os
from collections.abc import Sequence
from typing import Any

from confluent_kafka import Producer

from config.logging_config import get_logger
from config.settings import settings

logger = get_logger(__name__)

_producer: Producer | None = None


def _create_producer() -> Producer:
    """Crée un producer Kafka configuré à partir des settings."""

    bootstrap = os.getenv("KAFKA_BOOTSTRAP_SERVERS", settings.kafka_bootstrap_servers)
    conf = {
        "bootstrap.servers": bootstrap,
        "acks": settings.kafka_producer_acks,  # "all" recommandé
        "retries": settings.kafka_producer_retries,
        "compression.type": settings.kafka_producer_compression_type,
        "enable.idempotence": True,  # évite les doublons en cas de retry
        "linger.ms": 50,  # batch léger
        "batch.num.messages": 1000,
        "message.timeout.ms": 30000,  # 30s avant timeout local
    }
    logger.info("Creating Kafka producer with bootstrap.servers=%s", bootstrap)
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
    - offers : liste de dicts,
    - topic : nom du topic,
    - key_field : champ utilisé comme clé (pour la partition), ex: "id".
    Retourne le nombre de messages envoyés (produced).
    """
    producer = get_producer()
    sent = 0
    error_count = 0

    def delivery_report(err, msg):
        nonlocal error_count
        if err is not None:
            error_count += 1
            logger.error(
                "Kafka delivery failed for %s [%s] at offset %s: %s",
                msg.topic(),
                msg.partition(),
                msg.offset(),
                err,
            )
        else:
            logger.debug(
                "Kafka message delivered to %s [%s] at offset %s",
                msg.topic(),
                msg.partition(),
                msg.offset(),
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
        except BufferError as e:
            logger.warning("Kafka local queue full, flushing producer: %s", e)
            producer.flush()
            try:
                producer.produce(
                    topic=topic,
                    key=key,
                    value=json.dumps(offer).encode("utf-8"),
                    callback=delivery_report,
                )
                sent += 1
            except Exception:
                logger.exception(
                    "Failed to publish offer to Kafka after flush (id=%s)",
                    offer.get("id"),
                )
        except Exception:
            logger.exception("Failed to publish offer to Kafka (id=%s)", offer.get("id"))

    producer.flush(60)

    if error_count > 0:
        logger.error(
            "Kafka publish finished with %d delivery errors on topic '%s'",
            error_count,
            topic,
        )

    logger.info("Published %d offers to Kafka topic '%s'", sent, topic)
    return sent
