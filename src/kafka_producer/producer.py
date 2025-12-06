# src/kafka_producer/producer.py
from __future__ import annotations

import json
from collections.abc import Iterable, Mapping

from confluent_kafka import KafkaError, Message, Producer

from config.logging_config import get_logger
from config.settings import settings

logger = get_logger(__name__)


class OfferKafkaProducer:
    def __init__(self) -> None:
        conf = {
            "bootstrap.servers": settings.kafka_bootstrap_servers,
            "acks": settings.kafka_producer_acks,
            "compression.type": settings.kafka_producer_compression_type,
            "retries": settings.kafka_producer_retries,
            # optionnel : un peu de batching
            # "linger.ms": 5,
        }
        logger.info(
            "Initializing Kafka producer with bootstrap.servers=%s", conf["bootstrap.servers"]
        )
        self._producer = Producer(conf)
        self._topic_raw = settings.kafka_topic_raw_offers

    def _delivery_report(self, err: KafkaError | None, msg: Message) -> None:
        if err is not None:
            logger.error(
                "Message delivery failed for %s [%d] at offset %s: %s",
                msg.topic(),
                msg.partition(),
                msg.offset(),
                err,
            )
        else:
            logger.debug(
                "Message delivered to %s [%d] at offset %d",
                msg.topic(),
                msg.partition(),
                msg.offset(),
            )

    def produce_offers(self, offers: Iterable[Mapping]) -> int:
        """
        Publie un batch d'offres (brutes) sur le topic raw.
        Retourne le nombre d'offres *tentées*.
        """
        count = 0

        for offer in offers:
            try:
                key = str(offer.get("id") or offer.get("idOffre") or "")
                value = json.dumps(offer, ensure_ascii=False)

                self._producer.produce(
                    topic=self._topic_raw,
                    key=key.encode() if key else None,
                    value=value.encode("utf-8"),
                    callback=self._delivery_report,
                )
                count += 1

            except BufferError as e:
                logger.warning("Producer buffer full, flushing… (%s)", e)
                self._producer.flush()
                try:
                    self._producer.produce(
                        topic=self._topic_raw,
                        key=key.encode() if key else None,
                        value=value.encode("utf-8"),
                        callback=self._delivery_report,
                    )
                    count += 1
                except Exception:
                    logger.exception(
                        "Failed to publish offer to Kafka after flush (id=%s)",
                        offer.get("id"),
                    )

            except Exception:
                logger.exception(
                    "Failed to publish offer to Kafka (id=%s)",
                    offer.get("id"),
                )

        # On force l’envoi de tout ce qui est en attente
        self._producer.flush()
        logger.info("Published %d offers to Kafka topic '%s'", count, self._topic_raw)
        return count
