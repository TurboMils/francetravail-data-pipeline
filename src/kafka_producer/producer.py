from __future__ import annotations

import json
from typing import Iterable, Mapping

from confluent_kafka import Producer

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
        }
        self._producer = Producer(conf)
        self._topic_raw = settings.kafka_topic_raw_offers
        
    def _delivery_report(self, err, msg) -> None:
        if err is not None:
            logger.error("Message delivery failed: %s", err)
        else:
            logger.debug(
                "Message delivered to %s [%d] at offset %d",
                msg.topic(),
                msg.partition(),
                msg.offset(),
            )
            
    def produce_offers(self, offers: Iterable[Mapping]) -> int:
        """Publie un batch d'offres (brutes) sur Kafka. Retourne le nb publié."""
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
                # buffer plein → flush puis retry
                logger.warning("Producer buffer full, flushing... : {e}")
                self._producer.flush()
                
        self._producer.flush()
        logger.info("Published %d offers to topic %s", count, self._topic_raw)
        return count