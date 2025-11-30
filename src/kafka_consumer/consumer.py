# src/kafka_consumer/consumer.py
from __future__ import annotations

import json
import os
import signal
import sys
from typing import Any

from confluent_kafka import Consumer, Producer

from config.logging_config import get_logger, setup_logging
from config.settings import settings
from db.repository import OfferRepository
from db.sessions import get_session
from etl.transformers.cleaner import clean_offer
from etl.transformers.validator import validate_offer 

logger = get_logger(__name__)


class OfferKafkaConsumer:
    def __init__(self) -> None:
        
        bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", 
                                      settings.kafka_bootstrap_servers)
        consumer_conf = {
            "bootstrap.servers": bootstrap_servers,
            "group.id": settings.kafka_consumer_group,
            "auto.offset.reset": settings.kafka_auto_offset_reset,
            "enable.auto.commit": settings.kafka_enable_auto_commit,
            "max.poll.interval.ms": 300000,
            "session.timeout.ms": settings.kafka_session_timeout_ms,
        }
        self._consumer = Consumer(consumer_conf)
        self._topic_raw = settings.kafka_topic_raw_offers
        self._topic_dlq = settings.kafka_topic_dlq

        # Producer pour la DLQ
        producer_conf = {
            "bootstrap.servers": settings.kafka_bootstrap_servers,
            "acks": "1",
        }
        self._dlq_producer = Producer(producer_conf)

        self._running = True

    def _send_to_dlq(self, msg, error: str) -> None:
        try:
            dlq_payload: dict[str, Any] = {
                "original_topic": msg.topic(),
                "original_partition": msg.partition(),
                "original_offset": msg.offset(),
                "key": msg.key().decode() if msg.key() else None,
                "value": msg.value().decode("utf-8") if msg.value() else None,
                "error": error,
            }
            self._dlq_producer.produce(
                topic=self._topic_dlq,
                value=json.dumps(dlq_payload).encode("utf-8"),
            )
        except Exception as e:
            logger.error("Failed to send message to DLQ: %s", e)

    def run(self) -> None:
        logger.info("Starting Kafka consumer, subscribing to %s", self._topic_raw)
        self._consumer.subscribe([self._topic_raw])

        def _signal_handler(sig, frame):
            logger.info("Signal %s received, stopping consumer...", sig)
            self._running = False

        signal.signal(signal.SIGINT, _signal_handler)
        signal.signal(signal.SIGTERM, _signal_handler)

        while self._running:
            msg = self._consumer.poll(timeout=1.0)
            if msg is None:
                continue
            if msg.error():
                logger.error("Consumer error: %s", msg.error())
                continue

            try:
                raw_json = msg.value().decode("utf-8")
                raw_offer = json.loads(raw_json)

                # 1) Clean + validate
                cleaned = clean_offer(raw_offer)
                if not validate_offer(cleaned):
                    logger.warning("Offer failed validation, sending to DLQ (id=%s)", cleaned.get("id"))
                    self._send_to_dlq(msg, "validation_failed")
                    self._consumer.commit(message=msg)
                    continue

                # 2) Persistence
                with get_session() as db:
                    repo = OfferRepository(db)
                    repo.upsert_from_api(cleaned)
                    db.commit()

                # 3) Commit si tout OK
                self._consumer.commit(message=msg)

            except Exception as e:
                logger.exception("Error processing message, sending to DLQ")
                self._send_to_dlq(msg, str(e))
                self._consumer.commit(message=msg)

        logger.info("Closing consumer...")
        self._consumer.close()
        self._dlq_producer.flush()


def main() -> None:
    setup_logging()
    consumer = OfferKafkaConsumer()
    consumer.run()


if __name__ == "__main__":
    main()
